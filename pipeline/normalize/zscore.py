"""
Robust Z-score computation module.

Uses median and MAD (Median Absolute Deviation) instead of mean and standard
deviation, providing resistance to outliers (e.g., COVID-era spikes).

Formula: z = (x - median) / MAD
Where MAD = median(|x_i - median(x)|) * 1.4826

The 1.4826 scaling constant makes MAD consistent with standard deviation
for normally distributed data.
"""

import numpy as np

from pipeline.config import (
    CONFIDENCE_HIGH_MIN_OBS,
    CONFIDENCE_MEDIUM_MIN_OBS,
    ZSCORE_MIN_YEARS,
    ZSCORE_WINDOW_YEARS,
)


def calculate_mad(values):
    """
    Calculate Median Absolute Deviation with normal-consistency scaling.

    MAD = median(|x_i - median(x)|) * 1.4826

    Args:
        values: numpy array of numeric values.

    Returns:
        Scaled MAD value. Returns 0.0 if all values are identical.
    """
    median = np.median(values)
    deviations = np.abs(values - median)
    mad = np.median(deviations) * 1.4826
    return float(mad)


def robust_zscore(current_value, window_values):
    """
    Compute a single robust Z-score.

    z = (current - median) / MAD

    Args:
        current_value: The value to compute Z-score for.
        window_values: numpy array of look-back window values.

    Returns:
        Z-score as float. Returns 0.0 if MAD is zero (no variability).
    """
    median = np.median(window_values)
    mad = calculate_mad(window_values)
    if mad == 0.0:
        return 0.0
    return float((current_value - median) / mad)


def compute_rolling_zscores(df, window_quarters=None, min_quarters=None):
    """
    Compute robust Z-scores over a rolling look-back window.

    For each row, compute the Z-score against the preceding window (excluding
    the current value). Rows before min_quarters get NaN.

    Args:
        df: DataFrame with 'date' and 'value' columns.
        window_quarters: Look-back window size in quarters (default: 10 years).
        min_quarters: Minimum observations required (default: 5 years).

    Returns:
        DataFrame with additional columns: z_score, rolling_median, rolling_mad,
        window_size.
    """
    if window_quarters is None:
        window_quarters = ZSCORE_WINDOW_YEARS * 4
    if min_quarters is None:
        min_quarters = ZSCORE_MIN_YEARS * 4

    result = df.copy()
    z_scores = []
    medians = []
    mads = []
    window_sizes = []

    values = result['value'].values

    for i in range(len(values)):
        # Look-back window: preceding observations, excluding current
        start = max(0, i - window_quarters)
        window = values[start:i]

        if len(window) < min_quarters:
            z_scores.append(np.nan)
            medians.append(np.nan)
            mads.append(np.nan)
            window_sizes.append(len(window))
            continue

        median = np.median(window)
        mad = calculate_mad(window)
        window_sizes.append(len(window))
        medians.append(float(median))
        mads.append(float(mad))

        if mad == 0.0:
            z_scores.append(0.0)
        else:
            z_scores.append(float((values[i] - median) / mad))

    result['z_score'] = z_scores
    result['rolling_median'] = medians
    result['rolling_mad'] = mads
    result['window_size'] = window_sizes

    return result


def determine_confidence(window_size):
    """
    Determine confidence level based on number of observations in window.

    Args:
        window_size: Number of observations used for Z-score calculation.

    Returns:
        "HIGH" (>= 32 obs / 8 years), "MEDIUM" (>= 20 obs / 5 years),
        or "LOW" (< 20 obs).
    """
    if window_size >= CONFIDENCE_HIGH_MIN_OBS:
        return "HIGH"
    elif window_size >= CONFIDENCE_MEDIUM_MIN_OBS:
        return "MEDIUM"
    else:
        return "LOW"
