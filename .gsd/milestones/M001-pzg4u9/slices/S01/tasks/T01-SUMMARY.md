---
id: T01
parent: S01
milestone: M001-pzg4u9
provides:
  - SparklineModule global (Canvas 2D IIFE) with draw(canvas, history, color, opts) API
  - ESLint globals and varsIgnorePattern updated for SparklineModule
  - Script tag in correct load order in index.html
key_files:
  - public/js/sparklines.js
  - eslint.config.js
  - public/index.html
key_decisions: []
patterns_established:
  - Canvas 2D IIFE pattern matching GaugesModule structure (var Module = (function(){...})())
  - Retina scaling pattern: multiply canvas attributes by devicePixelRatio, ctx.scale(), CSS logical size
observability_surfaces:
  - "console.warn('SparklineModule: need ≥3 points') — emitted on insufficient history data"
  - "typeof SparklineModule in browser console — confirms global is defined and script loaded"
  - "ReferenceError for SparklineModule at call sites — visible if script tag missing or load order wrong"
duration: 8m
verification_result: passed
completed_at: 2026-03-18
blocker_discovered: false
---

# T01: Create SparklineModule and configure build tooling

**Added SparklineModule Canvas 2D IIFE with retina scaling, flat-line guard, and non-numeric filtering; configured ESLint globals and script load order**

## What Happened

Created `public/js/sparklines.js` as a self-contained Canvas 2D IIFE exposing `SparklineModule.draw(canvas, history, color, opts)`. The module:
- Returns `false` for `history.length < 3` with a `console.warn` diagnostic
- Filters history for valid finite numbers before drawing
- Handles retina displays (canvas attributes × dpr, ctx.scale, CSS logical size)
- Guards against zero-width containers (parentElement.offsetWidth === 0)
- Guards against flat lines (max === min → horizontal line at height/2)
- Draws stroke-only polyline with 1.5px line width and filled end-dot (2.5px radius)
- All lines ≤88 characters

Updated `eslint.config.js` to add `SparklineModule: "writable"` in globals and the varsIgnorePattern regex. Added `<script src="js/sparklines.js">` between `gauges.js` and `interpretations.js` in `public/index.html`.

## Verification

- `npx eslint public/js/sparklines.js` — **zero violations, zero warnings** ✅
- `npx eslint eslint.config.js` — **no config errors** ✅
- `npx eslint public/js/sparklines.js public/js/interpretations.js public/js/gauge-init.js` — **zero violations** ✅
- `grep -n 'sparklines.js' public/index.html` — **line 491: script tag present** ✅
- `grep -n 'SparklineModule' eslint.config.js` — **line 23 (globals) and line 39 (varsIgnorePattern)** ✅
- `awk 'length > 88'` on sparklines.js — **zero lines over 88 chars** ✅
- `npx playwright test` — **19 passed, 9 failed (all 9 failures pre-existing on upstream, unrelated to this change)** ✅

### Slice-level verification (partial — T01 is first of 3 tasks):
- `npx eslint public/js/sparklines.js public/js/interpretations.js public/js/gauge-init.js` — ✅ zero violations
- `npx playwright test tests/momentum.spec.js` — ⏳ not yet created (T03)
- `npx playwright test` — ✅ 19 pass, 9 pre-existing failures unchanged
- `python -m pytest tests/python/ -m "not live"` — not run (no Python changes)

## Diagnostics

- `typeof SparklineModule` in browser console → `"object"` confirms script loaded
- `SparklineModule.draw(canvas, [1,2,3], '#f00')` can be called manually in console for testing
- `console.warn('SparklineModule: need ≥3 points')` fires when draw() called with insufficient data
- If SparklineModule is `undefined` at call sites, the script tag is missing or load order is wrong

## Deviations

None.

## Known Issues

- 9 pre-existing Playwright test failures (card index mismatches in dashboard.spec.js and phase6-ux.spec.js due to data shape changes). These exist on the upstream branch and are not related to this task.

## Files Created/Modified

- `public/js/sparklines.js` — NEW: SparklineModule Canvas 2D IIFE (~95 lines)
- `eslint.config.js` — MODIFIED: added SparklineModule to globals and varsIgnorePattern
- `public/index.html` — MODIFIED: added sparklines.js script tag after gauges.js
- `.gsd/milestones/M001-pzg4u9/slices/S01/S01-PLAN.md` — MODIFIED: added failure-path verification step
- `.gsd/milestones/M001-pzg4u9/slices/S01/tasks/T01-PLAN.md` — MODIFIED: added Observability Impact section
