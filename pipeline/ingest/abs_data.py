"""
ABS (Australian Bureau of Statistics) data ingestor.
Fetches economic indicators via ABS Data API (SDMX 2.1).
"""

import sys
import pandas as pd
from pipeline.config import ABS_API_BASE, ABS_CONFIG, DATA_DIR, DEFAULT_TIMEOUT
from pipeline.utils.csv_handler import append_to_csv
from pipeline.utils.http_client import create_session


def fetch_abs_series(dataflow_id: str, key: str, params: dict = None, filters: dict = None) -> pd.DataFrame:
    """
    Fetch a data series from ABS Data API.

    Args:
        dataflow_id: ABS dataflow identifier (e.g., "CPI", "LF")
        key: Series key/filter (use "all" for wildcard)
        params: Optional query parameters (e.g., {"startPeriod": "2014"})
        filters: Optional dimension filters to apply after fetching

    Returns:
        DataFrame with columns: date, value, source, series_id
    """
    # Build URL
    url = f"{ABS_API_BASE}/ABS,{dataflow_id}/{key}"

    print(f"Fetching ABS {dataflow_id} from {url}")

    # Create session and set headers
    session = create_session()
    headers = {
        'Accept': 'application/vnd.sdmx.data+csv;labels=both'
    }

    # Make request
    response = session.get(url, headers=headers, params=params, timeout=DEFAULT_TIMEOUT)

    if response.status_code != 200:
        raise Exception(f"ABS API error: {response.status_code} for {url}\nResponse: {response.text[:500]}")

    # Parse CSV response
    df = pd.read_csv(pd.io.common.StringIO(response.text))

    if len(df) == 0:
        raise Exception(f"No data returned from ABS API for {dataflow_id}/{key}")

    # Find TIME_PERIOD and OBS_VALUE columns (they may have labels appended)
    time_col = [c for c in df.columns if c.startswith('TIME_PERIOD')][0]
    value_col = 'OBS_VALUE'

    # Apply filters if specified
    if filters:
        for col_name, filter_value in filters.items():
            # Find matching column (ABS uses format "COLUMN: Label")
            matching_cols = [c for c in df.columns if c.startswith(f"{col_name}:")]
            if matching_cols:
                col = matching_cols[0]
                # Filter by checking if value starts with the filter (handles "code: label" format)
                df = df[df[col].astype(str).str.contains(f"^{filter_value}:", regex=True, na=False)]

        print(f"After filtering: {len(df)} rows")

    # Rename columns
    df = df.rename(columns={
        time_col: 'date',
        value_col: 'value'
    })

    # Parse date column (handles both YYYY-MM and YYYY-QN formats)
    df['date'] = df['date'].apply(_parse_abs_date)

    # Add metadata columns
    df['source'] = 'ABS'
    df['series_id'] = f"{dataflow_id}/{key}"

    # Select only needed columns
    df = df[['date', 'value', 'source', 'series_id']]

    # Drop any rows with missing values
    df = df.dropna(subset=['date', 'value'])

    # Convert value to numeric
    df['value'] = pd.to_numeric(df['value'], errors='coerce')
    df = df.dropna(subset=['value'])

    # Sort by date
    df = df.sort_values('date').reset_index(drop=True)

    print(f"Final: {len(df)} rows for {dataflow_id}")

    return df


def _parse_abs_date(date_str: str) -> str:
    """
    Parse ABS date format to ISO 8601.

    Handles:
    - Monthly: "2024-01" -> "2024-01-01"
    - Quarterly: "2024-Q1" -> "2024-01-01"

    Args:
        date_str: Date string from ABS API

    Returns:
        ISO 8601 date string (YYYY-MM-DD)
    """
    date_str = str(date_str).strip()

    if 'Q' in date_str:
        # Quarterly format: "2024-Q1"
        year, quarter = date_str.split('-Q')
        quarter_month = {
            '1': '01',
            '2': '04',
            '3': '07',
            '4': '10'
        }
        month = quarter_month.get(quarter, '01')
        return f"{year}-{month}-01"
    else:
        # Monthly format: "2024-01"
        if len(date_str) == 7 and date_str[4] == '-':
            return f"{date_str}-01"
        else:
            # Try parsing as-is
            return pd.to_datetime(date_str).strftime('%Y-%m-%d')


# Individual fetchers for each indicator

def fetch_cpi() -> pd.DataFrame:
    """Fetch Consumer Price Index (All Groups, Monthly)."""
    config = ABS_CONFIG["cpi"]
    return fetch_abs_series(
        config["dataflow"],
        config["key"],
        config.get("params"),
        config.get("filters")
    )


def fetch_employment() -> pd.DataFrame:
    """Fetch Labour Force employment (Monthly)."""
    config = ABS_CONFIG["employment"]
    return fetch_abs_series(
        config["dataflow"],
        config["key"],
        config.get("params"),
        config.get("filters")
    )


def fetch_retail_trade() -> pd.DataFrame:
    """Fetch Retail Trade turnover (Monthly)."""
    config = ABS_CONFIG["retail_trade"]
    return fetch_abs_series(
        config["dataflow"],
        config["key"],
        config.get("params"),
        config.get("filters")
    )


def fetch_wage_price_index() -> pd.DataFrame:
    """Fetch Wage Price Index (Quarterly)."""
    config = ABS_CONFIG["wage_price_index"]
    return fetch_abs_series(
        config["dataflow"],
        config["key"],
        config.get("params"),
        config.get("filters")
    )


def fetch_building_approvals() -> pd.DataFrame:
    """
    Fetch Building Approvals for total dwellings (Monthly).

    NOTE: Building approvals dataflow not currently available in ABS Data API.
    This is a placeholder for future implementation.
    """
    raise NotImplementedError("Building approvals dataflow not found in ABS Data API. Needs investigation.")


# Fetcher registry
FETCHERS = {
    'cpi': (fetch_cpi, ABS_CONFIG["cpi"]["output_file"]),
    'employment': (fetch_employment, ABS_CONFIG["employment"]["output_file"]),
    'retail_trade': (fetch_retail_trade, ABS_CONFIG["retail_trade"]["output_file"]),
    'wage_price_index': (fetch_wage_price_index, ABS_CONFIG["wage_price_index"]["output_file"]),
    # 'building_approvals': (fetch_building_approvals, ABS_CONFIG["building_approvals"]["output_file"]),
}


def fetch_and_save(series: str = None) -> dict:
    """
    Fetch and save ABS data series.

    Args:
        series: Optional specific series name (e.g., "cpi"). If None, fetches all.

    Returns:
        Dict mapping series name to row count
    """
    results = {}

    if series:
        # Fetch single series
        if series not in FETCHERS:
            raise ValueError(f"Unknown series: {series}. Available: {list(FETCHERS.keys())}")

        fetch_func, output_file = FETCHERS[series]
        df = fetch_func()
        output_path = DATA_DIR / output_file
        row_count = append_to_csv(output_path, df)
        results[series] = row_count
    else:
        # Fetch all series
        for name, (fetch_func, output_file) in FETCHERS.items():
            print(f"\n--- Fetching {name} ---")
            try:
                df = fetch_func()
                output_path = DATA_DIR / output_file
                row_count = append_to_csv(output_path, df)
                results[name] = row_count
            except Exception as e:
                print(f"ERROR fetching {name}: {e}")
                results[name] = 0

    return results


if __name__ == '__main__':
    print("=== ABS Economic Data Ingestor ===\n")

    # Check for series argument
    series_arg = sys.argv[1] if len(sys.argv) > 1 else None

    results = fetch_and_save(series_arg)

    print("\n=== Summary ===")
    for name, count in results.items():
        status = "✓" if count > 0 else "✗"
        print(f"{status} {name}: {count} rows")
