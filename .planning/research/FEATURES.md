# Feature Research

**Domain:** Financial/Economic Data Dashboard — Visual Overhaul (v4.0)
**Researched:** 2026-02-25
**Confidence:** HIGH (dashboard UX patterns well-established; implementation details verified against existing codebase and Plotly.js documentation)

---

## Context: What Already Exists

The existing dashboard (v3.0, fully shipped) has:
- Plotly.js semicircle gauge (hero hawk score 0-100, 52px number, zone-coloured needle)
- 7 metric bullet gauges in a 3-column card grid with plain English interpretation
- ASX futures multi-meeting table with stacked probability bars
- Verdict text beneath the gauge: "HOLDING STEADY — The economy is giving mixed signals..."
- "Why it matters" one-liners per indicator card
- Mortgage calculator with scenario slider and comparison table
- Dark theme: `finance-dark #0a0a0a`, `finance-gray #1a1a1a`, `finance-border #2d2d2d`, `finance-accent #60a5fa`
- Tailwind CSS (CDN), Plotly 2.35.2, vanilla JS modules (no build step)
- `getZoneColor()`, `getStanceLabel()`, `getDisplayLabel()`, `getPlainVerdict()` functions already defined
- `generateMetricInterpretation()` and `getWhyItMatters()` already implemented per indicator

The milestone adds: (1) above-the-fold hero redesign, (2) verdict explanation section, (3) visual polish.

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features a polished financial/economic data dashboard in 2026 must have. Missing these makes the product feel unfinished compared to CNN Fear & Greed, Bloomberg, and peer dashboards.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Verdict dominates the hero** — the plain-English verdict label is the largest, most prominent element visible without scrolling | CNN Fear & Greed, Bloomberg Economic Conditions Dashboard — all best-in-class tools put the verdict ("FEAR", "GREED") first. Users arrive asking "will rates go up or down?" — the label IS the answer. | LOW | Currently `#verdict-container` sits below the gauge at text-lg. Needs to be the visual centre of gravity: font-size 36-48px, zone-coloured, above or overlapping the gauge area. Pure CSS change. |
| **Score is immediately legible as a number** — "34/100" is readable on first glance, not just readable from the gauge needle position | Best-in-class KPI dashboards (Robinhood, Bloomberg terminals) anchor the experience with a big tabular number. The needle IS useful but secondary to the number. | LOW | Plotly `number.font.size: 52` exists. May need layout tuning on mobile to prevent collision. Score should read clearly before the user understands what the gauge means. |
| **Score scale is explained physically near the verdict** — "Below 50 = pressure to cut. Above 50 = pressure to rise." | NN/g research: users need anchors to interpret scores. Without this, a "34" is meaningless. | LOW | `#scale-explainer` exists as a paragraph below the hero section. Needs to be repositioned inside or immediately adjacent to the hero card — currently it can scroll below the fold on mobile. |
| **Status colours are consistent across all elements** — same red = same zone everywhere (gauge needle, verdict label, verdict explanation headings, metric card borders) | Users learn a colour vocabulary. If the red verdict label and the blue gauge needle reference different zones, trust collapses. | LOW | `getZoneColor()` already returns the correct hex for any score. Verdict label, hero card border, and verdict explanation need to use this function consistently. The bullet gauges already use it. |
| **Loading states are graceful** — no layout shift, no blank areas during data fetch | Users read "blank = broken". Existing loading placeholders exist but may produce CLS (Cumulative Layout Shift). | LOW | Verify all loading placeholder `min-height` values match loaded content height. Hero gauge container has `min-height: 280px` — confirm this matches Plotly's rendered height. |
| **Mobile layout works first-tap** — no horizontal scroll, verdict is readable, gauge fits screen | 60%+ of Australian mortgage holders visit on phone. The hero verdict must be the first thing seen, not half a gauge. | LOW | Existing `lg:col-span-3/2` grid collapses correctly. Test specifically that verdict label wraps gracefully at narrow widths (< 375px) and gauge doesn't overflow. |
| **Data freshness is visible near the score** — users know if the score is current before they trust it | Economic data is monthly/quarterly. A user viewing in February needs to know if the score reflects January data. | LOW | `#data-freshness` div exists but sits above the gauge grid, separated from the verdict. Move it inside the hero card, directly beneath the verdict label. |

### Differentiators (Competitive Advantage)

Features that elevate this dashboard above any comparable tool. These serve the "Data, not opinion" value proposition.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Verdict Explanation Section** — a dedicated block that answers "why is the score X?" with two plain-English lists: what's pushing rates up, what's pulling them down | No comparable Australian mortgage tool does this. CNN Fear & Greed shows 7 indicator scores but gives no narrative synthesis. This is the missing layer between the score and the indicator cards. Users currently must infer the story themselves. | MEDIUM | New HTML section between hero and indicator grid. Logic: read `status.json` gauge values, filter those > 60 (hawkish, pushing rates up) and < 40 (dovish, pulling rates down), render as two labelled lists with coloured status dots and plain English names. Uses existing `getDisplayLabel()` + `generateMetricInterpretation()`. No new data needed — reads from existing status.json schema. |
| **Hero verdict label as the centrepiece** — oversized verdict text (e.g., 40-48px bold, zone-coloured) positioned above or overlapping the gauge, making the conclusion unmissable | CNN Fear & Greed's most-copied design decision: the large coloured word "FEAR" or "GREED" is what users remember and share. The number proves it; the word IS the message. | LOW | CSS-only change: increase `#verdict-container` font-size, move it above the Plotly gauge plot or into a banner above the gauge wrapper. Apply `color: getZoneColor(hawkScore)` inline via JS. Already called in `renderVerdict()` — extend it to set font size. |
| **Hero card with zone-coloured accent border** — the above-the-fold container has a top or left border coloured to match the current zone (e.g., `border-t-4 border-red-600` for hawkish) | Creates a visual "premium" zone distinct from supporting content below. The colour change reinforces the verdict at the card boundary level. Used by TradingView's market structure dashboards and Bloomberg's condition indicators. | LOW | Tailwind utility class applied dynamically via JS to the hero section wrapper: `border-t-4` + the appropriate zone colour class (or `style.borderColor = getZoneColor(score)`). Subtle but immediately perceived. |
| **Gauge entrance animation** — hero gauge needle sweeps from 0 to final value over ~800ms on page load | Creates a "reveal" moment that makes the score feel meaningful rather than static. Used by Bloomberg and Robinhood for primary KPI displays. | MEDIUM | Plotly indicator gauges do NOT support smooth native animation (confirmed: only scatter traces animate smoothly; indicator gauge transitions are instantaneous per Plotly docs and community). Workaround: manual `requestAnimationFrame` loop calling `Plotly.react` with value incrementing from 0 to target. Cap at hero gauge only — bullet gauges should not animate (performance, attention fragmentation). Approximately 60 frames at 16ms = ~960ms total. |
| **"What's driving this" two-column layout inside verdict explanation** — hawkish signals (red, right) and dovish signals (blue/green, left), omitting neutral indicators | Best pattern from consensus financial dashboards (ATC Dashboard / TradingView, MacroMicro Hawkish-Dovish Index). Users immediately see "Inflation is pushing rates up. Employment is pulling them down." Actionable in seconds. | MEDIUM | JS function: `getSignalLists(gauges)` → returns `{ hawkish: [...], dovish: [...] }` where hawkish = gauge value > 60, dovish = gauge value < 40. Render as CSS grid with two columns. Each entry: coloured dot + indicator name + one-line status from `generateMetricInterpretation()`. Depends entirely on existing data and functions. |
| **Score freshness badge integrated into hero** — "Updated 3 days ago" displayed immediately beneath the score/verdict | Users must know if they can trust the score before acting on it. Particularly critical for quarterly data (housing) that may be 2+ months old. | LOW | Reuse existing `renderStalenessWarning()` function, target it to a new element inside the hero card rather than the separate `#data-freshness` div above the grid. Two-line change in gauge-init.js and a new element in index.html. |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| **Native Plotly gauge transition animation** | Looks polished in concept — set `transition.duration` and the needle sweeps | Plotly.js only smoothly animates scatter/bar/line traces. Indicator gauge transitions are instantaneous regardless of `transition.duration` setting. Setting it creates false expectations and no effect. Confirmed in Plotly community forum and issue tracker. | Manual `requestAnimationFrame` loop: increment value from 0 to target in ~60 steps, call `Plotly.react` each frame. Scoped to hero gauge only. |
| **Dark/light theme toggle** | Modern UX expectation; users expect system preference respect | Every Tailwind class, every Plotly `paper_bgcolor`/`plot_bgcolor`/font colour, and every custom CSS variable would need dual definitions. This project uses no build step — Tailwind CDN with `class` dark mode cannot be toggled without `localStorage` + JS rewrite of all inline Plotly styles. High complexity for minimal value. | Stay dark. The finance-terminal aesthetic IS the brand. Document it. If system preference becomes important, add it in a future dedicated accessibility phase. |
| **Real-time refresh/polling** | Feels live and modern | ABS/RBA data updates monthly or quarterly. Fetching status.json every N seconds is pure theatre — the file won't change between browser visits. Adds JavaScript complexity, potential rate-limit issues with GitHub Pages, and user confusion about why the score never changes mid-session. | Keep the existing weekly GitHub Actions batch update. Show a clear "Last updated: 3 days ago" timestamp. Freshness is an honest display problem, not a polling problem. |
| **Sparkline charts inside each indicator card** | Shows trend over time | Each sparkline requires a historical series per metric — a significant schema extension (status.json currently stores only the latest snapshot). At 155px card height, adding a Plotly sparkline creates visual noise and performance cost (7 additional Plotly traces). | If trend context is needed, express it as text: "Inflation trending up over the past 3 months." This uses information already derivable from the multi-period z-score calculation. |
| **Zone colour on every UI element across the whole page** — make every section heading, card border, and table row match the hawk score zone | Seems visually rich and thematic | If everything is red when the score is high, the colour loses all meaning. Colour overuse in dashboards (confirmed by datacamp and UXPin guidelines) reduces scannability and can make a "warning" feel like "decoration". | Reserve zone colour for: (1) the verdict label, (2) the hero card accent border, (3) the verdict explanation section headings. Everything else stays in the neutral grey palette. |
| **Indicator direction delta badges (up/down arrow with "was 42, now 68")** | Trend context is valuable | Requires a `previous_value` or `delta` field per metric in status.json — a data pipeline change (engine.py must store and compute period-over-period deltas). This is a backend change masquerading as a frontend feature. | Defer to a future milestone when status.json schema is extended. The "why it matters" text already provides directional context in words. |
| **User accounts or saved configurations** | Personalisation — save my mortgage inputs, email alerts | Authentication requires backend infrastructure that GitHub Pages cannot provide. localStorage already persists calculator inputs without auth. | Continue localStorage for calculator. No accounts needed for this tool's scope. |

---

## Feature Dependencies

```
[Verdict Explanation Section]
    └──reads──> [status.json gauge values]                      (exists: status.json with .gauges)
    └──calls──> [getDisplayLabel(metricId)]                     (exists: gauges.js)
    └──calls──> [generateMetricInterpretation(metricId, data)]  (exists: interpretations.js)
    └──enhances──> [Hero Verdict Label Redesign]                (both reference same hawk_score zone)

[Hero Verdict Label Redesign]
    └──calls──> [getZoneColor(hawkScore)]                       (exists: gauges.js)
    └──calls──> [getStanceLabel(hawkScore)]                     (exists: gauges.js)
    └──required by──> [Hero Card Zone-Coloured Border]          (same zone colour logic)

[Hero Card Zone-Coloured Border]
    └──requires──> [getZoneColor()]                             (exists)
    └──enhances──> [Verdict Label Redesign]                     (consistent zone colour system)

[Gauge Entrance Animation]
    └──requires──> [hero gauge DOM element: #hero-gauge-plot]   (exists)
    └──conflicts──> [Plotly native indicator transitions]       (do not animate smoothly)
    └──requires──> [requestAnimationFrame loop workaround]      (manual implementation)
    └──independent of all other features in this milestone]

[Data Freshness in Hero Zone]
    └──calls──> [renderStalenessWarning()]                      (exists: interpretations.js)
    └──requires──> [new DOM element inside hero card]           (new: 1 HTML line)
    └──enhances──> [Hero Verdict Label Redesign]

[Direction Delta Badges per Indicator Card]
    └──requires──> [status.json delta/previous_value field]     (NOT IN SCHEMA — defer)
    └──requires──> [engine.py changes]                          (pipeline work, out of scope)
```

### Dependency Notes

- **Verdict Explanation Section is entirely self-contained on the frontend.** All required data structures and utility functions already exist. No engine.py, no status.json schema changes. This is a pure JS + HTML addition.
- **Gauge entrance animation conflicts with Plotly native.** Must implement via `requestAnimationFrame`. Scope strictly to hero gauge — bullet gauges must not animate.
- **All P1 features are frontend-only.** Zero backend changes for the core milestone deliverables.
- **Direction delta badges are explicitly deferred.** They require a data pipeline schema change that is out of scope for a visual overhaul milestone.

---

## MVP Definition

### Launch With (v4.0)

Minimum needed to deliver the three milestone goals: hero redesign, verdict explanation, visual polish.

- [ ] **Verdict label promoted to visual hero** — large (36-48px), zone-coloured, positioned above or at the top of the gauge area. CSS + `renderVerdict()` update. Single most impactful visual change.
- [ ] **Verdict explanation section** — new HTML section between hero and indicator grid. Two plain-English lists: "Pushing rates up: Inflation (above target), Housing (prices rising)." and "Holding rates down: Employment (jobs softening), Spending (consumers cautious)." Derived from gauge values at runtime. No new data.
- [ ] **Hero card with zone-coloured accent border** — top or left border of the hero section card matches current zone colour. Reinforces verdict visually. CSS + 1 line of JS.
- [ ] **Data freshness repositioned into hero zone** — `renderStalenessWarning()` called on a new element inside the hero card, not the separate `#data-freshness` div above the gauge grid. Users need "this score is current" near the verdict.
- [ ] **Scale explainer physically adjacent to verdict** — `#scale-explainer` moved inside or directly below the hero card. Currently separated by the gauge; can scroll below fold on mobile.

### Add After Validation (v4.x)

- [ ] **Gauge entrance animation** — hero gauge sweeps from 0 to final value on load. Delight feature. Implement after P1 features ship and are verified working.
- [ ] **Mobile hero height profiling** — profile actual render heights on sub-400px viewports and adjust Plotly `height` config if gauge overflows.

### Future Consideration (v5+)

- [ ] **Indicator delta/direction badges** — "Inflation up from 45 last month." Requires pipeline schema extension.
- [ ] **Historical hawk score chart** — line chart of composite score over time. Requires archiving status.json snapshots (not currently stored — only current snapshot exists).
- [ ] **Notification alerts** — "Email me when score crosses 70." Requires backend infrastructure beyond GitHub Pages scope.

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Verdict label as hero (large, coloured, prominent) | HIGH | LOW | P1 |
| Verdict explanation section (what's driving the score) | HIGH | MEDIUM | P1 |
| Hero card zone-coloured accent border | HIGH | LOW | P1 |
| Data freshness inside hero zone | MEDIUM | LOW | P1 |
| Scale explainer adjacent to verdict | MEDIUM | LOW | P1 |
| Gauge entrance animation (sweep from 0) | MEDIUM | MEDIUM | P2 |
| Mobile hero height tuning | LOW | LOW | P2 |
| Indicator direction delta badges | HIGH | HIGH (pipeline required) | P3 |
| Historical hawk score chart | MEDIUM | HIGH (data model change) | P3 |

**Priority key:**
- P1: Ships with v4.0 — core milestone deliverables
- P2: Add after v4.0 verification, within same milestone if time allows
- P3: Future milestone — requires backend or data model work

---

## Competitor Feature Analysis

| Feature | CNN Fear & Greed | MacroMicro Hawk-Dove Index | Our Approach (v4.0) |
|---------|-----------------|---------------------------|---------------------|
| Composite score 0-100 | Yes — large semicircle dial | Yes — line chart | Plotly gauge (exists) |
| Verdict label prominent | Yes — "FEAR" large, coloured, dominant above dial | Yes — zone label prominent | Promoted to hero centrepiece (new) |
| Data freshness near score | Yes — "as of yesterday" | Yes — date label near chart | Move `#data-freshness` into hero card (new) |
| Individual indicator breakdown | Yes — 7 sub-meters below dial | Yes — multiple indicator lines | Exists: 7 bullet gauge cards |
| "What's driving" narrative | No — shows raw sub-scores only | No — shows raw time series | DIFFERENTIATOR: verdict explanation section (new) |
| Plain English per-indicator copy | No — uses financial jargon | No | Exists: "why it matters" text per card |
| Entrance animation | No — static on load | No | To add (P2) |
| Dark theme | No (light) | Partial | Exists — maintained |
| Zone-coloured card accent | No | No | New: hero card border (new) |
| Mortgage impact calculator | No | No | Exists |

---

## Sources

- CNN Fear & Greed Index — reference for verdict-as-hero design pattern: [https://www.cnn.com/markets/fear-and-greed](https://www.cnn.com/markets/fear-and-greed)
- UXPin dashboard design principles — hero placement, progressive disclosure, indicator cards: [https://www.uxpin.com/studio/blog/dashboard-design-principles/](https://www.uxpin.com/studio/blog/dashboard-design-principles/)
- Plotly.js indicator gauge animation limitations — only scatter traces animate; gauge is instantaneous: [https://community.plotly.com/t/animations-on-gauge-needle/5804](https://community.plotly.com/t/animations-on-gauge-needle/5804)
- Plotly.js animations reference — `requestAnimationFrame` workaround documented: [https://plotly.com/javascript/animations/](https://plotly.com/javascript/animations/)
- Typography hierarchy for data dashboards — 24-32px hero, 3-4 levels max, 4.5:1 contrast: [https://datafloq.com/typography-basics-for-data-dashboards/](https://datafloq.com/typography-basics-for-data-dashboards/)
- Dark mode UI best practices 2025 — charcoal over pure black, off-white body text, 1.5x line height: [https://www.graphiceagle.com/dark-mode-ui/](https://www.graphiceagle.com/dark-mode-ui/)
- Dashboard design DataCamp — inverted pyramid, top-left critical placement, minimal hierarchy: [https://www.datacamp.com/tutorial/dashboard-design-tutorial](https://www.datacamp.com/tutorial/dashboard-design-tutorial)
- Fintech KPI card patterns — big number + short label + delta: [https://uisea.net/fintech-dashboard-ui-kpis-card-patterns-tables-figma-guide/](https://uisea.net/fintech-dashboard-ui-kpis-card-patterns-tables-figma-guide/)
- MNI FOMC Hawk-Dove Spectrum — indicator contribution display reference: [https://www.mnimarkets.com/mni-fomc-hawk-dove-spectrum](https://www.mnimarkets.com/mni-fomc-hawk-dove-spectrum)
- Tailwind gradient/glow border patterns: [https://tailwindflex.com/@prashant/glowing-gradient-border](https://tailwindflex.com/@prashant/glowing-gradient-border)
- Fintech dashboard UX trends 2025: [https://www.designstudiouiux.com/blog/fintech-ux-design-trends/](https://www.designstudiouiux.com/blog/fintech-ux-design-trends/)
- Existing codebase: `/Users/annon/projects/rba-hawko-meter/public/` — confirmed all utility functions and data shapes (HIGH confidence, direct analysis)

---
*Feature research for: RBA Hawk-O-Meter v4.0 Dashboard Visual Overhaul*
*Researched: 2026-02-25*
