/**
 * ChartModule - Plotly.js chart with dark theme, timeframe toggles, and rate change annotations.
 * Uses safe DOM methods throughout.
 */
var ChartModule = (function () {
  'use strict';

  /**
   * Create Plotly layout object for dark finance theme.
   * @returns {Object} Plotly layout configuration
   */
  function createDarkLayout() {
    return {
      template: 'plotly_dark',
      paper_bgcolor: '#0a0a0a',
      plot_bgcolor: '#0a0a0a',
      font: {
        color: '#e5e5e5',
        family: 'Inter, system-ui, sans-serif'
      },
      xaxis: {
        gridcolor: '#2d2d2d',
        type: 'date',
        rangeslider: { visible: false }
      },
      yaxis: {
        gridcolor: '#2d2d2d',
        title: { text: 'Cash Rate (%)' },
        ticksuffix: '%',
        zeroline: false
      },
      hovermode: 'x unified',
      margin: { t: 40, r: 20, b: 60, l: 60 },
      autosize: true
    };
  }

  /**
   * Create rangeselector buttons for timeframe toggles.
   * @returns {Object} Plotly rangeselector configuration
   */
  function createTimeframeButtons() {
    return {
      buttons: [
        { count: 1, label: '1Y', step: 'year', stepmode: 'backward' },
        { count: 5, label: '5Y', step: 'year', stepmode: 'backward' },
        { count: 10, label: '10Y', step: 'year', stepmode: 'backward' },
        { step: 'all', label: 'All' }
      ],
      bgcolor: '#2d2d2d',
      activecolor: '#60a5fa',
      bordercolor: '#3d3d3d',
      borderwidth: 1,
      font: { color: '#e5e5e5', size: 12 },
      x: 0,
      y: 1.12
    };
  }

  /**
   * Generate shapes and annotations for rate change events.
   * @param {Array} rateChanges - Array of rate change objects
   * @returns {{shapes: Array, annotations: Array}}
   */
  function addRateChangeAnnotations(rateChanges) {
    if (!rateChanges || !rateChanges.length) {
      return { shapes: [], annotations: [] };
    }

    var shapes = [];
    var annotations = [];

    rateChanges.forEach(function (change) {
      var color = change.direction === 'up' ? '#ef4444' : '#10b981';

      shapes.push({
        type: 'line',
        yref: 'paper',
        y0: 0,
        y1: 1,
        xref: 'x',
        x0: change.date,
        x1: change.date,
        line: {
          color: color,
          width: 1,
          dash: 'dot'
        },
        opacity: 0.5
      });

      var sign = change.direction === 'up' ? '+' : '-';
      annotations.push({
        x: change.date,
        y: 0.97,
        yref: 'paper',
        text: sign + change.amount.toFixed(2) + '%',
        showarrow: false,
        font: {
          color: color,
          size: 10
        },
        bgcolor: 'rgba(10,10,10,0.8)',
        borderpad: 3
      });
    });

    return { shapes: shapes, annotations: annotations };
  }

  /**
   * Create the rate history chart.
   * @param {string} containerId - Target element ID
   * @param {Object} rateData - Rate data from rates.json
   */
  function create(containerId, rateData) {
    var container = document.getElementById(containerId);
    if (!container) return;

    // Clear loading placeholder
    while (container.firstChild) {
      container.removeChild(container.firstChild);
    }

    var trace = {
      x: rateData.history.dates,
      y: rateData.history.rates,
      type: 'scatter',
      mode: 'lines',
      line: {
        color: '#60a5fa',
        width: 2,
        shape: 'hv'
      },
      name: 'Cash Rate',
      hovertemplate: '%{y:.2f}%<extra>RBA Cash Rate</extra>'
    };

    var layout = createDarkLayout();
    layout.xaxis.rangeselector = createTimeframeButtons();

    // Add rate change annotations
    var rateAnnotations = addRateChangeAnnotations(rateData.rate_changes);
    layout.shapes = rateAnnotations.shapes;
    layout.annotations = rateAnnotations.annotations;

    var config = {
      responsive: true,
      displayModeBar: true,
      displaylogo: false,
      modeBarButtonsToRemove: ['select2d', 'lasso2d', 'autoScale2d']
    };

    Plotly.newPlot(containerId, [trace], layout, config);
  }

  /**
   * Resize chart to fit container (for orientation changes).
   * @param {string} containerId - Target element ID
   */
  function resize(containerId) {
    var el = document.getElementById(containerId);
    if (el && el.data) {
      Plotly.Plots.resize(el);
    }
  }

  return {
    create: create,
    resize: resize
  };
})();
