# Roadmap: RBA Hawk-O-Meter

## Milestones

- ✅ **v1.0 MVP** — Phases 1-7 (shipped 2026-02-24)
- ✅ **v1.1 Full Indicator Coverage** — Phases 8-10 (shipped 2026-02-24)
- ✅ **v2.0 Local CI & Test Infrastructure** — Phases 11-17 (shipped 2026-02-25)
- ✅ **v3.0 Full Test Coverage** — Phases 18-20 (shipped 2026-02-25)
- 🚧 **v4.0 Dashboard Visual Overhaul** — Phases 21-23 (in progress)

## Phases

<details>
<summary>✅ v1.0 MVP (Phases 1-7) — SHIPPED 2026-02-24</summary>

7 phases, 19 plans completed. Full details in milestones/v1.0-ROADMAP.md.

Delivered: Automated data pipeline (5 ABS indicators + RBA cash rate), interactive dark-theme dashboard with Plotly.js, Z-score normalization engine, Hawk-O-Meter gauges, mortgage calculator, ASIC-compliant plain English UX, daily/weekly GitHub Actions automation.

</details>

<details>
<summary>✅ v1.1 Full Indicator Coverage (Phases 8-10) — SHIPPED 2026-02-24</summary>

3 phases, 6 plans completed. Full details in milestones/v1.1-ROADMAP.md.

Delivered: ASX futures multi-meeting probability table, ABS RPPI + Cotality HVI housing gauge with fallback hierarchy, NAB capacity utilisation scraper with URL discovery and PDF fallback, Business Conditions trend label, dashboard coverage at 7 of 8 indicators.

</details>

<details>
<summary>✅ v2.0 Local CI & Test Infrastructure (Phases 11-17) — SHIPPED 2026-02-25</summary>

7 phases, 11 plans completed. Full details in milestones/v2.0-ROADMAP.md.

Delivered: Test foundation (pyproject.toml + isolated fixtures), 60+ pytest unit tests guarding mathematical core, dual-language linting (ruff + ESLint v10) at zero violations, live verification suite for all data sources, lefthook pre-push quality gate in <10s, DATA_DIR late-binding fix with env var override.

</details>

<details>
<summary>✅ v3.0 Full Test Coverage (Phases 18-20) — SHIPPED 2026-02-25</summary>

3 phases, 6 plans completed. Full details in milestones/v3.0-ROADMAP.md.

Delivered: pytest-cov auto-measurement on every run, 10 scraper fixture files for all 5 data sources, 411 unit tests covering all 13 pipeline/ modules at 85%+, per-module coverage enforcement in npm test:fast and lefthook pre-push hook.

</details>

### 🚧 v4.0 Dashboard Visual Overhaul (In Progress)

**Milestone Goal:** Transform Hawk-O-Meter from data-dense dashboard into a polished, shareable product where the verdict and hawk score dominate the above-the-fold view.

## Phase Details

### Phase 21: Hero HTML Restructure
**Goal**: Users see the verdict and hawk score as the dominant above-the-fold experience with a stable, correctly-sized DOM ready for JS and CSS work
**Depends on**: Phase 20 (v3.0 complete)
**Requirements**: HERO-01, HERO-02, HERO-03, HERO-04, HERO-05, HERO-06
**Success Criteria** (what must be TRUE):
  1. User sees the verdict label as the largest above-the-fold text element on any viewport from 375px to 1440px, without scrolling
  2. User sees the hawk score as a prominent number ("38/100") and the scale explainer ("0 = Strongly Dovish → 100 = Strongly Hawkish") alongside the verdict inside the hero card — both visible above the fold
  3. User sees a data freshness badge inside the hero card and a zone-coloured accent border that changes colour with the hawk/dove/neutral zone
  4. The Plotly hawk gauge renders at its correct width on all tested viewports after the DOM restructure — no zero-width render regression
  5. All 28 Playwright tests pass after the structural HTML change
**Plans**: 1 plan, 1 wave

Plans:
- [x] 21-01: Hero section DOM restructure, Inter font, keyframes, tailwind.config extension

### Phase 22: Verdict Explanation Component
**Goal**: Users understand which indicators are pushing the hawk score up or down via a plain-English, ASIC-compliant explanation section
**Depends on**: Phase 21
**Requirements**: EXPL-01, EXPL-02, EXPL-03, EXPL-04
**Success Criteria** (what must be TRUE):
  1. User sees a plain-English list of the top 3 hawkish indicators driving the score up, rendered below the hero on page load
  2. User sees a plain-English list of the top 2 dovish indicators pulling the score down — neutral indicators are absent from both lists
  3. All explanation copy uses hedged language ("tends to", "historically associated with", "the data is consistent with") with no predictive statements or recommendations
  4. The explanation section updates correctly with real data from status.json and uses zone colours via element.style (not Tailwind class concatenation)
**Plans**: 1 plan, 1 wave

Plans:
- [x] 22-01: renderVerdictExplanation() in interpretations.js, wire in gauge-init.js

### Phase 23: Visual Polish and Animations
**Goal**: Users experience a visually cohesive dashboard with consistent typography, spacing, and colour hierarchy, plus animated entry effects on the hero score and gauge
**Depends on**: Phase 22
**Requirements**: POLX-01, POLX-02, POLX-03, POLX-04, ANIM-01, ANIM-02
**Success Criteria** (what must be TRUE):
  1. User perceives a clear typography hierarchy: verdict label is largest, hawk score is prominent, secondary labels are visually distinct, body text and metadata are readable but subordinate
  2. Zone colour (blue/grey/red) appears on exactly three element types — verdict label, hero card border, explanation section headings — and nowhere else on the dashboard
  3. User on a 375px phone sees verdict and score above the fold with no layout congestion and consistent spacing across all dashboard sections
  4. User sees the hawk score count up from 0 to the live value on page load, with the Plotly gauge sweeping from 0 to the live score — both animations respect prefers-reduced-motion
**Plans**: TBD

Plans:
- [ ] 23-01: CSS audit, typography hierarchy, spacing standardisation, CountUp.js, gauge sweep animation

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1-7. MVP Phases | v1.0 | 19/19 | Complete | 2026-02-24 |
| 8. ASX Futures Live Data | v1.1 | 2/2 | Complete | 2026-02-24 |
| 9. Housing Prices Gauge | v1.1 | 2/2 | Complete | 2026-02-24 |
| 10. NAB Capacity Utilisation Gauge | v1.1 | 2/2 | Complete | 2026-02-24 |
| 11. Test Foundation | v2.0 | 2/2 | Complete | 2026-02-25 |
| 12. Python Unit Tests | v2.0 | 2/2 | Complete | 2026-02-25 |
| 13. Linting Baseline | v2.0 | 2/2 | Complete | 2026-02-25 |
| 14. Live Verification | v2.0 | 1/1 | Complete | 2026-02-25 |
| 15. Pre-Push Hook | v2.0 | 1/1 | Complete | 2026-02-25 |
| 16. Verify Linting Baseline | v2.0 | 1/1 | Complete | 2026-02-25 |
| 17. Fix DATA_DIR & Verify Chain | v2.0 | 2/2 | Complete | 2026-02-25 |
| 18. Test Infrastructure | v3.0 | 2/2 | Complete | 2026-02-25 |
| 19. Ingest Module Tests | v3.0 | 2/2 | Complete | 2026-02-25 |
| 20. Orchestration Tests and Enforcement | v3.0 | 2/2 | Complete | 2026-02-25 |
| 21. Hero HTML Restructure | v4.0 | Complete    | 2026-02-25 | 2026-02-26 |
| 22. Verdict Explanation Component | v4.0 | 1/1 | Complete | 2026-02-26 |
| 23. Visual Polish and Animations | v4.0 | 0/1 | Not started | - |
