# Post-ingest playbook (for the operator)

Once `case/index.duckdb` exists and `case/manifest.json` is written:

## Sanity checks (run first)

```sql
-- Table counts vs. expectations
SELECT 'senate_filings' AS t, count(*) FROM senate_filings
UNION ALL SELECT 'senate_contributions', count(*) FROM senate_contributions
UNION ALL SELECT 'house_filings', count(*) FROM house_filings
UNION ALL SELECT 'press_releases', count(*) FROM press_releases
UNION ALL SELECT 'members', count(*) FROM members;

-- Year coverage
SELECT filing_year, count(*) FROM senate_filings GROUP BY 1 ORDER BY 1;
SELECT report_year, count(*) FROM house_filings WHERE report_year IS NOT NULL GROUP BY 1 ORDER BY 1;

-- Bridge-key coverage (how many House filings link to a Senate registrant)
SELECT
  count(*) AS total_house,
  count(*) FILTER (WHERE senate_id_registrant IS NOT NULL) AS with_bridge,
  round(100.0 * count(*) FILTER (WHERE senate_id_registrant IS NOT NULL) / count(*), 1) AS pct
FROM house_filings;

-- How many Senate registrants have a house_registrant_id bridge already populated
SELECT
  count(DISTINCT registrant_id) AS senate_regs,
  count(DISTINCT registrant_id) FILTER (WHERE registrant_house_id IS NOT NULL) AS with_house_bridge
FROM senate_filings;

-- Foreign filings density
SELECT count(DISTINCT filing_uuid) FROM senate_foreign_entities;
SELECT foreign_principal_country, count(*) FROM fara_foreign_principals GROUP BY 1 ORDER BY 2 DESC LIMIT 20;
```

## Run order

1. `uv run skill/scripts/resolve_entities.py --db case/index.duckdb --out case/`
2. `uv run skill/scripts/external/fara.py --db case/index.duckdb --cache case/fara/cache --offline`
3. `uv run skill/scripts/query.py --db case/index.duckdb --detector all --out case/anomalies`
4. Skim CSVs in `case/anomalies/` — pick top candidates by detector
5. Drill via ad-hoc SQL through `query.py --sql ...`
6. Generate evidence cards for chosen records

## Threads I'm planning to chase

**Thread 1 (open exploration):**
- D5 single_client_juggernauts → top 20: which firms have one client paying them millions?
- D3 revolving_door_candidates → top 30: parse `covered_position` text; identify members/committees
- D1 spending_spikes → top 20: any registrant that jumped 5x+ in Q1 2025 deserves a look

**Thread 2 (foreign / FARA):**
- D4 foreign_filings → top 50, intersect with FARA: 
  - Senate filings with foreign_entities[] but **registrant not in FARA**
  - FARA foreign principals with **no matching Senate registrant** in our LDA data
  - Same registrant with **different country** declared in LDA vs FARA
- Clients with foreign-looking suffixes (Pty Ltd, GmbH, SA, AG) but no foreign_entities declaration

**Cross-corpus thread:**
- For top-N members by total contribution_items honoree amount, scan their press releases for issue topics that diverge from what their donors lobby on.

## Reproducibility checkpoints

- Commit `case/manifest.json` after ingest.
- Commit `case/anomalies/*.provenance.json` after queries.
- Cite query SHA-16 in every numeric claim in `findings-report.md`.
