# Phase 20: Research — Orchestration Tests and Enforcement

**Generated:** 2026-02-25
**Method:** Direct file analysis

---

## 1. engine.py — All Functions

File: `pipeline/normalize/engine.py` (432 lines)

### Imports (bound at import time)
```python
from pipeline.config import (INDICATOR_CONFIG, OPTIONAL_INDICATOR_CONFIG,
    STATUS_OUTPUT, WEIGHTS_FILE, ZSCORE_CLAMP_MAX, ZSCORE_CLAMP_MIN, ZSCORE_WINDOW_YEARS)
from pipeline.normalize.gauge import (apply_polarity, classify_zone, compute_hawk_score,
    generate_verdict, load_weights, zscore_to_gauge)
from pipeline.normalize.ratios import load_asx_futures_csv, normalize_indicator
from pipeline.normalize.zscore import compute_rolling_zscores, determine_confidence
```

**KEY FINDING:** `STATUS_OUTPUT` is imported via `from pipeline.config import STATUS_OUTPUT` — bound at import time. Patch target must be `pipeline.normalize.engine.STATUS_OUTPUT`.

### Function: `generate_interpretation(indicator_name, zone, raw_value)`
- **Pure function** — no I/O, no side effects.
- `indicator_name`: one of 8 keys: inflation, wages, employment, spending, building_approvals, housing, business_confidence, asx_futures
- `zone`: one of: cold, cool, neutral, warm, hot
- Returns: string from nested dict lookup, or fallback `f'{indicator_name} data available'`
- **Branches:** 8 indicators × 5 zones = 40 known cases + fallback (unknown indicator or unknown zone)
- **Test approach:** `@pytest.mark.parametrize` with all 8×5 + fallback

### Function: `build_gauge_entry(name, latest_row, z_df, weight_config, config=None)`
- **Mixed pure/I/O** — normally pure, but has two special branches that read CSV files from `DATA_DIR`
- Parameters:
  - `name`: indicator name string
  - `latest_row`: dict-like row with `z_score`, `value`, `date` (datetime), `window_size`
  - `z_df`: DataFrame with `z_score` column (for history)
  - `weight_config`: dict with `polarity` (default 1), `weight`
  - `config`: optional indicator config dict
- Key operations: `apply_polarity`, `zscore_to_gauge`, `classify_zone`, `determine_confidence`, `generate_interpretation`
- **Housing branch** (line 150): reads `corelogic_housing.csv` from `pipeline.config.DATA_DIR`. Uses `pipeline.config.DATA_DIR` at call time — isolated by `isolate_data_dir` autouse fixture.
- **Business_confidence branch** (line 185): reads `nab_capacity.csv` from `pipeline.config.DATA_DIR`. Computes `long_run_avg`, `direction` (STEADY/RISING/FALLING).
- Returns: dict with gauge metadata fields matching status.json schema
- `staleness_days` computed as `(datetime.now() - data_date).days` — need datetime freeze
- `data_date` is a datetime object from the row

### Function: `build_asx_futures_entry()`
- Reads `pipeline.config.DATA_DIR / "asx_futures.csv"` via `load_asx_futures_csv`
- If data is None: returns None
- Direction logic: `change_bp < -5` → 'cut', `> 5` → 'hike', else 'hold'
- `staleness_days` computed from `data_date` string via `datetime.strptime` — need datetime freeze
- Optional `meetings` array processing with date label formatting
- **Patch target for load_asx_futures_csv:** `pipeline.normalize.engine.load_asx_futures_csv`

### Function: `process_indicator(name, config, weight_config)`
- Calls `normalize_indicator` (bound import), then `compute_rolling_zscores`, then `build_gauge_entry`
- Returns `(None, None)` if: normalize returns None, empty df, or no valid z-scores
- Has adaptive `min_q` logic for indicators with limited history
- **Patch targets:** `pipeline.normalize.engine.normalize_indicator`, `pipeline.normalize.engine.compute_rolling_zscores`

### Function: `generate_status()`
- Top-level orchestrator — calls `process_indicator` for all configs, computes hawk score, writes `STATUS_OUTPUT`
- Calls `load_weights(WEIGHTS_FILE)` — mock `pipeline.normalize.engine.load_weights`
- Calls `compute_hawk_score`, `classify_zone`, `generate_verdict` — all bound imports from gauge
- Calls `build_asx_futures_entry()` — same module, no mocking needed (mock its dep `load_asx_futures_csv`)
- **Writes STATUS_OUTPUT:** `STATUS_OUTPUT.parent.mkdir(parents=True, exist_ok=True); json.dump(status, f)`
- Returns: complete status dict

---

## 2. main.py — All Functions

File: `pipeline/main.py` (280 lines)

### Module-level lists (module attributes, patchable)
```python
CRITICAL_SOURCES = [('RBA Cash Rate', rba_data), ('ABS CPI', lambda: ...), ('ABS Employment', lambda: ...)]
IMPORTANT_SOURCES = [('ABS Household Spending', lambda: ...), ('ABS Wage Price Index', lambda: ...)]
OPTIONAL_SOURCES = [('ABS Building Approvals', lambda: ...), ('CoreLogic Housing', corelogic_scraper), ('NAB Capacity', nab_scraper)]
```

### `NORMALIZATION_AVAILABLE` flag (module-level)
- Set at import time via try/except ImportError of `generate_status`
- Patch target: `pipeline.main.NORMALIZATION_AVAILABLE`

### Function: `run_pipeline() -> dict[str, Any]`
- Phase 1: Iterates `CRITICAL_SOURCES` — calls lambda or `.fetch_and_save()`. On exception: sets `results['status'] = 'failed'`, calls `sys.exit(1)`
- Phase 2: Iterates `IMPORTANT_SOURCES` — on exception: adds to `important_failures`, continues
- Phase 3: Iterates `OPTIONAL_SOURCES` — on exception OR `result.get('status') == 'failed'`: adds to `optional_failures`
- Phase 4: Normalization — if `NORMALIZATION_AVAILABLE`, calls `generate_status()`; on exception: non-fatal
- Returns: results dict

### `sys.exit(1)` location: line 106 — inside `except Exception` block for critical sources

### Lambda detection logic (lines 77-81):
```python
is_lambda = callable(module) and hasattr(module, '__name__') and '<lambda>' in str(module)
if is_lambda:
    result = module()
else:
    result = module.fetch_and_save()
```

---

## 3. STATUS_OUTPUT — Import Chain

In `config.py`:
```python
STATUS_OUTPUT = Path("public") / "data" / "status.json"  # line 242
```

In `engine.py`:
```python
from pipeline.config import STATUS_OUTPUT  # line 19 — bound at import time!
```

**Patch target: `pipeline.normalize.engine.STATUS_OUTPUT`** (not `pipeline.config.STATUS_OUTPUT`)

---

## 4. Existing Fixtures in conftest.py

### Autouse (every test):
1. `isolate_data_dir(monkeypatch, tmp_path)` — patches `pipeline.config.DATA_DIR` to `tmp_path`
2. `block_network(monkeypatch, request)` — blocks all network unless `@pytest.mark.live`

### Named fixtures (request explicitly):
- `fixture_cpi_df`, `fixture_employment_df`, `fixture_wages_df`, `fixture_spending_df`, `fixture_building_approvals_df`, `fixture_housing_df`, `fixture_nab_capacity_df`
- `fixture_abs_response`, `fixture_abs_response_empty`, `fixture_rba_response`, `fixture_rba_response_empty`
- `fixture_asx_response`, `fixture_asx_response_empty`
- `fixture_nab_html`, `fixture_nab_html_no_data`, `fixture_corelogic_html`, `fixture_corelogic_html_no_pdf`

### Available fixture CSV files:
`abs_cpi.csv`, `abs_employment.csv`, `abs_wage_price_index.csv`, `abs_household_spending.csv`, `abs_building_approvals.csv`, `corelogic_housing.csv`, `nab_capacity.csv`, `asx_response.json`

---

## 5. Current npm Scripts

```json
"test:fast": "npm run lint && python -m pytest tests/python/ -m \"not live\"",
"verify:fast": "npm run lint && python -m pytest tests/python/ -m \"not live\""
```

Target: append `&& python scripts/check_coverage.py --min 85` to both.

---

## 6. lefthook.yml Current State

```yaml
pre-push:
  parallel: true
  commands:
    lint-py:
      run: ruff check pipeline/ tests/
      timeout: "30s"
    lint-js:
      run: npx eslint public/js/
      timeout: "30s"
    unit-tests:
      run: pytest tests/python/ -m "not live"
      timeout: "30s"
```

Target: Chain `&& python scripts/check_coverage.py --min 85` into the `unit-tests` run command; bump timeout to `45s`.

---

## 7. Current Coverage State

```
pipeline/main.py                           123    123     0%   14-278
pipeline/normalize/engine.py               155    155     0%   12-431
pipeline/normalize/gauge.py                 62     12    81%   (below 85% threshold)
pipeline/normalize/ratios.py               133     43    68%   (below 85% threshold)
```

**Test count:** 264 passing unit tests + 10 deselected live tests

**Gaps to fix:** engine.py (0%), main.py (0%), gauge.py (81%), ratios.py (68%) all need work.

---

## 8. Existing Test Pattern (Phase 19)

From `test_ingest_abs.py`:
- Helper `_make_mock_session(responses)` returns `MagicMock()` session
- Patch target pattern: `pipeline.ingest.abs_data.create_session`
- Uses `with patch('pipeline.ingest.abs_data.create_session', return_value=mock_session):`
- Classes organized by function under test (`TestParseAbsDate`, `TestFetchAbsSeries`, etc.)

---

## 9. check_coverage.py Behavior

- Reads `.coverage.json` at project root (written by `--cov-report=json:.coverage.json` in pyproject.toml addopts)
- Filters to files starting with `pipeline/` with `num_statements > 0`
- Exits 0 if all modules >= threshold, exits 1 if any below
- Already wired in pyproject.toml addopts: `--cov-report=json:.coverage.json` runs on every pytest invocation

---

## 10. Weights File

`WEIGHTS_FILE = DATA_DIR / "weights.json"` — accessed via `pipeline.config.DATA_DIR` at call time (late-bound). Must provide a `weights.json` in `tmp_path` for `generate_status()` tests, OR mock `load_weights` directly.

Since `isolate_data_dir` patches `DATA_DIR` to `tmp_path`, the `WEIGHTS_FILE` will resolve to `tmp_path / "weights.json"` — which won't exist. Mock `pipeline.normalize.engine.load_weights` is the safest approach.

---

*Research completed: 2026-02-25*
