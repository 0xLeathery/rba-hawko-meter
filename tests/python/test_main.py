"""
Unit tests for pipeline.main.run_pipeline().

Covers: all-success path, critical failure (sys.exit(1)), important source
failure (partial), optional source failure (exception path), optional source
returning failed dict, normalization unavailable, normalization exception.

All tier lists are patched with single controlled mock entries using lambdas
(matching the lambda detection logic in main.py).
"""

from unittest.mock import MagicMock

import pytest

# =============================================================================
# Helpers
# =============================================================================


def _make_lambda_mock(return_value=None, side_effect=None):
    """Return a lambda wrapping a MagicMock for use in tier source lists."""
    m = MagicMock(return_value=return_value, side_effect=side_effect)
    return lambda: m()


# =============================================================================
# TestRunPipeline
# =============================================================================


class TestRunPipeline:
    """Tests for run_pipeline() covering all tier behaviors and sys.exit contract."""

    def test_all_sources_succeed_returns_success(self, monkeypatch):
        """All critical, important, optional sources succeed → status 'success'."""
        critical_mock = _make_lambda_mock(return_value={"rows": 10})
        important_mock = _make_lambda_mock(return_value={"rows": 5})
        optional_mock = _make_lambda_mock(return_value={"rows": 3})

        mock_status = {
            "overall": {"hawk_score": 55.0, "zone_label": "Balanced"},
            "metadata": {"indicators_available": 6, "indicators_missing": []},
        }

        monkeypatch.setattr(
            "pipeline.main.CRITICAL_SOURCES", [("Test Critical", critical_mock)]
        )
        monkeypatch.setattr(
            "pipeline.main.IMPORTANT_SOURCES", [("Test Important", important_mock)]
        )
        monkeypatch.setattr(
            "pipeline.main.OPTIONAL_SOURCES", [("Test Optional", optional_mock)]
        )
        monkeypatch.setattr("pipeline.main.NORMALIZATION_AVAILABLE", True)
        monkeypatch.setattr("pipeline.main.generate_status", lambda: mock_status)

        from pipeline.main import run_pipeline

        results = run_pipeline()

        assert results["status"] == "success"
        assert results["critical"]["Test Critical"]["status"] == "success"
        assert results["important"]["Test Important"]["status"] == "success"
        assert results["optional"]["Test Optional"]["status"] == "success"
        assert results["normalization"]["status"] == "success"
        assert results["normalization"]["hawk_score"] == 55.0

    def test_critical_failure_calls_sys_exit_1(self, monkeypatch):
        """Critical source failure triggers sys.exit(1) — test runner does not die."""
        critical_mock = _make_lambda_mock(
            side_effect=RuntimeError("Connection failed")
        )

        monkeypatch.setattr(
            "pipeline.main.CRITICAL_SOURCES", [("Test Critical", critical_mock)]
        )
        monkeypatch.setattr("pipeline.main.IMPORTANT_SOURCES", [])
        monkeypatch.setattr("pipeline.main.OPTIONAL_SOURCES", [])

        from pipeline.main import run_pipeline

        with pytest.raises(SystemExit) as exc_info:
            run_pipeline()

        assert exc_info.value.code == 1

    def test_important_failure_returns_partial_with_failures_list(self, monkeypatch):
        """Important source failure → status 'partial', important_failures populated."""
        critical_mock = _make_lambda_mock(return_value={"rows": 10})
        important_mock = _make_lambda_mock(side_effect=ValueError("Parse error"))

        mock_status = {
            "overall": {"hawk_score": 50.0, "zone_label": "Balanced"},
            "metadata": {"indicators_available": 4, "indicators_missing": ["wages"]},
        }

        monkeypatch.setattr(
            "pipeline.main.CRITICAL_SOURCES", [("Test Critical", critical_mock)]
        )
        monkeypatch.setattr(
            "pipeline.main.IMPORTANT_SOURCES", [("Test Important", important_mock)]
        )
        monkeypatch.setattr("pipeline.main.OPTIONAL_SOURCES", [])
        monkeypatch.setattr("pipeline.main.NORMALIZATION_AVAILABLE", True)
        monkeypatch.setattr("pipeline.main.generate_status", lambda: mock_status)

        from pipeline.main import run_pipeline

        results = run_pipeline()

        assert results["status"] == "partial"
        assert "Test Important" in results["important_failures"]
        assert results["important"]["Test Important"]["status"] == "failed"
        assert "Parse error" in results["important"]["Test Important"]["error"]

    def test_optional_exception_returns_partial(self, monkeypatch):
        """Optional source exception → status 'partial', optional_failures populated."""
        critical_mock = _make_lambda_mock(return_value={"rows": 10})
        optional_mock = _make_lambda_mock(
            side_effect=ConnectionError("Timeout")
        )

        monkeypatch.setattr(
            "pipeline.main.CRITICAL_SOURCES", [("Test Critical", critical_mock)]
        )
        monkeypatch.setattr("pipeline.main.IMPORTANT_SOURCES", [])
        monkeypatch.setattr(
            "pipeline.main.OPTIONAL_SOURCES", [("Test Optional", optional_mock)]
        )
        monkeypatch.setattr("pipeline.main.NORMALIZATION_AVAILABLE", False)

        from pipeline.main import run_pipeline

        results = run_pipeline()

        assert results["status"] == "partial"
        assert "Test Optional" in results["optional_failures"]
        assert results["optional"]["Test Optional"]["status"] == "failed"

    def test_optional_returns_failed_dict_marks_partial(self, monkeypatch):
        """Optional source returning {'status': 'failed'} dict → partial."""
        critical_mock = _make_lambda_mock(return_value={"rows": 5})
        # Scraper pattern: returns dict with status='failed' instead of raising
        optional_mock = _make_lambda_mock(
            return_value={"status": "failed", "error": "PDF not found"}
        )

        monkeypatch.setattr(
            "pipeline.main.CRITICAL_SOURCES", [("Test Critical", critical_mock)]
        )
        monkeypatch.setattr("pipeline.main.IMPORTANT_SOURCES", [])
        monkeypatch.setattr(
            "pipeline.main.OPTIONAL_SOURCES", [("Test Optional", optional_mock)]
        )
        monkeypatch.setattr("pipeline.main.NORMALIZATION_AVAILABLE", False)

        from pipeline.main import run_pipeline

        results = run_pipeline()

        assert results["status"] == "partial"
        assert "Test Optional" in results["optional_failures"]

    def test_normalization_not_available_is_skipped(self, monkeypatch):
        """When NORMALIZATION_AVAILABLE is False, normalization phase is skipped."""
        critical_mock = _make_lambda_mock(return_value={"rows": 5})

        monkeypatch.setattr(
            "pipeline.main.CRITICAL_SOURCES", [("Test Critical", critical_mock)]
        )
        monkeypatch.setattr("pipeline.main.IMPORTANT_SOURCES", [])
        monkeypatch.setattr("pipeline.main.OPTIONAL_SOURCES", [])
        monkeypatch.setattr("pipeline.main.NORMALIZATION_AVAILABLE", False)

        from pipeline.main import run_pipeline

        results = run_pipeline()

        assert results["normalization"]["status"] == "skipped"
        assert results["normalization"]["reason"] == "module not available"

    def test_normalization_exception_is_non_fatal(self, monkeypatch):
        """Normalization exception does not prevent pipeline returning 'success'."""
        critical_mock = _make_lambda_mock(return_value={"rows": 5})

        monkeypatch.setattr(
            "pipeline.main.CRITICAL_SOURCES", [("Test Critical", critical_mock)]
        )
        monkeypatch.setattr("pipeline.main.IMPORTANT_SOURCES", [])
        monkeypatch.setattr("pipeline.main.OPTIONAL_SOURCES", [])
        monkeypatch.setattr("pipeline.main.NORMALIZATION_AVAILABLE", True)
        monkeypatch.setattr(
            "pipeline.main.generate_status",
            MagicMock(side_effect=RuntimeError("Engine error")),
        )

        from pipeline.main import run_pipeline

        results = run_pipeline()

        # Critical sources succeeded, so overall status is 'success'
        assert results["status"] == "success"
        assert results["normalization"]["status"] == "failed"
        assert "Engine error" in results["normalization"]["error"]

    def test_first_critical_failure_exits_immediately(self, monkeypatch):
        """On first critical failure, sys.exit(1) fires immediately (fail-fast)."""
        first_mock = _make_lambda_mock(side_effect=RuntimeError("First failure"))
        second_mock = _make_lambda_mock(return_value={"rows": 5})

        monkeypatch.setattr(
            "pipeline.main.CRITICAL_SOURCES",
            [("First", first_mock), ("Second", second_mock)],
        )
        monkeypatch.setattr("pipeline.main.IMPORTANT_SOURCES", [])
        monkeypatch.setattr("pipeline.main.OPTIONAL_SOURCES", [])

        from pipeline.main import run_pipeline

        with pytest.raises(SystemExit) as exc_info:
            run_pipeline()

        assert exc_info.value.code == 1

    def test_results_contains_run_date_in_iso_format(self, monkeypatch):
        """Results dict contains run_date in ISO format ending with 'Z'."""
        critical_mock = _make_lambda_mock(return_value={"rows": 5})

        monkeypatch.setattr(
            "pipeline.main.CRITICAL_SOURCES", [("Test Critical", critical_mock)]
        )
        monkeypatch.setattr("pipeline.main.IMPORTANT_SOURCES", [])
        monkeypatch.setattr("pipeline.main.OPTIONAL_SOURCES", [])
        monkeypatch.setattr("pipeline.main.NORMALIZATION_AVAILABLE", False)

        from pipeline.main import run_pipeline

        results = run_pipeline()

        assert "run_date" in results
        assert results["run_date"].endswith("Z")

    def test_results_contains_all_tier_dicts(self, monkeypatch):
        """Results always has 'critical', 'important', 'optional' dicts."""
        critical_mock = _make_lambda_mock(return_value={"rows": 5})

        monkeypatch.setattr(
            "pipeline.main.CRITICAL_SOURCES", [("Test Critical", critical_mock)]
        )
        monkeypatch.setattr("pipeline.main.IMPORTANT_SOURCES", [])
        monkeypatch.setattr("pipeline.main.OPTIONAL_SOURCES", [])
        monkeypatch.setattr("pipeline.main.NORMALIZATION_AVAILABLE", False)

        from pipeline.main import run_pipeline

        results = run_pipeline()

        assert "critical" in results
        assert "important" in results
        assert "optional" in results

    def test_multiple_important_failures_all_listed(self, monkeypatch):
        """Multiple important source failures all appear in important_failures."""
        critical_mock = _make_lambda_mock(return_value={"rows": 5})
        important_mock1 = _make_lambda_mock(side_effect=ValueError("err1"))
        important_mock2 = _make_lambda_mock(side_effect=ValueError("err2"))

        monkeypatch.setattr(
            "pipeline.main.CRITICAL_SOURCES", [("Critical", critical_mock)]
        )
        monkeypatch.setattr(
            "pipeline.main.IMPORTANT_SOURCES",
            [("Source A", important_mock1), ("Source B", important_mock2)],
        )
        monkeypatch.setattr("pipeline.main.OPTIONAL_SOURCES", [])
        monkeypatch.setattr("pipeline.main.NORMALIZATION_AVAILABLE", False)

        from pipeline.main import run_pipeline

        results = run_pipeline()

        assert results["status"] == "partial"
        assert "Source A" in results["important_failures"]
        assert "Source B" in results["important_failures"]

    def test_normalization_reports_hawk_score_and_indicators(self, monkeypatch):
        """Normalization success records hawk_score and indicator counts."""
        critical_mock = _make_lambda_mock(return_value={"rows": 5})

        mock_status = {
            "overall": {"hawk_score": 72.5, "zone_label": "Warm"},
            "metadata": {
                "indicators_available": 7,
                "indicators_missing": ["business_confidence"],
            },
        }

        monkeypatch.setattr(
            "pipeline.main.CRITICAL_SOURCES", [("Test Critical", critical_mock)]
        )
        monkeypatch.setattr("pipeline.main.IMPORTANT_SOURCES", [])
        monkeypatch.setattr("pipeline.main.OPTIONAL_SOURCES", [])
        monkeypatch.setattr("pipeline.main.NORMALIZATION_AVAILABLE", True)
        monkeypatch.setattr("pipeline.main.generate_status", lambda: mock_status)

        from pipeline.main import run_pipeline

        results = run_pipeline()

        norm = results["normalization"]
        assert norm["status"] == "success"
        assert norm["hawk_score"] == 72.5
        assert norm["indicators_available"] == 7
        assert "business_confidence" in norm["indicators_missing"]


# =============================================================================
# Module-level checks
# =============================================================================


def test_normalization_available_is_bool():
    """NORMALIZATION_AVAILABLE is set at module import time and is a bool."""
    import pipeline.main

    assert isinstance(pipeline.main.NORMALIZATION_AVAILABLE, bool)


def test_critical_sources_is_list():
    """CRITICAL_SOURCES is a non-empty list of (name, module_or_callable) tuples."""
    import pipeline.main

    assert isinstance(pipeline.main.CRITICAL_SOURCES, list)
    assert len(pipeline.main.CRITICAL_SOURCES) > 0
    for name, module in pipeline.main.CRITICAL_SOURCES:
        assert isinstance(name, str)
        # Module entries have fetch_and_save; lambda entries are callable
        assert callable(module) or hasattr(module, "fetch_and_save")


def test_important_sources_is_list():
    """IMPORTANT_SOURCES is a non-empty list of (name, callable) tuples."""
    import pipeline.main

    assert isinstance(pipeline.main.IMPORTANT_SOURCES, list)
    assert len(pipeline.main.IMPORTANT_SOURCES) > 0


def test_optional_sources_is_list():
    """OPTIONAL_SOURCES is a non-empty list."""
    import pipeline.main

    assert isinstance(pipeline.main.OPTIONAL_SOURCES, list)
    assert len(pipeline.main.OPTIONAL_SOURCES) > 0
