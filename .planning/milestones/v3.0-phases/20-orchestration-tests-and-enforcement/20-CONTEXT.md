# Phase 20: Orchestration Tests and Enforcement - Context

**Generated:** 2026-02-25
**Method:** Synthetic discuss (5 agents)
**Status:** Ready for planning

<domain>
## Phase Boundary

Unit tests for `pipeline/normalize/engine.py` and `pipeline/main.py` reaching 85%+ coverage each, plus wiring `scripts/check_coverage.py --min 85` into `npm run test:fast` and the lefthook pre-push hook. Tests mock all ingest functions and normalization dependencies so no real data or network access is needed. STATUS_OUTPUT writes are isolated so `public/data/status.json` is never touched. The critical failure `sys.exit(1)` path in `main.py` is tested without killing the test runner. No new production code changes. No changes to ingest module tests (Phase 19). No CI/CD pipeline integration (future milestone).

</domain>

<decisions>
## Implementation Decisions

### 1. STATUS_OUTPUT Isolation Strategy
- **Decision:** Monkeypatch `pipeline.config.STATUS_OUTPUT` to a `tmp_path / "status.json"` in an `engine_data_dir` fixture. This fixture extends the existing autouse `isolate_data_dir` by also patching `STATUS_OUTPUT`. Since `generate_status()` reads `STATUS_OUTPUT` from the `pipeline.config` module at call time (`from pipeline.config import STATUS_OUTPUT` is bound at import time in engine.py), the patch target must be `pipeline.normalize.engine.STATUS_OUTPUT` (the import site), not `pipeline.config.STATUS_OUTPUT`.
- **Rationale:** `STATUS_OUTPUT` is defined as `Path("public") / "data" / "status.json"` in config.py -- it does NOT use `DATA_DIR`, so the existing `isolate_data_dir` autouse fixture does not protect it. engine.py uses `from pipeline.config import STATUS_OUTPUT`, binding the name at import time. Following the Phase 19 convention of patching at the import site, we must patch `pipeline.normalize.engine.STATUS_OUTPUT`. The fixture writes to `tmp_path` which is automatically cleaned up by pytest.
- **Consensus:** 5/5 agents agreed

### 2. engine.py Test Approach -- Mock at Function Level vs. End-to-End
- **Decision:** Test `generate_interpretation()`, `build_asx_futures_entry()`, and `process_indicator()` as unit functions with direct input/output. Test `generate_status()` by mocking `normalize_indicator`, `compute_rolling_zscores`, `load_weights`, `compute_hawk_score`, `classify_zone`, `generate_verdict`, and `load_asx_futures_csv` at their import sites in the engine module. For `build_gauge_entry()`, pass pre-constructed DataFrames and row dicts directly rather than mocking the Z-score pipeline.
- **Rationale:** engine.py has clear function boundaries. `generate_interpretation()` is a pure lookup -- test directly with parametrized zones. `build_gauge_entry()` takes explicit args (no external I/O except the housing/business_confidence CSV reads which go through `pipeline.config.DATA_DIR`, already isolated by `isolate_data_dir`). `generate_status()` is the integration point that calls everything -- mock its dependencies at the engine module's import sites. `process_indicator()` calls `normalize_indicator` and `compute_rolling_zscores` -- mock those to return canned DataFrames.
- **Consensus:** 5/5 agents agreed

### 3. main.py sys.exit Testing Strategy
- **Decision:** Use `pytest.raises(SystemExit) as exc_info` to catch `sys.exit(1)` in the critical failure path, then assert `exc_info.value.code == 1`. Mock all ingest module references (`rba_data`, `abs_data`, `corelogic_scraper`, `nab_scraper`) and `generate_status` at their import sites in main.py. For the critical failure test, make one critical source mock raise an exception.
- **Rationale:** All 5 agents agreed this is the canonical pytest pattern. `sys.exit()` raises `SystemExit` (a subclass of `BaseException`), which `pytest.raises` catches cleanly. The test runner does not terminate because the exception is caught by the context manager. No special subprocess or signal handling needed. This directly satisfies Success Criterion 3.
- **Consensus:** 5/5 agents agreed

### 4. main.py Tier Coverage Strategy
- **Decision:** Write separate test functions for each tier behavior: (a) all-success path returning `status: "success"`, (b) critical failure triggering `sys.exit(1)`, (c) important source failure returning `status: "partial"` with `important_failures` list, (d) optional source failure (exception path) returning `status: "partial"`, (e) optional source returning `status: "failed"` dict (scraper dict path), (f) normalization unavailable path (`NORMALIZATION_AVAILABLE = False`), (g) normalization exception path. Each test mocks only what it needs using `monkeypatch.setattr` on the module-level lists (`CRITICAL_SOURCES`, `IMPORTANT_SOURCES`, `OPTIONAL_SOURCES`) to reduce the number of mocks per test.
- **Rationale:** 4 of 5 agents preferred patching the tier lists to keep tests focused. The module defines `CRITICAL_SOURCES`, `IMPORTANT_SOURCES`, and `OPTIONAL_SOURCES` as module-level lists. Replacing them with single-entry lists containing controlled mocks isolates each tier's behavior without needing to mock 8 separate ingest modules per test. The Engineer and DevOps Expert noted this is cleaner than individually mocking every import.
- **Consensus:** 4/5 agents agreed (Test Architect, Engineer, QA Expert, DevOps Expert)

### 5. Coverage Enforcement Wiring in npm Scripts
- **Decision:** Append `&& python scripts/check_coverage.py --min 85` to the existing `test:fast` and `verify:fast` npm scripts, after the pytest command. This makes coverage checking automatic on every fast test run. The full command becomes: `npm run lint && python -m pytest tests/python/ -m "not live" && python scripts/check_coverage.py --min 85`. Do NOT create a separate `test:coverage` script -- keep the gate in the main developer workflow.
- **Rationale:** All 5 agents agreed. The coverage check must read `.coverage.json` which is generated by the pytest run (via `--cov-report=json:.coverage.json` in pyproject.toml addopts). Running it as a chained `&&` ensures it only executes when tests pass. Embedding it in `test:fast` means developers cannot accidentally skip it. A separate script would require developers to remember to run it.
- **Consensus:** 5/5 agents agreed

### 6. Pre-Push Hook Coverage Check
- **Decision:** Add a `coverage-check` command to the lefthook.yml `pre-push` block that runs `python scripts/check_coverage.py --min 85`. This command must NOT run in parallel with `unit-tests` because it depends on `.coverage.json` being written by pytest first. Instead, restructure the hook: keep lint commands parallel, run unit-tests sequentially before coverage-check, or use lefthook's `piped: true` mode for the test+coverage sequence. The recommended approach is to change `unit-tests` run command to `pytest tests/python/ -m "not live" && python scripts/check_coverage.py --min 85` (chain them in a single command), keeping the parallel structure for lint vs. test+coverage.
- **Rationale:** 4 of 5 agents agreed on chaining within the unit-tests command. The coverage check reads `.coverage.json` which is only valid after pytest completes. Running them as separate parallel commands would race. Chaining them in a single `run:` command is the simplest approach -- it preserves the existing parallel lint+test structure while adding coverage enforcement. The 30s timeout may need bumping to 45s to accommodate the extra script invocation.
- **Consensus:** 4/5 agents agreed (Test Architect, Engineer, QA Expert, DevOps Expert)

### Claude's Discretion
- **Tier list patching vs. individual mock (Gray Area 4):** The Devil's Advocate argued that patching `CRITICAL_SOURCES` etc. tests the framework, not the actual wiring -- if someone reorders the real list, the test wouldn't catch it. However, 4/5 agents noted that testing the tier logic (critical=fail-fast, important=warn, optional=degrade) is the actual goal, and wiring correctness is verified by live tests and the pipeline's real-world runs. The tier list patching approach is adopted.

</decisions>

<specifics>
## Specific Ideas

- **engine_data_dir fixture:** Create a non-autouse fixture `engine_data_dir(monkeypatch, tmp_path)` that patches both `pipeline.normalize.engine.STATUS_OUTPUT` and creates the necessary subdirectory structure in `tmp_path`. Tests that call `generate_status()` or `build_gauge_entry()` for housing/business_confidence request this fixture explicitly. The autouse `isolate_data_dir` already handles `DATA_DIR`.
- **generate_interpretation parametrized tests:** Use `@pytest.mark.parametrize` across all 8 indicators x 5 zones (40 cases) plus the fallback case (unknown indicator). This is a pure function with no side effects -- ideal for parametrize.
- **build_gauge_entry housing/business_confidence special paths:** These branches read CSV files from `DATA_DIR`. Populate `tmp_path` with minimal CSV fixtures (reuse from `tests/python/fixtures/`) before calling `build_gauge_entry`. The autouse `isolate_data_dir` already redirects `DATA_DIR` to `tmp_path`.
- **build_asx_futures_entry mock pattern:** Mock `load_asx_futures_csv` at `pipeline.normalize.engine.load_asx_futures_csv` to return a canned dict with `change_bp`, `implied_rate`, `data_date`, `meeting_date`, `probability_cut/hold/hike`, and optionally `meetings` array. Test the direction logic (cut/hold/hike thresholds at -5/+5 bp) with parametrize.
- **datetime freezing in engine tests:** `build_gauge_entry()` and `build_asx_futures_entry()` call `datetime.now()` and `datetime.strptime()`. Use the same `MockDatetime` pattern from Phase 19 -- monkeypatch `pipeline.normalize.engine.datetime` with a class that freezes `.now()` while delegating `.strptime()` and `.strftime()` to the real datetime.
- **NORMALIZATION_AVAILABLE flag:** In main.py tests, patch `pipeline.main.NORMALIZATION_AVAILABLE` to `False` to test the skip-normalization path, and to `True` with a mocked `generate_status` for the success/failure normalization paths.
- **Timeout bump for lefthook:** Consider increasing the unit-tests timeout from 30s to 45s since the coverage check script adds ~2-3s of overhead (JSON parsing + table formatting).

</specifics>

<deferred>
## Deferred Ideas

- **Integration-level generate_status test with real normalization:** Running `generate_status()` with real fixture CSVs through the actual normalization pipeline (no mocking) would provide a true end-to-end test. This is valuable but is an integration test, not a unit test. Defer to a future coverage phase or ECOV-01.
- **Coverage badge in README:** The check_coverage.py script could output a badge-compatible JSON file. Out of scope per REQUIREMENTS.md (ECOV-03 is a future requirement).
- **GitHub Actions CI coverage gate:** Running `check_coverage.py` in CI is ECOV-02, explicitly out of scope. Local enforcement via pre-push hook is sufficient for v3.0.
- **Per-module coverage overrides:** Some modules may legitimately need lower thresholds (e.g., config.py is mostly constants). The current `--min 85` applies uniformly. If this causes false failures, a per-module override mechanism could be added later. Not needed now since all pipeline modules have executable logic.

</deferred>

---
*Phase: 20-orchestration-tests-and-enforcement*
*Context generated: 2026-02-25 via synthetic discuss*
