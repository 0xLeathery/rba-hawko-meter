"""
Unit tests for pipeline.ingest.rba_data — RBA cash rate ingestion.

Patches create_session at: pipeline.ingest.rba_data.create_session
"""

from unittest.mock import MagicMock, patch

import pytest
import requests.exceptions

from pipeline.ingest.rba_data import fetch_and_save, fetch_cash_rate

PATCH_TARGET = "pipeline.ingest.rba_data.create_session"


def _make_mock_session(responses):
    """Build a MagicMock session from response specs."""
    mock_session = MagicMock()
    mock_responses = []
    for spec in responses:
        resp = MagicMock()
        resp.status_code = spec.get("status_code", 200)
        resp.text = spec.get("text", "")
        resp.content = spec.get("content", b"")
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


class TestFetchCashRate:
    """Tests for fetch_cash_rate()."""

    def test_happy_path(self, fixture_rba_response):
        mock_session = _make_mock_session([
            {"status_code": 200, "text": fixture_rba_response}
        ])
        with patch(PATCH_TARGET, return_value=mock_session):
            df = fetch_cash_rate()

        assert list(df.columns) == ["date", "value", "source"]
        assert (df["source"] == "RBA").all()
        assert len(df) == 4  # 4 data rows in fixture
        # Verify dates are ISO format
        for d in df["date"]:
            assert len(d) == 10  # YYYY-MM-DD
            assert d[4] == "-" and d[7] == "-"

    def test_finds_header_row(self, fixture_rba_response):
        """Verify that metadata rows above 'Series ID' row are skipped."""
        mock_session = _make_mock_session([
            {"status_code": 200, "text": fixture_rba_response}
        ])
        with patch(PATCH_TARGET, return_value=mock_session):
            df = fetch_cash_rate()
        # If header detection works, first date should be a valid date
        # not metadata like "Title" or "Description"
        assert df["date"].iloc[0].startswith("20")

    def test_http_error(self):
        mock_session = _make_mock_session([
            {"status_code": 500, "text": "server error"}
        ])
        with patch(PATCH_TARGET, return_value=mock_session):
            with pytest.raises(requests.exceptions.HTTPError):
                fetch_cash_rate()

    def test_empty_csv(self, fixture_rba_response_empty):
        """Empty RBA CSV (headers only, no data) returns empty DataFrame."""
        mock_session = _make_mock_session([
            {"status_code": 200, "text": fixture_rba_response_empty}
        ])
        with patch(PATCH_TARGET, return_value=mock_session):
            df = fetch_cash_rate()
        assert len(df) == 0

    def test_value_range_extraction(self):
        """Verify regex extracts last number from range like '17.00 to 17.50'."""
        rba_csv = (
            "Row,Col1,Col2,Col3\n"
            "Series ID,X,Y,Z\n"
            "Title,Cash Rate Target,New Cash Rate Target,Votes\n"
            "01-Jan-1990,17.00 to 17.50,17.50,\n"
        )
        mock_session = _make_mock_session([
            {"status_code": 200, "text": rba_csv}
        ])
        with patch(PATCH_TARGET, return_value=mock_session):
            df = fetch_cash_rate()
        assert len(df) == 1
        assert df["value"].iloc[0] == 17.50

    def test_values_are_numeric(self, fixture_rba_response):
        mock_session = _make_mock_session([
            {"status_code": 200, "text": fixture_rba_response}
        ])
        with patch(PATCH_TARGET, return_value=mock_session):
            df = fetch_cash_rate()
        # All values should be float
        for v in df["value"]:
            assert isinstance(v, float)

    def test_dayfirst_date_parsing(self):
        """Verify Australian date format (DD-Mon-YYYY) is parsed correctly."""
        rba_csv = (
            "Row,Col1,Col2,Col3\n"
            "Series ID,X,Y,Z\n"
            "Title,Cash Rate Target,New Cash Rate Target,Votes\n"
            "05-Jun-2019,1.25,1.25,\n"
        )
        mock_session = _make_mock_session([
            {"status_code": 200, "text": rba_csv}
        ])
        with patch(PATCH_TARGET, return_value=mock_session):
            df = fetch_cash_rate()
        assert df["date"].iloc[0] == "2019-06-05"


class TestFetchAndSave:
    """Tests for fetch_and_save()."""

    def test_happy_path(self, fixture_rba_response, tmp_path):
        mock_session = _make_mock_session([
            {"status_code": 200, "text": fixture_rba_response}
        ])
        with patch(PATCH_TARGET, return_value=mock_session):
            row_count = fetch_and_save()
        assert row_count > 0
        # Verify CSV was created at DATA_DIR path (tmp_path via autouse)
        import pipeline.config
        csv_path = pipeline.config.DATA_DIR / "rba_cash_rate.csv"
        assert csv_path.exists()

    def test_returns_row_count(self, fixture_rba_response):
        mock_session = _make_mock_session([
            {"status_code": 200, "text": fixture_rba_response}
        ])
        with patch(PATCH_TARGET, return_value=mock_session):
            row_count = fetch_and_save()
        assert row_count == 4  # 4 data rows in fixture
