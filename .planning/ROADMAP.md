# Roadmap: RBA Hawk-O-Meter

## Milestones

- ✅ **v1.0 MVP** — Phases 1-7 (shipped 2026-02-24)
- ✅ **v1.1 Full Indicator Coverage** — Phases 8-10 (shipped 2026-02-24)
- ✅ **v2.0 Local CI & Test Infrastructure** — Phases 11-17 (shipped 2026-02-25)
- ✅ **v3.0 Full Test Coverage** — Phases 18-20 (shipped 2026-02-25)

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
