# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-04)

**Core value:** "Data, not opinion." Empowers laypeople to understand interest rate drivers without relying on media sensationalism or biased advice.
**Current focus:** Phase 6 - UX Plain English (in progress)

## Current Position

Phase: 6 of 6 (UX Plain English)
Plan: 1 of 3 complete
Status: In progress
Last activity: 2026-02-06 — Completed 06-01-PLAN.md (Plain English Labels & Onboarding)

Progress: [█████████████████████████░] 92% (11/12 plans complete)

## Performance Metrics

**Velocity:**
- Total plans completed: 11
- Average duration: 3.2 minutes
- Total execution time: 0.60 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01 | 4/5 | 18.4 min | 4.6 min |
| 03 | 2/2 | 6 min | 3.0 min |
| 04 | 2/2 | 4 min | 2.0 min |
| 05 | 2/2 | 12.5 min | 6.25 min |
| 06 | 1/3 | 2 min | 2.0 min |

**Recent Trend:**
- Last 5 plans: 04-01 (2 min), 04-02 (2 min), 05-01 (9.5 min), 05-02 (3 min), 06-01 (2 min)
- Phase 6 starting strong with straightforward UX improvements

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

### Pending Todos

None yet.

### Blockers/Concerns

- **Building Approvals data source** (RESOLVED 01-04): ABS Data API "BA" dataflow not found -- resolved by using BA_GCCSA dataflow. Building approvals now implemented with 144 rows of historical data.
- **Web scraper maintenance burden** (01-02): CoreLogic, NAB, ASX scrapers have TODOs for actual implementation. May need PDF parsing, Selenium/Playwright for JS-rendered pages, or alternative data sources. Optional sources pattern means pipeline continues even if these fail.
- **Mixed ABS series data** (03-02): Employment and retail trade CSVs contain multiple ABS series mixed together (wildcard queries). Produces invalid YoY% values. Need ABS filter refinement in Phase 1 gap closure.

## Session Continuity

Last session: 2026-02-06 08:43 UTC
Stopped at: Completed 06-01-PLAN.md -- Plain English Labels & Onboarding
Resume file: None
Next: Continue Phase 6 with Plan 06-02 (Time context & visual hierarchy) or Plan 06-03 (Information architecture).
