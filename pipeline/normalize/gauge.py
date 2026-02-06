"""
Gauge mapping and scoring module.

Maps Z-scores to 0-100 gauge values via [-3, +3] linear clamp, classifies
into 5 zones, and computes weighted hawk score.
"""

import json
import math

from pipeline.config import ZSCORE_CLAMP_MIN, ZSCORE_CLAMP_MAX


def zscore_to_gauge(z, clamp_min=None, clamp_max=None):
    """
    Linear map from Z-score to 0-100 gauge value.

    gauge = ((z - clamp_min) / (clamp_max - clamp_min)) * 100
    Clipped to [0, 100].

    Args:
        z: Z-score value.
        clamp_min: Lower Z-score bound (default: -3.0).
        clamp_max: Upper Z-score bound (default: +3.0).

    Returns:
        Gauge value between 0.0 and 100.0. Returns NaN if input is NaN.
    """
    if clamp_min is None:
        clamp_min = ZSCORE_CLAMP_MIN
    if clamp_max is None:
        clamp_max = ZSCORE_CLAMP_MAX

    if isinstance(z, float) and math.isnan(z):
        return float('nan')

    gauge = ((z - clamp_min) / (clamp_max - clamp_min)) * 100
    return max(0.0, min(100.0, gauge))


def classify_zone(gauge):
    """
    Classify a gauge value into one of 5 zones.

    Args:
        gauge: Gauge value between 0 and 100, or NaN.

    Returns:
        Tuple of (zone_id, zone_label).
    """
    if isinstance(gauge, float) and math.isnan(gauge):
        return ("unknown", "Insufficient data")

    if gauge < 20:
        return ("cold", "Strong dovish pressure")
    elif gauge < 40:
        return ("cool", "Mild dovish pressure")
    elif gauge < 60:
        return ("neutral", "Balanced")
    elif gauge < 80:
        return ("warm", "Mild hawkish pressure")
    else:
        return ("hot", "Strong hawkish pressure")


def apply_polarity(z, polarity):
    """
    Apply polarity to a Z-score.

    Args:
        z: Z-score value.
        polarity: +1 (standard) or -1 (inverted).

    Returns:
        Oriented Z-score.
    """
    return z * polarity


def load_weights(path):
    """
    Load and validate weights from a JSON file.

    Args:
        path: Path to weights.json.

    Returns:
        Dict of weight configurations.

    Raises:
        ValueError: If weights are invalid (negative or don't sum to ~1.0).
    """
    with open(path) as f:
        weights = json.load(f)

    total = 0.0
    for name, config in weights.items():
        w = config['weight']
        if w <= 0:
            raise ValueError(f"Weight for '{name}' must be positive, got {w}")
        total += w

    if not (0.99 <= total <= 1.01):
        raise ValueError(f"Weights must sum to ~1.0, got {total}")

    return weights


def compute_hawk_score(gauge_values, weights, exclude_benchmark=True):
    """
    Compute weighted average hawk score from gauge values.

    Rebalances weights when indicators are missing so available weights
    sum to 1.0.

    Args:
        gauge_values: Dict of {indicator_name: gauge_value}.
        weights: Dict of weight configurations (from load_weights).
        exclude_benchmark: If True, exclude 'asx_futures' from score.

    Returns:
        Hawk score between 0.0 and 100.0.
    """
    weighted_sum = 0.0
    weight_sum = 0.0

    for name, config in weights.items():
        if exclude_benchmark and name == 'asx_futures':
            continue
        if name not in gauge_values:
            continue
        weighted_sum += gauge_values[name] * config['weight']
        weight_sum += config['weight']

    if weight_sum == 0.0:
        return 50.0  # Neutral if no data

    # Rebalance: scale to account for missing indicators
    score = weighted_sum / weight_sum
    return max(0.0, min(100.0, score))


def generate_verdict(hawk_score):
    """
    Generate a plain-text verdict from the hawk score.

    Args:
        hawk_score: Overall hawk score between 0 and 100.

    Returns:
        Verdict string.
    """
    if hawk_score < 20:
        return "Economic indicators suggest strong easing pressure"
    elif hawk_score < 40:
        return "Economic indicators suggest mild easing pressure"
    elif hawk_score < 60:
        return "Economic indicators are broadly balanced"
    elif hawk_score < 80:
        return "Economic indicators suggest moderate tightening pressure"
    else:
        return "Economic indicators suggest strong tightening pressure"
