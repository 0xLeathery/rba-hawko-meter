# RBA Decision Drivers: Research for the Hawk-O-Meter

> Research compiled: February 2026
> Purpose: Inform indicator selection, weighting, and polarity for the Hawk-O-Meter hawk score

---

## 1. What the RBA Explicitly Cites in Monetary Policy Statements

Analysis of RBA Monetary Policy Board statements from 2025-2026 reveals a consistent set of indicators the Board references when making rate decisions. The February 2026 rate hike to 3.85% (the first hike since 2023) provides an excellent case study of what drives RBA action.

### Primary Indicators Cited (every statement)

1. **Inflation (headline and underlying/trimmed mean)** - Always the lead paragraph. The Feb 2026 statement opened with: "inflationary pressures picked up materially in the second half of 2025." Underlying inflation at 3.7% and headline at 4.2% were forecast to peak mid-2026.

2. **Labour market conditions** - Unemployment rate (4.25% range), labour underutilisation, job vacancies, unit labour costs (5.4% YoY in Sep quarter), and forward-looking indicators like hiring intentions.

3. **Private demand growth** - Household consumption, dwelling investment, and business investment. The Feb 2026 statement highlighted "growth in private demand strengthening substantially more than expected."

4. **Capacity pressures** - Survey measures of capacity utilisation, output gap estimates, unit labour cost growth. The Board noted capacity pressures were "greater than previously anticipated."

### Secondary Indicators Cited (most statements)

5. **Financial conditions** - Credit availability, exchange rate, money market rates, government bond yields. Noted as having "eased over 2025."

6. **Housing market activity** - Housing prices and dwelling investment were cited as "continuing to pick up."

7. **Global economic developments** - Trading partner growth, trade policy impacts (US tariffs), global demand conditions.

8. **Wages** - Private sector WPI eased to 3.2% YoY, but unit labour costs remained elevated at 5.4%, reflecting weak productivity.

### Occasional Mentions

9. **Public demand / fiscal policy** - Government spending trajectory and its impact on aggregate demand.
10. **Exchange rate** - Primarily through its effect on import prices and financial conditions.
11. **Productivity growth** - Mentioned as context for elevated unit labour costs.

### Key Observation
The RBA does NOT cite individual indicators in isolation. It synthesises multiple data points into a narrative about "demand vs supply balance" and "capacity pressures." The Hawk-O-Meter should mirror this approach - individual indicator gauges feeding a composite hawk score.

---

## 2. Leading Indicators That Predict Rate Changes

### Classification by Lead Time

**Long-leading (6-18 months before rate change):**
- **ASX 30-day interbank cash rate futures** - Market pricing of expectations; reflects all available information. Most direct predictor.
- **Yield curve slope** - Gap between long-term bond yields and short-term rates signals whether policy is tight or loose.
- **Building approvals** - Leads the construction cycle and housing-related inflation by 12-18 months.
- **Money supply / credit growth** - Credit growth picking up "noticeably" was cited in the Feb 2026 hike context.

**Medium-leading (3-6 months):**
- **NAB Business Confidence / Conditions** - Forward-looking survey of ~600-900 non-agricultural businesses. Changes in business sentiment are early signals of future spending, hiring, and investment. The NAB December 2025 survey specifically "suggested a potential rate hike by the RBA."
- **Job advertisements and vacancies** - RBA research confirms these are "useful in informing near-term forecasts for the unemployment rate."
- **Consumer sentiment / unemployment expectations** - Consumers' expectations for unemployment over the year ahead found to have predictive value.
- **CPI (quarterly and monthly)** - The actual inflation read, though somewhat lagging in measurement, drives the next decision directly.

**Short-leading / coincident (0-3 months):**
- **Trimmed mean CPI** - The RBA's preferred inflation measure. Quarterly reads directly trigger policy reassessment.
- **Retail trade** - Timely indicator of household consumption strength.
- **Labour Force Survey** - Monthly unemployment rate and participation.

**Lagging indicators (confirm rather than predict):**
- **GDP** - Confirms the demand picture but published with significant lag.
- **Wage Price Index** - Quarterly, significant publication lag. Confirms rather than leads wage pressures.
- **Unemployment rate itself** - Companies are "invariably slow to adjust hiring decisions."

### RBA's Own Research on Leading Labour Market Indicators
The RBA's April 2025 Bulletin specifically examined leading labour market indicators and found that models containing job advertisements, vacancies, consumer unemployment expectations, and firms' hiring intentions "can complement the RBA's existing framework for forecasting the unemployment rate."

---

## 3. Gap Analysis: Current Indicator Set vs What's Needed

### Currently Tracked

| Indicator | Type | RBA Citation Frequency | Verdict |
|-----------|------|----------------------|---------|
| CPI (headline) | Official | Every statement | Essential - KEEP |
| Retail trade | Official | Most statements | Good proxy for demand - KEEP |
| Employment/unemployment | Official | Every statement | Essential - KEEP |
| Wage Price Index (WPI) | Official | Most statements | Essential - KEEP |
| Building approvals | Official | Occasionally | Good leading indicator - KEEP |
| CoreLogic housing data | Scraped | Most statements | Good - KEEP |
| NAB business confidence | Scraped | Occasionally | Good leading indicator - KEEP |
| ASX cash rate futures | Market | N/A (market pricing) | Essential benchmark - KEEP |

### Critical Missing Indicators

| Indicator | Source | Priority | Rationale |
|-----------|--------|----------|-----------|
| **Trimmed mean CPI** | ABS | **CRITICAL** | RBA's preferred inflation measure. Headline CPI is volatile; trimmed mean is what actually drives policy. Must add. |
| **Unit labour costs** | ABS National Accounts | **HIGH** | Cited in every recent statement. 5.4% growth was a key driver of the Feb 2026 hike. Captures wage-productivity interaction. |
| **Capacity utilisation** | NAB Business Survey | **HIGH** | "Survey measures of capacity utilisation are above their long-run average" - directly cited in Feb 2026 decision. Already scraping NAB; could extract this alongside confidence. |
| **Credit growth** | RBA | **MEDIUM** | "Credit was readily available... credit growth picking up noticeably" - cited as evidence financial conditions may no longer be restrictive. |
| **Job vacancies** | ABS | **MEDIUM** | Part of RBA's full employment assessment framework. Vacancies-to-searchers ratio has "additional information about inflation beyond... the unemployment gap." |

### Lower Priority (Consider for v2)

| Indicator | Rationale |
|-----------|-----------|
| **GDP growth** | Lagging, but provides demand context. Published quarterly with significant delay. |
| **Consumer sentiment** | Westpac-Melbourne Institute survey. Leading indicator for consumption. |
| **Terms of trade / commodity prices** | Influences AUD and export income. Indirect monetary policy channel. |
| **Global factors (Fed rate, China growth)** | Important context but hard to reduce to a single directional signal. |
| **Exchange rate (AUD/USD)** | Affects imported inflation but is partly endogenous to RBA policy. |
| **Household savings rate** | Indicates consumer buffer; lower savings = more spending = more inflationary. |

### Recommendation
The current set covers ~60% of the indicators the RBA explicitly cites. Adding trimmed mean CPI, unit labour costs, and capacity utilisation would bring coverage to ~85%. These three additions should be the top priority for Phase 2 data expansion.

---

## 4. ASX 30-Day Interbank Cash Rate Futures

### How It Works

- **Contract specs:** Cash-settled against the monthly average of the Interbank Overnight Cash Rate (published by the RBA). Notional value AUD 3,000,000. Quoted in yield percent per annum in multiples of 0.005%, with yield deducted from 100 for quotation (i.e., a price of 96.15 implies a 3.85% rate).
- **Available contracts:** Monthly contracts extending 18+ months forward.
- **Settlement:** Against the realised average cash rate for the calendar month, so each contract maps cleanly to specific RBA meetings.

### Rate Probability Calculation

The ASX RBA Rate Tracker calculates implied probabilities using the following methodology:

1. The expected rate change is derived by comparing the implied yield of the futures contract for the month containing an RBA meeting with the current cash rate.
2. The calculation accounts for the number of days before vs after the RBA Board meeting within the month (since the rate change only applies to post-meeting days).
3. Formula: `P(change) = (Implied rate - Current rate) / Change size`, adjusted for the within-month day split.

### Reliability Assessment

**Strengths:**
- Exchange-traded, transparent, and freely accessible (easy to audit).
- Reflects the aggregated view of sophisticated market participants (banks, funds, dealers).
- Updated daily; captures new information quickly.
- Historically tracks actual outcomes reasonably well over short horizons (1-3 months).

**Limitations:**
- Deviations from theoretical prices post-announcement are common, "particularly when a large amount of uncertainty exists around the RBA decision."
- Term premia can distort longer-dated implied rates (markets demand compensation for uncertainty, biasing implied rates upward).
- Liquidity drops for contracts 6+ months out, reducing signal reliability.
- Reflects market consensus, not necessarily the correct outcome - markets can be wrong (as seen in multiple historical episodes where cuts were priced but hikes occurred, and vice versa).

### Recommendation for Hawk-O-Meter
ASX futures should serve as a **market benchmark** rather than an input to the hawk score calculation. Display it prominently as "what the market thinks" alongside the Hawk-O-Meter's own assessment (derived from fundamental indicators). This creates a useful comparison: if the hawk score and futures diverge significantly, that itself is informative.

---

## 5. Indicator Weights and Polarity

### Analytical Framework

The RBA operates under a modified Taylor rule framework where:
- **Inflation deviation from target** receives the highest implicit weight
- **Output gap / capacity pressures** receive secondary weight
- **Labour market tightness** is assessed through multiple indicators
- **Financial conditions** are monitored as a transmission mechanism

Academic research on Australian monetary policy (Gross, 2022) finds that RBA policy decisions are "better than the decisions that would have been made by mechanically following the macroeconomic model's optimal simple rule" - meaning the RBA exercises judgement beyond any simple weighting formula.

### Proposed Weight Framework

Given the RBA's revealed preferences from statement analysis, the following weight distribution is recommended:

| Category | Weight | Rationale |
|----------|--------|-----------|
| Inflation measures | 35% | "Sustainably returning inflation to target is the Board's highest priority" |
| Labour market / wages | 25% | Second pillar of dual mandate; unit labour costs increasingly emphasised |
| Demand / activity | 20% | Private demand strength was key driver of Feb 2026 hike |
| Housing / financial conditions | 10% | Cited but as supporting evidence rather than primary drivers |
| Leading / sentiment indicators | 10% | Forward-looking but noisy signals |

### Polarity (Direction of Hawkishness)

For each indicator, higher values push toward hawkish (rate hike) or dovish (rate cut):

| Indicator | Hawkish Signal | Dovish Signal | Polarity |
|-----------|---------------|---------------|----------|
| CPI (headline) | Rising above 3% | Falling below 2% | Positive (higher = more hawkish) |
| Trimmed mean CPI | Rising above 3% | Falling below 2% | Positive |
| Unemployment rate | Falling below NAIRU (~4.5%) | Rising above 5% | Negative (higher = more dovish) |
| Employment growth | Strong growth (tight market) | Weak/negative | Positive |
| WPI | Rising above 3.5% | Below 3% | Positive |
| Unit labour costs | Rising (above productivity) | Falling | Positive |
| Retail trade | Strong growth | Weak/contracting | Positive |
| Building approvals | Strong (demand pressure) | Weak | Positive |
| CoreLogic housing | Rising prices | Falling prices | Positive |
| NAB business confidence | High/rising | Low/falling | Positive |
| NAB capacity utilisation | Above long-run average | Below average | Positive |
| Credit growth | Accelerating | Decelerating | Positive |
| Job vacancies | High/rising | Low/falling | Positive |
| ASX futures implied rate | Above current cash rate | Below current cash rate | N/A (benchmark) |

---

## 6. Trimmed Mean CPI vs Headline CPI in RBA Decision-Making

### Key Differences

- **Headline CPI** measures the overall change in prices of the full consumer basket, including volatile items (fuel, fruit, vegetables) and government-influenced items (childcare subsidies, energy rebates).
- **Trimmed mean CPI** strips out the items with the largest positive and negative price changes each quarter (typically the top and bottom 15%), providing a smoother measure of "underlying" inflation.

### RBA's Stated Preference

The RBA explicitly prefers trimmed mean as its guide for policy:

> "Considering forecasts of underlying inflation allows the Board to look through volatility in prices and the effect of one-off or temporary measures that do not influence the underlying degree of price pressures in the economy."

However, there is an important nuance: The Statement on the Conduct of Monetary Policy defines the inflation target as "consumer price inflation between 2 and 3 per cent" - which technically refers to headline CPI. Trimmed mean is the RBA's operational guide, but headline CPI is the formal target.

### Recent Example
In H2 2025, headline CPI rose to 3.8% (October monthly read) while trimmed mean was at 3.3%. Both were cited in the Feb 2026 decision. The Board noted that "part of the pick-up in inflation was assessed to reflect temporary factors" (headline-specific) but that "the lift in price pressures was seen in a broad range of categories" (confirmed by trimmed mean).

### Recommendation for Hawk-O-Meter
- Track BOTH headline and trimmed mean CPI
- Give trimmed mean a **higher weight** (approximately 2:1 ratio vs headline) since it drives actual policy action
- When headline diverges significantly from trimmed mean, flag this divergence in the dashboard UI as it indicates temporary factors are at play
- Use the quarterly trimmed mean series from the ABS as the primary source (the RBA has stated it will continue to focus on quarterly measures while monthly CPI data matures)

---

## 7. Typical Lead Times of Indicators Before Rate Changes

| Indicator | Lead Time | Classification | Notes |
|-----------|-----------|---------------|-------|
| ASX cash rate futures | 1-6 months | Forward-looking market | Most accurate at 1-3 month horizon; degrades beyond 6 months |
| Building approvals | 12-18 months | Long-leading | Leads construction cycle and housing-related inflation |
| Credit growth | 6-12 months | Long-leading | Credit expansion precedes demand-driven inflation |
| NAB business confidence | 3-6 months | Medium-leading | Forward-looking survey; confidence changes precede investment/hiring |
| Job vacancies | 3-6 months | Medium-leading | Leads actual employment changes |
| Consumer sentiment / unemployment expectations | 3-6 months | Medium-leading | RBA research confirms predictive value for unemployment rate |
| Retail trade | 1-3 months | Short-leading | Timely indicator but relatively coincident with consumption |
| CPI (trimmed mean) | 0-1 quarter | Coincident/trigger | Published with ~1 month lag; directly triggers policy reassessment |
| Labour Force Survey | 0-1 month | Coincident | Monthly publication; confirms labour market state |
| Wage Price Index | Lagging | Lagging | Published quarterly with significant delay; confirms wage dynamics |
| GDP | Lagging | Lagging | Published ~2 months after quarter end; confirms demand picture |
| CoreLogic housing | 1-3 months | Short-leading/coincident | Monthly publication; timely but somewhat reactive |

### Monetary Policy Transmission Lag
RBA research (and BIS papers) indicates that monetary policy changes take 12-24 months to have full effect on the economy. This means the RBA must be forward-looking, which is why leading indicators matter more than lagging ones for predicting rate changes.

### Recommendation for Hawk-O-Meter
The hawk score should weight leading indicators more heavily than lagging ones. A possible time-weighting scheme:
- **Leading indicators (6-18 month lead):** 1.2x multiplier
- **Coincident indicators:** 1.0x multiplier
- **Lagging indicators:** 0.8x multiplier

This can be applied on top of the category weights from Section 5.

---

## 8. RBA's Dual Mandate and Indicator Priority

### The Mandate

Since the 2023 RBA Review, the RBA has an explicit dual mandate:
1. **Price stability** - Inflation between 2-3% (targeting the midpoint)
2. **Full employment** - Maximum sustainable employment

### How It Translates to Indicator Priority

Governor Bullock's July 2025 speech ("The RBA's Dual Mandate - Inflation and Employment") clarified the practical interpretation:

> "Sustainably returning inflation to target within a reasonable timeframe is the Board's highest priority, which is consistent with the RBA's mandate for price stability and full employment."

Board member Fry-McKibbin added nuance: the review recommended "equal consideration" of inflation and employment, not equal weighting. The appropriate emphasis shifts over time - "inflation may take precedence in some periods, while employment becomes the priority in others."

### Full Employment Assessment Framework (Updated Feb 2026)

The RBA does NOT have a numerical full employment target (unlike its 2-3% inflation target). Instead, it uses a multi-indicator dashboard:

1. **Unemployment rate** - Compared to estimated NAIRU (~4.25-4.5%)
2. **Vacancies-to-searchers ratio** - Broader than vacancies-to-unemployment; captures people already employed who are searching plus those outside the labour force. Found to have "additional information about inflation beyond... the unemployment gap."
3. **Hours worked per capita** - When high relative to trend, suggests tighter labour market
4. **Job-finding rate of the unemployed** - Speed at which unemployed find work
5. **Non-mining capacity utilisation** - Broader economic tightness measure

### Practical Implication for Hawk-O-Meter
When inflation is above target AND unemployment is low (as in Feb 2026), both mandates point the same way (tighten). The hawk score should be strongly hawkish.

When mandates conflict (e.g., inflation above target but unemployment rising), the RBA has revealed a preference for prioritising inflation - but with more caution and slower adjustment. The hawk score should reflect this asymmetry: inflation deviation gets priority but labour market deterioration acts as a moderating force.

---

## 9. Global Factors in RBA Decision-Making

### How Global Factors Enter RBA Thinking

Global factors are cited in every RBA statement but primarily as **context** rather than direct policy triggers:

1. **Trading partner growth** - Australia's major trading partners' GDP growth affects demand for exports, terms of trade, and domestic income. The Feb 2026 statement noted growth was "more resilient to developments in trade policy than anticipated."

2. **US Federal Reserve policy** - Interest rate differentials between Australia and the US influence capital flows and the AUD/USD exchange rate. A higher Fed rate relative to RBA rate puts downward pressure on the AUD, which increases imported inflation.

3. **Commodity prices** - Commodities account for a large share of Australian exports. Higher commodity prices improve terms of trade and boost national income, which can be inflationary domestically.

4. **China's economy** - Australia's largest trading partner. Chinese demand for iron ore, coal, and LNG directly impacts Australia's export revenue and GDP.

5. **Global trade policy** - US tariffs and trade disruptions were a significant consideration in 2025-2026 RBA deliberations.

### Transmission Channels
- **Exchange rate** - Rising domestic rates strengthen the AUD via yield-seeking capital inflows, moderating imported inflation but hurting export competitiveness
- **Import prices** - AUD depreciation feeds through to CPI with a lag of 6-12 months
- **Terms of trade** - Affects national income and government revenue
- **Confidence** - Global uncertainty weighs on business and consumer confidence

### Recommendation for Hawk-O-Meter
Global factors are important context but difficult to reduce to a single directional gauge. Two approaches:

**Option A (Recommended for v1):** Do not include a separate global factor gauge. Instead, note that global factors are already partially captured through:
- CPI (import price channel)
- NAB business confidence (confidence channel)
- ASX futures (market pricing of all information including global)

**Option B (Consider for v2):** Add a "Global Risk" composite indicator using:
- AUD/USD (inverse relationship - weaker AUD = more hawkish via import prices)
- Iron ore price (positive relationship - higher = more income = more demand)
- Fed funds rate differential (larger negative spread = dovish AUD pressure)

---

## 10. Recommendations for the Hawk-O-Meter

### Recommended Indicator Scorecard

#### Tier 1: Core Indicators (must have, drive the hawk score)

| # | Indicator | Source | Weight | Polarity | Lead Time | Status |
|---|-----------|--------|--------|----------|-----------|--------|
| 1 | Trimmed mean CPI | ABS (quarterly) | 20% | Positive | Coincident | **ADD** |
| 2 | Headline CPI | ABS (monthly/quarterly) | 10% | Positive | Coincident | Exists |
| 3 | Unemployment rate | ABS Labour Force | 12% | Negative | Coincident | Exists |
| 4 | Employment growth | ABS Labour Force | 5% | Positive | Coincident | Exists |
| 5 | Wage Price Index | ABS (quarterly) | 8% | Positive | Lagging | Exists |
| 6 | Retail trade | ABS (monthly) | 8% | Positive | Short-leading | Exists |

#### Tier 2: Important Supporting Indicators

| # | Indicator | Source | Weight | Polarity | Lead Time | Status |
|---|-----------|--------|--------|----------|-----------|--------|
| 7 | Unit labour costs | ABS National Accounts | 7% | Positive | Lagging | **ADD** |
| 8 | NAB capacity utilisation | NAB survey (scraped) | 5% | Positive | Medium-leading | **ADD** |
| 9 | CoreLogic housing | Scraped | 5% | Positive | Short-leading | Exists |
| 10 | Building approvals | ABS (monthly) | 5% | Positive | Long-leading | Exists |
| 11 | NAB business confidence | NAB (scraped) | 5% | Positive | Medium-leading | Exists |
| 12 | Credit growth | RBA (monthly) | 5% | Positive | Long-leading | **ADD** |
| 13 | Job vacancies | ABS (quarterly) | 5% | Positive | Medium-leading | **ADD** |

#### Benchmark (displayed separately, not in hawk score)

| # | Indicator | Source | Purpose |
|---|-----------|--------|---------|
| 14 | ASX 30-day cash rate futures | ASX | Market expectations benchmark |

**Total weights: 100%** across indicators 1-13.

### How to Calculate the Hawk Score

1. **Normalise** each indicator to a Z-score (number of standard deviations from its historical mean).
2. **Apply polarity** - multiply negative-polarity indicators (unemployment) by -1 so that higher Z-scores always mean "more hawkish."
3. **Apply time-weighting** - multiply by lead-time multiplier (1.2x for leading, 1.0x for coincident, 0.8x for lagging). Renormalise weights after.
4. **Apply category weights** - multiply each Z-score by its weight from the scorecard above.
5. **Sum** weighted Z-scores to produce a raw hawk score.
6. **Scale** to a 0-100 gauge using the historical distribution of the composite score.

### Threshold Interpretation

| Hawk Score | Interpretation | Colour |
|------------|---------------|--------|
| 0-20 | Strong dovish pressure (rate cut likely) | Deep green |
| 20-40 | Mild dovish pressure | Light green |
| 40-60 | Neutral / balanced | Amber |
| 60-80 | Mild hawkish pressure | Light red |
| 80-100 | Strong hawkish pressure (rate hike likely) | Deep red |

### Implementation Priority

**Phase 1 (Current):** Use existing 8 indicators with the weights and polarities above. Trimmed mean CPI can be derived from the same ABS data source as headline CPI with minimal additional work.

**Phase 2 (Next sprint):** Add unit labour costs, capacity utilisation (from NAB scrape), credit growth (from RBA statistics), and job vacancies (from ABS).

**Phase 3 (Future):** Consider consumer sentiment, global composite, GDP growth, and household savings rate.

### Key Design Principles

1. **ASX futures as benchmark, not input** - Display market expectations alongside the hawk score for comparison, but keep the hawk score independent (derived from fundamentals only). Divergence between the two is itself informative.

2. **Trimmed mean over headline** - The 2:1 weighting ratio reflects the RBA's own operational preference. Flag large divergences between the two.

3. **Asymmetric mandate weighting** - When inflation is above target, inflation indicators dominate. When inflation is within target, labour market indicators gain relative importance. Consider implementing this as a dynamic weight adjustment.

4. **Lead time bonus** - Leading indicators get a modest boost (1.2x) because they predict where the economy is going, not just where it has been. This is consistent with the RBA's stated approach of being "forward-looking and data-dependent."

5. **No nominal values** - Per project constraints, all indicators should be rates, ratios, or indices, never nominal dollar values. CoreLogic housing data should be expressed as growth rate or price-to-income ratio, not dollar values.

---

## Sources

- [RBA Monetary Policy Decision, February 2026](https://www.rba.gov.au/media-releases/2026/mr-26-03.html)
- [RBA Statement on Monetary Policy, February 2026](https://www.rba.gov.au/publications/smp/2026/feb/overview.html)
- [RBA Statement on Monetary Policy, November 2025](https://www.rba.gov.au/publications/smp/2025/nov/outlook.html)
- [RBA Board Minutes, December 2025](https://www.rba.gov.au/monetary-policy/rba-board-minutes/2025/2025-12-09.html)
- [RBA: The Dual Mandate - Inflation and Employment (Bullock speech, July 2025)](https://www.rba.gov.au/speeches/2025/sp-gov-2025-07-24.html)
- [RBA: Update on Approach to Assessing Full Employment, February 2026](https://www.rba.gov.au/publications/technical-notes/2026/update-on-the-rbas-approach-to-assessing-full-employment.html)
- [RBA: Leading Labour Market Indicators (Bulletin, April 2025)](https://www.rba.gov.au/publications/bulletin/2025/apr/how-useful-are-leading-labour-market-indicators-at-forecasting-the-unemployment-rate.html)
- [RBA: Headline and Underlying Inflation (Box C, August 2024)](https://www.rba.gov.au/publications/smp/2024/aug/box-c-headline-and-underlying-inflation.html)
- [RBA: Monthly CPI Transition (Technical Note, November 2025)](https://www.rba.gov.au/publications/smp/2025/nov/technical-note-the-transition-to-a-complete-monthly-cpi.html)
- [RBA: Assessing Full Employment (Bulletin, April 2024)](https://www.rba.gov.au/publications/bulletin/2024/apr/assessing-full-employment-in-australia.html)
- [RBA: Monetary Policy - Forward Looking and Data Dependent (speech, March 2025)](https://www.rba.gov.au/speeches/2025/sp-ag-2025-03-18.html)
- [ASX 30-Day Interbank Cash Rate Futures Factsheet](https://www.asx.com.au/content/dam/asx/markets/trade-our-derivatives-market/derivatives-market-overview/interest-rate-derivatives/short-term-derivatives/30-day-interbank-cash-rate-factsheet.pdf)
- [ASX RBA Rate Tracker](https://www.asx.com.au/markets/trade-our-derivatives-market/futures-market/rba-rate-tracker)
- [ASX Rate Tracker Calculation Methodology](https://www.asx.com.au/data/trt/rate_tracker_calc.htm)
- [Gross (2022): Assessing Australian Monetary Policy in the Twenty-First Century, Economic Record](https://onlinelibrary.wiley.com/doi/10.1111/1475-4932.12689)
- [BIS: The Lags of Monetary Policy (Gruen, Romalis, Chandra)](https://www.bis.org/publ/confp04l.pdf)
- [CBA: RBA Rate Rise Forecast, December 2025](https://www.commbank.com.au/articles/newsroom/2025/12/cba-economists-tip-february-rba-rate-rise.html)
- [CBA: RBA Increases Cash Rate to 3.85%, February 2026](https://www.commbank.com.au/articles/newsroom/2026/02/rba-lifts-increases-official-cash-rate.html)
