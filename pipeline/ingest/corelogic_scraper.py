"""
Cotality (formerly CoreLogic) Housing Value Index PDF scraper.
Downloads monthly HVI media release PDFs, extracts national annual YoY % change.

OPTIONAL source - fails gracefully if scraping unsuccessful.
Filename kept as corelogic_scraper.py for codebase continuity (Cotality rebrand 2024).
"""

import io
import logging
import re
import traceback
from datetime import datetime, timedelta

import pandas as pd
import requests

from pipeline.config import BROWSER_USER_AGENT, DATA_DIR, DEFAULT_TIMEOUT
from pipeline.utils.csv_handler import append_to_csv
from pipeline.utils.http_client import create_session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MONTH_ABBREV = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
    7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
}

OUTPUT_FILE = "corelogic_housing.csv"


def get_candidate_urls(year: int, month: int) -> list:
    """
    Return candidate Cotality HVI PDF URLs to try in order.

    URL pattern is inconsistent across months (confirmed by research):
    - Jan/Feb 2026: discover.cotality.com/hubfs/
      Article-Reports/COTALITY HVI {Mon} {Year} FINAL.pdf
    - Dec 2025: discover.cotality.com/hubfs/Article-Reports/Cotality_HVI_December.pdf
    - Nov 2025: different pattern entirely (404 on standard patterns)

    Strategy: try multiple candidate URLs, proceed with first 200 response.
    """
    mon = MONTH_ABBREV[month]
    mon_full = datetime(year, month, 1).strftime("%B")

    base_discover = "https://discover.cotality.com/hubfs/Article-Reports"
    base_pages = "https://pages.cotality.com/hubfs/CoreLogic%20AU/Article%20Reports"

    return [
        f"{base_discover}/COTALITY%20HVI%20{mon}%20{year}%20FINAL.pdf",
        f"{base_discover}/Cotality_HVI_{mon_full}.pdf",
        f"{base_pages}/COTALITY%20HVI%20{mon_full}%20{year}%20FINAL.pdf",
        f"{base_pages}/COTALITY%20HVI%20{mon}%20{year}%20FINAL.pdf",
    ]


def download_cotality_pdf(
    year: int, month: int, session: requests.Session
) -> bytes | None:
    """
    Try candidate URLs to download Cotality HVI PDF for given month.

    Returns:
        PDF bytes if found, None if all candidates fail.
    """
    candidates = get_candidate_urls(year, month)

    for url in candidates:
        try:
            resp = session.get(url, timeout=DEFAULT_TIMEOUT)
            content_type = resp.headers.get(
                'content-type', ''
            )
            if (resp.status_code == 200
                    and content_type.startswith('application/pdf')):
                logger.info(f"Cotality PDF found at: {url}")
                return resp.content
        except Exception:
            continue

    logger.warning(
        f"Cotality PDF not found for {MONTH_ABBREV[month]} {year} "
        f"-- tried {len(candidates)} candidate URLs"
    )
    return None


def extract_cotality_yoy(pdf_bytes: bytes) -> float | None:
    """
    Extract national annual YoY % from Cotality HVI PDF bytes.

    The PDF contains a line like: "Australia 0.8% 2.4% 9.4%"
    (month / 3-month / 12-month change). We extract the 3rd value (annual).

    Returns:
        Float YoY % change (e.g., 9.4) or None if pattern not found.
    """
    try:
        import pdfplumber
    except ImportError:
        logger.error(
            "pdfplumber not installed -- "
            "run: pip install pdfplumber>=0.11,<1.0"
        )
        return None

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages[:4]:
            text = page.extract_text() or ""
            match = re.search(
                r'Australia\s+([-\d.]+)%\s+([-\d.]+)%\s+([-\d.]+)%',
                text
            )
            if match:
                annual_pct = float(match.group(3))
                logger.info(f"Extracted national annual change: {annual_pct}%")
                return annual_pct

    logger.warning("Could not find 'Australia X% X% X%' pattern in PDF")
    return None


def _current_month_already_scraped(output_path) -> bool:
    """
    Check if the current month's Cotality data is already in the CSV.
    Prevents duplicate rows when pipeline runs multiple times per month.
    """
    if not output_path.exists():
        return False

    try:
        df = pd.read_csv(output_path)
        if df.empty or 'source' not in df.columns:
            return False

        cotality_rows = df[df['source'] == 'Cotality HVI']
        if cotality_rows.empty:
            return False

        cotality_rows = cotality_rows.copy()
        cotality_rows['date'] = pd.to_datetime(cotality_rows['date'])
        latest = cotality_rows['date'].max()
        now = datetime.now()

        # If latest Cotality row is from current month, skip
        if latest.year == now.year and latest.month == now.month:
            logger.info(
                f"Current month ({now.strftime('%b %Y')}) "
                "already scraped -- skipping"
            )
            return True
    except Exception:
        pass

    return False


def scrape_cotality() -> pd.DataFrame:
    """
    Scrape Cotality HVI PDF for the current month's national YoY % change.

    Returns:
        DataFrame with one row [date, value, source, series_id] or empty DataFrame.
    """
    output_path = DATA_DIR / OUTPUT_FILE

    # Idempotency: skip if current month already scraped
    if _current_month_already_scraped(output_path):
        return pd.DataFrame(columns=['date', 'value', 'source', 'series_id'])

    session = create_session(
        retries=3, backoff_factor=0.5,
        user_agent=BROWSER_USER_AGENT,
    )

    now = datetime.now()

    # Try current month first, then previous month (PDF may lag by a few days)
    months_to_try = [
        (now.year, now.month),
    ]
    prev = now.replace(day=1) - timedelta(days=1)
    months_to_try.append((prev.year, prev.month))

    for year, month in months_to_try:
        pdf_bytes = download_cotality_pdf(year, month, session)
        if pdf_bytes is None:
            continue

        yoy_pct = extract_cotality_yoy(pdf_bytes)
        if yoy_pct is None:
            continue

        # Build the data row: date is last day of the reference month
        if month == 12:
            period_end = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            period_end = datetime(year, month + 1, 1) - timedelta(days=1)

        row = pd.DataFrame([{
            'date': period_end.strftime('%Y-%m-%d'),
            'value': yoy_pct,
            'source': 'Cotality HVI',
            'series_id': 'Cotality/HVI/National/Annual',
        }])

        logger.info(
            f"Cotality HVI data for "
            f"{MONTH_ABBREV[month]} {year}: {yoy_pct}% YoY"
        )
        return row

    logger.warning("Cotality PDF scraper: no data extracted for any candidate month")
    return pd.DataFrame(columns=['date', 'value', 'source', 'series_id'])


def fetch_and_save() -> dict[str, str | int]:
    """
    Fetch Cotality data and save to CSV.
    NEVER raises - returns status dict with success/failure.

    Returns:
        Dict with 'status' key ('success' or 'failed') and additional info
    """
    try:
        df = scrape_cotality()

        if df.empty:
            logger.warning(
                "Cotality scraper returned no new data "
                "(may already be current)"
            )
            return {
                'status': 'failed',
                'error': 'No new Cotality data extracted'
            }

        output_path = DATA_DIR / OUTPUT_FILE
        row_count = append_to_csv(output_path, df, date_column='date')

        logger.info(f"Cotality data saved: {row_count} total rows in {OUTPUT_FILE}")
        return {
            'status': 'success',
            'rows': row_count
        }

    except Exception as e:
        logger.warning(f"Cotality scraper failed (optional source): {e}")
        logger.debug(traceback.format_exc())
        return {
            'status': 'failed',
            'error': str(e)
        }


if __name__ == '__main__':
    print("Cotality HVI PDF Scraper")
    print("=" * 50)
    result = fetch_and_save()
    print(f"\nResult: {result}")
