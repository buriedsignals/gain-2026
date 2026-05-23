#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "duckdb>=1.1",
# ]
# ///
"""
data-detective :: evidence_card

Given a source record identifier (filing_uuid, house_xml_filename, or press_id),
emit a one-page markdown evidence card. Cards are the audit surface: each card
is one source record, with the exact fields cited in a claim and a link back
to the canonical public document.

Two paths:

  # Single source by id
  uv run evidence_card.py --db <db> --source senate_filing --id <filing_uuid> --out <dir>
  uv run evidence_card.py --db <db> --source house_filing  --id <filename.xml> --out <dir>
  uv run evidence_card.py --db <db> --source press_release --id <press_id>    --out <dir>

  # Bulk from a CSV (e.g. query.py output)
  uv run evidence_card.py --db <db> --source senate_filing --from-csv <csv> --id-column filing_uuid

Cards land in <out>/<source>_<id>.md. The claim-card index lives at
<out>/index.json and links claims to the cards that support them.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

import duckdb


# ---------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------

SENATE_PUBLIC_FILING_URL = "https://lda.senate.gov/filings/public/filing/{uuid}/print/"
HOUSE_PUBLIC_BASE = "https://disclosurespreview.house.gov/"


def card_senate_filing(con, fuuid: str) -> dict[str, Any]:
    rec = con.execute(
        "SELECT * FROM senate_filings WHERE filing_uuid = ?", [fuuid]
    ).fetchone()
    if not rec:
        return {"error": f"no senate filing found for filing_uuid={fuuid}"}
    cols = [c[0] for c in con.description]
    row = dict(zip(cols, rec))

    activities = con.execute(
        """SELECT activity_index, general_issue_code, general_issue_code_display, description
           FROM senate_lobbying_activities
           WHERE filing_uuid = ?
           ORDER BY activity_index""",
        [fuuid],
    ).fetchall()
    act_cols = [c[0] for c in con.description]

    lobbyists = con.execute(
        """SELECT first_name, last_name, covered_position
           FROM senate_activity_lobbyists
           WHERE filing_uuid = ?""",
        [fuuid],
    ).fetchall()
    lob_cols = [c[0] for c in con.description]

    foreigns = con.execute(
        """SELECT foreign_entity_name, country, ppb_country, ownership_percentage, contribution
           FROM senate_foreign_entities
           WHERE filing_uuid = ?""",
        [fuuid],
    ).fetchall()
    fe_cols = [c[0] for c in con.description]

    govt_entities = con.execute(
        """SELECT DISTINCT govt_entity_name
           FROM senate_activity_govt_entities
           WHERE filing_uuid = ?""",
        [fuuid],
    ).fetchall()

    return {
        "source": "senate_filing",
        "id": fuuid,
        "filing": row,
        "activities": [dict(zip(act_cols, a)) for a in activities],
        "lobbyists": [dict(zip(lob_cols, l)) for l in lobbyists],
        "foreign_entities": [dict(zip(fe_cols, fe)) for fe in foreigns],
        "government_entities_lobbied": [g[0] for g in govt_entities if g[0]],
        "public_url": SENATE_PUBLIC_FILING_URL.format(uuid=fuuid),
    }


def card_house_filing(con, fname: str) -> dict[str, Any]:
    rec = con.execute(
        "SELECT * FROM house_filings WHERE house_xml_filename = ?", [fname]
    ).fetchone()
    if not rec:
        return {"error": f"no house filing found for filename={fname}"}
    cols = [c[0] for c in con.description]
    row = dict(zip(cols, rec))

    activities = con.execute(
        """SELECT activity_index, issue_area_code, specific_issues, federal_agencies
           FROM house_lobbying_activities
           WHERE house_xml_filename = ?
           ORDER BY activity_index""",
        [fname],
    ).fetchall()
    act_cols = [c[0] for c in con.description]

    lobbyists = con.execute(
        """SELECT first_name, last_name, covered_position
           FROM house_activity_lobbyists
           WHERE house_xml_filename = ?""",
        [fname],
    ).fetchall()
    lob_cols = [c[0] for c in con.description]

    foreigns = con.execute(
        """SELECT foreign_entity_name, country, contribution, ownership_percentage
           FROM house_foreign_entities
           WHERE house_xml_filename = ?""",
        [fname],
    ).fetchall()
    fe_cols = [c[0] for c in con.description]

    return {
        "source": "house_filing",
        "id": fname,
        "filing": row,
        "activities": [dict(zip(act_cols, a)) for a in activities],
        "lobbyists": [dict(zip(lob_cols, l)) for l in lobbyists],
        "foreign_entities": [dict(zip(fe_cols, fe)) for fe in foreigns],
        "public_url": HOUSE_PUBLIC_BASE,
    }


def card_press_release(con, press_id: str) -> dict[str, Any]:
    rec = con.execute(
        "SELECT * FROM press_releases WHERE press_id = ?", [press_id]
    ).fetchone()
    if not rec:
        return {"error": f"no press release found for press_id={press_id}"}
    cols = [c[0] for c in con.description]
    row = dict(zip(cols, rec))
    return {"source": "press_release", "id": press_id, "release": row, "public_url": row.get("url")}


# ---------------------------------------------------------------------------
# Markdown rendering
# ---------------------------------------------------------------------------

def render_senate_filing(data: dict) -> str:
    f = data["filing"]
    lines = [
        f"# Evidence card :: Senate LDA filing `{f['filing_uuid']}`",
        "",
        f"- **Source kind:** senate_filing",
        f"- **Filing UUID:** `{f['filing_uuid']}`",
        f"- **Public document:** {data['public_url']}",
        f"- **API record:** {f.get('url')}",
        f"- **Filing type / period:** {f.get('filing_type_display')} ({f.get('filing_year')} {f.get('filing_period')})",
        f"- **Posted:** {f.get('dt_posted')}",
        "",
        "## Registrant",
        f"- {f.get('registrant_name')} (id {f.get('registrant_id')})",
        f"- State: {f.get('registrant_state')}; country: {f.get('registrant_country')}; PPB country: {f.get('registrant_ppb_country')}",
        f"- House registrant id (bridge): {f.get('registrant_house_id')}",
        "",
        "## Client",
        f"- {f.get('client_name')} (id {f.get('client_id')})",
        f"- State: {f.get('client_state')}; country: {f.get('client_country')}; PPB country: {f.get('client_ppb_country')}",
        f"- Description: {f.get('client_general_description')}",
        "",
        "## Financials",
        f"- Income reported: {f.get('income')}",
        f"- Expenses reported: {f.get('expenses')} ({f.get('expenses_method') or 'no method'})",
        "",
        "## Lobbying activities",
    ]
    for a in data["activities"]:
        lines.append(f"- **{a.get('general_issue_code')}** ({a.get('general_issue_code_display')}) — {a.get('description') or '_no description_'}")

    if data["lobbyists"]:
        lines += ["", "## Lobbyists"]
        for l in data["lobbyists"]:
            cp = l.get("covered_position") or ""
            cp_note = f"  \n    _covered position:_ {cp}" if cp else ""
            lines.append(f"- {l.get('first_name')} {l.get('last_name')}{cp_note}")

    if data["foreign_entities"]:
        lines += ["", "## Foreign entities"]
        for fe in data["foreign_entities"]:
            lines.append(f"- {fe.get('foreign_entity_name')} — country: {fe.get('country')}, ppb: {fe.get('ppb_country')}, ownership: {fe.get('ownership_percentage')}, contribution: {fe.get('contribution')}")

    if data["government_entities_lobbied"]:
        lines += ["", "## Government entities lobbied"]
        for g in data["government_entities_lobbied"]:
            lines.append(f"- {g}")

    return "\n".join(lines) + "\n"


def render_house_filing(data: dict) -> str:
    f = data["filing"]
    lines = [
        f"# Evidence card :: House LDA filing `{f['house_xml_filename']}`",
        "",
        f"- **Source kind:** house_filing",
        f"- **Filename:** `{f['house_xml_filename']}`",
        f"- **Doc type:** {f.get('doc_type')} ({f.get('report_year')} {f.get('report_type')})",
        f"- **Senate ID (bridge):** {f.get('senate_id')} (parses to Senate registrant id: {f.get('senate_id_registrant')})",
        f"- **House ID:** {f.get('house_id')}",
        f"- **Public lookup:** {data['public_url']}",
        f"- **Signed:** {f.get('signed_date')} by {f.get('printed_name')}",
        "",
        "## Registrant",
        f"- {f.get('organization_name')}",
        f"- Address: {f.get('address_1')}, {f.get('city')}, {f.get('state')} {f.get('zip')} {f.get('country')}",
        "",
        "## Client",
        f"- {f.get('client_name')} (client_govt_entity={f.get('client_govt_entity')}, self_select={f.get('self_select')})",
        "",
        "## Financials",
        f"- Income: {f.get('income')}",
        f"- Expenses: {f.get('expenses')} ({f.get('expenses_method')})",
        f"- No lobbying flag: {f.get('no_lobbying')}",
        "",
        "## Activities (ALIs)",
    ]
    for a in data["activities"]:
        si = (a.get("specific_issues") or "").replace("\n", "  \n    ")
        lines.append(f"- **{a.get('issue_area_code')}**")
        if si:
            lines.append(f"  - Specific issues: {si}")
        if a.get("federal_agencies"):
            lines.append(f"  - Federal agencies: {a.get('federal_agencies')}")

    if data["lobbyists"]:
        lines += ["", "## Lobbyists"]
        for l in data["lobbyists"]:
            cp = l.get("covered_position") or ""
            cp_note = f"  \n    _covered position:_ {cp}" if cp else ""
            lines.append(f"- {l.get('first_name')} {l.get('last_name')}{cp_note}")

    if data["foreign_entities"]:
        lines += ["", "## Foreign entities"]
        for fe in data["foreign_entities"]:
            lines.append(f"- {fe.get('foreign_entity_name')} — country: {fe.get('country')}, ownership: {fe.get('ownership_percentage')}, contribution: {fe.get('contribution')}")

    return "\n".join(lines) + "\n"


def render_press_release(data: dict) -> str:
    r = data["release"]
    lines = [
        f"# Evidence card :: press release `{r['press_id']}`",
        "",
        f"- **Source kind:** press_release",
        f"- **Member:** {r.get('member_name')} ({r.get('member_party')}-{r.get('member_state')}, {r.get('member_chamber')}, bioguide `{r.get('bioguide_id')}`)",
        f"- **Title:** {r.get('title')}",
        f"- **Date:** {r.get('date')} ({r.get('date_source')})",
        f"- **URL:** {r.get('url')}",
        f"- **Collected at:** {r.get('collected_at')}",
        "",
        "## Body",
        "",
        "```",
        (r.get("text") or "")[:5000],
        "```",
    ]
    if r.get("text") and len(r["text"]) > 5000:
        lines.append(f"\n_(truncated; full text {r['text_length']} chars)_")
    return "\n".join(lines) + "\n"


RENDERERS = {
    "senate_filing": render_senate_filing,
    "house_filing": render_house_filing,
    "press_release": render_press_release,
}

CARD_FACTORIES = {
    "senate_filing": card_senate_filing,
    "house_filing": card_house_filing,
    "press_release": card_press_release,
}


def write_card(con, source: str, ident: str, out_dir: Path) -> Path | None:
    data = CARD_FACTORIES[source](con, ident)
    if "error" in data:
        print(f"  skip {source}/{ident}: {data['error']}", file=sys.stderr)
        return None
    md = RENDERERS[source](data)
    safe_id = ident.replace("/", "_")
    out_path = out_dir / f"{source}_{safe_id}.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(md)
    return out_path


def main():
    ap = argparse.ArgumentParser(description="data-detective :: evidence card emitter")
    ap.add_argument("--db", required=True, type=Path)
    ap.add_argument("--source", required=True, choices=sorted(CARD_FACTORIES.keys()))
    ap.add_argument("--out", type=Path, default=Path("./evidence-cards"))
    ap.add_argument("--id", help="single source id")
    ap.add_argument("--from-csv", type=Path, help="bulk ingest a CSV of ids")
    ap.add_argument("--id-column", default=None,
                    help="column name in CSV that holds the id (default: first column)")
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    con = duckdb.connect(str(args.db), read_only=True)

    written = []
    if args.id:
        p = write_card(con, args.source, args.id, args.out)
        if p:
            written.append(p)
    elif args.from_csv:
        with args.from_csv.open() as f:
            reader = csv.DictReader(f)
            col = args.id_column or reader.fieldnames[0]
            for i, row in enumerate(reader):
                if args.limit and i >= args.limit:
                    break
                ident = row.get(col)
                if not ident:
                    continue
                p = write_card(con, args.source, ident, args.out)
                if p:
                    written.append(p)
    else:
        ap.print_help()
        return

    print(f"\nwrote {len(written)} card(s) to {args.out}")
    for p in written[:5]:
        print(f"  {p}")
    if len(written) > 5:
        print(f"  ... +{len(written)-5} more")


if __name__ == "__main__":
    main()
