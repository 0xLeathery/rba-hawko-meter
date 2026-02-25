"""
Unit tests for pipeline.ingest.corelogic_scraper — Cotality HVI PDF scraper.

Patches create_session at: pipeline.ingest.corelogic_scraper.create_session
Patches datetime at: pipeline.ingest.corelogic_scraper.datetime
Patches pdfplumber at: pipeline.ingest.corelogic_scraper.pdfplumber
"""

import io
import sys
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import requests.exceptions

import pipeline.config
import pipeline.ingest.corelogic_scraper as cl_mod
from pipeline.ingest.corelogic_scraper import (
    _current_month_already_scraped,
    download_cotality_pdf,
    extract_cotality_yoy,
    fetch_and_save,
    get_candidate_urls,
    scrape_cotality,
)

PATCH_TARGET = "pipeline.ingest.corelogic_scraper.create_session"


def _make_mock_session(responses):
    """Build a MagicMock session from response specs."""
    mock_session = MagicMock()
    mock_responses = []
    for spec in responses:
        resp = MagicMock()
        resp.status_code = spec.get("status_code", 200)
        resp.text = spec.get("text", "")
        resp.content = spec.get("content", b"pdf-bytes")
        resp.headers = spec.get("headers", {"content-type": "application/pdf"})
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
    """datetime replacement that freezes now() to 2026-02-25."""

    _fixed_now = datetime(2026, 2, 25, 10, 0, 0)

    @classmethod
    def now(cls, tz=None):
        return cls._fixed_now

    @classmethod
    def strptime(cls, date_string, fmt):
        return datetime.strptime(date_string, fmt)


def _make_mock_pdfplumber(page_texts):
    """
    Build a mock pdfplumber module and inject it into sys.modules.

    pdfplumber is imported lazily inside extract_cotality_yoy(), so we
    inject the mock into sys.modules before calling the function.

    Args:
        page_texts: list of strings, one per page's extract_text() return.

    Returns:
        Mock pdfplumber module (also injected into sys.modules).
    """
    mock_pdf = MagicMock()
    mock_pages = []
    for text in page_texts:
        page = MagicMock()
        page.extract_text.return_value = text
        mock_pages.append(page)
    mock_pdf.pages = mock_pages
    mock_pdfplumber = MagicMock()
    mock_pdfplumber.open.return_value.__enter__ = MagicMock(return_value=mock_pdf)
    mock_pdfplumber.open.return_value.__exit__ = MagicMock(return_value=False)
    return mock_pdfplumber


@pytest.fixture(autouse=True)
def _inject_mock_pdfplumber(monkeypatch):
    """Ensure pdfplumber in sys.modules doesn't leak between tests."""
    yield


# ---------------------------------------------------------------------------
# Tests for get_candidate_urls
# ---------------------------------------------------------------------------


class TestGetCandidateUrls:
    """Tests for get_candidate_urls()."""

    def test_returns_4_urls(self):
        urls = get_candidate_urls(2026, 2)
        assert len(urls) == 4
        # Check URLs contain the month abbreviation or full name
        assert any("Feb" in u for u in urls)
        assert any("February" in u for u in urls)

    def test_december(self):
        urls = get_candidate_urls(2025, 12)
        assert any("Dec" in u for u in urls)
        assert any("December" in u for u in urls)


# ---------------------------------------------------------------------------
# Tests for download_cotality_pdf
# ---------------------------------------------------------------------------


class TestDownloadCotalityPdf:
    """Tests for download_cotality_pdf()."""

    def test_found(self):
        mock_session = _make_mock_session([
            {"status_code": 200, "content": b"pdf-data",
             "headers": {"content-type": "application/pdf"}}
        ])
        result = download_cotality_pdf(2026, 2, mock_session)
        assert result == b"pdf-data"

    def test_not_found(self):
        # All 4 candidate URLs return 404
        mock_session = _make_mock_session([
            {"status_code": 404, "headers": {}} for _ in range(4)
        ])
        result = download_cotality_pdf(2026, 2, mock_session)
        assert result is None

    def test_non_pdf_content_type(self):
        """200 response but text/html content-type -> not treated as PDF."""
        mock_session = _make_mock_session([
            {"status_code": 200, "content": b"<html>",
             "headers": {"content-type": "text/html"}}
            for _ in range(4)
        ])
        result = download_cotality_pdf(2026, 2, mock_session)
        assert result is None

    def test_request_exception(self):
        """Session.get raises exception -> returns None after trying all."""
        mock_session = MagicMock()
        mock_session.get.side_effect = ConnectionError("network error")
        result = download_cotality_pdf(2026, 2, mock_session)
        assert result is None


# ---------------------------------------------------------------------------
# Tests for extract_cotality_yoy
# ---------------------------------------------------------------------------


class TestExtractCotalityYoy:
    """Tests for extract_cotality_yoy()."""

    def test_happy_path(self, monkeypatch):
        mock_pdfplumber = _make_mock_pdfplumber(
            ["Australia 0.8% 2.4% 9.4%"]
        )
        monkeypatch.setitem(sys.modules, "pdfplumber", mock_pdfplumber)
        result = extract_cotality_yoy(b"fake-pdf")
        assert result == 9.4

    def test_pattern_not_found(self, monkeypatch):
        mock_pdfplumber = _make_mock_pdfplumber(
            ["No relevant data on this page"]
        )
        monkeypatch.setitem(sys.modules, "pdfplumber", mock_pdfplumber)
        result = extract_cotality_yoy(b"fake-pdf")
        assert result is None

    def test_pdfplumber_import_error(self, monkeypatch):
        """When pdfplumber is not installed, returns None."""
        monkeypatch.delitem(sys.modules, "pdfplumber", raising=False)

        original_import = __import__

        def mock_import(name, *args, **kwargs):
            if name == "pdfplumber":
                raise ImportError("No module named 'pdfplumber'")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            result = extract_cotality_yoy(b"fake-pdf")
        assert result is None

    def test_negative_values(self, monkeypatch):
        mock_pdfplumber = _make_mock_pdfplumber(
            ["Australia -0.3% -1.2% -2.5%"]
        )
        monkeypatch.setitem(sys.modules, "pdfplumber", mock_pdfplumber)
        result = extract_cotality_yoy(b"fake-pdf")
        assert result == -2.5

    def test_found_on_second_page(self, monkeypatch):
        mock_pdfplumber = _make_mock_pdfplumber([
            "Introduction and methodology",
            "Australia 0.5% 1.8% 7.2%",
        ])
        monkeypatch.setitem(sys.modules, "pdfplumber", mock_pdfplumber)
        result = extract_cotality_yoy(b"fake-pdf")
        assert result == 7.2


# ---------------------------------------------------------------------------
# Tests for _current_month_already_scraped
# ---------------------------------------------------------------------------


class TestCurrentMonthAlreadyScraped:
    """Tests for _current_month_already_scraped()."""

    def test_true(self, monkeypatch):
        monkeypatch.setattr(cl_mod, "datetime", MockDatetime)
        output_path = pipeline.config.DATA_DIR / "corelogic_housing.csv"
        df = pd.DataFrame({
            "date": ["2026-02-28"],
            "value": [9.4],
            "source": ["Cotality HVI"],
        })
        df.to_csv(output_path, index=False)
        assert _current_month_already_scraped(output_path) is True

    def test_false_old_data(self, monkeypatch):
        monkeypatch.setattr(cl_mod, "datetime", MockDatetime)
        output_path = pipeline.config.DATA_DIR / "corelogic_housing.csv"
        df = pd.DataFrame({
            "date": ["2026-01-31"],
            "value": [8.0],
            "source": ["Cotality HVI"],
        })
        df.to_csv(output_path, index=False)
        assert _current_month_already_scraped(output_path) is False

    def test_false_no_file(self):
        output_path = pipeline.config.DATA_DIR / "nonexistent.csv"
        assert _current_month_already_scraped(output_path) is False

    def test_false_empty_csv(self):
        output_path = pipeline.config.DATA_DIR / "corelogic_housing.csv"
        pd.DataFrame(columns=["date", "value", "source"]).to_csv(
            output_path, index=False
        )
        assert _current_month_already_scraped(output_path) is False

    def test_false_no_source_column(self, monkeypatch):
        monkeypatch.setattr(cl_mod, "datetime", MockDatetime)
        output_path = pipeline.config.DATA_DIR / "corelogic_housing.csv"
        df = pd.DataFrame({"date": ["2026-02-28"], "value": [9.4]})
        df.to_csv(output_path, index=False)
        assert _current_month_already_scraped(output_path) is False


# ---------------------------------------------------------------------------
# Tests for scrape_cotality
# ---------------------------------------------------------------------------


class TestScrapeCotality:
    """Tests for scrape_cotality()."""

    def test_happy_path(self, monkeypatch):
        monkeypatch.setattr(cl_mod, "datetime", MockDatetime)
        mock_pdfplumber = _make_mock_pdfplumber(
            ["Australia 0.8% 2.4% 9.4%"]
        )
        monkeypatch.setitem(sys.modules, "pdfplumber", mock_pdfplumber)
        # Mock session: first candidate URL returns PDF
        mock_session = _make_mock_session([
            {"status_code": 200, "content": b"pdf",
             "headers": {"content-type": "application/pdf"}}
        ])
        with patch(PATCH_TARGET, return_value=mock_session):
            df = scrape_cotality()

        assert len(df) == 1
        assert df["value"].iloc[0] == 9.4
        assert df["source"].iloc[0] == "Cotality HVI"

    def test_already_scraped(self, monkeypatch):
        monkeypatch.setattr(cl_mod, "datetime", MockDatetime)
        output_path = pipeline.config.DATA_DIR / "corelogic_housing.csv"
        pd.DataFrame({
            "date": ["2026-02-28"],
            "value": [9.4],
            "source": ["Cotality HVI"],
        }).to_csv(output_path, index=False)

        mock_session = _make_mock_session([])
        with patch(PATCH_TARGET, return_value=mock_session):
            df = scrape_cotality()
        assert df.empty

    def test_no_pdf_found(self, monkeypatch):
        monkeypatch.setattr(cl_mod, "datetime", MockDatetime)
        # All candidate URLs for both months return 404
        mock_session = _make_mock_session([
            {"status_code": 404, "headers": {}} for _ in range(8)
        ])
        with patch(PATCH_TARGET, return_value=mock_session):
            df = scrape_cotality()
        assert df.empty

    def test_tries_previous_month(self, monkeypatch):
        """Current month PDF not found, previous month PDF found."""
        monkeypatch.setattr(cl_mod, "datetime", MockDatetime)
        mock_pdfplumber = _make_mock_pdfplumber(
            ["Australia 0.5% 1.8% 8.0%"]
        )
        monkeypatch.setitem(sys.modules, "pdfplumber", mock_pdfplumber)

        # First 4 URLs (current month) return 404
        # 5th URL (prev month) returns PDF
        responses = [
            {"status_code": 404, "headers": {}} for _ in range(4)
        ] + [
            {"status_code": 200, "content": b"pdf",
             "headers": {"content-type": "application/pdf"}}
        ]
        mock_session = _make_mock_session(responses)
        with patch(PATCH_TARGET, return_value=mock_session):
            df = scrape_cotality()

        assert len(df) == 1
        assert df["value"].iloc[0] == 8.0
        # Date should be end of January 2026 (previous month)
        assert df["date"].iloc[0] == "2026-01-31"

    def test_pdf_found_but_no_pattern(self, monkeypatch):
        """PDF downloaded but extract_cotality_yoy returns None."""
        monkeypatch.setattr(cl_mod, "datetime", MockDatetime)
        mock_pdfplumber = _make_mock_pdfplumber(
            ["No relevant data here"]
        )
        monkeypatch.setitem(sys.modules, "pdfplumber", mock_pdfplumber)
        # All 8 candidates return PDF (both months)
        mock_session = _make_mock_session([
            {"status_code": 200, "content": b"pdf",
             "headers": {"content-type": "application/pdf"}}
            for _ in range(8)
        ])
        with patch(PATCH_TARGET, return_value=mock_session):
            df = scrape_cotality()
        assert df.empty


# ---------------------------------------------------------------------------
# Tests for fetch_and_save
# ---------------------------------------------------------------------------


class TestFetchAndSave:
    """Tests for fetch_and_save()."""

    def test_success(self, monkeypatch):
        row = pd.DataFrame([{
            "date": "2026-02-28",
            "value": 9.4,
            "source": "Cotality HVI",
            "series_id": "Cotality/HVI/National/Annual",
        }])
        monkeypatch.setattr(cl_mod, "scrape_cotality", lambda: row)
        result = fetch_and_save()
        assert result["status"] == "success"

    def test_empty_scrape(self, monkeypatch):
        monkeypatch.setattr(
            cl_mod, "scrape_cotality",
            lambda: pd.DataFrame(columns=["date", "value", "source", "series_id"]),
        )
        result = fetch_and_save()
        assert result["status"] == "failed"

    def test_exception_caught(self, monkeypatch):
        def raise_error():
            raise RuntimeError("test")
        monkeypatch.setattr(cl_mod, "scrape_cotality", raise_error)
        result = fetch_and_save()
        assert result["status"] == "failed"
        assert "test" in result["error"]
