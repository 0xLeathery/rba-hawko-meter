# Phase 19: Ingest Module Tests - Research

**Generated:** 2026-02-25
**Status:** Research complete

## 1. Pipeline Module Analysis

### http_client.py (12 statements, 42% covered, 7 missing)
- **Single function:** `create_session(retries, backoff_factor, user_agent)` -> `requests.Session`
- **Logic:** Creates Session, configures Retry strategy (total, backoff_factor, status_forcelist=[500,502,503,504], allowed_methods=["GET","POST"]), mounts HTTPAdapter on http:// and https://, sets User-Agent header
- **Imports:** `pipeline.config.USER_AGENT` for default user agent
- **Branches:** `user_agent or USER_AGENT` (custom vs default UA)
- **Error paths:** None (pure configuration)
- **Lines missing (37-57):** The entire function body is untested

### abs_data.py (117 statements, 17% covered, 97 missing)
- **Functions:**
  - `fetch_abs_series(dataflow_id, key, params, filters, timeout)` -> DataFrame
  - `_parse_abs_date(date_str)` -> str (monthly "YYYY-MM", quarterly "YYYY-QN", other)
  - `fetch_cpi()`, `fetch_employment()`, `fetch_household_spending()`, `fetch_wage_price_index()`, `fetch_building_approvals()`, `fetch_rppi()` — thin wrappers
  - `fetch_and_save(series=None)` -> dict — fetch one or all series
  - `FETCHERS` dict mapping names to (function, output_file)
- **Error paths in fetch_abs_series:**
  - HTTP non-200 status -> Exception
  - Empty response body -> Exception
  - Response too short (<100 bytes) -> Exception
  - CSV parse failure -> Exception (from ParserError)
  - No data rows -> Exception
- **Error paths in fetch_and_save:**
  - Unknown series name -> ValueError
  - ChunkedEncodingError, Timeout, ConnectionError -> caught, returns 0
  - Generic Exception -> caught, returns 0
- **Date-dependent logic:** `_parse_abs_date` handles Q1-Q4 and monthly formats
- **Imports to patch:** `pipeline.ingest.abs_data.create_session`

### rba_data.py (45 statements, 24% covered, 34 missing)
- **Functions:**
  - `fetch_cash_rate()` -> DataFrame — fetches RBA CSV, finds header row ("Series ID"/"Series Id"), extracts date + value columns, parses dates, extracts numeric from ranges
  - `fetch_and_save()` -> int — fetches and saves to CSV
- **Error paths:**
  - `response.raise_for_status()` — raises on non-200
  - Header row detection: scans for "Series ID" or "Series Id"
  - Value extraction from ranges: regex `([\d.]+)$` handles "17.00 to 17.50"
  - Date parsing with `dayfirst=True` for AU format
- **Imports to patch:** `pipeline.ingest.rba_data.create_session`

### asx_futures_scraper.py (144 statements, 13% covered, 125 missing)
- **Functions:**
  - `_get_current_cash_rate()` -> float — reads CSV, falls back to 4.35
  - `_get_rba_meeting_dates()` -> list[str] — reads meetings.json (hardcoded Path)
  - `_find_meeting_for_contract(contract_expiry, meeting_dates)` -> str|None
  - `_derive_probabilities(implied_rate, current_rate)` -> tuple[float, int, int, int]
  - `scrape_asx_futures()` -> DataFrame
  - `_check_staleness(csv_path)` -> None (logs warnings)
  - `fetch_and_save()` -> dict
- **Error paths:**
  - Cash rate CSV missing -> fallback 4.35
  - meetings.json missing -> empty list
  - No futures items -> empty DataFrame
  - Missing expiry or settlement -> skip item
  - Implied rate out of range (0-15) -> skip item
  - No meeting found -> use contract expiry as proxy
  - Exception in fetch_and_save -> caught, returns failed dict
- **Date-dependent logic:** `datetime.now()` for scrape_date, staleness checks
- **Path issues:** `_get_rba_meeting_dates()` uses hardcoded `Path("public/data/meetings.json")` NOT affected by DATA_DIR fixture

### corelogic_scraper.py (114 statements, 19% covered, 92 missing)
- **Functions:**
  - `get_candidate_urls(year, month)` -> list — 4 URL patterns
  - `download_cotality_pdf(year, month, session)` -> bytes|None
  - `extract_cotality_yoy(pdf_bytes)` -> float|None — uses pdfplumber
  - `_current_month_already_scraped(output_path)` -> bool
  - `scrape_cotality()` -> DataFrame
  - `fetch_and_save()` -> dict
- **Error paths:**
  - PDF not found at any candidate URL -> None
  - pdfplumber ImportError -> None
  - Pattern not found in PDF text -> None
  - Current month already scraped -> empty DF
  - No data for any candidate month -> empty DF
  - Exception in fetch_and_save -> caught
- **Date-dependent:** `datetime.now()` for current month, previous month calc, period_end calc
- **pdfplumber usage:** `pdfplumber.open(io.BytesIO(pdf_bytes))` -> pages[:4] -> `extract_text()` -> regex

### nab_scraper.py (203 statements, 14% covered, 175 missing)
- **Functions:**
  - `discover_latest_survey_url(session)` -> str|None — crawls tag archives
  - `fetch_article(url, session)` -> bytes|None
  - `extract_capacity_from_html(html_bytes)` -> float|None — BeautifulSoup + regex
  - `get_pdf_link(html_bytes)` -> str|None
  - `extract_capacity_from_pdf(pdf_bytes)` -> float|None — pdfplumber
  - `_current_month_already_scraped(output_path)` -> bool
  - `backfill_nab_history(session, months=12)` -> int
  - `scrape_nab_capacity()` -> DataFrame
  - `fetch_and_save()` -> dict
- **Error paths:**
  - Tag archive non-200 -> continue
  - Tag archive fetch exception -> continue
  - No survey URL found -> None
  - Article fetch failure -> None
  - HTML extraction returns None -> PDF fallback
  - No PDF link -> None
  - PDF fetch failure -> None
  - pdfplumber ImportError -> None
  - pdfplumber extraction exception -> None
  - Current month already scraped -> empty DF
  - Backfill: per-month failures -> skip that month
- **Date-dependent:** `datetime.now()` for idempotency, period dates
- **MONTH_URL_PATTERNS:** List of 3 lambda URL templates for backfill

## 2. Existing Test Patterns

### conftest.py
- `isolate_data_dir` (autouse): monkeypatches `pipeline.config.DATA_DIR` to `tmp_path`
- `block_network` (autouse): replaces `socket.socket` to block network; exempts `@pytest.mark.live`
- CSV loader fixtures: `fixture_cpi_df`, `fixture_employment_df`, `fixture_wages_df`, `fixture_spending_df`, `fixture_building_approvals_df`, `fixture_housing_df`, `fixture_nab_capacity_df`
- No JSON/HTML loader fixtures yet

### Existing test modules
- `test_zscore.py`: Heavy parametrize usage, known-answer tests
- `test_gauge.py`: Tests gauge mapping
- `test_csv_handler.py`: Tests CSV append/dedup
- `test_ratios.py`: Tests normalization ratios
- `test_schema.py`: JSON schema validation
- `test_smoke.py`: Basic import tests
- No ingest module tests exist yet

## 3. Fixture Files Available

### CSV fixtures (6 ABS + 2 RBA + 1 CoreLogic + 1 NAB)
- `abs_cpi.csv`, `abs_employment.csv`, `abs_wage_price_index.csv`, `abs_household_spending.csv`, `abs_building_approvals.csv` — stored CSV output format
- `abs_response.csv` — ABS API response format (SDMX CSV with labels)
- `abs_response_empty.csv` — headers only, no data rows
- `rba_cashrate.csv` — RBA format with metadata header rows, 4 data rows
- `rba_cashrate_empty.csv` — headers + metadata only, no data rows
- `corelogic_housing.csv` — stored CSV output format

### JSON fixtures
- `asx_response.json` — MarkitDigital API response with 2 items (IB2603, IB2604)
- `asx_response_empty.json` — response with empty items array

### HTML fixtures
- `nab_article.html` — NAB survey article with "capacity utilisation rose further to 83.6%" + PDF link
- `nab_article_no_data.html` — NAB article without capacity data or PDF link
- `corelogic_article.html` — Cotality article with PDF download link
- `corelogic_article_no_pdf.html` — Cotality article without PDF link

## 4. Current Coverage Baseline

| Module | Stmts | Covered | Missing |
|--------|-------|---------|---------|
| http_client.py | 12 | 42% | 7 |
| abs_data.py | 117 | 17% | 97 |
| rba_data.py | 45 | 24% | 34 |
| asx_futures_scraper.py | 144 | 13% | 125 |
| corelogic_scraper.py | 114 | 19% | 92 |
| nab_scraper.py | 203 | 14% | 175 |

Target: 85%+ per module

## 5. Key Patterns for Tests

### Mock Session Pattern
Patch `create_session` at import site (e.g., `pipeline.ingest.abs_data.create_session`). Return MagicMock session with `.get()` returning mock Response object.

### pdfplumber Mock
Mock `pdfplumber.open()` as context manager returning object with `.pages` list where each page has `.extract_text()` returning the target pattern string.

### Datetime Freezing
Use `monkeypatch.setattr()` to replace `datetime` on the module under test. Mock class must delegate `.strptime()` and other class methods to real datetime.

### Fixture Loading
CSV fixtures loaded via conftest fixtures. Need to add JSON and HTML fixture loaders.

---
*Research completed: 2026-02-25*
