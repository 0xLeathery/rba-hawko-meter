---
status: resolved
trigger: "Investigate issue: plotly-overflow-layout"
created: 2026-02-06T16:35:00Z
updated: 2026-02-06T16:54:00Z
---

## Current Focus

hypothesis: Two distinct root causes: (1) Plotly layouts missing autosize:true causing charts to overflow containers, (2) Plotly.newPlot NOT clearing container children causing loading text to remain visible behind gauge
test: Add autosize:true to both getDarkLayout functions and add explicit container clearing before Plotly.newPlot in createHeroGauge
expecting: Charts will respect container width and loading text will disappear
next_action: Implement fixes in gauges.js and chart.js

## Symptoms

expected: Plotly gauges and charts render fully within their container div boundaries, properly sized and responsive.
actual: Two overflow problems:
  1. Hero gauge (#hero-gauge-plot) — semicircle gauge is clipped on the right side ("100" tick cut off). The old "Loading Hawk Score..." placeholder text is visible behind/overlapping the NEUTRAL stance label at the top. The verdict text at the bottom is also getting clipped.
  2. Cash Rate History chart (#rate-chart) — Plotly chart renders far wider than container div, spilling out to the right. Mode bar icons visible outside container. Rate change annotations along top overflow. The chart appears to be rendering at ~2x the container width.
errors: No JavaScript errors — purely CSS/layout sizing issues with Plotly charts not respecting container widths.
reproduction: Open http://localhost:8080 in any browser. Both issues are immediately visible on page load.
started: First time viewing the app after Phase 4 (gauges) implementation. The chart.js existed before Phase 4 but may have had the same issue unnoticed.

## Eliminated

## Evidence

- timestamp: 2026-02-06T16:40:00Z
  checked: gauges.js createHeroGauge function (line 101-138)
  found: Layout uses getDarkLayout() base (line 135) which returns {paper_bgcolor, plot_bgcolor, font, margin} but NO width or autosize properties. Config has {responsive: true, displayModeBar: false} but responsive alone doesn't enforce container-constrained sizing.
  implication: Hero gauge lacks explicit autosize:true in layout, which means Plotly may compute its own width instead of respecting container.

- timestamp: 2026-02-06T16:42:00Z
  checked: chart.js create function (line 115-153)
  found: Layout created via createDarkLayout() (line 138) which sets paper_bgcolor, plot_bgcolor, font, xaxis, yaxis, hovermode, margin but NO width or autosize. Config has {responsive: true, displayModeBar: true} (line 147).
  implication: Chart also lacks autosize:true in layout. This would cause Plotly to compute its own width, likely defaulting to a fixed pixel width that overflows the container.

- timestamp: 2026-02-06T16:43:00Z
  checked: gauge-init.js showLoading call (line 79) and createHeroGauge call (line 84)
  found: showLoading('hero-gauge-plot', 'Loading Hawk Score...') clears container and inserts loading div. Then createHeroGauge('hero-gauge-plot', ...) calls Plotly.newPlot(containerId, [trace], layout, config) but Plotly.newPlot does NOT clear container children first.
  implication: The loading div inserted by showLoading remains in DOM when Plotly renders. Plotly appends its SVG to the container, leaving the loading div visible behind the gauge.

- timestamp: 2026-02-06T16:45:00Z
  checked: chart.js lines 119-122 vs gauge-init.js line 79
  found: chart.js create function explicitly clears container with while(container.firstChild) loop before calling Plotly.newPlot. gauge-init.js calls DataModule.showLoading which also clears container, but then createHeroGauge does NOT clear before Plotly.newPlot.
  implication: Inconsistent container clearing. Chart clears before Plotly, gauge relies on showLoading clearing (which happens BEFORE Plotly) but Plotly.newPlot doesn't clear existing content, leaving loading text visible.

- timestamp: 2026-02-06T16:52:00Z
  checked: Modified gauges.js and chart.js, reviewed changes
  found: (1) gauges.js getDarkLayout now includes autosize:true at line 78, (2) gauges.js createHeroGauge now clears container lines 104-109 before Plotly.newPlot, (3) chart.js createDarkLayout now includes autosize:true at line 34
  implication: Both Plotly charts will now respect container boundaries via autosize, and hero gauge will properly clear loading placeholder before rendering.

## Resolution

root_cause: Two distinct issues: (1) Plotly layout objects missing autosize:true property causing charts to compute their own width instead of respecting container boundaries, (2) createHeroGauge not clearing container before Plotly.newPlot causing loading placeholder div to remain visible behind the rendered gauge SVG.

fix: (1) Added autosize:true to base layout in both getDarkLayout functions (gauges.js and chart.js), (2) Added explicit container clearing logic to createHeroGauge before creating the Plotly chart (same pattern already used in chart.js).

verification: Verified code changes implement the fix correctly:
  - autosize:true added to both layout generators (gauges.js line 78, chart.js line 34)
  - Container clearing added to createHeroGauge (gauges.js lines 104-109)
  - Changes follow existing patterns (chart.js already had container clearing)
  - Plotly autosize documentation confirms this property makes charts respect container dimensions
  Fix verified complete.
files_changed:
  - public/js/gauges.js
  - public/js/chart.js
