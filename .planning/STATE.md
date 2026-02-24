# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-24)

**Core value:** "Data, not opinion." Empowers laypeople to understand interest rate drivers without relying on media sensationalism or biased advice.
**Current focus:** v2.0 Local CI & Test Infrastructure — Phase 12: Python Unit Tests

## Current Position

Phase: 12 (Python Unit Tests)
Plan: 02 complete
Status: Plan 12-02 complete
Last activity: 2026-02-25 — Plan 12-02 complete (54 unit tests for ratios.py, csv_handler.py, schema contract)

```
v2.0 Progress: [████      ] 40%
Phase 11 [✓] Phase 12 [~] Phase 13 [ ] Phase 14 [ ] Phase 15 [ ]
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

**v2.0 decisions (Plan 11-02):**
- Import pipeline.config as a module (not from...import) so monkeypatch targets module attribute
- block_network blocks localhost too — no exceptions for non-live tests (per user decision)
- FIXTURES_DIR uses Path(__file__).parent to avoid CWD sensitivity
- Fixture CSVs are real production snapshots, not synthetic data (per user decision)
- nab_capacity.csv copied in full (only 7 rows exist in production)

**v2.0 decisions (Plan 12-01):**
- No test classes — all top-level test functions per project convention
- Hand-calculated expected MAD values documented in test docstrings with full derivation
- Regression detection test uses stable-value series + spike to 10.0 at row 8, asserts z_score > 1.5
- compute_hawk_score rebalancing verified manually: (60*0.4 + 40*0.4) / 0.8 = 50.0
- Boundary tables use exact threshold values (19.9/20.0, 39.9/40.0, 59.9/60.0, 79.9/80.0)

**v2.0 decisions (Plan 12-02):**
- Use jsonschema StrictValidator (Draft7 + custom type_checker) to enforce hawk_score as Python int, not float
- Auto-fixed load_indicator_csv to return None for header-only CSV (empty DataFrame was missing correctness check)

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
Stopped at: Completed .planning/phases/12-python-unit-tests/12-02-PLAN.md
Resume file: .planning/phases/12-python-unit-tests/12-02-SUMMARY.md
Next action: Continue Phase 12 (additional plans if any) or proceed to Phase 13
