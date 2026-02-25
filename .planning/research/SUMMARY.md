# Project Research Summary

**Project:** RBA Hawk-O-Meter — v4.0 Dashboard Visual Overhaul
**Domain:** Static financial/economic data dashboard — frontend UX overhaul of existing vanilla JS app
**Researched:** 2026-02-25
**Confidence:** HIGH

## Executive Summary

The RBA Hawk-O-Meter v4.0 milestone is a pure frontend visual overhaul of a fully-shipped v3.0 dashboard. The project uses a no-build-step architecture (Tailwind CDN, Plotly.js CDN, vanilla JS IIFE modules) that is already mature and well-validated. The three milestone deliverables — hero section redesign, verdict explanation section, and visual polish — are all achievable using existing data structures and utility functions with no changes to the Python pipeline, status.json schema, or any backend infrastructure. The recommended approach is strictly additive: restructure one HTML section, extend one existing JS module, and tune CSS classes.

The recommended implementation sequence is HTML restructure first, JS logic second, CSS polish third. This order is dictated by the architectural constraint that the DOM must be stable before CSS is tuned to avoid rework, and by the Plotly.js sizing constraint that gauge containers must be in their final layout before `Plotly.newPlot()` is called. The single optional dependency addition is Inter font via Google Fonts CDN (already referenced in the Plotly font stack but never loaded), plus CountUp.js 2.9.0 as an optional delight feature for the score counter animation.

The key risks are all well-understood and have clear mitigations: Plotly gauge zero-width rendering after DOM restructure (prevent with `requestAnimationFrame` + explicit resize call), Tailwind CDN silently dropping dynamically concatenated class names (prevent by using complete literal strings or `element.style` with hex values), ASIC compliance violations in verdict explanation copy (prevent with hedged factual-information framing), and Playwright test brittleness from nth-index selectors (prevent by running the suite after every structural HTML change). All risks are LOW-MEDIUM recovery cost if caught early.

---

## Key Findings

### Recommended Stack

The existing stack requires no significant changes for v4.0. All tooling — Tailwind CDN v3, Plotly.js 2.35.2, Decimal.js, vanilla JS IIFE modules — must stay at current versions. Tailwind v4 CDN uses a fundamentally incompatible configuration format, and Plotly v3 has breaking changes to `title` handling that would require auditing every layout call with no feature benefit for this milestone.

Two additions are recommended: Inter via Google Fonts CDN (already declared in `getDarkLayout()`'s font stack but never actually loaded, causing Windows browsers to fall back to Segoe UI), and CountUp.js 2.9.0 UMD from jsDelivr (optional — creates the most impactful UX moment of the hero redesign). All hero animations use native CSS `@keyframes` in the existing `<style>` block — no animation library needed.

**Core technologies:**
- Tailwind CDN v3 (`cdn.tailwindcss.com`): utility-first CSS — stay on v3; v4 CDN is incompatible with existing JS config object
- Plotly.js 2.35.2 (`cdn.plot.ly`): gauge and chart rendering — stay pinned; v3 has breaking title API changes with no feature benefit for this milestone
- Inter (Google Fonts CDN): typography — ADD via preconnect + link tag; already referenced in Plotly font stack, just never loaded
- CountUp.js 2.9.0 (jsDelivr UMD): hero score count-up animation — ADD as optional; 5.83KB, MIT, handles edge cases correctly; replaceable with ~25 lines of vanilla `requestAnimationFrame`
- Native CSS `@keyframes`: hero entry animations — no library needed; two keyframe definitions (`fadeSlideIn`, `fadeIn`) cover all animation needs

### Expected Features

The feature research establishes a clear P1/P2/P3 hierarchy. All P1 features are pure frontend additions requiring zero backend or schema changes. The single differentiating feature — the verdict explanation section showing what is driving the score — has no comparable equivalent in CNN Fear & Greed or the MacroMicro Hawk-Dove Index.

**Must have (table stakes — v4.0 P1):**
- Verdict label as visual hero (large, zone-coloured, above-the-fold) — the primary UX purpose of the milestone
- Score immediately legible as a number with context — users cannot interpret a gauge needle alone
- Scale explainer physically adjacent to the verdict — currently can scroll below fold on mobile
- Data freshness badge inside the hero card — users must know if the score is current before trusting it
- Consistent zone colour across hero verdict, card accent border, and explanation headings — colour vocabulary collapses if inconsistent
- Graceful loading states with no layout shift — `min-height: 280px` on gauge container must be preserved

**Should have (differentiators — v4.0 P1/P2):**
- Verdict explanation section: two plain-English lists of "pushing rates up" and "pulling rates down" indicators — the feature no competitor offers
- Hero card with zone-coloured accent border — reinforces verdict at the card boundary level
- Gauge entrance animation (sweep from 0 to score) — P2, after P1 features verified; requires `requestAnimationFrame` workaround since Plotly indicator gauges do not animate natively

**Defer (v4.x or v5+):**
- Indicator direction delta badges — requires `previous_value` field in status.json; backend pipeline change, not frontend work
- Historical hawk score chart — requires archiving status.json snapshots; no current archive mechanism
- Dark/light theme toggle — requires dual Tailwind class definitions and Plotly style rewrites across every module; high complexity for low value against the finance-terminal aesthetic
- Real-time polling — ABS/RBA data is monthly/quarterly; polling is theatre

### Architecture Approach

v4.0 adds no new directories, no new JS modules, and no new data sources. Three files change: `public/index.html` (hero section restructure + `#verdict-explanation` div), `public/js/interpretations.js` (add `renderVerdictExplanation()` + expose in return object), and `public/js/gauge-init.js` (add one function call in the existing `.then()` callback). Everything else is unchanged.

The key architectural insight from direct codebase inspection is that `DataModule` already caches `status.json` by URL — any module can call `DataModule.fetch("data/status.json")` and get the cached result as a resolved Promise with no network cost and no coordination protocol. This means `renderVerdictExplanation` does not need its own data fetch; it receives `data.gauges` and `data.overall.hawk_score` directly from gauge-init.js's existing `.then()` callback, where the data is already available.

**Major components and v4.0 change surface:**
1. `public/index.html` — MODIFIED: promote `#verdict-container` above the 5-column gauge grid; add `#verdict-explanation` container; add Inter font link tags; add `@keyframes` to `<style>` block; extend `tailwind.config` with `fontFamily.sans`
2. `public/js/interpretations.js` (InterpretationsModule) — MODIFIED: add `renderVerdictExplanation(containerId, gaugesData, overallScore)`; expose in return object; reuse `getWhyItMatters()` and `generateMetricInterpretation()` for ASIC-safe copy
3. `public/js/gauge-init.js` — MODIFIED: add one call to `InterpretationsModule.renderVerdictExplanation()` after `renderVerdict()` in the existing `.then()` callback
4. `public/js/gauges.js` (GaugesModule) — UNCHANGED: `getZoneColor()` and `getStanceLabel()` already support all new colour logic needs
5. `public/js/data.js` (DataModule) — UNCHANGED: cache mechanism handles repeated status.json fetches transparently

### Critical Pitfalls

1. **Plotly gauge renders at zero width after hero DOM restructure** — Plotly measures `offsetWidth` at `newPlot()` call time. If new above-the-fold elements change the grid layout before paint, the gauge initialises at 0px and never recovers via `autosize` (which only listens to `window.resize`). Prevention: wrap `createHeroGauge()` in `requestAnimationFrame()`; call `Plotly.Plots.resize('hero-gauge-plot')` explicitly after inserting new hero HTML. Test at 375px, 768px, 1024px, 1440px immediately after any structural change. Never reduce `min-height: 280px` on the gauge container.

2. **Tailwind CDN silently drops dynamically concatenated class names** — CDN scans source for literal class name tokens at load time; it cannot execute JS expressions. `'border-' + zoneColor + '-500'` produces a class Tailwind never generates CSS for — the style fails silently with no error. Prevention: use complete-string lookup objects (`ZONE_BORDER_CLASSES = { cold: 'border-blue-800', ... }`) or bypass Tailwind entirely with `element.style.color = GaugesModule.getZoneColor(score)` — already the established pattern in `gauges.js`.

3. **Verdict explanation copy crosses into ASIC general advice territory** — Explaining why a score is high naturally pulls language toward prediction and recommendation. "Rates will rise" and "you should consider fixing now" are ASIC RG 244 violations. Prevention: strict framing rules — state what the indicator is doing, not what it means for user decisions. Use "tends to," "historically associated with," "the data is consistent with." Mirror `getPlainVerdict()`'s hedged language pattern. Review every new sentence against: "Would a person reading this feel they have received personal advice?"

4. **Playwright nth-index selectors break after any DOM insertion near the gauge grid** — Tests use `.nth(0)`, `.nth(1)`, `.nth(5)` to address metric cards. Any new `bg-finance-gray` element inserted near `#metric-gauges-grid` shifts all indices. Prevention: keep `#verdict-explanation` structurally separate from `#metric-gauges-grid`; run the full 28-test Playwright suite before and after every structural HTML change; replace nth selectors for named indicators with `.filter({ hasText: 'Indicator Name' })` when updating tests.

5. **Mobile above-the-fold congestion after hero redesign** — The existing vertical stack (disclaimer + header + onboarding accordion + gauge at 280px + verdict + links) is already long on 375px viewports. Adding a prominent hero verdict block without removing other elements pushes the verdict below the fold, defeating the purpose of the redesign. Prevention: hero redesign must *replace* the current verbose verdict container and scale explainer, not add above them. Design constraint: score + verdict + 1 sentence explanation must fit in approximately 350-400px on mobile. Consider changing the onboarding `<details>` to default-closed on mobile.

---

## Implications for Roadmap

Based on combined research, the architecture prescribes a strict three-phase sequence where each phase is a prerequisite for the next.

### Phase 1: Hero HTML Restructure

**Rationale:** DOM structure must be stable before any JS or CSS work begins. Plotly gauge sizing depends on container dimensions at render time — restructuring HTML after JS is wired creates zero-width gauge risk and CSS rework. The existing element IDs (`#verdict-container`, `#hero-gauge-plot`, etc.) are Playwright test targets that must survive the restructure. Establish the final DOM shape first so subsequent phases have a stable target.

**Delivers:** Above-the-fold hero section with `#verdict-container` promoted to visual top position; `#verdict-explanation` empty placeholder div added; Inter font preconnect + link tags in `<head>`; `tailwind.config` extended with `fontFamily.sans`; `@keyframes fadeSlideIn` and `fadeIn` added to `<style>` block; existing Playwright suite still passing 28/28; gauge rendering verified at 375px, 768px, 1024px, 1440px.

**Addresses features from FEATURES.md:** Verdict label as visual hero (P1); scale explainer adjacent to verdict (P1); data freshness inside hero zone (P1); hero card zone-coloured accent border (P1 — CSS + 1 JS line).

**Avoids pitfalls:** Plotly zero-width render (test at all breakpoints immediately; wrap `createHeroGauge()` in `requestAnimationFrame()`); Playwright nth-selector breakage (run suite after every structural change); mobile above-fold congestion (test at 375x812 throughout; hero is a replacement, not an addition).

**Research flag:** Standard patterns — no deeper research needed. All changes are HTML restructure and CSS class tuning with well-documented patterns.

---

### Phase 2: Verdict Explanation Component

**Rationale:** Requires Phase 1's `#verdict-explanation` container to exist in the DOM. The explanation logic ranks indicators by `(value - 50) * weight` — this is the only new algorithmic work in the milestone. Must be completed before visual polish so the explanation section's typography and spacing can be tuned in Phase 3 against real rendered content.

**Delivers:** `renderVerdictExplanation()` function added to `interpretations.js` and exposed in its return object; wired in `gauge-init.js` `.then()` after `renderVerdict()`; two plain-English lists of hawkish and dovish indicator drivers rendered into `#verdict-explanation`; ASIC compliance verified on all new copy; safe DOM methods (`createElement`/`textContent`) used throughout; `GaugesModule.getZoneColor()` used for colour — no Tailwind class concatenation.

**Uses from STACK.md:** No new libraries required. Uses existing `GaugesModule.getZoneColor()`, `getWhyItMatters()`, `generateMetricInterpretation()`, and `getStanceLabel()`. Safe DOM methods following established `renderMetricCard()` pattern.

**Implements architecture component:** `renderVerdictExplanation(containerId, gaugesData, overallScore)` — sorts indicators by absolute contribution (`(value - 50) * weight`), renders top 3 hawkish and top 2 dovish drivers with ASIC-compliant copy.

**Addresses features from FEATURES.md:** Verdict explanation section — "what's driving the score" (P1 differentiator); hawkish/dovish two-list layout per driver (P1 differentiator).

**Avoids pitfalls:** Tailwind CDN concatenated class names (use `element.style` with hex values from `getZoneColor()`); ASIC copy compliance (hedge every sentence; apply factual-information review checklist per commit); new IIFE anti-pattern (extend InterpretationsModule, not a new IIFE with independent data fetch — avoids race conditions).

**Research flag:** Standard patterns — ASIC framing rules are clear from existing `getWhyItMatters()` and `getPlainVerdict()` implementations. No deeper research needed.

---

### Phase 3: Visual Polish

**Rationale:** Must come last — CSS tuning against a DOM that is still changing causes double rework. Typography scale, spacing standardisation, and colour hierarchy require real content in all sections to evaluate correctly. The optional CountUp.js score animation and gauge entrance animation also belong here as final delight layers once structure and data rendering are confirmed working.

**Delivers:** Consistent typography hierarchy (36-48px verdict label, 52px score, defined text-gray scale for secondary/body/metadata); standardised spacing across all sections; zone colour consistently applied to verdict label, hero border, and explanation headings; `fadeSlideIn` animation applied via `classList.add` on data load; CountUp.js integration for score number (with `prefers-reduced-motion` guard); final mobile verification at 375x812; gauge entrance animation if time permits (P2).

**Uses from STACK.md:** Inter font (activated in Phase 1, applied universally in Phase 3 via `font-sans`); CountUp.js 2.9.0 UMD (added in script tags with `prefers-reduced-motion` guard); native CSS `@keyframes` (declared in Phase 1, triggered in Phase 3 JS).

**Addresses features from FEATURES.md:** Visual polish — spacing, typography, colour hierarchy (all P1); gauge entrance animation via `requestAnimationFrame` workaround (P2 — add if time allows).

**Avoids pitfalls:** Never reduce `min-height: 280px` on gauge container; never add zone colour to every page element (reserve for verdict label, hero border, explanation headings — colour overuse destroys signal value); always include `prefers-reduced-motion` guard around CountUp.js.

**Research flag:** Standard patterns — established Tailwind CDN + `<style>` block pattern is fully documented. No deeper research needed.

---

### Phase Ordering Rationale

- **HTML before JS:** Plotly gauge container dimensions are measured at `newPlot()` call time. The final DOM layout must exist before gauge initialisation fires — or an explicit `Plotly.Plots.resize()` call must follow any DOM change. Doing HTML restructure in Phase 1 means the gauge renders correctly in its final container from the start, eliminating the most critical pitfall at its source.
- **JS before CSS:** The verdict explanation section must have real content rendered before spacing and typography can be tuned correctly. CSS polish applied to empty or placeholder content requires rework when content arrives.
- **Pitfalls drive phase boundaries:** The three most critical pitfalls (Plotly zero-width, Tailwind class concatenation, ASIC copy) each map to a specific phase. Separating the phases makes each pitfall the sole focus of its phase's verification checklist.
- **Feature dependencies confirm this order:** All P1 features are frontend-only with no backend dependencies. No feature in Phase 2 or 3 requires anything outside the frontend codebase. Parallel execution is not beneficial — the dependencies are strictly sequential.

### Research Flags

Phases with standard patterns (no `/gsd:research-phase` needed):
- **Phase 1 (HTML Restructure):** Direct codebase inspection provides a complete implementation map. Tailwind CDN + Plotly resize patterns are well-documented with specific code examples. All element IDs and Playwright test targets are fully known from direct file inspection.
- **Phase 2 (Verdict Explanation):** InterpretationsModule extension pattern follows direct precedent from `renderMetricCard()`. ASIC framing rules are established by existing compliant functions. The contribution ranking algorithm `(value - 50) * weight` is documented with worked examples in ARCHITECTURE.md.
- **Phase 3 (Visual Polish):** Tailwind utility class application has no unknowns. CountUp.js integration is documented in STACK.md with a complete production-ready code snippet including the `prefers-reduced-motion` guard.

No phase in this milestone requires a `/gsd:research-phase` pass. All implementation decisions are fully resolved by existing codebase inspection and verified external documentation.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All technology decisions verified against official CDN registries, official docs, and Plotly changelog. Versions pinned and confirmed. Explicit anti-list (Tailwind v4, Plotly v3, Animate.css, Alpine.js, GSAP) grounded in confirmed breaking changes or architectural mismatches. |
| Features | HIGH | Competitor analysis against CNN Fear & Greed and MacroMicro confirmed directly. Feature prioritisation anchored to existing utility functions verified in the live codebase. Anti-feature list includes specific technical reasons for each deferral. |
| Architecture | HIGH | All findings from direct codebase inspection of 6 JS modules (98-694 LOC each), live status.json, and Playwright test files. No inference required. Integration points, data flow map, and build order all derived from reading actual source. |
| Pitfalls | HIGH | All 5 critical pitfalls verified against Plotly GitHub issues (#3984, #2769), official Tailwind CDN docs, official ASIC RG 244, and official Playwright locator docs. Recovery strategies and warning signs are concrete and specific. |

**Overall confidence:** HIGH

### Gaps to Address

- **CountUp.js `prefers-reduced-motion` guard:** STACK.md includes the correct wrapper pattern but it must be implemented (not just documented) in Phase 3. The guard is not optional — it is an accessibility requirement.
- **Onboarding accordion mobile behaviour:** PITFALLS.md flags the `<details open>` default as a mobile congestion risk after the hero redesign. Whether to change it to default-closed on mobile is a measurement-driven decision deferred to Phase 1 execution — test at 375x812 and decide based on actual vertical height.
- **Gauge entrance animation timing:** FEATURES.md marks this P2 (add after P1 features verified). The `requestAnimationFrame` workaround for Plotly indicator gauge animation is documented — the implementation approach is clear. The decision is whether Phase 3 has time for it, not how to implement it.

---

## Sources

### Primary (HIGH confidence)
- Direct codebase inspection: `public/index.html`, `public/js/gauge-init.js`, `public/js/interpretations.js`, `public/js/gauges.js`, `public/js/data.js`, `public/js/main.js`, `public/data/status.json`, `tests/dashboard.spec.js`, `tests/phase6-ux.spec.js`
- Plotly.js changelog: [plotly.com/javascript/version-3-changes](https://plotly.com/javascript/version-3-changes/) — v3 breaking title API changes confirmed
- Plotly GitHub issues #3984, #2769 — `responsive: true` only responds to `window.resize`; hidden container sizing bug confirmed
- Google Fonts CSS2 API docs: [developers.google.com/fonts/docs/css2](https://developers.google.com/fonts/docs/css2) — `wght@300..900` variable range syntax verified
- Tailwind CDN v3 docs: [tailwindcss.com/docs/installation/play-cdn](https://tailwindcss.com/docs/installation/play-cdn) — CDN class scanning limitations confirmed
- ASIC RG 244 (December 2012, updated 2021) — factual information vs. general advice distinction; hedged language requirements
- Official Playwright locator docs — `.nth()` flagged as fragile; `.filter({ hasText: ... })` preferred
- jsDelivr: [cdn.jsdelivr.net/npm/countup.js](https://cdn.jsdelivr.net/npm/countup.js/) — CountUp.js 2.9.0 UMD build confirmed

### Secondary (MEDIUM confidence)
- Tailwind community discussion #14210 — dynamic class concatenation not detected by CDN scanner
- Plotly community forum — `Plotly.Plots.resize(divId)` required after container reparenting
- CNN Fear & Greed Index — reference for verdict-as-hero design pattern
- MacroMicro Hawk-Dove Index — competitor feature comparison
- Toptal dashboard design — above-the-fold hero on mobile must fit within ~350px

### Tertiary (noted for completeness)
- Tailwind CDN v4 config format: [tailkits.com/blog/tailwind-css-v4-cdn-setup](https://tailkits.com/blog/tailwind-css-v4-cdn-setup/) — confirms migration cost; validates stay-on-v3 decision

---
*Research completed: 2026-02-25*
*Ready for roadmap: yes*
