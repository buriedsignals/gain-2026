---
name: evidence-cards
description: Generate one-page markdown evidence cards from records in a DuckDB index of structured records. Each card is a single source record (filing UUID, House XML filename, press release URL hash, FARA entity ID, etc.) rendered in full, with the canonical public document URL linked at the top — the audit surface an editor uses to verify a claim in under a minute. Used by the data-detective orchestrator at Phase 3 and Phase 5 (synthesis). Triggers on prompts about evidence cards, audit cards, claim-to-source links, "render this filing as markdown," or "give me a one-page summary of this record."
license: MIT
metadata:
  parent: data-detective
  step: P3+P5_evidence
  inputs: DuckDB index + record IDs (filing_uuid, house_xml_filename, press_id)
  outputs: <source>_<id>.md per record
---

# data-detective-evidence-cards

One source record → one markdown card. Audit surface for editors.

## When to use

Called from the `data-detective` orchestrator whenever a claim cites a specific record. Also called by the investigator subagent inside Phase 3 cycles.

## What a card contains

- Source kind (senate_filing | house_filing | press_release | fara_principal | ...)
- Source ID (the primary key)
- Public document URL (lda.senate.gov, disclosurespreview.house.gov, original press URL, ...)
- Every field cited in the claim
- Raw excerpt for free-text fields (lobbying activity descriptions, press release body)
- Related records via joins (lobbyists, government entities, foreign entities)

Cards are **byte-deterministic from the index**: same input → same output (good for diffs).

## How to invoke

### Single card by ID

```bash
uv run scripts/evidence_card.py \
  --db <index.duckdb> \
  --source senate_filing \
  --id <filing_uuid> \
  --out <case>/cards
```

### Bulk from CSV (typical: pipe a detector output)

```bash
uv run scripts/evidence_card.py \
  --db <index.duckdb> \
  --source senate_filing \
  --from-csv <case>/anomalies/D4_foreign_filings.csv \
  --id-column filing_uuid \
  --limit 25 \
  --out <case>/cards
```

## Supported sources (current implementation)

- `senate_filing` — Senate LDA filing UUID
- `house_filing` — House LDA XML filename
- `press_release` — Press release press_id (URL hash)

Adding a new source kind: add an entry to `CARD_FACTORIES` + `RENDERERS` in `scripts/evidence_card.py`. The card renders the full record with field labels; the URL field anchors public verification.

## Reasoning behind cards (vs raw record dumps)

A reporter reading a $180M LDA filing wants:
- The text of the activity descriptions (not just the issue codes)
- The lobbyist roster with their `covered_position` text
- The foreign-entities table for this filing
- The government entities lobbied
- A URL to the canonical public document

A card gives all of that in ~50 lines. An editor verifies in <60 seconds.

## Composes with

- Input ← `data-detective-detect` (CSV of IDs)
- Used by `data-detective-passover` to package the cards alongside the Spotlight brief
