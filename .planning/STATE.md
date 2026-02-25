# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-24)

**Core value:** "Data, not opinion." Empowers laypeople to understand interest rate drivers without relying on media sensationalism or biased advice.
**Current focus:** v2.0 Local CI & Test Infrastructure — Phase 17: Fix DATA_DIR & npm verify Chain (COMPLETE)

## Current Position

Phase: 17 (Fix DATA_DIR Wiring & npm verify Chain)
Plan: 02 complete
Status: Phase 17 complete — v2.0 gap closure phases complete
Last activity: 2026-02-25 — Phase 17 complete (DATA_DIR late-binding fix + verify_summary.py wiring)

```
v2.0 Progress: [██████████] 100%
Phase 11 [✓] Phase 12 [✓] Phase 13 [✓] Phase 14 [✓] Phase 15 [✓] Phase 16 [✓] Phase 17 [✓]
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

**v2.0 decisions (Phase 13):**
- Ruff auto-fix first, then manual B904 + E501 — no noqa suppressions policy
- ESLint v10 flat config with sourceType: script for IIFE module pattern
- @eslint/js installed separately (not bundled with ESLint v10)
- builtinGlobals: false for no-redeclare to allow IIFE var re-declarations
- varsIgnorePattern for module names avoids no-unused-vars false positives
- max-len 88 for JS matching Python ruff convention for cross-language consistency
- Catch params prefixed with _ (e.g. _e) for caughtErrorsIgnorePattern

**v2.0 decisions (Plan 14-01):**
- warnings.warn(UserWarning) for endpoint unavailability — not pytest.warns() — so tests pass whether endpoint is up or down
- Shared _run_abs_test() helper for 5 ABS tests avoids duplication while keeping individual test functions
- Staleness threshold 90 days — warns but does not fail
- verify_summary.py checks only 7 gauge keys + hawk_score range — full JSON schema validation owned by test_schema.py

**v2.0 decisions (Plan 15-01):**
- Use @evilmartians/lefthook with parallel pre-push hook (lint-py + lint-js + unit-tests); silent on success, 30s timeout
- npm test:fast = lint + pytest non-live; npm verify = test:fast + live + playwright (three-tier sequence)
- npx eslint in both lefthook.yml and lint:js for consistent local binary resolution

**v2.0 decisions (Phase 17):**
- All ingestors and normalize modules use `pipeline.config.DATA_DIR` at call time (late-bound) instead of `from pipeline.config import DATA_DIR` (import-time bound)
- `DATA_DIR` supports environment variable override: `DATA_DIR=/custom/path`
- Each ingestor's `fetch_and_save()` logs DATA_DIR at startup for debugging
- `npm run verify` chain: verify:fast && verify:live && verify:playwright && verify_summary.py
- Individual tier scripts available: verify:fast, verify:live, verify:playwright
- test:fast and verify:fast are intentionally identical for backward compatibility with lefthook

### Critical Context for v2.0

- `DATA_DIR = Path(os.environ.get("DATA_DIR", "data"))` in `pipeline/config.py` — supports env var override; all modules use late-bound `pipeline.config.DATA_DIR` access
- ESLint v10 uses flat config (`eslint.config.js`) only — no `.eslintrc` supported; must use `sourceType: 'script'` for IIFE modules in `public/js/`
- Ruff baseline audit must run before hook is enabled — first run on unaudited codebase will produce violations; do a one-time `ruff check --fix` baseline commit first
- Live tests (`@pytest.mark.live`) must never run in the pre-push hook — only in `npm run verify` on demand
- Lefthook venv activation: configure to use explicit `.venv/bin/ruff` and `.venv/bin/pytest` paths, or document venv prerequisite

### Blockers/Concerns

None active.

## Session Continuity

Last session: 2026-02-25
Stopped at: Completed Phase 15 (Pre-Push Hook) — lefthook pre-push hook + test:fast + verify npm scripts
Resume file: .planning/phases/15-pre-push-hook/15-01-SUMMARY.md
Next action: v2.0 complete — all 5 phases (11-15) delivered
