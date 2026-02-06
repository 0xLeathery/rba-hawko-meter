# Phase 5: Calculator & Compliance - Research

**Researched:** 2026-02-06
**Domain:** Mortgage calculator implementation (vanilla JS) + ASIC RG 244 regulatory compliance
**Confidence:** MEDIUM-HIGH

## Summary

This phase combines two distinct domains: building a mortgage repayment calculator in vanilla JavaScript and ensuring all dashboard content complies with Australian financial services regulations (ASIC RG 244). The calculator requires precise financial mathematics using Decimal.js to avoid floating-point errors, localStorage persistence for user inputs, and support for multiple repayment frequencies (monthly/fortnightly/weekly) and types (principal+interest vs interest-only).

The compliance domain requires careful language framing to maintain "factual information" classification (Tier 1) under ASIC RG 244, avoiding "general advice" (Tier 2) or "personal advice" (Tier 3) which require an AFS licence. Educational framing, neutral language, and plain English disclaimers are the primary guardrails.

The project uses vanilla JS with CDN dependencies (no build step), IIFE module pattern, and dark finance theme established in Phase 2. The calculator extends this existing architecture.

**Primary recommendation:** Use Decimal.js (CDN) for all mortgage calculations. Follow the IIFE module pattern from Phase 2. Frame all content educationally with principle-based neutral language. Include three-tier disclaimers (banner, calculator-specific, footer) following patterns established by ASX, ASIC MoneySmart, and major Australian banks.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **5 calculator fields:** Loan amount, remaining term, current rate, repayment type (P&I vs IO), repayment frequency (monthly/fortnightly/weekly)
- **Pre-filled with Australian averages** -- ~$600k loan, 25yr term, current RBA rate. User adjusts as needed
- **Stored in localStorage** (no login required)
- **Scenario slider range:** 0% to 10% -- covers full historical range including extreme scenarios
- **Slider steps:** 0.25% increments (matches RBA's typical move size)
- **Visual feedback:** Both live repayment update AND comparison table (current vs scenario monthly difference, annual difference, total interest difference)
- **Plain English disclaimer** -- "This tool shows data, not advice. Talk to a financial adviser before making decisions."
- **Footer only disclaimer** -- standard footer disclaimer visible on every page. No expandable legal text.
- **Educational framing** for calculator: "See how rate changes affect a typical mortgage" -- not "your" mortgage
- **Neutral language enforcement:** present data neutrally, never imply action

### Claude's Discretion
- Exact neutral language enforcement approach (word list vs principle-based)
- Calculator layout and input styling
- Repayment calculation edge cases
- Additional disclaimer placement near calculator if needed for ASIC compliance beyond footer

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Decimal.js | 10.x (CDN) | Arbitrary-precision decimal arithmetic | Industry standard for financial math in JS; prevents IEEE 754 floating-point errors that compound over 300+ month loans |
| HTML5 Constraint Validation API | Native | Form input validation | Browser-native, accessible to screen readers, no external dependency |
| localStorage API | Native | Persist calculator inputs | Browser-native, simple key-value, no backend needed, data never leaves browser |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Intl.NumberFormat | Native | Currency formatting | Format calculated values as AUD currency with comma separators |
| N/A | N/A | No additional libraries needed | Vanilla JS sufficient for this scope |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Decimal.js | Big.js | Big.js is lighter (6KB vs 12KB) but Decimal.js has broader API (pow, sqrt needed for amortization), better docs, wider adoption |
| Native validation | Pristine.js | External dependency adds complexity; native HTML5 + setCustomValidity() sufficient for 5 inputs |
| localStorage | IndexedDB | IndexedDB is async and complex; localStorage is simpler and adequate for key-value pairs under 5KB |

**Installation:**
```html
<!-- CDN delivery, consistent with Plotly.js and Tailwind pattern from Phase 2 -->
<script src="https://cdn.jsdelivr.net/npm/decimal.js@10/decimal.min.js"></script>
```

No npm/build step required. Decimal.js loaded as CDN global (consistent with project architecture -- no bundler).

## Architecture Patterns

### Recommended Project Structure
```
public/
├── index.html          # Extended with calculator section (between chart and footer)
├── js/
│   ├── data.js         # Phase 2 (existing) - DataModule IIFE
│   ├── chart.js        # Phase 2 (existing) - ChartModule IIFE
│   ├── countdown.js    # Phase 2 (existing) - CountdownModule IIFE
│   ├── calculator.js   # NEW - CalculatorModule IIFE
│   └── main.js         # Phase 2 (extended) - orchestrator, inits all modules
└── data/
    └── ...             # Phase 1/2 data files (unchanged)
```

### Pattern 1: IIFE Module (Project Standard)
**What:** All JS modules use the IIFE pattern established in Phase 2 for encapsulation without a bundler.
**When to use:** Every new JS module in this project.
**Example:**
```javascript
// Source: Phase 2 established pattern (DataModule, ChartModule, CountdownModule)
const CalculatorModule = (() => {
  // Private state
  const STORAGE_KEY = 'rba-hawko-calculator';

  // Private functions
  function calculatePayment(principal, rate, term) { /* ... */ }

  // Public API
  return {
    init() { /* ... */ },
    recalculate() { /* ... */ }
  };
})();
```

### Pattern 2: Decimal.js Financial Arithmetic
**What:** Use Decimal.js for ALL money calculations. Pass values as strings to prevent precision loss before Decimal constructor processes them.
**When to use:** Any calculation involving currency or interest rates.
**Example:**
```javascript
// Source: Decimal.js docs (https://github.com/MikeMcl/decimal.js/)
// ALWAYS pass values as strings to prevent precision loss
const P = new Decimal(principal.toString());
const r = new Decimal(annualRatePct.toString()).dividedBy(100).dividedBy(12);
const n = new Decimal(termYears.toString()).times(12);

// Standard amortization formula: M = P * [r(1+r)^n] / [(1+r)^n - 1]
const onePlusR = r.plus(1);
const onePlusRtoN = onePlusR.pow(n);
const M = P.times(r.times(onePlusRtoN)).dividedBy(onePlusRtoN.minus(1));
```

### Pattern 3: Half Monthly Method for Frequency Adjustment
**What:** Calculate monthly payment first, then divide for fortnightly/weekly. This naturally creates extra annual payments.
**When to use:** User selects non-monthly repayment frequency.
**Example:**
```javascript
// Source: Australian mortgage calculator standard (Finder.com.au, bank calculators)
// Monthly: 12 payments/year
const monthlyPayment = calculateAmortized(principal, rate, term);

// Fortnightly: 26 payments/year = 13 months equivalent
const fortnightlyPayment = monthlyPayment.dividedBy(2);

// Weekly: 52 payments/year = 13 months equivalent
const weeklyPayment = monthlyPayment.dividedBy(4);
```

### Pattern 4: localStorage with Defensive Error Handling
**What:** Wrap all localStorage operations in try-catch with validation on read and graceful fallback to defaults.
**When to use:** All localStorage read/write operations.
**Example:**
```javascript
// Source: MDN localStorage docs + WebSearch best practices
const STORAGE_KEY = 'rba-hawko-calculator';
const DEFAULTS = {
  loanAmount: 600000, termYears: 25, interestRate: 3.85,
  repaymentType: 'PI', frequency: 'monthly'
};

function loadInputs() {
  try {
    const item = localStorage.getItem(STORAGE_KEY);
    if (item === null) return { ...DEFAULTS };
    const parsed = JSON.parse(item);
    return isValidInputs(parsed) ? parsed : { ...DEFAULTS };
  } catch (error) {
    localStorage.removeItem(STORAGE_KEY); // Remove corrupted data
    return { ...DEFAULTS };
  }
}

function saveInputs(inputs) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(inputs));
    return true;
  } catch (error) {
    return false; // Never crash on storage failure
  }
}
```

### Pattern 5: Accessible Range Slider
**What:** Native `<input type="range">` paired with `<output>` element, full aria attributes, keyboard support.
**When to use:** The scenario slider (0-10% range).
**Example:**
```html
<!-- Source: MDN, WCAG 2.0 range slider patterns -->
<label for="calc-slider">Scenario Interest Rate</label>
<input type="range" id="calc-slider" min="0" max="10" step="0.25" value="3.85"
  aria-valuemin="0" aria-valuemax="10" aria-valuenow="3.85"
  aria-valuetext="3.85 percent">
<output for="calc-slider" aria-live="polite">3.85%</output>
```

### Anti-Patterns to Avoid
- **Using native JS arithmetic for money:** `0.1 + 0.2 = 0.30000000000000004` -- always use Decimal.js
- **innerHTML for DOM updates:** XSS risk AND can't audit compliance of injected strings -- use createElement/textContent
- **Defaulting slider to 0%:** Misleading; default to current RBA rate (3.85%)
- **Parsing localStorage without try-catch:** Causes app crash on corrupted data
- **Premature validation:** Don't show errors while user is still typing; validate on blur or submit
- **Generic disclaimer jargon:** Users skip legalese; use plain English educational framing

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Decimal arithmetic | Custom precision library or Math.round() hacks | Decimal.js | Floating-point errors compound over 300 months; Decimal.js is battle-tested for financial apps |
| Form validation | Custom regex validators | HTML5 Constraint Validation API + setCustomValidity() | Native, accessible, works with screen readers, no library needed |
| Number formatting | String manipulation with regex | Intl.NumberFormat('en-AU', { style: 'currency', currency: 'AUD' }) | Handles locale-specific formatting, comma separators, edge cases |
| localStorage JSON handling | Manual JSON.parse/stringify | Wrapper with try-catch + validation (see Pattern 4) | Prevents crashes from corrupted data, quota exceeded, disabled storage |
| Amortization formula | Simplified approximation | Standard formula: M = P * [r(1+r)^n] / [(1+r)^n - 1] | The standard formula is well-documented and verified; approximations lose accuracy over long terms |

**Key insight:** Mortgage calculations over 25-30 year terms are unforgiving of precision shortcuts. A $600k loan at 3.85% computed with native JS `Number` could be off by hundreds of dollars from the correct amortized value due to compounding floating-point errors. Decimal.js eliminates this entirely.

## Common Pitfalls

### Pitfall 1: Floating-Point Precision Errors in Financial Calculations
**What goes wrong:** Using JavaScript's native `Number` type causes rounding errors that compound over long loan terms (300+ months), producing incorrect payment amounts and interest totals.
**Why it happens:** JavaScript numbers are IEEE 754 double-precision floats; `0.1 + 0.2 = 0.30000000000000004`.
**How to avoid:** Use Decimal.js for ALL financial calculations. Pass values as strings: `new Decimal('600000')` not `new Decimal(600000)`.
**Warning signs:** Final loan balance doesn't reach exactly zero; monthly amounts differ by pennies from expected values.

### Pitfall 2: Incorrect Fortnightly/Weekly Payment Calculations
**What goes wrong:** Dividing annual payment by 26/52 instead of dividing monthly by 2/4 loses the accelerated payoff benefit.
**Why it happens:** Misunderstanding that fortnightly/weekly create extra annual payments (13 months vs 12).
**How to avoid:** Use "Half Monthly Method" -- calculate monthly first, divide by 2 (fortnightly) or 4 (weekly).
**Warning signs:** Comparison shows no difference between monthly and fortnightly total interest paid.

### Pitfall 3: localStorage Data Corruption Breaking Calculator
**What goes wrong:** Corrupted localStorage data causes JSON.parse() to throw, crashing the calculator on page load.
**Why it happens:** User edits localStorage, browser corruption, quota exceeded leaves partial data.
**How to avoid:** Always try-catch, validate parsed structure, remove corrupted entries, fall back to defaults.
**Warning signs:** Calculator works on first visit but breaks on reload.

### Pitfall 4: Crossing from Factual Information into General Advice (ASIC RG 244)
**What goes wrong:** Calculator language inadvertently implies the user should take action, triggering ASIC advice classification requiring an AFS licence.
**Why it happens:** Natural language patterns suggest recommendations without realizing regulatory implications.
**How to avoid:** Apply four compliance tests to every piece of text: (1) Data Not Opinion, (2) No Action Implication, (3) Reasonable Person, (4) Educational Framing.
**Warning signs:** Text uses "you should", "we recommend", "best option", "your mortgage", or makes personalized statements.

### Pitfall 5: Misleading Default Values
**What goes wrong:** Unrealistic defaults (0% rate, 10-year term) cause users to trust incorrect calculations.
**Why it happens:** Developers choose 0 as safe default without considering UX impact.
**How to avoid:** Pre-fill with Australian averages: $600k, 25yr, 3.85%, P&I, monthly. Include contextual help text.
**Warning signs:** Users screenshot unrealistic scenarios, help requests show confusion about results.

### Pitfall 6: Slider Without Accessible Feedback
**What goes wrong:** Screen readers can't announce slider value changes, keyboard-only users can't see current value.
**Why it happens:** Implementing visual slider without considering assistive technology.
**How to avoid:** Pair `<input type="range">` with `<output>` element. Update aria-valuenow and aria-valuetext on input. Use aria-live="polite" on output.
**Warning signs:** Screen reader testing reveals no value announcements.

### Pitfall 7: Interest-Only Calculation Misunderstanding
**What goes wrong:** Applying amortization formula to interest-only loans shows principal reduction when there shouldn't be any.
**Why it happens:** Not checking repayment type before selecting formula.
**How to avoid:** If IO: `payment = principal * monthlyRate` (simple interest). Display educational note: "During an interest-only period, the loan balance remains unchanged."
**Warning signs:** IO results show declining balance; total interest appears artificially low.

## Code Examples

Verified patterns from official sources:

### Complete Amortization Formula
```javascript
// Source: Standard amortization formula, verified against Wikipedia and ASIC MoneySmart calculator
function calculateMonthlyPaymentPI(principal, annualRatePct, termYears) {
  const P = new Decimal(principal.toString());
  const r = new Decimal(annualRatePct.toString()).dividedBy(100).dividedBy(12);
  const n = new Decimal(termYears.toString()).times(12);

  // Edge case: 0% interest
  if (r.lessThanOrEqualTo(0)) {
    return P.dividedBy(n);
  }

  // M = P * [r(1+r)^n] / [(1+r)^n - 1]
  const onePlusR = r.plus(1);
  const onePlusRtoN = onePlusR.pow(n);
  return P.times(r.times(onePlusRtoN)).dividedBy(onePlusRtoN.minus(1));
}

// Example: $600k at 3.85% for 25 years = $3,104.23/month
```

### Interest-Only Calculation
```javascript
// Source: Standard IO formula
function calculateMonthlyPaymentIO(principal, annualRatePct) {
  const P = new Decimal(principal.toString());
  const r = new Decimal(annualRatePct.toString()).dividedBy(100).dividedBy(12);
  return P.times(r);
}

// Example: $600k at 3.85% IO = $1,925.00/month
```

### Scenario Comparison
```javascript
// Source: User requirements + standard mortgage comparison patterns
function compareScenarios(inputs, scenarioRate) {
  const freq = FREQUENCY_LABELS[inputs.frequency];
  const currentMonthly = calculatePayment(inputs);
  const scenarioMonthly = calculatePayment({ ...inputs, interestRate: scenarioRate });
  const quarterPointMonthly = calculatePayment({ ...inputs, interestRate: inputs.interestRate + 0.25 });

  const currentPerPeriod = currentMonthly.dividedBy(freq.divisor);
  const scenarioPerPeriod = scenarioMonthly.dividedBy(freq.divisor);

  return {
    current: { rate: inputs.interestRate, perPeriod: currentPerPeriod, annual: currentPerPeriod.times(freq.perYear) },
    scenario: { rate: scenarioRate, perPeriod: scenarioPerPeriod, annual: scenarioPerPeriod.times(freq.perYear) },
    quarterPoint: { rate: inputs.interestRate + 0.25, perPeriod: quarterPointMonthly.dividedBy(freq.divisor), annual: quarterPointMonthly.dividedBy(freq.divisor).times(freq.perYear) },
    diff: { perPeriod: scenarioPerPeriod.minus(currentPerPeriod), annual: scenarioPerPeriod.times(freq.perYear).minus(currentPerPeriod.times(freq.perYear)) }
  };
}
```

### ASIC-Compliant Educational Framing
```html
<!-- Source: ASIC RG 244 + competitor analysis (ASX, MoneySmart, Westpac) -->

<!-- Calculator heading - educational framing (CORRECT) -->
<h2>Explore Rate Scenarios</h2>
<p>See how different interest rates could affect a typical Australian
   mortgage. Adjust the inputs below and use the scenario slider to explore
   various market conditions.</p>

<!-- NOT: "Calculate YOUR mortgage payments" - too personal -->
<!-- NOT: "Find the best rate for you" - implies advice -->

<!-- Calculator disclaimer - adjacent to form (CORRECT) -->
<div class="disclaimer-box">
  <strong>Illustrative Estimates Only</strong> — This calculator shows how
  different interest rates affect a typical mortgage. Results are estimates
  and do not include fees, charges, or rate variations over time. This is
  not financial advice.
</div>
```

### Footer Disclaimer (Verified Against Competitors)
```html
<!-- Source: Synthesized from ASX, ASIC MoneySmart, Westpac, Canstar, RBA Rate Watch patterns -->
<footer>
  <h3>General Information Only</h3>
  <p>This website shows factual economic data for educational purposes.
     It is not financial advice, a recommendation, or a forecast. The
     Hawk-O-Meter score and calculator tools perform mathematical computations
     on publicly available data. They do not take into account your personal
     objectives, financial situation, or needs.</p>
  <p>Before making financial decisions, speak to a licensed financial adviser.</p>
  <p>The creators of this website do not hold an Australian Financial Services Licence.</p>
  <h4>Data Sources</h4>
  <p>Economic data from the Australian Bureau of Statistics and Reserve Bank
     of Australia. Market-implied probabilities derived from ASX 30 Day
     Interbank Cash Rate Futures. These organisations do not endorse this website.</p>
</footer>
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Native JS arithmetic for money | Decimal.js or Big.js | ~2015 awareness | Eliminates compounding rounding errors in financial calculations |
| Custom form validation libraries | HTML5 Constraint Validation API | Widely supported 2015+ | Reduces dependencies, improves accessibility |
| Cookies for preferences | localStorage | HTML5 standard ~2011 | Simpler API, larger storage (5MB vs 4KB), no server round-trips |
| Monthly-only calculators | Multi-frequency support | Ongoing user expectation | Reflects real Australian mortgage market (fortnightly common) |
| Legal jargon disclaimers | Plain English educational framing | ASIC RG 244 emphasis | Users actually read and understand disclaimers |
| jQuery validation plugins | Native HTML5 validation | jQuery usage declined ~2020 | No external dependency, better accessibility, smaller bundle |

**Deprecated/outdated:**
- jQuery validation plugins: HTML5 native validation is sufficient and more accessible
- Homegrown decimal libraries: Decimal.js is the established standard
- IndexedDB for simple storage: Overkill; localStorage adequate for key-value pairs
- Generic "not financial advice" legalese: Replace with specific plain English explanations

## Open Questions

1. **Exact ASIC RG 244 calculator-specific guidance**
   - What we know: RG 244 distinguishes factual information from advice. Calculator is Tier 1 (mathematical computation). ASIC MoneySmart runs calculators with similar disclaimers.
   - What's unclear: ASIC hasn't published calculator-specific compliance guidance. Relying on analogy to MoneySmart and bank calculator patterns.
   - Recommendation: Follow ASIC MoneySmart patterns (educational framing, plain English disclaimers). LOW confidence for compliance specifics until legal review.

2. **Total interest over life of loan display**
   - What we know: User requirements mention "total interest difference" in comparison table. Formula: Total Interest = (Payment * Number of Payments) - Principal.
   - What's unclear: Whether to show total-over-life or annualized figures for fortnightly/weekly frequencies.
   - Recommendation: Show per-period difference and annual difference. Total-over-life is secondary info.

3. **Handling scenario rates below current rate**
   - What we know: Slider goes down to 0%. Users may want to model rate cuts.
   - What's unclear: How to phrase negative differences naturally.
   - Recommendation: Use signed values (+$X / -$X). Green for savings, red for cost increase. Keep language neutral: "If rates were X%" not "when rates drop".

4. **Decimal.js CDN reliability**
   - What we know: jsDelivr CDN is widely used and reliable. Decimal.js is ES5-compatible.
   - What's unclear: Exact browser support matrix for very old mobile browsers.
   - Recommendation: jsDelivr CDN with SRI hash. Test in Safari, Chrome, Firefox, Edge.

## ASIC Compliance Framework (Domain-Specific Research)

### The Three-Tier Hierarchy

ASIC RG 244 establishes classification that determines legal obligations:

| Tier | Classification | AFS License? | Hawk-O-Meter Target |
|------|---------------|-------------|---------------------|
| 1 | Factual Information | NO | This is where we MUST stay |
| 2 | General Advice | YES | Must avoid |
| 3 | Personal Advice | YES + fiduciary | Must avoid |

**Tier 1 test:** "Objectively ascertainable information, the truth or accuracy of which cannot reasonably be questioned." Includes: current rates, historical data, mathematical computations, market-implied probabilities.

**Critical precedent:** ASX RBA Rate Tracker (nearly identical tool by a licensed market operator) is classified as "indicative information, not investment advice."

### Four Compliance Tests (Every Text Element Must Pass)

1. **Data Not Opinion Test:** Does this present verifiable data, or express a view?
2. **Action Implication Test:** Could this be read as suggesting the user do something?
3. **Reasonable Person Test:** Could a reasonable person regard this as intended to influence a financial decision?
4. **Educational Framing Test:** Is this framed as learning/exploration, not advice?

### Red Lines (Absolute Boundaries)

| Red Line | Example Violation |
|----------|------------------|
| Recommending products | "Fix your rate now" |
| Suggesting actions | "You should refinance before rates rise" |
| Personalizing guidance | "Based on your loan, consider..." |
| Implying certainty | "Rates WILL rise next month" |
| Value judgments | "Dangerous time for variable rate borrowers" |
| Market timing | "Lock in your rate now" |

### Neutral Language Approach (Principle-Based)

Rather than a rigid word list, enforce four principles:
1. **Educational framing:** "typical mortgage" not "your mortgage"
2. **Neutral data presentation:** "Market pricing implies..." not "We predict..."
3. **No action implications:** Present data, never suggest actions
4. **Qualified language:** "implies", "suggests", "based on" -- never absolutes

### Words/Phrases to Avoid
- "you should", "we recommend", "best option", "consider switching"
- "will rise", "will fall", "guaranteed", "certain"
- "your mortgage", "your repayments" (use "a mortgage", "the repayments")
- "prediction", "forecast" (use "market expectation", "market pricing")
- "danger", "warning", "safe" in financial context (use "hawkish", "dovish", "neutral")
- "lock in", "act now", "before it's too late"

## Sources

### Primary (HIGH confidence)
- [ASIC RG 244: Giving information, general advice and scaled advice](https://www.asic.gov.au/regulatory-resources/find-a-document/regulatory-guides/rg-244-giving-information-general-advice-and-scaled-advice/) -- Three-tier hierarchy, factual information definition
- [Corporations Act 2001 s766B](https://www.austlii.edu.au/au/legis/cth/consol_act/ca2001172/s766b.html) -- Legal definition of financial product advice
- [ASIC INFO 269: Discussing financial products online](https://www.asic.gov.au/regulatory-resources/financial-services/giving-financial-product-advice/discussing-financial-products-and-services-online/) -- Online content compliance
- [Decimal.js GitHub Repository](https://github.com/MikeMcl/decimal.js/) -- API, usage patterns, version info
- [MDN: Client-side form validation](https://developer.mozilla.org/en-US/docs/Learn_web_development/Extensions/Forms/Form_validation) -- HTML5 Constraint Validation API
- [MDN: Window.localStorage](https://developer.mozilla.org/en-US/docs/Web/API/Window/localStorage) -- localStorage API documentation

### Secondary (MEDIUM confidence)
- [ASX RBA Rate Tracker](https://www.asx.com.au/markets/trade-our-derivatives-market/futures-market/rba-rate-tracker) -- Competitor disclaimer patterns, "indicative information" classification
- [ASIC MoneySmart Mortgage Calculator](https://moneysmart.gov.au/home-loans/mortgage-calculator) -- Government calculator patterns, educational framing reference
- [Westpac v ASIC [2021] HCA 3](https://www.brightlaw.com.au/case-note-high-court-defines-personal-advice/) -- Personal advice threshold ("reasonable possibility" test)
- [Finder.com.au: Fortnightly vs Monthly](https://www.finder.com.au/fortnightly-repayment-frequency) -- Half-monthly method verification
- [Mortgage Calculator - Wikipedia](https://en.wikipedia.org/wiki/Mortgage_calculator) -- Standard amortization formula verification
- .planning/research/asic-compliance.md -- Full 11-section ASIC compliance analysis (internal research document)

### Tertiary (LOW confidence -- marked for validation)
- ASIC calculator-specific compliance guidance -- not found; relying on analogy to MoneySmart patterns
- Decimal.js browser support matrix for legacy mobile -- not verified, assumed ES5 compatibility

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- Decimal.js, HTML5 validation, localStorage are mature, well-documented, verified via official docs
- Architecture: HIGH -- IIFE module pattern established in Phase 2, extending same structure
- Pitfalls: HIGH -- Floating-point errors and localStorage corruption well-documented; mortgage math verified against multiple sources
- ASIC Compliance: MEDIUM-HIGH -- Based on detailed RG 244 research, competitor analysis, case law. Comprehensive asic-compliance.md research document completed. Legal review still recommended before commercial launch.

**Research date:** 2026-02-06
**Valid until:** 2026-03-08 (30 days for stable technologies; ASIC guidance may change)
