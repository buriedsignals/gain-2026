# Evidence map format

`case/evidence-map.json` is the audit ledger that connects claims to source
records and SQL queries. An editor reads this to verify a finding without
re-doing the work.

## Top-level shape

```json
{
  "schema_version": "1.0",
  "case_id": "northwestern-gain-challenge",
  "generated_at": "2026-05-22T10:00:00Z",
  "db_path": "case/index.duckdb",
  "claims": {
    "C-001": { /* claim object */ },
    "C-002": { ... },
    ...
  }
}
```

## Claim object

```json
{
  "statement": "<one-sentence claim, written as it appears in the findings report>",
  "confidence": "high | medium | low",
  "category": "spending | revolving_door | foreign_influence | data_quality | other",
  "supporting_query_hashes": [
    "<sha16>",
    "<sha16>"
  ],
  "supporting_cards": [
    "senate_filing_<uuid>.md",
    "house_filing_<filename.xml>.md",
    "press_release_<press_id>.md"
  ],
  "external_sources": [
    {
      "url": "https://efile.fara.gov/...",
      "fetched_at": "2026-05-22T11:23:00Z",
      "archive_path": "case/external/fara_<slug>.html",
      "wayback_url": "https://web.archive.org/web/.../..."
    }
  ],
  "fact_check_status": "pending | verified | partially_verified | disputed | unable_to_verify",
  "fact_check_notes": "<freeform>",
  "limitations": [
    "<known weakness — e.g. 'numbers exclude termination filings'>"
  ]
}
```

## Rules

- **Every numeric statement** in `statement` must be reproducible by re-running
  one of the queries identified by `supporting_query_hashes`. If a number in
  the statement can't be tied to a query, it doesn't belong in the claim.
- **Every named record** (filing, lobbyist, member) must have a matching
  evidence card in `supporting_cards`.
- **External sources** are archived before citing. The `archive_path` is the
  local copy; the `wayback_url` is the public copy (when available).
- **No claim with empty `supporting_cards`.** A claim with no evidence is an
  open question and lives in `case/state.json → open_questions` instead.
- **Claim IDs are stable.** Use `C-001`, `C-002`, ... in append order. Don't
  renumber.

## Companion files

- `case/findings.json` — the same claims in append-only working form during the
  investigation. `evidence-map.json` is the **frozen, gate-approved subset** at
  P7.
- `case/findings-report.md` — the human-readable narrative, with hyperlinks
  into the cards.
- `case/anomalies/<detector>.provenance.json` — per-query provenance receipts.
  The `sql_hash` here is what `supporting_query_hashes` refers to.

## Generation

The evidence map is built once at Gate 1 (P7) from the validated subset of
`findings.json`. There is no automatic generator — the orchestrator writes it
during synthesis. The validation rule is that every claim ID present in
`findings.json` with `confidence in (high, medium)` and
`fact_check_status in (verified, partially_verified)` must appear in the
evidence map, and every claim in the evidence map must satisfy the rules
above.
