---
phase: 18-test-infrastructure
plan: 01
subsystem: testing
tags: [pytest-cov, pytest-mock, responses, coverage]

requires:
  - phase: 17-fix-datadir-verify-chain
    provides: Isolated test fixtures and DATA_DIR late-binding
provides:
  - pytest-cov auto-measurement on every pytest invocation
  - pytest-mock and responses libraries for mock-based testing
  - .coverage.json output for coverage enforcement script
affects: [18-02, 19-ingest-module-tests, 20-orchestration-tests]

tech-stack:
  added: [pytest-cov>=4.0, pytest-mock>=3.15, responses>=0.26]
  patterns: [auto-coverage via addopts, json coverage output]

key-files:
  created: []
  modified:
    - pyproject.toml
    - requirements-dev.txt
    - .gitignore

key-decisions:
  - "Coverage scoped to pipeline/ only via --cov=pipeline — test files excluded from measurement"
  - "JSON output uses :DEST suffix (.coverage.json) for deterministic path"
  - "No --cov-fail-under in addopts — per-module enforcement handled by check_coverage.py in Plan 18-02"

patterns-established:
  - "Auto-coverage: every pytest run generates terminal report + .coverage.json without extra flags"

requirements-completed: [INFRA-01, INFRA-02]

duration: 2min
completed: 2026-02-25
---

# Phase 18 Plan 01: Wire pytest-cov and Dev Dependencies Summary

**pytest-cov wired into pyproject.toml addopts with term-missing and JSON output, plus pytest-mock and responses added to dev deps**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-25T09:30:07Z
- **Completed:** 2026-02-25T09:32:30Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Every `pytest` invocation now auto-generates per-module coverage report in terminal (with missing line numbers)
- `.coverage.json` written at project root after every test run for programmatic consumption
- pytest-mock and responses libraries installed and importable for Phase 19 ingest tests
- Coverage artifacts (.coverage, .coverage.*, .coverage.json) gitignored

## Task Commits

Each task was committed atomically:

1. **Task 1: Wire pytest-cov addopts and add dev dependencies** - `146931b` (chore)
2. **Task 2: Gitignore coverage artifacts** - `9d8a77d` (chore)

## Files Created/Modified
- `pyproject.toml` - Added --cov=pipeline, --cov-report=term-missing, --cov-report=json:.coverage.json to addopts
- `requirements-dev.txt` - Added pytest-cov>=4.0, pytest-mock>=3.15, responses>=0.26
- `.gitignore` - Added .coverage, .coverage.*, .coverage.json entries

## Decisions Made
- Coverage scoped to `pipeline/` only — test files excluded from measurement
- JSON output path uses `:DEST` suffix (`.coverage.json`) for deterministic naming
- No `--cov-fail-under` in addopts — per-module enforcement is the coverage script's job (Plan 18-02)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Coverage measurement backbone in place — Plan 18-02 can now create the enforcement script that reads .coverage.json
- pytest-mock and responses ready for Phase 19 ingest unit tests
- All 118 existing tests pass with coverage enabled (28% overall baseline)

---
*Phase: 18-test-infrastructure*
*Completed: 2026-02-25*
