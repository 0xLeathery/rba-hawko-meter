"""
Unit tests for pipeline.ingest.nab_scraper — NAB capacity utilisation scraper.

Patches create_session at: pipeline.ingest.nab_scraper.create_session
Patches datetime at: pipeline.ingest.nab_scraper.datetime
"""

import io
import sys
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import requests.exceptions

import pipeline.config
import pipeline.ingest.nab_scraper as nab_mod
from pipeline.ingest.nab_scraper import (
    _current_month_already_scraped,
    backfill_nab_history,
    discover_latest_survey_url,
    extract_capacity_from_html,
    extract_capacity_from_pdf,
    fetch_and_save,
    fetch_article,
    get_pdf_link,
    scrape_nab_capacity,
)

PATCH_TARGET = "pipeline.ingest.nab_scraper.create_session"


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


class MockDatetime(datetime):
    """datetime replacement freezing now() to 2026-02-25."""

    _fixed_now = datetime(2026, 2, 25, 10, 0, 0)

    @classmethod
    def now(cls, tz=None):
        return cls._fixed_now

    @classmethod
    def strptime(cls, date_string, fmt):
        return datetime.strptime(date_string, fmt)


def _make_mock_pdfplumber(page_texts):
    """Build a mock pdfplumber module."""
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


# ---------------------------------------------------------------------------
# Tests for discover_latest_survey_url
# ---------------------------------------------------------------------------


class TestDiscoverLatestSurveyUrl:
    """Tests for discover_latest_survey_url()."""

    def test_found(self, fixture_nab_html):
        """Tag archive contains a survey link -> returns absolute URL."""
        mock_session = _make_mock_session([
            {"status_code": 200, "content": fixture_nab_html}
        ])
        result = discover_latest_survey_url(mock_session)
        # fixture_nab_html doesn't have a tag-archive link. Let's use HTML
        # with a survey link directly.
        html_with_link = (
            b'<html><body>'
            b'<a href="https://business.nab.com.au/nab-monthly-business-survey-jan-2026/">'
            b'NAB Monthly Business Survey</a>'
            b'</body></html>'
        )
        mock_session2 = _make_mock_session([
            {"status_code": 200, "content": html_with_link}
        ])
        result = discover_latest_survey_url(mock_session2)
        assert result is not None
        assert "monthly-business-survey" in result.lower()

    def test_relative_href(self):
        html = (
            b'<html><body>'
            b'<a href="/nab-monthly-business-survey-jan-2026/">'
            b'Survey</a>'
            b'</body></html>'
        )
        mock_session = _make_mock_session([
            {"status_code": 200, "content": html}
        ])
        result = discover_latest_survey_url(mock_session)
        assert result is not None
        assert result.startswith("https://business.nab.com.au")

    def test_not_found(self):
        html = b'<html><body><a href="/other-page">Other</a></body></html>'
        mock_session = _make_mock_session([
            {"status_code": 200, "content": html},
            {"status_code": 200, "content": html},
        ])
        result = discover_latest_survey_url(mock_session)
        assert result is None

    def test_archive_error(self):
        mock_session = MagicMock()
        mock_session.get.side_effect = ConnectionError("network error")
        result = discover_latest_survey_url(mock_session)
        assert result is None

    def test_non_200(self):
        mock_session = _make_mock_session([
            {"status_code": 404, "content": b""},
            {"status_code": 404, "content": b""},
        ])
        result = discover_latest_survey_url(mock_session)
        assert result is None


# ---------------------------------------------------------------------------
# Tests for fetch_article
# ---------------------------------------------------------------------------


class TestFetchArticle:
    """Tests for fetch_article()."""

    def test_success(self):
        mock_session = _make_mock_session([
            {"status_code": 200, "content": b"<html>article</html>"}
        ])
        result = fetch_article("https://example.com/article", mock_session)
        assert result == b"<html>article</html>"

    def test_non_200(self):
        mock_session = _make_mock_session([
            {"status_code": 404, "content": b""}
        ])
        result = fetch_article("https://example.com/missing", mock_session)
        assert result is None

    def test_exception(self):
        mock_session = MagicMock()
        mock_session.get.side_effect = ConnectionError("fail")
        result = fetch_article("https://example.com/err", mock_session)
        assert result is None


# ---------------------------------------------------------------------------
# Tests for extract_capacity_from_html
# ---------------------------------------------------------------------------


class TestExtractCapacityFromHtml:
    """Tests for extract_capacity_from_html()."""

    def test_found(self, fixture_nab_html):
        result = extract_capacity_from_html(fixture_nab_html)
        assert result == 83.6

    def test_not_found(self, fixture_nab_html_no_data):
        result = extract_capacity_from_html(fixture_nab_html_no_data)
        assert result is None

    def test_australian_spelling_variant(self):
        """Regex handles 'Capacity utilisation' in various text contexts."""
        html = b'<html><body><p>Capacity utilisation increased to 82.1% in the quarter.</p></body></html>'
        result = extract_capacity_from_html(html)
        assert result == 82.1


# ---------------------------------------------------------------------------
# Tests for get_pdf_link
# ---------------------------------------------------------------------------


class TestGetPdfLink:
    """Tests for get_pdf_link()."""

    def test_found(self, fixture_nab_html):
        result = get_pdf_link(fixture_nab_html)
        assert result is not None
        assert ".pdf" in result.lower()

    def test_not_found(self, fixture_nab_html_no_data):
        result = get_pdf_link(fixture_nab_html_no_data)
        assert result is None

    def test_relative_url(self):
        html = b'<html><body><a href="/report.pdf">PDF</a></body></html>'
        result = get_pdf_link(html)
        assert result.startswith("https://business.nab.com.au")
        assert result.endswith("/report.pdf")


# ---------------------------------------------------------------------------
# Tests for extract_capacity_from_pdf
# ---------------------------------------------------------------------------


class TestExtractCapacityFromPdf:
    """Tests for extract_capacity_from_pdf()."""

    def test_found(self, monkeypatch):
        mock_pdfplumber = _make_mock_pdfplumber(
            ["Capacity utilisation 83.2%"]
        )
        monkeypatch.setitem(sys.modules, "pdfplumber", mock_pdfplumber)
        result = extract_capacity_from_pdf(b"fake-pdf")
        assert result == 83.2

    def test_not_found(self, monkeypatch):
        mock_pdfplumber = _make_mock_pdfplumber(
            ["No capacity data here"]
        )
        monkeypatch.setitem(sys.modules, "pdfplumber", mock_pdfplumber)
        result = extract_capacity_from_pdf(b"fake-pdf")
        assert result is None

    def test_import_error(self, monkeypatch):
        original_import = __import__

        def mock_import(name, *args, **kwargs):
            if name == "pdfplumber":
                raise ImportError("No module named 'pdfplumber'")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            result = extract_capacity_from_pdf(b"fake-pdf")
        assert result is None

    def test_pdfplumber_exception(self, monkeypatch):
        mock_pdfplumber = MagicMock()
        mock_pdfplumber.open.side_effect = Exception("corrupt PDF")
        monkeypatch.setitem(sys.modules, "pdfplumber", mock_pdfplumber)
        result = extract_capacity_from_pdf(b"fake-pdf")
        assert result is None


# ---------------------------------------------------------------------------
# Tests for _current_month_already_scraped
# ---------------------------------------------------------------------------


class TestCurrentMonthAlreadyScraped:
    """Tests for _current_month_already_scraped()."""

    def test_true(self, monkeypatch):
        monkeypatch.setattr(nab_mod, "datetime", MockDatetime)
        output_path = pipeline.config.DATA_DIR / "nab_capacity.csv"
        pd.DataFrame({
            "date": ["2026-02-01"],
            "value": [83.6],
        }).to_csv(output_path, index=False)
        assert _current_month_already_scraped(output_path) is True

    def test_false_old_data(self, monkeypatch):
        monkeypatch.setattr(nab_mod, "datetime", MockDatetime)
        output_path = pipeline.config.DATA_DIR / "nab_capacity.csv"
        pd.DataFrame({
            "date": ["2026-01-01"],
            "value": [83.0],
        }).to_csv(output_path, index=False)
        assert _current_month_already_scraped(output_path) is False

    def test_false_no_file(self):
        output_path = pipeline.config.DATA_DIR / "nonexistent.csv"
        assert _current_month_already_scraped(output_path) is False

    def test_false_empty_csv(self):
        output_path = pipeline.config.DATA_DIR / "nab_capacity.csv"
        pd.DataFrame(columns=["date", "value"]).to_csv(output_path, index=False)
        assert _current_month_already_scraped(output_path) is False


# ---------------------------------------------------------------------------
# Tests for backfill_nab_history
# ---------------------------------------------------------------------------


class TestBackfillNabHistory:
    """Tests for backfill_nab_history()."""

    def test_success(self, monkeypatch):
        monkeypatch.setattr(nab_mod, "datetime", MockDatetime)
        # Mock: months=2, first month finds article with capacity data,
        # second month returns 404
        call_count = 0

        def mock_get(url, timeout=None):
            nonlocal call_count
            call_count += 1
            resp = MagicMock()
            # First 3 calls are URL pattern attempts for month 1
            if call_count <= 3:
                if call_count == 1:
                    # First pattern succeeds with capacity data
                    resp.status_code = 200
                    resp.content = (
                        b'<html><body>'
                        b'<p>Capacity utilisation was 82.5%</p>'
                        b'</body></html>'
                    )
                    return resp
                resp.status_code = 404
                resp.content = b""
                return resp
            # Remaining calls are for month 2 (all 404)
            resp.status_code = 404
            resp.content = b""
            return resp

        mock_session = MagicMock()
        mock_session.get = mock_get
        result = backfill_nab_history(mock_session, months=2)
        assert result >= 1

    def test_all_fail(self, monkeypatch):
        monkeypatch.setattr(nab_mod, "datetime", MockDatetime)
        mock_session = MagicMock()
        resp = MagicMock()
        resp.status_code = 404
        resp.content = b""
        mock_session.get.return_value = resp
        result = backfill_nab_history(mock_session, months=2)
        assert result == 0

    def test_pdf_fallback(self, monkeypatch):
        """HTML extraction fails, but PDF link exists and PDF extraction succeeds."""
        monkeypatch.setattr(nab_mod, "datetime", MockDatetime)
        mock_pdfplumber = _make_mock_pdfplumber(
            ["Capacity utilisation 81.0%"]
        )
        monkeypatch.setitem(sys.modules, "pdfplumber", mock_pdfplumber)

        call_count = 0

        def mock_get(url, timeout=None):
            nonlocal call_count
            call_count += 1
            resp = MagicMock()
            if call_count == 1:
                # First URL pattern: article HTML without capacity data
                # but with PDF link
                resp.status_code = 200
                resp.content = (
                    b'<html><body>'
                    b'<p>Business conditions improved.</p>'
                    b'<a href="https://business.nab.com.au/report.pdf">PDF</a>'
                    b'</body></html>'
                )
                return resp
            if call_count == 2:
                # PDF download
                resp.status_code = 200
                resp.content = b"pdf-bytes"
                return resp
            # All other calls (remaining months/patterns)
            resp.status_code = 404
            resp.content = b""
            return resp

        mock_session = MagicMock()
        mock_session.get = mock_get
        result = backfill_nab_history(mock_session, months=1)
        assert result == 1


# ---------------------------------------------------------------------------
# Tests for scrape_nab_capacity
# ---------------------------------------------------------------------------


class TestScrapeNabCapacity:
    """Tests for scrape_nab_capacity()."""

    def test_happy_path(self, monkeypatch):
        monkeypatch.setattr(nab_mod, "datetime", MockDatetime)
        # Pre-create CSV with enough rows to skip backfill
        output_path = pipeline.config.DATA_DIR / "nab_capacity.csv"
        pd.DataFrame({
            "date": ["2025-11-01", "2025-12-01", "2026-01-01"],
            "value": [82.0, 82.5, 83.0],
        }).to_csv(output_path, index=False)

        # Mock session: discover URL -> fetch article -> extract HTML
        survey_html = (
            b'<html><body>'
            b'<p>Capacity utilisation rose to 83.6%</p>'
            b'</body></html>'
        )
        archive_html = (
            b'<html><body>'
            b'<a href="https://business.nab.com.au/nab-monthly-business-survey-jan-2026/">'
            b'Survey</a></body></html>'
        )
        mock_session = _make_mock_session([
            # discover_latest_survey_url: tag archive
            {"status_code": 200, "content": archive_html},
            # fetch_article: article page
            {"status_code": 200, "content": survey_html},
        ])
        with patch(PATCH_TARGET, return_value=mock_session):
            df = scrape_nab_capacity()

        assert len(df) == 1
        assert df["value"].iloc[0] == 83.6
        assert df["source"].iloc[0] == "NAB Monthly Business Survey"

    def test_already_scraped(self, monkeypatch):
        monkeypatch.setattr(nab_mod, "datetime", MockDatetime)
        output_path = pipeline.config.DATA_DIR / "nab_capacity.csv"
        pd.DataFrame({
            "date": ["2026-02-01"],
            "value": [83.6],
        }).to_csv(output_path, index=False)

        mock_session = _make_mock_session([])
        with patch(PATCH_TARGET, return_value=mock_session):
            df = scrape_nab_capacity()
        assert df.empty

    def test_no_url_discovered(self, monkeypatch):
        monkeypatch.setattr(nab_mod, "datetime", MockDatetime)
        # Pre-create CSV with enough rows
        output_path = pipeline.config.DATA_DIR / "nab_capacity.csv"
        pd.DataFrame({
            "date": ["2025-11-01", "2025-12-01", "2026-01-01"],
            "value": [82.0, 82.5, 83.0],
        }).to_csv(output_path, index=False)

        # Tag archives have no survey links
        no_link_html = b'<html><body><a href="/other">Other</a></body></html>'
        mock_session = _make_mock_session([
            {"status_code": 200, "content": no_link_html},
            {"status_code": 200, "content": no_link_html},
        ])
        with patch(PATCH_TARGET, return_value=mock_session):
            df = scrape_nab_capacity()
        assert df.empty

    def test_html_fails_pdf_succeeds(self, monkeypatch):
        """HTML extraction None, PDF extraction succeeds."""
        monkeypatch.setattr(nab_mod, "datetime", MockDatetime)
        mock_pdfplumber = _make_mock_pdfplumber(
            ["Capacity utilisation 84.0%"]
        )
        monkeypatch.setitem(sys.modules, "pdfplumber", mock_pdfplumber)

        output_path = pipeline.config.DATA_DIR / "nab_capacity.csv"
        pd.DataFrame({
            "date": ["2025-11-01", "2025-12-01", "2026-01-01"],
            "value": [82.0, 82.5, 83.0],
        }).to_csv(output_path, index=False)

        archive_html = (
            b'<html><body>'
            b'<a href="https://business.nab.com.au/nab-monthly-business-survey-jan-2026/">'
            b'Survey</a></body></html>'
        )
        article_html = (
            b'<html><body>'
            b'<p>Business conditions improved.</p>'
            b'<a href="https://business.nab.com.au/report.pdf">Report PDF</a>'
            b'</body></html>'
        )
        mock_session = _make_mock_session([
            {"status_code": 200, "content": archive_html},
            {"status_code": 200, "content": article_html},
            # PDF download
            {"status_code": 200, "content": b"pdf-bytes"},
        ])
        with patch(PATCH_TARGET, return_value=mock_session):
            df = scrape_nab_capacity()
        assert len(df) == 1
        assert df["value"].iloc[0] == 84.0

    def test_both_fail(self, monkeypatch):
        """HTML and PDF extraction both fail."""
        monkeypatch.setattr(nab_mod, "datetime", MockDatetime)
        output_path = pipeline.config.DATA_DIR / "nab_capacity.csv"
        pd.DataFrame({
            "date": ["2025-11-01", "2025-12-01", "2026-01-01"],
            "value": [82.0, 82.5, 83.0],
        }).to_csv(output_path, index=False)

        archive_html = (
            b'<html><body>'
            b'<a href="https://business.nab.com.au/nab-monthly-business-survey-jan-2026/">'
            b'Survey</a></body></html>'
        )
        # Article without capacity data and without PDF link
        article_html = (
            b'<html><body><p>No data here.</p></body></html>'
        )
        mock_session = _make_mock_session([
            {"status_code": 200, "content": archive_html},
            {"status_code": 200, "content": article_html},
        ])
        with patch(PATCH_TARGET, return_value=mock_session):
            df = scrape_nab_capacity()
        assert df.empty

    def test_triggers_backfill_no_csv(self, monkeypatch):
        """When CSV doesn't exist, backfill is triggered."""
        monkeypatch.setattr(nab_mod, "datetime", MockDatetime)
        # Don't create any CSV -> triggers backfill
        # Mock all HTTP to return 404 (backfill + discover both fail)
        resp = MagicMock()
        resp.status_code = 404
        resp.content = b""
        mock_session = MagicMock()
        mock_session.get.return_value = resp
        with patch(PATCH_TARGET, return_value=mock_session):
            df = scrape_nab_capacity()
        # Backfill ran (calls were made) but found nothing
        assert mock_session.get.call_count > 0
        assert df.empty

    def test_triggers_backfill_sparse_csv(self, monkeypatch):
        """When CSV has <3 rows, backfill is triggered."""
        monkeypatch.setattr(nab_mod, "datetime", MockDatetime)
        output_path = pipeline.config.DATA_DIR / "nab_capacity.csv"
        pd.DataFrame({
            "date": ["2026-01-01"],
            "value": [83.0],
        }).to_csv(output_path, index=False)

        resp = MagicMock()
        resp.status_code = 404
        resp.content = b""
        mock_session = MagicMock()
        mock_session.get.return_value = resp
        with patch(PATCH_TARGET, return_value=mock_session):
            df = scrape_nab_capacity()
        assert mock_session.get.call_count > 0

    def test_no_pdf_link_path(self, monkeypatch):
        """HTML extraction None, article has no PDF link -> empty df."""
        monkeypatch.setattr(nab_mod, "datetime", MockDatetime)
        output_path = pipeline.config.DATA_DIR / "nab_capacity.csv"
        pd.DataFrame({
            "date": ["2025-11-01", "2025-12-01", "2026-01-01"],
            "value": [82.0, 82.5, 83.0],
        }).to_csv(output_path, index=False)

        archive_html = (
            b'<html><body>'
            b'<a href="https://business.nab.com.au/nab-monthly-business-survey-jan-2026/">'
            b'Survey</a></body></html>'
        )
        # Article with no capacity data and no PDF link
        article_html = (
            b'<html><body><p>General commentary only.</p></body></html>'
        )
        mock_session = _make_mock_session([
            {"status_code": 200, "content": archive_html},
            {"status_code": 200, "content": article_html},
        ])
        with patch(PATCH_TARGET, return_value=mock_session):
            df = scrape_nab_capacity()
        assert df.empty


# ---------------------------------------------------------------------------
# Tests for fetch_and_save
# ---------------------------------------------------------------------------


class TestFetchAndSave:
    """Tests for fetch_and_save()."""

    def test_success(self, monkeypatch):
        row = pd.DataFrame([{
            "date": "2026-01-01",
            "value": 83.6,
            "source": "NAB Monthly Business Survey",
        }])
        monkeypatch.setattr(nab_mod, "scrape_nab_capacity", lambda: row)
        result = fetch_and_save()
        assert result["status"] == "success"

    def test_empty_with_backfill_data(self, monkeypatch):
        """Scrape returns empty, but CSV has data from backfill."""
        monkeypatch.setattr(
            nab_mod, "scrape_nab_capacity",
            lambda: pd.DataFrame(columns=["date", "value", "source"]),
        )
        output_path = pipeline.config.DATA_DIR / "nab_capacity.csv"
        pd.DataFrame({
            "date": ["2026-01-01"],
            "value": [83.0],
            "source": ["NAB Monthly Business Survey"],
        }).to_csv(output_path, index=False)
        result = fetch_and_save()
        assert result["status"] == "success"

    def test_empty_no_data(self, monkeypatch):
        monkeypatch.setattr(
            nab_mod, "scrape_nab_capacity",
            lambda: pd.DataFrame(columns=["date", "value", "source"]),
        )
        result = fetch_and_save()
        assert result["status"] == "failed"

    def test_exception_caught(self, monkeypatch):
        def raise_error():
            raise RuntimeError("test error")
        monkeypatch.setattr(nab_mod, "scrape_nab_capacity", raise_error)
        result = fetch_and_save()
        assert result["status"] == "failed"
        assert "test error" in result["error"]
