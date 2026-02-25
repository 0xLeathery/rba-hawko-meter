# Plan 24-02 Summary: Pipeline Integration

**Status:** Complete
**Completed:** 2026-02-26

## What Was Built

Integrated the archive module into the production pipeline:

1. **config.py** — Added `SNAPSHOTS_DIR = Path("public") / "data" / "snapshots"` constant
2. **engine.py** — Added `save_snapshot()`, `read_previous_snapshot()`, `inject_deltas()` calls in `generate_status()`, wrapped in try/except for non-fatal degradation
3. **weekly-pipeline.yml** — Updated `file_pattern` to include `public/data/snapshots/` so snapshot files are committed by git-auto-commit-action
4. **Frontend verification** — Confirmed gauge-init.js and all JS modules handle missing delta fields gracefully (no changes needed)

## Key Decisions

- Renamed gauge-level `direction` field to `delta_direction` to avoid collision with business_confidence's existing `direction` field (RISING/FALLING/STEADY vs up/down/unchanged)
- Archive calls wrapped in try/except — non-fatal: pipeline still writes status.json without deltas if archival fails
- No changes needed to frontend JS — new fields are extra properties that current code ignores; Phase 25 will consume them

## Deviation from Plan

- **Field rename:** Plan specified `direction` field, but implementation uses `delta_direction` to avoid collision with the pre-existing `direction` field in business_confidence gauge entries. This was discovered during frontend verification (interpretations.js line 483 reads `metricData.direction` for capacity utilisation display).

## Test Results

- 441 tests passing (no regressions)
- archive.py: 100% coverage
- engine.py: 93% coverage (unchanged)
- Zero ruff violations, zero ESLint violations

## Key Files

### Modified
- `pipeline/config.py` — Added SNAPSHOTS_DIR constant
- `pipeline/normalize/engine.py` — Added archive integration in generate_status()
- `.github/workflows/weekly-pipeline.yml` — Updated file_pattern for snapshots

### Commits
1. `d410cbb` — feat(24-02): integrate archive module into pipeline engine
2. `211ee51` — feat(24-02): update workflow + rename direction to delta_direction

## Requirements Addressed

| ID | Status |
|----|--------|
| SNAP-01 | save_snapshot() called in generate_status(); workflow commits snapshots |
| SNAP-02 | inject_deltas() adds previous_value, delta, delta_direction per gauge |
| SNAP-03 | inject_deltas() adds previous_hawk_score, hawk_score_delta to overall |
