# Spotlight investigation brief — OS-006

**Lead.** Per LegiStorm (confirmed by the adversarial fact-checker for C-004), Mark Warren left Brownstein Hyatt for Capitol Tax Partners in May 2026 — during this report's publication window. Did Apollo Global Management (his $8.92M Brownstein engagement) follow him? Did Athene, J&J, T-Mobile, Bloom Energy, API? When did the move actually happen and what triggered it?

**Source.** Hand-off from data-detective C-004 + adversarial fact-checker correction. See `../findings.json` (C-004 limitations) and `../candidates-for-osint.md` (OS-006).

**Confidence level (data-side).** Verified that the move occurred (LegiStorm). Open: client migration patterns + business context.

## Named entities for OSINT

### Priority targets

1. **Mark Warren** at Capitol Tax Partners (May 2026–).
   - Prior: Brownstein Hyatt Farber Schreck (May 2021–May 2026).
   - Earlier: Senate Finance Committee (Chief Tax Counsel under Chairman Grassley), Sen. John Thune (Sr Tax Counsel), House Ways and Means (Tax Counsel), Treasury Office of Legislative Affairs (Deputy Assistant Secretary).

2. **Capitol Tax Partners LLP** — the new firm.
   - Open: firm size; partnership structure; existing client roster; whether they're known as a Republican-aligned tax shop.

3. **Apollo Global Management** — did the engagement migrate?
   - Open: any new LDA filing under Capitol Tax Partners for Apollo (post May 2026); Sullivan-only filings at Brownstein for Apollo (post-Warren); Politico / Bloomberg Influence coverage of the move.

### Secondary targets

- **Russell Sullivan** (Brownstein Hyatt) — Warren's former partner on the Apollo file. Did Sullivan retain Apollo?
- **Other former Brownstein clients of Warren's** — Athene Holding, Johnson & Johnson, T-Mobile, Bloom Energy, American Petroleum Institute.

## URLs already in the case-trace (start here)

- C-004 finding chain in `../findings-report.md`
- LegiStorm Mark E. Warren: https://www.legistorm.com/person/bio/371/Mark_E_Warren.html
- Brownstein 2021 hire-announcement press release: https://www.bhfs.com/news-event/brownstein-adds-former-senate-finance-committee-chief-tax-counsel-mark-warren-to-d-c-office/
- Mark Warren LinkedIn: https://www.linkedin.com/in/mark-warren-ba5b48213

## What data-detective established

- Sullivan + Warren co-lobbied Apollo at Brownstein through Q1 2026 ($8.92M Brownstein-side revenue).
- D11 + D12 confirmed the Senate Finance Committee revolving-door + bipartisan say-vs-pay (Warren D + Grassley R) attack pattern on Apollo over Steward Health Care.
- LegiStorm timeline puts Warren's move at May 2026 — within the publication window.

## What Spotlight should pursue

- **Capitol Tax Partners** website and team page (does Warren appear).
- **LDA recent registrations** — search lda.senate.gov for any new Capitol Tax Partners filing naming Warren as lobbyist post-May 2026.
- **Politico Influence newsletter** — coverage of the Warren move; reasons cited.
- **Bloomberg Government** — DC tax-lobby reporting.
- **OpenSecrets** — Capitol Tax Partners firm profile + client list.
- **The Hill Bottom Line** column — likely covered the move.

## Out of scope (data-detective already handled)

- The C-004 finding through Q1 2026 (verified).
- Sullivan's tenure at Brownstein (verified via Brownstein bio + Chambers USA).

## Suggested Spotlight investigation deliverables

- A definitive answer: did Apollo migrate with Warren or stay with Sullivan at Brownstein?
- Trigger for the move: client pressure, leadership change at Brownstein, business opportunity at Capitol Tax Partners, or personal?
- Updated C-004 narrative with the post-publication temporal correction.
