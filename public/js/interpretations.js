/**
 * InterpretationsModule - Verdict rendering, ASX futures table, metric interpretations.
 * Uses safe DOM methods throughout (no innerHTML).
 */
var InterpretationsModule = (function () {
  'use strict';

  var ZONE_LABEL_MAP = {
    'Strong dovish pressure': 'RATES LIKELY FALLING',
    'Mild dovish pressure': 'LEANING TOWARDS CUTS',
    'Balanced': 'HOLDING STEADY',
    'Mild hawkish pressure': 'LEANING TOWARDS RISES',
    'Strong hawkish pressure': 'RATES LIKELY RISING'
  };

  var percentFormatter = new Intl.NumberFormat('en-AU', {
    style: 'percent',
    minimumFractionDigits: 1,
    maximumFractionDigits: 1
  });

  /**
   * Render overall verdict text with colored stance label.
   * @param {string} containerId - DOM element ID
   * @param {Object|string} overallData - data.overall from status.json or plain string
   */
  function renderVerdict(containerId, overallData) {
    var container = document.getElementById(containerId);
    if (!container) return;
    container.textContent = '';

    if (typeof overallData === 'string') {
      var textSpan = document.createElement('span');
      textSpan.className = 'text-gray-300';
      textSpan.textContent = overallData;
      container.appendChild(textSpan);
      return;
    }

    var stance = ZONE_LABEL_MAP[overallData.zone_label] || overallData.zone_label || 'NEUTRAL';

    var labelSpan = document.createElement('span');
    labelSpan.className = 'font-bold';
    labelSpan.style.color = GaugesModule.getZoneColor(overallData.hawk_score);
    labelSpan.textContent = stance;

    var dashSpan = document.createElement('span');
    dashSpan.className = 'text-gray-300';
    dashSpan.textContent = ' \u2014 ' + (overallData.verdict || '');

    container.appendChild(labelSpan);
    container.appendChild(dashSpan);
  }

  /**
   * Render ASX Futures probability table.
   * @param {string} containerId - DOM element ID
   * @param {Object|null} asxData - { current_rate, implied_rate, probabilities, source, source_date, next_meeting }
   */
  function renderASXTable(containerId, asxData) {
    var container = document.getElementById(containerId);
    if (!container) return;
    container.textContent = '';

    var heading = document.createElement('h3');
    heading.className = 'text-lg font-semibold text-gray-200 mb-3';
    heading.textContent = 'ASX Futures \u2014 Next Meeting';
    container.appendChild(heading);

    if (!asxData || !asxData.probabilities) {
      var unavail = document.createElement('p');
      unavail.className = 'text-gray-500 text-sm';
      unavail.textContent = 'ASX Futures data unavailable';
      container.appendChild(unavail);
      return;
    }

    var probs = asxData.probabilities;
    var outcomes = [
      { label: 'Rate Cut (-0.25%)', prob: probs.cut, color: '#60a5fa' },
      { label: 'Hold (unchanged)', prob: probs.hold, color: '#9ca3af' },
      { label: 'Rate Hike (+0.25%)', prob: probs.hike, color: '#f87171' }
    ];

    var maxProb = Math.max(probs.cut || 0, probs.hold || 0, probs.hike || 0);

    var table = document.createElement('table');
    table.className = 'w-full text-sm';

    var thead = document.createElement('thead');
    var headRow = document.createElement('tr');
    headRow.className = 'border-b border-finance-border';

    var thOutcome = document.createElement('th');
    thOutcome.className = 'text-left py-2 text-gray-400 font-medium';
    thOutcome.textContent = 'Outcome';

    var thProb = document.createElement('th');
    thProb.className = 'text-right py-2 text-gray-400 font-medium';
    thProb.textContent = 'Probability';

    headRow.appendChild(thOutcome);
    headRow.appendChild(thProb);
    thead.appendChild(headRow);
    table.appendChild(thead);

    var tbody = document.createElement('tbody');
    outcomes.forEach(function (outcome) {
      var row = document.createElement('tr');
      row.className = 'border-b border-finance-border/50';

      var isHighest = outcome.prob === maxProb;
      if (isHighest) {
        row.style.borderLeft = '3px solid ' + outcome.color;
      }

      var labelCell = document.createElement('td');
      labelCell.className = 'py-2 pl-2';
      labelCell.style.color = isHighest ? outcome.color : '#9ca3af';
      labelCell.textContent = outcome.label;

      var probCell = document.createElement('td');
      probCell.className = 'py-2 text-right font-mono';
      probCell.style.color = isHighest ? '#f3f4f6' : '#9ca3af';
      probCell.textContent = outcome.prob != null ? percentFormatter.format(outcome.prob) : '--';

      row.appendChild(labelCell);
      row.appendChild(probCell);
      tbody.appendChild(row);
    });
    table.appendChild(tbody);
    container.appendChild(table);

    if (asxData.implied_rate != null) {
      var implied = document.createElement('p');
      implied.className = 'text-sm text-gray-400 mt-3';
      implied.textContent = 'Implied rate: ' + asxData.implied_rate.toFixed(2) + '%';
      container.appendChild(implied);
    }

    var citation = document.createElement('p');
    citation.className = 'text-xs text-gray-600 mt-1';
    citation.textContent = 'Source: ' + (asxData.source || 'ASX') +
      (asxData.source_date ? ' (' + asxData.source_date + ')' : '');
    container.appendChild(citation);
  }

  /**
   * Render a staleness/freshness warning.
   * @param {string} containerId - DOM element ID
   * @param {string} lastUpdated - ISO 8601 date string
   */
  function renderStalenessWarning(containerId, lastUpdated) {
    var container = document.getElementById(containerId);
    if (!container) return;
    container.textContent = '';

    if (!lastUpdated) return;

    var updatedDate = new Date(lastUpdated);
    var now = new Date();
    var diffMs = now - updatedDate;
    var diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    var span = document.createElement('span');

    if (diffDays > 7) {
      span.className = 'text-amber-400';
      span.textContent = 'Data is ' + diffDays + ' days old \u2014 update may be overdue';
    } else {
      span.className = 'text-gray-500';
      span.textContent = 'Updated ' + diffDays + ' day' + (diffDays !== 1 ? 's' : '') + ' ago';
    }

    container.appendChild(span);
  }

  /**
   * Generate data-driven interpretation text for a metric.
   * @param {string} metricId - Metric identifier (e.g. 'inflation')
   * @param {Object} metricData - { value, z_score, raw_value, raw_unit, data_date, staleness_days, confidence, interpretation }
   * @returns {string} Plain text interpretation
   */
  function generateMetricInterpretation(metricId, metricData) {
    var v = metricData.value;
    var raw = metricData.raw_value != null ? parseFloat(metricData.raw_value).toFixed(1) : '?';
    var unit = metricData.raw_unit || '';

    switch (metricId) {
      case 'inflation':
        if (v < 40) return 'CPI at ' + raw + unit + ' \u2014 within or below 2-3% target band';
        if (v <= 60) return 'CPI at ' + raw + unit + ' \u2014 near top of 2-3% target band';
        return 'CPI at ' + raw + unit + ' \u2014 above 2-3% target band';

      case 'wages':
        if (v < 40) return 'Wages growing ' + raw + unit + ' \u2014 subdued growth';
        if (v <= 60) return 'Wages growing ' + raw + unit + ' \u2014 moderate growth';
        return 'Wages growing ' + raw + unit + ' \u2014 strong growth adding to cost pressure';

      case 'building_approvals':
        if (v < 40) return 'Building approvals at ' + raw + unit + ' \u2014 below trend, easing construction pressure';
        if (v <= 60) return 'Building approvals at ' + raw + unit + ' \u2014 near long-run average';
        return 'Building approvals at ' + raw + unit + ' \u2014 above trend, adding to demand pressure';

      case 'housing':
        if (v < 40) return 'Housing prices at ' + raw + unit + ' \u2014 easing affordability pressure';
        if (v <= 60) return 'Housing prices at ' + raw + unit + ' \u2014 stable';
        return 'Housing prices at ' + raw + unit + ' \u2014 elevated affordability pressure';

      case 'employment':
        if (v < 40) return 'Labour market at ' + raw + unit + ' \u2014 softening conditions';
        if (v <= 60) return 'Labour market at ' + raw + unit + ' \u2014 balanced conditions';
        return 'Labour market at ' + raw + unit + ' \u2014 tight conditions adding to wage pressure';

      case 'spending':
        if (v < 40) return 'Consumer spending at ' + raw + unit + ' \u2014 subdued demand';
        if (v <= 60) return 'Consumer spending at ' + raw + unit + ' \u2014 moderate demand';
        return 'Consumer spending at ' + raw + unit + ' \u2014 strong demand adding to price pressure';

      case 'business_confidence':
        if (v < 40) return 'Business confidence at ' + raw + unit + ' \u2014 below average';
        if (v <= 60) return 'Business confidence at ' + raw + unit + ' \u2014 near long-term average';
        return 'Business confidence at ' + raw + unit + ' \u2014 above average';

      default:
        return metricData.interpretation || (GaugesModule.getDisplayLabel(metricId) + ': ' + raw + unit);
    }
  }

  /**
   * Render a complete metric card with gauge container, interpretation, weight, and source.
   * @param {string} containerId - Parent container DOM element ID
   * @param {string} metricId - Metric identifier
   * @param {Object} metricData - Gauge data from status.json
   * @param {number} weight - Weight value (0-1)
   */
  function renderMetricCard(containerId, metricId, metricData, weight) {
    var container = document.getElementById(containerId);
    if (!container) return;

    var stale = metricData.staleness_days > 90;

    var card = document.createElement('div');
    card.className = 'bg-finance-gray rounded-lg p-4 border border-finance-border';
    if (stale) {
      card.className += ' border-amber-500/50';
    }

    // Header row: label + weight badge
    var header = document.createElement('div');
    header.className = 'flex items-center justify-between mb-2';

    var label = document.createElement('h4');
    label.className = 'font-semibold text-gray-200';
    label.textContent = GaugesModule.getDisplayLabel(metricId);

    var weightBadge = document.createElement('span');
    weightBadge.className = 'text-xs text-gray-500';
    weightBadge.textContent = Math.round(weight * 100) + '% weight';

    header.appendChild(label);
    header.appendChild(weightBadge);
    card.appendChild(header);

    // Low confidence badge
    if (metricData.confidence === 'LOW') {
      var badge = document.createElement('span');
      badge.className = 'text-xs text-amber-400 mb-2 inline-block';
      badge.textContent = '(low confidence)';
      card.appendChild(badge);
    }

    // Gauge container
    var gaugeDiv = document.createElement('div');
    gaugeDiv.id = 'gauge-' + metricId;
    gaugeDiv.className = 'w-full';
    card.appendChild(gaugeDiv);

    // Interpretation text
    var interpDiv = document.createElement('div');
    interpDiv.id = 'interp-' + metricId;
    interpDiv.className = 'text-sm text-gray-400 mt-2';
    interpDiv.textContent = generateMetricInterpretation(metricId, metricData);
    card.appendChild(interpDiv);

    // Source citation
    var sourceDiv = document.createElement('div');
    sourceDiv.className = 'text-xs text-gray-600 mt-2';
    sourceDiv.textContent = 'Data as of ' + (metricData.data_date || 'unknown');
    if (stale) {
      var staleNote = document.createElement('span');
      staleNote.className = 'text-amber-400 ml-2';
      staleNote.textContent = '(stale)';
      sourceDiv.appendChild(staleNote);
    }
    card.appendChild(sourceDiv);

    container.appendChild(card);
  }

  return {
    renderVerdict: renderVerdict,
    renderASXTable: renderASXTable,
    renderStalenessWarning: renderStalenessWarning,
    generateMetricInterpretation: generateMetricInterpretation,
    renderMetricCard: renderMetricCard
  };
})();
