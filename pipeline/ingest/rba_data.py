"""
RBA (Reserve Bank of Australia) data ingestor.
Fetches cash rate target from RBA statistical tables.
"""

import io
import logging

import pandas as pd

import pipeline.config
from pipeline.config import DEFAULT_TIMEOUT, RBA_BASE_URL, RBA_CONFIG
from pipeline.utils.csv_handler import append_to_csv
from pipeline.utils.http_client import create_session

logger = logging.getLogger(__name__)


def fetch_cash_rate() -> pd.DataFrame:
    """
    Fetch RBA cash rate target data from RBA Table A2.

    Returns:
        DataFrame with columns: date, value, source
    """
    config = RBA_CONFIG["cash_rate"]
    url = f"{RBA_BASE_URL}/{config['table_id']}{config['url_suffix']}"

    print(f"Fetching RBA cash rate from {url}")

    session = create_session()
    response = session.get(url, timeout=DEFAULT_TIMEOUT)
    response.raise_for_status()

    # RBA CSVs have metadata rows at the top
    # Find the header row by looking for "Series ID" or similar
    lines = response.text.splitlines()
    header_row = 0

    for i, line in enumerate(lines):
        if 'Series ID' in line or 'Series Id' in line:
            header_row = i
            break

    # Read CSV skipping metadata rows
    df = pd.read_csv(
        io.StringIO(response.text),
        skiprows=header_row
    )

    # The first column is date (DD-Mon-YYYY format)
    # The second column is "New Cash Rate Target"
    date_col = df.columns[0]
    value_col = df.columns[2]  # "New Cash Rate Target" is the 3rd column (index 2)

    # Extract and clean data
    df = df[[date_col, value_col]].copy()
    df.columns = ['date', 'value']

    # Parse dates with dayfirst=True for Australian format
    df['date'] = pd.to_datetime(df['date'], dayfirst=True, errors='coerce')

    # Drop rows with invalid dates
    df = df.dropna(subset=['date'])

    # Clean value column - remove ranges like "17.00 to 17.50"
    # and keep only the upper value
    # Some early entries have ranges, extract the number
    df['value'] = df['value'].astype(str).str.extract(r'([\d.]+)$')[0]

    # Convert to numeric and drop any remaining NaN values
    df['value'] = pd.to_numeric(df['value'], errors='coerce')
    df = df.dropna(subset=['value'])

    # Convert date to ISO 8601 string format
    df['date'] = df['date'].dt.strftime('%Y-%m-%d')

    # Add source column
    df['source'] = 'RBA'

    print(f"Fetched {len(df)} rows of RBA cash rate data")

    return df


def fetch_and_save() -> int:
    """
    Fetch RBA cash rate data and save to CSV.

    Returns:
        Number of rows written
    """
    logger.info("DATA_DIR: %s", pipeline.config.DATA_DIR)
    df = fetch_cash_rate()

    output_path = pipeline.config.DATA_DIR / RBA_CONFIG["cash_rate"]["output_file"]
    row_count = append_to_csv(output_path, df)

    return row_count


if __name__ == '__main__':
    print("=== RBA Cash Rate Ingestor ===")
    rows = fetch_and_save()
    print(f"Completed: {rows} total rows in output file")
