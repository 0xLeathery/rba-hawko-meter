# Phase 22: Verdict Explanation Component -- Implementation Context

**Generated:** 2026-02-26
**Method:** Synthetic discuss (5 agents: UX Designer, Engineer, Product Owner, QA/Edge Cases, Devil's Advocate)
**Phase Goal:** Users understand which indicators are pushing the hawk score up or down via a plain-English, ASIC-compliant explanation section

---

## Phase Boundary

**In scope (EXPL-01 through EXPL-04):**
- New `#verdict-explanation` section rendered below the hero, above the countdown
- Top 3 hawkish indicators listed with plain-English explanation sentences
- Top 2 dovish indicators listed with plain-English explanation sentences
- Neutral indicators omitted from both lists (EXPL-03)
- All copy uses ASIC-compliant hedged language (EXPL-04)
- Zone colours on section headings via `element.style.color` (warm for hawkish, cool for dovish)
- New `renderVerdictExplanation()` function in InterpretationsModule
- New `getExplanationSentence()` helper exposed on InterpretationsModule API
- Wired into gauge-init.js `initGauges()` success path

**Out of scope (deferred to Phase 23 or later):**
- Typography hierarchy audit (Phase 23: POLX-01)
- Spacing standardisation (Phase 23: POLX-03)
- CountUp.js score animation (Phase 23: ANIM-01)
- Plotly gauge sweep animation (Phase 23: ANIM-02)
- Any changes to hero card, metric gauge cards, calculator, or footer sections
- Indicator delta badges (future: DELT-01)

---

## Implementation Decisions

### 1. Indicator Ranking Method: Weighted Contribution
**Decision:** LOCKED (5/5 consensus)
**Position:** Rank indicators by their weighted contribution to the hawk score: `(value - 50) * weight`. Positive contributions are hawkish (pushing score up); negative contributions are dovish (pushing score down). Sort each group by absolute magnitude descending.

**Rationale:** All 5 agents agreed that weighted contribution directly answers the user's question: "Why is the score what it is?" An indicator at value=30 with weight=0.25 (contribution: -5.0) matters far more than an indicator at value=80 with weight=0.05 (contribution: +1.5). Using z-score or raw gauge value would misrepresent each indicator's actual influence on the final number.

**Formula:**
```javascript
// For each metric in data.gauges:
var contribution = (metricData.value - 50) * metricData.weight;
// contribution > 0  => hawkish (pushing score up)
// contribution < 0  => dovish (pulling score down)
// contribution ~= 0 => neutral (omitted per EXPL-03)
```

**Example with current data:**
| Indicator | Value | Weight | Contribution | Direction |
|-----------|-------|--------|-------------|-----------|
| wages | 84.8 | 0.15 | +5.22 | Hawkish |
| business_confidence | 72.5 | 0.05 | +1.13 | Hawkish |
| housing | 59.4 | 0.15 | +1.41 | Hawkish |
| spending | 60.4 | 0.10 | +1.04 | Hawkish |
| building_approvals | 57.9 | 0.05 | +0.40 | Neutral (below threshold) |
| employment | 33.7 | 0.15 | -2.45 | Dovish |
| inflation | 30.2 | 0.25 | -4.95 | Dovish |

Top 3 hawkish: wages (+5.22), housing (+1.41), business_confidence (+1.13)
Top 2 dovish: inflation (-4.95), employment (-2.45)

### 2. Minimum Contribution Threshold
**Decision:** Claude's Discretion (3/2 split)
**Position A (3 votes: UX, Engineer, PO):** Use 0.5 absolute contribution points as the minimum threshold. Indicators below this contribute negligible amounts to the score and would clutter the explanation.
**Position B (2 votes: QA, Devil's Advocate):** Use 0.25 or a dynamic threshold.

**Resolution:** Use 0.5 as the default threshold. If the score is non-neutral (outside 40-60) but no individual indicator passes the threshold, show the top 1 indicator anyway with softer language to avoid an empty explanation for a non-neutral score.

**Edge case guard:** With current weights (max 0.25), maximum single-indicator contribution is 12.5 points. A 0.5 threshold equals ~4% of max, which is a sensible noise floor.

### 3. Explanation Copy: Single Sentence Per Indicator
**Decision:** LOCKED (5/5 consensus)
**Position:** Each indicator gets a single sentence combining a factual reading with a hedged causal link to interest rates. Create `getExplanationSentence(metricId, metricData)` that returns one sentence.

**Rationale:** All 5 agents agreed that one sentence per indicator maximises scannability. The sentence follows the pattern: "[Factual observation], which [hedged causal link]." This mirrors the existing `generateMetricInterpretation()` + `getWhyItMatters()` patterns but combines them into a single thought.

**Hedging vocabulary (ASIC RG 244 compliant):**
- Primary: "tends to", "has historically been associated with"
- Secondary: "the data is consistent with", "is typically linked to"
- Forbidden: "will", "should", "must", "we recommend", "you should"

**Sentence templates by indicator:**

```
inflation (dovish, value < 50):
"Inflation at [raw]% per year is within the RBA's target range, which has historically been associated with less pressure to raise interest rates."

inflation (hawkish, value > 60):
"Inflation at [raw]% per year is above the RBA's target range, which tends to increase pressure on interest rates."

wages (hawkish, value > 60):
"Wages growing at [raw]% per year tends to push up costs and prices, which has historically been associated with upward pressure on rates."

wages (dovish, value < 40):
"Wage growth at [raw]% per year is subdued, which tends to reduce upward pressure on prices and interest rates."

employment (hawkish, value > 60):
"The job market is very tight, with strong demand for workers, which tends to push up wages and prices."

employment (dovish, value < 40):
"The job market is softening, which has historically been associated with less pressure on interest rates."

housing (hawkish, value > 60):
"Housing prices are rising at [raw]% per year, which has historically been associated with upward pressure on interest rates."

housing (dovish, value < 40):
"Housing price growth has slowed, which tends to reduce pressure on interest rates."

spending (hawkish, value > 60):
"Consumer spending is running above trend, which tends to add to price pressures."

spending (dovish, value < 40):
"Consumer spending is subdued, which has historically been associated with less inflationary pressure."

building_approvals (hawkish, value > 60):
"Building approvals are above average, which is consistent with strong demand in the construction sector."

building_approvals (dovish, value < 40):
"Building approvals are below average, which tends to signal a slowing construction sector."

business_confidence (hawkish, value > 60):
"Capacity utilisation at [raw]% is above the long-run average, which tends to signal inflationary pressure."

business_confidence (dovish, value < 40):
"Capacity utilisation is below average, which has historically been associated with reduced pressure on prices."
```

**Fallback (unknown metric):**
"This indicator is currently [above/below] its historical average."

### 4. Visual Layout: Two Grouped Lists with Zone-Coloured Headings
**Decision:** LOCKED (5/5 consensus)
**Position:** Render two grouped list sections: "Pushing the score up" (hawkish, warm zone colour heading) and "Pulling the score down" (dovish, cool zone colour heading). Each item is a single text line within a `<ul>` list.

**Rationale:** All 5 agents agreed that two distinct groups provide the clearest narrative structure. Cards (alternative B) would compete visually with the metric gauge grid below. Prose paragraphs (alternative C) bury the structure. The grouped list approach matches the user's mental model: "What's pushing rates up? What's pulling them down?"

**Zone colour application:**
- "Pushing the score up" heading: `element.style.color = GaugesModule.getZoneColor(75)` (warm zone = `#f87171`)
- "Pulling the score down" heading: `element.style.color = GaugesModule.getZoneColor(25)` (cool zone = `#60a5fa`)
- These are fixed colours, not dynamic per the current score. Per POLX-02, zone colour applies to "explanation section headings."
- Individual list items use standard `text-gray-300` for readability.

**Visual structure:**
```
#verdict-explanation (section, bg-finance-gray, rounded-xl, border)
  h3 "Pushing the score up" (warm zone colour via element.style)
  ul
    li [sentence for hawkish indicator 1]
    li [sentence for hawkish indicator 2]
    li [sentence for hawkish indicator 3]
  h3 "Pulling the score down" (cool zone colour via element.style)
  ul
    li [sentence for dovish indicator 1]
    li [sentence for dovish indicator 2]
```

### 5. DOM Placement: New Section Between Hero and Countdown
**Decision:** LOCKED (5/5 consensus)
**Position:** Create `#verdict-explanation` as a new `<section>` element inserted between `#hawk-o-meter-section` and `#countdown-section` in the DOM. Create it dynamically in JS (not static HTML) since it depends on data. Use `insertBefore` targeting the countdown section.

**Rationale:** All 5 agents agreed on the narrative flow: What (hero score) -> Why (explanation) -> When (countdown) -> Detail (metric gauges). The explanation section is the "why" companion to the hero's "what." Keeping it structurally separate from `#metric-gauges-grid` avoids Playwright nth-index selector issues (MEMORY.md pitfall #4).

**Implementation:**
```javascript
// In gauge-init.js, after rendering hero and before metric gauges:
var mainEl = document.querySelector('main');
var countdownSection = document.getElementById('countdown-section');
var explanationSection = document.createElement('section');
explanationSection.id = 'verdict-explanation';
explanationSection.setAttribute('aria-label', 'Score explanation');
// ... populate via InterpretationsModule.renderVerdictExplanation()
mainEl.insertBefore(explanationSection, countdownSection);
```

**Failure mode:** If data fetch fails, do NOT create the section. It only renders in the `.then()` success path.

### 6. Data Flow: Single Entry Point with Internal Helpers
**Decision:** LOCKED (5/5 consensus)
**Position:** Create `renderVerdictExplanation(containerId, data)` as the public entry point on InterpretationsModule. It receives the full status.json data object. Internally, it calls `rankIndicators(gaugesData)` to sort and filter, then `getExplanationSentence(metricId, metricData)` for each indicator's text. Both `renderVerdictExplanation` and `getExplanationSentence` are exposed on the module's public API for testability.

**Rationale:** All 5 agents agreed that encapsulating ranking logic inside InterpretationsModule keeps gauge-init.js clean (one function call). Exposing `getExplanationSentence` enables unit testing of copy without DOM rendering. This follows the same pattern as `getWhyItMatters()` and `getPlainVerdict()` which are already public.

**Function signatures:**
```javascript
// Public API additions to InterpretationsModule:
renderVerdictExplanation(containerId, data)
  // @param {string} containerId - Target section element ID
  // @param {Object} data - Full status.json data object
  // Creates the section content: headings + lists

getExplanationSentence(metricId, metricData)
  // @param {string} metricId - e.g. 'inflation'
  // @param {Object} metricData - Gauge data from status.json
  // @returns {string} Single hedged explanation sentence

// Internal (not exported):
rankIndicators(gaugesData)
  // @param {Object} gaugesData - data.gauges from status.json
  // @returns {{ hawkish: Array, dovish: Array }} Sorted, filtered arrays
```

**Wire-up in gauge-init.js:**
```javascript
// Inside .then() callback, after renderVerdict and before renderMetricGauges:
InterpretationsModule.renderVerdictExplanation('verdict-explanation', data);
```

---

## Edge Cases (QA Agent Contributions)

### All Indicators Neutral
If no indicator passes the 0.5 contribution threshold:
- Show a single message: "No indicators are currently applying significant pressure in either direction, which is consistent with the balanced reading."
- Do NOT show empty "Pushing the score up" / "Pulling the score down" sections.

### Fewer Than Expected Indicators
- If fewer than 3 hawkish indicators pass threshold: show however many exist (1 or 2).
- If fewer than 2 dovish indicators pass threshold: show however many exist (0 or 1).
- If 0 in a direction: omit that entire group (heading + list).

### Missing or Null Data
- If `data.gauges` is null/undefined/empty: do not render the section at all.
- If an individual indicator has `value: null`: skip it in ranking.
- If an indicator has `confidence: 'LOW'`: still include in ranking. The LOW badge is already shown on the metric card; the explanation sentence does not need to repeat it.

### Non-Neutral Score But No Qualifying Indicators
- If hawk_score is outside 40-60 but no indicator has contribution >= 0.5:
  - Show top 1 indicator from the dominant direction with qualifier: "The main contributor is [sentence], though no single indicator is applying strong pressure."

### Data Fetch Failure
- If DataModule.fetch fails: do not create `#verdict-explanation` section at all.
- The section only renders in the `.then()` success path.

### Indicator with `isDataSuspect()` True
- Skip the indicator in explanation ranking (same as it's handled in metric cards — shows "data is currently being updated").

---

## Specific Ideas

### Rendering Flow in gauge-init.js

After `DataModule.fetch('data/status.json')` resolves, insert between existing verdict render and metric gauges render:

```javascript
// Create explanation section dynamically
var mainEl = document.querySelector('main');
var countdownSection = document.getElementById('countdown-section');
if (mainEl && countdownSection) {
  var explanationSection = document.createElement('section');
  explanationSection.id = 'verdict-explanation';
  explanationSection.setAttribute('aria-label', 'Score explanation');
  explanationSection.className =
    'bg-finance-gray border border-finance-border'
    + ' rounded-xl px-6 py-5';
  mainEl.insertBefore(explanationSection, countdownSection);
  InterpretationsModule.renderVerdictExplanation(
    'verdict-explanation', data
  );
}
```

### InterpretationsModule additions

```javascript
// New internal helper (not exported)
function rankIndicators(gaugesData) {
  var hawkish = [];
  var dovish = [];
  var THRESHOLD = 0.5;

  Object.keys(gaugesData).forEach(function (metricId) {
    var m = gaugesData[metricId];
    if (m.value == null) return;
    if (isDataSuspect(metricId, m)) return;

    var contribution = (m.value - 50) * m.weight;

    if (contribution >= THRESHOLD) {
      hawkish.push({ id: metricId, data: m, contribution: contribution });
    } else if (contribution <= -THRESHOLD) {
      dovish.push({ id: metricId, data: m, contribution: contribution });
    }
  });

  // Sort hawkish descending, dovish by absolute descending
  hawkish.sort(function (a, b) { return b.contribution - a.contribution; });
  dovish.sort(function (a, b) { return a.contribution - b.contribution; });

  return {
    hawkish: hawkish.slice(0, 3),
    dovish: dovish.slice(0, 2)
  };
}

// New public function
function getExplanationSentence(metricId, metricData) {
  var raw = metricData.raw_value != null
    ? parseFloat(metricData.raw_value).toFixed(1)
    : null;
  var v = metricData.value;

  switch (metricId) {
    case 'inflation':
      if (v < 50) {
        return 'Inflation at ' + raw
          + '% per year is within the RBA\u2019s target range,'
          + ' which has historically been associated with less'
          + ' pressure to raise interest rates.';
      }
      return 'Inflation at ' + raw
        + '% per year is above the RBA\u2019s target range,'
        + ' which tends to increase pressure'
        + ' on interest rates.';
    // ... (similar patterns for all 7 indicators)
  }
}

// New public function
function renderVerdictExplanation(containerId, data) {
  var container = document.getElementById(containerId);
  if (!container || !data || !data.gauges) return;
  container.textContent = '';

  var ranked = rankIndicators(data.gauges);

  // Handle case: no qualifying indicators
  if (ranked.hawkish.length === 0 && ranked.dovish.length === 0) {
    var neutral = document.createElement('p');
    neutral.className = 'text-sm text-gray-400';
    neutral.textContent =
      'No indicators are currently applying significant'
      + ' pressure in either direction, which is consistent'
      + ' with the balanced reading.';
    container.appendChild(neutral);
    return;
  }

  // Hawkish section
  if (ranked.hawkish.length > 0) {
    var hawkH = document.createElement('h3');
    hawkH.className = 'text-base font-semibold mb-2';
    hawkH.style.color = GaugesModule.getZoneColor(75);
    hawkH.textContent = 'Pushing the score up';
    container.appendChild(hawkH);
    // ... render list items
  }

  // Dovish section
  if (ranked.dovish.length > 0) {
    var doveH = document.createElement('h3');
    doveH.className = 'text-base font-semibold mb-2 mt-4';
    doveH.style.color = GaugesModule.getZoneColor(25);
    doveH.textContent = 'Pulling the score down';
    container.appendChild(doveH);
    // ... render list items
  }
}
```

### Updated InterpretationsModule Return Object
Add to the existing return object:
```javascript
return {
  // ... existing exports ...
  renderVerdictExplanation: renderVerdictExplanation,
  getExplanationSentence: getExplanationSentence
};
```

### Playwright Test Compatibility
- `#verdict-explanation` is a new section, not modifying any existing element
- `#metric-gauges-grid` remains structurally separate (pitfall #4)
- `#verdict-container` stays inside `#hero-card` (unchanged)
- Run all 28 Playwright tests after implementation

### CSS Notes
- No new CSS keyframes or animations needed for Phase 22
- Section uses existing Tailwind classes: `bg-finance-gray`, `border`, `border-finance-border`, `rounded-xl`, `px-6`, `py-5`
- List items: `text-sm text-gray-300` for readability against dark background
- List bullet styling: `list-disc list-inside` Tailwind classes on `<ul>`

---

## Deferred Ideas

| Idea | Source Agent | Reason Deferred |
|------|-------------|-----------------|
| Animated entry for explanation section (fade-in on scroll) | UX Designer | Visual polish belongs in Phase 23 (POLX); keep Phase 22 focused on content |
| Collapsible explanation section (details/summary) | Devil's Advocate | Adds friction to the "why" answer; hero + explanation should be immediately visible |
| Indicator trend arrows in explanation list | Product Owner | Requires `previous_value` in status.json (DELT-01, future requirement) |
| Explanation as tooltip hover on hero score | UX Designer | Not accessible on mobile (no hover), and hides critical content behind interaction |
| Dynamic threshold based on score distance from 50 | Devil's Advocate | Over-engineering for 7 indicators; fixed 0.5 threshold works for all current data |
| Separate explanation module (verdict-explanation.js) | Engineer | Over-engineering for 2 functions; InterpretationsModule is the natural home |
| Z-score display in explanation sentences | QA/Edge Cases | Technical jargon violates plain English principle; z-score drives the ranking internally only |

---

*Generated by synthetic multi-agent discuss. 5 agents, 6 gray areas, 6 decisions (5 locked, 1 discretion, 7 deferred).*
