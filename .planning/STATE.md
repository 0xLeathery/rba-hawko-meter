# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-04)

**Core value:** "Data, not opinion." Empowers laypeople to understand interest rate drivers without relying on media sensationalism or biased advice.
**Current focus:** Phase 6 - UX Plain English (complete)

## Current Position

Phase: 7 of 7 (ASX Futures Integration)
Plan: 2 of 3 complete
Status: In progress
Last activity: 2026-02-07 — Completed 07-02-PLAN.md (ASX Futures Normalization Pipeline)

Progress: [████████████████████████░░] 93.75% (15/16 plans complete)

## Performance Metrics

**Velocity:**
- Total plans completed: 15
- Average duration: 3.0 minutes
- Total execution time: 0.75 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01 | 4/5 | 18.4 min | 4.6 min |
| 03 | 2/2 | 6 min | 3.0 min |
| 04 | 2/2 | 4 min | 2.0 min |
| 05 | 2/2 | 12.5 min | 6.25 min |
| 06 | 3/3 | 8.8 min | 2.9 min |
| 07 | 2/3 | 4 min | 2.0 min |

**Recent Trend:**
- Last 5 plans: 06-01 (2 min), 06-03 (3 min), 06-02 (3.8 min), 07-01 (2 min), 07-02 (2 min)
- Phase 7 in progress - ASX futures pipeline integration complete

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- **Netlify Hosting**: User preference for existing workflow/infrastructure
- **Serverless/Static**: Minimizes cost and complexity (Netlify + JSON flat files)
- **Z-Score Algorithm**: Normalizes diverse metrics into single 0-100 scale
- **Scraping**: Official APIs don't cover all leading indicators (accepted maintenance burden)
- **No Framework**: React/Vue is overkill for single-page dashboard (Vanilla JS + Tailwind + Plotly)
- **ABS API Wildcard Approach** (01-01): Use "all" queries with filters for maintainability
- **CSV Storage** (01-01): Per-source CSV files in data/ directory for simplicity
- **BA_GCCSA for Building Approvals** (01-04): Use BA_GCCSA dataflow (Greater Capital Cities) instead of missing "BA"
- **Building Approvals as Non-Critical** (01-04): Mark critical=False since it's a secondary indicator
- **Graceful Degradation for Optional Sources** (01-02): CoreLogic/NAB scrapers never crash, return status dicts
- **Scraper Diagnostics Pattern** (01-02): JS-rendering detection, validation checks for brittleness
- **BROWSER_USER_AGENT** (01-02): Realistic Chrome UA in config for web scraping
- **Tiered Failure Handling with Exit Codes** (01-03): 0=success, 1=critical failure, 2=partial success for nuanced monitoring
- **Off-Peak Cron Scheduling** (01-03): Use :07 and :23 minutes to avoid GitHub Actions load spikes
- **Manual Seed Files for CoreLogic/NAB Historical** (01-03): PDF-based data requires manual backfill from archived reports
- **numpy-only MAD calculation** (03-01): No scipy dependency for single function; np.median(|x - median|) * 1.4826
- **[-3,+3] clamp range** (03-01): Widened from original [-2,+2] per research (reduces clipping 4.6% -> 0.3%)
- **ASX futures excluded from hawk score** (03-01): Displayed as benchmark, excluded via exclude_benchmark parameter
- **Guarded normalization import** (03-02): NORMALIZATION_AVAILABLE flag prevents pipeline crash if module broken
- **Non-fatal normalization** (03-02): Normalization failure does not change pipeline exit code
- **Blue/Grey/Red color scheme** (04-01): Colorblind-accessible gauge colors instead of Green/Amber/Red (8% of males have red-green deficiency)
- **Bullet gauge shape for metrics** (04-02): Compact horizontal bullet gauges visually distinct from hero semicircle
- **staticPlot for bullet gauges** (04-02): Prevents mobile touch conflicts on view-only gauges
- **90-day staleness threshold** (04-02): Amber border indicator for stale metric data
- **Half-monthly frequency method** (05-01): Divide monthly by 2/4 for fortnightly/weekly (standard AU mortgage calculator approach)
- **Decimal.js string conversion** (05-01): Always toString() before new Decimal() to prevent IEEE 754 precision loss
- **Footer disclaimer rewrite** (05-02): ASIC RG 244 compliant with AFS Licence statement, non-endorsement, personal circumstances caveat
- **Plain English zone labels** (06-01): RATES LIKELY FALLING/RISING instead of DOVISH/HAWKISH for layperson clarity
- **Native details/summary for onboarding** (06-01): HTML5 semantic element instead of custom JS accordion (zero overhead, accessible)
- **Hide ASX panel completely when unavailable** (06-03): display:none when data null instead of showing "unavailable" message (cleaner UX)
- **Exclude asx_futures from placeholder cards** (06-03): It's a benchmark, not a core indicator
- **HTML5 details/summary for collapsible chart** (06-03): Native browser element for mobile-friendly chart toggle
- **Calculator bridge uses neutral language** (06-03): "could mean" not "will mean" per ASIC RG 244
- **Data quality guard for building approvals** (06-02): Filter raw_value < -90 or > 500, show "data being updated" instead of bogus -99.9%
- **Importance labels over percentages** (06-02): High/Medium/Lower mapped from 20%/10% thresholds for layperson clarity
- **Australian date format** (06-02): Intl.DateTimeFormat with en-AU locale (1 Dec 2025 not 2025-12-01)
- **Plain verdict from score ranges** (06-02): Map hawk_score to 5 ASIC-compliant verdict texts using "likely to", "may be more likely" language
- **ASX JSON endpoints** (07-01): Use ASX DAM JSON endpoints (dynamic_text, market_expectations) instead of HTML parsing
- **Probability derivation algorithm** (07-01): Derive rate movement probabilities from implied vs current rate with 5bp deadband
- **Composite-key dedup for ASX** (07-01): Deduplicate on [date, meeting_date] instead of date alone for multi-meeting scrapes
- **ASX futures bypass Z-score pipeline** (07-02): Benchmark indicators read directly via load_asx_futures_csv(), bypass normalization/Z-score/gauge flow
- **Top-level asx_futures key in status.json** (07-02): asx_futures sits at same level as gauges/overall/metadata, NOT inside gauges dict
- **Direction thresholds for ASX** (07-02): change_bp < -5 → cut, > 5 → hike, else hold (5bp deadband matches probability derivation)
- **CSV schema validation in ratios.py** (07-02): load_indicator_csv() checks for 'value' column before processing to handle non-standard multi-column formats

### Pending Todos

None yet.

### Blockers/Concerns

- **Building Approvals data source** (RESOLVED 01-04): ABS Data API "BA" dataflow not found -- resolved by using BA_GCCSA dataflow. Building approvals now implemented with 144 rows of historical data.
- **Web scraper maintenance burden** (01-02): CoreLogic, NAB, ASX scrapers have TODOs for actual implementation. May need PDF parsing, Selenium/Playwright for JS-rendered pages, or alternative data sources. Optional sources pattern means pipeline continues even if these fail.
- **Mixed ABS series data** (03-02): Employment and retail trade CSVs contain multiple ABS series mixed together (wildcard queries). Produces invalid YoY% values. Need ABS filter refinement in Phase 1 gap closure.
- **ASX endpoint availability** (07-01): Both ASX DAM JSON endpoints (dynamic_text, market_expectations) return 404 as of Feb 2026. ASX appears to have restructured their Rate Tracker API. Options: monitor for restoration, find alternative endpoints, implement Selenium scraper, or use alternative data source. Graceful degradation pattern means pipeline continues with other indicators.

## Session Continuity

Last session: 2026-02-07 21:39 UTC
Stopped at: Completed 07-02-PLAN.md -- ASX Futures Normalization Pipeline
Resume file: None
Next: One more plan (07-03) to complete Phase 7. ASX futures data flows from scraper → CSV → status.json. Frontend integration and end-to-end testing remaining.
