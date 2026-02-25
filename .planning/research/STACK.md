# Technology Stack

**Project:** RBA Hawk-O-Meter — v4.0 Dashboard Visual Overhaul
**Researched:** 2026-02-25
**Scope:** NEW capabilities only — hero redesign, verdict explanation section, visual polish. Does NOT re-research what v1–v3 already established.
**Confidence:** HIGH (versions verified against CDN registries and official docs)

---

## Context: What v1–v3 Already Established (Do NOT Re-research or Change)

| Layer | Technology | Version | Status |
|-------|------------|---------|--------|
| CSS framework | Tailwind CSS CDN (v3 Play CDN) | cdn.tailwindcss.com | Loaded via script tag, config in JS block |
| Charts | Plotly.js | 2.35.2 | Loaded via cdn.plot.ly CDN |
| Precision math | Decimal.js | 10.x | Loaded via jsDelivr CDN |
| JS pattern | Vanilla JS IIFE modules | — | 8 modules: data.js, chart.js, countdown.js, calculator.js, main.js, gauges.js, interpretations.js, gauge-init.js |
| Gauge colors | Blue/Grey/Red 5-zone | — | Colorblind-safe (avoids red/green) |
| Dark theme | Tailwind `dark` class on `<html>` | — | finance-dark (#0a0a0a), finance-gray (#1a1a1a), finance-border (#2d2d2d) |
| Data format | status.json flat file | — | Includes overall.hawk_score, overall.zone, gauges.{metric}.value/weight/interpretation, gauges.{metric}.z_score |

---

## Recommended Stack Additions for v4.0

### 1. Inter Variable Font — Google Fonts CDN

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **Inter** (Google Fonts CDN) | Variable (wght 100..900) | Typography baseline for hero and verdict sections | Already referenced in Plotly's `getDarkLayout` font stack (`Inter, system-ui, sans-serif`) but never loaded via a `<link>` tag. Without loading, the browser falls through to `system-ui`, which is Segoe UI on Windows — inconsistent across platforms. Loading Inter gives the hero number display, verdict text, and all UI text a unified, screen-optimised letterform designed for dashboards. |

**CDN HTML:**
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300..900&display=swap" rel="stylesheet">
```

**Tailwind config change needed** — add `fontFamily` to the existing `tailwind.config` block:
```js
tailwind.config = {
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      // ... existing colors
    }
  }
}
```

**Confidence:** HIGH. Google Fonts CSS2 API (`wght@300..900` syntax) is stable and documented at [developers.google.com/fonts/docs/css2](https://developers.google.com/fonts/docs/css2). Preconnect pattern is current Google Fonts embed standard.

**Privacy note:** Google Fonts serves fonts from Google's CDN. This project already loads Plotly.js from cdn.plot.ly and Decimal.js from jsdelivr.net — a Google Fonts CDN dependency is consistent with the existing third-party CDN posture.

---

### 2. CSS @keyframes in `<style>` Block — Hero Entry Animations

**No new library.** All hero entry animations use native CSS `@keyframes` declared in the existing `<style>` block in `index.html`.

| Animation | Technique | Target |
|-----------|-----------|--------|
| Fade-in + slide-up for hero section | `@keyframes fadeSlideIn` + `animation: 0.6s ease-out` | Hero verdict text, hawk score display |
| Score number transition | CSS `transition: opacity 0.3s ease` | Score value span while loading state resolves |
| Verdict section reveal | `@keyframes fadeIn` with `animation-delay` | Verdict explanation cards, staggered per-indicator row |

**Why not Animate.css?** Animate.css (v4.1.1, ~77KB minified) adds 80+ animation classes the project will never use. The hero needs exactly two animations: a fade-slide-in on page load and an opacity transition during data load. These are 15 lines of CSS.

**Why not GSAP or Motion One?** JavaScript animation orchestration libraries are for complex sequenced animations with scroll triggers and physics. A dark-theme dashboard with a 0.6s entry animation does not need an orchestration engine.

**CSS added to `<style>` block:**
```css
@keyframes fadeSlideIn {
  from { opacity: 0; transform: translateY(16px); }
  to   { opacity: 1; transform: translateY(0); }
}
@keyframes fadeIn {
  from { opacity: 0; }
  to   { opacity: 1; }
}
```

Apply via inline Tailwind-style classes using the `style` attribute or small helper classes added in the `<style>` block. The IIFE module pattern means animation triggers can be applied by adding/removing CSS classes via `classList` when data loads.

**Confidence:** HIGH. Native CSS `@keyframes` with `animation` property has universal browser support. No CDN, no dependency, no risk.

---

### 3. CountUp.js 2.9.0 — Hero Score Number Animation (OPTIONAL)

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **countUp.js** | 2.9.0 (UMD) | Animate the hero hawk score counting from 0 to its current value on page load | Creates the single most impactful UX moment in the hero redesign: the score counts up from 0 to e.g. 52 over ~1.5 seconds with easing. Establishes the score as the focal point before the verdict text renders. |

**CDN URL (jsDelivr UMD build):**
```html
<script src="https://cdn.jsdelivr.net/npm/countup.js@2.9.0/dist/countUp.umd.js"></script>
```

**Integration (vanilla JS, no module system needed):**
```js
// After status.json loads, inside the IIFE that renders the hero:
var counter = new CountUp('hero-score-number', status.overall.hawk_score, {
  duration: 1.5,
  useEasing: true,
  decimalPlaces: 0
});
if (!counter.error) counter.start();
```

**Why CountUp.js vs. hand-rolled `requestAnimationFrame`?** A correct count-up animation with easing (slows near the end), resilience to `prefers-reduced-motion`, and error handling is ~80 lines of vanilla JS. CountUp.js is 5.83KB minified, dependency-free, MIT license, and provides all of these. The UMD build exposes `CountUp` as a global, requiring no module system. Verified latest: 2.9.0 (June 2025).

**`prefers-reduced-motion` handling:** CountUp.js does not auto-detect `prefers-reduced-motion`. Wrap the call:
```js
if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
  counter.start();
} else {
  document.getElementById('hero-score-number').textContent = status.overall.hawk_score;
}
```

**Mark as OPTIONAL:** If the team wants to avoid a new CDN dependency, replace with 25 lines of vanilla `requestAnimationFrame` + `easeOutQuart`. The STACK.md recommends CountUp.js because it handles edge cases correctly, but the verdict section and hero redesign work without it.

**Confidence:** HIGH. Version 2.9.0 verified on jsDelivr ([cdn.jsdelivr.net/npm/countup.js](https://cdn.jsdelivr.net/npm/countup.js/)). UMD build confirmed at `dist/countUp.umd.js`.

---

## What NOT to Add

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| **Tailwind CSS v4 CDN** (`@tailwindcss/browser@4`) | Completely different configuration format — v4 uses `<style type="text/tailwindcss">` + `@theme` directive, not a JavaScript `tailwind.config` object. Migrating would require rewriting all custom color definitions and the dark mode setup. Net benefit for a polish milestone: zero. Risk: breaking existing gauge colours, finance-dark backgrounds, and all custom classes. | Stay on current `cdn.tailwindcss.com` (v3 Play CDN) |
| **Plotly.js v3.x** (currently on 2.35.2) | v3 introduced breaking changes: `title` can no longer be set as a string (must use `title.text`), removed deprecated attributes. The `getDarkLayout()` function in `gauges.js` passes layout objects with string titles — upgrading would require auditing every layout call. Indicator/gauge trace API is unchanged in v3, so there is no feature benefit for this milestone. | Stay on 2.35.2. Pin the version explicitly (already done: `plotly-2.35.2.min.js`) |
| **Animate.css** | 77KB of animations, 80+ classes, only two of which would ever be used. Runtime-loaded from a CDN. | Native `@keyframes` in `<style>` block (see section 2) |
| **GSAP / Motion One** | JavaScript animation orchestration engines for complex scroll/physics-based animations. The hero needs a 0.6s fade-slide; this is not that use case. | Native CSS `@keyframes` |
| **Alpine.js** | Reactive attribute binding framework. The project explicitly chose vanilla JS IIFE modules over a framework (`Key Decisions` in PROJECT.md). Adding Alpine.js for a new section contradicts this architectural decision and would create two competing data-binding paradigms in the same page. | Vanilla JS DOM manipulation in a new `verdict-explanation.js` IIFE module |
| **Chart.js / D3.js** | Alternative charting libraries. Plotly.js is already embedded for the gauges. Adding a second charting library for any visual in the hero (e.g., a sparkline) doubles the charting dependency footprint. | Plotly.js indicator trace or CSS-only visual for supporting elements |
| **Tailwind UI / Flowbite** | Component libraries that depend on a build step or Alpine.js. No build system in this project. | Hand-authored Tailwind utility classes |
| **Bootstrap / Bulma** | Separate CSS frameworks. Tailwind is already loaded; a second CSS framework creates class naming conflicts and doubles the CSS footprint. | Tailwind utility classes |
| **Web Fonts: Geist, DM Sans, Manrope** | Modern alternatives to Inter. All are good fonts. None are already referenced in the project's Plotly font stack. Switching would require updating `getDarkLayout()` in `gauges.js`. Inter is the correct choice because it is _already declared_ in the existing Plotly font configuration. | Inter (already in `getDarkLayout` font stack) |
| **CSS-in-JS solutions** | Any solution requiring a bundler (styled-components, emotion, vanilla-extract). No build system. | `<style>` block + Tailwind utility classes |

---

## Stack Patterns for the Three v4.0 Features

**Above-the-fold hero redesign:**
- Layout: Tailwind flex/grid utilities (already available)
- Score display: Large `<span>` with tabular-nums, CountUp.js animation on load
- Verdict text: Existing `InterpretationsModule.getPlainVerdict()` output, styled with Tailwind
- Entry animation: CSS `@keyframes fadeSlideIn` applied via `classList.add` after data load
- No new library required beyond CountUp.js (optional)

**Verdict explanation section:**
- Data source: `status.json` `gauges` object — already fetched by `DataModule` in `data.js`
- Logic: Sort indicators by `Math.abs(z_score) * weight` descending, take top 3 "drivers"
- Rendering: New IIFE module `verdict-explanation.js` using safe DOM methods (`createElement`, `textContent`) consistent with existing pattern
- Copy: Extend `InterpretationsModule.getWhyItMatters()` and `generateMetricInterpretation()` — already exist
- Styling: Tailwind utility classes on a `<section>` element positioned between hero and indicator grid
- No new library required

**Visual polish — spacing, typography, colour hierarchy:**
- Inter font load: Google Fonts CDN link tag (section 1 above)
- Spacing: Tailwind spacing utilities (already available)
- Typography: `font-sans` applies Inter once the `fontFamily` theme extension is added
- Colour hierarchy: Audit and standardise existing Tailwind colour classes — `text-white` for primary, `text-gray-200` for secondary, `text-gray-400` for body, `text-gray-500` for metadata
- Dark theme refinement: CSS custom property overrides in `<style>` block for any values Tailwind's `extend` cannot cover
- No new library required

---

## Version Compatibility

| Package | Current Version | Status | Notes |
|---------|----------------|--------|-------|
| Tailwind CSS CDN | v3 (cdn.tailwindcss.com) | Stay | v4 CDN incompatible with existing config format |
| Plotly.js | 2.35.2 | Stay | v3 has breaking changes irrelevant to v4.0 goals |
| Decimal.js | 10.x | Stay | Calculator unaffected by visual milestone |
| Inter (Google Fonts) | Variable (wght 300..900) | ADD | Preconnect + link tag in `<head>` |
| countUp.js | 2.9.0 | ADD (optional) | UMD build, global `CountUp` class, MIT license |

---

## Integration Points

| Change | File | How |
|--------|------|-----|
| Add Inter font load | `public/index.html` `<head>` | Two preconnect links + one stylesheet link before Tailwind script |
| Extend Tailwind `fontFamily` | `public/index.html` `tailwind.config` block | Add `fontFamily.sans` array to `theme.extend` |
| Add `@keyframes` | `public/index.html` `<style>` block | Append to existing custom CSS |
| Add CountUp.js | `public/index.html` script tags | After Plotly.js, before `data.js` |
| Verdict explanation | `public/js/verdict-explanation.js` | New IIFE module; add `<script>` tag after `interpretations.js` |
| Hero section restructure | `public/index.html` `#hawk-o-meter-section` | Restructure markup within existing section — no new sections needed |

---

## Installation

No npm install required. All additions are CDN-loaded or native CSS.

```html
<!-- Add to <head> — BEFORE Tailwind CDN script -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300..900&display=swap" rel="stylesheet">

<!-- Add to script tags — AFTER Plotly.js, BEFORE data.js (optional) -->
<script src="https://cdn.jsdelivr.net/npm/countup.js@2.9.0/dist/countUp.umd.js"></script>
```

No build step. No package.json changes. No Python dependency changes.

---

## Sources

- **Inter via Google Fonts** — [developers.google.com/fonts/docs/css2](https://developers.google.com/fonts/docs/css2) — CSS2 API `wght@300..900` range syntax verified (HIGH confidence)
- **Inter preconnect pattern** — [cdnplanet.com/blog/faster-google-webfonts-preconnect](https://www.cdnplanet.com/blog/faster-google-webfonts-preconnect) — current Google Fonts embed standard (HIGH confidence)
- **Tailwind CDN v3 vs v4 differences** — [tailwindcss.com/docs/installation/play-cdn](https://tailwindcss.com/docs/installation/play-cdn) — confirmed v4 CDN uses different script URL and config format (HIGH confidence)
- **Tailwind CDN v4 config format** — [tailkits.com/blog/tailwind-css-v4-cdn-setup](https://tailkits.com/blog/tailwind-css-v4-cdn-setup/) — v4 requires `<style type="text/tailwindcss">` + `@theme` directive, confirmed breaking change from v3 JS config object (MEDIUM confidence)
- **Plotly.js v3 breaking changes** — [plotly.com/javascript/version-3-changes](https://plotly.com/javascript/version-3-changes/) — title-as-string removed, no indicator/gauge API changes (HIGH confidence)
- **Plotly.js latest version** — [github.com/plotly/plotly.js/releases](https://github.com/plotly/plotly.js/releases) — v3.4.0 is latest as of Feb 2026 (HIGH confidence)
- **countUp.js 2.9.0** — [cdn.jsdelivr.net/npm/countup.js](https://cdn.jsdelivr.net/npm/countup.js/) + [jsdelivr.com/package/npm/countup.js](https://www.jsdelivr.com/package/npm/countup.js) — version 2.9.0 released June 2025, UMD build at `dist/countUp.umd.js` confirmed (HIGH confidence)
- **CSS @keyframes browser support** — [MDN Web Docs](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/animation-iteration-count) — universal support, no polyfill needed (HIGH confidence)
- **Native CSS counter animation** — [css-tricks.com/animating-number-counters](https://css-tricks.com/animating-number-counters/) — `@property` approach requires Chromium; `requestAnimationFrame` is cross-browser fallback (HIGH confidence)
- **Animate.css size** — [animate.style](https://animate.style/) — v4.1.1, confirmed overkill for single-animation use case (HIGH confidence)

---

*Stack research for: RBA Hawk-O-Meter v4.0 Dashboard Visual Overhaul*
*Researched: 2026-02-25*
