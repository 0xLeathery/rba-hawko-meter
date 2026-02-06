/**
 * GaugesModule - Plotly gauge rendering for Hawk-O-Meter.
 * Creates hero semicircle gauge and bullet gauges with 5-zone Blue/Grey/Red color scheme.
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
    business_confidence: 'Capacity'
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
      title: {
        text: getStanceLabel(hawkScore),
        font: { size: 20, color: getZoneColor(hawkScore) }
      },
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
   * Efficiently update the hero gauge value.
   * @param {string} containerId - DOM element ID
   * @param {number} hawkScore - New hawk score 0-100
   */
  function updateHeroGauge(containerId, hawkScore) {
    var trace = {
      type: 'indicator',
      mode: 'gauge+number',
      value: hawkScore,
      title: {
        text: getStanceLabel(hawkScore),
        font: { size: 20, color: getZoneColor(hawkScore) }
      },
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
   * Create a compact horizontal bullet gauge for an individual metric.
   * @param {string} containerId - DOM element ID
   * @param {Object} metricData - { value, weight, staleness_days, confidence }
   */
  function createBulletGauge(containerId, metricData) {
    var trace = {
      type: 'indicator',
      mode: 'number+gauge',
      value: metricData.value,
      number: {
        font: { size: 24, color: '#f3f4f6' },
        valueformat: '.0f',
        suffix: '/100'
      },
      gauge: {
        shape: 'bullet',
        axis: { range: [0, 100], dtick: 20 },
        bar: { color: getZoneColor(metricData.value), thickness: 0.5 },
        bgcolor: '#1f2937',
        borderwidth: 0,
        steps: getGaugeSteps(),
        threshold: {
          line: { color: '#fbbf24', width: 2 },
          thickness: 0.75,
          value: 50
        }
      },
      domain: { x: [0.05, 0.95], y: [0.15, 0.85] }
    };

    var layout = getDarkLayout({
      height: 80,
      margin: { t: 0, r: 40, l: 10, b: 0 }
    });

    var config = { responsive: true, displayModeBar: false, staticPlot: true };

    Plotly.newPlot(containerId, [trace], layout, config);
  }

  /**
   * Efficiently update a bullet gauge value.
   * @param {string} containerId - DOM element ID
   * @param {number} gaugeValue - New gauge value 0-100
   */
  function updateBulletGauge(containerId, gaugeValue) {
    Plotly.react(containerId, [{
      type: 'indicator',
      mode: 'number+gauge',
      value: gaugeValue,
      number: {
        font: { size: 24, color: '#f3f4f6' },
        valueformat: '.0f',
        suffix: '/100'
      },
      gauge: {
        shape: 'bullet',
        axis: { range: [0, 100], dtick: 20 },
        bar: { color: getZoneColor(gaugeValue), thickness: 0.5 },
        bgcolor: '#1f2937',
        borderwidth: 0,
        steps: getGaugeSteps(),
        threshold: {
          line: { color: '#fbbf24', width: 2 },
          thickness: 0.75,
          value: 50
        }
      },
      domain: { x: [0.05, 0.95], y: [0.15, 0.85] }
    }]);
  }

  return {
    getZoneColor: getZoneColor,
    getStanceLabel: getStanceLabel,
    getDisplayLabel: getDisplayLabel,
    createHeroGauge: createHeroGauge,
    updateHeroGauge: updateHeroGauge,
    createBulletGauge: createBulletGauge,
    updateBulletGauge: updateBulletGauge
  };
})();
