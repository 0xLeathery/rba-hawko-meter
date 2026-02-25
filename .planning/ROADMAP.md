# Roadmap: RBA Hawk-O-Meter

## Milestones

- ✅ **v1.0 MVP** — Phases 1-7 (shipped 2026-02-24)
- ✅ **v1.1 Full Indicator Coverage** — Phases 8-10 (shipped 2026-02-24)
- ✅ **v2.0 Local CI & Test Infrastructure** — Phases 11-17 (shipped 2026-02-25)
- 🚧 **v3.0 Full Test Coverage** — Phases 18-20 (in progress)

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

<details>
<summary>✅ v2.0 Local CI & Test Infrastructure (Phases 11-17) — SHIPPED 2026-02-25</summary>

7 phases, 11 plans completed. Full details in milestones/v2.0-ROADMAP.md.

Delivered: Test foundation (pyproject.toml + isolated fixtures), 60+ pytest unit tests guarding mathematical core, dual-language linting (ruff + ESLint v10) at zero violations, live verification suite for all data sources, lefthook pre-push quality gate in <10s, DATA_DIR late-binding fix with env var override.

</details>

### 🚧 v3.0 Full Test Coverage (In Progress)

**Milestone Goal:** 85%+ per-module coverage across all `pipeline/` modules, closing the gap on ingest, orchestration, and normalization layers via mocked unit tests and an enforced coverage gate.

- [ ] **Phase 18: Test Infrastructure** — Wire pytest-cov into addopts, add pytest-mock and responses deps, create scraper fixture files, and write the per-module coverage check script
- [ ] **Phase 19: Ingest Module Tests** — Unit tests for all 6 ingest/utility modules (abs_data, rba_data, asx_futures_scraper, corelogic_scraper, nab_scraper, http_client) reaching 85%+ each
- [ ] **Phase 20: Orchestration Tests and Enforcement** — Unit tests for engine.py and main.py at 85%+, coverage check wired into npm scripts and pre-push hook

## Phase Details

### Phase 18: Test Infrastructure
**Goal**: The test harness is ready to measure and enforce per-module coverage — pytest-cov runs automatically on every test invocation, scraper fixture files exist, and the coverage check script can validate 85% per module
**Depends on**: Nothing (v3.0 starting phase)
**Requirements**: INFRA-01, INFRA-02, INFRA-03, INFRA-04
**Success Criteria** (what must be TRUE):
  1. Running `pytest` (without any extra flags) produces a per-module coverage report in the terminal and writes `.coverage.json` to the project root
  2. `pytest-mock` and `responses` are importable in test files without install errors
  3. `tests/python/fixtures/` contains at least three scraper fixture files usable in ingest tests (sample ASX JSON response, RBA CSV with metadata headers, NAB article HTML)
  4. `python scripts/check_coverage.py --min 85` exits non-zero with a diff table when any `pipeline/` module is below 85%, and exits zero when all are at or above 85%
**Plans**: TBD

Plans:
- [ ] 18-01: Wire pytest-cov into pyproject.toml addopts, add pytest-mock and responses to requirements-dev.txt, install and verify importability
- [ ] 18-02: Create scraper fixture files and scripts/check_coverage.py

### Phase 19: Ingest Module Tests
**Goal**: Every ingest and utility module in `pipeline/` has 85%+ unit test coverage, with the mock-session pattern established and error paths fully exercised across all five scrapers and http_client
**Depends on**: Phase 18
**Requirements**: INGEST-01, INGEST-02, INGEST-03, INGEST-04, INGEST-05, INGEST-06
**Success Criteria** (what must be TRUE):
  1. `python scripts/check_coverage.py --min 85` passes for `http_client.py`, `abs_data.py`, `rba_data.py`, `asx_futures_scraper.py`, `corelogic_scraper.py`, and `nab_scraper.py`
  2. All new ingest tests pass with the socket-level network blocker active — no test makes a real HTTP request
  3. Error paths (HTTP errors, parse failures, empty responses, stale data) are tested in each scraper module — no module's error branches are entirely uncovered
  4. Date-dependent tests produce consistent results regardless of when they are run (datetime patched or frozen per-test)
**Plans**: TBD

Plans:
- [ ] 19-01: test_http_client.py + test_ingest_abs.py (establishes _make_mock_session pattern and correct patch target)
- [ ] 19-02: test_ingest_rba.py + test_ingest_asx.py + test_ingest_corelogic.py + test_ingest_nab.py

### Phase 20: Orchestration Tests and Enforcement
**Goal**: The pipeline orchestration layer (engine.py, main.py) reaches 85%+ coverage and the per-module coverage gate is active in npm scripts and the pre-push hook, making coverage regression impossible to push undetected
**Depends on**: Phase 19
**Requirements**: ORCH-01, ORCH-02, ENFORCE-01, ENFORCE-02
**Success Criteria** (what must be TRUE):
  1. `python scripts/check_coverage.py --min 85` passes for `engine.py` and `main.py`, and for all previously covered modules (full milestone gate green)
  2. Tests calling `generate_status()` do not write to `public/data/status.json` — STATUS_OUTPUT is isolated via the engine_data_dir fixture
  3. Tests for `main.run_pipeline()` critical failure path use `pytest.raises(SystemExit)` and assert exit code 1 — the test runner does not terminate
  4. `npm run test:fast` executes the coverage check after unit tests and fails the run if any module is below 85%
  5. The lefthook pre-push hook runs the coverage check — a push with a module below 85% is blocked
**Plans**: TBD

Plans:
- [ ] 20-01: test_engine.py covering generate_interpretation, build_asx_futures_entry, build_gauge_entry, process_indicator, and generate_status with engine_data_dir fixture
- [ ] 20-02: test_main.py covering all tier behaviors and sys.exit contract, then wire check_coverage.py into npm scripts and lefthook

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1-7. MVP Phases | v1.0 | 19/19 | Complete | 2026-02-24 |
| 8. ASX Futures Live Data | v1.1 | 2/2 | Complete | 2026-02-24 |
| 9. Housing Prices Gauge | v1.1 | 2/2 | Complete | 2026-02-24 |
| 10. NAB Capacity Utilisation Gauge | v1.1 | 2/2 | Complete | 2026-02-24 |
| 11. Test Foundation | v2.0 | 2/2 | Complete | 2026-02-25 |
| 12. Python Unit Tests | v2.0 | 2/2 | Complete | 2026-02-25 |
| 13. Linting Baseline | v2.0 | 2/2 | Complete | 2026-02-25 |
| 14. Live Verification | v2.0 | 1/1 | Complete | 2026-02-25 |
| 15. Pre-Push Hook | v2.0 | 1/1 | Complete | 2026-02-25 |
| 16. Verify Linting Baseline | v2.0 | 1/1 | Complete | 2026-02-25 |
| 17. Fix DATA_DIR & Verify Chain | v2.0 | 2/2 | Complete | 2026-02-25 |
| 18. Test Infrastructure | v3.0 | 0/2 | Not started | - |
| 19. Ingest Module Tests | v3.0 | 0/2 | Not started | - |
| 20. Orchestration Tests and Enforcement | v3.0 | 0/2 | Not started | - |
