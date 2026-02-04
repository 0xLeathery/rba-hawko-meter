# Domain Pitfalls

**Domain:** Economic Data Automation & Visualization
**Researched:** 2025-05-20

## Critical Pitfalls

Mistakes that cause system failure or fundamentally misleading data.

### Pitfall 1: The "COVID Outlier" Effect (Z-Score Distortion)
**What goes wrong:** A massive outlier (e.g., Q2 2020 GDP drop) skews the Mean and Standard Deviation for the entire history.
**Why it happens:** Standard Z-score ($z = (x - \mu) / \sigma$) assumes a normal distribution. Extreme outliers inflate $\sigma$, causing all other normal fluctuations to appear tiny (near 0).
**Consequences:** The dashboard becomes "flat" and unresponsive to normal economic shifts because the scale is stretched by the outlier.
**Prevention:**
*   **Robust Scaling:** Use Median and IQR instead of Mean and Std Dev.
*   **Windowing:** Calculate Z-score based on a rolling window (e.g., last 10 years) rather than "since 1990", or explicitly exclude pandemic periods from baseline calculations.
*   **Winsorizing:** Cap extreme values at the 95th/5th percentiles.

### Pitfall 2: Scraper Fragility (CoreLogic & NAB)
**What goes wrong:** The ingestion pipeline fails silently or crashes because a DOM element changed ID.
**Why it happens:** Commercial sites (CoreLogic) and PDF-heavy sites (NAB Surveys) are not designed for machine consumption. They often use dynamic JS (React/Angular) or anti-bot measures (Cloudflare).
**Consequences:** "Hawk Score" relies on stale data or shows `NaN`.
**Prevention:**
*   **Primary Source Preference:** Use `readabs` (R package or Python equivalent) and RBA direct CSVs for 80% of data.
*   **Defensive Coding:** Wrap scrapers in `try/except` with fallbacks to "Last Known Good" data.
*   **Browser Automation:** Use Playwright/Selenium for CoreLogic if `requests` fails due to JS rendering.
*   **Mocking:** Ensure dev environments don't hammer production sites (get banned).

### Pitfall 3: Money Illusion (Nominal Value Bias)
**What goes wrong:** Showing nominal values (e.g., "House Prices" or "Credit Aggregates") in Z-scores.
**Why it happens:** In an inflationary economy, nominal values have a unit root (they drift upwards forever). A Z-score of a non-stationary series is mathematically invalid and misleading.
**Consequences:** The gauge will eventually get stuck on "High" (Red) simply because time has passed, not because risks are higher relative to income/CPI.
**Prevention:** **Strictly** use ratios or rates of change.
*   *Bad:* Median House Price ($).
*   *Good:* Debt-to-Income Ratio, YoY % Change in House Prices.

## Moderate Pitfalls

Mistakes that cause user confusion or minor accuracy issues.

### Pitfall 4: Directionality & Color Semantics (UX)
**What goes wrong:** Users misinterpret "Red" or "Green".
**Why it happens:**
*   In finance: Green = Profit, Red = Loss.
*   In risk: Green = Safe, Red = Danger.
*   In economics: High GDP (Good?) vs High Unemployment (Bad?).
**Prevention:**
*   **Unified Axis:** Normalize everything to "Inflationary Pressure" (Hawk Score).
*   **Explicit Labels:** Use "High Pressure / Low Pressure" instead of just colors.
*   **Consistency:** "Red" must always mean "Higher Probability of Rate Hike", even if high GDP is technically "good" for the country.

### Pitfall 5: Structural Breaks
**What goes wrong:** Comparing current data to pre-2008 or pre-COVID eras.
**Why it happens:** The economy undergoes structural shifts (e.g., NAIRU changes, neutral interest rate changes). A 4% unemployment rate in 1990 meant something different than 4% in 2024.
**Consequences:** Historical baselines imply safety/danger that doesn't exist.
**Prevention:**
*   Limit lookback windows (e.g., "Post-GFC" baseline).
*   Use regime-switching models (too complex for MVP?) -> Stick to shorter rolling windows (e.g., 5-10 year Z-scores).

## Minor Pitfalls

### Pitfall 6: Jargon Overload
**What goes wrong:** Using terms like "Trimmed Mean CPI", "Basis Points", "Seasonally Adjusted".
**Prevention:** Tooltips everywhere. Translate to plain English: "Underlying Inflation", "0.25%", "Smoothed".

### Pitfall 7: Data Lag
**What goes wrong:** Users think the dashboard is "Live".
**Reality:** GDP is quarterly and lags by months.
**Mitigation:** Clearly label "Data as of [Month]". Use "Leading Indicators" (Job Ads, Business Confidence) to balance lagging ones (GDP, CPI).

## Sources
- **Scraping:** [Common Python Scraping Pitfalls](https://stackoverflow.com/questions/tagged/web-scraping) (Dynamic content, Anti-bot).
- **Statistics:** "Z-score normalization pitfalls in time series" (Stationarity, Outliers).
- **UX:** [Nielsen Norman Group](https://www.nngroup.com/articles/financial-data/) on presenting financial data.