# Phase 8: ASX Futures Live Data - Research

**Researched:** 2026-02-24
**Domain:** Python data pipeline (staleness detection) + vanilla JS dashboard UI (multi-meeting table, stacked probability bars)
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Multi-meeting layout**
- Vertical table with rows for each of the next 3-4 upcoming RBA meetings
- Next meeting row highlighted with a subtle accent (border or background)
- Keep existing "What Markets Expect" heading — no change to section title
- Horizontal scroll on mobile for the full table (no responsive card stacking)

**Probability visualization**
- Stacked horizontal bar per table row spanning the probability columns
- Traffic light color scheme: green (cut), amber (hold), red (hike) — replacing the existing blue/gray/red
- Update the existing single-meeting probability display colors to match the new traffic light scheme for consistency

**Staleness signals**
- Always show "Data as of [date]" below the table — visible whether data is fresh or stale
- When ASX endpoint returns no data at all, show a placeholder message ("Market futures data currently unavailable") rather than hiding the section
- Pipeline: warn at 14 days stale, error at 30 days stale (ASX is optional tier, so error is non-fatal but logged)

**Meeting date labels**
- Full date format: "20 May 2026", "1 Jul 2026", etc.
- Exact RBA meeting dates shown (not just month approximations)

### Claude's Discretion

- Whether to add a "NEXT" badge on the highlighted first row, or rely on visual highlight alone
- Whether to show current cash rate as a reference note above the table
- Whether to include a basis-point change column alongside implied rate
- Percentage label placement on stacked bars (inside segments vs below)
- How to handle zero-width segments (omit vs show hairline)
- Staleness display styling (inline annotation, banner, or dim) — pick approach matching existing dashboard patterns

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope
</user_constraints>

---

## Summary

Phase 8 upgrades the ASX futures section from a single-meeting snapshot to a multi-meeting probability table. The data pipeline and CSV infrastructure are already largely built — `asx_futures.csv` already contains multi-meeting rows per scrape date, and the scraper already calls the confirmed-live MarkitDigital endpoint. The work is therefore primarily: (1) expanding `status.json` to carry multi-meeting data, (2) adding staleness detection logic to the pipeline, and (3) replacing the existing `renderASXTable` function in `interpretations.js` with a new multi-meeting table renderer using the traffic light color scheme and stacked bars.

The ASX MarkitDigital endpoint (`https://asx.api.markitdigital.com/asx-research/1.0/derivatives/interest-rate/IB/futures?days=365&height=1&width=1`) was confirmed live on 2026-02-24, returning 18 contracts. The existing scraper code in `pipeline/ingest/asx_futures_scraper.py` already processes all 18 contracts into `asx_futures.csv` with the full schema required. The normalization engine in `pipeline/normalize/engine.py` currently only extracts the single next-meeting row via `build_asx_futures_entry()` — this function must be extended to pass an array of upcoming meetings.

The frontend currently renders the ASX section via `InterpretationsModule.renderASXTable()` in `public/js/interpretations.js`. This single function controls all ASX UI. The `status.json` contract needs a new `meetings` array field alongside the existing single-meeting fields to maintain backward compatibility while adding multi-meeting support.

**Primary recommendation:** Extend the `status.json` `asx_futures` object with a `meetings` array (next 3-4 meetings), add staleness warnings to the pipeline, and rewrite `renderASXTable` to produce a multi-meeting table with stacked traffic-light bars and an always-visible "Data as of" footer.

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| ASX-01 | ASX MarkitDigital endpoint verified working in GitHub Actions CI and `asx_futures.csv` contains rows dated within the past 7 days | Endpoint confirmed live (18 items, 2026-02-24). CI workflow `daily-asx-futures.yml` already runs weekdays. Verification step needed in CI to assert CSV freshness. |
| ASX-02 | Dashboard "What Markets Expect" section shows implied rate percentage and cut/hold/hike probability bars drawn from fresh data, not placeholders | `renderASXTable` in `interpretations.js` must be replaced with multi-meeting renderer. `status.json` needs `meetings[]` array. Stacked bars built with CSS `flex` — no extra library needed. |
| ASX-03 | Pipeline warns (non-fatal) when `asx_futures.csv` has no rows newer than 14 days | Staleness check in `fetch_and_save()` in `asx_futures_scraper.py`. Use `logger.warning()` at 14 days, `logger.error()` at 30 days. Pipeline must still exit 0 — ASX is optional tier. |
| ASX-04 | Dashboard shows probability bars for the next 3-4 upcoming RBA meetings, not just the soonest one | `build_asx_futures_entry()` in `engine.py` must return `meetings[]` array instead of single row. Frontend renderer loops over array. |
</phase_requirements>

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pandas | >=2.0,<3.0 | CSV read, date filtering, freshness check | Already in requirements.txt; project uses it throughout |
| Python logging | stdlib | Pipeline warn/error for staleness | Already used in `asx_futures_scraper.py` |
| Tailwind CSS | CDN (via `tailwind.config`) | Table layout, traffic light colors, overflow-x-auto | Already in `index.html`; all existing UI uses Tailwind |
| Intl.DateTimeFormat | Browser built-in | "20 May 2026" date format | Already in `interpretations.js` as `ausDateFormatter` |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `stefanzweifel/git-auto-commit-action` | v5 | CI auto-commit for data updates | Already wired in both workflow files |
| requests (via `create_session`) | >=2.28,<3.0 | HTTP with retry/backoff | Already used in `asx_futures_scraper.py` |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| CSS flex stacked bars | Plotly bar chart | Plotly adds ~3MB bundle weight, requires async render; CSS flex is instant, no dependencies |
| CSS flex stacked bars | SVG `<rect>` | SVG requires coordinate math; CSS flex is simpler and already used for other UI elements |
| Python logging warn/error | Custom exception classes | Overkill — ASX is optional tier; log-and-continue is the project pattern |

**Installation:** No new packages required. All dependencies are already present.

---

## Architecture Patterns

### Recommended Project Structure

No new files needed beyond modifying existing ones:

```
pipeline/
├── ingest/
│   └── asx_futures_scraper.py    # Add staleness check to fetch_and_save()
├── normalize/
│   ├── engine.py                 # Extend build_asx_futures_entry() → meetings[]
│   └── ratios.py                 # Extend load_asx_futures_csv() → multi-meeting
public/
├── js/
│   └── interpretations.js        # Replace renderASXTable() with multi-meeting renderer
├── data/
│   └── status.json               # Contract change: asx_futures.meetings[] added
```

### Pattern 1: status.json Contract Extension

**What:** Add a `meetings` array to the existing `asx_futures` top-level object in `status.json`. Keep all existing fields for backward compatibility.

**When to use:** The frontend already reads `data.asx_futures` — adding a `meetings[]` array alongside existing fields means tests 6 and 7 in `dashboard.spec.js` continue to pass without modification.

**Example — new asx_futures shape:**
```json
{
  "asx_futures": {
    "current_rate": 3.85,
    "next_meeting": "2026-03-03",
    "implied_rate": 3.86,
    "probabilities": { "cut": 0, "hold": 100, "hike": 0 },
    "direction": "hold",
    "data_date": "2026-02-24",
    "staleness_days": 0,
    "meetings": [
      {
        "meeting_date": "2026-03-03",
        "meeting_date_label": "3 Mar 2026",
        "implied_rate": 3.86,
        "change_bp": 1.0,
        "probability_cut": 0,
        "probability_hold": 100,
        "probability_hike": 0
      },
      {
        "meeting_date": "2026-04-07",
        "meeting_date_label": "7 Apr 2026",
        "implied_rate": 3.875,
        "change_bp": 2.5,
        "probability_cut": 0,
        "probability_hold": 100,
        "probability_hike": 0
      }
    ]
  }
}
```

### Pattern 2: load_asx_futures_csv() Extension

**What:** The existing `load_asx_futures_csv()` in `ratios.py` returns a single-row dict. Extend it to also return the 3-4 upcoming meetings as a list.

**When to use:** Keep the existing single-row return path intact (still used by `build_asx_futures_entry()`). Add a second return path or extend the return dict with a `meetings` list.

**Example:**
```python
def load_asx_futures_csv(csv_path):
    # ... existing code to find latest_date and next_meeting_row ...

    # NEW: collect next 3-4 upcoming meetings from the latest scrape
    upcoming = future_meetings.sort_values('meeting_date').head(4)
    meetings = []
    for _, row in upcoming.iterrows():
        meetings.append({
            'meeting_date': row['meeting_date'].strftime('%Y-%m-%d'),
            'implied_rate': float(row['implied_rate']),
            'change_bp': float(row['change_bp']),
            'probability_cut': float(row['probability_cut']),
            'probability_hold': float(row['probability_hold']),
            'probability_hike': float(row['probability_hike']),
        })

    return {
        # ... existing fields ...
        'meetings': meetings,
    }
```

### Pattern 3: Staleness Detection in Pipeline

**What:** After saving CSV, check the maximum `date` in the file and emit `logger.warning()` at >=14 days stale or `logger.error()` at >=30 days stale. Never raise — return status dict with `'stale': True`.

**When to use:** Inside `fetch_and_save()` in `asx_futures_scraper.py`, after writing the CSV. The pipeline already handles `status == 'failed'` gracefully for optional sources.

**Example:**
```python
def _check_staleness(csv_path: Path) -> None:
    """Log warnings if ASX data is stale. Non-fatal — ASX is optional tier."""
    try:
        df = pd.read_csv(csv_path)
        df['date'] = pd.to_datetime(df['date'])
        latest = df['date'].max()
        staleness_days = (datetime.now() - latest).days
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
```

### Pattern 4: Multi-Meeting Table with CSS Stacked Bars

**What:** Build the table using the existing safe DOM pattern (`createElement`/`textContent` only — no `innerHTML`). Stacked bar is a `div.flex` containing three `div` children sized by `flex: <probability>`.

**When to use:** Inside the replacement `renderASXTable()` function in `interpretations.js`. The existing function is entirely replaced.

**Traffic light colors (match `tailwind.config` custom colors):**
- Cut: `#10b981` (`gauge-green`)
- Hold: `#f59e0b` (`gauge-amber`)
- Hike: `#ef4444` (`gauge-red`)

**Mobile horizontal scroll:** Wrap the table in `div.overflow-x-auto` — already established in the methodology table (`index.html` line ~367).

**Example DOM structure:**
```javascript
// Stacked bar for one meeting row
function createStackedBar(probCut, probHold, probHike) {
  var bar = document.createElement('div');
  bar.className = 'flex h-4 rounded overflow-hidden w-full';
  bar.style.minWidth = '120px';

  // Only render segment if probability > 0
  if (probCut > 0) {
    var cutSeg = document.createElement('div');
    cutSeg.style.flex = String(probCut);
    cutSeg.style.backgroundColor = '#10b981';
    bar.appendChild(cutSeg);
  }
  if (probHold > 0) {
    var holdSeg = document.createElement('div');
    holdSeg.style.flex = String(probHold);
    holdSeg.style.backgroundColor = '#f59e0b';
    bar.appendChild(holdSeg);
  }
  if (probHike > 0) {
    var hikeSeg = document.createElement('div');
    hikeSeg.style.flex = String(probHike);
    hikeSeg.style.backgroundColor = '#ef4444';
    bar.appendChild(hikeSeg);
  }
  return bar;
}
```

**Zero-width segments:** Omit segments with `probability === 0` entirely (no hairline). This avoids rendering an invisible flex child and is the cleanest visual outcome.

**First row highlight:** Apply `border-l-2 border-finance-accent bg-finance-gray/50` to the `<tr>` of the first (soonest) upcoming meeting row.

**"Data as of [date]":** Rendered as a `<p>` below the table, always visible, using `formatAusDate()` (already in `InterpretationsModule`).

**Placeholder when no data:** When `asxData` is null or `asxData.meetings` is empty, show `container.style.display = ''` (visible, not hidden as in current code) and render "Market futures data currently unavailable" text.

### Anti-Patterns to Avoid

- **Hiding section on no data:** Current `renderASXTable` calls `container.style.display = 'none'` when data is unavailable. Phase 8 changes this to always show the section — either the table or the placeholder message.
- **innerHTML for bar segments:** The project prohibits `innerHTML`. Use `createElement` + `style.flex` only.
- **Raising exceptions for staleness:** Staleness is log-only. Never throw — it would escalate ASX from optional to critical failure tier.
- **Fetching a new endpoint:** The MarkitDigital endpoint is confirmed working. Do not add a second endpoint. Do not change the URL.
- **Modifying asx_futures.csv schema:** The CSV already has the correct multi-column schema. No schema changes needed.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Stacked probability bars | Canvas or SVG drawing code | CSS `flex` with `style.flex = probability` | Three lines of DOM code; no coordinate math; already responsive |
| Date formatting | Custom date parser | `Intl.DateTimeFormat` (already `ausDateFormatter` in `interpretations.js`) | Already present; handles locale correctly |
| HTTP retry logic | Manual retry loop | `create_session(retries=3, backoff_factor=0.5)` | Already used in scraper; handles 503/429 automatically |

**Key insight:** The project's existing infrastructure handles almost everything. The primary work is wiring existing data (already in CSV) through the JSON contract (minor engine change) to a new UI renderer (replacement of one function).

---

## Common Pitfalls

### Pitfall 1: Past Meetings in CSV Confuse "Next 3-4" Selection

**What goes wrong:** `load_asx_futures_csv()` finds meetings from the latest scrape date, but some `meeting_date` values may already be in the past by the time the dashboard renders (e.g., if pipeline ran last week).

**Why it happens:** The CSV accumulates rows over time. The current code already handles this with `future_meetings = latest_rows[latest_rows['meeting_date'] >= today]` — but "today" in Python (pipeline time) differs from "today" in JavaScript (browser time).

**How to avoid:** Filter by `meeting_date >= today` in Python at pipeline time. Accept that a meeting that passes between pipeline runs and page load may briefly show. This is acceptable for a daily-updated dashboard.

**Warning signs:** Multi-meeting table shows a meeting that already happened as the first row.

### Pitfall 2: Probabilities Don't Sum to 100

**What goes wrong:** Due to float rounding in `_derive_probabilities()`, `probability_cut + probability_hold + probability_hike` may sum to 99 or 101.

**Why it happens:** `round()` on each probability independently. The existing code uses `min(100, round(...))` which can leave gaps.

**How to avoid:** In the frontend renderer, verify the sum before drawing bars. If sum != 100, normalize by adjusting the largest segment. Alternatively, compute `probability_hold = 100 - probability_cut - probability_hike` in the frontend rather than trusting three independent values.

**Warning signs:** Stacked bar doesn't reach full width, or overflows.

### Pitfall 3: ASX Endpoint 404 History

**What goes wrong:** The endpoint returned 404 on 2026-02-07 but 200 on 2026-02-24 (confirmed in STATE.md). This intermittency is a real concern for CI verification.

**Why it happens:** MarkitDigital API appears to have periodic outages. The `create_session(retries=3)` handles transient failures.

**How to avoid:** The `daily-asx-futures.yml` CI job already runs the scraper — ASX-01 verification should check whether the CSV was _recently updated_ (within 7 days), not whether the endpoint returned 200 in this specific run. Add a post-run step that reads `asx_futures.csv` and asserts `max(date) >= today - 7 days`.

**Warning signs:** CI passes (scraper runs without exception) but CSV has no rows from the past week.

### Pitfall 4: Existing Tests Broke by ASX Section Behavior Change

**What goes wrong:** Test 7 in `dashboard.spec.js` asserts `expect(asxContainer).toBeHidden()` when `asx_futures` is null. Phase 8 changes this behavior — the section must now be _visible_ with a placeholder message.

**Why it happens:** The current `renderASXTable()` calls `container.style.display = 'none'` when data is unavailable. This behavior is tested explicitly.

**How to avoid:** Update test 7 to assert `expect(asxContainer).toBeVisible()` and `expect(asxContainer).toContainText('Market futures data currently unavailable')` instead.

**Warning signs:** Test 7 fails after Phase 8 implementation.

### Pitfall 5: Mobile Overflow Without Explicit Min-Width

**What goes wrong:** The stacked bar columns in the table compress to zero width on narrow screens because `flex` children collapse without a `min-width`.

**Why it happens:** CSS `flex` on table cells interacts poorly with `table-layout: auto` on narrow viewports.

**How to avoid:** Set `overflow-x-auto` on the table wrapper (already the project pattern for the methodology table). Set `minWidth: '120px'` on the stacked bar div. The table itself should have `style="min-width: 480px"` or `class="w-full min-w-[480px]"`.

---

## Code Examples

### Extending build_asx_futures_entry() in engine.py

```python
def build_asx_futures_entry():
    """
    Build the top-level asx_futures dict for status.json.
    Extended in Phase 8 to include meetings[] array.
    """
    csv_path = DATA_DIR / "asx_futures.csv"
    data = load_asx_futures_csv(csv_path)
    if data is None:
        return None

    # ... existing direction + staleness logic ...

    entry = {
        'current_rate': current_rate,
        'next_meeting': data['meeting_date'],
        'implied_rate': round(data['implied_rate'], 2),
        'probabilities': {
            'cut': round(data['probability_cut'], 0),
            'hold': round(data['probability_hold'], 0),
            'hike': round(data['probability_hike'], 0),
        },
        'direction': direction,
        'data_date': data['data_date'],
        'staleness_days': staleness_days,
    }

    # Phase 8: add meetings array
    if 'meetings' in data:
        aus_date_fmt = lambda d: datetime.strptime(d, '%Y-%m-%d').strftime('%-d %b %Y')
        entry['meetings'] = [
            {
                'meeting_date': m['meeting_date'],
                'meeting_date_label': aus_date_fmt(m['meeting_date']),
                'implied_rate': round(m['implied_rate'], 2),
                'change_bp': m['change_bp'],
                'probability_cut': round(m['probability_cut'], 0),
                'probability_hold': round(m['probability_hold'], 0),
                'probability_hike': round(m['probability_hike'], 0),
            }
            for m in data['meetings']
        ]

    return entry
```

Note: `%-d` for day-without-zero-padding is Linux/macOS only. For cross-platform safety use `str(int(d.day))` or `lstrip('0')`.

### Staleness check in asx_futures_scraper.py fetch_and_save()

```python
# After result_df.to_csv(output_path, index=False):
_check_staleness(output_path)
```

Where `_check_staleness()` is the function shown in Pattern 3 above.

### CI freshness assertion (daily-asx-futures.yml addition)

```yaml
- name: Verify ASX data freshness
  run: |
    python3 -c "
    import pandas as pd
    from datetime import datetime, timedelta
    df = pd.read_csv('data/asx_futures.csv')
    df['date'] = pd.to_datetime(df['date'])
    latest = df['date'].max()
    threshold = datetime.now() - timedelta(days=7)
    if latest < threshold:
        print(f'FAIL: Latest ASX data is {latest.date()}, older than 7 days')
        exit(1)
    print(f'OK: Latest ASX data is {latest.date()}')
    "
```

### Frontend multi-meeting table skeleton (interpretations.js)

```javascript
function renderASXTable(containerId, asxData) {
  var container = document.getElementById(containerId);
  if (!container) return;
  container.textContent = '';

  // Phase 8: always show section; use placeholder if no data
  container.style.display = '';

  var heading = document.createElement('h3');
  heading.className = 'text-lg font-semibold text-gray-200 mb-3';
  heading.textContent = 'What Markets Expect';
  container.appendChild(heading);

  if (!asxData || !asxData.meetings || asxData.meetings.length === 0) {
    var placeholder = document.createElement('p');
    placeholder.className = 'text-sm text-gray-500 italic';
    placeholder.textContent = 'Market futures data currently unavailable';
    container.appendChild(placeholder);
    return;
  }

  var subline = document.createElement('p');
  subline.className = 'text-xs text-gray-500 mb-3';
  subline.textContent = 'Based on ASX 30 Day Interbank Cash Rate Futures pricing';
  container.appendChild(subline);

  // Table with overflow-x-auto for mobile
  var wrapper = document.createElement('div');
  wrapper.className = 'overflow-x-auto';

  var table = document.createElement('table');
  table.className = 'w-full text-sm';
  table.style.minWidth = '480px';

  // ... thead with Meeting / Implied Rate / Probability columns ...
  // ... tbody: loop asxData.meetings, first row highlighted ...
  // ... each row: meeting_date_label, implied_rate%, stacked bar + % labels ...

  wrapper.appendChild(table);
  container.appendChild(wrapper);

  // Always-visible "Data as of" footer
  var footer = document.createElement('p');
  footer.className = 'text-xs text-gray-500 mt-3';
  footer.textContent = 'Data as of ' + formatAusDate(asxData.data_date);
  container.appendChild(footer);
}
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single-meeting ASX display | Multi-meeting table | Phase 8 | Shows market curve, not just next meeting |
| Blue/gray/red probability colors | Traffic light (green/amber/red) | Phase 8 | Consistent with Tailwind custom colors already defined |
| Section hidden when no data | Section visible with placeholder | Phase 8 | Dashboard always shows section, consistent UX |
| No staleness signal in pipeline | warn@14d / error@30d | Phase 8 | Operators know when data is stale |

**Deprecated/outdated:**
- `container.style.display = 'none'` in `renderASXTable`: removed in Phase 8 (section always visible)
- Single-meeting `probabilities` object as sole UI source: supplemented by `meetings[]` array

---

## Open Questions

1. **"NEXT" badge on first row vs visual highlight alone**
   - What we know: User left this to Claude's discretion. Existing dashboard uses `border-l` accents for highlighting (see existing single-meeting table in `renderASXTable`).
   - What's unclear: Whether a text badge adds clarity or clutter in a compact table.
   - Recommendation: Use `border-l-2 border-finance-accent` on the first `<tr>` only (no badge). This matches the existing `renderASXTable` highlight pattern and is unambiguous without adding text.

2. **Current cash rate reference above table**
   - What we know: `asxData.current_rate` is already in `status.json`. User left this to discretion.
   - Recommendation: Show it as a one-line note above the table: "Current cash rate: 3.85%". Small text, `text-xs text-gray-400`. Provides reference without being prominent.

3. **Basis-point change column**
   - What we know: `change_bp` is already in the CSV and will be in `meetings[]`. User left this to discretion.
   - Recommendation: Include it. The dashboard philosophy is "data, not opinion" and bp change directly answers "how much is the market pricing in?". Show as `+2.5bp` / `-25bp` in a narrow column.

4. **Percentage label placement on stacked bars**
   - What we know: User left this to discretion.
   - Recommendation: Show percentage labels below the bar as a single line (`"0% cut / 100% hold / 0% hike"` condensed), not inside bar segments. Inside segments break at narrow widths; below is always legible.

---

## Sources

### Primary (HIGH confidence)

- Live endpoint test: `curl https://asx.api.markitdigital.com/asx-research/1.0/derivatives/interest-rate/IB/futures?days=365&height=1&width=1` — confirmed 200 + 18 items on 2026-02-24
- Codebase read: `pipeline/ingest/asx_futures_scraper.py` — full scraper logic, CSV schema, retry setup
- Codebase read: `pipeline/normalize/engine.py` — `build_asx_futures_entry()`, `generate_status()`
- Codebase read: `pipeline/normalize/ratios.py` — `load_asx_futures_csv()` function
- Codebase read: `public/js/interpretations.js` — `renderASXTable()`, DOM patterns, `formatAusDate()`
- Codebase read: `public/js/gauge-init.js` — how `renderASXTable` is called
- Codebase read: `data/asx_futures.csv` — confirmed multi-meeting data already present (17 meetings per scrape date across 9 scrape dates)
- Codebase read: `.github/workflows/daily-asx-futures.yml` — CI structure
- Codebase read: `public/data/status.json` — current `asx_futures` contract shape
- Codebase read: `tests/dashboard.spec.js` — existing ASX tests (tests 6 and 7)
- Codebase read: `public/index.html` — Tailwind config with `gauge-green`, `gauge-amber`, `gauge-red` custom colors

### Secondary (MEDIUM confidence)

- STATE.md: ASX endpoint had 404 on 2026-02-07, 200 on 2026-02-24 — intermittency confirmed by project history

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries already in use; no new dependencies
- Architecture: HIGH — based on direct codebase reading; all patterns match existing project conventions
- Pitfalls: HIGH — sourced from live testing (endpoint), test file inspection (test 7 breakage), and project state history (endpoint intermittency)

**Research date:** 2026-02-24
**Valid until:** 2026-03-24 (stable — no fast-moving dependencies; endpoint URL may change but MarkitDigital API has been stable)
