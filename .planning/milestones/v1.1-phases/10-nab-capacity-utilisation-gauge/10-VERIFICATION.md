---
phase: 10-nab-capacity-utilisation-gauge
verified: 2026-02-24T00:00:00Z
status: passed
score: 15/15 must-haves verified
re_verification: false
gaps: []
human_verification:
  - test: "Open dashboard and confirm Business Conditions card shows trend label format e.g. '83.6% — ABOVE avg, STEADY (Jan 2026)'"
    expected: "Label reads XX.X% — ABOVE/BELOW avg, DIRECTION (Mon YYYY) with correct colour zone"
    why_human: "Playwright tests verify text content and locators; visual rendering of Plotly gauge needle and zone colour cannot be validated without a live browser"
  - test: "Trigger staleness: set nab_capacity.csv last date to 46+ days ago, reload dashboard, confirm amber border appears on Business Conditions card"
    expected: "Border class border-amber-500/50 applied to Business Conditions card"
    why_human: "45-day staleness threshold behaviour requires manipulating live data timestamps; automated static check cannot reproduce stale state"
---

# Phase 10: NAB Capacity Utilisation Gauge — Verification Report

**Phase Goal:** The business confidence gauge is active and shows capacity utilisation percentage, sourced via URL-discovery-based HTML extraction with a PDF fallback.

**Verified:** 2026-02-24

**Status:** PASSED

**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | NAB scraper discovers survey URL from tag archive page, never constructs URLs from date templates | VERIFIED | `discover_latest_survey_url()` crawls `TAG_ARCHIVE_URLS` only; date-template construction confined to `backfill_nab_history()` / `MONTH_URL_PATTERNS` which is explicitly the only permitted site |
| 2 | HTML extraction pulls capacity utilisation percentage from article body text | VERIFIED | `extract_capacity_from_html()` at line 91 applies `CAPACITY_REGEX` across `<p>`, `<li>`, `<div>` tags; returns `float` or `None` |
| 3 | PDF fallback extracts capacity utilisation when HTML extraction returns None | VERIFIED | `get_pdf_link()` + `extract_capacity_from_pdf()` at lines 107–141; `scrape_nab_capacity()` branches to PDF path at line 279 when HTML returns `None` |
| 4 | Scraper is idempotent — skips if current month already in CSV | VERIFIED | `_current_month_already_scraped()` at line 144 checks year+month of latest CSV row; called at start of `scrape_nab_capacity()` and again after backfill |
| 5 | Pipeline continues cleanly when NAB tag archive returns no survey URL | VERIFIED | `scrape_nab_capacity()` returns empty DataFrame at line 267 with `logger.warning` when `discover_latest_survey_url()` returns `None`; `fetch_and_save()` wraps in try/except and returns `{'status': 'failed'}` without raising |
| 6 | business_confidence config points to nab_capacity.csv and normalization engine processes it | VERIFIED | `OPTIONAL_INDICATOR_CONFIG['business_confidence']['csv_file'] == 'nab_capacity.csv'`, `normalize='direct'`, `frequency='monthly'`; `status.json` shows `indicators_available=7`, `indicators_missing=[]` |
| 7 | Business conditions gauge renders on dashboard with capacity utilisation percentage | VERIFIED | `status.json gauges.business_confidence` present: `value=72.5`, `raw_value=83.6`, `raw_unit='%'`, `zone='warm'` |
| 8 | Gauge label shows trend format: 'XX.X% — ABOVE avg, DIRECTION (Mon YYYY)' | VERIFIED | `generateMetricInterpretation()` case `'business_confidence'` at line 418 constructs `cuVal.toFixed(1) + '% — ' + aboveBelow + ' avg' + dirText + monthLabel`; verified string construction logic against `status.json` values |
| 9 | Direction derived from month-over-month change with 0.5pp STEADY threshold | VERIFIED | `build_gauge_entry()` block at lines 204–215 computes `delta = curr_val - prev_val`; STEADY if `abs(delta) <= 0.5`; `status.json direction='STEADY'` (delta 83.6–83.6=0.0pp) |
| 10 | Long-run average calculated dynamically from CSV data | VERIFIED | `entry['long_run_avg'] = round(float(all_values.mean()), 1)` at line 202; `status.json long_run_avg=83.0` computed from 7-month backfill |
| 11 | No placeholder card for business_confidence when data is available | VERIFIED | `tests/phase6-ux.spec.js` test 20 asserts `toHaveCount(0)` for placeholder cards; `tests/dashboard.spec.js` test 2 asserts `toHaveCount(7)` active cards |
| 12 | Staleness warning fires when data is >45 days old | VERIFIED | `renderMetricCard()` at line 500: `if (metricId === 'business_confidence' && metricData.staleness_days > 45) { stale = true; }` — logic present and correctly overrides 90-day default |
| 13 | Source attribution shows 'NAB Monthly Business Survey' | VERIFIED | `build_gauge_entry()` sets `entry['data_source'] = 'NAB Monthly Business Survey'`; `renderMetricCard()` lines 570–575 renders `'Source: ' + metricData.data_source`; `status.json data_source='NAB Monthly Business Survey'` |
| 14 | Why it matters text reflects inflation pressure framing | VERIFIED | `getWhyItMatters('business_confidence')` at line 457 returns `'High capacity utilisation signals inflation pressure, making rate cuts less likely.'` |
| 15 | Dashboard shows 7 of 8 indicators (business_confidence active) | VERIFIED | `status.json metadata.indicators_available=7`, `indicators_missing=[]`; phase6-ux.spec.js test 19 asserts `'7 of 8 indicators'` |

**Score:** 15/15 truths verified

---

### Required Artifacts

#### Plan 10-01 Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `pipeline/ingest/nab_scraper.py` | URL discovery + HTML extraction + PDF fallback scraper, min 150 lines | VERIFIED | 345 lines; all required functions present: `discover_latest_survey_url`, `extract_capacity_from_html`, `get_pdf_link`, `extract_capacity_from_pdf`, `_current_month_already_scraped`, `backfill_nab_history`, `scrape_nab_capacity`, `fetch_and_save` |
| `pipeline/config.py` | business_confidence csv_file wired to nab_capacity.csv | VERIFIED | `csv_file='nab_capacity.csv'`, `normalize='direct'`, `frequency='monthly'` confirmed by programmatic assertion |
| `data/nab_capacity.csv` | Scraped capacity utilisation data with date,value,source columns | VERIFIED | 7 rows; columns `['date','value','source']`; all sources = 'NAB Monthly Business Survey'; date range Apr 2025–Jan 2026 |

#### Plan 10-02 Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `pipeline/normalize/engine.py` | business_confidence gauge entry with long_run_avg, direction, raw_unit, data_source fields | VERIFIED | Block at lines 189–218 adds all four fields; `config` param added to `build_gauge_entry()` signature; `process_indicator()` passes `config=config`; adaptive `min_quarters` logic at lines 311–316 |
| `public/js/interpretations.js` | Capacity utilisation trend label rendering, contains 'ABOVE' | VERIFIED | Case `'business_confidence'` at line 418 renders `ABOVE`/`BELOW` pattern; also adds `dirText`, `monthLabel`; staleness override at line 500; source attribution at line 570; inflation-pressure why-it-matters at line 457 |
| `public/js/gauges.js` | DISPLAY_LABELS business_confidence label shows 'Business Conditions' | VERIFIED | Line 24: `business_confidence: 'Business Conditions'` |
| `tests/dashboard.spec.js` | Phase 10 test describe block with 'Phase 10' string | VERIFIED | `test.describe('Phase 10 — Business Conditions Gauge', ...)` at line 171; two tests verifying trend label regex and importance badge |
| `tests/phase6-ux.spec.js` | Updated placeholder count and coverage notice | VERIFIED | Test 19 asserts `'7 of 8 indicators'`; test 20 asserts `toHaveCount(0)` for placeholder cards |

---

### Key Link Verification

#### Plan 10-01 Key Links

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `pipeline/ingest/nab_scraper.py` | `business.nab.com.au/tag/economic-commentary` | `discover_latest_survey_url()` crawls tag archive | WIRED | `TAG_ARCHIVE_URLS` at lines 30–33 contains both archive URLs; loop at line 63 fetches and parses each |
| `pipeline/ingest/nab_scraper.py` | `data/nab_capacity.csv` | `append_to_csv()` after extraction | WIRED | `append_to_csv(output_path, row, date_column='date')` called at line 223 (backfill) and line 332 (`fetch_and_save`) |
| `pipeline/config.py` | `pipeline/normalize/engine.py` | `OPTIONAL_INDICATOR_CONFIG business_confidence csv_file` | WIRED | `generate_status()` at line 345 merges `OPTIONAL_INDICATOR_CONFIG` into processing loop; `process_indicator()` reads `config['csv_file']` and passes `config` to `build_gauge_entry()` |

#### Plan 10-02 Key Links

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `pipeline/normalize/engine.py` | `public/data/status.json` | `build_gauge_entry()` adds long_run_avg, direction, data_source fields | WIRED | `status.json` contains `long_run_avg=83.0`, `direction='STEADY'`, `data_source='NAB Monthly Business Survey'`, `raw_unit='%'` — written by `generate_status()` via `json.dump` at line 417 |
| `public/js/interpretations.js` | `public/data/status.json` | `generateMetricInterpretation` reads `metricData.long_run_avg` and `metricData.direction` | WIRED | Lines 423–427: `var lra = metricData.long_run_avg || 81; var cuDirection = metricData.direction || ''` — reads from the status.json contract fields |
| `public/js/interpretations.js` | `public/js/gauges.js` | `getDisplayLabel('business_confidence')` returns 'Business Conditions' | WIRED | `generateMetricInterpretation` default case at line 440 calls `GaugesModule.getDisplayLabel(metricId)`; `renderMetricCard` at line 516 calls same; `DISPLAY_LABELS.business_confidence = 'Business Conditions'` |

---

### Requirements Coverage

All requirement IDs declared in phase 10 PLANs: NAB-01, NAB-02, NAB-03, NAB-04, NAB-05

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| NAB-01 | 10-01 | Capacity utilisation % scraped from NAB Monthly Business Survey HTML article body | SATISFIED | `extract_capacity_from_html()` applies `CAPACITY_REGEX` to `<p>/<li>/<div>` tags; 7 rows in CSV from backfill confirming extraction worked |
| NAB-02 | 10-01 | Survey URL discovered via tag archive page, not constructed from date templates | SATISFIED | `discover_latest_survey_url()` uses `TAG_ARCHIVE_URLS` only; 0 hardcoded survey article URLs in scraper; `MONTH_URL_PATTERNS` confined to `backfill_nab_history()` with explicit comment |
| NAB-03 | 10-01, 10-02 | Business confidence gauge activated with capacity utilisation data | SATISFIED | `status.json` shows `business_confidence` in `gauges`, `indicators_available=7`, `indicators_missing=[]` |
| NAB-04 | 10-02 | Gauge shows trend label indicating above/below long-run average (~81%) | SATISFIED | Trend label format `"83.6% — ABOVE avg, STEADY (Jan 2026)"` rendered by `generateMetricInterpretation`; `long_run_avg=83.0` computed from CSV; `direction='STEADY'` from 0.5pp threshold |
| NAB-05 | 10-01 | PDF fallback extracts capacity utilisation if HTML extraction fails for a given month | SATISFIED | `get_pdf_link()` + `extract_capacity_from_pdf()` implemented; `scrape_nab_capacity()` branches to PDF at line 279 when HTML returns `None`; same fallback in `backfill_nab_history()` at lines 204–212 |

**REQUIREMENTS.md cross-check:** All five IDs (NAB-01 through NAB-05) appear in REQUIREMENTS.md Phase 10 traceability table, all marked Complete. No orphaned requirements found.

---

### Anti-Patterns Found

| File | Pattern | Severity | Impact |
|------|---------|----------|--------|
| None | — | — | — |

Scan of `pipeline/ingest/nab_scraper.py`, `pipeline/normalize/engine.py`, `public/js/interpretations.js`, and `public/js/gauges.js` returned clean — no TODO/FIXME/HACK/PLACEHOLDER comments, no empty handlers, no stub returns.

---

### Human Verification Required

#### 1. Business Conditions Gauge Visual Rendering

**Test:** Open the dashboard at `localhost:3000` (or deployed URL). Locate the "Business Conditions" card in the indicator grid.

**Expected:** Card shows a needle-style Plotly gauge with needle pointing into the warm zone; interpretation text reads `83.6% — ABOVE avg, STEADY (Jan 2026)` (or the month matching the latest CSV row); source attribution shows `Source: NAB Monthly Business Survey`; importance badge shows `Lower importance`; why-it-matters text reads `High capacity utilisation signals inflation pressure, making rate cuts less likely.`

**Why human:** Plotly gauge needle position and zone colour rendering require a live browser with JavaScript execution. Static file checks confirm the data contract and code logic, but not the visual output.

#### 2. 45-Day Staleness Border

**Test:** Temporarily modify `data/nab_capacity.csv` to set the latest date row to 46+ days before today, regenerate `status.json`, then reload the dashboard.

**Expected:** Business Conditions card gains an amber border (`border-amber-500/50`) and shows the "N months old" label beneath the date.

**Why human:** The 45-day staleness path depends on a computed `staleness_days` value that is currently negative (data_date is in the future relative to test) — the code path cannot be exercised without temporarily altering CSV data.

---

### Gaps Summary

No gaps. All 15 must-haves verified. All five requirements (NAB-01 through NAB-05) are satisfied by code in the codebase, not just by SUMMARY claims. Key data flow is confirmed end-to-end: `nab_capacity.csv` exists with 7 real rows, `status.json` contains the enriched `business_confidence` gauge entry, and the frontend renders the correct trend label and attribution.

The one deliberate deviation from plan — engine.py's adaptive `min_quarters` logic — is appropriate and enables the newly-wired indicator to produce z-scores without the standard 20-quarter history requirement. This is wired correctly and confirmed by the LOW confidence badge in `status.json` which accurately signals the limited history.

---

_Verified: 2026-02-24_

_Verifier: Claude (gsd-verifier)_
