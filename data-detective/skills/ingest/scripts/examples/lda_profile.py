"""
data-detective profile :: Lobbying Disclosure Act + Congressional Press corpus.

Worked example for the Northwestern GAIN Challenge corpus.

Corpus shape:
  senate/{year}/filings/filings_{year}.json        Senate LDA filings (JSON array)
  senate/{year}/contributions/contributions_{year}.json   Senate LDA contributions (JSON array)
  senate/constants/*.json                          Lookup tables (issue codes, gov entities, ...)
  house/{period}_XML/*.xml                         House LDA filings (LD-1 and LD-2)
  congress_press/{year}/{year}-{month}.jsonl       Congressional press releases (JSONL)
  congress_press/{year}-{month}.jsonl              2026 Q1 press releases (top level)

Bridge keys this profile preserves:
  senate.registrant.id <-> first segment of house.senateID
  senate.registrant.house_registrant_id <-> (potential) house registrant id
  press.member.bioguide_id <-> Congress member identifier
  filing_uuid is the Senate primary key.
  house_xml_filename (the file name itself, e.g. "301639546.xml") is the House primary key.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

NAME = "Lobbying Disclosure Act + Congressional Press"
DESCRIPTION = "Senate LDA filings & contributions (JSON), House LDA filings (XML), Congressional press releases (JSONL)."


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_float(v: Any) -> float | None:
    if v in (None, "", " "):
        return None
    try:
        return float(str(v).strip().replace("$", "").replace(",", ""))
    except (ValueError, TypeError):
        return None


def _to_int(v: Any) -> int | None:
    if v in (None, "", " "):
        return None
    try:
        return int(str(v).strip())
    except (ValueError, TypeError):
        return None


def _strip(s: Any) -> str | None:
    if s is None:
        return None
    s = str(s).strip()
    return s if s else None


def _xml_text(elem, path: str, default: Any = None) -> str | None:
    """Strip-aware findtext."""
    if elem is None:
        return default
    val = elem.findtext(path)
    if val is None:
        return default
    val = val.strip()
    return val if val else default


def _parse_senate_id_first(senate_id: str | None) -> int | None:
    """The Senate registrant.id is the first segment of the senateID string."""
    if not senate_id:
        return None
    m = re.match(r"^(\d+)", senate_id)
    return int(m.group(1)) if m else None


# ---------------------------------------------------------------------------
# Schemas (explicit -> consistent types across loads)
# ---------------------------------------------------------------------------

TABLES = {
    # Senate side
    "senate_filings": {
        "columns": {
            "filing_uuid": "VARCHAR PRIMARY KEY",
            "filing_type": "VARCHAR",
            "filing_type_display": "VARCHAR",
            "filing_year": "INTEGER",
            "filing_period": "VARCHAR",
            "filing_document_url": "VARCHAR",
            "url": "VARCHAR",
            "income": "DOUBLE",
            "expenses": "DOUBLE",
            "expenses_method": "VARCHAR",
            "dt_posted": "VARCHAR",
            "termination_date": "VARCHAR",
            "registrant_id": "INTEGER",
            "registrant_name": "VARCHAR",
            "registrant_state": "VARCHAR",
            "registrant_country": "VARCHAR",
            "registrant_ppb_country": "VARCHAR",
            "registrant_house_id": "INTEGER",
            "registrant_description": "VARCHAR",
            "client_id": "INTEGER",
            "client_name": "VARCHAR",
            "client_state": "VARCHAR",
            "client_country": "VARCHAR",
            "client_ppb_country": "VARCHAR",
            "client_general_description": "VARCHAR",
            "client_self_select": "BOOLEAN",
            "posted_by_name": "VARCHAR",
            "source_file": "VARCHAR",
        }
    },
    "senate_lobbying_activities": {
        "columns": {
            "activity_id": "VARCHAR PRIMARY KEY",
            "filing_uuid": "VARCHAR",
            "activity_index": "INTEGER",
            "general_issue_code": "VARCHAR",
            "general_issue_code_display": "VARCHAR",
            "description": "VARCHAR",
        }
    },
    "senate_activity_lobbyists": {
        "columns": {
            "activity_id": "VARCHAR",
            "filing_uuid": "VARCHAR",
            "lobbyist_id": "INTEGER",
            "first_name": "VARCHAR",
            "last_name": "VARCHAR",
            "middle_name": "VARCHAR",
            "suffix": "VARCHAR",
            "covered_position": "VARCHAR",
            "new_lobbyist": "BOOLEAN",
        }
    },
    "senate_activity_govt_entities": {
        "columns": {
            "activity_id": "VARCHAR",
            "filing_uuid": "VARCHAR",
            "govt_entity_id": "INTEGER",
            "govt_entity_name": "VARCHAR",
        }
    },
    "senate_foreign_entities": {
        "columns": {
            "filing_uuid": "VARCHAR",
            "foreign_entity_name": "VARCHAR",
            "country": "VARCHAR",
            "ppb_country": "VARCHAR",
            "ownership_percentage": "DOUBLE",
            "contribution": "DOUBLE",
            "city": "VARCHAR",
            "state": "VARCHAR",
        }
    },
    # Senate contributions
    "senate_contributions": {
        "columns": {
            "filing_uuid": "VARCHAR PRIMARY KEY",
            "filing_type": "VARCHAR",
            "filing_period": "VARCHAR",
            "filing_year": "INTEGER",
            "filer_type": "VARCHAR",
            "dt_posted": "VARCHAR",
            "registrant_id": "INTEGER",
            "registrant_name": "VARCHAR",
            "lobbyist_id": "INTEGER",
            "lobbyist_first_name": "VARCHAR",
            "lobbyist_last_name": "VARCHAR",
            "no_contributions": "BOOLEAN",
            "url": "VARCHAR",
            "source_file": "VARCHAR",
        }
    },
    "senate_contribution_items": {
        "columns": {
            "item_id": "VARCHAR PRIMARY KEY",
            "filing_uuid": "VARCHAR",
            "item_index": "INTEGER",
            "contribution_type": "VARCHAR",
            "amount": "DOUBLE",
            "contributor_name": "VARCHAR",
            "payee_name": "VARCHAR",
            "honoree_name": "VARCHAR",
            "contribution_date": "VARCHAR",
        }
    },
    "senate_contribution_pacs": {
        "columns": {
            "filing_uuid": "VARCHAR",
            "pac_name": "VARCHAR",
        }
    },
    # House side
    "house_filings": {
        "columns": {
            "house_xml_filename": "VARCHAR PRIMARY KEY",
            "doc_type": "VARCHAR",
            "report_year": "INTEGER",
            "report_type": "VARCHAR",
            "organization_name": "VARCHAR",
            "client_name": "VARCHAR",
            "senate_id": "VARCHAR",
            "senate_id_registrant": "INTEGER",
            "house_id": "VARCHAR",
            "income": "DOUBLE",
            "expenses": "DOUBLE",
            "expenses_method": "VARCHAR",
            "signed_date": "VARCHAR",
            "printed_name": "VARCHAR",
            "address_1": "VARCHAR",
            "address_2": "VARCHAR",
            "city": "VARCHAR",
            "state": "VARCHAR",
            "zip": "VARCHAR",
            "country": "VARCHAR",
            "termination_date": "VARCHAR",
            "no_lobbying": "VARCHAR",
            "self_select": "VARCHAR",
            "client_govt_entity": "VARCHAR",
            "source_file": "VARCHAR",
        }
    },
    "house_lobbying_activities": {
        "columns": {
            "activity_id": "VARCHAR PRIMARY KEY",
            "house_xml_filename": "VARCHAR",
            "activity_index": "INTEGER",
            "issue_area_code": "VARCHAR",
            "specific_issues": "VARCHAR",
            "federal_agencies": "VARCHAR",
        }
    },
    "house_activity_lobbyists": {
        "columns": {
            "activity_id": "VARCHAR",
            "house_xml_filename": "VARCHAR",
            "first_name": "VARCHAR",
            "middle_name": "VARCHAR",
            "last_name": "VARCHAR",
            "suffix": "VARCHAR",
            "covered_position": "VARCHAR",
            "lobbyist_new": "VARCHAR",
        }
    },
    "house_foreign_entities": {
        "columns": {
            "house_xml_filename": "VARCHAR",
            "foreign_entity_name": "VARCHAR",
            "country": "VARCHAR",
            "contribution": "DOUBLE",
            "ownership_percentage": "DOUBLE",
            "address": "VARCHAR",
        }
    },
    # Press
    "press_releases": {
        "columns": {
            "press_id": "VARCHAR PRIMARY KEY",
            "url": "VARCHAR",
            "title": "VARCHAR",
            "date": "VARCHAR",
            "date_source": "VARCHAR",
            "source_index_page": "VARCHAR",
            "domain": "VARCHAR",
            "scraper": "VARCHAR",
            "bioguide_id": "VARCHAR",
            "member_name": "VARCHAR",
            "member_party": "VARCHAR",
            "member_state": "VARCHAR",
            "member_chamber": "VARCHAR",
            "text": "VARCHAR",
            "text_length": "INTEGER",
            "collected_at": "VARCHAR",
            "updated_at": "VARCHAR",
            "source_file": "VARCHAR",
        }
    },
    "members": {
        "columns": {
            "bioguide_id": "VARCHAR PRIMARY KEY",
            "name": "VARCHAR",
            "party": "VARCHAR",
            "state": "VARCHAR",
            "chamber": "VARCHAR",
        }
    },
    # Constants
    "issue_codes": {
        "columns": {
            "code": "VARCHAR PRIMARY KEY",
            "name": "VARCHAR",
        }
    },
    "government_entities_lookup": {
        "columns": {
            "entity_id": "VARCHAR PRIMARY KEY",
            "name": "VARCHAR",
        }
    },
}


# ---------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------

SOURCES = [
    {
        "id": "senate_constants",
        "format": "json_array",
        "glob": "senate/constants/lobbying_activity_issues.json",
        "mapper": "map_issue_codes",
        "batch": 1000,
    },
    {
        "id": "senate_govt_entities_lookup",
        "format": "json_array",
        "glob": "senate/constants/government_entities.json",
        "mapper": "map_govt_entities_lookup",
        "batch": 1000,
    },
    {
        "id": "senate_filings",
        "format": "json_array",
        "glob": "senate/{year}/filings/filings_{year}.json",
        "mapper": "map_senate_filing",
        "batch": 5000,
    },
    {
        "id": "senate_contributions",
        "format": "json_array",
        "glob": "senate/{year}/contributions/contributions_{year}.json",
        "mapper": "map_senate_contribution",
        "batch": 5000,
    },
    {
        "id": "house_filings",
        "format": "xml_dir",
        "glob": "house/{year}_*_XML",
        "mapper": "map_house_xml",
        "batch": 5000,
    },
    {
        "id": "press_releases_yeared",
        "format": "jsonl",
        "glob": "congress_press/{year}/*.jsonl",
        "mapper": "map_press_release",
        "batch": 5000,
    },
    {
        "id": "press_releases_2026",
        "format": "jsonl",
        "glob": "congress_press/2026-*.jsonl",
        "mapper": "map_press_release",
        "batch": 5000,
    },
]


INDEXES = [
    ("senate_filings", ["registrant_id"]),
    ("senate_filings", ["client_id"]),
    ("senate_filings", ["filing_year"]),
    ("senate_filings", ["client_country"]),
    ("senate_filings", ["client_ppb_country"]),
    ("senate_lobbying_activities", ["filing_uuid"]),
    ("senate_lobbying_activities", ["general_issue_code"]),
    ("senate_activity_lobbyists", ["filing_uuid"]),
    ("senate_activity_lobbyists", ["last_name"]),
    ("senate_activity_govt_entities", ["filing_uuid"]),
    ("senate_activity_govt_entities", ["govt_entity_id"]),
    ("senate_foreign_entities", ["filing_uuid"]),
    ("senate_foreign_entities", ["country"]),
    ("senate_contributions", ["registrant_id"]),
    ("senate_contributions", ["lobbyist_id"]),
    ("senate_contribution_items", ["filing_uuid"]),
    ("senate_contribution_items", ["payee_name"]),
    ("senate_contribution_items", ["honoree_name"]),
    ("house_filings", ["senate_id_registrant"]),
    ("house_filings", ["report_year"]),
    ("house_filings", ["organization_name"]),
    ("house_filings", ["client_name"]),
    ("house_lobbying_activities", ["house_xml_filename"]),
    ("house_lobbying_activities", ["issue_area_code"]),
    ("house_foreign_entities", ["country"]),
    ("press_releases", ["bioguide_id"]),
    ("press_releases", ["date"]),
    ("press_releases", ["domain"]),
]


# ---------------------------------------------------------------------------
# Mappers
# ---------------------------------------------------------------------------

def map_issue_codes(record: dict, source_file) -> dict[str, list[dict]]:
    return {"issue_codes": [{"code": record.get("value"), "name": record.get("name")}]}


def map_govt_entities_lookup(record: dict, source_file) -> dict[str, list[dict]]:
    eid = record.get("id") or record.get("value")
    return {
        "government_entities_lookup": [
            {"entity_id": str(eid) if eid is not None else None, "name": record.get("name")}
        ]
    }


def map_senate_filing(rec: dict, source_file) -> dict[str, list[dict]]:
    fuuid = rec.get("filing_uuid")
    if not fuuid:
        return {}
    registrant = rec.get("registrant") or {}
    client = rec.get("client") or {}

    filing_row = {
        "filing_uuid": fuuid,
        "filing_type": rec.get("filing_type"),
        "filing_type_display": rec.get("filing_type_display"),
        "filing_year": _to_int(rec.get("filing_year")),
        "filing_period": rec.get("filing_period"),
        "filing_document_url": rec.get("filing_document_url"),
        "url": rec.get("url"),
        "income": _to_float(rec.get("income")),
        "expenses": _to_float(rec.get("expenses")),
        "expenses_method": rec.get("expenses_method_display"),
        "dt_posted": rec.get("dt_posted"),
        "termination_date": rec.get("termination_date"),
        "registrant_id": _to_int(registrant.get("id")),
        "registrant_name": _strip(registrant.get("name")),
        "registrant_state": registrant.get("state"),
        "registrant_country": registrant.get("country"),
        "registrant_ppb_country": registrant.get("ppb_country"),
        "registrant_house_id": _to_int(registrant.get("house_registrant_id")),
        "registrant_description": registrant.get("description"),
        "client_id": _to_int(client.get("client_id") or client.get("id")),
        "client_name": _strip(client.get("name")),
        "client_state": client.get("state"),
        "client_country": client.get("country"),
        "client_ppb_country": client.get("ppb_country"),
        "client_general_description": client.get("general_description"),
        "client_self_select": bool(client.get("client_self_select")) if client.get("client_self_select") is not None else None,
        "posted_by_name": rec.get("posted_by_name"),
        "source_file": str(source_file.name),
    }

    activities = []
    activity_lobbyists = []
    activity_govt_entities = []

    for i, act in enumerate(rec.get("lobbying_activities") or []):
        aid = f"{fuuid}::a{i}"
        activities.append({
            "activity_id": aid,
            "filing_uuid": fuuid,
            "activity_index": i,
            "general_issue_code": act.get("general_issue_code"),
            "general_issue_code_display": act.get("general_issue_code_display"),
            "description": act.get("description"),
        })
        for lob in act.get("lobbyists") or []:
            l = lob.get("lobbyist") or lob  # API sometimes nests under "lobbyist"
            activity_lobbyists.append({
                "activity_id": aid,
                "filing_uuid": fuuid,
                "lobbyist_id": _to_int(l.get("id")),
                "first_name": _strip(l.get("first_name")),
                "last_name": _strip(l.get("last_name")),
                "middle_name": _strip(l.get("middle_name")),
                "suffix": _strip(l.get("suffix")),
                "covered_position": _strip(lob.get("covered_position") or l.get("covered_position")),
                "new_lobbyist": bool(lob.get("new")) if lob.get("new") is not None else None,
            })
        for ge in act.get("government_entities") or []:
            activity_govt_entities.append({
                "activity_id": aid,
                "filing_uuid": fuuid,
                "govt_entity_id": _to_int(ge.get("id")),
                "govt_entity_name": _strip(ge.get("name")),
            })

    foreign_entities = []
    for fe in rec.get("foreign_entities") or []:
        foreign_entities.append({
            "filing_uuid": fuuid,
            "foreign_entity_name": _strip(fe.get("name")),
            "country": fe.get("country"),
            "ppb_country": fe.get("ppb_country"),
            "ownership_percentage": _to_float(fe.get("ownership_percentage")),
            "contribution": _to_float(fe.get("contribution")),
            "city": _strip(fe.get("city")),
            "state": _strip(fe.get("state")),
        })

    out = {"senate_filings": [filing_row]}
    if activities:
        out["senate_lobbying_activities"] = activities
    if activity_lobbyists:
        out["senate_activity_lobbyists"] = activity_lobbyists
    if activity_govt_entities:
        out["senate_activity_govt_entities"] = activity_govt_entities
    if foreign_entities:
        out["senate_foreign_entities"] = foreign_entities
    return out


def map_senate_contribution(rec: dict, source_file) -> dict[str, list[dict]]:
    fuuid = rec.get("filing_uuid")
    if not fuuid:
        return {}
    registrant = rec.get("registrant") or {}
    lobbyist = rec.get("lobbyist") or {}

    row = {
        "filing_uuid": fuuid,
        "filing_type": rec.get("filing_type"),
        "filing_period": rec.get("filing_period"),
        "filing_year": _to_int(rec.get("filing_year")),
        "filer_type": rec.get("filer_type"),
        "dt_posted": rec.get("dt_posted"),
        "registrant_id": _to_int(registrant.get("id")),
        "registrant_name": _strip(registrant.get("name")),
        "lobbyist_id": _to_int(lobbyist.get("id")),
        "lobbyist_first_name": _strip(lobbyist.get("first_name")),
        "lobbyist_last_name": _strip(lobbyist.get("last_name")),
        "no_contributions": bool(rec.get("no_contributions")) if rec.get("no_contributions") is not None else None,
        "url": rec.get("url"),
        "source_file": str(source_file.name),
    }

    items = []
    for i, it in enumerate(rec.get("contribution_items") or []):
        items.append({
            "item_id": f"{fuuid}::ci{i}",
            "filing_uuid": fuuid,
            "item_index": i,
            "contribution_type": it.get("contribution_type") or it.get("type"),
            "amount": _to_float(it.get("amount")),
            "contributor_name": _strip(it.get("contributor_name")),
            "payee_name": _strip(it.get("payee_name") or it.get("payee")),
            "honoree_name": _strip(it.get("honoree_name") or it.get("honoree")),
            "contribution_date": it.get("contribution_date") or it.get("date"),
        })

    pacs = []
    for p in rec.get("pacs") or []:
        if isinstance(p, dict):
            pname = _strip(p.get("name"))
        else:
            pname = _strip(p)
        if pname:
            pacs.append({"filing_uuid": fuuid, "pac_name": pname})

    out = {"senate_contributions": [row]}
    if items:
        out["senate_contribution_items"] = items
    if pacs:
        out["senate_contribution_pacs"] = pacs
    return out


def map_house_xml(root, source_file: Path) -> dict[str, list[dict]]:
    fname = source_file.name
    tag = root.tag
    doc_type = "LD1" if tag == "LOBBYINGDISCLOSURE1" else "LD2"

    senate_id = _xml_text(root, "senateID")
    senate_id_reg = _parse_senate_id_first(senate_id)

    income = _xml_text(root, "income")
    expenses = _xml_text(root, "expenses")

    filing_row = {
        "house_xml_filename": fname,
        "doc_type": doc_type,
        "report_year": _to_int(_xml_text(root, "reportYear")),
        "report_type": _xml_text(root, "reportType") or _xml_text(root, "RegistrationDate"),
        "organization_name": _xml_text(root, "organizationName"),
        "client_name": _xml_text(root, "clientName"),
        "senate_id": senate_id,
        "senate_id_registrant": senate_id_reg,
        "house_id": _xml_text(root, "houseID"),
        "income": _to_float(income),
        "expenses": _to_float(expenses),
        "expenses_method": _xml_text(root, "expensesMethod"),
        "signed_date": _xml_text(root, "signedDate"),
        "printed_name": _xml_text(root, "printedName"),
        "address_1": _xml_text(root, "address1"),
        "address_2": _xml_text(root, "address2"),
        "city": _xml_text(root, "city"),
        "state": _xml_text(root, "state"),
        "zip": _xml_text(root, "zip"),
        "country": _xml_text(root, "country"),
        "termination_date": _xml_text(root, "terminationDate"),
        "no_lobbying": _xml_text(root, "noLobbying"),
        "self_select": _xml_text(root, "selfSelect"),
        "client_govt_entity": _xml_text(root, "clientGovtEntity"),
        "source_file": str(source_file.parent.name) + "/" + fname,
    }

    activities = []
    activity_lobbyists = []

    # ALIs (LD2)
    for i, ali in enumerate(root.findall(".//alis/ali_info")):
        aid = f"{fname}::a{i}"
        # specific_issues can have multiple description children
        descs = ali.findall(".//specific_issues/description")
        spec_text = "\n".join(d.text.strip() for d in descs if d.text and d.text.strip())
        activities.append({
            "activity_id": aid,
            "house_xml_filename": fname,
            "activity_index": i,
            "issue_area_code": _xml_text(ali, "issueAreaCode"),
            "specific_issues": spec_text or None,
            "federal_agencies": _xml_text(ali, "federal_agencies"),
        })
        for lob in ali.findall(".//lobbyists/lobbyist"):
            activity_lobbyists.append({
                "activity_id": aid,
                "house_xml_filename": fname,
                "first_name": _xml_text(lob, "lobbyistFirstName"),
                "middle_name": _xml_text(lob, "lobbyistMiddleName"),
                "last_name": _xml_text(lob, "lobbyistLastName"),
                "suffix": _xml_text(lob, "lobbyistSuffix"),
                "covered_position": _xml_text(lob, "coveredPosition"),
                "lobbyist_new": _xml_text(lob, "lobbyistNew"),
            })

    # LD1 may have alis_specific (registration-level issues) but no lobbyists/activities
    if not activities:
        for i, ali in enumerate(root.findall(".//alis_specific/ali_specific")):
            aid = f"{fname}::a{i}"
            activities.append({
                "activity_id": aid,
                "house_xml_filename": fname,
                "activity_index": i,
                "issue_area_code": _xml_text(ali, "issueAreaCode"),
                "specific_issues": _xml_text(ali, "specific_issue") or _xml_text(ali, "description"),
                "federal_agencies": None,
            })

    # Foreign entities (skip empty placeholders)
    foreign_entities = []
    for fe in root.findall(".//foreignEntities/foreignEntity"):
        name = _xml_text(fe, "name")
        country = _xml_text(fe, "country")
        if not name and not country:
            continue
        foreign_entities.append({
            "house_xml_filename": fname,
            "foreign_entity_name": name,
            "country": country,
            "contribution": _to_float(_xml_text(fe, "contribution")),
            "ownership_percentage": _to_float(_xml_text(fe, "ownershipPercentage")),
            "address": _xml_text(fe, "address"),
        })

    out = {"house_filings": [filing_row]}
    if activities:
        out["house_lobbying_activities"] = activities
    if activity_lobbyists:
        out["house_activity_lobbyists"] = activity_lobbyists
    if foreign_entities:
        out["house_foreign_entities"] = foreign_entities
    return out


def map_press_release(rec: dict, source_file) -> dict[str, list[dict]]:
    url = rec.get("url")
    if not url:
        return {}
    member = rec.get("member") or {}
    bioguide = member.get("bioguide_id")

    # Synthetic stable ID from URL hash
    import hashlib as _h
    press_id = _h.sha1(url.encode()).hexdigest()[:16]

    text = rec.get("text") or ""

    row = {
        "press_id": press_id,
        "url": url,
        "title": rec.get("title"),
        "date": rec.get("date"),
        "date_source": rec.get("date_source"),
        "source_index_page": rec.get("source"),
        "domain": rec.get("domain"),
        "scraper": rec.get("scraper"),
        "bioguide_id": bioguide,
        "member_name": member.get("name"),
        "member_party": member.get("party"),
        "member_state": member.get("state"),
        "member_chamber": member.get("chamber"),
        "text": text,
        "text_length": len(text),
        "collected_at": rec.get("collected_at"),
        "updated_at": rec.get("updated_at"),
        "source_file": str(source_file.name),
    }

    members_rows = []
    if bioguide:
        members_rows.append({
            "bioguide_id": bioguide,
            "name": member.get("name"),
            "party": member.get("party"),
            "state": member.get("state"),
            "chamber": member.get("chamber"),
        })

    out = {"press_releases": [row]}
    if members_rows:
        out["members"] = members_rows
    return out
