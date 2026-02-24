# Project: RBA Hawk-O-Meter

## What This Is
An automated, unbiased economic dashboard for Australian mortgage holders. Ingests raw economic data from ABS, RBA, ASX, CoreLogic/Cotality, and NAB, normalizes it via Z-scores, and presents interest rate pressure through traffic-light gauges, a mortgage impact calculator, and plain English interpretations. 7 of 8 indicators active with full data coverage. Live at Netlify with daily/weekly automated data updates via GitHub Actions.

## Core Value
**"Data, not opinion."**
Empowers laypeople to understand interest rate drivers without relying on media sensationalism or biased advice from banks/brokers.

## Constraints
- **Zero Cost Hosting:** Must run on Netlify (frontend) and GitHub Actions (backend).
- **Maintenance:** "Silent Automation" preferred, though scraping maintenance is accepted.
- **Data Integrity:** Strictly NO nominal currency values in gauges to avoid inflation bias; must use ratios/per-capita metrics.
- **ASIC Compliance:** All language must use neutral framing per RG 244. No personal or general financial advice.

## Scope
- **Backend:** Python-based ETL pipeline (ingest → normalize → Z-score → status.json).
- **Frontend:** Static HTML/JS dashboard using Plotly.js for gauges, Tailwind CSS, Decimal.js for calculator.
- **Automation:** Weekly pipeline (Monday) + daily ASX futures scraper (weekdays) via GitHub Actions.
- **Data Sources:** ABS (official — CPI, employment, wages, spending, building approvals, RPPI housing), RBA (official — cash rate, meetings), ASX (JSON API — futures), Cotality HVI (PDF scraping — dwelling prices), NAB (HTML/PDF scraping — capacity utilisation).

## Requirements

### Validated
- ✓ PIPE-01: RBA cash rate ingestion via readabs — v1.0
- ✓ PIPE-02: ABS economic indicators (CPI, employment, retail) — v1.0
- ✓ PIPE-05: Data appends with timestamps — v1.0 (per-source CSVs with dedup)
- ✓ PIPE-06: Metrics normalized to ratios — v1.0 (YoY % change)
- ✓ PIPE-07: Z-scores with 10-year rolling window — v1.0 (robust median/MAD)
- ✓ PIPE-08: Z-scores mapped to 0-100 gauge scale — v1.0
- ✓ PIPE-09: status.json output — v1.0
- ✓ PIPE-10: Weekly GitHub Action — v1.0 (confirmed with 11+ automated commits)
- ✓ PIPE-11: Fallback on scraper failure — v1.0 (exit code 2 pattern)
- ✓ PIPE-12: ABS Wage Price Index — v1.0
- ✓ PIPE-13: ABS Building Approvals — v1.0 (BA_GCCSA dataflow)
- ✓ DASH-01 through DASH-06: Full dashboard display — v1.0
- ✓ COMP-01 through COMP-03: ASIC compliance — v1.0
- ✓ HAWK-01 through HAWK-03, HAWK-05: Hawk-O-Meter gauges and verdicts — v1.0
- ✓ CALC-01 through CALC-04: Mortgage calculator — v1.0
- ✓ ASX-01 through ASX-04: ASX futures multi-meeting display with CI freshness — v1.1
- ✓ HOUS-01 through HOUS-04: Housing gauge with ABS RPPI + Cotality HVI fallback — v1.1
- ✓ NAB-01 through NAB-05: NAB capacity utilisation scraper and gauge — v1.1
- ✓ PIPE-03: CoreLogic/Cotality dwelling price scraping (HVI PDF media releases) — v1.1
- ✓ PIPE-04: NAB capacity utilisation survey (HTML extraction + PDF fallback) — v1.1
- ✓ HAWK-04: ASX Futures multi-meeting probability display — v1.1

### Active
(No active requirements — next milestone not yet defined)

### Out of Scope
| Feature | Reason |
|---------|--------|
| "You should fix" recommendations | Constitutes personal financial advice — requires AFS License (ASIC RG 244) |
| Direct lender/product comparisons | Shifts from "macro tool" to "lead gen site" — dilutes unbiased value |
| "Best rate" tables | Quickly outdated, biased by referral fees |
| User accounts/login | Increases friction and privacy liability — stateless app preferred |
| Opinionated blog/news | Violates "Data, not opinion" core value |
| Real-time data updates | Weekly cadence is sufficient for macro indicators; real-time adds cost/complexity |
| Mobile native app | Web-first, responsive design sufficient for v1 |

## Key Decisions
| Decision | Rationale | Outcome |
|----------|-----------|---------|
| **Netlify Hosting** | User preference for existing workflow/infrastructure | ✓ Auto-deploys from Git |
| **Serverless/Static** | Minimizes cost and complexity | ✓ Netlify + JSON flat files |
| **Z-Score Algorithm** | Normalizes diverse metrics into 0-100 scale | ✓ Robust median/MAD with [-3,+3] clamp |
| **Scraping** | Official APIs don't cover all leading indicators | ✓ CoreLogic/NAB scrapers shipped in v1.1 |
| **No Framework** | React/Vue is overkill for single-page dashboard | ✓ Vanilla JS + Tailwind + Plotly |
| **Blue/Grey/Red gauges** | 8% of males have red-green color deficiency | ✓ Colorblind-accessible |
| **IIFE modules** | Encapsulate private state without a build system | ✓ Clean module pattern |
| **Decimal.js for calculator** | IEEE 754 precision loss with native JS floats | ✓ Exact mortgage math |
| **ASX futures as benchmark** | Market-derived, not an economic indicator | ✓ Excluded from hawk score, displayed separately |
| **Plain English labels** | "RATES LIKELY FALLING" not "DOVISH" | ✓ Layperson clarity |
| **ABS as primary housing source** | Cotality ToS (8.4d) prohibits automated scraping | ✓ ABS RPPI activates gauge; Cotality monthly PDF as supplement |
| **Hybrid normalization** | Cotality YoY pre-computed, ABS is index | ✓ ratios.py separates sources to prevent double-normalization |
| **NAB HTML-first extraction** | Capacity utilisation is inline in article HTML | ✓ PDF is fallback only; 7-month backfill successful |
| **URL discovery for NAB** | Tag archive pages list current surveys | ✓ Never construct URLs from date templates for current month |
| **Adaptive min_quarters** | New indicators lack 20 quarters of history | ✓ Lower z-score threshold for limited data with LOW confidence badge |
| **45-day staleness for NAB** | Monthly data needs tighter threshold than 90d default | ✓ Business Conditions card fires amber border at 45d |

## Context

Shipped v1.1 with ~6,276 LOC (3,227 Python + 3,049 JS).
Tech stack: Python (pandas, numpy, requests, beautifulsoup4, pdfplumber), Vanilla JS, Tailwind CSS, Plotly.js, Decimal.js.
28 Playwright tests (100% pass).
7 of 8 economic indicators active (ASX futures displayed separately as 8th). All data source gaps closed.
Dashboard coverage: "Based on 7 of 8 indicators".
Automated data updates: weekly pipeline (Monday) + daily ASX futures (weekdays) via GitHub Actions.

## Success Criteria
1. **Fully Automated:** ✓ Runs weekly + daily without manual intervention.
2. **Understandable:** ✓ Layperson understands rate pressure in < 5 seconds via plain English verdicts.
3. **Accurate:** ✓ All metrics normalized via ratios/Z-scores, no nominal currency values.

---
*Last updated: 2026-02-24 after v1.1 milestone completion*
