# Plan 20-02: Summary

**Phase:** 20 — Orchestration Tests and Enforcement
**Plan:** 20-02 — test_main.py + coverage enforcement wiring
**Completed:** 2026-02-25
**Status:** Complete

## What Was Built

1. Created `tests/python/test_main.py` with 16 tests covering all tier behaviors in `pipeline/main.py`
2. Added `load_weights` tests to `test_gauge.py` (gauge.py now 100%)
3. Added `load_asx_futures_csv` and `normalize_indicator` edge cases to `test_ratios.py` (ratios.py to 92%)
4. Wired `check_coverage.py --min 85` into `npm run test:fast` and `npm run verify:fast`
5. Wired `check_coverage.py --min 85` into `lefthook.yml` `unit-tests` command with 45s timeout

## Key Files

### Created
- `tests/python/test_main.py` — 16 tests covering all pipeline tier behaviors

### Modified
- `tests/python/test_gauge.py` — added `load_weights` tests (gauge.py 100%)
- `tests/python/test_ratios.py` — added `load_asx_futures_csv` and edge case tests
- `package.json` — test:fast and verify:fast now include coverage check
- `lefthook.yml` — unit-tests run includes coverage check, timeout bumped to 45s

## Coverage Results

| Module | Before | After |
|--------|--------|-------|
| main.py | 0% | 93% |
| gauge.py | 81% | 100% |
| ratios.py | 68% | 92% |

## All 13 pipeline/ modules at 85%+

```
abs_data.py          94%
asx_futures_scraper  90%
config.py           100%
corelogic_scraper    93%
csv_handler.py      100%
engine.py            96%
gauge.py            100%
http_client.py      100%
main.py              93%
nab_scraper.py       90%
ratios.py            92%
rba_data.py          93%
zscore.py            96%
```

## Test Summary (test_main.py)

| Test | What it verifies |
|------|-----------------|
| test_all_sources_succeed_returns_success | All 3 tiers succeed → status 'success' |
| test_critical_failure_calls_sys_exit_1 | sys.exit(1) caught by pytest.raises(SystemExit) |
| test_important_failure_returns_partial_with_failures_list | important_failures populated |
| test_optional_exception_returns_partial | optional exception → partial |
| test_optional_returns_failed_dict_marks_partial | scraper dict path → partial |
| test_normalization_not_available_is_skipped | NORMALIZATION_AVAILABLE=False → skipped |
| test_normalization_exception_is_non_fatal | normalization error non-fatal |
| test_first_critical_failure_exits_immediately | fail-fast: only first critical error fires |
| test_results_contains_run_date_in_iso_format | run_date ends with 'Z' |
| test_normalization_reports_hawk_score_and_indicators | normalization result fields |
| test_normalization_available_is_bool | module-level bool |
| test_critical_sources_is_list | CRITICAL_SOURCES structure |
| test_important_sources_is_list | IMPORTANT_SOURCES structure |
| test_optional_sources_is_list | OPTIONAL_SOURCES structure |

## Enforcement Wiring

**package.json test:fast:**
```
npm run lint && python -m pytest tests/python/ -m "not live" && python scripts/check_coverage.py --min 85
```

**lefthook.yml unit-tests:**
```yaml
run: pytest tests/python/ -m "not live" && python scripts/check_coverage.py --min 85
timeout: "45s"
```

## Self-Check

- All 411 unit tests pass
- `python scripts/check_coverage.py --min 85` exits 0
- `npm run test:fast` passes end-to-end (lint + tests + coverage)
- `pytest.raises(SystemExit)` with `exc_info.value.code == 1` — critical failure test works
- `ruff check` — zero violations on all test files
