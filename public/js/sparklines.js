/**
 * SparklineModule - Canvas 2D sparklines for indicator cards.
 * Stroke-only line with end-dot; zone colour from caller.
 * Uses safe DOM methods only (no innerHTML).
 */
var SparklineModule = (function () {
  'use strict';

  var DEFAULTS = {
    lineWidth: 1.5,
    dotRadius: 3,
    padding: 2,
    height: 40
  };

  /**
   * Filter history to finite numbers.
   * @param {Array} historyArray
   * @returns {Array<number>}
   */
  function numericHistory(historyArray) {
    if (!Array.isArray(historyArray)) return [];
    var out = [];
    for (var i = 0; i < historyArray.length; i++) {
      var n = Number(historyArray[i]);
      if (isFinite(n)) out.push(n);
    }
    return out;
  }

  /**
   * Map values to canvas Y coordinates (padded).
   * Narrow ranges are intentionally exaggerated (min/max of series).
   * @param {Array<number>} values
   * @param {number} height
   * @param {number} padding
   * @returns {Array<number>} y positions top-down
   */
  function toYCoords(values, height, padding) {
    var min = values[0];
    var max = values[0];
    for (var i = 1; i < values.length; i++) {
      if (values[i] < min) min = values[i];
      if (values[i] > max) max = values[i];
    }
    var span = max - min;
    var usable = height - padding * 2;
    var ys = [];
    for (var j = 0; j < values.length; j++) {
      var t = span === 0 ? 0.5 : (values[j] - min) / span;
      // Canvas y grows downward; higher gauge value → higher on chart
      ys.push(padding + usable * (1 - t));
    }
    return ys;
  }

  /**
   * Draw a sparkline into a canvas element.
   * @param {HTMLCanvasElement} canvasElement
   * @param {Array} historyArray - gauge history values (0-100)
   * @param {string} color - stroke/dot colour (hex)
   * @param {Object} [options] - lineWidth, dotRadius, padding, height
   * @returns {boolean} true if drawn, false if skipped
   */
  function draw(canvasElement, historyArray, color, options) {
    if (!canvasElement || !canvasElement.getContext) return false;

    var opts = options || {};
    var lineWidth = opts.lineWidth != null ? opts.lineWidth : DEFAULTS.lineWidth;
    var dotRadius = opts.dotRadius != null ? opts.dotRadius : DEFAULTS.dotRadius;
    var padding = opts.padding != null ? opts.padding : DEFAULTS.padding;
    var height = opts.height != null ? opts.height : DEFAULTS.height;

    var values = numericHistory(historyArray);
    if (values.length < 3) return false;

    var logicalWidth = canvasElement.offsetWidth || canvasElement.clientWidth;
    if (!logicalWidth || logicalWidth < 1) {
      // Parent may not be laid out yet
      logicalWidth = canvasElement.parentElement
        ? canvasElement.parentElement.clientWidth
        : 0;
    }
    if (!logicalWidth || logicalWidth < 1) return false;

    var dpr = window.devicePixelRatio || 1;
    canvasElement.width = Math.round(logicalWidth * dpr);
    canvasElement.height = Math.round(height * dpr);
    canvasElement.style.width = logicalWidth + 'px';
    canvasElement.style.height = height + 'px';

    var ctx = canvasElement.getContext('2d');
    if (!ctx) return false;
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, logicalWidth, height);

    var ys = toYCoords(values, height, padding);
    var n = values.length;
    var stepX = n === 1 ? 0 : (logicalWidth - padding * 2) / (n - 1);

    ctx.beginPath();
    ctx.strokeStyle = color || '#6b7280';
    ctx.lineWidth = lineWidth;
    ctx.lineJoin = 'round';
    ctx.lineCap = 'round';

    for (var i = 0; i < n; i++) {
      var x = padding + stepX * i;
      var y = ys[i];
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();

    // End-dot at current position
    var lastX = padding + stepX * (n - 1);
    var lastY = ys[n - 1];
    ctx.beginPath();
    ctx.fillStyle = color || '#6b7280';
    ctx.arc(lastX, lastY, dotRadius, 0, Math.PI * 2);
    ctx.fill();

    return true;
  }

  return {
    draw: draw,
    // Exported for tests / callers that pre-filter
    numericHistory: numericHistory
  };
})();
