# Project: RBA Hawk-O-Meter

## What This Is

An automated, unbiased economic dashboard for Australian mortgage holders. Ingests public economic data from ABS, RBA, ASX, CoreLogic, and NAB, normalises each indicator as a Z-score against its 10-year history, then maps everything to a single 0–100 hawk score. Live at rbahawkometer.com.au with weekly + daily automated data updates via GitHub Actions. Static site on Netlify, Python pipeline, vanilla JS frontend with Plotly.js gauges.

## Core Value

**"Data, not opinion."** Empowers laypeople to understand interest rate drivers without relying on media sensationalism or biased advice from banks/brokers.

## Current State

Four milestones shipped (v1.0 MVP, v1.1 Full Indicator Coverage, v2.0 Local CI & Test Infrastructure, v3.0 Full Test Coverage, v4.0 Dashboard Visual Overhaul). Phase 24 (pipeline temporal layer — snapshot archiving and delta injection) shipped as part of v5.0. Phases 25-28 remain.

- 7 of 8 indicators active (housing and business_confidence scrapers currently failing in production — pre-existing)
- 431 pytest unit tests + 28 Playwright E2E tests, all passing
- 13 pipeline modules at 85%+ coverage, enforced by pre-push hook
- 2,895 lines of frontend JS across 8 IIFE modules
- Snapshot archive in place with 2 weekly snapshots accumulated
- Delta fields (`delta`, `delta_direction`, `previous_value`, `hawk_score_delta`) injected by pipeline but not yet consumed by frontend

## Architecture / Key Patterns

- **Pipeline:** Python 3.11+, pandas, numpy, requests, beautifulsoup4, pdfplumber. Three-tier failure handling (critical/important/optional). Tiered ingest → ratios → Z-scores → 0-100 gauge → status.json.
- **Frontend:** Vanilla JS IIFE modules (no build step, no ESM). Tailwind CSS v3 (CDN), Plotly.js 2.35.2, Decimal.js, CountUp.js 2.9.0. All colours via `element.style` hex (never Tailwind class concatenation). No innerHTML — createElement/textContent only.
- **Hosting:** Netlify (static, auto-deploy from main). GitHub Actions (weekly pipeline Monday + daily ASX futures weekdays).
- **Quality:** Lefthook pre-push (ruff + ESLint + pytest + coverage in parallel). Three-tier npm verify (fast/live/Playwright).
- **Data:** Flat JSON files in public/data/. Rolling snapshot archive in public/data/snapshots/ (52-file cap).

## Capability Contract

See `.gsd/REQUIREMENTS.md` for the explicit capability contract, requirement status, and coverage mapping.

## Milestone Sequence

- [ ] M001-pzg4u9: Direction & Momentum — Delta badges, sparklines, social sharing, historical chart, newsletter capture
