"""
Unit tests for pipeline.normalize.ratios module.

Tests:
  - load_indicator_csv: happy path, missing file, empty file,
    missing column, header-only
  - compute_yoy_pct_change: quarterly/monthly data, fixture data, edge case
  - filter_valid_data: mixed, all-valid, all-invalid data
  - resample_to_quarterly: 12-month -> 4-quarter, last value semantics
  - normalize_indicator: standard path, missing CSV,
    hybrid Cotality/ABS path, direct normalization
"""

import shutil
from pathlib import Path

import numpy as np
import pandas as pd

from pipeline.normalize.ratios import (
    compute_yoy_pct_change,
    filter_valid_data,
    load_indicator_csv,
    normalize_indicator,
    resample_to_quarterly,
)

# Locate fixture directory relative to this file (avoids CWD sensitivity)
FIXTURES_DIR = Path(__file__).parent / "fixtures"


# =============================================================================
# load_indicator_csv
# =============================================================================


def test_load_indicator_csv_happy_path(tmp_path):
    """Happy path: valid 5-row CSV with date/value columns loads correctly."""
    csv_path = tmp_path / "test.csv"
    csv_path.write_text(
        "date,value\n"
        "2023-01-01,100.0\n"
        "2023-04-01,101.0\n"
        "2023-07-01,102.0\n"
        "2023-10-01,103.0\n"
        "2024-01-01,104.0\n"
    )
    df = load_indicator_csv(csv_path)

    assert df is not None
    assert len(df) == 5
    # Dates must be datetime64 (parsed)
    assert pd.api.types.is_datetime64_any_dtype(df["date"])
    # Values must be numeric
    assert pd.api.types.is_numeric_dtype(df["value"])
    # Must be sorted by date ascending
    assert list(df["value"]) == [100.0, 101.0, 102.0, 103.0, 104.0]


def test_load_indicator_csv_missing_file(tmp_path):
    """Missing file returns None."""
    result = load_indicator_csv(tmp_path / "nonexistent.csv")
    assert result is None


def test_load_indicator_csv_empty_file(tmp_path):
    """Empty (0-byte) file returns None."""
    empty_path = tmp_path / "empty.csv"
    empty_path.write_bytes(b"")
    result = load_indicator_csv(empty_path)
    assert result is None


def test_load_indicator_csv_missing_value_column(tmp_path):
    """CSV with 'amount' instead of 'value' column returns None."""
    csv_path = tmp_path / "bad_schema.csv"
    csv_path.write_text(
        "date,amount\n"
        "2023-01-01,100.0\n"
        "2023-04-01,101.0\n"
    )
    result = load_indicator_csv(csv_path)
    assert result is None


def test_load_indicator_csv_header_only(tmp_path):
    """CSV with header row but no data rows returns None."""
    csv_path = tmp_path / "header_only.csv"
    csv_path.write_text("date,value\n")
    result = load_indicator_csv(csv_path)
    assert result is None


# =============================================================================
# compute_yoy_pct_change
# =============================================================================


def test_compute_yoy_quarterly_known_value():
    """Quarterly data (periods=4): row 0 value=100, row 4 value=110 -> YoY = 10.0%."""
    dates = pd.date_range("2020-01-01", periods=8, freq="QE")
    values = [100.0, 98.0, 101.0, 99.0, 110.0, 107.8, 111.1, 108.9]
    df = pd.DataFrame({"date": dates, "value": values})

    result = compute_yoy_pct_change(df, periods=4)

    # Output length must be input - periods (leading NaNs dropped)
    assert len(result) == len(df) - 4

    # First result row: 110/100 - 1 * 100 = 10.0%
    assert abs(result["value"].iloc[0] - 10.0) < 0.01


def test_compute_yoy_monthly_known_value():
    """Monthly data (periods=12): row 0 value=100, row 12 value=105 -> YoY = 5.0%."""
    dates = pd.date_range("2020-01-01", periods=15, freq="MS")
    # Base values for first 12 months, then row 12 = 105
    values = [100.0, 101.0, 102.0, 103.0, 104.0, 105.0,
              106.0, 107.0, 108.0, 109.0, 110.0, 111.0,
              105.0, 102.0, 103.0]
    df = pd.DataFrame({"date": dates, "value": values})

    result = compute_yoy_pct_change(df, periods=12)

    # Output length = 15 - 12 = 3
    assert len(result) == 3
    # row 12 (index 0 in result): 105/100 - 1 * 100 = 5.0%
    assert abs(result["value"].iloc[0] - 5.0) < 0.01


def test_compute_yoy_output_length():
    """Output length equals input length minus periods."""
    dates = pd.date_range("2020-01-01", periods=10, freq="QE")
    df = pd.DataFrame({"date": dates, "value": [float(i + 100) for i in range(10)]})

    result = compute_yoy_pct_change(df, periods=4)
    assert len(result) == 10 - 4


def test_compute_yoy_with_fixture_data(fixture_cpi_df):
    """Using fixture CPI data with periods=4: result has len - 4 rows, all non-NaN."""
    # Parse dates for proper computation
    df = fixture_cpi_df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.sort_values("date").reset_index(drop=True)

    result = compute_yoy_pct_change(df, periods=4)

    assert len(result) == len(df) - 4
    assert result["value"].notna().all()


def test_compute_yoy_edge_case_zero_result():
    """Value goes from 100 to 0 in one period -> YoY = -100.0%."""
    dates = pd.date_range("2020-01-01", periods=5, freq="QE")
    # Row 0: 100, row 4: 0
    df = pd.DataFrame({"date": dates, "value": [100.0, 90.0, 80.0, 70.0, 0.0]})

    result = compute_yoy_pct_change(df, periods=4)

    # 0/100 - 1 * 100 = -100.0%
    assert abs(result["value"].iloc[0] - (-100.0)) < 0.01


# =============================================================================
# filter_valid_data
# =============================================================================


def test_filter_valid_data_mixed():
    """Mixed data: only rows with 1.0 and 5.0 survive."""
    dates = pd.date_range("2020-01-01", periods=6, freq="MS")
    df = pd.DataFrame({
        "date": dates,
        "value": [1.0, np.nan, np.inf, -np.inf, 0.0, 5.0],
    })

    result = filter_valid_data(df)

    assert len(result) == 2
    assert list(result["value"]) == [1.0, 5.0]


def test_filter_valid_data_all_valid():
    """All valid rows: all 3 rows retained."""
    dates = pd.date_range("2020-01-01", periods=3, freq="MS")
    df = pd.DataFrame({"date": dates, "value": [1.0, 2.0, 3.0]})

    result = filter_valid_data(df)

    assert len(result) == 3
    assert list(result["value"]) == [1.0, 2.0, 3.0]


def test_filter_valid_data_all_invalid():
    """All invalid rows: empty DataFrame returned."""
    dates = pd.date_range("2020-01-01", periods=3, freq="MS")
    df = pd.DataFrame({"date": dates, "value": [0.0, np.nan, np.inf]})

    result = filter_valid_data(df)

    assert len(result) == 0


# =============================================================================
# resample_to_quarterly
# =============================================================================


def test_resample_to_quarterly_produces_4_rows():
    """12-month monthly DataFrame resampled to quarterly produces 4 rows."""
    dates = pd.date_range("2020-01-01", periods=12, freq="MS")
    df = pd.DataFrame({
        "date": dates,
        "value": [float(i + 1) for i in range(12)],
    })

    result = resample_to_quarterly(df)

    assert len(result) == 4


def test_resample_to_quarterly_uses_last_value():
    """Last value of each quarter is used (not mean/first)."""
    # Q1: Jan=1, Feb=2, Mar=3 (last = 3)
    # Q2: Apr=4, May=5, Jun=6 (last = 6)
    # Q3: Jul=7, Aug=8, Sep=9 (last = 9)
    # Q4: Oct=10, Nov=11, Dec=12 (last = 12)
    dates = pd.date_range("2020-01-01", periods=12, freq="MS")
    df = pd.DataFrame({
        "date": dates,
        "value": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0],
    })

    result = resample_to_quarterly(df)

    # End-of-quarter last values: March=3, June=6, September=9, December=12
    assert list(result["value"]) == [3.0, 6.0, 9.0, 12.0]


# =============================================================================
# normalize_indicator
# =============================================================================


def test_normalize_indicator_standard_path(tmp_path, monkeypatch):
    """Standard path: CPI fixture CSV produces non-empty
    DataFrame with date/value columns."""
    import pipeline.config
    monkeypatch.setattr(pipeline.config, "DATA_DIR", tmp_path)

    # Copy fixture CSV to tmp_path (DATA_DIR is patched to tmp_path by autouse fixture,
    # but we also patch here explicitly to be safe)
    shutil.copy(FIXTURES_DIR / "abs_cpi.csv", tmp_path / "abs_cpi.csv")

    result = normalize_indicator(
        "inflation",
        {
            "csv_file": "abs_cpi.csv",
            "normalize": "yoy_pct_change",
            "frequency": "monthly",
            "yoy_periods": 12,
        },
    )

    assert result is not None
    assert len(result) > 0
    assert "date" in result.columns
    assert "value" in result.columns


def test_normalize_indicator_missing_csv(tmp_path, monkeypatch):
    """Config with non-existent csv_file returns None."""
    import pipeline.config
    monkeypatch.setattr(pipeline.config, "DATA_DIR", tmp_path)

    result = normalize_indicator(
        "inflation",
        {
            "csv_file": "nonexistent.csv",
            "normalize": "yoy_pct_change",
            "frequency": "monthly",
            "yoy_periods": 12,
        },
    )

    assert result is None


def test_normalize_indicator_hybrid_cotality_abs_path(tmp_path, monkeypatch):
    """
    Hybrid Cotality/ABS path: ABS index rows get YoY-normalized, Cotality HVI row
    (pre-computed YoY) is appended unchanged, avoiding double-normalization.
    """
    import pipeline.config
    monkeypatch.setattr(pipeline.config, "DATA_DIR", tmp_path)

    # Build a mixed-source CSV: 4 ABS quarterly index rows + 1 Cotality HVI row
    csv_path = tmp_path / "corelogic_housing.csv"
    csv_content = (
        "date,value,source\n"
        "2020-03-31,100.0,ABS\n"
        "2021-03-31,105.0,ABS\n"
        "2022-03-31,110.0,ABS\n"
        "2023-03-31,115.0,ABS\n"
        "2024-01-31,9.4,Cotality HVI\n"
    )
    csv_path.write_text(csv_content)

    result = normalize_indicator(
        "housing",
        {
            "csv_file": "corelogic_housing.csv",
            "normalize": "yoy_pct_change",
            "frequency": "quarterly",
            "yoy_periods": 4,
        },
    )

    assert result is not None
    assert len(result) > 0
    assert "date" in result.columns
    assert "value" in result.columns

    # (a) Cotality HVI value (9.4) must appear in output —
    # pre-computed, not double-normalized
    assert 9.4 in result["value"].values

    # (b) ABS YoY rows must be present (first ABS row after YoY: 105/100 - 1 = 5%)
    yoy_values = result["value"].values
    assert any(abs(v - 5.0) < 0.1 for v in yoy_values), (
        f"Expected ABS YoY value ~5.0% not found in {yoy_values}"
    )

    # (c) Last row's value should be 9.4 (Cotality is the most recent date)
    assert abs(result["value"].iloc[-1] - 9.4) < 0.01


def test_normalize_indicator_direct_normalization(tmp_path, monkeypatch):
    """Direct normalization: values pass through unchanged without YoY computation."""
    import pipeline.config
    monkeypatch.setattr(pipeline.config, "DATA_DIR", tmp_path)

    shutil.copy(FIXTURES_DIR / "nab_capacity.csv", tmp_path / "nab_capacity.csv")

    result = normalize_indicator(
        "business_confidence",
        {
            "csv_file": "nab_capacity.csv",
            "normalize": "direct",
            "frequency": "monthly",
            "yoy_periods": None,
        },
    )

    assert result is not None
    assert len(result) > 0

    # Values should be the raw fixture values (no YoY transformation)
    # The fixture has values around 81-84 (NAB capacity utilisation %)
    assert result["value"].min() > 70.0
    assert result["value"].max() < 90.0
