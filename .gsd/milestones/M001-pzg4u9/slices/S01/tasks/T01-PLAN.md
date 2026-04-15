---
estimated_steps: 5
estimated_files: 3
---

# T01: Create SparklineModule and configure build tooling

**Slice:** S01 — Indicator Card Momentum UI
**Milestone:** M001-pzg4u9

## Description

Create the standalone `SparklineModule` as a Canvas 2D IIFE in a new file `public/js/sparklines.js`, add the ESLint globals so the module passes lint, and insert the `<script>` tag in index.html in the correct load order position. This module is the only new file in S01 and all sparkline rendering in later tasks depends on it.

**Key skill:** The `lint` skill (`/Users/annon/.gsd/agent/skills/lint/SKILL.md`) is relevant if ESLint issues arise.

## Steps

1. **Create `public/js/sparklines.js`** — Write the `SparklineModule` IIFE:
   - Public API: `SparklineModule.draw(canvas, history, color, opts)`
   - `canvas`: an HTMLCanvasElement already in the DOM
   - `history`: array of numeric values (the gauge's `history[]` field)
   - `color`: hex string from `GaugesModule.getZoneColor()`
   - `opts`: optional `{ height: 40 }` (default 40px)
   - Return `false` immediately if `history.length < 3` (caller handles placeholder)
   - Filter `history` for valid numbers only (`typeof v === 'number' && isFinite(v)`)
   - Handle retina displays: multiply canvas `.width` / `.height` attributes by `window.devicePixelRatio`, call `ctx.scale(dpr, dpr)`, set CSS `width`/`height` to logical dimensions
   - Read logical width from `canvas.parentElement.offsetWidth` (canvas must already be in the DOM)
   - If `canvas.parentElement.offsetWidth === 0`, return `false` (container not yet visible)
   - Calculate x/y coordinates: distribute points evenly across width, map values to 0–height range
   - **Flat line guard**: if `max === min`, render horizontal line at `height / 2`
   - Draw stroke-only polyline with `ctx.beginPath()`, `moveTo`, `lineTo`, `ctx.stroke()`
   - Draw filled circle (end-dot) at the last point: `ctx.arc()`, `ctx.fill()`
   - Line width: 1.5px. End-dot radius: 2.5px. Line color and dot color both `color` parameter.
   - `console.warn('SparklineModule: need ≥3 points')` when returning false due to insufficient history (aids debugging)
   - **All lines must be ≤88 characters.** Use variable extraction and string concatenation where needed.
   - **No innerHTML.** This module only uses Canvas API, no DOM construction.

2. **Update `eslint.config.js`** — Add `SparklineModule: "writable"` to the globals object (alongside existing modules like GaugesModule, ChartModule etc.). Add `SparklineModule` to the `varsIgnorePattern` regex in the `no-unused-vars` rule (matching the existing pattern of string concatenation).

3. **Update `public/index.html`** — Add `<script src="js/sparklines.js"></script>` in the correct load order: **after** `gauges.js` (SparklineModule needs GaugesModule.getZoneColor at call time, not definition time) and **before** `interpretations.js`. Find the existing `<script src="js/gauges.js">` tag and insert the new tag on the line immediately after it.

4. **Verify ESLint** — Run `npx eslint public/js/sparklines.js` and confirm zero violations.

5. **Verify existing tests** — Run `npx playwright test` (briefly) to confirm the script tag addition doesn't break existing dashboard rendering. The new module defines a global but nothing calls it yet — this is a smoke check.

## Must-Haves

- [ ] `SparklineModule.draw(canvas, history, color, opts)` returns `false` for `history.length < 3`
- [ ] Retina scaling: canvas attributes × devicePixelRatio, ctx.scale(), CSS logical size
- [ ] Flat-line guard: renders horizontal line when all values identical (no division by zero)
- [ ] Non-numeric filtering: filters history for valid finite numbers before drawing
- [ ] Zero-width guard: returns `false` if `canvas.parentElement.offsetWidth === 0`
- [ ] All lines ≤88 characters (ESLint max-len)
- [ ] ESLint globals and varsIgnorePattern updated for SparklineModule
- [ ] Script tag in correct load order in index.html

## Verification

- `npx eslint public/js/sparklines.js` — zero violations, zero warnings
- `npx eslint eslint.config.js` — no config errors
- `npx playwright test` — existing 28+ tests still pass (smoke check)
- `grep -n 'sparklines.js' public/index.html` — script tag present
- `grep -n 'SparklineModule' eslint.config.js` — appears in globals and varsIgnorePattern

## Observability Impact

- **New signal:** `console.warn('SparklineModule: need ≥3 points')` — emitted when `draw()` is called with insufficient history data. Aids debugging cold-start and partial-data scenarios.
- **Inspection:** `typeof SparklineModule` in browser console — confirms the global is defined and the script loaded correctly.
- **Failure visibility:** If the script tag is missing or load-order is wrong, `SparklineModule` will be `undefined` at call sites, producing a `ReferenceError` in the browser console.

## Inputs

- `public/js/gauges.js` — provides `GaugesModule.getZoneColor(value)` API (called at render time, not import time)
- `eslint.config.js` — current globals list and varsIgnorePattern format
- `public/index.html` — current script tag order (gauges.js before interpretations.js)
- `.gsd/milestones/M001-pzg4u9/slices/S01/S01-RESEARCH.md` — full SparklineModule spec, pitfalls (retina blur, zero-width, flat line)

## Expected Output

- `public/js/sparklines.js` — NEW, ~40-60 lines, self-contained Canvas 2D IIFE
- `eslint.config.js` — MODIFIED, SparklineModule added to globals and varsIgnorePattern
- `public/index.html` — MODIFIED, one new script tag line added
