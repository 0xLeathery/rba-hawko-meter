# Phase 4: Hawk-O-Meter Gauges - Research

**Researched:** 2026-02-04
**Domain:** Plotly.js gauge visualization, vanilla JavaScript DOM manipulation, data-driven text generation
**Confidence:** HIGH

## Summary

Phase 4 creates visual gauge displays using Plotly.js indicator traces. The research confirms that Plotly.js provides robust support for both angular (semicircle speedometer) and bullet (horizontal bar) gauges with extensive customization for color zones, thresholds, and responsive layouts. The library is framework-agnostic and works seamlessly with vanilla JavaScript via CDN.

Key findings show that Plotly.js indicator traces support color steps for zone visualization, single threshold markers, and complete styling control. The library handles responsiveness through a simple config flag, making it suitable for mobile-first dashboards. For compact individual metric gauges, bullet charts provide a space-efficient alternative to angular gauges.

**Primary recommendation:** Use Plotly.js v3.3+ with the basic bundle (277kB minified + gzip) loaded via CDN. Implement the hero Hawk Score as an angular gauge with color steps mapping to the 5 Z-score zones, and render individual metric gauges as bullet charts for space efficiency. Generate interpretation text dynamically using template literals with actual data values from status.json.

## Standard Stack

The established libraries/tools for gauge visualization with vanilla JavaScript:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Plotly.js | v3.3+ | Interactive gauge visualization | Industry standard for scientific/financial dashboards, extensive customization, no framework dependency |
| Plotly.js Basic Bundle | 277kB gzip | Reduced bundle size | Includes indicator traces without 3D/geographic bloat |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Intl.NumberFormat | Native API | Locale-aware number formatting | Formatting percentages for ASX Futures probabilities |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Plotly.js | Chart.js | Chart.js lacks native gauge support, would require custom pie chart hacks |
| Plotly.js | D3.js | D3 requires significantly more code for same result, steeper learning curve |
| Full Bundle (3MB) | Basic Bundle (277kB) | Basic bundle sufficient for indicator traces, 90% size reduction |

**Installation:**
```html
<!-- CDN approach (recommended for static sites) -->
<head>
  <script src="https://cdn.plot.ly/plotly-3.3.1.min.js" charset="utf-8"></script>
</head>

<!-- Or use basic bundle for smaller size -->
<head>
  <script src="https://cdn.plot.ly/plotly-basic-3.3.1.min.js" charset="utf-8"></script>
</head>
```

**Critical:** Avoid `plotly-latest.js` URLs — these are frozen at v1.58.5 (July 2021) and no longer maintained. Always specify explicit version numbers.

## Architecture Patterns

### Recommended Project Structure
```
src/
├── js/
│   ├── gauges.js          # Plotly gauge initialization and update logic
│   ├── interpretations.js # Dynamic text generation from data
│   └── dashboard.js       # Main orchestration, fetch status.json
├── css/
│   └── dashboard.css      # Layout, responsive grid, Tailwind utilities
└── index.html             # Static HTML with gauge containers
```

### Pattern 1: Gauge Initialization
**What:** Create gauge configurations as objects, initialize with Plotly.newPlot()
**When to use:** On page load, one-time setup for each gauge container

**Example:**
```javascript
// Source: https://plotly.com/javascript/gauge-charts/
function createHawkScoreGauge(value, targetDiv) {
  const data = [{
    type: "indicator",
    mode: "gauge+number",
    value: value,
    title: { text: "Hawk Score", font: { size: 24 } },
    gauge: {
      axis: { range: [0, 100], tickwidth: 1, tickcolor: "darkgray" },
      bar: { color: "darkblue", thickness: 0.7 },
      bgcolor: "white",
      borderwidth: 2,
      bordercolor: "gray",
      steps: [
        { range: [0, 20], color: "#3b82f6" },    // Cold (STRONGLY DOVISH)
        { range: [20, 40], color: "#60a5fa" },   // Cool (DOVISH)
        { range: [40, 60], color: "#d1d5db" },   // Neutral
        { range: [60, 80], color: "#fb923c" },   // Warm (HAWKISH)
        { range: [80, 100], color: "#dc2626" }   // Hot (STRONGLY HAWKISH)
      ],
      threshold: {
        line: { color: "red", width: 4 },
        thickness: 0.75,
        value: 80  // Example threshold at 80 (HAWKISH boundary)
      }
    }
  }];

  const layout = {
    width: 500,
    height: 400,
    margin: { t: 50, r: 25, l: 25, b: 25 }
  };

  const config = { responsive: true };

  Plotly.newPlot(targetDiv, data, layout, config);
}
```

### Pattern 2: Compact Bullet Gauges for Individual Metrics
**What:** Use bullet chart style for space-efficient horizontal gauge display
**When to use:** Individual metric gauges (Housing, Jobs, etc.) where vertical space is limited

**Example:**
```javascript
// Source: https://plotly.com/javascript/bullet-charts/
function createMetricBulletGauge(value, label, targetDiv) {
  const data = [{
    type: "indicator",
    mode: "number+gauge+delta",
    value: value,
    delta: { reference: 50 },  // Reference to neutral zone
    gauge: {
      shape: "bullet",
      axis: { range: [0, 100] },
      bar: { color: "darkblue", thickness: 0.5 },
      steps: [
        { range: [0, 20], color: "#3b82f6" },
        { range: [20, 40], color: "#60a5fa" },
        { range: [40, 60], color: "#d1d5db" },
        { range: [60, 80], color: "#fb923c" },
        { range: [80, 100], color: "#dc2626" }
      ],
      threshold: {
        line: { color: "black", width: 2 },
        thickness: 0.85,
        value: 50
      }
    },
    domain: { x: [0, 1], y: [0, 1] },
    title: { text: label }
  }];

  const layout = {
    width: 350,
    height: 100,
    margin: { t: 20, r: 10, l: 100, b: 20 }
  };

  const config = { responsive: true };

  Plotly.newPlot(targetDiv, data, layout, config);
}
```

### Pattern 3: Fetch and Update Dashboard
**What:** Load status.json and update all gauges + interpretation text
**When to use:** On page load and potentially periodic refresh

**Example:**
```javascript
// Source: https://gomakethings.com/how-to-use-the-fetch-api-with-vanilla-js/
async function loadDashboard() {
  try {
    const response = await fetch('data/status.json');

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();

    // Update hero gauge
    updateGauge('hawk-score-gauge', data.overall.hawk_score);

    // Update individual gauges
    data.metrics.forEach(metric => {
      updateGauge(`gauge-${metric.name}`, metric.gauge_value);
    });

    // Update interpretation text
    updateInterpretation(data.overall.verdict, data.overall.interpretation);

    // Update ASX Futures table
    updateFuturesTable(data.asx_futures);

  } catch (error) {
    console.error('Dashboard load failed:', error);
    showErrorState();
  }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', loadDashboard);
```

### Pattern 4: Dynamic Text Generation from Data
**What:** Generate plain-English interpretations using template literals with actual values
**When to use:** Displaying data-driven insights, not static templates

**Example:**
```javascript
// Source: https://gomakethings.com/html-templates-with-vanilla-javascript/
function generateInterpretation(metricsData) {
  const housing = metricsData.find(m => m.name === 'housing');
  const wages = metricsData.find(m => m.name === 'wages');
  const inflation = metricsData.find(m => m.name === 'inflation');

  // Use actual data values in the text
  const housingYoY = housing.raw_value.yoy_change;
  const wagesYoY = wages.raw_value.yoy_change;
  const cpiYoY = inflation.raw_value.yoy_change;

  // Template literal with actual numbers
  return `Housing prices up ${housingYoY.toFixed(1)}% YoY while wages grew only ${wagesYoY.toFixed(1)}%,
          with CPI at ${cpiYoY.toFixed(1)}%. This gap indicates cost-of-living pressure.`;
}

function updateInterpretation(verdict, interpretationText) {
  const container = document.getElementById('interpretation');

  // Sanitize verdict and use textContent for security
  const verdictSpan = document.createElement('span');
  verdictSpan.className = 'font-bold text-lg';
  verdictSpan.textContent = verdict;

  const textNode = document.createTextNode(` — ${interpretationText}`);

  // Safe: clearing our own generated content, not user input
  container.textContent = '';
  container.appendChild(verdictSpan);
  container.appendChild(textNode);
}
```

### Pattern 5: Responsive Grid Layout
**What:** CSS Grid with responsive breakpoints for gauge layout
**When to use:** Arranging 6 individual gauges on different screen sizes

**Example:**
```css
/* Mobile-first approach */
.gauges-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
  padding: 1rem;
}

/* Tablet: 2 columns */
@media (min-width: 768px) {
  .gauges-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* Desktop: 3 columns */
@media (min-width: 1024px) {
  .gauges-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

/* Hero gauge gets full width on all screens */
.hero-gauge {
  grid-column: 1 / -1;
  max-width: 600px;
  margin: 0 auto;
}
```

### Anti-Patterns to Avoid

- **Creating new plots on update:** Use `Plotly.update()` or `Plotly.react()` instead of `Plotly.newPlot()` for value changes — recreating is much slower
- **Multiple threshold lines:** Plotly only supports one threshold value per gauge (it's not an array) — use steps for multiple color zones
- **Mixing warm/cool colors:** For colorblind accessibility, don't use both warm red and warm green — use cool green (#3b82f6) with warm red (#dc2626)
- **Global state mutations:** Pass data explicitly rather than mutating global objects — makes testing and debugging easier
- **Using textContent with HTML:** Use textContent only for plain text; never set HTML content via textContent as it won't render. For trusted HTML use safe DOM methods

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Gauge visualization | Custom SVG/Canvas gauge | Plotly.js indicator trace | Handles responsive sizing, colors, animations, accessibility out of the box |
| Number formatting | String concatenation + rounding | Intl.NumberFormat | Handles locales, currency, percentages, edge cases (NaN, Infinity) |
| Responsive chart sizing | Manual resize event listeners | Plotly config: {responsive: true} | Automatically handles window resize without custom code |
| Color interpolation for zones | Manual RGB calculations | Plotly steps array | Declarative color zones with automatic transitions |
| Data fetching with error handling | XMLHttpRequest or manual fetch | Async/await fetch pattern | Cleaner error handling, no callback hell, works with try/catch |

**Key insight:** Plotly.js has already solved the hard problems of gauge rendering (responsive sizing, color zones, thresholds, touch interactions). Don't rebuild SVG gauge logic — configure Plotly's extensive API instead.

## Common Pitfalls

### Pitfall 1: Using "plotly-latest.js" CDN URL
**What goes wrong:** Application uses outdated version (v1.58.5 from July 2021), missing 5 years of features and bug fixes
**Why it happens:** The URL looks convenient, documentation examples from 2021 use it
**How to avoid:** Always use explicit version numbers: `plotly-3.3.1.min.js`
**Warning signs:** Gauge features mentioned in docs don't work, console shows Plotly version < 2.0

### Pitfall 2: Loading Full Bundle (3MB) Instead of Basic Bundle
**What goes wrong:** Dashboard takes 2-3 seconds to load on mobile/3G connections, poor lighthouse scores
**Why it happens:** Default documentation examples use full bundle
**How to avoid:** Use basic bundle (`plotly-basic-3.3.1.min.js`) for projects only using indicator/scatter/bar charts — 90% smaller (277kB)
**Warning signs:** Network tab shows 3MB+ plotly.js download, mobile users complain about slow loading

### Pitfall 3: Confusing Threshold (Single Line) with Steps (Color Zones)
**What goes wrong:** Attempting to create multiple "threshold" markers fails silently, only last one renders
**Why it happens:** API naming is misleading — "threshold" sounds like it should be plural
**How to avoid:** Use `steps` array for color zones, use single `threshold` only for reference line/needle
**Warning signs:** Only one threshold line appears despite configuring multiple values

### Pitfall 4: Zero-Value Threshold Bug
**What goes wrong:** Threshold line doesn't render when value is exactly 0
**Why it happens:** Known bug in Plotly.js (Issue #5428)
**How to avoid:** If threshold must be at 0, use a very small value like 0.001 instead, or use a step boundary at 0
**Warning signs:** Threshold line visible at all values except 0

### Pitfall 5: Creating New Plots on Data Updates
**What goes wrong:** Gauge flickers, re-renders slowly, loses animation continuity
**Why it happens:** Calling `Plotly.newPlot()` recreates entire chart from scratch
**How to avoid:** Use `Plotly.update()` or `Plotly.react()` for value changes only
**Warning signs:** Gauge "blinks" when updating, CPU spikes on data refresh

### Pitfall 6: Red-Green Color Zones Without Colorblind Consideration
**What goes wrong:** 8% of male users (1 in 12) can't distinguish red/green zones, gauge is unreadable
**Why it happens:** Traffic light metaphor seems natural, designer has normal color vision
**How to avoid:** Use blue (#3b82f6) instead of green for low/dovish zones, keep red (#dc2626) for high/hawkish. Add labels to zones, not just colors
**Warning signs:** User feedback mentions "zones look the same", accessibility audit failures

### Pitfall 7: Hardcoded Interpretation Text Templates
**What goes wrong:** Interpretation says "Housing up significantly" when it's actually flat or down
**Why it happens:** Easier to write static templates than generate text from data
**How to avoid:** Always use template literals with actual `${data.value}` interpolation
**Warning signs:** Interpretation text doesn't match gauge values, contradicts visible data

### Pitfall 8: No Error State for Missing/Stale Data
**What goes wrong:** Dashboard shows stale data without warning user, misleading decisions
**Why it happens:** Forgot to check status.json metadata for staleness flags
**How to avoid:** Check `data.timestamp` age and `data.staleness_warning` flags, show visual indicator if data > 7 days old
**Warning signs:** Users make decisions on week-old data, no visible freshness indicator

### Pitfall 9: Multiple Charts Causing Performance Issues
**What goes wrong:** Page with 7 gauges (1 hero + 6 individual) renders slowly, CPU usage high
**Why it happens:** Each Plotly chart is independent, initialization compounds
**How to avoid:** Use bullet gauges for individual metrics (more compact), stagger initialization with `requestAnimationFrame()`, consider lazy loading off-screen gauges
**Warning signs:** Slow page load, mobile devices lag when scrolling

### Pitfall 10: Responsive Config Not Enabling Properly
**What goes wrong:** Gauges overflow container on mobile, don't resize with window
**Why it happens:** `responsive: true` flag not passed to config object
**How to avoid:** Always pass config as third argument: `Plotly.newPlot(div, data, layout, {responsive: true})`
**Warning signs:** Gauges fixed-width on mobile, horizontal scrolling required

## Code Examples

Verified patterns from official sources:

### ASX Futures Probability Table
```javascript
// Source: Vanilla JavaScript table creation pattern
function updateFuturesTable(futuresData) {
  const tableBody = document.getElementById('futures-tbody');

  // Clear previous rows (safe: clearing our own generated table rows)
  tableBody.textContent = '';

  // futuresData = { cut: 0.15, hold: 0.70, hike: 0.15 }
  const outcomes = [
    { label: 'Rate Cut', probability: futuresData.cut },
    { label: 'Hold', probability: futuresData.hold },
    { label: 'Rate Hike', probability: futuresData.hike }
  ];

  // Format percentages using Intl.NumberFormat
  const percentFormatter = new Intl.NumberFormat('en-AU', {
    style: 'percent',
    minimumFractionDigits: 1,
    maximumFractionDigits: 1
  });

  outcomes.forEach(outcome => {
    const row = document.createElement('tr');

    const labelCell = document.createElement('td');
    labelCell.textContent = outcome.label;
    labelCell.className = 'px-4 py-2 font-medium';

    const probCell = document.createElement('td');
    probCell.textContent = percentFormatter.format(outcome.probability);
    probCell.className = 'px-4 py-2 text-right';

    row.appendChild(labelCell);
    row.appendChild(probCell);
    tableBody.appendChild(row);
  });
}
```

### Complete Dashboard Initialization
```javascript
// Source: https://plotly.com/javascript/getting-started/ + vanilla JS patterns
async function initializeDashboard() {
  try {
    // Fetch status.json
    const response = await fetch('data/status.json');
    if (!response.ok) throw new Error(`HTTP ${response.status}`);

    const statusData = await response.json();

    // Check data freshness
    const dataAge = Date.now() - new Date(statusData.metadata.timestamp).getTime();
    const daysSinceUpdate = dataAge / (1000 * 60 * 60 * 24);

    if (daysSinceUpdate > 7) {
      showStalenessWarning(daysSinceUpdate);
    }

    // Initialize hero gauge
    createHawkScoreGauge(
      statusData.overall.hawk_score,
      'hawk-score-gauge'
    );

    // Initialize individual metric gauges
    const metricsToDisplay = [
      'housing', 'jobs', 'spending',
      'capacity', 'inflation', 'wages'
    ];

    metricsToDisplay.forEach(metricName => {
      const metricData = statusData.metrics.find(m => m.id === metricName);
      createMetricBulletGauge(
        metricData.gauge_value,
        metricData.label,
        `gauge-${metricName}`
      );
    });

    // Generate and display interpretation
    const interpretation = generateInterpretation(statusData.metrics);
    updateInterpretation(statusData.overall.verdict, interpretation);

    // Update ASX Futures table
    updateFuturesTable(statusData.asx_futures);

  } catch (error) {
    console.error('Dashboard initialization failed:', error);
    showErrorMessage('Unable to load economic data. Please try again later.');
  }
}

function showStalenessWarning(days) {
  const warning = document.getElementById('staleness-warning');
  warning.textContent = `Data is ${Math.floor(days)} days old. Next update expected soon.`;
  warning.classList.remove('hidden');
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', initializeDashboard);
```

### Gauge Update (Not Recreation)
```javascript
// Source: Plotly.js update methods
function updateGaugeValue(divId, newValue) {
  // Use Plotly.update() for efficient value changes
  // Don't use Plotly.newPlot() — that recreates the entire chart
  Plotly.update(divId, {
    value: [newValue]
  });
}

// Or use Plotly.react() for more complex updates
function updateGaugeWithMetadata(divId, newValue, threshold) {
  const update = {
    value: [newValue],
    'gauge.threshold.value': [threshold]
  };

  Plotly.react(divId, update);
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Custom SVG gauges | Plotly.js indicator traces | 2015+ | Reduced code complexity, better mobile support, built-in responsiveness |
| Plotly v1 (via "latest" CDN) | Plotly v3.3+ (explicit version) | July 2021 | 5 years of bug fixes, performance improvements, new features |
| Full bundle (3MB) | Partial bundles (277kB basic) | 2019+ | 90% size reduction for projects using only core chart types |
| Template-based text | Data-driven text with template literals | ES6 (2015) | Dynamic, accurate interpretations instead of generic phrases |
| Manual resize handlers | responsive: true config | Plotly 1.x+ | No custom resize code needed, automatic chart reflow |
| String concatenation for formatting | Intl.NumberFormat | ES6+ (2015) | Locale-aware, handles edge cases, no external library needed |
| XMLHttpRequest | Async/await fetch | ES2017 (2017) | Cleaner error handling, no callback nesting |

**Deprecated/outdated:**
- **plotly-latest.js CDN URL**: Frozen at v1.58.5 (July 2021), will never update. Use explicit version numbers.
- **Creating new plots on update**: Use `Plotly.update()` or `Plotly.react()` instead for better performance.
- **Plotly.Plots.resize()**: Superseded by `responsive: true` config option.

## Open Questions

Things that couldn't be fully resolved:

1. **Optimal gauge update frequency**
   - What we know: status.json updates weekly via GitHub Action
   - What's unclear: Whether to implement client-side polling for updates or rely on page refresh
   - Recommendation: Start with page-refresh only (simplest). Add polling later if users request it. Most mortgage decisions don't require real-time updates.

2. **Gauge animation duration**
   - What we know: Plotly supports animation, can be configured
   - What's unclear: Optimal transition speed for gauge needle movement (too fast = jarring, too slow = sluggish)
   - Recommendation: Use Plotly defaults initially (they're well-tuned for gauge transitions), adjust based on user feedback.

3. **Color zone boundary precision**
   - What we know: Phase 3 defines 5 zones (0-20, 20-40, 40-60, 60-80, 80-100)
   - What's unclear: Whether to show exact Z-score boundaries on axis labels or just the 0-100 scale
   - Recommendation: Show 0-100 scale for simplicity. Z-scores are internal calculation, not user-facing concept.

4. **Mobile gesture conflicts**
   - What we know: Plotly supports touch interactions (pan, zoom)
   - What's unclear: Whether default Plotly touch gestures interfere with page scrolling on mobile
   - Recommendation: Test on mobile devices. If conflicts occur, disable Plotly interactions via config: `{staticPlot: true}` since gauges are view-only, not interactive charts.

## Sources

### Primary (HIGH confidence)
- [Plotly.js Gauge Charts Documentation](https://plotly.com/javascript/gauge-charts/) - Official gauge chart guide
- [Plotly.js Indicator Reference](https://plotly.com/javascript/reference/indicator/) - Complete API reference for indicator traces
- [Plotly.js Bullet Charts](https://plotly.com/javascript/bullet-charts/) - Compact horizontal gauge documentation
- [Plotly.js Getting Started](https://plotly.com/javascript/getting-started/) - Installation and initialization patterns
- [Plotly.js Responsive Layouts](https://plotly.com/javascript/responsive-fluid-layout/) - Responsive configuration

### Secondary (MEDIUM confidence)
- [GitHub plotly.js Issue #5428](https://github.com/plotly/plotly.js/issues/5428) - Zero-value threshold bug documentation
- [GitHub plotly.js Issue #6270](https://github.com/plotly/plotly.js/issues/6270) - Multiple threshold limitation
- [Plotly.js Performance Issues (GitHub)](https://github.com/plotly/plotly.js/issues/3416) - Multiple charts performance
- [Beautiful, Accessible Traffic Light Colors](https://uxdesign.cc/beautiful-accessible-traffic-light-colors-b2b14a102a38) - Colorblind-friendly color design
- [Go Make Things: Fetch API](https://gomakethings.com/how-to-use-the-fetch-api-with-vanilla-js/) - Vanilla JS fetch patterns
- [Go Make Things: HTML Templates](https://gomakethings.com/html-templates-with-vanilla-javascript/) - Template literal patterns

### Tertiary (LOW confidence)
- [Plotly.js Bundle Size Optimization](https://community.plotly.com/t/how-can-i-reduce-bundle-size-of-plotly-js-in-react-app/89910) - Community discussion on bundle sizes
- [Intl.NumberFormat Best Practices](https://www.omarileon.me/blog/javascript-format-percentage) - JavaScript percentage formatting

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Plotly.js is well-documented, actively maintained, official docs confirm gauge capabilities
- Architecture: HIGH - Patterns verified from official documentation and modern vanilla JS best practices
- Pitfalls: MEDIUM-HIGH - Most pitfalls documented in official issue tracker, some from community reports

**Research date:** 2026-02-04
**Valid until:** 2026-03-04 (30 days - Plotly.js is stable, gauge API unlikely to change)
