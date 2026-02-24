"""
ASX 30-Day Interbank Cash Rate Futures scraper.

Fetches IB futures settlement data from the MarkitDigital API and derives
market-implied RBA cash rate expectations for upcoming meetings.

The implied cash rate for each contract month is calculated as:
    implied_rate = 100 - settlement_price

Probabilities are derived by comparing the implied rate against the current
cash rate (sourced from data/rba_cash_rate.csv).
"""

import json
import logging
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import pandas as pd

from pipeline.config import ASX_FUTURES_URLS, DATA_DIR, BROWSER_USER_AGENT, DEFAULT_TIMEOUT
from pipeline.utils.http_client import create_session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _get_current_cash_rate() -> float:
    """
    Read the current RBA cash rate from data/rba_cash_rate.csv.

    Returns:
        Current cash rate as a percentage (e.g., 3.85).
        Falls back to 4.35 if the file is missing or unreadable.
    """
    csv_path = DATA_DIR / "rba_cash_rate.csv"
    try:
        df = pd.read_csv(csv_path)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        rate = float(df.iloc[-1]['value'])
        logger.info(f"Current cash rate from CSV: {rate}%")
        return rate
    except Exception as e:
        logger.warning(f"Could not read cash rate CSV, using fallback: {e}")
        return 4.35


def _get_rba_meeting_dates() -> List[str]:
    """
    Load RBA meeting dates from public/data/meetings.json.

    Returns:
        Sorted list of meeting date strings (YYYY-MM-DD) for upcoming meetings.
    """
    meetings_path = Path("public/data/meetings.json")
    try:
        with open(meetings_path) as f:
            data = json.load(f)
        dates = []
        for key in sorted(data.keys()):
            if key.startswith('meetings_'):
                for m in data[key]:
                    date_str = m['date'][:10]  # Extract YYYY-MM-DD from ISO string
                    dates.append(date_str)
        return sorted(dates)
    except Exception as e:
        logger.warning(f"Could not load meetings.json: {e}")
        return []


def _find_meeting_for_contract(contract_expiry: str, meeting_dates: List[str]) -> Optional[str]:
    """
    Find the RBA meeting date that a futures contract most closely covers.

    IB futures settle on the last business day of the month. The contract
    expiring in a given month reflects the average cash rate for that month.
    We match each contract to the RBA meeting in the same month, or the
    nearest future meeting if none falls in the same month.

    Args:
        contract_expiry: Contract expiry date as YYYY-MM-DD.
        meeting_dates: Sorted list of RBA meeting dates.

    Returns:
        Matching meeting date string, or None if no suitable meeting found.
    """
    contract_dt = datetime.strptime(contract_expiry, '%Y-%m-%d')
    contract_ym = contract_dt.strftime('%Y-%m')

    # First, look for a meeting in the same month as the contract
    for md in meeting_dates:
        if md.startswith(contract_ym):
            return md

    # If no meeting in the contract month, find the nearest future meeting
    for md in meeting_dates:
        meeting_dt = datetime.strptime(md, '%Y-%m-%d')
        if meeting_dt >= contract_dt:
            return md

    return None


def _derive_probabilities(implied_rate: float, current_rate: float) -> Tuple[float, int, int, int]:
    """
    Derive rate movement probabilities from implied vs current rate.

    A standard RBA move is 25bp. The probability of a cut or hike is
    proportional to how far the implied rate has moved from the current rate.

    Args:
        implied_rate: Market-implied rate (percentage, e.g., 3.82).
        current_rate: Current cash rate (percentage, e.g., 3.85).

    Returns:
        Tuple of (change_bp, probability_cut, probability_hold, probability_hike)
        where probabilities are percentages (0-100) that sum to 100.
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
        # Within +/-5bp deadband — assume hold
        probability_hold = 100
        probability_cut = 0
        probability_hike = 0

    return (change_bp, probability_cut, probability_hold, probability_hike)


def scrape_asx_futures() -> pd.DataFrame:
    """
    Scrape ASX 30-day IB futures data from the MarkitDigital API.

    Returns:
        DataFrame with columns: [date, meeting_date, implied_rate, change_bp,
                                probability_cut, probability_hold, probability_hike]

    Raises:
        Exception: If fetching or parsing fails.
    """
    session = create_session(retries=3, backoff_factor=0.5, user_agent=BROWSER_USER_AGENT)

    url = ASX_FUTURES_URLS["ib_futures"]
    logger.info(f"Fetching IB futures from {url}")

    response = session.get(url, timeout=DEFAULT_TIMEOUT)
    response.raise_for_status()

    data = response.json()
    items = data.get('data', {}).get('items', [])

    if not items:
        logger.warning("No futures items returned from API")
        return pd.DataFrame()

    logger.info(f"Received {len(items)} futures contracts")

    # Get current cash rate and RBA meeting dates
    current_rate = _get_current_cash_rate()
    meeting_dates = _get_rba_meeting_dates()

    scrape_date = datetime.now().strftime('%Y-%m-%d')
    rows = []

    for item in items:
        expiry = item.get('dateExpiry')
        settlement = item.get('pricePreviousSettlement')

        if not expiry or settlement is None:
            continue

        # Implied cash rate = 100 - futures settlement price
        implied_rate = round(100 - float(settlement), 3)

        # Validate rate range
        if not (0 <= implied_rate <= 15):
            logger.warning(f"Implied rate {implied_rate} outside expected range 0-15%")
            continue

        # Match to RBA meeting
        meeting_date = _find_meeting_for_contract(expiry, meeting_dates)
        if not meeting_date:
            # Use the contract expiry as a proxy if no meeting found
            meeting_date = expiry

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
    logger.info(f"Extracted {len(df)} meeting expectations from ASX IB futures")
    return df


def _check_staleness(csv_path: Path) -> None:
    """
    Check if the ASX futures CSV contains stale data and log warnings.

    Non-fatal — ASX is an optional tier. Logs a warning at 14 days and an
    error at 30 days without raising. Called after every successful CSV write
    so operators know when the endpoint is returning stale data.

    Args:
        csv_path: Path to the asx_futures.csv file.
    """
    try:
        df = pd.read_csv(csv_path)
        df['date'] = pd.to_datetime(df['date'])
        staleness_days = (datetime.now() - df['date'].max()).days
        if staleness_days >= 30:
            logger.error(
                f"ASX futures data is {staleness_days} days old (threshold: 30). "
                "Endpoint may be down or data is missing."
            )
        elif staleness_days >= 14:
            logger.warning(
                f"ASX futures data is {staleness_days} days old (threshold: 14). "
                "Fresh data expected but not received."
            )
    except Exception as e:
        logger.warning(f"Could not check ASX staleness: {e}")


def fetch_and_save() -> Dict[str, Union[str, int]]:
    """
    Fetch ASX futures data and save to CSV.
    Returns status dict — logs errors but doesn't raise (graceful degradation).

    Returns:
        Dict with 'status' key ('success' or 'failed') and additional info.
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

        if output_path.exists() and output_path.stat().st_size > 0:
            try:
                existing_df = pd.read_csv(output_path)
                combined_df = pd.concat([existing_df, df], ignore_index=True)
                # Deduplicate on composite key [date, meeting_date], keeping latest
                result_df = combined_df.drop_duplicates(subset=['date', 'meeting_date'], keep='last')
            except (pd.errors.EmptyDataError, pd.errors.ParserError):
                logger.warning("Existing CSV unreadable, overwriting")
                result_df = df
        else:
            result_df = df

        # Write to CSV
        result_df.to_csv(output_path, index=False)

        # Check for stale data even after a successful scrape — the endpoint
        # may return data but the max date may still be old
        _check_staleness(output_path)

        logger.info(f"ASX futures data saved: {len(result_df)} total rows, {len(df)} new")
        return {
            'status': 'success',
            'rows': len(result_df),
            'meetings': len(df)
        }

    except Exception as e:
        # Log error but don't crash — allows pipeline to continue with other sources
        logger.error(f"ASX scraper failed: {e}")
        logger.debug(traceback.format_exc())
        return {
            'status': 'failed',
            'error': str(e)
        }


if __name__ == '__main__':
    print("ASX 30-Day Interbank Cash Rate Futures Scraper")
    print("=" * 50)
    result = fetch_and_save()
    print(f"\nResult: {result}")

    if result['status'] == 'success':
        try:
            df = pd.read_csv(DATA_DIR / "asx_futures.csv")
            print(f"\nData sample (first 5 rows):")
            print(df.head())
        except Exception as e:
            print(f"Could not read CSV: {e}")
