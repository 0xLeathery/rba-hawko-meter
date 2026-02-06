# Z-Score Methodology for Economic Indicator Normalization

**Researched:** 2026-02-06
**Domain:** Statistical normalization of heterogeneous economic indicators into a composite rate-hike probability gauge
**Confidence:** HIGH

---

## Table of Contents

1. [Is Z-Score the Right Approach?](#1-is-z-score-the-right-approach)
2. [Rolling Window Selection](#2-rolling-window-selection)
3. [Z-Score to 0-100 Gauge Mapping](#3-z-score-to-0-100-gauge-mapping)
4. [Pitfalls and Edge Cases](#4-pitfalls-and-edge-cases)
5. [Alternatives and Complements](#5-alternatives-and-complements)
6. [How Professionals Build Composite Indices](#6-how-professionals-build-composite-indices)
7. [Indicator Weighting Approaches](#7-indicator-weighting-approaches)
8. [Directional Polarity Handling](#8-directional-polarity-handling)
9. [Recommendations for Hawk-O-Meter](#9-recommendations-for-hawk-o-meter)
10. [Sources](#10-sources)

---

## 1. Is Z-Score the Right Approach?

### Short Answer

Yes, with caveats. Z-score normalization is the established standard for combining heterogeneous economic indicators into composite indices. It is used by the Chicago Fed NFCI (105 variables), the OECD Composite Leading Indicators, and numerous financial conditions indices worldwide. However, the *standard* Z-score (mean/std) is inappropriate for data with outliers -- the project's existing decision to use **robust Z-scores (median/MAD)** is well-founded.

### Why Z-Scores Work for This Use Case

| Requirement | Z-Score Capability |
|---|---|
| Combine different units (%, $, index) | Converts all to dimensionless standard deviations from center |
| Handle different magnitudes | Normalizes scale automatically |
| Identify "unusual" readings | Values beyond +/-2 are statistically noteworthy |
| Simple to explain to laypeople | "How far from normal" is intuitive |
| Computationally lightweight | No model fitting required beyond rolling statistics |
| Transparent and auditable | Formula is deterministic, no black-box components |

### Why Z-Scores Are Imperfect

| Limitation | Severity for Hawk-O-Meter | Mitigation |
|---|---|---|
| Assumes symmetric distributions | MEDIUM -- some indicators (housing prices) are right-skewed | Use robust Z-scores (MAD) which are less sensitive to skew |
| Sensitive to outliers (standard version) | HIGH -- COVID created extreme outliers | Already mitigated: project uses MAD instead of std |
| Loses information about tails | LOW -- we clip to 0-100 anyway | Flag extreme values separately in metadata |
| No inherent probability interpretation | MEDIUM -- Z=1.5 doesn't mean "75% chance of hike" | Use CDF transform or clearly label as "pressure index" not "probability" |
| Assumes stationarity within window | MEDIUM -- structural breaks can shift the "normal" | Rolling window partially addresses this; shorter windows adapt faster |

### Verdict

Z-score normalization is the correct foundation. It is the same approach used by the Chicago Fed NFCI (the most-cited financial conditions index in the world) and the OECD CLI system. The project's existing choice of robust Z-scores (median/MAD) over standard Z-scores is strongly supported by the literature.

---

## 2. Rolling Window Selection

### The 10-Year Window: Analysis

The project currently specifies a 10-year rolling window. This is a defensible middle ground, but the tradeoffs are significant.

### Window Size Tradeoffs

| Window | Bias-Variance Tradeoff | Structural Break Sensitivity | Data Requirement | Best For |
|---|---|---|---|---|
| **3-5 years** | High variance, low bias toward old regimes | Adapts quickly (good) | Modest | Rapidly changing economies, post-crisis recalibration |
| **7-10 years** | Balanced | Moderate adaptation speed | Substantial | General-purpose economic dashboards |
| **15-20 years** | Low variance, high bias if structural breaks exist | Slow to adapt (risky) | Very high | Stable, mature economies with no regime changes |
| **Full history** | Lowest variance but highest structural break risk | Does not adapt | Maximum | Only if no structural breaks exist (rare) |

### Evidence from the Literature

**Pesaran and Timmermann (2007)** showed that forecasting performance of rolling window estimators in the presence of structural breaks is highly sensitive to window size choice. They propose methods for choosing the optimal size that minimizes mean squared forecast error by balancing bias and variance.

**Giannellis (2025)** found that fixed-length rolling windows provide little advantage over conventional methods when data is stationary, but **varying-length window techniques outperform fixed-length windows when the data-generating process changes** (e.g., from stationary to non-stationary).

**Hall and Tavlas (2024)** compared 5-year and 10-year rolling windows for inflation forecasting and found that no single window size consistently dominates -- the optimal size depends on the frequency and magnitude of structural breaks in the sample.

### Australia-Specific Considerations

Australia's economic history since 2000 includes several structural breaks:
- **2008 GFC** -- sharp but brief recession, followed by mining boom
- **2013-2019** -- prolonged low-inflation, low-rate environment (different from prior decades)
- **2020-2021 COVID** -- extreme outliers in employment, spending, housing
- **2022-2023** -- rapid rate hiking cycle (fastest in RBA history)
- **2024-2026** -- transition to "new normal" with rates at 4%+ (not seen since 2012)

A 10-year window starting in 2016 would include both COVID extremes and the rapid hiking cycle. Starting in 2026, a 10-year lookback captures 2016-2026, which includes radically different monetary policy regimes.

### Recommendation

**Keep the 10-year window as the primary calculation** but implement these safeguards:

1. **Minimum 5-year fallback** -- for indicators with less than 10 years of history (already planned with `min_periods`)
2. **Confidence degradation** -- report MEDIUM confidence when window < 8 years, LOW when < 5 years
3. **Consider logging window coverage** -- e.g., "Based on 37 of 40 possible quarterly observations"
4. **Future enhancement (post-MVP)** -- adaptive window that expands/contracts based on detected structural break tests (Bai-Perron test via `ruptures` Python package)

---

## 3. Z-Score to 0-100 Gauge Mapping

Three main approaches exist for mapping Z-scores to a bounded gauge scale. The project has already decided on linear clamp, but understanding the alternatives validates this choice.

### Approach Comparison

#### Option A: Linear Clamp (Current Decision)

```
gauge = clip((z + 2) / 4 * 100, 0, 100)
```

| Property | Value |
|---|---|
| Z = -2 maps to | 0 |
| Z = 0 maps to | 50 |
| Z = +2 maps to | 100 |
| Beyond +/-2 | Clipped to 0 or 100 |
| Interpretation | Equal sensitivity across entire range |

**Pros:**
- Simplest to explain and audit
- Linear relationship is intuitive ("twice the Z-score = twice the gauge movement")
- Already decided by the project
- Used by many financial dashboards for simplicity

**Cons:**
- ~5% of normally distributed observations fall outside +/-2, so information is lost for tails
- Equal spacing doesn't reflect the increasing rarity of extreme observations
- A move from Z=1.5 to Z=2.0 (moderately unusual to unusual) gets the same gauge movement as Z=0 to Z=0.5 (average to slightly above average)

#### Option B: CDF Transform (Normal Probability)

```
gauge = scipy.stats.norm.cdf(z) * 100
```

| Property | Value |
|---|---|
| Z = -2 maps to | 2.3 |
| Z = 0 maps to | 50 |
| Z = +2 maps to | 97.7 |
| Z = +3 maps to | 99.9 |
| Interpretation | Percentile position assuming normal distribution |

**Pros:**
- Naturally bounded (0-100) without clipping
- Reflects the true rarity of extreme values (Z=3 is much rarer than Z=2)
- Has a probabilistic interpretation ("X% of historical observations were below this")
- More sensitive in the middle (where most action happens), less sensitive at extremes

**Cons:**
- Assumes normality (many economic indicators are not normally distributed)
- Compresses the extremes excessively (Z=2 and Z=3 both look ~98-100)
- Harder to explain to laypeople ("cumulative distribution function" vs "how far from normal")
- The "gauge" becomes a percentile, not a linear pressure scale

#### Option C: Sigmoid / Logistic Transform

```
gauge = 100 / (1 + exp(-k * z))  # k controls steepness
```

| Property | Value |
|---|---|
| Z = -2 maps to | ~12 (with k=1.5) |
| Z = 0 maps to | 50 |
| Z = +2 maps to | ~88 (with k=1.5) |
| Interpretation | S-curve with adjustable sensitivity |

**Pros:**
- Naturally bounded (0-100) without clipping
- Tunable steepness parameter (k) to control sensitivity
- More sensitive around neutral (Z~0) where most policy-relevant variation occurs
- Smooth behavior at extremes (no hard clipping)

**Cons:**
- Introduces an extra parameter (k) that requires justification
- Harder to explain than linear
- The steepness parameter is arbitrary and changes gauge behavior significantly
- Less interpretable: "what does gauge=73 mean?" is harder to answer

### Mapping Comparison Table

| Z-Score | Linear Clamp | CDF | Sigmoid (k=1.5) |
|---|---|---|---|
| -3.0 | 0 (clipped) | 0.1 | 1.1 |
| -2.0 | 0 | 2.3 | 4.7 |
| -1.5 | 12.5 | 6.7 | 9.6 |
| -1.0 | 25 | 15.9 | 18.2 |
| -0.5 | 37.5 | 30.9 | 32.1 |
| 0.0 | 50 | 50.0 | 50.0 |
| +0.5 | 62.5 | 69.1 | 67.9 |
| +1.0 | 75 | 84.1 | 81.8 |
| +1.5 | 87.5 | 93.3 | 90.4 |
| +2.0 | 100 | 97.7 | 95.3 |
| +3.0 | 100 (clipped) | 99.9 | 98.9 |

### Recommendation

**Stick with the linear clamp.** The project's existing decision is sound for these reasons:

1. **Transparency** is a core project value ("Data, not opinion"). Linear mapping is the most transparent.
2. **Laypeople** can understand "0 = very dovish, 50 = neutral, 100 = very hawkish" without needing to understand CDFs.
3. **The 5% information loss from clipping is acceptable** because the project already flags extreme values (>3 IQR) separately in metadata.
4. **CDF assumes normality**, which contradicts the project's robust statistics approach.
5. The Chicago Fed NFCI also uses a simple standardized score (Z-score units) rather than a CDF transform.

**One refinement worth considering:** widen the clamp range from [-2, +2] to [-2.5, +2.5] or [-3, +3]. This retains linearity and transparency while reducing the frequency of "pegged at 0 or 100" readings. With [-3, +3], only 0.3% of normally-distributed observations would be clipped (vs. 4.6% with [-2, +2]).

---

## 4. Pitfalls and Edge Cases

### 4.1 Non-Normal Distributions

**Problem:** Many economic indicators are not normally distributed. Housing prices are right-skewed. Employment changes have fat tails. CPI changes can be bimodal during regime transitions.

**Impact on Z-scores:** When data is skewed, a standard Z-score of +2 does not correspond to the 97.7th percentile as it would for normal data. It could be the 90th percentile (for right-skewed data) or the 99th (for left-skewed data).

**Mitigation (already in project):** The decision to use MAD-based robust Z-scores substantially reduces this problem. MAD is resistant to skew because the median is the measure of center and median absolute deviation is the measure of spread -- neither is inflated by skewed tails the way mean and standard deviation are.

**Additional mitigation options (post-MVP):**
- Apply log transform to inherently right-skewed indicators (housing price ratios, spending levels) before Z-scoring
- Use empirical percentile ranks as a complement (see Section 5.1)

### 4.2 Structural Breaks (COVID, GFC, Regime Changes)

**Problem:** When the economy undergoes a fundamental shift, historical statistics become misleading. A 4% unemployment rate meant something different in 1990 than in 2024. COVID created observations that were 5-10 standard deviations from the pre-COVID mean.

**Impact on Z-scores:** A rolling window that includes a structural break mixes two different data-generating processes, producing statistics that are representative of neither regime.

**The COVID Problem Specifically:**
- COVID outliers in 2020-2021 will remain in the 10-year window until 2030-2031
- They inflate MAD (though less than they inflate standard deviation)
- They shift the rolling median away from the "true" center of the current regime
- They make current "normal" readings look artificially close to the median

**Mitigation approaches:**

| Approach | Complexity | Effectiveness | Transparency |
|---|---|---|---|
| **Robust statistics (MAD)** | Low | High -- handles outliers without removal | High |
| **Explicit COVID flag** | Low | Medium -- relies on manual date range | High |
| **Winsorize at 95th/5th percentile** | Low | Medium -- caps extreme values | High |
| **Shorter rolling window** | Low | Medium -- eventually drops outliers | High |
| **Regime-switching model** | Very High | High -- detects breaks formally | Low |
| **Exclude known outlier periods** | Low | High for known events, zero for unknown | Medium -- introduces subjectivity |

**Recommendation:** The project's current approach (robust statistics + flag extreme values) is the right balance for an MVP. The combination of MAD-based Z-scores and a 10-year rolling window means COVID outliers have diminishing influence over time, and by 2030 they will have rolled out of the window entirely. No manual exclusion is needed.

### 4.3 Base Effects

**Problem:** Year-over-year percentage changes can produce misleadingly large readings when the base period was abnormal. For example, CPI YoY in Q2 2021 appeared very high partly because Q2 2020 was artificially depressed by COVID.

**Impact on Z-scores:** The base effect creates a mechanical spike in the indicator that the Z-score correctly identifies as "unusual" but that doesn't represent genuine economic pressure.

**Mitigation:** The project's rolling window approach naturally handles this because:
1. The Z-score is calculated against a 10-year distribution, not just the prior year
2. MAD-based scoring identifies the spike as an outlier without it distorting the scale
3. The extreme value flag alerts users to potentially misleading readings

**Additional mitigation:** For indicators expressed as YoY changes, consider using a 2-year compound annual growth rate (CAGR) instead of simple YoY during known base-effect periods. This smooths out the mechanical spike.

### 4.4 Data Frequency Mismatch

**Problem:** The project combines indicators with different frequencies:
- Monthly: Employment, retail trade, building approvals, NAB business confidence
- Quarterly: CPI, wages (WPI)
- Irregular: Housing prices (monthly from CoreLogic but quarterly for broader measures)
- Real-time: ASX futures

**Impact on Z-scores:** Rolling windows measured in "number of observations" have different calendar coverage for monthly vs quarterly data. A "40-observation window" covers 10 years for quarterly data but only 3.3 years for monthly data.

**Mitigation:** Standardize all indicators to quarterly frequency before Z-score calculation:
- Monthly data: take the end-of-quarter value or quarterly average
- ASX futures: take the value as of the last day of the quarter
- This aligns all indicators to the same time axis

### 4.5 Indicator Staleness

**Problem:** Different indicators are released at different times. Employment data arrives monthly, but CPI is quarterly with a ~4 week lag. Building approvals can lag by 6+ weeks.

**Impact on the gauge:** Some gauges will be based on data from 1-3 months ago while others are near real-time. The "Hawk Score" could be driven by stale readings.

**Mitigation (already planned):** The project includes staleness flags and data timestamps in `status.json`. The confidence level system (HIGH/MEDIUM/LOW) should factor in data age.

### 4.6 Zero Dispersion (Flat Data)

**Problem:** When all values in the rolling window are identical or nearly identical (e.g., RBA cash rate held constant for years), MAD = 0, causing division by zero.

**Existing mitigation:** Return Z = 0 (neutral) when MAD = 0. This is correct because if the indicator hasn't moved, it definitionally isn't generating rate-hike pressure.

---

## 5. Alternatives and Complements

### 5.1 Percentile Ranks

**How it works:** Instead of measuring "how many standard deviations from the median," measure "what percentage of historical observations were below this value."

```python
percentile_rank = (sum(historical < current_value) / len(historical)) * 100
```

| Aspect | Z-Score | Percentile Rank |
|---|---|---|
| Assumes distribution shape | Yes (implicitly, for interpretation) | No -- distribution-free |
| Handles skewed data | Poorly (standard) / Well (robust) | Well -- by definition |
| Handles outliers | Poorly (standard) / Well (robust) | Well -- bounded by design |
| Interpretation | "How unusual" (distance from center) | "How high relative to history" (rank) |
| Sensitivity to new data | Moderate | Each new observation shifts all ranks |
| Differentiates extreme values | Yes (Z=3 vs Z=5 are different) | Poorly (both map to ~100th percentile) |

**Verdict:** Percentile ranks are a strong complement to Z-scores, especially as a **validation check**. If Z-score says "Hot" but percentile rank says 60th percentile, the Z-score may be distorted. Consider reporting both in `status.json` metadata.

### 5.2 Factor Models (PCA)

**How it works:** Principal Component Analysis extracts the common variance across all indicators. The first principal component (PC1) captures the single dimension that explains the most variance.

**Pros:**
- Data-driven weighting: indicators that co-move strongly get higher effective weight
- Reduces dimensionality: many indicators become one score
- Used by the Chicago Fed NFCI and many professional financial conditions indices

**Cons:**
- Opaque: PCA weights are hard to explain to laypeople ("eigenvector loadings")
- Requires enough data for stable factor estimation (10+ years of quarterly data = 40+ observations)
- Can assign counterintuitive weights (highly correlated indicators dominate)
- Not transparent: violates the project's "Data, not opinion" principle

**Verdict:** Too complex and opaque for this project's transparency goals. However, PCA could be used as a post-hoc validation: run PCA on the indicators and compare the implied weights against the project's chosen weights.

### 5.3 Probit/Logit Models

**How it works:** Train a binary classification model where the target is "RBA hiked rates = 1 / did not hike = 0" and the features are the economic indicators. The model outputs a true probability (0-100%) of a rate hike.

**Pros:**
- Produces a genuine probability (calibrated, unlike Z-scores)
- Can be validated against historical RBA decisions
- Naturally handles indicator interactions and nonlinearities (with appropriate specification)
- Used by the Federal Reserve for recession probability estimation

**Cons:**
- Requires labeled training data (historical RBA decisions)
- Australia has had ~30 rate changes in 20 years -- small sample for model fitting
- Overfitting risk with 8 indicators and ~30 events
- Model becomes a "black box" -- less transparent than Z-scores
- Requires regular re-estimation as the economy evolves

**Verdict:** Not appropriate for the MVP due to small sample size and transparency concerns. However, it's a strong candidate for a **future "model confidence" overlay** that could complement the Z-score gauge. The project could collect a few years of parallel Z-score data and RBA decisions, then fit a simple logistic regression as a calibration check.

### 5.4 Taylor Rule Deviations

**How it works:** The Taylor Rule prescribes an "ideal" interest rate based on inflation and the output gap:

```
r* = neutral_rate + 1.5 * (inflation - target) + 0.5 * output_gap
```

The deviation between the actual cash rate and the Taylor Rule rate indicates whether policy is "too loose" (hawkish pressure building) or "too tight" (dovish pressure building).

**Pros:**
- Theoretically grounded in monetary economics
- Simple formula with clear interpretation
- Widely used by central bank researchers (Atlanta Fed publishes a Taylor Rule tracker)
- Directly relevant to rate-hike prediction

**Cons:**
- Requires estimates of the "neutral rate" and "output gap" -- both are unobservable and contested
- Assumes the RBA follows a Taylor-type rule (they don't explicitly)
- The RBA's reaction function includes factors beyond inflation and output (financial stability, housing, global conditions)
- Research shows Taylor Rule predictions have deteriorated since 2008

**Verdict:** A Taylor Rule deviation could be a valuable **single additional indicator** displayed alongside the Hawk-O-Meter (not as a replacement). It provides independent, theory-based context. Display it as "Taylor Rule suggests rates should be X.XX%" alongside the empirical gauge.

### 5.5 Comparison Matrix

| Method | Transparency | Complexity | Data Needs | Probability Output | Outlier Robust |
|---|---|---|---|---|---|
| **Robust Z-Score** | HIGH | LOW | Moderate | No (pressure scale) | YES (with MAD) |
| Percentile Rank | HIGH | LOW | Moderate | No (rank) | YES |
| PCA Factor Model | LOW | MEDIUM | High | No (factor score) | Depends on estimation |
| Probit/Logit | LOW | HIGH | Very High (labeled) | YES | Depends on specification |
| Taylor Rule | MEDIUM | LOW | Low (2 inputs) | No (deviation) | N/A |

---

## 6. How Professionals Build Composite Indices

### 6.1 OECD Composite Leading Indicators (CLI)

**Method:** Deviation-from-trend approach.

**Steps:**
1. **Component selection** -- choose series with consistent leading relationship to reference series (GDP)
2. **Seasonal adjustment** -- remove seasonal patterns
3. **Outlier detection** -- identify and treat extreme values
4. **De-trending** -- remove long-term trend to isolate cyclical component (typically HP filter or PAT method)
5. **Smoothing** -- apply Henderson moving average to reduce noise
6. **Normalization** -- express each component as deviations from its mean, divided by its mean absolute deviation
7. **Aggregation** -- combine components using equal weights

**Key insight:** The OECD uses **equal weights** for all components, but the normalization step (dividing by mean absolute deviation) creates an **implicit weighting** where less volatile series get relatively more weight. This is because dividing by MAD makes a series that moves +/-1 unit contribute the same as a series that moves +/-100 units.

**Relevance to Hawk-O-Meter:** The OECD approach validates the project's MAD-based normalization. The "implicit weighting" through normalization is mathematically similar to what happens when you compute Z-scores -- volatile indicators are automatically scaled down relative to stable ones.

### 6.2 Conference Board Leading Economic Index (LEI)

**Method:** Symmetric percent change with inverse-volatility weighting.

**Steps:**
1. **Compute symmetric percent changes** for each component
2. **Standardize** by dividing each component's change by its historical standard deviation (standardization factor)
3. **Apply component weights** that are inversely proportional to standard deviation (i.e., less volatile components get more weight)
4. **Sum** the weighted standardized changes
5. **Apply trend adjustment** to match the trend of the coincident index

**Key insight:** The Conference Board weights are **inversely related to the standard deviation** of month-to-month changes. Volatile indicators get less weight because their signal-to-noise ratio is lower. The factors were calibrated using 1984-2011 as the sample period.

**Relevance to Hawk-O-Meter:** The Conference Board approach suggests that **inverse-volatility weighting is a defensible alternative** to equal weighting. More volatile indicators (like building approvals, which swing wildly) would get less weight than stable indicators (like trimmed mean CPI).

### 6.3 Chicago Fed National Financial Conditions Index (NFCI)

**Method:** Dynamic factor model on Z-scored variables.

**Steps:**
1. **Standardize** each of 105 variables relative to sample average and standard deviation (Z-score)
2. **Extract common factor** using a dynamic factor model (similar to PCA but accounts for time dynamics)
3. **Weight** each variable by its contribution to the common factor
4. **Scale** the index to have mean=0, std=1 over the full sample (1971-present)

**Key insight:** The NFCI starts with Z-score normalization and then applies factor analysis to determine weights. This is more sophisticated than equal weighting or expert judgment, but requires 105 variables and 50+ years of data. The Hawk-O-Meter has 8 indicators and ~15 years, so factor analysis is not feasible.

**Relevance to Hawk-O-Meter:** The NFCI validates Z-score normalization as the starting point. The project's simpler approach (Z-scores with expert-assigned weights) is appropriate given the much smaller number of indicators.

### 6.4 Summary of Professional Approaches

| Index | Normalization | Weighting | Aggregation | Transparency |
|---|---|---|---|---|
| OECD CLI | MAD-based deviation | Equal (with implicit volatility weighting) | Simple average | High |
| Conference Board LEI | Standard deviation scaling | Inverse volatility | Weighted sum | Medium |
| Chicago Fed NFCI | Z-score (mean/std) | Dynamic factor model | Weighted average | Low |
| Goldman Sachs FCI | Varies | Macro model-derived | Weighted sum | Very Low |

---

## 7. Indicator Weighting Approaches

### 7.1 Equal Weighting

**How it works:** Every indicator contributes equally to the overall Hawk Score.

```python
hawk_score = mean(gauge_values)
```

**Pros:**
- Simplest, most transparent
- No arbitrary decisions about "which indicator matters more"
- Used by OECD CLI (the most widely-used composite leading indicator)
- Robust: no single indicator can dominate

**Cons:**
- Ignores that some indicators are more relevant to rate decisions than others (inflation is arguably more important than building approvals)
- Treats redundant information the same as unique information (if two indicators measure similar things, they effectively get double weight)

### 7.2 Expert Judgment Weights

**How it works:** Assign weights based on domain knowledge of what drives RBA decisions.

```python
weights = {
    "inflation": 0.25,    # CPI is the RBA's primary mandate
    "wages": 0.15,        # Key input to inflation outlook
    "employment": 0.15,   # Second part of dual mandate
    "housing": 0.15,      # Major financial stability concern
    "spending": 0.10,     # Demand pressure indicator
    "building_approvals": 0.05,  # Leading indicator but noisy
    "business_confidence": 0.05, # Soft data, less reliable
    "asx_futures": 0.10   # Market expectations
}
```

**Pros:**
- Reflects actual RBA decision-making priorities (inflation targeting mandate)
- Can incorporate domain knowledge about leading vs lagging indicators
- Allows transparent documentation of reasoning

**Cons:**
- Subjective -- different economists would assign different weights
- Hard to validate empirically with small samples
- May not adapt to regime changes (RBA shifted from inflation-only to dual mandate in 2023)

### 7.3 Inverse-Volatility Weighting

**How it works:** Weight each indicator inversely proportional to its standard deviation. Less volatile indicators get more weight because they have a higher signal-to-noise ratio.

```python
volatilities = {k: rolling_std(v) for k, v in indicators.items()}
inv_vol = {k: 1/v for k, v in volatilities.items()}
total = sum(inv_vol.values())
weights = {k: v/total for k, v in inv_vol.items()}
```

**Pros:**
- Data-driven and objective
- Used by the Conference Board LEI
- Automatically reduces the influence of noisy indicators (building approvals)
- Adapts as volatility regimes change

**Cons:**
- May underweight important but volatile indicators
- A constant indicator (no variation) gets infinite weight -- needs a floor
- Volatility is not the same as importance

### 7.4 PCA-Derived Weights

**How it works:** Use the loadings of the first principal component as weights.

**Pros:**
- Maximizes explained variance
- Data-driven, no subjective choices

**Cons:**
- Assigns highest weight to the most correlated indicators (not necessarily the most important)
- Requires sufficient data for stable estimation
- Opaque and hard to explain

### 7.5 Historical Regression Weights

**How it works:** Regress historical RBA rate decisions on the indicator Z-scores to find which indicators best predict decisions.

```
P(hike) = logit(b1*z_inflation + b2*z_employment + ... + b8*z_futures)
```

**Pros:**
- Empirically grounded in actual RBA behavior
- Produces calibrated probability estimates
- Testable with out-of-sample validation

**Cons:**
- Small sample (~30 rate changes in 20 years)
- Overfitting risk with 8 predictors
- RBA reaction function changes over time
- Requires ongoing re-estimation

### 7.6 Weighting Comparison

| Method | Objectivity | Transparency | Adaptability | Data Needs | Recommended For |
|---|---|---|---|---|---|
| Equal | HIGH | HIGH | None | None | MVP starting point |
| Expert Judgment | LOW | HIGH (if documented) | Manual | Domain expertise | Primary approach |
| Inverse Volatility | HIGH | MEDIUM | Automatic | Rolling volatility estimates | Complementary validation |
| PCA | HIGH | LOW | Automatic | 40+ observations | Post-MVP research |
| Regression | HIGH | LOW | Requires re-fitting | Labeled decisions | Future probability model |

### Recommendation

**Use expert judgment weights** (configurable via `weights.json`) with the following rationale:

1. **Start with a defensible default** based on the RBA's dual mandate (inflation and employment are primary)
2. **Document the reasoning** transparently -- users can see why inflation gets 0.25 and building approvals gets 0.05
3. **Backtest against history** -- compare weighted Hawk Score against actual RBA decisions to validate
4. **Iterate** -- adjust weights based on backtesting results

**Suggested default weights (based on RBA mandate analysis):**

| Indicator | Suggested Weight | Rationale |
|---|---|---|
| Inflation (CPI) | 0.25 | Primary RBA mandate -- inflation targeting is the core objective |
| Wages (WPI) | 0.15 | Key leading indicator for inflation; RBA watches wages closely |
| Employment | 0.15 | Second arm of dual mandate (maximum sustainable employment) |
| Housing | 0.15 | Financial stability concern; major transmission mechanism of rate changes |
| ASX Futures | 0.10 | Market expectations embed collective wisdom; forward-looking |
| Retail Trade | 0.10 | Demand-side pressure; consumer spending drives GDP |
| Building Approvals | 0.05 | Leading indicator for construction but very noisy month-to-month |
| Business Confidence | 0.05 | Soft data; useful but less reliable than hard data |

---

## 8. Directional Polarity Handling

### The Problem

Some indicators are "hawkish when rising" (higher = more rate-hike pressure) and some are "hawkish when falling" or have inverted relationships. The Z-score must be oriented so that **positive Z always means hawkish**.

### Polarity Map for Hawk-O-Meter Indicators

| Indicator | Raw Direction | Hawkish When | Z-Score Polarity | Implementation |
|---|---|---|---|---|
| **Inflation (CPI YoY)** | Higher = more inflation | Rising | **Standard (+)** | Z-score as-is |
| **Wages (WPI YoY)** | Higher = faster wage growth | Rising | **Standard (+)** | Z-score as-is |
| **Employment (ratio)** | Higher = tighter labor market | Rising | **Standard (+)** | Z-score as-is |
| **Housing (price/income ratio)** | Higher = more overheated | Rising | **Standard (+)** | Z-score as-is |
| **Retail Trade (real spending)** | Higher = stronger demand | Rising | **Standard (+)** | Z-score as-is |
| **Building Approvals (per capita)** | Higher = more construction | Rising (leading indicator of housing demand) | **Standard (+)** | Z-score as-is |
| **Business Confidence** | Higher = more optimistic | Rising (demand pressure) | **Standard (+)** | Z-score as-is |
| **ASX Futures** | Higher implied rate = more hikes priced | Rising | **Standard (+)** | Z-score as-is |

### Analysis

For the Hawk-O-Meter's current indicator set, **all indicators have standard (positive) polarity** because they've been chosen and normalized to represent "inflationary/tightening pressure." The normalization formulas from the project (price/income ratio, per-capita metrics, real spending) already handle the orientation.

However, the system should still implement polarity handling as a configurable property because:

1. **Future indicators might have inverted polarity** (e.g., unemployment rate is dovish when rising)
2. **It's trivial to implement:** `z_score = z_score * polarity` where polarity is +1 or -1
3. **It documents the intention** -- even if all current indicators are +1, making polarity explicit in the config makes the methodology auditable

### Implementation

```python
# In weights.json or indicator_config.json:
{
    "inflation": {"weight": 0.25, "polarity": 1},
    "wages": {"weight": 0.15, "polarity": 1},
    "employment": {"weight": 0.15, "polarity": 1},
    "housing": {"weight": 0.15, "polarity": 1},
    "asx_futures": {"weight": 0.10, "polarity": 1},
    "spending": {"weight": 0.10, "polarity": 1},
    "building_approvals": {"weight": 0.05, "polarity": 1},
    "business_confidence": {"weight": 0.05, "polarity": 1}
}
```

If unemployment rate were added in the future:
```python
"unemployment": {"weight": 0.10, "polarity": -1}  # Higher unemployment = dovish
```

---

## 9. Recommendations for Hawk-O-Meter

### Core Statistical Approach (Validated)

The project's existing decisions are well-supported by the research:

| Decision | Status | Evidence |
|---|---|---|
| Robust Z-scores (MAD) over standard Z-scores | **CONFIRMED** | OECD CLI uses MAD-based normalization; robust statistics literature strongly supports this for outlier-heavy data |
| 10-year rolling window | **CONFIRMED** | Standard in the literature; balances adaptation speed and statistical stability |
| Linear clamp [-2, +2] to [0, 100] | **CONFIRMED** | Simplest and most transparent; aligns with project's "Data, not opinion" principle |
| 5 zones (Cold/Cool/Neutral/Warm/Hot) | **CONFIRMED** | Reasonable heuristic; map to stance labels well |
| Configurable weights in weights.json | **CONFIRMED** | Expert judgment weights are used by many professional indices; transparency through configuration |

### Refinements to Consider

1. **Widen the clamp range to [-3, +3]** -- reduces the frequency of pegged-at-0-or-100 readings from ~5% to ~0.3%. The zone boundaries would need adjusting accordingly, or keep zones as-is and accept that the "Cold" and "Hot" zones are wider.

2. **Add percentile ranks as a secondary metric** in `status.json` -- provides a distribution-free validation of the Z-score. If they diverge significantly, the data may be non-normal.

3. **Document polarity explicitly** in the indicator configuration, even though all current indicators are positive polarity. This makes the system ready for future indicators with inverted polarity.

4. **Consider inverse-volatility weighting as a validation** -- compute what the weights *would be* if determined purely by inverse volatility, and compare against expert-assigned weights. Large discrepancies warrant investigation.

### Suggested Default Weights

| Indicator | Weight | Rationale |
|---|---|---|
| Inflation (CPI) | 0.25 | Primary mandate |
| Wages (WPI) | 0.15 | Leading inflation indicator |
| Employment | 0.15 | Second mandate arm |
| Housing | 0.15 | Financial stability + rate transmission |
| ASX Futures | 0.10 | Forward-looking market expectations |
| Retail Trade | 0.10 | Demand pressure |
| Building Approvals | 0.05 | Leading but noisy |
| Business Confidence | 0.05 | Soft data |

### Post-MVP Enhancements (Not for Phase 3)

| Enhancement | Complexity | Value | When |
|---|---|---|---|
| Backtest weights against historical RBA decisions | Medium | High -- validates the entire methodology | After 6+ months of data collection |
| Add Taylor Rule deviation as supplementary display | Low | Medium -- theory-based cross-check | Phase 4 or 5 |
| Adaptive window with structural break detection | High | Medium -- marginal improvement over fixed 10-year | V2.0 |
| Logistic regression probability model | High | High -- true probability estimates | After sufficient training data (2+ years) |
| PCA validation of indicator weights | Medium | Low-Medium -- academic interest | V2.0 |

### What NOT to Do

1. **Do not use CDF transform for the gauge mapping** -- it assumes normality and is harder to explain
2. **Do not use PCA for weighting** -- opaque and requires more data than available
3. **Do not attempt to build a probit/logit model for MVP** -- insufficient labeled training data
4. **Do not use standard (mean/std) Z-scores** -- the robust approach is strictly superior for this use case
5. **Do not use a window shorter than 7 years** -- too few observations for stable statistics at quarterly frequency
6. **Do not manually exclude COVID data points** -- robust statistics handle them; manual exclusion introduces subjectivity

---

## 10. Sources

### Primary (HIGH confidence)

- [OECD Handbook on Constructing Composite Indicators](https://www.oecd.org/en/publications/handbook-on-constructing-composite-indicators-methodology-and-user-guide_9789264043466-en.html) -- Authoritative methodology guide for composite index construction
- [OECD System of Composite Leading Indicators](https://www.oecd.org/content/dam/oecd/en/data/methods/OECD-System-of-Composite-Leading-Indicators.pdf) -- Technical methodology document for OECD CLI construction
- [OECD CLI FAQ](https://www.oecd.org/en/data/insights/data-explainers/2024/04/composite-leading-indicators-frequently-asked-questions.html) -- Frequently asked questions about CLI methodology
- [Chicago Fed NFCI Methodology](https://www.chicagofed.org/research/data/nfci/about) -- Construction methodology for the most-cited financial conditions index
- [Conference Board LEI Methodology](https://www.conference-board.org/data/bci/index.cfm?id=2161) -- Construction methodology for the Conference Board's Leading Economic Index
- [Federal Reserve Financial Conditions Index](https://www.federalreserve.gov/econres/notes/feds-notes/a-new-index-to-measure-us-financial-conditions-20230630.html) -- Fed's own FCI construction methodology (2023)
- [RBA Monetary Policy Framework](https://www.rba.gov.au/monetary-policy/) -- RBA's own description of its monetary policy framework and dual mandate

### Secondary (MEDIUM confidence)

- [Pesaran & Timmermann (2007) -- Rolling Window Selection](https://www.sciencedirect.com/science/article/abs/pii/S0304407616301713) -- Optimal rolling window size in the presence of structural breaks
- [Giannellis (2025) -- Rolling Windows Revisited](https://onlinelibrary.wiley.com/doi/10.1002/for.3269) -- Policymaking with structural changes and rolling windows
- [Hall & Tavlas (2024) -- Inflation Forecasting with Rolling Windows](https://onlinelibrary.wiley.com/doi/10.1002/for.3059) -- Comparison of 5-year vs 10-year windows for inflation forecasting
- [Hatzius et al. (2010) -- Financial Conditions Indexes](https://www.princeton.edu/~mwatson/papers/USMPF-2010.pdf) -- Comprehensive review of FCI construction methodologies
- [Cleveland Fed (2014) -- Improved Taylor Rule for Predicting Policy Changes](https://www.clevelandfed.org/publications/economic-commentary/2014/ec-201402-using-an-improved-taylor-rule-to-predict-when-policy-changes-will-occur) -- Using Taylor Rule deviations to predict rate changes
- [Atlanta Fed Taylor Rule Utility](https://www.atlantafed.org/cqer/research/taylor-rule) -- Interactive Taylor Rule calculator
- [Springer: Methodological Framework of Composite Indices](https://link.springer.com/article/10.1007/s11205-017-1832-9) -- Review of weighting, aggregation, and robustness issues
- [PCA for Socioeconomic Composite Indicators (2024)](https://link.springer.com/article/10.1007/s43545-024-00920-x) -- Theoretical and empirical considerations for PCA weighting
- [COINr: Weighting Chapter](https://bluefoxr.github.io/COINrDoc/weighting-1.html) -- Practical guide to composite indicator weighting in R
- [ECB Probit-Based Recession Forecasting](https://www.ecb.europa.eu/pub/pdf/scpwps/ecbwp1255.pdf) -- Probit model application for predicting recessions
- [Fed -- Recession Probabilities from Yield Curve](https://www.federalreserve.gov/econres/notes/feds-notes/predicting-recession-probabilities-using-the-slope-of-the-yield-curve-20180301.html) -- Probit model for recession probability
- [BIS -- Taylor Rules and Global Deviation](https://www.bis.org/publ/qtrpdf/r_qt1209f.pdf) -- Taylor Rule deviations across countries
- [Wikipedia -- Median Absolute Deviation](https://en.wikipedia.org/wiki/Median_absolute_deviation) -- Technical reference for MAD properties and breakdown point
- [Wikipedia -- Robust Statistics](https://en.wikipedia.org/wiki/Robust_statistics) -- Overview of robust statistical measures
- [Statology -- Beyond the Z-Score: Decoding Percentiles](https://www.statology.org/beyond-the-z-score-decoding-what-percentiles-really-mean/) -- Percentile rank vs Z-score comparison
- [DataCamp -- Sigmoid Function](https://www.datacamp.com/tutorial/sigmoid-function) -- Technical reference for sigmoid transform
- [RBA Dual Mandate Speech (Bullock 2025)](https://www.bis.org/review/r250728f.pdf) -- RBA Governor on inflation and employment mandate
- [RBA Statement on Monetary Policy (Nov 2025)](https://www.rba.gov.au/publications/smp/2025/nov/economic-conditions.html) -- Current economic assessment and indicators monitored
- [Westpac IQ -- RBA Decision Analysis (Feb 2026)](https://www.westpaciq.com.au/economics/2026/02/rba-decision-3-february-2026) -- Recent RBA decision context

### Tertiary (LOW confidence -- require validation)

- Various Medium articles on robust statistics and Z-score normalization
- Stack Overflow discussions on rolling window edge cases
- Blog posts on composite indicator construction

---

## Metadata

**Research date:** 2026-02-06
**Valid until:** 2026-05-06 (90 days -- statistical methodology is stable; RBA framework changes slowly)
**Confidence:** HIGH for methodology recommendations; MEDIUM for specific weight suggestions (require backtesting validation)
**Researcher:** Claude (Z-score methodology specialist)
