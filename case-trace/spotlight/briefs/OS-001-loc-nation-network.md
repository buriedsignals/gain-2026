# Spotlight investigation brief — OS-001

**Lead.** A second sovereign-citizen-style LDA filing operator — Rico Dukes, filing for an "Independent sovereign government" called THEYFEARTRUTH FEDERAL GOVERNMENT OF AMERICA — appears in the federal lobbying database alongside LOC Nation. Investigate whether Dukes and Christina Loren Clement (LOC Nation operator) are connected, and whether a wider network of similar filers exists.

**Source.** Hand-off from data-detective finding C-001 + cycle-5 D9 shell-pattern detector hit. See `../findings.json` and `../candidates-for-osint.md` (OS-001) for full data-side context.

**Confidence level (data-side).** Verified by adversarial fact-checker. The LDA filings exist verbatim on `lda.senate.gov`. THEYFEARTRUTH is a confirmed second instance of the pattern (zero income reported).

## Named entities for OSINT

### Priority targets

1. **Rico Dukes** — Registered THEYFEARTRUTH FEDERAL GOVERNMENT OF AMERICA in Q2 2025 (filing_uuid `e17ba492-75a0-4b18-b212-8b273ee23f79`).
   - Known so far: name + the entity he filed for; status as `posted_by_name`.
   - Open OSINT questions:
     - Real person? Pseudonym?
     - Other LDA filings or LLC registrations under this name?
     - Social-media / public-web presence?
     - Connection to Christina Clement / LOC Nation?
     - Connection to other sovereign-citizen / Moorish movements?

2. **Christina Loren Clement** — LOC Nation founder, already extensively verified (court case + website + Reddit + executive orders). Known facts:
   - Pro se litigant in *CLEMENT v. GARLAND* 1:24-cv-00479 (DDC); appeal 24-5263 surfaced in PacerMonitor.
   - Self-styled "President of Black USA," "HH Empress Queen," "2024 Presidential Candidate."
   - "Christina Loren Clement LLC" at 8 The Green, Suite A, Dover, DE 19901.
   - Open OSINT questions:
     - Other Delaware LLCs in the same registered-agent cluster?
     - Other federal court filings?
     - Connection to specific reparations / sovereign-citizen organizations?
     - Connection to Rico Dukes?

### Secondary targets

- **8 The Green, Suite A, Dover, DE 19901** — mass-LLC registered-agent address.
- **"Loc Nation Central Bank"** — referenced on stateoflocnation.com as a self-operated subdomain.
- **"SOLN Central Bank.gov"** — separate domain claim per fact-checker.
- **"Clement Dynasty Dynasty Trust"** — entity name surfaced in the court case affidavit PDF.

## URLs already in the case-trace (start here)

- LDA filing (LOC Nation registration): https://lda.senate.gov/filings/public/filing/5000632b-e40b-4762-affc-551b46a40c91/print/
- LDA filing (THEYFEARTRUTH registration): https://lda.senate.gov/filings/public/filing/e17ba492-75a0-4b18-b212-8b273ee23f79/print/
- Entity website: https://stateoflocnation.com/about
- Court case (CourtListener): https://www.courtlistener.com/docket/68269445/clement-v-garland/
- Court case (PacerMonitor): https://www.pacermonitor.com/public/case/52408377/CLEMENT_v_GARLAND
- LegiStorm article: https://www.legistorm.com/pro_news/4318/sovereignty-group-claims-40m-lobbying-total.html (paywall — fact-checker confirmed title)
- OpenLobby aggregator: https://www.openlobby.us/clients/state-of-loc-nation-global-public-benefit-corporation
- Reddit subreddit: https://www.reddit.com/r/locnation/

## What data-detective established

- $180M of LDA filings (15 records, 2024-2025) by LOC COMMUNITY ASSOCIATION for STATE OF LOC NATION GLOBAL PUBLIC BENEFIT CORPORATION.
- Court case `1:24-cv-00479-RC` (CLEMENT v. GARLAND) is real; co-defendants include Chief Justice Roberts, the UN Secretary General, the ICJ Registrar, and AG Garland.
- The LDA filings carry a self-disclaimer that the $20M is "pending HR 40 research reimbursement... not a federal payment."
- D9 (shell-pattern detector) confirms LOC NATION is the only multi-signal sovereign-citizen-pattern outlier in 418,098 filings; THEYFEARTRUTH is the next-closest pattern member (single, zero-income filing).
- Adversarial fact-checker (Spotlight pattern) issued `verified / high` on C-001.

## What Spotlight should pursue

- **Delaware Division of Corporations** — list every LLC tied to "Christina Loren Clement" or "Rico Dukes" or registered at "8 The Green, Suite A."
- **PACER / CourtListener** — pull all federal complaints filed by Christina Clement or Rico Dukes; any appellate filings; any sealed docket entries.
- **Florida + Georgia state corporation registries** — Clement reportedly ran for Senate Georgia 2026; surface campaign / corporate filings there.
- **FEC** — any committee registered by Clement or Dukes; any contributions in/out.
- **Web archive trail** — `stateoflocnation.com` capture history; any other sovereign-citizen / Moorish entity websites linking to it.
- **Social media** — Twitter/X, Facebook, Instagram, Truth Social handles for Clement and Dukes; cross-pollination with each other.
- **Sovereign-citizen movement research** — Southern Poverty Law Center / ADL / GW Program on Extremism may have profile entries.
- **Press releases / news mentions** — local news coverage of Clement's presidential campaign or Senate run; any LDA-related reporting.

## Out of scope (data-detective already handled)

- Confirming the LDA filings exist (they do, verified on `lda.senate.gov`).
- Confirming the court case exists (verified on CourtListener AND PacerMonitor).
- Internal corpus statistics (D9 shell-pattern detector confirms this is the only multi-signal outlier).

## Suggested Spotlight investigation deliverables

- A network diagram: Clement / Dukes / their LLCs / their court cases / their entities.
- A definitive answer: are LOC Nation and THEYFEARTRUTH operationally connected, or independent sovereign-citizen filers?
- A timeline of Clement's federal litigation + LDA filings + political-campaign self-declarations.
- Any specific bills (HR 40 reparations) the lobbying activity claims to "research" — and whether Congress.gov shows any actual interaction.
