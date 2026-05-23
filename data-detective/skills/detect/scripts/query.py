#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "duckdb>=1.1",
# ]
# ///
"""
data-detective :: query

Two modes:

1. Built-in detectors. Stable IDs, parameterized, output ranked CSV + a row in
   the provenance ledger.

     uv run query.py --db <db> --detector D1 --out <dir>

2. Ad-hoc SQL. The query layer the agent should reach for in execution cycles
   instead of asking the model to scan documents. Every run is logged.

     uv run query.py --db <db> --sql "<SQL>" --out <dir>
     uv run query.py --db <db> --sql-file <file> --out <dir>

Every result CSV has an accompanying `<name>.provenance.json` capturing:
  - the SQL executed, the SHA-256 of that SQL, the DB path
  - the row count and timestamp
  - the schema (column names + types)
This is the audit trail. Every finding cites a query by SHA, so an editor can
re-run the exact query against the exact DB and reproduce the row.

Detectors:
  D1  spending_spikes              -- registrant z-score quarter over quarter
  D2  missing_income_filings       -- quarterly filings with null income
  D3  revolving_door_candidates    -- lobbyists with covered_position text
  D4  foreign_filings              -- filings with foreign_entities[]
  D5  single_client_juggernauts    -- registrants with 1-2 clients and high income
  D6  pac_contribution_flow        -- aggregate contribution_items by payee/honoree
  D7  issue_concentration_shifts   -- general_issue_code QoQ deltas
  D8  new_registrant_surge         -- new registrants ranked by first-quarter income

  L   list                         -- print detectors and exit
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import time
from pathlib import Path

import duckdb


# ---------------------------------------------------------------------------
# Detector catalog
# ---------------------------------------------------------------------------

DETECTORS: dict[str, dict] = {
    "D1": {
        "name": "spending_spikes",
        "description": "Registrant-quarter income z-score against the prior 4 quarters. |z| >= 2 surfaces.",
        "params": {"limit": 200, "min_z_abs": 2.0, "min_income": 50000},
        "sql": """
            WITH quarterly AS (
                SELECT
                    registrant_id,
                    registrant_name,
                    filing_year,
                    filing_period,
                    sum(coalesce(income, 0)) AS total_income,
                    count(*) AS n_filings
                FROM senate_filings
                WHERE filing_type IN ('Q1','Q2','Q3','Q4')
                  AND income IS NOT NULL
                GROUP BY 1,2,3,4
            ),
            windowed AS (
                SELECT
                    registrant_id, registrant_name, filing_year, filing_period, total_income,
                    avg(total_income) OVER (PARTITION BY registrant_id ORDER BY filing_year, filing_period
                                            ROWS BETWEEN 4 PRECEDING AND 1 PRECEDING) AS prior_mean,
                    stddev_pop(total_income) OVER (PARTITION BY registrant_id ORDER BY filing_year, filing_period
                                                   ROWS BETWEEN 4 PRECEDING AND 1 PRECEDING) AS prior_sd,
                    count(*) OVER (PARTITION BY registrant_id ORDER BY filing_year, filing_period
                                   ROWS BETWEEN 4 PRECEDING AND 1 PRECEDING) AS prior_n
                FROM quarterly
            )
            SELECT
                registrant_id, registrant_name, filing_year, filing_period,
                total_income, prior_mean, prior_sd, prior_n,
                CASE WHEN prior_sd > 0 THEN (total_income - prior_mean) / prior_sd END AS z_score
            FROM windowed
            WHERE prior_n >= 3
              AND prior_sd > 0
              AND total_income >= {min_income}
              AND abs((total_income - prior_mean) / prior_sd) >= {min_z_abs}
            ORDER BY abs((total_income - prior_mean) / prior_sd) DESC
            LIMIT {limit}
        """,
    },
    "D2": {
        "name": "missing_income_filings",
        "description": "Quarterly filings where income is null. Clustered by registrant. Quality + accountability angle.",
        "params": {"limit": 200, "min_filings": 4},
        "sql": """
            SELECT
                registrant_id, registrant_name,
                count(*) AS quarterly_filings_with_null_income,
                count(DISTINCT client_id) AS distinct_clients,
                min(filing_year || '-' || filing_period) AS first_seen,
                max(filing_year || '-' || filing_period) AS last_seen
            FROM senate_filings
            WHERE filing_type IN ('Q1','Q2','Q3','Q4')
              AND income IS NULL
            GROUP BY 1,2
            HAVING count(*) >= {min_filings}
            ORDER BY quarterly_filings_with_null_income DESC, distinct_clients DESC
            LIMIT {limit}
        """,
    },
    "D3": {
        "name": "revolving_door_candidates",
        "description": "Lobbyists whose covered_position text is populated. Surfaces revolving-door talent + their current clients.",
        "params": {"limit": 500},
        "sql": """
            WITH personal AS (
                SELECT
                    lobbyist_id,
                    first_name, last_name,
                    any_value(covered_position) AS sample_position,
                    count(DISTINCT filing_uuid) AS filings_with_lobbyist,
                    count(DISTINCT covered_position) AS distinct_positions
                FROM senate_activity_lobbyists
                WHERE covered_position IS NOT NULL AND length(covered_position) >= 12
                GROUP BY 1,2,3
            ),
            with_clients AS (
                SELECT
                    p.*,
                    (
                        SELECT string_agg(DISTINCT f.client_name, ' | ')
                        FROM senate_activity_lobbyists al
                        JOIN senate_filings f USING (filing_uuid)
                        WHERE al.lobbyist_id = p.lobbyist_id
                          AND f.client_name IS NOT NULL
                    ) AS clients_lobbied_for
                FROM personal p
            )
            SELECT *
            FROM with_clients
            ORDER BY filings_with_lobbyist DESC
            LIMIT {limit}
        """,
    },
    "D4": {
        "name": "foreign_filings",
        "description": "Senate filings carrying foreign_entities[]. Anchor for FARA cross-reference.",
        "params": {"limit": 500},
        "sql": """
            SELECT
                f.filing_uuid,
                f.filing_year,
                f.filing_period,
                f.registrant_name,
                f.client_name,
                f.client_country,
                f.client_ppb_country,
                fe.foreign_entity_name,
                fe.country AS foreign_entity_country,
                fe.ppb_country AS foreign_entity_ppb,
                f.income,
                f.url
            FROM senate_foreign_entities fe
            JOIN senate_filings f USING (filing_uuid)
            ORDER BY f.income DESC NULLS LAST
            LIMIT {limit}
        """,
    },
    "D5": {
        "name": "single_client_juggernauts",
        "description": "Registrants with very few clients but very high income. Possible captive lobby shops.",
        "params": {"limit": 200, "min_total_income": 250000},
        "sql": """
            SELECT
                registrant_id,
                any_value(registrant_name) AS registrant_name,
                count(DISTINCT client_id) AS distinct_clients,
                count(DISTINCT filing_uuid) AS filings,
                sum(coalesce(income, 0)) AS total_income,
                min(filing_year) AS earliest_year,
                max(filing_year) AS latest_year,
                string_agg(DISTINCT client_name, ' | ') AS clients
            FROM senate_filings
            WHERE filing_type IN ('Q1','Q2','Q3','Q4')
            GROUP BY 1
            HAVING distinct_clients BETWEEN 1 AND 2
               AND total_income >= {min_total_income}
            ORDER BY total_income DESC
            LIMIT {limit}
        """,
    },
    "D6": {
        "name": "pac_contribution_flow",
        "description": "Top contribution_items by payee + honoree, aggregated from LD-203 reports.",
        "params": {"limit": 500},
        "sql": """
            SELECT
                payee_name,
                honoree_name,
                count(*) AS n_contributions,
                sum(coalesce(amount, 0)) AS total_amount,
                count(DISTINCT filing_uuid) AS distinct_filings,
                count(DISTINCT contributor_name) AS distinct_contributors
            FROM senate_contribution_items
            WHERE payee_name IS NOT NULL OR honoree_name IS NOT NULL
            GROUP BY 1,2
            ORDER BY total_amount DESC NULLS LAST
            LIMIT {limit}
        """,
    },
    "D7": {
        "name": "issue_concentration_shifts",
        "description": "Issue-code QoQ delta: total registrants and total income per general_issue_code.",
        "params": {"limit": 500, "min_qoq_delta_pct": 25},
        "sql": """
            WITH per_q AS (
                SELECT
                    a.general_issue_code,
                    f.filing_year,
                    f.filing_period,
                    count(DISTINCT f.registrant_id) AS registrants,
                    sum(coalesce(f.income, 0)) AS total_income
                FROM senate_lobbying_activities a
                JOIN senate_filings f USING (filing_uuid)
                WHERE f.filing_type IN ('Q1','Q2','Q3','Q4')
                  AND a.general_issue_code IS NOT NULL
                GROUP BY 1,2,3
            ),
            ordered AS (
                SELECT
                    general_issue_code, filing_year, filing_period, registrants, total_income,
                    lag(total_income) OVER (PARTITION BY general_issue_code
                                            ORDER BY filing_year, filing_period) AS prior_income,
                    lag(registrants) OVER (PARTITION BY general_issue_code
                                           ORDER BY filing_year, filing_period) AS prior_registrants
                FROM per_q
            )
            SELECT *,
                   CASE WHEN prior_income > 0 THEN round(100.0 * (total_income - prior_income) / prior_income, 1) END AS income_delta_pct,
                   CASE WHEN prior_registrants > 0 THEN round(100.0 * (registrants - prior_registrants) / prior_registrants, 1) END AS registrants_delta_pct
            FROM ordered
            WHERE prior_income IS NOT NULL
              AND prior_income > 0
              AND abs((total_income - prior_income) / prior_income) * 100 >= {min_qoq_delta_pct}
            ORDER BY abs(total_income - prior_income) DESC
            LIMIT {limit}
        """,
    },
    "D9": {
        "name": "shell_pattern_filings",
        "description": "Suspect-pattern LDA filings: free-mail contacts, self-aggrandizing covered_position text, sovereign-citizen-style markers in activity descriptions or client descriptions. Multi-signal score.",
        "params": {"limit": 100, "min_score": 2},
        "sql": """
            WITH activity_text AS (
                SELECT filing_uuid,
                       string_agg(coalesce(description,''), ' ' ORDER BY activity_index) AS act_text
                FROM senate_lobbying_activities GROUP BY 1
            ),
            lobbyist_text AS (
                SELECT filing_uuid,
                       string_agg(coalesce(covered_position,''), ' | ') AS pos_text
                FROM senate_activity_lobbyists GROUP BY 1
            ),
            scored AS (
                SELECT
                    f.filing_uuid,
                    f.filing_year, f.filing_period, f.filing_type,
                    f.registrant_name, f.client_name,
                    f.client_general_description AS client_desc,
                    f.income, f.url,
                    -- Shell-pattern signals (each adds 1 to score)
                    (lower(coalesce(f.client_general_description,'')) LIKE '%sovereign%')::int                              AS sig_sovereign_client,
                    (lower(coalesce(f.client_general_description,'')) LIKE '%established government%')::int                 AS sig_established_govt,
                    (lower(coalesce(actv.act_text,'')) LIKE '%empress%' OR
                     lower(coalesce(actv.act_text,'')) LIKE '%annuit coeptis%' OR
                     lower(coalesce(actv.act_text,'')) LIKE '%king solomon%' OR
                     lower(coalesce(actv.act_text,'')) LIKE '%sui generis%')::int                                              AS sig_esoteric_terms,
                    (lower(coalesce(lt.pos_text,'')) LIKE '%empress%' OR
                     lower(coalesce(lt.pos_text,'')) LIKE '%head of state%' OR
                     lower(coalesce(lt.pos_text,'')) LIKE '%assumed the presiden%' OR
                     lower(coalesce(lt.pos_text,'')) LIKE '%queen%')::int                                                    AS sig_self_styled_title,
                    (f.posted_by_name LIKE '%/%/%' OR f.posted_by_name LIKE '%LLC%')::int                                    AS sig_posted_by_llc_slashes,
                    (upper(coalesce(f.client_name,'')) LIKE '%GLOBAL PUBLIC BENEFIT%')::int                                  AS sig_global_pbc_naming
                FROM senate_filings f
                LEFT JOIN activity_text actv USING (filing_uuid)
                LEFT JOIN lobbyist_text lt USING (filing_uuid)
            )
            SELECT
                filing_uuid, filing_year, filing_period, filing_type,
                registrant_name, client_name, client_desc, income,
                (sig_sovereign_client + sig_established_govt + sig_esoteric_terms +
                 sig_self_styled_title + sig_posted_by_llc_slashes + sig_global_pbc_naming) AS shell_score,
                sig_sovereign_client, sig_established_govt, sig_esoteric_terms,
                sig_self_styled_title, sig_posted_by_llc_slashes, sig_global_pbc_naming,
                url
            FROM scored
            WHERE (sig_sovereign_client + sig_established_govt + sig_esoteric_terms +
                   sig_self_styled_title + sig_posted_by_llc_slashes + sig_global_pbc_naming) >= {min_score}
            ORDER BY shell_score DESC, income DESC NULLS LAST
            LIMIT {limit}
        """,
    },
    "D10": {
        "name": "fara_gap_narrowed",
        "description": "LDA filings with foreign-government-policy lobbying topics or non-US client country, where the registrant is NOT in FARA — promoted from aggregate gap to named candidates.",
        "params": {"limit": 200},
        "sql": """
            WITH norm_sf AS (
                SELECT DISTINCT
                    f.filing_uuid, f.registrant_name, f.client_name,
                    f.client_country, f.client_ppb_country,
                    f.filing_year, f.income, f.url,
                    upper(regexp_replace(coalesce(f.registrant_name,''), '[^A-Z0-9 ]', ' ', 'g')) AS norm_r
                FROM senate_filings f
                WHERE f.filing_year IN (2024, 2025, 2026)
                  AND EXISTS (SELECT 1 FROM senate_foreign_entities fe WHERE fe.filing_uuid = f.filing_uuid)
            ),
            norm_fara AS (
                SELECT DISTINCT
                    upper(regexp_replace(coalesce(registrant_name,''), '[^A-Z0-9 ]', ' ', 'g')) AS norm_r
                FROM fara_registrants
            ),
            activity_text AS (
                SELECT filing_uuid,
                       string_agg(coalesce(description,''), ' ' ORDER BY activity_index) AS act_text
                FROM senate_lobbying_activities GROUP BY 1
            ),
            fp_country_for_filing AS (
                SELECT filing_uuid,
                       string_agg(DISTINCT country, ',' ORDER BY country) AS fe_countries
                FROM senate_foreign_entities GROUP BY 1
            )
            SELECT
                sf.filing_uuid, sf.filing_year,
                sf.registrant_name, sf.client_name,
                sf.client_country, sf.client_ppb_country,
                fp.fe_countries,
                sf.income,
                (sf.client_country IS NOT NULL AND sf.client_country NOT IN ('US','United States of America'))::int AS sig_non_us_client,
                (sf.client_ppb_country IS NOT NULL AND sf.client_ppb_country NOT IN ('US','United States of America'))::int AS sig_non_us_ppb,
                (lower(coalesce(actv.act_text,'')) LIKE '%foreign government%' OR
                 lower(coalesce(actv.act_text,'')) LIKE '%embassy%' OR
                 lower(coalesce(actv.act_text,'')) LIKE '%fara%' OR
                 lower(coalesce(actv.act_text,'')) LIKE '%sanctions%' OR
                 lower(coalesce(actv.act_text,'')) LIKE '%ambassador%')::int AS sig_foreign_gov_topic,
                (lower(coalesce(sf.client_name,'')) LIKE '%national oil%' OR
                 lower(coalesce(sf.client_name,'')) LIKE '%state-owned%' OR
                 lower(coalesce(sf.client_name,'')) LIKE '%national bank%' OR
                 lower(coalesce(sf.client_name,'')) LIKE '%republic of%' OR
                 lower(coalesce(sf.client_name,'')) LIKE '%kingdom of%' OR
                 lower(coalesce(sf.client_name,'')) LIKE '%ministry of%' OR
                 lower(coalesce(sf.client_name,'')) LIKE '%embassy of%')::int AS sig_soe_pattern,
                sf.url
            FROM norm_sf sf
            LEFT JOIN activity_text actv ON actv.filing_uuid = sf.filing_uuid
            LEFT JOIN fp_country_for_filing fp ON fp.filing_uuid = sf.filing_uuid
            WHERE NOT EXISTS (SELECT 1 FROM norm_fara nf WHERE nf.norm_r = sf.norm_r)
              AND (
                  (sf.client_country IS NOT NULL AND sf.client_country NOT IN ('US','United States of America'))
               OR (sf.client_ppb_country IS NOT NULL AND sf.client_ppb_country NOT IN ('US','United States of America'))
               OR (lower(coalesce(actv.act_text,'')) LIKE '%foreign government%' OR
                   lower(coalesce(actv.act_text,'')) LIKE '%embassy%' OR
                   lower(coalesce(actv.act_text,'')) LIKE '%fara%' OR
                   lower(coalesce(actv.act_text,'')) LIKE '%sanctions%' OR
                   lower(coalesce(actv.act_text,'')) LIKE '%ambassador%')
               OR (lower(coalesce(sf.client_name,'')) LIKE '%national oil%' OR
                   lower(coalesce(sf.client_name,'')) LIKE '%state-owned%' OR
                   lower(coalesce(sf.client_name,'')) LIKE '%national bank%' OR
                   lower(coalesce(sf.client_name,'')) LIKE '%republic of%' OR
                   lower(coalesce(sf.client_name,'')) LIKE '%kingdom of%' OR
                   lower(coalesce(sf.client_name,'')) LIKE '%ministry of%' OR
                   lower(coalesce(sf.client_name,'')) LIKE '%embassy of%')
              )
            ORDER BY sf.income DESC NULLS LAST
            LIMIT {limit}
        """,
    },
    "D11": {
        "name": "revolving_door_committee_match",
        "description": "Multi-hop: lobbyist's covered_position references a committee/member; that lobbyist now lobbies clients whose activities mention the same committee. Surfaces conflict-of-interest patterns by SQL alone (no embeddings).",
        "params": {"limit": 200},
        "sql": """
            WITH lobbyist_positions AS (
                -- Distinct lobbyist + covered_position pairs with relevant keywords
                SELECT DISTINCT
                    lobbyist_id, first_name, last_name, covered_position,
                    -- Extract committee acronym/name from covered_position text
                    CASE
                        WHEN lower(covered_position) LIKE '%armed services%' THEN 'armed_services'
                        WHEN lower(covered_position) LIKE '%ways and means%' THEN 'ways_means'
                        WHEN lower(covered_position) LIKE '%appropriation%' THEN 'appropriations'
                        WHEN lower(covered_position) LIKE '%finance%' THEN 'finance'
                        WHEN lower(covered_position) LIKE '%judiciary%' THEN 'judiciary'
                        WHEN lower(covered_position) LIKE '%intelligence%' THEN 'intelligence'
                        WHEN lower(covered_position) LIKE '%foreign relations%' THEN 'foreign_relations'
                        WHEN lower(covered_position) LIKE '%foreign affairs%' THEN 'foreign_affairs'
                        WHEN lower(covered_position) LIKE '%energy and commerce%' OR lower(covered_position) LIKE '%energy & commerce%' THEN 'energy_commerce'
                        WHEN lower(covered_position) LIKE '%homeland security%' THEN 'homeland_security'
                        WHEN lower(covered_position) LIKE '%veterans%' THEN 'veterans_affairs'
                        WHEN lower(covered_position) LIKE '%health%' THEN 'health'
                        WHEN lower(covered_position) LIKE '%agriculture%' THEN 'agriculture'
                        ELSE NULL
                    END AS former_committee
                FROM senate_activity_lobbyists
                WHERE covered_position IS NOT NULL AND length(covered_position) >= 12
            ),
            current_activities AS (
                -- Current activities of those lobbyists; check if topic matches their former committee
                SELECT
                    al.lobbyist_id,
                    f.filing_uuid, f.filing_year, f.filing_period,
                    f.registrant_name, f.client_name, f.income,
                    a.general_issue_code, a.description, f.url
                FROM senate_activity_lobbyists al
                JOIN senate_lobbying_activities a USING (filing_uuid)
                JOIN senate_filings f USING (filing_uuid)
                WHERE f.filing_year IN (2024, 2025, 2026)
                  AND f.filing_type IN ('Q1','Q2','Q3','Q4')
            )
            SELECT
                lp.lobbyist_id, lp.first_name, lp.last_name,
                lp.former_committee, lp.covered_position,
                ca.filing_uuid, ca.filing_year, ca.filing_period,
                ca.registrant_name, ca.client_name, ca.general_issue_code,
                ca.description, ca.income, ca.url
            FROM lobbyist_positions lp
            JOIN current_activities ca USING (lobbyist_id)
            WHERE lp.former_committee IS NOT NULL
              AND (
                  (lp.former_committee = 'armed_services'   AND ca.general_issue_code IN ('DEF','HOM','INT')) OR
                  (lp.former_committee = 'ways_means'       AND ca.general_issue_code IN ('TAX','BUD','TRD','HCR')) OR
                  (lp.former_committee = 'appropriations'   AND ca.general_issue_code IN ('BUD','DEF','HCR','EDU')) OR
                  (lp.former_committee = 'finance'          AND ca.general_issue_code IN ('TAX','BUD','BAN','FIN')) OR
                  (lp.former_committee = 'judiciary'        AND ca.general_issue_code IN ('LAW','IMM','BNK','CON','CIV')) OR
                  (lp.former_committee = 'intelligence'     AND ca.general_issue_code IN ('INT','DEF','HOM','CSP')) OR
                  (lp.former_committee = 'foreign_relations' AND ca.general_issue_code IN ('FOR','TRD','DEF')) OR
                  (lp.former_committee = 'foreign_affairs'  AND ca.general_issue_code IN ('FOR','TRD','DEF')) OR
                  (lp.former_committee = 'energy_commerce'  AND ca.general_issue_code IN ('ENG','HCR','TEC','TRA','CPT')) OR
                  (lp.former_committee = 'homeland_security' AND ca.general_issue_code IN ('HOM','IMM','CSP')) OR
                  (lp.former_committee = 'health'           AND ca.general_issue_code IN ('HCR','MED','HPI')) OR
                  (lp.former_committee = 'agriculture'      AND ca.general_issue_code IN ('AGR','FOO','TRD'))
              )
              AND ca.income IS NOT NULL
              AND ca.income > 0
            ORDER BY ca.income DESC NULLS LAST
            LIMIT {limit}
        """,
    },
    "D12": {
        "name": "committee_say_vs_pay",
        "description": "Joins three corpora: lobbying firms with revolving-door lobbyists, the committees those lobbyists previously staffed, current members of those committees, and press releases from those members criticizing the firms' top clients. Surfaces say-vs-pay patterns deterministically.",
        "params": {"limit": 200, "target_committee": "finance", "client_pattern": "%apollo%"},
        "sql": """
            WITH lobbyist_positions AS (
                SELECT DISTINCT lobbyist_id, first_name, last_name, covered_position
                FROM senate_activity_lobbyists
                WHERE lower(covered_position) LIKE '%' || '{target_committee}' || '%'
            ),
            current_committee_members AS (
                SELECT DISTINCT m.bioguide_id, m.name AS member_name, m.party, m.state, a.role
                FROM congress_committee_assignments a
                JOIN congress_members m USING (bioguide_id)
                WHERE lower(a.committee_name) LIKE '%' || '{target_committee}' || '%'
            ),
            press_attacks AS (
                SELECT pr.bioguide_id, pr.member_name, pr.date, pr.title, pr.url,
                       substr(pr.text, 1, 200) AS excerpt
                FROM press_releases pr
                WHERE lower(pr.text) LIKE '{client_pattern}'
                  AND lower(pr.text) LIKE '%private equity%'
            ),
            lobbying_for_target AS (
                SELECT DISTINCT f.filing_uuid, f.registrant_name, f.client_name, f.income,
                       lp.first_name AS lobbyist_first, lp.last_name AS lobbyist_last,
                       lp.covered_position
                FROM senate_filings f
                JOIN senate_activity_lobbyists al USING (filing_uuid)
                JOIN lobbyist_positions lp ON lp.lobbyist_id = al.lobbyist_id
                WHERE lower(f.client_name) LIKE '{client_pattern}'
                  AND f.filing_year IN (2024, 2025, 2026)
            )
            SELECT
                lft.registrant_name      AS lobbying_firm,
                lft.client_name          AS lobbied_client,
                lft.lobbyist_first || ' ' || lft.lobbyist_last AS lobbyist,
                lft.covered_position     AS former_role,
                (SELECT count(*) FROM current_committee_members) AS current_committee_members,
                (SELECT count(*) FROM press_attacks)             AS attack_press_releases,
                (SELECT count(DISTINCT member_name) FROM press_attacks
                 WHERE bioguide_id IN (SELECT bioguide_id FROM current_committee_members))
                                          AS committee_members_attacking,
                lft.income
            FROM lobbying_for_target lft
            ORDER BY lft.income DESC NULLS LAST
            LIMIT {limit}
        """,
    },
    "D8": {
        "name": "new_registrant_surge",
        "description": "New registrants (first filing in most recent 2 quarters) ranked by first-quarter income.",
        "params": {"limit": 200, "lookback_quarters": 2},
        "sql": """
            WITH first_filing AS (
                SELECT
                    registrant_id,
                    min(filing_year * 10 + CAST(substr(filing_type, 2, 1) AS INTEGER)) AS first_yp
                FROM senate_filings
                WHERE filing_type IN ('Q1','Q2','Q3','Q4')
                GROUP BY 1
            ),
            recent_qs AS (
                SELECT max(filing_year * 10 + CAST(substr(filing_type, 2, 1) AS INTEGER)) AS max_yp
                FROM senate_filings
                WHERE filing_type IN ('Q1','Q2','Q3','Q4')
            ),
            new_regs AS (
                SELECT ff.registrant_id, ff.first_yp
                FROM first_filing ff, recent_qs r
                WHERE ff.first_yp >= r.max_yp - {lookback_quarters}
            )
            SELECT
                f.registrant_id,
                any_value(f.registrant_name) AS registrant_name,
                count(DISTINCT f.filing_uuid) AS filings_in_window,
                count(DISTINCT f.client_id) AS distinct_clients,
                sum(coalesce(f.income, 0)) AS total_income,
                string_agg(DISTINCT f.client_name, ' | ') AS clients
            FROM senate_filings f
            JOIN new_regs nr ON f.registrant_id = nr.registrant_id
            WHERE f.filing_type IN ('Q1','Q2','Q3','Q4')
            GROUP BY 1
            HAVING total_income > 0
            ORDER BY total_income DESC
            LIMIT {limit}
        """,
    },
}


def list_detectors() -> None:
    print(f"{'ID':<4}  {'name':<30}  description")
    print("-" * 110)
    for did, d in DETECTORS.items():
        print(f"{did:<4}  {d['name']:<30}  {d['description']}")


# ---------------------------------------------------------------------------
# Execution + provenance
# ---------------------------------------------------------------------------

def sql_hash(sql: str) -> str:
    return hashlib.sha256(sql.encode()).hexdigest()[:16]


def execute_and_write(con: duckdb.DuckDBPyConnection, sql: str, name: str, out_dir: Path,
                      params: dict | None = None, db_path: str = "") -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    final_sql = sql.format(**(params or {})) if params else sql
    csv_path = out_dir / f"{name}.csv"
    prov_path = out_dir / f"{name}.provenance.json"

    start = time.time()
    result = con.execute(final_sql)
    columns = [(c[0], c[1]) for c in result.description]
    rows = result.fetchall()
    elapsed = time.time() - start

    with csv_path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow([c[0] for c in columns])
        w.writerows(rows)

    provenance = {
        "name": name,
        "db_path": db_path,
        "sql": final_sql,
        "sql_hash": sql_hash(final_sql),
        "params": params or {},
        "schema": [{"column": c[0], "type": str(c[1])} for c in columns],
        "row_count": len(rows),
        "elapsed_seconds": round(elapsed, 3),
        "executed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    prov_path.write_text(json.dumps(provenance, indent=2))

    print(f"  {name}: {len(rows):,} rows  ({elapsed:.2f}s)")
    print(f"    csv  → {csv_path}")
    print(f"    prov → {prov_path}")
    return csv_path


def main():
    ap = argparse.ArgumentParser(description="data-detective :: query")
    ap.add_argument("--db", type=Path, help="DuckDB index file")
    ap.add_argument("--out", type=Path, default=Path("./query_out"),
                    help="output directory (default: ./query_out)")
    grp = ap.add_mutually_exclusive_group()
    grp.add_argument("--detector", help="run a built-in detector by id (D1..D8) or 'all'")
    grp.add_argument("--sql", help="ad-hoc SQL string")
    grp.add_argument("--sql-file", type=Path, help="path to a .sql file")
    grp.add_argument("--list", action="store_true", help="list detectors and exit")
    ap.add_argument("--name", default=None, help="output name (defaults to detector id or sql-file stem)")
    ap.add_argument("--param", action="append", default=[],
                    help="override detector params: key=value (repeatable)")
    args = ap.parse_args()

    if args.list or args.detector == "list":
        list_detectors()
        return

    if not args.db:
        sys.exit("--db required unless --list")

    con = duckdb.connect(str(args.db), read_only=True)

    if args.detector:
        ids = list(DETECTORS.keys()) if args.detector == "all" else [args.detector]
        for did in ids:
            if did not in DETECTORS:
                print(f"unknown detector: {did}", file=sys.stderr)
                continue
            d = DETECTORS[did]
            params = dict(d["params"])
            for p in args.param:
                k, v = p.split("=", 1)
                # try int then float then leave as str
                try:
                    params[k] = int(v)
                except ValueError:
                    try:
                        params[k] = float(v)
                    except ValueError:
                        params[k] = v
            name = args.name or f"{did}_{d['name']}"
            execute_and_write(con, d["sql"], name, args.out, params=params, db_path=str(args.db))
    elif args.sql or args.sql_file:
        sql = args.sql or args.sql_file.read_text()
        name = args.name or (args.sql_file.stem if args.sql_file else "ad_hoc")
        execute_and_write(con, sql, name, args.out, db_path=str(args.db))
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
