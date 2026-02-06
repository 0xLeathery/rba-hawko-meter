"""
Central configuration for RBA Hawk-O-Meter data pipeline.
Defines data source URLs, API parameters, file paths, and metadata.
"""

from pathlib import Path

# Data output directory
DATA_DIR = Path("data")

# HTTP client configuration
DEFAULT_TIMEOUT = 30  # seconds
USER_AGENT = "RBA-Hawko-Meter/1.0 (Data Pipeline)"
BROWSER_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

# RBA (Reserve Bank of Australia) configuration
RBA_BASE_URL = "https://www.rba.gov.au/statistics/tables/csv"
RBA_CONFIG = {
    "cash_rate": {
        "table_id": "a2-data",
        "url_suffix": ".csv",
        "output_file": "rba_cash_rate.csv",
        "description": "Cash Rate Target (changes in monetary policy)",
        "critical": True,
    }
}

# ABS (Australian Bureau of Statistics) Data API configuration
ABS_API_BASE = "https://data.api.abs.gov.au/data"
ABS_CONFIG = {
    "cpi": {
        "dataflow": "CPI",
        "key": "all",
        "params": {"startPeriod": "2014", "detail": "dataonly"},
        "filters": {
            "MEASURE": "1",  # Index numbers
            "INDEX": "10001",  # All groups CPI
            "TSEST": "10",  # Original (not seasonally adjusted)
            "REGION": "50",  # Australia
        },
        "output_file": "abs_cpi.csv",
        "description": "Consumer Price Index (monthly)",
        "critical": True,
    },
    "employment": {
        "dataflow": "LF",
        "key": "M3.3.1599.20.AUS.M",
        "params": {"startPeriod": "2014", "detail": "dataonly"},
        "filters": {},
        "output_file": "abs_employment.csv",
        "description": "Total employed persons, Australia, Seasonally Adjusted (monthly, thousands)",
        "critical": True,
    },
    "retail_trade": {
        "dataflow": "RT",
        "key": "M1.20.20.AUS.M",
        "params": {"startPeriod": "2014", "detail": "dataonly"},
        "filters": {},
        "output_file": "abs_retail_trade.csv",
        "description": "Retail Trade turnover, Total Australia, Seasonally Adjusted, Current Prices (monthly, $millions)",
        "critical": True,
    },
    "wage_price_index": {
        "dataflow": "WPI",
        "key": "all",
        "params": {"startPeriod": "2014", "detail": "dataonly"},
        "filters": {
            "MEASURE": "1",  # Index numbers
            "INDEX": "THRPEB",  # Total hourly rates of pay excluding bonuses
            "TSEST": "10",  # Original
        },
        "output_file": "abs_wage_price_index.csv",
        "description": "Wage Price Index (quarterly)",
        "critical": True,
    },
    "building_approvals": {
        "dataflow": "BA_GCCSA",
        "key": "all",
        "params": {"startPeriod": "2014", "detail": "dataonly"},
        "filters": {
            "MEASURE": "1",           # Number of dwelling units
            "REGION": "AUS",          # Australia total
            "BUILDING_TYPE": "100",   # Total Residential
            "VALUE": "1",             # Total (all value ranges)
            "WORK_TYPE": "1",         # New work
            "SECTOR": "9",            # Total Sectors
            "TSEST": "10",            # Original
        },
        "output_file": "abs_building_approvals.csv",
        "description": "Building Approvals, total new residential dwellings, Australia (monthly, original)",
        "critical": False,
    },
}

# Source metadata for all data sources
SOURCE_METADATA = {
    "RBA": {
        "file_path": DATA_DIR / "rba_cash_rate.csv",
        "critical": True,
        "description": "Reserve Bank of Australia cash rate target",
    },
    "ABS_CPI": {
        "file_path": DATA_DIR / "abs_cpi.csv",
        "critical": True,
        "description": "Consumer Price Index",
    },
    "ABS_EMPLOYMENT": {
        "file_path": DATA_DIR / "abs_employment.csv",
        "critical": True,
        "description": "Labour Force employment",
    },
    "ABS_RETAIL": {
        "file_path": DATA_DIR / "abs_retail_trade.csv",
        "critical": True,
        "description": "Retail Trade turnover",
    },
    "ABS_WPI": {
        "file_path": DATA_DIR / "abs_wage_price_index.csv",
        "critical": True,
        "description": "Wage Price Index",
    },
    "ABS_BA": {
        "file_path": DATA_DIR / "abs_building_approvals.csv",
        "critical": True,
        "description": "Building Approvals",
    },
}


# =============================================================================
# Phase 3: Normalization engine configuration
# =============================================================================

# Indicator configuration for normalization pipeline
# Maps each indicator to its CSV file, normalization method, and parameters
INDICATOR_CONFIG = {
    "inflation": {
        "csv_file": "abs_cpi.csv",
        "normalize": "yoy_pct_change",
        "frequency": "quarterly",
        "yoy_periods": 4,
        "description": "Consumer Price Index YoY % change",
    },
    "wages": {
        "csv_file": "abs_wage_price_index.csv",
        "normalize": "yoy_pct_change",
        "frequency": "quarterly",
        "yoy_periods": 4,
        "description": "Wage Price Index YoY % change",
    },
    "employment": {
        "csv_file": "abs_employment.csv",
        "normalize": "yoy_pct_change",
        "frequency": "monthly",
        "yoy_periods": 12,
        "description": "Labour force YoY % change",
    },
    "spending": {
        "csv_file": "abs_retail_trade.csv",
        "normalize": "yoy_pct_change",
        "frequency": "monthly",
        "yoy_periods": 12,
        "description": "Retail trade turnover YoY % change",
    },
    "building_approvals": {
        "csv_file": "abs_building_approvals.csv",
        "normalize": "yoy_pct_change",
        "frequency": "monthly",
        "yoy_periods": 12,
        "description": "Building approvals YoY % change",
    },
}

# Optional indicators (stubs -- csv_file=None until scrapers implemented)
OPTIONAL_INDICATOR_CONFIG = {
    "housing": {
        "csv_file": None,
        "normalize": "yoy_pct_change",
        "frequency": "monthly",
        "yoy_periods": 12,
        "description": "Housing prices YoY % change",
    },
    "business_confidence": {
        "csv_file": None,
        "normalize": "direct",
        "frequency": "quarterly",
        "yoy_periods": None,
        "description": "NAB Business Confidence index",
    },
    "asx_futures": {
        "csv_file": None,
        "normalize": "direct",
        "frequency": "monthly",
        "yoy_periods": None,
        "description": "ASX implied futures rate",
    },
}

# Z-score computation parameters
ZSCORE_WINDOW_YEARS = 10
ZSCORE_MIN_YEARS = 5
ZSCORE_CLAMP_MIN = -3.0
ZSCORE_CLAMP_MAX = 3.0

# Confidence thresholds (in quarterly observations)
CONFIDENCE_HIGH_MIN_OBS = 32   # 8 years quarterly
CONFIDENCE_MEDIUM_MIN_OBS = 20  # 5 years quarterly

# Output paths
WEIGHTS_FILE = DATA_DIR / "weights.json"
STATUS_OUTPUT = Path("public") / "data" / "status.json"
