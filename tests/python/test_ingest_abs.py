"""
Unit tests for pipeline.ingest.abs_data — ABS data ingestion.

Establishes the _make_mock_session pattern used by all ingest test modules.
Patches create_session at the import site: pipeline.ingest.abs_data.create_session.
"""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import requests.exceptions

from pipeline.config import ABS_CONFIG, DEFAULT_TIMEOUT, TIMEOUT_OVERRIDES
from pipeline.ingest.abs_data import (
    FETCHERS,
    _parse_abs_date,
    fetch_abs_series,
    fetch_and_save,
    fetch_building_approvals,
    fetch_cpi,
)

# ---------------------------------------------------------------------------
# Helper: mock session builder (pattern used across all ingest test modules)
# ---------------------------------------------------------------------------


def _make_mock_session(responses):
    """
    Build a MagicMock session from a list of response specs.

    Each spec is a dict with optional keys:
        status_code (int), text (str), content (bytes),
        json (dict), headers (dict).

    session.get() side_effect returns responses in order.
    """
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


# ---------------------------------------------------------------------------
# Tests for _parse_abs_date
# ---------------------------------------------------------------------------


class TestParseAbsDate:
    """Tests for the private _parse_abs_date helper."""

    def test_monthly_format(self):
        assert _parse_abs_date("2024-01") == "2024-01-01"

    def test_monthly_format_december(self):
        assert _parse_abs_date("2024-12") == "2024-12-01"

    @pytest.mark.parametrize(
        "quarter, expected_month",
        [("Q1", "01"), ("Q2", "04"), ("Q3", "07"), ("Q4", "10")],
    )
    def test_quarterly_format(self, quarter, expected_month):
        result = _parse_abs_date(f"2024-{quarter}")
        assert result == f"2024-{expected_month}-01"

    def test_iso_format_passthrough(self):
        result = _parse_abs_date("2024-01-15")
        assert result == "2024-01-15"

    def test_strips_whitespace(self):
        assert _parse_abs_date("  2024-01  ") == "2024-01-01"


# ---------------------------------------------------------------------------
# Tests for fetch_abs_series
# ---------------------------------------------------------------------------

PATCH_TARGET = "pipeline.ingest.abs_data.create_session"


class TestFetchAbsSeries:
    """Tests for the core fetch_abs_series function."""

    def test_happy_path(self, fixture_abs_response):
        mock_session = _make_mock_session([
            {"status_code": 200, "text": fixture_abs_response}
        ])
        with patch(PATCH_TARGET, return_value=mock_session):
            df = fetch_abs_series("CPI", "all", params={"startPeriod": "2014"})

        assert isinstance(df, pd.DataFrame)
        assert list(df.columns) == ["date", "value", "source", "series_id"]
        assert len(df) == 3
        assert (df["source"] == "ABS").all()
        assert df["series_id"].iloc[0] == "CPI/all"

    def test_with_filters(self, fixture_abs_response):
        mock_session = _make_mock_session([
            {"status_code": 200, "text": fixture_abs_response}
        ])
        with patch(PATCH_TARGET, return_value=mock_session):
            df = fetch_abs_series(
                "CPI", "all",
                filters={"MEASURE": "1"},
            )

        # The fixture has MEASURE column starting with "1: Index Numbers"
        # so all 3 rows should match the filter
        assert len(df) == 3

    @pytest.mark.parametrize("status_code", [400, 404, 500])
    def test_http_error(self, status_code):
        mock_session = _make_mock_session([
            {"status_code": status_code, "text": "error"}
        ])
        with patch(PATCH_TARGET, return_value=mock_session):
            with pytest.raises(Exception, match="ABS API error"):
                fetch_abs_series("CPI", "all")

    def test_empty_response_body(self):
        mock_session = _make_mock_session([
            {"status_code": 200, "text": ""}
        ])
        with patch(PATCH_TARGET, return_value=mock_session):
            with pytest.raises(Exception, match="Empty response body"):
                fetch_abs_series("CPI", "all")

    def test_short_response(self):
        mock_session = _make_mock_session([
            {"status_code": 200, "text": "short"}
        ])
        with patch(PATCH_TARGET, return_value=mock_session):
            with pytest.raises(Exception, match="Response too short"):
                fetch_abs_series("CPI", "all")

    def test_csv_parse_error(self):
        # Construct text that's >100 chars but will fail CSV parsing
        bad_csv = "a" * 101 + '\n"unclosed'
        mock_session = _make_mock_session([
            {"status_code": 200, "text": bad_csv}
        ])
        with patch(PATCH_TARGET, return_value=mock_session):
            with pytest.raises(Exception, match="Failed to parse CSV"):
                fetch_abs_series("CPI", "all")

    def test_no_data_rows_short_response(self, fixture_abs_response_empty):
        """Empty fixture is <100 bytes, so hits 'too short' guard first."""
        mock_session = _make_mock_session([
            {"status_code": 200, "text": fixture_abs_response_empty}
        ])
        with patch(PATCH_TARGET, return_value=mock_session):
            with pytest.raises(Exception, match="Response too short"):
                fetch_abs_series("CPI", "all")

    def test_no_data_rows_empty_dataframe(self):
        """CSV with header but no matching data after filtering -> 'No data'."""
        # Long enough to pass the 100-byte check, but zero data rows
        csv_text = (
            "DATAFLOW,TIME_PERIOD,OBS_VALUE" + " " * 80 + "\n"
        )
        mock_session = _make_mock_session([
            {"status_code": 200, "text": csv_text}
        ])
        with patch(PATCH_TARGET, return_value=mock_session):
            with pytest.raises(Exception, match="No data returned"):
                fetch_abs_series("CPI", "all")

    def test_custom_timeout(self, fixture_abs_response):
        mock_session = _make_mock_session([
            {"status_code": 200, "text": fixture_abs_response}
        ])
        with patch(PATCH_TARGET, return_value=mock_session):
            fetch_abs_series("CPI", "all", timeout=60)
        # Verify timeout was passed to session.get
        _, kwargs = mock_session.get.call_args
        assert kwargs["timeout"] == 60

    def test_default_timeout(self, fixture_abs_response):
        mock_session = _make_mock_session([
            {"status_code": 200, "text": fixture_abs_response}
        ])
        with patch(PATCH_TARGET, return_value=mock_session):
            fetch_abs_series("CPI", "all")
        _, kwargs = mock_session.get.call_args
        assert kwargs["timeout"] == DEFAULT_TIMEOUT

    def test_dates_parsed_quarterly(self):
        csv_text = (
            "DATAFLOW,TIME_PERIOD,OBS_VALUE\n"
            "ABS:CPI,2024-Q1,136.8\n"
            "ABS:CPI,2024-Q2,137.4\n"
            "ABS:CPI,2024-Q3,138.1\n"
            "ABS:CPI,2024-Q4,139.0\n"
        )
        mock_session = _make_mock_session([
            {"status_code": 200, "text": csv_text}
        ])
        with patch(PATCH_TARGET, return_value=mock_session):
            df = fetch_abs_series("CPI", "all")
        dates = df["date"].tolist()
        assert dates == ["2024-01-01", "2024-04-01", "2024-07-01", "2024-10-01"]

    def test_drops_nan_values(self):
        # Pad header to ensure >100 bytes total
        csv_text = (
            "DATAFLOW,TIME_PERIOD,OBS_VALUE\n"
            "ABS:CPI,2024-01,136.8\n"
            "ABS:CPI,2024-02,\n"
            "ABS:CPI,2024-03,138.1\n"
            "ABS:CPI,2024-04,139.0\n"
        )
        mock_session = _make_mock_session([
            {"status_code": 200, "text": csv_text}
        ])
        with patch(PATCH_TARGET, return_value=mock_session):
            df = fetch_abs_series("CPI", "all")
        assert len(df) == 3  # Row with empty value dropped


# ---------------------------------------------------------------------------
# Tests for individual fetcher wrappers
# ---------------------------------------------------------------------------


class TestFetchers:
    """Tests for thin fetcher wrappers (fetch_cpi, fetch_building_approvals, etc.)."""

    def test_fetch_cpi_uses_config(self, fixture_abs_response):
        mock_session = _make_mock_session([
            {"status_code": 200, "text": fixture_abs_response}
        ])
        with patch(PATCH_TARGET, return_value=mock_session):
            df = fetch_cpi()
        assert len(df) > 0

    def test_fetch_building_approvals_uses_timeout_override(
        self, fixture_abs_response
    ):
        mock_session = _make_mock_session([
            {"status_code": 200, "text": fixture_abs_response}
        ])
        with patch(PATCH_TARGET, return_value=mock_session):
            fetch_building_approvals()
        _, kwargs = mock_session.get.call_args
        expected_timeout = TIMEOUT_OVERRIDES.get(
            "building_approvals", DEFAULT_TIMEOUT
        )
        assert kwargs["timeout"] == expected_timeout

    def test_fetchers_registry_has_all_series(self):
        expected = {
            "cpi", "employment", "household_spending",
            "wage_price_index", "building_approvals", "rppi",
        }
        assert set(FETCHERS.keys()) == expected

    def test_fetchers_registry_output_files_match_config(self):
        for name, (_, output_file) in FETCHERS.items():
            assert output_file == ABS_CONFIG[name]["output_file"]


# ---------------------------------------------------------------------------
# Tests for fetch_and_save
# ---------------------------------------------------------------------------


class TestFetchAndSave:
    """Tests for fetch_and_save orchestration function."""

    def test_single_series(self, fixture_abs_response):
        mock_session = _make_mock_session([
            {"status_code": 200, "text": fixture_abs_response}
        ])
        with patch(PATCH_TARGET, return_value=mock_session):
            results = fetch_and_save("cpi")
        assert "cpi" in results
        assert results["cpi"] > 0

    def test_unknown_series(self):
        with pytest.raises(ValueError, match="Unknown series"):
            fetch_and_save("nonexistent")

    def test_all_series(self, fixture_abs_response):
        # Each of the 6 fetchers calls create_session once -> 6 calls total.
        # The CPI fixture data has specific column values (INDEX=10001, etc.)
        # so series with incompatible filters (e.g., WPI with INDEX=THRPEB)
        # will match 0 rows after filtering and raise Exception -> caught as 0.
        mock_session = _make_mock_session(
            [{"status_code": 200, "text": fixture_abs_response}] * 6
        )
        with patch(PATCH_TARGET, return_value=mock_session):
            results = fetch_and_save()
        assert len(results) == 6
        # At minimum, series without filters should succeed
        assert results["employment"] > 0
        assert results["household_spending"] > 0
        assert results["rppi"] > 0

    def test_chunked_encoding_error(self):
        mock_session = MagicMock()
        mock_session.get.side_effect = (
            requests.exceptions.ChunkedEncodingError("transfer interrupted")
        )
        with patch(PATCH_TARGET, return_value=mock_session):
            results = fetch_and_save()
        # All series should have 0 rows (error caught)
        for count in results.values():
            assert count == 0

    def test_timeout_error(self):
        mock_session = MagicMock()
        mock_session.get.side_effect = (
            requests.exceptions.Timeout("timed out")
        )
        with patch(PATCH_TARGET, return_value=mock_session):
            results = fetch_and_save()
        for count in results.values():
            assert count == 0

    def test_connection_error(self):
        mock_session = MagicMock()
        mock_session.get.side_effect = (
            requests.exceptions.ConnectionError("connection failed")
        )
        with patch(PATCH_TARGET, return_value=mock_session):
            results = fetch_and_save()
        for count in results.values():
            assert count == 0

    def test_generic_exception(self):
        mock_session = MagicMock()
        mock_session.get.side_effect = RuntimeError("unexpected")
        with patch(PATCH_TARGET, return_value=mock_session):
            results = fetch_and_save()
        for count in results.values():
            assert count == 0
