"""
NAB Business Survey capacity utilisation scraper.
OPTIONAL source - fails gracefully if scraping unsuccessful.
"""

import logging
import traceback
from datetime import datetime
from typing import Dict, Union

import pandas as pd
from bs4 import BeautifulSoup

from pipeline.config import DATA_DIR, BROWSER_USER_AGENT, DEFAULT_TIMEOUT
from pipeline.utils.csv_handler import append_to_csv
from pipeline.utils.http_client import create_session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def scrape_nab_survey() -> pd.DataFrame:
    """
    Scrape NAB Business Survey capacity utilisation data.

    Returns:
        DataFrame with columns: [date, value, metric, source]

    Raises:
        ValueError: If page structure doesn't match expectations
        requests.RequestException: If HTTP request fails
    """
    session = create_session(retries=3, backoff_factor=0.5, user_agent=BROWSER_USER_AGENT)

    # NAB Business Survey page
    # The actual survey data is published monthly in PDF reports
    target_url = "https://business.nab.com.au/nab-monthly-business-survey-39780/"

    logger.info(f"Fetching NAB Business Survey data from {target_url}")

    try:
        response = session.get(target_url, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'lxml')

        # NAB publishes their business survey as monthly PDF reports
        # The capacity utilisation data is typically in the report body or summary tables
        # This is a placeholder implementation that needs refinement

        # TODO: NAB Business Survey data is in PDF format
        # Options:
        # 1. Parse the PDF directly (requires pypdf or pdfplumber)
        # 2. Look for summary data on the web page (if available)
        # 3. Find the latest report link and parse PDF metadata
        # 4. Use alternative capacity utilisation source (e.g., ABS Business Indicators)

        # Check if we got actual content
        if len(soup.get_text(strip=True)) < 500:
            raise ValueError("NAB page appears to have minimal content - page structure may have changed")

        # Look for links to latest survey reports
        pdf_links = soup.find_all('a', href=lambda x: x and '.pdf' in x.lower())
        if pdf_links:
            logger.info(f"Found {len(pdf_links)} PDF reports on NAB survey page")
            logger.warning("NAB data is in PDF format - scraper needs PDF parsing capability")
        else:
            logger.warning("No PDF links found on NAB survey page")

        # For now, return empty DataFrame with proper structure
        # This allows the scraper to be integrated without blocking other work
        logger.warning("NAB scraper needs refinement - PDF parsing not yet implemented")
        logger.warning("Consider alternative: ABS Business Indicators for capacity utilisation proxy")

        # Return empty but properly structured DataFrame
        return pd.DataFrame(columns=['date', 'value', 'metric', 'source'])

    except Exception as e:
        logger.error(f"Failed to scrape NAB survey: {e}")
        raise


def fetch_and_save() -> Dict[str, Union[str, int]]:
    """
    Fetch NAB Business Survey data and save to CSV.
    NEVER raises - returns status dict with success/failure.

    Returns:
        Dict with 'status' key ('success' or 'failed') and additional info
    """
    try:
        df = scrape_nab_survey()

        if df.empty:
            logger.warning("NAB scraper returned no data (implementation incomplete)")
            return {
                'status': 'failed',
                'error': 'No data extracted - scraper needs PDF parsing capability'
            }

        output_path = DATA_DIR / "nab_capacity.csv"
        row_count = append_to_csv(output_path, df, date_column='date')

        logger.info(f"NAB data saved successfully: {row_count} total rows")
        return {
            'status': 'success',
            'rows': row_count
        }

    except Exception as e:
        # NEVER crash - this is an optional data source
        logger.warning(f"NAB scraper failed (optional source): {e}")
        logger.debug(traceback.format_exc())
        return {
            'status': 'failed',
            'error': str(e)
        }


if __name__ == '__main__':
    print("NAB Business Survey Capacity Utilisation Scraper")
    print("=" * 50)
    result = fetch_and_save()
    print(f"\nResult: {result}")
