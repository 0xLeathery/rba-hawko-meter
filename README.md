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
| Consumer Price Index | ABS | 25% |
| Cash Rate | RBA | 20% |
| Wage Price Index | ABS | 15% |
| Unemployment Rate | ABS | 15% |
| Housing Prices | CoreLogic | 10% |
| Business Capacity Utilisation | NAB | 10% |
| Building Approvals | ABS | 5% |

ASX rate futures provide a live read on market expectations for the next four RBA meetings.

---

## Architecture

```
GitHub Actions (cron)
    │
    ▼
pipeline/main.py          ← 3-tier ingest + normalise
    │
    ├── ingest/            ← ABS, RBA, CoreLogic, NAB, ASX adapters
    ├── normalize/         ← ratios → z-scores → 0-100 gauge values
    └── public/data/status.json   ← pre-built for the frontend
            │
            ▼
    public/index.html      ← static dashboard (vanilla JS + Plotly)
            │
            ▼
    Netlify               ← static hosting, auto-deploy from main
```

The pipeline runs on a schedule; the frontend is entirely static. There is no server-side rendering and no Node.js backend.

### Pipeline failure tiers

| Tier | Sources | Failure behaviour |
|------|---------|-------------------|
| **Critical** | RBA, ABS CPI, ABS Employment | Fail fast — exit code 1, no output written |
| **Important** | ABS Spending, ABS Wages | Non-fatal warning |
| **Optional** | CoreLogic, NAB, ASX Futures | Graceful degradation |

---

## Tech Stack

**Backend**
- Python 3.11+
- pandas, numpy, requests, beautifulsoup4, pdfplumber, lxml

**Frontend**
- Vanilla JS (IIFE modules, no build step)
- Tailwind CSS v3 (CDN)
- Plotly.js 2.35.2
- Decimal.js 10, CountUp.js 2.9.0

**Infrastructure**
- Netlify (static hosting)
- GitHub Actions (weekly pipeline + daily ASX futures)
- Lefthook (pre-push quality gate)

---

## Development

### Prerequisites

- Python 3.11+
- Node.js 18+ (for dev tooling only)

### Setup

```bash
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

This writes updated CSVs to `data/` and regenerates `public/data/status.json`.

---

## Testing

```bash
# Unit tests + coverage check (≥85%)
npm run test:fast

# Playwright E2E tests (requires local server on :8080)
npm run verify:playwright

# Full suite
npm run verify
```

Tests are split into:
- **Python unit tests** (`tests/python/`) — 421 tests, all pipeline modules at ≥85% coverage
- **Playwright E2E** (`tests/`) — 28 tests covering the dashboard, calculator, and UX

Live network tests are marked `@pytest.mark.live` and skipped by default.

### Pre-push hook

Lefthook runs three checks in parallel on every `git push`:

1. `ruff check pipeline/ tests/` — Python linting
2. `eslint public/js/` — JS linting
3. `pytest -m "not live"` + coverage check ≥85%

---

## Data Pipeline Schedules

| Workflow | Schedule | Updates |
|----------|----------|---------|
| `weekly-pipeline.yml` | Monday 2:07 AM UTC | All indicators + `status.json` |
| `daily-asx-futures.yml` | Weekdays 6:23 AM UTC | ASX futures + `status.json` |

Both workflows auto-commit output files via `git-auto-commit-action`.

---

## Project Structure

```
rba-hawko-meter/
├── pipeline/
│   ├── main.py              # Entry point
│   ├── config.py            # Dataset IDs, weights, column mappings
│   ├── ingest/              # Data source adapters
│   └── normalize/           # Ratios, z-scores, archive, engine
├── public/
│   ├── index.html           # Single-file dashboard
│   ├── js/                  # IIFE modules (gauge-init, gauges, data, chart, …)
│   └── data/
│       ├── status.json      # Generated — do not edit
│       ├── rates.json       # RBA rate history
│       ├── meetings.json    # Upcoming RBA meeting dates
│       └── snapshots/       # Rolling 52-entry archive
├── data/                    # Raw CSVs (committed, append-only)
├── tests/
│   ├── python/              # Pytest unit tests
│   └── *.spec.js            # Playwright E2E tests
├── .github/workflows/       # GitHub Actions
├── netlify.toml             # Deploy config + security headers
├── lefthook.yml             # Pre-push hooks
├── pyproject.toml           # Pytest + ruff config
└── package.json             # npm scripts + dev deps
```

---

## License

MIT
