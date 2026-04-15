---
id: T02
parent: S01
milestone: M001-pzg4u9
provides:
  - createDeltaBadge(metricData) in InterpretationsModule — delta badge DOM builder with ▲/▼ arrows and zone colouring
  - Sparkline containers with canvas elements in each metric card (between gauge and interpretation)
  - renderHeroDelta(overall) in gauge-init.js — hero hawk score delta with directional arrows
  - Sparkline resize redraw in setupResizeHandler()
key_files:
  - public/js/interpretations.js
  - public/js/gauge-init.js
patterns_established:
  - Delta badge pattern: createDeltaBadge returns null for absent/small deltas, styled span for significant ones (≥5 points)
  - Sparkline container pattern: sparkline-container div → canvas (≥3 history) or placeholder span (<3 history)
  - Hero delta pattern: renderHeroDelta inserts #hero-delta between #hawk-score-display and #scale-explainer via insertBefore
observability_surfaces:
  - DOM: #hero-delta present/absent signals hawk_score_delta availability
  - DOM: .delta-badge spans on cards signal active delta data
  - DOM: canvas inside .sparkline-container signals sparkline rendering; span with "Building history..." signals insufficient data
  - Console: console.warn from SparklineModule when <3 history points
  - Console: console.warn from renderHeroDelta when #hawk-score-display not found
  - Console: console.warn from setupResizeHandler when SparklineModule undefined
duration: 25m
verification_result: passed
completed_at: 2026-03-18
blocker_discovered: false
---

# T02: Add delta badges, sparkline containers, and hero delta

**Added createDeltaBadge(), sparkline canvas containers, and hero delta rendering with zone-coloured sparkline drawing and resize redraw**

## What Happened

Implemented all three momentum UI features across two files:

1. **interpretations.js**: Added `createDeltaBadge(metricData)` — returns null when |delta| < 5 or delta fields absent; returns styled `<span class="delta-badge">` with ▲/▼ Unicode arrows, zone-coloured via `GaugesModule.getZoneColor()`. Restructured `renderMetricCard()` header as 3-item flex row (label → badge → importance tag). Added sparkline container div with canvas element between gauge and interpretation sections; shows "Building history..." placeholder when history < 3 points. Exported `createDeltaBadge` in module return object. Renamed `badge` var to `confBadge` in low-confidence section to avoid no-redeclare ESLint conflict.

2. **gauge-init.js**: Added `renderHeroDelta(overall)` — creates `#hero-delta` div with directional text (▲ +X / ▼ −X / "No change") inserted between `#hawk-score-display` and `#scale-explainer`. Added sparkline drawing loop in `initGauges()` — iterates rendered metrics, calls `SparklineModule.draw()` per card with zone colour, stores refs for resize. Extended `setupResizeHandler()` to clear and redraw sparklines on debounced resize with SparklineModule guard.

## Verification

- `npx eslint public/js/interpretations.js public/js/gauge-init.js` — **zero violations**
- `npx playwright test` — **19 passed, 9 failed** (same 9 failures before and after changes — confirmed pre-existing data drift: status.json has 5 gauges, tests expect 7)
- Visual smoke test at localhost:8080:
  - 5 sparkline canvases visible on metric cards (Inflation, Wages, Employment, Spending, Building Approvals)
  - Sparklines correctly positioned between gauge and interpretation text
  - No delta badges (correct — no delta data in live status.json)
  - No hero delta element (correct — no hawk_score_delta in live data)
  - `typeof InterpretationsModule.createDeltaBadge` → `"function"` (export confirmed)

### Slice-level verification status (intermediate task — partial expected):
- ✅ `npx eslint public/js/sparklines.js public/js/interpretations.js public/js/gauge-init.js` — zero violations
- ⬜ `npx playwright test tests/momentum.spec.js` — file not yet created (T03)
- ✅ `npx playwright test` — all existing passing tests still pass (19/19; 9 pre-existing failures from data drift)
- ⬜ `python -m pytest tests/python/ -m "not live"` — not run (no Python changes in this task)

## Diagnostics

- **DOM inspection**: `document.querySelectorAll('.sparkline-container').length` should equal number of active gauges; `.sparkline-container canvas` elements indicate successful sparkline placement; `#hero-delta` presence indicates hawk_score_delta data availability; `.delta-badge` spans indicate active delta data
- **Console diagnostics**: `console.warn('SparklineModule: need ≥3 points')` fires when history insufficient; `console.warn('renderHeroDelta: #hawk-score-display not found')` fires if anchor element missing; `console.warn('setupResizeHandler: SparklineModule not loaded')` fires if script order wrong
- **Export check**: `typeof InterpretationsModule.createDeltaBadge === 'function'` in browser console

## Deviations

- Renamed `badge` variable to `confBadge` in low-confidence badge section to avoid `no-redeclare` ESLint error (new `badge` variable introduced by `createDeltaBadge()` call in same function scope)

## Known Issues

- 9 pre-existing Playwright test failures from data drift (status.json has 5 gauges, tests expect 7 including housing and business_confidence). These failures exist on the baseline commit before any T02 changes.

## Files Created/Modified

- `public/js/interpretations.js` — MODIFIED: Added createDeltaBadge(), restructured renderMetricCard() header with badge and sparkline container, exported createDeltaBadge
- `public/js/gauge-init.js` — MODIFIED: Added renderHeroDelta(), sparkline drawing loop in initGauges(), sparkline resize redraw in setupResizeHandler()
- `.gsd/milestones/M001-pzg4u9/slices/S01/tasks/T02-PLAN.md` — MODIFIED: Added Observability Impact section
