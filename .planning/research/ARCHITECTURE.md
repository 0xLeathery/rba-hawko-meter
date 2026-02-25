# Architecture Research

**Domain:** Static dashboard frontend — visual/UX overhaul of existing vanilla JS IIFE app
**Researched:** 2026-02-25
**Confidence:** HIGH (all findings derived from direct codebase inspection — no guesswork)

## Context: What This Research Covers

v4.0 adds three frontend features to an existing 468-line single-file HTML app with IIFE JS modules
and Tailwind CDN. This document answers four specific questions:

1. Where in the HTML does a hero section live?
2. How does a verdict explanation component read from status.json?
3. What CSS patterns work for dark theme polish without a build system?
4. What is the right build order given shared data dependencies?

All conclusions are drawn from direct inspection of `public/index.html`, `public/js/gauge-init.js`,
`public/js/interpretations.js`, `public/js/gauges.js`, `public/js/main.js`, `public/js/data.js`,
and `public/data/status.json`.

---

## System Overview

### Current Architecture (v3.0, unchanged by v4.0)

```
index.html (468 LOC)
  │
  ├── <head>
  │     Tailwind CDN + inline tailwind.config (custom color tokens)
  │     Decimal.js CDN
  │     Plotly.js CDN
  │     <style> block — scrollbar, chart-details media query
  │
  ├── <body>
  │     ├── <aside>   disclaimer-banner (ASIC COMP-03)
  │     ├── <header>  site title + tagline
  │     │
  │     ├── <main>    max-w-6xl mx-auto
  │     │     ├── #onboarding         <details> explainer
  │     │     ├── #hawk-o-meter-section   ← HERO GAUGE lives here now
  │     │     │     ├── #hero-gauge-plot  (Plotly, lg:col-span-3)
  │     │     │     ├── #asx-futures-container (lg:col-span-2)
  │     │     │     ├── RBA cash rate card
  │     │     │     ├── #verdict-container
  │     │     │     ├── #calculator-jump-link
  │     │     │     └── #scale-explainer
  │     │     ├── #countdown-section
  │     │     ├── chart-details       rate history chart
  │     │     ├── #individual-gauges-section
  │     │     ├── #methodology        <details>
  │     │     └── #calculator-section
  │     │
  │     └── "What to do next" section (outside <main>)
  │
  ├── <footer id="disclaimer">
  │
  └── <script> blocks (in order):
        data.js → chart.js → countdown.js → calculator.js
        → main.js → gauges.js → interpretations.js → gauge-init.js
```

### Data Flow (unchanged by v4.0)

```
Page load
    │
    ▼
DataModule.fetch("data/status.json")     [gauge-init.js, one fetch, cached]
    │
    ├─► GaugesModule.createHeroGauge()   data.overall.hawk_score
    ├─► InterpretationsModule.renderVerdict()   data.overall
    ├─► InterpretationsModule.renderASXTable()  data.asx_futures
    ├─► renderMetricGauges()             data.gauges (all 7 indicators)
    └─► renderCalculatorBridge()         data.overall.hawk_score

DataModule.fetch("data/rates.json")      [main.js, parallel]
DataModule.fetch("data/meetings.json")   [main.js, parallel]
```

Key constraint: `DataModule` caches by URL. Any module can call
`DataModule.fetch("data/status.json")` a second time and get the cached result
synchronously (as a resolved Promise). No coordination protocol is needed for
new modules that need status.json data.

---

## Component Responsibilities

| Module | Responsibility | Exposes |
|--------|---------------|---------|
| `data.js` (DataModule) | Fetch + cache JSON; showError/showLoading UI helpers | `fetch`, `showError`, `showLoading` |
| `gauges.js` (GaugesModule) | Plotly gauge rendering; zone colors/labels; display labels | `createHeroGauge`, `createBulletGauge`, `getZoneColor`, `getStanceLabel`, `getDisplayLabel` |
| `interpretations.js` (InterpretationsModule) | All text rendering: verdict, ASX table, metric cards, staleness | `renderVerdict`, `renderASXTable`, `renderMetricCard`, `getPlainVerdict`, `getWhyItMatters`, `generateMetricInterpretation` |
| `gauge-init.js` (IIFE, anonymous) | Orchestrator: fetches status.json, calls all render functions in sequence | None (self-executing) |
| `main.js` (IIFE, anonymous) | Orchestrator: fetches rates.json + meetings.json; initialises calculator; handles resize | None (self-executing) |
| `calculator.js` (CalculatorModule) | Mortgage math and UI | `init` |
| `chart.js` (ChartModule) | Plotly rate history chart | `create`, `resize` |
| `countdown.js` (CountdownModule) | RBA meeting countdown timer | `start` |

---

## Recommended Project Structure

No new directories are needed. v4.0 adds one new JS file and modifies index.html + gauge-init.js.

```
public/
├── index.html                  MODIFIED — hero restructure + verdict-explanation div
├── js/
│   ├── data.js                 UNCHANGED
│   ├── gauges.js               UNCHANGED
│   ├── interpretations.js      MODIFIED — add renderVerdictExplanation()
│   ├── gauge-init.js           MODIFIED — call renderVerdictExplanation() after gauges render
│   ├── main.js                 UNCHANGED
│   ├── calculator.js           UNCHANGED
│   ├── chart.js                UNCHANGED
│   └── countdown.js            UNCHANGED
└── data/
    └── status.json             UNCHANGED (no schema changes)
```

---

## Architectural Patterns

### Pattern 1: Hero Section Placement — Replace, Don't Precede

**What:** The v4.0 hero section (verdict + hawk score dominant) replaces the current
`#hawk-o-meter-section` content layout, not precedes it. The section already exists at the
right position in the DOM — it just needs internal restructuring.

**Current layout inside `#hawk-o-meter-section`:**
```
grid lg:grid-cols-5
  col-span-3  →  hero-gauge-plot  (Plotly gauge)
  col-span-2  →  asx-futures-container + cash rate card

#verdict-container  (beneath grid, text only, small)
#calculator-jump-link
#scale-explainer
```

**v4.0 target layout:**
```
#verdict-container   ← PROMOTE to top of section, large typography, full-width
#hawk-o-meter-section content  ← gauge + side panels remain below
```

**Why replace vs precede:** Adding a new `<section>` above `#hawk-o-meter-section` would
push the existing gauge content below the fold on mobile AND duplicate the section landmark
role. The ASIC compliance banner + header + onboarding section already consume vertical space.
Promoting `#verdict-container` to the top of the existing section preserves the DOM structure
while achieving the above-the-fold hierarchy.

**Concrete implementation approach:**
Move `#verdict-container` from its current position (after the 5-column grid) to before
the grid within the same section. Increase its typography weight and size. The existing
`id` attribute means gauge-init.js's `InterpretationsModule.renderVerdict('verdict-container', data.overall)`
continues to work with zero JS changes.

**When to use this approach:** Any time a new visual feature targets an already-named
container that existing JS renders into. The HTML structure owns the DOM position; the JS
only cares about the element ID.

### Pattern 2: Verdict Explanation — Extend InterpretationsModule, Not a New IIFE

**What:** The verdict explanation ("why is the score X?") reads `data.gauges` and
`data.overall.hawk_score` to produce a short list of indicator contributions. This is a
render function, not an orchestration function.

**Why extend InterpretationsModule rather than a new IIFE:**
- `data.gauges` is already available in `gauge-init.js`'s `.then()` callback as `data`
- InterpretationsModule already has `getWhyItMatters(metricId)` and
  `generateMetricInterpretation(metricId, metricData)` — the explanation needs both
- A new IIFE would need to make a second `DataModule.fetch("data/status.json")` call
  (returns cached result, so no network cost, but adds an unnecessary orchestration point)
- Existing test surface (Playwright) targets InterpretationsModule's rendered output;
  staying in the same module keeps test targeting consistent

**New function signature:**
```javascript
// in interpretations.js
function renderVerdictExplanation(containerId, gaugesData, overallScore) {
  // 1. Sort indicators by contribution to score (value * weight, descending)
  // 2. Pick top 3 hawkish and top 2 dovish drivers
  // 3. Render a brief "what's pushing the score up/down" list
  // 4. ASIC constraint: neutral framing — "X is above average" not "X is bad"
}

// Expose in the return object
return {
  // existing...
  renderVerdictExplanation: renderVerdictExplanation
};
```

**Call site in gauge-init.js:**
```javascript
DataModule.fetch('data/status.json')
  .then(function (data) {
    // existing calls...
    GaugesModule.createHeroGauge('hero-gauge-plot', data.overall.hawk_score);
    InterpretationsModule.renderVerdict('verdict-container', data.overall);

    // NEW — call after gauge data is ready
    InterpretationsModule.renderVerdictExplanation(
      'verdict-explanation',
      data.gauges,
      data.overall.hawk_score
    );

    // existing calls continue...
    renderMetricGauges(data.gauges);
  });
```

**status.json fields available for explanation logic:**
- `data.gauges[id].value` — 0-100 gauge score
- `data.gauges[id].weight` — contribution weight (0.05–0.25)
- `data.gauges[id].zone_label` — "Mild hawkish pressure", "Balanced", etc.
- `data.gauges[id].z_score` — signed deviation; negative = dovish, positive = hawkish
- `data.gauges[id].raw_value` — actual statistic (3.76% CPI, 5.45% WPI, etc.)
- `data.gauges[id].confidence` — "HIGH"/"LOW" — respect in UI (show "low confidence" badge)

**ASIC constraint for explanation copy:** The existing `getWhyItMatters` and
`generateMetricInterpretation` functions already use neutral framing. The verdict
explanation must follow the same pattern: "Wages grew X% — above the historical average"
is compliant; "Wages are dangerously high" is not.

### Pattern 3: CSS Polish Without a Build System — Tailwind CDN + Inline Style Block

**What:** Tailwind CDN (v3 via `cdn.tailwindcss.com`) with an inline `tailwind.config`
block and a `<style>` block in `<head>`. This is the only mechanism available without
introducing a build step.

**The existing config block already defines all custom tokens:**
```javascript
tailwind.config = {
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        'finance-dark': '#0a0a0a',
        'finance-gray': '#1a1a1a',
        'finance-border': '#2d2d2d',
        'finance-accent': '#60a5fa',
        'gauge-green': '#10b981',
        'gauge-amber': '#f59e0b',
        'gauge-red': '#ef4444'
      }
    }
  }
}
```

These tokens can be used directly in new HTML with standard Tailwind class syntax.

**What CDN Tailwind supports (relevant to visual polish):**

HIGH confidence (observed in existing codebase):
- All utility classes: spacing (`p-4`, `mt-6`, `gap-4`), typography (`text-xl`, `font-bold`,
  `tracking-tight`), colour (`text-gray-200`, `bg-finance-gray`, `border-finance-border`)
- Responsive prefixes: `sm:`, `md:`, `lg:` — already used throughout
- State variants: `hover:`, `focus:`, `group-open:` — already used
- Opacity modifiers: `bg-finance-gray/50`, `border-finance-border/50` — already used
- Arbitrary values: `h-[500px]` — already used in chart section

**CSS patterns for dark theme visual polish (no build step needed):**

```html
<!-- Large verdict text — promote hierarchy -->
<div class="text-3xl sm:text-4xl font-black tracking-tight text-center">

<!-- Subtle card with coloured left border (zone indicator) -->
<div class="bg-finance-gray border border-finance-border border-l-4 border-l-[#60a5fa] rounded-xl p-5">

<!-- Score emphasis with monospace number rendering -->
<span class="text-5xl font-bold tabular-nums" style="color: #60a5fa;">

<!-- Divider line -->
<hr class="border-finance-border my-6">

<!-- Muted label / eyebrow text -->
<p class="text-xs text-gray-500 uppercase tracking-widest mb-2">

<!-- Progress/contribution bar (pure CSS, no JS) -->
<div class="h-1.5 rounded-full bg-finance-border overflow-hidden">
  <div class="h-full rounded-full" style="width: 73%; background: #60a5fa;"></div>
</div>
```

**What CDN Tailwind does NOT support:**

- `@apply` directives in `<style>` blocks — CDN does not process CSS at build time.
  Use class strings directly on elements instead.
- Custom animations beyond `animate-pulse`, `animate-spin` — no custom keyframe support
  without a `<style>` block.
- JIT-only arbitrary variants like `[&>div]:` — avoid; use standard class composition.

**The inline `<style>` block is the escape hatch** for anything Tailwind CDN cannot express:

```html
<style>
  /* Existing */
  html { scroll-behavior: smooth; }
  /* Add for visual polish: */
  .verdict-hero-card {
    background: linear-gradient(135deg, #1a1a1a 0%, #0f172a 100%);
  }
  .indicator-bar-fill {
    transition: width 0.6s ease-out;
  }
</style>
```

**When to use `<style>` vs Tailwind classes:**
- Transitions/animations: `<style>` block — CDN JIT does not support `transition-[width]`
- Gradients more complex than `from-/to-` built-ins: `<style>` block
- `::-webkit-*` pseudo-elements: already in `<style>` block, extend there
- Everything else: Tailwind classes

### Pattern 4: Script Loading Order — Add New Module Before gauge-init.js

**What:** The existing script loading order at the bottom of `<body>` reflects dependency
order. Any new module that provides functions called by `gauge-init.js` must load before it.
Any module that merely reuses `InterpretationsModule` is safe extending that existing file.

**Current order:**
```html
<script src="js/data.js"></script>        <!-- DataModule -->
<script src="js/chart.js"></script>       <!-- ChartModule -->
<script src="js/countdown.js"></script>   <!-- CountdownModule -->
<script src="js/calculator.js"></script>  <!-- CalculatorModule -->
<script src="js/main.js"></script>        <!-- IIFE orchestrator (rates + meetings) -->
<script src="js/gauges.js"></script>      <!-- GaugesModule -->
<script src="js/interpretations.js"></script>  <!-- InterpretationsModule -->
<script src="js/gauge-init.js"></script>  <!-- IIFE orchestrator (status.json) -->
```

**v4.0 does NOT need a new script tag** if `renderVerdictExplanation` is added to
`interpretations.js`. The function loads with that existing file. `gauge-init.js` already
loads after `interpretations.js` and calls into it — this works without order change.

**If a new module IS introduced** (e.g., `verdict-explanation.js`):
```html
<!-- Insert before gauge-init.js, after interpretations.js -->
<script src="js/interpretations.js"></script>
<script src="js/verdict-explanation.js"></script>  <!-- NEW -->
<script src="js/gauge-init.js"></script>
```

This preserves the pattern: library modules (GaugesModule, InterpretationsModule) load
before orchestrator IIFEs that consume them.

---

## Data Flow

### v4.0 Status.json Consumption Map

```
DataModule.fetch("data/status.json")   [single fetch, cached]
    │
    ├── data.overall.hawk_score ─────► GaugesModule.createHeroGauge()
    │                                  InterpretationsModule.renderVerdict()
    │                                  renderCalculatorBridge()
    │
    ├── data.overall ─────────────────► InterpretationsModule.renderVerdict()
    │
    ├── data.asx_futures ─────────────► InterpretationsModule.renderASXTable()
    │
    ├── data.gauges ──────────────────► renderMetricGauges()   [gauge-init.js]
    │                                   InterpretationsModule.renderMetricCard()
    │                                                           (called per indicator)
    │
    └── data.gauges + data.overall.hawk_score ──► [NEW] InterpretationsModule.renderVerdictExplanation()
```

No new data sources. No changes to status.json schema. All v4.0 features consume
the same data already fetched by gauge-init.js.

### Verdict Explanation Calculation Logic

The explanation must rank indicators by their contribution to the hawk score diverging
from 50. Contribution = `(value - 50) * weight`. Positive contribution = hawkish pressure.

```
Example with current status.json:
  wages:     value=84.8, weight=0.15  → contribution = (84.8-50) * 0.15 = +5.22  (hawkish)
  inflation: value=30.2, weight=0.25  → contribution = (30.2-50) * 0.25 = -4.95  (dovish)
  employment:value=33.7, weight=0.15  → contribution = (33.7-50) * 0.15 = -2.45  (dovish)
  spending:  value=60.4, weight=0.10  → contribution = (60.4-50) * 0.10 = +1.04  (hawkish)
  ...
```

Sort by absolute contribution. Top 3 explain the most of the current score.
Render as: "[Indicator] is [above/below] average — pushing the score [up/down]."

ASIC-safe framing already exists in `generateMetricInterpretation()` — re-use it,
don't write new copy from scratch.

---

## Build Order

Build features in this sequence. Dependencies drive the order.

**Phase 1: HTML Restructure — Hero Section**

Modify `index.html` only. No JS changes.

1. Move `#verdict-container` above the 5-column gauge grid inside `#hawk-o-meter-section`
2. Increase verdict typography (larger text class, bolder weight)
3. Add `id="verdict-explanation"` container below the verdict (empty div — JS fills it)
4. Adjust grid layout if verdict now occupies full width above gauge

Dependency: None. Can be done before any JS work. The existing
`InterpretationsModule.renderVerdict('verdict-container', ...)` call continues to work
because the element ID is unchanged.

Verification: Load page — verdict should appear above-the-fold before the gauge.
`#verdict-explanation` remains empty (intentional until Phase 2).

**Phase 2: Verdict Explanation Component**

Add `renderVerdictExplanation(containerId, gaugesData, overallScore)` to
`interpretations.js` and wire the call in `gauge-init.js`.

1. Add `renderVerdictExplanation` function to `interpretations.js` (before the `return` object)
2. Expose it in `return { ..., renderVerdictExplanation: renderVerdictExplanation }`
3. In `gauge-init.js` `.then()`, after `renderVerdict`, add:
   `InterpretationsModule.renderVerdictExplanation('verdict-explanation', data.gauges, data.overall.hawk_score);`

Dependency: Phase 1 must have created `id="verdict-explanation"` in the HTML.
The function must reference `GaugesModule.getZoneColor()` (already available) for
colour-coded indicators.

Verification: Score explanation appears below the verdict verdict label with 3-5 indicator
lines, all using neutral ASIC-safe language. Each line matches the `getWhyItMatters`
pattern — no financial advice framing.

**Phase 3: Visual Polish**

Modify `index.html` CSS classes and the `<style>` block.

1. Typography hierarchy — section headings, card labels, body text must form a clear scale
2. Consistent spacing — audit `py-` and `px-` values across all sections; standardise
3. Colour hierarchy — verdict zone colour (blue/grey/red) should bleed into the hero
   section treatment (left border, text accent)
4. Dark theme refinement — card backgrounds, border treatments, separator lines

Dependency: Phases 1 and 2 establish final DOM structure before CSS is tuned. Polish
after structure is stable to avoid rework.

Verification: Screenshot above-the-fold before/after. Key check: verdict + score visible
without scrolling on mobile (375px viewport) and desktop (1280px viewport).

---

## Integration Points

### New vs Modified

| File | Change Type | What Changes |
|------|-------------|-------------|
| `public/index.html` | Modified | Hero section restructure; `#verdict-explanation` div added; CSS class updates for visual polish |
| `public/js/interpretations.js` | Modified | Add `renderVerdictExplanation()` function; expose in return object |
| `public/js/gauge-init.js` | Modified | Add `InterpretationsModule.renderVerdictExplanation()` call in `.then()` |
| `public/js/gauges.js` | Unchanged | Zone colors/labels already support all new UI needs |
| `public/js/data.js` | Unchanged | Cache hit on status.json — no second fetch needed |
| `public/js/main.js` | Unchanged | rates.json + meetings.json orchestration unaffected |
| `public/data/status.json` | Unchanged | All required fields already present: `gauges[id].value`, `.weight`, `.z_score`, `.zone_label`, `.confidence` |

### Internal Module Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| `gauge-init.js` → `InterpretationsModule` | Direct function call | `renderVerdictExplanation` joins existing call chain in `.then()` |
| `renderVerdictExplanation` → `GaugesModule` | Direct function call | Uses `GaugesModule.getZoneColor()` for indicator colour coding |
| `renderVerdictExplanation` → `InterpretationsModule` internals | Internal call | Can call private `generateMetricInterpretation()` and `getWhyItMatters()` since same module |
| `verdict-explanation` DOM element | Data flows in one direction only | gauge-init.js writes; no other module reads the DOM output |

### ASIC Compliance Checkpoints

All new UI copy must pass these checks (from PROJECT.md constraints):

| Rule | What It Means for v4.0 |
|------|------------------------|
| Neutral framing | "Wages are growing above average" not "Wages are dangerously high" |
| No personal financial advice | Verdict explanation describes indicators, not user actions |
| No predictions | "Economic data is currently showing..." not "Rates WILL rise" |
| Existing disclaimer visible | Hero restructure must not push ASIC banner off screen |

---

## Anti-Patterns

### Anti-Pattern 1: Adding a New IIFE to Fetch status.json Again

**What people do:** Create `js/verdict-explanation.js` as an IIFE that calls
`DataModule.fetch('data/status.json')` independently.

**Why it's wrong:** DataModule already fetches and caches status.json in gauge-init.js.
A second fetch call returns the cache immediately but adds an independent execution order —
if the new IIFE runs before gauge-init.js's `.then()` resolves (a race), the explanation
could render before the gauge, causing brief empty-state flicker. It also adds a new
script tag and file to maintain.

**Do this instead:** Add `renderVerdictExplanation` to `interpretations.js` and call
it from gauge-init.js's existing `.then()` callback where `data` is already available.
One fetch, one orchestrator, zero race conditions.

### Anti-Pattern 2: Using innerHTML to Build the Explanation

**What people do:** `container.innerHTML = '<div class="..."><span>' + text + '</span></div>';`

**Why it's wrong:** The existing codebase is strict about safe DOM methods
(`createElement`/`textContent` only — no `innerHTML`). The ESLint config enforces this
(ESLint v10 flat config, `sourceType: script`). A `no-innerHTML` pattern violation would
fail linting in the pre-push hook. More importantly: `status.json` data includes
user-visible text from scraped sources (NAB survey content, CoreLogic labels). Any text
inserted via `innerHTML` is an XSS vector even in a static app.

**Do this instead:** Use `createElement`/`textContent`/`appendChild` — the same pattern
used throughout `interpretations.js`. The `renderMetricCard` function (680 lines in
interpretations.js) demonstrates the full pattern for a complex card.

### Anti-Pattern 3: Rebuilding Zone Logic in the Explanation Component

**What people do:** Write a new colour/zone lookup inside `renderVerdictExplanation`
to determine whether an indicator is hawkish or dovish.

**Why it's wrong:** `GaugesModule` already exposes `getZoneColor(value)` and
`getStanceLabel(value)`. Duplicating this logic creates two sources of truth for zone
boundaries (the `ZONE_COLORS` array in gauges.js). If zone boundaries are ever adjusted,
two places need updating.

**Do this instead:** Call `GaugesModule.getZoneColor(metricData.value)` and
`GaugesModule.getStanceLabel(metricData.value)` directly. They accept any 0-100 value.

### Anti-Pattern 4: Doing Visual Polish Before Structure Is Stable

**What people do:** Apply CSS class changes (spacing, typography, colour hierarchy) to
`index.html` while the hero section restructure is still in progress.

**Why it's wrong:** If Phase 1 (hero restructure) changes which element holds the verdict
text, the CSS classes applied in the polish phase target elements that will be moved or
replaced. Double rework, and it is difficult to review the visual result until layout
is stable.

**Do this instead:** Complete Phase 1 (HTML structure) and Phase 2 (verdict explanation
JS + rendering) before Phase 3 (CSS polish). Polish after the final DOM structure is
confirmed.

### Anti-Pattern 5: Placing the Hero Section Below the Onboarding Accordion

**What people do:** Add a new `<section>` for the hero verdict above `#hawk-o-meter-section`
but below `#onboarding`, thinking the onboarding can stay in its current above-the-fold position.

**Why it's wrong:** The `#onboarding` section is a `<details>` element that defaults to
`open`, making it ~100px tall on mobile. It visually competes with the hero verdict for
above-the-fold dominance. The goal is verdict + score as the dominant above-the-fold element.

**Do this instead:** Either (a) move the verdict to the very top of `#hawk-o-meter-section`
so it appears first within that section, and accept the onboarding detail sits above it but
is collapsible — OR (b) change the onboarding accordion to default-closed so users can
dismiss it. Option (a) is zero-risk; option (b) is a minor UX decision.

---

## Scaling Considerations

This is a static dashboard with no server-side rendering and a fixed data file.
Scaling concerns are about page load performance, not server capacity.

| Concern | Current State | v4.0 Risk |
|---------|--------------|-----------|
| Plotly.js CDN load | ~3.5MB, already loading | No change — no new Plotly usage |
| Tailwind CDN JIT | Scans DOM for classes at runtime | New classes auto-included if valid utilities |
| status.json size | ~5KB, one fetch, cached | No change — no new data fields |
| DOM node count | Moderate — 7 gauge cards + table | Verdict explanation adds ~10-20 nodes |
| CSS specificity | Tailwind utilities + custom tokens | Risk: arbitrary values override custom tokens — test in browser |

---

## Sources

- Direct inspection: `public/index.html` (468 LOC) — DOM structure, existing section IDs, script loading order
- Direct inspection: `public/js/gauge-init.js` (272 LOC) — status.json data flow, all render call sites
- Direct inspection: `public/js/interpretations.js` (694 LOC) — `renderVerdict`, `renderMetricCard`, `getWhyItMatters`, `generateMetricInterpretation`, `getPlainVerdict`
- Direct inspection: `public/js/gauges.js` (270 LOC) — `ZONE_COLORS`, `getZoneColor`, `getStanceLabel`, `GaugesModule` public API
- Direct inspection: `public/js/data.js` (98 LOC) — cache mechanism (URL-keyed `cache` object)
- Direct inspection: `public/js/main.js` (168 LOC) — script loading and initialization order
- Direct inspection: `public/data/status.json` — live data schema, all fields available for explanation logic
- `.planning/PROJECT.md` — ASIC compliance constraints, v4.0 goal statement, out-of-scope items
- Tailwind CDN documentation — confirmed CDN supports all utility classes but not `@apply` processing

---

*Architecture research for: v4.0 Dashboard Visual Overhaul — frontend integration patterns*
*Researched: 2026-02-25*
