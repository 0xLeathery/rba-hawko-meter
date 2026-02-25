---
phase: 18-test-infrastructure
plan: 02
subsystem: testing
tags: [fixtures, coverage-enforcement, scraper-data, check-coverage]

requires:
  - phase: 18-test-infrastructure
    provides: pytest-cov auto-measurement and .coverage.json output
provides:
  - 10 scraper fixture files for all 5 data sources (happy-path + error variant)
  - Per-module coverage enforcement script (scripts/check_coverage.py)
affects: [19-ingest-module-tests, 20-orchestration-tests]

tech-stack:
  added: []
  patterns: [fixture-per-source naming, per-module threshold enforcement]

key-files:
  created:
    - tests/python/fixtures/asx_response.json
    - tests/python/fixtures/asx_response_empty.json
    - tests/python/fixtures/rba_cashrate.csv
    - tests/python/fixtures/rba_cashrate_empty.csv
    - tests/python/fixtures/nab_article.html
    - tests/python/fixtures/nab_article_no_data.html
    - tests/python/fixtures/abs_response.csv
    - tests/python/fixtures/abs_response_empty.csv
    - tests/python/fixtures/corelogic_article.html
    - tests/python/fixtures/corelogic_article_no_pdf.html
    - scripts/check_coverage.py
  modified: []

key-decisions:
  - "Fixtures trimmed to 2-3 rows but structurally identical to production data"
  - "Coverage script walks up from script location to find project root — works from any CWD"
  - "Modules with 0 statements (empty __init__.py) filtered from coverage reporting"

patterns-established:
  - "Fixture naming: {source}_{variant}.{ext} (e.g., asx_response_empty.json)"
  - "Coverage enforcement: per-module threshold via --min flag, not global --cov-fail-under"

requirements-completed: [INFRA-03, INFRA-04]

duration: 3min
completed: 2026-02-25
---

# Phase 18 Plan 02: Scraper Fixtures and Coverage Script Summary

**10 scraper fixture files covering all 5 data sources plus per-module coverage enforcement script reading .coverage.json**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-25T09:32:43Z
- **Completed:** 2026-02-25T09:36:00Z
- **Tasks:** 2
- **Files modified:** 11

## Accomplishments
- Created 10 fixture files in tests/python/fixtures/ matching production data structures for ASX, RBA, NAB, ABS, and CoreLogic
- Each data source has happy-path and error variant fixtures for testing both success and failure paths
- scripts/check_coverage.py enforces per-module coverage thresholds with formatted diff tables
- Coverage script auto-detects terminal vs pipe for ANSI color output
- At --min 0: exits 0 (all pass). At --min 85: exits 1 (expected — ingest modules untested). At --min 100: exits 1 (11 modules below)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create scraper fixture files for all 5 data sources** - `c4c1b7a` (feat)
2. **Task 2: Create per-module coverage check script** - `8b6862a` (feat)

## Files Created/Modified
- `tests/python/fixtures/asx_response.json` - MarkitDigital API JSON with 2 futures contracts
- `tests/python/fixtures/asx_response_empty.json` - Empty items array for no-data path
- `tests/python/fixtures/rba_cashrate.csv` - RBA CSV with metadata headers and Series ID landmark
- `tests/python/fixtures/rba_cashrate_empty.csv` - Headers only, no data rows
- `tests/python/fixtures/nab_article.html` - NAB article with capacity utilisation text and PDF link
- `tests/python/fixtures/nab_article_no_data.html` - Article with no capacity data or PDF link
- `tests/python/fixtures/abs_response.csv` - ABS SDMX CSV with CPI data in quarterly format
- `tests/python/fixtures/abs_response_empty.csv` - Header row only
- `tests/python/fixtures/corelogic_article.html` - Cotality article with HVI PDF download link
- `tests/python/fixtures/corelogic_article_no_pdf.html` - Article with no PDF link
- `scripts/check_coverage.py` - Per-module coverage enforcement reading .coverage.json

## Decisions Made
- Fixtures trimmed to 2-3 rows but structurally identical to production responses
- Coverage script uses Path resolution from script location for project root discovery
- Empty __init__.py files (0 statements) excluded from coverage reporting

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All Phase 18 infrastructure in place — fixture files ready for Phase 19 ingest unit tests
- Coverage enforcement script ready for Phase 20 integration into npm scripts and pre-push hook
- Current baseline: 13 pipeline modules tracked, 2 at 100%, 1 at 96%, most at 0-24%

---
*Phase: 18-test-infrastructure*
*Completed: 2026-02-25*
