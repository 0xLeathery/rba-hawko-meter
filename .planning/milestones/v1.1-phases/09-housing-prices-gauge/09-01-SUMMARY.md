---
phase: 09-housing-prices-gauge
plan: 01
subsystem: pipeline + frontend
tags: [housing, abs-rppi, gauge, interpretations, playwright]
dependency-graph:
  requires: []
  provides: [corelogic_housing.csv, housing-gauge-in-status.json, housing-card-frontend]
  affects: [public/data/status.json, dashboard-indicator-count]
tech-stack:
  added: []
  patterns: [abs-sdmx-fetch, yoy-normalization, quarter-label-js]
key-files:
  created:
    - data/corelogic_housing.csv
    - .planning/phases/09-housing-prices-gauge/09-01-SUMMARY.md
  modified:
    - pipeline/config.py
    - pipeline/ingest/abs_data.py
    - pipeline/normalize/engine.py
    - public/js/interpretations.js
    - tests/dashboard.spec.js
    - public/data/status.json
decisions:
  - Neutral zone threshold set to +/-1% for STEADY label (low in practice with ABS data ending 2021-Q4 at +23.67%)
  - data_source mapped from 'ABS' to 'ABS RPPI' in engine.py for display clarity
  - stale_display field added per-indicator (only set for housing) to control amber border suppression
key-decisions:
  - data_source field injected by reading raw CSV in build_gauge_entry() to preserve source column lost during z-score normalization
  - stale_display: 'quarter_only' suppresses amber border; toQuarterLabel() in JS doubles as staleness signal
metrics:
  duration: 6 minutes
  completed: 2026-02-24
  tasks-completed: 2
  files-modified: 6
  files-created: 1
  commits: 2
---

# Phase 9 Plan 01: Housing Prices Gauge (ABS RPPI Pipeline + Frontend) Summary

**One-liner:** ABS RPPI data fetched (74 quarterly rows 2003-2021) activating housing gauge with directional labels, quarter format, source attribution, and no amber staleness border.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | ABS RPPI pipeline integration + housing gauge activation in engine | 0acf4cf | pipeline/config.py, pipeline/ingest/abs_data.py, pipeline/normalize/engine.py, data/corelogic_housing.csv, public/data/status.json |
| 2 | Frontend housing gauge customization + Playwright test | 8dedb97 | public/js/interpretations.js, tests/dashboard.spec.js |

## What Was Built

### Task 1: ABS RPPI Pipeline Integration

Added the Residential Property Price Index (RPPI) data source to the pipeline using the existing ABS SDMX API pattern:

- `pipeline/config.py`: Added `ABS_CONFIG["rppi"]` with dataflow `RPPI`, key `1.3.100.Q`, `startPeriod=2002`. Updated `OPTIONAL_INDICATOR_CONFIG["housing"]` to activate: `csv_file="corelogic_housing.csv"`, `frequency="quarterly"`, `yoy_periods=4`.
- `pipeline/ingest/abs_data.py`: Added `fetch_rppi()` following `fetch_building_approvals()` pattern. Registered `'rppi'` in `FETCHERS` dict.
- `pipeline/normalize/engine.py`: Added housing-specific block in `build_gauge_entry()` that reads raw CSV to extract `source` column (lost during z-score normalization), maps `'ABS'` to `'ABS RPPI'` for display, and sets `stale_display='quarter_only'`. Fields `data_source` and `stale_display` added conditionally to gauge entry dict.
- `data/corelogic_housing.csv`: Populated with 74 quarterly rows from 2003-Q3 to 2021-Q4. Columns: `date, value, source, series_id`.

Result: Housing gauge active in `status.json` with `data_source="ABS RPPI"`, `stale_display="quarter_only"`, `raw_value=23.67%` YoY, `staleness_days=1607`. Housing removed from `indicators_missing` list. Dashboard coverage increases from 5 to 6 of 8 indicators.

### Task 2: Frontend Housing Gauge Customization

Updated `public/js/interpretations.js` with three housing-specific behaviours:

1. **`toQuarterLabel(isoDateStr)`**: New helper converting ISO date to quarter format `(Q4 2021)`. Exposed in module return object.
2. **Directional interpretation text**: Housing case in `generateMetricInterpretation()` replaced with RISING/FALLING/STEADY label logic. Neutral zone is +/-1% YoY. Output: `"RISING +23.7% year-on-year (Q4 2021)"`.
3. **Staleness suppression**: `stale` variable set to `false` for housing when `stale_display === 'quarter_only'` — prevents amber border despite 1607 staleness days.
4. **Source attribution**: `<div class="text-xs text-gray-500 mt-1">Source: ABS RPPI</div>` injected after "why it matters" section for housing cards.

Updated `tests/dashboard.spec.js` with:
- `Phase 9 — Housing Prices Gauge` describe block with two tests (directional label + source attribution; no amber border).
- Fixed existing test 2 card index assertions (housing now at index 3 shifts spending to 4, building approvals to 5).
- Updated comments in tests 3 and 5 from "5 active + 2 placeholder" to "6 active + 1 placeholder".

## Verification Results

All verification criteria passed:

```
PASS: housing in gauges
PASS: corelogic_housing.csv exists
PASS: data_source=ABS RPPI
PASS: stale_display=quarter_only
PASS: housing not in missing
PASS: staleness_days > 90
```

Playwright: 9/9 tests passing (2 new housing tests + 7 existing tests).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed card index assertions in existing Playwright test 2**
- **Found during:** Task 2 verification (full test suite run)
- **Issue:** Test 2 used `cards.nth(3)` to assert 'Consumer spending' and `cards.nth(4)` for 'Building Approvals'. These were written when housing was a placeholder (index 3 was spending). With housing now active at index 3, spending shifts to 4 and building approvals to 5.
- **Fix:** Updated assertions to `cards.nth(3)` for housing (RISING/FALLING/STEADY regex), `cards.nth(4)` for Consumer spending, `cards.nth(5)` for Building Approvals. Updated count comments from "5 active + 2 placeholder" to "6 active + 1 placeholder" in tests 2, 3, and 5.
- **Files modified:** tests/dashboard.spec.js
- **Commit:** 8dedb97

## Decisions Made

1. **Neutral zone threshold = +/-1% YoY**: Conservative range that maps to STEADY. With ABS data ending at +23.67% in 2021-Q4, RISING is always shown with current data.

2. **data_source read from raw CSV in build_gauge_entry()**: The z-score pipeline strips the `source` column — it only threads `date` and `value`. Reading `corelogic_housing.csv` directly in `build_gauge_entry()` when `name == 'housing'` is the correct pattern (documented in RESEARCH.md anti-patterns).

3. **Conditional dict extension for data_source/stale_display**: Rather than adding `None` values for all non-housing indicators, the entry dict is extended only when values are set. Keeps status.json schema clean.

## Self-Check: PASSED

All files exist and both task commits verified present (0acf4cf, 8dedb97).
