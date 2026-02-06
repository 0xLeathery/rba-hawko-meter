# Project: RBA Hawk-O-Meter

## What This Is
An automated, unbiased economic dashboard ("Traffic Light" system) that visualizes the probability of Australian interest rate hikes for mortgage holders. It ingests raw economic data, normalizes it (Z-scores), and presents it via simple gauges to help users decide between fixed and variable rates.

## Core Value
**"Data, not opinion."**
Empowers laypeople to understand interest rate drivers without relying on media sensationalism or biased advice from banks/brokers.

## Constraints
- **Zero Cost Hosting:** Must run on Netlify (frontend) and GitHub Actions (backend).
- **Maintenance:** "Silent Automation" preferred, though scraping maintenance is accepted.
- **Data Integrity:** Strictly NO nominal currency values in gauges to avoid inflation bias; must use ratios/per-capita metrics.

## Scope
- **Backend:** Python-based ETL pipeline (ingest → normalize → Z-score).
- **Frontend:** Static HTML/JS dashboard using Plotly.js for gauges.
- **Automation:** Weekly scheduled GitHub Action.
- **Data Sources:** ABS (official), RBA (official), CoreLogic (scraped), NAB (scraped).

## Key Decisions
| Decision | Rationale | Outcome |
|----------|-----------|---------|
| **Netlify Hosting** | User preference for existing workflow/infrastructure. | Netlify auto-deploys from Git. |
| **Serverless/Static** | Minimizes cost and complexity. No database server required. | Netlify + JSON flat files. |
| **Z-Score Algorithm** | Normalizes diverse metrics ($, %, index) into a single 0-100 scale. | "Traffic Light" visualization logic. |
| **Scraping** | Official APIs don't cover all "leading indicators" like capacity utilization. | Accepted maintenance burden for better data. |
| **No Framework** | React/Vue is overkill for a single-page dashboard. | Vanilla JS + Tailwind + Plotly. |

## Success Criteria
1.  **Fully Automated:** Runs weekly without manual intervention (unless scrapers break).
2.  **Understandable:** A layperson can look at the "Hawk Score" and understand the rate pressure in < 5 seconds.
3.  **Accurate:** Data pipeline correctly normalizes nominal values (e.g., housing prices) against inflation/wages.
