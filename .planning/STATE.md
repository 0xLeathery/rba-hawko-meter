# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-24)

**Core value:** "Data, not opinion." Empowers laypeople to understand interest rate drivers without relying on media sensationalism or biased advice.
**Current focus:** Phase 8 — ASX Futures Live Data (v1.1 milestone start)

## Current Position

Phase: 8 of 10 (ASX Futures Live Data)
Plan: 0 of ? in current phase
Status: Ready to plan
Last activity: 2026-02-24 — v1.1 roadmap created; phases 8-10 defined; 13/13 requirements mapped

Progress: [███████░░░] 70% (7 of 10 phases complete — v1.0 shipped)

## Performance Metrics

**Velocity (v1.0):**
- Total plans completed: 19
- v1.0 timeline: 20 days (2026-02-04 → 2026-02-24)
- Commits: 81

**v1.1 (not yet started):**

| Phase | Plans | Status |
|-------|-------|--------|
| 8. ASX Futures Live Data | TBD | Not started |
| 9. Housing Prices Gauge | TBD | Not started |
| 10. NAB Capacity Utilisation Gauge | TBD | Not started |

## Accumulated Context

### Decisions

- [v1.0] ABS is primary housing source — Cotality ToS (Clause 8.4d) prohibits automated scraping; ABS RPPI activates gauge even with stale Dec 2021 data
- [v1.0] ASX futures excluded from hawk score — market-derived, not economic indicator; displayed separately in "What Markets Expect"
- [v1.1] NAB HTML extraction first — capacity utilisation figure is inline in HTML body; PDF is fallback only, not primary approach
- [v1.1] URL discovery required for NAB — never construct NAB URLs from date templates; always discover via tag archive page

### Research Flags (check before implementing)

- Phase 9: Verify ABS RPPI SDMX key `3.2.100.Q` with a live API call before implementation begins
- Phase 9: HOUS-03/HOUS-04 (Cotality PDF) requires explicit project owner sign-off on ToS risk before any code is written
- Phase 10: Manually verify NAB HTML regex matches the current month's page before committing Phase 10 implementation

### Blockers/Concerns

- ASX endpoint has intermittent availability history (404 on 2026-02-07, 200 on 2026-02-24) — verify live before Phase 8 implementation
- Cotality ToS (Clause 8.4d) prohibits scraping; HOUS-03/HOUS-04 are blocked until project owner documents risk decision

## Session Continuity

Last session: 2026-02-24
Stopped at: v1.1 roadmap created; all 13 requirements mapped to phases 8-10; ready to plan Phase 8
Resume file: None
