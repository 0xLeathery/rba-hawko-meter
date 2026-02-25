"""
Unit tests for pipeline.normalize.gauge.

Covers:
  - zscore_to_gauge: linear map z->gauge, clipped to [0,100], NaN passthrough
  - classify_zone: 5-zone classification at exact boundary values
  - compute_hawk_score: weighted average with rebalancing,
    empty fallback, benchmark exclusion
  - generate_verdict: threshold-based verdict strings at all 5 zones

All tests are pure math — no network access, no disk I/O to the live data/ folder.
"""

import math

import pytest

from pipeline.normalize.gauge import (
    classify_zone,
    compute_hawk_score,
    generate_verdict,
    zscore_to_gauge,
)

# =============================================================================
# zscore_to_gauge
# =============================================================================


@pytest.mark.parametrize(
    "z,expected",
    [
        (0.0, 50.0),    # Midpoint: z=0 maps to exactly 50
        (-3.0, 0.0),    # Lower clamp boundary
        (3.0, 100.0),   # Upper clamp boundary
        (1.5, 75.0),    # Three-quarters up: z=1.5 in [-3,3] range
        (-1.5, 25.0),   # One-quarter up: z=-1.5 in [-3,3] range
        (4.0, 100.0),   # Beyond upper clamp: clamped to 100
        (-4.0, 0.0),    # Beyond lower clamp: clamped to 0
    ],
)
def test_zscore_to_gauge_standard_cases(z, expected):
    """
    Linear map: gauge = ((z - (-3)) / (3 - (-3))) * 100, clipped to [0,100].
    Default clamp_min=-3.0, clamp_max=3.0.
    """
    result = zscore_to_gauge(z)
    assert result == pytest.approx(expected), (
        f"z={z}: expected gauge={expected}, got {result}"
    )


def test_zscore_to_gauge_nan_passthrough():
    """NaN input must return NaN, not raise and not return 0 or 50."""
    result = zscore_to_gauge(float("nan"))
    assert math.isnan(result), f"Expected NaN for NaN input, got {result}"


def test_zscore_to_gauge_custom_clamp():
    """
    Custom clamp: clamp_min=-2.0, clamp_max=2.0, z=0.0 -> midpoint -> 50.0.
    gauge = ((0 - (-2)) / (2 - (-2))) * 100 = (2/4)*100 = 50.0
    """
    result = zscore_to_gauge(0.0, clamp_min=-2.0, clamp_max=2.0)
    assert result == pytest.approx(50.0), (
        f"Custom clamp midpoint: expected 50.0, got {result}"
    )


# =============================================================================
# classify_zone
# =============================================================================


@pytest.mark.parametrize(
    "gauge,expected_zone_id,expected_zone_label",
    [
        # Cold zone: gauge < 20
        (0.0, "cold", "Strong dovish pressure"),
        (19.9, "cold", "Strong dovish pressure"),
        # Cool zone: 20 <= gauge < 40
        (20.0, "cool", "Mild dovish pressure"),   # Boundary: >= 20 is cool, not cold
        (39.9, "cool", "Mild dovish pressure"),
        # Neutral zone: 40 <= gauge < 60
        (40.0, "neutral", "Balanced"),             # Boundary: >= 40 is neutral
        (50.0, "neutral", "Balanced"),
        (59.9, "neutral", "Balanced"),
        # Warm zone: 60 <= gauge < 80
        (60.0, "warm", "Mild hawkish pressure"),   # Boundary: >= 60 is warm
        (79.9, "warm", "Mild hawkish pressure"),
        # Hot zone: gauge >= 80
        (80.0, "hot", "Strong hawkish pressure"),  # Boundary: >= 80 is hot
        (100.0, "hot", "Strong hawkish pressure"),
    ],
)
def test_classify_zone_boundaries(gauge, expected_zone_id, expected_zone_label):
    """
    5-zone classification with exact boundary values.
    Boundaries at 20, 40, 60, 80 (inclusive on upper side).
    """
    zone_id, zone_label = classify_zone(gauge)
    assert zone_id == expected_zone_id, (
        f"gauge={gauge}: expected zone_id='{expected_zone_id}', got '{zone_id}'"
    )
    assert zone_label == expected_zone_label, (
        f"gauge={gauge}: expected zone_label="
        f"'{expected_zone_label}', got '{zone_label}'"
    )


def test_classify_zone_nan_returns_unknown():
    """NaN gauge -> ('unknown', 'Insufficient data')."""
    zone_id, zone_label = classify_zone(float("nan"))
    assert zone_id == "unknown"
    assert zone_label == "Insufficient data"


# =============================================================================
# compute_hawk_score
# =============================================================================


def test_compute_hawk_score_single_indicator():
    """
    Single indicator: gauge=60.0, weight=0.25.
    After rebalancing (only available indicator), score = 60.0.
    """
    gauge_values = {"inflation": 60.0}
    weights = {"inflation": {"weight": 0.25}}
    result = compute_hawk_score(gauge_values, weights, exclude_benchmark=False)
    assert result == pytest.approx(60.0), (
        f"Single indicator: expected 60.0, got {result}"
    )


def test_compute_hawk_score_two_equal_indicators():
    """
    Two indicators with equal weight: (40.0 + 80.0) / 2 = 60.0.
    """
    gauge_values = {"inflation": 40.0, "wages": 80.0}
    weights = {
        "inflation": {"weight": 0.5},
        "wages": {"weight": 0.5},
    }
    result = compute_hawk_score(gauge_values, weights, exclude_benchmark=False)
    assert result == pytest.approx(60.0), (
        f"Two equal indicators: expected 60.0, got {result}"
    )


def test_compute_hawk_score_missing_indicator_rebalancing():
    """
    Weights define 3 indicators but gauge_values only provides 2.
    Available weights are rescaled to sum=1.0:
      inflation: w=0.4, wages: w=0.4, spending: w=0.2 (missing)
      available sum = 0.8
      inflation rebalanced = 0.4/0.8 = 0.5, wages rebalanced = 0.4/0.8 = 0.5
      score = (60.0 * 0.4 + 40.0 * 0.4) / 0.8 = (24 + 16) / 0.8 = 50.0
    """
    gauge_values = {"inflation": 60.0, "wages": 40.0}
    weights = {
        "inflation": {"weight": 0.4},
        "wages": {"weight": 0.4},
        "spending": {"weight": 0.2},  # Not in gauge_values
    }
    result = compute_hawk_score(gauge_values, weights, exclude_benchmark=False)
    assert result == pytest.approx(50.0), (
        f"Missing indicator rebalancing: expected 50.0, got {result}"
    )


def test_compute_hawk_score_empty_gauge_values_returns_neutral():
    """
    All indicators missing -> weight_sum = 0.0 -> neutral fallback of 50.0.
    """
    gauge_values = {}
    weights = {"inflation": {"weight": 0.5}, "wages": {"weight": 0.5}}
    result = compute_hawk_score(gauge_values, weights, exclude_benchmark=False)
    assert result == pytest.approx(50.0), (
        f"Empty gauge_values: expected 50.0 (neutral fallback), got {result}"
    )


def test_compute_hawk_score_exclude_benchmark():
    """
    exclude_benchmark=True must exclude 'asx_futures' from the computation.
    gauge_values has both inflation (60.0) and asx_futures (100.0).
    With exclude_benchmark=True, only inflation contributes -> score = 60.0.
    """
    gauge_values = {"inflation": 60.0, "asx_futures": 100.0}
    weights = {
        "inflation": {"weight": 0.8},
        "asx_futures": {"weight": 0.2},
    }
    result = compute_hawk_score(gauge_values, weights, exclude_benchmark=True)
    assert result == pytest.approx(60.0), (
        f"Exclude benchmark: expected 60.0 (asx_futures excluded), got {result}"
    )


def test_compute_hawk_score_clamped_to_range():
    """
    Result must always be clamped to [0.0, 100.0].
    With a valid single indicator at 100.0, result should be 100.0 (not exceed it).
    """
    gauge_values = {"inflation": 100.0}
    weights = {"inflation": {"weight": 1.0}}
    result = compute_hawk_score(gauge_values, weights, exclude_benchmark=False)
    assert 0.0 <= result <= 100.0, (
        f"Result {result} is outside [0.0, 100.0] range"
    )
    assert result == pytest.approx(100.0)


# =============================================================================
# generate_verdict
# =============================================================================


@pytest.mark.parametrize(
    "hawk_score,expected_verdict",
    [
        # Strong easing: < 20
        (10.0, "Economic indicators suggest strong easing pressure"),
        (19.9, "Economic indicators suggest strong easing pressure"),
        # Mild easing: 20 <= score < 40
        (20.0, "Economic indicators suggest mild easing pressure"),   # Boundary
        (30.0, "Economic indicators suggest mild easing pressure"),
        (39.9, "Economic indicators suggest mild easing pressure"),
        # Balanced: 40 <= score < 60
        (40.0, "Economic indicators are broadly balanced"),           # Boundary
        (50.0, "Economic indicators are broadly balanced"),
        (59.9, "Economic indicators are broadly balanced"),
        # Moderate tightening: 60 <= score < 80
        (60.0, "Economic indicators suggest moderate tightening pressure"),  # Boundary
        (70.0, "Economic indicators suggest moderate tightening pressure"),
        (79.9, "Economic indicators suggest moderate tightening pressure"),
        # Strong tightening: >= 80
        (80.0, "Economic indicators suggest strong tightening pressure"),    # Boundary
        (90.0, "Economic indicators suggest strong tightening pressure"),
        (100.0, "Economic indicators suggest strong tightening pressure"),
    ],
)
def test_generate_verdict(hawk_score, expected_verdict):
    """
    5-zone verdict strings at exact boundary values.
    Boundaries at 20, 40, 60, 80 (inclusive on upper side).
    """
    result = generate_verdict(hawk_score)
    assert result == expected_verdict, (
        f"hawk_score={hawk_score}: expected '{expected_verdict}', got '{result}'"
    )
