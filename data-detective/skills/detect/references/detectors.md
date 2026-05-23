# Detector catalog

The pre-built detector battery. Run via `scripts/query.py --detector <ID>` or `--detector all`. Every detector emits a CSV plus a `.provenance.json` with the SHA-16 hash of the executed SQL.

## D1 — `spending_spikes`

Registrant-quarter income z-score against the prior 4 quarters. Surfaces sudden 4-5× quarterly increases.

| Param | Default |
|---|---|
| `limit` | 200 |
| `min_z_abs` | 2.0 |
| `min_income` | 50000 |

## D2 — `missing_income_filings`

Quarterly filings where income is null. Clustered by registrant. The gap is itself reportable.

| Param | Default |
|---|---|
| `limit` | 200 |
| `min_filings` | 4 |

## D3 — `revolving_door_candidates`

Lobbyists whose `covered_position` text is populated. The first pass at the revolving-door surface.

| Param | Default |
|---|---|
| `limit` | 500 |

## D4 — `foreign_filings`

Senate filings with non-empty `foreign_entities[]`. Anchor for FARA cross-reference.

| Param | Default |
|---|---|
| `limit` | 500 |

## D5 — `single_client_juggernauts`

Registrants with 1-2 clients but very high income. Possible captive lobby shops, or unusual single-client cases (e.g. fictitious filings, sole-purpose trade associations).

| Param | Default |
|---|---|
| `limit` | 200 |
| `min_total_income` | 250000 |

## D6 — `pac_contribution_flow`

Aggregate `senate_contribution_items` by payee + honoree. Reveals who lobbyists' PACs are funding.

| Param | Default |
|---|---|
| `limit` | 500 |

## D7 — `issue_concentration_shifts`

Issue-code QoQ deltas. Surfaces emerging issues by registrant count + total income.

| Param | Default |
|---|---|
| `limit` | 500 |
| `min_qoq_delta_pct` | 25 |

## D8 — `new_registrant_surge`

New registrants (first filing in the most recent 2 quarters) ranked by first-quarter income.

| Param | Default |
|---|---|
| `limit` | 200 |
| `lookback_quarters` | 2 |

## D9 — `shell_pattern_filings`

Multi-signal score for sovereign-citizen / fake-filer patterns. Six signals: sovereign-government client description, established-government language, esoteric terms ("Annuit Coeptis" / "Empress" / "sui generis"), self-styled-title covered_position, LLC-slash posted_by format, Global Public Benefit Corporation naming. Score 0-6.

| Param | Default |
|---|---|
| `limit` | 100 |
| `min_score` | 2 |

## D10 — `fara_gap_narrowed`

LDA filings with foreign-government-policy lobbying topics, non-US client country, or state-owned-enterprise client naming, where the registrant is **not** in FARA. Promotes the aggregate FARA gap from a methodology critique to a named candidate list.

| Param | Default |
|---|---|
| `limit` | 200 |

## D11 — `revolving_door_committee_match`

Multi-hop SQL: lobbyist's `covered_position` text references a committee/member; that lobbyist now lobbies clients whose activities match the same committee's jurisdiction. Surfaces conflict-of-interest patterns deterministically.

Maps covered_position text → committee acronym for 12 major committees (Armed Services, Ways & Means, Appropriations, Finance, Judiciary, Intelligence, Foreign Relations/Affairs, Energy & Commerce, Homeland Security, Veterans, Health, Agriculture). Then matches each lobbyist's current lobbying activities to issue codes aligned with their former committee.

| Param | Default |
|---|---|
| `limit` | 200 |

## D12 — `committee_say_vs_pay`

Four-way multi-corpus join: lobbyists' covered_position → committee → **current** committee members → press releases attacking the lobbied client. Surfaces say-vs-pay patterns deterministically.

Requires the Congress.gov committee graph to be loaded (see `data-detective-external-data/scripts/congress_gov.py`).

| Param | Default |
|---|---|
| `limit` | 200 |
| `target_committee` | finance |
| `client_pattern` | `%apollo%` |

Override params for other committee × client combinations, e.g.:

```bash
uv run scripts/query.py --db <db> --detector D12 \
  --param target_committee=ways_means --param client_pattern=%palantir% \
  --out <case>/anomalies --name D12_ways_means_palantir
```

## Adding a new detector

Add an entry to `DETECTORS` in `scripts/query.py`:

```python
"D13": {
    "name": "my_detector",
    "description": "What it catches and why",
    "params": {"limit": 200, "threshold": 1.5},
    "sql": "SELECT ... FROM ... WHERE ... LIMIT {limit}",
},
```

The SQL is a Python `str.format` template; parameter overrides work via `--param key=value`.
