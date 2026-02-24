# Roadmap: RBA Hawk-O-Meter

## Milestones

- ✅ **v1.0 MVP** - Phases 1-7 (shipped 2026-02-24)
- 🚧 **v1.1 Full Indicator Coverage** - Phases 8-10 (in progress)

## Phases

<details>
<summary>✅ v1.0 MVP (Phases 1-7) - SHIPPED 2026-02-24</summary>

7 phases, 19 plans, 8 tasks completed. Full details in MILESTONES.md.

Delivered: Automated data pipeline (5 ABS indicators + RBA cash rate), interactive dark-theme dashboard with Plotly.js, Z-score normalization engine, Hawk-O-Meter gauges, mortgage calculator, ASIC-compliant plain English UX, daily/weekly GitHub Actions automation.

</details>

### 🚧 v1.1 Full Indicator Coverage (In Progress)

**Milestone Goal:** Close all 3 remaining data source gaps. Dashboard reports "Based on 8 of 8 indicators" instead of "5 of 8."

#### Phase 8: ASX Futures Live Data

**Goal**: The "What Markets Expect" section displays fresh, multi-meeting probability data sourced from a verified working endpoint
**Depends on**: Phase 7 (v1.0 complete)
**Requirements**: ASX-01, ASX-02, ASX-03, ASX-04
**Success Criteria** (what must be TRUE):
  1. The ASX MarkitDigital endpoint is confirmed working in GitHub Actions CI and `asx_futures.csv` contains rows dated within the past 7 days
  2. The dashboard "What Markets Expect" section shows an implied rate percentage and cut/hold/hike probability bars drawn from fresh data, not placeholders
  3. The pipeline logs a warning (and pipeline still exits cleanly) when `asx_futures.csv` has no rows newer than 14 days
  4. The dashboard displays probability bars for the next 3-4 upcoming RBA meetings, not just the soonest one
**Plans**: 2 plans

Plans:
- [ ] 08-01-PLAN.md — Pipeline staleness detection + multi-meeting engine extension + CI freshness assertion
- [ ] 08-02-PLAN.md — Frontend multi-meeting table with traffic light stacked bars + test updates

---

#### Phase 9: Housing Prices Gauge

**Goal**: The housing gauge is active and shows dwelling price YoY % change, with a clear fallback hierarchy between ABS RPPI and Cotality HVI data
**Depends on**: Phase 8
**Requirements**: HOUS-01, HOUS-02, HOUS-03, HOUS-04
**Success Criteria** (what must be TRUE):
  1. `corelogic_housing.csv` is populated via the ABS RPPI SDMX API and the housing gauge renders on the dashboard (indicator count moves from 6 to 7 of 8)
  2. When housing data is older than 90 days, the gauge label includes a staleness note such as "(data to Dec 2021)" visible to the user
  3. The Cotality HVI PDF scraper runs monthly and appends current dwelling price data to `corelogic_housing.csv`
  4. The pipeline uses Cotality data when available and falls back to ABS RPPI when the Cotality scrape fails or returns no new data
**Plans**: 2 plans

Plans:
- [ ] 09-01-PLAN.md — ABS RPPI pipeline integration + housing gauge activation with directional labels, quarter format, source attribution
- [ ] 09-02-PLAN.md — Cotality HVI PDF scraper + fallback logic + dynamic source attribution (gated on ToS decision)

---

#### Phase 10: NAB Capacity Utilisation Gauge

**Goal**: The business confidence gauge is active and shows capacity utilisation percentage, sourced via URL-discovery-based HTML extraction with a PDF fallback
**Depends on**: Phase 9
**Requirements**: NAB-01, NAB-02, NAB-03, NAB-04, NAB-05
**Success Criteria** (what must be TRUE):
  1. `nab_capacity.csv` is populated with monthly capacity utilisation values and the business confidence gauge renders on the dashboard (indicator count reaches 8 of 8)
  2. The survey URL is discovered by crawling the NAB tag archive page, not constructed from a date template — a hardcoded URL pattern never appears in the scraper code
  3. The gauge label shows a trend indicator ("ABOVE long-run average of ~81%" or "BELOW long-run average of ~81%") based on the latest reading
  4. When HTML extraction fails for a given month, the scraper attempts PDF extraction and recovers the capacity utilisation figure without the pipeline failing
**Plans**: TBD

Plans:
- [ ] 10-01: TBD

---

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1-7. MVP Phases | v1.0 | 19/19 | Complete | 2026-02-24 |
| 8. ASX Futures Live Data | 2/2 | Complete   | 2026-02-24 | - |
| 9. Housing Prices Gauge | 1/2 | In Progress|  | - |
| 10. NAB Capacity Utilisation Gauge | v1.1 | 0/? | Not started | - |
