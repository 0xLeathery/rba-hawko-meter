# Pitfalls Research

**Domain:** Dashboard Visual Overhaul — Adding hero redesign and verdict explanation to existing vanilla JS / Tailwind CDN / Plotly.js dashboard
**Researched:** 2026-02-25
**Confidence:** HIGH (direct codebase analysis + verified against Plotly.js issues, Tailwind CDN docs, ASIC RG 244, Playwright docs)

---

## Critical Pitfalls

### Pitfall 1: Plotly Gauge Renders at Zero Width After Hero DOM Restructure

**What goes wrong:**
The hero section currently places `#hero-gauge-plot` inside a `lg:col-span-3` grid column. If the redesign wraps the gauge in a new flex or grid container — or inserts new sibling elements that change the parent's computed width before Plotly renders — the gauge initializes with zero or minimal width and never recovers. The Plotly SVG renders at 0px width and the gauge appears as a thin sliver or disappears entirely. `responsive: true` in the config only triggers re-layout on **window resize**, not on container-size changes caused by DOM mutation.

**Why it happens:**
Plotly measures the container's `offsetWidth` at the moment `Plotly.newPlot()` is called. If the parent element's layout is still settling (e.g., flexbox is redistributing space, a sibling above-the-fold element has been inserted but not painted), the container may report a smaller or zero width. `autosize: true` does not fix this — it only subscribes to the `window.resize` event. The existing code in `gauge-init.js` already calls `Plotly.relayout('hero-gauge-plot', { autosize: true })` in the resize handler, but this handler fires on window resize only, not on programmatic layout changes.

**How to avoid:**
- Never rely on implicit paint timing for gauge initialization. Call `Plotly.newPlot()` inside a `requestAnimationFrame()` callback, or add a zero-delay `setTimeout()` after inserting new above-the-fold elements.
- After adding the new hero section HTML above the gauge, call `Plotly.Plots.resize('hero-gauge-plot')` explicitly once the new elements have painted.
- If adding a verdict summary block **above** the gauge container in the DOM, measure impact on grid column layout before calling `createHeroGauge()`.
- Set `min-height: 280px` on `#hero-gauge-plot` (already present via inline style) — do not remove or reduce this value.

**Warning signs:**
- Hero gauge container is visible but gauge SVG is present with `width="0"`.
- Gauge renders correctly on mobile (narrow viewport where no reflow occurs) but is broken on desktop where the new hero grid applies.
- Playwright test "Hero gauge renders with hawk score" times out waiting for `svg.main-svg` instead of failing cleanly.

**Phase to address:**
Phase 1 (hero redesign). Test gauge rendering at 375px, 768px, 1024px, and 1440px immediately after adding any new above-the-fold HTML. Do not leave this for the visual polish phase.

---

### Pitfall 2: Tailwind CDN Drops Dynamically Constructed Classes

**What goes wrong:**
The existing codebase uses Tailwind utilities correctly — all class names are statically present as complete strings. But when adding verdict explanation cards or score-driven color highlighting to the new hero section, developers construct class names via string concatenation in JS, e.g.:

```javascript
// WRONG — Tailwind CDN cannot detect this at runtime
card.className = 'border-' + zoneColor + '-500';

// WRONG — same problem with template literals
card.className = `bg-${direction === 'up' ? 'red' : 'blue'}-400`;
```

The Tailwind CDN scans the document source at runtime to generate CSS. It cannot execute JS expressions to discover what class names will eventually appear. Concatenated class names are never generated, so the styles silently fail to apply.

**Why it happens:**
Tailwind's Play CDN works by scanning for class name tokens at load time. String concatenation produces class names that are not present as literal tokens, so Tailwind never generates the corresponding CSS rules. The component renders, the class is applied, but there is no CSS to match it. This is identical to the build-time purging problem in production Tailwind, but it affects the CDN version at runtime.

**How to avoid:**
Use a complete-class lookup object for any JS-driven class assignment:

```javascript
// CORRECT — all class names are literal strings Tailwind can detect
var ZONE_BORDER_CLASSES = {
  cold:    'border-blue-800',
  cool:    'border-blue-400',
  neutral: 'border-gray-500',
  warm:    'border-red-400',
  hot:     'border-red-600'
};
card.className = 'border ' + ZONE_BORDER_CLASSES[zone];
```

This pattern is already used indirectly via `GaugesModule.getZoneColor()` (which returns hex values applied via `style.color`, bypassing Tailwind entirely). Follow the same pattern for any new verdict card colour logic: use `element.style.backgroundColor = hexValue` for dynamic colours, not Tailwind utility classes.

**Warning signs:**
- New verdict card appears with correct layout but incorrect (missing) background or border colour.
- Colour applies in the browser devtools when you manually add the class, but not when JS applies it.
- Playwright test for verdict colour passes because it checks text content, not visual colour.

**Phase to address:**
Phase 2 (verdict explanation section). Audit every `className` assignment in new code before committing. For score-driven colours, prefer `element.style` with hex values (following `GaugesModule.getZoneColor()` pattern) over Tailwind utility classes.

---

### Pitfall 3: Verdict Explanation Text Crosses Into General Advice Territory

**What goes wrong:**
The v4.0 verdict explanation section will show "which indicators are driving the score up/down." Developers write copy that sounds intuitive but crosses from factual information into general advice under ASIC RG 244. The violation is subtle — it is not the data itself but the framing that creates the problem.

Examples of language that crosses the line:

- "Inflation is high. **You should consider locking in a fixed rate now.**" — personal financial advice
- "The RBA is **likely to raise rates at the next meeting.**" — forward-looking prediction presented as probable fact
- "This indicator suggests **rates will rise** in the next quarter." — prediction, not factual summary
- "**Now is a good time** to speak to a mortgage broker." — recommendation

The existing `getPlainVerdict()` function is compliant: "Interest rates may be more likely to rise than fall" uses hedged language ("may be more likely"). The risk emerges when adding explanatory bullet points per indicator, where authors instinctively write more direct copy.

**Why it happens:**
Explaining *why* a score is high naturally pulls language toward prediction and recommendation. Plain English clarity and compliance neutrality are in direct tension. The more readable an explanation, the more likely it sounds like advice.

**How to avoid:**
Strict framing rules for all new verdict copy:
- State what the indicator is doing, not what it means for the user's decisions.
- Use "the data shows" / "this indicator is" / "historically, this has been associated with" — not "therefore you should" or "this means rates will."
- Never predict a specific RBA outcome. "The data is consistent with pressure to raise rates" is compliant. "The RBA will raise rates" is not.
- Mirror the existing `getWhyItMatters()` pattern: "When prices rise too fast, the RBA **tends to** raise interest rates to slow things down" — note the use of "tends to," which expresses a historical pattern, not a forecast.
- Every new explanatory paragraph must pass the test: "Would a person reading this feel they have received personal advice about their financial decisions?" If yes, rewrite.

**Warning signs:**
- Any sentence containing "you should," "you need to," "it is time to," "now is a good time."
- Any forward prediction without hedging: "rates will," "the RBA will," "this means rates are going to."
- Copy that is specific to a user's personal situation ("if you have a variable rate mortgage...").
- A non-lawyer reviewer describes the text as "advice."

**Phase to address:**
Phase 2 (verdict explanation section). Review all new copy against this checklist before each commit. If uncertain, use the most conservative hedging available.

---

### Pitfall 4: Playwright Tests Break on nth-Index Selectors After Card Count Changes

**What goes wrong:**
`dashboard.spec.js` and `phase6-ux.spec.js` use `.nth(0)`, `.nth(1)`, `.nth(5)`, etc. to address specific metric cards:

```javascript
// This breaks if a new card is inserted above inflation in the hero area,
// or if the verdict explanation renders into the metric-gauges-grid
const inflationCard = allCards.nth(0);   // Assumes inflation is always first
const wagesCard = allCards.nth(1);       // Assumes wages is always second
const buildingCard = allCards.nth(5);    // Assumes building_approvals is 6th
```

If the hero redesign adds any new `bg-finance-gray` element into or near `#metric-gauges-grid`, or if the verdict explanation section uses the same CSS class structure, these nth selectors will point to the wrong cards and tests will either fail with wrong assertions or silently pass against unexpected elements.

**Why it happens:**
The tests rely on positional ordering (nth) which is structurally brittle. Any insertion of a new element that matches the `[class*="bg-finance-gray"]` selector before the expected card invalidates all subsequent nth indices. The existing tests acknowledge this risk in comments ("index 5 — housing now active at index 3") — the indices have already shifted once during development.

**How to avoid:**
- Do not add any new `bg-finance-gray` elements into `#metric-gauges-grid` except for indicator cards rendered by `renderMetricCard()`.
- The verdict explanation section must use a distinct container ID (`#verdict-explanation` or similar) that is **outside** the `#metric-gauges-grid` element.
- Before any DOM change that affects the grid, run the full Playwright suite to establish a passing baseline.
- When the tests inevitably need updating: replace nth selectors for named indicators with `.filter({ hasText: 'Inflation' })` — which the housing and business conditions tests already use correctly.
- Do not add `data-testid` attributes to existing elements (changes are intentionally minimal), but do add `data-testid` to any new hero or verdict elements introduced in v4.0.

**Warning signs:**
- Playwright test 2 ("Individual metric cards render with interpretations") passes but `allCards.nth(0)` contains text other than "Prices up."
- Playwright test 18 ("Weight badges show importance labels") fails because `allCards.nth(5)` is no longer the building approvals card.
- Adding a new hero summary card causes a cascade of test failures across dashboard.spec.js and phase6-ux.spec.js.

**Phase to address:**
Phase 1 (hero redesign). Run Playwright suite before and after every structural HTML change. Do not touch `#metric-gauges-grid` from the hero redesign phase — that is the verdict explanation section's concern.

---

### Pitfall 5: Mobile Above-the-Fold Congestion After Hero Redesign

**What goes wrong:**
The current hero section at mobile (375px) already stacks: disclaimer banner → header → onboarding details → data freshness → hero gauge (280px min-height) → verdict container → jump link → scale explainer → ASX futures → cash rate. This vertical stack is already long. Adding a prominent verdict + hawk score "visual centrepiece" without reducing other elements will push the critical content (the verdict) below the fold on mobile, defeating the purpose of the redesign.

The grid layout `grid-cols-1 lg:grid-cols-5` already collapses to full-width columns on mobile. Any new element inserted into the hero section adds to mobile height without a corresponding reduction elsewhere.

**Why it happens:**
Designers prototype at desktop dimensions where the 5-column grid spreads content horizontally. On mobile, every grid item stacks. The hero gauge alone is 280px. The onboarding `<details open>` element adds ~120px. Adding a verdict hero section that is visually prominent on desktop (e.g., large score + bold verdict text) adds another 100-200px on mobile. The page is too long before the user sees the indicators.

**How to avoid:**
- Measure total above-the-fold height at 375px after each hero change. The verdict and score must be visible without scrolling on a 812px-tall mobile viewport (iPhone SE height).
- Consider collapsing the onboarding `<details>` to `open` only on desktop, or moving it below the hero at mobile.
- The hero redesign should **replace** the current verbose verdict container and scale explainer, not **add above** them.
- Design constraint: on mobile, the entire hero (score + verdict + 1 sentence explanation) must fit in approximately 350-400px vertical space.

**Warning signs:**
- Playwright viewport test at 375x812 requires scrolling to see the verdict.
- The onboarding details element and the hero verdict area are both fully expanded on mobile, causing >600px of content before the first indicator.
- Page LCP (Largest Contentful Paint) is the Plotly gauge SVG at >300px offset from the viewport on mobile.

**Phase to address:**
Phase 1 (hero redesign). Test at 375px after every above-the-fold HTML change, not just at desktop. Consider whether the onboarding `<details open>` default should change for mobile users.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Adding new Tailwind classes dynamically via string concatenation | Readable code | Classes silently absent at runtime — CDN cannot detect them | Never — use complete-string lookup tables or `element.style` with hex values |
| Embedding verdict copy directly in JS strings without compliance review | Fast to write | ASIC compliance risk; may constitute general advice | Never — all new verdict copy must pass the factual-information test |
| Referencing metric cards by nth index in tests | Simple to write | Breaks on any DOM insertion; has already caused test failures in v1.x | Never for named indicators — use `.filter({ hasText: ... })` instead |
| Reducing `min-height` on `#hero-gauge-plot` to make room for new elements | More room for hero content | Gauge renders at insufficient height; SVG clips; looks broken on mid-size viewports | Never — 280px is the minimum safe height for Plotly indicator gauges |
| Wrapping the existing gauge container in a new div without calling `Plotly.Plots.resize()` | Simpler DOM manipulation | Gauge renders at wrong size inside new container | Never — always trigger a resize after reparenting a Plotly container |
| Keeping `open` attribute on onboarding `<details>` at all viewport sizes | Consistent behavior | Pushes hero content below fold on mobile after redesign adds more height above it | Acceptable only if hero redesign removes sufficient vertical space to compensate |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Plotly.js + new above-the-fold hero elements | Call `Plotly.newPlot()` before new DOM elements have painted | Wrap `createHeroGauge()` in `requestAnimationFrame()` or call `Plotly.Plots.resize()` after inserting new hero HTML |
| Tailwind CDN + JS-driven score colours | Use Tailwind utility classes assembled by string concatenation | Use `element.style.color = GaugesModule.getZoneColor(score)` — already the established pattern in `gauges.js` |
| Verdict explanation section + `#metric-gauges-grid` | Add explanation cards inside the gauges grid | Put explanation in a dedicated `<section id="verdict-explanation">` that is structurally separate |
| Playwright + `nth()` selectors + new cards | Add new `bg-finance-gray` cards anywhere near the gauges grid | Use `.filter({ hasText: 'Indicator Name' })` for named cards; never add elements that match the grid card selector to other sections |
| ASIC compliance + indicator-specific explanations | Write "CPI is above target therefore rates will rise" | Write "Inflation data shows prices rising at X% — historically this has been associated with upward rate pressure" |
| Python pipeline + JS-only changes | Accidentally modify `status.json` schema expectations in JS | v4.0 is frontend-only; `status.json` schema must not change; any new field in JS must be optional and defaulted |
| Hero redesign + `#verdict-container` / `#calculator-jump-link` | Remove or rename existing IDs that Playwright tests assert against | Phase6-ux.spec.js tests IDs: `#verdict-container`, `#scale-explainer`, `#calculator-jump-link`, `#onboarding` — these must survive the redesign |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Plotly renders all 8 gauges (hero + 7 metric) simultaneously on load | Visible layout jank; first meaningful paint delayed by 400-800ms | The existing `requestAnimationFrame()` stagger in `gauge-init.js` handles this — do not remove it | If the hero redesign calls `createHeroGauge()` outside the RAF stagger pattern |
| Large hero section causes layout shift before Plotly renders | CLS (Cumulative Layout Shift) spike; hero snaps from placeholder to full gauge | Set `min-height: 280px` on gauge container (already present); do not set it to `auto` | If new hero wrapper removes the `min-height` style |
| Tailwind CDN scanning large new hero HTML at load | Page style recalculation noticeably delayed on first load | Minimal new HTML only; avoid embedding large SVGs or complex template HTML in the hero | If hero section adds >100 new DOM elements |
| New `<details>` or collapsed sections above the gauge | Plotly renders inside a hidden/zero-height container before section expands | Open all sections by default, or render gauge only after the section opens (add event listener on `toggle`) | If any new collapsible element wraps the hero gauge container |

---

## Security Mistakes

This is a static, read-only dashboard — no user inputs are stored or transmitted except the mortgage calculator (client-side only). Security surface is minimal. The relevant risks are:

| Mistake | Risk | Prevention |
|---------|------|------------|
| Adding `innerHTML` to new verdict explanation elements | XSS if `status.json` data is ever compromised or tampered | Follow the established pattern: use `element.textContent` only. Never use `innerHTML` for data-driven content. The existing modules are already safe — maintain this invariant. |
| Adding user-editable text fields to the verdict explanation | Stored XSS if field content is ever persisted | The verdict explanation is read-only output from `status.json` — do not add input fields |
| Referencing `status.json` fields with loose null checks | Broken display if pipeline changes field names | Guard every new field access with `data.field != null` checks before use |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Hero score displayed as raw number without context ("37/100") | User does not know if 37 is good or bad | Display score + zone label + brief verdict sentence together; do not separate them |
| Verdict explanation lists all 7 indicators with equal weight | Information overload; user cannot identify the key drivers | Show top 2-3 drivers only — the indicators with the largest deviation from neutral (z-score furthest from 50) |
| Indicator cards in verdict explanation repeat the same data as the gauges grid below | Redundant information; no reason to scroll | The explanation section should show only the *drivers* (indicators pulling score strongly in one direction), not all 7 |
| Hawk score hero is the only element with colour (others stay grey) | Dark theme looks polished but verdict colour is disconnected from the rest of the page | Apply zone colour consistently to: score text, verdict heading, any verdict explanation card borders — not just the gauge needle |
| "See what this means for your mortgage" link is the only call-to-action | Users who are not mortgage holders are not served | The jump link is appropriate; do not add more CTAs (financial advice risk) |

---

## "Looks Done But Isn't" Checklist

- [ ] **Gauge renders correctly at all breakpoints:** Verify `#hero-gauge-plot` is not zero-width at 375px, 768px, 1024px, and 1440px viewports. Run `Playwright.Plots.resize()` test manually.
- [ ] **No concatenated Tailwind classes in new JS:** Search all new JS files for `bg-\$` or `border-\$` or `text-\$` patterns. Every Tailwind class used in JS must be a complete literal string.
- [ ] **ASIC copy review complete:** Every new sentence in verdict/explanation copy has been reviewed against the factual-information test. No sentence contains "you should," "rates will," or "now is the time."
- [ ] **Playwright suite still passes 28/28 tests:** Run `npm run verify:playwright` after every structural HTML change. Do not defer this to end of milestone.
- [ ] **Existing element IDs preserved:** Confirm `#verdict-container`, `#scale-explainer`, `#calculator-jump-link`, `#onboarding`, `#hero-gauge-plot`, `#metric-gauges-grid`, `#asx-futures-container` all still exist in the DOM after redesign.
- [ ] **Mobile above-fold test:** Open browser at 375x812. Everything above "Economic Indicators" heading should be visible — hawk score and verdict in particular — without scrolling.
- [ ] **Python pipeline untouched:** Run `npm run test:fast` (411 unit tests + coverage check). Any Python test failure is a sign that something in the JS phase accidentally modified shared files.
- [ ] **status.json schema not changed:** The verdict explanation section reads from `status.json` but must not require new fields to function. All new field accesses must be optional with graceful defaults.

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Gauge renders at zero width after hero change | LOW | Call `Plotly.Plots.resize('hero-gauge-plot')` in browser console to confirm resize fixes it; then wrap the `createHeroGauge()` call in `requestAnimationFrame()` |
| Concatenated Tailwind class is not applying | LOW | Switch the CSS assignment to `element.style.color = hexValue` using the existing `GaugesModule.getZoneColor()` return value |
| ASIC copy violation discovered in review | MEDIUM | Rewrite using hedged language ("the data is consistent with," "historically associated with"); do not attempt to soften rather than rewrite |
| Playwright nth-selector tests break after DOM change | LOW-MEDIUM | Replace `allCards.nth(N)` with `allCards.filter({ hasText: 'Indicator Name' })` for any named indicator; update count assertions |
| Mobile hero overflows viewport after redesign | MEDIUM | Remove one of: onboarding `<details open>`, scale explainer text, or verdict container redundancy — the hero should be a replacement, not an addition |
| Python tests fail after frontend-only commit | LOW | Check if `public/data/status.json` was accidentally modified; restore from git; pipeline tests are isolated from JS changes unless data files change |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Plotly zero-width render after DOM restructure | Phase 1: Hero redesign | Playwright test "Hero gauge renders with hawk score" passes at 375px, 768px, 1024px |
| Tailwind CDN concatenated class names | Phase 2: Verdict explanation section | Grep for `bg-\$` / `border-\$` / `text-\$` in new JS files; visual test shows correct colours |
| ASIC compliance — general advice language | Phase 2: Verdict explanation copy | Copy review checklist applied to every new sentence before commit |
| Playwright nth-selector fragility | Phase 1: Hero redesign | Full Playwright suite runs passing before and after each structural HTML change |
| Mobile above-fold congestion | Phase 1: Hero redesign | Browser test at 375x812 — verdict visible without scrolling |
| Dynamically structured DOM breaking card count assertions | Phase 2: Verdict explanation section | `toHaveCount(7)` assertion in dashboard.spec.js still passes after verdict section added |
| IIFE module load order regression | Phase 1 or 2 | `data.js` → `chart.js` → `countdown.js` → `calculator.js` → `main.js` → `gauges.js` → `interpretations.js` → `gauge-init.js` order preserved in `index.html` |
| New hero element IDs shadowing existing IDs | Phase 1: Hero redesign | All 28 Playwright tests pass; no `duplicate ID` warnings in browser console |
| status.json schema dependency for new features | Phase 2: Verdict explanation section | Simulate `status.json` with missing new fields; verify explanation renders a default/empty state gracefully |

---

## Sources

- Direct codebase analysis: `public/js/gauge-init.js` — `setupResizeHandler()` only fires on `window.resize`; `Plotly.relayout({autosize: true})` does not trigger on container DOM changes
- Direct codebase analysis: `public/js/gauges.js` — `getZoneColor()` returns hex values; existing colour logic uses `element.style.color`, not Tailwind classes — established safe pattern
- Direct codebase analysis: `public/js/interpretations.js` — `getPlainVerdict()` and `getWhyItMatters()` show the correct compliant language patterns already in use
- Direct codebase analysis: `tests/dashboard.spec.js` and `tests/phase6-ux.spec.js` — nth-index selectors `.nth(0)`, `.nth(1)`, `.nth(5)` identified as fragility risk; existing filter pattern `.filter({ hasText: '...' })` already in use for housing and business conditions cards
- Direct codebase analysis: `public/index.html` — existing element IDs that Playwright asserts against; hero section HTML structure; script load order
- Plotly.js GitHub issue #3984: "Plotly Not Responsive When Parent Size Changes" — confirms `responsive: true` only responds to window resize, not container resize (HIGH confidence — official issue tracker)
- Plotly.js GitHub issue #2769: "Resize bug using Details/hidden Div and width=100%" — confirms hidden-container sizing bug (HIGH confidence — official issue tracker)
- Plotly community forum: resize after container change requires `Plotly.Plots.resize(divId)` explicit call (MEDIUM confidence — community verified pattern)
- Tailwind CSS v3 Play CDN docs: "not intended for production; cannot use tailwind.config.js customizations" — confirms CDN class scanning limitations (HIGH confidence — official Tailwind docs)
- Tailwind community discussion #14210 and Medium article: dynamic class name concatenation is not detected by CDN or build scanner; complete class names required (HIGH confidence — official docs + community confirmation)
- ASIC RG 244 (December 2012, updated 2021): defines factual information vs. general advice distinction; key test is whether provider "has considered one or more of the client's objectives, financial situation and needs" (HIGH confidence — official regulatory guide)
- ASIC "Tips for giving limited advice": hedged language patterns; "tends to," "historically associated with," "may be more likely" (HIGH confidence — official ASIC guidance)
- Playwright docs — locators: `.nth()` flagged as fragile; prefer `getByRole()`, `getByTestId()`, `.filter({ hasText: ... })` (HIGH confidence — official Playwright docs)
- BrowserStack "15 Playwright Selector Best Practices 2026": nth selectors break when DOM structure changes; data-testid is preferred (MEDIUM confidence — practitioner source, consistent with official docs)
- Toptal "Intuitive Mobile Dashboard UI": above-the-fold hero on mobile must fit within ~350px to avoid scroll requirement (MEDIUM confidence — practitioner design source)

---
*Pitfalls research for: Dashboard Visual Overhaul (v4.0) — hero redesign, verdict explanation, visual polish*
*Researched: 2026-02-25*
