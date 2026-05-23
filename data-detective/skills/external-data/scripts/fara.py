#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "duckdb>=1.1",
#     "lxml>=5.0",
#     "httpx>=0.28",
# ]
# ///
"""
data-detective :: external/fara

Pull the U.S. DOJ Foreign Agents Registration Act (FARA) bulk dataset and
load it into the same DuckDB index used by the rest of the skill.

The DOJ's own FARA bulk-data page is slow and JS-driven; OpenSanctions mirrors
the original XML files daily and exposes them at:

    https://data.opensanctions.org/datasets/latest/us_fara_filings/

Two source XMLs:

  FARA_All_Registrants.xml         registered firms / persons
  FARA_All_ForeignPrincipals.xml   the foreign principals they represent

Tables produced:

  fara_registrants
  fara_foreign_principals

These can be joined to `senate_filings`, `senate_foreign_entities`, and
`house_foreign_entities` by normalized name. That join is what surfaces
"lobbying disclosed under LDA but absent from FARA" or vice versa.

Usage:
  uv run external/fara.py --db <db> --cache <dir>          # download + load
  uv run external/fara.py --db <db> --cache <dir> --offline # skip download
"""
from __future__ import annotations

import argparse
import io
import sys
import zipfile
from datetime import datetime
from pathlib import Path

import duckdb
import httpx
from lxml import etree


REGISTRANTS_URL = "https://data.opensanctions.org/datasets/latest/us_fara_filings/FARA_All_Registrants.xml"
FOREIGN_PRINCIPALS_URL = "https://data.opensanctions.org/datasets/latest/us_fara_filings/FARA_All_ForeignPrincipals.xml"


def download(url: str, cache_dir: Path) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    name = url.rsplit("/", 1)[-1]
    out_path = cache_dir / name
    if out_path.exists():
        print(f"  cached: {out_path.name}")
        return out_path
    print(f"  fetching {url}")
    with httpx.Client(follow_redirects=True, timeout=120) as client:
        with client.stream("GET", url) as resp:
            resp.raise_for_status()
            with out_path.open("wb") as f:
                for chunk in resp.iter_bytes(chunk_size=1 << 20):
                    f.write(chunk)
    print(f"  saved   {out_path.name} ({out_path.stat().st_size:,} bytes)")
    return out_path


def open_maybe_zip(path: Path) -> bytes:
    """Some mirrored XML files are gzipped/zipped. Return raw bytes."""
    with path.open("rb") as f:
        head = f.read(4)
        f.seek(0)
        if head[:2] == b"PK":
            with zipfile.ZipFile(f) as zf:
                # OpenSanctions packages one XML per zip
                names = [n for n in zf.namelist() if n.lower().endswith(".xml")]
                if not names:
                    raise ValueError(f"no XML in zip: {path.name}")
                return zf.read(names[0])
        return f.read()


def _strip(s: str | None) -> str | None:
    if s is None:
        return None
    s = s.strip()
    return s if s else None


def parse_registrants(xml_bytes: bytes) -> list[dict]:
    """Parse FARA_All_Registrants.xml. Each <ROW> = one registrant snapshot."""
    rows = []
    parser = etree.XMLParser(recover=True, encoding="utf-8")
    root = etree.fromstring(xml_bytes, parser=parser)
    for r in root.iter("ROW"):
        row = {child.tag.lower(): _strip(child.text) for child in r}
        rows.append({
            "registration_number": row.get("registration_number"),
            "registrant_name": row.get("name"),
            "address_1": row.get("address_1"),
            "address_2": row.get("address_2"),
            "city": row.get("city"),
            "state": row.get("state"),
            "zip": row.get("zip"),
            "registration_date": row.get("registration_date"),
            "termination_date": row.get("termination_date"),
            "registration_type": row.get("type"),
        })
    return rows


def parse_foreign_principals(xml_bytes: bytes) -> list[dict]:
    """Parse FARA_All_ForeignPrincipals.xml. Each <ROW> = one foreign principal record."""
    rows = []
    parser = etree.XMLParser(recover=True, encoding="utf-8")
    root = etree.fromstring(xml_bytes, parser=parser)
    for r in root.iter("ROW"):
        row = {child.tag.lower(): _strip(child.text) for child in r}
        rows.append({
            "registration_number": row.get("registration_number"),
            "registrant_name": row.get("registrant_name"),
            "foreign_principal_name": row.get("foreign_principal"),
            "foreign_principal_address": row.get("address_1"),
            "foreign_principal_city": row.get("city"),
            "foreign_principal_state": row.get("state"),
            "foreign_principal_country": row.get("country_location_represented"),
            "fp_registration_date": row.get("fp_registration_date"),
            "registrant_registration_date": row.get("registration_date"),
        })
    return rows


def load_into_duckdb(con, registrants: list[dict], principals: list[dict]) -> None:
    con.execute("""
        CREATE TABLE IF NOT EXISTS fara_registrants (
            registration_number VARCHAR,
            registrant_name VARCHAR,
            address_1 VARCHAR,
            address_2 VARCHAR,
            city VARCHAR,
            state VARCHAR,
            zip VARCHAR,
            registration_date VARCHAR,
            termination_date VARCHAR,
            registration_type VARCHAR
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS fara_foreign_principals (
            registration_number VARCHAR,
            registrant_name VARCHAR,
            foreign_principal_name VARCHAR,
            foreign_principal_address VARCHAR,
            foreign_principal_city VARCHAR,
            foreign_principal_state VARCHAR,
            foreign_principal_country VARCHAR,
            fp_registration_date VARCHAR,
            registrant_registration_date VARCHAR
        )
    """)
    con.execute("DELETE FROM fara_registrants")
    con.execute("DELETE FROM fara_foreign_principals")

    if registrants:
        cols = list(registrants[0].keys())
        placeholder = ", ".join(["?"] * len(cols))
        sql = f"INSERT INTO fara_registrants ({', '.join(cols)}) VALUES ({placeholder})"
        con.executemany(sql, [tuple(r.get(c) for c in cols) for r in registrants])
    if principals:
        cols = list(principals[0].keys())
        placeholder = ", ".join(["?"] * len(cols))
        sql = f"INSERT INTO fara_foreign_principals ({', '.join(cols)}) VALUES ({placeholder})"
        con.executemany(sql, [tuple(r.get(c) for c in cols) for r in principals])

    con.execute("CREATE INDEX IF NOT EXISTS idx_fara_reg_name ON fara_registrants(registrant_name)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_fara_fp_name ON fara_foreign_principals(foreign_principal_name)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_fara_fp_country ON fara_foreign_principals(foreign_principal_country)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_fara_fp_regname ON fara_foreign_principals(registrant_name)")


def main():
    ap = argparse.ArgumentParser(description="data-detective :: FARA puller")
    ap.add_argument("--db", required=True, type=Path)
    ap.add_argument("--cache", type=Path, default=Path("./fara-cache"),
                    help="directory to cache downloaded XML")
    ap.add_argument("--offline", action="store_true",
                    help="use cached files only; fail if missing")
    args = ap.parse_args()

    print(f"FARA puller :: {datetime.utcnow().isoformat()}Z")
    if args.offline and not args.cache.exists():
        sys.exit(f"--offline set but no cache at {args.cache}")

    if not args.offline:
        registrants_path = download(REGISTRANTS_URL, args.cache)
        principals_path = download(FOREIGN_PRINCIPALS_URL, args.cache)
    else:
        registrants_path = args.cache / "FARA_All_Registrants.xml"
        principals_path = args.cache / "FARA_All_ForeignPrincipals.xml"
        for p in (registrants_path, principals_path):
            if not p.exists():
                sys.exit(f"missing cached file: {p}")

    print("\nparsing XML...")
    registrants = parse_registrants(open_maybe_zip(registrants_path))
    principals = parse_foreign_principals(open_maybe_zip(principals_path))
    print(f"  registrants:         {len(registrants):,}")
    print(f"  foreign_principals:  {len(principals):,}")

    print("\nloading into DuckDB...")
    con = duckdb.connect(str(args.db))
    load_into_duckdb(con, registrants, principals)
    n_r = con.execute("SELECT count(*) FROM fara_registrants").fetchone()[0]
    n_p = con.execute("SELECT count(*) FROM fara_foreign_principals").fetchone()[0]
    print(f"  fara_registrants:           {n_r:,}")
    print(f"  fara_foreign_principals:    {n_p:,}")

    # Snapshot summary by country (helps later FARA-vs-LDA joins)
    countries = con.execute("""
        SELECT foreign_principal_country, count(*) AS n
        FROM fara_foreign_principals
        WHERE foreign_principal_country IS NOT NULL
        GROUP BY 1
        ORDER BY n DESC
        LIMIT 15
    """).fetchall()
    print("\nTop 15 FP countries in FARA:")
    for c, n in countries:
        print(f"  {n:>5}  {c}")


if __name__ == "__main__":
    main()
