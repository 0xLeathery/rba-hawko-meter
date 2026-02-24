---
phase: 11-test-foundation
plan: 01
subsystem: testing
tags: [pytest, ruff, pyproject.toml, python, linting, test-configuration]

# Dependency graph
requires: []
provides:
  - pyproject.toml dual config hub for pytest and ruff
  - requirements-dev.txt dev dependency manifest (pytest, ruff, jsonschema)
  - live marker registered with --strict-markers enforcement
  - testpaths scoped to tests/python (Playwright tests isolated)
  - pythonpath=. so import pipeline.config works from test files
affects: [12-unit-tests, 13-smoke-tests, 14-git-hooks, 15-ci-scripts]

# Tech tracking
tech-stack:
  added: [pytest>=9.0.2, ruff>=0.15.2, jsonschema>=4.23]
  patterns:
    - pyproject.toml as single config hub for multiple tools (no pytest.ini, no setup.cfg)
    - requirements-dev.txt separate from requirements.txt (dev vs production deps)
    - strict-markers enforced to catch marker typos at collection time
    - live marker for network-requiring test tier separation

key-files:
  created:
    - pyproject.toml
    - requirements-dev.txt
  modified: []

key-decisions:
  - "Use [tool.pytest.ini_options] (not [tool.pytest] native TOML) for pytest 6+ compatibility"
  - "testpaths = [tests/python] scopes discovery to Python tests only, keeping Playwright tests in tests/*.spec.js isolated"
  - "pythonpath = [.] added so import pipeline.config works from flat layout (no src/)"
  - "ruff select E/F/W/B/I/UP — pycodestyle, pyflakes, warnings, bugbear, isort, pyupgrade — with no ignores"
  - "jsonschema included in requirements-dev.txt now (needed in Phase 12) so one install gets all dev tools"

patterns-established:
  - "Pattern: pyproject.toml dual config hub — both pytest and ruff configured from one file"
  - "Pattern: live marker tier separation — @pytest.mark.live for network tests, -m 'not live' for fast suite"

requirements-completed: [FOUND-01, FOUND-04, FOUND-05]

# Metrics
duration: 7min
completed: 2026-02-25
---

# Phase 11 Plan 01: Config Hub and Dev Dependencies Summary

**pyproject.toml dual config hub with pytest strict-markers/live-marker and ruff E/F/W/B/I/UP rules, plus requirements-dev.txt one-command dev install**

## Performance

- **Duration:** ~7 min
- **Started:** 2026-02-24T21:58:13Z
- **Completed:** 2026-02-24T21:59:20Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Created `pyproject.toml` as single config hub for pytest and ruff with no [project] section
- Registered the `live` marker in pyproject.toml with `--strict-markers` enforced so typos fail fast
- Scoped `testpaths = ["tests/python"]` to keep Python tests separate from Playwright tests
- Added `pythonpath = ["."]` so `import pipeline.config` works from `tests/python/` (flat layout)
- Created `requirements-dev.txt` with pytest>=9.0.2, ruff>=0.15.2, jsonschema>=4.23 — all three install and import successfully

## Task Commits

Each task was committed atomically:

1. **Task 1: Create pyproject.toml config hub with pytest and ruff sections** - `f5d6f62` (chore)
2. **Task 2: Create requirements-dev.txt with pinned dev dependencies** - `ec9d509` (chore)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `pyproject.toml` — Tool configuration hub: [tool.pytest.ini_options] with testpaths, pythonpath, strict-markers, live marker; [tool.ruff] with py313 target; [tool.ruff.lint] with E/F/W/B/I/UP rules
- `requirements-dev.txt` — Dev dependency manifest: pytest>=9.0.2, ruff>=0.15.2, jsonschema>=4.23,<5.0

## Decisions Made

- Used `[tool.pytest.ini_options]` (not `[tool.pytest]` native TOML format) for pytest 6+ compatibility — safer across environments
- No `[project]` section — this is a tool config hub only, not a distributable package
- ruff rule set `["E", "F", "W", "B", "I", "UP"]` — comprehensive but no custom suppressions (clean slate)
- jsonschema pinned to `>=4.23,<5.0` — stable LTS series, upper bound prevents unexpected major API breaks in Phase 12

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None. `ruff check pipeline/ --statistics` produced 116 existing violations (E501, I001, UP* etc.) — this is expected per STATE.md note ("Ruff baseline audit must run before hook is enabled — first run on unaudited codebase will produce violations"). These are pre-existing issues, not introduced by this plan.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- `pyproject.toml` ready: pytest will discover `tests/python/` when created in Phase 11 Plans 02-03
- `ruff` will lint `pipeline/` in Phase 14 pre-push hooks (baseline fix commit needed first)
- `requirements-dev.txt` ready: `pip install -r requirements-dev.txt` installs all test tooling in one command
- `live` marker registered: `--strict-markers` will enforce it from Plan 02 onwards

---
*Phase: 11-test-foundation*
*Completed: 2026-02-25*
