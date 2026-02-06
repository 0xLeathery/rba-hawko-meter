/**
 * CalculatorModule - Mortgage repayment calculator with scenario comparison.
 * Uses Decimal.js for all financial arithmetic (no native JS math on money).
 * Uses safe DOM methods (createElement/textContent) throughout -- no innerHTML.
 * Persists inputs in localStorage with validation and graceful fallback.
 */
var CalculatorModule = (function () {
  'use strict';

  var STORAGE_KEY = 'rba-hawko-calculator';

  var DEFAULTS = {
    loanAmount: 600000,
    termYears: 25,
    interestRate: 3.85,
    repaymentType: 'PI',
    frequency: 'monthly'
  };

  var FREQUENCY_LABELS = {
    monthly: { label: 'per month', divisor: 1, perYear: 12 },
    fortnightly: { label: 'per fortnight', divisor: 2, perYear: 26 },
    weekly: { label: 'per week', divisor: 4, perYear: 52 }
  };

  var debounceTimer = null;

  // ---------------------------------------------------------------------------
  // Financial calculations (all Decimal.js)
  // ---------------------------------------------------------------------------

  /**
   * Calculate monthly P&I repayment using standard amortization formula.
   * M = P * [r(1+r)^n] / [(1+r)^n - 1]
   * @param {number|string} principal - Loan amount
   * @param {number|string} annualRatePct - Annual interest rate as percentage
   * @param {number|string} termYears - Loan term in years
   * @returns {Decimal} Monthly payment
   */
  function calculateMonthlyPaymentPI(principal, annualRatePct, termYears) {
    var P = new Decimal(principal.toString());
    var r = new Decimal(annualRatePct.toString()).dividedBy(100).dividedBy(12);
    var n = new Decimal(termYears.toString()).times(12);

    // Edge case: 0% or near-zero interest
    if (r.lessThanOrEqualTo(new Decimal('0.0000001'))) {
      return P.dividedBy(n);
    }

    var onePlusR = r.plus(1);
    var onePlusRtoN = onePlusR.pow(n);
    return P.times(r.times(onePlusRtoN)).dividedBy(onePlusRtoN.minus(1));
  }

  /**
   * Calculate monthly interest-only repayment.
   * @param {number|string} principal - Loan amount
   * @param {number|string} annualRatePct - Annual interest rate as percentage
   * @returns {Decimal} Monthly IO payment
   */
  function calculateMonthlyPaymentIO(principal, annualRatePct) {
    var P = new Decimal(principal.toString());
    var r = new Decimal(annualRatePct.toString()).dividedBy(100).dividedBy(12);
    return P.times(r);
  }

  /**
   * Calculate per-period payment for given inputs and rate.
   * Dispatches to PI or IO formula, then adjusts for frequency.
   * @param {Object} inputs - Calculator inputs
   * @param {number} [rateOverride] - Optional rate to use instead of inputs.interestRate
   * @returns {Decimal} Per-period payment
   */
  function calculatePayment(inputs, rateOverride) {
    var rate = rateOverride !== undefined ? rateOverride : inputs.interestRate;
    var monthly;

    if (inputs.repaymentType === 'IO') {
      monthly = calculateMonthlyPaymentIO(inputs.loanAmount, rate);
    } else {
      monthly = calculateMonthlyPaymentPI(inputs.loanAmount, rate, inputs.termYears);
    }

    var freq = FREQUENCY_LABELS[inputs.frequency];
    return monthly.dividedBy(freq.divisor);
  }

  /**
   * Build full scenario comparison object.
   * @param {Object} inputs - Calculator inputs
   * @param {number} scenarioRate - Rate from slider
   * @returns {Object} Comparison data with current, scenario, quarterPoint, and diff
   */
  function calculateComparison(inputs, scenarioRate) {
    var freq = FREQUENCY_LABELS[inputs.frequency];

    var currentPerPeriod = calculatePayment(inputs);
    var scenarioPerPeriod = calculatePayment(inputs, scenarioRate);
    var quarterPointRate = new Decimal(inputs.interestRate.toString()).plus('0.25').toNumber();
    var quarterPointPerPeriod = calculatePayment(inputs, quarterPointRate);

    var currentAnnual = currentPerPeriod.times(freq.perYear);
    var scenarioAnnual = scenarioPerPeriod.times(freq.perYear);
    var quarterPointAnnual = quarterPointPerPeriod.times(freq.perYear);

    return {
      current: {
        rate: inputs.interestRate,
        perPeriod: currentPerPeriod.toFixed(2),
        annual: currentAnnual.toFixed(2)
      },
      scenario: {
        rate: scenarioRate,
        perPeriod: scenarioPerPeriod.toFixed(2),
        annual: scenarioAnnual.toFixed(2)
      },
      quarterPoint: {
        rate: quarterPointRate,
        perPeriod: quarterPointPerPeriod.toFixed(2),
        annual: quarterPointAnnual.toFixed(2)
      },
      diff: {
        perPeriod: scenarioPerPeriod.minus(currentPerPeriod).toFixed(2),
        annual: scenarioAnnual.minus(currentAnnual).toFixed(2)
      }
    };
  }

  // ---------------------------------------------------------------------------
  // Formatting
  // ---------------------------------------------------------------------------

  var currencyFormatter = typeof Intl !== 'undefined'
    ? new Intl.NumberFormat('en-AU', { style: 'currency', currency: 'AUD', minimumFractionDigits: 2 })
    : null;

  /**
   * Format a numeric value as AUD currency.
   * @param {string|number} value
   * @returns {string} e.g. "$3,104.23"
   */
  function formatCurrency(value) {
    var num = parseFloat(value);
    if (isNaN(num)) return '$0.00';
    if (currencyFormatter) return currencyFormatter.format(num);
    return '$' + num.toFixed(2);
  }

  /**
   * Format a numeric value as a signed currency difference.
   * Returns object with text and className for color coding.
   * @param {string|number} value
   * @returns {{ text: string, className: string }}
   */
  function formatDifference(value) {
    var num = parseFloat(value);
    if (isNaN(num) || Math.abs(num) < 0.005) {
      return { text: '$0.00', className: 'text-gray-400' };
    }
    var abs = Math.abs(num);
    var formatted = formatCurrency(abs);
    if (num > 0) {
      return { text: '+' + formatted, className: 'text-red-400' };
    }
    return { text: '-' + formatted, className: 'text-green-400' };
  }

  // ---------------------------------------------------------------------------
  // localStorage persistence
  // ---------------------------------------------------------------------------

  /**
   * Validate that parsed inputs have correct types and ranges.
   * @param {*} data
   * @returns {boolean}
   */
  function isValidInputs(data) {
    if (data === null || typeof data !== 'object') return false;

    if (typeof data.loanAmount !== 'number' || data.loanAmount < 1000 || data.loanAmount > 10000000) return false;
    if (typeof data.termYears !== 'number' || data.termYears < 1 || data.termYears > 30) return false;
    if (typeof data.interestRate !== 'number' || data.interestRate < 0.01 || data.interestRate > 15) return false;
    if (data.repaymentType !== 'PI' && data.repaymentType !== 'IO') return false;
    if (data.frequency !== 'monthly' && data.frequency !== 'fortnightly' && data.frequency !== 'weekly') return false;

    return true;
  }

  /**
   * Load inputs from localStorage, falling back to defaults.
   * @returns {Object} Valid inputs object
   */
  function loadInputs() {
    try {
      var item = localStorage.getItem(STORAGE_KEY);
      if (item === null) return assign({}, DEFAULTS);
      var parsed = JSON.parse(item);
      return isValidInputs(parsed) ? parsed : assign({}, DEFAULTS);
    } catch (e) {
      try { localStorage.removeItem(STORAGE_KEY); } catch (_) { /* ignore */ }
      return assign({}, DEFAULTS);
    }
  }

  /**
   * Save inputs to localStorage.
   * @param {Object} inputs
   * @returns {boolean} true if saved successfully
   */
  function saveInputs(inputs) {
    if (inputs === null || typeof inputs !== 'object') return false;
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(inputs));
      return true;
    } catch (e) {
      return false;
    }
  }

  // ---------------------------------------------------------------------------
  // DOM helpers (safe methods only -- no innerHTML)
  // ---------------------------------------------------------------------------

  /**
   * Simple Object.assign polyfill for ES5 compatibility.
   */
  function assign(target) {
    for (var i = 1; i < arguments.length; i++) {
      var source = arguments[i];
      if (source) {
        for (var key in source) {
          if (Object.prototype.hasOwnProperty.call(source, key)) {
            target[key] = source[key];
          }
        }
      }
    }
    return target;
  }

  /**
   * Set text content of an element by ID.
   * @param {string} id - Element ID
   * @param {string} text - Text content
   */
  function setText(id, text) {
    var el = document.getElementById(id);
    if (el) el.textContent = text;
  }

  /**
   * Set text content and className of an element by ID.
   * Preserves base classes, applies diff color class.
   * @param {string} id - Element ID
   * @param {string} text
   * @param {string} className - Color class to apply
   */
  function setDiffText(id, text, className) {
    var el = document.getElementById(id);
    if (!el) return;
    el.textContent = text;
    // Replace color classes while preserving layout classes
    el.className = el.className
      .replace(/text-red-\d+/g, '')
      .replace(/text-green-\d+/g, '')
      .replace(/text-gray-\d+/g, '')
      .trim() + ' ' + className;
  }

  /**
   * Update the slider output element.
   * @param {HTMLInputElement} slider
   * @param {HTMLOutputElement} output
   */
  function updateSliderOutput(slider, output) {
    if (!slider || !output) return;
    output.textContent = slider.value + '%';
    slider.setAttribute('aria-valuenow', slider.value);
    slider.setAttribute('aria-valuetext', slider.value + ' percent');
  }

  /**
   * Read current inputs from the form fields.
   * @returns {Object} inputs
   */
  function getInputsFromForm() {
    var loanEl = document.getElementById('calc-loan-amount');
    var termEl = document.getElementById('calc-term');
    var rateEl = document.getElementById('calc-rate');
    var typeEl = document.getElementById('calc-type');
    var freqEl = document.getElementById('calc-frequency');

    return {
      loanAmount: loanEl ? parseFloat(loanEl.value) || DEFAULTS.loanAmount : DEFAULTS.loanAmount,
      termYears: termEl ? parseInt(termEl.value, 10) || DEFAULTS.termYears : DEFAULTS.termYears,
      interestRate: rateEl ? parseFloat(rateEl.value) || DEFAULTS.interestRate : DEFAULTS.interestRate,
      repaymentType: typeEl ? typeEl.value : DEFAULTS.repaymentType,
      frequency: freqEl ? freqEl.value : DEFAULTS.frequency
    };
  }

  /**
   * Populate form fields from an inputs object.
   * @param {Object} inputs
   */
  function populateForm(inputs) {
    var loanEl = document.getElementById('calc-loan-amount');
    var termEl = document.getElementById('calc-term');
    var rateEl = document.getElementById('calc-rate');
    var typeEl = document.getElementById('calc-type');
    var freqEl = document.getElementById('calc-frequency');

    if (loanEl) loanEl.value = inputs.loanAmount;
    if (termEl) termEl.value = inputs.termYears;
    if (rateEl) rateEl.value = inputs.interestRate;
    if (typeEl) typeEl.value = inputs.repaymentType;
    if (freqEl) freqEl.value = inputs.frequency;
  }

  /**
   * Update all display elements with comparison data.
   * @param {Object} comparison - From calculateComparison
   * @param {string} frequency - 'monthly' | 'fortnightly' | 'weekly'
   */
  function updateDisplay(comparison, frequency) {
    var freq = FREQUENCY_LABELS[frequency];

    // Current payment
    setText('calc-current-payment', formatCurrency(comparison.current.perPeriod));
    setText('calc-current-rate-label', 'at ' + comparison.current.rate + '%');
    setText('calc-current-freq-label', freq.label);

    // Scenario payment
    setText('calc-scenario-payment', formatCurrency(comparison.scenario.perPeriod));
    setText('calc-scenario-rate-label', 'at ' + comparison.scenario.rate + '%');
    setText('calc-scenario-freq-label', freq.label);

    // Difference displays
    var perPeriodDiff = formatDifference(comparison.diff.perPeriod);
    var annualDiff = formatDifference(comparison.diff.annual);

    setDiffText('calc-diff-per-period', perPeriodDiff.text + ' ' + freq.label, perPeriodDiff.className);
    setDiffText('calc-diff-annual', annualDiff.text + ' per year', annualDiff.className);

    // Comparison table
    updateComparisonTable(comparison, freq);
  }

  /**
   * Update the comparison table rows using safe DOM methods.
   * @param {Object} comparison
   * @param {Object} freq - Frequency config
   */
  function updateComparisonTable(comparison, freq) {
    var tbody = document.getElementById('calc-table-body');
    if (!tbody) return;

    // Clear existing rows
    while (tbody.firstChild) {
      tbody.removeChild(tbody.firstChild);
    }

    var rows = [
      { label: 'Current Rate', data: comparison.current, isCurrent: true },
      { label: 'Scenario Rate', data: comparison.scenario, isCurrent: false },
      { label: '+0.25% (Standard RBA Move)', data: comparison.quarterPoint, isCurrent: false }
    ];

    for (var i = 0; i < rows.length; i++) {
      var row = rows[i];
      var tr = document.createElement('tr');
      tr.className = i % 2 === 0
        ? 'bg-transparent'
        : 'bg-white/[0.02]';

      var tdRate = document.createElement('td');
      tdRate.className = 'px-4 py-3 text-sm text-gray-300';
      tdRate.textContent = row.data.rate + '%';
      if (row.isCurrent) {
        var badge = document.createElement('span');
        badge.className = 'ml-2 text-xs px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-300';
        badge.textContent = 'current';
        tdRate.appendChild(badge);
      }
      tr.appendChild(tdRate);

      var tdPayment = document.createElement('td');
      tdPayment.className = 'px-4 py-3 text-sm text-gray-200 font-medium';
      tdPayment.textContent = formatCurrency(row.data.perPeriod) + ' ' + freq.label;
      tr.appendChild(tdPayment);

      var tdAnnual = document.createElement('td');
      tdAnnual.className = 'px-4 py-3 text-sm text-gray-300';
      tdAnnual.textContent = formatCurrency(row.data.annual);
      tr.appendChild(tdAnnual);

      var tdDiff = document.createElement('td');
      tdDiff.className = 'px-4 py-3 text-sm';
      if (row.isCurrent) {
        tdDiff.textContent = '--';
        tdDiff.className += ' text-gray-500';
      } else {
        var diffVal = new Decimal(row.data.annual).minus(new Decimal(comparison.current.annual));
        var diffFormatted = formatDifference(diffVal.toFixed(2));
        tdDiff.textContent = diffFormatted.text + '/yr';
        tdDiff.className += ' ' + diffFormatted.className;
      }
      tr.appendChild(tdDiff);

      tbody.appendChild(tr);
    }
  }

  // ---------------------------------------------------------------------------
  // Event handling
  // ---------------------------------------------------------------------------

  /**
   * Simple debounce helper.
   * @param {Function} fn
   * @param {number} delay - Milliseconds
   * @returns {Function}
   */
  function debounce(fn, delay) {
    return function () {
      if (debounceTimer) clearTimeout(debounceTimer);
      debounceTimer = setTimeout(fn, delay);
    };
  }

  /**
   * Handle input changes: recalculate and save.
   */
  function onInputChange() {
    recalculate();
    var inputs = getInputsFromForm();
    saveInputs(inputs);
  }

  /**
   * Handle slider input: recalculate live (no debounce, no save).
   */
  function onSliderInput() {
    var slider = document.getElementById('calc-slider');
    var output = document.getElementById('calc-slider-output');
    updateSliderOutput(slider, output);
    recalculate();
  }

  /**
   * Handle slider change (release): save to localStorage.
   */
  function onSliderChange() {
    var inputs = getInputsFromForm();
    saveInputs(inputs);
  }

  /**
   * Sync slider default position when current rate input changes.
   */
  function onRateInputChange() {
    var rateEl = document.getElementById('calc-rate');
    var slider = document.getElementById('calc-slider');
    if (!rateEl || !slider) return;

    var rate = parseFloat(rateEl.value);
    if (!isNaN(rate) && rate >= 0 && rate <= 10) {
      slider.value = rate;
      var output = document.getElementById('calc-slider-output');
      updateSliderOutput(slider, output);
    }
  }

  /**
   * Attach event listeners to all calculator form elements.
   */
  function attachListeners() {
    var loanEl = document.getElementById('calc-loan-amount');
    var termEl = document.getElementById('calc-term');
    var rateEl = document.getElementById('calc-rate');
    var typeEl = document.getElementById('calc-type');
    var freqEl = document.getElementById('calc-frequency');
    var slider = document.getElementById('calc-slider');

    var debouncedChange = debounce(onInputChange, 300);

    // Select elements: immediate on change
    if (typeEl) typeEl.addEventListener('change', onInputChange);
    if (freqEl) freqEl.addEventListener('change', onInputChange);

    // Number inputs: debounced on input, immediate on change
    if (loanEl) {
      loanEl.addEventListener('input', debouncedChange);
      loanEl.addEventListener('change', onInputChange);
    }
    if (termEl) {
      termEl.addEventListener('input', debouncedChange);
      termEl.addEventListener('change', onInputChange);
    }
    if (rateEl) {
      rateEl.addEventListener('input', debouncedChange);
      rateEl.addEventListener('change', function () {
        onInputChange();
        onRateInputChange();
      });
    }

    // Slider: instant on input, save on change
    if (slider) {
      slider.addEventListener('input', onSliderInput);
      slider.addEventListener('change', onSliderChange);
    }
  }

  // ---------------------------------------------------------------------------
  // Public API
  // ---------------------------------------------------------------------------

  /**
   * Perform a full recalculation and update the display.
   */
  function recalculate() {
    var inputs = getInputsFromForm();

    // Validate inputs
    if (!isValidInputs(inputs)) return;

    var slider = document.getElementById('calc-slider');
    var scenarioRate = slider ? parseFloat(slider.value) : inputs.interestRate;
    if (isNaN(scenarioRate)) scenarioRate = inputs.interestRate;

    var comparison = calculateComparison(inputs, scenarioRate);
    updateDisplay(comparison, inputs.frequency);
  }

  /**
   * Initialize the calculator module.
   * Loads saved inputs, populates the form, runs initial calculation,
   * and attaches event listeners.
   * @returns {boolean} true if initialized successfully
   */
  function init() {
    // Verify Decimal.js is available
    if (typeof Decimal === 'undefined') {
      var calcResults = document.getElementById('calc-results');
      if (calcResults) {
        var errMsg = document.createElement('p');
        errMsg.className = 'text-red-400 text-sm';
        errMsg.textContent = 'Calculator requires Decimal.js library. Please refresh the page.';
        calcResults.appendChild(errMsg);
      }
      return false;
    }

    // Load saved inputs or defaults
    var inputs = loadInputs();

    // Populate form
    populateForm(inputs);

    // Set slider to current interest rate
    var slider = document.getElementById('calc-slider');
    var output = document.getElementById('calc-slider-output');
    if (slider) {
      slider.value = inputs.interestRate;
      updateSliderOutput(slider, output);
    }

    // Initial calculation
    recalculate();

    // Attach event listeners
    attachListeners();

    return true;
  }

  return {
    init: init,
    recalculate: recalculate
  };
})();
