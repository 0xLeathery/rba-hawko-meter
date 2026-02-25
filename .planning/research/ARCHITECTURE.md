# Architecture Research

**Domain:** Snapshot archiving, delta/momentum tracking, sparklines, and social sharing on an existing Python pipeline + Vanilla JS + Netlify dashboard
**Researched:** 2026-02-26
**Confidence:** HIGH (all findings derived from direct codebase inspection + first-principles analysis of the existing architecture; no guesswork)

---

## System Overview (Existing v4.0)

```
┌─────────────────────────────────────────────────────────────────────┐
│                     GitHub Actions (scheduled)                       │
│  ┌──────────────────┐             ┌──────────────────────────────┐  │
│  │ weekly-pipeline  │             │  daily-asx-futures           │  │
│  │ (Mon 2:07 UTC)   │             │  (weekdays)                  │  │
│  └────────┬─────────┘             └───────────────┬──────────────┘  │
└───────────┼───────────────────────────────────────┼─────────────────┘
            │ python -m pipeline.main                │ asx_futures_scraper
            ▼                                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          Python Pipeline                             │
│                                                                      │
│  pipeline/ingest/           pipeline/normalize/                     │
│  ┌──────────────────┐       ┌──────────────────┐   ┌────────────┐  │
│  │ abs_data.py      │──────▶│ ratios.py        │──▶│ engine.py  │  │
│  │ rba_data.py      │       │ zscore.py        │   │            │  │
│  │ asx_futures_     │       │ gauge.py         │   └─────┬──────┘  │
│  │   scraper.py     │       └──────────────────┘         │          │
│  │ corelogic_       │                                     │          │
│  │   scraper.py     │  ──────────────────────────────────┘          │
│  │ nab_scraper.py   │                                                │
│  └──────────────────┘                                                │
│          │                                                            │
│          ▼                                                            │
│  data/*.csv (append-only, deduplicated per-source)                   │
│          ▼ engine.py writes                                           │
│  public/data/status.json  (complete pipeline output, ~5KB)           │
└─────────────────────────────────────────────────────────────────────┘
            │
            │ git commit → Netlify auto-deploy
            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Netlify CDN (static)                          │
│                                                                      │
│  public/index.html                                                   │
│  public/js/                                                          │
│  ┌────────────┐  ┌───────────┐  ┌────────────────────┐  ┌────────┐ │
│  │gauge-init  │  │gauges.js  │  │interpretations.js  │  │data.js │ │
│  │.js (orch.) │  │(Plotly)   │  │(text/card render)  │  │(cache) │ │
│  └────────────┘  └───────────┘  └────────────────────┘  └────────┘ │
│                                                                      │
│  Fetches: public/data/status.json at page load (DataModule.fetch)   │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Location |
|-----------|----------------|----------|
| `pipeline/ingest/*.py` | Fetch raw data from ABS/RBA/ASX/scrapers, append to CSV | `data/*.csv` |
| `pipeline/normalize/ratios.py` | YoY % normalization, CSV to DataFrame | In-memory |
| `pipeline/normalize/zscore.py` | Rolling Z-scores (10yr window, robust median/MAD) | In-memory |
| `pipeline/normalize/gauge.py` | Z-score to 0-100 gauge value, zone classification, hawk score | In-memory |
| `pipeline/normalize/engine.py` | Orchestrates all indicators, writes `status.json` | `public/data/status.json` |
| `public/js/data.js` | `DataModule.fetch()` with caching, error/loading state | Browser |
| `public/js/gauge-init.js` | Main orchestrator: fetches status.json, calls all renderers | Browser |
| `public/js/gauges.js` | `GaugesModule`: Plotly hero/bullet gauge rendering | Browser |
| `public/js/interpretations.js` | `InterpretationsModule`: verdict, ASX table, metric cards | Browser |

---

## V5.0 Feature Integration Architecture

### New Features and Where They Fit

```
┌────────────────────────────────────────────────────────────────────┐
│                   V5.0 ADDITIONS (highlighted)                      │
│                                                                     │
│  NEW: pipeline/normalize/archive.py                                │
│    snapshot_current(status) → public/data/snapshots/YYYY-MM-DD.json│
│    read_previous_snapshot() → dict | None                           │
│            │                                                         │
│            │ previous_value injected                                 │
│            ▼                                                         │
│  MODIFIED: pipeline/normalize/engine.py                            │
│    build_gauge_entry() gains previous_value, delta, direction       │
│    generate_status() calls archive.py before writing status.json   │
│            │                                                         │
│            ▼                                                         │
│  MODIFIED: public/data/status.json                                 │
│    per-gauge: + previous_value, delta, direction (optional fields)  │
│    overall:  + previous_hawk_score, hawk_score_delta                │
│    snapshots: public/data/snapshots/YYYY-MM-DD.json (new)          │
│              public/data/snapshots/index.json (new)                 │
│            │                                                         │
│            ▼                                                         │
│  MODIFIED: public/js/interpretations.js                            │
│    renderMetricCard() gains delta badge + canvas slot for sparkline │
│                                                                     │
│  NEW: public/js/sparklines.js                                      │
│    SparklinesModule.render(canvasId, historyArray, color)          │
│    Canvas 2D API, no CDN dependency                                 │
│                                                                     │
│  NEW: public/js/share.js                                           │
│    ShareModule.share(score, verdict)                                │
│    Web Share API with clipboard fallback                            │
│                                                                     │
│  MODIFIED: public/index.html                                       │
│    + static OG/Twitter meta tags                                    │
│    + share button in hero card                                      │
│    + newsletter Netlify Form                                        │
│    + <script> tags for new JS modules                               │
└────────────────────────────────────────────────────────────────────┘
```

---

## Feature 1: Snapshot Archiving + `previous_value`

### Storage Decision: Git-Committed JSON Snapshot Files

**Use one file per pipeline run in `public/data/snapshots/YYYY-MM-DD.json`, committed to git.**

Why not alternatives:

| Option | Verdict | Reason |
|--------|---------|--------|
| Git-committed per-date snapshot files | **USE THIS** | Zero infrastructure cost; Netlify serves as static files; history preserved in git; fits existing commit pattern; no merge conflicts |
| Append to a single `hawk_score_history.json` | Avoid | Grows unbounded; git merge conflicts if GHA re-triggered; harder to query a specific date |
| External DB (Supabase, PlanetScale) | Avoid | Introduces paid dependency and network call at pipeline time; violates zero-cost constraint |
| Rely only on existing CSV data | Avoid | CSVs store raw values; reconstructing prior gauge score requires re-running full Z-score normalization pipeline — slow and fragile |

**Snapshot file structure** (`public/data/snapshots/2026-02-17.json`):

```json
{
  "date": "2026-02-17",
  "hawk_score": 48.3,
  "gauges": {
    "inflation":          { "value": 32.1, "raw_value": 3.9 },
    "wages":              { "value": 82.0, "raw_value": 5.2 },
    "employment":         { "value": 35.0, "raw_value": 1.1 },
    "spending":           { "value": 58.5, "raw_value": 4.8 },
    "building_approvals": { "value": 55.2, "raw_value": 3.1 },
    "housing":            { "value": 61.0, "raw_value": 9.1 },
    "business_confidence":{ "value": 70.0, "raw_value": 83.0 }
  }
}
```

Keep snapshots minimal: gauge values (0-100) and raw_value only. Full status.json remains the source of truth for current rendering. This keeps snapshot files under 500 bytes each.

**Snapshot index file** (`public/data/snapshots/index.json`):

```json
["2026-02-24", "2026-02-17", "2026-02-10", "2026-02-03"]
```

Written by `archive.py` each run (most-recent-first). Frontend uses this to know which dates are available for the historical hawk score chart without directory listing (Netlify does not expose directory indexes).

### New Python Module: `pipeline/normalize/archive.py`

```python
"""
Snapshot archival for v5.0 direction/momentum tracking.

Writes a minimal gauge snapshot on each pipeline run and
reads the most recent prior snapshot for previous_value computation.
"""

import json
from datetime import date
from pathlib import Path

import pipeline.config

SNAPSHOTS_DIR = Path("public/data/snapshots")
INDEX_FILE = SNAPSHOTS_DIR / "index.json"


def snapshot_current(status: dict) -> None:
    """Write today's minimal snapshot and update index.json."""
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()  # "2026-02-24"

    minimal = {
        "date": today,
        "hawk_score": status["overall"]["hawk_score"],
        "gauges": {
            name: {
                "value": g["value"],
                "raw_value": g["raw_value"],
            }
            for name, g in status.get("gauges", {}).items()
        },
    }

    snap_path = SNAPSHOTS_DIR / f"{today}.json"
    with open(snap_path, "w") as f:
        json.dump(minimal, f, indent=2)

    # Update index (prepend today, deduplicate, keep most recent 52)
    existing = _read_index()
    updated = [today] + [d for d in existing if d != today]
    updated = updated[:52]
    with open(INDEX_FILE, "w") as f:
        json.dump(updated, f)


def read_previous_snapshot(min_age_days: int = 5) -> dict | None:
    """
    Read the most recent snapshot that is at least min_age_days old.

    The age guard prevents same-week double-runs from treating the
    current week's snapshot as "previous". Returns None if no
    qualifying snapshot exists.
    """
    index = _read_index()
    today = date.today()
    for date_str in index:
        snap_date = date.fromisoformat(date_str)
        if (today - snap_date).days >= min_age_days:
            snap_path = SNAPSHOTS_DIR / f"{date_str}.json"
            if snap_path.exists():
                with open(snap_path) as f:
                    return json.load(f)
    return None


def _read_index() -> list:
    if INDEX_FILE.exists():
        with open(INDEX_FILE) as f:
            return json.load(f)
    return []
```

### Modified: `pipeline/normalize/engine.py`

`generate_status()` reads the prior snapshot before the main indicator loop and passes it into `build_gauge_entry()`:

```python
# At the top of generate_status():
from pipeline.normalize.archive import read_previous_snapshot, snapshot_current
prev_snap = read_previous_snapshot()
prev_gauges = prev_snap.get("gauges", {}) if prev_snap else {}

# Inside process_indicator() call chain → build_gauge_entry() signature change:
entry = build_gauge_entry(name, latest, df, weight_config,
                          config=config, prev_gauges=prev_gauges)

# In build_gauge_entry():
prev = prev_gauges.get(name)
if prev is not None:
    delta = round(gauge_value - prev["value"], 1)
    entry["previous_value"] = prev["value"]
    entry["delta"] = delta
    if abs(delta) <= 2.0:
        entry["direction"] = "STEADY"
    elif delta > 0:
        entry["direction"] = "RISING"
    else:
        entry["direction"] = "FALLING"

# At the end of generate_status(), after writing status.json:
snapshot_current(status)
```

Overall section gets similar treatment:

```python
if prev_snap is not None:
    status["overall"]["previous_hawk_score"] = prev_snap["hawk_score"]
    status["overall"]["hawk_score_delta"] = round(
        hawk_score - prev_snap["hawk_score"], 1
    )
```

### Modified: `public/data/status.json` Contract

Per-gauge additions (all optional — absent on first pipeline run before any snapshot exists):

```json
"inflation": {
  "value": 30.2,
  "previous_value": 32.1,
  "delta": -1.9,
  "direction": "FALLING",
  "history": [100.0, 100.0, 87.2, 39.0, 10.3, 0.0, 26.4, 30.2]
}
```

Overall section addition:

```json
"overall": {
  "hawk_score": 52.0,
  "previous_hawk_score": 48.3,
  "hawk_score_delta": 3.7
}
```

The existing `history` arrays (up to 12 values) in each gauge entry are untouched — they power sparklines without any pipeline modification.

---

## Feature 2: Delta Badges on Indicator Cards

### Existing Card DOM Structure

`InterpretationsModule.renderMetricCard()` in `interpretations.js` builds cards into `#metric-gauges-grid`. Each card's internal structure (as built by `renderMetricCard`):

```
div.card (bg-finance-gray, rounded-lg, p-4, border, etc.)
  div.header-row (flex items-center justify-between mb-2)
    h4.label (font-semibold, indicator name)
    span.weight-badge (text-xs, "X% weight")
  div#gauge-{metricId}          ← Plotly bullet gauge target
  p.interpretation-text
  p.staleness-text
  p.why-it-matters (optional)
```

### Delta Badge Integration Point

The delta badge slots into the header row between the label and weight badge:

```
div.header-row
  h4.label
  span.delta-badge   ← NEW: "+2.1" / "-1.9" / "—"
  span.weight-badge
```

The Plotly gauge `div#gauge-{metricId}` must retain its current DOM position and element reference for the existing double-rAF resize pattern to continue working.

**Implementation constraints:**

- Create with `createElement`/`textContent` (ESLint enforces no-innerHTML)
- Color via `element.style.color` with hardcoded hex — never concatenated Tailwind class strings
  - RISING: `#10b981` (green)
  - FALLING: `#ef4444` (red)
  - STEADY: `#9ca3af` (gray-400)
- Arrow characters: `\u25b2` (up triangle), `\u25bc` (down triangle), `\u2014` (em-dash for STEADY)
- Badge text format: `+2.1` / `-1.9` / `—` (no "pts" suffix — keeps badge compact on mobile)
- `flex-shrink-0` on the badge prevents wrapping that would break the header row layout

**Direction threshold:** 2.0 gauge points. Below 2.0 absolute delta = STEADY. This prevents badge noise from floating-point churn between pipeline runs. Defined as a constant in `engine.py` and mirrored in badge rendering logic.

**Graceful degradation:** When `metricData.delta == null` (no prior snapshot), the badge is not created — the header row shows only label and weight badge as before.

---

## Feature 3: Sparklines on Indicator Cards

### Existing `history` Array (No Pipeline Changes Needed)

Each gauge entry in status.json already has a `history` array of up to 12 gauge values (0-100 scale), built in `build_gauge_entry()` from the last 12 valid Z-score rows. Sparklines can use this directly — no pipeline modification required.

### Sparkline Implementation: Canvas 2D API, No CDN

Use the native Canvas 2D API. No library needed. Reasons:

- History arrays are small (max 12 values) — no need for a full charting library
- The visual is a simple static line — no tooltip, zoom, or animation needed
- Adding a CDN library (Chart.js, uPlot) introduces a new external dependency and violates the minimal-CDN philosophy
- Canvas API is universally supported in all modern browsers

**New module:** `public/js/sparklines.js`

```javascript
var SparklinesModule = (function () {
  'use strict';

  /**
   * Render a sparkline into a canvas element.
   * @param {string} canvasId - ID of the canvas element
   * @param {number[]} values - Gauge values (0-100)
   * @param {string} color - Hex color for the line
   */
  function render(canvasId, values, color) {
    var canvas = document.getElementById(canvasId);
    if (!canvas || !canvas.getContext) return;
    if (!values || values.length < 2) return;

    var ctx = canvas.getContext('2d');
    var w = canvas.width;
    var h = canvas.height;
    ctx.clearRect(0, 0, w, h);

    var min = Math.min.apply(null, values);
    var max = Math.max.apply(null, values);
    var range = max - min || 1;  // guard against flat lines

    ctx.beginPath();
    ctx.strokeStyle = color;
    ctx.lineWidth = 1.5;
    ctx.lineJoin = 'round';

    values.forEach(function (v, i) {
      var x = (i / (values.length - 1)) * w;
      var y = h - ((v - min) / range) * (h - 4) - 2;  // 2px padding top/bottom
      if (i === 0) { ctx.moveTo(x, y); } else { ctx.lineTo(x, y); }
    });
    ctx.stroke();
  }

  return { render: render };
})();
```

**Card DOM addition in `renderMetricCard()`:**

```
div.card
  div.header-row
    h4.label
    span.delta-badge
    span.weight-badge
  canvas#sparkline-{metricId}   ← NEW: width="80" height="28"
  div#gauge-{metricId}          ← Plotly bullet gauge (unchanged position)
  p.interpretation-text
  ...
```

The canvas element is placed above the Plotly gauge div so it renders immediately without interfering with the double-rAF resize chain. Canvas size is set with inline `width` and `height` HTML attributes (not CSS `width/height`) to ensure correct pixel dimensions independent of device pixel ratio.

**Wiring in `gauge-init.js`:** After `GaugesModule.createBulletGauge()` inside the `requestAnimationFrame` call:

```javascript
requestAnimationFrame(function () {
  GaugesModule.createBulletGauge('gauge-' + metricId, metricData);
  // NEW: sparkline immediately after bullet gauge creation
  SparklinesModule.render(
    'sparkline-' + metricId,
    metricData.history,
    GaugesModule.getZoneColor(metricData.value)
  );
});
```

The sparkline color matches the current zone color, giving a visual cue about where the indicator sits in context of its 12-period trend.

**prefers-reduced-motion:** Sparklines are static (no animation), so no guard is needed.

---

## Feature 4: Historical Hawk Score Chart

### Data Source: Snapshot Files

The existing `history` arrays cover per-indicator gauge values but not the overall hawk score trend over time. The snapshot files written by `archive.py` contain `hawk_score` per date.

**Data flow for historical chart:**

```
Page load (parallel with status.json fetch)
    │
    ├─ fetch("data/snapshots/index.json")
    │     → ["2026-02-24", "2026-02-17", "2026-02-10", ...]
    │
    ├─ fetch last 26 entries from index (6 months)
    │     → Promise.all([fetch("data/snapshots/2026-02-24.json"), ...])
    │
    └─ extract { date, hawk_score } per snapshot
         → Plotly line chart in chart.js
```

**Why last 26 only:** After 1 year, weekly snapshots accumulate to 52 files. Fetching all 52 on every page load would be 52 separate HTTP requests. Fetch only the last 26 (6 months). Add a "load more" button later if demand warrants.

**Implementation:** Add `renderHawkScoreHistory(containerId, snapshots)` to `chart.js` alongside the existing `renderCashRateChart()`. Both are Plotly line charts. No new module needed — `ChartModule` is the natural home.

**Fallback:** If `index.json` is absent (first pipeline run before any snapshot is written), the historical chart section is hidden. This matches existing missing-data patterns (e.g., placeholder cards for missing indicators).

---

## Feature 5: OG Meta Tags + Share Button

### OG Meta Tags: Static Defaults in HTML

Netlify is a pure static host. Social crawlers (Twitter/X, Facebook, LinkedIn, Slack) consume OG tags at HTML parse time, before JavaScript executes. JavaScript-overwritten meta tag values are not visible to most OG crawlers.

**Approach:** Write meaningful static OG defaults in `<head>` of `index.html`:

```html
<meta property="og:title" content="RBA Hawk-O-Meter — Are Australian rates going up?">
<meta property="og:description" content="Live economic dashboard tracking whether the RBA is likely to raise, cut, or hold interest rates. Updated weekly. No opinion — just data.">
<meta property="og:type" content="website">
<meta property="og:url" content="https://hawkometer.com.au/">
<meta property="og:image" content="https://hawkometer.com.au/og-image.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="RBA Hawk-O-Meter">
<meta name="twitter:description" content="Live tracker of RBA rate pressure. Updated weekly. Data, not opinion.">
<meta name="twitter:image" content="https://hawkometer.com.au/og-image.png">
```

**OG image:** A static 1200x630 PNG committed as `public/og-image.png`. This is the most reliable approach — no server-side rendering, no external service needed. Design a minimal card showing the Hawk-O-Meter name, the 0-100 dial concept, and the tagline. Update manually when branding changes.

Dynamic OG image generation (Puppeteer via Netlify Functions, Vercel OG, Cloudinary) requires either a paid Netlify tier or an external paid service. Out of scope for v5.0 given the zero-cost constraint.

**Optional JS override:** After status.json loads, JS can update `og:description` with the current hawk score — useful when the page URL is shared from within a mobile browser (some share sheets re-read meta). This does not affect crawler previews.

### Share Button: Web Share API + Clipboard Fallback

**New module:** `public/js/share.js`

```javascript
var ShareModule = (function () {
  'use strict';

  var BTN_TEXT_DEFAULT = 'Share';
  var BTN_TEXT_COPIED  = 'Link copied!';

  /**
   * Trigger native share sheet or copy URL to clipboard.
   * @param {string} btnId - ID of the share button element (for feedback)
   * @param {number} score - Current hawk score
   * @param {string} verdict - Short verdict string
   */
  function share(btnId, score, verdict) {
    var url   = window.location.href;
    var title = 'RBA Hawk\u2011O\u2011Meter';
    var text  = 'Hawk-O-Meter: '
      + Math.round(score) + '/100 \u2014 '
      + verdict + '. Track Australian rate pressure:';

    if (navigator.share) {
      navigator.share({ title: title, text: text, url: url })
        .catch(function () { /* user dismissed — no action needed */ });
    } else {
      navigator.clipboard.writeText(url)
        .then(function () { _showFeedback(btnId); })
        .catch(function () { /* clipboard permission denied */ });
    }
  }

  function _showFeedback(btnId) {
    var btn = document.getElementById(btnId);
    if (!btn) return;
    btn.textContent = BTN_TEXT_COPIED;
    setTimeout(function () {
      btn.textContent = BTN_TEXT_DEFAULT;
    }, 2000);
  }

  return { share: share };
})();
```

**Button creation in `gauge-init.js`:** Created with `createElement`/`textContent`, placed in the hero card after the freshness badge. The button calls `ShareModule.share('share-btn', data.overall.hawk_score, stanceLabel)`.

**Browser support:** `navigator.share` is available in Chrome 93+, Safari 15+, iOS Safari 14+ (confirmed HIGH confidence — MDN). Desktop Firefox and older Edge fall back to clipboard copy. Both paths are graceful.

**IIFE module loading order in `index.html`:** `share.js` is loaded before `gauge-init.js` (same pattern as all other modules):

```html
<script src="js/share.js"></script>          <!-- NEW before gauge-init -->
<script src="js/sparklines.js"></script>     <!-- NEW before gauge-init -->
<script src="js/gauge-init.js"></script>
```

---

## Feature 6: Newsletter Email Capture

### Architecture Constraint: No Server

The existing stack has no server-side component. Email capture without a backend requires an external service or Netlify Forms.

**Recommended approach: Netlify Forms.** Zero cost, zero JS required, zero external service dependency.

```html
<form name="newsletter" netloc="newsletter"
      method="POST" data-netlify="true"
      netlify-honeypot="bot-field"
      action="/thanks.html">
  <input type="hidden" name="form-name" value="newsletter">
  <p hidden><input name="bot-field"></p>
  <input type="email" name="email"
         placeholder="your@email.com" required>
  <button type="submit">Get weekly updates</button>
</form>
```

Netlify detects `data-netlify="true"` at deploy time and handles the form backend automatically. Submissions appear in the Netlify Dashboard under Forms. No JS needed — native HTML POST.

**Limitation:** Netlify Forms free tier caps at 100 submissions/month. Above that, the form silently stops accepting. For higher volume: add Beehiiv or Mailchimp API integration via a JS `fetch()` POST to their public API endpoint (no server proxy needed for those services).

**`/thanks.html`:** Create a simple static thank-you page (`public/thanks.html`) so users get confirmation on submission rather than the Netlify generic page.

**Form placement:** Below the hero section, above the indicator grid — highest-intent position for users who have just understood the rate outlook and want to stay informed.

---

## Data Flow: `previous_value` from Archive to Frontend

```
Weekly GitHub Actions pipeline run
    │
    1. ingest/*.py runs → data/*.csv updated
    │
    2. pipeline/normalize/engine.py:
    │     a. archive.read_previous_snapshot(min_age_days=5)
    │           → reads public/data/snapshots/2026-02-17.json (most recent qualifying)
    │           → returns { hawk_score: 48.3, gauges: { inflation: { value: 32.1 }, ... } }
    │
    │     b. For each indicator:
    │           process_indicator() → build_gauge_entry() receives prev_gauges[name]
    │           → adds previous_value, delta, direction to entry
    │
    │     c. generate_status() writes public/data/status.json
    │           (now includes optional previous_value/delta/direction per gauge)
    │
    │     d. archive.snapshot_current(status)
    │           → writes public/data/snapshots/2026-02-24.json
    │           → updates public/data/snapshots/index.json
    │
    3. git-auto-commit-action commits:
    │     data/*.csv
    │     public/data/status.json
    │     public/data/snapshots/2026-02-24.json   ← NEW
    │     public/data/snapshots/index.json        ← NEW
    │
    4. Netlify deploys static files
    │
    5. Browser (user visits page):
         DataModule.fetch("data/status.json")
           → delta/direction fields available in per-gauge data
           → interpretations.js renders delta badge per card
           → sparklines.js renders history[] per card
         DataModule.fetch("data/snapshots/index.json")    ← NEW fetch
           → last 26 dates loaded
           → chart.js renders historical hawk score chart
```

---

## Component Inventory: New vs Modified

### New Components

| Component | File | Type | Responsibility |
|-----------|------|------|----------------|
| `archive.py` | `pipeline/normalize/archive.py` | New Python module | Read/write minimal snapshots; provide `previous_value` to engine |
| `SparklinesModule` | `public/js/sparklines.js` | New JS IIFE module | Canvas 2D sparkline from `history[]` array |
| `ShareModule` | `public/js/share.js` | New JS IIFE module | Web Share API + clipboard fallback |
| OG image | `public/og-image.png` | New static asset | Social preview card (1200x630 PNG) |
| Thanks page | `public/thanks.html` | New static page | Newsletter form confirmation |

### Modified Components

| Component | File | What Changes |
|-----------|------|--------------|
| `engine.py` | `pipeline/normalize/engine.py` | Import archive.py; call `read_previous_snapshot()` before loop; add delta/direction to `build_gauge_entry()`; call `snapshot_current()` after writing status.json |
| `status.json` | `public/data/status.json` | Optional new fields: `previous_value`, `delta`, `direction` per gauge; `previous_hawk_score`, `hawk_score_delta` in overall |
| `interpretations.js` | `public/js/interpretations.js` | `renderMetricCard()` adds delta badge element + canvas element for sparkline |
| `gauge-init.js` | `public/js/gauge-init.js` | Wire `SparklinesModule.render()` after bullet gauge; create share button; fetch `index.json` for historical chart |
| `chart.js` | `public/js/chart.js` | Add `renderHawkScoreHistory(containerId, snapshots)` function |
| `index.html` | `public/index.html` | Add static OG/Twitter meta tags; add `<script>` tags for `sparklines.js` and `share.js`; add newsletter form; add share button anchor in hero; add historical chart container |
| `weekly-pipeline.yml` | `.github/workflows/weekly-pipeline.yml` | Add `public/data/snapshots/` to `file_pattern` in `git-auto-commit-action` step |

---

## Architectural Patterns

### Pattern 1: Optional Fields in status.json

New fields (`previous_value`, `delta`, `direction`) are added as optional to each gauge entry. The engine writes them only when a prior snapshot exists. Frontend tests for existence before rendering:

```javascript
if (metricData.delta != null) {
  // render delta badge
}
```

This makes the first pipeline run safe — no snapshot exists yet, no badge renders. Badges appear from the second run onward.

### Pattern 2: Minimal Snapshot Schema

Snapshots store only `hawk_score` and per-indicator `{ value, raw_value }` — not the full status.json (~5KB). Full status.json is the source of truth for current rendering. Minimal snapshots (~400 bytes each) are the source of truth for historical comparison only.

### Pattern 3: IIFE Module for New JS Features

Both `SparklinesModule` and `ShareModule` follow the existing `var ModuleName = (function() { 'use strict'; ... return { ... }; })();` pattern. Global variable, IIFE wrapper, explicit return object. Consistent with `GaugesModule`, `InterpretationsModule`, `DataModule`.

### Pattern 4: Canvas for Micro-Charts

Use native Canvas 2D API for sparklines rather than importing a charting library. Acceptable for 12-point static sparklines on indicator cards. Would need reconsideration if interactivity (hover tooltips) were required.

---

## Anti-Patterns

### Anti-Pattern 1: Appending to a Single `hawk_score_history.json`

**What people do:** Write a single JSON array that grows by one entry per week (`history.json`).

**Why it's wrong:** Git merge conflicts if the GHA workflow runs concurrently or is re-triggered manually. File grows without bound. Harder to query by date than reading a single `snapshots/YYYY-MM-DD.json`. A corrupt append breaks the entire history.

**Do this instead:** One file per snapshot date in `public/data/snapshots/`, with `index.json` listing available dates. Each file is immutable once written.

### Anti-Pattern 2: innerHTML for Delta Badge or Share Button

**What people do:** `element.innerHTML = '<span class="text-green-400">' + delta + '</span>'` for brevity.

**Why it's wrong:** ESLint v10 flat config in this codebase enforces `no-restricted-syntax` against innerHTML. Causes lint failure in the pre-push hook. Also an XSS risk: `metricData.delta` is pipeline-computed (safe), but consistent safe-DOM discipline avoids future mistakes.

**Do this instead:** `createElement`/`textContent`/`style.color`/`appendChild`. Arrow Unicode literals: `'\u25b2'` (up), `'\u25bc'` (down), `'\u2014'` (steady).

### Anti-Pattern 3: Fetching All Snapshot Files on Page Load

**What people do:** Fetch every snapshot file to build the historical hawk score chart.

**Why it's wrong:** After 1 year of weekly runs, that is 52 HTTP requests on page load. Each is a separate TCP round-trip on Netlify CDN.

**Do this instead:** Fetch `index.json`, then only the last 26 entries (6 months) via `Promise.all()`. Add "Load more" button later if users request it.

### Anti-Pattern 4: Dynamic OG Image Generation

**What people do:** Use Netlify Functions + Puppeteer or a third-party API to render a dashboard screenshot as the OG image per request.

**Why it's wrong:** Netlify Functions require a paid tier for meaningful usage (free tier limits are very low). External OG image services (Vercel OG, Cloudinary) introduce a paid dependency. Complexity is high for marginal benefit.

**Do this instead:** A static 1200x630 PNG committed as `public/og-image.png`. Update it when the visual design changes significantly (quarterly at most).

### Anti-Pattern 5: Concatenated Tailwind Class Strings for Delta Badge Color

**What people do:** `element.className = 'text-' + (delta > 0 ? 'green' : 'red') + '-400'`.

**Why it's wrong:** Tailwind CDN silently drops classes whose names are assembled at runtime. The class is not present in the scanned/purged output. This is a documented pitfall in this codebase (KEY DECISION in PROJECT.md).

**Do this instead:** `element.style.color = delta > 0 ? '#10b981' : '#ef4444'` — hardcoded hex, applied via `element.style`. Same pattern used throughout `gauge-init.js` for zone border colors.

---

## Suggested Build Order (Dependencies First)

```
Phase 1 — Pipeline temporal layer (no frontend changes)
    NEW: archive.py (snapshot_current, read_previous_snapshot)
    MOD: engine.py (inject previous_value/delta/direction into build_gauge_entry)
    MOD: weekly-pipeline.yml (add snapshots/ to file_pattern)
    Tests: archive.py unit tests; updated engine.py tests for new fields
    Output: status.json gains optional delta fields; first snapshot written
    Depends on: nothing (pure Python addition)

Phase 2 — Delta badges (depends on Phase 1's status.json contract)
    MOD: interpretations.js (renderMetricCard adds delta badge)
    MOD: gauge-init.js (passes metricData.delta to renderMetricCard)
    Test: Playwright — delta badge visible when delta != null; absent otherwise
    Depends on: Phase 1 (status.json must have delta field)

Phase 3 — Sparklines (no pipeline dependency — history[] already exists)
    NEW: sparklines.js (SparklinesModule)
    MOD: index.html (add <script src="js/sparklines.js"> before gauge-init.js)
    MOD: interpretations.js (renderMetricCard adds canvas element above gauge div)
    MOD: gauge-init.js (call SparklinesModule.render after createBulletGauge)
    Test: Playwright — canvas element present; non-zero pixels drawn
    Depends on: Phase 2 (card DOM structure finalized)

Phase 4 — Historical hawk score chart (depends on Phase 1 snapshots)
    MOD: chart.js (add renderHawkScoreHistory function)
    MOD: gauge-init.js (fetch index.json + last 26 snapshots)
    MOD: index.html (add historical chart container)
    Test: Playwright — chart container visible after data loads; hidden if index.json absent
    Depends on: Phase 1 (snapshots must exist); can run in parallel with Phase 2/3

Phase 5 — OG meta + share button (no pipeline dependency)
    NEW: og-image.png (1200x630 static PNG, designed externally)
    NEW: share.js (ShareModule)
    MOD: index.html (static OG/Twitter meta tags; <script src="js/share.js">)
    MOD: gauge-init.js (create share button in hero card)
    Test: Check meta tag presence in HTML source; manual share test on mobile
    Depends on: nothing pipeline-related; can run in parallel with any phase

Phase 6 — Newsletter form (no pipeline or JS dependency)
    NEW: public/thanks.html (form confirmation page)
    MOD: index.html (Netlify Form markup below hero)
    Test: Manual form submission on Netlify preview deploy
    Depends on: nothing; can run at any point
```

---

## Integration Points

### Pipeline to Frontend

| Pipeline Output | Frontend Consumer | Notes |
|-----------------|-------------------|-------|
| `public/data/status.json` | `DataModule.fetch()` in `data.js` | Unchanged fetch path; new optional fields consumed by `gauge-init.js` and `interpretations.js` |
| `public/data/snapshots/index.json` | `gauge-init.js` (new parallel fetch) | Fetched only when historical chart container is in DOM |
| `public/data/snapshots/YYYY-MM-DD.json` | `gauge-init.js` / `chart.js` | Fetched for last 26 dates from index via `Promise.all()` |

### GitHub Actions to Netlify

| File Pattern | Trigger | Change |
|--------------|---------|--------|
| `data/*.csv` | Existing weekly + daily | No change |
| `public/data/status.json` | Existing weekly + daily | No change |
| `public/data/snapshots/*.json` | Weekly only | Add to `file_pattern` in `weekly-pipeline.yml` |
| `public/data/snapshots/index.json` | Weekly only | Same |

### External Services

| Service | Integration Pattern | Cost | Notes |
|---------|---------------------|------|-------|
| Netlify Forms | HTML `data-netlify` attribute | Free (100/month) | No JS; built-in spam protection via honeypot |
| Web Share API | `navigator.share()` browser-native | Free | No external service |
| `navigator.clipboard` | Clipboard API (share fallback) | Free | Requires HTTPS (Netlify provides) |

---

## Scaling Considerations

| Scale | Architecture Adjustment |
|-------|-------------------------|
| 0-10k weekly visitors | No changes needed; Netlify CDN handles static files |
| 10k-100k weekly | Combine last-N snapshots into a single `public/data/hawk_score_chart.json` to reduce HTTP round-trips; `archive.py` rebuilds this file on each run |
| 100k+ weekly | Consider Netlify Edge Functions for dynamic OG image; pre-rendered static pages per week |
| Newsletter > 100 subs/month | Migrate from Netlify Forms to Beehiiv/Mailchimp API; add lightweight Netlify Function as proxy to protect API key |

---

## Sources

- Direct inspection: `pipeline/normalize/engine.py` — `build_gauge_entry()`, `generate_status()`, `history` array construction
- Direct inspection: `public/data/status.json` — live schema, all existing fields including `history[]` arrays
- Direct inspection: `public/js/gauge-init.js` — orchestration pattern, double-rAF pattern, `DataModule.fetch()` cache
- Direct inspection: `public/js/interpretations.js` — `renderMetricCard()` DOM structure, no-innerHTML discipline
- Direct inspection: `public/js/gauges.js` — `ZONE_COLORS`, `getZoneColor()` API
- Direct inspection: `.github/workflows/weekly-pipeline.yml` — `git-auto-commit-action` `file_pattern`
- Direct inspection: `pipeline/config.py` — `STATUS_OUTPUT`, `DATA_DIR`, all path constants
- PROJECT.md — zero-cost constraint, no-build-system constraint, ASIC compliance requirements, Tailwind CDN class-drop pitfall
- Netlify Forms docs: https://docs.netlify.com/forms/setup/ (HIGH confidence — long-standing Netlify feature)
- Web Share API MDN: https://developer.mozilla.org/en-US/docs/Web/API/Web_Share_API (HIGH confidence — widely supported)
- Open Graph protocol: https://ogp.me/ (HIGH confidence — static HTML meta tags)
- Canvas 2D API MDN: https://developer.mozilla.org/en-US/docs/Web/API/CanvasRenderingContext2D (HIGH confidence — browser-native)

---

*Architecture research for: v5.0 Direction & Momentum — snapshot archiving, delta badges, sparklines, OG sharing, and newsletter integration into RBA Hawk-O-Meter*
*Researched: 2026-02-26*
