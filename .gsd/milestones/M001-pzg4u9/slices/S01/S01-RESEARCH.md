# S01 (Indicator Card Momentum UI) — Research

**Date:** 2026-03-17
**Depth:** Targeted — established patterns, well-documented prior research (`.planning/phases/25-indicator-card-ui/`)

## Summary

S01 adds three visual features to the existing dashboard: delta badges (▲/▼) on indicator cards (R001), Canvas 2D sparklines showing trend history (R002), and a hawk score delta in the hero section (R003). All consume data from Phase 24's `inject_deltas()` pipeline function, which produces `delta`, `delta_direction`, `previous_value` per gauge and `hawk_score_delta` in the overall block.

The work is well-scoped: one new file (`sparklines.js`), modifications to two existing files (`interpretations.js`, `gauge-init.js`), and a script tag + ESLint config update. All patterns (IIFE modules, `createElement`/`textContent` DOM construction, `element.style` colour application, `GaugesModule.getZoneColor()`) are already established in the codebase. Detailed implementation decisions and code examples exist in `.planning/phases/25-indicator-card-ui/25-CONTEXT.md` and `25-RESEARCH.md` — these are the primary reference for the planner.

**Critical data fact:** The live `status.json` currently has **no delta fields** — `inject_deltas()` only runs when a previous snapshot exists with a different date, and the pipeline hasn't run twice on different days in the current data. All 5 active gauges have 12+ history points (sufficient for sparklines). Housing and business_confidence are missing from live data entirely (scraper failures — pre-existing, out of scope). Playwright tests must use fixture data with injected delta fields.

## Recommendation

Follow the locked decisions from Phase 25 CONTEXT exactly. The approach is: create `SparklineModule` as a Canvas 2D IIFE, add `createDeltaBadge()` as a helper in `InterpretationsModule`, add `renderHeroDelta()` in `gauge-init.js`, and wire sparkline rendering into the existing `initGauges()` flow. Build in this order: sparklines.js module first (independent, testable), then delta badge helper, then hero delta, then integration into gauge-init.js, then Playwright tests.

## Implementation Landscape

### Key Files

- **`public/js/sparklines.js`** (NEW) — `SparklineModule.draw(canvas, history, color, opts)` IIFE. Canvas 2D stroke-only line with end-dot, retina scaling, 40px height. Returns `false` if history < 3 points. ~40-50 lines.
- **`public/js/interpretations.js`** (MODIFY) — Add `createDeltaBadge(metricData)` helper function (returns DOM element or null). Modify `renderMetricCard()` to: (1) restructure header as 3-item flex with delta badge between label and importance, (2) insert sparkline container `div#sparkline-{id}` after gauge container and before interpretation text. Export `createDeltaBadge` in the return object.
- **`public/js/gauge-init.js`** (MODIFY) — Add `renderHeroDelta(overall)` function that inserts `div#hero-delta` between `#hawk-score-display` and `#scale-explainer`. In `initGauges()`: call `renderHeroDelta(data.overall)` after score display, call `SparklineModule.draw()` for each metric card after gauge render. In `setupResizeHandler()`: redraw sparklines on resize.
- **`public/index.html`** (MODIFY) — Add `<script src="js/sparklines.js"></script>` between gauges.js (line 490) and interpretations.js (line 491).
- **`eslint.config.js`** (MODIFY) — Add `SparklineModule: "writable"` to globals and add to `varsIgnorePattern`.

### Data Contract (from `inject_deltas()` in `pipeline/normalize/archive.py`)

Per-gauge fields (present only when previous snapshot exists):
```
gauge.delta: float          — current_value - previous_value, rounded to 1dp
gauge.delta_direction: str  — "up" | "down" | "unchanged"
gauge.previous_value: float — previous run's gauge value
```

Overall fields (present only when previous snapshot exists):
```
overall.hawk_score_delta: float      — current - previous hawk_score
overall.previous_hawk_score: float   — previous run's hawk_score
```

Pre-existing field always present:
```
gauge.history: float[]  — rolling array of historical gauge values (up to 12)
```

**Absence handling:** When delta fields are absent (cold start / first run), no badge/hero-delta should render. This is R001 and R003's graceful degradation requirement.

### Build Order

1. **`sparklines.js`** — Independent module, no dependencies beyond `window.devicePixelRatio`. Can be unit-tested in isolation. Unblocks sparkline rendering.
2. **`createDeltaBadge()` in interpretations.js** — Pure function returning DOM element or null. Depends on `GaugesModule.getZoneColor()` (already loaded). Independently testable.
3. **`renderMetricCard()` modifications** — Integrates delta badge into header, adds sparkline container div. Depends on steps 1-2.
4. **`renderHeroDelta()` in gauge-init.js** — Independent of sparklines. Inserts into existing hero DOM.
5. **`initGauges()` integration** — Calls `SparklineModule.draw()` per card, calls `renderHeroDelta()`. Depends on steps 1-4.
6. **`setupResizeHandler()` extension** — Redraws sparklines on window resize. Depends on step 5.
7. **Script tag + ESLint config** — Must be in place before steps 1-6 can run in browser / pass lint.
8. **Playwright E2E tests** — Fixture-based tests verifying delta badges, sparklines, hero delta, and placeholder states.

### Verification Approach

**Lint:** `npx eslint public/js/sparklines.js public/js/interpretations.js public/js/gauge-init.js` — zero violations.

**Existing tests:** `python -m pytest tests/python/ -m "not live"` — 431+ tests pass. `npx playwright test` — 28+ tests pass.

**New Playwright tests** (fixture-based with injected delta fields in status.json):
1. Delta badge visible on card when `|delta| >= 5` — check for `▲` or `▼` text in header
2. Delta badge absent when `|delta| < 5` — verify no arrow character in header
3. Delta badge absent when delta fields missing — cold start graceful degradation
4. Sparkline canvas present for indicators with `history.length >= 3`
5. "Building history..." placeholder for indicators with `history.length < 3`
6. Hero delta element present when `hawk_score_delta` exists and non-zero
7. Hero delta shows "No change since last update" when `hawk_score_delta === 0`
8. Hero delta absent when `hawk_score_delta` missing (cold start)

**Visual smoke test:** Start dev server (`python3 -m http.server 8080 --directory public`), verify sparklines render on existing live data (12 history points available), verify no delta badges appear (no delta fields in live data — correct behavior).

## Constraints

- **ESLint max-len 88 chars** — all JS lines must be ≤88 characters. Use string concatenation and variable extraction for long expressions.
- **No innerHTML** — all DOM construction via `createElement`/`textContent`/`appendChild`. ESLint enforced.
- **Colour via `element.style`** — never Tailwind class concatenation (`'text-' + color`). CDN drops dynamic classes.
- **Canvas 2D only for sparklines** — NOT Plotly. 8 Plotly instances already on page; Firefox freezes above ~15.
- **`delta_direction` not `direction`** — `business_confidence` already has a `direction` field (RISING/FALLING/STEADY) from engine.py. Phase 24 deliberately named the delta field `delta_direction`.
- **Script load order** — sparklines.js must load after gauges.js (needs `GaugesModule.getZoneColor()`) and before gauge-init.js (orchestrator).

## Common Pitfalls

- **Canvas zero-width on first render** — `offsetWidth` is 0 before element is in the DOM. Append canvas to visible parent first, then read width, then draw. Or use `requestAnimationFrame`.
- **Blurry canvas on retina** — Must multiply canvas `width`/`height` attributes by `devicePixelRatio`, scale context with `ctx.scale(dpr, dpr)`, and set CSS dimensions to logical size.
- **Flat sparkline division by zero** — When all history values are identical, `(max - min)` is 0. Check for this and render as horizontal line at vertical center.
- **Non-numeric history values** — Filter `history` array for valid numbers before rendering. Null/undefined values would produce NaN in canvas drawing.
- **Resize handler doesn't redraw sparklines** — Canvas buffer doesn't auto-resize with CSS `width:100%`. Must store references and redraw on window resize using the existing debounced handler.

## Sources

- `.planning/phases/25-indicator-card-ui/25-CONTEXT.md` — locked implementation decisions (5/5 consensus on all visual designs, placements, and patterns)
- `.planning/phases/25-indicator-card-ui/25-RESEARCH.md` — complete code examples for `SparklineModule.draw()`, `createDeltaBadge()`, `renderHeroDelta()`, pitfall analysis
- `pipeline/normalize/archive.py:111-164` — `inject_deltas()` implementation confirming field names and types
- `public/js/interpretations.js:renderMetricCard()` — current card DOM structure (header, gauge, interp, source)
- `public/js/gauge-init.js:initGauges()` — orchestration flow and resize handler
- `public/js/gauges.js` — `getZoneColor()`, `getDisplayLabel()` APIs
