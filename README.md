# GAIN Challenge submission — Buried Signals

**Northwestern University · GAIN Agentic AI Investigative Journalism Challenge · 2026.**

This repository is the frozen submission. Tag `final-submission` marks the exact state evaluated by the jury. Future evolution of the underlying `data-detective` skill happens in `github.com/buriedsignals/skills`, not here.

**Quick links:**
- Open `report.html` in a browser for the public-facing findings report (or read it at <https://buriedsignals.com/gain-2026/report.html>).
- Read `findings-report.md` for the narrative audit document.
- Read `data-detective/SKILL.md` for the orchestrator skill that produced the report.
- Read the bottom of this file for replication instructions.

---

## Submission contents

```
gain-2026/
├── README.md                              (this file)
├── report.html                            visual findings report (open in browser)
├── findings-report.md                     4 findings with full chain-of-evidence
├── evidence-map.json                      machine-readable claim → cards → records → query hashes
│
│  ── Primary deliverable — ten Agent Skills (orchestrator + nine sub-skills) ──
├── data-detective/                        ★ orchestrator (Spotlight-pattern phase orchestration)
│   ├── SKILL.md                           workflow + gates + agent routing table
│   ├── run_pipeline.sh                    end-to-end driver
│   └── references/                        methodology playbook + evidence-map format
├── ingest/                 P1: corpus → DuckDB ETL (profile-driven)
│   ├── SKILL.md
│   ├── PROFILE-FORMAT.md
│   └── scripts/ingest.py + examples/lda_profile.py
├── resolve/                P2: bridge-key + fuzzy entity resolution
├── detect/                 P3: detector catalog + ad-hoc SQL with SHA provenance
│   ├── SKILL.md
│   ├── references/detectors.md            catalog of D1–D12
│   └── scripts/query.py
├── evidence-cards/         P3/P5: source record → markdown audit card
├── external-data/          P3: FARA, Congress.gov, USAspending pullers
├── similarity-search/      P3 optional: vector NN over text columns
├── report-drafting/                 ★ P5: synthesis — findings-report.md + report.html + evidence-map.json (ships template + design discipline)
├── spotlight-handoff/               ★ P6: handoff to spotlight for external OSINT
├── vault-ingest/           P7: final report → Obsidian (mirrors spotlight:ingest, --sensitive aware)
│
│  ── This investigation's trace (clean data-side / OSINT-side split) ──
├── case-trace/
│   ├── data-detective/                    ALL data-side work
│   │   ├── brief-directions.txt           approved scope
│   │   ├── methodology.json + summary.md  phase plan + Gate-1 artifact
│   │   ├── findings.json                  full claim ledger
│   │   ├── evidence-map.json              claim → cards → query hashes
│   │   ├── investigation-log.json         append-only action log
│   │   ├── manifest.json                  index reproducibility receipt
│   │   ├── data/fact-check.json           adversarial Spotlight fact-checker verdicts
│   │   ├── anomalies/                     14 detector outputs + provenance JSONs
│   │   ├── cards/                         26 evidence cards
│   │   ├── external/                      FARA cache, USAspending, factcheck archives
│   │   ├── entity-resolution-report.md
│   │   └── playbook.md
│   └── spotlight/                         ALL OSINT-side work (passover handoff + Spotlight results)
│       ├── spotlight-handoff.md           ranked passover candidates table
│       ├── briefs/                        one brief per chosen lead (OS-001..OS-006)
│       └── results/                       Spotlight investigator output per lead
│           ├── OS-001-loc-nation-network/     ← running
│           │   ├── data/findings.json
│           │   ├── investigation-log.json
│           │   └── external/                  ← archived web sources
│           ├── OS-002-akin-gump-foreign-cluster/  ← running
│           └── ...
└── interaction-traces/traces.md           session structure + human-judgment moments
```

Each skill directory is a valid Agent Skill (name matches dir, description ≤ 1024 chars, body < 500 lines). The orchestrator references the nine sub-skills at each phase.

## The skill architecture (one-paragraph summary)

**`data-detective`** is a Spotlight-pattern orchestrator for **structured-records investigations** — lobbying filings, FEC reports, court records, IRS 990s, anything tabular or nested where the story is a relationship. The orchestrator runs phases (brief → methodology → execution cycles → adversarial fact-check → gates → synthesis → spotlight-handoff → vault-ingestion), invoking nine sibling sub-skills for the actual work and reusing the existing `spotlight:investigator` (PLANNING + EXECUTION) and `spotlight:fact-checker` (adversarial) subagents. ETL, entity resolution, anomaly detection, and aggregation all run on deterministic Python + DuckDB; the LLM reasons over already-filtered candidates. Every finding ties to a specific source record via an evidence card, every numeric claim cites a SQL query by SHA-16 hash, every external source is archived. The **spotlight-handoff** sub-skill is the cycle's innovation: data-side findings hand off to Spotlight for external OSINT amplification, composing the two skills' strengths.

## Findings

| ID | Claim (one sentence) | Confidence | FC verdict | Category | Skill invocations |
|---|---|---|---|---|---|
| **C-001** | A self-styled "sovereign government" (State of LOC Nation GPBC) filed $180M of LDA records in 2024-2025 through Rev. Dr. Christina Loren Clement; D9 confirms it is the only multi-signal sovereign-citizen pattern in 418K filings. Court case verified on PacerMonitor + CourtListener. | high | verified | data_quality | detect D5/D9 → drill SQL → evidence_card |
| **C-002** | Anchor & Arrow has registered 13 AI-defense startups in 2 years; founders are former HASC / Sen. Cotton NSA / Navy comptroller staff. **USAspending: $35.9M DoD contracts to 4 clients incl. $22M Air Force STRATFI to Apex Technology.** | high | verified | revolving_door | detect D8 → drill SQL → external/usaspending → evidence_card |
| **C-003** | 682 of 743 LDA registrants disclosing foreign entities have no FARA counterpart. D10 narrows the gap to 200 named candidates incl. Akin Gump × Ant Group Co. (China). | medium | partially_verified | foreign_influence | external/fara + detect D10 |
| **C-004** | Brownstein Hyatt's Sen-Finance-alumni cluster (Sullivan + Warren) lobbies Apollo for $8.92M while **two current Sen. Finance Cmte members — Warren (D) and Grassley (R), bipartisan** — publicly attack Apollo. D12 makes the say-vs-pay structure deterministic via the Congress.gov committee graph. | high | verified | revolving_door + cross-corpus | detect D11+D12 → external/congress_gov → evidence_card |

Full narrative with chain of evidence: `findings-report.md`. Machine-readable: `evidence-map.json`. Adversarial verdicts: `case-trace/fact-check.json` with 8 archived sources at `case-trace/external/factcheck/`.

## Spotlight handoff (Phase 6) — passover to external OSINT

After Gate 1 approval, the `spotlight-handoff` sub-skill ranked 10 candidates for handoff to Spotlight for external OSINT amplification. Tier 1 + Tier 2 are in flight or queued:

| Lead | Topic | Status |
|---|---|---|
| **OS-001** | THEYFEARTRUTH + "Rico Dukes" — second sovereign-citizen filer beyond LOC Nation | spotlight:investigator running |
| **OS-002** | Akin Gump's foreign-tied client portfolio — Ant Group, TP-Link, Adani, United Solar Polysilicon | spotlight:investigator running |
| **OS-003** | Daniel McFaul + Ballard Partners — former Matt Gaetz CoS portfolio | Brief ready |
| **OS-004** | D11 second-tier revolving door — Richards/Lazarski/Young/Teague/O'Neill ($50M+ each) | Brief ready |
| **OS-005** | Tarplin Downs & Young — healthcare boutique with HHS leadership pedigree | Brief ready |
| **OS-006** | Mark Warren → Capitol Tax Partners (May 2026 move) | Brief ready |

Per-candidate Spotlight briefs at `case-trace/spotlight/briefs/`. Spotlight investigator output goes to `case-trace/spotlight/results/OS-NNN/` and is then optionally promoted to a new data-detective finding (C-005, C-006...) when OSINT amplification adds material new evidence.

## Outside data used

| Source | URL | Purpose | Local archive |
|---|---|---|---|
| FARA bulk via OpenSanctions DOJ mirror | https://data.opensanctions.org/datasets/latest/us_fara_filings/ | Cross-reference LDA `foreign_entities[]` against FARA (C-003, D10) | `case-trace/fara/cache/` |
| USAspending.gov DoD contract awards API | https://api.usaspending.gov/api/v2/search/spending_by_award/ | DoD contracts for Anchor & Arrow clients (C-002) | `case-trace/external/usaspending_aa_clients.json` |
| Congress.gov committee jurisdiction graph via `unitedstates/congress-legislators` | https://raw.githubusercontent.com/unitedstates/congress-legislators/main | 536 members × 230 committees × 3,879 assignments; enables D12 multi-corpus join (C-004) | Loaded into the index via `external/congress_gov.py` |
| CourtListener + PacerMonitor federal court records | https://www.courtlistener.com / https://www.pacermonitor.com | Verification of CLEMENT v. GARLAND 1:24-cv-00479 (DDC) cited in LOC Nation LDA filings (C-001) | Linked from findings + archived in `case-trace/external/factcheck/pacermonitor-clement-garland-20260522.md` |
| Live LDA filing pages | https://lda.senate.gov/filings/public/filing/{uuid}/print/ | Archive evidence for cited filings | `case-trace/external/lda_*.md` |
| State of LOC Nation entity website | https://stateoflocnation.com/about | Independent corroboration of C-001 entity | `case-trace/external/stateoflocnation_about.md` |
| The Hill, Polaris National Security, LinkedIn, Legistorm, Leatherneck Magazine | (various) | Biographical verification (C-002 + C-004) | Linked from `findings-report.md`; key ones archived in `factcheck/` |
| Brownstein Hyatt firm bios, OpenSecrets revolving-door records, Chambers USA, Boston Globe/Herald | (various) | C-004 verification (Sullivan + Warren) | Linked from findings; key ones archived in `factcheck/` |

No confidential or sensitive data was used. All sources are public records or public-web content.

## Reproducibility

To reproduce on a fresh machine:

```bash
# Prereqs: Python 3.11+, uv (https://docs.astral.sh/uv/)

# Single-command end-to-end pipeline
./data-detective/run_pipeline.sh \
  --profile  ingest/scripts/examples/lda_profile.py \
  --data-root /path/to/gain-corpus \
  --case     case-trace

# Or by phase:
uv run ingest/scripts/ingest.py \
  --profile ingest/scripts/examples/lda_profile.py \
  --data-root /path/to/gain-corpus \
  --db case-trace/index.duckdb \
  --manifest case-trace/manifest.json

uv run resolve/scripts/resolve_entities.py --db case-trace/index.duckdb --out case-trace/
uv run external-data/scripts/fara.py --db case-trace/index.duckdb --cache case-trace/fara/cache
uv run external-data/scripts/congress_gov.py --db case-trace/index.duckdb
uv run detect/scripts/query.py --db case-trace/index.duckdb --detector all --out case-trace/anomalies
# (includes D1–D12. D9 = shell-pattern; D10 = FARA-gap narrowing; D11 = multi-hop revolving door; D12 = committee say-vs-pay)

# Generate evidence cards for cited filings
uv run evidence-cards/scripts/evidence_card.py --db case-trace/index.duckdb --source senate_filing \
  --from-csv case-trace/loc_nation_filing_uuids.csv --id-column filing_uuid --out case-trace/cards

# Optional: vector similarity (for future investigations; not required to reproduce these findings)
# uv run similarity-search/scripts/vector_search.py --db case-trace/index.duckdb \
#     --embed --table senate_lobbying_activities --text-column description --id-column activity_id
```

**Reproducibility receipt.** `case-trace/manifest.json` records per-source-file SHA-256 hashes. Any drift between the evaluator's corpus and ours surfaces as a hash mismatch.

**Expected timing on a 2023-era Apple Silicon laptop:** ingest ~3 min, entity resolution ~30s, FARA pull <30s, Congress.gov pull <30s, all detectors <5s combined. The LLM is not in the hot path.

## Conflicts of interest

None. Tom Vaillant (Buried Signals) has no relationship to any registrant, client, member, or lobbyist named above.

## Legal-violation flags

- **C-001 (LOC Nation):** False statements in federal filings (**18 U.S.C. § 1001**) and Lobbying Disclosure Act enforcement (**2 U.S.C. § 1605**) are potentially implicated. The fact-checker confirmed the filings carry their own disclaimer that the $20M is "pending HR 40 research reimbursement... not a federal payment." Flagged for editorial discretion; no determination of intent made.
- **C-002 (Anchor & Arrow), C-003 (FARA gap), C-004 (Brownstein):** No legal violation indicated. Patterns are legal but newsworthy.

## Validation

The skills conform to the [Agent Skills specification](https://agentskills.io/specification.md). To validate locally:

```bash
# Per-skill validation (manual)
for sk in data-detective*/; do
  python3 -c "
import re, yaml
c = open('$sk/SKILL.md').read()
fm = re.match(r'---\n(.*?)\n---', c, re.S)
m = yaml.safe_load(fm.group(1))
print(f'  {m[\"name\"]:42s} desc={len(m[\"description\"])}  body={c.count(chr(10))} lines')
"
done

# Per the reference library (if installed):
# skills-ref validate data-detective/
# (and each sibling sub-skill)
```

All 10 skills validate (orchestrator at 970 description chars, ~400 body lines; sub-skills at 593-1019 description chars, 58-176 body lines).
