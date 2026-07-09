<div align="center">

# GAIN 2026 — data-detective

### Agentic structured-records journalism · Buried Signals

**Northwestern University · GAIN Agentic AI Investigative Journalism Challenge**

A single Agent Skill orchestrates a full investigation against a million U.S. lobbying records<br>and produces nine verified findings, every claim grounded in a primary source.

[**Findings**](#what-this-run-produced) · [**Report**](report.html) · [**Replication**](#replication) · [**Audit chain**](case-trace/) · [**Interaction traces**](interaction-traces/) · [**Acknowledgments**](#acknowledgments)

![License](https://img.shields.io/badge/license-MIT%20skills%20·%20CC--BY--4.0%20findings-green)
![Findings](https://img.shields.io/badge/findings-9%20verified-6f42c1)
![Corpus](https://img.shields.io/badge/corpus-~1M%20records-blue)
![Skills](https://img.shields.io/badge/agent%20skills-10-orange)
![Detectors](https://img.shields.io/badge/detectors-D1→D12-8b0000)
![Verification](https://img.shields.io/badge/verification-3%20passes%2C%20corrections%20logged-2ea44f)

</div>

---

```
/data-detective
```

That's the launcher. The orchestrator takes the brief, designs a methodology, spawns subagents, invokes nine sub-skills across seven phases, runs an adversarial fact-check, gates on user approval, and produces three deliverables.

- 📄 **Findings report:** [`report.html`](report.html) — public-facing artifact · [`findings-report.md`](findings-report.md) — narrative audit
- 📋 **Audit ledger:** [`evidence-map.json`](evidence-map.json) — every claim → cards → query hashes → URLs
- 🔁 **Full audit chain:** [`case-trace/`](case-trace/) — anomalies, evidence cards, fact-check verdicts, OSINT cycles
- 🌐 **Web landing:** https://buriedsignals.com/gain-2026

---

## The orchestration

The `data-detective` package is one self-contained unit. Mirrors the [Spotlight](https://github.com/buriedsignals/spotlight) layout convention: agents at the package root, all skills as siblings under `skills/` (orchestrator named after the package), references + pipeline driver at the package root.

```
data-detective/                          ← drop this in your agent's skills dir
├── agents/
│   ├── investigator.md                  ← PLANNING + EXECUTION subagent
│   └── fact-checker.md                  ← adversarial verifier subagent
├── skills/                              ← all skills siblings; runtime resolves by bare name
│   ├── data-detective/SKILL.md          ← orchestrator (the launcher)
│   ├── ingest/SKILL.md                  ← P1 · corpus → DuckDB
│   ├── resolve/SKILL.md                 ← P2 · entity resolution
│   ├── detect/SKILL.md                  ← P3 · detector catalog (D1-D12)
│   ├── evidence-cards/SKILL.md          ← P3 + P5 · record → audit card
│   ├── external-data/SKILL.md           ← P3 · FARA, Congress.gov, USAspending
│   ├── similarity-search/SKILL.md       ← P3 · vector NN (optional)
│   ├── report-drafting/SKILL.md         ← P5 · synthesis (direct path)
│   ├── spotlight-handoff/SKILL.md       ← P6 · → Spotlight (handover path)
│   └── vault-ingest/SKILL.md            ← P7 · Obsidian write-back
├── references/                          ← orchestrator-level docs
└── run_pipeline.sh                      ← end-to-end pipeline driver (CWD-agnostic)
```

Every sub-skill validates against agentskills.io spec: name matches dir, description ≤ 1024 chars, body < 500 lines.

### Phase × sub-skill × subagent map

| Phase | What | Sub-skill invoked | Subagent spawned |
|---|---|---|---|
| **P0 preflight** | Skill discovery, profile pick | — | — |
| **P1 ingest** | Profile-driven ETL to DuckDB | `ingest` | — |
| **P2 resolve + methodology** | Bridge-key entity resolution; investigator plans | `resolve` | `investigator` (PLANNING) |
| **P3 cycles + fact-check** | Detectors + drill + external joins + evidence cards + adversarial verification | `detect`, `evidence-cards`, `external-data`, `similarity-search` | `investigator` (EXECUTION), `fact-checker` (adversarial) |
| **P4 Gate 1** | User reviews findings, picks finishing path | — | — |
| **P5 synthesis** *(direct path)* | report.html + findings-report.md + evidence-map.json | `report-drafting` | — |
| **P6 spotlight-handoff** *(handover path)* | Hand chosen leads to Spotlight for OSINT amplification | `spotlight-handoff` | `spotlight:investigator`, `spotlight:fact-checker` (external) |
| **P7 vault-ingest** | Obsidian write-back, `--sensitive` aware | `vault-ingest` | — |

Gate 1 is binary: **direct report** (data-detective drafts the final report) or **spotlight handover** (Spotlight runs its own pipeline and produces the report on its end, in hybrid mode that walks both orchestrators' phases). Both paths converge at P7.

### Composes with Spotlight

`data-detective` reuses Spotlight's orchestration discipline (brief → methodology → cycles → fact-check → gate → ingest) but on a different medium: structured records instead of web OSINT. At Phase 6 handover, the two skills compose — Spotlight's web-side personas pick up where the data-side personas leave off, with the upstream audit chain preserved as context.

---

## What this run produced

Nine verified findings. Eight high-confidence, one medium. Five were promoted to data-detective from the six formal Spotlight handoff cycles (OS-001 through OS-006; OS-006 updated C-004), and five of the handoffs surfaced material new evidence. Corrections passes ran 2026-05-25 and 2026-07-09 — see the Corrections log at the end of [`findings-report.md`](findings-report.md).

- **C-001** — A self-styled "sovereign government" filed $180M of LDA records via Rev. Dr. Christina Loren Clement in 2024-2025
- **C-002** — Anchor & Arrow (HASC / Sen. Cotton / Navy-comptroller alumni) signed 13 AI-defense startups; client Apex Technology won a $22M Air Force STRATFI during the engagement
- **C-003** — 682 LDA registrants disclosing foreign entities have no FARA counterpart; D10 narrows the gap to 200 named candidates
- **C-004** — Brownstein's Senate-Finance alumni lobby Apollo while Warren and Grassley attack it from that committee; Apollo followed Mark Warren to Capitol Tax Partners in June 2026
- **C-005** — The FEC flagged Clement's $50.25M campaign self-loan (RFAI, April 28, 2026) and moved it to its false/fictitious repository; Quinnipiac Prof. John Martin on record
- **C-006** — Akin Gump's Adani retainer is effective the day after the EDNY indictment was unsealed (LD-1 effective 11/21/2024); DOJ's move to drop the case awaits court approval
- **C-007** — Vertex Pharmaceuticals (TDY client) sued HHS-OIG, lost at district court, appeal pending; TDY founders were Part D architects at HHS
- **C-008** — $5M RAI Services → MAGA Inc (C00892471) → FDA flavored-vape guidance timeline, via McFaul/Ballard
- **C-009** — Lazarski (Cornerstone) extends C-004's pattern to Senate Armed Services via Apollo portfolio company Arconic

Full claim-by-claim narrative + replication paths in [`report.html`](report.html).

---

## Replication

```bash
# 1. Clone
git clone https://github.com/buriedsignals/gain-2026.git
cd gain-2026

# 2. Install — copies all 10 skills + 2 agent personas into ~/.claude/
./install.sh

# 3. Place the corpus where the profile expects it
#    (see data-detective/skills/ingest/PROFILE-FORMAT.md).
#    For this run: U.S. Senate LDA JSON 2008-2025, House LDA XML 2008-2025,
#    congressional press release JSONL.

# 4. Launch in a fresh Claude Code session
/data-detective
```

The installer mirrors what Spotlight's marketplace handler does at install time: flat-copies each sub-skill from `data-detective/skills/<name>/` to `~/.claude/skills/<name>/` so the runtime registers each individually, and copies the agent personas to `~/.claude/agents/`. Override destinations with `CLAUDE_SKILLS_DIR=... CLAUDE_AGENTS_DIR=... ./install.sh` for non-Claude-Code harnesses.

The orchestrator handles the rest: preflight, brief, methodology, cycles, Gate 1, finishing path.

---

## Submission details

- **Submitter:** Tom Vaillant · Buried Signals · tom@buriedsignals.com
- **Repository:** https://github.com/buriedsignals/gain-2026 (will be tagged `final-submission` at the submission deadline)
- **License:** MIT (skills) · CC-BY-4.0 (findings + report)
- **Conflicts of interest:** None. No relationship to any registrant, client, member, or lobbyist named in findings.
- **Future development:** This repository is frozen. Productized `data-detective` evolves at [github.com/buriedsignals/skills](https://github.com/buriedsignals/skills).

### Data sources

See [Acknowledgments](#acknowledgments) for the full categorized list of data providers, trackers, and tooling this investigation stands on.

### Interaction traces

The human-judgment moments in the run (brief approval, methodology approval, Gate 1, finishing-path choice, OSINT lead curation, post-publication verification pushback) are documented in [`interaction-traces/`](interaction-traces/) — see [`interaction-traces/README.md`](interaction-traces/README.md) for the manifest mapping each transcript to the findings it produced. The directory contains the full raw Claude Code session transcripts in JSONL form: the main investigation (`01-data-detective-investigation-20260522.jsonl`, 9.7M), the post-publication verification + corrections pass (`02-verification-and-corrections-20260525.jsonl`, 1.7M), and five parallel `spotlight:fact-checker` subagent traces (one per finding cluster).

---

## Acknowledgments

This investigation stands on public-interest data infrastructure and open-source tooling. A genuine thank-you to every provider below — the findings simply would not exist without this work. *(Listing here does not imply affiliation or endorsement; always respect each provider's terms of service.)*

| Category | Projects & services we're grateful to |
|---|---|
| **Challenge & corpus** | [Northwestern University — GAIN](https://generative-ai-newsroom.com/) (Generative AI in the Newsroom) Agentic AI Investigative Journalism Challenge — Senate LDA JSON, House LDA XML, and congressional press-release corpus |
| **Federal primary sources** | [Senate LDA database + REST API](https://lda.senate.gov/) · [House Clerk lobbying disclosures](https://disclosurespreview.house.gov/) · [DOJ FARA eFile](https://efile.fara.gov/) · [FEC / openFEC API](https://api.open.fec.gov/) · [FEC docquery](https://docquery.fec.gov/) · [USAspending.gov API](https://www.usaspending.gov/) · [Congress.gov](https://www.congress.gov/) · [govinfo](https://www.govinfo.gov/) |
| **Open-data mirrors & trackers** | [OpenSanctions](https://www.opensanctions.org/) (DOJ FARA bulk mirror) · [unitedstates/congress-legislators](https://github.com/unitedstates/congress-legislators) · [OpenSecrets](https://www.opensecrets.org/) · [LegiStorm](https://www.legistorm.com/) |
| **Court records** | [Free Law Project — CourtListener / RECAP](https://www.courtlistener.com/) · [PacerMonitor](https://www.pacermonitor.com/) |
| **Corporate registries** | [Delaware iCIS](https://icis.corp.delaware.gov/) · [Florida Sunbiz](https://search.sunbiz.org/) |
| **Journalism cited** | The New York Times · ProPublica · Law360 · The Hill · Boston Globe / Boston Herald · KFF Health News · Politico · Reuters |
| **Tooling & runtime** | [Anthropic — Claude Code](https://claude.com/claude-code) (Agent Skills) · [DuckDB](https://duckdb.org/) · [PyArrow](https://arrow.apache.org/) · [fastembed](https://github.com/qdrant/fastembed) + DuckDB VSS · [Firecrawl](https://firecrawl.dev/) · [Internet Archive Wayback Machine](https://web.archive.org/) · [Astral — uv](https://docs.astral.sh/uv/) · [Spotlight](https://github.com/buriedsignals/spotlight) (Buried Signals) |
