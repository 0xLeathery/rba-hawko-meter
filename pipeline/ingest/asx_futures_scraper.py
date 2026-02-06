"""
ASX RBA Rate Tracker futures scraper.
CRITICAL source - provides daily market expectations for RBA rate decisions.

Fetches JSON data from ASX DAM public endpoints instead of HTML parsing.
"""

import json
import logging
import traceback
from datetime import datetime
from typing import Dict, List, Tuple, Union

import pandas as pd

from pipeline.config import ASX_FUTURES_URLS, DATA_DIR, BROWSER_USER_AGENT, DEFAULT_TIMEOUT
from pipeline.utils.http_client import create_session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _fetch_json(session, url: str, label: str) -> Dict:
    """
    Fetch JSON data from a URL.

    Args:
        session: requests.Session instance
        url: URL to fetch
        label: Label for logging

    Returns:
        Parsed JSON response as dict

    Raises:
        requests.RequestException: If request fails
    """
    logger.info(f"Fetching {label} from {url}")
    try:
        response = session.get(url, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Failed to fetch {label}: {e}")
        raise


def _derive_probabilities(implied_rate: float, current_rate: float) -> Tuple[float, int, int, int]:
    """
    Derive rate movement probabilities from implied vs current rate.

    Args:
        implied_rate: Market-implied rate (percentage, e.g., 4.10)
        current_rate: Current cash rate (percentage, e.g., 4.35)

    Returns:
        Tuple of (change_bp, probability_cut, probability_hold, probability_hike)
        where probabilities are percentages (0-100) that sum to 100
    """
    change_bp = round((implied_rate - current_rate) * 100, 1)

    if change_bp < -5:
        # Implied cut
        probability_cut = min(100, round(abs(change_bp) / 25 * 100))
        probability_hold = 100 - probability_cut
        probability_hike = 0
    elif change_bp > 5:
        # Implied hike
        probability_hike = min(100, round(change_bp / 25 * 100))
        probability_hold = 100 - probability_hike
        probability_cut = 0
    else:
        # Within +/-5bp deadband - assume hold
        probability_hold = 100
        probability_cut = 0
        probability_hike = 0

    return (change_bp, probability_cut, probability_hold, probability_hike)


def scrape_asx_futures() -> pd.DataFrame:
    """
    Scrape ASX RBA Rate Tracker futures data from JSON endpoints.

    Returns:
        DataFrame with columns: [date, meeting_date, implied_rate, change_bp,
                                probability_cut, probability_hold, probability_hike]

    Raises:
        Exception: If fetching or parsing fails
    """
    session = create_session(retries=3, backoff_factor=0.5, user_agent=BROWSER_USER_AGENT)

    # Fetch current cash rate from dynamic text endpoint
    dynamic_data = _fetch_json(session, ASX_FUTURES_URLS["dynamic_text"], "dynamic text")
    current_rate = float(dynamic_data["currentCashRate"])
    logger.info(f"Current cash rate: {current_rate}%")

    # Fetch market expectations from main endpoint
    expectations_data = _fetch_json(session, ASX_FUTURES_URLS["market_expectations"], "market expectations")

    # Extract meeting expectations array
    meetings = expectations_data.get("meetings", expectations_data.get("data", []))
    if not meetings:
        logger.warning("No meetings array found in expectations data")
        return pd.DataFrame()

    # Log structure of first entry for debugging
    if meetings:
        logger.debug(f"First meeting entry keys: {list(meetings[0].keys())}")

    scrape_date = datetime.now().strftime('%Y-%m-%d')
    rows = []

    for meeting in meetings:
        # Parse meeting date
        meeting_date_str = meeting.get("meetingDate") or meeting.get("date")
        if not meeting_date_str:
            logger.warning(f"No meeting date in entry: {meeting}")
            continue

        # Try to parse date - try ISO format first, then day-month-year
        try:
            if "-" in str(meeting_date_str) and len(str(meeting_date_str)) == 10:
                # Already ISO format YYYY-MM-DD
                meeting_date = str(meeting_date_str)
            else:
                # Try parsing "18 Feb 2026" format
                parsed = datetime.strptime(str(meeting_date_str), "%d %b %Y")
                meeting_date = parsed.strftime("%Y-%m-%d")
        except ValueError:
            logger.warning(f"Could not parse meeting date: {meeting_date_str}")
            continue

        # Extract implied rate - try multiple possible key names
        implied_rate = None
        for key in ["impliedRate", "ExpectedRate", "expectedRate", "rate"]:
            if key in meeting:
                try:
                    implied_rate = float(meeting[key])
                    break
                except (ValueError, TypeError):
                    continue

        if implied_rate is None:
            logger.warning(f"No implied rate found in meeting: {meeting}")
            continue

        # Validate rate range
        if not (0 <= implied_rate <= 15):
            logger.warning(f"Implied rate {implied_rate} outside expected range 0-15%")

        # Derive probabilities
        change_bp, prob_cut, prob_hold, prob_hike = _derive_probabilities(implied_rate, current_rate)

        rows.append({
            "date": scrape_date,
            "meeting_date": meeting_date,
            "implied_rate": implied_rate,
            "change_bp": change_bp,
            "probability_cut": prob_cut,
            "probability_hold": prob_hold,
            "probability_hike": prob_hike,
        })

    df = pd.DataFrame(rows)
    logger.info(f"Extracted {len(df)} meeting expectations from ASX")
    return df


def fetch_and_save() -> Dict[str, Union[str, int]]:
    """
    Fetch ASX futures data and save to CSV.
    Returns status dict - logs errors but doesn't raise (graceful degradation).

    Returns:
        Dict with 'status' key ('success' or 'failed') and additional info
    """
    try:
        df = scrape_asx_futures()

        if df.empty:
            logger.warning("ASX scraper returned no data")
            return {
                'status': 'failed',
                'error': 'No data extracted from ASX endpoints'
            }

        # Write to CSV with composite-key deduplication
        output_path = DATA_DIR / "asx_futures.csv"

        if output_path.exists():
            # Read existing data and merge
            existing_df = pd.read_csv(output_path)
            combined_df = pd.concat([existing_df, df], ignore_index=True)
            # Deduplicate on composite key [date, meeting_date], keeping latest
            result_df = combined_df.drop_duplicates(subset=['date', 'meeting_date'], keep='last')
        else:
            result_df = df

        # Write to CSV
        result_df.to_csv(output_path, index=False)

        logger.info(f"ASX futures data saved successfully: {len(result_df)} total rows, {len(df)} new meetings")
        return {
            'status': 'success',
            'rows': len(result_df),
            'meetings': len(df)
        }

    except Exception as e:
        # Log error but don't crash - allows pipeline to continue with other sources
        logger.error(f"ASX scraper failed: {e}")
        logger.debug(traceback.format_exc())
        return {
            'status': 'failed',
            'error': str(e)
        }


if __name__ == '__main__':
    print("ASX RBA Rate Tracker Scraper")
    print("=" * 50)
    result = fetch_and_save()
    print(f"\nResult: {result}")

    # If successful, show a sample of the data
    if result['status'] == 'success':
        try:
            df = pd.read_csv(DATA_DIR / "asx_futures.csv")
            print(f"\nData sample (first 5 rows):")
            print(df.head())
        except Exception as e:
            print(f"Could not read CSV: {e}")
