# Phase 20: Verification

**Phase:** 20 — Orchestration Tests and Enforcement
**Verified:** 2026-02-25
**Status:** passed

## Success Criteria

### SC1: check_coverage.py --min 85 passes for all modules

**Status:** PASSED

```
python scripts/check_coverage.py --min 85
```

Output: All 13 pipeline/ modules at or above 85%:
- abs_data.py: 94%
- asx_futures_scraper.py: 90%
- config.py: 100%
- corelogic_scraper.py: 93%
- csv_handler.py: 100%
- engine.py: 96%
- gauge.py: 100%
- http_client.py: 100%
- main.py: 93%
- nab_scraper.py: 90%
- ratios.py: 92%
- rba_data.py: 93%
- zscore.py: 96%

Exit code: 0 ✓

### SC2: generate_status() does NOT write to public/data/status.json

**Status:** PASSED

Test `TestGenerateStatus::test_status_output_written_to_tmp_path_not_public` verifies:
- `engine_data_dir` fixture patches `pipeline.normalize.engine.STATUS_OUTPUT` to `tmp_path/status.json`
- Asserts `(engine_data_dir / "status.json").exists()`
- Test `test_public_status_json_not_written` verifies modification time of `public/data/status.json` unchanged

### SC3: main.run_pipeline() critical failure uses pytest.raises(SystemExit) with code==1

**Status:** PASSED

Two tests verify this:
```python
# test_critical_failure_calls_sys_exit_1
with pytest.raises(SystemExit) as exc_info:
    run_pipeline()
assert exc_info.value.code == 1

# test_first_critical_failure_exits_immediately
with pytest.raises(SystemExit) as exc_info:
    run_pipeline()
assert exc_info.value.code == 1
```

Test runner does NOT terminate — `pytest.raises` catches `SystemExit` cleanly.

### SC4: npm run test:fast executes coverage check

**Status:** PASSED

package.json test:fast:
```
npm run lint && python -m pytest tests/python/ -m "not live" && python scripts/check_coverage.py --min 85
```

Verified: `npm run test:fast` runs end-to-end (lint + 411 tests + coverage check), exits 0.

### SC5: lefthook pre-push hook runs coverage check

**Status:** PASSED

lefthook.yml unit-tests command:
```yaml
run: pytest tests/python/ -m "not live" && python scripts/check_coverage.py --min 85
timeout: "45s"
```

Coverage check chained in single `run:` command — executes after pytest completes, reads `.coverage.json`.

## Requirements Coverage

| Requirement | Status |
|-------------|--------|
| ORCH-01: engine.py at 85%+ | PASSED (96%) |
| ORCH-02: main.py at 85%+ | PASSED (93%) |
| ENFORCE-01: Coverage check in npm scripts | PASSED |
| ENFORCE-02: Coverage check in pre-push hook | PASSED |

## Test Counts

- Total tests: 411 passing
- New tests added in Phase 20:
  - test_engine.py: 117 tests
  - test_main.py: 16 tests
  - test_gauge.py additions: 5 tests (load_weights)
  - test_ratios.py additions: 10+ tests (load_asx_futures_csv, edge cases)

## Phase Goal

Goal: "The pipeline orchestration layer (engine.py, main.py) reaches 85%+ coverage and the per-module coverage gate is active in npm scripts and the pre-push hook, making coverage regression impossible to push undetected"

**Achieved:** engine.py 96%, main.py 93%, all 13 modules ≥85%, coverage gate active in both npm test:fast and lefthook pre-push.
