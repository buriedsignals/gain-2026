# Spotlight investigation brief — OS-005

**Lead.** Tarplin, Downs & Young LLC is a healthcare-policy lobbying boutique whose roster includes Pamela Smith (former Legislative Director to Sen. Tom Harkin; DOJ Office of Legislative Affairs) on $32M+ across BCBS, Abbott, Alzheimer's Association, Vertex, BIO 2022-2026 — and Raissa Downs (former Principal Deputy Assistant Secretary for Legislation, HHS) on a similar revenue profile. Profile the firm's leadership, its full client roster, its HHS / Senate HELP / Senate Finance Committee ties, and any HHS-OIG enforcement actions involving its clients.

**Source.** Hand-off from data-detective D3 + ad-hoc drill. See `../candidates-for-osint.md` (OS-005).

**Confidence level (data-side).** Verified — covered_position fields match public records; client roster directly visible in LDA.

## Named entities for OSINT

### Priority targets

1. **Tarplin, Downs & Young LLC** (the firm).
   - Open: founders' bios; staff count; office address; partner list; how their HHS-leadership pedigree differs from larger firms.

2. **Pamela Smith**
   - LDA covered_position: "Principal Deputy Assistant Secretary for Legislation HHS; Deputy Assistant Secretary for Legislation HHS; Staff Director, Subcommittee on Employment, Senate HELP Committee."
   - Top clients (LDA-confirmed): Blue Cross Blue Shield Association ($7.15M), Abbott / Alere ($6.72M), Alzheimer's Association ($6.51M), Vertex Pharmaceuticals ($6.00M), BIO ($5.84M).

3. **Raissa Downs**
   - LDA covered_position: "Principal Deputy Assistant Secretary for Legislation HHS; Deputy Assistant Secretary for Legislation HHS; Staff Director, Subcommittee on Employment, Senate HELP Committee."
   - Open: identical-looking position text to Smith — are they HHS contemporaries who co-founded the firm?

### Secondary targets

- **Linda Tarplin** — almost certainly the "Tarplin" in the firm name. Open: prior public role.
- **Firm partners across all D11 results at this firm** — there may be 4-6 named lobbyists all from HHS leadership backgrounds.

## URLs already in the case-trace (start here)

- D11 detector CSV: case/data-detective/anomalies/D11_revolving_door_committee_match.csv — search "TARPLIN" for relevant rows
- D3 detector CSV with raw covered_position text

## What data-detective established

- $32M+ of 2022-2026 lobbying revenue assigned to Pamela Smith.
- Identical or near-identical covered_position text for Raissa Downs.
- Both work the same client roster.
- Clients are predominantly pharma + insurance + disease-advocacy.

## What Spotlight should pursue

- **Tarplin, Downs & Young website + partner pages**.
- **HHS-OIG enforcement-actions database** — any actions against BCBS / Abbott / Vertex during the engagement window.
- **OpenSecrets revolving-door** — Tarplin, Downs, Young individual profiles.
- **Healthcare-policy press coverage** — Politico Pulse, Inside Health Policy, Bloomberg Government.
- **Specific bills lobbied** — pull from LDA `specific_issues` + cross-reference to Congress.gov; identify the 5 most consequential bills the firm engaged on.
- **D12 say-vs-pay** — for Senate HELP / Senate Finance / House E&C current members, does anyone publicly attack one of this firm's clients?

## Out of scope (data-detective already handled)

- The lobbyist-to-client mapping in LDA.
- The covered_position → committee inference.

## Suggested Spotlight investigation deliverables

- A profile card per founding partner of Tarplin Downs & Young.
- A diagram of HHS-leadership → Tarplin Downs & Young → pharma/insurance clients → committee jurisdiction.
- A timing chart: when did each partner leave HHS, when did they begin lobbying their respective subsequent agencies / committees, and what cooling-off period applied.
