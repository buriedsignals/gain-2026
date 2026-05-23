# `data-detective` — methodology playbook

The investigation discipline, phase by phase. Read this when you have the
SKILL overview and want concrete guidance on running cycles.

The phases mirror `spotlight`'s investigation pattern (brief → methodology →
cycles → fact-check → gate → ingestion) but the **medium is records, not URLs**.
Where `spotlight` archives a webpage to anchor a claim, `data-detective`
anchors a claim to a `filing_uuid`, a `house_xml_filename`, or a `press_id`.

---

## Phase 0 — Brief

Before touching code, agree with the user on:

1. **The lead.** What might be going on? What would be newsworthy?
2. **The scope.** Which slices of the corpus? Whole time range or recent only?
3. **The angle.** Open exploration, or a specific hypothesis (e.g. revolving
   door, foreign influence, "say vs. pay")?
4. **Constraints.** Anything off-limits? Time budget?

Write the agreed direction to `case/brief-directions.txt`. The user signs off
before P1 begins. This is the **gate that prevents wasted infrastructure builds**.

---

## Phase 1 — Configure + Ingest

### Configuring a profile

A profile is a Python module that describes the corpus to `ingest.py`. The
worked example at `references/examples/lda_profile.py` is the template.

What you need to provide:

```python
NAME = "..."
DESCRIPTION = "..."

SOURCES = [
    {
        "id": "<unique_id>",
        "format": "json_array | jsonl | xml_dir",
        "glob": "<path/glob/relative/to/data-root>",
        "mapper": "<name_of_mapper_function_in_this_module>",
        "batch": 5000,  # optional
    },
    ...
]

TABLES = {
    "<table_name>": {
        "columns": {
            "<col>": "<SQL_TYPE>",
            ...
        }
    },
    ...
}

INDEXES = [("<table>", ["<col>", ...]), ...]

def <mapper_name>(record_or_xml_root, source_file) -> dict[str, list[dict]]:
    ...
    return {"<table>": [row, ...], ...}
```

### Running ingest

```bash
uv run scripts/ingest.py \
  --profile <profile.py> \
  --data-root <corpus_root> \
  --db case/index.duckdb \
  --manifest case/manifest.json
```

For development, restrict scope: `--source <id>`, `--year <YYYY>`, `--limit <n>`.

**Resumability:** `_ingest_checkpoints` records every (source, file, SHA-256)
ingested. Re-running is idempotent. Pass `--force` to re-ingest.

**Manifest:** `case/manifest.json` records per-table row counts and per-source
file/row totals. Commit this. It is the reproducibility receipt.

---

## Phase 2 — Resolve entities

```bash
uv run scripts/resolve_entities.py --db case/index.duckdb --out case/
```

The resolver runs three passes in strict order. Earlier passes are cheaper and
more defensible:

| Pass | Method | Cost | Confidence |
|---|---|---|---|
| 1 | Bridge keys (existing join fields) | O(n) join | Exact |
| 2 | Exact normalized name | O(n) hash join | High |
| 3 | Fuzzy (token_set_ratio ≥ threshold) | O(n · m) | Inspect ambiguity queue |

The `canonical_registrants` view unions all three. The report
(`entity-resolution-report.md`) tells you what fraction of entities resolved
and how many ambiguous matches need human review.

### Calibrating the fuzzy threshold

Default is 92. Lower to 88 if pass-3 coverage is thin and you can afford more
ambiguity-queue review. Higher to 95 if false positives are a concern.

### When to skip P2

If your corpus has only one source system (no cross-source join), entity
resolution is unnecessary; go straight to P3.

---

## Phase 3 — Anomaly detectors

```bash
uv run scripts/query.py --db case/index.duckdb --detector all --out case/anomalies
```

Detector outputs are **ranked candidate lists**, not findings. Each row is a
candidate for the investigator to chase. The investigator should:

1. Read the top N rows (default 50, never more than 500 per detector).
2. Pick threads worth chasing based on the user's brief.
3. For chosen threads, drill in via ad-hoc SQL through `query.py --sql`.
4. Only after a thread is promising, pull full records via `evidence_card.py`.

### Writing a new detector

Add to `DETECTORS` in `scripts/query.py`:

```python
"D9": {
    "name": "my_detector",
    "description": "What it catches and why",
    "params": {"limit": 200, "threshold": 1.5},
    "sql": "SELECT ... FROM ... WHERE ... LIMIT {limit}",
}
```

The SQL is a Python `str.format` template. Parameter overrides work via
`--param key=value`.

---

## Phase 4 — Investigator cycles

A cycle is one round of: read candidates → pick threads → drill via SQL → write
findings. Max 5 cycles before stall protocol.

**Discipline:**
- Update `case/state.json` after each cycle.
- Append to `case/investigation-log.json` for every significant action
  (query run, thread opened/closed, finding promoted to high-confidence).
- Every numeric statement in a finding must cite the SQL hash from a
  provenance JSON. No exceptions.

**Stop conditions:**
- 3+ findings at high confidence and 2+ independent sources each → exit to P5.
- 5 cycles done without convergence → stall protocol (user picks: more cycles,
  pivot angle, or accept current findings).

---

## Phase 5 — Fact-check

Two layers:

1. **Internal.** Re-run every cited query against the index, confirm the
   numbers match what the finding states. (A typo in a claim is a typo.)
2. **External.** For any claim that references context outside the corpus
   (FARA, FEC, news, a member's public statement), pull and archive that
   source via the `web-archiving` skill (or your client's equivalent) before
   citing.

Mark each claim's `fact_check_status` in `case/findings.json`. Write a brief
`case/fact-check.json` with the verdict and the archived URLs.

A high-confidence claim must have:
- An internal verification (query re-run, matched)
- At least one independent corroborating source (a second filing, a press
  release, an external archive — not a second SQL query against the same
  data)

---

## Phase 6 — Evidence cards

```bash
uv run scripts/evidence_card.py --db case/index.duckdb --source senate_filing \
                               --from-csv case/anomalies/D4_foreign_filings.csv \
                               --id-column filing_uuid \
                               --out case/cards
```

A card is **one source record rendered in full**, with the canonical public
URL linked at the top. The card is what an editor opens to verify a claim in
under a minute.

Cards are commodity outputs — generate them for any record you cite. They are
deterministic from the index, so cards generated from the same index will be
byte-identical (good for diffs).

---

## Phase 7 — Gate: editor review

Build `case/evidence-map.json` (the schema is in
[evidence-map-format.md](evidence-map-format.md)).

Build `case/findings-report.md` — the human narrative around the claims, with
links to each card.

Hand both to the editor. The editor signs off claim-by-claim. Anything that
fails moves back to P4 with a specific gap to close.

---

## Phase 8 — Submission packaging

For a competition or external deliverable:

- The skill directory (the canonical, generic, reusable artifact).
- The case workspace as the trace.
- A `README.md` mapping each finding to its supporting queries and cards.
- Interaction logs (your client's session transcripts), keyed to the skill
  invocations they came from.

Validate: `skills-ref validate path/to/data-detective`.

---

## Stall protocol

If 5 cycles complete and the exit criteria aren't met:

1. List the open gaps explicitly (in `case/state.json` → `open_questions`).
2. Present the user with three options:
   - Continue with more cycles (specify what changes about the next batch).
   - Pivot angle (re-enter at P3 with a different detector set, or change
     the brief at P0).
   - Accept current findings as-is, document limitations, and ship.

Do not silently extend cycles. Stall is a user decision, not an agent decision.
