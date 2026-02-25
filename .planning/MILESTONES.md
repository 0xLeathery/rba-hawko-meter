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


## v2.0 Local CI & Test Infrastructure (Shipped: 2026-02-25)

**Phases completed:** 7 phases, 11 plans

**Key accomplishments:**
- Test foundation with pyproject.toml config hub + isolated test harness (autouse DATA_DIR/network fixtures, fixture CSVs from production snapshots)
- 60+ pytest unit tests covering Z-score, gauge, ratios, CSV handler, and jsonschema validation — the full mathematical core guarded by deterministic tests
- Dual-language linting baseline: Ruff (Python) + ESLint v10 (JS) at zero violations with unified npm scripts (lint:py, lint:js, lint)
- Live verification suite: 9 @pytest.mark.live tests for all data sources + verify_summary.py ASCII table with exit code signalling
- Lefthook pre-push quality gate running lint + unit tests in parallel, blocking broken pushes in <10s
- DATA_DIR late-binding fix across 7 modules with environment variable override support

**Stats:**
- Timeline: 2026-02-24 → 2026-02-25 (2 days)
- Commits: 64
- Files modified: 95
- Lines changed: +13,776 / -1,190
- Codebase total: ~8,087 LOC (5,577 Python + 2,510 JS), 1,984 test LOC
- Test suite: 60+ pytest unit tests + 9 live tests + 28 Playwright tests

---


## v3.0 Full Test Coverage (Shipped: 2026-02-25)

**Phases completed:** 3 phases, 6 plans

**Key accomplishments:**
- pytest-cov auto-measurement wired into every `pytest` run — terminal report + `.coverage.json` generated without extra flags, 28% baseline captured
- 10 scraper fixture files covering all 5 data sources (happy-path + error variants) plus `scripts/check_coverage.py` per-module enforcement with `--min` threshold and diff table output
- 132 ingest unit tests across all 6 pipeline ingest modules (http_client, abs_data, rba_data, asx_futures, corelogic, nab) — zero real HTTP requests, fully socket-blocked
- 117 engine.py tests at 96% coverage with `engine_data_dir` fixture isolating `STATUS_OUTPUT`; 16 main.py tests covering all tier behaviors and `sys.exit(1)` contract
- All 13 `pipeline/` modules at 85%+ coverage (range: 90–100%) — 411 total unit tests passing
- Coverage enforcement wired into `npm run test:fast` and lefthook pre-push hook — coverage regression impossible to push undetected

**Stats:**
- Timeline: 2026-02-25 (1 day)
- Commits: 26
- Files modified: 100
- Lines changed: +9,779
- Codebase total: ~9,514 Python LOC
- Test suite: 411 pytest unit tests + 9 live tests + 28 Playwright tests

---

