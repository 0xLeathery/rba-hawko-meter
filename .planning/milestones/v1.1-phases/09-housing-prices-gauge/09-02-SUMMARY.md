---
phase: 09-housing-prices-gauge
plan: 02
subsystem: pipeline + normalization + frontend
tags: [cotality, hvi, pdf-scraping, pdfplumber, housing-gauge, normalization, fallback]
dependency-graph:
  requires: [09-01]
  provides: [cotality-hvi-scraper, hybrid-normalization, monthly-housing-data]
  affects: [data/corelogic_housing.csv, public/data/status.json, dashboard-housing-card]
tech-stack:
  added: [pdfplumber>=0.11,<1.0]
  patterns: [candidate-url-try-list, hybrid-source-normalization, idempotent-monthly-scrape]
key-files:
  created:
    - .planning/phases/09-housing-prices-gauge/09-02-SUMMARY.md
  modified:
    - requirements.txt
    - pipeline/ingest/corelogic_scraper.py
    - pipeline/normalize/ratios.py
    - data/corelogic_housing.csv
    - public/data/status.json
    - tests/dashboard.spec.js
    - tests/phase6-ux.spec.js
decisions:
  - Cotality PDF scraper wired into automated pipeline (not manual mode) per project owner approval
  - Hybrid normalization in ratios.py separates ABS index rows from Cotality pre-computed YoY rows
  - Cotality rows stored as YoY % directly in CSV (not re-expressed as index values)
key-decisions:
  - precomputed_yoy_sources set in normalize_indicator detects Cotality HVI rows and bypasses YoY computation
  - Idempotency guard checks current month in CSV before downloading PDF
  - 4-candidate URL try-list handles Cotality URL pattern inconsistency (monthly and annually named variants)
metrics:
  duration: 25 minutes
  completed: 2026-02-24
  tasks-completed: 2
  files-modified: 7
  files-created: 1
  commits: 1
---

# Phase 9 Plan 02: Cotality HVI PDF Scraper Summary

**One-liner:** Cotality HVI PDF scraper downloads Feb 2026 monthly release (9.4% YoY), appends to corelogic_housing.csv, with pdfplumber extraction, hybrid normalization fix, and dynamic source attribution.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Cotality ToS risk acknowledgement (checkpoint resolved) | — | No code — decision checkpoint |
| 2 | Cotality PDF scraper implementation + pipeline integration | ccf5496 | requirements.txt, pipeline/ingest/corelogic_scraper.py, pipeline/normalize/ratios.py, data/corelogic_housing.csv, public/data/status.json, tests/dashboard.spec.js, tests/phase6-ux.spec.js |

## What Was Built

### Task 1: Decision Checkpoint

Project owner approved the Cotality PDF scraper with reasoning: "This is publicly available information we are trying to ingest programmatically." Decision recorded: proceed with automated pipeline integration (not manual mode).

### Task 2: Cotality PDF Scraper

**`pipeline/ingest/corelogic_scraper.py`** — complete replacement of the non-functional stub:

- `get_candidate_urls(year, month)`: Returns 4 candidate Cotality PDF URLs across discover.cotality.com and pages.cotality.com with both abbreviated (Jan/Feb) and full-name (January/February) variants.
- `download_cotality_pdf(year, month, session)`: Tries each candidate URL, returns PDF bytes on first 200+PDF response, returns None if all fail (graceful degradation).
- `extract_cotality_yoy(pdf_bytes)`: Uses pdfplumber to scan first 4 pages for `Australia X% X% X%` pattern, extracts the 3rd value (annual YoY %).
- `_current_month_already_scraped(output_path)`: Idempotency guard — checks if current month's Cotality row exists in CSV; skips download if so.
- `scrape_cotality()`: Orchestrates download+extraction for current month then previous month (lag fallback). Returns one-row DataFrame with `date, value, source='Cotality HVI', series_id`.
- `fetch_and_save()`: Pipeline-compatible entry point, never raises, returns status dict.

**Live result**: Successfully downloaded Feb 2026 HVI PDF from `discover.cotality.com/hubfs/Article-Reports/COTALITY%20HVI%20Feb%202026%20FINAL.pdf` and extracted 9.4% national annual YoY change.

**`requirements.txt`** — Added `pdfplumber>=0.11,<1.0`.

**`pipeline/normalize/ratios.py`** — Hybrid normalization logic added to `normalize_indicator()`:

The ABS RPPI data stores absolute index values (e.g., 183.9). Cotality HVI stores pre-computed YoY % (9.4). Without this fix, the normalization computed `(9.4/183.9 - 1)*100 = -94%` — severely wrong. The fix:
1. Detect if the CSV has a `source` column with Cotality HVI rows.
2. Extract Cotality rows separately (most recent only).
3. Run standard YoY normalization on ABS index rows only.
4. Append the Cotality YoY % directly as the latest data point.

Result: housing gauge reads Z=0.56, Gauge=59.4, Zone=neutral, raw_value=9.4% — correct and meaningful.

**`data/corelogic_housing.csv`** — 75 rows (74 ABS quarterly rows + 1 Cotality Feb 2026 row with `source='Cotality HVI'`).

**`public/data/status.json`** — Housing gauge updated: `data_source='Cotality HVI'`, `raw_value=9.4`, `staleness_days=-4` (period end 2026-02-28 is 4 days future, expected for monthly release).

**Test updates (`tests/dashboard.spec.js`, `tests/phase6-ux.spec.js`)**:
- Source attribution test accepts either `ABS RPPI` or `Cotality HVI` via regex
- Card index for building approvals updated from 4 to 5 (housing now active at index 3)
- Coverage notice updated from "5 of 8" to "6 of 8 indicators"
- Placeholder count updated from 2 to 1 (business_confidence only)
- 26/26 Playwright tests passing

## Verification Results

All plan verification checks passed:
```
pdfplumber installed: OK
corelogic_scraper imports: OK
Candidate URLs for Feb 2026: 4 URLs generated
fetch_and_save result: {'status': 'failed', 'error': 'No new Cotality data extracted'}  # Correct -- idempotency
Housing data_source in status.json: Cotality HVI
requirements.txt includes pdfplumber: OK
raw_value: 9.4 (correct YoY %)
ALL CHECKS PASSED
```

Note: `fetch_and_save` returns `failed` on second call because the idempotency guard correctly skips re-downloading data already present for the current month.

Pipeline normalization:
```
[6/8] Processing housing... Z=0.56, Gauge=59.4, Zone=neutral
Hawk Score: 50.8 (Balanced)
Indicators: 6 available, 1 missing
```

Playwright: 26/26 tests passing.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed double-normalization of Cotality pre-computed YoY values**
- **Found during:** Task 2 verification (normalization engine)
- **Issue:** Cotality HVI stores 9.4% as a pre-computed annual YoY %. ABS RPPI stores absolute index values. The `compute_yoy_pct_change()` function computed `(9.4/183.9 - 1)*100 = -94%`, corrupting the housing gauge (raw_value=-94, zone=cold).
- **Fix:** Modified `normalize_indicator()` in `ratios.py` to detect Cotality HVI rows via `source` column, separate them from ABS index rows, run standard YoY normalization on ABS-only data, then append the Cotality YoY value directly as the latest data point.
- **Files modified:** `pipeline/normalize/ratios.py`
- **Commit:** ccf5496

**2. [Rule 1 - Bug] Updated Playwright tests reflecting Cotality integration**
- **Found during:** Task 2 Playwright test run (5 failures)
- **Issue:** Tests written during Plan 09-01 expected `Source: ABS RPPI`, building card at index 4, "5 of 8 indicators", 2 placeholder cards. All assertions became stale when housing activated via Cotality.
- **Fix:** Updated source attribution assertion to regex accepting either source; updated building card index from 4 to 5; updated coverage from "5 of 8" to "6 of 8"; updated placeholder count from 2 to 1.
- **Files modified:** `tests/dashboard.spec.js`, `tests/phase6-ux.spec.js`
- **Commit:** ccf5496

## Decisions Made

1. **Automated pipeline integration (not manual)**: Project owner explicitly approved: "This is publicly available information we are trying to ingest programmatically." Cotality rows in `OPTIONAL_SOURCES` in `main.py` — no changes needed.

2. **Cotality value stored as pre-computed YoY %**: The PDF gives us the annual change directly (9.4%). Storing as raw YoY avoids needing to infer an index continuation from the 2021 ABS series. The normalization engine detects and handles this via `precomputed_yoy_sources` set in `ratios.py`.

3. **4-candidate URL try-list**: Cotality URL patterns vary across months (abbreviated vs full month name, discover vs pages subdomain). Try-list pattern handles inconsistency without brittle single-URL assumptions.

4. **Idempotency at monthly granularity**: Pipeline runs weekly; Cotality scraper skips if the current month is already in the CSV. This prevents duplicate rows while allowing re-runs within the same month.

## Self-Check: PASSED

All files verified:
- `requirements.txt` contains `pdfplumber` — FOUND
- `pipeline/ingest/corelogic_scraper.py` contains `extract_cotality_yoy` — FOUND
- `data/corelogic_housing.csv` contains `Cotality HVI` row — FOUND
- `public/data/status.json` shows `data_source: Cotality HVI` — FOUND
- Commit ccf5496 verified present — FOUND
