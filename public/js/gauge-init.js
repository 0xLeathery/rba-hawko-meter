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
  /** @type {Array<{id: string, history: Array, color: string}>} */
  var sparklineRegistry = [];

  /**
   * Render hero hawk-score delta (DELT-02).
   * Inserts #hero-delta between #hawk-score-display and #scale-explainer.
   * Absent when hawk_score_delta is missing (cold start / DELT-04).
   * @param {Object} overall - data.overall from status.json
   * @param {boolean} reducedMotion
   */
  function renderHeroDelta(overall, reducedMotion) {
    var existing = document.getElementById('hero-delta');
    if (existing) existing.parentNode.removeChild(existing);

    if (!overall || overall.hawk_score_delta == null) return;

    var delta = Number(overall.hawk_score_delta);
    if (!isFinite(delta)) return;

    var scoreDisplay = document.getElementById('hawk-score-display');
    var scaleExplainer = document.getElementById('scale-explainer');
    if (!scoreDisplay || !scaleExplainer || !scoreDisplay.parentNode) return;

    var el = document.createElement('div');
    el.id = 'hero-delta';
    el.className = 'text-base text-center mt-2';
    if (!reducedMotion) {
      el.classList.add('hero-animate-in');
    }

    if (delta === 0) {
      el.className += ' text-gray-500';
      el.textContent = 'No change since last update';
    } else {
      var arrow = delta > 0 ? '\u25B2' : '\u25BC';
      var absVal = Math.abs(delta).toFixed(1);
      var sign = delta > 0 ? '+' : '\u2212';

      var coloured = document.createElement('span');
      coloured.style.color = GaugesModule.getZoneColor(overall.hawk_score);
      coloured.textContent = arrow + ' ' + sign + absVal;

      var suffix = document.createElement('span');
      suffix.className = 'text-gray-400';
      suffix.textContent = ' since last update';

      el.appendChild(coloured);
      el.appendChild(suffix);
      el.setAttribute(
        'aria-label',
        'Hawk score '
          + (delta > 0 ? 'increased' : 'decreased')
          + ' by ' + absVal + ' points since last update'
      );
    }

    scoreDisplay.parentNode.insertBefore(el, scaleExplainer);
  }

  /**
   * Fill sparkline host: canvas draw or "Building history..." placeholder.
   * @param {string} metricId
   * @param {Object} metricData
   */
  function renderSparklineForMetric(metricId, metricData) {
    var host = document.getElementById('sparkline-' + metricId);
    if (!host) return;
    host.textContent = '';

    var history = metricData && metricData.history;
    var values = (typeof SparklineModule !== 'undefined'
      && SparklineModule.numericHistory)
      ? SparklineModule.numericHistory(history)
      : [];
    var color = GaugesModule.getZoneColor(metricData.value);

    if (values.length < 3) {
      // SPRK-03
      host.className =
        'w-full mt-1 mb-1 flex items-center justify-center';
      host.style.height = '40px';
      var ph = document.createElement('p');
      ph.className = 'text-xs text-gray-500 italic';
      ph.textContent = 'Building history...';
      host.appendChild(ph);
      return;
    }

    host.className = 'w-full mt-1 mb-1';
    host.style.height = '';
    var canvas = document.createElement('canvas');
    canvas.setAttribute('aria-hidden', 'true');
    canvas.className = 'w-full block';
    host.appendChild(canvas);

    var drawn = false;
    if (typeof SparklineModule !== 'undefined' && SparklineModule.draw) {
      drawn = SparklineModule.draw(canvas, values, color);
    }
    if (drawn) {
      sparklineRegistry.push({
        id: metricId,
        history: values,
        color: color
      });
    }
  }

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
    sparklineRegistry = [];

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

      // Staggered rendering for bullet gauges + sparklines (need layout width)
      requestAnimationFrame(function () {
        GaugesModule.createBulletGauge('gauge-' + metricId, metricData);
        renderSparklineForMetric(metricId, metricData);
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
        // Check reduced motion once for all animations (Phase 23)
        var reducedMotion = window.matchMedia(
          '(prefers-reduced-motion: reduce)'
        ).matches;

        // Render hero gauge wrapped in rAF to prevent zero-width after DOM restructure
        requestAnimationFrame(function () {
          if (reducedMotion) {
            GaugesModule.createHeroGauge('hero-gauge-plot', data.overall.hawk_score);
          } else {
            GaugesModule.createHeroGaugeAnimated(
              'hero-gauge-plot', data.overall.hawk_score
            );
          }
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

        // Render hawk score with CountUp animation (ANIM-01)
        var scoreDisplay = document.getElementById('hawk-score-display');
        if (scoreDisplay) {
          var hawkScore = data.overall.hawk_score;
          if (reducedMotion || typeof countUp === 'undefined'
              || typeof countUp.CountUp !== 'function') {
            // Static fallback: reduced motion or CDN failure
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

        // Hero hawk score delta (Phase 25 / DELT-02)
        renderHeroDelta(data.overall, reducedMotion);

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

        // Render verdict explanation section (Phase 22)
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
   * Debounced resize handler for Plotly gauges and Canvas sparklines.
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
        // Redraw sparklines at new card widths
        sparklineRegistry.forEach(function (entry) {
          var host = document.getElementById('sparkline-' + entry.id);
          if (!host) return;
          var canvas = host.querySelector('canvas');
          if (!canvas || typeof SparklineModule === 'undefined') return;
          SparklineModule.draw(canvas, entry.history, entry.color);
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
