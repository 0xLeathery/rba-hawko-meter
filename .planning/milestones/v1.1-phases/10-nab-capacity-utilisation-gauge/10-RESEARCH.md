# Phase 10: NAB Capacity Utilisation Gauge - Research

**Researched:** 2026-02-24
**Domain:** Web scraping (HTML + PDF fallback), pipeline integration, frontend gauge customisation
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Gauge display & labeling**
- Gauge title: "Business Conditions" (broad, matches RBA framing — capacity utilisation is a component of business conditions)
- Trend label shows BOTH level and direction: "83.2% — ABOVE avg, RISING" or "79.1% — BELOW avg, FALLING"
- Hawk/dove color mapping: high capacity utilisation = red/hawkish (inflationary pressure), low = blue/dovish. Consistent with housing gauge's inflation-aligned coloring
- Data period format: month + year "(Jan 2026)" — matches the monthly release cadence of NAB surveys
- Gauge range: 70-90% — covers realistic historical range with headroom, ~81% average sits near middle

**Direction detection**
- Direction determined by month-over-month change (compare latest to previous month)
- Flat/STEADY threshold: +/- 0.5 percentage points — changes within this band show "STEADY" instead of RISING/FALLING
- When only one data point exists (no previous month), Claude decides how to handle gracefully (likely omit direction, show level only)

**Staleness indication**
- Explicit staleness warning when data is >45 days old (more prominent than just the month label)
- Month label always shows data period "(Jan 2026)" regardless of staleness

**Scraper behavior & resilience**
- If NAB tag archive crawl finds no survey URL: log clear warning, skip this indicator, pipeline continues (consistent with other scrapers)
- PDF fallback: when HTML extraction fails, attempt PDF extraction. Logged in pipeline but silent to dashboard user — no visual difference
- If BOTH HTML and PDF fail: don't write anything to CSV. Next pipeline run re-attempts (retry, don't mark as permanent gap)
- Scraper is idempotent: runs on every pipeline invocation, skips if current month's data already exists in CSV. No date-awareness or timing logic

**Historical data handling**
- Initial backfill: scrape last 12 months of NAB surveys from tag archive
- CSV gaps: skip missing months (only rows for successfully extracted months). No null/NA placeholder rows
- Long-run average: calculated dynamically from CSV data, not hardcoded at 81%

**Data source transparency**
- Source label format: Claude's discretion (pick what's consistent with other gauge source labels)
- Plain-English interpretation: inflation pressure framing — "High capacity utilisation signals inflation pressure, making rate cuts less likely"
- Indicator count: just update to "8 of 8 indicators" — no celebration badge or special UI

**Pipeline integration**
- Composite score weighting: Claude's discretion (determine appropriate weighting based on existing normalization approach)
- When NAB data is missing: exclude from composite and show "Based on 7 of 8 indicators" — transparent, don't carry forward stale values
- Z-score polarity: explicit in config (higher_is_hawkish: true) — clear, auditable, matches existing indicator config pattern
- Schedule: runs daily with other scrapers (idempotent skip when current month already collected). No separate monthly job

### Claude's Discretion
- Seed data approach for initial CSV average calculation (whether to pre-populate historical values or start with 81% baseline until enough data accumulates)
- Source label exact wording (consistency with other gauges)
- Gauge outlier handling (clamp to 70-90% edge or auto-expand)
- Single data point direction label handling
- Composite score weighting relative to other indicators

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| NAB-01 | Capacity utilisation percentage scraped from NAB Monthly Business Survey HTML article body | Confirmed: data lives in `<p>` tag plain text, pattern "Capacity utilisation rose to 83.1%..." — regex `r'[Cc]apacity utilisation[^.]*?([\d.]+)%'` captures it |
| NAB-02 | Survey URL discovered via tag archive page, not constructed from date templates | Confirmed: two live tag archive URLs exist; HTML links to monthly articles discoverable via BeautifulSoup |
| NAB-03 | Business confidence gauge activated with capacity utilisation data | Confirmed: `business_confidence` key already exists in `weights.json` (5% weight), `OPTIONAL_INDICATOR_CONFIG`, `engine.py` interpretation templates, and `gauges.js` DISPLAY_LABELS — only csv_file stub needs wiring |
| NAB-04 | Gauge shows trend label indicating above/below long-run average (~81%) | Confirmed: trend label logic belongs in `interpretations.js` `generateMetricInterpretation('business_confidence')` — currently shows generic text, needs replacement with capacity utilisation specific logic |
| NAB-05 | PDF fallback extracts capacity utilisation if HTML extraction fails for a given month | Confirmed: `pdfplumber` already in `requirements.txt`; PDF URL pattern known (`/content/dam/nab-business/document/...`); text in PDF follows same sentence structure |
</phase_requirements>

---

## Summary

The NAB Monthly Business Survey publishes capacity utilisation as a plain-text percentage figure in the HTML article body, within a standard `<p>` tag containing text like "Capacity utilisation rose to 83.1%, to be above the long run average by 2ppts". This is extractable with a simple regex — no JavaScript rendering required, no table parsing, no special markup. The HTML-first approach (NAB-01) is confirmed straightforward.

URL discovery (NAB-02) is the trickiest aspect. NAB uses two distinct URL formats simultaneously: older articles (2024 and earlier) follow `/nab-monthly-business-survey-{month}-{year}/` directly off the root, while newer articles (late 2025 onward) appear under `/tag/economic-commentary/nab-monthly-business-survey---{month}-{year}` with three hyphens. The tag archive pages (`/tag/economic-commentary` and `/tag/business-survey`) list only the most recent few articles, not a full paginated listing. The safe discovery strategy is to crawl the tag archive page and parse `href` attributes containing "monthly-business-survey", which surfaces the most recent URL regardless of format variation. For backfill, the scraper must try both URL patterns per month.

The pipeline integration (NAB-03) is already 80% done: `business_confidence` has an entry in `weights.json` (5% weight, polarity: 1), `OPTIONAL_INDICATOR_CONFIG`, `engine.py` interpretation templates, and `gauges.js` DISPLAY_LABELS. The stub `csv_file: None` in config just needs updating to `"nab_capacity.csv"`. The normalization approach differs from other indicators: capacity utilisation is already an absolute percentage (not a YoY ratio), so it normalises via z-score directly on the raw value (`normalize: "direct"`). The gauge rendering (NAB-04) requires replacing the generic `business_confidence` interpretation in `interpretations.js` with a capacity utilisation-specific template showing the trend label format (e.g. "83.2% — ABOVE avg, RISING").

**Primary recommendation:** Implement in a single plan. The scraper rewrite (nab_scraper.py), config wire-up, and frontend customisation are tightly coupled — splitting into multiple plans adds coordination overhead without benefit.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| requests (via `create_session`) | already installed | HTTP GET to NAB pages | Project-standard session with retry/backoff |
| BeautifulSoup4 + lxml | already installed | HTML parsing for URL discovery and article extraction | Project-standard, used by existing scrapers |
| pdfplumber | >=0.11,<1.0 (already in requirements.txt) | PDF text extraction for fallback | Already used by corelogic_scraper.py |
| pandas | already installed | DataFrame construction, CSV append | Project-standard data layer |
| re (stdlib) | stdlib | Regex to extract percentage from article text | No additional deps needed |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| python-dateutil | already installed | Month/year date parsing for backfill loop | When constructing date objects per survey month |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| BeautifulSoup (lxml) | html.parser | html.parser is slower, lxml already installed |
| pdfplumber for PDF | pypdf / camelot-py / tabula-py | REQUIREMENTS.md explicitly bans camelot-py (Ghostscript) and tabula-py (JVM); pypdf is less reliable for text extraction from columnar PDFs; pdfplumber already present |
| regex extraction | full HTML table parser | No table exists; data is in prose paragraphs |

**Installation:** No new packages required. All dependencies already present in `requirements.txt`.

---

## Architecture Patterns

### Recommended Project Structure

The nab_scraper.py already exists as a stub at `pipeline/ingest/nab_scraper.py`. The plan rewrites it in-place. No new files are needed for the scraper. Frontend changes go into existing `public/js/interpretations.js` and `public/js/gauges.js`. Config changes go into `pipeline/config.py` and `data/weights.json`.

```
pipeline/
├── ingest/
│   └── nab_scraper.py          # REWRITE: URL discovery + HTML extraction + PDF fallback
├── config.py                   # UPDATE: OPTIONAL_INDICATOR_CONFIG csv_file stub → "nab_capacity.csv"
data/
├── nab_capacity.csv            # CREATED by scraper (backfill + ongoing)
├── weights.json                # UPDATE: csv_file wiring (already has business_confidence entry)
public/js/
├── interpretations.js          # UPDATE: business_confidence interpretation template
└── gauges.js                   # UPDATE: DISPLAY_LABELS business_confidence label if needed
```

### Pattern 1: URL Discovery via Tag Archive Crawl

**What:** Fetch the tag archive page, find all `<a>` tags whose `href` contains "monthly-business-survey", take the first match (most recent) as the survey URL.

**When to use:** Every pipeline run to find the current month's article.

**Example:**
```python
# Source: verified against business.nab.com.au tag archive pages
def discover_latest_survey_url(session):
    """
    Crawl NAB tag archive to find the most recent Monthly Business Survey URL.
    Returns absolute URL string or None if not found.
    """
    TAG_ARCHIVE_URLS = [
        "https://business.nab.com.au/tag/economic-commentary",
        "https://business.nab.com.au/tag/business-survey",
    ]
    BASE = "https://business.nab.com.au"

    for archive_url in TAG_ARCHIVE_URLS:
        try:
            resp = session.get(archive_url, timeout=DEFAULT_TIMEOUT)
            if resp.status_code != 200:
                continue
            soup = BeautifulSoup(resp.content, 'lxml')
            for a in soup.find_all('a', href=True):
                href = a['href']
                if 'monthly-business-survey' in href.lower():
                    # Make absolute
                    if href.startswith('http'):
                        return href
                    return BASE + href
        except Exception:
            continue
    return None
```

### Pattern 2: HTML Extraction via Regex on Article Text

**What:** Fetch the discovered article URL, extract all paragraph text, apply regex to find the capacity utilisation percentage.

**When to use:** Primary extraction method (NAB-01).

**Example:**
```python
# Source: verified against Aug 2025, May 2025, Nov 2025, Dec 2025 articles
CAPACITY_REGEX = re.compile(
    r'[Cc]apacity utilisa?tion[^.]*?([\d]+\.?\d*)%',
    re.IGNORECASE
)

def extract_capacity_from_html(html_bytes):
    """
    Extract capacity utilisation % from NAB Monthly Business Survey HTML.
    Returns float or None.
    """
    soup = BeautifulSoup(html_bytes, 'lxml')
    # Search all paragraph text
    for p in soup.find_all(['p', 'li']):
        text = p.get_text()
        m = CAPACITY_REGEX.search(text)
        if m:
            return float(m.group(1))
    return None
```

Confirmed text patterns from live pages:
- Aug 2025: "Capacity utilisation rose to 83.1%, to be above the long run average by 2ppts"
- May 2025: "Capacity utilisation rose to 82.3% from 81.4%"
- Nov 2025: "capacity utilisation rose further to 83.6%, the highest it has been in 18 months"
- Dec 2025: 83.2% (confirmed by search results)
- Jan 2026: declined 0.6ppt from peak (no exact figure in article text found — may need PDF)

### Pattern 3: PDF Fallback Extraction

**What:** Download the PDF linked in the article, extract text, apply the same regex.

**When to use:** HTML extraction returns None (NAB-05).

**Example:**
```python
# Source: pattern confirmed from corelogic_scraper.py + NAB PDF URL examples
def extract_capacity_from_pdf(pdf_bytes):
    """PDF fallback: same regex applied to pdfplumber text."""
    import pdfplumber, io
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages[:6]:
            text = page.extract_text() or ""
            m = CAPACITY_REGEX.search(text)
            if m:
                return float(m.group(1))
    return None

def get_pdf_link_from_article(html_bytes):
    """Extract PDF href from article page."""
    soup = BeautifulSoup(html_bytes, 'lxml')
    for a in soup.find_all('a', href=True):
        if '.pdf' in a['href'].lower():
            href = a['href']
            if not href.startswith('http'):
                href = 'https://business.nab.com.au' + href
            return href
    return None
```

Known PDF URL patterns (for reference, NOT for hardcoding):
- Aug 2025: `https://www.nab.com.au/content/dam/nab-business/document//NAB-Monthly-Business-Survey-August-2025.pdf`
- Nov 2025: `/content/dam/nab-business/document/2025m11%20NAB%20Monthly%20Business%20Survey.pdf`
- Jan 2026: `https://www.nab.com.au/content/dam/nab-email-composer/nabmarketsresearchembargo/economics/pdf/2026m01%20NAB%20Monthly%20Business%20Survey%20evfbdhdn.pdf`

Note: PDF URLs are inconsistent across months (different base paths, naming schemes, even random suffixes in embargo versions). Always discover PDF link from the HTML article, never construct.

### Pattern 4: Backfill Loop

**What:** For initial population, loop over the last 12 months, try multiple URL patterns per month, extract and append to CSV.

**When to use:** One-time backfill before the scraper enters idempotent mode.

**Example:**
```python
def backfill_nab_history(session, months=12):
    """Try both URL patterns for each of the last N months."""
    from dateutil.relativedelta import relativedelta
    from datetime import datetime

    results = []
    now = datetime.now()
    for i in range(months):
        target = now - relativedelta(months=i+1)
        month_name = target.strftime('%B').lower()   # "august"
        year = target.year

        # Two URL patterns NAB uses
        candidate_urls = [
            # Pattern A: /tag/economic-commentary/ (newer, late 2025+)
            f"https://business.nab.com.au/tag/economic-commentary/nab-monthly-business-survey---{month_name}-{year}",
            # Pattern B: root-level (2024 and earlier)
            f"https://business.nab.com.au/nab-monthly-business-survey-{month_name}-{year}/",
            f"https://business.nab.com.au/nab-monthly-business-survey-{month_name}-{year}",
        ]
        # Try each, extract, append on first success
        ...
```

### Pattern 5: Idempotency Check

**What:** Before scraping, check whether the current month's data is already in the CSV. Mirrors the pattern from `corelogic_scraper.py`.

**Example:**
```python
def _current_month_already_scraped(output_path):
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
            logger.info(f"Current month already scraped — skipping")
            return True
    except Exception:
        pass
    return False
```

### Pattern 6: Normalization — Direct (not YoY)

**What:** Capacity utilisation is already an absolute percentage (e.g., 83.1%). It does NOT need YoY transformation. The pipeline must use `normalize: "direct"` so the z-score is computed on the raw capacity utilisation values.

**Config update required in `pipeline/config.py`:**
```python
OPTIONAL_INDICATOR_CONFIG = {
    ...
    "business_confidence": {
        "csv_file": "nab_capacity.csv",  # was None
        "normalize": "direct",            # keep as-is — correct
        "frequency": "monthly",           # keep as-is
        "yoy_periods": None,
        "description": "NAB Capacity Utilisation %",
    },
    ...
}
```

The `normalize: "direct"` path in `ratios.py` passes values through unchanged. Monthly data gets resampled to quarterly (end-of-quarter last value) via `resample_to_quarterly()`. This is correct — the quarterly z-score reflects the capacity utilisation level.

### Pattern 7: Trend Label in Frontend

**What:** The `generateMetricInterpretation('business_confidence')` function in `interpretations.js` currently returns generic zone-based text. It needs replacing with a capacity utilisation-specific template.

**Current code (to replace):**
```javascript
case 'business_confidence':
  if (v < 40) return 'Business confidence is below average — businesses are cautious';
  if (v <= 60) return 'Business confidence is around average levels';
  return 'Business confidence is high — businesses are investing and hiring more';
```

**New pattern:**
```javascript
case 'business_confidence':
  // metricData.raw_value is the capacity utilisation %
  // metricData.data_date is the survey month
  var cuPct = parseFloat(metricData.raw_value);
  // Direction and level computed server-side and embedded in status.json,
  // OR computed client-side from raw_value and long_run_avg
  // The trend label format: "83.2% — ABOVE avg, RISING"
  // ... (implementation follows status.json contract)
```

**Key design decision:** The trend label needs both the current percentage AND direction (RISING/FALLING/STEADY). Direction requires comparing latest to previous month — this must be computed either:
1. In the pipeline (engine.py adds `direction` and `long_run_avg` fields to the gauge entry), or
2. In the frontend (pass history[] and compute from last two values)

**Recommendation:** Compute in the pipeline. The `build_gauge_entry()` function in `engine.py` already has access to the full z_df (historical data). Add `capacity_utilisation_pct`, `direction`, and `long_run_avg` to the gauge entry for `business_confidence` specifically. The frontend then reads these fields.

### Anti-Patterns to Avoid

- **Constructing NAB URLs from date templates:** NAB changes URL structure without notice. The URL pattern has already changed between 2024 (root-level) and late 2025 (under `/tag/economic-commentary/` with triple-hyphens). Always discover from the tag archive. Never construct.
- **Using `csv_file: None` stub in OPTIONAL_INDICATOR_CONFIG:** The current stub causes the normalization engine to skip `business_confidence`. Update to `"nab_capacity.csv"` when the scraper is live.
- **Applying YoY normalization:** Capacity utilisation is already a ratio (%). YoY of a percentage is meaningless. The existing `normalize: "direct"` config is correct — do not change it to `yoy_pct_change`.
- **Double-counting sources in ratios.py:** The `precomputed_yoy_sources` set in `normalize_indicator()` is currently `{'Cotality HVI'}`. NAB capacity data is not a YoY ratio; it is a direct value but should NOT be treated as a precomputed YoY row. Do not add `'NAB'` to `precomputed_yoy_sources`.
- **Writing PDF URL construction logic:** PDF URLs change naming conventions per month (see examples above). Always extract the PDF link from the HTML article's anchor tags.
- **Marking failed months as permanent gaps:** If both HTML and PDF fail, write nothing to CSV. The next pipeline run will retry. This is the established behavior from the CONTEXT decisions.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| HTTP retries with backoff | Custom retry loop | `create_session(retries=3, backoff_factor=0.5)` | Already in `pipeline/utils/http_client.py` |
| CSV deduplication | Custom dedup logic | `append_to_csv()` in `pipeline/utils/csv_handler.py` | Already handles date-keyed dedup |
| PDF text extraction | Custom PDF parser | `pdfplumber` (already in requirements.txt) | Used in corelogic_scraper.py; handles NAB PDF text layout |
| Z-score normalization | Custom stats | `compute_rolling_zscores()` in `pipeline/normalize/zscore.py` | Handles window, MAD-based robust stats, clamping |
| Gauge value mapping | Custom scale | `zscore_to_gauge()` in `pipeline/normalize/gauge.py` | Linear [-3,+3] → [0,100] mapping already validated |

**Key insight:** The project has a mature pipeline abstraction. The nab_scraper.py rewrite only needs to deliver `nab_capacity.csv` with schema `[date, value, source]`; all normalization, z-scoring, and gauge rendering flows are already wired.

---

## Common Pitfalls

### Pitfall 1: NAB URL Pattern Inconsistency
**What goes wrong:** The scraper constructs a URL like `/nab-monthly-business-survey-january-2026` but the actual January 2026 article is at `/tag/economic-commentary/nab-monthly-business-survey---january-2026` (or similar). The request 404s and the pipeline logs a failure.
**Why it happens:** NAB changed their URL scheme in late 2025 without redirects. There are now at least two active patterns simultaneously.
**How to avoid:** Always discover via tag archive crawl. Keep two archive URLs to check: `/tag/economic-commentary` and `/tag/business-survey`. Extract all `href` values matching "monthly-business-survey", take the first (most recent).
**Warning signs:** HTTP 404 on a URL that looks well-formed.

### Pitfall 2: Tag Archive Only Shows Recent Articles (No Full Pagination)
**What goes wrong:** Tag archive page shows 1-3 most recent articles. Backfill loop tries to discover historical months from the archive and finds nothing beyond the most recent.
**Why it happens:** The NAB tag archive does not paginate or expose a full archive listing. It's a marketing page, not a proper CMS archive.
**How to avoid:** For backfill, the scraper must TRY multiple URL patterns per month by construction (not by discovery). Two patterns per month, try both, move on. This is the only reliable approach for historical data.
**Warning signs:** Backfill loop extracts only 1-2 months instead of 12.

### Pitfall 3: "Capacity utilisation" vs "capacity utilization" Spelling
**What goes wrong:** Regex uses only `utilisation` (Australian English) and misses `utilization` (US spelling).
**Why it happens:** NAB consistently uses Australian spelling, but the regex flag `re.IGNORECASE` doesn't handle spelling variants.
**How to avoid:** Use `utilisa?tion` in the regex (the `?` makes the second 's' optional, catching both spellings). Pattern: `r'[Cc]apacity utilisa?tion[^.]*?([\d]+\.?\d*)%'`
**Warning signs:** Extraction returns None despite correct page content.

### Pitfall 4: The `business_confidence` Key Already Used for Other Purposes
**What goes wrong:** Developer adds a new indicator key `nab_capacity_utilisation` to `OPTIONAL_INDICATOR_CONFIG`, `weights.json`, `engine.py` templates, and `gauges.js` DISPLAY_LABELS — creating a second card next to the existing `business_confidence` placeholder.
**Why it happens:** `business_confidence` with `csv_file: None` is already the stub for this gauge. It is NOT a separate indicator.
**How to avoid:** Update `business_confidence` in all configs to point to `nab_capacity.csv`. Do NOT create a new key. The frontend gauge is already wired to `business_confidence`.
**Warning signs:** Dashboard shows 9 gauge cards, or `business_confidence` shows "Data coming soon" alongside a new `nab_capacity_utilisation` card.

### Pitfall 5: Direct % Values Don't Behave Like YoY Ratios in Z-Score
**What goes wrong:** The z-score window covers 10 years of capacity utilisation values. If the historical range is 78-85%, the standard deviation is small (~1.5-2%), so a reading of 83% gives a large positive z-score that clamps at +3 (gauge at 100). Dashboard shows max hawkish even for moderate readings.
**Why it happens:** Z-score is sensitive to the variance in the data. Capacity utilisation is relatively stable; small changes in % can translate to large z-scores.
**How to avoid:** Verify the z-score output after the first data run. The gauge value of 50 represents the 10-year median. Values of 83% (well above historical average) should give a warm-hot reading; values near 81% (average) should give neutral. If the z-score exceeds ±3 for typical values, the distribution is narrow and the output is still valid — capacity utilisation IS unusually high by historical standards.
**Warning signs:** Gauge always shows 100 (max hawkish) for any above-average reading.

### Pitfall 6: BOTH HTML and PDF Fail — Don't Write Empty Row
**What goes wrong:** Scraper writes a row with `value: None` or `value: NaN` to the CSV, which then causes `filter_valid_data()` in ratios.py to drop it silently. No visible error, but the month is recorded as attempted.
**Why it happens:** CSV append logic without a None check.
**How to avoid:** Only call `append_to_csv()` when `value` is a valid float. If extraction fails completely, log warning and return — do not append.
**Warning signs:** `nab_capacity.csv` has rows with NaN or empty value column.

### Pitfall 7: 45-Day Staleness Check vs Monthly Data Cadence
**What goes wrong:** NAB data is released mid-month for the prior month (e.g., January 2026 data released 11 February 2026). If the pipeline runs on 12 February and the February scrape fails, the January data is ~32 days old — not stale. But if the scraper fails through all of March (46 days after the Feb 11 release), the staleness warning fires.
**Why it happens:** 45-day threshold is deliberately conservative for monthly data.
**How to avoid:** The staleness threshold is a UI concern, not a pipeline concern. `engine.py` writes `staleness_days` to the gauge entry. `interpretations.js` checks this field. No change needed to the calculation; just implement the 45-day frontend check for the `business_confidence` card.
**Warning signs:** Amber staleness border appearing within the same month as data release.

---

## Code Examples

### Complete Scraper Structure (nab_scraper.py rewrite)

```python
"""
NAB Business Survey capacity utilisation scraper.
URL discovery via tag archive — never constructs URLs from date templates.
HTML extraction primary, PDF fallback on failure (NAB-01, NAB-02, NAB-05).
"""
import io, logging, re, traceback
from datetime import datetime, timedelta
from typing import Dict, Optional, Union

import pandas as pd
from bs4 import BeautifulSoup

from pipeline.config import DATA_DIR, BROWSER_USER_AGENT, DEFAULT_TIMEOUT
from pipeline.utils.csv_handler import append_to_csv
from pipeline.utils.http_client import create_session

logger = logging.getLogger(__name__)

OUTPUT_FILE = "nab_capacity.csv"
NAB_BASE = "https://business.nab.com.au"

TAG_ARCHIVE_URLS = [
    f"{NAB_BASE}/tag/economic-commentary",
    f"{NAB_BASE}/tag/business-survey",
]

# Matches both Australian (utilisation) and US (utilization) spelling
CAPACITY_REGEX = re.compile(
    r'[Cc]apacity utilisa?tion[^.]*?([\d]+\.?\d*)%',
    re.IGNORECASE
)

MONTH_URL_PATTERNS = [
    # Pattern A: /tag/economic-commentary/ slug with triple hyphens (late 2025+)
    lambda m, y: f"{NAB_BASE}/tag/economic-commentary/nab-monthly-business-survey---{m}-{y}",
    # Pattern B: root-level with trailing slash (2024 and earlier)
    lambda m, y: f"{NAB_BASE}/nab-monthly-business-survey-{m}-{y}/",
    # Pattern C: root-level without trailing slash (some 2025 articles)
    lambda m, y: f"{NAB_BASE}/nab-monthly-business-survey-{m}-{y}",
]


def discover_latest_survey_url(session) -> Optional[str]:
    """Crawl tag archive pages to find the most recent Monthly Business Survey URL."""
    for archive_url in TAG_ARCHIVE_URLS:
        try:
            resp = session.get(archive_url, timeout=DEFAULT_TIMEOUT)
            if resp.status_code != 200:
                continue
            soup = BeautifulSoup(resp.content, 'lxml')
            for a in soup.find_all('a', href=True):
                href = a['href']
                if 'monthly-business-survey' in href.lower():
                    return href if href.startswith('http') else NAB_BASE + href
        except Exception as e:
            logger.warning(f"Tag archive fetch failed for {archive_url}: {e}")
    return None


def fetch_article(url, session) -> Optional[bytes]:
    """Fetch article HTML, return bytes or None."""
    try:
        resp = session.get(url, timeout=DEFAULT_TIMEOUT)
        if resp.status_code == 200:
            return resp.content
    except Exception:
        pass
    return None


def extract_capacity_from_html(html_bytes: bytes) -> Optional[float]:
    """Extract capacity utilisation % from article HTML."""
    soup = BeautifulSoup(html_bytes, 'lxml')
    for tag in soup.find_all(['p', 'li', 'div']):
        text = tag.get_text()
        m = CAPACITY_REGEX.search(text)
        if m:
            return float(m.group(1))
    return None


def get_pdf_link(html_bytes: bytes) -> Optional[str]:
    """Extract first PDF link from article HTML."""
    soup = BeautifulSoup(html_bytes, 'lxml')
    for a in soup.find_all('a', href=True):
        if '.pdf' in a['href'].lower():
            href = a['href']
            return href if href.startswith('http') else NAB_BASE + href
    return None


def extract_capacity_from_pdf(pdf_bytes: bytes) -> Optional[float]:
    """PDF fallback: apply same regex to pdfplumber-extracted text."""
    try:
        import pdfplumber
    except ImportError:
        logger.error("pdfplumber not installed")
        return None
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages[:6]:
            text = page.extract_text() or ""
            m = CAPACITY_REGEX.search(text)
            if m:
                return float(m.group(1))
    return None


def _current_month_already_scraped(output_path) -> bool:
    """Idempotency: skip if current month's data already in CSV."""
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
            logger.info("Current month already scraped — skipping")
            return True
    except Exception:
        pass
    return False


def scrape_nab_capacity() -> pd.DataFrame:
    """
    Main scraper: discover URL, extract HTML, fall back to PDF.
    Returns single-row DataFrame or empty DataFrame.
    """
    output_path = DATA_DIR / OUTPUT_FILE
    if _current_month_already_scraped(output_path):
        return pd.DataFrame(columns=['date', 'value', 'source'])

    session = create_session(retries=3, backoff_factor=0.5, user_agent=BROWSER_USER_AGENT)

    survey_url = discover_latest_survey_url(session)
    if not survey_url:
        logger.warning("NAB: no survey URL discovered from tag archive — skipping")
        return pd.DataFrame(columns=['date', 'value', 'source'])

    logger.info(f"NAB: fetching survey article {survey_url}")
    html_bytes = fetch_article(survey_url, session)
    if not html_bytes:
        logger.warning(f"NAB: failed to fetch article {survey_url}")
        return pd.DataFrame(columns=['date', 'value', 'source'])

    # Primary: HTML extraction
    capacity_pct = extract_capacity_from_html(html_bytes)

    # Fallback: PDF extraction
    if capacity_pct is None:
        logger.info("NAB: HTML extraction failed — attempting PDF fallback")
        pdf_url = get_pdf_link(html_bytes)
        if pdf_url:
            try:
                pdf_resp = session.get(pdf_url, timeout=DEFAULT_TIMEOUT)
                if pdf_resp.status_code == 200:
                    capacity_pct = extract_capacity_from_pdf(pdf_resp.content)
            except Exception as e:
                logger.warning(f"NAB: PDF fetch failed: {e}")

    if capacity_pct is None:
        logger.warning("NAB: both HTML and PDF extraction failed — no data written")
        return pd.DataFrame(columns=['date', 'value', 'source'])

    # Date: end of previous month (surveys report on prior month)
    now = datetime.now()
    prev = now.replace(day=1) - timedelta(days=1)
    period_end = prev.replace(day=1)  # first of prev month as date key

    row = pd.DataFrame([{
        'date': period_end.strftime('%Y-%m-%d'),
        'value': capacity_pct,
        'source': 'NAB Monthly Business Survey',
    }])
    logger.info(f"NAB: capacity utilisation {capacity_pct}% for {period_end.strftime('%b %Y')}")
    return row


def fetch_and_save() -> Dict[str, Union[str, int]]:
    """
    Fetch NAB data and save to CSV. NEVER raises.
    Returns status dict with 'status' key.
    """
    try:
        df = scrape_nab_capacity()
        if df.empty:
            return {'status': 'failed', 'error': 'No data extracted'}
        output_path = DATA_DIR / OUTPUT_FILE
        row_count = append_to_csv(output_path, df, date_column='date')
        return {'status': 'success', 'rows': row_count}
    except Exception as e:
        logger.warning(f"NAB scraper failed (optional source): {e}")
        logger.debug(traceback.format_exc())
        return {'status': 'failed', 'error': str(e)}
```

### Backfill Script Pattern

```python
# scripts/backfill_nab.py — standalone, run once for initial 12-month history
from dateutil.relativedelta import relativedelta
from datetime import datetime

def backfill(months=12):
    session = create_session(...)
    now = datetime.now()
    for i in range(1, months + 1):
        target = now - relativedelta(months=i)
        month_str = target.strftime('%B').lower()
        year = target.year

        html_bytes = None
        survey_url = None
        for pattern_fn in MONTH_URL_PATTERNS:
            url = pattern_fn(month_str, year)
            html_bytes = fetch_article(url, session)
            if html_bytes:
                survey_url = url
                break

        if not html_bytes:
            logger.warning(f"No article found for {month_str} {year}")
            continue

        capacity_pct = extract_capacity_from_html(html_bytes)
        if capacity_pct is None:
            # try PDF fallback
            ...
        if capacity_pct is None:
            continue

        # Append to CSV
        period_end = target.replace(day=1)
        row = pd.DataFrame([{'date': period_end.strftime('%Y-%m-%d'),
                              'value': capacity_pct,
                              'source': 'NAB Monthly Business Survey'}])
        append_to_csv(DATA_DIR / "nab_capacity.csv", row, date_column='date')
```

### Frontend Interpretation Update (interpretations.js)

```javascript
// In generateMetricInterpretation(), replace the 'business_confidence' case:
case 'business_confidence':
  // raw_value is capacity utilisation %
  var cuVal = parseFloat(metricData.raw_value);
  if (isNaN(cuVal)) return 'Capacity utilisation data unavailable';

  // Long-run average from status.json extra fields (added by engine.py)
  var lra = metricData.long_run_avg || 81;
  var aboveBelow = cuVal >= lra ? 'ABOVE' : 'BELOW';

  // Direction from status.json (added by engine.py from month-over-month change)
  var direction = metricData.direction || '';
  var dirText = direction ? ', ' + direction : '';

  // Month label from data_date
  var d = new Date(metricData.data_date);
  var monthLabel = '';
  if (!isNaN(d.getTime())) {
    monthLabel = ' (' + d.toLocaleString('en-AU', {month: 'short'}) + ' ' + d.getFullYear() + ')';
  }

  return cuVal.toFixed(1) + '% \u2014 ' + aboveBelow + ' avg' + dirText + monthLabel;
```

### Status.json Extra Fields for business_confidence Gauge

Add to `build_gauge_entry()` in `engine.py` for the `business_confidence` indicator:

```python
if name == 'business_confidence':
    # Compute long-run average from all available values
    all_values = z_df['value'].dropna()
    long_run_avg = float(all_values.mean()) if len(all_values) >= 2 else 81.0

    # Compute direction from last two values
    valid_vals = z_df['value'].dropna()
    if len(valid_vals) >= 2:
        prev_val = float(valid_vals.iloc[-2])
        curr_val = float(latest_row['value'])
        delta = curr_val - prev_val
        if abs(delta) <= 0.5:
            direction = 'STEADY'
        elif delta > 0:
            direction = 'RISING'
        else:
            direction = 'FALLING'
    else:
        direction = None  # Single data point — omit direction

    entry['long_run_avg'] = round(long_run_avg, 1)
    if direction is not None:
        entry['direction'] = direction
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| nab_scraper.py returned empty DataFrame (stub) | Will be rewritten with URL discovery + HTML + PDF fallback | Phase 10 | Activates the 8th indicator |
| `business_confidence: csv_file: None` | Will be wired to `nab_capacity.csv` | Phase 10 | Enables normalization engine to process the indicator |
| Generic `business_confidence` interpretation in interpretations.js | Will show "83.2% — ABOVE avg, RISING (Jan 2026)" | Phase 10 | Fulfills NAB-04 |
| NAB URL: root-level with trailing slash (2024) | tag/economic-commentary slug + triple hyphens (late 2025+) | Approximately late 2025 | Discovery via archive crawl is the only robust approach |

**Deprecated/outdated:**
- The `business_confidence` stub entry in `OPTIONAL_INDICATOR_CONFIG` with `csv_file: None` — this was a placeholder. It will be replaced with `csv_file: "nab_capacity.csv"` and `description: "NAB Capacity Utilisation %"`.
- The old `target_url = "https://business.nab.com.au/nab-monthly-business-survey-39780/"` in the existing scraper stub — this URL returns 404 and should not be reused.

---

## Open Questions

1. **Exact date to assign to each monthly reading**
   - What we know: NAB releases monthly surveys mid-month for the prior month (e.g., January 2026 data released 11 Feb 2026). The survey covers the prior month.
   - What's unclear: Should the CSV `date` be the first of the reference month (2026-01-01) or the last day, or the release date?
   - Recommendation: Use first-of-month for the reference month (e.g., 2026-01-01 for January 2026 data). This is consistent with how ABS monthly data is dated and is unambiguous. The `data_date` in the status.json entry will reflect the actual date.

2. **January 2026 data availability and format**
   - What we know: January 2026 survey released 11 Feb 2026. The article says capacity utilisation "declined 0.6ppt from its recent peak" but the search results did not surface the exact article page URL.
   - What's unclear: Whether the January 2026 article is at `/tag/economic-commentary/nab-monthly-business-survey---january-2026` or a different URL.
   - Recommendation: STATE.md explicitly flags "manually verify NAB HTML regex matches the current month's page before committing Phase 10 implementation." Do a live test fetch against the discovered URL as part of implementation verification.

3. **Seed data for long-run average calculation**
   - What we know: With only 12 months of backfill, the dynamically-calculated average will be ~82-83% (above the long-established ~81% historical average). This means early readings will all show "ABOVE avg" even if they represent a slight recent decline.
   - What's unclear: Whether to seed with pre-2024 historical data.
   - Recommendation (Claude's discretion): Start with 12-month backfill only. The dynamic average will stabilize at approximately the correct value within 1-2 years of data. Add a note in the code comment that the 81% figure is the established long-run average from NAB research.

4. **Composite score weight for business_confidence**
   - What we know: Current `weights.json` has `business_confidence: 0.05` (5%). The weights currently sum to 1.0 (including asx_futures at 10% which is excluded from the hawk score calculation).
   - What's unclear: Whether 5% is appropriate or should be higher given capacity utilisation's direct RBA relevance.
   - Recommendation (Claude's discretion): Keep at 5%. Capacity utilisation is a useful but lagging indicator with monthly granularity matched to other indicators. 5% is appropriate alongside inflation (25%) as the primary driver.

---

## Sources

### Primary (HIGH confidence)
- Live page fetch: `business.nab.com.au/nab-monthly-business-survey-august-2025` — confirmed HTML structure, capacity utilisation in `<p>` tag, regex pattern, PDF URL
- Live page fetch: `business.nab.com.au/nab-monthly-business-survey-may-2025` — confirmed same pattern for May 2025 (82.3%)
- Live page fetch: `business.nab.com.au/tag/economic-commentary/nab-monthly-business-survey---november-2025` — confirmed late-2025 URL format with triple hyphens, Nov 2025 (83.6%), PDF link format
- Project codebase analysis: `pipeline/ingest/corelogic_scraper.py` — URL discovery pattern, idempotency, PDF extraction with pdfplumber
- Project codebase analysis: `pipeline/normalize/ratios.py` — `normalize: "direct"` path, precomputed_yoy_sources, quarterly resampling
- Project codebase analysis: `pipeline/normalize/engine.py` — `build_gauge_entry()`, `process_indicator()`, status.json schema
- Project codebase analysis: `data/weights.json` — confirmed `business_confidence` at 5% weight, polarity 1
- Project codebase analysis: `public/js/interpretations.js` — `generateMetricInterpretation('business_confidence')` current text (to replace), `renderMetricCard()` pattern
- Project codebase analysis: `public/js/gauges.js` — DISPLAY_LABELS, METRIC_ORDER

### Secondary (MEDIUM confidence)
- WebSearch: NAB Monthly Business Survey URL pattern survey 2024/2025 — confirmed two active URL schemas
- WebSearch: NAB December 2025 capacity utilisation (83.2%), November 2025 (83.6%), January 2026 context
- WebSearch: January 2026 survey released 11 Feb 2026 (via MarketScreener); PDF URL pattern for 2026m01

### Tertiary (LOW confidence)
- WebSearch: January 2026 exact capacity utilisation figure — only found "declined 0.6ppt" language, not a hard percentage from the article HTML
- Tag archive full listing — the two tag archive pages only surfaced 1-3 recent articles; full pagination behavior not confirmed

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries already present in the project
- Architecture: HIGH — URL discovery pattern confirmed from live pages; scraper structure mirrors proven corelogic_scraper.py
- Pitfalls: HIGH — NAB URL inconsistency confirmed from live observation; other pitfalls derived from codebase analysis
- Frontend pattern: HIGH — interpretations.js pattern is clear and well-understood from Phase 9

**Research date:** 2026-02-24
**Valid until:** 2026-03-24 (30 days; NAB site structure is unlikely to change but URL patterns may evolve)
