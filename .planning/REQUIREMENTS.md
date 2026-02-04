# Requirements: RBA Hawk-O-Meter

**Defined:** 2026-02-04
**Core Value:** "Data, not opinion." Empowers laypeople to understand interest rate drivers without relying on media sensationalism or biased advice.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Data Pipeline

- [ ] **PIPE-01**: System ingests RBA cash rate data via `readabs` on a weekly schedule
- [ ] **PIPE-02**: System ingests ABS economic indicators (CPI, retail trade, employment) via `readabs`
- [ ] **PIPE-03**: System scrapes CoreLogic median dwelling price data
- [ ] **PIPE-04**: System scrapes NAB capacity utilisation survey data
- [ ] **PIPE-05**: System appends raw data to `raw_history.csv` with timestamped rows
- [ ] **PIPE-06**: System normalizes all metrics to ratios (price-to-income, per-capita, real volume) — no nominal currency values
- [ ] **PIPE-07**: System calculates Z-scores using 10-year rolling window (mean and standard deviation)
- [ ] **PIPE-08**: System maps Z-scores to 0-100 gauge scale
- [ ] **PIPE-09**: System outputs `status.json` with overall hawk score, per-gauge values, and metadata
- [ ] **PIPE-10**: GitHub Action runs weekly (Monday) and commits updated data back to repo
- [ ] **PIPE-11**: System falls back to previous week's data if a scraper fails, logging a warning

### Dashboard Display

- [ ] **DASH-01**: User can see the current RBA cash rate prominently displayed
- [ ] **DASH-02**: User can view an interactive historical rate chart (1yr/5yr/10yr) with hover details
- [ ] **DASH-03**: User can see the next RBA meeting date with countdown
- [ ] **DASH-04**: Dashboard is fully responsive on mobile devices (charts stack/scale)
- [ ] **DASH-05**: Every data point cites its source (RBA, ABS, CoreLogic, NAB, ASX)
- [ ] **DASH-06**: Legal disclaimer ("General Information Only") is visible on every page

### Hawk-O-Meter

- [ ] **HAWK-01**: User can see an overall "Hawk Score" gauge (0-100, traffic light: Blue/Grey/Red)
- [ ] **HAWK-02**: User can see individual gauges for each metric (Housing, Jobs, Spending, Capacity, Inflation)
- [ ] **HAWK-03**: Each gauge shows a plain-text interpretation (e.g., "Prices rising faster than wages")
- [ ] **HAWK-04**: User can see ASX Futures implied probability of next rate move
- [ ] **HAWK-05**: Overall verdict text summarizes the hawk/dove stance in plain English

### Calculator

- [ ] **CALC-01**: User can enter their mortgage details (loan amount, remaining term, current rate)
- [ ] **CALC-02**: User can see the monthly repayment impact of a 0.25% rate change
- [ ] **CALC-03**: User can use a slider to explore rate scenarios (e.g., "What if rates hit 6%?")
- [ ] **CALC-04**: Calculator stores inputs in localStorage (no login required)

### Compliance

- [ ] **COMP-01**: All language uses neutral framing ("Market Expectation" not "Prediction")
- [ ] **COMP-02**: No content constitutes personal or general financial advice per ASIC RG 244
- [ ] **COMP-03**: Disclaimer footer is present and visible without scrolling on page load

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Sentiment Analysis

- **SENT-01**: System performs NLP analysis of RBA minutes to extract sentiment score
- **SENT-02**: User can see a "Sentiment Timeline" showing RBA language shifts over time
- **SENT-03**: User can see word clouds from RBA minutes highlighting key themes

### Notifications

- **NOTF-01**: User can subscribe to email alerts for rate changes
- **NOTF-02**: User can receive push notifications for RBA meeting outcomes

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| "You should fix" recommendations | Constitutes personal financial advice — requires AFS License (ASIC RG 244) |
| Direct lender/product comparisons | Shifts from "macro tool" to "lead gen site" — dilutes unbiased value |
| "Best rate" tables | Quickly outdated, biased by referral fees |
| User accounts/login | Increases friction and privacy liability — stateless app preferred |
| Opinionated blog/news | Violates "Data, not opinion" core value |
| Real-time data updates | Weekly cadence is sufficient for macro indicators; real-time adds cost/complexity |
| Mobile native app | Web-first, responsive design sufficient for v1 |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| PIPE-01 | — | Pending |
| PIPE-02 | — | Pending |
| PIPE-03 | — | Pending |
| PIPE-04 | — | Pending |
| PIPE-05 | — | Pending |
| PIPE-06 | — | Pending |
| PIPE-07 | — | Pending |
| PIPE-08 | — | Pending |
| PIPE-09 | — | Pending |
| PIPE-10 | — | Pending |
| PIPE-11 | — | Pending |
| DASH-01 | — | Pending |
| DASH-02 | — | Pending |
| DASH-03 | — | Pending |
| DASH-04 | — | Pending |
| DASH-05 | — | Pending |
| DASH-06 | — | Pending |
| HAWK-01 | — | Pending |
| HAWK-02 | — | Pending |
| HAWK-03 | — | Pending |
| HAWK-04 | — | Pending |
| HAWK-05 | — | Pending |
| CALC-01 | — | Pending |
| CALC-02 | — | Pending |
| CALC-03 | — | Pending |
| CALC-04 | — | Pending |
| COMP-01 | — | Pending |
| COMP-02 | — | Pending |
| COMP-03 | — | Pending |

**Coverage:**
- v1 requirements: 29 total
- Mapped to phases: 0
- Unmapped: 29 ⚠️

---
*Requirements defined: 2026-02-04*
*Last updated: 2026-02-04 after initial definition*
