"""
Unit tests for pipeline.normalize.zscore.

Covers:
  - calculate_mad: MAD = median(|x_i - median(x)|) * 1.4826
  - robust_zscore: z = (current - median) / MAD, with zero-MAD guard
  - compute_rolling_zscores: rolling look-back window with NaN for insufficient data
  - determine_confidence: threshold-based HIGH/MEDIUM/LOW classification

All tests are pure math — no network access, no disk I/O to the live data/ folder.
"""

import numpy as np
import pandas as pd
import pytest

from pipeline.normalize.zscore import (
    calculate_mad,
    compute_rolling_zscores,
    determine_confidence,
    robust_zscore,
)

# =============================================================================
# calculate_mad
# =============================================================================


def test_calculate_mad_three_values():
    """
    Known-answer: [1.0, 2.0, 3.0]
    median = 2.0
    deviations = [|1-2|, |2-2|, |3-2|] = [1.0, 0.0, 1.0]
    median(deviations) = 1.0
    MAD = 1.0 * 1.4826 = 1.4826
    """
    values = np.array([1.0, 2.0, 3.0])
    result = calculate_mad(values)
    assert result == pytest.approx(1.4826, rel=1e-4)


def test_calculate_mad_four_values():
    """
    Known-answer: [2.0, 4.0, 6.0, 8.0]
    median = 5.0
    deviations = [|2-5|, |4-5|, |6-5|, |8-5|] = [3.0, 1.0, 1.0, 3.0]
    median(deviations) = 2.0
    MAD = 2.0 * 1.4826 = 2.9652
    """
    values = np.array([2.0, 4.0, 6.0, 8.0])
    result = calculate_mad(values)
    assert result == pytest.approx(2.9652, rel=1e-4)


def test_calculate_mad_all_identical():
    """Edge case: all identical values -> deviations all zero -> MAD = 0.0 exactly."""
    values = np.array([5.0, 5.0, 5.0])
    result = calculate_mad(values)
    assert result == pytest.approx(0.0, abs=1e-9)


def test_calculate_mad_single_value():
    """Edge case: single value -> deviation from self is 0 -> MAD = 0.0."""
    values = np.array([3.0])
    result = calculate_mad(values)
    assert result == pytest.approx(0.0, abs=1e-9)


def test_calculate_mad_majority_identical():
    """
    Edge case: [1.0, 1.0, 5.0]
    median = 1.0
    deviations = [|1-1|, |1-1|, |5-1|] = [0.0, 0.0, 4.0]
    median(deviations) = 0.0
    MAD = 0.0 (majority-identical values yield zero MAD)
    """
    values = np.array([1.0, 1.0, 5.0])
    result = calculate_mad(values)
    assert result == pytest.approx(0.0, abs=1e-9)


# =============================================================================
# robust_zscore
# =============================================================================


def test_robust_zscore_standard_case():
    """
    Known-answer: current=5.0, window=[1,2,3,4,5]
    median = 3.0
    MAD = 1.4826 (see test_calculate_mad_three_values for derivation)
    z = (5.0 - 3.0) / 1.4826 = 1.34898...
    """
    window = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    result = robust_zscore(5.0, window)
    assert result == pytest.approx(1.3490, rel=1e-3)


def test_robust_zscore_zero_mad_guard():
    """
    Zero-MAD guard: when all window values are identical, MAD=0.
    Function must return 0.0 instead of raising ZeroDivisionError.
    """
    window = np.array([3.0, 3.0, 3.0])
    result = robust_zscore(5.0, window)
    assert result == pytest.approx(0.0, abs=1e-9)


def test_robust_zscore_current_equals_median():
    """
    When current_value equals the window median, z-score should be exactly 0.0.
    window=[1,2,3,4,5], median=3.0, current=3.0 -> z=0.0
    """
    window = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    result = robust_zscore(3.0, window)
    assert result == pytest.approx(0.0, abs=1e-9)


# =============================================================================
# compute_rolling_zscores
# =============================================================================


def _make_df(values):
    """Helper: build a minimal date/value DataFrame for testing."""
    n = len(values)
    dates = pd.date_range("2020-01-01", periods=n, freq="QS")
    return pd.DataFrame({"date": dates, "value": values})


def test_compute_rolling_zscores_nan_for_insufficient_window():
    """
    With min_quarters=2, rows 0 and 1 should have NaN z_score
    (window sizes 0 and 1 are too small).
    Row 2 onward should have valid (non-NaN) z_score.
    """
    df = _make_df([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
    result = compute_rolling_zscores(df, window_quarters=40, min_quarters=2)

    assert "z_score" in result.columns
    assert "rolling_median" in result.columns
    assert "rolling_mad" in result.columns
    assert "window_size" in result.columns

    # Rows with window < min_quarters have NaN
    assert pd.isna(result["z_score"].iloc[0])
    assert pd.isna(result["z_score"].iloc[1])

    # Row 2+ (window size >= 2) has valid z_score
    for i in range(2, len(result)):
        assert not pd.isna(result["z_score"].iloc[i]), (
            f"Row {i} z_score should not be NaN "
            f"(window size {result['window_size'].iloc[i]})"
        )


def test_compute_rolling_zscores_zero_mad_produces_zero_not_nan():
    """
    When all values in the window are identical, MAD=0.
    The result must be 0.0, not NaN (division by zero guard must apply).
    """
    df = _make_df([5.0, 5.0, 5.0, 5.0, 5.0, 5.0])
    result = compute_rolling_zscores(df, window_quarters=40, min_quarters=2)

    for i in range(2, len(result)):
        assert result["z_score"].iloc[i] == pytest.approx(0.0, abs=1e-9), (
            f"Row {i}: expected 0.0 for all-identical "
            f"window, got {result['z_score'].iloc[i]}"
        )


def test_compute_rolling_zscores_with_fixture_data(fixture_cpi_df):
    """
    Use realistic fixture data with min_quarters=5.
    First 5 rows must have NaN z_scores (window too small).
    Remaining rows must have non-NaN z_scores.
    """
    result = compute_rolling_zscores(fixture_cpi_df, window_quarters=40, min_quarters=5)

    # First 5 rows: window sizes 0..4, all < 5 -> NaN
    for i in range(5):
        assert pd.isna(result["z_score"].iloc[i]), (
            f"Row {i} should be NaN (window_size={result['window_size'].iloc[i]})"
        )

    # Rows 5+: window size >= 5 -> valid z_score
    for i in range(5, len(result)):
        assert not pd.isna(result["z_score"].iloc[i]), (
            f"Row {i} z_score should not be NaN"
        )


def test_compute_rolling_zscores_window_size_column():
    """
    window_size column must correctly track how many preceding observations
    were used. Increments from 0 and is capped at window_quarters.
    """
    df = _make_df([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0])
    result = compute_rolling_zscores(df, window_quarters=4, min_quarters=1)

    # Window sizes: 0, 1, 2, 3, 4, 4, 4 (capped at window_quarters=4)
    expected_sizes = [0, 1, 2, 3, 4, 4, 4]
    for i, expected in enumerate(expected_sizes):
        assert result["window_size"].iloc[i] == expected, (
            f"Row {i}: expected window_size={expected}, "
            f"got {result['window_size'].iloc[i]}"
        )


def test_compute_rolling_zscores_regression_detection():
    """
    Regression detection: a known spike at row 8 must produce a significantly
    positive z-score, proving a regression in the z-score formula would be caught.

    Rows 0-7: stable values around 2.0 (small variance).
    Row 8: deliberate spike to 10.0.
    Row 9: return to normal.

    With min_quarters=3, row 8's z_score must be > 1.5 (clearly anomalous).

    If someone breaks zscore.py to return 0.0 always, this test fails with:
        AssertionError: z_score for spike row should be > 1.5, got 0.0
    """
    values = [2.0, 2.1, 1.9, 2.2, 1.8, 2.0, 2.1, 1.9, 10.0, 2.0]
    df = _make_df(values)
    result = compute_rolling_zscores(df, window_quarters=40, min_quarters=3)

    spike_z = result["z_score"].iloc[8]
    assert not pd.isna(spike_z), "Spike row z_score should not be NaN"
    assert spike_z > 1.5, (
        f"z_score for spike row should be > 1.5 (clearly anomalous), got {spike_z}. "
        "A regression in the z-score formula may have caused this."
    )


# =============================================================================
# determine_confidence
# =============================================================================


@pytest.mark.parametrize(
    "window_size,expected",
    [
        (32, "HIGH"),   # Exactly CONFIDENCE_HIGH_MIN_OBS (8 years quarterly)
        (40, "HIGH"),   # Well above high threshold
        (20, "MEDIUM"), # Exactly CONFIDENCE_MEDIUM_MIN_OBS (5 years quarterly)
        (31, "MEDIUM"), # One below high threshold
        (19, "LOW"),    # One below medium threshold
        (0, "LOW"),     # Zero observations
    ],
)
def test_determine_confidence(window_size, expected):
    """
    Threshold-based classification:
    - >= 32 (CONFIDENCE_HIGH_MIN_OBS) -> HIGH
    - >= 20 (CONFIDENCE_MEDIUM_MIN_OBS) -> MEDIUM
    - < 20 -> LOW
    """
    result = determine_confidence(window_size)
    assert result == expected, (
        f"window_size={window_size}: expected '{expected}', got '{result}'"
    )
