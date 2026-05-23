# Spotlight investigation brief — OS-004

**Lead.** Beyond Brownstein Hyatt's Senate-Finance cluster (C-004), D11 surfaces a second tier of mega-revenue revolving-door lobbyists each with $50M+ in 2022-2026 committee-aligned lobbying revenue. Map biographical detail, current firm affiliation, top clients, and any active conflicts.

**Source.** Hand-off from data-detective D11 (multi-hop revolving-door committee match). See `../candidates-for-osint.md` (OS-004).

**Confidence level (data-side).** Medium-high — the LDA covered_position fields are verified; D11's keyword-based committee mapping is heuristic so individual classifications need spot-checking.

## Named entities for OSINT

### Priority targets

1. **James Richards**
   - LDA covered_position: "Chief of Staff House Member Office (Pearce); Director IGA USDA; Appropriations Associate House Member Office (Skeen, Bonilla)."
   - D11 matched income: $84.6M lifetime (highest in our top-15).
   - Open: current firm; current client roster; FEC donor pattern; House Appropriations defense / agriculture specialty.

2. **Anthony Lazarski**
   - LDA covered_position: "Senior Legislative Advisor, Senate Member Office (Inhofe); Professional Staff Member, [HASC]."
   - D11 matched income: $78.3M.
   - Open: current firm; Inhofe (R-OK) legacy network; defense / energy lobbying specialty.

3. **Jennifer Young**
   - LDA covered_position: "Assistant Secretary for Legislation, HHS; Deputy Assistant Secretary for Legislation, HHS."
   - D11 matched income: $73.3M.
   - Open: current firm (likely a healthcare boutique); active pharma client list; HHS rules they engage on.

4. **Cornell Teague**
   - LDA covered_position: "Professional Staff, House Appropriations Committee – Defense; Professional Staff, House Budget."
   - D11 matched income: $63.9M.
   - Open: current firm; defense-appropriations specialty; client overlap with Anchor & Arrow founders.

5. **John O'Neill**
   - LDA covered_position: "Policy Director/Counsel, Senate Minority Whip (04-06); Tax Counsel, Senate Finance; ..."
   - D11 matched income: $62.7M.
   - Open: current firm; tax-policy specialty; Senate Republican Whip legacy network.

### Secondary targets (other D11 hits worth flagging)

- **Kimberly Brandt** — former HHS-OIG Senior Counsel; $52.5M matched.
- **Peter Fise** — former Sen. Finance Committee + Sen. Shaheen Health Counsel; $51.3M.
- **Martin Reiser** — former Policy Dir to Rep Steve Scalise + Ways and Means; $49.4M.
- **Daniel Todd** — former Senior Health Counsel, Senate Finance Committee; $42.0M.

## URLs already in the case-trace (start here)

- D11 detector CSV: `case/data-detective/anomalies/D11_revolving_door_committee_match.csv` (top 200 rows; first 15 surfaced above)
- D11 provenance: `case/data-detective/anomalies/D11_revolving_door_committee_match.provenance.json` (SQL hash `a7712c723043a717`)

## What data-detective established

- Each lobbyist's `covered_position` text → mapped heuristically to a former Congressional committee.
- Each lobbyist's current 2024-2026 quarterly LDA filings → matched to issue codes aligned with that committee's jurisdiction.
- Total revenue per lobbyist on matched activities computed deterministically.

## What Spotlight should pursue

For each named lobbyist:

- **OpenSecrets revolving-door profile** — they're all almost certainly indexed there.
- **LegiStorm biography** — verifies dates, exact roles.
- **LinkedIn** — current firm + practice area.
- **FEC** — personal donations + PAC affiliations.
- **Press coverage** — Politico / Bloomberg / Roll Call lobbying-beat profiles.
- **D12 follow-up** — for each, identify current committee members on their former committee; check whether ANY of those members publicly oppose their clients' interests (the say-vs-pay pattern that worked for C-004 Apollo).

## Out of scope (data-detective already handled)

- LDA-side aggregate revenue and client matching.
- Detector D11 produced the ranking; D12 produces the say-vs-pay structure when extended.

## Suggested Spotlight investigation deliverables

- A profile-card per lobbyist (5 cards for Tier 1, 4 for Tier 2).
- For each, the strongest say-vs-pay candidate (e.g. who publicly opposes their biggest current client).
- Identification of any one of them as a candidate for a follow-up dedicated finding (parallel to C-004).
