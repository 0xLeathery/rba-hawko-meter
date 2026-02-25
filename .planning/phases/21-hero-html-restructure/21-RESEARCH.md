# Phase 21: Hero HTML Restructure - Research

**Researched:** 2026-02-26
**Domain:** Vanilla JS DOM restructure, Tailwind CDN v3, Plotly.js 2.35.2, Google Fonts CDN
**Confidence:** HIGH

## Summary

Phase 21 restructures the hero section of the Hawk-O-Meter dashboard to make the verdict and hawk score the dominant above-the-fold experience. The core work is: (1) create a `#hero-card` wrapper with zone-coloured border, verdict, score, explainer, and freshness badge; (2) restructure the existing grid to support mobile-first ordering; (3) add Inter font loading; (4) add fadeSlideIn animation; (5) wrap Plotly gauge creation in `requestAnimationFrame()` to prevent zero-width render regression.

All decisions are locked in CONTEXT.md (5-agent consensus). The stack is unchanged: vanilla JS IIFE modules, Tailwind CDN v3, Plotly.js 2.35.2, no build system. No new dependencies are needed (Inter is a Google Fonts CDN link, not an npm package).

**Primary recommendation:** Implement as a single plan with 4 sequenced tasks: (1) HTML structure + CSS + font, (2) JS hero card rendering in gauge-init.js, (3) Plotly rAF wrapper + resize fix, (4) Playwright test updates + full suite run.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
1. **Hero Card DOM Structure** (5/5 consensus): New `#hero-card` div wraps verdict, score, explainer, freshness. Plotly gauge stays in current DOM position. `#verdict-container` absorbed into hero card keeping its ID. Structure: `#hero-card` in `.lg:col-span-2`, gauge in `.lg:col-span-3`.
2. **Mobile Layout** (4/5 majority): On mobile, hero card content appears first (verdict + score), gauge below. Use `order-first lg:order-none` on hero card column.
3. **Hawk Score DOM Element** (5/5 consensus): New `#hawk-score-display` showing "38/100" via `Math.round(hawkScore) + '/100'`.
4. **Zone-Coloured Border** (4/5 majority): `border-t-4 border-transparent` static class, `element.style.borderTopColor = GaugesModule.getZoneColor(hawkScore)` in JS.
5. **Freshness Badge** (4/5 majority): New `#hero-freshness` inside hero card. Remove/hide `#data-freshness` above grid. Use `InterpretationsModule.renderStalenessWarning('hero-freshness', data.generated_at)`.
6. **fadeSlideIn** (3/2 split, merged): CSS class `hero-animate-in` added after data loads. Keyframe: opacity 0->1 + translateY 8px->0 over 300ms ease-out. `prefers-reduced-motion` guard via `window.matchMedia`. Only in success path.

### Claude's Discretion
- fadeSlideIn animation implementation details (merged from both positions in CONTEXT.md)

### Deferred Ideas (OUT OF SCOPE)
- Reduce Plotly gauge size on mobile instead of reordering
- Loading skeleton placeholder for hero card
- Score change indicator (delta badge)
- Animated gradient border
- Separate hero card JS module
- Duplicate freshness badge
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| HERO-01 | Verdict label as dominant above-the-fold element | Hero card structure (Decision #1), mobile ordering (Decision #2), Inter font for typography hierarchy |
| HERO-02 | Hawk score as prominent number "38/100" | New `#hawk-score-display` element (Decision #3), set via `Math.round()` in gauge-init.js |
| HERO-03 | Scale explainer adjacent to verdict inside hero card | Move `#scale-explainer` inside `#hero-card` (Decision #1 concrete structure) |
| HERO-04 | Data freshness badge inside hero card | New `#hero-freshness` element (Decision #5), `renderStalenessWarning` targeting new element |
| HERO-05 | Zone-coloured accent border | `border-t-4` with JS `borderTopColor` (Decision #4), `GaugesModule.getZoneColor()` |
| HERO-06 | fadeSlideIn entry animation | CSS keyframe + `hero-animate-in` class (Decision #6), `prefers-reduced-motion` guard |
</phase_requirements>

## Standard Stack

### Core (unchanged)
| Library | Version | Purpose | Notes |
|---------|---------|---------|-------|
| Tailwind CSS | CDN v3 | Utility-first styling | No upgrade; v4 has breaking config format |
| Plotly.js | 2.35.2 CDN | Gauge rendering | No upgrade; v3 breaks title API |
| Decimal.js | 10.x CDN | Financial arithmetic | Unchanged |

### Additions
| Resource | Source | Purpose | Notes |
|----------|--------|---------|-------|
| Inter font | Google Fonts CDN | Typography hierarchy | `wght@400;600;700`, `display=swap` |

### No NPM Dependencies
This phase adds zero npm packages. Inter is a `<link>` tag. All animation is CSS keyframes.

## Architecture Patterns

### Current Hero Section DOM (before)
```
#hawk-o-meter-section
  #data-freshness (text-center, standalone)
  .grid.grid-cols-1.lg:grid-cols-5
    .lg:col-span-3
      #hero-gauge-plot
    .lg:col-span-2.space-y-4
      #asx-futures-container
      Cash Rate card
  #verdict-container (mt-6, standalone below grid)
  #calculator-jump-link (mt-3, standalone)
  #scale-explainer (mt-2, standalone)
```

### Target Hero Section DOM (after)
```
#hawk-o-meter-section
  .grid.grid-cols-1.lg:grid-cols-5
    .lg:col-span-3
      #hero-gauge-plot (UNCHANGED position)
    .lg:col-span-2.order-first.lg:order-none.space-y-4
      #hero-card.bg-finance-gray.rounded-xl.p-6.border.border-finance-border.border-t-4.border-transparent
        #verdict-container (MOVED inside, keep ID)
        #hawk-score-display (NEW)
        #scale-explainer (MOVED inside, keep ID)
        #hero-freshness (NEW)
        #calculator-jump-link (MOVED inside, keep ID)
      #asx-futures-container (STAYS below hero card)
      Cash Rate card (STAYS below ASX)
```

### Key Structural Changes
1. `#data-freshness` div above grid: REMOVED (content moves to `#hero-freshness` inside hero card)
2. `#verdict-container`: moves from below grid into hero card (keeps ID for Playwright)
3. `#calculator-jump-link`: moves from below grid into hero card
4. `#scale-explainer`: moves from below grid into hero card (keep as `<p>` with ID)
5. Right column (`.lg:col-span-2`): gets `order-first lg:order-none` for mobile-first hero
6. New `#hero-card` wrapper: `bg-finance-gray rounded-xl p-6 border border-finance-border border-t-4 border-transparent`
7. New `#hawk-score-display`: `text-5xl sm:text-6xl font-bold text-white tabular-nums`
8. New `#hero-freshness`: container for freshness badge (empty div, filled by JS)

### Anti-Patterns to Avoid
- **Moving `#hero-gauge-plot`**: Plotly gauge MUST stay in its current DOM position to avoid zero-width bug
- **Dynamic Tailwind class concatenation**: Never do `'border-' + color`. Use `element.style.borderTopColor = hex`
- **innerHTML**: ESLint enforces no innerHTML. Use createElement/textContent/appendChild
- **Adding zone colour to non-approved elements**: Zone colour only on verdict label, hero border, explanation headings

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Font loading | Custom font-face | Google Fonts CDN `<link>` | Handles subsetting, caching, FOUT |
| Animation | JS animation loop | CSS `@keyframes` + class toggle | GPU-accelerated, respects reduced-motion media query |
| Zone colour | Tailwind class builder | `GaugesModule.getZoneColor(score)` + `element.style` | Existing function, proven pattern |
| Freshness rendering | New function | `InterpretationsModule.renderStalenessWarning()` | Existing function, just change target ID |

## Common Pitfalls

### Pitfall 1: Plotly Zero-Width Render
**What goes wrong:** After DOM restructure, Plotly gauge renders with zero width because the container dimensions aren't computed when `newPlot()` is called.
**Why it happens:** The parent container may not have final layout dimensions when Plotly calculates chart size. This is especially problematic when the grid structure changes.
**How to avoid:** Wrap `GaugesModule.createHeroGauge()` in `requestAnimationFrame()`. After rendering, call `Plotly.Plots.resize('hero-gauge-plot')` in a second `requestAnimationFrame()`.
**Warning signs:** Gauge appears as a thin vertical line or completely invisible.

### Pitfall 2: Tailwind CDN Silent Class Drop
**What goes wrong:** Dynamically constructed class strings like `'border-' + zoneColor` are silently dropped by Tailwind CDN because the JIT compiler never sees the full class literal.
**Why it happens:** Tailwind CDN scans the HTML at load time for class literals. Dynamic strings aren't in the scan.
**How to avoid:** Use full literal class strings (`border-t-4 border-transparent`) and set colours via `element.style`.

### Pitfall 3: Playwright Test Breakage
**What goes wrong:** Moving DOM elements breaks existing Playwright selectors that depend on element position or parent-child relationships.
**Why it happens:** Tests like `dashboard.spec.js` test 1 check `#hero-gauge-plot` contains text `{score}/100` and the stance label. If these move out of the Plotly container, tests fail.
**How to avoid:**
- Keep `#verdict-container` as a DOM element with that exact ID
- Keep `#hero-gauge-plot` in its current position (left column)
- The score text `52/100` and stance label are rendered BY Plotly inside `#hero-gauge-plot` SVG -- they stay there
- The new `#hawk-score-display` is a SEPARATE element that duplicates the score in the hero card
- Test 1 should still pass because it checks `#hero-gauge-plot` which is unchanged
- Tests 14, 15, 21 check `#scale-explainer`, `#verdict-container`, `#calculator-jump-link` by ID -- IDs are preserved

### Pitfall 4: Mobile Above-Fold Congestion
**What goes wrong:** Hero card + gauge both render above the fold on mobile, creating a cramped layout.
**Why it happens:** Not using CSS order to sequence hero card before gauge on mobile.
**How to avoid:** The right column (`.lg:col-span-2`) uses `order-first lg:order-none`. On mobile (stacked), hero card renders first. On desktop (grid), normal source order.

### Pitfall 5: `#data-freshness` Removal Breaks Existing Code
**What goes wrong:** Removing `#data-freshness` from HTML causes `renderStalenessWarning('data-freshness', ...)` to silently fail (returns early because container is null).
**Why it happens:** gauge-init.js currently targets `data-freshness`.
**How to avoid:** Change the target in gauge-init.js from `'data-freshness'` to `'hero-freshness'`. The function handles missing containers gracefully (returns early), so even if the old ID is referenced somewhere else, it won't error.

## Code Examples

### Google Fonts Preconnect + Link (in `<head>`)
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
```

### CSS Keyframe Animation (in `<style>` block)
```css
@keyframes fadeSlideIn {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}
.hero-animate-in {
  animation: fadeSlideIn 300ms ease-out both;
}
@media (prefers-reduced-motion: reduce) {
  .hero-animate-in { animation: none; }
}
```

### Tailwind Config Extension (font family)
```javascript
tailwind.config = {
  darkMode: 'class',
  theme: {
    extend: {
      colors: { /* existing */ },
      fontFamily: {
        'sans': ['Inter', 'system-ui', 'sans-serif']
      }
    }
  }
}
```

### Hero Card Rendering in gauge-init.js
```javascript
// In .then() callback after data loads:

// 1. Set hawk score display
var scoreEl = document.getElementById('hawk-score-display');
if (scoreEl) {
  scoreEl.textContent = Math.round(data.overall.hawk_score) + '/100';
}

// 2. Set zone border colour
var heroCard = document.getElementById('hero-card');
if (heroCard) {
  heroCard.style.borderTopColor = GaugesModule.getZoneColor(data.overall.hawk_score);
}

// 3. Render freshness into hero card (replaces old #data-freshness target)
InterpretationsModule.renderStalenessWarning('hero-freshness', data.generated_at);

// 4. Wrap hero gauge in rAF
requestAnimationFrame(function () {
  GaugesModule.createHeroGauge('hero-gauge-plot', data.overall.hawk_score);
  // Second rAF for resize after paint
  requestAnimationFrame(function () {
    var heroEl = document.getElementById('hero-gauge-plot');
    if (heroEl && heroEl.data) {
      Plotly.Plots.resize('hero-gauge-plot');
    }
  });
});

// 5. Animate hero card (only on success, respect reduced motion)
if (heroCard && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
  heroCard.classList.add('hero-animate-in');
}
```

## Playwright Test Impact Analysis

### Tests That Must Still Pass Without Changes
| Test | File | Selector | Why Safe |
|------|------|----------|----------|
| Test 1 | dashboard.spec.js | `#hero-gauge-plot` | Unchanged DOM position, Plotly still renders score/stance inside SVG |
| Test 2-3 | dashboard.spec.js | `#metric-gauges-grid` | Structurally separate from hero changes |
| Test 4 | dashboard.spec.js | `#hero-gauge-plot` error state | Unchanged |
| Test 5 | dashboard.spec.js | `#metric-gauges-grid` staleness | Unchanged |
| Tests 6-7 | dashboard.spec.js | `#asx-futures-container` | Stays in right column, unchanged |
| Housing/BC tests | dashboard.spec.js | `#metric-gauges-grid .bg-finance-gray` | Unchanged |
| Tests 11-12 | phase6-ux.spec.js | `#hero-gauge-plot`, `#metric-gauges-grid` | Unchanged |
| Test 13 | phase6-ux.spec.js | `#onboarding` | Outside hero section |
| Test 17 | phase6-ux.spec.js | `#metric-gauges-grid` | Unchanged |
| Test 18-19 | phase6-ux.spec.js | `#metric-gauges-grid` | Unchanged |
| Test 22 | phase6-ux.spec.js | `#chart-details` | Outside hero section |
| Calculator tests | calculator.spec.js | All calculator selectors | Outside hero section |

### Tests That May Need Updates
| Test | File | Concern | Action |
|------|------|---------|--------|
| Test 14 | phase6-ux.spec.js | `#scale-explainer` visibility | ID preserved, just moved inside hero card -- should still pass |
| Test 15 | phase6-ux.spec.js | `#verdict-container` text check | ID preserved, moved inside hero card -- should still pass |
| Test 20 | phase6-ux.spec.js | Placeholder card count | No change to metric grid -- should still pass |
| Test 21 | phase6-ux.spec.js | `#calculator-jump-link` | ID preserved, moved inside hero card -- should still pass |

**Prediction:** All 28 tests should pass without modification because:
1. `#hero-gauge-plot` is unchanged
2. All moved elements keep their IDs
3. Tests use ID selectors, not positional selectors relative to removed parents
4. `#metric-gauges-grid` is untouched

## Open Questions

None. All decisions are locked. The implementation path is clear.

## Sources

### Primary (HIGH confidence)
- Direct codebase analysis: `public/index.html`, `public/js/gauge-init.js`, `public/js/gauges.js`, `public/js/interpretations.js`, `public/js/data.js`
- CONTEXT.md: 5-agent synthetic discussion with locked decisions
- Playwright test suite: 28 tests across 3 spec files

### Secondary (HIGH confidence)
- Google Fonts CDN usage: standard pattern, widely documented
- CSS `@keyframes` + `prefers-reduced-motion`: W3C standard media query
- Plotly.js `requestAnimationFrame` workaround: documented pattern for deferred rendering

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - no new dependencies, existing codebase patterns
- Architecture: HIGH - locked decisions from 5-agent consensus, clear DOM structure
- Pitfalls: HIGH - all pitfalls documented in MEMORY.md and CONTEXT.md from prior research
- Test impact: HIGH - all 28 tests analysed against specific selectors

**Research date:** 2026-02-26
**Valid until:** 2026-03-26 (stable stack, no external dependency changes)
