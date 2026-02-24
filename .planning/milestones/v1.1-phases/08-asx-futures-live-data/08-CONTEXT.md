# Phase 8: ASX Futures Live Data - Context

**Gathered:** 2026-02-24
**Status:** Ready for planning

<domain>
## Phase Boundary

The "What Markets Expect" section displays fresh, multi-meeting probability data sourced from the ASX MarkitDigital endpoint, verified working in GitHub Actions CI. Pipeline includes staleness detection with warnings and errors. This phase does NOT add new indicators or gauges — it upgrades the existing ASX futures section from single-meeting to multi-meeting display with robust data freshness handling.

</domain>

<decisions>
## Implementation Decisions

### Multi-meeting layout
- Vertical table with rows for each of the next 3-4 upcoming RBA meetings
- Next meeting row highlighted with a subtle accent (border or background)
- Keep existing "What Markets Expect" heading — no change to section title
- Horizontal scroll on mobile for the full table (no responsive card stacking)

### Probability visualization
- Stacked horizontal bar per table row spanning the probability columns
- Traffic light color scheme: green (cut), amber (hold), red (hike) — replacing the existing blue/gray/red
- Update the existing single-meeting probability display colors to match the new traffic light scheme for consistency

### Staleness signals
- Always show "Data as of [date]" below the table — visible whether data is fresh or stale
- When ASX endpoint returns no data at all, show a placeholder message ("Market futures data currently unavailable") rather than hiding the section
- Pipeline: warn at 14 days stale, error at 30 days stale (ASX is optional tier, so error is non-fatal but logged)

### Meeting date labels
- Full date format: "20 May 2026", "1 Jul 2026", etc.
- Exact RBA meeting dates shown (not just month approximations)

### Claude's Discretion
- Whether to add a "NEXT" badge on the highlighted first row, or rely on visual highlight alone
- Whether to show current cash rate as a reference note above the table
- Whether to include a basis-point change column alongside implied rate
- Percentage label placement on stacked bars (inside segments vs below)
- How to handle zero-width segments (omit vs show hairline)
- Staleness display styling (inline annotation, banner, or dim) — pick approach matching existing dashboard patterns

</decisions>

<specifics>
## Specific Ideas

- User wants traffic light colors (green/amber/red) — specifically mentioned remembering a traffic light system, prefers this over the blue/gray/red currently in code
- Dashboard philosophy is "data, not opinion" for laypeople — full dates and always-visible freshness timestamp support transparency
- Stacked bars chosen over plain numbers or inline mini-bars — user wants visual weight for probability splits

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 08-asx-futures-live-data*
*Context gathered: 2026-02-24*
