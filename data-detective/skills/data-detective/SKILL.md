---
name: data-detective
description: "Orchestrate a structured-records investigation against a large data corpus (XML, JSON, JSONL, CSV) — lobbying filings, FEC reports, court records, IRS 990s, anything tabular or nested where the story lives in relationships. Mirrors the Spotlight orchestration pattern (brief, methodology, execution cycles, adversarial fact-check, gates, handoff) but geared for structured data instead of web OSINT. Pushes ETL, entity resolution, anomaly detection, and aggregation to deterministic Python + DuckDB; reserves the LLM for reasoning over already-filtered candidates. Composes with the nine sibling sub-skills (ingest, resolve, detect, evidence-cards, external-data, similarity-search, report-drafting, spotlight-handoff, vault-ingest). Reuses the spotlight investigator and fact-checker subagents. Triggers on prompts mentioning data-driven investigation, lobbying records, LDA, FEC, FARA, corporate filings, large XML or JSON corpora, structured-records journalism, or finding a story in this dataset."
license: MIT
metadata:
  author: Tom Vaillant (Buried Signals)
  version: "2.0"
  pattern: spotlight-style orchestrator with phase gates + adversarial verification
  composes_with: spotlight (investigator + fact-checker subagents; spotlight-handoff)
compatibility: Requires Python 3.11+ and uv. Built on DuckDB and lxml. Designed for Claude Code or any Agent Skills client that supports subagent spawning.
---

# data-detective — orchestrator

You — the host session — execute. This skill instructs. You call Agent() to spawn subagents, run scripts via Bash, evaluate gates, and present synthesis at user checkpoints.

**Two absolute rules** (borrowed from Spotlight discipline):

1. **You orchestrate; subagents investigate.** The investigator agent reads ranked candidate CSVs and drills via SQL — it never scans raw documents during exploration. The fact-checker runs adversarially after every cycle.
2. **Gates are real and require the user — no exceptions, on every runtime.** At each gate (brief, methodology, Gate 1), present your synthesis and decisions, then **END YOUR TURN**. Do not proceed, delegate past the gate, or self-approve. Act only on the user's reply; never treat the absence of a reply as approval — stopping and waiting IS the correct behavior. The inverse holds for subagents: they have no user and no gates — they run their delegated task end-to-end and return their result to you (their personas carry this contract).

The discipline borrowed from Spotlight (brief → methodology → cycles → fact-check → gate → ingest) is preserved. The medium is different: where Spotlight verifies claims about people and organizations through web OSINT, `data-detective` finds and verifies claims **inside a corpus of structured records**. After Gate 1, the **spotlight-handoff** phase hands chosen findings to Spotlight for external OSINT amplification.

---

## Sub-skill architecture

`data-detective` is an orchestrator. The actual work happens in nine sibling skills, each invoked by phase:

| Sub-skill | Phase | What it does |
|---|---|---|
| `ingest` | P1 | Profile-driven ETL: corpus → DuckDB index |
| `resolve` | P2 | Bridge-key + fuzzy entity resolution across sources |
| `detect` | P3 | Detector catalog + ad-hoc SQL with SHA-tagged provenance |
| `evidence-cards` | P3/P5 | Source record → markdown audit card |
| `external-data` | P3 | Pullers for FARA, Congress.gov committee graph, USAspending |
| `similarity-search` | P3 (optional) | Vector similarity for anomalies not expressible as keyword rules |
| `report-drafting` | P5 | Synthesis: findings-report.md + report.html + evidence-map.json (ships journalist-grade template + design discipline) |
| `spotlight-handoff` | P6 | Handoff to Spotlight for external OSINT amplification |
| `vault-ingest` | P7 | Final-report → Obsidian vault (mirrors `spotlight:ingest`; `--sensitive` aware) |

Each sub-skill has its own `SKILL.md` describing how to invoke it. The orchestrator (this file) tells you *when* to invoke each.

---

## Agent routing table

| Phase | Subagent | Mode | Purpose |
|---|---|---|---|
| P2 methodology | `spotlight:investigator` | PLANNING (data-corpus context) | Design investigation plan over the indexed corpus |
| P3 execution | `spotlight:investigator` | EXECUTION (one cycle) | Read ranked CSVs, drill via SQL, write findings.json |
| P3 fact-check | `spotlight:fact-checker` | adversarial | Verify claims independently; surface disconfirming evidence |
| P6 spotlight-handoff | `Skill(spotlight)` (orchestrator) | normal | External OSINT amplification of chosen findings |

`spotlight:investigator` and `spotlight:fact-checker` are reused unchanged. They already know how to operate over evidence chains — we adapt the prompt to give them corpus-aware tools instead of firecrawl search.

---

## Phases

```
P0 Preflight  →  P1 Brief  →  P2 Methodology  →  P3 Execution cycles (max 5)
                                                         ↓
                                              [investigator → fact-checker → gap eval]
                                                         ↓
                                                 P4 Gate 1 (user review)
                                                         ↓
                                       ┌─────────────────┴─────────────────┐
                                       ↓                                   ↓
                              [DIRECT path]                     [HANDOVER path]
                                       ↓                                   ↓
                          P5 report-drafting                   P6 spotlight-handoff
                          (report.html +                       (Spotlight runs its full
                           findings-report.md +                 pipeline; draws the
                           evidence-map.json)                   final report on its end
                                       ↓                        via its own
                                       │                        report-drafting skill
                                       │                        in hybrid mode)
                                       ↓                                   ↓
                                       └─────────────────┬─────────────────┘
                                                         ↓
                                                  P7 vault-ingest
```

The Phase 4 Gate 1 branch is a binary user choice. Direct = data-detective draws the report; handover = Spotlight draws the report. Both paths converge at Phase 7.

Every phase records an ISO-timestamped entry in `case/investigation-log.json`. Date stamps gate transitions.

---

### Phase 0 — Preflight

Check the working directory:

```bash
# Detect deps
command -v duckdb || command -v uv      # need uv (PEP 723 scripts) or duckdb CLI
ls .spotlight-config.json 2>/dev/null   # vault config; required if ingesting findings to Obsidian
```

Confirm a profile exists for the corpus (see `ingest`). If not, prompt the user to write one against the worked example at `ingest/scripts/examples/lda_profile.py`.

Create the case workspace if absent:

```
case/
  brief-directions.txt          # written at P1 gate
  methodology.json              # written at P2 gate
  state.json                    # session-persistent investigation state
  findings.json                 # claims, append-only during P3
  investigation-log.json        # append-only date-stamped event log
  anomalies/                    # detector outputs + provenance JSONs
  cards/                        # evidence cards
  external/                     # archived external sources
  data/                         # findings.json + fact-check.json (Spotlight-shape paths)
```

Write `state.json` initializing `phase: "P1_brief"` and `last_updated: <ISO>`.

---

### Phase 1 — Brief (skill ↔ user; gate)

Conversation, not subagent. Ask the user:

1. **Lead.** What might be in this corpus?
2. **Scope.** Which slices? Time range? Geography?
3. **Angle.** Open exploration or specific hypothesis?
4. **Constraints.** What's off-limits? Budget?

Restate the agreed direction in 2-3 sentences. Write to `case/brief-directions.txt` with the ISO timestamp.

**Gate 1 (user approval).** Do not proceed without explicit "approved."

Append to `case/investigation-log.json`:

```json
{ "ts": "<ISO>", "event": "brief_approved", "summary": "<one line>" }
```

---

### Phase 2 — Methodology (spawn investigator in PLANNING; gate)

Build/refresh the index first via `ingest`. Then spawn the investigator in planning mode:

```
Agent(
  subagent_type: "spotlight:investigator",
  prompt: "MODE: PLANNING
PROJECT: <project_slug>
SEARCH_LIBRARY: not-applicable (this is a structured-records investigation)
INVESTIGATION_KIND: data-corpus
CORPUS_INDEX: case/index.duckdb (~<size> GB; tables: <list>)
ENTITY_GRAPH: built via resolve (99%+ deterministic via bridge keys)
DETECTOR_CATALOG: see detect/references/detectors.md (D1-D12+)
EXTERNAL_JOINS_AVAILABLE: FARA bulk, Congress.gov committee graph, USAspending
SKILLS_AVAILABLE: detect (run detector battery / ad-hoc SQL),
                  evidence-cards (emit per-record audit cards),
                  external-data (pull FARA / Congress.gov / USAspending),
                  similarity-search (vector NN over text columns).
NO_RAW_SCANS: Do not request raw filings during planning. Plan ranked-CSV pivots only.

Approved brief directions:
<contents of case/brief-directions.txt>

Write the methodology plan to case/data/methodology.json (Spotlight-shape path).
For each thread, declare: detector(s) to run, expected anomaly shape, drill-down queries,
external joins needed, and evidence-card targets.
Do NOT execute. Planning only.",
  model: "opus",
  run_in_background: true
)
```

When the agent completes, read `case/data/methodology.json`, present a summary to the user, iterate if needed.

**Gate 2 (user approval).** Append `methodology_approved` to investigation-log.json.

---

### Phase 3 — Execution cycles (max 5)

Each cycle: [run detectors] → [investigator picks threads + drills] → [fact-checker adversarially verifies] → [evaluate readiness or loop].

```
CYCLE N (N starts at 1):

1. Run/refresh detector battery via detect:
     uv run detect/scripts/query.py \
       --db case/index.duckdb \
       --detector all --out case/anomalies

2. Spawn investigator in EXECUTION mode:
     Agent(
       subagent_type: "spotlight:investigator",
       prompt: "MODE: EXECUTION
PROJECT: <slug>
CYCLE: <N>
PRIOR_FINDINGS: <case/findings.json contents>
PRIOR_GAPS: <gaps from fact-check.json if N > 1>
RANKED_CSV_INPUTS: case/anomalies/*.csv (top 50-500 per detector with provenance.json next to each)
TOOLS: detect for ad-hoc SQL (query.py --sql ...),
       evidence-cards for emitting per-record cards.
NO_RAW_SCANS: read CSVs not raw filings during exploration.

Pick the 2-3 strongest threads from the ranked CSVs. For each:
- Drill via query.py --sql to surface specific records
- Emit evidence cards for 5-15 cited records per thread
- Append the claim to case/data/findings.json with confidence level + supporting_cards + supporting_query_hashes
- Append a log entry to case/investigation-log.json

Stop when 3+ high-confidence claims accumulate OR you exhaust strong leads.",
       model: "opus",
       run_in_background: true
     )

3. Spawn fact-checker adversarially:
     Agent(
       subagent_type: "spotlight:fact-checker",
       prompt: "PROJECT: <slug>
SEARCH_LIBRARY: firecrawl
INVESTIGATION_KIND: data-corpus
SKILLS: spotlight:web-archiving, spotlight:content-access
INPUT: case/data/findings.json
OUTPUT: case/data/fact-check.json
ADVERSARIAL: For each claim, independently re-verify via firecrawl. Look for
disconfirming evidence. Apply SIFT. Archive every cited source. Issue per-claim
verdicts: verified | partially_verified | disputed | unable_to_verify.
Also surface monitoring_recommendations[] for future cycles.",
       model: "opus",
       run_in_background: true
     )

4. Editorial standards check (host-side):
   - Every claim cites at least one filing_uuid / house_xml / press_id via evidence card?
   - Every numeric claim cites a SQL hash from provenance.json?
   - investigation-log.json has substance (queries run, threads opened/closed)?
   - All high-confidence claims have 2+ independent sources?
   - All external sources archived?
   If any fail: re-spawn the responsible agent with a specific fix instruction.

5. Readiness criteria:

   | Criterion | Threshold |
   |---|---|
   | Minimum findings | 3+ at high confidence |
   | Source independence | 2+ independent sources per key claim |
   | Adversarial verdict | All high-confidence claims verified or partially_verified |
   | Evidence cards | One per cited source record |
   | Limitations documented | Yes for each claim |

6. If ALL criteria met → Gate 1 (Phase 4).
   If NOT met AND N < 5 → identify specific gaps, increment N, loop.
   If NOT met AND N >= 5 → stall protocol (user picks: continue, pivot, accept as-is).
```

Date-stamp each cycle boundary in `investigation-log.json`.

**Optional inside any cycle:** Invoke `similarity-search` when keyword detectors won't surface an anomaly — e.g., "find more filings that smell like LOC Nation" — and feed the nearest neighbors back as a candidate set.

---

### Phase 4 — Gate 1 (user review)

Generate `case/summary.md` in the Spotlight Gate-1 shape:

```markdown
# <Investigation Title>
**Date:** YYYY-MM-DD | **Cycles:** N | **Status:** Pending review

## Overview
2-3 paragraph narrative.

## Scope
What was investigated; what was out of scope.

## Key Conclusions
- ...

## Findings
| # | Claim | Confidence | Verdict | Sources |
| C-001 | ... | high | verified | N cards |

## Limitations
- ...
```

Present headline ("N verified findings across M cycles"), findings table, method summary, limitations, confidence assessment.

**Gate 1 (user approval).** Iterate on follow-up cycles if requested.

#### Path branch — at Gate 1, ask the user which finishing path

After approval, prompt the user to choose ONE finishing path:

> "Findings approved. Two finishing paths:
>
> (a) **Direct report** — data-detective drafts the public-facing report.html + findings-report.md + evidence-map.json now (Phase 5 here). No external OSINT amplification. Choose this when the data corpus is the whole story and no external follow-up is needed.
>
> (b) **Spotlight handover** — skip Phase 5 here. Hand off the verified findings to Spotlight for external OSINT amplification; Spotlight runs its full pipeline (brief → methodology → cycles → fact-check → Gate 1) and draws the final report on its end via its own `report-drafting` skill. Choose this when external corroboration is the next step and you want OSINT cycles to inform the public report."
>
> Write the user's choice to `case/data/finishing-path.txt` as either `direct` or `handover`. Both paths converge at Phase 7 (vault ingestion).

**If `direct`:** run Phase 5 below, then SKIP Phase 6, go to Phase 7.
**If `handover`:** SKIP Phase 5, run Phase 6 below, let Spotlight produce the report on its end, then go to Phase 7 here once Spotlight's pipeline completes.

---

### Phase 5 — Synthesis (DIRECT PATH ONLY)

Run only if user chose `direct` at Gate 1.

Invoke `report-drafting` (the Phase 5 sub-skill). It produces three deliverables:

1. **`case/findings-report.md`** — narrative audit document (editor / fact-checker read).
2. **`case/report.html`** — public-facing journalism artifact, built from `report-drafting/references/report-template.html`. Required structure per finding: novelty pill + confidence pill, replication-path block (`.path`), inline primary-source strip (`.sources`). Methodology section walks all executed phases in order, with the adversarial fact-check verdict table INSIDE the Phase 3 block — NOT a separate top-level section.
3. **`case/evidence-map.json`** — machine-readable audit ledger (see `references/evidence-map-format.md` at the data-detective package root — sibling of `agents/` and `skills/`, not inside this skill dir). Every claim → cards → query hashes → external URLs.

Editing protocol: use `Read` + `Edit` with anchored old_strings. Never run greedy regex on the live HTML — past investigations lost hours to a single `re.sub(..., re.DOTALL)` that ate the file.

Append `synthesis_complete` to investigation-log.json. Then SKIP Phase 6, advance to Phase 7.

---

### Phase 6 — Spotlight handover (HANDOVER PATH ONLY)

Run only if user chose `handover` at Gate 1.

This is the *spotlight-handoff cycle*: data-driven findings hand off to the Spotlight orchestrator for external OSINT amplification. **Spotlight draws the final report on its end** via its own `report-drafting` skill in hybrid mode — do NOT also run Phase 5 here.

For each candidate finding (subset of findings.json, user-curated at Gate 1):

1. Invoke `spotlight-handoff` to generate Spotlight-ready briefs. The output is one structured `spotlight-brief.md` per candidate, with:
   - One-sentence claim
   - Named entities (people, companies, agencies) needing external research
   - URLs to investigate
   - What data-detective already established (with evidence card refs)
   - What Spotlight should pursue (suggested OSINT angles)

2. Spawn Spotlight on the chosen brief:

   ```
   Skill(spotlight) with brief=<path-to-spotlight-brief.md>
   ```

3. Spotlight runs its own cycles externally. Its output (`cases/<project>/summary.md`, evidence cards, web archives) joins data-detective's case-trace as upstream context.

The composite result — data-side audit trail + spotlight-side external OSINT — is richer than either alone. See [spotlight-handoff/SKILL.md](../spotlight-handoff/SKILL.md) for the full protocol.

---

### Phase 7 — Ingestion (vault archive)

Two ingestion paths run in parallel:

1. **`vault-ingest`** — the data-detective side. Limited by design to what's in the final report (findings-report.md + evidence-map.json). Mirrors `spotlight:ingest`'s pattern but uses source-record / detector / query-hash note types. Honors `--sensitive` for source-redacted notes destined for outside-counsel or pre-publication review vaults.

   ```bash
   uv run vault-ingest/scripts/vault_ingest.py \
     --report case/findings-report.md \
     --evidence-map case/evidence-map.json \
     --vault <obsidian-vault-path> \
     --subfolder "Investigations/<project>" \
     [--sensitive]
   ```

2. **`spotlight:ingest`** — if the spotlight-handoff cycle produced its own findings (web-archived sources, social-media notes, etc.), archive those too:

   ```
   Skill(spotlight:ingest) with case_path=<spotlight case dir>
   ```

Both write to the same vault subfolder, cross-linking data-side and web-side notes. The composite graph (findings ↔ entities ↔ source-records ↔ URLs ↔ queries) is navigable in Obsidian's graph view.

---

## Communication style (Spotlight discipline preserved)

- Direct and concise. No filler.
- Synthesize agent results — never dump raw output. Highlight what is surprising or does not add up.
- Use structured output (bullets, tables) for summaries.
- Gates are conversations, not announcements. Present information, challenge assumptions, answer questions, iterate.
- When spawning agents: state what you are doing and why.
- When something fails: say so clearly with what was tried.

---

## Context recovery

All state in files. If a session ends mid-investigation, re-read in this order:

```
case/state.json                       — current phase + open threads
case/brief-directions.txt             — approved brief
case/data/methodology.json            — approved plan
case/findings.json                    — claims so far
case/data/fact-check.json             — adversarial verdicts
case/anomalies/*.csv + *.provenance.json  — query outputs + audit hashes
case/cards/                           — evidence cards generated
case/investigation-log.json           — what happened, with timestamps
```

Resume at the phase indicated by `state.json`. The investigation has no oral history that needs reconstruction.

---

## Citation provenance (orchestrator-wide hard rule)

**No phase of this pipeline — investigator, fact-checker, report-drafting, or any sub-skill — may originate a primary-source citation from semantic memory.** Every UUID, every URL, every court docket caption, every direct quote MUST be copied verbatim from a file written by an earlier phase or by an explicit web fetch.

This is the single most common way investigative-journalism submissions get killed: a draft that "looks right" but contains URLs that 404 or UUIDs that resolve to the wrong filing under adversarial editorial review. LLM-generated citations are guesses formatted to look like sources. They are not sources.

### The four classes of citation drift, and how each phase prevents them

| Drift class | Where it happens | Prevention |
|---|---|---|
| **Hallucinated URL** ("nytimes.com/2026/05/18/business/<plausible-slug>") | P3 investigator inventing a URL that "sounds right"; P5 synthesis re-deriving a URL from headline | Every URL must come from `firecrawl scrape` output, not from memory. The investigator agent records `urls_accessed` in `investigation-log.json`; P5 reads from there. |
| **Wrong filing UUID** ("3a6e17c0-... is the Ant Group filing" → actually Posco America) | P3 investigator picking a plausible-looking UUID from a search-results page without verifying client name; P5 re-deriving a UUID from prose | Every LDA UUID must be present in an evidence card (`case/cards/senate_filing_<UUID>.md`) OR in a Spotlight-archived scrape (`case-trace/spotlight/results/*/research/*.md`). |
| **Wrong-person attribution** ("Stephen Pomper" at Akin Gump → actual partner is Brian Pomper) | P5 synthesis "remembering" a name and formatting a URL from it | Every named person must be quoted from primary-source text (an actual LDA filing, an actual firm bio page, an actual court docket). If the name only appears in your reasoning, not in an archived file, do not cite it. |
| **Stale archive snapshot** (Wayback URL no longer resolves; original page moved) | Any phase that captures a `web.archive.org/web/<ts>/<URL>` link without verifying it later | Always also capture the canonical (non-archive) URL. Prefer the canonical URL in citations; reference the local archive file by relative path. |

### The closure script (every phase must pass it)

Before any phase declares completion, run:

```bash
# Extract every UUID and external URL from this phase's outputs
grep -ohE '[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}|https?://[^[:space:])"]+' \
  <phase-output-files> | sort -u > /tmp/phase-citations.txt

# Confirm each appears in a ground-truth file
while read -r token; do
  if ! grep -rlq -- "$token" case/cards/ case-trace/spotlight/results/ case-trace/data-detective/external/ case-trace/data-detective/anomalies/ case-trace/data-detective/data/ 2>/dev/null; then
    echo "ORPHAN: $token"
  fi
done < /tmp/phase-citations.txt
```

An orphan citation is a phase bug. Resolve before advancing — either by fetching the source (firecrawl into `external/`) or by removing the claim from the output. The `report-drafting` sub-skill ships the canonical implementation; other phases should call it identically.

### Audit breadcrumbs

When a later phase catches and corrects an earlier-phase citation error, leave the breadcrumb in the corrected file:

```
"description": "<corrected claim>. Previous version of this entry cited <wrong-token> in error — that resolves to <what-it-actually-is>. Citation corrected against <ground-truth-file>."
```

The case-trace's defensibility is not "we never made mistakes" — it's "we caught and corrected the ones we made, with the audit trail in the artifact."

---

## Anti-patterns (the orchestrator enforces these)

- **No claim without a sourced evidence card.** Gate readiness check will bounce these.
- **No numeric claim without a SQL hash.** Provenance JSON next to each query is the audit ledger.
- **No naive RAG over raw filings.** The query layer is the only path the investigator should use during exploration.
- **No fuzzy entity matching where bridge keys exist.** The resolver's three-pass enforces this.
- **No skipping the adversarial fact-checker.** Phase 3 step 3 is mandatory before Gate 1.
- **No undated transitions.** Every gate appends a date-stamped event to investigation-log.json.
- **No citation that didn't exist before this phase started.** See "Citation provenance" above — closure script is mandatory before declaring a phase complete.
- **No novelty inflation.** If a finding's core claim was previously published by a mainstream outlet (NYT/ProPublica/WaPo/Reuters), the finding gets `.pill-connected` not `.pill-novel`; the novel sub-element (typically a cross-corpus join) must be called out explicitly in a "Novelty" paragraph.

---

## References

- [methodology.md](references/methodology.md) — full phase-by-phase playbook (deep dive)
- `references/evidence-map-format.md` (package root) — claim → cards → records schema
- [Agent Skills specification](https://agentskills.io/specification.md)

## Sub-skills (sibling directories)

- [ingest](../ingest/SKILL.md)
- [resolve](../resolve/SKILL.md)
- [detect](../detect/SKILL.md)
- [evidence-cards](../evidence-cards/SKILL.md)
- [external-data](../external-data/SKILL.md)
- [similarity-search](../similarity-search/SKILL.md)
- [spotlight-handoff](../spotlight-handoff/SKILL.md)
- [vault-ingest](../vault-ingest/SKILL.md)
