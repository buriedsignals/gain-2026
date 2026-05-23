# Interaction Traces

This investigation ran in a single Claude Code session on 2026-05-22 with Claude
Opus 4.7 (1M-context). The conversation is preserved in the session transcript;
this document indexes the moments where human judgment intervened and the
skill-invocation boundaries.

## Session structure

| Phase | Activity | Key skill invocation | Notes |
|---|---|---|---|
| Brief | Strategic disagreement on whether to use Spotlight as-is or build a new skill | (none — design discussion) | Agent pushed back on retrofitting Spotlight; user agreed; user named the new skill `data-detective` |
| Methodology | Drafted phases P0-P8 into `case/methodology.json` | (none) | User reviewed; user clarified the skill must be **portable**, not LDA-specific |
| Tooling build | Wrote `ingest.py`, `resolve_entities.py`, `query.py`, `evidence_card.py`, `external/fara.py`, and the LDA profile | (none — code generation) | First ingest attempt was 60× slower than necessary; switched to pyarrow bulk insert mid-session |
| Pipeline run | Built index, resolved entities, pulled FARA, ran all detectors | `run_pipeline.sh` equivalent (run as separate commands) | 3 min total |
| Cycle 1 — LOC Nation thread | Drilled into D5 top result; pulled all 15 filings; built evidence cards; web-archive corroboration | `evidence_card.py --from-csv ... --out case/cards`; `firecrawl scrape` (URL + entity website) | Single ad-hoc SQL: `SELECT ... FROM senate_filings WHERE upper(client_name) LIKE '%LOC NATION%'` |
| Cycle 1 — Anchor & Arrow thread | Drilled into D8 top result; pulled distinct clients with totals; pulled founder covered_position text | `evidence_card.py --from-csv`; `firecrawl search` for founder bios | Single ad-hoc SQL: `SELECT registrant_name, count(*), sum(income) FROM senate_filings WHERE upper(registrant_name) LIKE '%ANCHOR%ARROW%'` |
| Cycle 1 — FARA gap aggregate | In-database join of `senate_foreign_entities` to `fara_registrants` | (in `case/investigation-log.json`) | One query, one number |
| Gate 1 | Wrote `findings.json`, `evidence-map.json`, `findings-report.md` | (synthesis) | User did not request more cycles |
| Submission | Packaged skill + case-trace + README + this file | (packaging) | All artifacts in `submission/` |

## Human judgment moments

1. **Strategic redirect (skill choice):** The user instructed the agent to invoke
   the existing Spotlight skill. The agent pushed back: Spotlight is an OSINT
   web-investigation tool, not a structured-records investigation tool. The
   user agreed and approved the new-skill direction, also naming it
   `data-detective`.
2. **Portability clarification:** The agent initially framed the build scripts
   as one-off tools used for this case. The user clarified the scripts must be
   **portable** to other corpora; the architecture was reframed accordingly
   (profile-driven ETL, generic resolver, generic evidence cards).
3. **Investigation angle:** The user picked open exploration + FARA gap as the
   two parallel threads, and indicated prize-targeting full effort. The agent
   adapted the methodology to run both threads through one shared index.
4. **Findings framing:** The agent surfaced the LOC Nation anomaly. The user
   was alerted to it explicitly in chat ("**This is huge.**") and confirmed
   the direction by responding with continued work.

## Skill-invocation log (in order)

| # | Command | Purpose |
|---|---|---|
| 1 | `uv run skill/scripts/ingest.py --profile ... --data-root ... --db ...` (initial) | First ingest attempt — too slow |
| 2 | (killed PID) | Diagnosis; switched to pyarrow |
| 3 | `uv run skill/scripts/ingest.py ...` (pyarrow path) | Full corpus ingest in 3 min |
| 4 | `uv run skill/scripts/resolve_entities.py --db ... --out case/` | Entity resolution (99.9% via bridge keys) |
| 5 | `uv run skill/scripts/external/fara.py --db ... --cache case/fara/cache` | FARA bulk load |
| 6 | `uv run skill/scripts/query.py --db ... --detector all --out case/anomalies` | All 8 detectors |
| 7 | `uv run skill/scripts/evidence_card.py --db ... --source senate_filing --from-csv ... --out case/cards` | LOC Nation cards (×15) |
| 8 | `uv run skill/scripts/evidence_card.py ...` | Anchor & Arrow cards (×8) |
| 9 | `firecrawl scrape <lda.senate.gov/filings/public/filing/{uuid}/print/>` (×3) | Archive evidence sources |
| 10 | `firecrawl search "..."` (×2) | Independent founder-biography verification |

## Notable cost-savers

- The investigator (the host model) never read a raw LDA filing during exploration. It read CSVs.
- Entity resolution did 7,451 of 7,458 (99.9%) of House↔Senate matches via deterministic bridge keys — no embeddings, no LLM-as-judge.
- All eight detectors combined ran in well under one second against the indexed corpus.
- Total LLM tokens spent on data scanning: zero. Tokens were spent on (a) strategy, (b) interpreting CSV rows the user wanted to investigate, and (c) writing the findings report.
