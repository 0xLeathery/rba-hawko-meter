#!/usr/bin/env python3
"""
One-time historical data backfill script.

Downloads 10 years of historical data from RBA and ABS sources to seed
the data/ directory with sufficient history for Phase 3 Z-score calculations
(10-year rolling window).

Run once during initial setup, then incremental pipeline takes over.

NOTE: CoreLogic and NAB historical data requires manual seed files.
These sources publish data in reports/PDFs that cannot be automatically
backfilled. Create manual CSV files in data/ directory with historical
values compiled from archives.
"""

import sys
import argparse
from datetime import datetime
from typing import Dict

from pipeline.ingest import rba_data, abs_data
from pipeline.config import DATA_DIR


def backfill_rba() -> int:
    """
    Backfill RBA cash rate historical data.

    The RBA Table A2 contains full historical data dating back decades,
    so a single fetch gets all the history we need.

    Returns:
        Total row count in output file
    """
    print("\n" + "=" * 60)
    print("BACKFILLING RBA CASH RATE")
    print("=" * 60)

    row_count = rba_data.fetch_and_save()

    print(f"\n✓ RBA cash rate: {row_count} total rows")

    # Get date range from file
    try:
        import pandas as pd
        df = pd.read_csv(DATA_DIR / 'rba_cash_rate.csv')
        date_min = df['date'].min()
        date_max = df['date'].max()
        print(f"  Date range: {date_min} to {date_max}")
    except Exception as e:
        print(f"  Could not determine date range: {e}")

    return row_count


def backfill_abs() -> Dict[str, int]:
    """
    Backfill ABS economic indicator historical data.

    The ABS Data API fetchers use startPeriod parameter from config.
    For CPI and WPI, config already has startPeriod="2014" (10+ years).
    For employment and retail, config has startPeriod="2020" which may
    need extension for full 10-year history.

    Returns:
        Dict mapping series name to total row count
    """
    print("\n" + "=" * 60)
    print("BACKFILLING ABS ECONOMIC INDICATORS")
    print("=" * 60)

    # Use the fetch_and_save function which fetches all configured series
    results = abs_data.fetch_and_save()

    print("\n" + "=" * 60)
    print("ABS BACKFILL SUMMARY")
    print("=" * 60)

    for series, count in results.items():
        print(f"✓ {series}: {count} total rows")

        # Get date range from file
        try:
            import pandas as pd
            output_file = abs_data.ABS_CONFIG[series]["output_file"]
            df = pd.read_csv(DATA_DIR / output_file)
            date_min = df['date'].min()
            date_max = df['date'].max()
            print(f"  Date range: {date_min} to {date_max}")
        except Exception as e:
            print(f"  Could not determine date range: {e}")

    return results


def main():
    """Main backfill execution."""
    parser = argparse.ArgumentParser(
        description='Backfill 10 years of historical economic data',
        epilog="""
NOTE: This script only backfills RBA and ABS data sources.
CoreLogic and NAB historical data must be manually compiled from
reports/archives and placed in the data/ directory as CSV files.
        """
    )
    parser.add_argument(
        '--source',
        choices=['rba', 'abs', 'all'],
        default='all',
        help='Source to backfill (default: all)'
    )

    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("HISTORICAL DATA BACKFILL SCRIPT")
    print("=" * 60)
    print(f"Started: {datetime.utcnow().isoformat()}Z")
    print(f"Target: {args.source}")

    try:
        if args.source in ('rba', 'all'):
            backfill_rba()

        if args.source in ('abs', 'all'):
            backfill_abs()

        print("\n" + "=" * 60)
        print("BACKFILL COMPLETE")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Run 'python -m pipeline.main' for incremental updates")
        print("2. For CoreLogic/NAB: manually compile historical CSV files")
        print("   from reports/archives and place in data/ directory")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Backfill failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
