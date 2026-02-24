# Phase 12: Python Unit Tests - Research

**Researched:** 2026-02-25
**Domain:** pytest unit testing of mathematical/data-pipeline Python modules
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Coverage depth**
- Thorough edge cases for z-score: empty input, single-row data, all-identical values (MAD=0), NaN in series, window larger than dataset
- Gauge/hawk score: known-answer tests with hand-verified indicator combinations AND zone boundary precision tests (exact threshold values like 50.0, 33.3)
- YoY ratios: standard ratios, hybrid Cotality-to-ABS data source transition, AND missing/partial/gapped prior-year data
- CSV handler: read/write happy path plus defensive coverage — missing columns, empty file, duplicate timestamps, encoding edge cases
- The live `data/` directory must remain untouched by all tests

**Test data strategy**
- Primarily lean on Phase 11 fixture CSVs as main test data source
- Add small inline data only for edge cases the fixtures don't cover
- Hand-calculated expected values for core formulas (MAD, median) — tests verify the code matches the math
- Use scipy/numpy as reference oracle for complex rolling-window scenarios
- Use `@pytest.mark.parametrize` where natural — especially for functions with clear input/output pairs (score-to-zone mapping, multiple CSV scenarios)

**Test file organization**
- All tests as top-level functions, no test classes for grouping
- File structure, naming conventions, and docstring approach at Claude's discretion — pick what best fits the actual source code layout and Phase 11's existing test infrastructure

**Schema validation strictness**
- `additionalProperties: false` — no extra keys allowed in status.json; catches drift early
- `hawk_score` must be an integer in [0, 100] — no decimals, no values outside range
- Zone enum values strictly validated — unknown zone strings must fail validation
- Validation library/approach at Claude's discretion (jsonschema available in requirements-dev.txt)

### Claude's Discretion
- Test file directory structure (tests/python/unit/ vs flat)
- Floating-point tolerance strategy per function
- Test naming and docstring conventions
- Schema validation implementation approach (jsonschema vs hand-written)
- Exact file-to-module mapping

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| UNIT-01 | Z-score calculations verified (rolling window, median/MAD, gauge mapping) | `calculate_mad`, `robust_zscore`, `compute_rolling_zscores` fully mapped; edge cases identified from source code inspection |
| UNIT-02 | Zone classification and hawk score computation verified | `classify_zone`, `compute_hawk_score`, `zscore_to_gauge`, `generate_verdict` fully mapped; exact boundary values documented |
| UNIT-03 | YoY ratio normalization verified (including hybrid Cotality/ABS handling) | `compute_yoy_pct_change`, `normalize_indicator` hybrid path fully mapped; fixture CSV has ABS-only rows; inline Cotality rows needed for hybrid path |
| UNIT-04 | CSV read/write operations verified (dedup, timestamp handling) | `append_to_csv` in `pipeline/utils/csv_handler.py` fully mapped; tmp_path isolation already provided by conftest |
| UNIT-05 | status.json validated against schema (required keys, value ranges [0-100], valid zone enums) | Full status.json schema derived from production file; jsonschema 4.26.0 installed |
</phase_requirements>

---

## Summary

Phase 12 writes unit tests for five Python modules that form the mathematical core and data pipeline of the RBA Hawk-O-Meter. All test infrastructure from Phase 11 is in place: pytest 9.0.2 with `--strict-markers`, an autouse `isolate_data_dir` fixture that patches `pipeline.config.DATA_DIR` to a `tmp_path`, an autouse `block_network` fixture, named CSV loader fixtures for all seven production fixture files, and a passing smoke test suite (4 tests, 0.01 seconds). The 10-second budget is trivially achievable — all target functions are pure Python/numpy/pandas with no I/O except for `csv_handler` tests, which write to `tmp_path`.

The five source modules under test are well-isolated and individually importable without side effects. `zscore.py` and `gauge.py` are purely functional (no I/O). `ratios.py` uses `DATA_DIR` which is already patched. `csv_handler.py` takes explicit `Path` arguments so tests simply pass `tmp_path / "test.csv"` — no patching needed for it. `status.json` schema validation is a pure data-validation test requiring no live pipeline execution.

The one subtlety worth planning around: `SOURCE_METADATA` paths in `pipeline/config.py` are computed at import time from the original `DATA_DIR` value and are NOT retroactively updated by the `monkeypatch` (noted in conftest.py comments). Any test that calls `normalize_indicator` must pass explicit `csv_path` values rather than relying on `SOURCE_METADATA`, or must additionally patch `SOURCE_METADATA` entries individually. The `ratios.py` `normalize_indicator` function computes its path as `DATA_DIR / csv_file` — since `DATA_DIR` is patched at call time (not import time), this path IS correctly redirected by the autouse fixture.

**Primary recommendation:** Organize test files flat in `tests/python/` (no subdirectory), one file per source module, using top-level functions and `@pytest.mark.parametrize` for data-driven cases.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest | 9.0.2 | Test runner, fixtures, parametrize, markers | Already installed; configured in pyproject.toml |
| numpy | (production dep) | Reference oracle for MAD/median calculations | Already in production; no additional install |
| pandas | (production dep) | DataFrame construction for test inputs | Already in production; no additional install |
| jsonschema | 4.26.0 | status.json schema validation (UNIT-05) | Already in requirements-dev.txt |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| scipy.stats | (optional) | Reference oracle for complex rolling scenarios | Only if hand-calculation is ambiguous; not required |
| pytest.approx | built-in | Floating-point equality assertions | Use for all float comparisons instead of `==` |
| tmp_path | built-in pytest fixture | Isolated file I/O for csv_handler tests | Use for UNIT-04; already available via conftest |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| jsonschema | hand-written validation | jsonschema gives declarative schema + better error messages; hand-written is more work for same coverage |
| pytest.approx | math.isclose | pytest.approx integrates with assert; math.isclose requires manual message construction |
| flat test files | tests/python/unit/ subdirectory | Flat is simpler; only meaningful if test count >15 files |

**Installation:** All packages already installed via `pip install -r requirements-dev.txt`.

---

## Architecture Patterns

### Recommended Project Structure

```
tests/python/
├── conftest.py              # Phase 11 — autouse fixtures, CSV loaders (DO NOT MODIFY)
├── fixtures/                # Phase 11 — production snapshot CSVs (DO NOT MODIFY)
│   ├── abs_cpi.csv
│   ├── abs_employment.csv
│   ├── abs_wage_price_index.csv
│   ├── abs_household_spending.csv
│   ├── abs_building_approvals.csv
│   ├── corelogic_housing.csv
│   └── nab_capacity.csv
├── test_smoke.py            # Phase 11 — infrastructure tests (DO NOT MODIFY)
├── test_zscore.py           # Phase 12 — UNIT-01 (calculate_mad, robust_zscore, compute_rolling_zscores)
├── test_gauge.py            # Phase 12 — UNIT-01 (zscore_to_gauge) + UNIT-02 (classify_zone, compute_hawk_score)
├── test_ratios.py           # Phase 12 — UNIT-03 (compute_yoy_pct_change, normalize_indicator hybrid path)
├── test_csv_handler.py      # Phase 12 — UNIT-04 (append_to_csv happy path + edge cases)
└── test_schema.py           # Phase 12 — UNIT-05 (status.json jsonschema validation)
```

### Pattern 1: Pure Function Unit Tests with Inline Data

**What:** Test pure mathematical functions (no I/O) by constructing small DataFrames inline.
**When to use:** `calculate_mad`, `robust_zscore`, `zscore_to_gauge`, `classify_zone`, `compute_hawk_score`, `compute_yoy_pct_change`, `filter_valid_data`.

```python
# Source: pyproject.toml pythonpath=["."] means pipeline imports work directly

import numpy as np
import pandas as pd
import pytest
from pipeline.normalize.zscore import calculate_mad, robust_zscore

def test_calculate_mad_known_values():
    """MAD = median(|x_i - median|) * 1.4826. Hand-verified: median([1,2,3])=2, deviations=[1,0,1], MAD=1*1.4826."""
    values = np.array([1.0, 2.0, 3.0])
    result = calculate_mad(values)
    assert result == pytest.approx(1.4826, rel=1e-4)

def test_calculate_mad_all_identical_returns_zero():
    """MAD must be 0.0 when all values identical — critical for zero-division guard in robust_zscore."""
    values = np.array([5.0, 5.0, 5.0])
    assert calculate_mad(values) == 0.0
```

### Pattern 2: Parametrize for Input/Output Pairs

**What:** Use `@pytest.mark.parametrize` for functions with clear input/output tables.
**When to use:** Zone classification (exact boundary values), `generate_verdict` verdicts, gauge-to-zone mapping.

```python
import pytest
from pipeline.normalize.gauge import classify_zone

@pytest.mark.parametrize("gauge,expected_zone,expected_label", [
    (0.0,  "cold",    "Strong dovish pressure"),
    (19.9, "cold",    "Strong dovish pressure"),
    (20.0, "cool",    "Mild dovish pressure"),
    (39.9, "cool",    "Mild dovish pressure"),
    (40.0, "neutral", "Balanced"),
    (50.0, "neutral", "Balanced"),
    (59.9, "neutral", "Balanced"),
    (60.0, "warm",    "Mild hawkish pressure"),
    (79.9, "warm",    "Mild hawkish pressure"),
    (80.0, "hot",     "Strong hawkish pressure"),
    (100.0,"hot",     "Strong hawkish pressure"),
])
def test_classify_zone_boundaries(gauge, expected_zone, expected_label):
    """Verify zone classification at exact boundary values (< 20, < 40, < 60, < 80, >= 80)."""
    zone_id, zone_label = classify_zone(gauge)
    assert zone_id == expected_zone
    assert zone_label == expected_label
```

### Pattern 3: Fixture CSV Tests via conftest.py Fixtures

**What:** Use named fixture fixtures from conftest.py (e.g., `fixture_cpi_df`) for tests that need realistic data shapes.
**When to use:** `compute_yoy_pct_change`, `compute_rolling_zscores`, `resample_to_quarterly` with real fixture data.

```python
def test_yoy_pct_change_monthly_fixture(fixture_cpi_df):
    """YoY on 40-row monthly CPI fixture should yield 28 valid rows (40 - 12 monthly shift)."""
    from pipeline.normalize.ratios import compute_yoy_pct_change
    result = compute_yoy_pct_change(fixture_cpi_df, periods=12)
    assert len(result) == len(fixture_cpi_df) - 12
    assert result['value'].notna().all()
```

### Pattern 4: tmp_path CSV Handler Tests

**What:** Use pytest's built-in `tmp_path` fixture for CSV write/read tests. The autouse `isolate_data_dir` fixture patches `DATA_DIR` but `append_to_csv` takes an explicit path argument — pass `tmp_path / "test.csv"` directly.
**When to use:** All `csv_handler.py` tests (UNIT-04).

```python
def test_append_to_csv_creates_new_file(tmp_path):
    """append_to_csv creates file if it doesn't exist, returns correct row count."""
    from pipeline.utils.csv_handler import append_to_csv
    import pandas as pd
    data = pd.DataFrame({"date": ["2024-01-01", "2024-02-01"], "value": [1.0, 2.0]})
    path = tmp_path / "test.csv"
    count = append_to_csv(path, data)
    assert count == 2
    assert path.exists()
    result = pd.read_csv(path)
    assert list(result["date"]) == ["2024-01-01", "2024-02-01"]
```

### Pattern 5: jsonschema Validation Tests

**What:** Define the status.json schema as a Python dict, then validate both valid and invalid documents.
**When to use:** UNIT-05 tests. Use `jsonschema.validate()` for valid cases, `pytest.raises(jsonschema.ValidationError)` for failure cases.

```python
import json
import pytest
import jsonschema

STATUS_SCHEMA = {
    "type": "object",
    "required": ["generated_at", "pipeline_version", "overall", "gauges", "weights", "metadata"],
    "additionalProperties": True,  # top-level allows asx_futures optional key
    "properties": {
        "overall": {
            "type": "object",
            "required": ["hawk_score", "zone", "zone_label", "verdict", "confidence"],
            "additionalProperties": False,
            "properties": {
                "hawk_score": {"type": "integer", "minimum": 0, "maximum": 100},
                "zone": {"type": "string", "enum": ["cold", "cool", "neutral", "warm", "hot", "unknown"]},
                "zone_label": {"type": "string"},
                "verdict": {"type": "string"},
                "confidence": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH"]},
            }
        },
        # ... other properties
    }
}

def test_schema_rejects_hawk_score_decimal():
    """hawk_score must be integer — 52.0 is not valid (float)."""
    doc = {"generated_at": "...", "pipeline_version": "1.0", "overall": {"hawk_score": 52.0, ...}, ...}
    with pytest.raises(jsonschema.ValidationError, match="hawk_score"):
        jsonschema.validate(doc, STATUS_SCHEMA)
```

### Anti-Patterns to Avoid

- **Importing `from pipeline.config import DATA_DIR` in tests:** The autouse fixture patches `pipeline.config.DATA_DIR` (the module attribute), not local name bindings. Always access via `pipeline.config.DATA_DIR` at call time, or pass paths explicitly.
- **Floating-point equality with `==`:** Use `pytest.approx()` for all float comparisons; the MAD formula involves multiplying by 1.4826 which creates representation noise.
- **Testing the normalization engine orchestrator (`engine.py`):** `generate_status()` and `process_indicator()` are integration-level; they're out of scope for Phase 12. Test the leaf functions they call instead.
- **Using autouse `isolate_data_dir` as justification to call `normalize_indicator` with no additional setup:** `normalize_indicator` reads from `DATA_DIR / csv_file`. The autouse fixture patches `DATA_DIR` to `tmp_path` (which is empty), so calling `normalize_indicator` will return `None` unless you copy fixture CSVs into `tmp_path` first — or pass the fixture DataFrame path explicitly to the underlying functions.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Floating-point comparison | custom `abs(a-b) < 1e-6` assertions | `pytest.approx()` | Handles relative vs absolute tolerance; integrates with `assert`; handles arrays |
| JSON schema definition and validation | manual key checking loops | `jsonschema.validate()` | Declarative; catches missing keys, type errors, range violations, enum violations in one call; installed |
| Temporary file isolation | `import tempfile; tempfile.mkdtemp()` | pytest `tmp_path` fixture | Auto-cleaned after test; already familiar from conftest autouse |
| Reference values for MAD | complex manual calculation | numpy computation inline | `np.median(np.abs(arr - np.median(arr))) * 1.4826` is the reference; use it to derive expected values |

**Key insight:** The test modules under test are themselves well-factored — leaf functions accept explicit arguments rather than reaching into global state, which makes them easy to test without mocking.

---

## Common Pitfalls

### Pitfall 1: SOURCE_METADATA Paths Baked at Import Time

**What goes wrong:** `SOURCE_METADATA` in `pipeline/config.py` is built as `DATA_DIR / "abs_cpi.csv"` at module import time. Patching `pipeline.config.DATA_DIR` later does NOT retroactively update these paths.
**Why it happens:** Python evaluates the `SOURCE_METADATA` dict at import time using the original `DATA_DIR` value.
**How to avoid:** Tests that call `normalize_indicator` don't need `SOURCE_METADATA` — `normalize_indicator` computes `csv_path = DATA_DIR / csv_file` at call time, which IS patched correctly. For `build_gauge_entry` in engine.py which accesses `DATA_DIR` at call time for housing/business_confidence — those are out of scope for Phase 12.
**Warning signs:** Test calls `normalize_indicator` and gets a file from the live `data/` directory despite the autouse fixture.

### Pitfall 2: normalize_indicator Returns None Unless Data Is in tmp_path

**What goes wrong:** `normalize_indicator` checks `DATA_DIR / csv_file` (which after autouse patching is `tmp_path / "abs_cpi.csv"`). Since `tmp_path` is empty, the function returns `None`.
**Why it happens:** The autouse fixture redirects the data directory to an empty temp directory.
**How to avoid:** For UNIT-03 tests, either: (a) copy the fixture CSV into `tmp_path / csv_file` before calling `normalize_indicator`, or (b) test the underlying functions directly (`compute_yoy_pct_change`, `load_indicator_csv`, `filter_valid_data`) using DataFrames loaded from fixtures.
**Recommendation:** Option (b) is cleaner — test the math functions directly with fixture DataFrames. Only use option (a) if you specifically want to test `normalize_indicator`'s hybrid-source detection path.

### Pitfall 3: Window Size Too Small for ZScore to Produce Non-NaN Results

**What goes wrong:** `compute_rolling_zscores` with default `min_quarters=20` won't produce any non-NaN z-scores unless the input DataFrame has at least 21 rows (current row needs 20-row look-back window).
**Why it happens:** The function requires `len(window) >= min_quarters` to compute z-score; for the first 20 rows, `window` is too small.
**How to avoid:** For edge case tests, pass explicit `min_quarters=2` (or `window_quarters` appropriate to test size). For fixture-based tests, verify fixture sizes first — abs_cpi.csv has 40 rows (quarterly after resampling: 40/3 ~ 13 quarters), which may still be under the default 20-quarter minimum. Pass `min_quarters=5` or smaller for fixture-based rolling tests.
**Warning signs:** Test asserts on `result['z_score']` but all values are NaN.

### Pitfall 4: Cotality/ABS Hybrid Test Requires CSV with `source` Column

**What goes wrong:** `normalize_indicator`'s hybrid detection reads the `source` column to separate Cotality HVI rows from ABS RPPI rows. Tests that pass a plain `date/value` DataFrame bypass this path.
**Why it happens:** The hybrid detection reads the raw CSV file from disk (`pd.read_csv(raw_path)`) before the standard load path runs.
**How to avoid:** To test the hybrid path in UNIT-03, write a test CSV with mixed `source` values into `tmp_path` and call `normalize_indicator` with the `tmp_path` version of `DATA_DIR` patched. The corelogic fixture doesn't contain Cotality rows — you'll need inline test data for this path.
**Warning signs:** Test for hybrid path passes even when Cotality handling code is deleted (the hybrid code was never exercised).

### Pitfall 5: hawk_score Schema Expects Integer, Engine Produces Float

**What goes wrong:** UNIT-05 requires `hawk_score` to be an integer. The production `status.json` contains `"hawk_score": 52.0` (a float). The schema test must validate the schema's integer requirement AND the production file would fail this test if validated directly.
**Why it happens:** `engine.py` uses `round(hawk_score, 1)` which produces a float. The schema requirement is a business rule, not the current implementation.
**How to avoid:** The schema validation test should NOT load the live `public/data/status.json` — it should construct minimal valid and invalid test documents inline. The schema definition is what's being tested, not the production file's current state. The NOTE in the conftest is clear: `STATUS_OUTPUT = Path("public") / "data" / "status.json"` is NOT patched by `isolate_data_dir` (only `DATA_DIR` is patched).
**Warning signs:** Confusion about whether tests should validate the current production status.json vs. the schema contract.

### Pitfall 6: compute_yoy_pct_change with periods=12 on Quarterly Data

**What goes wrong:** `abs_cpi.csv` fixture has 40 rows of quarterly data but `periods=12` is for monthly. Using `periods=12` on quarterly data would shift by 12 quarters (3 years), not 12 months (1 year).
**Why it happens:** The fixture CSVs are quarterly snapshots from production but the production pipeline resamples monthly data to quarterly before computing z-scores.
**How to avoid:** When testing `compute_yoy_pct_change` with fixture data, use `periods=4` (quarterly) to match fixture frequency. When testing the monthly path, construct small inline DataFrames. Alternatively, note that `abs_employment.csv` and `abs_cpi.csv` have 40+ rows so `periods=4` on them gives 36+ valid rows — sufficient for z-score tests.

---

## Code Examples

Verified patterns from source code inspection:

### calculate_mad Reference Values (for test assertions)

```python
# From pipeline/normalize/zscore.py:
# MAD = median(|x_i - median(x)|) * 1.4826
#
# Hand-verified test cases:
# [1.0, 2.0, 3.0]:  median=2.0, deviations=[1,0,1], median(deviations)=1.0, MAD=1.4826
# [1.0, 1.0, 5.0]:  median=1.0, deviations=[0,0,4], median(deviations)=0.0, MAD=0.0 ← edge case
# [2.0, 4.0, 6.0, 8.0]: median=5.0, deviations=[3,1,1,3], median(deviations)=2.0, MAD=2.9652
```

### zscore_to_gauge Reference Values (for test assertions)

```python
# From pipeline/normalize/gauge.py:
# gauge = ((z - clamp_min) / (clamp_max - clamp_min)) * 100
# With clamp_min=-3.0, clamp_max=3.0:
#   z=0.0  → gauge = (0.0 - (-3.0)) / 6.0 * 100 = 50.0
#   z=3.0  → gauge = 100.0 (then clipped to 100.0)
#   z=-3.0 → gauge = 0.0
#   z=1.5  → gauge = (1.5 + 3.0) / 6.0 * 100 = 75.0
#   z=4.0  → gauge = clipped to 100.0 (out of range)
#   z=NaN  → gauge = NaN (isnan guard in source)
```

### jsonschema — Validate Overall Section

```python
# jsonschema 4.26.0 is installed (verified via pip)
import jsonschema

# Use Draft7Validator or default validate() — both work for this schema
schema = {
    "type": "object",
    "required": ["hawk_score", "zone", "zone_label", "verdict", "confidence"],
    "additionalProperties": False,
    "properties": {
        "hawk_score": {"type": "integer", "minimum": 0, "maximum": 100},
        "zone": {"type": "string", "enum": ["cold", "cool", "neutral", "warm", "hot", "unknown"]},
        "zone_label": {"type": "string"},
        "verdict": {"type": "string"},
        "confidence": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH"]},
    }
}

# Valid document — no exception raised
jsonschema.validate({"hawk_score": 52, "zone": "neutral", ...}, schema)

# Invalid — hawk_score is float, not integer
with pytest.raises(jsonschema.ValidationError):
    jsonschema.validate({"hawk_score": 52.0, "zone": "neutral", ...}, schema)

# Invalid — unknown zone string
with pytest.raises(jsonschema.ValidationError):
    jsonschema.validate({"hawk_score": 52, "zone": "scorching", ...}, schema)
```

### Hybrid-Source CSV Construction for UNIT-03

```python
import pandas as pd

def make_hybrid_housing_csv(tmp_path):
    """Create a housing CSV with mixed ABS/Cotality rows for hybrid path testing."""
    rows = [
        # ABS RPPI index values (need YoY normalization)
        {"date": "2020-01-01", "value": 100.0, "source": "ABS"},
        {"date": "2021-01-01", "value": 105.0, "source": "ABS"},
        {"date": "2022-01-01", "value": 110.0, "source": "ABS"},
        # Cotality HVI pre-computed YoY % (should NOT be double-normalized)
        {"date": "2023-01-01", "value": 9.4, "source": "Cotality HVI"},
    ]
    df = pd.DataFrame(rows)
    csv_path = tmp_path / "corelogic_housing.csv"
    df.to_csv(csv_path, index=False)
    return csv_path
```

### append_to_csv Deduplication Verification

```python
def test_append_to_csv_deduplicates_by_date(tmp_path):
    """Duplicate date keeps last occurrence (newest data wins)."""
    import pandas as pd
    from pipeline.utils.csv_handler import append_to_csv

    path = tmp_path / "test.csv"
    initial = pd.DataFrame({"date": ["2024-01-01"], "value": [1.0]})
    append_to_csv(path, initial)

    # Same date, different value (simulates re-scrape with correction)
    updated = pd.DataFrame({"date": ["2024-01-01"], "value": [1.5]})
    append_to_csv(path, updated)

    result = pd.read_csv(path)
    assert len(result) == 1  # deduplicated
    assert result["value"].iloc[0] == pytest.approx(1.5)  # last wins
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `pytest.ini` or `setup.cfg` | `[tool.pytest.ini_options]` in `pyproject.toml` | pytest 6.0+ | Already using current approach (pyproject.toml) |
| `unittest.TestCase` classes | top-level functions with fixtures | pytest idiom | User locked: no test classes |
| `assert a == b` for floats | `assert a == pytest.approx(b)` | pytest 3.0+ | Must use approx for all MAD/zscore assertions |

**Deprecated/outdated:**
- `pytest.ini` / `setup.cfg`: Legacy config locations; project uses `pyproject.toml` correctly.
- `jsonschema.Draft4Validator`: Current jsonschema 4.x defaults to Draft 2020-12; use `jsonschema.validate()` directly for simplicity.

---

## Open Questions

1. **Floating-point tolerance for MAD tests**
   - What we know: `calculate_mad([1,2,3])` produces `1.4826` multiplied by `np.float64`; `pytest.approx` default is `rel=1e-6`
   - What's unclear: Whether `rel=1e-4` or `abs=1e-9` is more appropriate for hand-verified cases
   - Recommendation: Use `pytest.approx(expected, rel=1e-4)` for MAD results; `abs=1e-9` for cases where expected is 0.0

2. **scipy availability for rolling oracle**
   - What we know: CONTEXT.md says "use scipy/numpy as reference oracle for complex rolling-window scenarios"
   - What's unclear: Whether scipy is installed in the venv
   - Recommendation: Check with `pip show scipy`; if not present, hand-calculate expected values for the rolling window tests (the window is small enough to compute by hand for 10-20 row test DataFrames)

3. **`hawk_score` integer vs float in schema**
   - What we know: Production status.json has `"hawk_score": 52.0` (float). CONTEXT.md says schema must require integer.
   - What's unclear: Whether a future engine fix to emit `int(round(hawk_score))` is in scope for Phase 12
   - Recommendation: Phase 12 defines the schema contract only. The schema test validates the rule; fixing the engine to comply is a separate concern (not in Phase 12 scope). The test should pass valid integer documents and reject float documents.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | `pyproject.toml` — `[tool.pytest.ini_options]` |
| Quick run command | `pytest tests/python/ -m "not live" -q` |
| Full suite command | `pytest tests/python/ -m "not live" -v` |
| Estimated runtime | < 2 seconds (all pure math/DataFrame operations; no disk or network I/O except tmp_path) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| UNIT-01 | `calculate_mad` with known values, MAD=0 edge case, `robust_zscore` zero-MAD guard, `compute_rolling_zscores` window behavior and NaN output | unit | `pytest tests/python/test_zscore.py -x -m "not live"` | ❌ Wave 0 gap |
| UNIT-01 | `zscore_to_gauge` linear mapping with known z-scores, NaN passthrough, clamping at ±3 | unit | `pytest tests/python/test_gauge.py -x -m "not live"` | ❌ Wave 0 gap |
| UNIT-02 | `classify_zone` at exact boundaries (19.9→cold, 20.0→cool, etc.), NaN→unknown, `compute_hawk_score` rebalancing with missing indicators, `generate_verdict` zone thresholds | unit | `pytest tests/python/test_gauge.py -x -m "not live"` | ❌ Wave 0 gap |
| UNIT-03 | `compute_yoy_pct_change` with monthly periods=12 and quarterly periods=4, `load_indicator_csv` with missing file/empty/missing column, hybrid Cotality/ABS normalization path | unit | `pytest tests/python/test_ratios.py -x -m "not live"` | ❌ Wave 0 gap |
| UNIT-04 | `append_to_csv` creates new file, appends without duplicates, deduplicates by date (last wins), handles missing columns gracefully | unit | `pytest tests/python/test_csv_handler.py -x -m "not live"` | ❌ Wave 0 gap |
| UNIT-05 | valid status.json passes schema, missing required key fails, `hawk_score` float fails, `hawk_score` out-of-range fails, invalid zone enum fails | unit | `pytest tests/python/test_schema.py -x -m "not live"` | ❌ Wave 0 gap |

### Nyquist Sampling Rate
- **Minimum sample interval:** After every committed task → run: `pytest tests/python/ -m "not live" -q`
- **Full suite trigger:** Before merging final task of any plan wave
- **Phase-complete gate:** Full suite green before `/gsd:verify-work` runs
- **Estimated feedback latency per task:** < 2 seconds

### Wave 0 Gaps (must be created before implementation)
- [ ] `tests/python/test_zscore.py` — covers UNIT-01 z-score calculations
- [ ] `tests/python/test_gauge.py` — covers UNIT-01 gauge mapping + UNIT-02 zone/hawk score
- [ ] `tests/python/test_ratios.py` — covers UNIT-03 YoY normalization + hybrid path
- [ ] `tests/python/test_csv_handler.py` — covers UNIT-04 CSV read/write
- [ ] `tests/python/test_schema.py` — covers UNIT-05 status.json schema validation

*(All five test files are Wave 0 gaps — none exist yet. No framework install needed; pytest 9.0.2 and jsonschema 4.26.0 are already installed.)*

---

## Sources

### Primary (HIGH confidence)
- Source code inspection: `/Users/annon/projects/rba-hawko-meter/pipeline/normalize/zscore.py` — all functions, signatures, and formulas verified directly
- Source code inspection: `/Users/annon/projects/rba-hawko-meter/pipeline/normalize/gauge.py` — all functions, zone boundaries, hawk score formula verified
- Source code inspection: `/Users/annon/projects/rba-hawko-meter/pipeline/normalize/ratios.py` — hybrid-source detection path, `compute_yoy_pct_change`, `load_indicator_csv` verified
- Source code inspection: `/Users/annon/projects/rba-hawko-meter/pipeline/utils/csv_handler.py` — `append_to_csv` full behavior verified
- Source code inspection: `/Users/annon/projects/rba-hawko-meter/tests/python/conftest.py` — autouse fixtures, named CSV loaders, SOURCE_METADATA warning verified
- Source code inspection: `/Users/annon/projects/rba-hawko-meter/public/data/status.json` — full schema structure derived from production file
- `pip show jsonschema` equivalent: jsonschema 4.26.0 confirmed installed
- `pytest --version`: pytest 9.0.2 confirmed installed
- `pytest tests/python/ -m "not live" -q`: 4 passed, 0.01s — baseline confirmed clean

### Secondary (MEDIUM confidence)
- pyproject.toml `[tool.pytest.ini_options]` configuration — verified matches pytest 6+ current standard

### Tertiary (LOW confidence)
- scipy availability in venv — not verified; CONTEXT.md mentions it as optional oracle; confirm before using in tests

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all packages verified as installed; no new installs required
- Architecture: HIGH — source modules read directly; function signatures, edge cases, and data paths verified from code
- Pitfalls: HIGH — discovered from conftest.py comments, source code analysis, and known pytest monkeypatch behavior

**Research date:** 2026-02-25
**Valid until:** 2026-03-27 (stable domain; no external dependencies changing)
