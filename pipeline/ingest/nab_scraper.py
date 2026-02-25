"""
NAB Business Survey capacity utilisation scraper.
URL discovery via tag archive — never constructs URLs from date templates.
HTML extraction primary, PDF fallback on failure (NAB-01, NAB-02, NAB-05).

Idempotent: skips if current month already in CSV.
Backfill: tries last 12 months on first run (when CSV is missing or sparse).
"""

import io
import logging
import re
import traceback
from datetime import datetime, timedelta

import pandas as pd
from bs4 import BeautifulSoup
from dateutil.relativedelta import relativedelta

import pipeline.config
from pipeline.config import BROWSER_USER_AGENT, DEFAULT_TIMEOUT
from pipeline.utils.csv_handler import append_to_csv
from pipeline.utils.http_client import create_session

logger = logging.getLogger(__name__)

OUTPUT_FILE = "nab_capacity.csv"
NAB_BASE = "https://business.nab.com.au"

TAG_ARCHIVE_URLS = [
    f"{NAB_BASE}/tag/economic-commentary",
    f"{NAB_BASE}/tag/business-survey",
]

# Matches both Australian (utilisation) and US (utilization) spelling via sa?tion
CAPACITY_REGEX = re.compile(
    r'[Cc]apacity utilisa?tion[^.]*?([\d]+\.?\d*)%',
    re.IGNORECASE
)

# URL patterns for backfill (historical months where tag
# archive doesn't list old articles).
# This is the ONLY place URLs are constructed from date
# templates — never for current-month discovery.
MONTH_URL_PATTERNS: list = [
    # Pattern A: /tag/economic-commentary/ slug with triple
    # hyphens (late 2025+)
    lambda m, y: (
        f"{NAB_BASE}/tag/economic-commentary/"
        f"nab-monthly-business-survey---{m}-{y}"
    ),
    # Pattern B: root-level with trailing slash (2024-)
    lambda m, y: (
        f"{NAB_BASE}/nab-monthly-business-survey-{m}-{y}/"
    ),
    # Pattern C: root-level without trailing slash (2025)
    lambda m, y: (
        f"{NAB_BASE}/nab-monthly-business-survey-{m}-{y}"
    ),
]


def discover_latest_survey_url(session) -> str | None:
    """
    Crawl NAB tag archive pages to find the most recent Monthly Business Survey URL.

    Tries TAG_ARCHIVE_URLS in order, returns the first href containing
    "monthly-business-survey" as an absolute URL. Returns None if not found.

    NEVER constructs URLs from date templates — tag archive is the source of truth
    for the current month's article URL.
    """
    for archive_url in TAG_ARCHIVE_URLS:
        try:
            resp = session.get(archive_url, timeout=DEFAULT_TIMEOUT)
            if resp.status_code != 200:
                logger.warning(
                    f"NAB: tag archive {archive_url} "
                    f"returned {resp.status_code}"
                )
                continue
            soup = BeautifulSoup(resp.content, 'lxml')
            for a in soup.find_all('a', href=True):
                href = a['href']
                if 'monthly-business-survey' in href.lower():
                    return href if href.startswith('http') else NAB_BASE + href
        except Exception as e:
            logger.warning(f"NAB: tag archive fetch failed for {archive_url}: {e}")
    return None


def fetch_article(url: str, session) -> bytes | None:
    """Fetch article HTML, return bytes or None on any error."""
    try:
        resp = session.get(url, timeout=DEFAULT_TIMEOUT)
        if resp.status_code == 200:
            return resp.content
        logger.debug(f"NAB: article fetch returned {resp.status_code} for {url}")
    except Exception as e:
        logger.debug(f"NAB: article fetch exception for {url}: {e}")
    return None


def extract_capacity_from_html(html_bytes: bytes) -> float | None:
    """
    Extract capacity utilisation % from NAB Monthly Business Survey article HTML.

    Searches <p>, <li>, and <div> tags for the CAPACITY_REGEX pattern.
    Returns float percentage or None if not found.
    """
    soup = BeautifulSoup(html_bytes, 'lxml')
    for tag in soup.find_all(['p', 'li', 'div']):
        text = tag.get_text()
        m = CAPACITY_REGEX.search(text)
        if m:
            return float(m.group(1))
    return None


def get_pdf_link(html_bytes: bytes) -> str | None:
    """
    Extract the first PDF link from article HTML anchor tags.

    Returns absolute URL or None if no PDF link found.
    """
    soup = BeautifulSoup(html_bytes, 'lxml')
    for a in soup.find_all('a', href=True):
        if '.pdf' in a['href'].lower():
            href = a['href']
            return href if href.startswith('http') else NAB_BASE + href
    return None


def extract_capacity_from_pdf(pdf_bytes: bytes) -> float | None:
    """
    PDF fallback: apply the same CAPACITY_REGEX to pdfplumber-extracted text.

    Scans the first 6 pages. Returns float percentage or None.
    """
    try:
        import pdfplumber
    except ImportError:
        logger.error("NAB: pdfplumber not installed — PDF fallback unavailable")
        return None
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages[:6]:
                text = page.extract_text() or ""
                m = CAPACITY_REGEX.search(text)
                if m:
                    return float(m.group(1))
    except Exception as e:
        logger.warning(f"NAB: pdfplumber extraction failed: {e}")
    return None


def _current_month_already_scraped(output_path) -> bool:
    """
    Idempotency check: return True if current month's data is already in the CSV.

    Mirrors the pattern from corelogic_scraper.py.
    """
    if not output_path.exists():
        return False
    try:
        df = pd.read_csv(output_path)
        if df.empty:
            return False
        df['date'] = pd.to_datetime(df['date'])
        latest = df['date'].max()
        now = datetime.now()
        if latest.year == now.year and latest.month == now.month:
            logger.info("NAB: current month already scraped — skipping")
            return True
    except Exception:
        pass
    return False


def backfill_nab_history(session, months: int = 12) -> int:
    """
    Backfill last N months of NAB capacity utilisation data.

    For each historical month, tries MONTH_URL_PATTERNS (constructed URLs) in order.
    This is the ONLY place URL construction from date templates is used — the tag
    archive does not list historical articles, so
    pattern-based construction is required.

    Returns the number of months successfully scraped and appended.
    """
    output_path = pipeline.config.DATA_DIR / OUTPUT_FILE
    now = datetime.now()
    scraped = 0

    logger.info(f"NAB: starting backfill for last {months} months")

    for i in range(1, months + 1):
        target = now - relativedelta(months=i)
        month_str = target.strftime('%B').lower()   # e.g. "january"
        year = target.year
        period_start = target.replace(day=1)

        html_bytes = None
        for pattern_fn in MONTH_URL_PATTERNS:
            url = pattern_fn(month_str, year)
            html_bytes = fetch_article(url, session)
            if html_bytes:
                logger.debug(
                    f"NAB backfill: found article for "
                    f"{month_str} {year} at {url}"
                )
                break

        if not html_bytes:
            logger.debug(f"NAB backfill: no article found for {month_str} {year}")
            continue

        capacity_pct = extract_capacity_from_html(html_bytes)

        if capacity_pct is None:
            logger.debug(
                f"NAB backfill: HTML extraction failed for "
                f"{month_str} {year} — trying PDF"
            )
            pdf_url = get_pdf_link(html_bytes)
            if pdf_url:
                try:
                    pdf_resp = session.get(pdf_url, timeout=DEFAULT_TIMEOUT)
                    if pdf_resp.status_code == 200:
                        capacity_pct = extract_capacity_from_pdf(pdf_resp.content)
                except Exception as e:
                    logger.debug(
                        f"NAB backfill: PDF fetch "
                        f"failed for {month_str} "
                        f"{year}: {e}"
                    )

        if capacity_pct is None:
            logger.debug(
                f"NAB backfill: both HTML and PDF failed "
                f"for {month_str} {year} — skipping"
            )
            continue

        row = pd.DataFrame([{
            'date': period_start.strftime('%Y-%m-%d'),
            'value': capacity_pct,
            'source': 'NAB Monthly Business Survey',
        }])
        append_to_csv(output_path, row, date_column='date')
        logger.info(
            f"NAB backfill: {month_str} {year} — "
            f"capacity utilisation {capacity_pct}%"
        )
        scraped += 1

    logger.info(f"NAB backfill complete: {scraped}/{months} months scraped")
    return scraped


def scrape_nab_capacity() -> pd.DataFrame:
    """
    Main scraper: discover current survey URL from tag archive, extract HTML,
    fall back to PDF if HTML extraction returns None.

    Returns a single-row DataFrame with columns [date, value, source],
    or an empty DataFrame on any failure (logs warning, never raises).

    Date field: first of the reference month (e.g. 2026-01-01 for Jan 2026 data).
    """
    output_path = pipeline.config.DATA_DIR / OUTPUT_FILE
    if _current_month_already_scraped(output_path):
        return pd.DataFrame(columns=['date', 'value', 'source'])

    session = create_session(
        retries=3, backoff_factor=0.5,
        user_agent=BROWSER_USER_AGENT,
    )

    # Trigger backfill if CSV is missing or fewer than 3 rows
    if not output_path.exists():
        logger.info("NAB: CSV missing — running backfill before current-month scrape")
        backfill_nab_history(session, months=12)
    else:
        try:
            existing = pd.read_csv(output_path)
            if len(existing) < 3:
                logger.info(
                    f"NAB: CSV has only {len(existing)} "
                    "rows — running backfill"
                )
                backfill_nab_history(session, months=12)
        except Exception:
            pass

    # Check idempotency again after backfill
    if _current_month_already_scraped(output_path):
        return pd.DataFrame(columns=['date', 'value', 'source'])

    survey_url = discover_latest_survey_url(session)
    if not survey_url:
        logger.warning(
            "NAB: no survey URL discovered from "
            "tag archive — skipping indicator"
        )
        return pd.DataFrame(columns=['date', 'value', 'source'])

    logger.info(f"NAB: fetching survey article {survey_url}")
    html_bytes = fetch_article(survey_url, session)
    if not html_bytes:
        logger.warning(f"NAB: failed to fetch article at {survey_url}")
        return pd.DataFrame(columns=['date', 'value', 'source'])

    # Primary: HTML extraction
    capacity_pct = extract_capacity_from_html(html_bytes)

    # Fallback: PDF extraction
    if capacity_pct is None:
        logger.info("NAB: HTML extraction returned None — attempting PDF fallback")
        pdf_url = get_pdf_link(html_bytes)
        if pdf_url:
            try:
                pdf_resp = session.get(pdf_url, timeout=DEFAULT_TIMEOUT)
                if pdf_resp.status_code == 200:
                    capacity_pct = extract_capacity_from_pdf(pdf_resp.content)
            except Exception as e:
                logger.warning(f"NAB: PDF fetch failed: {e}")
        else:
            logger.debug("NAB: no PDF link found in article HTML")

    if capacity_pct is None:
        logger.warning("NAB: both HTML and PDF extraction failed — no data written")
        return pd.DataFrame(columns=['date', 'value', 'source'])

    # Date: first of the reference month (NAB releases mid-month for prior month)
    now = datetime.now()
    prev = now.replace(day=1) - timedelta(days=1)
    period_start = prev.replace(day=1)

    row = pd.DataFrame([{
        'date': period_start.strftime('%Y-%m-%d'),
        'value': capacity_pct,
        'source': 'NAB Monthly Business Survey',
    }])
    logger.info(
        f"NAB: capacity utilisation {capacity_pct}% "
        f"for {period_start.strftime('%b %Y')}"
    )
    return row


def fetch_and_save() -> dict[str, str | int]:
    """
    Fetch NAB capacity utilisation and save to CSV.

    NEVER raises. Returns status dict: {'status': 'success'/'failed', ...}.
    """
    logger.info("DATA_DIR: %s", pipeline.config.DATA_DIR)
    try:
        df = scrape_nab_capacity()
        if df.empty:
            # Check if data exists from backfill — if so, this is not a failure
            output_path = pipeline.config.DATA_DIR / OUTPUT_FILE
            if output_path.exists():
                try:
                    existing = pd.read_csv(output_path)
                    if not existing.empty:
                        return {'status': 'success', 'rows': len(existing)}
                except Exception:
                    pass
            return {'status': 'failed', 'error': 'No data extracted'}
        output_path = pipeline.config.DATA_DIR / OUTPUT_FILE
        row_count = append_to_csv(output_path, df, date_column='date')
        return {'status': 'success', 'rows': row_count}
    except Exception as e:
        logger.warning(f"NAB scraper failed (optional source): {e}")
        logger.debug(traceback.format_exc())
        return {'status': 'failed', 'error': str(e)}


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    print("NAB Business Survey Capacity Utilisation Scraper")
    print("=" * 50)
    result = fetch_and_save()
    print(f"\nResult: {result}")
