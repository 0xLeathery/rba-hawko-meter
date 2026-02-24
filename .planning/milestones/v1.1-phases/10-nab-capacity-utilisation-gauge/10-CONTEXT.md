# Phase 10: NAB Capacity Utilisation Gauge - Context

**Gathered:** 2026-02-24
**Status:** Ready for planning

<domain>
## Phase Boundary

The business confidence gauge activates on the dashboard showing capacity utilisation percentage, sourced via URL-discovery-based HTML extraction from the NAB Monthly Business Survey with a PDF fallback. This is the final indicator — completing it moves the dashboard from "7 of 8" to "8 of 8 indicators." This phase does NOT add other NAB survey metrics (business confidence index, trading conditions, etc.), city-level breakdowns, or new gauge types — it adds the capacity utilisation indicator to the existing gauge set with robust scraping and fallback handling.

</domain>

<decisions>
## Implementation Decisions

### Gauge display & labeling
- Gauge title: "Business Conditions" (broad, matches RBA framing — capacity utilisation is a component of business conditions)
- Trend label shows BOTH level and direction: "83.2% — ABOVE avg, RISING" or "79.1% — BELOW avg, FALLING"
- Hawk/dove color mapping: high capacity utilisation = red/hawkish (inflationary pressure), low = blue/dovish. Consistent with housing gauge's inflation-aligned coloring
- Data period format: month + year "(Jan 2026)" — matches the monthly release cadence of NAB surveys
- Gauge range: 70-90% — covers realistic historical range with headroom, ~81% average sits near middle

### Direction detection
- Direction determined by month-over-month change (compare latest to previous month)
- Flat/STEADY threshold: +/- 0.5 percentage points — changes within this band show "STEADY" instead of RISING/FALLING
- When only one data point exists (no previous month), Claude decides how to handle gracefully (likely omit direction, show level only)

### Staleness indication
- Explicit staleness warning when data is >45 days old (more prominent than just the month label)
- Month label always shows data period "(Jan 2026)" regardless of staleness

### Scraper behavior & resilience
- If NAB tag archive crawl finds no survey URL: log clear warning, skip this indicator, pipeline continues (consistent with other scrapers)
- PDF fallback: when HTML extraction fails, attempt PDF extraction. Logged in pipeline but silent to dashboard user — no visual difference
- If BOTH HTML and PDF fail: don't write anything to CSV. Next pipeline run re-attempts (retry, don't mark as permanent gap)
- Scraper is idempotent: runs on every pipeline invocation, skips if current month's data already exists in CSV. No date-awareness or timing logic

### Historical data handling
- Initial backfill: scrape last 12 months of NAB surveys from tag archive
- CSV gaps: skip missing months (only rows for successfully extracted months). No null/NA placeholder rows
- Long-run average: calculated dynamically from CSV data, not hardcoded at 81%

### Data source transparency
- Source label format: Claude's discretion (pick what's consistent with other gauge source labels)
- Plain-English interpretation: inflation pressure framing — "High capacity utilisation signals inflation pressure, making rate cuts less likely"
- Indicator count: just update to "8 of 8 indicators" — no celebration badge or special UI

### Pipeline integration
- Composite score weighting: Claude's discretion (determine appropriate weighting based on existing normalization approach)
- When NAB data is missing: exclude from composite and show "Based on 7 of 8 indicators" — transparent, don't carry forward stale values
- Z-score polarity: explicit in config (higher_is_hawkish: true) — clear, auditable, matches existing indicator config pattern
- Schedule: runs daily with other scrapers (idempotent skip when current month already collected). No separate monthly job

### Claude's Discretion
- Seed data approach for initial CSV average calculation (whether to pre-populate historical values or start with 81% baseline until enough data accumulates)
- Source label exact wording (consistency with other gauges)
- Gauge outlier handling (clamp to 70-90% edge or auto-expand)
- Single data point direction label handling
- Composite score weighting relative to other indicators

</decisions>

<specifics>
## Specific Ideas

- "Data, not opinion" philosophy: capacity utilisation is a hard economic metric that directly informs RBA policy decisions about spare capacity in the economy
- The 81% long-run average is well-established in RBA/NAB research — even when calculating dynamically, this serves as a sanity check
- NAB survey URL discovery via tag archive (not date templates) is critical — NAB's URL structure is inconsistent and changes without notice
- This completes the full indicator set: GDP, employment, inflation, wages, housing, ASX futures, RBA rate, and now business conditions
- Hawk/dove color alignment is critical — high capacity utilisation = inflationary = hawkish (red), even though business owners might see high utilisation as "good"

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 10-nab-capacity-utilisation-gauge*
*Context gathered: 2026-02-24*
