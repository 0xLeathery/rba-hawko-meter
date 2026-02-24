---
phase: 08-asx-futures-live-data
plan: 01
subsystem: pipeline
tags: [python, pandas, asx-futures, staleness-detection, multi-meeting, github-actions, ci]

# Dependency graph
requires:
  - phase: 07-ci-pipeline
    provides: daily-asx-futures.yml CI workflow already running weekdays
provides:
  - pipeline/ingest/asx_futures_scraper.py with _check_staleness() (warn 14d / error 30d)
  - pipeline/normalize/ratios.py load_asx_futures_csv() returning meetings[] list (next 3-4 RBA meetings)
  - pipeline/normalize/engine.py build_asx_futures_entry() writing meetings[] array to status.json
  - .github/workflows/daily-asx-futures.yml with CSV freshness assertion step
  - public/data/status.json asx_futures.meetings[] with 4 upcoming meetings and meeting_date_label
affects: [09-housing-prices-gauge, frontend-asx-table-render, dashboard-spec-tests]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Non-fatal staleness: log warn/error but never raise — ASX is optional tier"
    - "Additive JSON contract extension: meetings[] added alongside all existing single-meeting fields"
    - "Cross-platform date day formatting: str(dt.day) instead of %-d (avoids Windows incompatibility)"
    - "CI freshness assertion with continue-on-error: stale data still commits, warning is sufficient"

key-files:
  created: []
  modified:
    - pipeline/ingest/asx_futures_scraper.py
    - pipeline/normalize/ratios.py
    - pipeline/normalize/engine.py
    - .github/workflows/daily-asx-futures.yml
    - public/data/status.json

key-decisions:
  - "continue-on-error: true on CI freshness step — intermittent ASX outages must not block data commits"
  - "meetings[] is additive — all existing single-meeting fields retained for backward compatibility"
  - "Cross-platform day formatting via str(dt.day) rather than %-d strftime directive"

patterns-established:
  - "Staleness check called inside success branch of fetch_and_save() — detects stale endpoint responses even when scraper succeeds"
  - "Multi-meeting list capped at head(4) — covers next 3-4 upcoming RBA decisions"

requirements-completed: [ASX-01, ASX-03, ASX-04]

# Metrics
duration: 4min
completed: 2026-02-24
---

# Phase 8 Plan 01: ASX Futures Pipeline Extension Summary

**Multi-meeting pipeline delivering meetings[] array in status.json with staleness detection at 14d/30d thresholds and CI freshness assertion**

## Performance

- **Duration:** ~4 min
- **Started:** 2026-02-24T05:35:45Z
- **Completed:** 2026-02-24T05:39:00Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Added `_check_staleness()` to `asx_futures_scraper.py` — non-fatal warning at 14 days, error at 30 days, called after every successful CSV write
- Extended `load_asx_futures_csv()` in `ratios.py` to return a `meetings[]` list of the next 3-4 upcoming RBA meetings alongside all existing single-meeting fields
- Extended `build_asx_futures_entry()` in `engine.py` to propagate `meetings[]` into `status.json` with human-readable `meeting_date_label` (e.g., "3 Mar 2026"), cross-platform day formatting, and rounded probability values
- Added "Verify ASX data freshness" step to `daily-asx-futures.yml` with `continue-on-error: true` that fails the step (but not the commit) when CSV is older than 7 days
- `public/data/status.json` now contains 4 upcoming RBA meetings: Mar 2026, Apr 2026, May 2026, Jun 2026

## Task Commits

Each task was committed atomically:

1. **Task 1: Add staleness detection and extend multi-meeting data extraction** - `f0e0c17` (feat)
2. **Task 2: Add CI freshness assertion to daily ASX workflow** - `db5e1bc` (feat)
3. **Regenerated status.json** - `48dda33` (chore)

## Files Created/Modified

- `pipeline/ingest/asx_futures_scraper.py` - Added `_check_staleness()` function and call in `fetch_and_save()`
- `pipeline/normalize/ratios.py` - Extended `load_asx_futures_csv()` to return `meetings[]` list with next 3-4 upcoming meetings
- `pipeline/normalize/engine.py` - Extended `build_asx_futures_entry()` to build `entry['meetings']` with formatted date labels
- `.github/workflows/daily-asx-futures.yml` - Added "Verify ASX data freshness" step with `continue-on-error: true`
- `public/data/status.json` - Regenerated with `asx_futures.meetings[]` containing 4 entries

## Decisions Made

- **`continue-on-error: true` on CI freshness step:** ASX endpoint has known intermittency (404 on 2026-02-07). Blocking data commits on freshness failure would prevent any commit when the endpoint is down — stale data committed is better than no data committed.
- **Additive contract extension:** All existing single-meeting fields (`next_meeting`, `implied_rate`, `probabilities`, `direction`, `data_date`, `staleness_days`) preserved unchanged. `meetings[]` is purely additive, so existing tests and frontend code continue to work without modification.
- **Cross-platform day formatting:** Used `str(dt.day)` instead of `%-d` strftime directive — `%-d` is Linux/macOS only and would crash on Windows CI runners.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- Python environment lacked `pandas` and `requests` packages at test time (not installed globally) — installed them to run verifications. This is expected: project uses pip requirements.txt and the packages are present in CI.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `status.json` now carries `asx_futures.meetings[]` with 4 upcoming meetings — ready for Phase 8 Plan 02 (frontend multi-meeting table renderer)
- All existing dashboard tests should still pass (backward-compatible contract extension)
- Frontend can access `data.asx_futures.meetings` array to render multi-meeting probability table

---
*Phase: 08-asx-futures-live-data*
*Completed: 2026-02-24*

## Self-Check: PASSED

- pipeline/ingest/asx_futures_scraper.py: FOUND
- pipeline/normalize/ratios.py: FOUND
- pipeline/normalize/engine.py: FOUND
- .github/workflows/daily-asx-futures.yml: FOUND
- .planning/phases/08-asx-futures-live-data/08-01-SUMMARY.md: FOUND
- Commit f0e0c17 (Task 1): FOUND
- Commit db5e1bc (Task 2): FOUND
- Commit 48dda33 (status.json regen): FOUND
