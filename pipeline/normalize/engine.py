"""
Normalization engine orchestrator.

Reads all available CSV data, computes gauge values for each indicator,
calculates the weighted overall hawk score, and writes the rich status.json
contract for the frontend.

Usage:
    python -m pipeline.normalize.engine
"""

import json
import math
from datetime import datetime
from pathlib import Path

import numpy as np

from pipeline.config import (
    DATA_DIR,
    INDICATOR_CONFIG,
    OPTIONAL_INDICATOR_CONFIG,
    ZSCORE_WINDOW_YEARS,
    ZSCORE_CLAMP_MIN,
    ZSCORE_CLAMP_MAX,
    WEIGHTS_FILE,
    STATUS_OUTPUT,
)
from pipeline.normalize.ratios import normalize_indicator, load_asx_futures_csv
from pipeline.normalize.zscore import compute_rolling_zscores, determine_confidence
from pipeline.normalize.gauge import (
    zscore_to_gauge,
    classify_zone,
    apply_polarity,
    load_weights,
    compute_hawk_score,
    generate_verdict,
)


def generate_interpretation(indicator_name, zone, raw_value):
    """
    Generate a factual, plain-text interpretation of an indicator's reading.

    Follows "Data, not opinion" -- no recommendations, just observations.

    Args:
        indicator_name: Indicator key (e.g. 'inflation', 'wages').
        zone: Zone ID (cold, cool, neutral, warm, hot).
        raw_value: The normalized value (e.g. YoY % change).

    Returns:
        Human-readable interpretation string.
    """
    templates = {
        'inflation': {
            'cold': 'Inflation well below long-run average',
            'cool': 'Inflation below long-run average',
            'neutral': 'Inflation near long-run average',
            'warm': 'Inflation above long-run average',
            'hot': 'Inflation significantly above long-run average',
        },
        'wages': {
            'cold': 'Wage growth well below long-run average',
            'cool': 'Wage growth below long-run average',
            'neutral': 'Wage growth near long-run average',
            'warm': 'Wage growth above long-run average',
            'hot': 'Wage growth significantly above long-run average',
        },
        'employment': {
            'cold': 'Labour market significantly looser than historical average',
            'cool': 'Labour market looser than historical average',
            'neutral': 'Labour market near historical average',
            'warm': 'Labour market tighter than historical average',
            'hot': 'Labour market significantly tighter than historical average',
        },
        'spending': {
            'cold': 'Consumer spending well below trend',
            'cool': 'Consumer spending below trend',
            'neutral': 'Consumer spending near trend',
            'warm': 'Consumer spending above trend',
            'hot': 'Consumer spending well above trend',
        },
        'building_approvals': {
            'cold': 'Building approvals well below trend',
            'cool': 'Building approvals below trend',
            'neutral': 'Building approvals near trend',
            'warm': 'Building approvals above trend',
            'hot': 'Building approvals well above trend',
        },
        'housing': {
            'cold': 'Housing prices well below trend',
            'cool': 'Housing prices below trend',
            'neutral': 'Housing prices near trend',
            'warm': 'Housing prices above trend',
            'hot': 'Housing prices well above trend',
        },
        'business_confidence': {
            'cold': 'Business confidence well below average',
            'cool': 'Business confidence below average',
            'neutral': 'Business confidence near average',
            'warm': 'Business confidence above average',
            'hot': 'Business confidence well above average',
        },
        'asx_futures': {
            'cold': 'Futures imply significant rate cuts ahead',
            'cool': 'Futures imply rate cuts ahead',
            'neutral': 'Futures imply stable rates',
            'warm': 'Futures imply rate hikes ahead',
            'hot': 'Futures imply significant rate hikes ahead',
        },
    }

    indicator_templates = templates.get(indicator_name, {})
    return indicator_templates.get(zone, f'{indicator_name} data available')


def build_gauge_entry(name, latest_row, z_df, weight_config):
    """
    Build a single gauge dict for status.json.

    Args:
        name: Indicator name.
        latest_row: Last valid row from Z-score DataFrame.
        z_df: Full Z-score DataFrame (for history extraction).
        weight_config: Weight config dict from weights.json.

    Returns:
        Dict with gauge metadata matching the status.json per-gauge schema.
    """
    polarity = weight_config.get('polarity', 1)
    oriented_z = apply_polarity(latest_row['z_score'], polarity)
    gauge_value = zscore_to_gauge(oriented_z)
    zone_id, zone_label = classify_zone(gauge_value)
    confidence = determine_confidence(int(latest_row['window_size']))

    data_date = latest_row['date']
    staleness_days = (datetime.now() - data_date).days

    interpretation = generate_interpretation(name, zone_id, latest_row['value'])

    # Extract history: last 12 valid gauge values from the Z-score series
    valid_rows = z_df.dropna(subset=['z_score']).tail(12)
    history = []
    for _, row in valid_rows.iterrows():
        hz = apply_polarity(row['z_score'], polarity)
        hg = zscore_to_gauge(hz)
        history.append(round(hg, 1))

    return {
        'value': round(gauge_value, 1),
        'zone': zone_id,
        'zone_label': zone_label,
        'z_score': round(oriented_z, 3),
        'raw_value': round(latest_row['value'], 2),
        'raw_unit': '% YoY',
        'weight': weight_config['weight'],
        'polarity': polarity,
        'data_date': data_date.strftime('%Y-%m-%d'),
        'staleness_days': staleness_days,
        'confidence': confidence,
        'interpretation': interpretation,
        'history': history,
    }


def build_asx_futures_entry():
    """
    Build the top-level asx_futures dict for status.json.

    Reads data/asx_futures.csv directly (bypasses Z-score pipeline).
    Returns the status.json asx_futures contract dict, or None if data
    unavailable.
    """
    csv_path = DATA_DIR / "asx_futures.csv"
    data = load_asx_futures_csv(csv_path)
    if data is None:
        return None

    # Determine direction from change_bp
    change_bp = data['change_bp']
    if change_bp < -5:
        direction = 'cut'
    elif change_bp > 5:
        direction = 'hike'
    else:
        direction = 'hold'

    # Compute staleness
    data_date = datetime.strptime(data['data_date'], '%Y-%m-%d')
    staleness_days = (datetime.now() - data_date).days

    # Get current cash rate from RBA data if available, otherwise use
    # implied_rate minus change as approximation
    current_rate = round(data['implied_rate'] - data['change_bp'] / 100, 2)

    entry = {
        'current_rate': current_rate,
        'next_meeting': data['meeting_date'],
        'implied_rate': round(data['implied_rate'], 2),
        'probabilities': {
            'cut': round(data['probability_cut'], 0),
            'hold': round(data['probability_hold'], 0),
            'hike': round(data['probability_hike'], 0),
        },
        'direction': direction,
        'data_date': data['data_date'],
        'staleness_days': staleness_days,
    }

    # Phase 8: add meetings array with human-readable date labels
    if 'meetings' in data:
        meetings_out = []
        for m in data['meetings']:
            dt = datetime.strptime(m['meeting_date'], '%Y-%m-%d')
            # Cross-platform day without zero-padding: str(int(day)) avoids %-d on Windows
            day = str(dt.day)
            meeting_date_label = f"{day} {dt.strftime('%b %Y')}"
            meetings_out.append({
                'meeting_date': m['meeting_date'],
                'meeting_date_label': meeting_date_label,
                'implied_rate': round(m['implied_rate'], 2),
                'change_bp': m['change_bp'],
                'probability_cut': round(m['probability_cut'], 0),
                'probability_hold': round(m['probability_hold'], 0),
                'probability_hike': round(m['probability_hike'], 0),
            })
        entry['meetings'] = meetings_out

    return entry


def process_indicator(name, config, weight_config):
    """
    Process a single indicator end-to-end: normalize -> Z-score -> gauge.

    Args:
        name: Indicator name.
        config: Indicator config dict from INDICATOR_CONFIG.
        weight_config: Weight config dict from weights.json.

    Returns:
        Tuple of (gauge_entry_dict, gauge_value) or (None, None) if data unavailable.
    """
    df = normalize_indicator(name, config)
    if df is None:
        return None, None

    if len(df) == 0:
        return None, None

    df = compute_rolling_zscores(df)

    # Get valid Z-score rows
    valid = df.dropna(subset=['z_score'])
    if len(valid) == 0:
        return None, None

    latest = valid.iloc[-1]
    entry = build_gauge_entry(name, latest, df, weight_config)

    return entry, entry['value']


def generate_status():
    """
    Main entry point: generate status.json with full contract.

    Processes all configured indicators, computes weighted hawk score,
    and writes the output JSON.

    Returns:
        The complete status dict.
    """
    weights = load_weights(WEIGHTS_FILE)
    gauges = {}
    gauge_values = {}
    missing_indicators = []

    # Process core indicators
    all_configs = list(INDICATOR_CONFIG.items()) + list(OPTIONAL_INDICATOR_CONFIG.items())
    total = len(all_configs)

    for i, (name, config) in enumerate(all_configs, 1):
        print(f"  [{i}/{total}] Processing {name}...", end=' ')

        if name not in weights:
            print("SKIP (no weight config)")
            missing_indicators.append(name)
            continue

        entry, value = process_indicator(name, config, weights[name])

        if entry is None:
            print("SKIP (no data)")
            missing_indicators.append(name)
        else:
            gauges[name] = entry
            gauge_values[name] = value
            print(f"Z={entry['z_score']:.2f}, Gauge={value:.1f}, Zone={entry['zone']}")

    # Compute overall hawk score
    hawk_score = compute_hawk_score(gauge_values, weights, exclude_benchmark=True)
    overall_zone, overall_zone_label = classify_zone(hawk_score)
    verdict = generate_verdict(hawk_score)

    # Determine overall confidence (lowest among available gauges)
    if gauges:
        confidence_order = {'LOW': 0, 'MEDIUM': 1, 'HIGH': 2}
        overall_confidence = min(
            (g['confidence'] for g in gauges.values()),
            key=lambda c: confidence_order.get(c, 0)
        )
    else:
        overall_confidence = 'LOW'

    # Build the complete status dict
    status = {
        'generated_at': datetime.utcnow().isoformat() + 'Z',
        'pipeline_version': '1.0.0',
        'overall': {
            'hawk_score': round(hawk_score, 1),
            'zone': overall_zone,
            'zone_label': overall_zone_label,
            'verdict': verdict,
            'confidence': overall_confidence,
        },
        'gauges': gauges,
        'weights': {name: cfg['weight'] for name, cfg in weights.items()},
        'metadata': {
            'window_years': ZSCORE_WINDOW_YEARS,
            'clamp_range': [ZSCORE_CLAMP_MIN, ZSCORE_CLAMP_MAX],
            'mapping': 'linear',
            'statistics': 'robust (median/MAD)',
            'indicators_available': len(gauges),
            'indicators_missing': missing_indicators,
        },
    }

    # Build ASX futures entry (top-level, not in gauges)
    asx_entry = build_asx_futures_entry()
    if asx_entry is not None:
        status['asx_futures'] = asx_entry
        # Remove asx_futures from missing indicators since we have data
        if 'asx_futures' in status['metadata']['indicators_missing']:
            status['metadata']['indicators_missing'].remove('asx_futures')
        print(f"\n  ASX Futures: implied={asx_entry['implied_rate']:.2f}%, "
              f"direction={asx_entry['direction']}, "
              f"P(cut)={asx_entry['probabilities']['cut']:.0f}%")

    # Write to output file
    STATUS_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(STATUS_OUTPUT, 'w') as f:
        json.dump(status, f, indent=2)

    print(f"\n  Hawk Score: {hawk_score:.1f} ({overall_zone_label})")
    print(f"  Indicators: {len(gauges)} available, {len(missing_indicators)} missing")
    print(f"  Output: {STATUS_OUTPUT}")

    return status


if __name__ == '__main__':
    print("RBA Hawk-O-Meter: Normalization Engine")
    print("=" * 50)
    generate_status()
