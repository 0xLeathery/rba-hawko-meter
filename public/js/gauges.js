/**
 * GaugesModule - Plotly gauge rendering for Hawk-O-Meter.
 * Creates hero and metric semicircle needle gauges
 * with 5-zone Blue/Grey/Red color scheme.
 * Uses safe DOM methods throughout (no innerHTML).
 */
var GaugesModule = (function () {
  'use strict';

  var ZONE_COLORS = [
    { range: [0, 20], color: '#1e40af', label: 'RATES LIKELY FALLING' },
    { range: [20, 40], color: '#60a5fa', label: 'LEANING TOWARDS CUTS' },
    { range: [40, 60], color: '#6b7280', label: 'HOLDING STEADY' },
    { range: [60, 80], color: '#f87171', label: 'LEANING TOWARDS RISES' },
    { range: [80, 100], color: '#dc2626', label: 'RATES LIKELY RISING' }
  ];

  var DISPLAY_LABELS = {
    inflation: 'Inflation',
    wages: 'Wages',
    employment: 'Jobs',
    housing: 'Housing',
    spending: 'Spending',
    building_approvals: 'Building Approvals',
    business_confidence: 'Business Conditions'
  };

  /**
   * Get the zone color for a given gauge value.
   * @param {number} value - Gauge value 0-100
   * @returns {string} Hex color string
   */
  function getZoneColor(value) {
    var v = Math.max(0, Math.min(100, value));
    for (var i = 0; i < ZONE_COLORS.length; i++) {
      if (v < ZONE_COLORS[i].range[1]) {
        return ZONE_COLORS[i].color;
      }
    }
    return ZONE_COLORS[ZONE_COLORS.length - 1].color;
  }

  /**
   * Get the stance label for a given gauge value.
   * @param {number} value - Gauge value 0-100
   * @returns {string} Stance label e.g. 'LEANING TOWARDS RISES'
   */
  function getStanceLabel(value) {
    var v = Math.max(0, Math.min(100, value));
    for (var i = 0; i < ZONE_COLORS.length; i++) {
      if (v < ZONE_COLORS[i].range[1]) {
        return ZONE_COLORS[i].label;
      }
    }
    return ZONE_COLORS[ZONE_COLORS.length - 1].label;
  }

  /**
   * Get Plotly gauge steps array from ZONE_COLORS.
   * @returns {Array} Plotly steps array
   */
  function getGaugeSteps() {
    return ZONE_COLORS.map(function (zone) {
      return { range: zone.range, color: zone.color };
    });
  }

  /**
   * Get dark theme Plotly layout with optional overrides.
   * @param {Object} [overrides] - Layout properties to merge
   * @returns {Object} Plotly layout object
   */
  function getDarkLayout(overrides) {
    var base = {
      paper_bgcolor: 'transparent',
      plot_bgcolor: 'transparent',
      font: { color: '#e5e5e5', family: 'Inter, system-ui, sans-serif' },
      margin: { t: 40, r: 25, l: 25, b: 0 },
      autosize: true
    };
    return Object.assign({}, base, overrides || {});
  }

  /**
   * Get display label for a metric ID.
   * @param {string} metricId
   * @returns {string} Display label
   */
  function getDisplayLabel(metricId) {
    if (DISPLAY_LABELS[metricId]) {
      return DISPLAY_LABELS[metricId];
    }
    return metricId.replace(/_/g, ' ').replace(/\b\w/g, function (c) {
      return c.toUpperCase();
    });
  }

  /**
   * Create the hero semicircle Hawk Score gauge.
   * @param {string} containerId - DOM element ID for the gauge
   * @param {number} hawkScore - Hawk score 0-100
   */
  function createHeroGauge(containerId, hawkScore) {
    // Clear container (remove loading placeholder)
    var container = document.getElementById(containerId);
    if (container) {
      while (container.firstChild) {
        container.removeChild(container.firstChild);
      }
    }

    var trace = {
      type: 'indicator',
      mode: 'gauge+number',
      value: hawkScore,
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
        bar: { color: getZoneColor(hawkScore), thickness: 0.6 },
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

    var layout = getDarkLayout();
    var config = { responsive: true, displayModeBar: false };

    Plotly.newPlot(containerId, [trace], layout, config);
  }

  /**
   * Create the hero gauge with sweep animation from 0 to live score.
   * Uses requestAnimationFrame + Plotly.react() because Plotly.animate()
   * does not smoothly transition indicator traces.
   * @param {string} containerId - DOM element ID for the gauge
   * @param {number} hawkScore - Hawk score 0-100
   */
  function createHeroGaugeAnimated(containerId, hawkScore) {
    var container = document.getElementById(containerId);
    if (container) {
      while (container.firstChild) {
        container.removeChild(container.firstChild);
      }
    }

    var animDuration = 1500;
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

    Plotly.newPlot(containerId, [buildTrace(0)], layout, config);

    requestAnimationFrame(function startAnimation() {
      requestAnimationFrame(function step(timestamp) {
        if (!startTime) startTime = timestamp;
        var elapsed = timestamp - startTime;
        var progress = Math.min(elapsed / animDuration, 1);
        var easedProgress = easeOutExpo(progress);
        var currentValue = easedProgress * hawkScore;

        Plotly.react(containerId, [buildTrace(currentValue)], layout, config);

        if (progress < 1) {
          requestAnimationFrame(step);
        }
      });
    });
  }

  /**
   * Efficiently update the hero gauge value.
   * @param {string} containerId - DOM element ID
   * @param {number} hawkScore - New hawk score 0-100
   */
  function updateHeroGauge(containerId, hawkScore) {
    var trace = {
      type: 'indicator',
      mode: 'gauge+number',
      value: hawkScore,
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
        bar: { color: getZoneColor(hawkScore), thickness: 0.6 },
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

    var layout = getDarkLayout();
    var config = { responsive: true, displayModeBar: false };

    Plotly.react(containerId, [trace], layout, config);
  }

  /**
   * Build a metric needle gauge trace (shared by create/update).
   * @param {number} value - Gauge value 0-100
   * @returns {Object} Plotly trace
   */
  function metricGaugeTrace(value) {
    return {
      type: 'indicator',
      mode: 'gauge+number',
      value: value,
      number: {
        font: { size: 28, color: '#f3f4f6' },
        valueformat: '.0f',
        suffix: '/100'
      },
      gauge: {
        shape: 'angular',
        axis: {
          range: [0, 100],
          tickwidth: 1,
          tickcolor: '#4a4a4a',
          tickfont: { size: 10, color: '#6b7280' },
          dtick: 20
        },
        bar: { color: 'rgba(0,0,0,0)', thickness: 0 },
        bgcolor: '#1f2937',
        borderwidth: 0,
        steps: getGaugeSteps(),
        threshold: {
          line: { color: '#ffffff', width: 4 },
          thickness: 0.85,
          value: value
        }
      },
      domain: { x: [0, 1], y: [0, 1] }
    };
  }

  /**
   * Create a semicircle needle gauge for an individual metric.
   * @param {string} containerId - DOM element ID
   * @param {Object} metricData - { value, weight, staleness_days, confidence }
   */
  function createBulletGauge(containerId, metricData) {
    var layout = getDarkLayout({
      height: 155,
      margin: { t: 20, r: 15, l: 15, b: 0 }
    });

    var config = { responsive: true, displayModeBar: false, staticPlot: true };

    Plotly.newPlot(containerId, [metricGaugeTrace(metricData.value)], layout, config);
  }

  /**
   * Efficiently update a metric needle gauge value.
   * @param {string} containerId - DOM element ID
   * @param {number} gaugeValue - New gauge value 0-100
   */
  function updateBulletGauge(containerId, gaugeValue) {
    Plotly.react(containerId, [metricGaugeTrace(gaugeValue)]);
  }

  return {
    getZoneColor: getZoneColor,
    getStanceLabel: getStanceLabel,
    getDisplayLabel: getDisplayLabel,
    createHeroGauge: createHeroGauge,
    createHeroGaugeAnimated: createHeroGaugeAnimated,
    updateHeroGauge: updateHeroGauge,
    createBulletGauge: createBulletGauge,
    updateBulletGauge: updateBulletGauge
  };
})();
