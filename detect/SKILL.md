---
name: detect
description: Run a deterministic anomaly-detector battery and ad-hoc SQL against a DuckDB index of structured records, with SHA-tagged provenance per query. Includes a catalog of 12+ pre-built detectors (spending spikes, missing-data clusters, revolving-door candidates, foreign filings, single-client juggernauts, PAC contribution flow, issue concentration shifts, new-registrant surges, shell-pattern outliers, FARA-gap narrowing, multi-hop committee-jurisdiction match, committee say-vs-pay). Every query writes a CSV plus a provenance.json (SQL hash, schema, row count, timestamp) so claims can cite a specific query. Use this sub-skill at Phase 3 of a data-detective investigation. Triggers on prompts mentioning anomaly detection, lobbying detectors, revolving door SQL, FARA gap analysis, structured-records anomalies, or "what's weird in this database."
license: MIT
metadata:
  parent: data-detective
  step: P3_detect
  inputs: DuckDB index (post-resolve)
  outputs: ranked CSVs + provenance JSON per query
---

# data-detective-detect

Deterministic anomaly detection + ad-hoc SQL with audit-grade provenance.

## When to use

Called from the `data-detective` orchestrator at Phase 3 (Execution cycles). The investigator subagent reads the output CSVs to pick threads to chase — it does **not** scan raw documents during exploration.

## Two modes

### 1. Detector battery (pre-built catalog)

```bash
uv run scripts/query.py --list                 # see catalog
uv run scripts/query.py --db <db> --detector D5 --out <case>/anomalies
uv run scripts/query.py --db <db> --detector all --out <case>/anomalies
```

See [references/detectors.md](references/detectors.md) for the full catalog and the SQL templates. Each detector has:

- Stable ID (D1, D2, ...)
- Parameters (limit, thresholds) overridable with `--param key=value`
- A SQL template

### 2. Ad-hoc SQL with provenance

```bash
uv run scripts/query.py --db <db> --sql "SELECT ..."  --out <case>/anomalies
uv run scripts/query.py --db <db> --sql-file <file>   --out <case>/anomalies --name <output_name>
```

This is the path the investigator subagent uses to drill into a specific thread. Every run writes:

- `<name>.csv` — query results
- `<name>.provenance.json` — SQL hash (SHA-16), parameters, schema, row count, elapsed seconds, timestamp

**Every numeric claim in a finding cites a SHA-16 query hash.** Editors re-run the SQL to verify.

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

## Anti-patterns

- **No raw-document scanning.** The query layer is the only path through the corpus during exploration.
- **No ad-hoc SQL without provenance.** Every `--sql` invocation writes a `.provenance.json` automatically.
- **No claim referring to a detector by name only.** Cite the SHA-16 hash; a detector's SQL may evolve.

## Composes with

- Input ← `data-detective-ingest` (DuckDB index) + `data-detective-resolve` (canonical IDs)
- Output → host model / `spotlight:investigator` reads ranked CSVs
- Output → `data-detective-evidence-cards` (per-record card emission)
