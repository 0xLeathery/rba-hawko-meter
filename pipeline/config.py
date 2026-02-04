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
        "key": "1.10001.10.Q",  # Index Number, All groups CPI, Original, Weighted Average of 8 Capital Cities
        "params": {"startPeriod": "2014", "detail": "dataonly"},
        "output_file": "abs_cpi.csv",
        "description": "Consumer Price Index (quarterly)",
        "critical": True,
    },
    "employment": {
        "dataflow": "LF",
        "key": "M1.1.AUS",  # Labour Force total employment, Australia
        "params": {"startPeriod": "2014", "detail": "dataonly"},
        "output_file": "abs_employment.csv",
        "description": "Labour Force employment (monthly)",
        "critical": True,
    },
    "retail_trade": {
        "dataflow": "RT",
        "key": "A3348827X",  # Retail Trade total turnover
        "params": {"startPeriod": "2014", "detail": "dataonly"},
        "output_file": "abs_retail_trade.csv",
        "description": "Retail Trade turnover (monthly)",
        "critical": True,
    },
    "wage_price_index": {
        "dataflow": "WPI",
        "key": "1.THRPEB.10.Q",  # Total hourly rates of pay excluding bonuses, Original
        "params": {"startPeriod": "2014", "detail": "dataonly"},
        "output_file": "abs_wage_price_index.csv",
        "description": "Wage Price Index (quarterly)",
        "critical": True,
    },
    "building_approvals": {
        "dataflow": "BA",
        "key": "1.1.AUS.M",  # Total dwellings, Australia, Monthly
        "params": {"startPeriod": "2014", "detail": "dataonly"},
        "output_file": "abs_building_approvals.csv",
        "description": "Building Approvals total dwellings (monthly)",
        "critical": True,
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
