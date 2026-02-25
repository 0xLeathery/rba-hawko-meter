/**
 * Gauge initialization orchestrator.
 * Fetches status.json and renders hero gauge, ASX table, verdict, and metric gauges.
 * Uses DataModule for fetch/cache/error, GaugesModule for
 * rendering, InterpretationsModule for text.
 */
(function () {
  'use strict';

  var METRIC_ORDER = [
    'inflation', 'wages', 'employment', 'housing',
    'spending', 'building_approvals', 'business_confidence'
  ];

  var resizeTimer = null;
  var renderedMetricIds = [];

  /**
   * Render greyed-out placeholder cards for missing indicators.
   * @param {HTMLElement} container - Grid container element
   * @param {Array<string>} missingList - Array of missing indicator IDs
   * @param {Object} weightsObj - Weights object from status.json
   */
  function renderMissingIndicatorCards(container, missingList, weightsObj) {
    if (!Array.isArray(missingList) || missingList.length === 0) return;

    missingList.forEach(function (indicatorId) {
      // Skip asx_futures since it's a benchmark, not an indicator card
      if (indicatorId === 'asx_futures') return;

      var weight = weightsObj[indicatorId] || 0;

      var card = document.createElement('div');
      card.className =
        'bg-finance-gray/50 rounded-lg p-4'
        + ' border border-finance-border/50 opacity-60';

      // Header row: label + weight badge
      var header = document.createElement('div');
      header.className = 'flex items-center justify-between mb-2';

      var label = document.createElement('h4');
      label.className = 'font-semibold text-gray-500';
      label.textContent = GaugesModule.getDisplayLabel(indicatorId);

      var weightBadge = document.createElement('span');
      weightBadge.className = 'text-xs text-gray-600';
      weightBadge.textContent = Math.round(weight * 100) + '% weight';

      header.appendChild(label);
      header.appendChild(weightBadge);
      card.appendChild(header);

      // Placeholder text
      var placeholder = document.createElement('p');
      placeholder.className = 'text-sm text-gray-600 italic';
      placeholder.textContent = 'Data coming soon';
      card.appendChild(placeholder);

      container.appendChild(card);
    });
  }

  /**
   * Render individual metric gauge cards into the grid.
   * @param {Object} gaugesData - data.gauges from status.json
   */
  function renderMetricGauges(gaugesData) {
    var container = document.getElementById('metric-gauges-grid');
    if (!container) return;
    container.textContent = '';

    if (!gaugesData || typeof gaugesData !== 'object') {
      var msg = document.createElement('p');
      msg.className = 'col-span-full text-center text-gray-500 py-8';
      msg.textContent = 'No metric data available';
      container.appendChild(msg);
      return;
    }

    // Build ordered list: METRIC_ORDER entries present in gaugesData, then extras
    var orderedIds = [];
    METRIC_ORDER.forEach(function (id) {
      if (gaugesData[id]) orderedIds.push(id);
    });
    Object.keys(gaugesData).forEach(function (id) {
      if (orderedIds.indexOf(id) === -1 && gaugesData[id]) {
        orderedIds.push(id);
      }
    });

    if (orderedIds.length === 0) {
      var noData = document.createElement('p');
      noData.className = 'col-span-full text-center text-gray-500 py-8';
      noData.textContent = 'No metric data available';
      container.appendChild(noData);
      return;
    }

    renderedMetricIds = [];

    // Render data coverage notice
    var coverageEl = document.getElementById('data-coverage-notice');
    if (coverageEl) {
      var total = 8;
      var available = orderedIds.length;
      if (available < total) {
        coverageEl.textContent =
          'Based on ' + available + ' of ' + total
          + ' indicators (more data coming soon)';
      } else {
        coverageEl.textContent = '';
      }
    }

    orderedIds.forEach(function (metricId) {
      var metricData = gaugesData[metricId];
      if (!metricData) return;

      // Attach metricId for display label lookup inside createBulletGauge
      metricData._metricId = metricId;

      InterpretationsModule.renderMetricCard(
        'metric-gauges-grid', metricId, metricData, metricData.weight
      );

      renderedMetricIds.push(metricId);

      // Staggered rendering for bullet gauges
      requestAnimationFrame(function () {
        GaugesModule.createBulletGauge('gauge-' + metricId, metricData);
      });
    });
  }

  /**
   * Render calculator bridge paragraph with dynamic score/zone text.
   * @param {number} score - Overall hawk score (0-100)
   * @param {string} zoneLabel - Zone label from status.json
   */
  function renderCalculatorBridge(score, _zoneLabel) {
    var calcSection = document.getElementById('calculator-section');
    if (!calcSection) return;

    // Find or create calculator bridge div
    var bridgeDiv = document.getElementById('calculator-bridge');
    if (!bridgeDiv) {
      bridgeDiv = document.createElement('div');
      bridgeDiv.id = 'calculator-bridge';
      bridgeDiv.className =
        'mb-4 p-4 bg-finance-gray'
        + ' border border-finance-border rounded-lg';
      // Insert before the first child (the h2 heading)
      calcSection.insertBefore(bridgeDiv, calcSection.firstChild);
    }

    bridgeDiv.textContent = '';

    var para = document.createElement('p');
    para.className = 'text-sm text-gray-300';

    // Convert zone label to plain English, lowercase
    var plainLabel = GaugesModule.getStanceLabel(score).toLowerCase();

    para.textContent =
      'The Hawk-O-Meter reads '
      + Math.round(score) + '/100 (' + plainLabel
      + '). Here\u2019s what current and potential'
      + ' rate changes could mean for a typical'
      + ' mortgage.';

    bridgeDiv.appendChild(para);
  }

  /**
   * Main initialization: fetch status.json and render all gauges.
   */
  function initGauges() {
    DataModule.showLoading('hero-gauge-plot', 'Loading Hawk Score...');

    DataModule.fetch('data/status.json')
      .then(function (data) {
        // Render hero gauge wrapped in rAF to prevent zero-width after DOM restructure
        requestAnimationFrame(function () {
          GaugesModule.createHeroGauge('hero-gauge-plot', data.overall.hawk_score);
          // Second rAF for resize after paint
          requestAnimationFrame(function () {
            var heroEl = document.getElementById('hero-gauge-plot');
            if (heroEl && heroEl.data) {
              Plotly.Plots.resize('hero-gauge-plot');
            }
          });
        });

        // Render verdict
        InterpretationsModule.renderVerdict('verdict-container', data.overall);

        // Render hawk score number in hero card
        var scoreDisplay = document.getElementById('hawk-score-display');
        if (scoreDisplay) {
          scoreDisplay.textContent =
            Math.round(data.overall.hawk_score) + '/100';
        }

        // Set zone-coloured top border on hero card
        var heroCard = document.getElementById('hero-card');
        if (heroCard) {
          heroCard.style.borderTopColor =
            GaugesModule.getZoneColor(data.overall.hawk_score);
        }

        // Render "jump to calculator" link in hero
        var jumpContainer = document.getElementById('calculator-jump-link');
        if (jumpContainer) {
          var jumpLink = document.createElement('a');
          jumpLink.href = '#calculator-section';
          jumpLink.className =
            'inline-block text-sm'
            + ' text-finance-accent hover:underline mt-1';
          jumpLink.textContent =
            'See what this means for your mortgage \u2193';
          jumpContainer.appendChild(jumpLink);
        }

        // Render ASX table (currently missing from data, will show unavailable)
        InterpretationsModule.renderASXTable(
          'asx-futures-container',
          data.asx_futures || null
        );

        // Render data freshness inside hero card
        InterpretationsModule.renderStalenessWarning(
          'hero-freshness', data.generated_at
        );

        // Render individual metric gauges
        renderMetricGauges(data.gauges);

        // Render placeholder cards for missing indicators
        if (data.metadata && Array.isArray(data.metadata.indicators_missing)) {
          var gridContainer = document.getElementById('metric-gauges-grid');
          if (gridContainer) {
            renderMissingIndicatorCards(
              gridContainer,
              data.metadata.indicators_missing,
              data.weights || {}
            );
          }
        }

        // Render calculator bridge text
        renderCalculatorBridge(data.overall.hawk_score, data.overall.zone_label);

        // Animate hero card entry (only on success, respect reduced motion)
        var reducedMotion = window.matchMedia(
          '(prefers-reduced-motion: reduce)'
        ).matches;
        if (heroCard && !reducedMotion) {
          heroCard.classList.add('hero-animate-in');
        }
      })
      .catch(function (err) {
        console.error('Gauge initialization failed:', err);
        DataModule.showError(
          'hero-gauge-plot',
          'Unable to load economic data.'
          + ' Please refresh the page.'
        );
      });
  }

  /**
   * Debounced resize handler for all Plotly gauges.
   */
  function setupResizeHandler() {
    window.addEventListener('resize', function () {
      if (resizeTimer) clearTimeout(resizeTimer);
      resizeTimer = setTimeout(function () {
        var heroEl = document.getElementById('hero-gauge-plot');
        if (heroEl && heroEl.data) {
          Plotly.relayout('hero-gauge-plot', { autosize: true });
        }
        renderedMetricIds.forEach(function (id) {
          var el = document.getElementById('gauge-' + id);
          if (el && el.data) {
            Plotly.relayout(el, { autosize: true });
          }
        });
      }, 250);
    });
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      initGauges();
      setupResizeHandler();
    });
  } else {
    initGauges();
    setupResizeHandler();
  }
})();
