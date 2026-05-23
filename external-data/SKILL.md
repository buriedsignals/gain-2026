---
name: external-data
description: "Pull external public datasets into the same DuckDB index used by data-detective so cross-corpus joins can happen in-database. Current pullers (extensible pattern) — FARA bulk data via the OpenSanctions DOJ mirror (Foreign Agents Registration Act registrants and foreign principals); Congress.gov committee jurisdiction graph via the open unitedstates/congress-legislators dataset (current Congress members, committees, assignments); USAspending.gov DoD contract awards via the federal USAspending API. Use this sub-skill in Phase 3 of a data-detective investigation when an anomaly requires external corroboration. Triggers on prompts mentioning FARA data, Congress.gov committee assignments, USAspending DoD contracts, external data joins, or pulling a public dataset into the index."
license: MIT
metadata:
  parent: data-detective
  step: P3_external_join
  inputs: DuckDB index, network access
  outputs: new tables in same DuckDB (fara_registrants, fara_foreign_principals, congress_members, congress_committees, congress_committee_assignments)
---

# data-detective-external-data

External-source pullers for the data-detective DuckDB index.

## When to use

Called inside a Phase 3 cycle of `data-detective` when an anomaly's interpretation requires external context the corpus doesn't have. Examples:

- LDA filings disclose foreign entities — pull FARA to surface which lobbyists are also registered as foreign agents and which are not.
- Press releases come from members identified by `bioguide_id` — pull Congress.gov committee assignments so you can ask "which current committee members are attacking the clients of a former staffer of the same committee?"
- An Anchor & Arrow-style finding cites defense lobbying — pull USAspending to confirm DoD contract flow to the lobbied clients.

## Pullers

### `scripts/fara.py` — FARA bulk

Source: <https://data.opensanctions.org/datasets/latest/us_fara_filings/> (OpenSanctions mirror of DOJ FARA bulk XML; daily-updated; no auth).

```bash
uv run scripts/fara.py --db <index.duckdb> --cache <case>/fara/cache
# or --offline if already cached
```

Tables created:
- `fara_registrants` — registered firms / persons (registration_number, name, address, dates)
- `fara_foreign_principals` — the foreign principals each registrant represents

### `scripts/congress_gov.py` — Congress + committee graph

Source: <https://github.com/unitedstates/congress-legislators> raw YAML on GitHub (community-maintained by ProPublica + GovTrack + Sunlight Foundation descendents; no auth).

```bash
uv run scripts/congress_gov.py --db <index.duckdb>
```

Tables created:
- `congress_members` — current Congress members (bioguide_id, name, chamber, state, district, party)
- `congress_committees` — committees + subcommittees with chamber and parent_committee_code
- `congress_committee_assignments` — member ↔ committee assignments with role

Joins natively to `press_releases.bioguide_id`.

### `scripts/usaspending.py` (worked-example pattern, no committed script)

For ad-hoc DoD contract lookups by recipient name. See `case/external/usaspending_aa_clients.json` in the reference case for an example: a list of clients, queried against the federal USAspending search API filtered to DoD as awarding agency, written as JSON.

## Adding a new puller

The pattern:
1. Fetch the source (XML / JSON / YAML / CSV) with the python `httpx` library.
2. Parse to flat row dicts.
3. `con.execute("DROP TABLE IF EXISTS <name>")` then `CREATE TABLE` with explicit schema.
4. `con.executemany("INSERT INTO ...", rows)`.
5. Create indexes on join columns.

Drop new pullers into `scripts/` next to the existing ones. Each is self-contained PEP 723.

## Anti-patterns

- **No new external sources without archiving.** If a finding cites a pulled dataset, the case-trace should keep a copy of the raw source (or a manifest of source-file SHAs).
- **No API-key-required pullers without graceful fallback.** Use community mirrors (OpenSanctions, unitedstates.io GitHub) where possible to maximize reproducibility.

## Composes with

- Input ← `data-detective-ingest` (the index)
- Output → `data-detective-detect` (new detectors that use the external tables)
