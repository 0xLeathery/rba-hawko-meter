# Milestones

## v1.0 MVP (Shipped: 2026-02-24)

**Phases completed:** 7 phases, 19 plans, 8 tasks

**Key accomplishments:**
- Automated data pipeline ingesting 5 ABS indicators + RBA cash rate via weekly GitHub Actions
- Interactive dark-theme dashboard with Plotly.js rate chart (1Y/5Y/10Y), live RBA meeting countdown, deployed on Netlify
- Z-score normalization engine (median/MAD) transforming diverse economic metrics into 0-100 gauge scale
- Hawk-O-Meter with hero semicircle gauge + 6 individual bullet gauges (Blue/Grey/Red colorblind-accessible scheme)
- Mortgage impact calculator with Decimal.js precision, scenario slider, ASIC RG 244 compliance
- Plain English UX overhaul — layperson-friendly labels, data quality guards, neutral verdict language
- ASX Futures integration with daily CI/CD automation and graceful degradation

**Known Gaps:**
- PIPE-03: CoreLogic scraper placeholder (graceful degradation)
- PIPE-04: NAB capacity survey placeholder (graceful degradation)
- HAWK-04: ASX endpoints 404 (external API change, implemented with graceful degradation)

**Stats:**
- Timeline: 2026-02-04 → 2026-02-24 (20 days)
- Commits: 81
- LOC: ~5,900 (2,683 Python + 2,750 JS + 468 HTML)
- Tests: 24 Playwright tests (100% pass)

---


## v1.1 Full Indicator Coverage (Shipped: 2026-02-24)

**Phases completed:** 3 phases, 6 plans, ~16 tasks

**Key accomplishments:**
- ASX futures multi-meeting probability table with traffic light stacked bars, CI freshness assertion, and 14d/30d staleness detection
- ABS RPPI housing gauge with YoY % directional labels, quarter format, source attribution, and stale_display override
- Cotality HVI PDF scraper with 4-candidate URL try-list, pdfplumber extraction, hybrid normalization fallback in ratios.py
- NAB capacity utilisation scraper with tag archive URL discovery, HTML regex extraction, PDF fallback, and 12-month backfill
- Business Conditions gauge with trend label format ("83.6% — ABOVE avg, STEADY (Jan 2026)"), 45-day staleness threshold, and inflation pressure framing
- Dashboard coverage moved from "5 of 8" to "7 of 8" indicators — all 3 data source gaps closed (ASX, Housing, NAB)

**Stats:**
- Timeline: 2026-02-24 (1 day)
- Files modified: 37
- Lines changed: +5,383 / -300
- Codebase total: ~6,276 LOC (3,227 Python + 3,049 JS)
- Tests: 28 Playwright tests (100% pass)
- Git range: feat(08-01) → feat(10-02)

---

