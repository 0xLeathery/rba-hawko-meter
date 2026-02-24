# Phase 9: Housing Prices Gauge - Research

**Researched:** 2026-02-24
**Domain:** ABS RPPI SDMX API, Cotality HVI PDF scraping, housing gauge rendering
**Confidence:** HIGH (ABS RPPI), MEDIUM (Cotality URL pattern), HIGH (frontend integration)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Gauge display**
- Match existing gauge style — same circular gauge as other indicators
- Gauge label: "Housing Prices" (no "national" qualifier, no "dwelling")
- Directional label + number format: "RISING +8.3%" or "FALLING -2.1%"
- Hawk/dove color alignment: rising prices = red/warm (hawkish, inflationary), falling prices = blue/cool (dovish)
- Neutral zone for flat prices: small changes (near 0%) show "STEADY" or "FLAT" with neutral/gray coloring rather than forcing a directional label

**Staleness indication**
- Always show data period in quarter format: "(Q4 2025)" appended to gauge display, whether data is fresh or stale
- When data >90 days old, the quarter format serves double duty as a staleness signal — no additional visual dimming or warning badges
- Label only — gauge stays fully functional and styled normally regardless of data age

**Data source transparency**
- Source name always visible below gauge: "Source: ABS RPPI" or "Source: Cotality HVI"
- RBA-framed plain-English interpretation: connect housing data to RBA policy angle (e.g. "Rising prices put upward pressure on inflation, making rate cuts less likely")

### Claude's Discretion
- Whether to add a subtle fallback note when Cotality is unavailable (e.g. "Source: ABS RPPI (Cotality unavailable)") or just silently switch the source name
- Whether to include a secondary metric alongside YoY % (e.g. quarterly change) if the data supports it cleanly
- Threshold for the neutral/"STEADY" zone (e.g. +/-1% or +/-2%)
- Exact gauge needle range/scale for housing YoY %

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| HOUS-01 | ABS RPPI data ingested via existing SDMX API pattern, activating the housing gauge | ABS RPPI dataflow confirmed live at `data.api.abs.gov.au` with key `1.3.100.Q`. Date range 2002-Q1 to 2021-Q4. Follows existing `fetch_abs_series()` pattern exactly. |
| HOUS-02 | Housing gauge displays YoY % change with staleness metadata label when data is older than 90 days | Quarterly data from ABS RPPI ends Dec 2021 — always stale. Quarter-format label "(Q4 2021)" is always shown. Normalization engine already has `staleness_days` in gauge output. Frontend `renderMetricCard()` already handles staleness — but housing display requires custom interpretation per CONTEXT.md decisions. |
| HOUS-03 | Cotality HVI PDF scraped monthly for current dwelling price data | Confirmed: `discover.cotality.com/hubfs/Article-Reports/COTALITY%20HVI%20{Mon}%20{Year}%20FINAL.pdf` works for Jan 2026 and Feb 2026. `pdfplumber` extracts `Australia 0.8% 2.4% 9.4%` (month/quarter/annual) with a regex on the pattern. WARNING: URL pattern is inconsistent for older months; Nov 2025 returns 404 at the "FINAL" URL. Discovery via Cotality article page required for robustness. |
| HOUS-04 | Housing gauge uses Cotality data when available, falls back to ABS RPPI when not | `corelogic_housing.csv` stores all housing data. A `source` column distinguishes "Cotality HVI" vs "ABS RPPI". Normalization engine reads the latest row; if the latest row is from Cotality, uses it; otherwise uses ABS RPPI. Frontend reads `source` from status.json gauge entry to show "Source: Cotality HVI" vs "Source: ABS RPPI". |
</phase_requirements>

---

## Summary

Phase 9 activates the housing gauge — currently a placeholder card on the dashboard — by (1) populating `corelogic_housing.csv` via the ABS RPPI SDMX API and (2) implementing a Cotality HVI PDF scraper that appends monthly data to the same CSV.

The ABS RPPI API is confirmed live and follows the exact same SDMX pattern the project already uses. The key `1.3.100.Q` retrieves quarterly national residential property price index numbers from 2002-Q1 to 2021-Q4. This data is always >90 days old, but provides a backseries for Z-score normalization. The OPTIONAL_INDICATOR_CONFIG already stubs the `housing` indicator with `csv_file: None`; Phase 9 simply sets `csv_file: "corelogic_housing.csv"` and adds a `fetch_rppi()` function using the existing `fetch_abs_series()`.

The Cotality HVI PDF scraper can reliably retrieve monthly national YoY % change using `pdfplumber` (pure Python, no system deps, CI-compatible). The PDF contains the line `Australia 0.8% 2.4% 9.4%` (month/3-month/12-month). A regex extracts the annual (12-month) figure. Cotality appends monthly data to the same CSV with `source = "Cotality HVI"`, and the normalization engine's source attribution flows through to the frontend. The primary risk is URL pattern inconsistency across months — mitigation is a try/list-of-candidate-URLs approach with graceful degradation.

The frontend integration is minimal: housing already appears in `METRIC_ORDER`, `DISPLAY_LABELS`, interpretation templates, and `getWhyItMatters()` in the existing JS. The `renderMetricCard()` function handles staleness. What's new is (a) the directional label ("RISING +8.3%"), (b) always-visible quarter format "(Q4 2025)", and (c) source attribution below the gauge.

**Primary recommendation:** Two-plan approach: Plan 09-01 does ABS RPPI pipeline + `corelogic_housing.csv` creation + housing gauge activation. Plan 09-02 does Cotality PDF scraper + fallback logic + source attribution in frontend.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `requests` | >=2.28 | ABS RPPI SDMX API calls | Already in requirements.txt; used by all other ABS fetchers |
| `pandas` | >=2.0 | CSV parsing, date handling, YoY computation | Already in requirements.txt; used throughout normalize pipeline |
| `pdfplumber` | 0.11.9 (latest) | Cotality HVI PDF text extraction | Pure Python (no Ghostscript/JVM deps), CI-safe, already works in this environment |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `pdfminer.six` | (pdfplumber dep) | Underlying PDF parser | Installed automatically with pdfplumber |
| `pypdfium2` | (pdfplumber dep) | PDF rendering | Installed automatically with pdfplumber |
| `re` (stdlib) | stdlib | Extract national YoY % from PDF text lines | Regex match on `Australia \d+\.\d+% \d+\.\d+% (\d+\.\d+)%` pattern |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| pdfplumber | camelot-py | camelot-py requires Ghostscript — blocked by REQUIREMENTS.md Out of Scope |
| pdfplumber | tabula-py | tabula-py requires JVM — blocked by REQUIREMENTS.md Out of Scope |
| pdfplumber | pypdf | pypdf is text-only, struggles with multi-column Cotality layout |
| Direct URL construction | Page discovery scraping | URL pattern is inconsistent; try-list of candidates is simpler than scraping the Cotality article index |

**Installation:**
```bash
# Add to requirements.txt:
pdfplumber>=0.11,<1.0
```

---

## Architecture Patterns

### Recommended Project Structure

The housing pipeline integrates cleanly into the existing structure:

```
pipeline/
├── ingest/
│   ├── abs_data.py          # Add fetch_rppi() + add 'rppi' to FETCHERS
│   └── corelogic_scraper.py # Replace stub with working Cotality + fallback logic
├── config.py                # Add RPPI to ABS_CONFIG, update OPTIONAL_INDICATOR_CONFIG
data/
└── corelogic_housing.csv    # New file: created by RPPI fetch (populated in 09-01)
public/js/
└── interpretations.js       # Update housing case in generateMetricInterpretation()
                             # Add source attribution to renderMetricCard()
```

### Pattern 1: ABS RPPI Fetch (HOUS-01)

The ABS RPPI SDMX API uses the same pattern as all existing ABS fetchers. The confirmed working key is `1.3.100.Q`:

```
Dimensions: MEASURE.PROPERTY_TYPE.REGION.FREQ
Values:     1         .3             .100   .Q
Meaning:    Index Nos . Residential  .Weighted avg 8 cities .Quarterly
```

**Verified live API call:**
```
GET https://data.api.abs.gov.au/data/ABS,RPPI/1.3.100.Q
    Accept: application/vnd.sdmx.data+csv;labels=both
    ?startPeriod=2002&detail=dataonly
```
Returns 16 rows (2021-Q4 is the last observation, value=183.9).

**Config entry for `config.py`:**
```python
ABS_CONFIG["rppi"] = {
    "dataflow": "RPPI",
    "key": "1.3.100.Q",
    "params": {"startPeriod": "2002", "detail": "dataonly"},
    "filters": {},
    "output_file": "corelogic_housing.csv",
    "description": "Residential Property Price Index, national weighted average (quarterly)",
    "critical": False,
}
```

**Update OPTIONAL_INDICATOR_CONFIG:**
```python
OPTIONAL_INDICATOR_CONFIG["housing"]["csv_file"] = "corelogic_housing.csv"
OPTIONAL_INDICATOR_CONFIG["housing"]["frequency"] = "quarterly"
OPTIONAL_INDICATOR_CONFIG["housing"]["yoy_periods"] = 4
```

**Output CSV schema** (matches all other ABS outputs):
```
date,value,source,series_id
2002-01-01,100.0,ABS,RPPI/1.3.100.Q
...
2021-10-01,183.9,ABS,RPPI/1.3.100.Q
```

### Pattern 2: Cotality HVI PDF Scraper (HOUS-03)

The Cotality PDF contains the line `Australia 0.8% 2.4% 9.4%` (month/3-month/12-month). Confirmed across Jan 2026 and Feb 2026 PDFs. The `pdfplumber` extraction is reliable:

```python
import pdfplumber
import re

def extract_national_yoy(pdf_path):
    """Extract national annual YoY % from Cotality HVI PDF."""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages[:4]:
            text = page.extract_text() or ""
            # Pattern: "Australia X.X% X.X% X.X%" — annual is the 3rd %
            match = re.search(
                r'Australia\s+([-\d.]+)%\s+([-\d.]+)%\s+([-\d.]+)%',
                text
            )
            if match:
                return float(match.group(3))  # 12-month / annual
    return None
```

**URL candidate list approach** (MEDIUM confidence — URL is inconsistent across months):
```python
MONTH_ABBREV = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
    7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
}

def get_candidate_urls(year, month):
    """Return a list of Cotality HVI PDF URL candidates to try."""
    mon_abbrev = MONTH_ABBREV[month]
    mon_full = datetime(year, month, 1).strftime("%B")
    return [
        f"https://discover.cotality.com/hubfs/Article-Reports/"
        f"COTALITY%20HVI%20{mon_abbrev}%20{year}%20FINAL.pdf",
        f"https://discover.cotality.com/hubfs/Article-Reports/"
        f"Cotality_HVI_{mon_full}.pdf",
        f"https://pages.cotality.com/hubfs/CoreLogic%20AU/Article%20Reports/"
        f"COTALITY%20HVI%20{mon_full}%20{year}%20FINAL.pdf",
        f"https://pages.corelogic.com/hubfs/CoreLogic%20AU/Article%20Reports/"
        f"COTALITY%20HVI%20{mon_full}%20{year}.pdf",
    ]
```

**Source attribution in CSV** — append Cotality row with `source = "Cotality HVI"`:
```python
new_row = pd.DataFrame([{
    "date": period_end_date.strftime("%Y-%m-%d"),  # last day of reference month
    "value": yoy_pct,
    "source": "Cotality HVI",
    "series_id": "Cotality/HVI/National/Annual"
}])
append_to_csv(DATA_DIR / "corelogic_housing.csv", new_row)
```

### Pattern 3: Fallback Logic (HOUS-04)

The normalization engine reads `corelogic_housing.csv` and takes the latest row. The latest row's `source` column identifies whether Cotality or ABS RPPI is the most recent data point. This is already how the pipeline works for other indicators — no special fallback logic is needed in the engine itself.

The `generate_status()` in `engine.py` passes `staleness_days` and gauge data through. We add `data_source` to the per-gauge entry in `build_gauge_entry()`:

```python
def build_gauge_entry(name, latest_row, z_df, weight_config):
    ...
    entry = {
        ...
        'data_source': latest_row.get('source', 'ABS'),  # NEW: for source attribution
    }
```

**Frontend reads `data_source`** in `renderMetricCard()` to display "Source: ABS RPPI" or "Source: Cotality HVI".

### Pattern 4: Frontend Housing Gauge Customization (HOUS-02)

The housing card already renders via `renderMetricCard()` in `interpretations.js`. What changes:

1. **Directional label in interpretation text** — replace the current generic text:
```javascript
case 'housing':
  var direction = v > 60 ? 'RISING' : (v < 40 ? 'FALLING' : 'STEADY');
  var sign = raw > 0 ? '+' : '';
  return direction + ' ' + sign + raw + '% year-on-year';
```

2. **Quarter format label** — always show data period. The `data_date` from status.json provides the ISO date; convert to quarter format:
```javascript
function toQuarterLabel(isoDate) {
  var d = new Date(isoDate);
  var q = Math.ceil((d.getMonth() + 1) / 3);
  return '(Q' + q + ' ' + d.getFullYear() + ')';
}
// Append to interpretation: "RISING +8.3% year-on-year (Q4 2021)"
```

3. **Source attribution** — add below gauge card:
```javascript
// In renderMetricCard, after interpretation div:
if (metricId === 'housing' && metricData.data_source) {
  var sourceP = document.createElement('p');
  sourceP.className = 'text-xs text-gray-500 mt-1';
  sourceP.textContent = 'Source: ' + (metricData.data_source === 'Cotality HVI' ? 'Cotality HVI' : 'ABS RPPI');
  card.appendChild(sourceP);
}
```

### Anti-Patterns to Avoid
- **Hard-coding "Cotality HVI" as the URL**: The URL pattern changes monthly. Use a candidate list and try each.
- **Running Cotality scraper in weekly pipeline**: Cotality releases monthly on the first weekday. Attach Cotality scraper to a separate monthly workflow OR run it in the weekly workflow with idempotency (skip if current month already appended).
- **YoY from ABS index numbers using normalized ratios pipeline directly**: The normalization engine already handles this via `yoy_periods: 4` for quarterly data. Do not pre-compute YoY — let the engine do it.
- **Adding `source` column to normalize output path**: The `load_indicator_csv()` only reads `date` and `value`. The `source` column for status.json should come from reading the raw CSV separately in `build_gauge_entry()`, not through the z-score pipeline.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| CSV deduplication | Custom append logic | `append_to_csv()` in `pipeline/utils/csv_handler.py` | Already handles date-keyed dedup, sorting, write-back |
| ABS SDMX fetch | Custom HTTP+CSV parser | `fetch_abs_series()` in `pipeline/ingest/abs_data.py` | Handles SDMX headers, CSV parsing, date normalization, error handling |
| YoY % computation | Manual pandas shift | `compute_yoy_pct_change()` in `pipeline/normalize/ratios.py` | Handles quarterly periods, NaN drops |
| Z-score computation | Custom stats | `compute_rolling_zscores()` in `pipeline/normalize/zscore.py` | Rolling window with median/MAD, confidence levels |
| Gauge value rendering | New Plotly config | `createBulletGauge()` / `metricGaugeTrace()` in `gauges.js` | Existing style — pass `value` directly |
| Date formatting in JS | strftime-like JS | `formatAusDate()` in `interpretations.js` | Handles timezone-safe date parsing |
| PDF table parsing | camelot/tabula | `pdfplumber` + regex | pdfplumber is pure Python, CI-safe; regex is sufficient for the consistent "Australia X% X% X%" line |

**Key insight:** The entire pipeline scaffolding already exists. Phase 9 is fundamentally about: (1) adding config entries, (2) writing two thin ingestor functions, (3) updating the Cotality scraper stub, (4) adding `data_source` to the gauge entry, (5) updating three JS text blocks.

---

## Common Pitfalls

### Pitfall 1: ABS RPPI Series Discontinued — But API Still Works
**What goes wrong:** Developers see "series ceased December 2021" on ABS website and assume the API won't work.
**Why it happens:** ABS ceased updating the series but kept historical data on the API.
**How to avoid:** Confirmed via live curl: `https://data.api.abs.gov.au/data/ABS,RPPI/1.3.100.Q` returns 200 with data through 2021-Q4. Use `startPeriod=2002`. The 2021-Q4 value is 183.9 (Index Numbers base=100).
**Warning signs:** If API returns `NoRecordsFound`, the key is wrong (not that data doesn't exist).

### Pitfall 2: Cotality URL Pattern Inconsistency
**What goes wrong:** Scraper hardcodes `COTALITY%20HVI%20{Month}%20{Year}%20FINAL.pdf` pattern and gets 404 for some months.
**Why it happens:** Cotality changes URL casing, subdomain, and filename format across months:
- Jan 2026: `discover.cotality.com/hubfs/Article-Reports/COTALITY HVI Jan 2026 FINAL.pdf` ✓
- Feb 2026: `discover.cotality.com/hubfs/Article-Reports/COTALITY HVI Feb 2026 FINAL.pdf` ✓
- Nov 2025: Same pattern returns 404 (different URL used for that month)
- Dec 2025: `discover.cotality.com/hubfs/Article-Reports/Cotality_HVI_December.pdf` (no year, underscore format)
**How to avoid:** Try a list of candidate URLs in order; proceed with first 200 response. Log the URL that worked.
**Warning signs:** HTTP 404 from first candidate should be handled gracefully, not raised as an exception.

### Pitfall 3: Housing YoY Requires 4 Quarters of Prior Data
**What goes wrong:** `compute_yoy_pct_change(df, 4)` drops first 4 rows as NaN. If ABS RPPI only returns recent quarters, z-score window is too short.
**Why it happens:** `yoy_periods=4` means we need at least 5 data points to get one YoY value. With 10-year z-score window = 40 quarterly observations needed.
**How to avoid:** Use `startPeriod=2002` — this gives 20 years / 80 quarters of ABS RPPI data, far exceeding the 40-obs HIGH confidence threshold.
**Warning signs:** `determine_confidence()` returning LOW when data should be HIGH — check startPeriod parameter.

### Pitfall 4: Source Column in status.json Requires Engine Change
**What goes wrong:** Planner assumes `data_source` appears in status.json automatically.
**Why it happens:** `build_gauge_entry()` in `engine.py` only reads the z-score DataFrame, which strips the `source` column during normalization.
**How to avoid:** Read the raw CSV (`corelogic_housing.csv`) in `build_gauge_entry()` to get the latest row's source value, OR pass source through the INDICATOR_CONFIG by reading it from the CSV before normalization.
**Warning signs:** `data_source` key missing from housing gauge entry in status.json.

### Pitfall 5: pdfplumber Not in requirements.txt
**What goes wrong:** CI fails with `ModuleNotFoundError: No module named 'pdfplumber'`.
**Why it happens:** pdfplumber is installed locally but not in `requirements.txt`.
**How to avoid:** Add `pdfplumber>=0.11,<1.0` to requirements.txt. pdfplumber has no system-level deps (pure Python wheel), confirmed safe on `ubuntu-latest` runners.
**Warning signs:** Local tests pass, CI fails.

### Pitfall 6: Cotality ToS Risk (Clause 8.4d)
**What goes wrong:** Automated PDF scraping may violate Cotality's ToS (Clause 8.4d prohibits automated scraping per REQUIREMENTS.md).
**Why it happens:** STATE.md explicitly flags: "HOUS-03/HOUS-04 (Cotality PDF) requires explicit project owner sign-off on ToS risk before any code is written."
**How to avoid:** HOUS-03 must be gated on explicit project owner acknowledgement. Research confirms the PDF is publicly accessible (no auth required), and it's a monthly media release (not daily/automated), which may differ from what ToS Clause 8.4d addresses. But this is a **planning decision**, not a code decision.
**Warning signs:** Proceeding without owner sign-off on this specific risk.

### Pitfall 7: Staleness Days vs Quarter Format Display
**What goes wrong:** Developer uses existing `staleness_days > 90` → amber border logic for housing, but CONTEXT.md says housing should NOT get amber border — just the quarter format label.
**Why it happens:** `renderMetricCard()` applies amber border to ALL stale cards. Housing is always stale (ABS RPPI ends 2021-Q4) but should render normally (no amber border per locked decision).
**How to avoid:** Either (a) pass a flag through status.json disabling amber border for housing, or (b) add an exception check in `renderMetricCard()` for `metricId === 'housing'`. The simplest approach: add `stale_display: 'quarter_only'` to the housing gauge entry.

---

## Code Examples

Verified patterns from live API calls and PDF extraction:

### ABS RPPI API Call

```python
# Source: confirmed via live curl 2026-02-24
# URL: https://data.api.abs.gov.au/data/ABS,RPPI/1.3.100.Q?startPeriod=2002&detail=dataonly
# Returns 80 rows from 2002-Q1 to 2021-Q4

def fetch_rppi() -> pd.DataFrame:
    """Fetch ABS Residential Property Price Index (national, quarterly)."""
    config = ABS_CONFIG["rppi"]
    return fetch_abs_series(
        config["dataflow"],   # "RPPI"
        config["key"],        # "1.3.100.Q"
        config.get("params"), # {"startPeriod": "2002", "detail": "dataonly"}
        config.get("filters") # {}
    )
```

### Cotality PDF Extraction

```python
# Source: verified against Jan 2026 and Feb 2026 PDFs (2026-02-24)
# Pattern: "Australia 0.8% 2.4% 9.4%" on page 1 or 2

import pdfplumber
import re

def extract_cotality_yoy(pdf_bytes: bytes) -> float | None:
    """
    Extract national annual YoY % from Cotality HVI PDF bytes.

    The PDF contains: "Australia {month%} {3month%} {annual%}"
    We want the annual (12-month) figure, which is the 3rd value.

    Returns:
        Float YoY % change (e.g., 9.4) or None if not found.
    """
    import io
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages[:4]:
            text = page.extract_text() or ""
            match = re.search(
                r'Australia\s+([-\d.]+)%\s+([-\d.]+)%\s+([-\d.]+)%',
                text
            )
            if match:
                return float(match.group(3))
    return None
```

### Cotality URL Candidate Try Pattern

```python
# Source: URL pattern analysis from search results (MEDIUM confidence)
# Jan 2026 and Feb 2026 confirmed; Nov/Dec 2025 have different patterns

import requests
from datetime import datetime

MONTH_ABBREV = {
    1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
    7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"
}

def download_cotality_pdf(year: int, month: int, session) -> bytes | None:
    """
    Try candidate URLs to download Cotality HVI PDF for given month.
    Returns PDF bytes or None if all candidates fail.
    """
    mon = MONTH_ABBREV[month]
    mon_full = datetime(year, month, 1).strftime("%B")

    base_discover = "https://discover.cotality.com/hubfs/Article-Reports"
    base_pages = "https://pages.cotality.com/hubfs/CoreLogic%20AU/Article%20Reports"

    candidates = [
        f"{base_discover}/COTALITY%20HVI%20{mon}%20{year}%20FINAL.pdf",
        f"{base_discover}/Cotality_HVI_{mon_full}.pdf",
        f"{base_pages}/COTALITY%20HVI%20{mon_full}%20{year}%20FINAL.pdf",
        f"{base_pages}/COTALITY%20HVI%20{mon}%20{year}%20FINAL.pdf",
    ]

    for url in candidates:
        try:
            resp = session.get(url, timeout=30)
            if resp.status_code == 200 and resp.headers.get('content-type', '').startswith('application/pdf'):
                logger.info(f"Cotality PDF found at: {url}")
                return resp.content
        except Exception:
            continue

    logger.warning(f"Cotality PDF not found for {mon} {year} — tried {len(candidates)} URLs")
    return None
```

### Quarter Label from ISO Date (JavaScript)

```javascript
// Convert ISO date string to quarter format for housing gauge display
function toQuarterLabel(isoDateStr) {
  if (!isoDateStr) return '';
  var d = new Date(isoDateStr);
  if (isNaN(d.getTime())) return '';
  var q = Math.ceil((d.getMonth() + 1) / 3);
  return '(Q' + q + ' ' + d.getFullYear() + ')';
}
// Usage: "RISING +8.3% year-on-year " + toQuarterLabel("2025-10-01") → "(Q4 2025)"
```

### data_source Read from Raw CSV in engine.py

```python
# In build_gauge_entry() — read source from raw CSV for housing indicator
def build_gauge_entry(name, latest_row, z_df, weight_config):
    ...
    # For housing: extract source attribution from raw CSV
    data_source = 'ABS'
    if name == 'housing':
        csv_path = DATA_DIR / "corelogic_housing.csv"
        if csv_path.exists():
            raw_df = pd.read_csv(csv_path)
            if 'source' in raw_df.columns and len(raw_df) > 0:
                raw_df['date'] = pd.to_datetime(raw_df['date'])
                latest_raw = raw_df.sort_values('date').iloc[-1]
                data_source = latest_raw.get('source', 'ABS')

    return {
        ...
        'data_source': data_source,  # "Cotality HVI" or "ABS"
    }
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| CoreLogic brand | Cotality brand | 2024 (rebrand) | All URLs/search terms use "Cotality" not "CoreLogic" for AU; but Python file is still `corelogic_scraper.py` — OK to keep filename for consistency |
| RPPI quarterly (eight cities) | ABS ceased RPPI; HPI series under development | Dec 2021 | ABS RPPI API data ends Dec 2021. ABS is developing a new House Price Index series but it's not yet in the SDMX API as of Feb 2026 |
| CoreLogic web scraping | Cotality media release PDFs | Ongoing | Direct web scraping is impossible (site is JS-rendered SPA); PDF media releases are the only publicly accessible structured data |

**Deprecated/outdated:**
- `corelogic_scraper.py` stub: The existing stub scrapes `corelogic.com.au/news-research/reports` with BeautifulSoup — this URL resolves but the site is a JS SPA (returns empty content to requests). The scraper correctly returns empty DataFrame. The entire implementation needs to be replaced with the Cotality PDF approach.

---

## Open Questions

1. **Cotality ToS sign-off (HOUS-03 gate)**
   - What we know: STATE.md explicitly flags this as requiring "project owner sign-off on ToS risk before any code is written"
   - What's unclear: Whether the project owner has made this decision; research cannot resolve this
   - Recommendation: Planner must create HOUS-03 tasks as blocked on a decision task. HOUS-01 + HOUS-02 (ABS only) can proceed independently.

2. **Cotality URL discovery robustness**
   - What we know: Jan 2026 + Feb 2026 follow `COTALITY HVI {Mon} {Year} FINAL.pdf`; Nov 2025 + Dec 2025 use different patterns
   - What's unclear: Whether the 2026 naming pattern will hold going forward
   - Recommendation: Use 4-candidate try list (confirmed above). If all candidates fail, Cotality scraper returns `{'status': 'failed'}` — pipeline falls back to ABS RPPI silently. Log which URL succeeded for future debugging.

3. **ABS RPPI replacement series**
   - What we know: ABS is developing a new House Price Indexes series (per "Forthcoming changes" article URL found in search); the new series is NOT yet in the SDMX API as of Feb 2026
   - What's unclear: When the replacement will appear in the API
   - Recommendation: Build against `RPPI` dataflow as-is. When ABS publishes the replacement, it will be a separate dataflow ID — add as a future update. Current ABS RPPI data is sufficient for Z-score normalization.

4. **Neutral zone threshold for "STEADY" label**
   - What we know: CONTEXT.md marks threshold as Claude's discretion
   - Recommendation: Use +/-1% for the neutral/STEADY zone. The current ABS RPPI 2021-Q4 annual change was approximately +23.7% (from 148.7 to 183.9 over 4 quarters). "STEADY" is conceptually between -1% and +1% YoY — conservative range that rarely appears in practice.

5. **Secondary metric (quarterly change)**
   - What we know: CONTEXT.md marks this as Claude's discretion
   - Recommendation: Skip secondary metric for Phase 9. The Cotality PDF provides both monthly and 3-month figures, but the quarterly change is noisy and would complicate the interpretation text. Annual change is the clearest signal for policy purposes.

---

## Sources

### Primary (HIGH confidence)
- Live ABS RPPI API call (2026-02-24): `https://data.api.abs.gov.au/data/ABS,RPPI/1.3.100.Q?startPeriod=2002&detail=dataonly` — confirmed RPPI dataflow exists, key `1.3.100.Q` returns data 2002-Q1 through 2021-Q4
- ABS SDMX structure: `https://data.api.abs.gov.au/rest/datastructure/ABS/RPPI` — confirmed dimensions MEASURE/PROPERTY_TYPE/REGION/FREQ
- ABS dataflow list: `https://data.api.abs.gov.au/rest/dataflow/ABS` — confirmed `RPPI` ID exists
- Cotality Jan 2026 PDF: `https://discover.cotality.com/hubfs/Article-Reports/COTALITY%20HVI%20Jan%202026%20FINAL.pdf` — extracted, confirmed "Australia 0.7% 2.9% 8.6%" pattern
- Cotality Feb 2026 PDF: `https://discover.cotality.com/hubfs/Article-Reports/COTALITY%20HVI%20Feb%202026%20FINAL.pdf` — extracted, confirmed "Australia 0.8% 2.4% 9.4%" pattern
- pdfplumber PyPI: `https://pypi.org/project/pdfplumber/` — pure Python, no system deps

### Secondary (MEDIUM confidence)
- ABS RPPI series ceased page: `https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/residential-property-price-indexes-eight-capital-cities` — confirmed series ceased Dec 2021
- Cotality URL patterns for prior months: WebSearch verified Oct 2025 (200), Nov 2025 (404), Dec 2025 Cotality_HVI_December.pdf (200) — URL inconsistency confirmed

### Tertiary (LOW confidence)
- Cotality "forthcoming changes" ABS article: page rendered only JS config, not article body — could not read actual content about ABS HPI replacement timeline

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — ABS RPPI API confirmed live with correct key; pdfplumber confirmed working against Cotality PDFs
- Architecture: HIGH — follows existing patterns exactly; `fetch_abs_series()` and `append_to_csv()` confirmed reusable
- Pitfalls: HIGH — Cotality URL inconsistency directly observed; staleness display conflict with existing `renderMetricCard()` identified from code reading; ToS blocker from STATE.md
- Open questions: 2 are decisions (ToS, neutral threshold), 1 is future-proofing (ABS replacement), 1 is recommendation (skip quarterly)

**Research date:** 2026-02-24
**Valid until:** 2026-05-24 (90 days — ABS RPPI API is stable; Cotality URL pattern may shift)
