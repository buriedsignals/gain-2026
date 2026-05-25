# Interaction Traces — manifest

This directory contains the full Claude Code session logs that produced the findings reported in [`../findings-report.md`](../findings-report.md) and [`../report.html`](../report.html), plus the post-publication verification + correction pass that hardened the citations.

For the human-readable narrative — phase order, human-judgment moments, skill-invocation log — see [`traces.md`](traces.md).

## Files

| File | Date | Size | Scope |
|---|---|---|---|
| [`01-data-detective-investigation-20260522.jsonl`](01-data-detective-investigation-20260522.jsonl) | 2026-05-22 → 2026-05-23 | 9.7M | **Main investigation.** Brief, methodology, tooling build, full corpus ingest, all 12 detectors, evidence cards, external-data pulls, Gate 1, P5 synthesis, OS-001..OS-006 spotlight-handoff briefs, ingest planning. Produced findings C-001 through C-009. |
| [`02-verification-and-corrections-20260525.jsonl`](02-verification-and-corrections-20260525.jsonl) | 2026-05-25 | 1.7M | **Post-publication verification + correction.** Independent re-verification of every citation against live web sources via firecrawl; identification of 8 P5 citation drifts (wrong UUIDs, hallucinated URL, wrong-person attribution); corrections applied; new Citation Provenance discipline added to `data-detective/SKILL.md` and `report-drafting/SKILL.md`; reproducible closure script that detects orphan citations. |
| [`03-verification-subagents/`](03-verification-subagents/) | 2026-05-25 | ~1.0M total | **Five parallel `spotlight:fact-checker` subagent traces** spawned during the verification pass. Each independently re-verified one cluster of findings using firecrawl against live primary sources. |

### Subagent traces (per-finding fact-check)

| File | Findings verified | Tools used | Key result |
|---|---|---|---|
| [`verify-c001-c005-loc-nation-fec.jsonl`](03-verification-subagents/verify-c001-c005-loc-nation-fec.jsonl) | **C-001** (LOC Nation $180M LDA), **C-005** (FEC reclassification + Dukes 11 NDTX cases) | firecrawl scrape × ~30 (LDA filings, CourtListener, FEC, OpenSecrets, govinfo PACER PDFs, OpenLobby, LegiStorm, stateoflocnation.com); cross-checked all 12 claims; "Dukes v. Roman Empire" docket caption literally real per govinfo | Clean. Two minor wording corrections applied: $180M→$80M/$160M aggregation framing already disclosed; "on the ballot" → "registered write-in candidate." |
| [`verify-c002-anchor-arrow.jsonl`](03-verification-subagents/verify-c002-anchor-arrow.jsonl) | **C-002** (Anchor & Arrow → 13 AI-defense clients → $35.9M DoD contracts) | firecrawl scrape (LDA filings, GovTribe, The Hill, Polaris US, LegiStorm, OpenSecrets) | Surfaced two wrong UUIDs in `findings-report.md` ("Saronic Q3 2025" pointing to Overland AI Q1 2026; "Epirus" pointing to American Phalanx) and Noonan title misattribution (EVP at Strategies, not President of LLC during 2024-25). $22M Apex STRATFI award FA880925CB005 confirmed real but "after registration" temporal causation could not be supported. All corrected. |
| [`verify-c003-c006-akin-gump.jsonl`](03-verification-subagents/verify-c003-c006-akin-gump.jsonl) | **C-003** (FARA gap aggregate), **C-006** (Akin Gump 4-engagement foreign cluster) | firecrawl scrape (House LDA, Senate LDA, NYT, DOJ EDNY, Reuters, BIS Entity List, govinfo, FARA eFile) | Surfaced critical citation forgery risk: Senate LDA UUID `3a6e17c0-...` cited as the Akin Gump×Ant Group filing actually resolves to a Posco America filing; NYT URL path `/2026/05/18/business/adani-doj-prosecution.html` returns 404 (real article at `/nyregion/gautam-adani-indictment-trump.html`); "day after Nov 20 2024 indictment" overstates (LDA registration is Dec 31, 2024 = six weeks after). All three corrected. Substance preserved — Ant Group filing IS real at the correct UUID `a4411100-...`; Adani indictment-drop story IS at the NYT but at a different path; the engagement IS related to the indictment, just not "day after." |
| [`verify-c004-brownstein-sullivan-warren.jsonl`](03-verification-subagents/verify-c004-brownstein-sullivan-warren.jsonl) | **C-004** (Brownstein Hyatt Senate Finance Committee alumni cluster) | firecrawl scrape (BHFS bios, OpenSecrets revolving-door, Capitol Tax Partners, senate.gov press releases, Congress.gov bill pages) | Clean. Sullivan + Warren co-lobby Apollo verified on UUID `c058d5af-...` Q1 2026 BHFS filing. Warren-Markey Aug 8 2024 Apollo/Steward press release verified verbatim. Warren → Capitol Tax Partners May 4 2026 transition verified including the BHFS bio 404 and the Capitol Tax team-page-not-yet-updated detail. |
| [`verify-c007-c008-c009-tdy-ballard-lazarski.jsonl`](03-verification-subagents/verify-c007-c008-c009-tdy-ballard-lazarski.jsonl) | **C-007** (TDY Medicare Part D), **C-008** (Reynolds-MAGA-FDA), **C-009** (Lazarski cross-committee Apollo) | firecrawl scrape (ProPublica 2009, Law360, FGS Global, NYT Vogel/Jewett, FEC, Ballard Partners, Cornerstone, OpenSecrets, Warren campaign platform) | C-008 (Reynolds → MAGA → FDA) rock-solid via NYT/Yahoo/Bloomberg/KFF Health News (this is amplification of NYT reporting — explicit novelty caveat added). C-007 surfaced one overstatement: Bass Berry & Sims were framed as Vertex's counsel but Law360 only quoted Jennifer Michael of Bass Berry as a third-party commentator; corrected, and the actual docket is Case 1:24-cv-02046 D.D.C. C-009 Lazarski portfolio + Warren attacks all verified. |

## Reading the JSONL

These are raw Claude Code transcript files — one JSON object per line, recording every user message, assistant message, tool call, tool result, and system event. To inspect interactively:

```bash
# Count message types
jq -r '.type' interaction-traces/01-data-detective-investigation-20260522.jsonl | sort | uniq -c

# Pull just the user-visible messages
jq -r 'select(.type == "user") | .message.content' interaction-traces/01-data-detective-investigation-20260522.jsonl | head -40

# Inspect tool calls
jq -r 'select(.type == "assistant") | .message.content[]? | select(.type == "tool_use") | "\(.name)\t\(.input | tostring | .[0:120])"' interaction-traces/01-data-detective-investigation-20260522.jsonl | head -30
```

## Connecting traces to findings

| Finding | Primary trace | Verification trace |
|---|---|---|
| C-001 LOC Nation $180M LDA | `01-...investigation-20260522.jsonl` | `03-verification-subagents/verify-c001-c005-loc-nation-fec.jsonl` |
| C-002 Anchor & Arrow 13 AI-defense clients | `01-...investigation-20260522.jsonl` | `03-verification-subagents/verify-c002-anchor-arrow.jsonl` |
| C-003 FARA gap (682 names) | `01-...investigation-20260522.jsonl` | `03-verification-subagents/verify-c003-c006-akin-gump.jsonl` |
| C-004 Brownstein Hyatt Senate Finance cluster | `01-...investigation-20260522.jsonl` | `03-verification-subagents/verify-c004-brownstein-sullivan-warren.jsonl` |
| C-005 FEC reclassification + Dukes | `01-...investigation-20260522.jsonl` (OS-001 handoff section) | `03-verification-subagents/verify-c001-c005-loc-nation-fec.jsonl` |
| C-006 Akin Gump foreign cluster | `01-...investigation-20260522.jsonl` (OS-002 handoff section) | `03-verification-subagents/verify-c003-c006-akin-gump.jsonl` |
| C-007 TDY Part D architects | `01-...investigation-20260522.jsonl` (OS-005 handoff section) | `03-verification-subagents/verify-c007-c008-c009-tdy-ballard-lazarski.jsonl` |
| C-008 Reynolds → MAGA → FDA | `01-...investigation-20260522.jsonl` (OS-003 handoff section) | `03-verification-subagents/verify-c007-c008-c009-tdy-ballard-lazarski.jsonl` |
| C-009 Lazarski cross-committee Apollo | `01-...investigation-20260522.jsonl` (OS-004 handoff section) | `03-verification-subagents/verify-c007-c008-c009-tdy-ballard-lazarski.jsonl` |

`02-verification-and-corrections-20260525.jsonl` is the host-session trace that orchestrated the five subagents in parallel, synthesized their reports, applied corrections to the deliverable files (`findings-report.md`, `report.html`, `evidence-map.json`, the case-trace JSONs), upgraded the skills with the new Citation Provenance discipline, and committed + pushed to `github.com/buriedsignals/gain-2026` and `github.com/buriedsignals/spotlight`.

## Human judgment moments

See [`traces.md`](traces.md) for the four documented human-judgment moments during the main run (strategic skill choice, portability clarification, investigation angle, findings framing). The verification session added one additional moment:

- **2026-05-25 — pushback on apparent hallucination findings.** When the verification host session reported two "likely hallucinated" citations (the Ant Group UUID and the NYT URL), the user pushed back: "Are you sure these are hallucinated? Just make sure the evidence trace isn't missing. We used the spotlight skill with browser-harness to source external information not available in the data in the directory." The host session then re-checked against the local Spotlight evidence files and confirmed: the substance was real (Spotlight scraped both correctly) but the data-detective P5 synthesis layer had drifted from the Spotlight-confirmed citations. This intervention prevented a false "hallucination" verdict and located the actual class of bug: P5 re-deriving citations from prose instead of passing through ground-truth files. The Citation Provenance discipline was written to prevent this recurrence.
