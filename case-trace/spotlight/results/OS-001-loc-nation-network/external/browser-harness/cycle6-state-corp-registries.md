# Cycle 6 — Direct browser-harness state corporate registry sweep

**Date:** 2026-05-22
**Tool:** `browser-harness` (CDP-driven Chrome) against state corp registries identified via OSINT Navigator
**Targets queried:** Delaware iCIS, Florida Sunbiz

## Delaware iCIS Entity Search (icis.corp.delaware.gov)

Queried terms: "Clement", "Christina Loren Clement", and broad sweep "LOC Nation / LOC Community / SOLN / Loren Clement / Rico Dukes / THEYFEARTRUTH / Black USA / Loc Nation Dollar".

**Result:** Only ONE Delaware entity exactly matches "Christina Loren Clement":

| File # | Entity Name |
|---|---|
| **7127855** | **CHRISTINA LOREN CLEMENT LLC** |

A broader "Clement" search returned 50+ unrelated entities. No Delaware shell-LLC network surfaced under either Christina Clement or Rico Dukes.

**Interpretation:** The Delaware corporate side appears to be a single registered LLC, not a multi-entity shell network. The "8 The Green, Suite A, Dover, DE 19901" registered-agent hypothesis from C-001 was already disconfirmed by the fact-checker (mass commercial RA address). Delaware iCIS confirms: no additional Clement-named entities.

## Florida Sunbiz (search.sunbiz.org)

Queried: "Christina Loren Clement", "LOC NATION".

**Novel finding — there is a separate "LOC NATION" entity in Florida:**

- **Entity:** LOC NATION JAX LLC
- **Document number:** L21000352541
- **FEI/EIN:** 87-2134353
- **Date filed:** 2021-08-05 (predates Clement's CLEMENT v. GARLAND lawsuit by 2.5 years and her LDA registration by 3 years)
- **Status:** ACTIVE (filed 2025 + 2026 annual reports)
- **Principal address:** 3535 University N, Jacksonville, FL 32277
- **Mailing address:** 6898 A C Skinner Pkwy, Jacksonville, FL 32256
- **Registered agent:** HICKS, ANISHA (not Clement)
- **Authorized person (MGR):** HICKS, ANISHA

**Interpretation.** Different operator (Anisha Hicks, Jacksonville FL) uses the "LOC NATION" brand in a Florida LLC formed before Clement's federal LDA scheme. Could be:
1. Namesake / coincidence (Loc Nation is also a hair/beauty brand);
2. Adjacent operator in the same broader movement;
3. Clement's franchise / co-branded affiliate;
4. Unrelated.

The August 2021 filing date is notable because it is well before Clement's federal LDA scheme (September 2024 registration) and before her federal court case (February 2024). The brand thus pre-existed Clement's federal-level deployment of it.

The Apopka FL address mystery (Clement's address on a Northrop Grumman creditor matrix, per the OS-001 spotlight investigator) returned no matches in Sunbiz's street-address search — implying Clement was listed there personally as a creditor, not as an entity registered at that address.

## OSINT Navigator tools consulted (for next-cycle work)

| Target | Top tool from Navigator | URL |
|---|---|---|
| Delaware corp lookup | iCIS Entity Search | https://icis.corp.delaware.gov/ecorp/entitysearch/namesearch.aspx |
| PACER docs | RECAP Archive (Free Law Project) | https://www.courtlistener.com/recap/ |
| FEC public records | fec.gov/data | https://www.fec.gov/data |
| Florida corp lookup | Sunbiz | https://dos.myflorida.com/sunbiz/search/ |
| Multi-state corp graphs | Corporation Wiki | https://www.corporationwiki.com/ |

## What did not return novel findings in this pass

- The Delaware Christina-Loren-Clement-LLC network hypothesis (only one entity).
- The Apopka address mystery (no Sunbiz entity at that address).
- The hypothetical Clement-Dukes operational connection (no Delaware or Florida common-address match).

## What did return novel findings in this pass

- The Florida LOC NATION JAX LLC — a separate operator (Hicks) using the LOC NATION brand since 2021. This is a journalistically tractable single fact: the brand pre-dates Clement's federal LDA scheme by 3 years, run from Jacksonville by a different person.

## Methods + audit

- 2 browser-harness sessions on the user's Chrome, no login required
- Pages live-rendered (ASP.NET form post for Delaware; standard form post for Florida)
- Results validated by direct entity-detail page navigation
- Submission archive at `case-trace/spotlight/results/OS-001-loc-nation-network/external/browser-harness/`
