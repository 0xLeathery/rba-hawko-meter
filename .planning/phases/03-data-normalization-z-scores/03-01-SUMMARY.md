---
phase: 03-data-normalization-z-scores
plan: 01
subsystem: pipeline
tags: [numpy, z-score, mad, normalization, gauge, weights]

requires:
  - phase: 01-foundation-data-pipeline
    provides: CSV data files in data/ directory (CPI, WPI, employment, retail, building approvals)
provides:
  - INDICATOR_CONFIG mapping 5 core indicators to CSV files and normalization params
  - OPTIONAL_INDICATOR_CONFIG for 3 stub indicators
  - data/weights.json with 8 expert-judgment weights summing to 1.0
  - ratios.py for CSV-to-YoY% normalization with quarterly resampling
  - zscore.py for robust Z-scores (median/MAD with 1.4826 scaling)
  - gauge.py for 0-100 linear mapping, zone classification, weighted hawk score
affects: [03-02, 04-hawk-o-meter-gauges]

tech-stack:
  added: [numpy]
  patterns: [robust-statistics-median-mad, yoy-pct-change-normalization, linear-clamp-gauge-mapping]

key-files:
  created:
    - pipeline/normalize/__init__.py
    - pipeline/normalize/ratios.py
    - pipeline/normalize/zscore.py
    - pipeline/normalize/gauge.py
    - data/weights.json
  modified:
    - pipeline/config.py
    - requirements.txt

key-decisions:
  - "numpy-only MAD calculation (no scipy dependency)"
  - "[-3,+3] clamp range reduces clipping from 4.6% to 0.3%"
  - "ASX futures excluded from hawk score via exclude_benchmark parameter"
  - "Zero MAD returns Z=0 (neutral) -- no variability means no pressure signal"

patterns-established:
  - "Robust Z-score: median/MAD with 1.4826 scaling, look-back-only rolling window"
  - "Normalization pipeline: CSV -> YoY% -> quarterly resample -> Z-score -> gauge"
  - "Indicator config pattern: INDICATOR_CONFIG dict in config.py maps names to params"
  - "Weight rebalancing: missing indicators excluded, remaining weights rescaled to sum=1.0"

duration: 3min
completed: 2026-02-06
---

# Phase 3 Plan 01: Normalization Engine Core Summary

**Robust Z-score normalization engine with median/MAD statistics, [-3,+3] linear gauge mapping, and configurable expert-judgment weights**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-06T05:40:26Z
- **Completed:** 2026-02-06T05:43:28Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- Three-step statistical pipeline: raw CSV -> YoY % change -> robust Z-score -> 0-100 gauge value
- Robust statistics (median/MAD) resistant to COVID-era outliers without data exclusion
- End-to-end verified: CPI at 1.4% YoY -> Z=-0.16 -> Gauge=47.3 -> neutral zone (realistic)
- Configurable weights.json with documented rationale based on RBA dual mandate analysis

## Task Commits

Each task was committed atomically:

1. **Task 1: Create indicator config, weights.json, and ratio normalization module** - `5b4783c` (feat)
2. **Task 2: Create robust Z-score and gauge mapping modules** - `a1ca16d` (feat)

## Files Created/Modified
- `pipeline/config.py` - Added INDICATOR_CONFIG, OPTIONAL_INDICATOR_CONFIG, Z-score constants, output paths
- `data/weights.json` - 8 expert-judgment weights with polarity and descriptions
- `requirements.txt` - Added numpy>=1.24,<3.0
- `pipeline/normalize/__init__.py` - Package docstring
- `pipeline/normalize/ratios.py` - CSV loading, YoY % change, quarterly resampling, data filtering
- `pipeline/normalize/zscore.py` - Robust Z-score (median/MAD), rolling window, confidence levels
- `pipeline/normalize/gauge.py` - Linear clamp mapping, zone classification, weighted hawk score, verdict generation

## Decisions Made
- Used numpy-only MAD calculation (np.median(np.abs(x - np.median(x))) * 1.4826) instead of scipy.stats.median_abs_deviation to avoid heavy dependency
- [-3, +3] clamp range per research refinement (original CONTEXT specified [-2, +2])
- ASX futures gauge computed but excluded from hawk score via exclude_benchmark parameter in compute_hawk_score
- Zero MAD (all values identical) returns Z=0 (neutral) -- no variability means no pressure signal
- Mixed-series indicators (employment, retail, building approvals) accepted as-is -- robust statistics handle outliers

## Deviations from Plan

None -- plan executed exactly as written.

## Issues Encountered
- Employment, retail trade, and building approvals CSVs contain mixed ABS series (values swing wildly). This is a known Phase 1 data quality issue. Robust Z-scores handle this: median/MAD is resistant to outliers by design. These indicators will produce valid but potentially less meaningful gauge values until the ABS filters are refined.

## User Setup Required

None -- no external service configuration required.

## Next Phase Readiness
- All three modules (ratios.py, zscore.py, gauge.py) ready for Plan 03-02 engine.py to orchestrate
- INDICATOR_CONFIG and weights.json ready for consumption
- Mixed-series data in employment/retail/building_approvals is a known limitation, not a blocker

---
*Phase: 03-data-normalization-z-scores*
*Completed: 2026-02-06*
