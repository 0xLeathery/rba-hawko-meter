/**
 * Main dashboard initialization.
 * Orchestrates DataModule, ChartModule, and CountdownModule.
 * Uses Promise.allSettled for independent data loading.
 * Uses safe DOM methods throughout.
 */
(function () {
  'use strict';

  var resizeTimer = null;

  /**
   * Update the cash rate display with data from rates.json.
   * @param {Object} rateData
   */
  function updateCashRate(rateData) {
    var rateEl = document.getElementById('cash-rate-value');
    var updatedEl = document.getElementById('cash-rate-updated');
    var footerUpdatedEl = document.getElementById('footer-updated');
    var chartSourceEl = document.getElementById('chart-source');

    if (rateEl) {
      rateEl.textContent = rateData.current_rate.toFixed(2) + '%';
    }

    var updatedText = 'Last updated: ' + rateData.last_updated;
    if (updatedEl) {
      updatedEl.textContent = updatedText;
    }
    if (footerUpdatedEl) {
      footerUpdatedEl.textContent = updatedText;
    }
    if (chartSourceEl) {
      chartSourceEl.textContent = 'Source: Reserve Bank of Australia | Updated ' + rateData.last_updated;
    }
  }

  /**
   * Show error state for the cash rate display.
   */
  function showCashRateError() {
    var rateEl = document.getElementById('cash-rate-value');
    var updatedEl = document.getElementById('cash-rate-updated');

    if (rateEl) {
      rateEl.textContent = '--';
      rateEl.className = rateEl.className.replace('text-white', 'text-red-400');
    }
    if (updatedEl) {
      updatedEl.textContent = 'Unable to load rate data';
      updatedEl.className = updatedEl.className.replace('text-gray-500', 'text-red-400');
    }
  }

  /**
   * Set up the dismiss banner handler.
   */
  function setupBannerDismiss() {
    var banner = document.getElementById('disclaimer-banner');
    var dismissBtn = document.getElementById('dismiss-banner');

    if (!banner || !dismissBtn) return;

    // Check if already dismissed this session
    if (sessionStorage.getItem('banner-dismissed') === '1') {
      banner.style.display = 'none';
      return;
    }

    dismissBtn.addEventListener('click', function () {
      banner.style.display = 'none';
      sessionStorage.setItem('banner-dismissed', '1');
    });
  }

  /**
   * Set up debounced chart resize on window resize.
   */
  function setupResizeHandler() {
    window.addEventListener('resize', function () {
      if (resizeTimer) {
        clearTimeout(resizeTimer);
      }
      resizeTimer = setTimeout(function () {
        ChartModule.resize('rate-chart');
      }, 250);
    });
  }

  /**
   * Initialize the calculator module (Phase 5).
   * Guarded so Phase 2 dashboard works without Phase 5 code.
   */
  function initCalculator() {
    try {
      if (typeof CalculatorModule !== 'undefined') {
        CalculatorModule.init();
      }
    } catch (error) {
      console.error('Calculator initialization failed:', error);
      var calcSection = document.getElementById('calculator-section');
      if (calcSection) {
        DataModule.showError('calc-results', 'Calculator failed to load. Please refresh the page.');
      }
    }
  }

  /**
   * Initialize the dashboard.
   */
  function init() {
    setupBannerDismiss();

    // Initialize calculator (independent of data loading)
    initCalculator();

    // Show loading states
    DataModule.showLoading('rate-chart', 'Loading chart data...');

    // Fetch data in parallel using allSettled
    Promise.allSettled([
      DataModule.fetch('data/rates.json'),
      DataModule.fetch('data/meetings.json')
    ]).then(function (results) {
      var ratesResult = results[0];
      var meetingsResult = results[1];

      // Handle rates data
      if (ratesResult.status === 'fulfilled') {
        var rateData = ratesResult.value;
        updateCashRate(rateData);
        ChartModule.create('rate-chart', rateData);
        setupResizeHandler();
      } else {
        showCashRateError();
        DataModule.showError('rate-chart', 'Failed to load rate data. Please refresh the page.');
      }

      // Handle meetings data
      var countdownEl = document.getElementById('countdown-section');
      if (meetingsResult.status === 'fulfilled' && countdownEl) {
        CountdownModule.start(countdownEl, meetingsResult.value);
      } else if (countdownEl) {
        DataModule.showError('countdown-section', 'Failed to load meeting schedule.');
      }
    });
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
