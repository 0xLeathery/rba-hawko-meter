---
estimated_steps: 7
estimated_files: 2
---

# T02: Add delta badges, sparkline containers, and hero delta

**Slice:** S01 — Indicator Card Momentum UI
**Milestone:** M001-pzg4u9

## Description

Implement all three momentum UI features: delta badges (R001), sparkline integration in cards (R002), and hero hawk score delta (R003). This modifies two existing files — `interpretations.js` (badge helper + card restructure) and `gauge-init.js` (hero delta + orchestration + resize handling).

**Key constraint:** All DOM construction via `createElement`/`textContent`/`appendChild` — no innerHTML. All colours via `element.style` with hex from `GaugesModule.getZoneColor()` — no Tailwind class concatenation. All lines ≤88 characters.

**Key skill:** The `lint` skill (`/Users/annon/.gsd/agent/skills/lint/SKILL.md`) is relevant if ESLint issues arise.

## Steps

1. **Add `createDeltaBadge(metricData)` to `interpretations.js`** — Add a new function inside the `InterpretationsModule` IIFE:
   - Input: a metric data object (one entry from `data.gauges` in status.json)
   - Return `null` if `metricData.delta` is undefined/null, or `Math.abs(metricData.delta) < 5`
   - Otherwise return a `<span>` element with:
     - Class: `delta-badge` (for test selector targeting)
     - Text: `▲ +{delta}` when `delta_direction === "up"`, `▼ −{Math.abs(delta)}` when `delta_direction === "down"` (use actual Unicode arrows ▲ U+25B2, ▼ U+25BC and minus − U+2212)
     - Colour: `element.style.color` set to `GaugesModule.getZoneColor(metricData.value)` (zone colour of current value)
     - Font: `element.style.fontWeight = 'bold'`; `element.style.fontSize = '0.85rem'`
   - Export in the module's return object: `createDeltaBadge: createDeltaBadge`

2. **Modify `renderMetricCard()` header structure** — Currently the card header has label and importance tag. Restructure to a 3-item flex row:
   - Existing label span (left-aligned)
   - Delta badge in the middle (from `createDeltaBadge(metricData)`) — only inserted if non-null
   - Existing importance/category tag (right-aligned, existing `margin-left: auto` keeps it right)
   - The header container already has `display: flex` — add `align-items: center` and `gap: 0.5rem` via `element.style`
   - **IMPORTANT**: Read the existing `renderMetricCard()` function to understand its exact current structure before modifying. The research says it has header, gauge, interp, and source sections.

3. **Add sparkline container to `renderMetricCard()`** — After the gauge container div and before the interpretation text section, insert:
   - A `<div>` with class `sparkline-container` and `id` = `sparkline-{metricId}`
   - Style: `width: 100%`, `height: 40px`, `margin: 0.5rem 0`
   - Inside it, a `<canvas>` element (no width/height attributes yet — SparklineModule reads from parent)
   - If `metricData.history` exists and has `length >= 3`: canvas is present for later drawing
   - If `metricData.history` is missing or has `length < 3`: instead of canvas, insert a `<span>` with text "Building history..." styled `color: #999; font-size: 0.75rem; font-style: italic`

4. **Add `renderHeroDelta(overall)` to `gauge-init.js`** — New function:
   - Input: `data.overall` object from status.json
   - If `overall.hawk_score_delta` is undefined/null: do nothing (no element created)
   - If `overall.hawk_score_delta === 0`: create `#hero-delta` div with text "No change since last update" in `color: #888`
   - If `overall.hawk_score_delta > 0`: text "▲ +{value} since last update" in `color: #c0392b` (hawkish red)
   - If `overall.hawk_score_delta < 0`: text "▼ −{|value|} since last update" in `color: #2980b9` (dovish blue)
   - Font: `fontSize: '1.1rem'`, `fontWeight: '600'`, `textAlign: 'center'`, `margin: '0.5rem 0'`
   - Insert the element: find `#hawk-score-display`, insert `#hero-delta` after it (before `#scale-explainer`) using `parentNode.insertBefore(heroDelta, scaleExplainer)`
   - If `#hawk-score-display` not found, log warning and return

5. **Wire sparkline drawing into `initGauges()`** — After the existing metric card rendering loop in `initGauges()`:
   - For each rendered metric card, find its `canvas` element inside `.sparkline-container`
   - Call `SparklineModule.draw(canvas, metricData.history, GaugesModule.getZoneColor(metricData.value))`
   - Store canvas/history/color references in a module-level array for resize handler
   - Call `renderHeroDelta(data.overall)` after the hawk score display setup

6. **Extend `setupResizeHandler()`** — In the existing debounced resize handler:
   - Iterate stored sparkline references
   - Clear each canvas (`ctx.clearRect`) and redraw via `SparklineModule.draw()`
   - Guard: if SparklineModule is undefined (shouldn't happen with correct script order), skip with console.warn

7. **Verify** — Run `npx eslint public/js/interpretations.js public/js/gauge-init.js` for zero violations. Run `npx playwright test` to confirm existing 28+ tests still pass. Start dev server (`python3 -m http.server 8080 --directory public`) and visually confirm: sparklines render on existing live data (12 history points per active gauge), no delta badges appear (correct — no delta fields in live status.json), no hero delta appears (correct — no hawk_score_delta in live data).

## Must-Haves

- [ ] `createDeltaBadge(metricData)` returns null when |delta| < 5 or delta fields absent
- [ ] `createDeltaBadge(metricData)` returns styled span with ▲/▼ + magnitude when |delta| ≥ 5
- [ ] Card header restructured as 3-item flex: label, badge (optional), importance tag
- [ ] Sparkline container with canvas added to each card (after gauge, before interpretation)
- [ ] "Building history..." placeholder when history < 3 points
- [ ] `renderHeroDelta(overall)` inserts `#hero-delta` between `#hawk-score-display` and `#scale-explainer`
- [ ] Hero delta shows correct text for positive, negative, zero, and absent hawk_score_delta
- [ ] SparklineModule.draw() called per card in initGauges() with correct colour
- [ ] Sparklines redraw on window resize via setupResizeHandler()
- [ ] All lines ≤88 characters (ESLint max-len)
- [ ] No innerHTML — all DOM via createElement/textContent/appendChild
- [ ] Colours via element.style hex, not Tailwind class concatenation
- [ ] `createDeltaBadge` exported in InterpretationsModule return object

## Verification

- `npx eslint public/js/interpretations.js public/js/gauge-init.js` — zero violations
- `npx playwright test` — existing 28+ tests still pass
- Visual smoke test: start `python3 -m http.server 8080 --directory public`, load page in browser, confirm sparklines visible on metric cards, no delta badges (correct for live data), no hero delta (correct for live data)

## Inputs

- `public/js/sparklines.js` — `SparklineModule.draw(canvas, history, color, opts)` (from T01)
- `public/js/interpretations.js` — existing `renderMetricCard()` function with header/gauge/interp/source sections
- `public/js/gauge-init.js` — existing `initGauges()` and `setupResizeHandler()` functions
- `public/js/gauges.js` — `GaugesModule.getZoneColor(value)` for zone-coloured rendering
- `public/data/status.json` — live data shape: `gauges.*.history[]` present (12+ points), `delta`/`delta_direction`/`hawk_score_delta` absent (pipeline hasn't produced deltas on current data)
- S01-RESEARCH data contract: `gauge.delta` (float), `gauge.delta_direction` ("up"/"down"/"unchanged"), `overall.hawk_score_delta` (float)

## Observability Impact

- **DOM inspection surfaces**: `#hero-delta` element present/absent indicates hawk_score_delta availability; `.delta-badge` spans on cards indicate active delta data; `canvas` inside `.sparkline-container` divs indicates sparkline rendering vs `"Building history..."` placeholder span
- **Console diagnostics**: `SparklineModule: need ≥3 points` warns when history too short; `console.warn` if `#hawk-score-display` not found during hero delta render; `console.warn` if SparklineModule undefined during resize redraw
- **Failure visibility**: Missing SparklineModule global → console.warn in resize handler; canvas draw failures → blank container div visible in DOM; absent delta fields → no badge/hero delta elements created (graceful no-op, not error)

## Expected Output

- `public/js/interpretations.js` — MODIFIED: `createDeltaBadge()` added, `renderMetricCard()` restructured with badge and sparkline container, createDeltaBadge exported
- `public/js/gauge-init.js` — MODIFIED: `renderHeroDelta()` added, initGauges() calls sparkline drawing and hero delta, setupResizeHandler() redraws sparklines
