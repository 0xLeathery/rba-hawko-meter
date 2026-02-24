---
phase: 12-python-unit-tests
plan: "02"
subsystem: python-tests
tags: [unit-tests, ratios, csv-handler, schema, jsonschema, yoy-normalization, hybrid-source]
dependency_graph:
  requires: [pipeline/normalize/ratios.py, pipeline/utils/csv_handler.py, pipeline/config.py, tests/python/conftest.py]
  provides: [tests/python/test_ratios.py, tests/python/test_csv_handler.py, tests/python/test_schema.py]
  affects: [pipeline/normalize/ratios.py]
tech_stack:
  added: [jsonschema StrictValidator (custom type checker), pytest.mark.parametrize]
  patterns: [tmp_path isolation, monkeypatch DATA_DIR, inline fixture construction, hybrid-source CSV testing]
key_files:
  created:
    - tests/python/test_ratios.py
    - tests/python/test_csv_handler.py
    - tests/python/test_schema.py
  modified:
    - pipeline/normalize/ratios.py
decisions:
  - "Use jsonschema StrictValidator (Draft7 + custom type_checker) to enforce hawk_score as Python int, not float"
  - "Auto-fixed load_indicator_csv to return None for header-only CSV (empty DataFrame was a missing correctness check)"
metrics:
  duration: "222s"
  completed: "2026-02-25"
  tasks_completed: 3
  files_created: 3
  files_modified: 1
---

# Phase 12 Plan 02: Pipeline Unit Tests Summary

Unit tests for ratios.py (YoY normalization, CSV loading, filtering, hybrid-source), csv_handler.py (dedup/append), and status.json schema contract — 54 new tests across 3 files, all passing in 0.14s with no real I/O.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create test_ratios.py | 9fc6f53 | tests/python/test_ratios.py, pipeline/normalize/ratios.py |
| 2 | Create test_csv_handler.py | 2627bfa | tests/python/test_csv_handler.py |
| 3 | Create test_schema.py | e2ad311 | tests/python/test_schema.py |

## Verification Results

```
tests/python/test_ratios.py      19 passed
tests/python/test_csv_handler.py  7 passed
tests/python/test_schema.py      28 passed
Full suite (not live):           118 passed in 0.14s
```

All success criteria met:
- test_ratios.py has 19 test functions covering load_indicator_csv, compute_yoy_pct_change, filter_valid_data, resample_to_quarterly, normalize_indicator (including hybrid path)
- test_csv_handler.py has 7 test functions covering create, append, dedup, sort, edge cases
- test_schema.py has 28 test functions covering valid/invalid documents, missing keys, type checking, range validation, enum validation
- Hybrid Cotality/ABS housing path explicitly tested with inline mixed-source CSV data
- status.json schema enforces hawk_score as Python integer, additionalProperties: false on overall
- Full suite passes in under 10 seconds (0.14s actual)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical Functionality] load_indicator_csv returned empty DataFrame for header-only CSV**
- **Found during:** Task 1 (test_load_indicator_csv_header_only)
- **Issue:** `load_indicator_csv` did not check for empty DataFrames after reading. A CSV with only a header row (`date,value\n`) would return an empty DataFrame instead of None, violating the documented contract.
- **Fix:** Added `if df.empty: return None` check after the column validation in `pipeline/normalize/ratios.py`.
- **Files modified:** `pipeline/normalize/ratios.py`
- **Commit:** 9fc6f53

**2. [Rule 1 - Bug] jsonschema default integer type accepts float 52.0**
- **Found during:** Task 3 (test_hawk_score_must_be_integer)
- **Issue:** jsonschema's default `"type": "integer"` accepts Python `52.0` (float with whole-number value) because the JSON spec treats integer as a subset of number. The user decision requires hawk_score to be a strict Python int.
- **Fix:** Created a `StrictValidator` using `Draft7Validator` extended with a custom type checker that enforces `isinstance(x, int) and not isinstance(x, (bool, float))`. All schema validations in test_schema.py use `_validate()` which delegates to StrictValidator.
- **Files modified:** `tests/python/test_schema.py`
- **Commit:** e2ad311

## Self-Check: PASSED
