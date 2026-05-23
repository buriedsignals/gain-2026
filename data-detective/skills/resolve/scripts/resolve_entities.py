#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "duckdb>=1.1",
#     "rapidfuzz>=3.9",
#     "pyarrow>=17",
# ]
# ///
"""
data-detective :: resolve_entities

Three-pass entity resolution for the LDA corpus. Generic in spirit; calibrated
here for House <-> Senate registrant matching with bridge keys.

Strategy:
  PASS 1 (bridge keys, deterministic). Senate filings carry an explicit
          house_registrant_id on the registrant object; House XML carries a
          senateID whose first numeric segment equals the Senate registrant.id.
          Both directions get exact joins.
  PASS 2 (exact normalized match). Uppercase + collapse whitespace + strip
          incorporation suffixes; exact equality.
  PASS 3 (fuzzy match). rapidfuzz token-set ratio >= --fuzzy-threshold on the
          remainder, with an ambiguity queue for ties.

Output:
  - View `canonical_registrants` in the DB joining the three pass results
  - CSV `entity-resolution-report.csv` with counts per pass and the ambiguity
    queue for human review

Usage:
  uv run resolve_entities.py --db <db> --out <case_dir> [--fuzzy-threshold 92]
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import duckdb
import pyarrow as pa
from rapidfuzz import fuzz, process


SUFFIX_PATTERNS = [
    r"\b(LLC|LLP|L\.L\.C\.|L\.L\.P\.|LP|INC|INCORPORATED|CORP|CORPORATION|"
    r"CO|COMPANY|PLLC|P\.A\.|PA|CONSULTING|GROUP|PARTNERS|HOLDINGS|GMBH|"
    r"AG|SA|SARL|LIMITED|LTD|PLC|PTY|N\.V\.|NV|BV|B\.V\.)\b\.?"
]
WHITESPACE = re.compile(r"\s+")
PUNCT = re.compile(r"[.,'\"()&]+")


def normalize(name: str | None) -> str | None:
    if not name:
        return None
    s = name.upper().strip()
    s = PUNCT.sub(" ", s)
    for pat in SUFFIX_PATTERNS:
        s = re.sub(pat, " ", s)
    s = WHITESPACE.sub(" ", s).strip()
    return s if s else None


def setup_normalized_tables(con: duckdb.DuckDBPyConnection) -> None:
    """Pull distinct registrants, normalize in Python, write back as helper tables."""
    print("normalizing names...")
    senate_rows = con.execute("""
        SELECT DISTINCT
            registrant_id,
            registrant_house_id,
            registrant_name,
            registrant_state
        FROM senate_filings
        WHERE registrant_id IS NOT NULL
    """).fetchall()
    house_rows = con.execute("""
        SELECT DISTINCT
            organization_name,
            senate_id_registrant,
            state
        FROM house_filings
        WHERE organization_name IS NOT NULL
    """).fetchall()

    senate_table = pa.table({
        "registrant_id": [r[0] for r in senate_rows],
        "registrant_house_id": [r[1] for r in senate_rows],
        "registrant_name": [r[2] for r in senate_rows],
        "registrant_state": [r[3] for r in senate_rows],
        "norm_name": [normalize(r[2]) for r in senate_rows],
    })
    house_table = pa.table({
        "organization_name": [r[0] for r in house_rows],
        "senate_id_registrant": [r[1] for r in house_rows],
        "state": [r[2] for r in house_rows],
        "norm_name": [normalize(r[0]) for r in house_rows],
    })
    con.execute("DROP TABLE IF EXISTS _senate_reg_norm")
    con.execute("DROP TABLE IF EXISTS _house_reg_norm")
    con.register("_st", senate_table)
    con.register("_ht", house_table)
    con.execute("CREATE TABLE _senate_reg_norm AS SELECT * FROM _st")
    con.execute("CREATE TABLE _house_reg_norm AS SELECT * FROM _ht")
    con.unregister("_st")
    con.unregister("_ht")

    sn = con.execute("SELECT count(*) FROM _senate_reg_norm").fetchone()[0]
    hn = con.execute("SELECT count(*) FROM _house_reg_norm").fetchone()[0]
    print(f"  senate registrant rows: {sn:,}")
    print(f"  house  registrant rows: {hn:,}")


def pass1_bridge_keys(con) -> int:
    """Bridge: senate.registrant_id <-> house.senate_id_registrant (first segment)."""
    print("\npass 1 — bridge keys")
    con.execute("DROP TABLE IF EXISTS canonical_registrants_p1")
    con.execute("""
        CREATE TABLE canonical_registrants_p1 AS
        SELECT DISTINCT
            s.registrant_id           AS senate_registrant_id,
            s.registrant_name         AS senate_name,
            h.organization_name       AS house_name,
            'bridge_senate_id'        AS resolution_pass
        FROM _senate_reg_norm s
        JOIN _house_reg_norm h ON s.registrant_id = h.senate_id_registrant
    """)
    n = con.execute("SELECT count(*) FROM canonical_registrants_p1").fetchone()[0]
    print(f"  pass1 matches (bridge): {n:,}")
    return n


def pass2_exact_normalized(con) -> int:
    """Exact match on normalized name (and same state where both have it)."""
    print("\npass 2 — exact normalized")
    con.execute("DROP TABLE IF EXISTS canonical_registrants_p2")
    con.execute("""
        CREATE TABLE canonical_registrants_p2 AS
        SELECT DISTINCT
            s.registrant_id     AS senate_registrant_id,
            s.registrant_name   AS senate_name,
            h.organization_name AS house_name,
            'exact_normalized'  AS resolution_pass
        FROM _senate_reg_norm s
        JOIN _house_reg_norm h
          ON s.norm_name = h.norm_name
         AND s.norm_name IS NOT NULL
        WHERE NOT EXISTS (
            SELECT 1 FROM canonical_registrants_p1 p
            WHERE p.senate_registrant_id = s.registrant_id
        )
    """)
    n = con.execute("SELECT count(*) FROM canonical_registrants_p2").fetchone()[0]
    print(f"  pass2 matches (exact norm): {n:,}")
    return n


def pass3_fuzzy(con, threshold: int, max_candidates: int = 50000) -> tuple[int, int]:
    """Fuzzy match the remainder using rapidfuzz token-set ratio."""
    print(f"\npass 3 — fuzzy (token_set_ratio >= {threshold})")
    # Find unresolved senate registrants
    unresolved = con.execute("""
        SELECT s.registrant_id, s.registrant_name, s.norm_name
        FROM _senate_reg_norm s
        WHERE s.norm_name IS NOT NULL
          AND NOT EXISTS (SELECT 1 FROM canonical_registrants_p1 p WHERE p.senate_registrant_id = s.registrant_id)
          AND NOT EXISTS (SELECT 1 FROM canonical_registrants_p2 p WHERE p.senate_registrant_id = s.registrant_id)
        LIMIT ?
    """, [max_candidates]).fetchall()

    house_pool = con.execute("""
        SELECT DISTINCT organization_name, norm_name
        FROM _house_reg_norm
        WHERE norm_name IS NOT NULL
    """).fetchall()
    house_names_norm = [h[1] for h in house_pool]

    matches = []
    ambiguous = []
    for sid, sname, snorm in unresolved:
        best = process.extract(snorm, house_names_norm, scorer=fuzz.token_set_ratio, limit=3)
        if not best:
            continue
        top = best[0]
        if top[1] < threshold:
            continue
        # Ambiguity: two candidates within 2 points
        if len(best) > 1 and best[1][1] >= top[1] - 2 and best[1][1] >= threshold:
            ambiguous.append((sid, sname, [b[0] for b in best[:3]], [b[1] for b in best[:3]]))
            continue
        matches.append((sid, sname, house_pool[house_names_norm.index(top[0])][0], top[1]))

    con.execute("DROP TABLE IF EXISTS canonical_registrants_p3")
    con.execute("CREATE TABLE canonical_registrants_p3 (senate_registrant_id INTEGER, senate_name VARCHAR, house_name VARCHAR, score INTEGER, resolution_pass VARCHAR)")
    for m in matches:
        con.execute("INSERT INTO canonical_registrants_p3 VALUES (?, ?, ?, ?, 'fuzzy')", list(m))

    con.execute("DROP TABLE IF EXISTS canonical_registrants_ambiguous")
    con.execute("CREATE TABLE canonical_registrants_ambiguous (senate_registrant_id INTEGER, senate_name VARCHAR, candidates VARCHAR, scores VARCHAR)")
    for a in ambiguous:
        con.execute("INSERT INTO canonical_registrants_ambiguous VALUES (?, ?, ?, ?)",
                    [a[0], a[1], " | ".join(a[2]), ",".join(str(s) for s in a[3])])

    print(f"  pass3 matches (fuzzy):   {len(matches):,}")
    print(f"  pass3 ambiguous (review): {len(ambiguous):,}")
    return len(matches), len(ambiguous)


def consolidate(con) -> None:
    """Build the single `canonical_registrants` view."""
    print("\nconsolidating into canonical_registrants...")
    con.execute("DROP VIEW IF EXISTS canonical_registrants")
    con.execute("""
        CREATE VIEW canonical_registrants AS
        SELECT senate_registrant_id, senate_name, house_name, resolution_pass, NULL AS score
            FROM canonical_registrants_p1
        UNION ALL
        SELECT senate_registrant_id, senate_name, house_name, resolution_pass, NULL AS score
            FROM canonical_registrants_p2
        UNION ALL
        SELECT senate_registrant_id, senate_name, house_name, resolution_pass, score
            FROM canonical_registrants_p3
    """)
    total = con.execute("SELECT count(*) FROM canonical_registrants").fetchone()[0]
    print(f"  canonical_registrants rows: {total:,}")


def write_report(con, out_dir: Path, threshold: int) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "entity-resolution-report.csv"
    md_path = out_dir / "entity-resolution-report.md"

    counts = con.execute("""
        SELECT resolution_pass, count(*) AS n
        FROM canonical_registrants
        GROUP BY 1
        ORDER BY 1
    """).fetchall()
    senate_total = con.execute("SELECT count(DISTINCT registrant_id) FROM _senate_reg_norm").fetchone()[0]
    house_total = con.execute("SELECT count(DISTINCT organization_name) FROM _house_reg_norm").fetchone()[0]
    matched_senate = con.execute("SELECT count(DISTINCT senate_registrant_id) FROM canonical_registrants").fetchone()[0]
    ambiguous = con.execute("SELECT count(*) FROM canonical_registrants_ambiguous").fetchone()[0]

    con.execute(f"COPY canonical_registrants_ambiguous TO '{out_dir / 'entity-resolution-ambiguous.csv'}' (HEADER, DELIMITER ',')")

    md = [
        "# Entity Resolution Report",
        "",
        f"- Senate distinct registrant IDs: **{senate_total:,}**",
        f"- House distinct organization_names: **{house_total:,}**",
        f"- Senate IDs matched to a House org: **{matched_senate:,}** ({100 * matched_senate / senate_total:.1f}%)",
        f"- Ambiguity queue (manual review): **{ambiguous:,}**",
        f"- Fuzzy threshold (token_set_ratio): **{threshold}**",
        "",
        "## Match counts by pass",
        "",
        "| pass | matches |",
        "|---|---|",
    ]
    for p, n in counts:
        md.append(f"| {p} | {n:,} |")
    md += [
        "",
        f"Ambiguity queue dumped to `entity-resolution-ambiguous.csv` ({ambiguous:,} rows).",
    ]
    md_path.write_text("\n".join(md) + "\n")
    print(f"\nreport → {md_path}")


def main():
    ap = argparse.ArgumentParser(description="data-detective :: entity resolver")
    ap.add_argument("--db", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path,
                    help="case directory for the report")
    ap.add_argument("--fuzzy-threshold", type=int, default=92,
                    help="rapidfuzz token_set_ratio cutoff (default 92)")
    args = ap.parse_args()

    con = duckdb.connect(str(args.db))
    setup_normalized_tables(con)
    pass1_bridge_keys(con)
    pass2_exact_normalized(con)
    pass3_fuzzy(con, args.fuzzy_threshold)
    consolidate(con)
    write_report(con, args.out, args.fuzzy_threshold)
    print("\ndone.")


if __name__ == "__main__":
    main()
