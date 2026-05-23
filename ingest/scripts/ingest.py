#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "duckdb>=1.1",
#     "lxml>=5.0",
#     "tqdm>=4.66",
#     "pyarrow>=17",
# ]
# ///
"""
data-detective :: ingest

Profile-driven ETL from structured records (JSON/JSONL/XML) into a DuckDB index.

A profile is a Python module that defines:
    NAME, DESCRIPTION : str
    SOURCES           : list of source descriptors
    TABLES            : optional explicit schemas
    INDEXES           : optional list of (table, [cols]) to create after load
    map_*             : mapper functions named in source descriptors

A source descriptor has:
    id        : str               unique id (used in manifest)
    format    : 'json_array'      load entire file as JSON list, iterate
              | 'jsonl'           load file line-by-line
              | 'xml_dir'         iterate *.xml in glob, parse each
    glob      : str               path glob relative to --data-root
    mapper    : str               name of mapper function in profile
    batch     : int (optional)    rows to accumulate before DB flush (default 5000)

Mapper signature:
    def map_X(record_or_root, source_file: Path) -> dict[str, list[dict]]
        # returns: { "table_name": [row_dict, ...], ... }

Usage:
    uv run ingest.py --profile <path/to/profile.py> \\
                     --data-root <corpus_root> \\
                     --db <output.duckdb> \\
                     [--source <source_id>]  # restrict to one source
                     [--year <year>]         # restrict to one year (filters globs)
                     [--limit <n>]           # cap records per source (smoke test)

Resumable: a checkpoint table (`_ingest_checkpoints`) records every (source_id, file)
combination that's been ingested. Re-running skips completed files unless --force.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import duckdb
import pyarrow as pa
from lxml import etree
from tqdm import tqdm


def load_profile(path: Path):
    spec = importlib.util.spec_from_file_location("profile", path)
    if spec is None or spec.loader is None:
        sys.exit(f"could not load profile: {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    for required in ("NAME", "SOURCES"):
        if not hasattr(mod, required):
            sys.exit(f"profile missing required attribute: {required}")
    return mod


def file_sha256(path: Path, chunk_size: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            buf = f.read(chunk_size)
            if not buf:
                break
            h.update(buf)
    return h.hexdigest()


def ensure_checkpoint_table(con: duckdb.DuckDBPyConnection) -> None:
    con.execute("""
        CREATE TABLE IF NOT EXISTS _ingest_checkpoints (
            source_id   VARCHAR,
            file_path   VARCHAR,
            file_sha256 VARCHAR,
            row_count   BIGINT,
            ingested_at TIMESTAMP DEFAULT current_timestamp,
            PRIMARY KEY (source_id, file_path)
        )
    """)


def is_file_done(con, source_id: str, file_path: str, sha: str) -> bool:
    row = con.execute(
        "SELECT file_sha256 FROM _ingest_checkpoints WHERE source_id=? AND file_path=?",
        [source_id, file_path],
    ).fetchone()
    return bool(row and row[0] == sha)


def record_checkpoint(con, source_id: str, file_path: str, sha: str, row_count: int) -> None:
    con.execute(
        "INSERT OR REPLACE INTO _ingest_checkpoints VALUES (?, ?, ?, ?, current_timestamp)",
        [source_id, file_path, sha, row_count],
    )


def ensure_tables(con, tables_schema: dict[str, dict]) -> None:
    """Create tables from an explicit schema dict (column_name -> SQL type)."""
    for table, spec in tables_schema.items():
        cols = ", ".join(f'"{name}" {sqltype}' for name, sqltype in spec["columns"].items())
        con.execute(f'CREATE TABLE IF NOT EXISTS "{table}" ({cols})')


def normalize_row(row: dict, columns: list[str]) -> tuple:
    """Order a row dict according to a column list, filling missing with None."""
    return tuple(row.get(c) for c in columns)


def insert_rows(con, table: str, rows: list[dict], schema_columns: list[str] | None) -> None:
    """Bulk-insert via pyarrow. Order of magnitude faster than executemany for DuckDB."""
    if not rows:
        return
    if schema_columns is None:
        keys = sorted({k for r in rows for k in r.keys()})
        col_defs = ", ".join(f'"{k}" VARCHAR' for k in keys)
        con.execute(f'CREATE TABLE IF NOT EXISTS "{table}" ({col_defs})')
        schema_columns = keys

    # Build a pyarrow Table with columns in target order. Strings everywhere
    # by default — DuckDB will cast at INSERT time to the declared column types.
    cols = {c: [] for c in schema_columns}
    for r in rows:
        for c in schema_columns:
            cols[c].append(r.get(c))
    # pyarrow.Table.from_pydict infers types per column; missing keys become None.
    pa_table = pa.Table.from_pydict(cols)
    col_list = ", ".join(f'"{c}"' for c in schema_columns)

    # Register the Arrow table as a temp view, then INSERT ... SELECT.
    con.register("_batch", pa_table)
    try:
        try:
            con.execute(f'INSERT INTO "{table}" ({col_list}) SELECT {col_list} FROM _batch ON CONFLICT DO NOTHING')
        except duckdb.Error:
            con.execute(f'INSERT INTO "{table}" ({col_list}) SELECT {col_list} FROM _batch')
    finally:
        con.unregister("_batch")


def iter_json_array(file_path: Path):
    with open(file_path) as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"json_array source expected list at top level: {file_path}")
    yield from data


def iter_jsonl(file_path: Path):
    with open(file_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def iter_xml_files(dir_or_glob: Path):
    """Yield (Path, etree.Element) for each .xml in a directory."""
    if dir_or_glob.is_dir():
        for p in sorted(dir_or_glob.glob("*.xml")):
            try:
                tree = etree.parse(str(p))
                yield p, tree.getroot()
            except etree.XMLSyntaxError as e:
                print(f"warn: skipping malformed XML {p}: {e}", file=sys.stderr)


def resolve_globs(data_root: Path, glob: str, year_filter: str | None) -> list[Path]:
    """Expand a glob that may contain {year} into actual file/dir paths."""
    paths: list[Path] = []
    if "{year}" in glob:
        years = [year_filter] if year_filter else ["2022", "2023", "2024", "2025", "2026"]
        for year in years:
            expanded = glob.format(year=year)
            paths.extend(sorted(data_root.glob(expanded)))
    else:
        paths.extend(sorted(data_root.glob(glob)))
    return paths


def ingest_source(
    con: duckdb.DuckDBPyConnection,
    source: dict,
    profile,
    data_root: Path,
    year_filter: str | None,
    limit: int | None,
    force: bool,
) -> dict:
    source_id = source["id"]
    fmt = source["format"]
    mapper = getattr(profile, source["mapper"])
    batch_size = source.get("batch", 5000)
    tables_schema = getattr(profile, "TABLES", {})

    paths = resolve_globs(data_root, source["glob"], year_filter)
    if not paths:
        print(f"[{source_id}] no files matched glob: {source['glob']}", file=sys.stderr)
        return {"source_id": source_id, "files": 0, "rows": 0}

    total_files = len(paths)
    total_rows = 0
    batch: dict[str, list[dict]] = defaultdict(list)

    def flush():
        nonlocal batch
        for tbl, rows in batch.items():
            cols = tables_schema.get(tbl, {}).get("columns")
            insert_rows(con, tbl, rows, list(cols.keys()) if cols else None)
        batch = defaultdict(list)

    print(f"\n[{source_id}] {total_files} files, format={fmt}")
    file_iter = tqdm(paths, desc=f"  {source_id}", unit="file")
    record_count_overall = 0

    for fp in file_iter:
        sha = file_sha256(fp) if fp.is_file() else "DIR-" + str(int(fp.stat().st_mtime))
        if not force and is_file_done(con, source_id, str(fp), sha):
            continue

        per_file_rows = 0

        if fmt == "json_array":
            iterator = iter_json_array(fp)
        elif fmt == "jsonl":
            iterator = iter_jsonl(fp)
        elif fmt == "xml_dir":
            iterator = iter_xml_files(fp)
        else:
            raise ValueError(f"unknown format: {fmt}")

        for item in iterator:
            if fmt == "xml_dir":
                xml_path, root = item
                row_groups = mapper(root, xml_path)
            else:
                row_groups = mapper(item, fp)
            for tbl, rows in row_groups.items():
                batch[tbl].extend(rows)
                per_file_rows += len(rows)
            record_count_overall += 1
            if sum(len(v) for v in batch.values()) >= batch_size:
                flush()
            if limit and record_count_overall >= limit:
                break

        record_checkpoint(con, source_id, str(fp), sha, per_file_rows)
        total_rows += per_file_rows
        if limit and record_count_overall >= limit:
            print(f"  [{source_id}] hit --limit {limit}")
            break

    flush()
    return {"source_id": source_id, "files": total_files, "rows": total_rows}


def create_indexes(con, indexes: list[tuple[str, list[str]]]) -> None:
    for table, cols in indexes:
        idx_name = f"idx_{table}_{'_'.join(cols)}"
        col_list = ", ".join(f'"{c}"' for c in cols)
        try:
            con.execute(f'CREATE INDEX IF NOT EXISTS "{idx_name}" ON "{table}" ({col_list})')
            print(f"  index: {idx_name}")
        except Exception as e:
            print(f"  warn: failed to create {idx_name}: {e}", file=sys.stderr)


def write_manifest(con, manifest_path: Path, profile_name: str) -> None:
    tables = con.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='main' AND table_name NOT LIKE '\\_%' ESCAPE '\\'"
    ).fetchall()
    table_counts = {}
    for (t,) in tables:
        n = con.execute(f'SELECT count(*) FROM "{t}"').fetchone()[0]
        table_counts[t] = n
    checkpoints = con.execute(
        "SELECT source_id, count(*), sum(row_count) FROM _ingest_checkpoints GROUP BY source_id"
    ).fetchall()
    manifest = {
        "profile": profile_name,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "table_counts": table_counts,
        "sources": [
            {"source_id": s, "files_ingested": int(f), "rows_emitted": int(r or 0)}
            for s, f, r in checkpoints
        ],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2))
    print(f"\nmanifest → {manifest_path}")
    for t, n in sorted(table_counts.items()):
        print(f"  {t}: {n:,}")


def main():
    ap = argparse.ArgumentParser(description="data-detective :: ingest")
    ap.add_argument("--profile", required=True, type=Path)
    ap.add_argument("--data-root", required=True, type=Path)
    ap.add_argument("--db", required=True, type=Path)
    ap.add_argument("--manifest", type=Path, default=None,
                    help="output manifest path (default: <db>.manifest.json)")
    ap.add_argument("--source", default=None, help="restrict to one source id")
    ap.add_argument("--year", default=None, help="restrict to one year")
    ap.add_argument("--limit", type=int, default=None,
                    help="cap records per source (smoke testing)")
    ap.add_argument("--force", action="store_true",
                    help="re-ingest files already in checkpoint table")
    args = ap.parse_args()

    if not args.profile.exists():
        sys.exit(f"profile not found: {args.profile}")
    if not args.data_root.is_dir():
        sys.exit(f"data root not a directory: {args.data_root}")

    args.db.parent.mkdir(parents=True, exist_ok=True)
    profile = load_profile(args.profile)
    print(f"profile: {profile.NAME}")
    print(f"data-root: {args.data_root}")
    print(f"db: {args.db}")

    con = duckdb.connect(str(args.db))
    ensure_checkpoint_table(con)
    if hasattr(profile, "TABLES"):
        ensure_tables(con, profile.TABLES)

    summary = []
    for source in profile.SOURCES:
        if args.source and source["id"] != args.source:
            continue
        result = ingest_source(con, source, profile, args.data_root, args.year, args.limit, args.force)
        summary.append(result)

    if hasattr(profile, "INDEXES"):
        print("\ncreating indexes...")
        create_indexes(con, profile.INDEXES)

    manifest_path = args.manifest or args.db.with_suffix(".manifest.json")
    write_manifest(con, manifest_path, profile.NAME)

    print("\ningest complete:")
    for s in summary:
        print(f"  {s['source_id']:30s}  files={s['files']:>6}  rows={s['rows']:>10,}")


if __name__ == "__main__":
    main()
