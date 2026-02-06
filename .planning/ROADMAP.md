# Roadmap: RBA Hawk-O-Meter

## Overview

This roadmap transforms raw economic data into a simple traffic-light dashboard for mortgage holders. We start by establishing a reliable automated data pipeline using GitHub Actions and "Git as Database", then build a static dashboard to display current rates and history, add the statistical engine to normalize metrics into Z-scores, implement the differentiating "Hawk-O-Meter" gauges, and finish with a personalized calculator and compliance polish. Each phase delivers verifiable user value while maintaining the "Data, not opinion" core principle.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Foundation & Data Pipeline** - Automated data ingestion skeleton
- [ ] **Phase 2: Core Dashboard** - Static UI with rate display and historical charts
- [ ] **Phase 3: Data Normalization & Z-Scores** - Statistical engine for metric transformation
- [ ] **Phase 4: Hawk-O-Meter Gauges** - Traffic-light visualization system
- [ ] **Phase 5: Calculator & Compliance** - Mortgage calculator and regulatory polish

## Phase Details

### Phase 1: Foundation & Data Pipeline
**Goal**: System reliably ingests economic data weekly and commits it to Git
**Depends on**: Nothing (first phase)
**Requirements**: PIPE-01, PIPE-02, PIPE-03, PIPE-04, PIPE-05, PIPE-10, PIPE-11, PIPE-12, PIPE-13
**Success Criteria** (what must be TRUE):
  1. GitHub Action runs weekly on Monday and commits updated data to the repo
  2. System ingests RBA cash rate data via readabs without manual intervention
  3. System ingests ABS economic indicators (CPI, retail trade, employment) via readabs
  4. System ingests ABS Wage Price Index and Building Approvals via readabs
  5. System scrapes CoreLogic and NAB data with fallback to previous week if scrapers fail
  5. All raw data appends to raw_history.csv with timestamped rows
**Plans**: 5 plans

Plans:
- [ ] 01-01-PLAN.md — Foundation scaffolding, shared utilities, RBA and ABS ingestors
- [ ] 01-02-PLAN.md — Web scrapers (CoreLogic, NAB, ASX Futures)
- [ ] 01-03-PLAN.md — Pipeline orchestrator, GitHub Actions workflows, historical backfill
- [ ] 01-04-PLAN.md — Gap closure: Building Approvals implementation (BA_GCCSA dataflow)
- [ ] 01-05-PLAN.md — Gap closure: GitHub Actions workflow validation and first execution

### Phase 2: Core Dashboard
**Goal**: Users can view current cash rate and historical trends on a live Netlify URL
**Depends on**: Phase 1
**Requirements**: DASH-01, DASH-02, DASH-03, DASH-04, DASH-05, DASH-06, COMP-03
**Success Criteria** (what must be TRUE):
  1. User can see the current RBA cash rate prominently displayed on the homepage
  2. User can view an interactive historical rate chart with 1yr/5yr/10yr toggles and hover details
  3. User can see the next RBA meeting date with countdown
  4. Dashboard is fully responsive on mobile devices with charts stacking appropriately
  5. Every data point displays its source citation (RBA, ABS, CoreLogic, NAB, ASX)
  6. Legal disclaimer ("General Information Only") is visible without scrolling on page load
**Plans**: 2 plans

Plans:
- [ ] 02-01-PLAN.md — Data transform script + HTML structure with dark theme and disclaimer
- [ ] 02-02-PLAN.md — Interactive JS modules (chart, countdown, data loading) + Netlify deployment

### Phase 3: Data Normalization & Z-Scores
**Goal**: System transforms diverse economic metrics into normalized 0-100 gauge values
**Depends on**: Phase 1
**Requirements**: PIPE-06, PIPE-07, PIPE-08, PIPE-09
**Success Criteria** (what must be TRUE):
  1. All metrics are normalized to ratios (price-to-income, per-capita, real volume) with no nominal currency values
  2. System calculates Z-scores using 10-year rolling window for mean and standard deviation
  3. System maps Z-scores to 0-100 gauge scale with documented transformation logic
  4. System outputs status.json with overall hawk score, per-gauge values, and metadata
**Plans**: 2 plans

Plans:
- [ ] 03-01-PLAN.md — Normalization engine core: config, weights.json, ratios.py, zscore.py, gauge.py
- [ ] 03-02-PLAN.md — Status.json generation engine and pipeline integration

### Phase 4: Hawk-O-Meter Gauges
**Goal**: Users can see visual traffic-light interpretation of interest rate pressure
**Depends on**: Phase 2, Phase 3
**Requirements**: HAWK-01, HAWK-02, HAWK-03, HAWK-04, HAWK-05
**Success Criteria** (what must be TRUE):
  1. User can see an overall "Hawk Score" gauge (0-100, traffic light: Blue/Grey/Red)
  2. User can see individual gauges for each metric (Housing, Jobs, Spending, Capacity, Inflation, Wages)
  3. Each gauge displays a plain-text interpretation (e.g., "Prices rising faster than wages")
  4. User can see ASX Futures implied probability of next rate move
  5. Overall verdict text summarizes the hawk/dove stance in plain English
**Plans**: 2 plans

Plans:
- [ ] 04-01-PLAN.md — Hero Hawk Score gauge (Plotly.js semicircle), ASX Futures probability table, overall verdict display
- [ ] 04-02-PLAN.md — Individual metric bullet gauges (Housing, Jobs, Spending, Capacity, Inflation, Wages) with data-driven interpretation text

### Phase 5: Calculator & Compliance
**Goal**: Users can personalize impact estimates and all content meets ASIC regulatory requirements
**Depends on**: Phase 4
**Requirements**: CALC-01, CALC-02, CALC-03, CALC-04, COMP-01, COMP-02
**Success Criteria** (what must be TRUE):
  1. User can enter mortgage details (loan amount, remaining term, current rate) and see calculated monthly repayment
  2. User can see the monthly repayment impact of a 0.25% rate change
  3. User can use a slider to explore rate scenarios (e.g., "What if rates hit 6%?")
  4. Calculator stores inputs in localStorage without requiring login
  5. All language uses neutral framing ("Market Expectation" not "Prediction")
  6. No content constitutes personal or general financial advice per ASIC RG 244
**Plans**: 2 plans

Plans:
- [ ] 05-01-PLAN.md — Mortgage impact calculator: input form, repayment math, scenario slider, localStorage persistence
- [ ] 05-02-PLAN.md — Compliance audit and polish: disclaimer verification, neutral language enforcement, ASIC compliance review, accessibility audit

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation & Data Pipeline | 3/5 | Gap closure | - |
| 2. Core Dashboard | 0/2 | Planned | - |
| 3. Data Normalization & Z-Scores | 0/2 | Planned | - |
| 4. Hawk-O-Meter Gauges | 0/2 | Planned | - |
| 5. Calculator & Compliance | 0/2 | Planned | - |
