---
phase: 12-python-unit-tests
plan: 01
subsystem: testing
tags: [pytest, numpy, pandas, zscore, mad, gauge, hawk-score, parametrize, unit-tests]

# Dependency graph
requires:
  - phase: 11-test-foundation
    provides: conftest.py with isolate_data_dir, block_network autouse fixtures and fixture CSV loaders
provides:
  - 60 unit tests covering zscore.py and gauge.py mathematical core
  - Regression detection spike test that catches formula regressions in compute_rolling_zscores
  - Parametrized boundary tests for all 5 gauge zones and all 5 verdict thresholds
  - Hand-calculated known-answer tests for calculate_mad with documented derivations
affects: [phase-13, phase-14, phase-15]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Top-level test functions (no classes) per project convention"
    - "@pytest.mark.parametrize for boundary value tables"
    - "pytest.approx(expected, rel=1e-4) for floating-point comparisons; abs=1e-9 when expected==0"
    - "_make_df helper pattern for constructing minimal date/value DataFrames inline"
    - "Regression detection via known-spike synthetic DataFrame"

key-files:
  created:
    - tests/python/test_zscore.py
    - tests/python/test_gauge.py
  modified: []

key-decisions:
  - "No test classes — all top-level test functions per user decision from Phase 11"
  - "Hand-calculated expected MAD values documented in test docstrings with full derivation"
  - "Regression detection test uses stable values 2.0 + spike to 10.0 at row 8 with assertion z_score > 1.5"
  - "compute_hawk_score tested with exclude_benchmark=True to verify asx_futures exclusion works correctly"

patterns-established:
  - "Known-answer pattern: document the manual calculation in docstring, then assert pytest.approx(expected)"
  - "Regression detection pattern: stable-value series + spike row + assert z > threshold"
  - "Boundary table pattern: parametrize with exact threshold values (e.g. 19.9/20.0, 39.9/40.0)"

requirements-completed: [UNIT-01, UNIT-02]

# Metrics
duration: 3min
completed: 2026-02-25
---

# Phase 12 Plan 01: Python Unit Tests (zscore + gauge) Summary

**60 parametrized unit tests for zscore.py and gauge.py with hand-calculated known-answer cases, exact boundary tables for all 5 zones, and a regression detection spike test**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-24T23:15:20Z
- **Completed:** 2026-02-25T00:00:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- 19 tests for zscore.py: 5 calculate_mad known-answer cases with documented derivations, 3 robust_zscore cases including zero-MAD guard, 5 compute_rolling_zscores cases including fixture data and regression detection spike test, 6 parametrized determine_confidence cases
- 41 tests for gauge.py: 9 zscore_to_gauge parametrized cases including NaN passthrough and custom clamp, 12 classify_zone boundary cases at exact thresholds 20/40/60/80, 6 compute_hawk_score cases including rebalancing and benchmark exclusion, 14 generate_verdict boundary cases
- Full suite grows from 30 to 90 tests, all passing in 0.11s combined with no live I/O

## Task Commits

Each task was committed atomically:

1. **Task 1: Create test_zscore.py** - `5d1c13a` (feat)
2. **Task 2: Create test_gauge.py** - `8ba55fe` (feat)

**Plan metadata:** (docs commit, see below)

## Files Created/Modified
- `tests/python/test_zscore.py` - Unit tests for calculate_mad, robust_zscore, compute_rolling_zscores, determine_confidence (260 lines, 19 tests)
- `tests/python/test_gauge.py` - Unit tests for zscore_to_gauge, classify_zone, compute_hawk_score, generate_verdict (251 lines, 41 tests)

## Decisions Made
- No test classes: all top-level test functions per user decision from Phase 11
- Hand-calculated MAD values documented in docstrings so a reader can verify the math without running code
- Regression detection test uses real numerical difference: stable values around 2.0, spike to 10.0 at row 8, asserts z_score > 1.5 with explicit failure message naming the formula regression as cause
- compute_hawk_score rebalancing test manually verified: inflation(0.4) + wages(0.4) with spending(0.2) missing = (60*0.4 + 40*0.4) / 0.8 = 50.0

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Mathematical core (zscore.py, gauge.py) is now guarded by 60 unit tests
- A regression in calculate_mad, robust_zscore, or compute_rolling_zscores will produce a clear assertion failure, not silent corruption
- Ready for Phase 13 (integration tests or CI hook integration)

## Self-Check: PASSED

- tests/python/test_zscore.py: FOUND
- tests/python/test_gauge.py: FOUND
- .planning/phases/12-python-unit-tests/12-01-SUMMARY.md: FOUND
- Commit 5d1c13a (feat: zscore tests): FOUND
- Commit 8ba55fe (feat: gauge tests): FOUND

---
*Phase: 12-python-unit-tests*
*Completed: 2026-02-25*
