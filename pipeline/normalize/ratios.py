"""
Ratio normalization module.

Converts raw CSV data to normalized ratios (primarily YoY % change).
Ensures no nominal currency values pass through to the gauge engine.
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

import pipeline.config

logger = logging.getLogger(__name__)

# If Cotality (or other overlay) is newer than ABS history by more than this,
# z-scores use ABS history only; overlay is display metadata (gap policy).
OVERLAY_GAP_DAYS = 365


def _read_csv_safe(path: Path) -> pd.DataFrame | None:
    """Read a CSV; return None on missing file or parse/IO errors."""
    if not path.exists() or path.stat().st_size == 0:
        return None
    try:
        return pd.read_csv(path)
    except (OSError, pd.errors.EmptyDataError, pd.errors.ParserError) as e:
        logger.warning("Could not read %s: %s", path, e)
        return None


def _frame_from_value_csv(
    raw: pd.DataFrame,
    *,
    source_filter: str | None = None,
    latest_only: bool = False,
) -> pd.DataFrame | None:
    """Normalize a raw CSV to date/value; optional source filter."""
    if raw is None or len(raw) == 0 or "value" not in raw.columns:
        return None
    df = raw
    if source_filter is not None and "source" in df.columns:
        df = df[df["source"] == source_filter]
    if len(df) == 0 or "date" not in df.columns:
        return None
    out = df[["date", "value"]].copy()
    out["date"] = pd.to_datetime(out["date"])
    out["value"] = pd.to_numeric(out["value"], errors="coerce")
    out = out.dropna(subset=["date", "value"]).sort_values("date")
    if latest_only:
        out = out.tail(1)
    return out.reset_index(drop=True) if len(out) > 0 else None


def _resolve_index_and_overlay(
    config: dict,
) -> tuple[pd.DataFrame | None, pd.DataFrame | None, str | None]:
    """Resolve ABS index history and optional Cotality YoY overlay.

    Supports:
    - Split files: csv_file=abs index, cotality_csv=Cotality YoY
    - Single file: pure index, or legacy mixed ABS+Cotality sources

    Returns:
        (index_df, cotality_df, data_source_label)
    """
    csv_file = config.get("csv_file")
    if not csv_file:
        return None, None, None

    csv_path = pipeline.config.DATA_DIR / csv_file
    cotality_name = config.get("cotality_csv")

    cotality_df = None
    if cotality_name:
        cot_raw = _read_csv_safe(pipeline.config.DATA_DIR / cotality_name)
        cotality_df = _frame_from_value_csv(
            cot_raw, source_filter="Cotality HVI", latest_only=True
        )
        # Pure Cotality file may omit source column
        if cotality_df is None and cot_raw is not None:
            cotality_df = _frame_from_value_csv(cot_raw, latest_only=True)

    main_raw = _read_csv_safe(csv_path)
    index_df = None

    if main_raw is not None and "source" in main_raw.columns:
        has_cotality_in_file = (main_raw["source"] == "Cotality HVI").any()
        if has_cotality_in_file and cotality_df is None:
            cotality_df = _frame_from_value_csv(
                main_raw, source_filter="Cotality HVI", latest_only=True
            )
        # Index rows = non-Cotality (ABS RPPI etc.)
        index_raw = main_raw[main_raw["source"] != "Cotality HVI"]
        if len(index_raw) > 0:
            index_df = _frame_from_value_csv(index_raw)
    elif main_raw is not None:
        index_df = _frame_from_value_csv(main_raw)

    if cotality_df is not None:
        data_source = "Cotality HVI"
    elif index_df is not None:
        data_source = "ABS RPPI" if csv_file.endswith("rppi.csv") else None
    else:
        data_source = None

    return index_df, cotality_df, data_source


def _normalize_index_frame(
    df: pd.DataFrame,
    config: dict,
    name: str,
) -> pd.DataFrame | None:
    """Run filter → YoY/direct → optional monthly resample. Flat, no nesting."""
    df = filter_valid_data(df)
    if len(df) == 0:
        print(f"  {name}: no valid data after filtering")
        return None

    normalize_type = config.get("normalize", "yoy_pct_change")
    if normalize_type == "yoy_pct_change":
        periods = config.get("yoy_periods", 4)
        df = compute_yoy_pct_change(df, periods)
    elif normalize_type == "direct":
        pass
    else:
        pass

    if len(df) == 0:
        print(f"  {name}: no data after normalization")
        return None

    if config.get("frequency", "quarterly") == "monthly":
        df = resample_to_quarterly(df)
        if len(df) == 0:
            print(f"  {name}: no data after resampling")
            return None

    df = df.replace([np.inf, -np.inf], np.nan).dropna(subset=["value"])
    if len(df) == 0:
        return None
    return df.reset_index(drop=True)


def _attach_indicator_meta(
    df: pd.DataFrame,
    *,
    data_source: str | None,
    cotality_df: pd.DataFrame | None,
    name: str,
) -> pd.DataFrame:
    """Attach display metadata; keep z-score series free of sparse overlays."""
    meta: dict = {}
    if name == "housing":
        meta["stale_display"] = "quarter_only"
        meta["data_source"] = data_source or "ABS RPPI"

    if cotality_df is not None and len(cotality_df) > 0 and len(df) > 0:
        overlay_date = pd.Timestamp(cotality_df["date"].iloc[-1])
        last_abs = pd.Timestamp(df["date"].iloc[-1])
        gap_days = (overlay_date - last_abs).days
        meta["display_raw_value"] = float(cotality_df["value"].iloc[-1])
        meta["display_data_date"] = overlay_date.strftime("%Y-%m-%d")
        meta["data_source"] = "Cotality HVI"
        meta["overlay_gap_days"] = int(gap_days)
        # Large gap: do not append into z-score series (temporal integrity).
        if gap_days > OVERLAY_GAP_DAYS:
            meta["sparse_overlay"] = True
            meta["confidence_cap"] = "LOW"
        else:
            # Continuous enough to append as latest YoY observation
            df = pd.concat([df, cotality_df[["date", "value"]]], ignore_index=True)
            df = df.sort_values("date").reset_index(drop=True)
            meta.pop("display_raw_value", None)
            meta.pop("display_data_date", None)

    elif cotality_df is not None and len(cotality_df) > 0 and len(df) == 0:
        df = cotality_df[["date", "value"]].reset_index(drop=True)
        meta["data_source"] = "Cotality HVI"

    df.attrs["indicator_meta"] = meta
    return df


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
    raw = _read_csv_safe(path)
    if raw is None:
        if not path.exists():
            print(f"  CSV not found: {path}")
        elif path.stat().st_size == 0:
            print(f"  CSV is empty: {path}")
        return None

    if "value" not in raw.columns:
        print(f"  CSV missing 'value' column (non-standard schema): {path}")
        return None

    if raw.empty:
        print(f"  CSV has headers but no data rows: {path}")
        return None

    return _frame_from_value_csv(raw)


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
    result["value"] = (result["value"] / result["value"].shift(periods) - 1) * 100
    result = result.dropna(subset=["value"]).reset_index(drop=True)
    return result


def resample_to_quarterly(df):
    """
    Resample monthly data to quarterly using end-of-quarter last value.

    Args:
        df: DataFrame with 'date' and 'value' columns (monthly frequency).

    Returns:
        DataFrame resampled to quarterly frequency.
    """
    df = df.set_index("date")
    quarterly = df[["value"]].resample("QE").last()
    quarterly = quarterly.dropna(subset=["value"]).reset_index()
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
    df = df.dropna(subset=["value"])
    df = df[df["value"] != 0]
    return df.reset_index(drop=True)


def normalize_indicator(name, config):
    """
    Main entry point: load CSV, normalize, and return quarterly DataFrame.

    Args:
        name: Indicator name (e.g. 'inflation', 'wages').
        config: Dict with csv_file, normalize, frequency, yoy_periods keys.
            Optional cotality_csv for housing overlay.

    Returns:
        DataFrame with [date, value] columns (quarterly, YoY % change),
        or None if data unavailable. May set df.attrs['indicator_meta'].
    """
    csv_file = config.get("csv_file")
    if csv_file is None:
        return None

    # Housing (and any dual-source config): one resolver for index + overlay
    if config.get("cotality_csv") or name == "housing":
        index_df, cotality_df, data_source = _resolve_index_and_overlay(config)
    else:
        index_df = load_indicator_csv(pipeline.config.DATA_DIR / csv_file)
        cotality_df, data_source = None, None

    yoy_df = None
    if index_df is not None and len(index_df) > 0:
        yoy_df = _normalize_index_frame(index_df, config, name)

    if yoy_df is None and cotality_df is None:
        return None
    if yoy_df is None:
        yoy_df = cotality_df[["date", "value"]].copy()
        yoy_df.attrs["indicator_meta"] = {
            "data_source": "Cotality HVI",
            "stale_display": "quarter_only",
        }
        return yoy_df.reset_index(drop=True)

    yoy_df = _attach_indicator_meta(
        yoy_df,
        data_source=data_source,
        cotality_df=cotality_df,
        name=name,
    )
    # Column subset can drop attrs in some pandas versions — re-attach.
    meta = dict(yoy_df.attrs.get("indicator_meta") or {})
    out = yoy_df[["date", "value"]].reset_index(drop=True)
    out.attrs["indicator_meta"] = meta
    return out


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
    df["date"] = pd.to_datetime(df["date"])
    df["meeting_date"] = pd.to_datetime(df["meeting_date"])

    # Sort by date descending to get the most recent scrape
    df = df.sort_values("date", ascending=False)

    # Get the latest scrape date
    latest_date = df["date"].iloc[0]
    latest_rows = df[df["date"] == latest_date]

    # From the latest scrape, find the next upcoming meeting
    # (meeting_date >= today)
    today = pd.Timestamp.now().normalize()
    future_meetings = latest_rows[latest_rows["meeting_date"] >= today]

    if future_meetings.empty:
        # All meetings in the past -- use the latest meeting as fallback
        next_meeting_row = latest_rows.iloc[0]
        # No future meetings to build array from
        upcoming_meetings = future_meetings  # empty DataFrame
    else:
        # Pick the nearest future meeting
        upcoming_meetings = future_meetings.sort_values("meeting_date")
        next_meeting_row = upcoming_meetings.iloc[0]

    # Build multi-meeting list: next 3-4 upcoming meetings
    meetings = []
    for _, row in upcoming_meetings.head(4).iterrows():
        meetings.append({
            "meeting_date": row["meeting_date"].strftime("%Y-%m-%d"),
            "implied_rate": float(row["implied_rate"]),
            "change_bp": float(row["change_bp"]),
            "probability_cut": float(row["probability_cut"]),
            "probability_hold": float(row["probability_hold"]),
            "probability_hike": float(row["probability_hike"]),
        })

    return {
        "data_date": latest_date.strftime("%Y-%m-%d"),
        "meeting_date": next_meeting_row["meeting_date"].strftime("%Y-%m-%d"),
        "implied_rate": float(next_meeting_row["implied_rate"]),
        "change_bp": float(next_meeting_row["change_bp"]),
        "probability_cut": float(next_meeting_row["probability_cut"]),
        "probability_hold": float(next_meeting_row["probability_hold"]),
        "probability_hike": float(next_meeting_row["probability_hike"]),
        "meetings": meetings,
    }
