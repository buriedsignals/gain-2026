#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "duckdb>=1.1",
#     "httpx>=0.28",
#     "pyyaml>=6.0",
# ]
# ///
"""
data-detective :: external/congress_gov

Pulls current congressional members + committee assignments into the DuckDB
index so the rest of the skill can join lobbying activity to committee
jurisdiction and member offices.

Source: the open `unitedstates/congress-legislators` dataset
(https://theunitedstates.io/congress-legislators/) — daily-updated YAML/JSON
maintained collaboratively by ProPublica, GovTrack, Sunlight Foundation
descendents, and academic groups. No API key required.

Three tables emitted (idempotent — DELETE+INSERT on each run):

  congress_members            (bioguide_id, name, chamber, party, state, district)
  congress_committees         (committee_code, chamber, name, parent_committee_code)
  congress_committee_assignments (bioguide_id, committee_code, committee_name, role)

These join naturally to:
  press_releases.bioguide_id        -> congress_members
  congress_members                  -> congress_committee_assignments
                                    -> committee_code -> congress_committees

Once loaded, you can resolve "former Senate Finance Committee staff" to
specific bioguide IDs of *current* members of that committee, deepening
D11's revolving-door analysis with deterministic jurisdiction mapping.

Usage:
  uv run external/congress_gov.py --db case/index.duckdb
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import duckdb
import httpx
import yaml


SOURCE_BASE = "https://raw.githubusercontent.com/unitedstates/congress-legislators/main"
LEGISLATORS_URL = f"{SOURCE_BASE}/legislators-current.yaml"
COMMITTEES_URL = f"{SOURCE_BASE}/committees-current.yaml"
MEMBERSHIP_URL = f"{SOURCE_BASE}/committee-membership-current.yaml"


def _client() -> httpx.Client:
    return httpx.Client(timeout=60, follow_redirects=True,
                        headers={"User-Agent": "data-detective/1.0"})


def fetch_legislators(client) -> list[dict]:
    r = client.get(LEGISLATORS_URL); r.raise_for_status()
    return yaml.safe_load(r.text)


def fetch_committees_yaml(client) -> list[dict]:
    r = client.get(COMMITTEES_URL); r.raise_for_status()
    return yaml.safe_load(r.text)


def fetch_membership_yaml(client) -> dict:
    r = client.get(MEMBERSHIP_URL); r.raise_for_status()
    return yaml.safe_load(r.text)


def parse_member(m: dict) -> dict:
    """Flatten a unitedstates legislators-current.json entry."""
    bid = m.get("id", {}).get("bioguide")
    name = m.get("name", {})
    full_name = name.get("official_full") or f"{name.get('first','')} {name.get('last','')}".strip()
    # latest term
    terms = m.get("terms", [])
    latest = terms[-1] if terms else {}
    return {
        "bioguide_id": bid,
        "name": full_name,
        "chamber": latest.get("type"),  # "sen" or "rep"
        "state": latest.get("state"),
        "district": str(latest.get("district")) if latest.get("district") is not None else None,
        "party": latest.get("party"),
        "url": latest.get("url"),
    }


def parse_committees(committees: list[dict]) -> list[dict]:
    """Flatten committees-current.json to (committee_code, name, chamber)."""
    rows = []
    for c in committees:
        code = c.get("thomas_id")  # e.g. "HSAS" (House Armed Services)
        rows.append({
            "committee_code": code,
            "name": c.get("name"),
            "chamber": c.get("type"),
            "parent_committee_code": None,
        })
        # Subcommittees
        for s in c.get("subcommittees", []) or []:
            sub_code = code + (s.get("thomas_id") or "")
            rows.append({
                "committee_code": sub_code,
                "name": s.get("name"),
                "chamber": c.get("type"),
                "parent_committee_code": code,
            })
    return rows


def parse_membership(membership: dict, committees: list[dict]) -> list[dict]:
    """
    membership maps thomas_id -> [list of {bioguide, party, title, ...}].
    """
    # Build name lookup for committees
    name_by_code = {c["committee_code"]: c["name"] for c in committees}
    rows = []
    for committee_code, members in membership.items():
        for m in members:
            bid = m.get("bioguide")
            if not bid:
                continue
            rows.append({
                "bioguide_id": bid,
                "committee_code": committee_code,
                "committee_name": name_by_code.get(committee_code) or committee_code,
                "role": m.get("title") or m.get("party") or None,
            })
    return rows


def insert_table(con, table: str, schema: list[tuple[str, str]], rows: list[dict]) -> None:
    cols_sql = ", ".join(f'"{c}" {t}' for c, t in schema)
    con.execute(f'CREATE TABLE IF NOT EXISTS "{table}" ({cols_sql})')
    con.execute(f'DELETE FROM "{table}"')
    if not rows:
        print(f"  {table}: 0 rows (no data)")
        return
    col_list = ", ".join(f'"{c}"' for c, _ in schema)
    placeholder = ", ".join(["?"] * len(schema))
    sql = f'INSERT INTO "{table}" ({col_list}) VALUES ({placeholder})'
    con.executemany(sql, [tuple(r.get(c) for c, _ in schema) for r in rows])
    print(f"  {table}: {len(rows):,} rows")


def main():
    ap = argparse.ArgumentParser(description="data-detective :: Congress.gov puller (via theunitedstates.io)")
    ap.add_argument("--db", required=True, type=Path)
    args = ap.parse_args()

    print(f"Congress.gov puller :: source = theunitedstates.io (current Congress)")
    client = _client()

    print("\nfetching legislators-current.json ...")
    legislators_raw = fetch_legislators(client)
    members = [parse_member(m) for m in legislators_raw if m.get("id", {}).get("bioguide")]
    print(f"  parsed {len(members):,} members")

    print("\nfetching committees-current.json ...")
    committees_raw = fetch_committees_yaml(client)
    committees = parse_committees(committees_raw)
    print(f"  parsed {len(committees):,} committees + subcommittees")

    print("\nfetching committee-membership-current.json ...")
    membership_raw = fetch_membership_yaml(client)
    assignments = parse_membership(membership_raw, committees)
    print(f"  parsed {len(assignments):,} committee assignment rows")

    print("\nloading into DuckDB...")
    con = duckdb.connect(str(args.db))
    insert_table(con, "congress_members", [
        ("bioguide_id","VARCHAR PRIMARY KEY"), ("name","VARCHAR"), ("chamber","VARCHAR"),
        ("state","VARCHAR"), ("district","VARCHAR"), ("party","VARCHAR"), ("url","VARCHAR"),
    ], members)
    insert_table(con, "congress_committees", [
        ("committee_code","VARCHAR PRIMARY KEY"), ("name","VARCHAR"),
        ("chamber","VARCHAR"), ("parent_committee_code","VARCHAR"),
    ], committees)
    insert_table(con, "congress_committee_assignments", [
        ("bioguide_id","VARCHAR"), ("committee_code","VARCHAR"),
        ("committee_name","VARCHAR"), ("role","VARCHAR"),
    ], assignments)
    con.execute("CREATE INDEX IF NOT EXISTS idx_assignments_bioguide ON congress_committee_assignments(bioguide_id)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_assignments_committee ON congress_committee_assignments(committee_code)")

    # Optional bill puller — disabled with theunitedstates.io source
    if False:
        bills_to_pull = []
        if args.bills_from_extracted_mentions and args.bills_from_extracted_mentions.exists():
            import csv as _csv
            with args.bills_from_extracted_mentions.open() as f:
                r = _csv.DictReader(f)
                for row in r:
                    bill = row.get("bill","")
                    # parse "H.R5376" / "S2587" -> ('HR', 5376) or ('S', 2587)
                    import re
                    m = re.match(r"^(H\.?R\.?|HR|S\.?J\.?RES\.?|H\.?J\.?RES\.?|S\.?)(\d{1,5})$", bill, re.I)
                    if not m: continue
                    typ = re.sub(r"\.","", m.group(1)).upper()
                    typ = {"HR":"hr","S":"s","HJRES":"hjres","SJRES":"sjres"}.get(typ, typ.lower())
                    bills_to_pull.append((args.congress, typ, m.group(2)))
                    if len(bills_to_pull) >= 100:  # cap for safety
                        break
        else:
            print("  no --bills-from-extracted-mentions specified; skipping bill pull")
            bills_to_pull = []
        if bills_to_pull:
            print(f"\nfetching {len(bills_to_pull)} bills with committee referrals...")
            bill_rows = []
            referral_rows = []
            for cg, bt, bn in bills_to_pull:
                try:
                    r = client.get(f"{BASE}/bill/{cg}/{bt}/{bn}", params={"format":"json"})
                    if r.status_code != 200: continue
                    bill = r.json().get("bill", {})
                    bill_rows.append({
                        "bill_id": f"{bt}{bn}-{cg}",
                        "congress": cg,
                        "bill_type": bt,
                        "bill_number": bn,
                        "title": (bill.get("title") or "")[:500],
                        "introduced_date": bill.get("introducedDate"),
                        "sponsor_bioguide_id": (bill.get("sponsors") or [{}])[0].get("bioguideId") if bill.get("sponsors") else None,
                    })
                    for comm in (bill.get("committees", {}).get("count") and bill.get("committees", {}).get("item") or []):
                        referral_rows.append({
                            "bill_id": f"{bt}{bn}-{cg}",
                            "committee_code": comm.get("systemCode"),
                            "committee_name": comm.get("name"),
                            "chamber": comm.get("chamber"),
                        })
                except httpx.HTTPError:
                    continue
                time.sleep(0.15)
            insert_table(con, "congress_bills", [
                ("bill_id","VARCHAR PRIMARY KEY"), ("congress","INTEGER"),
                ("bill_type","VARCHAR"), ("bill_number","VARCHAR"),
                ("title","VARCHAR"), ("introduced_date","VARCHAR"),
                ("sponsor_bioguide_id","VARCHAR"),
            ], bill_rows)
            insert_table(con, "congress_bill_committees", [
                ("bill_id","VARCHAR"), ("committee_code","VARCHAR"),
                ("committee_name","VARCHAR"), ("chamber","VARCHAR"),
            ], referral_rows)

    # Quick sanity
    print("\nsanity:")
    for q in [
        "SELECT count(*) AS n FROM congress_members WHERE bioguide_id IS NOT NULL",
        "SELECT count(DISTINCT committee_code) AS n FROM congress_committee_assignments",
        "SELECT count(*) AS n FROM congress_committees",
    ]:
        print(f"  {q}: {con.execute(q).fetchone()[0]}")

    print("\ndone.")


if __name__ == "__main__":
    main()
