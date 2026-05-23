---
name: spotlight-handoff
description: The handoff phase of a data-detective investigation — translate finalized data-side findings into Spotlight-ready briefs and pass leads to the spotlight orchestrator for external OSINT amplification. Each candidate finding becomes a spotlight-brief.md with named entities, URLs already gathered, what data-detective established (with evidence card refs), and suggested external angles. The skill also generates a spotlight-handoff.md ranking sheet so the user can pick which leads warrant Spotlight's web-based investigation. Use in Phase 6 of a data-detective investigation, after Gate 1 approval. Triggers on prompts mentioning passover, handoff to spotlight, generate OSINT briefs, what should we research externally, or "take these findings and dig deeper online."
license: MIT
metadata:
  parent: data-detective
  step: P6_passover
  pattern: data → web OSINT handoff
  inputs: finalized findings.json + evidence-map.json
  outputs: spotlight-handoff.md (ranking) + spotlight-briefs/*.md (one per chosen lead)
---

# data-detective-passover

The handoff cycle: data-side findings → Spotlight briefs → external OSINT.

## When to use

Called from the `data-detective` orchestrator at Phase 6, after the user approves Gate 1 (`case/summary.md`).

This is the *passover cycle*: data-detective has found anomalies in the corpus and verified them via the adversarial fact-checker. Now we hand off to Spotlight for the external-world OSINT — court records (PACER), corporate filings (Delaware DOC, OpenCorporates), social media, news archives, FOIA traces, business networks.

The combination — **data-side audit trail + Spotlight-side web OSINT** — is richer than either alone.

## Two-step protocol

### Step 1 — Generate the candidates ranking sheet

For each verified finding plus each unchased thread from the detector CSVs, emit a row in `case/spotlight-handoff.md`:

```markdown
# Candidates for Spotlight OSINT amplification
Generated: <ISO timestamp>

| Rank | ID | One-line claim | OSINT yield | Effort | Suggested angle |
|---|---|---|---|---|---|
| 1 | OS-001 | <claim> | high | medium | <angle> |
| 2 | OS-002 | ... | ... | ... | ... |
```

Rank by:
- **OSINT yield**: how much external context would amplify this? (named individuals + corporate connections + political stakes = high)
- **Effort**: how much OSINT work is realistic? (one court case to pull = low; full network mapping = high)
- **Newsworthiness**: how strong is the story if external evidence lands?

Present the table to the user. User picks which to pursue.

### Step 2 — Generate Spotlight briefs for picked candidates

For each candidate the user picks, emit `case/spotlight-briefs/<id>.md`:

```markdown
# Spotlight investigation brief — OS-<NNN>

**Lead.** <one-sentence claim from data-detective>

**Source.** Hand-off from data-detective finding C-<NNN> (see ../findings-report.md for full evidence chain).

**Confidence level (data-side).** verified | partially_verified | medium | high

## Named entities for OSINT

### Priority targets
1. **<Person/Org name>** — <one-line role>. Known so far: <bullets>. Open OSINT questions: <bullets>.
2. ...

### Secondary targets
- <name> — <role>

## URLs already in the case-trace (start here)

- <lda.senate.gov public filing URL>
- <courtlistener URL if relevant>
- <entity-own website if relevant>
- <archived snapshot URLs from case/external/factcheck/>

## What data-detective established

<3-5 bullet summary with evidence-card refs (filing UUIDs / press_ids / FARA registration numbers)>

## What Spotlight should pursue (suggested angles)

- Corporate registrations: <state, search terms>
- Court records: <PACER docket numbers if any> + appeals
- Social media / web: <handles, profile URLs>
- Network mapping: <funded by, board memberships, prior employers>
- FOIA: <agencies that should have records>
- Adjacent press coverage: <topical search terms>

## Out of scope

<things data-detective intentionally did not pursue and Spotlight should not feel obligated to>
```

### Step 3 — Spawn Spotlight on the chosen brief

```
Skill(spotlight) with brief=case/spotlight-briefs/<id>.md
```

Spotlight runs its own preflight (config, search library check), accepts the brief at Phase 1 (skipping the conversational brief stage since the data-detective brief is detailed enough), and proceeds through its own cycles. Its output (web-archived sources, social-media-intelligence outputs, etc.) joins `case/external/spotlight-<id>/` to merge with the data-detective trace.

## Why this works

- **Data-detective is great at structured-records anomaly detection.** It can find that "$180M of LDA filings come from one Delaware shell named after a 'Loc Nation'" in seconds against a 8.6 GB corpus.
- **Spotlight is great at structured external investigation.** It can pull PACER, archive Reddit / Facebook profile pages, map shell-LLC networks via Delaware DOC, and verify against open sanctions lists.
- **Neither alone tells the whole story.** Sullivan lobbying Apollo while Warren attacks Apollo is a data-detective insight; *what Apollo and the people moving between them are doing in the world* is a Spotlight insight.

The passover protocol formalizes the handoff so the work composes cleanly: data-detective's findings become Spotlight's brief at Phase 1.

## Reverse handoff (optional, Phase 7+)

Once Spotlight's external investigation completes, its findings can be brought BACK into data-detective as a new detector seed. Example: Spotlight identifies a new actor name → data-detective greps the corpus for that name → finds N additional filings → loops back through P3.

## Anti-patterns

- **No automatic spawn without user choice.** Always present `spotlight-handoff.md` and let the user pick. Spotlight cycles cost real time/tokens; the user picks which leads to spend on.
- **No briefs without an evidence card link.** Every Spotlight brief must reference at least one data-detective evidence card by ID so the data-side audit trail is preserved.
- **No briefs that re-investigate what data-detective already established.** The brief asks Spotlight to *amplify*, not to re-verify.

## Composes with

- Input ← `data-detective` orchestrator (Phase 5 synthesis output: findings-report.md, evidence-map.json)
- Output → `Skill(spotlight)` with brief
- Reverse output → seeds for next data-detective cycle
