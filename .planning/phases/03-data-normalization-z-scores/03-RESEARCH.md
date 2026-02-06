# Phase 3 Research: Data Normalization & Z-Scores

**Synthesized from:** z-score-methodology.md, rba-decision-drivers.md, 03-RESEARCH.md (original)
**Purpose:** Implementation-relevant findings for the Phase 3 executor agent
**Date:** 2026-02-06

---

## 1. Statistical Approach (Validated)

### Robust Z-Scores (Median + MAD)

Standard Z-scores `z = (x - mean) / std` are inappropriate because COVID-era outliers inflate both mean and standard deviation. The project uses **robust Z-scores**:

```
z = (x - median) / MAD
```

Where MAD = `median(|x_i - median(x)|) * 1.4826` (scaling constant for normal-distribution consistency).

This is validated by the OECD Composite Leading Indicators system and the Chicago Fed NFCI, both of which start with MAD-based normalization.

**Implementation:** Use `scipy.stats.median_abs_deviation(data, scale='normal')` which applies the 1.4826 factor automatically. However, to avoid adding scipy as a dependency for a single function, a numpy-only implementation is also acceptable: `np.median(np.abs(x - np.median(x))) * 1.4826`.

**Zero-dispersion guard:** When MAD = 0 (all values identical, e.g., cash rate held constant), return Z = 0 (neutral). No movement means no pressure signal.

### Rolling Window: 10 Years

- **40 quarterly observations** provides statistical stability while capturing regime changes
- Captures at least one full monetary policy cycle
- COVID outliers (2020-2021) roll out by 2030-2031; robust statistics handle them until then
- **Minimum 5 years fallback** via `min_periods` parameter
- **Confidence levels:** HIGH (>= 32 obs / 8 years), MEDIUM (20-31 obs / 5-8 years), LOW (< 20 obs / < 5 years)

### Frequency Standardization

All indicators must be aligned to **quarterly frequency** before Z-scoring:
- Monthly data (employment, retail, building approvals): use end-of-quarter value
- Quarterly data (CPI, WPI): already aligned
- Event-based (cash rate): use end-of-quarter value

This ensures a "40-observation window" covers the same 10-year calendar period for all indicators.

---

## 2. Available Data & Normalization Formulas

### Phase 1 CSV Files (data/ directory)

| File | Content | Frequency | Rows | Date Range | Schema |
|------|---------|-----------|------|------------|--------|
| rba_cash_rate.csv | Cash rate target | Event-based | ~96 | 1990-2025 | date,value,source |
| abs_cpi.csv | CPI index numbers | Quarterly | ~62 | 2014-2025 | date,value,source,series_id |
| abs_employment.csv | Labour force data | Monthly | ~72 | 2020-2025 | date,value,source,series_id |
| abs_retail_trade.csv | Retail turnover | Monthly | ~66 | 2020-2025 | date,value,source,series_id |
| abs_wage_price_index.csv | WPI index | Quarterly | ~47 | 2014-2025 | date,value,source,series_id |
| abs_building_approvals.csv | Dwelling approvals | Monthly | ~144 | 2014-2025 | date,value,source,series_id |

**Data quality notes:**
- Employment CSV has mixed series (values jump from ~5 to ~146) -- must filter for correct series or handle carefully
- Retail trade contains nominal values -- must convert to YoY % change
- Building approvals starts with zeros in early 2014 -- filter these out
- CoreLogic and NAB scrapers are stubs -- engine must handle missing indicators gracefully

### Normalization to Ratios (No Nominal Values)

Per project constraint ("strictly NO nominal currency values in gauges"), all indicators must be rates, ratios, or indices:

| Indicator | Raw Data | Normalization | Output |
|-----------|----------|---------------|--------|
| Inflation (CPI) | Index number | YoY % change: `(cpi_t / cpi_{t-4} - 1) * 100` | % change |
| Wages (WPI) | Index number | YoY % change: `(wpi_t / wpi_{t-4} - 1) * 100` | % change |
| Employment | Mixed series | Use unemployment rate or employment-population ratio (already %) | % |
| Retail Trade | Turnover ($M) | YoY % change: `(val_t / val_{t-4} - 1) * 100` | % change |
| Housing | Price data | YoY % change or price-to-income ratio | % or ratio |
| Building Approvals | Count | YoY % change: `(val_t / val_{t-12} - 1) * 100` (monthly) | % change |
| Business Confidence | NAB index | Already a ratio/index | Index |
| ASX Futures | Implied rate | Displayed as benchmark, not in hawk score | % |

**Pragmatic approach for MVP:** YoY percentage change is the primary normalization method. It eliminates nominal values, is simple to implement, and is standard for economic dashboards.

---

## 3. Gauge Mapping & Zones

### Linear Clamp: [-3, +3] to [0, 100]

```python
gauge = max(0, min(100, (z + 3) / 6 * 100))
```

**Refinement from research:** The original 03-CONTEXT.md specified [-2, +2]. Research recommends widening to **[-3, +3]** because:
- With [-2, +2], ~4.6% of observations clip to 0 or 100 (too many "pegged" readings)
- With [-3, +3], only ~0.3% clip (much more informative range)
- Linearity and transparency are preserved

### 5 Zones

| Zone | Gauge Range | Label | Color |
|------|-------------|-------|-------|
| Cold | 0-20 | Strong dovish pressure | Blue/Green |
| Cool | 20-40 | Mild dovish pressure | Light Green |
| Neutral | 40-60 | Balanced | Amber |
| Warm | 60-80 | Mild hawkish pressure | Light Red |
| Hot | 80-100 | Strong hawkish pressure | Red |

### Polarity

All currently tracked indicators have **positive polarity** (higher = more hawkish) because normalizations orient them that way. System supports configurable polarity for future indicators:

```python
oriented_z = z_score * polarity  # polarity is +1 or -1
```

---

## 4. Weights Configuration

### Expert-Judgment Weights (weights.json)

Based on RBA dual mandate analysis from rba-decision-drivers.md:

```json
{
  "inflation": { "weight": 0.25, "polarity": 1, "label": "Inflation (CPI)" },
  "wages": { "weight": 0.15, "polarity": 1, "label": "Wages (WPI)" },
  "employment": { "weight": 0.15, "polarity": 1, "label": "Employment" },
  "housing": { "weight": 0.15, "polarity": 1, "label": "Housing" },
  "spending": { "weight": 0.10, "polarity": 1, "label": "Retail Trade" },
  "building_approvals": { "weight": 0.05, "polarity": 1, "label": "Building Approvals" },
  "business_confidence": { "weight": 0.05, "polarity": 1, "label": "Business Confidence" },
  "asx_futures": { "weight": 0.10, "polarity": 1, "label": "ASX Futures" }
}
```

**Rationale:** Inflation (0.25) as primary mandate. Employment and wages (0.15 each) as dual mandate. Housing (0.15) for financial stability. ASX futures (0.10) forward-looking. Spending (0.10) demand pressure. Building approvals and business confidence (0.05 each) are noisy but useful.

**Validation rule:** Weights must sum to 1.0 (with floating-point tolerance: 0.99-1.01).

**Key decision from rba-decision-drivers.md:** ASX futures serve as a **benchmark displayed separately**, not as an input to the hawk score. This means the hawk score is derived from fundamental indicators only, and futures provide an independent market-based comparison. However, the weights.json includes it for now -- the engine can easily exclude it from the weighted calculation while still computing its gauge value.

---

## 5. Technology Stack

### Dependencies

| Library | Purpose | Status |
|---------|---------|--------|
| pandas | Rolling windows, DataFrame ops, CSV I/O | Already in requirements.txt |
| numpy | MAD calculation, numerical operations | **Add to requirements.txt** |

**No scipy needed.** The MAD calculation is simple enough with numpy: `np.median(np.abs(x - np.median(x))) * 1.4826`. This avoids adding a heavy dependency for one function.

**No pydantic needed for MVP.** While the original 03-RESEARCH.md recommended pydantic for status.json validation, the project's "avoid over-engineering" constraint suggests using simple dict construction with manual validation. The status.json schema is stable and small enough that pydantic adds unnecessary complexity.

---

## 6. Module Structure

The normalization engine integrates into the existing pipeline:

```
pipeline/
  normalize/
    __init__.py
    ratios.py        # Raw CSV -> normalized ratios (YoY %, etc.)
    zscore.py        # Rolling window robust Z-score computation
    gauge.py         # Z-score -> 0-100 mapping, zone classification
    engine.py        # Orchestrator: reads CSVs, computes all gauges, outputs status.json
  config.py          # Add INDICATOR_CONFIG dict mapping indicators to CSV files + params
data/
  weights.json       # Expert-judgment weights (configurable)
public/
  data/
    status.json      # Output: rich contract for frontend (Phase 4)
```

### Pipeline Flow

```
data/*.csv --> ratios.py (normalize) --> zscore.py (rolling stats) --> gauge.py (map) --> engine.py --> public/data/status.json
```

### Integration with pipeline/main.py

After ingestors complete, the orchestrator calls the normalization engine:
```python
# In pipeline/main.py, after Phase 2 (optional sources):
from pipeline.normalize.engine import generate_status
generate_status()
```

---

## 7. status.json Contract

```json
{
  "generated_at": "2026-02-06T10:30:00Z",
  "pipeline_version": "1.0.0",
  "overall": {
    "hawk_score": 67.3,
    "zone": "warm",
    "zone_label": "Mild hawkish pressure",
    "verdict": "Economic indicators suggest moderate tightening pressure",
    "confidence": "HIGH"
  },
  "gauges": {
    "inflation": {
      "value": 78.2,
      "zone": "warm",
      "z_score": 1.69,
      "raw_value": 3.7,
      "raw_unit": "% YoY",
      "weight": 0.25,
      "polarity": 1,
      "data_date": "2025-12-01",
      "staleness_days": 67,
      "confidence": "HIGH",
      "interpretation": "Inflation above long-run average",
      "history": [62.1, 65.3, 68.9, 71.2, 73.5, 74.8, 76.1, 77.0, 77.5, 77.9, 78.0, 78.2]
    }
  },
  "weights": {
    "inflation": 0.25,
    "wages": 0.15
  },
  "metadata": {
    "window_years": 10,
    "clamp_range": [-3, 3],
    "mapping": "linear",
    "statistics": "robust (median/MAD)",
    "indicators_available": 6,
    "indicators_missing": ["housing", "business_confidence"]
  }
}
```

Key features:
- **Per-gauge history array** (last 12 quarterly values) for sparklines
- **Staleness tracking** via `data_date` and `staleness_days`
- **Missing indicator handling** via `metadata.indicators_missing`
- **Transparency** via `weights` and `metadata` sections

---

## 8. Risks & Mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| Employment CSV has mixed series (values 5 to 146) | HIGH | Filter for consistent series_id; validate data ranges |
| Only ~5 years of employment data (2020+) | MEDIUM | Use 5-year window with LOW confidence flag |
| Building approvals starts with zeros (2014) | MEDIUM | Filter out zero rows before computing stats |
| CoreLogic/NAB scrapers are stubs | HIGH | Engine skips missing indicators, reports in metadata |
| CPI is quarterly, others monthly | LOW | Standardize all to quarterly before Z-scoring |
| Retail trade has mixed nominal values | MEDIUM | Use YoY % change which eliminates nominal dependency |
| Weights are subjective | LOW | Documented rationale, configurable via JSON, backtestable |

---

## 9. Resolved Open Questions

| Question | Resolution |
|----------|------------|
| IQR vs MAD for Z-score? | **MAD** -- standard for robust Z-scores; IQR mentioned in 03-CONTEXT.md was informal; MAD with 1.4826 scaling is the statistical norm |
| Clamp range [-2,+2] or wider? | **[-3,+3]** -- reduces clipping from 4.6% to 0.3% of observations |
| scipy dependency? | **No** -- numpy-only MAD calculation is sufficient |
| pydantic for validation? | **No** -- manual validation keeps dependencies minimal for MVP |
| Sparkline data: raw or gauge? | **Gauge values (0-100)** -- last 12 quarters (3 years of trend) |
| ASX futures in hawk score? | **No** -- display as benchmark alongside hawk score; futures gauge computed but excluded from weighted average |
| Zone thresholds basis? | **Heuristic** -- equal 20-point bands on 0-100 scale; will validate against historical RBA decisions post-MVP |
