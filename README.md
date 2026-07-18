# RBA Hawk-O-Meter

An automated economic dashboard that tracks the hawkishness of Australian monetary policy in real time. No opinions, no predictions — just the data, mapped to a 0–100 gauge.

**Live site:** [rbahawkometer.com.au](https://rbahawkometer.com.au)

---

## What It Does

The Hawk-O-Meter ingests public economic data from the ABS, RBA, and ASX, normalises each indicator as a Z-score against its 10-year history, then maps everything to a single 0–100 score across three zones:

| Zone | Score | Meaning |
|------|-------|---------|
| **Cool** | 0–40 | Data supports rate cuts (dovish) |
| **Neutral** | 40–60 | Data supports holding rates |
| **Warm** | 60–100 | Data supports rate hikes (hawkish) |

Seven economic indicators feed the score — each weighted by the RBA's stated policy framework:

| Indicator | Source | Weight |
|-----------|--------|--------|
| Consumer Price Index | ABS (quarterly) | 25% |
| Cash Rate | RBA | 20% |
| Wage Price Index | ABS | 15% |
| Unemployment Rate | ABS | 15% |
| Housing Prices | ABS RPPI + Cotality YoY overlay | 10% |
| Business Capacity Utilisation | NAB | 10% |
| Building Approvals | ABS | 5% |

ASX rate futures provide a live read on market expectations for the next four RBA meetings. Calendar and rate history for the frontend come from `meetings.json` and `rates.json`, regenerated every pipeline run.

---

## Architecture

```
GitHub Actions (cron + CI)
    │
    ▼
pipeline/main.py          ← 3-tier ingest + normalise + frontend JSON
    │
    ├── ingest/            ← ABS, RBA, Cotality, NAB, ASX adapters
    ├── normalize/         ← ratios → z-scores → gauge + frontend_data
    └── public/data/       ← status.json, meetings.json, rates.json, snapshots/
            │
            ▼
    public/index.html      ← static dashboard (vanilla JS + Plotly)
            │
            ▼
    Netlify               ← static hosting, auto-deploy from main
```

The pipeline runs on a schedule; the frontend is entirely static. There is no server-side rendering and no Node.js backend.

### ABS Data API

All ABS series use the **Data API REST path**:

```text
https://data.api.abs.gov.au/rest/data/{dataflow}/{key}
```

Configured in `pipeline/config.py` as `ABS_API_BASE`. Queries use **targeted SDMX keys** (not `all`) so responses stay small and reliable. CPI is **quarterly only** (`…Q` key); monthly CPI is intentionally not mixed into the 10-year history.

### Pipeline failure tiers

| Tier | Sources | Failure behaviour |
|------|---------|-------------------|
| **Critical** | RBA, ABS CPI, ABS Employment | Exit code 1 after a best-effort refresh of `meetings.json` and last-known-good `status.json` from existing CSVs |
| **Important** | ABS Spending, ABS Wages | Non-fatal warning; pipeline continues |
| **Optional** | Housing (ABS RPPI / Cotality), NAB, ASX Futures | Graceful degradation |

Housing uses ABS RPPI as the durable index series; Cotality YoY points are a sparse overlay applied only when the gap to the previous point is **> 365 days** (see `pipeline/normalize/ratios.py`).

---

## Tech Stack

**Backend**
- Python **3.11+** (required; CI and local verify assume 3.11)
- pandas, numpy, requests, beautifulsoup4, pdfplumber, lxml

**Frontend**
- Vanilla JS (IIFE modules, no build step)
- Tailwind CSS v3 (CDN)
- Plotly.js 2.35.2
- Decimal.js 10, CountUp.js 2.9.0

**Infrastructure**
- Netlify (static hosting)
- GitHub Actions (`ci`, weekly pipeline, daily ASX, live canary)
- Lefthook (pre-push quality gate)

---

## Development

### Prerequisites

- **Python 3.11+** (3.9 is not supported)
- Node.js 18+ (for lint / Playwright tooling only)

### Setup

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
npm install
```

### Run the frontend locally

```bash
python3 -m http.server 8080 --directory public
# open http://localhost:8080
```

### Run the data pipeline

```bash
python -m pipeline.main
```

This:

1. Ingests source CSVs into `data/`
2. Normalises indicators and writes `public/data/status.json` (+ snapshot archive)
3. Regenerates frontend calendar/history via `pipeline.normalize.frontend_data`:
   - `public/data/meetings.json`
   - `public/data/rates.json`

Standalone frontend generators (same modules):

```bash
python scripts/generate_frontend_data.py
```

---

## Testing

```bash
# Lint + unit tests + coverage (≥85%) — same suite as GitHub CI
npm run verify:fast

# Playwright E2E tests (requires local server on :8080)
npm run verify:playwright

# Live network tests (ABS / RBA / ASX / scrapers)
npm run verify:live

# Full suite
npm run verify
```

Tests are split into:

- **Python unit tests** (`tests/python/`) — pipeline modules at ≥85% coverage
- **Playwright E2E** (`tests/`) — dashboard, calculator, and UX
- **Live** (`@pytest.mark.live`) — real endpoints; skipped by default and by `verify:fast`

### Pre-push hook

Lefthook runs three checks in parallel on every `git push`:

1. `ruff check pipeline/ tests/` — Python linting
2. `eslint public/js/` — JS linting
3. `pytest -m "not live"` + coverage check ≥85%

---

## Data Pipeline Schedules

| Workflow | Schedule | Updates |
|----------|----------|---------|
| `ci.yml` | Push to `main` + all PRs | `npm run verify:fast` (no data commits) |
| `weekly-pipeline.yml` | Monday 2:07 AM UTC | Full ingest + `status.json` + meetings/rates + snapshots |
| `daily-asx-futures.yml` | Weekdays 6:23 AM UTC | ASX futures + status/meetings refresh |
| `live-canary.yml` | Mon + Thu 04:17 UTC | `pytest -m live` against real sources |

Scheduled jobs auto-commit data via `git-auto-commit-action` with `[skip ci]` in the message to avoid CI loops. Weekly and canary failures open/update a GitHub issue labelled `pipeline-failure` (and auto-close it on the next green run). Daily ASX intentionally does not open issues — ASX is optional/lower-severity.

### Manual dispatch (ops)

Re-fire the weekly pipeline after a source fix or during recovery:

```bash
gh workflow run weekly-pipeline.yml
gh run watch   # optional: follow the latest run
```

Live canary (endpoint health without a full ingest):

```bash
gh workflow run live-canary.yml
```

List recent results:

```bash
gh run list --workflow=weekly-pipeline.yml --limit 5
gh run list --workflow=ci.yml --limit 5
gh run list --workflow=live-canary.yml --limit 5
```

### Required status check (branch protection)

To block merges when CI fails, enable branch protection on `main` and require the **Lint + unit tests + coverage** job from `ci.yml` (workflow name: **CI**). In GitHub: **Settings → Branches → Branch protection rules → Require status checks to pass before merging**.

---

## Project Structure

```
rba-hawko-meter/
├── pipeline/
│   ├── main.py              # Entry point (tiered ingest + fail-still-refresh)
│   ├── config.py            # ABS REST base, series keys, weights, paths
│   ├── ingest/              # Data source adapters
│   └── normalize/           # ratios, z-scores, archive, engine, frontend_data
├── public/
│   ├── index.html           # Single-file dashboard
│   ├── js/                  # IIFE modules (gauge-init, gauges, data, chart, …)
│   └── data/
│       ├── status.json      # Generated — do not edit
│       ├── rates.json       # Generated RBA rate history
│       ├── meetings.json    # Generated upcoming RBA meeting dates
│       └── snapshots/       # Rolling 52-entry archive
├── data/                    # Raw CSVs (committed, append-only)
│   ├── abs_rppi.csv         # Housing index (ABS RPPI)
│   └── corelogic_housing.csv # Cotality YoY overlay points
├── scripts/
│   ├── generate_frontend_data.py  # meetings.json + rates.json
│   └── check_coverage.py
├── tests/
│   ├── python/              # Pytest unit tests
│   └── *.spec.js            # Playwright E2E tests
├── .github/workflows/       # CI, weekly, daily, live canary
├── netlify.toml
├── lefthook.yml
├── pyproject.toml
└── package.json
```

---

## Recovery status (2026-07)

Pipeline recovery is complete for production data path:

1. ABS base URL fixed to `/rest/data` with targeted series keys
2. Meetings/rates generators wired into weekly and daily jobs
3. Wages + housing contracts corrected (WPI series, ABS RPPI + Cotality overlay)
4. CI on every PR/push, louder weekly failures, live source canary

**Next product work:** v5.0 Phase 25+ (indicator card deltas/sparklines, social sharing, history chart, newsletter) — see `.planning/ROADMAP.md`.

---

## License

MIT
