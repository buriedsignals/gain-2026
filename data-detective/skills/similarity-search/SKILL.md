---
name: similarity-search
description: Vector similarity search over any free-text column in the data-detective DuckDB index using fastembed (ONNX, no torch) and DuckDB's VSS extension. Use when keyword detectors can't surface an anomaly — e.g. "find more filings that smell like LOC Nation" — by embedding the activity descriptions or press release texts and asking for nearest neighbors of a known anomaly. The skill ships ready-to-use as a complement to keyword-based detectors; not always needed because keyword detectors are cheaper and more auditable, but valuable when the anomaly is a semantic pattern rather than a string match. Use in Phase 3 of a data-detective investigation when a keyword detector fails to surface a suspected pattern. Triggers on "find similar records to X," "nearest neighbor search," "embed activity descriptions," or "discover anomalies by semantic similarity."
license: MIT
metadata:
  parent: data-detective
  step: P3_similarity (optional)
  inputs: DuckDB index, a text column
  outputs: nearest-neighbor results (id, distance, text)
---

# data-detective-similarity-search

Vector NN over any text column. Optional cycle-3 capability.

## When to use

Keyword detectors are the default. They are cheap, fast, and auditable (the SQL is the audit). Use this sub-skill when:

- You suspect a pattern but can't enumerate every keyword variation (e.g. sovereign-citizen-style filings might use any of a hundred different esoteric terms).
- You have one known anomaly and want to find "more like it" by meaning rather than by keyword.
- You want to cluster a free-text column to see what emerges (lobbying topic discovery).

Use the keyword detectors first. Reach for vector search only when keyword detection demonstrably fails.

## What it does

`scripts/vector_search.py` uses **fastembed** (ONNX-backed, no torch dependency) with the **BGE-small-en-v1.5** model (384-dim) and **DuckDB's VSS extension** for the HNSW index.

Two operations:

### 1. Embed a column

```bash
uv run scripts/vector_search.py \
  --db <index.duckdb> \
  --embed \
  --table senate_lobbying_activities \
  --text-column description \
  --id-column activity_id
```

Builds `_embed_<table>` with columns `(id VARCHAR PRIMARY KEY, embedding FLOAT[384])`. The HNSW index is created if VSS is available; otherwise falls back to brute-force NN.

**Budget:** ~5-15 minutes on CPU for 800K rows; first run downloads the ~30MB model.

### 2. Query nearest neighbors

By known anomalous row:

```bash
uv run scripts/vector_search.py \
  --db <index.duckdb> \
  --table senate_lobbying_activities \
  --query-id "<an activity_id from a known anomaly>" \
  --k 25
```

By text:

```bash
uv run scripts/vector_search.py \
  --db <index.duckdb> \
  --table senate_lobbying_activities \
  --query-text "Established sovereign government drafting constitution" \
  --k 25
```

Returns top-K records with (id, distance, text excerpt). Pipe IDs into `data-detective-evidence-cards` to inspect the actual records.

## Tradeoffs vs keyword detectors

| | Keyword detector | Vector search |
|---|---|---|
| Auditability | SQL is the audit | "embedding similarity" — less defensible per claim |
| Speed (query) | <1 second | <1 second (with HNSW) |
| Setup cost | None | ~10 min for first embedding |
| Recall on semantic variants | Misses unknown phrasings | Catches them |
| Recall on exact patterns | Catches them | May rank exact matches lower than semantic neighbors |

For journalism, prefer keyword detectors and use vector NN only as a discovery aid. Cite findings to the underlying records (via evidence cards), not to "embedding distance."

## Composes with

- Input ← `data-detective-ingest`
- Output → IDs fed back into `data-detective-evidence-cards` for record-level inspection
- Output → ad-hoc inputs into the investigator subagent's threading
