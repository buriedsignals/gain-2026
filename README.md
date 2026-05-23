# GAIN 2026 — Buried Signals

**Northwestern University · GAIN Agentic AI Investigative Journalism Challenge.**

A single Agent Skill orchestrates a full investigation against a million U.S. lobbying records and produces nine verified findings, every claim grounded in a primary source.

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

Nine verified findings. Eight high-confidence, one medium. Six were promoted to data-detective from formal Spotlight handoffs (OS-001 through OS-006); five surfaced material new evidence.

- **C-001** — A self-styled "sovereign government" filed $180M of LDA records via Rev. Dr. Christina Loren Clement in 2024-2025
- **C-002** — Polaris Government Strategies (HQMC OLA founders) won a $22M Apex STRATFI DoD award
- **C-003** — Akin Gump's foreign-client engagements appear to evade FARA at the engagement level
- **C-004** — Brownstein + Cornerstone double-team Apollo; the same senator (Warren) attacks from both committee positions
- **C-005** — FEC reclassified Clement's $50M LDA filing as "pending HR 40 reimbursement"; Quinnipiac Prof. John Martin on record
- **C-006** — Akin Gump retained Adani the day after the EDNY indictment; NYT 5/18/2026 reports DOJ moving to drop the case
- **C-007** — Vertex Pharmaceuticals (TDY client) sues HHS-OIG; TDY founders were Part D architects at HHS
- **C-008** — $5M Reynolds → MAGA Inc → FDA flavored-vape reversal timeline, via McFaul/Ballard
- **C-009** — Lazarski (Cornerstone) extends C-004's pattern to Senate Armed Services

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

lda.senate.gov · FARA bulk (OpenSanctions DOJ mirror) · USAspending.gov · Congress.gov / unitedstates/congress-legislators · FEC docquery · OpenSecrets · LegiStorm · CourtListener · PacerMonitor · Delaware iCIS · Florida Sunbiz · NYT · ProPublica · Law360 · Boston Globe · The Hill

### Interaction traces

The human-judgment moments in the run (brief approval, methodology approval, Gate 1, finishing-path choice, OSINT lead curation) are documented in [`interaction-traces/`](interaction-traces/).
