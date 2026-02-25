# Architecture Research

**Domain:** Python test suite expansion — scraper mocking, orchestration testing
**Researched:** 2026-02-25
**Confidence:** HIGH (all findings derived from direct codebase inspection)

## Context: What This Research Covers

This extends the v2.0 ARCHITECTURE.md (test infrastructure: pyproject.toml, conftest, hook, lint) with v3.0 focus: integrating new test modules for the 5 ingest scrapers, `engine.py`, `main.py`, and `http_client.py` into the existing test architecture. No new infrastructure is needed. The question is: what new files are required, how do they use existing fixtures, what mocking patterns apply to each module, and in what order should they be built.

---

## System Overview

### Existing Architecture (v2.0, unchanged)

```
tests/python/
├── conftest.py              autouse: isolate_data_dir, block_network
│                            explicit: fixture_cpi_df, fixture_employment_df,
│                                      fixture_wages_df, fixture_spending_df,
│                                      fixture_building_approvals_df,
│                                      fixture_housing_df, fixture_nab_capacity_df
├── fixtures/                Static CSVs (version-controlled)
│   ├── abs_cpi.csv
│   ├── abs_employment.csv
│   ├── abs_household_spending.csv
│   ├── abs_wage_price_index.csv
│   ├── abs_building_approvals.csv
│   ├── corelogic_housing.csv
│   └── nab_capacity.csv
├── test_smoke.py            Infrastructure smoke tests (autouse verification)
├── test_zscore.py           Pure math — rolling z-score, MAD, confidence
├── test_gauge.py            Pure math — gauge scale, zones, hawk score
├── test_ratios.py           normalize_indicator: load, yoy, filter, resample
├── test_csv_handler.py      append_to_csv: create, dedup, sort, parents
├── test_schema.py           status.json contract validation (jsonschema)
└── test_live_sources.py     @pytest.mark.live — real HTTP calls
```

### v3.0 Target: New Test Files

```
tests/python/
├── [all existing files unchanged]
│
├── fixtures/                [add new fixture files]
│   ├── asx_futures_api_response.json   Minimal MarkitDigital API JSON
│   ├── rba_a2_data.csv                 Minimal RBA A2 CSV with metadata header rows
│   └── nab_article.html                Minimal NAB article HTML with capacity value
│
├── test_http_client.py      create_session: retry adapter, user-agent, custom UA
├── test_ingest_abs.py       fetch_abs_series, _parse_abs_date, fetch_and_save
├── test_ingest_rba.py       fetch_cash_rate, fetch_and_save
├── test_ingest_asx.py       _derive_probabilities, _find_meeting_for_contract,
│                             _get_current_cash_rate, scrape_asx_futures,
│                             _check_staleness, fetch_and_save
├── test_ingest_corelogic.py get_candidate_urls, extract_cotality_yoy (mock pdf),
│                             _current_month_already_scraped, fetch_and_save
├── test_ingest_nab.py       extract_capacity_from_html, get_pdf_link,
│                             extract_capacity_from_pdf (mock pdf),
│                             discover_latest_survey_url, _current_month_already_scraped,
│                             scrape_nab_capacity, backfill_nab_history, fetch_and_save
├── test_engine.py           build_gauge_entry, build_asx_futures_entry,
│                             process_indicator, generate_status, generate_interpretation
└── test_main.py             run_pipeline tier behavior (critical/important/optional),
                              result dict structure, sys.exit contracts
```

### Integration with Existing Infrastructure

All new test files plug directly into the existing conftest.py autouse fixtures:

- `isolate_data_dir` — already active for every test, patches `pipeline.config.DATA_DIR` to `tmp_path`. Scraper tests writing to `DATA_DIR / "output.csv"` automatically write to `tmp_path`.
- `block_network` — already active for every non-`@pytest.mark.live` test. All scraper tests must mock the HTTP layer; any accidental real call raises `RuntimeError("Network access blocked in tests.")`.
- Existing CSV fixture loaders — available for engine.py tests that need to populate `tmp_path` with realistic data.

No changes to `conftest.py` are required for ingest tests. One optional addition for engine tests is described below.

---

## Component Responsibilities

| New File | Module Under Test | Coverage Targets |
|----------|------------------|-----------------|
| `test_http_client.py` | `pipeline/utils/http_client.py` | `create_session`: retry count, backoff, status_forcelist, user-agent header, custom UA override |
| `test_ingest_abs.py` | `pipeline/ingest/abs_data.py` | `fetch_abs_series`: 200 response, HTTP error, empty response, short response, CSV parse error; `_parse_abs_date`: monthly, quarterly, passthrough; `fetch_and_save`: single series, all series |
| `test_ingest_rba.py` | `pipeline/ingest/rba_data.py` | `fetch_cash_rate`: header-row skipping, date parsing (dayfirst), range extraction; `fetch_and_save`: row count return |
| `test_ingest_asx.py` | `pipeline/ingest/asx_futures_scraper.py` | `_derive_probabilities`: cut/hold/hike branches, deadband; `_find_meeting_for_contract`: same-month, nearest-future, no match; `_get_current_cash_rate`: CSV present, CSV missing (fallback); `scrape_asx_futures`: JSON parse, empty items; `_check_staleness`: fresh, 14-day warn, 30-day error; `fetch_and_save`: success, empty df, exception |
| `test_ingest_corelogic.py` | `pipeline/ingest/corelogic_scraper.py` | `get_candidate_urls`: URL structure; `extract_cotality_yoy`: pattern found, not found; `_current_month_already_scraped`: not exists, empty, already scraped, prior month; `fetch_and_save`: success, no data, exception |
| `test_ingest_nab.py` | `pipeline/ingest/nab_scraper.py` | `extract_capacity_from_html`: found, not found, US spelling; `get_pdf_link`: found, not found; `extract_capacity_from_pdf`: pattern found, not found; `discover_latest_survey_url`: found, not found; `_current_month_already_scraped`; `fetch_and_save` |
| `test_engine.py` | `pipeline/normalize/engine.py` | `generate_interpretation`: all indicator/zone combos; `build_gauge_entry`: standard, housing enrichment, business_confidence enrichment; `build_asx_futures_entry`: data present, CSV missing; `process_indicator`: data present, data missing; `generate_status`: end-to-end with fixture CSVs |
| `test_main.py` | `pipeline/main.py` | `run_pipeline`: critical success, critical failure (sys.exit 1), important failure (continues), optional failure (continues), normalization success, normalization failure, result dict structure |

---

## Architectural Patterns

### Pattern 1: Mock at `create_session`, Not at the Socket

The `block_network` autouse fixture already blocks at the socket level. This means any real HTTP call fails loudly. For scraper unit tests, the HTTP layer must be mocked one level up: mock `create_session` to return a `MagicMock` session whose `.get()` returns a controlled `MagicMock` response.

**Patch target rule:** Patch the name where it is *used*, not where it is *defined*. Each scraper module does `from pipeline.utils.http_client import create_session`, binding the name in its own module namespace. Patch that bound name.

```python
# Correct — patches the name in the module that uses it
with patch("pipeline.ingest.abs_data.create_session") as mock_factory:
    ...

# Wrong — patches the source module; the scraper's bound name is unaffected
with patch("pipeline.utils.http_client.create_session") as mock_factory:
    ...
```

**Minimal mock response pattern:**
```python
from unittest.mock import MagicMock, patch

def _make_mock_session(status_code=200, text="", content=b"", json_data=None):
    """Helper: build a fake requests.Session.get response."""
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.text = text
    mock_response.content = content
    if json_data is not None:
        mock_response.json.return_value = json_data
    mock_response.headers = {"content-type": "application/json"}
    mock_response.raise_for_status.return_value = None

    mock_session = MagicMock()
    mock_session.get.return_value = mock_response

    return mock_session


def test_fetch_abs_series_success(tmp_path, monkeypatch):
    import pipeline.config
    monkeypatch.setattr(pipeline.config, "DATA_DIR", tmp_path)

    csv_text = "TIME_PERIOD,OBS_VALUE\n2024-01,120.5\n2024-02,121.0\n"
    mock_session = _make_mock_session(status_code=200, text=csv_text)

    with patch("pipeline.ingest.abs_data.create_session",
               return_value=mock_session):
        from pipeline.ingest.abs_data import fetch_abs_series
        df = fetch_abs_series("CPI", "all")

    assert len(df) == 2
    assert "date" in df.columns
    assert "value" in df.columns
```

### Pattern 2: Module-Level Mocking for Orchestration Tests

`main.py` imports entire modules (`rba_data`, `abs_data`, `corelogic_scraper`, `nab_scraper`) and calls `.fetch_and_save()` on them. Tests for `run_pipeline()` mock at the module level, not at `create_session`.

```python
# tests/python/test_main.py
from unittest.mock import MagicMock, patch
import pytest


def test_critical_failure_exits_1():
    """Critical source failure: run_pipeline calls sys.exit(1)."""
    with patch("pipeline.main.rba_data") as mock_rba, \
         patch("pipeline.main.abs_data"), \
         patch("sys.exit") as mock_exit:
        mock_rba.fetch_and_save.side_effect = Exception("RBA connection refused")
        from pipeline.main import run_pipeline
        # run_pipeline catches the exception and calls sys.exit(1)
        try:
            run_pipeline()
        except SystemExit:
            pass
        mock_exit.assert_called_once_with(1)


def test_optional_failure_continues():
    """Optional source failure: run_pipeline returns 'partial' status, not 'failed'."""
    with patch("pipeline.main.rba_data") as mock_rba, \
         patch("pipeline.main.abs_data") as mock_abs, \
         patch("pipeline.main.corelogic_scraper") as mock_core, \
         patch("pipeline.main.nab_scraper") as mock_nab, \
         patch("pipeline.normalize.engine.generate_status") as mock_gen:
        mock_rba.fetch_and_save.return_value = 100
        mock_abs.fetch_and_save.return_value = {"cpi": 50}
        mock_core.fetch_and_save.return_value = {"status": "failed", "error": "PDF 404"}
        mock_nab.fetch_and_save.return_value = {"status": "failed", "error": "no URL"}
        mock_gen.return_value = {"overall": {"hawk_score": 50.0, "zone_label": "Neutral"}}

        from pipeline.main import run_pipeline
        result = run_pipeline()

    assert result["status"] == "partial"
```

### Pattern 3: PDF Library Mocking Without Fixture PDFs

`corelogic_scraper.extract_cotality_yoy` and `nab_scraper.extract_capacity_from_pdf` both use `pdfplumber`. Creating a real binary PDF as a fixture is fragile. Instead, mock `pdfplumber.open` to return a context manager with controlled page text.

```python
# tests/python/test_ingest_corelogic.py
from unittest.mock import MagicMock, patch


def test_extract_cotality_yoy_pattern_found():
    """extract_cotality_yoy returns float when 'Australia X% X% X%' pattern found."""
    mock_page = MagicMock()
    mock_page.extract_text.return_value = (
        "Australia 0.8% 2.4% 9.4%\nSome other text\n"
    )
    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page]
    mock_pdf.__enter__ = lambda s: mock_pdf
    mock_pdf.__exit__ = MagicMock(return_value=False)

    with patch("pipeline.ingest.corelogic_scraper.pdfplumber.open",
               return_value=mock_pdf):
        from pipeline.ingest.corelogic_scraper import extract_cotality_yoy
        result = extract_cotality_yoy(b"fake_pdf_bytes")

    assert result == pytest.approx(9.4)


def test_extract_cotality_yoy_pattern_not_found():
    """extract_cotality_yoy returns None when pattern absent from all pages."""
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "No matching content here."
    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page]
    mock_pdf.__enter__ = lambda s: mock_pdf
    mock_pdf.__exit__ = MagicMock(return_value=False)

    with patch("pipeline.ingest.corelogic_scraper.pdfplumber.open",
               return_value=mock_pdf):
        from pipeline.ingest.corelogic_scraper import extract_cotality_yoy
        result = extract_cotality_yoy(b"fake_pdf_bytes")

    assert result is None
```

Note: `corelogic_scraper.py` does `import pdfplumber` inside the function body. The patch target is `pipeline.ingest.corelogic_scraper.pdfplumber` — this works because after the first call, the `pdfplumber` name exists in the module's namespace.

### Pattern 4: HTML Fixtures as Inline Bytes

NAB scraper helper functions (`extract_capacity_from_html`, `get_pdf_link`, `discover_latest_survey_url`) operate on HTML bytes. These are pure transformations — pass minimal HTML bytes inline rather than loading a fixture file.

```python
# tests/python/test_ingest_nab.py
import pytest
from pipeline.ingest.nab_scraper import (
    extract_capacity_from_html,
    get_pdf_link,
)

MINIMAL_NAB_HTML_WITH_CAPACITY = b"""
<html><body>
<article>
  <p>The NAB Monthly Business Survey for October 2025 showed
     capacity utilisation rose to 83.5% nationally.</p>
  <a href="https://business.nab.com.au/survey-oct-2025.pdf">Download PDF</a>
</article>
</body></html>
"""

MINIMAL_NAB_HTML_NO_CAPACITY = b"""
<html><body>
<article><p>No relevant capacity data in this page.</p></article>
</body></html>
"""


def test_extract_capacity_from_html_finds_value():
    result = extract_capacity_from_html(MINIMAL_NAB_HTML_WITH_CAPACITY)
    assert result == pytest.approx(83.5)


def test_extract_capacity_from_html_returns_none_when_absent():
    result = extract_capacity_from_html(MINIMAL_NAB_HTML_NO_CAPACITY)
    assert result is None


def test_get_pdf_link_finds_absolute_url():
    result = get_pdf_link(MINIMAL_NAB_HTML_WITH_CAPACITY)
    assert result == "https://business.nab.com.au/survey-oct-2025.pdf"


def test_get_pdf_link_returns_none_when_no_pdf():
    result = get_pdf_link(MINIMAL_NAB_HTML_NO_CAPACITY)
    assert result is None
```

### Pattern 5: Engine Tests with Fixture CSV Wiring

`generate_status()` reads from `DATA_DIR` (patched to `tmp_path`) and writes to `STATUS_OUTPUT` (NOT patched by autouse — requires explicit patching). Copy fixture CSVs and the real `weights.json` into `tmp_path`.

```python
# tests/python/test_engine.py
import json
import shutil
from pathlib import Path
import pytest
import pipeline.config

FIXTURES_DIR = Path(__file__).parent / "fixtures"
WEIGHTS_FILE = Path("data/weights.json")  # real file, committed to repo


@pytest.fixture
def engine_data_dir(tmp_path, monkeypatch):
    """
    Populate tmp_path with all fixture CSVs and weights.json.
    Patch STATUS_OUTPUT to tmp_path so generate_status() doesn't
    write to the real public/data/status.json.
    """
    # Copy all fixture CSVs
    for csv_file in FIXTURES_DIR.glob("*.csv"):
        shutil.copy(csv_file, tmp_path / csv_file.name)

    # Copy real weights.json (contains indicator weights — required by engine)
    if WEIGHTS_FILE.exists():
        shutil.copy(WEIGHTS_FILE, tmp_path / "weights.json")

    # Patch DATA_DIR (redundant with autouse but explicit is clearer)
    monkeypatch.setattr(pipeline.config, "DATA_DIR", tmp_path)

    # CRITICAL: patch STATUS_OUTPUT — not covered by isolate_data_dir autouse
    monkeypatch.setattr(pipeline.config, "STATUS_OUTPUT", tmp_path / "status.json")

    return tmp_path


def test_generate_status_produces_valid_output(engine_data_dir):
    """generate_status writes status.json with correct top-level structure."""
    from pipeline.normalize.engine import generate_status

    result = generate_status()

    assert "overall" in result
    assert "gauges" in result
    assert "metadata" in result
    assert 0 <= result["overall"]["hawk_score"] <= 100
    assert result["overall"]["zone"] in ("cold", "cool", "neutral", "warm", "hot")

    # Verify the output file was actually written
    status_file = engine_data_dir / "status.json"
    assert status_file.exists()
    written = json.loads(status_file.read_text())
    assert written["overall"]["hawk_score"] == result["overall"]["hawk_score"]
```

### Pattern 6: Pure Function Tests Need No Mocking

`_parse_abs_date`, `_derive_probabilities`, `_find_meeting_for_contract`, `get_candidate_urls`, `generate_interpretation`, `build_asx_futures_entry` — these are pure transformations. Test them directly with constructed inputs; no patching required.

```python
# tests/python/test_ingest_abs.py
import pytest
from pipeline.ingest.abs_data import _parse_abs_date


@pytest.mark.parametrize("input_str,expected", [
    ("2024-01", "2024-01-01"),     # Monthly
    ("2024-Q1", "2024-01-01"),     # Quarterly Q1
    ("2024-Q2", "2024-04-01"),     # Quarterly Q2
    ("2024-Q3", "2024-07-01"),     # Quarterly Q3
    ("2024-Q4", "2024-10-01"),     # Quarterly Q4
])
def test_parse_abs_date(input_str, expected):
    assert _parse_abs_date(input_str) == expected


# tests/python/test_ingest_asx.py
from pipeline.ingest.asx_futures_scraper import _derive_probabilities


@pytest.mark.parametrize("implied,current,expected_direction", [
    (3.60, 3.85, "cut"),    # 25bp cut: change_bp = -25
    (3.85, 3.85, "hold"),   # No move: change_bp = 0 (within deadband)
    (3.87, 3.85, "hold"),   # 2bp: within deadband
    (4.10, 3.85, "hike"),   # 25bp hike: change_bp = +25
])
def test_derive_probabilities_direction(implied, current, expected_direction):
    change_bp, prob_cut, prob_hold, prob_hike = _derive_probabilities(implied, current)
    if expected_direction == "cut":
        assert prob_cut > 0
        assert prob_hike == 0
    elif expected_direction == "hold":
        assert prob_hold == 100
        assert prob_cut == 0
        assert prob_hike == 0
    else:  # hike
        assert prob_hike > 0
        assert prob_cut == 0
    assert prob_cut + prob_hold + prob_hike == 100
```

---

## Data Flow

### Mock Data Flow for Ingest Tests

```
test calls fetch_and_save()
    │
    ▼
fetch_and_save() calls scrape_X() / fetch_X()
    │
    ▼
scrape_X() calls create_session()
    │
    ▼  [MOCKED — patch("pipeline.ingest.X.create_session") returns fake_session]
fake_session.get(url) returns MagicMock response
    │   .status_code = 200
    │   .text = "<controlled CSV/HTML>"
    │   .content = b"<controlled bytes>"
    │   .json() = {"data": {"items": [...]}}
    ▼
Scraper parses response → builds DataFrame
    │
    ▼
append_to_csv(tmp_path / "output.csv", df)  [REAL — writes to isolated tmp_path]
    │
    ▼
Test asserts:
    - return dict: {"status": "success", "rows": N}
    - CSV file exists at tmp_path / "output.csv"
    - CSV has expected columns and row count
```

### Isolation Guarantee Layers

```
Layer 1: Socket level
    block_network autouse — any real socket.socket() call raises RuntimeError
    Applied to: ALL tests without @pytest.mark.live

Layer 2: HTTP session level
    patch("pipeline.ingest.X.create_session") in each ingest test
    Controls: what session.get(url) returns for each specific test

Layer 3: Data directory level
    isolate_data_dir autouse — pipeline.config.DATA_DIR = tmp_path
    Applied to: ALL tests — scraper writes go to tmp_path, never data/

Layer 4: Status output level (engine tests only)
    Must patch pipeline.config.STATUS_OUTPUT explicitly
    NOT covered by isolate_data_dir — computed at import time from public/data/
    Applied to: test_engine.py only
```

### Key Return Contracts by Module

| Module | `fetch_and_save` return type | Success contract | Failure contract |
|--------|------------------------------|-----------------|-----------------|
| `rba_data` | `int` | Row count > 0 | Raises exception (critical) |
| `abs_data` | `dict[str, int]` | `{"cpi": 50, ...}` | Row count = 0 per series |
| `asx_futures_scraper` | `dict` | `{"status": "success", "rows": N, "meetings": M}` | `{"status": "failed", "error": "..."}` |
| `corelogic_scraper` | `dict` | `{"status": "success", "rows": N}` | `{"status": "failed", "error": "..."}` |
| `nab_scraper` | `dict` | `{"status": "success", "rows": N}` | `{"status": "failed", "error": "..."}` |

Tests must assert on the full return contract, not just the presence of a `status` key.

---

## Build Order

Build new test files in this sequence. Each step builds on patterns established by prior steps.

**Step 1: `test_http_client.py`**
- Zero dependencies on mocking or pipeline modules.
- Call `create_session()` with various args; inspect the returned session object.
- Assert: `session.adapters["https://"].max_retries.total == 3`
- Assert: `session.headers["User-Agent"]` matches expected string.
- Establishes pattern: inspecting real objects, not mocking them.

**Step 2: `test_ingest_abs.py`**
- First use of `patch("pipeline.ingest.abs_data.create_session")`.
- Establishes the `_make_mock_session` helper pattern.
- Start with pure functions: `_parse_abs_date` (parametrized, no mocking).
- Then `fetch_abs_series` happy path (200 response, CSV with right columns).
- Then error paths (non-200 status, empty text, short text, parse error).
- Then `fetch_and_save` single series and all series.

**Step 3: `test_ingest_rba.py`**
- Similar pattern to ABS. Key difference: RBA CSV has metadata header rows that must be skipped.
- Use a realistic fixture `rba_a2_data.csv` with 3-4 header rows before `Series ID` row.
- Test `fetch_cash_rate` with mock response using this fixture content.
- Test range extraction (`"17.00 to 17.50"` → `17.50`).

**Step 4: `test_ingest_asx.py`**
- Start with pure functions: `_derive_probabilities` (parametrized, no mocking).
- Then `_find_meeting_for_contract` (pure, just date logic).
- Then `_get_current_cash_rate` (reads from `tmp_path / "rba_cash_rate.csv"` — use `isolate_data_dir` + write a CSV to `tmp_path`).
- Then `scrape_asx_futures` with mocked JSON API response.
- Then `_check_staleness` with a CSV written to `tmp_path`.
- Then `fetch_and_save` success, empty df, exception paths.

**Step 5: `test_ingest_corelogic.py`**
- Start with pure functions: `get_candidate_urls` (no mocking — just asserts URL structure).
- Then `extract_cotality_yoy` using PDF mocking pattern (Pattern 3 above).
- Then `_current_month_already_scraped` with various CSV states in `tmp_path`.
- Then `fetch_and_save` with mock session + mock PDF.

**Step 6: `test_ingest_nab.py`**
- Start with pure functions from inline HTML bytes: `extract_capacity_from_html`, `get_pdf_link` (Pattern 4 above).
- Then `extract_capacity_from_pdf` using PDF mocking pattern.
- Then `_current_month_already_scraped`.
- Then `discover_latest_survey_url` with mocked session returning HTML that contains survey URL.
- Then `fetch_and_save` and `backfill_nab_history`.
- Most complex module — build last among ingest tests.

**Step 7: `test_engine.py`**
- Add `engine_data_dir` fixture to conftest.py or keep it local to this file.
- Start with pure functions: `generate_interpretation` (all 8 indicator × 5 zone combos — no data needed).
- Then `build_asx_futures_entry` with a minimal `asx_futures.csv` in `tmp_path`.
- Then `build_gauge_entry` with synthetic z-score DataFrame.
- Then `process_indicator` with fixture CSVs in `tmp_path`.
- Then `generate_status` end-to-end (requires `engine_data_dir` fixture with all CSVs + weights.json).

**Step 8: `test_main.py`**
- Build last — depends on understanding all scraper return contracts.
- Mock entire ingest modules at `pipeline.main.*` level.
- Test tier behavior: critical failure → sys.exit(1), important failure → continues, optional failure → "partial" status.
- Test normalization success and failure paths.
- Test result dict structure for all outcomes.

---

## Integration Points

### New Files Required

| File | Type | Why Needed |
|------|------|-----------|
| `tests/python/test_http_client.py` | New test | Zero existing coverage on `create_session` |
| `tests/python/test_ingest_abs.py` | New test | No unit tests for ABS ingest module |
| `tests/python/test_ingest_rba.py` | New test | No unit tests for RBA ingest module |
| `tests/python/test_ingest_asx.py` | New test | No unit tests for ASX scraper |
| `tests/python/test_ingest_corelogic.py` | New test | No unit tests for CoreLogic scraper |
| `tests/python/test_ingest_nab.py` | New test | No unit tests for NAB scraper |
| `tests/python/test_engine.py` | New test | No unit tests for normalization engine |
| `tests/python/test_main.py` | New test | No unit tests for pipeline orchestrator |
| `tests/python/fixtures/asx_futures_api_response.json` | New fixture | Provides controlled MarkitDigital API response |
| `tests/python/fixtures/rba_a2_data.csv` | New fixture | Provides RBA A2 CSV with metadata header rows |
| `tests/python/fixtures/nab_article.html` | New fixture (optional) | Alternative to inline HTML for complex NAB tests |

### Files Modified

| File | Change | Reason |
|------|--------|--------|
| `tests/python/conftest.py` | Add `engine_data_dir` fixture (optional) | Shared setup for engine tests; can stay local if not reused |
| No other existing files | None | The existing autouse infrastructure handles all new tests |

### Existing Files Unchanged

All existing test files (`test_smoke.py`, `test_zscore.py`, `test_gauge.py`, `test_ratios.py`, `test_csv_handler.py`, `test_schema.py`, `test_live_sources.py`) remain unchanged. No existing fixture CSVs need modification.

---

## Critical Isolation Gaps

### Gap 1: STATUS_OUTPUT Not Isolated by Autouse

`pipeline.config.STATUS_OUTPUT = Path("public") / "data" / "status.json"` is assigned at import time. The `isolate_data_dir` autouse fixture patches `DATA_DIR` but not `STATUS_OUTPUT`. Any test that calls `generate_status()` will write to the real `public/data/status.json` unless explicitly patched.

**Required fix in `test_engine.py`:**
```python
monkeypatch.setattr(pipeline.config, "STATUS_OUTPUT", tmp_path / "status.json")
```

This can be encapsulated in an `engine_data_dir` fixture to avoid repetition.

### Gap 2: SOURCE_METADATA Paths Are Import-Time Bound

`pipeline.config.SOURCE_METADATA` values contain `Path` objects computed from the original `DATA_DIR` value at import time. If any module reads `SOURCE_METADATA["RBA"]["file_path"]`, it will point to the original `data/` directory, not `tmp_path`. The conftest.py already documents this. For ingest tests, this is not an issue — scrapers read from `pipeline.config.DATA_DIR` at call time (late binding), not from SOURCE_METADATA.

### Gap 3: `_get_rba_meeting_dates` Reads from `public/data/meetings.json`

`asx_futures_scraper._get_rba_meeting_dates()` opens `Path("public/data/meetings.json")` — a hardcoded relative path, not through `DATA_DIR`. Tests for `scrape_asx_futures()` must either:
- Ensure CWD is the project root when running pytest (already true: `pyproject.toml` at root, `testpaths = ["tests/python"]`), or
- Patch `_get_rba_meeting_dates` to return a fixed list of meeting dates.

The simpler approach is to patch the function since the test is about the futures scraping logic, not the meeting date loading:
```python
with patch("pipeline.ingest.asx_futures_scraper._get_rba_meeting_dates",
           return_value=["2025-04-01", "2025-05-06"]):
    ...
```

---

## Anti-Patterns

### Anti-Pattern 1: Patching at the Wrong Module Level

**What people do:** `patch("pipeline.utils.http_client.create_session")` in scraper tests.
**Why it's wrong:** Scrapers imported `create_session` at module load time via `from pipeline.utils.http_client import create_session`. The name is now bound in the scraper module. Patching the source has no effect.
**Do this instead:** `patch("pipeline.ingest.abs_data.create_session")` — patch the binding in the consuming module.

### Anti-Pattern 2: Forgetting to Patch STATUS_OUTPUT in Engine Tests

**What people do:** Call `generate_status()` in a test that uses `isolate_data_dir`, assuming all file I/O is isolated.
**Why it's wrong:** `STATUS_OUTPUT` points to `public/data/status.json` — outside `DATA_DIR`. The autouse fixture does not patch it.
**Do this instead:** Always add `monkeypatch.setattr(pipeline.config, "STATUS_OUTPUT", tmp_path / "status.json")` in engine tests. Or use an `engine_data_dir` fixture that does this.

### Anti-Pattern 3: Using Binary PDF Fixtures

**What people do:** Generate or download a real `.pdf` file, add it to `tests/python/fixtures/`, pass it to `extract_cotality_yoy`.
**Why it's wrong:** Real PDFs are binary, opaque, platform-sensitive, and fragile. The regex extraction logic is what needs testing, not pdfplumber itself.
**Do this instead:** Mock `pdfplumber.open` to return a controlled context manager. The test controls exactly what `page.extract_text()` returns.

### Anti-Pattern 4: Testing Only the Return Value of `fetch_and_save`

**What people do:** `assert result["status"] == "success"` — only checks the return dict.
**Why it's wrong:** The side effect (writing a CSV) is equally important. A scraper that returns `{"status": "success"}` but writes no file would pass the test.
**Do this instead:** Also assert the CSV file exists in `tmp_path` with the expected content.
```python
assert result["status"] == "success"
output_file = tmp_path / "asx_futures.csv"
assert output_file.exists()
df = pd.read_csv(output_file)
assert len(df) > 0
```

### Anti-Pattern 5: Mocking Too Deep in Engine Tests

**What people do:** Mock `normalize_indicator`, `compute_rolling_zscores`, `compute_hawk_score` inside engine tests to avoid needing real data.
**Why it's wrong:** These are fast pure functions that are already tested in `test_ratios.py` and `test_zscore.py`. Mocking them adds test complexity without adding confidence.
**Do this instead:** Wire up the real fixture CSVs and let the full stack run. Engine tests should verify the integration (does the right data flow through?), not re-mock the logic already tested elsewhere.

---

## Sources

- Direct inspection of `/Users/annon/projects/rba-hawko-meter/pipeline/` source files (all modules read)
- Direct inspection of `/Users/annon/projects/rba-hawko-meter/tests/python/` (all test files read)
- `pyproject.toml` — pytest configuration (`testpaths`, `pythonpath`, `markers`, `--strict-markers`)
- `tests/python/conftest.py` — autouse fixture implementation and documented gaps
- `.planning/PROJECT.md` — v3.0 milestone goals and key decisions

---

*Architecture research for: v3.0 test coverage expansion — scraper mocking, orchestration testing*
*Researched: 2026-02-25*
