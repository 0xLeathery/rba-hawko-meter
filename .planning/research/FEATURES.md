# Feature Research

**Domain:** Unit test coverage for Python I/O-heavy scraper/ingest/orchestration modules
**Researched:** 2026-02-25
**Confidence:** HIGH (derived from direct codebase analysis, verified against pytest/unittest.mock official docs)

---

## Context: What This Milestone Is Adding

v2.0 shipped the test *foundation*: pyproject.toml, conftest autouse fixtures (DATA_DIR isolation +
socket-level network blocking), pytest markers, fixture CSVs from production snapshots, and 118 unit
tests covering the pure-math core (zscore, gauge, ratios, csv_handler, config) at 96-100%.

v3.0 adds **coverage for the I/O-heavy layer** — the modules that call the network, parse HTTP
responses, scrape HTML/PDFs, and orchestrate the full pipeline. These modules are currently at 0-42%
because they were not touched in v2.0.

**Current coverage gaps (from milestone context):**

| Module | Current % | Gap |
|--------|-----------|-----|
| `pipeline/main.py` | 0% | Full orchestration logic untested |
| `pipeline/normalize/engine.py` | 0% | Status.json generation untested |
| `pipeline/ingest/abs_data.py` | 17% | Only `_parse_abs_date` partially covered |
| `pipeline/ingest/rba_data.py` | 24% | Fetch/parse logic untested |
| `pipeline/ingest/asx_futures_scraper.py` | 13% | Most scraper logic untested |
| `pipeline/ingest/corelogic_scraper.py` | 19% | PDF scraper logic untested |
| `pipeline/ingest/nab_scraper.py` | 14% | HTML/PDF extraction untested |
| `pipeline/utils/http_client.py` | 42% | Session config partially covered |
| `pipeline/normalize/ratios.py` | 68% | `load_asx_futures_csv`, hybrid paths uncovered |
| `pipeline/normalize/gauge.py` | 81% | `load_weights`, `generate_verdict` edge cases |

**What already exists (do not rebuild):**
- `conftest.py`: `isolate_data_dir` (autouse, monkeypatches `pipeline.config.DATA_DIR` to `tmp_path`),
  `block_network` (autouse, replaces `socket.socket` with a `RuntimeError` raiser; exempt via `@pytest.mark.live`)
- Named CSV fixture loaders for all 6 ABS/CoreLogic/NAB fixture CSVs
- `@pytest.mark.live` registered and working for opt-in network tests
- 118 passing unit tests for math core

---

## Feature Landscape

### Table Stakes (Teams Expect These When Reaching 85% Coverage on I/O Modules)

These are the testing patterns that are non-negotiable for covering network/file I/O modules.
Missing any of these means the 85% target is structurally unreachable for at least one module.

#### 1. Response Object Mocking for `requests.Session`

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **`MagicMock` response objects with `.status_code`, `.text`, `.content`, `.json()`** | Every ingest module calls `session.get(url, ...)`. Without a mock response, all paths through the HTTP call are dead to tests — 0% coverage on the most important branches. | LOW | `unittest.mock.MagicMock()` with `.status_code = 200`, `.text = "..."`, `.json.return_value = {...}`. This covers happy path. Requires patching the session returned by `create_session()`. |
| **Patching `create_session` at the call site (not at `requests` layer)** | The existing `block_network` fixture blocks at `socket.socket` level. Unit tests that mock `create_session` bypass the socket entirely — the mock session's `.get()` returns a fake response without touching the network. | LOW | Use `monkeypatch.setattr("pipeline.ingest.abs_data.create_session", lambda **kw: mock_session)` in test. The critical pattern: patch the name *in the module under test*, not in `pipeline.utils.http_client`. Import-path targeting is the most common mock pitfall. |
| **Error path mocking (4xx/5xx, `requests.exceptions.Timeout`, `ConnectionError`)** | `abs_data.py`, `rba_data.py`, `asx_futures_scraper.py` all have explicit exception handlers. These branches are only reachable by making the mock raise or return a non-200 status code. Without them, coverage on exception handlers stays at 0%. | LOW | `mock_session.get.side_effect = requests.exceptions.Timeout()` for timeout paths. `mock_response.status_code = 500` + `mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()` for 5xx paths. Each exception type in the handler needs its own test. |
| **`raise_for_status` mock** | `rba_data.fetch_cash_rate()` calls `response.raise_for_status()`. A mock that does nothing by default means the no-error path is tested, but the raise path is not. | LOW | `mock_response.raise_for_status = MagicMock()` (does nothing) for happy path. `mock_response.raise_for_status.side_effect = HTTPError("404")` for error path test. |

#### 2. CSV Response Body Fixtures for ABS/RBA Parsing

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Minimal CSV strings that match real ABS SDMX response format** | `abs_data.fetch_abs_series()` parses `response.text` as a pandas CSV. Without a realistic response body, the column-detection logic (`TIME_PERIOD`, `OBS_VALUE`, filter columns) cannot be exercised. | LOW | Create inline string constants in the test file matching the ABS SDMX CSV format: `"TIME_PERIOD,OBS_VALUE,MEASURE: CPI\n2023-Q1,126.1,1\n"`. Do not use real production CSVs as inline strings — synthetic minimal ones suffice. |
| **RBA CSV format string (metadata rows + data)** | `rba_data.fetch_cash_rate()` uses `skiprows` to skip metadata lines before the `Series ID` header row. The test CSV string must include those metadata rows or the row-detection loop produces wrong results. | LOW | Inline test string: `"Title Description Row\nSeries ID,Description,New Cash Rate Target\n01-Feb-2023,,4.35\n"`. Verifying the `skiprows` logic requires the header search to find `Series ID` at a non-zero row. |
| **Filter-path CSV strings (ABS indicator-specific columns)** | `fetch_abs_series()` applies `filters` dict to narrow multi-dimensional ABS data. This path (lines 95-111 of `abs_data.py`) is 0% covered. Needs a CSV with a column like `"MEASURE: CPI Monthly"` to trigger the filter logic. | MEDIUM | Filter logic test: construct a CSV with two measure types, apply `filters={"MEASURE": "1"}`, assert only matching rows are returned. Tests both the column-matching regex and the row-filtering step. |

#### 3. HTML/PDF Parsing Tests (No Network, Byte-Level Fixtures)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Inline HTML bytes fixtures for NAB scraper** | `extract_capacity_from_html()` and `get_pdf_link()` in `nab_scraper.py` take raw `bytes`. Tests can pass synthetic HTML bytes without any mocking at all — no session, no requests. These functions are pure HTML parsing. | LOW | `html = b"<p>Capacity utilisation was 82.1%</p>"` → call `extract_capacity_from_html(html)` → assert `82.1`. Also test the "utilization" US spelling variant via the regex. Test missing pattern → assert `None`. |
| **Inline PDF bytes via real minimal PDF OR patching pdfplumber** | `extract_capacity_from_pdf()` and `extract_cotality_yoy()` require actual PDF bytes (pdfplumber opens them). Generating real PDF bytes in tests is heavyweight. Patching pdfplumber is simpler. | MEDIUM | Two approaches: (a) `monkeypatch.setattr("pdfplumber.open", ...)` returning a mock PDF object with mock pages and `.extract_text()` returning a fixture string — works for coverage. (b) A pre-built minimal test PDF checked into `tests/python/fixtures/` — more realistic but adds a binary file. Approach (a) is strongly preferred: keeps tests fast, avoids binary fixtures. |
| **Idempotency check tests for NAB and CoreLogic scrapers** | `_current_month_already_scraped()` in both scrapers is pure file I/O on `tmp_path` CSV. The `isolate_data_dir` autouse fixture means `DATA_DIR` already points to `tmp_path` — just write a fixture CSV there before calling the function. | LOW | Write a CSV with current-month date to `tmp_path / "nab_capacity.csv"`, call `_current_month_already_scraped(path)`, assert `True`. Write a CSV with last-month date, assert `False`. Write nothing, assert `False`. Three tests, zero mocking needed. |

#### 4. Orchestration Testing (main.py and engine.py)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Mock all ingest modules to test orchestration logic in `main.py`** | `run_pipeline()` imports and calls `rba_data`, `abs_data`, `corelogic_scraper`, `nab_scraper`. Testing it requires all four to be mocked so the orchestration logic (tier handling, exit code, partial success) can be exercised without any real I/O. | MEDIUM | `monkeypatch.setattr("pipeline.main.rba_data.fetch_and_save", lambda: 50)` for the module-level mocking pattern. Critical: patch the name in `pipeline.main`, not in the source module. Mock all three tiers independently to test critical-fail vs partial scenarios. |
| **`sys.exit` testing with `pytest.raises(SystemExit)`** | `run_pipeline()` calls `sys.exit(1)` on critical source failure. This is a real `SystemExit` that will terminate the test process if not caught. Must use `pytest.raises(SystemExit)` context manager to intercept it. | LOW | `with pytest.raises(SystemExit) as exc_info: run_pipeline()` → `assert exc_info.value.code == 1`. This is the only safe way to test code paths that call `sys.exit`. The `monkeypatch.setattr(sys, "exit", lambda code: ...)` alternative is fragile and harder to reason about. |
| **engine.py: mock `normalize_indicator` and `compute_rolling_zscores` to test JSON assembly** | `generate_status()` in `engine.py` calls `process_indicator()` for each indicator, then assembles the status dict, computes hawk score, and writes JSON. Mocking `normalize_indicator` to return a fixture DataFrame lets the assembly logic be tested without the full data stack. | MEDIUM | Patch `pipeline.normalize.engine.normalize_indicator` to return a synthetic DataFrame with known z-scores. Assert the output status dict has correct structure: `overall.hawk_score` in [0, 100], `gauges` keyed by indicator names, `metadata.indicators_available` count matches. |
| **`build_gauge_entry` direct unit testing** | `build_gauge_entry()` takes a `latest_row` Series and `z_df` DataFrame. It can be called directly with synthetic inputs — no mocking needed. Tests `apply_polarity`, `zscore_to_gauge`, `classify_zone`, `determine_confidence`, `generate_interpretation` integration. | LOW | Create a minimal `pd.Series` and `pd.DataFrame` with known values, call `build_gauge_entry()`, assert all expected keys exist in the output dict with correct types. This alone covers a large portion of `engine.py`. |
| **`build_asx_futures_entry` with tmp_path CSV** | `build_asx_futures_entry()` reads `asx_futures.csv` from `DATA_DIR`. Since `isolate_data_dir` patches `DATA_DIR` to `tmp_path`, writing a fixture CSV there and calling the function exercises the full code path. | LOW | Write a minimal `asx_futures.csv` to `tmp_path`, call `build_asx_futures_entry()`, assert `direction`, `probabilities`, `meetings` keys. Write nothing, assert return is `None`. |

#### 5. http_client.py Coverage to 85%+

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Verify `create_session` returns a `requests.Session` with correct adapter config** | `http_client.py` is 42% covered. The untested paths are: non-default `retries`/`backoff_factor` parameters and custom `user_agent`. These are reachable through direct calls with different args. | LOW | Call `create_session(retries=5, backoff_factor=1.0, user_agent="TestBot/1.0")`. Assert the session's headers contain the custom user agent. The retry adapter configuration lives inside the `HTTPAdapter` — asserting `session.get_adapter("https://").max_retries.total == 5` validates the retry was applied. No mocking needed. |
| **Session mounting on both http:// and https://**  | The `session.mount("http://", adapter)` and `session.mount("https://", adapter)` lines are in the function. Test by inspecting `session.get_adapter("http://example.com")` and `session.get_adapter("https://example.com")` — both should return the configured `HTTPAdapter`. | LOW | Direct assertion after `create_session()` call. No mocking needed. This is pure function-output testing. |

---

### Differentiators (Valuable But Not Required for 85%)

Features that improve test quality beyond the coverage number.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Parametrized tests for `_parse_abs_date`** | `abs_data._parse_abs_date()` has three code paths: quarterly (`2024-Q1`), monthly (`2024-01`), and generic ISO fallback. Parametrizing covers all three with one test function. | LOW | `@pytest.mark.parametrize("input,expected", [("2024-Q1", "2024-01-01"), ("2024-01", "2024-01-01"), ("2024-01-15", "2024-01-15")])`. Currently at 0% — covers a self-contained function with no I/O. |
| **Parametrized tests for `_derive_probabilities`** | `asx_futures_scraper._derive_probabilities()` has three branches: cut (change_bp < -5), hike (change_bp > 5), hold (within deadband). Pure math with no I/O. | LOW | Same parametrize pattern. Tests the probability capping logic (`min(100, ...)`) at boundary values too. Covers one of the most decision-logic-dense functions in the scraper. |
| **`discover_latest_survey_url` with mock BeautifulSoup responses** | The NAB tag-archive discovery loop tries multiple URLs. Testing it with a mock session that returns synthetic HTML confirms the `href` matching logic and the fallback to the second archive URL. | MEDIUM | Mock session with `.get()` returning different responses for each archive URL. Test: first URL returns HTML with a matching href → assert result URL. First URL 404s, second URL has matching href → assert fallback worked. Both fail → assert `None`. |
| **`get_candidate_urls` direct unit tests (no mocking)** | `corelogic_scraper.get_candidate_urls(year, month)` is a pure function that builds URL strings. 0% covered currently. Four URL patterns are generated. Direct call with known inputs is enough. | LOW | `urls = get_candidate_urls(2026, 2)`. Assert `len(urls) == 4`. Assert expected substrings appear in each URL (e.g., `"Feb"`, `"2026"`, `"FINAL"`). No mocking. Covers URL construction logic completely. |
| **`_find_meeting_for_contract` direct unit tests** | `asx_futures_scraper._find_meeting_for_contract()` is pure logic: same-month match, nearest-future fallback, no match. No I/O. | LOW | Call directly with synthetic `contract_expiry` dates and `meeting_dates` lists. Three parametrized scenarios: same month, future fallback, no match (returns `None`). |
| **`_get_current_cash_rate` with tmp_path CSV** | Reads `rba_cash_rate.csv` from `DATA_DIR`. The `isolate_data_dir` fixture makes this a simple write-to-tmp-path test. Also test the fallback (no CSV → returns 4.35). | LOW | Write a CSV with a known rate to `tmp_path / "rba_cash_rate.csv"`, call `_get_current_cash_rate()`, assert return value. Delete the file, call again, assert `4.35` fallback. |
| **`generate_interpretation` parametrized across all indicators and zones** | `engine.generate_interpretation()` has a static template dict. Pure function, no I/O. 35 combinations (7 indicators × 5 zones) can be parametrized. | LOW | One parametrized test covers the whole function. Tests the unknown-indicator fallback too. Zero mocking. Very high coverage return for a short test. |

---

### Anti-Features (Commonly Requested, Will Not Help Here)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| **VCR.py / responses library cassette recording** | Record real HTTP interactions once, replay without network | Cassettes recorded against the ABS SDMX, MarkitDigital, and NAB/Cotality endpoints go stale when URL formats or response shapes change (they have changed multiple times in this codebase's history). A stale cassette passes tests against an outdated API contract. | Use `unittest.mock.MagicMock` with inline fixture strings. Less realistic but never stale. Reserve `@pytest.mark.live` for actual contract verification. |
| **Full integration tests that run the real pipeline end-to-end** | Would test the system as a whole, not just units | `run_pipeline()` calls all ingestors which call the network. An integration test that runs the full pipeline requires network access, takes 30+ seconds, and fails non-deterministically on CI when external endpoints are down. The `@pytest.mark.live` live test suite already covers this. | Mock all ingestors in `main.py` unit tests to test orchestration logic. Run live tests manually with `pytest -m live` when endpoint contracts need verification. |
| **Generating real PDF bytes for pdfplumber tests** | More realistic than mocking pdfplumber | Requires a PDF generation library (reportlab or fpdf2) as a test-only dependency, adds binary fixture files to the repo, and creates fragile tests that break when pdfplumber changes its internal API. The actual PDF-to-text extraction is pdfplumber's responsibility, not ours. | Patch `pdfplumber.open()` to return a mock object whose pages have `.extract_text()` returning a fixture string. Tests our regex logic without testing pdfplumber's PDF parser. |
| **Achieving 100% coverage on `main.py`** | Completeness | The `if __name__ == '__main__':` block at the bottom of `main.py` (and other modules) is unreachable from pytest. Reaching 100% requires either removing the guard or using subprocess. This is not worth the effort. | Accept ~90-95% as the realistic ceiling for modules with `__main__` guards. The 85% milestone target accounts for this. |
| **Mocking `datetime.now()` globally** | Some tests need deterministic dates | Patching `datetime.datetime.now` globally breaks other tests that legitimately need current time. Partial patching via `monkeypatch.setattr("pipeline.ingest.nab_scraper.datetime", ...)` is fragile because `datetime` is a C extension. | For idempotency tests that compare to "current month", write the test CSV with a date matching the *actual* current month (use `datetime.now()` in the test setup too). For tests that need a specific known date, use `monkeypatch.setattr` scoped to the specific test. |
| **pytest-cov coverage gates in pre-push hook** | Enforce minimum coverage before every push | Coverage measurement adds 2-3 seconds to every test run. The pre-push hook must complete in <10s. Coverage is valuable to measure in CI, not in the hot path of every developer commit. | Run coverage manually: `pytest --cov=pipeline --cov-report=term-missing`. Add to a separate `npm run coverage` script. Do not put it in the pre-push hook. |

---

## Feature Dependencies

```
[Existing v2.0 infrastructure]
    └──provides──> [isolate_data_dir autouse fixture]
                       └──required by──> [all tmp_path-based tests for file-reading functions]
                       └──required by──> [build_asx_futures_entry tests]
                       └──required by──> [_get_current_cash_rate tests]
                       └──required by──> [_current_month_already_scraped tests]
    └──provides──> [block_network autouse fixture]
                       └──required by: ensures mock-based tests do not accidentally hit network]
    └──provides──> [@pytest.mark.live marker]
                       └──exempts live tests from block_network]
    └──provides──> [named CSV fixture loaders]
                       └──not directly needed for v3.0 (new tests use inline synthetic data)]

[unittest.mock.MagicMock session pattern]
    └──required by──> [abs_data fetch tests]
    └──required by──> [rba_data fetch tests]
    └──required by──> [asx_futures_scraper scrape tests]
    └──required by──> [corelogic_scraper download tests]
    └──required by──> [nab_scraper discover/fetch tests]
    └──enables──> [response body fixture strings for CSV parsing tests]

[Inline HTML bytes fixtures]
    └──no dependencies (pure bytes passed to parsing functions)]
    └──required by──> [extract_capacity_from_html tests]
    └──required by──> [get_pdf_link tests]

[pdfplumber mock pattern]
    └──requires──> [monkeypatch on pdfplumber.open]
    └──required by──> [extract_capacity_from_pdf tests]
    └──required by──> [extract_cotality_yoy tests]

[engine.py build_gauge_entry direct tests]
    └──requires──> [synthetic pd.Series / pd.DataFrame inputs — no mocking]
    └──enables partial coverage without needing full normalize pipeline]

[engine.py generate_status mock pattern]
    └──requires──> [normalize_indicator patched to return fixture DataFrame]
    └──requires──> [load_weights patched OR real weights.json accessible from tests]
    └──required by──> [full generate_status JSON assembly tests]

[main.py orchestration tests]
    └──requires──> [all ingest modules patched in pipeline.main namespace]
    └──requires──> [pytest.raises(SystemExit) for sys.exit(1) testing]
    └──independent of engine.py tests — can be written in parallel]

[http_client.py tests]
    └──no mocking dependencies — direct session inspection]
    └──independent: write first or last, no ordering constraint]

[Pure-function tests: _parse_abs_date, _derive_probabilities, get_candidate_urls,
 _find_meeting_for_contract, generate_interpretation, _check_staleness]
    └──no dependencies (pure logic, no I/O, no mocking needed)]
    └──highest coverage return per line of test code: write these first]
```

### Dependency Notes

- **Pure functions first:** `_parse_abs_date`, `_derive_probabilities`, `get_candidate_urls`,
  `_find_meeting_for_contract`, `generate_interpretation` — all have zero dependencies. These can be
  written immediately and deliver immediate coverage percentage gains with minimal test code.
- **Fixture-CSV tests second:** `_current_month_already_scraped` (NAB + CoreLogic), `_get_current_cash_rate`,
  `build_asx_futures_entry` — all depend only on `isolate_data_dir` which already exists.
- **Mock-session tests third:** The full fetch paths in abs_data, rba_data, asx_futures, corelogic, nab —
  require the MagicMock session pattern. These are medium complexity but follow the same repeatable pattern
  across all five modules.
- **Orchestration tests last:** `main.py` and `engine.py:generate_status` depend on all ingest modules being
  patchable. Write them after you have confidence the individual module tests work correctly.

---

## MVP Definition

### For 85%+ Coverage (This Milestone)

Ordered by coverage return vs implementation effort:

- [ ] **Pure function tests for all 7 zero-I/O functions** (`_parse_abs_date`, `_derive_probabilities`,
  `get_candidate_urls`, `_find_meeting_for_contract`, `generate_interpretation`, `_find_meeting_for_contract`,
  `_check_staleness`) — fastest wins, zero mocking overhead.
- [ ] **`http_client.py` direct tests** (`create_session` with custom params, adapter assertion) — no mocking
  needed, reaches 85%+ on this module immediately.
- [ ] **`build_gauge_entry` direct tests** — synthetic Series/DataFrame inputs, covers large portion of engine.py.
- [ ] **`build_asx_futures_entry` tmp_path tests** — needs only isolate_data_dir, already available.
- [ ] **HTML bytes fixture tests** (`extract_capacity_from_html`, `get_pdf_link`) — direct call, no mocking.
- [ ] **Idempotency tests for NAB + CoreLogic** (`_current_month_already_scraped`) — tmp_path only.
- [ ] **Mock-session tests for `abs_data.fetch_abs_series`** — happy path + error paths.
- [ ] **Mock-session tests for `rba_data.fetch_cash_rate`** — happy path + `raise_for_status` path.
- [ ] **`main.py` orchestration tests** — patch all ingest modules, test all three tiers + sys.exit.
- [ ] **pdfplumber mock tests** (`extract_capacity_from_pdf`, `extract_cotality_yoy`) — pdfplumber.open mock.

### Add If Time Allows (Pushes Coverage Beyond 85%)

- [ ] **`abs_data.fetch_and_save` filter-path tests** (ABS multi-dimensional CSV filter logic)
- [ ] **`asx_futures_scraper.scrape_asx_futures` full flow** (mock session, fixture JSON response body)
- [ ] **`engine.py:generate_status` assembly test** (mock normalize_indicator, verify JSON output structure)
- [ ] **`nab_scraper.discover_latest_survey_url`** (mock session, two-archive-URL fallback logic)
- [ ] **`nab_scraper.backfill_nab_history`** (mock session, verify month iteration logic)

### Defer to Future Milestone

- [ ] **`engine.py:generate_status` full integration** (requires real pipeline data, more appropriate as a
  smoke test than a unit test)
- [ ] **`asx_futures_scraper._get_rba_meeting_dates`** (reads `public/data/meetings.json` — path not under
  DATA_DIR, needs additional monkeypatching of the `Path("public/data/meetings.json")` open call)

---

## Feature Prioritization Matrix

| Feature | Coverage Return | Implementation Cost | Priority |
|---------|-----------------|---------------------|----------|
| Pure function tests (7 functions, no I/O) | HIGH — each function is 100% uncovered | LOW — parametrize + direct call | P1 |
| `http_client.py` direct session inspection | HIGH — module at 42%, gets to 85%+ | LOW — no mocking | P1 |
| `build_gauge_entry` direct tests | HIGH — covers large engine.py section | LOW — synthetic data | P1 |
| HTML bytes tests (NAB extract, pdf link) | HIGH — 0% covered functions | LOW — pass bytes directly | P1 |
| Idempotency tests (tmp_path CSV) | MEDIUM — covers important guard logic | LOW — write CSV, call function | P1 |
| `build_asx_futures_entry` tmp_path tests | MEDIUM — covers engine.py branch | LOW — isolate_data_dir already exists | P1 |
| Mock-session tests: abs_data | HIGH — abs_data at 17% → ~70%+ | MEDIUM — MagicMock session pattern | P2 |
| Mock-session tests: rba_data | HIGH — rba_data at 24% → ~80%+ | MEDIUM — same pattern | P2 |
| `main.py` orchestration tests | HIGH — 0% → ~85%+ | MEDIUM — patch 4 modules + sys.exit | P2 |
| pdfplumber mock tests | MEDIUM — covers fallback paths | MEDIUM — mock pdfplumber.open | P2 |
| `asx_futures_scraper.scrape_asx_futures` | HIGH — 13% → ~70%+ | MEDIUM — fixture JSON response | P2 |
| `engine.py:generate_status` assembly | HIGH — covers JSON assembly | HIGH — many dependencies to mock | P3 |
| `nab_scraper.backfill_nab_history` | MEDIUM — complex backfill loop | HIGH — many mock interactions | P3 |

**Priority key:**
- P1: Direct call or tmp_path only — write immediately, highest effort-to-coverage ratio
- P2: Requires MagicMock session — write after confirming the mock pattern in one module works
- P3: Multiple layers of mocking — write if 85% not yet reached after P1+P2

---

## Implementation Patterns

### Pattern 1: MagicMock Session (Core Pattern for All Ingest Tests)

```python
from unittest.mock import MagicMock
import requests

def test_fetch_abs_series_happy_path(monkeypatch):
    """fetch_abs_series returns a DataFrame with expected columns on 200 response."""
    csv_body = (
        "TIME_PERIOD,OBS_VALUE\n"
        "2023-Q1,126.1\n"
        "2023-Q2,127.8\n"
    )
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = csv_body

    mock_session = MagicMock()
    mock_session.get.return_value = mock_response

    # Patch create_session IN THE MODULE UNDER TEST, not in http_client
    monkeypatch.setattr(
        "pipeline.ingest.abs_data.create_session",
        lambda **kw: mock_session,
    )

    from pipeline.ingest.abs_data import fetch_abs_series
    df = fetch_abs_series("CPI", "all")

    assert list(df.columns) == ["date", "value", "source", "series_id"]
    assert len(df) == 2
```

Key rule: always patch `"pipeline.ingest.<module>.create_session"`, not
`"pipeline.utils.http_client.create_session"`. The mock must replace the name
*as it appears in the module being tested*.

### Pattern 2: sys.exit Testing

```python
import pytest

def test_run_pipeline_critical_failure_exits(monkeypatch):
    """Critical source failure triggers sys.exit(1)."""
    monkeypatch.setattr(
        "pipeline.main.rba_data.fetch_and_save",
        lambda: (_ for _ in ()).throw(RuntimeError("RBA API down")),
    )
    # Mock the lambda sources too
    monkeypatch.setattr(
        "pipeline.main.CRITICAL_SOURCES",
        [("RBA Cash Rate", lambda: (_ for _ in ()).throw(RuntimeError("down")))],
    )

    from pipeline.main import run_pipeline
    with pytest.raises(SystemExit) as exc:
        run_pipeline()

    assert exc.value.code == 1
```

Alternative: patch `sys.exit` with a side_effect that raises a custom exception,
then catch that exception. `pytest.raises(SystemExit)` is simpler and preferred.

### Pattern 3: pdfplumber Mocking

```python
from unittest.mock import MagicMock, patch

def test_extract_cotality_yoy_happy_path():
    """Regex matches 'Australia X% X% X%' pattern in PDF text."""
    mock_page = MagicMock()
    mock_page.extract_text.return_value = (
        "CoreLogic HVI February 2026\n"
        "Australia 0.8% 2.4% 9.4%\n"
    )
    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page]
    mock_pdf.__enter__ = lambda s: mock_pdf
    mock_pdf.__exit__ = MagicMock(return_value=False)

    with patch("pdfplumber.open", return_value=mock_pdf):
        from pipeline.ingest.corelogic_scraper import extract_cotality_yoy
        result = extract_cotality_yoy(b"fake-pdf-bytes")

    assert result == pytest.approx(9.4)
```

Note: `pdfplumber.open()` is used as a context manager. The mock must implement
`__enter__`/`__exit__` to avoid `AttributeError: __enter__`. Using `MagicMock`
automatically provides context manager protocol, but the return value of `__enter__`
must be configured explicitly.

### Pattern 4: HTML Bytes Fixture Tests (No Mocking)

```python
def test_extract_capacity_from_html_finds_australian_spelling():
    """CAPACITY_REGEX matches 'utilisation' (Australian spelling)."""
    from pipeline.ingest.nab_scraper import extract_capacity_from_html

    html = b"<p>Capacity utilisation was 82.1% in November.</p>"
    result = extract_capacity_from_html(html)
    assert result == pytest.approx(82.1)


def test_extract_capacity_from_html_finds_us_spelling():
    """CAPACITY_REGEX matches 'utilization' (US spelling variant)."""
    from pipeline.ingest.nab_scraper import extract_capacity_from_html

    html = b"<div>Capacity utilization reached 79.5%.</div>"
    result = extract_capacity_from_html(html)
    assert result == pytest.approx(79.5)


def test_extract_capacity_from_html_returns_none_when_no_match():
    """Returns None when CAPACITY_REGEX pattern is absent."""
    from pipeline.ingest.nab_scraper import extract_capacity_from_html

    html = b"<p>Business conditions improved in the quarter.</p>"
    result = extract_capacity_from_html(html)
    assert result is None
```

These require zero mocking and zero fixtures — just bytes in, value out.

### Pattern 5: Pure Function Parametrize

```python
import pytest

@pytest.mark.parametrize("date_str,expected", [
    ("2024-Q1", "2024-01-01"),
    ("2024-Q2", "2024-04-01"),
    ("2024-Q3", "2024-07-01"),
    ("2024-Q4", "2024-10-01"),
    ("2024-01", "2024-01-01"),
    ("2024-12", "2024-12-01"),
    ("2024-01-15", "2024-01-15"),
])
def test_parse_abs_date(date_str, expected):
    """_parse_abs_date handles quarterly, monthly, and full ISO formats."""
    from pipeline.ingest.abs_data import _parse_abs_date
    assert _parse_abs_date(date_str) == expected
```

---

## Sources

- pytest `unittest.mock` patterns: https://docs.python.org/3/library/unittest.mock.html (HIGH confidence)
- pytest monkeypatch docs: https://docs.pytest.org/en/stable/how-to/monkeypatch.html (HIGH confidence)
- `pytest.raises(SystemExit)` for `sys.exit` testing: https://docs.pytest.org/en/stable/reference/reference.html (HIGH confidence)
- requests mocking with MagicMock: https://www.pythontutorial.net/python-unit-testing/python-mock-requests/ (MEDIUM confidence — pattern verified against official mock docs)
- Web scraper testing with mocking: https://datawookie.dev/blog/2025/01/test-a-web-scraper-using-mocking/ (MEDIUM confidence)
- responses library (considered, rejected): https://github.com/getsentry/responses (MEDIUM confidence — see anti-features rationale)
- pdfplumber BytesIO known behaviour: https://github.com/jsvine/pdfplumber/issues/124 (MEDIUM confidence — confirms mock approach is correct)
- Import-path targeting for mocks ("where to patch"): https://docs.python.org/3/library/unittest.mock.html#where-to-patch (HIGH confidence — critical rule)
- Live codebase analysis: `/Users/annon/projects/rba-hawko-meter/pipeline/` (HIGH confidence — verified directly)

---

*Feature research for: RBA Hawk-O-Meter v3.0 — 85%+ per-module unit test coverage*
*Researched: 2026-02-25*
