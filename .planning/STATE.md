# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-24)

**Core value:** "Data, not opinion." Empowers laypeople to understand interest rate drivers without relying on media sensationalism or biased advice.
**Current focus:** Phase 8 — ASX Futures Live Data (v1.1 milestone start)

## Current Position

Phase: 8 of 10 (ASX Futures Live Data)
Plan: 2 of 2 in current phase (08-02 complete)
Status: In progress
Last activity: 2026-02-24 — 08-02 complete: multi-meeting ASX table with traffic light bars, placeholder fallback, updated Playwright tests

Progress: [███████░░░] 70% (7 of 10 phases complete — v1.0 shipped)

## Performance Metrics

**Velocity (v1.0):**
- Total plans completed: 19
- v1.0 timeline: 20 days (2026-02-04 → 2026-02-24)
- Commits: 81

**v1.1 (in progress):**

| Phase | Plans | Status |
|-------|-------|--------|
| 8. ASX Futures Live Data | 2 | Complete (08-01 pipeline, 08-02 frontend table) |
| 9. Housing Prices Gauge | TBD | Not started |
| 10. NAB Capacity Utilisation Gauge | TBD | Not started |

## Accumulated Context

### Decisions

- [v1.0] ABS is primary housing source — Cotality ToS (Clause 8.4d) prohibits automated scraping; ABS RPPI activates gauge even with stale Dec 2021 data
- [v1.0] ASX futures excluded from hawk score — market-derived, not economic indicator; displayed separately in "What Markets Expect"
- [v1.1] NAB HTML extraction first — capacity utilisation figure is inline in HTML body; PDF is fallback only, not primary approach
- [v1.1] URL discovery required for NAB — never construct NAB URLs from date templates; always discover via tag archive page
- [08-01] CI freshness step uses continue-on-error: true — intermittent ASX outages must not block data commits
- [08-01] meetings[] contract extension is additive — all existing single-meeting fields preserved for backward compatibility
- [08-01] Cross-platform day formatting via str(dt.day) — %-d strftime is Linux/macOS only, crashes on Windows CI
- [08-02] ASX section always visible — container.style.display='' unconditionally; placeholder shown when meetings[] null/empty
- [08-02] Traffic light colors replace old blue/gray/red — green (#10b981) cut, amber (#f59e0b) hold, red (#ef4444) hike

### Research Flags (check before implementing)

- Phase 9: Verify ABS RPPI SDMX key `3.2.100.Q` with a live API call before implementation begins
- Phase 9: HOUS-03/HOUS-04 (Cotality PDF) requires explicit project owner sign-off on ToS risk before any code is written
- Phase 10: Manually verify NAB HTML regex matches the current month's page before committing Phase 10 implementation

### Blockers/Concerns

- ASX endpoint has intermittent availability history (404 on 2026-02-07, 200 on 2026-02-24) — verify live before Phase 8 implementation
- Cotality ToS (Clause 8.4d) prohibits scraping; HOUS-03/HOUS-04 are blocked until project owner documents risk decision

## Session Continuity

Last session: 2026-02-24
Stopped at: Completed 08-02-PLAN.md — multi-meeting ASX table with traffic light bars, always-visible placeholder, Playwright tests updated
Resume file: None
