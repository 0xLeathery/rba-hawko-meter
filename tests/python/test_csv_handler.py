"""
Unit tests for pipeline.utils.csv_handler module.

Tests append_to_csv with:
  - New file creation
  - Appending new rows
  - Deduplication by date column (last wins semantics)
  - Mixed new and duplicate rows
  - Sort by date after append
  - Parent directory creation
  - Empty new_data DataFrame edge case
"""

import pandas as pd
import pytest

from pipeline.utils.csv_handler import append_to_csv


def test_append_to_csv_creates_new_file(tmp_path):
    """Pass non-existent path: file is created and returns correct row count."""
    csv_path = tmp_path / "new_file.csv"
    assert not csv_path.exists()

    new_data = pd.DataFrame({"date": ["2024-01-01", "2024-02-01"], "value": [1.0, 2.0]})
    result = append_to_csv(csv_path, new_data)

    assert csv_path.exists()
    assert result == 2

    written = pd.read_csv(csv_path)
    assert len(written) == 2
    assert list(written["value"]) == [1.0, 2.0]


def test_append_to_csv_appends_new_rows(tmp_path):
    """Append new rows to existing file: file now has 4 rows sorted by date."""
    csv_path = tmp_path / "existing.csv"

    # Create initial file
    initial = pd.DataFrame({"date": ["2024-01-01", "2024-02-01"], "value": [1.0, 2.0]})
    append_to_csv(csv_path, initial)

    # Append new rows
    new_rows = pd.DataFrame({"date": ["2024-03-01", "2024-04-01"], "value": [3.0, 4.0]})
    result = append_to_csv(csv_path, new_rows)

    assert result == 4

    written = pd.read_csv(csv_path)
    assert len(written) == 4
    # Dates should be in ascending order
    assert list(written["date"]) == ["2024-01-01", "2024-02-01", "2024-03-01", "2024-04-01"]


def test_append_to_csv_deduplicates_last_wins(tmp_path):
    """Dedup by date: appending same date with new value keeps new value (last wins)."""
    csv_path = tmp_path / "dedup.csv"

    initial = pd.DataFrame({"date": ["2024-01-01"], "value": [1.0]})
    append_to_csv(csv_path, initial)

    # Append same date with updated value
    updated = pd.DataFrame({"date": ["2024-01-01"], "value": [1.5]})
    result = append_to_csv(csv_path, updated)

    assert result == 1

    written = pd.read_csv(csv_path)
    assert len(written) == 1
    assert written["value"].iloc[0] == 1.5


def test_append_to_csv_mixed_new_and_duplicate_rows(tmp_path):
    """Mixed new/dupe rows: 3 rows total, duplicate date gets updated value."""
    csv_path = tmp_path / "mixed.csv"

    initial = pd.DataFrame({
        "date": ["2024-01-01", "2024-02-01"],
        "value": [1.0, 2.0],
    })
    append_to_csv(csv_path, initial)

    # 2024-02-01 is a duplicate (updated to 2.5), 2024-03-01 is new
    mixed = pd.DataFrame({
        "date": ["2024-02-01", "2024-03-01"],
        "value": [2.5, 3.0],
    })
    result = append_to_csv(csv_path, mixed)

    assert result == 3

    written = pd.read_csv(csv_path)
    assert len(written) == 3

    # 2024-02-01 should have the updated value 2.5
    feb_row = written[written["date"] == "2024-02-01"]
    assert len(feb_row) == 1
    assert feb_row["value"].iloc[0] == 2.5


def test_append_to_csv_sorted_ascending(tmp_path):
    """Rows appended in reverse chronological order are written sorted ascending."""
    csv_path = tmp_path / "sort_test.csv"

    # Append rows in reverse order
    reversed_data = pd.DataFrame({
        "date": ["2024-04-01", "2024-02-01", "2024-03-01", "2024-01-01"],
        "value": [4.0, 2.0, 3.0, 1.0],
    })
    result = append_to_csv(csv_path, reversed_data)

    assert result == 4

    written = pd.read_csv(csv_path)
    dates = list(written["date"])
    assert dates == sorted(dates), f"Expected sorted dates, got: {dates}"


def test_append_to_csv_creates_parent_directories(tmp_path):
    """Deep nested path: parent directories are created automatically."""
    csv_path = tmp_path / "sub" / "dir" / "test.csv"
    assert not csv_path.parent.exists()

    new_data = pd.DataFrame({"date": ["2024-01-01"], "value": [99.0]})
    result = append_to_csv(csv_path, new_data)

    assert csv_path.exists()
    assert result == 1


def test_append_to_csv_empty_new_data_unchanged(tmp_path):
    """Appending empty DataFrame to existing file leaves data unchanged."""
    csv_path = tmp_path / "stable.csv"

    initial = pd.DataFrame({
        "date": ["2024-01-01", "2024-02-01"],
        "value": [10.0, 20.0],
    })
    append_to_csv(csv_path, initial)

    # Append empty DataFrame
    empty_df = pd.DataFrame({"date": [], "value": []})
    result = append_to_csv(csv_path, empty_df)

    assert result == 2

    written = pd.read_csv(csv_path)
    assert len(written) == 2
    assert list(written["value"]) == [10.0, 20.0]
