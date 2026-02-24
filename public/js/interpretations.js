/**
 * InterpretationsModule - Verdict rendering, ASX futures table, metric interpretations.
 * Uses safe DOM methods throughout (createElement/textContent only).
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
   * Create a stacked traffic-light probability bar.
   * @param {number} probCut - Cut probability (0-100)
   * @param {number} probHold - Hold probability (0-100)
   * @param {number} probHike - Hike probability (0-100)
   * @returns {HTMLElement} Stacked bar container element
   */
  function createStackedBar(probCut, probHold, probHike) {
    var TRAFFIC_COLORS = {
      cut: '#10b981',
      hold: '#f59e0b',
      hike: '#ef4444'
    };

    var bar = document.createElement('div');
    bar.className = 'flex rounded overflow-hidden w-full';
    bar.style.height = '16px';
    bar.style.minWidth = '120px';

    var segments = [
      { prob: probCut, color: TRAFFIC_COLORS.cut },
      { prob: probHold, color: TRAFFIC_COLORS.hold },
      { prob: probHike, color: TRAFFIC_COLORS.hike }
    ];

    segments.forEach(function (seg) {
      if (seg.prob > 0) {
        var div = document.createElement('div');
        div.style.flex = String(seg.prob);
        div.style.backgroundColor = seg.color;
        bar.appendChild(div);
      }
    });

    return bar;
  }

  /**
   * Render ASX Futures multi-meeting probability table with traffic light stacked bars.
   * @param {string} containerId - DOM element ID
   * @param {Object|null} asxData - { current_rate, meetings[], data_date, ... }
   */
  function renderASXTable(containerId, asxData) {
    var TRAFFIC_COLORS = {
      cut: '#10b981',
      hold: '#f59e0b',
      hike: '#ef4444'
    };

    var container = document.getElementById(containerId);
    if (!container) return;
    container.textContent = '';
    container.style.display = '';

    var heading = document.createElement('h3');
    heading.className = 'text-lg font-semibold text-gray-200 mb-3';
    heading.textContent = 'What Markets Expect';
    container.appendChild(heading);

    if (!asxData || !asxData.meetings || asxData.meetings.length === 0) {
      var placeholder = document.createElement('p');
      placeholder.className = 'text-sm text-gray-500 italic';
      placeholder.textContent = 'Market futures data currently unavailable';
      container.appendChild(placeholder);
      return;
    }

    if (asxData.current_rate != null) {
      var currentRate = document.createElement('p');
      currentRate.className = 'text-xs text-gray-400 mb-3';
      currentRate.textContent = 'Current cash rate: ' + asxData.current_rate.toFixed(2) + '%';
      container.appendChild(currentRate);
    }

    var subline = document.createElement('p');
    subline.className = 'text-xs text-gray-500 mb-3';
    subline.textContent = 'Based on ASX 30 Day Interbank Cash Rate Futures pricing';
    container.appendChild(subline);

    var scrollWrapper = document.createElement('div');
    scrollWrapper.className = 'overflow-x-auto';

    var table = document.createElement('table');
    table.className = 'w-full text-sm';
    table.style.minWidth = '480px';

    var thead = document.createElement('thead');
    var headRow = document.createElement('tr');

    var columns = [
      { text: 'Meeting', style: null },
      { text: 'Implied Rate', style: null },
      { text: 'Change', style: null },
      { text: 'Probability', style: 'minWidth:180px' }
    ];

    columns.forEach(function (col) {
      var th = document.createElement('th');
      th.className = 'text-left py-2 text-gray-400 font-medium';
      th.textContent = col.text;
      if (col.style) {
        th.style.minWidth = '180px';
      }
      headRow.appendChild(th);
    });

    thead.appendChild(headRow);
    table.appendChild(thead);

    var tbody = document.createElement('tbody');

    asxData.meetings.forEach(function (meeting, index) {
      var row = document.createElement('tr');
      row.className = 'border-b border-finance-border/50';

      if (index === 0) {
        row.className += ' border-l-2 border-finance-accent';
        row.style.backgroundColor = 'rgba(26, 26, 26, 0.5)';
      }

      // Meeting date cell
      var dateCell = document.createElement('td');
      dateCell.className = 'py-2 pl-2 text-gray-300';
      dateCell.textContent = meeting.meeting_date_label;
      row.appendChild(dateCell);

      // Implied rate cell
      var rateCell = document.createElement('td');
      rateCell.className = 'py-2 text-gray-300 font-mono';
      rateCell.textContent = meeting.implied_rate.toFixed(2) + '%';
      row.appendChild(rateCell);

      // Change cell with sign and color
      var changeCell = document.createElement('td');
      changeCell.className = 'py-2 font-mono';
      var changeBp = meeting.change_bp;
      var changeText = (changeBp >= 0 ? '+' : '') + changeBp.toFixed(1) + 'bp';
      changeCell.textContent = changeText;
      if (changeBp < -5) {
        changeCell.style.color = '#10b981';
      } else if (changeBp > 5) {
        changeCell.style.color = '#ef4444';
      } else {
        changeCell.style.color = '#9ca3af';
      }
      row.appendChild(changeCell);

      // Probability cell: stacked bar + label
      var probCell = document.createElement('td');
      probCell.className = 'py-2';

      var probCut = meeting.probability_cut;
      var probHold = meeting.probability_hold;
      var probHike = meeting.probability_hike;

      var stackedBar = createStackedBar(probCut, probHold, probHike);
      probCell.appendChild(stackedBar);

      // Percentage labels below bar
      var labelParts = [];
      if (probCut > 0) {
        labelParts.push({ text: Math.round(probCut) + '% cut', color: TRAFFIC_COLORS.cut });
      }
      if (probHold > 0) {
        labelParts.push({ text: Math.round(probHold) + '% hold', color: TRAFFIC_COLORS.hold });
      }
      if (probHike > 0) {
        labelParts.push({ text: Math.round(probHike) + '% hike', color: TRAFFIC_COLORS.hike });
      }

      var labelP = document.createElement('p');
      labelP.className = 'text-xs text-gray-500 mt-1';

      labelParts.forEach(function (part, i) {
        if (i > 0) {
          var dot = document.createTextNode(' \u00b7 ');
          labelP.appendChild(dot);
        }
        var span = document.createElement('span');
        span.style.color = part.color;
        span.textContent = part.text;
        labelP.appendChild(span);
      });

      probCell.appendChild(labelP);
      row.appendChild(probCell);
      tbody.appendChild(row);
    });

    table.appendChild(tbody);
    scrollWrapper.appendChild(table);
    container.appendChild(scrollWrapper);

    // Legend row
    var legend = document.createElement('div');
    legend.className = 'flex gap-4 mt-2 text-xs text-gray-500';

    var legendItems = [
      { color: TRAFFIC_COLORS.cut, label: 'Cut' },
      { color: TRAFFIC_COLORS.hold, label: 'Hold' },
      { color: TRAFFIC_COLORS.hike, label: 'Hike' }
    ];

    legendItems.forEach(function (item) {
      var itemDiv = document.createElement('div');

      var dot = document.createElement('span');
      dot.style.display = 'inline-block';
      dot.style.width = '8px';
      dot.style.height = '8px';
      dot.style.borderRadius = '50%';
      dot.style.backgroundColor = item.color;
      dot.style.marginRight = '4px';
      dot.style.verticalAlign = 'middle';

      var labelNode = document.createTextNode(item.label);

      itemDiv.appendChild(dot);
      itemDiv.appendChild(labelNode);
      legend.appendChild(itemDiv);
    });

    container.appendChild(legend);

    // "Data as of" footer — always visible
    var footer = document.createElement('p');
    footer.className = 'text-xs text-gray-500 mt-3';
    footer.textContent = 'Data as of ' + formatAusDate(asxData.data_date);
    container.appendChild(footer);
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
   * Convert ISO date string to quarter format label.
   * @param {string} isoDateStr - ISO 8601 date string (e.g. "2021-10-01")
   * @returns {string} Quarter label e.g. "(Q4 2021)" or empty string if invalid
   */
  function toQuarterLabel(isoDateStr) {
    if (!isoDateStr) return '';
    var d = new Date(isoDateStr);
    if (isNaN(d.getTime())) return '';
    var q = Math.ceil((d.getMonth() + 1) / 3);
    return '(Q' + q + ' ' + d.getFullYear() + ')';
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
        var direction, sign;
        var rawNum = parseFloat(raw);
        // Neutral zone: +/-1% per research recommendation
        if (isNaN(rawNum) || (rawNum > -1 && rawNum < 1)) {
          direction = 'STEADY';
          sign = '';
        } else if (rawNum >= 1) {
          direction = 'RISING';
          sign = '+';
        } else {
          direction = 'FALLING';
          sign = '';
        }
        var quarterLabel = toQuarterLabel(metricData.data_date);
        return direction + ' ' + sign + raw + '% year-on-year ' + quarterLabel;

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
    // Housing: quarter-only staleness — suppress amber border per CONTEXT.md
    if (metricId === 'housing' && metricData.stale_display === 'quarter_only') {
      stale = false;
    }

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

    // Source attribution for housing
    if (metricId === 'housing' && metricData.data_source) {
      var srcAttr = document.createElement('div');
      srcAttr.className = 'text-xs text-gray-500 mt-1';
      srcAttr.textContent = 'Source: ' + metricData.data_source;
      card.appendChild(srcAttr);
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
    isDataSuspect: isDataSuspect,
    toQuarterLabel: toQuarterLabel
  };
})();
