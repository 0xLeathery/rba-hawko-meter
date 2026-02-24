# Project: RBA Hawk-O-Meter

## What This Is
An automated, unbiased economic dashboard for Australian mortgage holders. Ingests raw economic data from ABS and RBA, normalizes it via Z-scores, and presents interest rate pressure through traffic-light gauges, a mortgage impact calculator, and plain English interpretations. Live at Netlify with daily/weekly automated data updates via GitHub Actions.

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
- **Data Sources:** ABS (official — CPI, employment, wages, spending, building approvals), RBA (official — cash rate, meetings), ASX (JSON API — futures), CoreLogic (placeholder), NAB (placeholder).

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

## Current Milestone: v1.1 Full Indicator Coverage

**Goal:** Close all 3 remaining data source gaps so the dashboard reports "Based on 8 of 8 indicators."

**Target features:**
- CoreLogic median dwelling prices via free public data scraping (quarterly reports/media releases)
- NAB capacity utilisation via quarterly business survey PDF parsing
- ASX rate futures via working endpoint discovery and integration

### Active
- [ ] PIPE-03: CoreLogic median dwelling price scraping (free public sources — quarterly reports, media releases)
- [ ] PIPE-04: NAB capacity utilisation survey (PDF parsing from quarterly business survey)
- [ ] HAWK-04: ASX Futures probability display (find current working endpoint)

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
| **Scraping** | Official APIs don't cover all leading indicators | ⚠️ CoreLogic/NAB still placeholders |
| **No Framework** | React/Vue is overkill for single-page dashboard | ✓ Vanilla JS + Tailwind + Plotly |
| **Blue/Grey/Red gauges** | 8% of males have red-green color deficiency | ✓ Colorblind-accessible |
| **IIFE modules** | Encapsulate private state without a build system | ✓ Clean module pattern |
| **Decimal.js for calculator** | IEEE 754 precision loss with native JS floats | ✓ Exact mortgage math |
| **ASX futures as benchmark** | Market-derived, not an economic indicator | ✓ Excluded from hawk score, displayed separately |
| **Plain English labels** | "RATES LIKELY FALLING" not "DOVISH" | ✓ Layperson clarity |

## Context

Shipped v1.0 with ~5,900 LOC (2,683 Python + 2,750 JS + 468 HTML).
Tech stack: Python (pandas, numpy, requests, beautifulsoup4), Vanilla JS, Tailwind CSS, Plotly.js, Decimal.js.
24 Playwright tests (100% pass).
5 of 8 economic indicators active. 3 placeholder (CoreLogic, NAB, ASX — all external data source issues).
Dashboard clearly communicates coverage: "Based on 5 of 8 indicators".
Hawk Score at launch: 41.8/100 (Balanced).

## Success Criteria
1. **Fully Automated:** ✓ Runs weekly + daily without manual intervention.
2. **Understandable:** ✓ Layperson understands rate pressure in < 5 seconds via plain English verdicts.
3. **Accurate:** ✓ All metrics normalized via ratios/Z-scores, no nominal currency values.

---
*Last updated: 2026-02-24 after v1.1 milestone initialization*
