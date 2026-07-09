---
name: vault-ingest
description: "Archive the final data-detective findings into an Obsidian vault (or generic directory) as structured knowledge — one finding note per claim, one entity note per named person/organization/agency, one source note per cited filing/court case/external archive, plus a methodology note describing the data-detective pipeline that produced them. Wikilinks the entire graph. Honors the spotlight:ingest --sensitive flag for source-redacted notes. Limited by design to what is contained in the final report (findings-report.md + evidence-map.json) — not the entire case-trace. Use after Gate 1 approval at Phase 7 of data-detective, or standalone to ingest a single finished report. Triggers on prompts mentioning ingest findings to obsidian, archive case to vault, write findings into the knowledge base, structured-records evidence to obsidian, or sensitive flag for case archive."
license: MIT
metadata:
  parent: data-detective
  step: P7_vault
  inputs: findings-report.md, evidence-map.json, optional vault config
  outputs: one entity / source / finding / methodology note per element in the report
---

# vault-ingest

Archive data-detective findings into an Obsidian vault. Mirrors `spotlight:ingest` with adaptations for data-side evidence.

## When to use

Called from the `data-detective` orchestrator at Phase 7 (post-Gate-1, post-handoff). Also standalone — pass a finished `findings-report.md` + `evidence-map.json` and ingest into any vault.

## What it differs from spotlight:ingest

| | spotlight:ingest | vault-ingest |
|---|---|---|
| Source kind | Web pages, screenshots, Wayback snapshots | Filing UUIDs, House XML filenames, court dockets, FARA records, USAspending awards |
| Note types | Entity, Source URL, Tool, Methodology, Registry | Entity, Source-record, Detector, Query-hash, Methodology, Registry |
| Wikilink graph | URL ↔ entity ↔ method ↔ tool | filing_uuid ↔ entity ↔ detector ↔ query-hash ↔ method |
| --sensitive | Redacts source URLs in note bodies | Redacts personal identifiers + entity names below confidence threshold |
| Scope | Entire spotlight case | **Only what appears in the final report** (no raw detector dumps, no full evidence card list) |

## How to invoke

```bash
uv run scripts/vault_ingest.py \
  --report <case>/findings-report.md \
  --evidence-map <case>/evidence-map.json \
  --vault <obsidian-vault-path> \
  --subfolder "Investigations/GAIN Challenge 2026" \
  [--sensitive]                    # redact mode
  [--dry-run]                      # print what would be created, write nothing
```

## Note types and naming convention

```
<vault>/<subfolder>/
├── 00 — Investigation Summary.md           ← top-level note linking to everything
├── findings/
│   ├── C-001 — LOC Nation.md
│   ├── C-002 — Anchor & Arrow.md
│   └── ...
├── entities/
│   ├── Christina Loren Clement.md
│   ├── State of LOC Nation Global Public Benefit Corporation.md
│   ├── LOC COMMUNITY ASSOCIATION.md
│   ├── Russell W. Sullivan.md
│   ├── Apollo Global Management.md
│   └── ...
├── source-records/
│   ├── filing_uuid 5000632b-e40b-4762.md   ← one per cited LDA filing
│   ├── house_xml 301639546.md
│   └── court CLEMENT v. GARLAND.md
├── detectors/
│   ├── D5 single_client_juggernauts.md     ← only detectors actually cited
│   ├── D9 shell_pattern_filings.md
│   └── D11 revolving_door_committee_match.md
├── query-hashes/
│   ├── f9e737b8f3554a90.md                  ← one per SHA cited in findings
│   └── ...
└── methodology/
    ├── data-detective pipeline.md
    └── adversarial fact-check protocol.md
```

## Wikilink rules

Every note links bidirectionally:

- **Finding note** `C-001 — LOC Nation.md` links to:
  - All `entities/` it names (Christina Clement, LOC Nation, etc.)
  - All `source-records/` it cites
  - All `detectors/` that surfaced it
  - All `query-hashes/` referenced
  - The `methodology/` note
- **Entity note** `Christina Loren Clement.md` links to:
  - Every finding mentioning her
  - Every source-record she appears in
  - Other entities adjacent (her LLC, her court case, her own website)
- **Source-record note** links to: the finding(s) citing it, the entities mentioned in the record, the public URL, the local archive path (or "[REDACTED]" under --sensitive).

This produces a navigable graph in Obsidian's graph view that an editor can use to follow any thread.

## --sensitive flag

When passed, the script:

- Replaces any free-text excerpt longer than 200 chars with `[REDACTED for --sensitive; see source-records/<id>.md in non-sensitive copy]`
- Replaces any low-confidence entity name (e.g. unverified individuals) with `[UNVERIFIED ENTITY]`
- Strips local archive paths from source-record notes (keeps the public URL)
- Marks all notes with frontmatter `sensitive: true` so vault-side queries can filter

The `--sensitive` mode is designed for vaults shared with editors / outside legal review before publication, where source-record bodies and unverified entity names should be controlled.

## Restriction to "final report only"

By design, `vault-ingest` does **not** ingest:

- Raw detector CSVs (only detectors actually cited get a note)
- Evidence cards that aren't referenced in `evidence-map.json`
- The ambiguity queue from entity resolution
- Investigation log entries
- Working brief / methodology working files
- The bill-mentions extraction (unless cited)

What's in the vault is what's in the final, gate-approved report. The case-trace remains the raw working layer.

## Registries, aliases, supersession (ported from the Spotlight vault contract)

Every collection directory (`findings/`, `entities/`, `source-records/`, `detectors/`, `query-hashes/`, `methodology/`) carries a `_registry.json` (`schema_version`, `last_updated`, per-note index), with a root `_registry.json` holding collection stats. `entities/` additionally carries `_aliases.json` (canonical-name → alias list; e.g. "MAGA INC." ↔ "Make America Great Again Inc." lives HERE, not resolved silently in note bodies) and `_merge-proposals.json` (suspected duplicate entities awaiting a human merge decision — never auto-merge).

Finding notes carry claim-lifecycle frontmatter:

```yaml
verdict: verified            # from fact-check.json
confidence: high
confidence_cap: high         # lower it for time-decaying claims ("through Q1 2026" framings)
layer: durable               # durable | session
recorded: 2026-05-22
verified: 2026-07-09         # date of the LATEST verification pass
verified_by: <pass id or trace file>
```

and a **Supersession History** table — one row per verification/correction pass:

```markdown
## Supersession History
| Date | Event | Note |
|---|---|---|
| 2026-05-22 | recorded | initial finding, Gate 1 approved |
| 2026-05-25 | corrected | citation drift fixes (see findings-report Corrections log) |
| 2026-07-09 | re-verified | Apollo→Arconic scope correction; still holds |
```

A claim that fails a later pass is not deleted — it gets a `superseded` row, `verdict: false` (or `mischaracterized`), and stays in the graph as a record of what was corrected. Re-running vault-ingest after a corrections pass appends supersession rows; it never silently overwrites note bodies.

## Dry-run output

```bash
uv run scripts/vault_ingest.py --report ... --evidence-map ... --dry-run
```

Prints a tree of notes that would be created, with the wikilink graph counted but not written. Useful before committing to a sensitive vault.

## Composes with

- Input ← `data-detective` orchestrator Phase 5 synthesis output: `findings-report.md` + `evidence-map.json`
- Composes with `spotlight:ingest` if the case also produced a spotlight-side output (via `spotlight-handoff`) — both can write to the same vault subfolder, cross-linking the data-side and web-side notes.
