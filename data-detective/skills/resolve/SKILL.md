---
name: resolve
description: Three-pass entity resolution for a structured-records corpus — bridge keys first, exact normalized name second, fuzzy match third. Builds a canonical_registrants view in the DuckDB index that joins across House and Senate filings (or any two source systems with overlapping entity references). Designed to be deterministic where possible; only falls back to fuzzy matching for the residual. Use this sub-skill after data-detective-ingest to deduplicate and cross-link entities. Triggers on prompts mentioning entity resolution, deduplicating names across data sources, joining House LDA to Senate LDA, fuzzy matching with rapidfuzz, or any "match entity X across two databases."
license: MIT
metadata:
  parent: data-detective
  step: P2_resolve
  inputs: DuckDB index with bridge-key columns + name columns
  outputs: canonical_registrants view + ambiguity queue CSV
---

# data-detective-resolve

Three-pass entity resolution: bridge keys → exact normalized → fuzzy. Cheapest passes win first.

## When to use

Called from the `data-detective` orchestrator at Phase 2 (post-ingest, pre-detection). Also usable standalone whenever you have two related source systems whose entity names need to be deduplicated and cross-linked.

## Why three passes (in this order)

Most agentic approaches default to embedding-based fuzzy matching on every pair. That is:
- Expensive (compute + LLM tokens)
- Lossy (false positives on common org-name patterns)
- Undefensible to an editor ("we used embeddings" is not source provenance)

The deterministic-first three-pass approach gets >99% of matches via bridge keys alone on the LDA corpus. Only the residual goes to fuzzy.

| Pass | Method | Cost | Confidence |
|---|---|---|---|
| 1 | Bridge keys (existing join fields, e.g. Senate `registrant.id` ↔ House `senateID` first segment) | O(n) join | Exact |
| 2 | Exact normalized name (uppercase, strip punctuation, drop incorporation suffixes) | O(n) hash join | High |
| 3 | Fuzzy (`rapidfuzz.token_set_ratio` ≥ threshold) on the residual | O(n × m) | Inspect ambiguity queue |

## How to invoke

```bash
uv run scripts/resolve_entities.py \
  --db <index.duckdb> \
  --out <case_dir> \
  [--fuzzy-threshold 92]   # default 92
```

Outputs:

- View `canonical_registrants` in the DB joining all three pass results
- `<case>/entity-resolution-report.md` with counts per pass and overall coverage %
- `<case>/entity-resolution-ambiguous.csv` with the manual-review queue (fuzzy ties within 2 points)

## Normalization

The normalizer strips:
- Whitespace and punctuation
- Common incorporation suffixes: LLC, LLP, INC, INCORPORATED, CORP, CORPORATION, CO, COMPANY, PLLC, P.A., PA, CONSULTING, GROUP, PARTNERS, HOLDINGS, GMBH, AG, SA, SARL, LIMITED, LTD, PLC, PTY, N.V., NV, BV, B.V.

This handles "BROWNSTEIN HYATT FARBER SCHRECK, LLP" → "BROWNSTEIN HYATT FARBER SCHRECK", which exact-matches the corresponding House registrant.

## Calibration

- Lower `--fuzzy-threshold` to 88 if pass-3 coverage is thin and you can handle more ambiguity-queue review.
- Higher (95) if false positives are a concern.

## Composes with

- Input ← `data-detective-ingest`
- Output → `data-detective-detect` (detectors use canonical IDs)
- Output → `data-detective-passover` (Spotlight gets canonical names for OSINT)
