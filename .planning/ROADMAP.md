# Roadmap: RBA Hawk-O-Meter

## Milestones

- ✅ **v1.0 MVP** — Phases 1-7 (shipped 2026-02-24)
- ✅ **v1.1 Full Indicator Coverage** — Phases 8-10 (shipped 2026-02-24)
- ✅ **v2.0 Local CI & Test Infrastructure** — Phases 11-17 (shipped 2026-02-25)
- ✅ **v3.0 Full Test Coverage** — Phases 18-20 (shipped 2026-02-25)
- ✅ **v4.0 Dashboard Visual Overhaul** — Phases 21-23 (shipped 2026-02-26)
- 🚧 **v5.0 Direction & Momentum** — Phases 24-28 (in progress)

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

<details>
<summary>✅ v4.0 Dashboard Visual Overhaul (Phases 21-23) — SHIPPED 2026-02-26</summary>

3 phases, 3 plans completed. Full details in milestones/v4.0-ROADMAP.md.

Delivered: Hero section DOM restructure with Inter font and zone-coloured border, verdict explanation component with ASIC-compliant hedged language, typography hierarchy and spacing standardisation, CountUp.js animated hawk score, Plotly gauge sweep animation, prefers-reduced-motion accessibility guards.

</details>

### 🚧 v5.0 Direction & Momentum (In Progress)

**Milestone Goal:** Transform the dashboard from a point-in-time snapshot into a momentum tracker that shows direction of change, enables organic sharing, and lays the foundation for newsletter-based monetization.

- [ ] **Phase 24: Pipeline Temporal Layer** - Archive snapshots and inject delta fields into status.json
- [ ] **Phase 25: Indicator Card UI** - Delta badges and sparklines on every indicator card
- [ ] **Phase 26: Social Sharing** - OG meta tags and share button for organic distribution
- [ ] **Phase 27: Historical Chart + Narrative** - Hawk score history chart and weekly change summary
- [ ] **Phase 28: Newsletter Capture + Delivery** - Email signup form and automated weekly digest

## Phase Details

### Phase 24: Pipeline Temporal Layer
**Goal**: status.json contains direction-of-change data that all frontend momentum features can consume
**Depends on**: Phase 23 (v4.0 complete)
**Requirements**: SNAP-01, SNAP-02, SNAP-03, SNAP-04, SNAP-05
**Success Criteria** (what must be TRUE):
  1. After each weekly pipeline run, a dated snapshot file appears in public/data/snapshots/ and index.json is updated
  2. Each gauge entry in status.json contains previous_value, delta, and direction fields populated from the prior week's snapshot
  3. The overall block in status.json contains previous_hawk_score and hawk_score_delta
  4. On the first pipeline run (no prior snapshot), all delta fields are absent and the frontend handles this gracefully with no badge shown
  5. pipeline/normalize/archive.py has unit test coverage at 85%+ enforced by the existing coverage gate
**Plans**: TBD

Plans:
- [ ] 24-01: TBD

### Phase 25: Indicator Card UI
**Goal**: Every indicator card shows direction of change and recent trend history at a glance
**Depends on**: Phase 24
**Requirements**: DELT-01, DELT-02, DELT-03, DELT-04, SPRK-01, SPRK-02, SPRK-03, SPRK-04
**Success Criteria** (what must be TRUE):
  1. Each indicator card displays a directional badge (up/down/neutral) with magnitude when the delta is 5 or more gauge points
  2. The hero section displays the hawk score delta since the previous pipeline run
  3. Indicator cards with no previous value show no badge — they do not show an error or placeholder
  4. Each indicator card displays a Canvas 2D sparkline drawn from the existing history[] array, coloured by zone
  5. Indicators with fewer than 3 history points display "Building history..." text in place of the sparkline
**Plans**: TBD

Plans:
- [ ] 25-01: TBD

### Phase 26: Social Sharing
**Goal**: Users can share the dashboard and link previews display a branded card on all platforms
**Depends on**: Phase 24 (for stable URL; OG tags themselves are independent)
**Requirements**: SHARE-01, SHARE-02, SHARE-03, SHARE-04
**Success Criteria** (what must be TRUE):
  1. Pasting the dashboard URL into Facebook, LinkedIn, or iMessage shows a branded 1200x630 preview card with title and description
  2. Pasting the URL into Twitter/X shows a Twitter Card preview with title and description
  3. Tapping the share button on a mobile browser triggers the native share sheet
  4. Tapping the share button on a desktop browser copies the URL to the clipboard and shows a brief toast confirmation
**Plans**: TBD

Plans:
- [ ] 26-01: TBD

### Phase 27: Historical Chart + Narrative
**Goal**: Users can see how hawk score pressure has changed over time and read a factual summary of what moved this week
**Depends on**: Phase 24
**Requirements**: HIST-01, HIST-02, HIST-03, NARR-01, NARR-02
**Success Criteria** (what must be TRUE):
  1. The dashboard displays a Plotly line chart of weekly hawk score values with zone colour bands in the background
  2. When fewer than 4 snapshot data points exist, the chart container shows "Building history — check back next week" instead of a chart
  3. status.json contains a change_summary array of factual, template-generated sentences describing what moved since the previous pipeline run
  4. The dashboard renders a "What changed this week" section populated from change_summary, visible below the hero
**Plans**: TBD

Plans:
- [ ] 27-01: TBD

### Phase 28: Newsletter Capture + Delivery
**Goal**: Interested users can subscribe to a weekly data digest that delivers automatically after each pipeline run
**Depends on**: Phase 26 (share button establishes organic traffic before asking for subscriptions)
**Requirements**: NEWS-01, NEWS-02, NEWS-03, NEWS-04
**Success Criteria** (what must be TRUE):
  1. The dashboard displays an email signup form that submits via Netlify Forms with an unchecked consent checkbox by default
  2. Submitting the form redirects the user to a confirmation page; the submission appears in the Netlify Forms dashboard
  3. MailerLite is configured with double opt-in so subscribers receive a confirmation email before being added to the list
  4. A weekly digest email template in MailerLite auto-assembles hawk score, zone, top movers, and change narrative from status.json data
**Plans**: TBD

Plans:
- [ ] 28-01: TBD

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
| 21. Hero HTML Restructure | v4.0 | 1/1 | Complete | 2026-02-26 |
| 22. Verdict Explanation Component | v4.0 | 1/1 | Complete | 2026-02-26 |
| 23. Visual Polish and Animations | v4.0 | 1/1 | Complete | 2026-02-26 |
| 24. Pipeline Temporal Layer | v5.0 | 0/? | Not started | - |
| 25. Indicator Card UI | v5.0 | 0/? | Not started | - |
| 26. Social Sharing | v5.0 | 0/? | Not started | - |
| 27. Historical Chart + Narrative | v5.0 | 0/? | Not started | - |
| 28. Newsletter Capture + Delivery | v5.0 | 0/? | Not started | - |
