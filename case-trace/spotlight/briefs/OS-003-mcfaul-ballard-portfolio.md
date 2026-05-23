# Spotlight investigation brief — OS-003

**Lead.** Daniel McFaul — former Chief of Staff to Reps. Joe Scarborough, Jeff Miller, and Matt Gaetz — is at Ballard Partners lobbying for a politically heterogenous portfolio: U.S. Sugar ($4.56M), Amazon.com ($4.08M), RAI Services / American Tobacco ($3.18M), Hard Rock Japan K.K. ($2.34M), MHP Food Trading LLC (Ukrainian poultry, $1.68M during the Russia-Ukraine war), LA 2028 Olympics, Nova Southeastern University, and others. Map the network: Gaetz ties, Ballard Partners' political relationships, and the specific bills/agencies each engagement targets.

**Source.** Hand-off from data-detective D3 (revolving-door candidates) + ad-hoc drill. See `../candidates-for-osint.md` (OS-003).

**Confidence level (data-side).** Verified — McFaul's covered_position text matches public Congressional staff records; Ballard Partners is a well-known DC firm; client roster confirmed in LDA filings.

## Named entities for OSINT

### Priority targets

1. **Daniel McFaul** — current lobbyist at Ballard Partners.
   - LDA covered_position: "Legislative Director to U.S. Representative Joe Scarborough; Chief of Staff to U.S. Representatives Jeff Miller and Matt Gaetz."
   - Open: current Ballard Partners role title; specific issue practice (energy / defense / tax?); FEC personal donation pattern.

2. **Brian Ballard / Ballard Partners** — the firm. One of Washington's top-tier Republican-aligned lobby shops; closely tied to the Trump orbit.
   - Open: full client roster; ownership/partnership structure; Trump-administration revolving-door staff intake.

3. **MHP Food Trading LLC** — US subsidiary of Myronivsky Hliboproduct (Ukraine's largest agricultural company, owned by Yuriy Kosyuk).
   - Open: lobbying topic — Ukraine-war aid? US import duties? Sanctions carve-outs? Ownership-disclosure adequacy.

4. **Hard Rock Japan K.K.** — Japanese affiliate of Hard Rock International. Why does it need US federal lobbying?
   - Open: likely Osaka or Hokkaido Integrated Resort license diplomacy; US-Japan gaming MOU.

5. **RAI Services Company (FKA RAISC)** — American Tobacco / Reynolds American services arm.
   - Open: current tobacco-regulation lobbying priorities; PMTA / vaping rules.

### Secondary targets

- **U.S. Sugar Corporation** — Florida sugar; politically connected.
- **Amazon.com** — multiple lobbying firms; what's Ballard's specific scope.
- **Renewable Energy Aggregators, Inc.** — $3.55M is a lot for a not-widely-known firm.
- **LA 2028 Olympic Organizing Committee** — what's Ballard's lobbying angle (visa? funding? federal security?).

## URLs already in the case-trace (start here)

- D3 detector CSV: `case/data-detective/anomalies/D3_revolving_door_candidates.csv`
- McFaul's row in D3 surfaced his covered_position and client list.
- LegiStorm bio for Daniel McFaul: https://www.legistorm.com/person/profile/McFaul%2C+Daniel.html (paywall)
- Ballard Partners official site: https://www.ballardpartners.com/

## What data-detective established

- McFaul has 989 LDA activities in 2024-2026.
- His client list — exactly enumerated from `senate_activity_lobbyists` joined to `senate_filings`.
- Top 15 clients by revenue tabulated above.
- He's a confirmed revolving-door figure (former CoS to 3 Republican Reps including Matt Gaetz).

## What Spotlight should pursue

- **FEC** — McFaul's personal donations; any committees he's directed; PAC affiliations.
- **OpenSecrets revolving-door profile** for Daniel McFaul.
- **Ballard Partners full client roster** — via LDA bulk + OpenSecrets; compare McFaul's slice to other partners'.
- **Matt Gaetz orbit** — McFaul's continued ties to Gaetz post-Gaetz-resignation-from-Congress; Florida politics.
- **MHP Foods Ukraine** — current investor / political-risk reporting; Hindenburg-style short-seller research if any; ownership disclosure (Kosyuk).
- **Hard Rock Japan K.K.** — Hokkaido / Osaka IR (integrated resort) licensing timeline; US Foreign Commercial Service engagements.
- **RAI Services / Reynolds tobacco** — what bills they're lobbying on; PMTA timelines.
- **Press coverage** — Politico Influence; The Hill Bottom Line newsletter; Bloomberg lobbying-beat reporting on Ballard.

## Out of scope (data-detective already handled)

- Confirming McFaul's covered_position (LDA-verified).
- Aggregating his client list (LDA + ad-hoc query done).

## Suggested Spotlight investigation deliverables

- A network diagram: McFaul → Ballard → Trump orbit → specific Gaetz / Scarborough alumni.
- For each top client: specific bills lobbied, key votes, outcomes.
- For each foreign-tied client (MHP, Hard Rock Japan): ownership structure + any FARA implications.
- The Gaetz-McFaul thread specifically — what continues after Gaetz left Congress?
