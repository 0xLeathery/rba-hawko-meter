# Phase 22: Verdict Explanation Component - Research

**Researched:** 2026-02-26
**Domain:** Vanilla JS DOM rendering, ASIC-compliant copy, weighted indicator ranking
**Confidence:** HIGH

## Summary

Phase 22 adds a plain-English explanation section below the hero that answers "Why is the score what it is?" by listing the top hawkish and dovish indicators ranked by weighted contribution. The CONTEXT.md from the synthetic discussion provides extremely detailed implementation specifications including exact function signatures, sentence templates for all 7 indicators, ranking formula, edge cases, and DOM placement strategy.

The implementation is straightforward: add `rankIndicators()` (internal) and `getExplanationSentence()` + `renderVerdictExplanation()` (public) to InterpretationsModule, then wire one call in gauge-init.js's `.then()` success path. No new libraries or CDN dependencies are needed. The entire phase touches only 2 JS files (interpretations.js, gauge-init.js) and adds no HTML changes since the section is created dynamically.

**Primary recommendation:** Implement exactly as specified in CONTEXT.md. The locked decisions are well-reasoned and the code examples are complete enough to serve as near-final implementation.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
1. **Indicator Ranking Method: Weighted Contribution** (5/5 consensus) -- Rank by `(value - 50) * weight`. Positive = hawkish, negative = dovish. Sort each group by absolute magnitude descending.
2. **Explanation Copy: Single Sentence Per Indicator** (5/5 consensus) -- Each indicator gets one sentence via `getExplanationSentence(metricId, metricData)`. Pattern: "[Factual observation], which [hedged causal link]."
3. **Visual Layout: Two Grouped Lists with Zone-Coloured Headings** (5/5 consensus) -- "Pushing the score up" (warm colour heading) and "Pulling the score down" (cool colour heading). List items use `text-gray-300`.
4. **DOM Placement: New Section Between Hero and Countdown** (5/5 consensus) -- `#verdict-explanation` as a `<section>` inserted via `insertBefore` targeting `#countdown-section`. Created only in `.then()` success path.
5. **Data Flow: Single Entry Point** (5/5 consensus) -- `renderVerdictExplanation(containerId, data)` is the public entry point. Internal: `rankIndicators(gaugesData)`. Both `renderVerdictExplanation` and `getExplanationSentence` exposed on module API.

### Claude's Discretion
- **Minimum Contribution Threshold** (3/2 split) -- Use 0.5 absolute contribution points as default. If score is non-neutral (outside 40-60) but no indicator passes threshold, show top 1 with softer language.

### Deferred Ideas (OUT OF SCOPE)
- Animated entry for explanation section (Phase 23: POLX)
- Collapsible explanation section
- Indicator trend arrows (requires `previous_value` in status.json)
- Explanation as tooltip hover on hero score
- Dynamic threshold based on score distance from 50
- Separate explanation module (verdict-explanation.js)
- Z-score display in explanation sentences
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| EXPL-01 | User sees plain-English list of top 3 hawkish indicators | rankIndicators() returns top 3 hawkish by contribution; getExplanationSentence() provides copy |
| EXPL-02 | User sees plain-English list of top 2 dovish indicators | rankIndicators() returns top 2 dovish by absolute contribution; same sentence pattern |
| EXPL-03 | Neutral indicators omitted from explanation | Threshold of 0.5 absolute contribution filters out low-impact indicators |
| EXPL-04 | ASIC-compliant hedged language throughout | Sentence templates use "tends to", "historically associated with", "consistent with" -- no predictions |
</phase_requirements>

## Standard Stack

### Core (Existing -- No Changes)
| Library | Version | Purpose | Notes |
|---------|---------|---------|-------|
| Vanilla JS IIFE | N/A | Module system | InterpretationsModule pattern |
| Tailwind CDN | v3 | Utility CSS | Classes applied as literal strings |
| Plotly.js | 2.35.2 | Gauges | Not involved in this phase |

### No New Dependencies
Phase 22 requires zero new libraries. All functionality is vanilla JS DOM manipulation within the existing InterpretationsModule IIFE pattern.

## Architecture Patterns

### Pattern 1: IIFE Module Extension (InterpretationsModule)
**What:** Add functions to existing IIFE, expose via return object
**Source:** Verified from current `interpretations.js` (lines 682-694)
**Example:**
```javascript
// Current module return object (line 682):
return {
  renderVerdict: renderVerdict,
  renderASXTable: renderASXTable,
  // ... existing exports ...
  // ADD:
  renderVerdictExplanation: renderVerdictExplanation,
  getExplanationSentence: getExplanationSentence
};
```

### Pattern 2: Safe DOM Creation (No innerHTML)
**What:** Use createElement/textContent/appendChild exclusively
**Source:** ESLint rule enforces this. Verified: every function in interpretations.js follows this pattern.
**Example from renderMetricCard (line 576):**
```javascript
var card = document.createElement('div');
card.className = 'bg-finance-gray rounded-lg p-4 border border-finance-border';
// ...
container.appendChild(card);
```

### Pattern 3: Zone Colour via element.style
**What:** Apply zone colours using `element.style.color = GaugesModule.getZoneColor(value)` -- never concatenate Tailwind classes
**Source:** CONTEXT.md locked decision + verified in renderVerdict (line 70):
```javascript
labelSpan.style.color = GaugesModule.getZoneColor(overallData.hawk_score);
```
**For this phase:**
- Hawkish heading: `element.style.color = GaugesModule.getZoneColor(75)` yields `#f87171`
- Dovish heading: `element.style.color = GaugesModule.getZoneColor(25)` yields `#60a5fa`

### Pattern 4: Orchestrator Wiring in gauge-init.js
**What:** Add a single function call in the `.then()` success path
**Source:** Verified from gauge-init.js (lines 182-261). The success path calls rendering functions sequentially. The explanation section should be wired after verdict rendering and before metric gauges.
**Placement:** After `renderStalenessWarning` (line 233) and before `renderMetricGauges` (line 237).

### Anti-Patterns to Avoid
- **Dynamic Tailwind class concatenation:** `'text-' + colorName + '-400'` will silently fail -- Tailwind CDN purges these. Use `element.style.color` with hex.
- **innerHTML usage:** ESLint will catch this. Use createElement/textContent only.
- **Rendering in error path:** The explanation section must NOT exist if data fetch fails. Only render in `.then()`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Zone colour lookup | Colour mapping function | `GaugesModule.getZoneColor(value)` | Already exists, tested, single source of truth |
| Data suspect check | Custom null/bogus filter | `isDataSuspect(metricId, metricData)` | Already exists in InterpretationsModule closure |
| Display labels | Metric ID formatting | `GaugesModule.getDisplayLabel(metricId)` | Already exists with proper mappings |

## Common Pitfalls

### Pitfall 1: Tailwind Class Not Rendering
**What goes wrong:** Dynamic class string like `'bg-' + zone` doesn't render
**Why it happens:** Tailwind CDN v3 scans for literal class strings at build time
**How to avoid:** Use full literal class strings OR element.style with hex values
**Warning signs:** Element appears unstyled despite having correct className

### Pitfall 2: Missing Data Guard
**What goes wrong:** `TypeError: Cannot read properties of null` on edge case data
**Why it happens:** Indicator might have `value: null` or `raw_value: null`
**How to avoid:** Guard in `rankIndicators()`: `if (m.value == null) return;`
**Warning signs:** Console errors on data fetch

### Pitfall 3: Playwright nth-Index Selector Breakage
**What goes wrong:** Existing Playwright tests fail because DOM structure changed
**Why it happens:** New section inserted between hero and countdown shifts indices
**How to avoid:** Use ID-based selectors (`#verdict-explanation`), keep section structurally separate from `#metric-gauges-grid`
**Warning signs:** Tests that worked before Phase 22 now fail with timeout

### Pitfall 4: Empty Section on All-Neutral Data
**What goes wrong:** Empty headings rendered when no indicators pass threshold
**Why it happens:** Not checking array lengths before rendering group sections
**How to avoid:** Check `ranked.hawkish.length > 0` before rendering "Pushing the score up" section; same for dovish

### Pitfall 5: Incorrect Sort Order for Dovish
**What goes wrong:** Dovish indicators sorted wrong (weakest first instead of strongest)
**Why it happens:** Dovish contributions are negative, so normal descending sort puts least negative first
**How to avoid:** Sort dovish by `a.contribution - b.contribution` (most negative first) or by absolute value descending

## Code Examples

### Verified: Current status.json Data Structure
```javascript
// data.gauges.inflation example:
{
  "value": 30.2,     // 0-100 gauge score
  "weight": 0.25,    // contribution weight
  "raw_value": 3.76, // human-readable raw value
  "raw_unit": "% YoY",
  "data_date": "2025-12-31",
  "confidence": "HIGH"
}
```

### Verified: Contribution Calculation with Current Data
| Indicator | Value | Weight | (value-50)*weight | Direction |
|-----------|-------|--------|-------------------|-----------|
| wages | 84.8 | 0.15 | +5.22 | Hawkish |
| inflation | 30.2 | 0.25 | -4.95 | Dovish |
| employment | 33.7 | 0.15 | -2.45 | Dovish |
| housing | 59.4 | 0.15 | +1.41 | Hawkish |
| business_confidence | 72.5 | 0.05 | +1.13 | Hawkish |
| spending | 60.4 | 0.10 | +1.04 | Hawkish |
| building_approvals | 57.9 | 0.05 | +0.40 | Below threshold |

**Expected output with current data:**
- Top 3 hawkish: wages (+5.22), housing (+1.41), business_confidence (+1.13)
- Top 2 dovish: inflation (-4.95), employment (-2.45)
- Omitted: building_approvals (contribution 0.40 < 0.5 threshold)

### Verified: GaugesModule.getZoneColor() Returns
```javascript
GaugesModule.getZoneColor(75)  // => '#f87171' (warm/hawkish)
GaugesModule.getZoneColor(25)  // => '#60a5fa' (cool/dovish)
GaugesModule.getZoneColor(50)  // => '#6b7280' (neutral)
```
Source: gauges.js ZONE_COLORS array (lines 10-16).

### Verified: DOM Insertion Point
```javascript
// Current DOM structure in index.html (line 121-164):
// <section id="hawk-o-meter-section"> ... hero ... </section>
// <section id="countdown-section"> ... countdown ... </section>
//
// New section goes BETWEEN these two:
var mainEl = document.querySelector('main');
var countdownSection = document.getElementById('countdown-section');
var explanationSection = document.createElement('section');
explanationSection.id = 'verdict-explanation';
mainEl.insertBefore(explanationSection, countdownSection);
```

## Open Questions

None. The CONTEXT.md provides complete specifications for all implementation details including edge cases.

## Sources

### Primary (HIGH confidence)
- Current codebase: `public/js/interpretations.js` (694 lines, full IIFE module)
- Current codebase: `public/js/gauge-init.js` (303 lines, orchestrator)
- Current codebase: `public/js/gauges.js` (270 lines, getZoneColor verified)
- Current codebase: `public/data/status.json` (real data, contribution calculations verified)
- CONTEXT.md: Synthetic discussion output from 5 agents, 6 locked decisions

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new dependencies, all existing patterns
- Architecture: HIGH -- extending existing module with verified patterns
- Pitfalls: HIGH -- all identified from codebase analysis and CONTEXT.md edge cases

**Research date:** 2026-02-26
**Valid until:** 2026-03-26 (stable -- no external dependencies changing)
