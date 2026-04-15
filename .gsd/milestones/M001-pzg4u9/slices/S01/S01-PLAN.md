# S01: Indicator Card Momentum UI

**Goal:** Every indicator card shows delta badges (▲/▼ with magnitude) and Canvas 2D sparklines; hero displays hawk score delta. Graceful degradation when data is absent.
**Demo:** Load the dashboard with fixture data containing delta fields → see delta badges on cards with |delta| ≥ 5, sparklines on cards with ≥3 history points, and hero delta between score and explainer. Load with no delta fields → no badges or hero delta rendered. Load with <3 history points → "Building history..." placeholder instead of sparkline.

## Must-Haves

- Delta badge (▲/▼ + magnitude) on indicator cards when `|delta| ≥ 5` gauge points, coloured by zone (R001)
- No delta badge when `|delta| < 5` or delta fields absent — cold start graceful degradation (R001)
- Canvas 2D sparkline on each indicator card from `history[]` array, coloured by zone (R002)
- "Building history..." placeholder when `history.length < 3` (R002)
- Hero section hawk score delta with directional arrow and "since last update" wording (R003)
- "No change since last update" when `hawk_score_delta === 0` (R003)
- No hero delta element when `hawk_score_delta` missing — cold start graceful degradation (R003)
- Sparklines redraw on window resize without visual artifacts
- All new JS passes ESLint (max-len 88, no innerHTML, element.style for colours)
- All existing tests (431+ pytest, 28+ Playwright) continue to pass

## Proof Level

- This slice proves: contract (fixture-verified UI rendering against known data shapes)
- Real runtime required: yes (browser rendering of Canvas 2D and DOM elements)
- Human/UAT required: no (Playwright assertions sufficient; visual clarity is UAT at milestone level)

## Verification

- `npx eslint public/js/sparklines.js public/js/interpretations.js public/js/gauge-init.js` — zero violations
- `npx playwright test tests/momentum.spec.js` — all 8 new tests pass
- `npx playwright test` — all existing tests still pass (28+)
- `python -m pytest tests/python/ -m "not live"` — all existing tests still pass (431+)
- Browser console check: load dashboard with `<3 history` fixture → `console.warn('SparklineModule: need ≥3 points')` appears (verifies diagnostic signal fires on degraded path)

## Observability / Diagnostics

- Runtime signals: `console.warn` when SparklineModule.draw() receives < 3 history points or non-numeric values (aids debugging without failing silently)
- Inspection surfaces: DOM element `#hero-delta` present/absent indicates delta data availability; `canvas` elements inside `.sparkline-container` divs indicate sparkline rendering; delta badges have class `.delta-badge` for selector targeting
- Failure visibility: missing SparklineModule global logs to console.error; canvas draw failures visible as blank container divs in DOM inspection

## Integration Closure

- Upstream surfaces consumed: `public/data/status.json` (gauges.*.delta, gauges.*.delta_direction, gauges.*.history[], overall.hawk_score_delta — from Phase 24 inject_deltas()); `public/js/gauges.js` (GaugesModule.getZoneColor(), GaugesModule.getDisplayLabel())
- New wiring introduced in this slice: `<script src="js/sparklines.js">` in index.html; SparklineModule.draw() called from gauge-init.js initGauges(); createDeltaBadge() called from interpretations.js renderMetricCard()
- What remains before the milestone is truly usable end-to-end: S02 (historical chart + change narrative), S03 (social sharing), S04 (newsletter)

## Tasks

- [x] **T01: Create SparklineModule and configure build tooling** `est:30m`
  - Why: Independent Canvas 2D module that all sparkline rendering depends on. ESLint and script tag must land first or nothing else passes lint or runs in browser.
  - Files: `public/js/sparklines.js`, `eslint.config.js`, `public/index.html`
  - Do: Create sparklines.js IIFE with `SparklineModule.draw(canvas, history, color, opts)` — retina scaling, stroke-only line with end-dot, 40px height, returns false for <3 points. Add `SparklineModule: "writable"` to ESLint globals and varsIgnorePattern. Add `<script src="js/sparklines.js">` between gauges.js and interpretations.js in index.html. All lines ≤88 chars. No innerHTML. Handle flat-line (all values equal) and non-numeric filtering.
  - Verify: `npx eslint public/js/sparklines.js` — zero violations
  - Done when: sparklines.js passes ESLint, script tag is in index.html, ESLint config updated

- [x] **T02: Add delta badges, sparkline containers, and hero delta** `est:45m`
  - Why: Implements all three requirements (R001 delta badges, R002 sparkline integration, R003 hero delta) by wiring the momentum UI into the existing card rendering and gauge initialization flows.
  - Files: `public/js/interpretations.js`, `public/js/gauge-init.js`
  - Do: (1) Add `createDeltaBadge(metricData)` to InterpretationsModule — returns styled DOM span with ▲/▼ + magnitude when |delta| ≥ 5, null otherwise. Colour via `GaugesModule.getZoneColor()` on `element.style`. (2) Modify `renderMetricCard()` — restructure header as 3-item flex container: label → delta badge → importance tag; add `div.sparkline-container` with canvas element after gauge container. (3) Add `renderHeroDelta(overall)` to gauge-init.js — inserts `#hero-delta` div between `#hawk-score-display` and `#scale-explainer`. Shows "▲ +X.X since last update" / "▼ −X.X" / "No change since last update" as appropriate. No element when data absent. (4) In `initGauges()`: call `renderHeroDelta(data.overall)` after score display; call `SparklineModule.draw()` for each metric card after gauge render. (5) In `setupResizeHandler()`: redraw sparklines on resize using stored references. All lines ≤88 chars. Export createDeltaBadge in InterpretationsModule return object.
  - Verify: `npx eslint public/js/interpretations.js public/js/gauge-init.js` — zero violations; start dev server and visually confirm: sparklines render on existing data (12 history points), no delta badges appear (correct — no delta fields in live data), no hero delta appears (correct — no hawk_score_delta in live data)
  - Done when: ESLint clean on both files; existing Playwright tests still pass (`npx playwright test`)

- [ ] **T03: Playwright E2E tests for momentum UI features** `est:45m`
  - Why: Fixture-based E2E tests verify all three requirements including graceful degradation edge cases. Live data lacks delta fields, so tests must inject fixture data via `page.route()` to exercise all code paths.
  - Files: `tests/momentum.spec.js`
  - Do: Create tests/momentum.spec.js with 8 tests using `page.route('**/data/status.json', ...)` to inject fixture status.json variants: (1) delta badge visible when |delta| ≥ 5, (2) delta badge absent when |delta| < 5, (3) delta badge absent when delta fields missing, (4) sparkline canvas present for history ≥ 3, (5) "Building history..." placeholder for history < 3, (6) hero delta visible with correct arrow/text when hawk_score_delta present and non-zero, (7) hero delta shows "No change" when hawk_score_delta === 0, (8) hero delta absent when hawk_score_delta missing. Build fixture data from the live status.json structure, injecting/removing delta fields per test. Follow existing test patterns (read live status.json at module level, use `page.route()` to intercept and modify).
  - Verify: `npx playwright test tests/momentum.spec.js` — 8 tests pass; `npx playwright test` — all tests pass (existing 28+ plus new 8)
  - Done when: All 8 new tests pass; all existing tests pass; `python -m pytest tests/python/ -m "not live"` still passes (431+)

## Files Likely Touched

- `public/js/sparklines.js` (NEW)
- `public/js/interpretations.js` (MODIFY)
- `public/js/gauge-init.js` (MODIFY)
- `public/index.html` (MODIFY — script tag)
- `eslint.config.js` (MODIFY — SparklineModule global)
- `tests/momentum.spec.js` (NEW)
