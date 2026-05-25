# Spotlight investigation brief — OS-002

**Lead.** Akin Gump Strauss Hauer & Feld's 2024-2026 LDA filings disclose foreign entities for four politically-sensitive clients spanning four jurisdictions: **Ant Group (CN), TP-Link Systems (SG/VG/GB), Adani North America (IN), United Solar Polysilicon (CN/OM)**. None of these specific engagements appear to be matched by Akin Gump firm-level FARA registrations (D10 surface). Investigate whether the firm has FARA registrations at the attorney level instead, and whether the engagement topics align with active US national-security reviews or sanctions actions.

**Source.** Hand-off from data-detective finding C-003 + cycle-4 D10 FARA-gap narrowing. See `../findings.json` and `../candidates-for-osint.md` (OS-002).

**Confidence level (data-side).** Partially verified by adversarial fact-checker (the Akin Gump × Ant Group specific pairing was end-to-end traced via the House LDA lookup `reg_id=31784, client 317840961`).

## Named entities for OSINT

### Priority targets

1. **Ant Group Co., Ltd.** (Chinese fintech; Alibaba affiliate)
   - LDA filing UUID `a4411100-2eef-4903-9950-850271612499` (Q1 2025, $90K income reported)
   - Open: what specific bills/topics; CFIUS history; SAMR (China State Administration for Market Regulation) entity-list status.

2. **TP-Link Systems Inc.**
   - Registered across Singapore / British Virgin Islands / Great Britain / US.
   - Currently subject of US Commerce + Justice national-security review (reported 2024-2025).
   - LDA filing UUID `36cfa565-c70f-4954-90c4-3807732e2324` (Q2 2024).
   - Open: status of US national-security review; specific Akin Gump lobbying topics; FCC/CFIUS docket activity.

3. **Adani North America** (FKA Adani Solar USA)
   - Indian / Mauritian / Singaporean ownership trail.
   - Indian parent (Adani Group) subject of Hindenburg short-seller report (Jan 2023) + US SEC indictment (Nov 2024) for alleged bribery scheme.
   - LDA filing UUID `17a1a677-573e-42a2-9752-e4697b287283` (Q4 2024).
   - Open: SEC docket details; State Department / Commerce engagement; whether Akin Gump represents Adani in the SEC matter directly.

4. **United Solar Polysilicon (FZC) SPC** (FZC = Free Zone Company; SPC = Segregated Portfolio Company)
   - Chinese + Omani ownership; PV-grade polysilicon supply chain.
   - Subject to Uyghur Forced Labor Prevention Act + DHS Xinjiang Supply Chain Business Advisory.
   - LDA filing UUID `eda7a0c7-5907-47ce-8581-30bd78fc3424` (Q3 2025).
   - Open: UFLPA Entity List status; CBP withholding orders; specific bill targets.

### Secondary targets

- **TP-Link Global Inc.** (FKA) — the parent / predecessor entity.
- **Akin Gump's FARA registry presence** — they ARE in FARA but for OTHER foreign principals (per fact-checker). What's the full Akin Gump FARA client list, and why aren't these four engagements there?
- **Akin Gump partners who personally signed the LDA filings** — they may have personal FARA registrations.

## URLs already in the case-trace (start here)

- D10 detector CSV: `case/data-detective/anomalies/D10_fara_gap_narrowed.csv`
- Akin Gump House LDA lookup: https://lobbyingdisclosure.house.gov/lookup.asp?reg_id=31784
- Akin Gump x Ant Group LDA filing: https://lda.senate.gov/filings/public/filing/a4411100-2eef-4903-9950-850271612499/print/  (Q1 2025 LD-2, Senate ID 682-1010014; previous version of brief cited UUID 3a6e17c0-... in error — that resolved to a Posco America filing.)
- Akin Gump FARA-registrants page (OpenSecrets): https://www.opensecrets.org/fara/registrants/D000000162
- FARA bulk source (OpenSanctions DOJ mirror): https://data.opensanctions.org/datasets/latest/us_fara_filings/

## What data-detective established

- D10 narrowed the 682-name FARA gap to 200 candidates by signal (non-US client country, foreign-government-policy lobbying topics, SOE client naming, FARA absence).
- These four Akin Gump engagements top the narrowed list.
- Per the adversarial fact-checker, Akin Gump itself IS in FARA — but for other clients, not these four. The "gap" is at engagement level, not firm level.
- Public-record evidence cards available for the Akin Gump × Ant Group pairing.

## What Spotlight should pursue

- **DOJ FARA registrations at the attorney level** — pull the full list of Akin Gump lawyers who have personal FARA registrations; check whether any of them cover these four engagements.
- **CFIUS docket** — TP-Link, Ant Group, Adani Solar US, and United Solar Polysilicon are all plausible CFIUS subjects; pull what's public.
- **SEC docket** — Adani Group November 2024 indictment; track Akin Gump's role.
- **Commerce / OFAC sanctions lists** — TP-Link review status; UFLPA Entity List for United Solar Polysilicon parent; OFAC SDN list checks.
- **Congress.gov bill text** — pull the specific bills Akin Gump's `specific_issues` mentions for each engagement; assess whether they touch foreign-government-policy.
- **Press / Trade-publication coverage** — Bloomberg / Reuters / WSJ on each pairing.
- **Hong Kong corporate registry** — Ant Group's affiliated entities.
- **British Virgin Islands corporate registry** — TP-Link's BVI ownership.

## Out of scope (data-detective already handled)

- Confirming Akin Gump's LDA filings exist (verified).
- Computing the 682-name FARA gap aggregate (D10 done).
- Building the in-database join of LDA `foreign_entities[]` to FARA `fara_registrants` (done).

## Suggested Spotlight investigation deliverables

- A table mapping each Akin Gump foreign-client engagement → matching FARA registration (if any) at firm or attorney level → active US government review (CFIUS / SEC / Commerce / OFAC / DHS) → likely policy outcome the lobbying targets.
- A clean answer: is the FARA gap explained by legitimate non-FARA-triggering arrangements (US subsidiary of foreign parent, no foreign-government agency relationship), or are there specific engagements that should have FARA filings and don't?
