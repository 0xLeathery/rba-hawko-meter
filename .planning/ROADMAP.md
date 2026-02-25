# Roadmap: RBA Hawk-O-Meter

## Milestones

- ✅ **v1.0 MVP** — Phases 1-7 (shipped 2026-02-24)
- ✅ **v1.1 Full Indicator Coverage** — Phases 8-10 (shipped 2026-02-24)
- **v2.0 Local CI & Test Infrastructure** — Phases 11-17 (active)

## Phases

<details>
<summary>✅ v1.0 MVP (Phases 1-7) — SHIPPED 2026-02-24</summary>

7 phases, 19 plans completed. Full details in milestones/v1.0-ROADMAP.md.

Delivered: Automated data pipeline (5 ABS indicators + RBA cash rate), interactive dark-theme dashboard with Plotly.js, Z-score normalization engine, Hawk-O-Meter gauges, mortgage calculator, ASIC-compliant plain English UX, daily/weekly GitHub Actions automation.

</details>

<details>
<summary>✅ v1.1 Full Indicator Coverage (Phases 8-10) — SHIPPED 2026-02-24</summary>

3 phases, 6 plans completed. Full details in milestones/v1.1-ROADMAP.md.

Delivered: ASX futures multi-meeting probability table, ABS RPPI + Cotality HVI housing gauge with fallback hierarchy, NAB capacity utilisation scraper with URL discovery and PDF fallback, Business Conditions trend label, dashboard coverage at 7 of 8 indicators.

</details>

### v2.0 Local CI & Test Infrastructure (Phases 11-17)

- [x] **Phase 11: Test Foundation** — pyproject.toml config hub + isolated test harness (conftest.py + fixtures)
- [x] **Phase 12: Python Unit Tests** — Pure-function coverage for zscore, gauge, ratios, csv_handler, status.json schema (completed 2026-02-24)
- [x] **Phase 13: Linting Baseline** — Ruff (Python) + ESLint v10 (JS) verified clean before hook is enabled (completed 2026-02-25)
- [x] **Phase 14: Live Verification** — On-demand end-to-end verification against real APIs and live scrapers (completed 2026-02-25)
- [x] **Phase 15: Pre-Push Hook** — Automated fast gate via lefthook + unified npm scripts (completed 2026-02-25)
- [ ] **Phase 16: Verify Linting Baseline** — Independent verification of Phase 13 linting work (gap closure)
- [ ] **Phase 17: Fix DATA_DIR Wiring & npm verify Chain** — Fix import-time binding bug + restore verify_summary.py (gap closure)

## Phase Details

### Phase 11: Test Foundation
**Goal**: Developer can run pytest against isolated test infrastructure with no risk of reading or writing production data
**Depends on**: Nothing (first phase of v2.0)
**Requirements**: FOUND-01, FOUND-02, FOUND-03, FOUND-04, FOUND-05
**Success Criteria** (what must be TRUE):
  1. Developer runs `pytest tests/python/ -m "not live"` and it discovers tests, reports 0 collected, exits 0 — confirming config is wired correctly before any tests are written
  2. A test that imports `pipeline.config` runs with `DATA_DIR` pointing to a `tmp_path` directory, not the live `data/` folder
  3. A test that calls `requests.get()` raises `RuntimeError` immediately (autouse network blocker is enforced)
  4. `pytest tests/python/` with a live-marked test and `-m "not live"` skips it; with `-m live` includes it — tier separation works
  5. Developer installs dev dependencies from `requirements-dev.txt` in one command and pytest, ruff, jsonschema are available
**Plans**: 2 plans
Plans:
- [x] 11-01-PLAN.md -- Config hub (pyproject.toml) and dev dependencies (requirements-dev.txt)
- [x] 11-02-PLAN.md -- Test fixtures (conftest.py, fixture CSVs) and smoke tests

### Phase 12: Python Unit Tests
**Goal**: The mathematical core and data pipeline of the project is guarded by a fast, deterministic test suite
**Depends on**: Phase 11
**Requirements**: UNIT-01, UNIT-02, UNIT-03, UNIT-04, UNIT-05
**Success Criteria** (what must be TRUE):
  1. Developer runs `pytest tests/python/ -m "not live"` and all unit tests pass without any real file I/O or HTTP calls
  2. A deliberate regression in `zscore.py` (e.g. returning 0.0 instead of computing rolling MAD) causes at least one test to fail with a clear assertion message
  3. `status.json` with a missing required key or an out-of-range `hawk_score` fails the schema validation test
  4. A `csv_handler` test writes to a temp CSV and reads it back — the live `data/` directory is untouched
  5. `pytest tests/python/ -m "not live"` completes in under 10 seconds on first run (no slow I/O or HTTP)
**Plans**: 2 plans
Plans:
- [ ] 12-01-PLAN.md -- Z-score + gauge unit tests (calculate_mad, robust_zscore, zscore_to_gauge, classify_zone, compute_hawk_score)
- [ ] 12-02-PLAN.md -- Ratios + CSV handler + schema validation tests (YoY normalization, hybrid Cotality/ABS, append_to_csv, status.json jsonschema)

### Phase 13: Linting Baseline
**Goal**: Python and JavaScript linting runs clean on the entire codebase with no pre-existing violations suppressed
**Depends on**: Phase 11
**Requirements**: LINT-01, LINT-02, LINT-03, LINT-04
**Success Criteria** (what must be TRUE):
  1. Developer runs `npm run lint:py` and ruff reports 0 violations across `pipeline/` — the baseline cleanup commit has absorbed all pre-existing violations
  2. Developer runs `npm run lint:js` and ESLint reports 0 violations across `public/js/` — IIFE `sourceType: 'script'` is configured, Plotly and Decimal globals are declared
  3. Developer runs `npm run lint` and both linters run in sequence and both exit 0
  4. Introducing an unused import in a pipeline file causes `npm run lint:py` to fail with a violation message pointing to the correct file and line
**Plans**: 2 plans
Plans:
- [x] 13-01-PLAN.md -- Ruff baseline cleanup (auto-fix + manual E501/B904)
- [x] 13-02-PLAN.md -- ESLint v10 setup, config, JS cleanup, and npm lint scripts

### Phase 14: Live Verification
**Goal**: Developer can confirm the full pipeline works against real external endpoints without touching the unit test suite
**Depends on**: Phase 11
**Requirements**: LIVE-01, LIVE-02, LIVE-03, LIVE-04
**Success Criteria** (what must be TRUE):
  1. Developer runs `npm run test:python:live` and tests that hit ABS, RBA, and ASX real endpoints either pass or emit a named warning — they never cause `pytest` to exit non-zero due to external service unavailability
  2. Developer runs `npm run test:python:live` and scraper tests for Cotality HVI and NAB capacity utilisation either pass or emit a warning — no unhandled exception crashes the suite
  3. Developer runs `npm run verify` and a full pipeline run produces a `status.json` file with all 7 indicator keys present and `hawk_score` in [0, 100]
  4. A live test that hits a URL that returns 404 emits a warning and exits 0 rather than failing the suite
**Plans**: 1 plan
Plans:
- [ ] 14-01-PLAN.md -- Live test file (9 @pytest.mark.live tests) + verify summary script + npm scripts

### Phase 15: Pre-Push Hook
**Goal**: Every `git push` automatically runs the fast quality gate and is rejected before reaching GitHub if the suite fails
**Depends on**: Phase 12, Phase 13, Phase 14
**Requirements**: HOOK-01, HOOK-02, HOOK-03, HOOK-04
**Success Criteria** (what must be TRUE):
  1. Developer adds an unused import to a pipeline file and runs `git push` — the push is rejected before reaching GitHub with an error pointing to the violation
  2. Developer runs `git push` on a clean, green codebase — the hook completes and the push succeeds in under 10 seconds
  3. Developer runs `npm run test:fast` directly and gets the same result as the pre-push hook (same gate, same exit code)
  4. Developer runs `npm run verify` and the full suite runs: fast tests + live pytest + Playwright — all three tiers run in sequence
**Plans**: 1 plan
Plans:
- [ ] 15-01-PLAN.md -- Lefthook pre-push hook + test:fast/verify npm scripts

### Phase 16: Verify Linting Baseline
**Goal**: Phase 13 linting work is independently verified, confirming all lint commands pass cleanly
**Depends on**: Phase 13
**Requirements**: LINT-01, LINT-02, LINT-03, LINT-04
**Gap Closure**: Closes verification gap from v2.0 audit — Phase 13 was never verified by gsd-verifier
**Success Criteria** (what must be TRUE):
  1. `npm run lint:py` reports 0 ruff violations across `pipeline/`
  2. `npm run lint:js` reports 0 ESLint violations across `public/js/`
  3. `npm run lint` runs both linters in sequence and both exit 0
  4. VERIFICATION.md exists for Phase 13 confirming all 4 LINT requirements satisfied
**Plans**: 1 plan
Plans:
- [ ] 16-01-PLAN.md -- Run lint verification + violation detection test, write 13-VERIFICATION.md

### Phase 17: Fix DATA_DIR Wiring & npm verify Chain
**Goal**: `npm run verify` runs all three tiers (fast + live + Playwright) without DATA_DIR assertion failures, and verify_summary.py is included in automation
**Depends on**: Phase 14, Phase 15
**Requirements**: LIVE-01, LIVE-02, LIVE-03, HOOK-04
**Gap Closure**: Closes DATA_DIR import-time binding bug and verify_summary.py orphan from v2.0 audit
**Success Criteria** (what must be TRUE):
  1. All 5 ingestors use late-bound `pipeline.config.DATA_DIR` instead of import-time binding
  2. Live tests pass with `isolate_data_dir` fixture correctly redirecting ingestor writes to tmp_path
  3. `npm run verify` chain includes `verify_summary.py` execution
  4. `npm run verify` completes all three tiers (fast tests + live pytest + Playwright) without DATA_DIR assertion failures

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1-7. MVP Phases | v1.0 | 19/19 | Complete | 2026-02-24 |
| 8. ASX Futures Live Data | v1.1 | 2/2 | Complete | 2026-02-24 |
| 9. Housing Prices Gauge | v1.1 | 2/2 | Complete | 2026-02-24 |
| 10. NAB Capacity Utilisation Gauge | v1.1 | 2/2 | Complete | 2026-02-24 |
| 11. Test Foundation | v2.0 | Complete    | 2026-02-24 | 2026-02-25 |
| 12. Python Unit Tests | 2/2 | Complete    | 2026-02-24 | - |
| 13. Linting Baseline | v2.0 | 2/2 | Complete | 2026-02-25 |
| 14. Live Verification | 1/1 | Complete    | 2026-02-25 | - |
| 15. Pre-Push Hook | 1/1 | Complete    | 2026-02-25 | - |
| 16. Verify Linting Baseline | v2.0 | 0/1 | Planned | - |
| 17. Fix DATA_DIR & verify Chain | v2.0 | 0/0 | Pending | - |
