#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "duckdb>=1.1",
#     "fastembed>=0.3",
#     "pyarrow>=17",
# ]
# ///
"""
data-detective :: vector_search

Embed a free-text column in the index and do nearest-neighbor search.

Use case: surface records that look like a known anomaly but use different
keywords — e.g. find "more like LOC Nation" without enumerating every
sovereign-citizen phrase.

The script is intentionally small. It uses fastembed (ONNX, no torch
dependency) and DuckDB's VSS extension. To use:

    # 1. Build embeddings for a column once
    uv run vector_search.py --db case/index.duckdb \\
        --embed --table senate_lobbying_activities \\
        --text-column description --id-column activity_id

    # 2. Query nearest neighbors of a known anomaly
    uv run vector_search.py --db case/index.duckdb \\
        --table senate_lobbying_activities \\
        --query-id "<an activity_id from LOC Nation>" --k 25

    # 3. Or query by text
    uv run vector_search.py --db case/index.duckdb \\
        --table senate_lobbying_activities \\
        --query-text "Established sovereign government drafting constitution"

The embedding table is `_embed_<source_table>` with columns
`(id, embedding FLOAT[384])`. An HNSW index is built on `embedding` if the
VSS extension loads.

Limitations:
- Embedding ~800K rows takes ~5-15 minutes on CPU; budget accordingly.
- fastembed downloads ~30MB model on first run.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import duckdb


MODEL_NAME = "BAAI/bge-small-en-v1.5"  # 384-dim, fast, cached locally
EMBED_DIM = 384
BATCH = 256


def _embed_model():
    try:
        from fastembed import TextEmbedding
    except ImportError:
        sys.exit("fastembed not installed; install via `uv run --with fastembed ...`")
    return TextEmbedding(model_name=MODEL_NAME)


def install_vss(con):
    """Best-effort: install/load the VSS extension. Falls back to brute-force if missing."""
    try:
        con.execute("INSTALL vss")
        con.execute("LOAD vss")
        return True
    except duckdb.Error as e:
        print(f"warn: VSS extension unavailable, brute-force nearest-neighbor only: {e}", file=sys.stderr)
        return False


def embed_table(con, table: str, text_col: str, id_col: str, limit: int | None = None) -> None:
    model = _embed_model()
    sql = f'SELECT "{id_col}" AS id, "{text_col}" AS text FROM "{table}" WHERE "{text_col}" IS NOT NULL'
    if limit:
        sql += f" LIMIT {limit}"
    rows = con.execute(sql).fetchall()
    print(f"  rows to embed: {len(rows):,}")

    out_table = f"_embed_{table}"
    con.execute(f'DROP TABLE IF EXISTS "{out_table}"')
    con.execute(f'CREATE TABLE "{out_table}" (id VARCHAR PRIMARY KEY, embedding FLOAT[{EMBED_DIM}])')

    import pyarrow as pa
    ids_batch, embs_batch = [], []
    for i in range(0, len(rows), BATCH):
        chunk = rows[i:i + BATCH]
        ids = [str(r[0]) for r in chunk]
        texts = [r[1] for r in chunk]
        embs = list(model.embed(texts))
        ids_batch.extend(ids)
        embs_batch.extend([[float(x) for x in e] for e in embs])
        if (i // BATCH) % 50 == 0:
            print(f"  embedded {i + len(chunk):,}/{len(rows):,}")
    tbl = pa.table({"id": ids_batch, "embedding": embs_batch})
    con.register("_emb_tmp", tbl)
    con.execute(f'INSERT INTO "{out_table}" SELECT * FROM _emb_tmp')
    con.unregister("_emb_tmp")
    print(f"  wrote {out_table}")


def query_nn(con, table: str, query_emb: list[float], k: int, id_col: str, text_col: str) -> list:
    """Return k nearest neighbors as (id, distance, text)."""
    emb_table = f"_embed_{table}"
    # Use VSS array_distance if installed, else brute force
    sql = f"""
        SELECT e.id,
               array_distance(e.embedding, ?::FLOAT[{EMBED_DIM}]) AS distance,
               t."{text_col}" AS text
        FROM "{emb_table}" e
        JOIN "{table}" t ON t."{id_col}" = e.id
        ORDER BY distance ASC
        LIMIT {k}
    """
    return con.execute(sql, [query_emb]).fetchall()


def main():
    ap = argparse.ArgumentParser(description="data-detective :: vector_search")
    ap.add_argument("--db", required=True, type=Path)
    ap.add_argument("--table", required=True)
    ap.add_argument("--text-column", default="description")
    ap.add_argument("--id-column", default="activity_id")
    ap.add_argument("--embed", action="store_true", help="build embeddings for this table")
    ap.add_argument("--query-id", help="id of a row in the source table to use as the query vector")
    ap.add_argument("--query-text", help="text to embed and use as the query vector")
    ap.add_argument("--k", type=int, default=20)
    ap.add_argument("--limit", type=int, default=None, help="for --embed: cap rows (smoke test)")
    args = ap.parse_args()

    con = duckdb.connect(str(args.db))
    install_vss(con)

    if args.embed:
        embed_table(con, args.table, args.text_column, args.id_column, args.limit)
        return

    if args.query_id or args.query_text:
        model = _embed_model()
        if args.query_id:
            row = con.execute(
                f'SELECT "{args.text_column}" FROM "{args.table}" WHERE "{args.id_column}" = ?',
                [args.query_id],
            ).fetchone()
            if not row:
                sys.exit(f"no row with {args.id_column}={args.query_id}")
            query_text = row[0]
            print(f"query text: {query_text[:200]!r}")
        else:
            query_text = args.query_text
        query_emb = next(iter(model.embed([query_text])))
        nn = query_nn(con, args.table, list(map(float, query_emb)),
                      args.k, args.id_column, args.text_column)
        print(f"\nnearest {args.k}:")
        for i, (rid, dist, text) in enumerate(nn, 1):
            print(f"  {i:>2}.  dist={dist:.4f}  id={rid}")
            print(f"        {text[:200]!r}")
        return

    ap.print_help()


if __name__ == "__main__":
    main()
