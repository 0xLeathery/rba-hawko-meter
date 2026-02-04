# Technology Stack

**Project:** RBA Hawk-O-Meter
**Researched:** 2025-05-20 (Simulated for 2026 Context)

## Recommended Stack

### Backend (Data Pipeline)
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **Python** | 3.11+ | Runtime | Standard for data science/ETL. |
| **readabs** | Latest | Data Fetching | **Best in Class.** Dedicated library for ABS/RBA spreadsheets with caching and metadata support. Replaces manual `pandas` scraping. |
| **pandas** | 2.x+ | Data Manipulation | Required for time-series normalization and Z-score calc. |
| **BeautifulSoup4** | 4.x | Scraping | Lightweight scraping for CoreLogic/NAB where APIs don't exist. |
| **GitHub Actions** | N/A | Orchestration | "Serverless" cron job (weekly). Free tier is sufficient. |

### Frontend (Dashboard)
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **Vanilla JS** | ES6+ | Logic | No framework needed for a single-page static dashboard. |
| **Plotly.js** | 2.x+ (CDN) | Visualization | **Recommended.** Best support for "Speedometer" / "Indicator" traces. Robust, even if heavy (use CDN). |
| **Tailwind CSS** | 3.x (CDN) | Styling | Rapid UI development. Use CDN for dev, CLI for optimized build if needed. |

### Infrastructure & Deployment
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **Netlify** | Standard | Hosting | Zero-config static hosting. Excellent global CDN. |
| **Git "As Database"** | N/A | Storage | Committing JSON back to repo provides free, versioned history of economic data. |

## Alternatives Considered

### Data Fetching
| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| ABS Data | `readabs` | `pandas-datareader` | `pandas-datareader` (WorldBank/OECD) is good but `readabs` is purpose-built for Australian ABS catalog complexities. |
| Scrapers | `bs4` | `Selenium`/`Playwright` | Overkill. CoreLogic/NAB sites are generally static enough for HTTP requests; keep it lightweight until broken. |

### Frontend
| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Gauges | `Plotly.js` | `Chart.js` | `Chart.js` requires plugins for gauges/speedometers. `Plotly` has them native (`type: 'indicator'`). |
| Gauges | `Plotly.js` | `gauge.js` / `canvas-gauges` | `gauge.js` is lighter (KB vs MB) but strictly limited to gauges. `Plotly` allows adding time-series history charts later if scope expands. |
| Framework | Vanilla | React/Vue | Overkill for a static JSON consumer. Adds build complexity (npm, bundlers) not needed for <500 lines of code. |

## Optimal Deployment Setup

**Goal:** Automate Python ETL -> Update Data -> Deploy Site.

**Recommended Pattern:** "The Self-Committing Action"
1.  **ETL:** Action runs Python script, generates `public/status.json`.
2.  **Commit:** Action commits `status.json` back to `main` branch.
3.  **Deploy:** Netlify (linked to repo) detects commit and auto-deploys.

**Optimization (for "2026 Standard"):**
To avoid triggering a "Build" on Netlify that just copies files (since the Action did the work), use **Netlify CLI** in the Action.

```yaml
# .github/workflows/weekly-update.yml
steps:
  - uses: actions/checkout@v4
  - run: python etl.py # Generates public/status.json
  
  # Commit history (Git as DB)
  - run: |
      git config user.name "HawkBot"
      git add data/
      git commit -m "Update data [skip ci]" # [skip ci] prevents Netlify auto-trigger
      git push

  # Direct Deploy (Fastest)
  - uses: netlify/actions/cli@master
    with:
      args: deploy --dir=public --prod
    env:
      NETLIFY_AUTH_TOKEN: ${{ secrets.NETLIFY_AUTH_TOKEN }}
      NETLIFY_SITE_ID: ${{ secrets.NETLIFY_SITE_ID }}
```

## Installation

```bash
# Python Requirements
pip install pandas readabs beautifulsoup4 requests numpy
```

## Sources
- **readabs:** [PyPI](https://pypi.org/project/readabs/) (Verified high confidence)
- **Netlify CLI:** [Docs](https://docs.netlify.com/cli/get-started/)
- **Plotly Indicators:** [Docs](https://plotly.com/javascript/indicator/)
