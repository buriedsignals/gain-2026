---
name: report-drafting
description: "Phase 5 synthesis sub-skill for data-detective — draft the journalist-grade deliverables editors actually read: findings-report.md (audit narrative), report.html (public-facing artifact, built from the report-template.html skeleton), and evidence-map.json (machine-readable ledger), with per-finding replication paths + sources strips, confidence/novelty pills, phase-by-phase methodology, and a hard citation-provenance rule with closure script. Use at Phase 5 after Gate 1, before Phase 6 spotlight-handoff. Triggers on draft the report, build the HTML report, journalist-grade output, synthesis phase, findings report, evidence map."
license: MIT
metadata:
  type: orchestration-subskill
  parent: data-detective
  phase: 5
---

# report-drafting — Phase 5 synthesis

You are at Phase 5. Gate 1 has approved verified findings. Ship the three deliverables editors actually read, building the HTML **from the template, not from scratch**.

**This skill is a workflow plus a set of references you load ON DEMAND** — read each `references/*.md` only when you reach the step that needs it; do NOT read them all up front. That keeps working context small during the most context-heavy, drift-prone phase.

## Deliverables (all three required)

| File | Audience | What it is |
|---|---|---|
| `case/findings-report.md` | editor / fact-checker | narrative audit, one section per finding — the authoritative claim-by-claim record |
| `case/report.html` | publication / reader | designed journalism artifact, built from `references/report-template.html` |
| `case/evidence-map.json` | audit / replication | machine-readable ledger: claim → cards → query hashes → URLs (format doc: `references/evidence-map-format.md` at the data-detective **package root**, not in this skill dir) |

## Workflow (open the referenced file when you reach that step)

1. Copy `references/report-template.html` → `case/report.html`. Fill header (title, deck, byline, lede) + the TL;DR table from `findings.json`.
2. **Before drafting any finding, build its citation manifest and obey the citation rule** → read **`references/citation-discipline.md`** (CRITICAL: the synthesis layer must NEVER originate a UUID/URL/quote — every one traces to a ground-truth file; write each finding's allowed set to `/tmp/c-NNN-citations.txt`; attribute at the filing level, not the aggregator-rollup level; timing from `effective_date` fields; litigation as posture, not event).
3. For each verified finding: draft the `<section class="finding">` per **`references/finding-structure.md`** (header+pills, deck, body with quoted primary text, mandatory `.path` replication block + `.sources` strip). Style per **`references/design-discipline.md`** (CSS vars, max-widths, pill semantics — don't reinvent).
4. Methodology: one `<div class="phase">` per phase (P0–P7) → **`references/methodology-pattern.md`** (fact-check verdict table INSIDE Phase 3; spotlight-handoff table INSIDE Phase 6; reconcile counts against evidence-map.json).
5. Fill "Open monitoring targets" from `findings.json`'s unresolved-gaps list; footer: conflicts of interest, database attributions.
6. Write `findings-report.md` (narrative, no styling, every claim from the same allowed-set manifest) and `evidence-map.json`.
7. **Run the citation closure script** (in `references/citation-discipline.md`) — every UUID and URL in the deliverables AND summary layers (README, TL;DR) must trace to ground-truth; fix orphans. Run the summary-layer entailment check. Then validate + smoke-test per **`references/html-protocol.md`**.
8. Append `synthesis_complete` + `draft_paths` + `citation_closure_passed` to `investigation-log.json`.

**Whenever you edit `report.html`:** never greedy-regex it → **`references/html-protocol.md`** (anchored `Read`+`Edit` only; a greedy `re.sub` once destroyed a whole report). Review **`references/anti-patterns.md`** if unsure — it now carries the full failure catalog from three verification passes.

## Corrections passes (post-publication)

When a later verification pass amends published artifacts: apply the correction to the finding **body** first, regenerate every summary layer from the corrected body, add an audit breadcrumb at the correction site, append a row to the "Corrections log" at the end of `findings-report.md`, scrape the corrected citation's source into `case-trace/data-detective/external/factcheck/<slug>-<yyyymmdd>.md`, and re-run the closure script.

## Inputs / Outputs

**Reads:** `case/data/{findings,fact-check,investigation-log}.json`, `case/anomalies/*/provenance.json`, `case-trace/spotlight/results/*/`.
**Writes:** `case/findings-report.md`, `case/report.html`, `case/evidence-map.json`.

## References (load on demand — do not preload)

- `references/report-template.html` — the HTML skeleton (step 1)
- `references/citation-discipline.md` — the hard citation rule, manifest build, filing-level attribution, closure + entailment scripts (steps 2, 7) **← highest-stakes**
- `references/finding-structure.md` — per-finding HTML structure + novelty labeling (step 3)
- `references/design-discipline.md` — CSS vars, max-widths, pill semantics (step 3)
- `references/methodology-pattern.md` — the phase-ordered methodology + count reconciliation (step 4)
- `references/html-protocol.md` — safe HTML editing + validation (whenever editing report.html)
- `references/anti-patterns.md` — the learned failure modes, dated by the pass that caught them
