"""
Unit tests for pipeline.ingest.asx_futures_scraper — ASX futures ingestion.

Patches create_session at: pipeline.ingest.asx_futures_scraper.create_session
Patches datetime at: pipeline.ingest.asx_futures_scraper.datetime
"""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import requests.exceptions

import pipeline.config
import pipeline.ingest.asx_futures_scraper as asx_mod
from pipeline.ingest.asx_futures_scraper import (
    _check_staleness,
    _derive_probabilities,
    _find_meeting_for_contract,
    _get_current_cash_rate,
    _get_rba_meeting_dates,
    fetch_and_save,
    scrape_asx_futures,
)

PATCH_TARGET = "pipeline.ingest.asx_futures_scraper.create_session"


def _make_mock_session(responses):
    """Build a MagicMock session from response specs."""
    mock_session = MagicMock()
    mock_responses = []
    for spec in responses:
        resp = MagicMock()
        resp.status_code = spec.get("status_code", 200)
        resp.text = spec.get("text", "")
        resp.content = spec.get("content", b"")
        resp.json.return_value = spec.get("json", {})
        resp.headers = spec.get("headers", {})
        if resp.status_code == 200:
            resp.raise_for_status.return_value = None
        else:
            resp.raise_for_status.side_effect = (
                requests.exceptions.HTTPError(f"{resp.status_code}")
            )
        mock_responses.append(resp)
    mock_session.get.side_effect = mock_responses
    return mock_session


class MockDatetime(datetime):
    """datetime replacement that freezes now() but delegates everything else."""

    _fixed_now = datetime(2026, 2, 25, 10, 0, 0)

    @classmethod
    def now(cls, tz=None):
        return cls._fixed_now

    @classmethod
    def strptime(cls, date_string, fmt):
        return datetime.strptime(date_string, fmt)


# ---------------------------------------------------------------------------
# Tests for _get_current_cash_rate
# ---------------------------------------------------------------------------


class TestGetCurrentCashRate:
    """Tests for _get_current_cash_rate()."""

    def test_reads_from_csv(self):
        """Write rba_cash_rate.csv to tmp_path and verify rate read."""
        csv_path = pipeline.config.DATA_DIR / "rba_cash_rate.csv"
        df = pd.DataFrame({
            "date": ["2025-01-01", "2025-02-04"],
            "value": [4.35, 4.10],
        })
        df.to_csv(csv_path, index=False)
        rate = _get_current_cash_rate()
        assert rate == 4.10  # Last row's value

    def test_missing_csv_returns_fallback(self):
        """When CSV doesn't exist, returns 4.35 fallback."""
        rate = _get_current_cash_rate()
        assert rate == 4.35


# ---------------------------------------------------------------------------
# Tests for _get_rba_meeting_dates
# ---------------------------------------------------------------------------


class TestGetRbaMeetingDates:
    """Tests for _get_rba_meeting_dates()."""

    def test_happy_path(self, monkeypatch, tmp_path):
        """Test the real function code path by providing meetings.json."""
        meetings_data = {
            "meetings_2026": [
                {"date": "2026-02-18T00:00:00+11:00"},
                {"date": "2026-04-01T00:00:00+11:00"},
            ]
        }
        meetings_file = tmp_path / "meetings.json"
        meetings_file.write_text(json.dumps(meetings_data))
        # Patch the open call to use our tmp_path file
        real_open = open

        def patched_open(path, *args, **kwargs):
            if "meetings.json" in str(path):
                return real_open(meetings_file, *args, **kwargs)
            return real_open(path, *args, **kwargs)

        with patch("builtins.open", side_effect=patched_open):
            result = _get_rba_meeting_dates()
        assert result == ["2026-02-18", "2026-04-01"]

    def test_missing_file_returns_empty_list(self, monkeypatch):
        """When meetings.json doesn't exist, returns empty list."""
        with patch("builtins.open", side_effect=FileNotFoundError):
            result = _get_rba_meeting_dates()
        assert result == []


# ---------------------------------------------------------------------------
# Tests for _find_meeting_for_contract
# ---------------------------------------------------------------------------


class TestFindMeetingForContract:
    """Tests for _find_meeting_for_contract()."""

    def test_same_month_match(self):
        meetings = ["2026-02-18", "2026-03-18", "2026-04-01"]
        result = _find_meeting_for_contract("2026-03-31", meetings)
        assert result == "2026-03-18"

    def test_nearest_future_meeting(self):
        meetings = ["2026-02-18", "2026-05-20"]
        result = _find_meeting_for_contract("2026-04-30", meetings)
        assert result == "2026-05-20"

    def test_no_suitable_meeting(self):
        meetings = ["2026-02-18"]
        result = _find_meeting_for_contract("2026-12-31", meetings)
        assert result is None

    def test_empty_meeting_list(self):
        result = _find_meeting_for_contract("2026-03-31", [])
        assert result is None


# ---------------------------------------------------------------------------
# Tests for _derive_probabilities
# ---------------------------------------------------------------------------


class TestDeriveProbabilities:
    """Tests for _derive_probabilities()."""

    def test_implied_cut(self):
        change_bp, prob_cut, prob_hold, prob_hike = _derive_probabilities(3.60, 3.85)
        assert change_bp < 0
        assert prob_cut > 0
        assert prob_hike == 0
        assert prob_cut + prob_hold + prob_hike == 100

    def test_implied_hike(self):
        change_bp, prob_cut, prob_hold, prob_hike = _derive_probabilities(4.20, 3.85)
        assert change_bp > 0
        assert prob_hike > 0
        assert prob_cut == 0
        assert prob_cut + prob_hold + prob_hike == 100

    def test_hold_within_deadband(self):
        change_bp, prob_cut, prob_hold, prob_hike = _derive_probabilities(3.84, 3.85)
        assert prob_hold == 100
        assert prob_cut == 0
        assert prob_hike == 0

    @pytest.mark.parametrize(
        "implied, current",
        [(3.00, 3.85), (3.50, 3.85), (4.10, 3.85), (4.50, 3.85), (3.85, 3.85)],
    )
    def test_probabilities_sum_to_100(self, implied, current):
        _, prob_cut, prob_hold, prob_hike = _derive_probabilities(implied, current)
        assert prob_cut + prob_hold + prob_hike == 100

    def test_max_100_percent_cut(self):
        """Large implied cut (>25bp) should cap at 100%."""
        _, prob_cut, prob_hold, prob_hike = _derive_probabilities(3.00, 4.00)
        assert prob_cut == 100
        assert prob_hold == 0


# ---------------------------------------------------------------------------
# Tests for scrape_asx_futures
# ---------------------------------------------------------------------------


class TestScrapeAsxFutures:
    """Tests for scrape_asx_futures()."""

    def test_happy_path(self, fixture_asx_response, monkeypatch):
        mock_session = _make_mock_session([
            {"status_code": 200, "json": fixture_asx_response}
        ])
        # Write cash rate CSV so _get_current_cash_rate works
        csv_path = pipeline.config.DATA_DIR / "rba_cash_rate.csv"
        pd.DataFrame({"date": ["2025-02-04"], "value": [4.10]}).to_csv(
            csv_path, index=False
        )
        # Mock meetings.json via patching _get_rba_meeting_dates
        monkeypatch.setattr(
            asx_mod, "_get_rba_meeting_dates",
            lambda: ["2026-03-18", "2026-04-01"],
        )
        monkeypatch.setattr(asx_mod, "datetime", MockDatetime)

        with patch(PATCH_TARGET, return_value=mock_session):
            df = scrape_asx_futures()

        assert len(df) == 2
        expected_cols = [
            "date", "meeting_date", "implied_rate", "change_bp",
            "probability_cut", "probability_hold", "probability_hike",
        ]
        assert list(df.columns) == expected_cols
        assert (df["date"] == "2026-02-25").all()

    def test_empty_items(self, fixture_asx_response_empty, monkeypatch):
        mock_session = _make_mock_session([
            {"status_code": 200, "json": fixture_asx_response_empty}
        ])
        monkeypatch.setattr(asx_mod, "datetime", MockDatetime)
        with patch(PATCH_TARGET, return_value=mock_session):
            df = scrape_asx_futures()
        assert df.empty

    def test_http_error(self, monkeypatch):
        mock_session = _make_mock_session([
            {"status_code": 500, "text": "error"}
        ])
        monkeypatch.setattr(asx_mod, "datetime", MockDatetime)
        with patch(PATCH_TARGET, return_value=mock_session):
            with pytest.raises(requests.exceptions.HTTPError):
                scrape_asx_futures()

    def test_skips_invalid_rate(self, monkeypatch):
        """Item with settlement=200 gives implied rate -100 (out of 0-15)."""
        bad_response = {
            "data": {
                "items": [
                    {
                        "dateExpiry": "2026-03-31",
                        "pricePreviousSettlement": 200,
                        "symbol": "IB2603",
                    }
                ]
            }
        }
        mock_session = _make_mock_session([
            {"status_code": 200, "json": bad_response}
        ])
        csv_path = pipeline.config.DATA_DIR / "rba_cash_rate.csv"
        pd.DataFrame({"date": ["2025-02-04"], "value": [4.10]}).to_csv(
            csv_path, index=False
        )
        monkeypatch.setattr(
            asx_mod, "_get_rba_meeting_dates", lambda: ["2026-03-18"]
        )
        monkeypatch.setattr(asx_mod, "datetime", MockDatetime)
        with patch(PATCH_TARGET, return_value=mock_session):
            df = scrape_asx_futures()
        assert df.empty

    def test_skips_missing_expiry(self, monkeypatch):
        no_expiry = {
            "data": {
                "items": [
                    {
                        "pricePreviousSettlement": 96.09,
                        "symbol": "IB2603",
                    }
                ]
            }
        }
        mock_session = _make_mock_session([
            {"status_code": 200, "json": no_expiry}
        ])
        csv_path = pipeline.config.DATA_DIR / "rba_cash_rate.csv"
        pd.DataFrame({"date": ["2025-02-04"], "value": [4.10]}).to_csv(
            csv_path, index=False
        )
        monkeypatch.setattr(
            asx_mod, "_get_rba_meeting_dates", lambda: ["2026-03-18"]
        )
        monkeypatch.setattr(asx_mod, "datetime", MockDatetime)
        with patch(PATCH_TARGET, return_value=mock_session):
            df = scrape_asx_futures()
        assert df.empty

    def test_no_meeting_uses_expiry_as_proxy(self, monkeypatch):
        """When no meeting matches, contract expiry is used as meeting_date."""
        response = {
            "data": {
                "items": [
                    {
                        "dateExpiry": "2027-12-31",
                        "pricePreviousSettlement": 96.00,
                        "symbol": "IB2712",
                    }
                ]
            }
        }
        mock_session = _make_mock_session([
            {"status_code": 200, "json": response}
        ])
        csv_path = pipeline.config.DATA_DIR / "rba_cash_rate.csv"
        pd.DataFrame({"date": ["2025-02-04"], "value": [4.10]}).to_csv(
            csv_path, index=False
        )
        # No meetings at all
        monkeypatch.setattr(asx_mod, "_get_rba_meeting_dates", lambda: [])
        monkeypatch.setattr(asx_mod, "datetime", MockDatetime)
        with patch(PATCH_TARGET, return_value=mock_session):
            df = scrape_asx_futures()
        assert len(df) == 1
        assert df["meeting_date"].iloc[0] == "2027-12-31"


# ---------------------------------------------------------------------------
# Tests for _check_staleness
# ---------------------------------------------------------------------------


class TestCheckStaleness:
    """Tests for _check_staleness()."""

    def test_fresh_data(self, caplog, monkeypatch):
        monkeypatch.setattr(asx_mod, "datetime", MockDatetime)
        csv_path = pipeline.config.DATA_DIR / "asx_futures.csv"
        pd.DataFrame({"date": ["2026-02-25"]}).to_csv(csv_path, index=False)
        with caplog.at_level("WARNING"):
            _check_staleness(csv_path)
        assert "days old" not in caplog.text

    def test_14_day_warning(self, caplog, monkeypatch):
        monkeypatch.setattr(asx_mod, "datetime", MockDatetime)
        csv_path = pipeline.config.DATA_DIR / "asx_futures.csv"
        pd.DataFrame({"date": ["2026-02-10"]}).to_csv(csv_path, index=False)
        with caplog.at_level("WARNING"):
            _check_staleness(csv_path)
        assert "days old" in caplog.text

    def test_30_day_error(self, caplog, monkeypatch):
        monkeypatch.setattr(asx_mod, "datetime", MockDatetime)
        csv_path = pipeline.config.DATA_DIR / "asx_futures.csv"
        pd.DataFrame({"date": ["2026-01-20"]}).to_csv(csv_path, index=False)
        with caplog.at_level("ERROR"):
            _check_staleness(csv_path)
        assert "days old" in caplog.text

    def test_missing_csv(self, caplog):
        csv_path = pipeline.config.DATA_DIR / "nonexistent.csv"
        with caplog.at_level("WARNING"):
            _check_staleness(csv_path)
        assert "Could not check" in caplog.text


# ---------------------------------------------------------------------------
# Tests for fetch_and_save
# ---------------------------------------------------------------------------


class TestFetchAndSave:
    """Tests for fetch_and_save()."""

    def test_success(self, monkeypatch):
        df = pd.DataFrame({
            "date": ["2026-02-25"],
            "meeting_date": ["2026-03-18"],
            "implied_rate": [3.91],
            "change_bp": [-19.0],
            "probability_cut": [76],
            "probability_hold": [24],
            "probability_hike": [0],
        })
        monkeypatch.setattr(asx_mod, "scrape_asx_futures", lambda: df)
        monkeypatch.setattr(asx_mod, "datetime", MockDatetime)
        result = fetch_and_save()
        assert result["status"] == "success"
        assert result["rows"] >= 1

    def test_empty_scrape(self, monkeypatch):
        monkeypatch.setattr(
            asx_mod, "scrape_asx_futures", lambda: pd.DataFrame()
        )
        result = fetch_and_save()
        assert result["status"] == "failed"

    def test_exception_caught(self, monkeypatch):
        def raise_error():
            raise RuntimeError("test error")
        monkeypatch.setattr(asx_mod, "scrape_asx_futures", raise_error)
        result = fetch_and_save()
        assert result["status"] == "failed"
        assert "test error" in result["error"]

    def test_existing_csv_unreadable(self, monkeypatch):
        """Existing CSV is corrupt -> overwrite with new data."""
        monkeypatch.setattr(asx_mod, "datetime", MockDatetime)
        csv_path = pipeline.config.DATA_DIR / "asx_futures.csv"
        # Write corrupt data that will cause ParserError
        csv_path.write_text("corrupt\x00garbage\x00data\nnot,valid,csv")

        new_df = pd.DataFrame({
            "date": ["2026-02-25"],
            "meeting_date": ["2026-03-18"],
            "implied_rate": [3.91],
            "change_bp": [-19.0],
            "probability_cut": [76],
            "probability_hold": [24],
            "probability_hike": [0],
        })
        monkeypatch.setattr(asx_mod, "scrape_asx_futures", lambda: new_df)
        result = fetch_and_save()
        assert result["status"] == "success"

    def test_deduplicates(self, monkeypatch):
        """Existing CSV + new scrape with overlapping rows -> deduplication."""
        monkeypatch.setattr(asx_mod, "datetime", MockDatetime)
        # Write existing CSV
        csv_path = pipeline.config.DATA_DIR / "asx_futures.csv"
        existing = pd.DataFrame({
            "date": ["2026-02-24"],
            "meeting_date": ["2026-03-18"],
            "implied_rate": [3.90],
            "change_bp": [-20.0],
            "probability_cut": [80],
            "probability_hold": [20],
            "probability_hike": [0],
        })
        existing.to_csv(csv_path, index=False)

        # New scrape with same meeting_date but different date
        new_df = pd.DataFrame({
            "date": ["2026-02-25"],
            "meeting_date": ["2026-03-18"],
            "implied_rate": [3.91],
            "change_bp": [-19.0],
            "probability_cut": [76],
            "probability_hold": [24],
            "probability_hike": [0],
        })
        monkeypatch.setattr(asx_mod, "scrape_asx_futures", lambda: new_df)
        result = fetch_and_save()
        assert result["status"] == "success"
        # Should have 2 rows (different dates for same meeting)
        final_df = pd.read_csv(csv_path)
        assert len(final_df) == 2
