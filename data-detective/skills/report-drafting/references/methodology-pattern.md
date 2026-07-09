# Methodology section pattern (the highest-leverage learning)

The methodology section serves a dual purpose: it documents the skill (the algorithm) AND it logs the actual run. It is NOT a separate generic methodology. It is the audit trail of THIS investigation, in phase order.

Structure: one `<div class="phase">` per executed phase (P0 through P7).

**Critical:** do NOT break the adversarial fact-check verdict table and the spotlight-handoff outcomes table into separate top-level sections — they read out of phase order. Instead:

- Adversarial fact-check verdicts table → INSIDE the Phase 3 `<div class="phase">`.
- Spotlight-handoff outcomes table (briefs OS-001..OS-N, what they did, what they promoted) → INSIDE the Phase 6 `<div class="phase">`.

A reader scrolling the methodology gets the full run in phase order: ingest → resolve → detect+factcheck → gate → synthesize → handoff → vault.

**Consistency rule:** the methodology's counts (detectors run, cycles executed, findings produced) are claims like any other — reconcile them against `evidence-map.json` and the finding sections before shipping. On GAIN-2026, "four findings," "detectors D1–D11," and "two cycles" all survived into a nine-finding, D12, five-cycle report.
