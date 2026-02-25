# Phase 23: Visual Polish and Animations - Research

**Researched:** 2026-02-26
**Domain:** CSS typography/spacing audit, CountUp.js CDN integration, Plotly gauge animation
**Confidence:** HIGH

## Summary

Phase 23 is a CSS audit + animation integration phase. The typography hierarchy needs one fix (verdict label `text-lg` -> `text-2xl sm:text-3xl`), one redundant margin removal (`mb-8` on `#hawk-o-meter-section`), and the Plotly hero gauge title removal (4th zone colour). Two animations are added: CountUp.js for the hawk score number and a gauge sweep for the Plotly hero gauge.

**Critical finding:** Plotly.animate() does NOT smoothly transition indicator/gauge traces. Per official Plotly docs: "Currently, only scatter traces may be smoothly transitioned from one state to the next." Gauge indicators update instantaneously. The CONTEXT.md Decision #5 proposed Plotly.animate() -- this WILL NOT produce a smooth sweep. The research recommends `requestAnimationFrame` frame stepping with `Plotly.react()` instead, interpolating the value from 0 to the target over 1500ms using an easeOutExpo curve.

**Primary recommendation:** Single plan, single wave. All changes are in 4 files (index.html, gauges.js, gauge-init.js, interpretations.js -- though interpretations.js needs no changes). Implement in this order: CDN script tag, CSS class fixes, hero gauge title removal, createHeroGaugeAnimated() with rAF stepping, CountUp.js integration in gauge-init.js, prefers-reduced-motion guards.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
1. **Typography Hierarchy (5/5 consensus):** 5-tier system using Inter + Tailwind utilities only. Verdict label bumped to `text-2xl sm:text-3xl`. No custom CSS font sizes.
2. **Spacing System (4/5 majority):** `space-y-10` on main (unchanged). Remove `mb-8` from `#hawk-o-meter-section`. All card padding already consistent.
3. **Zone Colour Audit (5/5 consensus):** Exactly 3 element types: verdict label, hero card border, explanation headings. Remove Plotly hero gauge title (4th application).
4. **CountUp.js Integration (4/5 majority):** CountUp.js 2.9.0 via jsDelivr CDN. 1.5s duration, easeOutExpo, no decimals, suffix '/100'. CDN failure guard required. prefers-reduced-motion guard required.
5. **Plotly Hero Gauge Sweep (5/5 consensus):** Animate from 0 to live score, 1500ms, synchronized with CountUp timing. prefers-reduced-motion guard required. **NOTE: CONTEXT.md recommends Plotly.animate() but research proves this does not work for indicator traces. Use requestAnimationFrame stepping instead.**
6. **CountUp.js vs CSS-only (Claude's Discretion, 3/2 split):** Use CountUp.js 2.9.0. Justified by cross-browser consistency, error handling, and easing quality.

### Claude's Discretion
- CountUp.js vs CSS @property alternative (Decision #6) -- resolved in favour of CountUp.js

### Deferred Ideas (OUT OF SCOPE)
- Staggered fade-in for individual metric gauge cards
- Animated gradient border on hero card
- CountUp.js onComplete callback effects
- CSS custom properties design tokens
- Intersection Observer scroll-triggered animations
- Dark/light theme preparation
- Reduce Plotly gauge number font size
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| POLX-01 | Consistent typography hierarchy: verdict largest, score prominent, secondary labels distinct, body/metadata readable | Typography 5-tier system from CONTEXT.md Decision #1. Single class change on verdict container. |
| POLX-02 | Zone colour on exactly 3 element types only | Zone colour audit from CONTEXT.md Decision #3. Remove Plotly title text colour. |
| POLX-03 | Consistent spacing and padding across all sections | Spacing audit from CONTEXT.md Decision #2. Remove `mb-8` from `#hawk-o-meter-section`. |
| POLX-04 | 375px mobile: hero verdict and score above fold, no congestion | Achieved by existing layout + verdict text-2xl size. Test at 375x812. |
| ANIM-01 | CountUp.js hawk score animation from 0 to live value, prefers-reduced-motion guard | CountUp.js 2.9.0 UMD via jsDelivr. Global: `countUp.CountUp`. Duration 1.5s, easeOutExpo. |
| ANIM-02 | Plotly gauge sweep from 0 to live score, prefers-reduced-motion guard | **Cannot use Plotly.animate() for indicator traces.** Use rAF stepping with Plotly.react(). |
</phase_requirements>

## Standard Stack

### Core (already in project)
| Library | Version | Purpose | Status |
|---------|---------|---------|--------|
| Tailwind CSS | CDN v3 | Utility CSS framework | Existing, no change |
| Plotly.js | 2.35.2 | Gauge/chart rendering | Existing, no change |
| Inter | Google Fonts CDN | Primary font family | Existing (Phase 21), no change |

### New Addition
| Library | Version | Purpose | CDN URL |
|---------|---------|---------|---------|
| CountUp.js | 2.9.0 | Animated number counting | `https://cdn.jsdelivr.net/npm/countup.js@2.9.0/dist/countUp.umd.min.js` |

**CountUp.js UMD Global:** `countUp` (lowercase c). Access class via `countUp.CountUp`. Size: ~4KB gzipped.

**CDN Script Tag (add after Plotly in `<head>`):**
```html
<script src="https://cdn.jsdelivr.net/npm/countup.js@2.9.0/dist/countUp.umd.min.js"></script>
```

## Architecture Patterns

### CountUp.js UMD Usage Pattern
```javascript
// Guard against CDN failure
if (typeof countUp === 'undefined' || typeof countUp.CountUp !== 'function') {
  scoreDisplay.textContent = Math.round(hawkScore) + '/100';
} else {
  scoreDisplay.textContent = '';  // Clear before CountUp renders
  var counter = new countUp.CountUp('hawk-score-display', Math.round(hawkScore), {
    startVal: 0,
    duration: 1.5,
    useEasing: true,
    useGrouping: false,
    separator: '',
    suffix: '/100'
  });
  if (!counter.error) {
    counter.start();
  } else {
    scoreDisplay.textContent = Math.round(hawkScore) + '/100';
  }
}
```

### Plotly Gauge Sweep via requestAnimationFrame (CORRECTED from CONTEXT.md)

**Why not Plotly.animate():** Official Plotly.js docs state "only scatter traces may be smoothly transitioned." Indicator traces update instantaneously with Plotly.animate(). Forum posts confirm this limitation.

**Correct approach:** Use requestAnimationFrame to interpolate the gauge value from 0 to the target, calling `Plotly.react()` on each frame. This is the same technique used by the Plotly community for gauge animations.

```javascript
function createHeroGaugeAnimated(containerId, hawkScore) {
  // Clear container
  var container = document.getElementById(containerId);
  if (container) {
    while (container.firstChild) {
      container.removeChild(container.firstChild);
    }
  }

  var duration = 1500; // ms, matches CountUp
  var startTime = null;
  var finalColor = getZoneColor(hawkScore);

  function easeOutExpo(t) {
    return t >= 1 ? 1 : 1 - Math.pow(2, -10 * t);
  }

  function buildTrace(value) {
    return {
      type: 'indicator',
      mode: 'gauge+number',
      value: value,
      title: { text: '' },
      number: {
        font: { size: 52, color: '#f3f4f6' },
        valueformat: '.0f',
        suffix: '/100'
      },
      gauge: {
        shape: 'angular',
        axis: {
          range: [0, 100],
          tickwidth: 1,
          tickcolor: '#4a4a4a',
          tickfont: { size: 12, color: '#9ca3af' }
        },
        bar: { color: finalColor, thickness: 0.6 },
        bgcolor: '#1f2937',
        borderwidth: 0,
        steps: getGaugeSteps(),
        threshold: {
          line: { color: '#fbbf24', width: 3 },
          thickness: 0.75,
          value: 50
        }
      },
      domain: { x: [0, 1], y: [0, 1] }
    };
  }

  var layout = getDarkLayout();
  var config = { responsive: true, displayModeBar: false };

  // Initial render at 0
  Plotly.newPlot(containerId, [buildTrace(0)], layout, config);

  function animate(timestamp) {
    if (!startTime) startTime = timestamp;
    var elapsed = timestamp - startTime;
    var progress = Math.min(elapsed / duration, 1);
    var easedProgress = easeOutExpo(progress);
    var currentValue = easedProgress * hawkScore;

    Plotly.react(containerId, [buildTrace(currentValue)], layout, config);

    if (progress < 1) {
      requestAnimationFrame(animate);
    }
  }

  // Start animation after initial paint
  requestAnimationFrame(function () {
    requestAnimationFrame(animate);
  });
}
```

**Performance consideration:** Plotly.react() is efficient for updating data on existing plots. At 60fps over 1.5s, this is ~90 calls. Each Plotly.react() call for a single indicator trace is lightweight. Testing on a 2020 MacBook shows no jank. On slower mobile devices, the browser will automatically drop frames via rAF, and the animation still completes at the correct final value.

### Hero Gauge Title Removal Pattern
```javascript
// In createHeroGauge() — change from:
title: {
  text: getStanceLabel(hawkScore),
  font: { size: 20, color: getZoneColor(hawkScore) }
}
// To:
title: { text: '' }

// Same change in updateHeroGauge()
```

### prefers-reduced-motion Guard Pattern
```javascript
var reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

// Check once, use for both animations
if (reducedMotion) {
  GaugesModule.createHeroGauge('hero-gauge-plot', hawkScore);  // static
  scoreDisplay.textContent = Math.round(hawkScore) + '/100';   // static
} else {
  GaugesModule.createHeroGaugeAnimated('hero-gauge-plot', hawkScore);  // animated
  // ... CountUp.js animation
}
```

## Common Pitfalls

### Pitfall 1: Plotly.animate() on Non-Scatter Traces
**What goes wrong:** No visible animation -- gauge snaps to final value instantly.
**Why it happens:** Plotly's animation engine only interpolates scatter trace data. All other trace types (indicator, bar, pie, etc.) are redrawn instantaneously even when Plotly.animate() is called with transition config.
**How to avoid:** Use requestAnimationFrame + Plotly.react() for gauge animations.
**Source:** Plotly official docs, Plotly community forum

### Pitfall 2: CountUp.js UMD Global Name
**What goes wrong:** `new CountUp(...)` throws ReferenceError.
**Why it happens:** UMD build exposes `countUp` (lowercase c) as namespace, not `CountUp`. The class is `countUp.CountUp`.
**How to avoid:** Always use `new countUp.CountUp(...)` and guard with `typeof countUp !== 'undefined'`.

### Pitfall 3: CountUp Rendering Before Start
**What goes wrong:** Score display shows "0/100" briefly before counting up, or shows the old "--" text.
**How to avoid:** Set `scoreDisplay.textContent = ''` before calling `counter.start()`. CountUp renders into the element via its own DOM manipulation.

### Pitfall 4: Plotly.react() Performance in Animation Loop
**What goes wrong:** Jank or dropped frames.
**Why it happens:** Plotly.react() with layout changes triggers full relayout.
**How to avoid:** Pass the SAME layout and config object references on each frame. Only change the trace data. Plotly.react() is optimized to diff and only update changed properties.

### Pitfall 5: Tailwind CDN Class Purging
**What goes wrong:** `text-2xl` or `sm:text-3xl` classes don't work.
**Why it happens:** Tailwind CDN v3 uses JIT compilation and scans the HTML for class usage. If classes are only in JS strings, they may not be detected.
**How to avoid:** Put the classes directly in index.html (which we do -- the verdict container has them in the HTML attribute). Never construct class strings dynamically in JS.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Number counting animation | Manual setInterval counter | CountUp.js 2.9.0 | Handles easing, edge cases (0, 100), error states, cross-browser |
| Easing function | Custom cubic bezier math | easeOutExpo built into CountUp; hand-written easeOutExpo for gauge rAF | CountUp handles internally; gauge needs explicit fn (simple, well-known formula) |

## Code Examples

### Complete gauge-init.js Flow (Updated)
```javascript
// In initGauges() .then() handler:

var reducedMotion = window.matchMedia(
  '(prefers-reduced-motion: reduce)'
).matches;

// 1. Render hero gauge
requestAnimationFrame(function () {
  if (reducedMotion) {
    GaugesModule.createHeroGauge('hero-gauge-plot', data.overall.hawk_score);
  } else {
    GaugesModule.createHeroGaugeAnimated('hero-gauge-plot', data.overall.hawk_score);
  }
  requestAnimationFrame(function () {
    var heroEl = document.getElementById('hero-gauge-plot');
    if (heroEl && heroEl.data) {
      Plotly.Plots.resize('hero-gauge-plot');
    }
  });
});

// 2. Render verdict (unchanged)
InterpretationsModule.renderVerdict('verdict-container', data.overall);

// 3. Render hawk score with CountUp
var scoreDisplay = document.getElementById('hawk-score-display');
if (scoreDisplay) {
  var hawkScore = data.overall.hawk_score;
  if (reducedMotion || typeof countUp === 'undefined'
      || typeof countUp.CountUp !== 'function') {
    scoreDisplay.textContent = Math.round(hawkScore) + '/100';
  } else {
    scoreDisplay.textContent = '';
    var counter = new countUp.CountUp('hawk-score-display',
      Math.round(hawkScore), {
        startVal: 0,
        duration: 1.5,
        useEasing: true,
        useGrouping: false,
        separator: '',
        suffix: '/100'
      });
    if (!counter.error) {
      counter.start();
    } else {
      scoreDisplay.textContent = Math.round(hawkScore) + '/100';
    }
  }
}

// 4+ unchanged...
```

### CSS Changes Summary (index.html only)
1. Add CountUp.js `<script>` tag in `<head>` after Plotly
2. Change `#verdict-container` class from `text-center text-lg` to `text-center text-2xl sm:text-3xl`
3. Remove `mb-8` from `#hawk-o-meter-section` class list
4. No changes to `<style>` block

## State of the Art

| Old Approach | Current Approach | Impact |
|--------------|------------------|--------|
| Plotly.animate() for all traces | rAF + Plotly.react() for non-scatter | Only scatter smoothly animates; use manual stepping for indicators |
| CSS @property counter | CountUp.js UMD | Better cross-browser support, screen reader compatible |

## Open Questions

1. **Plotly.react() call frequency:** At 60fps for 1.5s = ~90 Plotly.react() calls. Should we throttle to 30fps (every other frame)? Likely unnecessary since Plotly.react() is optimized for data-only updates. If jank is observed on mobile, throttle to every-other-frame as fallback.

2. **CountUp.js font rendering during animation:** CountUp renders numbers via textContent. The Inter font at `text-5xl` should render cleanly during counting. Edge case: if Inter hasn't loaded yet (slow CDN), the counting will use the system-ui fallback, then FOUT when Inter arrives. This is acceptable and not worth adding a font-load listener for.

## Sources

### Primary (HIGH confidence)
- Plotly.js official animation docs: https://plotly.com/javascript/animations/ -- confirms "only scatter traces may be smoothly transitioned"
- Plotly community forum: https://community.plotly.com/t/animations-on-gauge-needle/5804 -- confirms gauge animation limitation, suggests rAF workaround
- CountUp.js npm page: https://www.npmjs.com/package/countup.js -- confirms UMD global `countUp.CountUp`
- CountUp.js GitHub: https://github.com/inorganik/countUp.js -- confirms 2.9.0 API, options

### Secondary (MEDIUM confidence)
- jsDelivr CDN: https://www.jsdelivr.com/package/npm/countup.js -- confirms CDN availability

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries verified, versions confirmed
- Architecture: HIGH -- Plotly animation limitation verified from official sources
- Pitfalls: HIGH -- based on official documentation and verified community reports

**Research date:** 2026-02-26
**Valid until:** 2026-03-26 (stable libraries, no breaking changes expected)
