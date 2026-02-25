"""
Incremental CSV file handler with deduplication.
Appends new data to existing CSVs without duplicating rows.
"""

from pathlib import Path

import pandas as pd


def append_to_csv(
    file_path: str | Path,
    new_data: pd.DataFrame,
    date_column: str = 'date'
) -> int:
    """
    Append new data to a CSV file, deduplicating on date column.

    Args:
        file_path: Path to CSV file (created if doesn't exist)
        new_data: DataFrame with new rows to append
        date_column: Column name to use for deduplication (default: 'date')

    Returns:
        Total number of rows in the file after append
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    if file_path.exists():
        # Load existing data
        existing = pd.read_csv(file_path)

        # Concatenate and deduplicate
        combined = pd.concat([existing, new_data], ignore_index=True)

        # Drop duplicates, keeping last occurrence (newest data)
        combined = combined.drop_duplicates(subset=[date_column], keep='last')

        # Sort by date
        combined = combined.sort_values(by=date_column).reset_index(drop=True)

        new_count = len(combined) - len(existing)
        total_count = len(combined)

        # Write back
        combined.to_csv(file_path, index=False, date_format='%Y-%m-%d')

        print(f"Written {total_count} rows to {file_path} ({new_count} new)")

        return total_count
    else:
        # No existing file, just write new data
        new_data = new_data.sort_values(by=date_column).reset_index(drop=True)
        new_data.to_csv(file_path, index=False, date_format='%Y-%m-%d')

        print(f"Written {len(new_data)} rows to {file_path} (new file)")

        return len(new_data)
