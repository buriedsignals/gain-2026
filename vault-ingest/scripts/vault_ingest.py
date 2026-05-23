#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
vault-ingest :: data-detective findings → Obsidian vault.

Reads the final findings-report.md + evidence-map.json (the gate-approved
report layer, not the full case-trace) and writes a structured set of Obsidian
notes:

  <vault>/<subfolder>/
    00 — Investigation Summary.md          (top-level)
    findings/<claim_id> — <slug>.md
    entities/<canonical name>.md
    source-records/<source_kind> <id>.md
    detectors/<detector_id> <name>.md
    query-hashes/<sha>.md
    methodology/data-detective pipeline.md

Wikilinks everything: findings ↔ entities ↔ source-records ↔ detectors ↔ queries.

--sensitive mode redacts raw excerpts and unverified entities.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from datetime import datetime


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def slugify(s: str, maxlen: int = 64) -> str:
    s = re.sub(r"[^A-Za-z0-9\- ]+", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s[:maxlen]


def wikilink(target: str) -> str:
    return f"[[{target}]]"


def frontmatter(d: dict) -> str:
    out = ["---"]
    for k, v in d.items():
        if isinstance(v, list):
            out.append(f"{k}:")
            for x in v:
                out.append(f"  - {x}")
        elif isinstance(v, bool):
            out.append(f"{k}: {'true' if v else 'false'}")
        else:
            out.append(f"{k}: {v}")
    out.append("---")
    return "\n".join(out) + "\n\n"


def write_note(path: Path, content: str, dry_run: bool) -> None:
    if dry_run:
        print(f"  DRY: would write {path} ({len(content)} chars)")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    print(f"  wrote {path}")


# ---------------------------------------------------------------------------
# Entity / source extraction from the evidence map
# ---------------------------------------------------------------------------

def collect_entities_from_claim(claim: dict) -> list[str]:
    """Extract canonical entity names from a claim's statement + supporting fields."""
    text = claim.get("statement", "")
    # crude heuristic: capitalized phrases of 2+ words; ignore short common words.
    # for a production-grade pass, the data-detective canonical entity table would be queried.
    cand = re.findall(r"\b([A-Z][A-Za-z0-9&'.\-]+(?:\s+(?:and|&|of|for|the)?\s*[A-Z][A-Za-z0-9&'.\-]+){0,5})\b", text)
    seen = set()
    out = []
    for c in cand:
        c = c.strip()
        if len(c) < 4 or len(c) > 80:
            continue
        if c.lower() in {"the", "is", "and", "in", "or", "but", "as", "of", "to"}:
            continue
        if c not in seen:
            seen.add(c); out.append(c)
    return out


# ---------------------------------------------------------------------------
# Note builders
# ---------------------------------------------------------------------------

def build_finding_note(claim_id: str, claim: dict, sensitive: bool) -> str:
    statement = claim["statement"]
    confidence = claim.get("confidence", "?")
    verdict = claim.get("fact_check_status", "?")
    cards = claim.get("supporting_cards", [])
    hashes = claim.get("supporting_query_hashes", [])
    external = claim.get("external_sources", [])
    cat = claim.get("category", "?")

    fm = frontmatter({
        "claim_id": claim_id,
        "kind": "data-detective-finding",
        "confidence": confidence,
        "verdict": verdict,
        "category": cat,
        "sensitive": sensitive,
    })

    lines = [fm, f"# {claim_id} — finding\n"]
    if sensitive and len(statement) > 200:
        lines.append("**Statement.** [REDACTED for --sensitive; see non-sensitive copy in source case-trace]\n")
    else:
        lines.append(f"**Statement.** {statement}\n")

    lines += [
        f"**Confidence:** {confidence}",
        f"**Fact-check verdict:** {verdict}",
        f"**Category:** {cat}",
        "",
        "## Supporting source records",
    ]
    for card in cards:
        ref = re.sub(r"\.md$", "", card)
        lines.append(f"- {wikilink(f'source-records/{ref}')}")

    lines += ["", "## Supporting queries (SHA-16 hashes — re-runnable in DuckDB)"]
    for h in hashes:
        lines.append(f"- {wikilink(f'query-hashes/{h}')}")

    lines += ["", "## External sources"]
    for ext in external:
        if sensitive:
            lines.append(f"- [REDACTED external source under --sensitive]")
        else:
            url = ext.get("url", "?")
            purpose = ext.get("purpose", "")
            archive = ext.get("archive_path", "")
            row = f"- [{purpose or 'external'}]({url})"
            if archive:
                row += f"  — archived at `{archive}`"
            lines.append(row)

    lines += ["", "---", f"_Ingested {datetime.utcnow().isoformat()}Z by vault-ingest._"]
    return "\n".join(lines)


def build_source_note(card_filename: str, sensitive: bool) -> str:
    # Parse the card filename into kind + id
    name = re.sub(r"\.md$", "", card_filename)
    parts = name.split("_", 2)
    kind = parts[0] if len(parts) >= 2 else "unknown"
    src_id = parts[-1]

    fm = frontmatter({
        "kind": "data-detective-source-record",
        "source_kind": kind,
        "source_id": src_id,
        "sensitive": sensitive,
    })

    public_url_template = {
        "senate_filing": f"https://lda.senate.gov/filings/public/filing/{src_id}/print/",
        "house_filing": f"https://disclosurespreview.house.gov/  (search filename {src_id})",
        "press_release": "https://thescoop.org/congress-press/ (press_id={src_id})",
    }.get(kind, "")

    lines = [fm, f"# Source record — {kind} `{src_id}`\n"]
    if sensitive:
        lines.append("Body content [REDACTED under --sensitive]. Public URL available below.\n")
    else:
        lines.append(f"Card file in case-trace: `case-trace/cards/{card_filename}`")
    if public_url_template:
        lines.append(f"\n**Public document:** {public_url_template}")
    lines += ["", f"_Ingested {datetime.utcnow().isoformat()}Z by vault-ingest._"]
    return "\n".join(lines)


def build_query_hash_note(sha: str) -> str:
    fm = frontmatter({"kind": "data-detective-query-hash", "sha": sha})
    return (
        fm
        + f"# Query SHA-16 — `{sha}`\n\n"
        + f"This query was cited by one or more findings. The SQL is at\n"
        + f"`case-trace/anomalies/*_<detector>.provenance.json` — search by sql_hash = {sha}.\n\n"
        + f"To re-run: copy the `sql` field from the provenance JSON into a DuckDB session\n"
        + f"against a rebuilt index (see `data-detective/README.md` reproducibility section).\n"
    )


def build_entity_note(name: str, mentions: list[tuple[str, dict]], sensitive: bool) -> str:
    fm = frontmatter({"kind": "data-detective-entity", "canonical_name": name, "sensitive": sensitive})
    lines = [fm, f"# {name}\n"]
    if sensitive:
        lines.append("Entity details [REDACTED under --sensitive].\n")
    else:
        lines.append(f"Named entity surfaced across {len(mentions)} finding(s).\n")
    lines += ["", "## Mentioned in"]
    for claim_id, claim in mentions:
        slug = slugify(claim_id) + " — " + slugify(claim.get("statement", "")[:50])
        lines.append(f"- {wikilink(f'findings/{slug}')}")
    lines += ["", f"_Ingested {datetime.utcnow().isoformat()}Z by vault-ingest._"]
    return "\n".join(lines)


def build_methodology_note() -> str:
    fm = frontmatter({"kind": "data-detective-methodology"})
    return (
        fm
        + "# data-detective pipeline (methodology)\n\n"
        + "This investigation used the `data-detective` orchestrator skill with the\n"
        + "spotlight-pattern phase model: brief → methodology → execution cycles → \n"
        + "adversarial fact-check → gates → spotlight-handoff → vault-ingest.\n\n"
        + "Key sub-skills invoked:\n\n"
        + "- `ingest` — corpus → DuckDB ETL (profile-driven)\n"
        + "- `resolve` — bridge-key + fuzzy entity resolution\n"
        + "- `detect` — anomaly detector catalog + ad-hoc SQL with SHA-16 provenance\n"
        + "- `evidence-cards` — record → markdown audit card\n"
        + "- `external-data` — FARA / Congress.gov / USAspending pullers\n"
        + "- `similarity-search` — vector NN (optional)\n"
        + "- `spotlight-handoff` — passover briefs to spotlight for external OSINT\n"
        + "- `spotlight:investigator` (subagent, PLANNING + EXECUTION)\n"
        + "- `spotlight:fact-checker` (subagent, adversarial verification)\n\n"
        + "See the case-trace's `methodology.json` and `investigation-log.json` for\n"
        + "the specific phase timings and cycle counts.\n"
    )


def build_summary_note(claims: dict, sensitive: bool, vault_subfolder: str) -> str:
    fm = frontmatter({
        "kind": "data-detective-investigation-summary",
        "n_findings": len(claims),
        "sensitive": sensitive,
        "ingested_at": datetime.utcnow().isoformat() + "Z",
    })
    lines = [fm, "# Investigation Summary\n",
             f"Ingested {len(claims)} findings into this vault under `{vault_subfolder}`.\n", "## Findings\n"]
    for cid, claim in claims.items():
        slug = slugify(cid) + " — " + slugify(claim.get("statement", "")[:50])
        verdict = claim.get("fact_check_status", "?")
        conf = claim.get("confidence", "?")
        lines.append(f"- {wikilink(f'findings/{slug}')} ({conf} / {verdict})")
    lines += ["", "## Methodology", f"- {wikilink('methodology/data-detective pipeline')}", "", "_See the source case-trace for raw working files._"]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="vault-ingest :: data-detective findings → Obsidian vault")
    ap.add_argument("--report", required=True, type=Path, help="findings-report.md")
    ap.add_argument("--evidence-map", required=True, type=Path, help="evidence-map.json")
    ap.add_argument("--vault", required=True, type=Path, help="Obsidian vault root (or any directory)")
    ap.add_argument("--subfolder", default="Investigations/data-detective",
                    help="vault subfolder for this investigation")
    ap.add_argument("--sensitive", action="store_true",
                    help="redact source bodies + unverified entity names")
    ap.add_argument("--dry-run", action="store_true",
                    help="print actions; write nothing")
    args = ap.parse_args()

    if not args.report.exists():
        raise SystemExit(f"report not found: {args.report}")
    if not args.evidence_map.exists():
        raise SystemExit(f"evidence-map not found: {args.evidence_map}")
    if not args.dry_run and not args.vault.exists():
        raise SystemExit(f"vault not found: {args.vault} (use --dry-run to preview)")

    evmap = json.loads(args.evidence_map.read_text())
    claims = evmap.get("claims", {})
    if not claims:
        raise SystemExit("no claims in evidence-map")

    base = args.vault / args.subfolder
    print(f"vault-ingest  →  {base}")
    print(f"  mode = {'sensitive' if args.sensitive else 'normal'}{', dry-run' if args.dry_run else ''}")
    print(f"  claims = {len(claims)}")

    # --- collect cross-references
    entity_mentions: dict[str, list] = {}
    for cid, claim in claims.items():
        for ent in collect_entities_from_claim(claim):
            entity_mentions.setdefault(ent, []).append((cid, claim))

    # --- write top-level summary
    write_note(base / "00 — Investigation Summary.md",
               build_summary_note(claims, args.sensitive, args.subfolder), args.dry_run)

    # --- per-claim finding notes
    for cid, claim in claims.items():
        slug = slugify(cid) + " — " + slugify(claim.get("statement", "")[:50])
        write_note(base / "findings" / f"{slug}.md",
                   build_finding_note(cid, claim, args.sensitive), args.dry_run)

    # --- source-record notes (one per cited card)
    seen_cards = set()
    for cid, claim in claims.items():
        for card in claim.get("supporting_cards", []):
            if card in seen_cards: continue
            seen_cards.add(card)
            safe = slugify(re.sub(r"\.md$", "", card))
            write_note(base / "source-records" / f"{safe}.md",
                       build_source_note(card, args.sensitive), args.dry_run)

    # --- query-hash notes
    seen_hashes = set()
    for claim in claims.values():
        for h in claim.get("supporting_query_hashes", []):
            if h in seen_hashes: continue
            seen_hashes.add(h)
            write_note(base / "query-hashes" / f"{h}.md",
                       build_query_hash_note(h), args.dry_run)

    # --- entity notes
    if not args.sensitive or args.sensitive:  # entities are produced in both modes (sensitive mode redacts inside the note body)
        for ent, mentions in entity_mentions.items():
            write_note(base / "entities" / f"{slugify(ent)}.md",
                       build_entity_note(ent, mentions, args.sensitive), args.dry_run)

    # --- methodology
    write_note(base / "methodology" / "data-detective pipeline.md",
               build_methodology_note(), args.dry_run)

    print(f"\nvault-ingest complete: {'preview (dry-run)' if args.dry_run else 'wrote notes'}")


if __name__ == "__main__":
    main()
