# Phase 9: Housing Prices Gauge - Context

**Gathered:** 2026-02-24
**Status:** Ready for planning

<domain>
## Phase Boundary

The housing gauge activates on the dashboard showing national dwelling price YoY % change, sourced from ABS RPPI (primary) with Cotality HVI (monthly fallback). Pipeline includes staleness detection and source attribution. This phase does NOT add city-level breakdowns, additional housing metrics, or new gauge types — it adds the housing indicator to the existing gauge set with robust dual-source data handling.

</domain>

<decisions>
## Implementation Decisions

### Gauge display
- Match existing gauge style — same circular gauge as other indicators
- Gauge label: "Housing Prices" (no "national" qualifier, no "dwelling")
- Directional label + number format: "RISING +8.3%" or "FALLING -2.1%"
- Hawk/dove color alignment: rising prices = red/warm (hawkish, inflationary), falling prices = blue/cool (dovish)
- Neutral zone for flat prices: small changes (near 0%) show "STEADY" or "FLAT" with neutral/gray coloring rather than forcing a directional label

### Staleness indication
- Always show data period in quarter format: "(Q4 2025)" appended to gauge display, whether data is fresh or stale
- When data >90 days old, the quarter format serves double duty as a staleness signal — no additional visual dimming or warning badges
- Label only — gauge stays fully functional and styled normally regardless of data age

### Data source transparency
- Source name always visible below gauge: "Source: ABS RPPI" or "Source: Cotality HVI"
- RBA-framed plain-English interpretation: connect housing data to RBA policy angle (e.g. "Rising prices put upward pressure on inflation, making rate cuts less likely")

### Claude's Discretion
- Whether to add a subtle fallback note when Cotality is unavailable (e.g. "Source: ABS RPPI (Cotality unavailable)") or just silently switch the source name
- Whether to include a secondary metric alongside YoY % (e.g. quarterly change) if the data supports it cleanly
- Threshold for the neutral/"STEADY" zone (e.g. +/-1% or +/-2%)
- Exact gauge needle range/scale for housing YoY %

</decisions>

<specifics>
## Specific Ideas

- User's core philosophy is "data, not opinion" for laypeople — source attribution and always-visible data period support this transparency
- National weighted average chosen to match RBA's focus on national housing conditions
- Quarter format for data period label matches how ABS publishes RPPI data (quarterly release cycle)
- Hawk/dove color alignment is critical — rising house prices are inflationary (hawkish signal), so red/warm coloring is correct despite consumer intuition that rising = good

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 09-housing-prices-gauge*
*Context gathered: 2026-02-24*
