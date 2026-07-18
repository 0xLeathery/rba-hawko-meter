"""
Ratio normalization module.

Converts raw CSV data to normalized ratios (primarily YoY % change).
Ensures no nominal currency values pass through to the gauge engine.
"""

from pathlib import Path

import numpy as np
import pandas as pd

import pipeline.config


def _load_cotality_yoy_overlay(config: dict) -> pd.DataFrame | None:
    """Load latest Cotality HVI YoY row from a dedicated CSV, if configured."""
    cotality_name = config.get('cotality_csv')
    if not cotality_name:
        return None
    path = pipeline.config.DATA_DIR / cotality_name
    if not path.exists() or path.stat().st_size == 0:
        return None
    try:
        raw = pd.read_csv(path)
    except Exception:
        return None
    if 'value' not in raw.columns or len(raw) == 0:
        return None
    if 'source' in raw.columns:
        raw = raw[raw['source'] == 'Cotality HVI']
    if len(raw) == 0:
        return None
    out = raw[['date', 'value']].copy()
    out['date'] = pd.to_datetime(out['date'])
    out['value'] = pd.to_numeric(out['value'], errors='coerce')
    out = out.dropna(subset=['date', 'value']).sort_values('date').tail(1)
    return out if len(out) > 0 else None


def _split_legacy_hybrid_csv(csv_path: Path):
    """Split a mixed ABS-index + Cotality-YoY CSV (legacy single-file shape).

    Returns:
        (precomputed_cotality_rows | None, abs_index_df | None)
    """
    precomputed_yoy_sources = {'Cotality HVI'}
    raw_path = Path(csv_path)
    if not raw_path.exists() or raw_path.stat().st_size == 0:
        return None, None
    try:
        _full = pd.read_csv(raw_path)
    except Exception:
        return None, None
    if 'source' not in _full.columns:
        return None, None
    mask = _full['source'].isin(precomputed_yoy_sources)
    if not mask.any():
        return None, None

    _precomp = _full[mask][['date', 'value']].copy()
    _precomp['date'] = pd.to_datetime(_precomp['date'])
    _precomp['value'] = pd.to_numeric(_precomp['value'], errors='coerce')
    _precomp = (
        _precomp.dropna(subset=['value']).sort_values('date').tail(1)
    )
    precomputed = _precomp if len(_precomp) > 0 else None

    _index_rows = _full[~mask][['date', 'value']].copy()
    _index_rows['date'] = pd.to_datetime(_index_rows['date'])
    _index_rows['value'] = pd.to_numeric(_index_rows['value'], errors='coerce')
    _index_rows = _index_rows.sort_values('date').reset_index(drop=True)
    return precomputed, _index_rows


def load_indicator_csv(csv_path):
    """
    Read a CSV file with date/value columns, parse dates, sort by date.

    Args:
        csv_path: Path to the CSV file.

    Returns:
        DataFrame with parsed date and numeric value columns, or None if file missing
        or if CSV doesn't have the expected date/value schema.
    """
    path = Path(csv_path)
    if not path.exists():
        print(f"  CSV not found: {path}")
        return None

    if path.stat().st_size == 0:
        print(f"  CSV is empty: {path}")
        return None

    try:
        df = pd.read_csv(path)
    except pd.errors.EmptyDataError:
        print(f"  CSV has no parseable data: {path}")
        return None

    # Check for required columns
    if 'value' not in df.columns:
        print(f"  CSV missing 'value' column (non-standard schema): {path}")
        return None

    if df.empty:
        print(f"  CSV has headers but no data rows: {path}")
        return None

    df['date'] = pd.to_datetime(df['date'])
    df['value'] = pd.to_numeric(df['value'], errors='coerce')
    df = df.sort_values('date').reset_index(drop=True)
    return df


def compute_yoy_pct_change(df, periods):
    """
    Compute year-over-year percentage change.

    Formula: ((value_t / value_{t-periods}) - 1) * 100

    Args:
        df: DataFrame with 'date' and 'value' columns.
        periods: Number of periods for YoY (4 for quarterly, 12 for monthly).

    Returns:
        DataFrame with 'date' and 'value' (now YoY % change), leading NaN rows dropped.
    """
    result = df.copy()
    result['value'] = (result['value'] / result['value'].shift(periods) - 1) * 100
    result = result.dropna(subset=['value']).reset_index(drop=True)
    return result


def resample_to_quarterly(df):
    """
    Resample monthly data to quarterly using end-of-quarter last value.

    Args:
        df: DataFrame with 'date' and 'value' columns (monthly frequency).

    Returns:
        DataFrame resampled to quarterly frequency.
    """
    df = df.set_index('date')
    quarterly = df[['value']].resample('QE').last()
    quarterly = quarterly.dropna(subset=['value']).reset_index()
    return quarterly


def filter_valid_data(df):
    """
    Drop NaN, inf, and zero-value rows.

    Args:
        df: DataFrame with 'value' column.

    Returns:
        DataFrame with invalid rows removed.
    """
    df = df.copy()
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.dropna(subset=['value'])
    df = df[df['value'] != 0]
    return df.reset_index(drop=True)


def normalize_indicator(name, config):
    """
    Main entry point: load CSV, normalize, and return quarterly DataFrame.

    Args:
        name: Indicator name (e.g. 'inflation', 'wages').
        config: Dict with csv_file, normalize, frequency, yoy_periods keys.

    Returns:
        DataFrame with [date, value] columns (quarterly, YoY % change),
        or None if data unavailable.
    """
    csv_file = config.get('csv_file')
    if csv_file is None:
        return None

    csv_path = pipeline.config.DATA_DIR / csv_file

    # Optional separate Cotality HVI file (pre-computed annual YoY %).
    # Kept out of the ABS index CSV so metric units never mix.
    precomputed_rows = _load_cotality_yoy_overlay(config)

    # Legacy hybrid: single CSV with mixed sources (tests / old data).
    # Prefer cotality_csv when configured; fall back to in-file Cotality rows.
    df_override = None
    if precomputed_rows is None:
        precomputed_rows, df_override = _split_legacy_hybrid_csv(csv_path)

    # Load CSV: use filtered df_override if available, otherwise load normally
    if df_override is not None:
        df = df_override
    else:
        df = load_indicator_csv(csv_path)

    has_index = df is not None and len(df) > 0
    has_cotality = precomputed_rows is not None and len(precomputed_rows) > 0
    if not has_index and not has_cotality:
        return None

    if has_index:
        # Filter out zeros and invalid values before normalization
        df = filter_valid_data(df)

        if len(df) == 0:
            print(f"  {name}: no valid data after filtering")
            df = None
        else:
            normalize_type = config.get('normalize', 'yoy_pct_change')

            if normalize_type == 'yoy_pct_change':
                periods = config.get('yoy_periods', 4)
                df = compute_yoy_pct_change(df, periods)
            elif normalize_type == 'direct':
                pass  # Use values as-is (already a ratio/index)

            if len(df) == 0:
                print(f"  {name}: no data after normalization")
                df = None
            else:
                # Resample monthly data to quarterly
                frequency = config.get('frequency', 'quarterly')
                if frequency == 'monthly':
                    df = resample_to_quarterly(df)

                if len(df) == 0:
                    print(f"  {name}: no data after resampling")
                    df = None
                else:
                    # Filter any remaining invalid values after normalization
                    df = df.replace([np.inf, -np.inf], np.nan)
                    df = df.dropna(subset=['value'])

    # Append pre-computed YoY rows (e.g. Cotality HVI) as the latest data point(s).
    # These values are already in YoY % format -- no further transformation needed.
    if has_cotality:
        cot = precomputed_rows[['date', 'value']]
        if df is not None and len(df) > 0:
            df = pd.concat([df, cot], ignore_index=True)
            df = df.sort_values('date').reset_index(drop=True)
        else:
            df = cot.reset_index(drop=True)

    if df is None or len(df) == 0:
        return None

    # Return only date and value columns
    return df[['date', 'value']].reset_index(drop=True)


def load_asx_futures_csv(csv_path):
    """
    Read the ASX futures multi-column CSV and return the latest row's data.

    The CSV has schema:
    date,meeting_date,implied_rate,change_bp,probability_cut,probability_hold,probability_hike

    Unlike standard indicator CSVs (date,value), this CSV has multiple columns
    with meeting-specific data. We find the row for the next upcoming meeting.

    Args:
        csv_path: Path to asx_futures.csv.

    Returns:
        Dict with keys matching status.json asx_futures contract, or None if
        file missing/empty/unparseable.
    """
    path = Path(csv_path)
    if not path.exists():
        print(f"  ASX futures CSV not found: {path}")
        return None

    if path.stat().st_size == 0:
        print("  ASX futures CSV is empty (0 bytes)")
        return None

    try:
        df = pd.read_csv(path)
    except pd.errors.EmptyDataError:
        print("  ASX futures CSV has no parseable data")
        return None

    if df.empty:
        print("  ASX futures CSV is empty")
        return None

    # Parse dates
    df['date'] = pd.to_datetime(df['date'])
    df['meeting_date'] = pd.to_datetime(df['meeting_date'])

    # Sort by date descending to get the most recent scrape
    df = df.sort_values('date', ascending=False)

    # Get the latest scrape date
    latest_date = df['date'].iloc[0]
    latest_rows = df[df['date'] == latest_date]

    # From the latest scrape, find the next upcoming meeting
    # (meeting_date >= today)
    today = pd.Timestamp.now().normalize()
    future_meetings = latest_rows[latest_rows['meeting_date'] >= today]

    if future_meetings.empty:
        # All meetings in the past -- use the latest meeting as fallback
        next_meeting_row = latest_rows.iloc[0]
        # No future meetings to build array from
        upcoming_meetings = future_meetings  # empty DataFrame
    else:
        # Pick the nearest future meeting
        upcoming_meetings = future_meetings.sort_values('meeting_date')
        next_meeting_row = upcoming_meetings.iloc[0]

    # Build multi-meeting list: next 3-4 upcoming meetings
    meetings = []
    for _, row in upcoming_meetings.head(4).iterrows():
        meetings.append({
            'meeting_date': row['meeting_date'].strftime('%Y-%m-%d'),
            'implied_rate': float(row['implied_rate']),
            'change_bp': float(row['change_bp']),
            'probability_cut': float(row['probability_cut']),
            'probability_hold': float(row['probability_hold']),
            'probability_hike': float(row['probability_hike']),
        })

    return {
        'data_date': latest_date.strftime('%Y-%m-%d'),
        'meeting_date': next_meeting_row['meeting_date'].strftime('%Y-%m-%d'),
        'implied_rate': float(next_meeting_row['implied_rate']),
        'change_bp': float(next_meeting_row['change_bp']),
        'probability_cut': float(next_meeting_row['probability_cut']),
        'probability_hold': float(next_meeting_row['probability_hold']),
        'probability_hike': float(next_meeting_row['probability_hike']),
        'meetings': meetings,
    }
