---
phase: 07-asx-futures-integration
plan: 02
subsystem: pipeline
tags: [python, pandas, normalization, status-json, asx-futures]

# Dependency graph
requires:
  - phase: 07-01
    provides: ASX futures scraper and config.py updates
provides:
  - ASX futures CSV loader for multi-column format
  - ASX futures entry builder (bypasses Z-score pipeline)
  - Top-level asx_futures key in status.json
  - Graceful CSV schema validation
affects: [frontend, 07-03]

# Tech tracking
tech-stack:
  added: []
  patterns: [Direct CSV reading for benchmark indicators, Top-level status.json keys for non-gauge data]

key-files:
  created: []
  modified: [pipeline/normalize/ratios.py, pipeline/normalize/engine.py]

key-decisions:
  - "ASX futures bypasses Z-score pipeline - read directly via load_asx_futures_csv()"
  - "asx_futures is top-level status.json key, NOT in gauges dict"
  - "Direction derived from change_bp with -5/+5 thresholds"
  - "load_indicator_csv() checks for 'value' column to gracefully handle non-standard schemas"

patterns-established:
  - "Benchmark indicators can bypass gauge pipeline by using separate loader + top-level status.json key"
  - "CSV loaders validate expected schema and return None for non-conforming files"

# Metrics
duration: 2min
completed: 2026-02-07
---

# Phase 7 Plan 2: ASX Futures Normalization Pipeline

**ASX futures data integrated into status.json as top-level benchmark via direct CSV reading, bypassing Z-score gauge pipeline**

## Performance

- **Duration:** 2 minutes
- **Started:** 2026-02-06T21:36:12Z
- **Completed:** 2026-02-06T21:39:03Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- ASX futures CSV loader reads multi-column format and finds next upcoming meeting
- ASX futures entry builder derives direction, computes staleness, and builds status.json contract
- status.json contains top-level `asx_futures` key when data available (not nested in gauges)
- Graceful degradation: missing CSV produces status.json without errors
- Existing 5 gauges and hawk score calculation completely unaffected

## Task Commits

Each task was committed atomically:

1. **Task 1: Add ASX futures CSV loader** - `6457718` (feat)
2. **Task 2: Build ASX futures entry and integrate into status.json generation** - `a577ec6` (feat)

## Files Created/Modified
- `pipeline/normalize/ratios.py` - Added load_asx_futures_csv() for multi-column CSV parsing, enhanced load_indicator_csv() to validate schema
- `pipeline/normalize/engine.py` - Added build_asx_futures_entry() and integrated into generate_status() to produce top-level asx_futures key

## Decisions Made
- **ASX futures bypasses Z-score pipeline**: Benchmark indicators displayed as-is, not normalized to gauge scale
- **Top-level status.json key**: asx_futures sits alongside gauges/overall/metadata, not inside gauges dict
- **Direction thresholds**: change_bp < -5 → cut, > 5 → hike, else hold
- **Current rate derivation**: Fallback calculation as implied_rate - (change_bp / 100)
- **Schema validation**: load_indicator_csv() checks for 'value' column before processing to handle non-standard CSV formats gracefully

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed load_indicator_csv to handle non-standard CSV schemas**
- **Found during:** Task 2 (Engine integration testing)
- **Issue:** asx_futures.csv has multi-column schema (date, meeting_date, implied_rate, etc.) but load_indicator_csv() expected date/value columns, causing KeyError when accessing 'value' column
- **Fix:** Added schema validation to load_indicator_csv() - checks for 'value' column existence before processing, returns None with descriptive message for non-conforming files
- **Files modified:** pipeline/normalize/ratios.py
- **Verification:** Engine runs without errors, asx_futures gets marked as missing (no data via standard pipeline), then build_asx_futures_entry() adds it as top-level key
- **Committed in:** a577ec6 (part of Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Auto-fix necessary for graceful degradation. Plan anticipated this flow ("Since normalize: 'direct' and the CSV has multi-column format... normalize_indicator() will return None") but didn't specify the implementation detail. No scope creep.

## Issues Encountered
None - all verifications passed first try after blocking issue fixed.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- ASX futures data pipeline complete (scraper → CSV → status.json)
- Frontend already has renderASXTable() expecting this exact status.json contract
- Plan 07-03 can now wire real data to UI and test end-to-end flow
- Note: ASX endpoints currently return 404 (Feb 2026), so pipeline will gracefully degrade until endpoints restored or scraper updated

## Self-Check: PASSED

All created files exist: (none created, only modified)
All commits exist:
- 6457718 ✓
- a577ec6 ✓

---
*Phase: 07-asx-futures-integration*
*Completed: 2026-02-07*
