---
name: ingest
description: Profile-driven ETL from a structured-records corpus (XML, JSON, JSONL) into a single DuckDB index with deterministic schemas, bridge-key columns preserved, and a manifest of source-file SHA-256 hashes for reproducibility. Use this sub-skill at Phase 1 of a data-detective investigation, or standalone to build a queryable index over any corpus that fits the profile contract (file globs → mapper functions). Used by the data-detective orchestrator. Triggers on prompts mentioning corpus ingestion, building a DuckDB index, ETL from XML/JSON to a database, lobbying-records-to-database, or any "I have a folder of structured files and want to query them as a single database."
license: MIT
metadata:
  parent: data-detective
  step: P1_ingest
  inputs: corpus directory, profile.py
  outputs: DuckDB index, manifest.json
---

# data-detective-ingest

Generic corpus → DuckDB index ETL, profile-driven.

## When to use

Called from the `data-detective` orchestrator at Phase 1 (Methodology → first action). Also usable standalone for any structured-records corpus you want to query as a single database.

## What it does

`scripts/ingest.py` reads a *profile* Python module that declares:

- `SOURCES`: list of file-glob + mapper-function descriptors
- `TABLES`: explicit DuckDB schemas (column → SQL type)
- `INDEXES`: columns to index after load
- mapper functions: transform one input record (or parsed XML root) into rows for one or more tables

The framework iterates each source, calls the mapper, batches rows into pyarrow Tables, and bulk-inserts via `INSERT ... SELECT FROM <registered batch>`. The pyarrow path is **60× faster** than naive `executemany`.

Checkpointed: each (source, file, SHA-256) is recorded in `_ingest_checkpoints`. Re-runs are idempotent.

## How to invoke

```bash
uv run scripts/ingest.py \
  --profile <path/to/profile.py> \
  --data-root <corpus-root> \
  --db <out.duckdb> \
  --manifest <out.manifest.json> \
  [--source <source_id>]      # restrict to one source
  [--year <YYYY>]              # restrict to one year (filters {year} in glob)
  [--limit <n>]                # cap records per source (smoke test)
  [--force]                    # re-ingest files in checkpoint table
```

Manifest output records per-table row counts and per-source file/row totals plus source-file SHA-256 hashes. **Commit this file.** It is the reproducibility receipt.

## Writing a profile

A profile is a Python module. The worked example at `scripts/examples/lda_profile.py` is the template — it ingests:

- Senate LDA filings + contributions (JSON arrays per year)
- House LDA filings (XML per filing)
- Congressional press releases (JSONL by month)

Full contract: see [PROFILE-FORMAT.md](PROFILE-FORMAT.md).

## Key patterns the framework enforces

- **Strip and type at the mapper boundary.** Don't let `"  "` or `"$1,200"` reach the database.
- **Synthetic stable IDs for child records** built from parent ID + index (e.g. `filing_uuid::a3`) so re-ingest is idempotent.
- **Bridge keys preserved as their own columns.** If your source has cross-system IDs (Senate `house_registrant_id`, House `senateID`, bioguide_id), preserve them. The resolver (data-detective-resolve) uses them in Pass 1.
- **Skip empty placeholder records.** Many XML corpora include `<foreignEntity/>` placeholders; filter those in the mapper.

## Sanity checks

After ingest, verify:

```sql
SELECT count(*) FROM <table> WHERE <pk> IS NULL;          -- expect 0
SELECT filing_year, count(*) FROM senate_filings GROUP BY 1 ORDER BY 1;
SELECT count(DISTINCT registrant_id) FROM senate_filings;
```

Manifest committed at `<db>.manifest.json` is the contract. Any drift between an evaluator's corpus and yours surfaces as a hash mismatch.

## Composes with

- Output → `data-detective-resolve` (entity resolution)
- Output → `data-detective-detect` (detector battery)
- Output → `data-detective-external-data` (FARA/Congress.gov pull into same index)
