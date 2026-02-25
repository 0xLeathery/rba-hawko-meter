# Plan 20-01: Summary

**Phase:** 20 — Orchestration Tests and Enforcement
**Plan:** 20-01 — test_engine.py with engine_data_dir fixture
**Completed:** 2026-02-25
**Status:** Complete

## What Was Built

Added `engine_data_dir` fixture to `tests/python/conftest.py` and created `tests/python/test_engine.py` with 117 tests covering all 5 functions in `pipeline/normalize/engine.py`.

## Key Files

### Created
- `tests/python/test_engine.py` — 117 tests across 5 test classes

### Modified
- `tests/python/conftest.py` — added `engine_data_dir` fixture (patches `pipeline.normalize.engine.STATUS_OUTPUT` to `tmp_path/status.json`)

## Coverage Result

`pipeline/normalize/engine.py`: **96%** (target was 85%)

Uncovered lines (6): 208-211 (RISING/FALLING direction branches in business_confidence), 429-431 (`if __name__ == '__main__':` block — not callable from pytest).

## Test Summary

| Class | Tests | What it covers |
|-------|-------|----------------|
| TestGenerateInterpretation | 46 | All 8×5 zone combinations + 2 fallback cases |
| TestBuildGaugeEntry | 9 | Required fields, polarity, history cap, staleness, housing branch, business_confidence branch |
| TestBuildAsxFuturesEntry | 6 | None path, 7 direction thresholds, required fields, current_rate, meetings array, staleness |
| TestProcessIndicator | 5 | None from normalize, empty df, NaN z-scores, happy path, adaptive min_q |
| TestGenerateStatus | 8 | STATUS_OUTPUT isolation, public file not written, complete dict, confidence, empty gauges, ASX, JSON validity |

## Key Decisions

- `engine_data_dir` patches `pipeline.normalize.engine.STATUS_OUTPUT` (import site), not `pipeline.config.STATUS_OUTPUT` (source) — because `engine.py` binds at import time
- `MockDatetime` class freezes `datetime.now()` and `utcnow()` to `2026-02-25 12:00:00` while delegating `strptime`/`strftime` to real datetime
- `_mock_generate_status_deps()` context manager mocks 6 import-site dependencies for `generate_status()` tests

## Self-Check

- All 117 tests pass
- `ruff check` — zero violations
- engine.py coverage: 96% (well above 85% threshold)
- STATUS_OUTPUT isolation verified by `test_status_output_written_to_tmp_path_not_public`
- No test writes to `public/data/status.json`
