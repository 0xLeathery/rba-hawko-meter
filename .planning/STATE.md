# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-24)

**Core value:** "Data, not opinion." Empowers laypeople to understand interest rate drivers without relying on media sensationalism or biased advice.
**Current focus:** Phase 9 — Housing Prices Gauge (v1.1 in progress)

## Current Position

Phase: 9 of 10 (Housing Prices Gauge)
Plan: 1 of TBD in current phase (09-01 complete)
Status: In progress
Last activity: 2026-02-24 — 09-01 complete: ABS RPPI pipeline integration, housing gauge activated, frontend directional labels + source attribution, Playwright tests

Progress: [████████░░] 75% (7.5 of 10 phases complete — v1.0 shipped, v1.1 in progress)

## Performance Metrics

**Velocity (v1.0):**
- Total plans completed: 19
- v1.0 timeline: 20 days (2026-02-04 → 2026-02-24)
- Commits: 81

**v1.1 (in progress):**

| Phase | Plans | Status |
|-------|-------|--------|
| 8. ASX Futures Live Data | 2 | Complete (08-01 pipeline, 08-02 frontend table) |
| 9. Housing Prices Gauge | TBD | In progress (09-01 complete: ABS RPPI + frontend) |
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
- [09-01] Neutral zone threshold is +/-1% YoY for housing STEADY label — conservative range, RISING in practice with ABS data at +23.67%
- [09-01] data_source read from raw CSV in build_gauge_entry() — z-score pipeline strips source column; raw CSV read is the correct pattern
- [09-01] stale_display: 'quarter_only' controls amber border suppression — only set for housing; toQuarterLabel() in JS doubles as staleness signal

### Research Flags (check before implementing)

- Phase 9 (resolved): ABS RPPI SDMX key confirmed as `1.3.100.Q` (not `3.2.100.Q`) — 74 rows fetched successfully
- Phase 9: HOUS-03/HOUS-04 (Cotality PDF) requires explicit project owner sign-off on ToS risk before any code is written
- Phase 10: Manually verify NAB HTML regex matches the current month's page before committing Phase 10 implementation

### Blockers/Concerns

- Cotality ToS (Clause 8.4d) prohibits scraping; HOUS-03/HOUS-04 are blocked until project owner documents risk decision

## Session Continuity

Last session: 2026-02-24
Stopped at: Completed 09-01-PLAN.md — ABS RPPI pipeline + housing gauge activation, frontend directional labels, source attribution, no amber border, 9/9 Playwright tests passing
Resume file: None
