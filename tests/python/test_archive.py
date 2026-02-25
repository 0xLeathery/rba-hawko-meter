"""
Tests for pipeline.normalize.archive — snapshot archival and delta injection.

Covers: save_snapshot, read_previous_snapshot, inject_deltas.
TDD RED phase: these tests are written before the implementation.
"""

import json
from datetime import UTC, datetime, timedelta

import pytest

from pipeline.normalize.archive import (
    inject_deltas,
    read_previous_snapshot,
    save_snapshot,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_status():
    """Minimal status dict matching status.json structure."""
    return {
        "generated_at": "2026-02-26T00:00:00Z",
        "pipeline_version": "1.0.0",
        "overall": {
            "hawk_score": 52.0,
            "zone": "neutral",
            "zone_label": "Balanced",
            "verdict": "Economic indicators are broadly balanced",
            "confidence": "LOW",
        },
        "gauges": {
            "inflation": {
                "value": 30.2,
                "zone": "cool",
                "zone_label": "Mild dovish pressure",
                "z_score": -1.185,
                "raw_value": 3.76,
                "raw_unit": "% YoY",
                "weight": 0.25,
                "polarity": 1,
                "data_date": "2025-12-31",
                "staleness_days": 55,
                "confidence": "HIGH",
                "interpretation": "Inflation below long-run average",
                "history": [100.0, 87.2, 39.0, 30.2],
            },
            "wages": {
                "value": 84.8,
                "zone": "hot",
                "zone_label": "Strong hawkish pressure",
                "z_score": 2.087,
                "raw_value": 5.45,
                "raw_unit": "% YoY",
                "weight": 0.15,
                "polarity": 1,
                "data_date": "2025-10-01",
                "staleness_days": 146,
                "confidence": "HIGH",
                "interpretation": "Wage growth significantly above long-run average",
                "history": [100.0, 63.4, 56.7, 84.8],
            },
        },
    }


@pytest.fixture
def previous_status():
    """Previous week's status dict for delta comparison."""
    return {
        "generated_at": "2026-02-19T00:00:00Z",
        "pipeline_version": "1.0.0",
        "overall": {
            "hawk_score": 48.5,
            "zone": "neutral",
            "zone_label": "Balanced",
            "verdict": "Economic indicators are broadly balanced",
            "confidence": "LOW",
        },
        "gauges": {
            "inflation": {
                "value": 28.0,
                "zone": "cool",
                "zone_label": "Mild dovish pressure",
                "z_score": -1.3,
                "raw_value": 3.5,
                "raw_unit": "% YoY",
                "weight": 0.25,
                "polarity": 1,
                "data_date": "2025-12-31",
                "staleness_days": 48,
                "confidence": "HIGH",
                "interpretation": "Inflation below long-run average",
                "history": [100.0, 87.2, 39.0, 28.0],
            },
            "wages": {
                "value": 84.8,
                "zone": "hot",
                "zone_label": "Strong hawkish pressure",
                "z_score": 2.087,
                "raw_value": 5.45,
                "raw_unit": "% YoY",
                "weight": 0.15,
                "polarity": 1,
                "data_date": "2025-10-01",
                "staleness_days": 139,
                "confidence": "HIGH",
                "interpretation": "Wage growth significantly above long-run average",
                "history": [100.0, 63.4, 56.7, 84.8],
            },
        },
    }


@pytest.fixture
def snapshots_dir(tmp_path):
    """Return a temporary snapshots directory."""
    d = tmp_path / "snapshots"
    d.mkdir()
    return d


# =============================================================================
# save_snapshot tests
# =============================================================================


class TestSaveSnapshot:
    def test_creates_file_and_index(self, snapshots_dir, sample_status):
        """Save a snapshot and verify dated file + index.json are created."""
        save_snapshot(sample_status, snapshots_dir)

        today = datetime.now(UTC).strftime("%Y-%m-%d")
        snapshot_file = snapshots_dir / f"{today}.json"
        index_file = snapshots_dir / "index.json"

        assert snapshot_file.exists(), "Dated snapshot file not created"
        assert index_file.exists(), "index.json not created"

        with open(snapshot_file) as f:
            saved = json.load(f)
        assert saved["overall"]["hawk_score"] == 52.0

        with open(index_file) as f:
            index = json.load(f)
        assert today in index["snapshots"]

    def test_idempotent(self, snapshots_dir, sample_status):
        """Calling twice on same date doesn't create duplicate index entries."""
        save_snapshot(sample_status, snapshots_dir)
        save_snapshot(sample_status, snapshots_dir)

        with open(snapshots_dir / "index.json") as f:
            index = json.load(f)

        today = datetime.now(UTC).strftime("%Y-%m-%d")
        assert index["snapshots"].count(today) == 1

    def test_rolling_cap(self, snapshots_dir, sample_status):
        """Creating 53 snapshots enforces 52-entry rolling cap."""
        base_date = datetime(2025, 1, 1)
        for i in range(53):
            date_str = (base_date + timedelta(weeks=i)).strftime("%Y-%m-%d")
            snapshot_path = snapshots_dir / f"{date_str}.json"
            with open(snapshot_path, "w") as f:
                json.dump(sample_status, f)

            index_path = snapshots_dir / "index.json"
            if index_path.exists():
                with open(index_path) as f:
                    index = json.load(f)
            else:
                index = {"snapshots": []}
            if date_str not in index["snapshots"]:
                index["snapshots"].append(date_str)
                index["snapshots"].sort()
            with open(index_path, "w") as f:
                json.dump(index, f)

        # Now call save_snapshot which should enforce the cap
        save_snapshot(sample_status, snapshots_dir, max_entries=52)

        with open(snapshots_dir / "index.json") as f:
            index = json.load(f)

        assert len(index["snapshots"]) <= 52, (
            f"Rolling cap not enforced: {len(index['snapshots'])} entries"
        )

    def test_creates_directory(self, tmp_path, sample_status):
        """Calling on non-existent directory creates it."""
        new_dir = tmp_path / "new" / "snapshots"
        assert not new_dir.exists()

        save_snapshot(sample_status, new_dir)

        assert new_dir.exists()
        assert (new_dir / "index.json").exists()

    def test_oldest_file_deleted_on_cap(self, snapshots_dir, sample_status):
        """When cap is exceeded, oldest snapshot file is deleted from disk."""
        base_date = datetime(2025, 1, 1)
        oldest_date_str = base_date.strftime("%Y-%m-%d")

        # Create index with 52 entries manually
        dates = []
        for i in range(52):
            date_str = (base_date + timedelta(weeks=i)).strftime("%Y-%m-%d")
            dates.append(date_str)
            snapshot_path = snapshots_dir / f"{date_str}.json"
            with open(snapshot_path, "w") as f:
                json.dump({"week": i}, f)

        index = {"snapshots": sorted(dates)}
        with open(snapshots_dir / "index.json", "w") as f:
            json.dump(index, f)

        # Now add one more via save_snapshot
        new_date = (base_date + timedelta(weeks=52)).strftime("%Y-%m-%d")
        # Override the date by writing the file ourselves and calling save
        snapshot_path = snapshots_dir / f"{new_date}.json"
        with open(snapshot_path, "w") as f:
            json.dump(sample_status, f)

        # Update index
        with open(snapshots_dir / "index.json") as f:
            index = json.load(f)
        index["snapshots"].append(new_date)
        index["snapshots"].sort()
        with open(snapshots_dir / "index.json", "w") as f:
            json.dump(index, f)

        # Now save_snapshot should enforce cap
        save_snapshot(sample_status, snapshots_dir, max_entries=52)

        # Oldest should be deleted
        assert not (snapshots_dir / f"{oldest_date_str}.json").exists(), (
            "Oldest snapshot file not deleted"
        )


# =============================================================================
# read_previous_snapshot tests
# =============================================================================


class TestReadPreviousSnapshot:
    def test_no_index(self, tmp_path):
        """Returns None when snapshots_dir has no index.json."""
        empty_dir = tmp_path / "empty_snapshots"
        empty_dir.mkdir()
        result = read_previous_snapshot(empty_dir)
        assert result is None

    def test_no_old_enough(self, snapshots_dir, sample_status):
        """Returns None when all snapshots younger than min_age_days."""
        today = datetime.now(UTC).strftime("%Y-%m-%d")
        yesterday = (datetime.now(UTC) - timedelta(days=1)).strftime("%Y-%m-%d")

        # Create two recent snapshots
        for date_str in [today, yesterday]:
            with open(snapshots_dir / f"{date_str}.json", "w") as f:
                json.dump(sample_status, f)

        index = {"snapshots": sorted([today, yesterday])}
        with open(snapshots_dir / "index.json", "w") as f:
            json.dump(index, f)

        result = read_previous_snapshot(snapshots_dir, min_age_days=5)
        assert result is None

    def test_returns_most_recent_eligible(self, snapshots_dir, sample_status):
        """With snapshots at ages 1, 7, 14 days, returns 7-day-old one."""
        today = datetime.now(UTC)
        dates = {
            "recent": (today - timedelta(days=1)).strftime("%Y-%m-%d"),
            "eligible": (today - timedelta(days=7)).strftime("%Y-%m-%d"),
            "older": (today - timedelta(days=14)).strftime("%Y-%m-%d"),
        }

        for label, date_str in dates.items():
            data = {**sample_status, "label": label}
            with open(snapshots_dir / f"{date_str}.json", "w") as f:
                json.dump(data, f)

        index = {"snapshots": sorted(dates.values())}
        with open(snapshots_dir / "index.json", "w") as f:
            json.dump(index, f)

        result = read_previous_snapshot(snapshots_dir, min_age_days=5)
        assert result is not None
        assert result["label"] == "eligible"

    def test_skips_missing_file(self, snapshots_dir, sample_status):
        """Index references a date but file is missing — skips gracefully."""
        today = datetime.now(UTC)
        missing_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        valid_date = (today - timedelta(days=14)).strftime("%Y-%m-%d")

        # Only create the valid file, not the missing one
        with open(snapshots_dir / f"{valid_date}.json", "w") as f:
            json.dump({**sample_status, "label": "valid"}, f)

        index = {"snapshots": sorted([missing_date, valid_date])}
        with open(snapshots_dir / "index.json", "w") as f:
            json.dump(index, f)

        result = read_previous_snapshot(snapshots_dir, min_age_days=5)
        assert result is not None
        assert result["label"] == "valid"

    def test_empty_snapshots_list(self, snapshots_dir):
        """index.json exists but snapshots list is empty — returns None."""
        with open(snapshots_dir / "index.json", "w") as f:
            json.dump({"snapshots": []}, f)

        result = read_previous_snapshot(snapshots_dir)
        assert result is None


# =============================================================================
# inject_deltas tests
# =============================================================================


class TestInjectDeltas:
    def test_none_previous(self, sample_status):
        """previous_snapshot=None leaves status_dict unchanged."""
        original_keys = set(sample_status["overall"].keys())
        inject_deltas(sample_status, None)
        assert set(sample_status["overall"].keys()) == original_keys

    def test_overall_block(self, sample_status, previous_status):
        """Verifies previous_hawk_score and hawk_score_delta added."""
        inject_deltas(sample_status, previous_status)

        assert sample_status["overall"]["previous_hawk_score"] == 48.5
        assert sample_status["overall"]["hawk_score_delta"] == 3.5

    def test_gauge_fields(self, sample_status, previous_status):
        """Verifies previous_value, delta, direction for inflation gauge."""
        inject_deltas(sample_status, previous_status)

        inflation = sample_status["gauges"]["inflation"]
        assert inflation["previous_value"] == 28.0
        assert inflation["delta"] == 2.2
        assert "delta_direction" in inflation

    def test_direction_up(self, sample_status, previous_status):
        """Positive delta yields delta_direction='up'."""
        inject_deltas(sample_status, previous_status)

        inflation = sample_status["gauges"]["inflation"]
        # 30.2 - 28.0 = 2.2 (positive)
        assert inflation["delta_direction"] == "up"

    def test_direction_down(self, sample_status, previous_status):
        """Negative delta yields delta_direction='down'."""
        # Make current lower than previous for wages
        sample_status["gauges"]["wages"]["value"] = 80.0
        inject_deltas(sample_status, previous_status)

        wages = sample_status["gauges"]["wages"]
        # 80.0 - 84.8 = -4.8 (negative)
        assert wages["delta_direction"] == "down"

    def test_direction_unchanged(self, sample_status, previous_status):
        """Zero delta yields delta_direction='unchanged'."""
        inject_deltas(sample_status, previous_status)

        wages = sample_status["gauges"]["wages"]
        # 84.8 - 84.8 = 0.0
        assert wages["delta_direction"] == "unchanged"

    def test_new_indicator(self, sample_status, previous_status):
        """Gauge exists in current but not previous — no delta fields."""
        # Add a new gauge to current that isn't in previous
        sample_status["gauges"]["housing"] = {
            "value": 59.4,
            "zone": "neutral",
        }
        inject_deltas(sample_status, previous_status)

        housing = sample_status["gauges"]["housing"]
        assert "previous_value" not in housing
        assert "delta" not in housing
        assert "delta_direction" not in housing

    def test_rounding(self, sample_status, previous_status):
        """Deltas are rounded to 1 decimal place."""
        # Set values to produce a float that needs rounding
        sample_status["gauges"]["inflation"]["value"] = 30.15
        previous_status["gauges"]["inflation"]["value"] = 30.0
        inject_deltas(sample_status, previous_status)

        inflation = sample_status["gauges"]["inflation"]
        # 30.15 - 30.0 = 0.15 → rounds to 0.1 or 0.2 depending on
        # Python's banker's rounding, but must be exactly 1 decimal place
        assert inflation["delta"] == round(30.15 - 30.0, 1)

    def test_overall_delta_rounding(self, sample_status, previous_status):
        """Overall hawk_score_delta is rounded to 1 decimal place."""
        sample_status["overall"]["hawk_score"] = 52.15
        previous_status["overall"]["hawk_score"] = 48.0
        inject_deltas(sample_status, previous_status)

        delta = sample_status["overall"]["hawk_score_delta"]
        assert delta == round(52.15 - 48.0, 1)

    def test_previous_gauge_missing_value(self, sample_status, previous_status):
        """Previous gauge exists but has no 'value' key — skip delta."""
        del previous_status["gauges"]["inflation"]["value"]
        inject_deltas(sample_status, previous_status)

        inflation = sample_status["gauges"]["inflation"]
        assert "delta" not in inflation
        assert "previous_value" not in inflation
