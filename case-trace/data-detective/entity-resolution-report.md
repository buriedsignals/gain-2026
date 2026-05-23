# Entity Resolution Report

- Senate distinct registrant IDs: **6,633**
- House distinct organization_names: **7,391**
- Senate IDs matched to a House org: **6,517** (98.3%)
- Ambiguity queue (manual review): **1**
- Fuzzy threshold (token_set_ratio): **92**

## Match counts by pass

| pass | matches |
|---|---|
| bridge_senate_id | 7,451 |
| exact_normalized | 2 |
| fuzzy | 5 |

Ambiguity queue dumped to `entity-resolution-ambiguous.csv` (1 rows).
