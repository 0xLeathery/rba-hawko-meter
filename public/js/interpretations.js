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

  var ausDateFormatter = new Intl.DateTimeFormat('en-AU', {
    day: 'numeric', month: 'short', year: 'numeric'
  });

  /**
   * Check if metric data contains suspect/bogus values.
   * @param {string} metricId - Metric identifier
   * @param {Object} metricData - Metric data object
   * @returns {boolean} True if data is suspect
   */
  function isDataSuspect(metricId, metricData) {
    if (metricId === 'building_approvals') {
      var raw = parseFloat(metricData.raw_value);
      if (isNaN(raw) || raw < -90 || raw > 500) return true;
    }
    return false;
  }

  /**
   * Format ISO date string as Australian format (1 Dec 2025).
   * @param {string} isoDateStr - ISO 8601 date string
   * @returns {string} Formatted date
   */
  function formatAusDate(isoDateStr) {
    if (!isoDateStr) return 'unknown';
    var d = new Date(isoDateStr);
    if (isNaN(d.getTime())) return isoDateStr;
    return ausDateFormatter.format(d);
  }

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
    var plainVerdict = getPlainVerdict(overallData.hawk_score);
    dashSpan.textContent = ' \u2014 ' + plainVerdict;

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

    if (!asxData || !asxData.probabilities) {
      container.style.display = 'none';
      return;
    }

    container.style.display = '';

    var heading = document.createElement('h3');
    heading.className = 'text-lg font-semibold text-gray-200 mb-3';
    heading.textContent = 'What Markets Expect';
    container.appendChild(heading);

    var subline = document.createElement('p');
    subline.className = 'text-xs text-gray-500 mb-3';
    subline.textContent = 'Based on ASX 30 Day Interbank Cash Rate Futures pricing';
    container.appendChild(subline);

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
    // Data quality guard
    if (isDataSuspect(metricId, metricData)) {
      return 'Building approvals data is currently being updated';
    }

    var v = metricData.value;
    var raw = metricData.raw_value != null ? parseFloat(metricData.raw_value).toFixed(1) : '?';

    switch (metricId) {
      case 'inflation':
        if (v < 40) return 'Prices up ' + raw + '% over the past year \u2014 within the RBA\'s 2\u20133% target';
        if (v <= 60) return 'Prices up ' + raw + '% over the past year \u2014 near the top of the RBA\'s 2\u20133% target';
        return 'Prices up ' + raw + '% over the past year \u2014 above the RBA\'s 2\u20133% target';

      case 'wages':
        if (v < 40) return 'Wages up ' + raw + '% over the past year \u2014 growing slowly';
        if (v <= 60) return 'Wages up ' + raw + '% over the past year \u2014 moderate growth';
        return 'Wages up ' + raw + '% over the past year \u2014 growing fast, which can push up prices';

      case 'building_approvals':
        if (v < 40) return 'New building approvals are below average \u2014 a sign of slowing construction';
        if (v <= 60) return 'New building approvals are near average levels';
        return 'New building approvals are above average \u2014 a sign of strong construction demand';

      case 'housing':
        if (v < 40) return 'House prices are easing \u2014 less pressure on affordability';
        if (v <= 60) return 'House prices are growing at a moderate pace';
        return 'House prices are rising strongly \u2014 adding to affordability pressure';

      case 'employment':
        if (v < 40) return 'The job market is softening \u2014 fewer new jobs being created';
        if (v <= 60) return 'The job market is steady \u2014 balanced conditions';
        return 'The job market is very tight \u2014 lots of demand for workers, which can push up wages';

      case 'spending':
        if (v < 40) return 'Consumer spending is subdued \u2014 people are holding back';
        if (v <= 60) return 'Consumer spending is at moderate levels';
        return 'Consumer spending is strong \u2014 which can push up prices';

      case 'business_confidence':
        if (v < 40) return 'Business confidence is below average \u2014 businesses are cautious';
        if (v <= 60) return 'Business confidence is around average levels';
        return 'Business confidence is high \u2014 businesses are investing and hiring more';

      default:
        return metricData.interpretation || GaugesModule.getDisplayLabel(metricId);
    }
  }

  /**
   * Get plain English explanation for why this indicator matters.
   * @param {string} metricId - Metric identifier
   * @returns {string|null} Explanation text or null
   */
  function getWhyItMatters(metricId) {
    var reasons = {
      inflation: 'When prices rise too fast, the RBA tends to raise interest rates to slow things down.',
      wages: 'Rising wages can push up prices, which can lead the RBA to raise rates.',
      building_approvals: 'Fewer approvals signals a slowing economy, which may support rate cuts.',
      housing: 'Rapidly rising house prices can prompt the RBA to raise rates to cool the market.',
      employment: 'Low unemployment means a strong economy, which can lead to rate rises.',
      spending: 'When consumers spend more, it can push prices up and lead to rate rises.',
      business_confidence: 'When businesses are confident, they invest and hire more, adding to inflation pressure.'
    };
    return reasons[metricId] || null;
  }

  /**
   * Get plain English verdict text based on hawk score.
   * @param {number} score - Overall hawk score (0-100)
   * @returns {string} ASIC-compliant verdict text
   */
  function getPlainVerdict(score) {
    if (score < 20) {
      return 'The economy is showing significant signs of slowing. Interest rates are more likely to come down.';
    }
    if (score < 40) {
      return 'The economy is showing some signs of easing. Interest rates may be more likely to fall than rise.';
    }
    if (score <= 60) {
      return 'The economy is giving mixed signals. Interest rates are likely to stay where they are for now.';
    }
    if (score <= 80) {
      return 'The economy is running warm. Interest rates may be more likely to rise than fall.';
    }
    return 'The economy is running hot. Interest rates are more likely to go up.';
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
    var pct = Math.round(weight * 100);
    var importanceLabel;
    if (pct >= 20) importanceLabel = 'High importance';
    else if (pct >= 10) importanceLabel = 'Medium importance';
    else importanceLabel = 'Lower importance';
    weightBadge.textContent = importanceLabel;
    weightBadge.title = pct + '% of overall score';

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

    // Why it matters one-liner
    var whyText = getWhyItMatters(metricId);
    if (whyText) {
      var whyDiv = document.createElement('div');
      whyDiv.className = 'text-xs text-gray-500 mt-1 italic';
      whyDiv.textContent = whyText;
      card.appendChild(whyDiv);
    }

    // Source citation with Australian date format
    var sourceDiv = document.createElement('div');
    sourceDiv.className = 'text-xs text-gray-600 mt-2';
    sourceDiv.textContent = 'Data as of ' + formatAusDate(metricData.data_date);
    if (stale) {
      var months = Math.round(metricData.staleness_days / 30);
      var staleNote = document.createElement('span');
      staleNote.className = 'text-amber-400 ml-2';
      staleNote.textContent = '(' + months + ' month' + (months !== 1 ? 's' : '') + ' old \u2014 newer data not yet available)';
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
    renderMetricCard: renderMetricCard,
    getWhyItMatters: getWhyItMatters,
    getPlainVerdict: getPlainVerdict,
    formatAusDate: formatAusDate,
    isDataSuspect: isDataSuspect
  };
})();
