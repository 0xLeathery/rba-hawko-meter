# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-25)

**Core value:** "Data, not opinion." Empowers laypeople to understand interest rate drivers without relying on media sensationalism or biased advice.
**Current focus:** v3.0 Full Test Coverage — Phase 18: Test Infrastructure

## Current Position

Phase: 18 of 20 (Test Infrastructure)
Plan: 2 of 2 in current phase
Status: Phase complete, verifying
Last activity: 2026-02-25 — Plan 18-02 complete (fixtures + coverage script)

Progress: [███░░░░░░░] 33% (v3.0 phases)

## Performance Metrics

**v1.0 MVP:**
- Phases: 1-7 (19 plans)
- Timeline: 20 days (2026-02-04 → 2026-02-24)
- Commits: 81

**v1.1 Full Indicator Coverage:**
- Phases: 8-10 (6 plans)
- Timeline: 1 day (2026-02-24)
- Files modified: 37, Lines: +5,383 / -300

**v2.0 Local CI & Test Infrastructure:**
- Phases: 11-17 (7 phases, 11 plans)
- Timeline: 2 days (2026-02-24 → 2026-02-25)
- Commits: 64, Files modified: 95, Lines: +13,776 / -1,190
- Tests: 60+ pytest + 9 live + 28 Playwright

## Accumulated Context

### Decisions

All v1.0–v2.0 decisions archived to PROJECT.md Key Decisions table.

Recent decisions affecting v3.0:
- Patch target is `pipeline.ingest.<module>.create_session`, never the source module — wrong target produces RuntimeError even with mock in place
- `pipeline.config.STATUS_OUTPUT` is NOT isolated by the autouse `isolate_data_dir` fixture — engine tests need an explicit `engine_data_dir` fixture that also patches STATUS_OUTPUT
- `main.run_pipeline()` calls `sys.exit(1)` on critical failure — must wrap in `pytest.raises(SystemExit)` or the entire test runner terminates
- Use `MagicMock` + `create_session` patching as primary HTTP mock pattern; `responses` library available if transport-layer interception is needed but not the default
- Date-dependent CoreLogic and NAB tests must patch `datetime` at module level or use `@freeze_time` to prevent non-deterministic CI failures
- Coverage scoped to pipeline/ only via --cov=pipeline — test files excluded from measurement
- No --cov-fail-under in addopts — per-module enforcement handled by check_coverage.py script

### Blockers/Concerns

None active.

## Session Continuity

Last session: 2026-02-25
Stopped at: Completed 18-02-PLAN.md, Phase 18 all plans done
Resume file: None
