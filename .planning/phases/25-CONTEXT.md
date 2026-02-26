# Phase 25: Indicator Card UI - Context

**Generated:** 2026-02-26
**Method:** Synthetic discuss (5 agents)
**Status:** Ready for planning

<domain>
## Phase Boundary

**Goal:** Every indicator card shows direction of change and recent trend history at a glance.

Phase 25 adds two visual features to the existing indicator card UI: delta badges and Canvas 2D sparklines. Delta badges show a directional arrow with magnitude (e.g., "▲ 8.3") on cards where the gauge value changed by 5 or more points since the previous pipeline run. Sparklines show the trend history from the existing `history[]` array in status.json as a minimal Canvas 2D line chart. The hero section gains a hawk score delta display below the score. All features consume data from Phase 24's `previous_value`, `delta`, and `delta_direction` fields, plus the pre-existing `history[]` arrays. No backend changes are required.

**Requirements:** DELT-01, DELT-02, DELT-03, DELT-04, SPRK-01, SPRK-02, SPRK-03, SPRK-04
**Depends on:** Phase 24 (delta fields in status.json)
**Downstream consumers:** Phase 27 (historical chart uses snapshots, not sparklines)
</domain>

<decisions>
## Implementation Decisions

### 1. Delta badge placement: in the card header row
**Consensus: 5/5 -- Locked Decision**

All agents agree: the delta badge belongs in the header row of each metric card, between the indicator label and the importance badge. The header row already uses `flex items-center justify-between` in `renderMetricCard()`. Restructure it as a 3-item flex: label (left), delta badge (center/right), importance badge (far right).

**Rationale:** Users scan top-to-bottom. The delta badge must be visible at the card's first line. Placing it near the gauge or interpretation text buries it below the fold on smaller cards.

**Mobile concern (from QA):** The header could get crowded with long labels like "Building Approvals". Group the delta badge and importance badge into a right-aligned `div` so they wrap together if needed. Test at 320px viewport width.

### 2. Hero hawk score delta: below the score as a separate element
**Consensus: 5/5 -- Locked Decision**

Insert a new `div#hero-delta` between `#hawk-score-display` and `#scale-explainer` in the hero card. Format: `[arrow] [+/-X.X] since last update`.

**Display rules:**
- If `data.overall.hawk_score_delta` exists AND is non-zero: show coloured arrow + delta value + "since last update"
- If `data.overall.hawk_score_delta` exists AND is zero: show "No change since last update" in gray-500
- If `data.overall.hawk_score_delta` is absent (cold start / first run): do not render the element at all (DELT-04)

**Styling:** `text-base text-center mt-2`. Arrow + delta number coloured by `getZoneColor(data.overall.hawk_score)`. The "since last update" text in gray-400.

**Rationale:** One additional line in a 6-element hero card is acceptable information density. The delta adds high-value momentum context without cluttering the visual hierarchy.

### 3. Sparkline module: new `sparklines.js` IIFE module
**Consensus: 4/5 -- Locked Decision** (Devil's Advocate conceded)

Create a new file `public/js/sparklines.js` as a dedicated IIFE module exporting a single public function: `SparklineModule.draw(canvasElement, historyArray, color)`.

**Script load order in index.html:**
```
gauges.js -> sparklines.js -> interpretations.js -> gauge-init.js
```

Sparklines.js must load after gauges.js (to access `GaugesModule.getZoneColor()`) and before gauge-init.js (which orchestrates rendering).

**Module responsibilities:**
- Validate input (array length >= 3, non-empty, numeric values)
- Normalize history values to canvas coordinate space
- Draw a stroke-only line with an end-dot
- Return early with no rendering for invalid input (caller handles placeholder)

**Rationale:** Canvas 2D rendering is fundamentally different from Plotly gauge rendering (GaugesModule) and from DOM construction (InterpretationsModule). A dedicated module maintains single-responsibility. At ~40-50 lines of code, it's small enough to be a single function module.

**Devil's Advocate concern:** A whole new module for 40 lines seems heavy. Counter: the IIFE pattern is the project convention for all JS files. Consistency outweighs minimalism. The module will grow if sparkline features expand (e.g., hover tooltips in a future phase).

### 4. Sparkline visual design: stroke-only with end-dot
**Consensus: 5/5 -- Locked Decision**

All agents agree on the minimal design:
- **Line:** Stroke-only (no fill/gradient), 1.5px line width
- **Colour:** Single zone colour from `getZoneColor(currentGaugeValue)` -- uses the card's current gauge value, not per-point colours
- **End-dot:** 3px radius circle at the last data point to indicate "current position"
- **Dimensions:** 40px max height (per SPRK-04), full card width via `width: 100%` on canvas element
- **Padding:** 2px top/bottom to prevent line clipping at extremes (0 or 100 values)
- **Normalization:** Scale history values from their actual min/max to the 2px-padded canvas height
- **No axes, no labels** (per SPRK-04)

**Canvas element attributes:** Set `width` to the canvas element's `offsetWidth` at render time (for crisp pixel rendering). Set `height` to 40. Handle devicePixelRatio for retina displays by scaling the canvas backing store.

**Edge cases (from QA):**
- Flat line (all values identical): renders as a horizontal line at vertical center -- correct behaviour
- Values at 0 and 100: 2px padding prevents clipping
- Single non-numeric value in array: filter out NaN/undefined before rendering

### 5. Delta badge visual design: Unicode arrows with zone colour
**Consensus: 5/5 -- Locked Decision**

All agents agree on the badge format:

**Characters:** `\u25B2` (▲ up), `\u25BC` (▼ down). No badge for unchanged or below threshold.

**Display threshold:** Show badge only when `|delta| >= 5` gauge points (per DELT-01). This is a FRONTEND display concern. The pipeline provides raw delta; the frontend filters.

**Format:** `[arrow] [absValue]` e.g., "▲ 8.3" or "▼ 12.1". Show absolute value of delta (no sign character -- the arrow conveys direction).

**Colour:** Zone colour from `getZoneColor(currentGaugeValue)` per DELT-03. Applied via `element.style.color` (not Tailwind class concatenation -- matching the established pattern).

**ASIC compliance note:** Zone colour is neutral -- it represents the absolute position on the 0-100 scale, not "good/bad." No opinion is conveyed.

**Boundary conditions (from QA):**
- `|delta| === 5.0`: show badge (>= 5, not > 5)
- `|delta| === 4.9`: no badge
- `delta === 0`: no badge
- `delta` field absent: no badge (DELT-04)
- `previous_value` field absent: no badge (DELT-04)

### 6. "Building history..." placeholder: gray italic text, matched height
**Consensus: 5/5 -- Locked Decision**

When `history.length < 3`, display a `<p>` element instead of a canvas:
- Text: "Building history..."
- Style: `text-xs text-gray-500 italic`, centered horizontally and vertically
- Height: 40px (matching sparkline height) to prevent layout shift
- Container: same div that would hold the canvas, with `flex items-center justify-center` and `height: 40px`

**Rendering logic location:** The check belongs in the sparkline rendering call in `gauge-init.js`. Before calling `SparklineModule.draw()`, check `metricData.history.length >= 3`. If not, create the placeholder `<p>` element. SparklineModule.draw() itself should also validate and return `false` if the array is too short (defensive programming).

**Edge cases (from QA):**
- `history` is `undefined` or `null`: show placeholder
- `history` is `[]` (empty array): show placeholder
- `history` has exactly 3 points: render sparkline (threshold is < 3)
- `history` has 2 points: show placeholder
- `history` has non-numeric values mixed in: filter before counting

### Claude's Discretion

#### Canvas element creation and insertion point
The canvas element for the sparkline should be appended AFTER the gauge container and BEFORE the interpretation text in the card DOM. This positions the sparkline visually between the Plotly gauge (showing current value) and the text interpretation (explaining it). The sparkline serves as a visual bridge: "here's where you are (gauge) and here's the trend (sparkline) and here's what it means (text)."

DOM order in renderMetricCard:
1. Header (label + delta badge + importance)
2. Low confidence badge (if applicable)
3. Gauge container (`div#gauge-{id}`)
4. **Sparkline container (NEW -- `div#sparkline-{id}`)** or placeholder
5. Interpretation text
6. "Why it matters" text
7. Source citation

#### Delta badge construction in renderMetricCard
Add a helper function `createDeltaBadge(metricData)` to InterpretationsModule that returns a DOM element or null. This keeps the badge creation logic testable and separated from card layout. The function reads `metricData.delta`, `metricData.delta_direction`, and checks `|delta| >= 5`. Returns null if conditions aren't met. The caller (`renderMetricCard`) simply checks if the return is non-null before appending.

#### Retina/HiDPI canvas scaling
For crisp sparklines on retina displays, multiply canvas width/height attributes by `window.devicePixelRatio`, then scale the context with `ctx.scale(dpr, dpr)`, and set CSS width/height to the logical size. This is a standard Canvas 2D pattern and should be handled inside `SparklineModule.draw()`.
</decisions>

<specifics>
## Specific Ideas

### From UX Designer
- **Delta badge typography:** Use `text-xs font-semibold` for the badge to differentiate it from the `text-xs text-gray-500` importance label. The font weight distinction makes the badge scannable.
- **Sparkline container spacing:** Add `mt-1 mb-1` to the sparkline container for breathing room between gauge and interpretation. The gauge already has no bottom margin, so this prevents them from feeling cramped.
- **Hero delta animation:** If reduced motion is not preferred, apply the same `hero-animate-in` class to the delta element. It should fade in with the rest of the hero card, not pop in separately.
- **Accessibility:** Add `aria-label` to the delta badge: e.g., `aria-label="Inflation gauge increased by 8.3 points"`. Screen readers should convey the delta without relying on visual arrows.

### From Engineer
- **Canvas resize on window resize:** The existing `setupResizeHandler()` in gauge-init.js handles Plotly relayout. Extend it to redraw sparklines on resize. Store references to rendered sparkline canvases and their data. On resize, recalculate canvas width and redraw.
- **SparklineModule.draw() signature:** `draw(canvasElement, historyArray, color, options)` where options is an optional object with `{ lineWidth: 1.5, dotRadius: 3, padding: 2 }`. Defaults baked in but overridable for testing or future customization.
- **No innerHTML:** All badge construction must use `createElement`/`textContent`/`appendChild` per ESLint enforcement. Unicode characters assigned via `textContent` (not entity references).
- **Script tag in index.html:** Add `<script src="js/sparklines.js"></script>` after `gauges.js` and before `interpretations.js` in the existing script block at bottom of `<body>`.

### From QA / Edge Cases
- **Playwright E2E test additions:**
  1. Verify delta badge appears on at least one indicator card when delta data exists in status.json
  2. Verify delta badge does NOT appear when delta < 5
  3. Verify sparkline canvas element exists for indicators with >= 3 history points
  4. Verify "Building history..." placeholder appears for business_confidence (currently 1 history point)
  5. Verify hero delta element appears when hawk_score_delta is present
  6. Verify hero delta element is absent when hawk_score_delta is not in status.json
- **Unit-testable functions:** `createDeltaBadge()` and sparkline normalization logic should be pure functions testable without DOM. Extract the math (normalize array to 0-1 range, compute canvas coordinates) into testable utilities.
- **Current status.json has no delta fields:** The live status.json doesn't yet contain delta/previous_value because no second pipeline run has occurred. Testing will require either: (a) a mock status.json with delta fields injected, or (b) running the pipeline twice. Recommend option (a) for Playwright tests.

### From Product Owner
- **business_confidence is the litmus test:** With only 1 history point, it MUST show "Building history..." not a broken sparkline. This is the most visible edge case in production.
- **Progressive enhancement principle:** If sparklines.js fails to load (CDN issue in future), the card should still be functional. The sparkline is additive -- the card works without it. No hard dependency.
- **"Since last update" wording over "since last week":** The pipeline runs weekly but could be triggered manually. "Since last update" is always accurate; "since last week" could be misleading if the pipeline ran twice in one week.

### From Devil's Advocate
- **Zone colour for delta badge is the CURRENT value's zone, not the delta's magnitude zone.** A delta of +12 on a gauge at 30 (cool zone) would show a blue-coloured up arrow. This is correct: it tells the user "this cool-zone indicator is rising." But some users might expect green/red for direction. The DELT-03 requirement explicitly says zone colours, so follow the spec. Document this in code comments.
- **Sparkline min/max normalization risk:** If all history values are in a narrow range (e.g., 58-62), the sparkline will exaggerate small fluctuations. This is actually DESIRABLE -- it shows the trend more clearly. But add a comment explaining the normalization choice.
- **The 5-point threshold is arbitrary.** Acknowledged. But it's specified in DELT-01. If it needs tuning, it can be changed in one place (the frontend check). The pipeline deliberately omits the threshold to keep concerns separated (Phase 24 CONTEXT decision).
</specifics>

<deferred>
## Deferred Ideas

### Sparkline hover/tap tooltip
The Devil's Advocate suggested showing the exact value on hover/tap for sparkline data points. The group agreed this adds complexity (hit detection on canvas, tooltip positioning) for marginal value. Sparklines are meant to be glanceable, not interactive. **Deferred to future enhancement.**

### Multi-zone sparkline colouring
The UX Designer considered colouring each segment of the sparkline based on the zone of each data point (blue for cool, red for hot, etc.). This would require drawing multiple path segments with different stroke colours. The group agreed this is visually noisy and overengineered for a 40px-tall chart. Single zone colour from the current value is sufficient. **Deferred: not needed.**

### Delta badge animation
The UX Designer suggested a brief scale-in animation on the delta badge (pulse or bounce). The group rejected this: the dashboard already has CountUp animation, gauge sweep, and fadeSlideIn. Adding another animation risks feeling "busy." The badge should appear statically. **Deferred: not needed.**

### Configurable delta threshold
The Devil's Advocate raised whether the |delta| >= 5 threshold should be configurable (e.g., via a constant at the top of the module). The Engineer agreed it should be a named constant (not a magic number), but it doesn't need to be user-configurable or stored in status.json. **Implementation detail: use `var DELTA_DISPLAY_THRESHOLD = 5;` as a module constant.**

### Delta percentage display
The Product Owner asked whether to show delta as a percentage of the gauge range (e.g., "+8.3%" instead of "+8.3 points"). The group agreed that "points" is clearer for a 0-100 gauge. Percentage of percentage is confusing. The format "▲ 8.3" without units is cleanest -- the context (it's on a /100 gauge) makes units unnecessary. **Deferred: not needed.**

### Sparkline fill gradient
The Engineer considered a semi-transparent gradient fill below the sparkline stroke for visual depth. The group decided this adds visual noise on a dark background with 7 cards. Stroke-only is cleaner. **Deferred: not needed.**
</deferred>
