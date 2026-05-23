# Profile format

A profile is a Python module that tells `scripts/ingest.py` how to map your
corpus into DuckDB. Profiles are the **portability seam** of `data-detective`
— a new corpus is a new profile, not a new fork of the skill.

## Required attributes

```python
NAME = "Lobbying Disclosure Act + Congressional Press"
DESCRIPTION = "Senate LDA filings & contributions, House LDA filings, Congressional press."

SOURCES = [
    {
        "id": "senate_filings",
        "format": "json_array",          # 'json_array' | 'jsonl' | 'xml_dir'
        "glob": "senate/{year}/filings/filings_{year}.json",
        "mapper": "map_senate_filing",   # function name in this module
        "batch": 5000,                   # rows accumulated before DB flush (optional)
    },
    ...
]
```

`format` values:
- `json_array` — file is one big JSON array; iterate elements.
- `jsonl` — file is newline-delimited JSON; iterate lines.
- `xml_dir` — `glob` resolves to a directory; iterate `*.xml` files in it.

`glob` can contain `{year}`; ingest expands across `2022..2026` (or restricts
with `--year`). Other placeholders are not currently supported — design glob
patterns to either include a year segment or be year-agnostic.

## Optional attributes

### `TABLES`

Explicit schemas. Strongly recommended for stable column types.

```python
TABLES = {
    "senate_filings": {
        "columns": {
            "filing_uuid": "VARCHAR PRIMARY KEY",
            "income": "DOUBLE",
            "filing_year": "INTEGER",
            ...
        }
    },
    ...
}
```

Without `TABLES`, ingest infers columns from the first batch of rows and
creates them as `VARCHAR`. Inferred schemas are fragile — define them.

### `INDEXES`

```python
INDEXES = [
    ("senate_filings", ["registrant_id"]),
    ("senate_filings", ["client_country"]),
    ("senate_lobbying_activities", ["general_issue_code"]),
]
```

Indexes are created once at the end of ingest. Pick the columns the detectors
join or filter on.

## Mapper contract

A mapper transforms one input record (or one parsed XML root) into rows for
one or more tables:

```python
def map_senate_filing(record: dict, source_file: Path) -> dict[str, list[dict]]:
    return {
        "senate_filings": [filing_row_dict],
        "senate_lobbying_activities": [activity_row_dict, ...],
        "senate_foreign_entities": [fe_dict, ...],
    }
```

For `xml_dir`:

```python
def map_house_xml(root: lxml.etree.Element, source_file: Path) -> dict[str, list[dict]]:
    ...
```

Return an empty dict `{}` to skip a record (e.g. malformed or filtered out).

Mappers should be **pure** (no side effects beyond returning rows) so ingest
can parallelize them in future versions without behavior changes.

## Patterns and tips

### Synthetic stable IDs

For child records (activities, contribution items), build IDs from the parent
ID and an index, so the same input always produces the same ID:

```python
activity_id = f"{filing_uuid}::a{index}"
```

This makes re-ingest idempotent and lets downstream tools (evidence cards,
queries) reference children by stable string keys.

### Bridge keys

If your source data has explicit cross-system IDs (House XML's `senateID`,
Senate registrant's `house_registrant_id`, bioguide IDs in press releases),
**preserve them as their own columns** in the mapped rows. The entity
resolver's Pass 1 depends on these.

If a bridge key needs parsing (e.g. House `senateID` is `"<registrant>-<client>"`),
extract the parts into separate columns at mapper time, not at query time.

### Strip and type at the mapper boundary

Don't let `"  "` (whitespace), `"$1,200"` (currency strings), or `"true"`/`""`
(boolean text) reach the database. Coerce at the mapper:

```python
from typing import Any

def _to_float(v: Any) -> float | None:
    if v in (None, "", " "): return None
    try: return float(str(v).strip().replace("$", "").replace(",", ""))
    except (ValueError, TypeError): return None
```

The worked example has tested helpers; copy them.

### Skip empty placeholder records

Many corpora include empty placeholder structures (e.g. `<foreignEntity/>`
elements in House XML when there are no foreign ties). Filter these in the
mapper — emit a row only if at least one meaningful field is populated.

## Validation

After ingest, verify the manifest with the corpus you expect:

```bash
uv run scripts/ingest.py --profile <profile> --data-root <root> --db <db>
# manifest written to <db>.manifest.json
```

Sanity checks (run against your DB):

```sql
-- 0% null on every primary key
SELECT count(*) FROM senate_filings WHERE filing_uuid IS NULL;

-- Reasonable distributions
SELECT filing_year, count(*) FROM senate_filings GROUP BY 1 ORDER BY 1;

-- Bridge-key coverage
SELECT count(DISTINCT registrant_id) AS senate_regs,
       count(DISTINCT registrant_house_id) FILTER (WHERE registrant_house_id IS NOT NULL) AS with_bridge
FROM senate_filings;
```

If any of these look off, the profile needs work before moving to P2.
