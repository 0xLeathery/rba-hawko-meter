# Project: RBA Hawk-O-Meter

## What This Is
An automated, unbiased economic dashboard for Australian mortgage holders. Ingests raw economic data from ABS, RBA, ASX, CoreLogic/Cotality, and NAB, normalizes it via Z-scores, and presents interest rate pressure through traffic-light gauges, a mortgage impact calculator, and plain English interpretations. 7 of 8 indicators active with full data coverage. Live at Netlify with daily/weekly automated data updates via GitHub Actions. All 13 pipeline/ modules covered at 85%+ by 421 unit tests with per-module enforcement in pre-push hook. Dashboard features a hero verdict section with animated hawk score, verdict explanation showing which indicators drive the score, and polished visual hierarchy with accessibility guards.

## Core Value
**"Data, not opinion."**
Empowers laypeople to understand interest rate drivers without relying on media sensationalism or biased advice from banks/brokers.

## Constraints
- **Zero Cost Hosting:** Must run on Netlify (frontend) and GitHub Actions (backend).
- **Maintenance:** "Silent Automation" preferred, though scraping maintenance is accepted.
- **Data Integrity:** Strictly NO nominal currency values in gauges to avoid inflation bias; must use ratios/per-capita metrics.
- **ASIC Compliance:** All language must use neutral framing per RG 244. No personal or general financial advice.

## Current Milestone: v5.0 Direction & Momentum

**Goal:** Transform the dashboard from a point-in-time snapshot into a momentum tracker that shows direction of change, enables organic sharing, and lays the foundation for newsletter-based monetization via mortgage broker affiliate links.

**Target features:**
- Snapshot archiving + `previous_value` in status.json (pipeline temporal layer)
- Delta badges on indicator cards showing direction of change
- Sparklines from existing `history` arrays on indicator cards
- OG meta tags + share button for organic distribution
- Historical hawk score chart

## Scope
- **Backend:** Python-based ETL pipeline (ingest → normalize → Z-score → status.json).
- **Frontend:** Static HTML/JS dashboard using Plotly.js for gauges, Tailwind CSS, Decimal.js for calculator, CountUp.js for score animation.
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
- ✓ FOUND-01 through FOUND-05: Test foundation (pyproject.toml, fixtures, isolation, tiering, dev deps) — v2.0
- ✓ UNIT-01 through UNIT-05: Python unit tests (Z-score, gauge, ratios, CSV handler, schema) — v2.0
- ✓ LINT-01 through LINT-04: Linting baseline (ruff + ESLint, zero violations, npm scripts) — v2.0
- ✓ LIVE-01 through LIVE-04: Live verification (ABS/RBA/ASX APIs, scrapers, verify_summary.py) — v2.0
- ✓ HOOK-01 through HOOK-04: Pre-push hook + unified npm scripts (test:fast, verify) — v2.0
- ✓ INFRA-01 through INFRA-04: Test infrastructure (pytest-cov, pytest-mock, fixtures, check_coverage.py) — v3.0
- ✓ INGEST-01 through INGEST-06: Ingest module unit tests (abs_data, rba_data, asx_futures, corelogic, nab, http_client at 85%+) — v3.0
- ✓ ORCH-01 through ORCH-02: Orchestration tests (engine.py 96%, main.py 93%) — v3.0
- ✓ ENFORCE-01 through ENFORCE-02: Coverage enforcement wired into npm test:fast and lefthook pre-push hook — v3.0
- ✓ HERO-01 through HERO-06: Hero section DOM restructure with Inter font, zone border, score display, freshness badge, fadeSlideIn animation — v4.0
- ✓ EXPL-01 through EXPL-04: Verdict explanation component with ranked hawkish/dovish indicators and ASIC-compliant hedged language — v4.0
- ✓ POLX-01 through POLX-04: Visual polish — typography hierarchy, zone colour audit, spacing standardisation, mobile above-fold — v4.0
- ✓ ANIM-01 through ANIM-02: CountUp.js hawk score animation + Plotly gauge sweep with prefers-reduced-motion guards — v4.0

### Active

(Defining requirements for v5.0 Direction & Momentum — see REQUIREMENTS.md)

### Out of Scope
| Feature | Reason |
|---------|--------|
| "You should fix" recommendations | Constitutes personal financial advice — requires AFS License (ASIC RG 244) |
| Direct lender/product comparisons | Shifts from "macro tool" to "lead gen site" — dilutes unbiased value |
| "Best rate" tables | Quickly outdated, biased by referral fees |
| User accounts/login | Increases friction and privacy liability — stateless app preferred |
| Opinionated blog/news | Violates "Data, not opinion" core value |
| Real-time data updates | Weekly cadence is sufficient for macro indicators; real-time adds cost/complexity |
| Mobile native app | Web-first, responsive design sufficient |
| GitHub Actions CI test workflow | Local CI covers pre-push; GHA test integration is a future milestone |
| Type checking (mypy) | Ruff catches most issues for this codebase size |
| Mutation testing | Overkill for current codebase size |
| Integration tests (E2E pipeline) | Future milestone — local mocked unit tests are sufficient now |
| Dark/light theme toggle | Dual Tailwind class definitions + Plotly rewrites — high complexity, low value |
| Tailwind v4 CDN upgrade | Incompatible config format; no feature benefit |
| Plotly.js v3 upgrade | Breaking changes to title API; no feature benefit |

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
| **pyproject.toml config hub** | Single source for pytest + ruff config | ✓ testpaths, pythonpath, markers, ruff rules all in one file |
| **Autouse DATA_DIR isolation** | Tests must never read/write production data/ | ✓ monkeypatch + tmp_path autouse fixture |
| **Socket-level network blocking** | Prevent accidental HTTP in unit tests | ✓ socket.socket monkeypatch raises RuntimeError |
| **Robust median/MAD known-answer tests** | Hand-calculated derivations catch formula regressions | ✓ 60+ parametrized tests with documented math |
| **jsonschema StrictValidator** | hawk_score must be Python int, not float | ✓ Custom type_checker enforces int constraint |
| **ESLint v10 flat config** | No .eslintrc support in v10; IIFE modules need sourceType:script | ✓ Zero violations, max-len 88 matching Python |
| **Lefthook parallel pre-push** | Lint + test in parallel for <10s gate | ✓ 3 parallel commands, 30s timeout, silent on success |
| **Late-bound DATA_DIR** | Import-time binding breaks test isolation | ✓ All 7 modules use pipeline.config.DATA_DIR at call time |
| **Three-tier npm verify** | Fast/live/Playwright as distinct tiers | ✓ verify:fast && verify:live && verify:playwright && verify_summary |
| **Patch at import site** | Wrong patch target gives RuntimeError even with mock in place | ✓ `pipeline.ingest.<module>.create_session`, never the source module |
| **engine_data_dir fixture** | `pipeline.config.STATUS_OUTPUT` not isolated by autouse fixture | ✓ Explicit fixture patches `pipeline.normalize.engine.STATUS_OUTPUT` |
| **pytest.raises(SystemExit)** | `main.run_pipeline()` calls `sys.exit(1)` — kills test runner without wrap | ✓ Critical failure path caught with `exc_info.value.code == 1` assertion |
| **MockDatetime class** | `@freeze_time` unavailable; need strptime/strftime delegation | ✓ MockDatetime freezes now()/utcnow() while delegating other methods |
| **pdfplumber via sys.modules** | Lazy import makes pdfplumber unreachable via normal patch path | ✓ Mock injected via sys.modules before module import |
| **No --cov-fail-under in addopts** | Global threshold hides per-module gaps | ✓ Per-module enforcement in check_coverage.py --min flag |
| **Double rAF for Plotly after DOM restructure** | Single rAF insufficient; Plotly needs layout pass before resize | ✓ Nested requestAnimationFrame + Plotly.Plots.resize prevents zero-width |
| **element.style for zone colours** | Tailwind CDN silently drops dynamically concatenated classes | ✓ All zone colours set via element.style with hex from getZoneColor() |
| **CountUp.js via CDN with fallback** | NPM not available (no build system); CDN failure must be graceful | ✓ jsDelivr CDN with static textContent fallback on load failure |
| **rAF stepping for gauge sweep** | Plotly.animate() doesn't support smooth transitions for indicator traces | ✓ requestAnimationFrame + Plotly.react() stepping over 1500ms |
| **Shared reducedMotion check** | Avoid repeated matchMedia calls across 3 animations | ✓ Single check at top of .then() handler, shared by CountUp/gauge/fadeSlideIn |

## Context

Shipped v4.0 with ~9,514 Python LOC (includes 421 unit tests + 9 live tests). JS at ~3,664 LOC (up from 2,510 after hero + explanation + animation additions).
Tech stack: Python (pandas, numpy, requests, beautifulsoup4, pdfplumber, pytest, pytest-cov, pytest-mock, responses, ruff), Vanilla JS (ESLint v10), Tailwind CSS v3, Plotly.js 2.35.2, Decimal.js, CountUp.js 2.9.0, Inter font (Google Fonts CDN).
Test suite: 421 pytest unit tests + 9 live tests + 28 Playwright tests (100% pass).
Coverage: All 13 pipeline/ modules at 85%+ (range: 90-100%). Coverage gate active in pre-push hook and npm test:fast.
Quality gate: Lefthook pre-push hook (lint + unit tests + coverage check in <45s), three-tier npm verify.
7 of 8 economic indicators active (ASX futures displayed separately as 8th). All data source gaps closed.
Dashboard: Hero verdict section with animated hawk score (CountUp.js), verdict explanation with ranked indicators, zone-coloured visual hierarchy, and prefers-reduced-motion accessibility guards.
Automated data updates: weekly pipeline (Monday) + daily ASX futures (weekdays) via GitHub Actions.

## Success Criteria
1. **Fully Automated:** ✓ Runs weekly + daily without manual intervention.
2. **Understandable:** ✓ Layperson understands rate pressure in < 5 seconds via plain English verdicts and indicator explanations.
3. **Accurate:** ✓ All metrics normalized via ratios/Z-scores, no nominal currency values.

---
*Last updated: 2026-02-26 after v5.0 milestone started*
