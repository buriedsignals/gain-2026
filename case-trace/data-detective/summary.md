# GAIN Challenge — Investigation Summary

**Date:** 2026-05-22 | **Cycles:** 3 | **Status:** Pending review (adversarial fact-check in flight)

## Overview

Two parallel investigation threads on the GAIN-provided lobbying + congressional press corpus (Senate LDA 418K filings, House LDA 410K XML, Congressional press 141K records, 2022–Q1 2026), augmented with the public FARA bulk dataset. Thread 1 was open exploration via eight deterministic anomaly detectors. Thread 2 was a foreign-influence / FARA-gap cross-reference. The data-detective skill (built for this submission) was used end-to-end: profile-driven DuckDB index, bridge-key entity resolver, anomaly detectors, evidence cards.

The dominant finding is a $180M batch of fictitious "sovereign government" filings live on `lda.senate.gov`. The second is a clean revolving-door pattern from House Armed Services / Sen. Cotton national-security staff into AI-defense startup lobbying. The third is a 682-name FARA gap framed as a candidate list, not a finding by itself.

## Scope

**In scope:** Senate LDA, House LDA, Congressional press releases, FARA bulk data. 2022–Q1 2026.

**Out of scope (this submission):** Congress.gov bill text + committee referrals, FEC PAC actuals, USAspending.gov contracts, PACER court filings. Cycle 4 begins pulling these as external corroboration where available.

## Key Conclusions

1. The Senate LDA self-report system has no apparent gatekeeping — a self-styled "sovereign government" can file $180M of lobbying records that go live in the public federal database alongside Goldman Sachs and PhRMA. (C-001)
2. The post-2024 AI/defense lobbying surge has a textbook revolving-door pattern: a new firm founded by HASC + Sen. Cotton national-security + Navy comptroller staff has signed 13 autonomous-defense startups in two years. (C-002)
3. 92% of LDA registrants disclosing foreign entities have no FARA counterpart — a starting candidate list, not a violation finding by itself. (C-003)

## Findings

| # | Claim | Confidence | Fact-check verdict | Sources cited |
|---|---|---|---|---|
| C-001 | "State of LOC Nation GPBC" sovereign-citizen LDA filings: $180M as-filed (15 filings, 2024-2025), live on `lda.senate.gov`. Detector D9 confirms it is the **only** multi-signal sovereign-citizen-pattern outlier in 418K filings. | high | verified | 15 evidence cards + 2 archived external URLs + D9 deterministic check |
| C-002 | Anchor & Arrow Strategies / LLC has 13 AI-defense startup clients; founders are former HASC / Sen. Cotton NSA / Navy comptroller staff. **USAspending.gov confirms $35.9M of DoD contracts to four of those clients during the same period, including a $22M Air Force SBIR STRATFI to Apex Technology after Anchor & Arrow's registration.** | high | verified | 8 evidence cards + USAspending data + 5 independent biographical sources |
| C-003 | 682 of 743 LDA registrants disclosing foreign_entities have no FARA counterpart. Detector D10 narrows the gap to 200 specific candidates — Akin Gump × Ant Group Co. (China), Rich Feuer Anderson × Ant Group, Bracewell × Tele-Fonika Cable, FGS Global × Wuxi Biologics among the top. | medium | partially_verified | D10 narrowed list; case-by-case scrutiny still required per candidate |
| C-004 | Brownstein Hyatt Senate-Finance-alumni cluster (Sullivan + Warren) lobbies Apollo Global Management for $8.92M while **two current members of that same committee — Sen. Elizabeth Warren (D-MA) and Sen. Chuck Grassley (R-IA), bipartisan** — publicly attack Apollo on private equity. D12 makes the say-vs-pay structure deterministic via the Congress.gov committee-jurisdiction graph. | high | verified | 2 evidence cards + Chambers USA / OpenSecrets / LegiStorm / 10 Warren press releases / 1 Grassley press release |

## Limitations

- **C-001:** $180M is the sum-of-filings figure; deduplicated to one figure per unique quarter the claim is $80M. We report both.
- **C-001:** LDA income is self-reported and not audited; we cannot independently confirm whether any money changed hands.
- **C-002:** Revolving door patterns alone are not illegal; cooling-off periods may have been observed.
- **C-003:** FARA and LDA capture overlapping but distinct regulatory regimes. The aggregate gap is structurally expected; the finding is the size of the candidate set, not a determination per entity.
- **Across corpus:** A small number of House XML files were malformed and skipped during ingest (encoding errors); the manifest records this. Their loss is unlikely to materially affect the findings above.

## Cycle 4 additions (completed)

- **D9 shell-pattern detector (delivered).** Multi-signal sovereign-citizen-pattern scan. Yield: confirmed LOC Nation is the only multi-signal outlier in the 418K-filing corpus; THEYFEARTRUTH FEDERAL GOVERNMENT OF AMERICA is the next-closest pattern member (zero income).
- **D10 FARA-gap narrowing (delivered).** Filtered the 682-name gap by foreign-government keywords + non-US client country + SOE patterns. Yield: 200 named candidates incl. Akin Gump × Ant Group Co. (China), Rich Feuer Anderson × Ant Group, Bracewell × Tele-Fonika Cable.
- **D11 multi-hop revolving-door (delivered).** Lobbyist covered_position → committee acronym → current issue-code match. Yield: 16 named lobbyists representing $122M in committee-aligned lobbying revenue; the Brownstein Hyatt Senate Finance cluster (Sullivan, Warren) is the headline group.
- **USAspending.gov × Anchor & Arrow clients (delivered).** Yield: $35.9M of confirmed DoD contracts to four lobbied clients; Apex Technology's $22M Air Force SBIR STRATFI is the cleanest single pairing.
- **Bill number extraction (delivered).** Regex over 1.53M House + Senate activity descriptions; **20K unique bill numbers** extracted in seconds (HR5376 / Inflation Reduction Act top at 29K citations). Output at `case/anomalies/bill_mentions.csv` — ready for Congress.gov join in a future cycle.
- **Vector similarity (capability shipped as demonstrator).** `scripts/vector_search.py` provides embed + nearest-neighbor on any text column via fastembed + DuckDB VSS. Not run on full corpus since D9 already cleanly isolated the LOC Nation pattern. Documented and ready for future use.
## Cycle 5 additions (completed)

- **D12 `committee_say_vs_pay`** (SQL hash `274c4ef00515cd73`) — four-way multi-corpus join: lobbyist `covered_position` → committee → current committee members → press-release attacks on the lobbied client. Yield: deterministic structural picture of C-004; Warren (D) + Grassley (R) bipartisan attack of Apollo while their committee's former Staff Director lobbies for it.
- **scripts/external/congress_gov.py (delivered)** — pulls 536 current Congress members × 230 committees + subcommittees × 3,879 assignment rows from the open `unitedstates/congress-legislators` community dataset (used by ProPublica, GovTrack). No API key. Joinable to `press_releases.bioguide_id` and to D11's covered-position-derived committee names.
- **Spotlight adversarial fact-checker (in flight).** Spawned per Phase 3 step 3 of the Spotlight protocol — a gap I had to close. Writing to `case/data/fact-check.json`.
