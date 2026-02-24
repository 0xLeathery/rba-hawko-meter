---
phase: 10-nab-capacity-utilisation-gauge
plan: 02
subsystem: pipeline/normalize + public/js + tests
tags: [frontend, gauge, interpretation, playwright, nab, capacity-utilisation]
dependency_graph:
  requires: [10-01]
  provides: [business_confidence frontend activation, capacity utilisation trend label]
  affects: [pipeline/normalize/engine.py, public/js/interpretations.js, public/js/gauges.js, public/data/status.json, tests/dashboard.spec.js, tests/phase6-ux.spec.js]
tech_stack:
  added: []
  patterns: [engine-indicator-enrichment, js-switch-case-interpretation, playwright-filter-locator]
key_files:
  created: []
  modified:
    - pipeline/normalize/engine.py
    - public/js/interpretations.js
    - public/js/gauges.js
    - public/data/status.json
    - tests/dashboard.spec.js
    - tests/phase6-ux.spec.js
decisions:
  - "Pass config param through build_gauge_entry()/process_indicator() — needed to access csv_file path for business_confidence enrichment"
  - "STEADY direction for Jan 2026 data — delta between Nov 2025 (83.6%) and Jan 2026 (83.6%) is 0.0pp, well within 0.5pp threshold"
  - "Long-run average computed as 83.0% from 7-month backfill — used as ABOVE/BELOW threshold in trend label"
  - "Coverage notice shows '7 of 8 indicators' — ASX futures is the 8th, shown separately in What Markets Expect section"
metrics:
  duration_seconds: 318
  completed_date: 2026-02-24
  tasks_completed: 2
  tasks_total: 2
  files_created: 0
  files_modified: 6
requirements_satisfied: [NAB-03, NAB-04]
---

# Phase 10 Plan 02: Business Conditions Frontend Activation Summary

**One-liner:** Business Conditions gauge activated with capacity utilisation trend label ("83.6% — ABOVE avg, STEADY"), source attribution, 45-day staleness threshold, inflation pressure framing, and all Playwright tests passing.

## What Was Built

### Task 1: engine.py enrichment (pipeline/normalize/engine.py)

Updated `build_gauge_entry()` with optional `config` parameter and a `business_confidence`-specific enrichment block:

- **`long_run_avg`**: Computed dynamically from `data/nab_capacity.csv` — 7-month backfill gives `83.0%`. Falls back to `81.0` if CSV missing or <2 rows.
- **`direction`**: Month-over-month delta between last two rows. With Jan 2026 (83.6%) vs Nov 2025 (83.6%), delta=0.0pp — within the 0.5pp threshold → `STEADY`.
- **`data_source`**: `"NAB Monthly Business Survey"` (hardcoded).
- **`raw_unit`**: Overridden from `'% YoY'` to `'%'` — capacity utilisation is an absolute percentage.
- Updated `generate_interpretation()` templates: cold/cool/neutral/warm/hot now reference "Capacity utilisation" instead of "Business confidence".
- Updated `process_indicator()` to pass `config=config` to `build_gauge_entry()`.

**Verification:** `public/data/status.json` shows `business_confidence.long_run_avg=83.0`, `direction=STEADY`, `data_source="NAB Monthly Business Survey"`, `raw_unit="%"`. `indicators_missing=[]`, `indicators_available=7`.

### Task 2: Frontend, interpretations, and Playwright tests

**public/js/gauges.js:**
- Changed `business_confidence: 'Capacity'` to `business_confidence: 'Business Conditions'` in `DISPLAY_LABELS`.

**public/js/interpretations.js:**
- Replaced `business_confidence` case in `generateMetricInterpretation()` — new format: `"83.6% — ABOVE avg, STEADY (Mar 2026)"` (reads `raw_value`, `long_run_avg`, `direction`, `data_date` from status.json).
- Updated `getWhyItMatters()` for `business_confidence`: inflation pressure framing — `'High capacity utilisation signals inflation pressure, making rate cuts less likely.'`
- Added 45-day staleness override for `business_confidence` in `renderMetricCard()`.
- Added source attribution block for `business_confidence` rendering `'Source: NAB Monthly Business Survey'`.

**tests/dashboard.spec.js:**
- Added `Phase 10 — Business Conditions Gauge` describe block with 2 tests:
  1. Trend label regex `/\d+\.\d+% — (?:ABOVE|BELOW) avg/` and source attribution.
  2. `'Lower importance'` badge and `'capacity utilisation'` in why-it-matters text.
- Updated existing card count comments from "6 active + 1 placeholder" to "7 active + 0 placeholder".

**tests/phase6-ux.spec.js:**
- Test 12: Updated comment from "5 active + 2 placeholder" to "7 active + 0 placeholder".
- Test 19: Changed coverage notice assertion from `'6 of 8 indicators'` to `'7 of 8 indicators'`.
- Test 20: Changed placeholder count assertion from `toHaveCount(1)` to `toHaveCount(0)`.

**Playwright result:** 28/28 tests passed.

## Verification Results

| Check | Result |
|-------|--------|
| engine produces business_confidence with long_run_avg | PASS — 83.0% from CSV |
| direction computed from month-over-month delta | PASS — STEADY (0.0pp delta <= 0.5pp) |
| data_source = "NAB Monthly Business Survey" | PASS |
| raw_unit = "%" | PASS |
| indicators_missing = [] | PASS — 7 available |
| Coverage notice shows "7 of 8 indicators" | PASS |
| Business Conditions card visible on dashboard | PASS |
| Trend label format regex match | PASS |
| Source attribution visible | PASS |
| Lower importance badge | PASS |
| Placeholder count = 0 | PASS |
| All Playwright tests | PASS — 28/28 |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Missing config param in build_gauge_entry() signature**
- **Found during:** Task 1 implementation
- **Issue:** The plan's implementation code used `config.get('csv_file', '')` but `build_gauge_entry()` had no `config` parameter. The business_confidence enrichment block needed CSV path access which is only in the indicator config dict.
- **Fix:** Added optional `config=None` parameter to `build_gauge_entry()`, updated `process_indicator()` call to pass `config=config`. Inside the block, used `_config = config or {}` for safe fallback.
- **Files modified:** `pipeline/normalize/engine.py`
- **Commit:** 7cc1518

## Auth Gates

None.

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| Task 1 | 7cc1518 | feat(10-02): enrich business_confidence gauge entry with direction, long-run avg, and source |
| Task 2 | 9c517ce | feat(10-02): frontend interpretation, display label, staleness, attribution, Playwright tests |

## Self-Check: PASSED

- pipeline/normalize/engine.py: FOUND (long_run_avg block present)
- public/js/gauges.js: FOUND (Business Conditions label)
- public/js/interpretations.js: FOUND (ABOVE/BELOW trend label case)
- tests/dashboard.spec.js: FOUND (Phase 10 describe block)
- tests/phase6-ux.spec.js: FOUND (7 of 8 indicators assertion)
- public/data/status.json: FOUND (long_run_avg=83.0, direction=STEADY)
- Commit 7cc1518: FOUND
- Commit 9c517ce: FOUND
