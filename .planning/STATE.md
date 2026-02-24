# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-24)

**Core value:** "Data, not opinion." Empowers laypeople to understand interest rate drivers without relying on media sensationalism or biased advice.
**Current focus:** v2.0 Local CI & Test Infrastructure — Phase 11: Test Foundation

## Current Position

Phase: 11 (Test Foundation)
Plan: 01 complete (1/2 plans done)
Status: In progress
Last activity: 2026-02-25 — Plan 11-01 complete: pyproject.toml config hub + requirements-dev.txt

```
v2.0 Progress: [=         ] 5%
Phase 11 [=] Phase 12 [ ] Phase 13 [ ] Phase 14 [ ] Phase 15 [ ]
```

## Performance Metrics

**v1.0 MVP:**
- Phases: 1-7 (19 plans)
- Timeline: 20 days (2026-02-04 → 2026-02-24)
- Commits: 81

**v1.1 Full Indicator Coverage:**
- Phases: 8-10 (6 plans)
- Timeline: 1 day (2026-02-24)
- Files modified: 37, Lines: +5,383 / -300
- Tests: 28 Playwright (100% pass)

**v2.0 Local CI & Test Infrastructure:**
- Phases: 11-15 (5 phases planned)
- Timeline: Started 2026-02-24
- Requirements: 22 (all mapped)

## Accumulated Context

### Decisions

Archived to PROJECT.md Key Decisions table. All v1.0 and v1.1 decisions preserved there.

**v2.0 decisions (Plan 11-01):**
- Use [tool.pytest.ini_options] (not [tool.pytest] native TOML) for pytest 6+ compatibility
- testpaths = [tests/python] to scope discovery and keep Playwright tests isolated
- pythonpath = [.] so import pipeline.config works from flat layout (no src/)
- ruff select E/F/W/B/I/UP with no ignores (clean slate baseline)
- jsonschema included in requirements-dev.txt now (needed Phase 12) for one-command dev install

### Critical Context for v2.0

- `DATA_DIR = Path("data")` in `pipeline/config.py` is a relative path — all tests must patch this via autouse fixture or they silently read/write live CSV files
- ESLint v10 uses flat config (`eslint.config.js`) only — no `.eslintrc` supported; must use `sourceType: 'script'` for IIFE modules in `public/js/`
- Ruff baseline audit must run before hook is enabled — first run on unaudited codebase will produce violations; do a one-time `ruff check --fix` baseline commit first
- Live tests (`@pytest.mark.live`) must never run in the pre-push hook — only in `npm run verify` on demand
- Lefthook venv activation: configure to use explicit `.venv/bin/ruff` and `.venv/bin/pytest` paths, or document venv prerequisite

### Blockers/Concerns

None active.

## Session Continuity

Last session: 2026-02-25
Stopped at: Plan 11-01 complete — pyproject.toml and requirements-dev.txt created
Resume file: .planning/phases/11-test-foundation/11-01-SUMMARY.md
Next action: Execute plan 11-02 (conftest.py + fixture CSVs + smoke tests)
