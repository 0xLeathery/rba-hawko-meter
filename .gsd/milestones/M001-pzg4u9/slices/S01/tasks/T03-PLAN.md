---
estimated_steps: 5
estimated_files: 1
---

# T03: Playwright E2E tests for momentum UI features

**Slice:** S01 — Indicator Card Momentum UI
**Milestone:** M001-pzg4u9

## Description

Create `tests/momentum.spec.js` with 8 fixture-based Playwright tests covering all three requirements (R001 delta badges, R002 sparklines, R003 hero delta) including graceful degradation edge cases.

Live `status.json` has no delta fields (inject_deltas() hasn't run on different-day snapshots), so tests **must** use `page.route('**/data/status.json', ...)` to intercept the fetch and inject fixture data with controlled delta values. This pattern is already established in `tests/dashboard.spec.js`.

**Key skill:** The `test` skill (`/Users/annon/.gsd/agent/skills/test/SKILL.md`) is relevant for test generation patterns.

## Steps

1. **Build fixture data factory** — At the top of `tests/momentum.spec.js`:
   - Read live `status.json` via `fs.readFileSync()` (same pattern as dashboard.spec.js)
   - Create a helper `makeFixture(overrides)` that deep-clones the live data and applies overrides to gauges and overall fields
   - Define fixture variants:
     - **withDeltas**: First gauge (inflation) gets `delta: 8.5, delta_direction: "up", previous_value: 50`; second gauge (wages) gets `delta: -6.2, delta_direction: "down", previous_value: 45`; `overall.hawk_score_delta: 2.1, overall.previous_hawk_score: 50`
     - **smallDeltas**: One gauge gets `delta: 3.0, delta_direction: "up"` (below threshold)
     - **noDeltas**: Live data as-is (no delta fields — cold start)
     - **zeroHawkDelta**: `overall.hawk_score_delta: 0, overall.previous_hawk_score: current_score`
     - **shortHistory**: One gauge with `history: [50, 55]` (only 2 points)
   - Use `page.route('**/data/status.json', route => route.fulfill({ json: fixture }))` per test

2. **R001 delta badge tests** (3 tests):
   - **"Delta badge visible when |delta| ≥ 5"**: Use withDeltas fixture. Navigate to `/`. Wait for metric cards to render. Assert `.delta-badge` elements exist. Assert text contains `▲` for the "up" gauge. Assert text contains `▼` for the "down" gauge. Assert magnitude values are present (8.5, 6.2).
   - **"Delta badge absent when |delta| < 5"**: Use smallDeltas fixture. Navigate. Assert no `.delta-badge` elements exist (delta of 3.0 is below threshold).
   - **"Delta badge absent when delta fields missing (cold start)"**: Use noDeltas fixture. Navigate. Assert no `.delta-badge` elements exist.

3. **R002 sparkline tests** (2 tests):
   - **"Sparkline canvas present for indicators with ≥3 history points"**: Use noDeltas fixture (live data has 12+ history points). Navigate. Wait for metric cards. Assert `canvas` elements exist inside `.sparkline-container` divs. Assert at least 5 canvas elements present (5 active gauges in live data).
   - **"Building history placeholder for indicators with <3 history points"**: Use shortHistory fixture (one gauge with only 2 history points). Navigate. Assert that gauge's sparkline container contains text "Building history...".

4. **R003 hero delta tests** (3 tests):
   - **"Hero delta visible with correct arrow when hawk_score_delta present"**: Use withDeltas fixture (hawk_score_delta: 2.1). Navigate. Assert `#hero-delta` element visible. Assert text contains `▲` and `2.1` and `since last update`.
   - **"Hero delta shows 'No change' when hawk_score_delta is zero"**: Use zeroHawkDelta fixture. Navigate. Assert `#hero-delta` contains "No change since last update".
   - **"Hero delta absent when hawk_score_delta missing (cold start)"**: Use noDeltas fixture. Navigate. Assert `#hero-delta` element does NOT exist in the DOM.

5. **Run and verify** — Run `npx playwright test tests/momentum.spec.js` and confirm all 8 pass. Run `npx playwright test` to confirm all existing tests (28+) also pass. Run `python -m pytest tests/python/ -m "not live"` to confirm Python tests (431+) unaffected.

## Must-Haves

- [ ] 8 test cases covering: badge ≥5, badge <5, badge cold-start, sparkline ≥3, sparkline <3, hero positive, hero zero, hero cold-start
- [ ] All tests use `page.route()` to intercept status.json with fixture data
- [ ] Fixture data built by cloning live status.json and applying controlled overrides
- [ ] Tests follow existing patterns: `require('@playwright/test')`, describe blocks, async/await
- [ ] No tests depend on pipeline having produced delta fields in live data
- [ ] All 8 new tests pass
- [ ] All existing 28+ Playwright tests still pass

## Verification

- `npx playwright test tests/momentum.spec.js` — 8 tests pass
- `npx playwright test` — all tests pass (28+ existing + 8 new)
- `python -m pytest tests/python/ -m "not live"` — 431+ tests still pass

## Inputs

- `tests/dashboard.spec.js` — existing fixture/route pattern to follow (read live status.json, use `page.route()` to intercept)
- `public/data/status.json` — live data structure (gauges with history[], no delta fields)
- `public/js/interpretations.js` — `.delta-badge` class name, "Building history..." placeholder text (from T02)
- `public/js/gauge-init.js` — `#hero-delta` element ID, "No change since last update" text, "since last update" text (from T02)
- S01-RESEARCH data contract: `gauge.delta`, `gauge.delta_direction`, `gauge.previous_value`, `overall.hawk_score_delta`, `overall.previous_hawk_score`

## Expected Output

- `tests/momentum.spec.js` — NEW, ~150-200 lines, 8 test cases in describe block
