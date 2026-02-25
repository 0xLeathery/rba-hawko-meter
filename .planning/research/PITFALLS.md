# Pitfalls Research

**Domain:** Adding 85%+ unit test coverage to existing Python scraper/pipeline modules
**Researched:** 2026-02-25
**Confidence:** HIGH (direct codebase analysis + verified patterns from pytest/requests-mock ecosystem)

---

## Critical Pitfalls

### Pitfall 1: Mocking the Session But Not the Module That Creates It

**What goes wrong:**
Tests for `abs_data.py`, `rba_data.py`, `asx_futures_scraper.py`, `corelogic_scraper.py`,
and `nab_scraper.py` all call `create_session()` from `pipeline.utils.http_client`, then
call `session.get(...)`. The test patches `requests.get` directly, or patches
`pipeline.utils.http_client.requests.Session`, but the actual code creates the session via
`create_session()`. The patch targets the wrong object — the real network call goes through,
hits the socket blocker (`RuntimeError: Network access blocked in tests`), and the test fails
with a confusing error that looks like an infrastructure problem.

**Why it happens:**
Python's `unittest.mock.patch` must target the name where it is **used**, not where it is
**defined**. The code under test calls `create_session()` which internally calls
`requests.Session()`. Patching `requests.Session` at the `requests` module level does not
intercept the already-imported `Session` reference inside `http_client.py`. The correct
target is `pipeline.utils.http_client.requests.Session` or, more practically, mock the
return value of `create_session` itself via
`monkeypatch.setattr("pipeline.ingest.abs_data.create_session", lambda **kw: mock_session)`.

**How to avoid:**
Patch `create_session` at the point of import in the module under test, not at the
`requests` library level:

```python
# Good: patches create_session where abs_data.py imports it
def test_fetch_abs_success(monkeypatch):
    mock_session = MagicMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = SAMPLE_ABS_CSV
    mock_session.get.return_value = mock_resp
    monkeypatch.setattr("pipeline.ingest.abs_data.create_session", lambda **kw: mock_session)
    df = fetch_abs_series("CPI", "all")
    assert len(df) > 0

# Bad: patches requests.Session at the library level — create_session already has
# the real requests.Session reference captured at import time in http_client.py
monkeypatch.setattr("requests.Session", lambda: mock_session)  # Does not work
```

**Warning signs:**
- Test for an ingestor raises `RuntimeError: Network access blocked` even with a mock in place.
- The mock `assert_called_once_with()` check passes but the function still makes network calls.
- Coverage report shows ingestor lines covered but the test was patching the wrong target.

**Phase to address:**
Phase 1 (ingest module tests). Establish the correct patching target in the first test
written for each ingestor — this pattern is reused for all 5 ingest modules.

---

### Pitfall 2: Missing Error-Path Coverage — The Dominant Coverage Gap

**What goes wrong:**
Each ingestor has explicit error paths: HTTP 4xx/5xx responses, empty response bodies,
malformed CSV/JSON, `pd.errors.ParserError`, and per-module graceful-degradation returns
(`{'status': 'failed', ...}`). Tests are written for the happy path only.
Coverage reaches 60-70% and then plateaus. The remaining uncovered lines are almost entirely
error branches. To reach 85%, these paths must be tested.

For `abs_data.py` specifically: the `fetch_abs_series()` function has guards for
`status_code != 200`, empty response body, body too short, `ParserError`, zero rows after
filtering, and missing columns after renaming. Each is a branch that takes 4-6 lines.
Testing only the success path covers ~50% of `fetch_abs_series`.

**Why it happens:**
Error paths feel "obvious" and are easy to deprioritize. The temptation is to write one
success test and one generic "raises on failure" test, but neither covers the specific
branches. `fetch_and_save()` in all ingestors catches exceptions per-source and returns
`{'status': 'failed'}` — this branch is invisible to a success-path-only test.

**How to avoid:**
For every public function in the ingest layer, explicitly enumerate its error branches:

```
abs_data.fetch_abs_series():
  [ ] HTTP status != 200
  [ ] response.text is empty
  [ ] response.text shorter than 100 bytes
  [ ] pd.errors.ParserError on malformed CSV
  [ ] len(df) == 0 after parse
  [ ] filters produce 0 rows
  [x] happy path

abs_data.fetch_and_save():
  [ ] ChunkedEncodingError during fetch
  [ ] Timeout during fetch
  [ ] ConnectionError during fetch
  [ ] Generic Exception
  [x] single-series happy path
  [x] all-series happy path
```

Write one test per error branch. Each test configures the mock to trigger that specific
condition. This is the only reliable way to reach 85%.

**Warning signs:**
- Module coverage is 60-70% and adding more success-path tests doesn't move the number.
- Running `pytest --cov-report=html` and the uncovered lines are all inside `except` blocks
  or `if status_code != 200` guards.
- Test file has 1 test per module function instead of 3-6.

**Phase to address:**
Phase 1 (ingest module tests). Budget ~3-6 tests per ingestor function, not 1.

---

### Pitfall 3: Date-Dependent Logic Makes Tests Non-Deterministic

**What goes wrong:**
`corelogic_scraper.scrape_cotality()` and `nab_scraper.scrape_nab_capacity()` both call
`datetime.now()` internally to determine which month's PDF to fetch, whether current-month
data is already scraped, and what date to assign the output row. Tests written today pass.
Tests written in January fail in February because `now.month` changed and the idempotency
check returns a different value.

`asx_futures_scraper.scrape_asx_futures()` writes `datetime.now().strftime('%Y-%m-%d')` as
the `date` column. A test asserting the date value in the output DataFrame will fail the
next day.

`nab_scraper._current_month_already_scraped()` compares `latest.year == now.year and
latest.month == now.month`. A fixture CSV with `date = 2026-01-01` passes this check in
January 2026 but fails (correctly) in February 2026, meaning the test produces a different
code path depending on when it runs.

**Why it happens:**
`datetime.now()` is a global side effect. It is easy to miss when writing tests because
the function "works" — it just produces different behavior at different calendar times.

**How to avoid:**
Freeze time for any test that exercises date-dependent logic. Use `freezegun` or patch
`datetime` directly:

```python
from unittest.mock import patch
from datetime import datetime

def test_current_month_already_scraped_false(tmp_path):
    # Fixture has data from Jan 2026. Test runs as if it's Feb 2026.
    # Without time-freeze, this test fails in Jan 2026 (returns True, not False).
    with patch("pipeline.ingest.corelogic_scraper.datetime") as mock_dt:
        mock_dt.now.return_value = datetime(2026, 2, 15)
        csv = tmp_path / "corelogic_housing.csv"
        csv.write_text("date,value,source\n2026-01-31,9.4,Cotality HVI\n")
        assert _current_month_already_scraped(csv) is False
```

Alternatively, install `freezegun` and use `@freeze_time("2026-02-15")`.

For the ASX futures `date` column: assert only that the date column exists and is a valid
date string, not its exact value.

**Warning signs:**
- A test passes today and fails next month with no code changes.
- Test for `_current_month_already_scraped()` with a fixture CSV containing the current
  month's date produces `True` when the test intends to test the "not scraped" path.
- Test for `scrape_cotality()` "months_to_try" logic fails depending on what month it is.

**Phase to address:**
Phase 1 (ingest module tests). Identify all `datetime.now()` calls before writing the
first test for corelogic and NAB scrapers.

---

### Pitfall 4: PDF Fixture Brittleness — Testing the Parser Not the PDF

**What goes wrong:**
`corelogic_scraper.extract_cotality_yoy()` and `nab_scraper.extract_capacity_from_pdf()`
open a real PDF file via pdfplumber. A test creates a fixture by saving a real Cotality
HVI PDF to `tests/python/fixtures/cotality_sample.pdf`. This introduces three problems:

1. **Binary fixture size**: Real PDFs are 500KB-5MB. The repository gains megabytes of
   binary test fixtures that diff poorly and inflate clone size.
2. **Fragility**: The regex `r'Australia\s+([-\d.]+)%\s+([-\d.]+)%\s+([-\d.]+)%'` relies
   on pdfplumber extracting text in a specific order from a specific PDF version. When
   Cotality changes their PDF layout (quarterly), the fixture becomes invalid.
3. **Copyright**: Committing a Cotality PDF to a public repo may violate their Terms of
   Service.

**Why it happens:**
The most obvious way to test `extract_cotality_yoy(pdf_bytes: bytes)` is to call it with
real PDF bytes. Creating a minimal synthetic PDF requires more effort upfront.

**How to avoid:**
Mock pdfplumber at the page-text level, not at the file level. The function under test
only calls `pdfplumber.open()` and `page.extract_text()`. Mock those two things:

```python
from unittest.mock import patch, MagicMock

def test_extract_cotality_yoy_found():
    """Test successful extraction when pattern is present in page text."""
    mock_page = MagicMock()
    mock_page.extract_text.return_value = (
        "Housing Values\n"
        "Australia 0.8% 2.4% 9.4%\n"
        "Sydney 1.2% 3.1% 11.2%\n"
    )
    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page]
    mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
    mock_pdf.__exit__ = MagicMock(return_value=False)

    with patch("pipeline.ingest.corelogic_scraper.pdfplumber.open", return_value=mock_pdf):
        result = extract_cotality_yoy(b"fake-pdf-bytes")
    assert result == 9.4
```

This tests the regex and extraction logic without a real PDF. It is immune to PDF format
changes, has no binary fixture overhead, and is fast (<1ms).

**Warning signs:**
- `tests/python/fixtures/` contains any `.pdf` file.
- `extract_cotality_yoy` or `extract_capacity_from_pdf` test takes more than 1 second.
- Test requires a specific Cotality PDF URL to be accessible.

**Phase to address:**
Phase 1 (corelogic and NAB scraper tests). Establish the pdfplumber mock pattern before
writing any PDF extraction tests.

---

### Pitfall 5: Coverage Gaming — Testing Trivial Paths to Hit the Number

**What goes wrong:**
After reaching 70% coverage on a module, the remaining 30% consists of complex error paths,
branching logic, and boundary conditions. Instead of testing these, additional trivial tests
are written: testing that `MONTH_ABBREV[1] == "Jan"`, testing the `__name__ == '__main__'`
block, testing that a config constant has the expected string value. Coverage climbs to 85%
but the tested lines provide no regression protection.

In `nab_scraper.py`, the `MONTH_URL_PATTERNS` list contains three lambda functions. Testing
each lambda's URL format is straightforward and covers 6 lines. But these lambdas only fail
if NAB changes their URL structure — a runtime concern, not a unit test concern. Meanwhile,
`backfill_nab_history()`'s inner loop through `MONTH_URL_PATTERNS` with session fallback
logic remains at 0% coverage.

**Why it happens:**
Coverage tools measure which lines are executed, not whether the assertions test meaningful
behavior. A test that calls a function and asserts `result is not None` covers every line
in that function. Chasing the percentage target without reviewing what the assertions
actually verify leads to tests that are executed but not meaningful.

**How to avoid:**
For each module, before writing tests, list the behaviors that would constitute a regression
if they broke silently:

```
corelogic_scraper.scrape_cotality():
  - If current month already scraped: returns empty DataFrame, does not re-download
  - If PDF found for current month: returns 1-row DataFrame with correct date
  - If current month PDF missing: tries previous month
  - If both months fail: returns empty DataFrame
  - Date assigned is last day of the reference month, not today's date
```

Every test should assert at least one of these behaviors. If a test passes regardless of
whether the behavior is correct, the test is not protecting against regression.

**Warning signs:**
- A test asserts `result is not None` or `result['status'] in ('success', 'failed')` as
  its primary assertion.
- Tests covering config constants, `__main__` blocks, or module-level `MONTH_ABBREV` dict.
- Coverage number climbs but the test descriptions do not describe behaviors.

**Phase to address:**
Phase 1 (ingest module tests) and Phase 2 (engine/main tests). Define behavior
assertions before writing each test, not after.

---

### Pitfall 6: Mocking Too Much in engine.py and main.py Tests

**What goes wrong:**
`engine.generate_status()` calls `normalize_indicator()`, `compute_rolling_zscores()`,
`build_gauge_entry()`, `compute_hawk_score()`, and writes `status.json`. A test for
`generate_status()` mocks all of these functions to return fixture data, then asserts the
output JSON matches expectations. Coverage of `generate_status()` reaches 90%.

But now the tests for `generate_status()` tell us nothing about whether the function
correctly wires its components together — they only verify that it calls the mocks in
the expected sequence. If `build_gauge_entry()` changes its return schema, the test for
`generate_status()` still passes (because the mock returns the old schema).

The same pattern in `main.run_pipeline()`: mocking all three tiers' `fetch_and_save()`
functions and asserting the result dict structure covers the orchestration logic, but tests
nothing about how failures in one tier affect the others.

**Why it happens:**
Mocking everything is the path of least resistance for complex orchestration functions.
It avoids fixture setup complexity and runs instantly. The coverage report shows green.

**How to avoid:**
Distinguish between two types of tests for orchestration functions:

**Integration-style unit tests** (preferred for engine/main): Use real sub-functions with
fixture CSV files as input. Patch only external I/O (file writes, network). Let
`normalize_indicator()`, `compute_rolling_zscores()`, and `build_gauge_entry()` run
for real on fixture data. This catches wiring errors and schema mismatches.

```python
def test_process_indicator_with_fixture_cpi(monkeypatch, tmp_path, fixture_cpi_df):
    # Write fixture to tmp_path (DATA_DIR is already patched by autouse)
    fixture_cpi_df.to_csv(tmp_path / "abs_cpi.csv", index=False)
    weights = {"inflation": {"weight": 1.0, "polarity": 1}}
    entry, value = process_indicator("inflation", CPI_CONFIG, weights["inflation"])
    assert entry is not None
    assert 0 <= entry['value'] <= 100
    assert entry['zone'] in ('cold', 'cool', 'neutral', 'warm', 'hot')
```

**Behavior-focused mock tests** (for edge cases): When testing that `generate_status()`
correctly handles a missing indicator (no data for one source), mock only the specific
`normalize_indicator()` call for that source to return `None`, leaving others real.

**Warning signs:**
- A test for `generate_status()` has more than 5 `monkeypatch.setattr()` calls.
- The test for `run_pipeline()` mocks `rba_data.fetch_and_save`, `abs_data.fetch_and_save`,
  and all scrapers simultaneously.
- Removing an assertion from the test does not change which mock calls are made.

**Phase to address:**
Phase 2 (engine and main tests). Use real fixture data for integration-style orchestration
tests; reserve full mocking for specific error-path tests.

---

### Pitfall 7: The `main.py` `sys.exit(1)` Terminating the Test Process

**What goes wrong:**
`main.run_pipeline()` calls `sys.exit(1)` when a critical source fails. A test that
triggers the critical failure path — e.g., `rba_data.fetch_and_save()` raises an exception
— causes the entire pytest process to exit with code 1. All subsequent tests are not run.
Coverage for those tests is not recorded.

**Why it happens:**
`sys.exit()` raises `SystemExit`, which propagates out of all function calls unless caught.
Pytest does not catch `SystemExit` by default in collected tests — it propagates up and
terminates the test runner.

**How to avoid:**
Use `pytest.raises(SystemExit)` as a context manager for tests that exercise the critical
failure path:

```python
def test_run_pipeline_critical_failure_exits(monkeypatch):
    def raise_exception():
        raise Exception("RBA API down")
    monkeypatch.setattr("pipeline.main.rba_data.fetch_and_save", raise_exception)
    monkeypatch.setattr("pipeline.main.abs_data.fetch_and_save", lambda s=None: {})

    with pytest.raises(SystemExit) as exc_info:
        run_pipeline()

    assert exc_info.value.code == 1
```

Do not allow `sys.exit()` to propagate unhandled in any test. Verify with
`pytest.raises(SystemExit)` for the specific code.

**Warning signs:**
- `pytest` output shows "INTERNALERROR" or truncated test results.
- Test count from `pytest --collect-only` does not match the number of tests that ran.
- Test for `run_pipeline()` critical path is listed as "ERROR" rather than "PASSED/FAILED".

**Phase to address:**
Phase 2 (main.py tests). Identify `sys.exit()` calls before writing the first test.

---

### Pitfall 8: `asx_futures_scraper` Path Dependencies Breaking Isolation

**What goes wrong:**
`asx_futures_scraper._get_rba_meeting_dates()` opens `public/data/meetings.json` using a
relative path: `Path("public/data/meetings.json")`. Unlike `DATA_DIR` (which is patched by
the autouse `isolate_data_dir` fixture in conftest.py), this path is not under `DATA_DIR`
and is not patched. When tests run in a directory other than the repo root, this file is
not found. When the `tmp_path` doesn't contain this file, the function falls back to
returning `[]` — silently changing the behavior under test.

Similarly, `_get_current_cash_rate()` reads from `pipeline.config.DATA_DIR / "rba_cash_rate.csv"`.
This path IS under `DATA_DIR` and IS patched. But tests for `scrape_asx_futures()` may not
create the `rba_cash_rate.csv` in `tmp_path`, causing fallback to `rate = 4.35` silently.

**Why it happens:**
`asx_futures_scraper.py` has two implicit file dependencies: one under `DATA_DIR` (patched)
and one under `public/data/` (not patched). The `isolate_data_dir` autouse fixture only
covers `DATA_DIR`.

**How to avoid:**
For tests of `scrape_asx_futures()`:
1. Create a fixture `rba_cash_rate.csv` in `tmp_path` (already covered by `DATA_DIR` patch).
2. Patch `_get_rba_meeting_dates` to return controlled fixture meeting dates, or patch
   `pipeline.ingest.asx_futures_scraper.Path` for the meetings.json path.

```python
def test_scrape_asx_futures_uses_rba_cash_rate(monkeypatch, tmp_path):
    # Create fixture cash rate CSV in the patched DATA_DIR
    cash_rate_csv = tmp_path / "rba_cash_rate.csv"
    cash_rate_csv.write_text("date,value\n2026-01-01,4.10\n")

    # Patch meetings to avoid the unpatched public/data/ path
    monkeypatch.setattr(
        "pipeline.ingest.asx_futures_scraper._get_rba_meeting_dates",
        lambda: ["2026-03-18", "2026-05-06"]
    )

    # Mock the HTTP session
    mock_session = MagicMock()
    mock_resp = MagicMock()
    mock_resp.json.return_value = SAMPLE_ASX_FUTURES_JSON
    mock_session.get.return_value = mock_resp
    monkeypatch.setattr(
        "pipeline.ingest.asx_futures_scraper.create_session",
        lambda **kw: mock_session
    )

    df = scrape_asx_futures()
    assert df['implied_rate'].gt(0).all()
```

**Warning signs:**
- `scrape_asx_futures()` test passes but uses `current_rate = 4.35` (fallback), not the
  fixture value — verify by asserting `change_bp` is computed from 4.10, not 4.35.
- Test for `_find_meeting_for_contract()` is skipped because meeting dates are always empty.
- Coverage shows `_get_rba_meeting_dates()` and `_get_current_cash_rate()` at 0%.

**Phase to address:**
Phase 1 (ASX futures scraper tests). Document the two path dependencies in the test plan
before writing tests.

---

### Pitfall 9: `engine.py` Housing Source Attribution Inline Import

**What goes wrong:**
`engine.build_gauge_entry()` contains `import pandas as _pd` and
`import pipeline.config as pipeline` inside the function body for the `housing` and
`business_confidence` branches. These deferred imports are there for scoping reasons but
create an invisible coverage gap: if neither branch is exercised in tests, those import
lines show as uncovered.

More importantly, the `housing` branch reads from `corelogic_housing.csv` to determine
`data_source`. A test that processes the `housing` indicator with fixture data but
does not create a `corelogic_housing.csv` in `tmp_path` will exercise the "csv_path.exists()
is False" code path, missing the `data_source` assignment logic.

**Why it happens:**
The `housing` and `business_confidence` enrichment blocks in `build_gauge_entry()` require
specific fixture CSV files beyond the primary indicator CSV. Tests written for the happy
path of these indicators may not think to create the auxiliary files.

**How to avoid:**
When writing tests for `build_gauge_entry()` with the housing indicator:
1. Create `corelogic_housing.csv` in `tmp_path` with a `source` column.
2. Test both the `source == 'ABS'` → `data_source = 'ABS RPPI'` path and the
   `source == 'Cotality HVI'` path.
3. Test the `csv_path.exists() is False` path (no file).

For `business_confidence`: create `nab_capacity.csv` in `tmp_path` with at least 2 rows
to trigger both the `long_run_avg` computation and the `direction` logic.

**Warning signs:**
- `engine.py` coverage shows uncovered lines in `build_gauge_entry()` after tests are written.
- The `data_source` and `stale_display` keys are absent from all test assertions.
- Test for `business_confidence` indicator only checks `entry['value']` and `entry['zone']`,
  not `entry['direction']`, `entry['long_run_avg']`, or `entry['data_source']`.

**Phase to address:**
Phase 2 (engine tests). Enumerate all auxiliary file reads in `build_gauge_entry()` before
writing housing and business_confidence tests.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Patching `requests.Session` instead of `create_session` | Looks right | Patch misses; test exercises real network; fails at socket level | Never — always patch the module-level reference |
| Assert `result is not None` as the primary assertion | Gets coverage | Zero regression protection; test passes even when function is broken | Never — assert specific structure or values |
| Using a real Cotality/NAB PDF as fixture | No mock setup required | Binary in repo; breaks when PDF format changes; potential ToS violation | Never — mock pdfplumber at `page.extract_text()` level |
| Not patching `datetime.now()` in date-dependent tests | Simpler test code | Test passes in Jan, fails in Feb; non-deterministic CI | Never for `_current_month_already_scraped()`, `scrape_cotality()`, `scrape_nab_capacity()` |
| Testing only happy path to get 60-70% quickly | Fast initial progress | Remaining 30% requires 3x more effort; error paths have higher bug density | Only if explicitly scoped to a "start" phase — must plan error-path phase |
| Full mock of all sub-functions in `generate_status()` | Easy to write | Catches zero wiring errors; test becomes a call-sequence verification | Only for specific error-path tests; use real sub-functions for integration-style tests |
| Skipping `sys.exit()` tests for `run_pipeline()` | Avoids complexity | Exit-on-failure path is untested; entire test runner terminates if test is wrong | Never — use `pytest.raises(SystemExit)` |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| `requests` + `create_session()` | Patch `requests.Session` globally | Patch `pipeline.ingest.MODULE.create_session` at point of use |
| `pdfplumber` + PDF bytes | Pass real PDF bytes or save PDF fixture | Mock `pdfplumber.open()` to return controlled `page.extract_text()` output |
| `BeautifulSoup` + HTML scraping (NAB) | Fixture HTML that mirrors live site exactly | Use minimal HTML with only the elements the parser needs; keep fixture small |
| `asx_futures_scraper` + `public/data/meetings.json` | Forget this path is NOT under `DATA_DIR` | Patch `_get_rba_meeting_dates()` directly or create the file in test setup |
| `engine.build_gauge_entry()` + housing/NAB auxiliary CSVs | Only create the primary indicator CSV | Create auxiliary `corelogic_housing.csv` and `nab_capacity.csv` in `tmp_path` |
| `main.run_pipeline()` + `sys.exit(1)` | Let SystemExit propagate — crashes test runner | Wrap in `pytest.raises(SystemExit)` for critical failure path tests |
| `freezegun` or `datetime` patch + `nab_scraper` | Patch `datetime.datetime.now` — wrong target | Patch `pipeline.ingest.nab_scraper.datetime` (the module-level `datetime` import) |
| `abs_data.fetch_abs_series()` + column name format | Fixture CSV column name differs from ABS API format | ABS API returns columns like `TIME_PERIOD: Time Period` with label appended; fixture must match or the `startswith` filter fails |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| `nab_scraper.backfill_nab_history()` running in test | Test takes 10-30 seconds; makes 36 HTTP calls (12 months × 3 URL patterns) | Patch `backfill_nab_history` or prevent the backfill trigger by pre-populating `tmp_path` with ≥3 rows in `nab_capacity.csv` | Any test for `scrape_nab_capacity()` that doesn't pre-create the CSV with ≥3 rows |
| Running `generate_status()` with real fixture CSVs for schema validation | 2-5 seconds per test; adds up with parametrized cases | Validate schema against a pre-built fixture `status.json`; run `generate_status()` only in targeted integration tests | When more than 3 schema tests call `generate_status()` |
| `asx_futures_scraper._check_staleness()` writing to real `DATA_DIR` | If `tmp_path` is not set up with the CSV first, falls through; if it is, reads from fixture — usually fine | Ensure `tmp_path / "asx_futures.csv"` exists before calling `fetch_and_save()`; `_check_staleness()` is called internally | Any test for `fetch_and_save()` that doesn't create the CSV first |
| pdfplumber loading real PDF files in tests | Tests take 0.5-2 seconds each (PDF parsing is slow) | Mock at `pdfplumber.open()` level, not at the file level | Any test that calls `extract_cotality_yoy(real_pdf_bytes)` |

---

## "Looks Done But Isn't" Checklist

- [ ] **Error path coverage:** Run `pytest --cov=pipeline --cov-report=term-missing` and
  check that uncovered lines are not `except` blocks or error guards. Every module should
  have at least one test per distinct error condition.
- [ ] **Patching targets verified:** For each ingestor test, confirm the mock is actually
  intercepted by running the test with the `block_network` autouse fixture active (no
  `@pytest.mark.live`). If the test raises `RuntimeError: Network access blocked`, the
  patch is wrong.
- [ ] **Date independence:** Run each scraper test twice: once with `freeze_time("2026-01-15")`
  and once with `freeze_time("2026-07-15")`. Both should pass with the same assertion.
- [ ] **No binary fixtures:** `find tests/python/fixtures/ -name "*.pdf" -o -name "*.xlsx"`
  should return nothing.
- [ ] **`sys.exit()` coverage:** `main.py`'s critical failure path is tested with
  `pytest.raises(SystemExit)`. Run `pytest --cov=pipeline.main --cov-report=term-missing`
  — the `sys.exit(1)` line must be covered.
- [ ] **Auxiliary file coverage in engine:** `build_gauge_entry()` for `housing` and
  `business_confidence` is tested with the auxiliary CSV present AND absent.
- [ ] **`asx_futures` dual path dependency:** Both `_get_current_cash_rate()` and
  `_get_rba_meeting_dates()` are exercised in tests (not both silently returning fallbacks).
- [ ] **85% per-module, not aggregate:** `pytest --cov=pipeline --cov-fail-under=85` passes
  without `--cov-config` ignoring any module. Verify each module individually with
  `--cov-report=term-missing` before declaring the milestone complete.

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Wrong patch target (patch misses, network blocked error) | LOW | Check the import path in the module under test; change `patch("requests.Session")` to `patch("pipeline.ingest.MODULE.create_session", ...)` |
| Test suite stalls at 65% due to untested error paths | MEDIUM | Run `pytest --cov-report=html`; open the HTML report; sort by missing lines; write one test per distinct error branch starting from the most-covered module |
| Date-dependent test failures on CI | LOW | Add `@freeze_time("2026-02-25")` or `patch("pipeline.ingest.MODULE.datetime")` to the offending tests; run once to verify |
| PDF fixture in repo | LOW | Delete the PDF file; replace the test with a pdfplumber mock; `git rm tests/python/fixtures/*.pdf` |
| `sys.exit()` terminates pytest run | LOW | Wrap the test body in `with pytest.raises(SystemExit) as exc_info:` and assert `exc_info.value.code == 1` |
| Coverage stuck at 85% aggregate but one module at 60% | MEDIUM | Identify the low-coverage module; enumerate its error branches; write targeted tests; do not add trivial tests to other modules to inflate aggregate |
| `backfill_nab_history()` running in every NAB test | LOW | Pre-create `tmp_path / "nab_capacity.csv"` with 5+ rows; the backfill trigger checks `len(existing) < 3` |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Wrong patching target for `create_session` | Phase 1 (ingest tests — first test written) | Test passes with `block_network` autouse active and no `@pytest.mark.live` |
| Missing error-path coverage | Phase 1 (ingest tests — all ingestors) | `pytest --cov-report=term-missing` shows no uncovered `except` blocks |
| Date-dependent non-determinism | Phase 1 (corelogic, NAB, ASX ingest tests) | Test passes identically with `freeze_time("2026-01-15")` and `freeze_time("2026-07-15")` |
| Binary PDF fixtures | Phase 1 (corelogic and NAB tests) | `find tests/python/fixtures/ -name "*.pdf"` returns nothing |
| Coverage gaming (trivial assertions) | Phase 1 and Phase 2 (all test phases) | Every test has at least one assertion that would fail if the function returned wrong data |
| Over-mocking `generate_status()` | Phase 2 (engine tests) | At least one test for `generate_status()` uses real `normalize_indicator()` with fixture CSV |
| `sys.exit()` terminating test runner | Phase 2 (main.py tests) | `run_pipeline()` critical failure path is in `pytest.raises(SystemExit)` context |
| `asx_futures` unpatched `meetings.json` path | Phase 1 (ASX futures tests) | `_get_rba_meeting_dates()` coverage > 80%; meeting dates in output match fixture, not fallback `[]` |
| Housing auxiliary file gap | Phase 2 (engine tests) | `build_gauge_entry()` tested with and without `corelogic_housing.csv`; `data_source` key asserted |
| `backfill_nab_history()` running in unit tests | Phase 1 (NAB scraper tests) | NAB scraper unit test suite runs in < 5 seconds total |

---

## Sources

- Direct codebase analysis: `pipeline/ingest/abs_data.py` — 7 distinct error paths in
  `fetch_abs_series()`, each a separate coverage branch
- Direct codebase analysis: `pipeline/ingest/asx_futures_scraper.py` — `public/data/meetings.json`
  is NOT under `DATA_DIR`; requires separate patching strategy
- Direct codebase analysis: `pipeline/ingest/corelogic_scraper.py` and `nab_scraper.py` —
  both call `datetime.now()` internally; tests must freeze time
- Direct codebase analysis: `pipeline/normalize/engine.py` — `build_gauge_entry()` has
  deferred `import pandas as _pd` inside housing and business_confidence branches
- Direct codebase analysis: `pipeline/main.py` — `sys.exit(1)` on critical failure; must
  be caught with `pytest.raises(SystemExit)` in tests
- Direct codebase analysis: `tests/python/conftest.py` — `isolate_data_dir` patches
  `pipeline.config.DATA_DIR` but does NOT patch `public/data/` paths
- pytest documentation — `pytest.raises(SystemExit)` for testing exit codes (HIGH confidence)
- pytest documentation — `monkeypatch.setattr` with dotted path for correct patch targeting
  (HIGH confidence — official docs)
- freezegun library — `@freeze_time` decorator for deterministic date-dependent tests
  (HIGH confidence — widely used, maintained 2025)
- Datawookie blog (Jan 2025) — "Test a Web Scraper using Mocking" — `responses` library
  and `unittest.mock` pattern comparison (MEDIUM confidence — recent, practitioner source)
- Python unittest.mock documentation — patch target must be where the name is used, not
  where it is defined (HIGH confidence — official docs, fundamental mock pitfall)
- Community pattern: HTML fixture minimalism — use only the markup the parser needs, not
  a full page snapshot (MEDIUM confidence — established scraper testing practice)

---
*Pitfalls research for: Adding 85%+ unit test coverage to Python scraper/pipeline modules (v3.0 milestone)*
*Researched: 2026-02-25*
