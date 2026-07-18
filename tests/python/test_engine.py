"""
Unit tests for pipeline.normalize.engine.

Covers: generate_interpretation, build_asx_futures_entry, build_gauge_entry,
process_indicator, generate_status.

STATUS_OUTPUT is isolated via the engine_data_dir fixture (patches
pipeline.normalize.engine.STATUS_OUTPUT to tmp_path/status.json).
All I/O dependencies in generate_status are mocked at their import sites
in pipeline.normalize.engine.
"""

from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

# =============================================================================
# Helpers
# =============================================================================


class MockDatetime:
    """Freezes datetime.now() and utcnow() to a fixed date for test isolation."""

    FROZEN = datetime(2026, 2, 25, 12, 0, 0)

    @classmethod
    def now(cls):
        return cls.FROZEN

    @classmethod
    def utcnow(cls):
        return cls.FROZEN

    @staticmethod
    def strptime(date_string, format_str):
        return datetime.strptime(date_string, format_str)

    @staticmethod
    def strftime(dt, format_str):
        return dt.strftime(format_str)


def _make_z_df(n_rows=15, base_date="2020-01-01"):
    """Create a minimal z-score DataFrame for testing build_gauge_entry."""
    dates = pd.date_range(base_date, periods=n_rows, freq="QS")
    values = [2.0 + i * 0.1 for i in range(n_rows)]
    z_scores = [0.3 + i * 0.05 for i in range(n_rows)]
    return pd.DataFrame(
        {
            "date": dates,
            "value": values,
            "z_score": z_scores,
            "window_size": [20] * n_rows,
        }
    )


@contextmanager
def _mock_generate_status_deps(confidence="HIGH", all_none=False):
    """
    Context manager that mocks all generate_status() I/O dependencies.

    Patches at their import sites in pipeline.normalize.engine so tests
    do not require real CSV data or weights.json.
    """
    mock_weights = {
        "inflation": {"weight": 0.25, "polarity": 1},
        "wages": {"weight": 0.20, "polarity": 1},
        "employment": {"weight": 0.20, "polarity": 1},
        "spending": {"weight": 0.15, "polarity": 1},
        "building_approvals": {"weight": 0.10, "polarity": -1},
        "housing": {"weight": 0.10, "polarity": 1},
    }

    mock_gauge_entry = {
        "value": 55.0,
        "zone": "neutral",
        "zone_label": "Balanced",
        "z_score": 0.3,
        "raw_value": 3.2,
        "raw_unit": "% YoY",
        "weight": 0.25,
        "polarity": 1,
        "data_date": "2025-10-01",
        "staleness_days": 100,
        "confidence": confidence,
        "interpretation": "test interpretation",
        "history": [50.0, 52.0, 55.0],
    }

    process_return = (None, None) if all_none else (mock_gauge_entry, 55.0)

    with patch("pipeline.normalize.engine.load_weights", return_value=mock_weights):
        with patch(
            "pipeline.normalize.engine.process_indicator",
            return_value=process_return,
        ):
            with patch(
                "pipeline.normalize.engine.compute_hawk_score", return_value=50.0
            ):
                with patch(
                    "pipeline.normalize.engine.classify_zone",
                    return_value=("neutral", "Balanced"),
                ):
                    with patch(
                        "pipeline.normalize.engine.generate_verdict",
                        return_value="Economic indicators are broadly balanced",
                    ):
                        with patch(
                            "pipeline.normalize.engine.load_asx_futures_csv",
                            return_value=None,
                        ):
                            yield


# =============================================================================
# TestGenerateInterpretation
# =============================================================================


class TestGenerateInterpretation:
    """Tests for generate_interpretation() — pure function, no side effects."""

    @pytest.mark.parametrize(
        "indicator,zone,expected_fragment",
        [
            # inflation
            ("inflation", "cold", "well below"),
            ("inflation", "cool", "below"),
            ("inflation", "neutral", "near"),
            ("inflation", "warm", "above"),
            ("inflation", "hot", "significantly above"),
            # wages
            ("wages", "cold", "well below"),
            ("wages", "cool", "below"),
            ("wages", "neutral", "near"),
            ("wages", "warm", "above"),
            ("wages", "hot", "significantly above"),
            # employment
            ("employment", "cold", "significantly looser"),
            ("employment", "cool", "looser"),
            ("employment", "neutral", "near"),
            ("employment", "warm", "tighter"),
            ("employment", "hot", "significantly tighter"),
            # spending
            ("spending", "cold", "well below"),
            ("spending", "cool", "below"),
            ("spending", "neutral", "near"),
            ("spending", "warm", "above"),
            ("spending", "hot", "well above"),
            # building_approvals
            ("building_approvals", "cold", "well below"),
            ("building_approvals", "cool", "below"),
            ("building_approvals", "neutral", "near"),
            ("building_approvals", "warm", "above"),
            ("building_approvals", "hot", "well above"),
            # housing
            ("housing", "cold", "well below"),
            ("housing", "cool", "below"),
            ("housing", "neutral", "near"),
            ("housing", "warm", "above"),
            ("housing", "hot", "well above"),
            # business_confidence
            ("business_confidence", "cold", "well below"),
            ("business_confidence", "cool", "below"),
            ("business_confidence", "neutral", "near"),
            ("business_confidence", "warm", "above"),
            ("business_confidence", "hot", "significantly above"),
            # asx_futures
            ("asx_futures", "cold", "significant rate cuts"),
            ("asx_futures", "cool", "rate cuts"),
            ("asx_futures", "neutral", "stable rates"),
            ("asx_futures", "warm", "rate hikes"),
            ("asx_futures", "hot", "significant rate hikes"),
        ],
    )
    def test_known_indicator_zones(self, indicator, zone, expected_fragment):
        from pipeline.normalize.engine import generate_interpretation

        result = generate_interpretation(indicator, zone, 1.0)
        assert expected_fragment in result

    @pytest.mark.parametrize(
        "indicator",
        [
            "inflation",
            "wages",
            "employment",
            "spending",
            "building_approvals",
            "housing",
            "business_confidence",
            "asx_futures",
        ],
    )
    @pytest.mark.parametrize("zone", ["cold", "cool", "neutral", "warm", "hot"])
    def test_all_combinations_return_non_empty_string(self, indicator, zone):
        from pipeline.normalize.engine import generate_interpretation

        result = generate_interpretation(indicator, zone, 0.0)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_unknown_indicator_returns_fallback(self):
        from pipeline.normalize.engine import generate_interpretation

        result = generate_interpretation("unknown_indicator", "neutral", 1.0)
        assert result == "unknown_indicator data available"

    def test_unknown_zone_on_known_indicator_returns_fallback(self):
        from pipeline.normalize.engine import generate_interpretation

        result = generate_interpretation("inflation", "unknown_zone", 1.0)
        assert result == "inflation data available"

    def test_raw_value_not_used_in_output(self):
        """raw_value parameter is accepted but not used in template lookup."""
        from pipeline.normalize.engine import generate_interpretation

        result1 = generate_interpretation("wages", "warm", 0.0)
        result2 = generate_interpretation("wages", "warm", 999.0)
        assert result1 == result2


# =============================================================================
# TestBuildGaugeEntry
# =============================================================================


class TestBuildGaugeEntry:
    """Tests for build_gauge_entry() — builds gauge dict for status.json."""

    def test_basic_indicator_returns_required_fields(self, monkeypatch):
        monkeypatch.setattr("pipeline.normalize.engine.datetime", MockDatetime)
        from pipeline.normalize.engine import build_gauge_entry

        z_df = _make_z_df()
        latest_row = z_df.iloc[-1]
        weight_config = {"polarity": 1, "weight": 0.2}

        entry = build_gauge_entry("inflation", latest_row, z_df, weight_config)

        required = [
            "value",
            "zone",
            "zone_label",
            "z_score",
            "raw_value",
            "raw_unit",
            "weight",
            "polarity",
            "data_date",
            "staleness_days",
            "confidence",
            "interpretation",
            "history",
        ]
        for field in required:
            assert field in entry, f"Missing field: {field}"
        assert isinstance(entry["history"], list)
        assert entry["weight"] == 0.2
        assert entry["raw_unit"] == "% YoY"
        assert entry["polarity"] == 1
        assert entry["data_date"] == "2023-07-01"

    def test_negative_polarity_inverts_z_score(self, monkeypatch):
        monkeypatch.setattr("pipeline.normalize.engine.datetime", MockDatetime)
        from pipeline.normalize.engine import build_gauge_entry

        z_df = _make_z_df()
        latest_row = z_df.iloc[-1]
        weight_pos = {"polarity": 1, "weight": 0.2}
        weight_neg = {"polarity": -1, "weight": 0.2}

        entry_pos = build_gauge_entry("inflation", latest_row, z_df, weight_pos)
        entry_neg = build_gauge_entry("inflation", latest_row, z_df, weight_neg)

        assert entry_pos["z_score"] != entry_neg["z_score"]
        assert abs(entry_pos["z_score"] + entry_neg["z_score"]) < 0.001

    def test_history_capped_at_12_entries(self, monkeypatch):
        monkeypatch.setattr("pipeline.normalize.engine.datetime", MockDatetime)
        from pipeline.normalize.engine import build_gauge_entry

        z_df = _make_z_df(n_rows=20)
        latest_row = z_df.iloc[-1]
        weight_config = {"polarity": 1, "weight": 0.1}

        entry = build_gauge_entry("wages", latest_row, z_df, weight_config)
        assert len(entry["history"]) <= 12

    def test_staleness_days_computed_correctly(self, monkeypatch):
        monkeypatch.setattr("pipeline.normalize.engine.datetime", MockDatetime)
        from pipeline.normalize.engine import build_gauge_entry

        # Create a df where last date is exactly 10 days before the frozen date
        # MockDatetime.FROZEN = 2026-02-25; data_date is 10 days earlier
        data_date = datetime(2026, 2, 15)  # 10 days before frozen
        z_df = pd.DataFrame(
            {
                "date": [data_date],
                "value": [3.0],
                "z_score": [0.5],
                "window_size": [20],
            }
        )
        latest_row = z_df.iloc[-1]
        weight_config = {"polarity": 1, "weight": 0.2}

        entry = build_gauge_entry("inflation", latest_row, z_df, weight_config)
        assert entry["staleness_days"] == 10

    def test_housing_meta_from_normalize_attrs(self, monkeypatch):
        """Housing meta comes from indicator_meta, not CSV sniffing."""
        monkeypatch.setattr("pipeline.normalize.engine.datetime", MockDatetime)
        from pipeline.normalize.engine import build_gauge_entry

        z_df = _make_z_df()
        latest_row = z_df.iloc[-1]
        weight_config = {"polarity": 1, "weight": 0.1}
        meta = {
            "data_source": "Cotality HVI",
            "stale_display": "quarter_only",
            "display_raw_value": 9.4,
            "display_data_date": "2026-02-28",
            "confidence_cap": "LOW",
        }

        entry = build_gauge_entry(
            "housing",
            latest_row,
            z_df,
            weight_config,
            indicator_meta=meta,
        )

        assert entry["data_source"] == "Cotality HVI"
        assert entry["stale_display"] == "quarter_only"
        assert entry["raw_value"] == 9.4
        assert entry["data_date"] == "2026-02-28"
        assert entry["confidence"] == "LOW"

    def test_housing_meta_abs_only(self, monkeypatch):
        """Housing ABS-only meta sets stale_display without CSV I/O."""
        monkeypatch.setattr("pipeline.normalize.engine.datetime", MockDatetime)
        from pipeline.normalize.engine import build_gauge_entry

        z_df = _make_z_df()
        latest_row = z_df.iloc[-1]
        weight_config = {"polarity": 1, "weight": 0.1}

        entry = build_gauge_entry(
            "housing",
            latest_row,
            z_df,
            weight_config,
            indicator_meta={
                "data_source": "ABS RPPI",
                "stale_display": "quarter_only",
            },
        )
        assert entry["data_source"] == "ABS RPPI"
        assert entry["stale_display"] == "quarter_only"

    def test_business_confidence_enrichment(self, monkeypatch, tmp_path):
        """Business confidence reads nab_capacity.csv; adds direction/long_run_avg."""
        monkeypatch.setattr("pipeline.normalize.engine.datetime", MockDatetime)
        import shutil

        fixtures_dir = Path(__file__).parent / "fixtures"
        shutil.copy(fixtures_dir / "nab_capacity.csv", tmp_path / "nab_capacity.csv")

        from pipeline.normalize.engine import build_gauge_entry

        z_df = _make_z_df()
        latest_row = z_df.iloc[-1]
        weight_config = {"polarity": 1, "weight": 0.1}
        config = {"csv_file": "nab_capacity.csv"}

        entry = build_gauge_entry(
            "business_confidence", latest_row, z_df, weight_config, config=config
        )

        assert "long_run_avg" in entry
        assert isinstance(entry["long_run_avg"], float)
        assert "direction" in entry
        assert entry["direction"] in ("STEADY", "RISING", "FALLING")
        assert entry["data_source"] == "NAB Monthly Business Survey"
        assert entry["raw_unit"] == "%"

    def test_business_confidence_no_csv_still_sets_data_source(self, monkeypatch):
        """Business confidence without CSV still sets data_source and raw_unit."""
        monkeypatch.setattr("pipeline.normalize.engine.datetime", MockDatetime)
        from pipeline.normalize.engine import build_gauge_entry

        z_df = _make_z_df()
        latest_row = z_df.iloc[-1]
        weight_config = {"polarity": 1, "weight": 0.1}
        config = {"csv_file": "nab_capacity.csv"}

        entry = build_gauge_entry(
            "business_confidence", latest_row, z_df, weight_config, config=config
        )

        assert entry["data_source"] == "NAB Monthly Business Survey"
        assert entry["raw_unit"] == "%"

    def test_non_special_indicator_no_extra_fields(self, monkeypatch):
        """Non-housing, non-business_confidence entries have no special fields."""
        monkeypatch.setattr("pipeline.normalize.engine.datetime", MockDatetime)
        from pipeline.normalize.engine import build_gauge_entry

        z_df = _make_z_df()
        latest_row = z_df.iloc[-1]
        weight_config = {"polarity": 1, "weight": 0.2}

        entry = build_gauge_entry("wages", latest_row, z_df, weight_config)

        assert "data_source" not in entry
        assert "stale_display" not in entry
        assert "long_run_avg" not in entry
        assert "direction" not in entry


# =============================================================================
# TestBuildAsxFuturesEntry
# =============================================================================


class TestBuildAsxFuturesEntry:
    """Tests for build_asx_futures_entry() — reads ASX CSV and builds entry dict."""

    def test_returns_none_when_csv_missing(self):
        """Returns None when asx_futures.csv not in DATA_DIR (isolated tmp_path)."""
        from pipeline.normalize.engine import build_asx_futures_entry

        result = build_asx_futures_entry()
        assert result is None

    @pytest.mark.parametrize(
        "change_bp,expected_direction",
        [
            (-20, "cut"),
            (-6, "cut"),
            (-5, "hold"),  # boundary: -5 is NOT < -5
            (0, "hold"),
            (5, "hold"),  # boundary: +5 is NOT > +5
            (6, "hike"),
            (20, "hike"),
        ],
    )
    def test_direction_thresholds(self, monkeypatch, change_bp, expected_direction):
        """Direction determined by change_bp: cut < -5, hike > +5, else hold."""
        monkeypatch.setattr("pipeline.normalize.engine.datetime", MockDatetime)
        mock_data = {
            "change_bp": change_bp,
            "implied_rate": 4.10,
            "data_date": "2026-02-20",
            "meeting_date": "2026-04-01",
            "probability_cut": 70.0,
            "probability_hold": 25.0,
            "probability_hike": 5.0,
        }
        with patch(
            "pipeline.normalize.engine.load_asx_futures_csv", return_value=mock_data
        ):
            from pipeline.normalize.engine import build_asx_futures_entry

            result = build_asx_futures_entry()

        assert result is not None
        assert result["direction"] == expected_direction

    def test_required_output_fields_present(self, monkeypatch):
        """All required status.json asx_futures fields are present in output."""
        monkeypatch.setattr("pipeline.normalize.engine.datetime", MockDatetime)
        mock_data = {
            "change_bp": -15,
            "implied_rate": 3.85,
            "data_date": "2026-02-20",
            "meeting_date": "2026-04-01",
            "probability_cut": 80.0,
            "probability_hold": 18.0,
            "probability_hike": 2.0,
        }
        with patch(
            "pipeline.normalize.engine.load_asx_futures_csv", return_value=mock_data
        ):
            from pipeline.normalize.engine import build_asx_futures_entry

            result = build_asx_futures_entry()

        for field in [
            "current_rate",
            "next_meeting",
            "implied_rate",
            "probabilities",
            "direction",
            "data_date",
            "staleness_days",
        ]:
            assert field in result
        for prob_key in ["cut", "hold", "hike"]:
            assert prob_key in result["probabilities"]

    def test_current_rate_computed_from_implied_minus_change(self, monkeypatch):
        """current_rate = implied_rate - change_bp/100."""
        monkeypatch.setattr("pipeline.normalize.engine.datetime", MockDatetime)
        mock_data = {
            "change_bp": -25,
            "implied_rate": 3.85,
            "data_date": "2026-02-20",
            "meeting_date": "2026-04-01",
            "probability_cut": 80.0,
            "probability_hold": 18.0,
            "probability_hike": 2.0,
        }
        with patch(
            "pipeline.normalize.engine.load_asx_futures_csv", return_value=mock_data
        ):
            from pipeline.normalize.engine import build_asx_futures_entry

            result = build_asx_futures_entry()

        # current_rate = 3.85 - (-25/100) = 3.85 + 0.25 = 4.10
        assert abs(result["current_rate"] - 4.10) < 0.01

    def test_meetings_array_processed_when_present(self, monkeypatch):
        """meetings array is processed and meeting_date_label is added."""
        monkeypatch.setattr("pipeline.normalize.engine.datetime", MockDatetime)
        mock_data = {
            "change_bp": -10,
            "implied_rate": 3.90,
            "data_date": "2026-02-20",
            "meeting_date": "2026-04-01",
            "probability_cut": 75.0,
            "probability_hold": 22.0,
            "probability_hike": 3.0,
            "meetings": [
                {
                    "meeting_date": "2026-04-01",
                    "implied_rate": 3.90,
                    "change_bp": -10,
                    "probability_cut": 75.0,
                    "probability_hold": 22.0,
                    "probability_hike": 3.0,
                }
            ],
        }
        with patch(
            "pipeline.normalize.engine.load_asx_futures_csv", return_value=mock_data
        ):
            from pipeline.normalize.engine import build_asx_futures_entry

            result = build_asx_futures_entry()

        assert "meetings" in result
        assert len(result["meetings"]) == 1
        meeting = result["meetings"][0]
        assert "meeting_date_label" in meeting
        # "1 Apr 2026" — day without zero-padding
        assert "Apr 2026" in meeting["meeting_date_label"]

    def test_staleness_days_computed(self, monkeypatch):
        """staleness_days computed as difference from frozen date to data_date."""
        monkeypatch.setattr("pipeline.normalize.engine.datetime", MockDatetime)
        mock_data = {
            "change_bp": 0,
            "implied_rate": 4.10,
            "data_date": "2026-02-20",  # 5 days before frozen 2026-02-25
            "meeting_date": "2026-04-01",
            "probability_cut": 20.0,
            "probability_hold": 75.0,
            "probability_hike": 5.0,
        }
        with patch(
            "pipeline.normalize.engine.load_asx_futures_csv", return_value=mock_data
        ):
            from pipeline.normalize.engine import build_asx_futures_entry

            result = build_asx_futures_entry()

        assert result["staleness_days"] == 5


# =============================================================================
# TestProcessIndicator
# =============================================================================


class TestProcessIndicator:
    """Tests for process_indicator() — end-to-end normalize->zscore->gauge."""

    def test_returns_none_when_normalize_returns_none(self):
        with patch(
            "pipeline.normalize.engine.normalize_indicator", return_value=None
        ):
            from pipeline.normalize.engine import process_indicator

            entry, value = process_indicator(
                "inflation", {}, {"polarity": 1, "weight": 0.2}
            )
        assert entry is None
        assert value is None

    def test_returns_none_for_empty_dataframe(self):
        empty_df = pd.DataFrame()
        with patch(
            "pipeline.normalize.engine.normalize_indicator", return_value=empty_df
        ):
            from pipeline.normalize.engine import process_indicator

            entry, value = process_indicator(
                "wages", {}, {"polarity": 1, "weight": 0.1}
            )
        assert entry is None
        assert value is None

    def test_returns_none_when_no_valid_zscores(self):
        """Returns (None, None) when all z-scores are NaN after compute."""
        df_input = pd.DataFrame(
            {
                "date": pd.date_range("2020-01-01", periods=5, freq="QS"),
                "value": [1.0, 2.0, 3.0, 4.0, 5.0],
            }
        )
        z_df_nan = pd.DataFrame(
            {
                "date": pd.date_range("2020-01-01", periods=5, freq="QS"),
                "value": [1.0, 2.0, 3.0, 4.0, 5.0],
                "z_score": [np.nan] * 5,
                "window_size": [0] * 5,
            }
        )

        with patch(
            "pipeline.normalize.engine.normalize_indicator", return_value=df_input
        ):
            with patch(
                "pipeline.normalize.engine.compute_rolling_zscores",
                return_value=z_df_nan,
            ):
                from pipeline.normalize.engine import process_indicator

                entry, value = process_indicator(
                    "inflation", {}, {"polarity": 1, "weight": 0.2}
                )
        assert entry is None
        assert value is None

    def test_happy_path_returns_entry_dict_and_float(self, monkeypatch):
        """Happy path: returns (entry_dict, float_value)."""
        monkeypatch.setattr("pipeline.normalize.engine.datetime", MockDatetime)
        z_df = _make_z_df()

        with patch(
            "pipeline.normalize.engine.normalize_indicator", return_value=z_df
        ):
            with patch(
                "pipeline.normalize.engine.compute_rolling_zscores",
                return_value=z_df,
            ):
                from pipeline.normalize.engine import process_indicator

                entry, value = process_indicator(
                    "inflation", {}, {"polarity": 1, "weight": 0.2}
                )

        assert entry is not None
        assert isinstance(value, float)
        assert "zone" in entry
        assert "value" in entry
        assert "history" in entry

    def test_adaptive_min_q_for_short_dataframe(self, monkeypatch):
        """Short dfs (< ZSCORE_MIN_YEARS*4) use adaptive min_quarters."""
        monkeypatch.setattr("pipeline.normalize.engine.datetime", MockDatetime)
        short_df = _make_z_df(n_rows=5)

        with patch(
            "pipeline.normalize.engine.normalize_indicator", return_value=short_df
        ):
            with patch(
                "pipeline.normalize.engine.compute_rolling_zscores",
                return_value=short_df,
            ) as mock_zscores:
                # Mock build_gauge_entry so no CSV reads are attempted
                mock_entry = {
                    "value": 55.0,
                    "zone": "neutral",
                    "zone_label": "Balanced",
                    "z_score": 0.3,
                    "raw_value": 3.2,
                    "raw_unit": "% YoY",
                    "weight": 0.1,
                    "polarity": 1,
                    "data_date": "2025-10-01",
                    "staleness_days": 100,
                    "confidence": "HIGH",
                    "interpretation": "test",
                    "history": [50.0],
                }
                with patch(
                    "pipeline.normalize.engine.build_gauge_entry",
                    return_value=mock_entry,
                ):
                    from pipeline.normalize.engine import process_indicator

                    process_indicator(
                        "inflation", {}, {"polarity": 1, "weight": 0.1}
                    )
                    call_kwargs = mock_zscores.call_args
                    assert call_kwargs is not None
                    # min_quarters should be < 20 (the default ZSCORE_MIN_YEARS * 4)
                    _, kwargs = call_kwargs
                    if "min_quarters" in kwargs:
                        assert kwargs["min_quarters"] < 20


# =============================================================================
# TestGenerateStatus
# =============================================================================


class TestGenerateStatus:
    """Tests for generate_status() — top-level orchestrator."""

    def test_status_output_written_to_tmp_path_not_public(
        self, engine_data_dir, monkeypatch
    ):
        """generate_status writes to engine_data_dir path, never to public/data/."""
        monkeypatch.setattr("pipeline.normalize.engine.datetime", MockDatetime)

        with _mock_generate_status_deps():
            from pipeline.normalize.engine import generate_status

            status = generate_status()

        # Written to tmp_path (engine_data_dir), not public/
        assert (engine_data_dir / "status.json").exists()
        assert status is not None

    def test_public_status_json_not_written(self, engine_data_dir, monkeypatch):
        """Public file not touched by generate_status() when engine_data_dir used."""
        monkeypatch.setattr("pipeline.normalize.engine.datetime", MockDatetime)

        real_status = Path("public/data/status.json")
        # Capture modification time if it exists
        mtime_before = real_status.stat().st_mtime if real_status.exists() else None

        with _mock_generate_status_deps():
            from pipeline.normalize.engine import generate_status

            generate_status()

        if real_status.exists() and mtime_before is not None:
            assert real_status.stat().st_mtime == mtime_before

    def test_returns_complete_status_dict(self, engine_data_dir, monkeypatch):
        """Returns dict with all required top-level keys."""
        monkeypatch.setattr("pipeline.normalize.engine.datetime", MockDatetime)

        with _mock_generate_status_deps():
            from pipeline.normalize.engine import generate_status

            status = generate_status()

        for key in [
            "generated_at",
            "pipeline_version",
            "overall",
            "gauges",
            "weights",
            "metadata",
        ]:
            assert key in status

        assert "hawk_score" in status["overall"]
        assert "zone" in status["overall"]
        assert "verdict" in status["overall"]
        assert "confidence" in status["overall"]
        assert "indicators_available" in status["metadata"]
        assert "indicators_missing" in status["metadata"]

    def test_generated_at_ends_with_z(self, engine_data_dir, monkeypatch):
        """generated_at is in ISO format ending with 'Z'."""
        monkeypatch.setattr("pipeline.normalize.engine.datetime", MockDatetime)

        with _mock_generate_status_deps():
            from pipeline.normalize.engine import generate_status

            status = generate_status()

        assert status["generated_at"].endswith("Z")

    def test_overall_confidence_matches_gauge_confidence(
        self, engine_data_dir, monkeypatch
    ):
        """overall.confidence is set based on minimum confidence among gauges."""
        monkeypatch.setattr("pipeline.normalize.engine.datetime", MockDatetime)

        with _mock_generate_status_deps(confidence="MEDIUM"):
            from pipeline.normalize.engine import generate_status

            status = generate_status()

        assert status["overall"]["confidence"] == "MEDIUM"

    def test_empty_gauges_returns_low_confidence(self, engine_data_dir, monkeypatch):
        """When all process_indicator calls return None, confidence is LOW."""
        monkeypatch.setattr("pipeline.normalize.engine.datetime", MockDatetime)

        with _mock_generate_status_deps(all_none=True):
            from pipeline.normalize.engine import generate_status

            status = generate_status()

        assert status["overall"]["confidence"] == "LOW"
        assert status["metadata"]["indicators_available"] == 0

    def test_asx_futures_included_when_data_available(
        self, engine_data_dir, monkeypatch
    ):
        """asx_futures key added to status when build_asx_futures_entry returns data."""
        monkeypatch.setattr("pipeline.normalize.engine.datetime", MockDatetime)

        mock_weights = {
            "inflation": {"weight": 0.25, "polarity": 1},
        }

        with patch("pipeline.normalize.engine.load_weights", return_value=mock_weights):
            with patch(
                "pipeline.normalize.engine.process_indicator", return_value=(None, None)
            ):
                with patch(
                    "pipeline.normalize.engine.compute_hawk_score", return_value=50.0
                ):
                    with patch(
                        "pipeline.normalize.engine.classify_zone",
                        return_value=("neutral", "Balanced"),
                    ):
                        with patch(
                            "pipeline.normalize.engine.generate_verdict",
                            return_value="Balanced",
                        ):
                            with patch(
                                "pipeline.normalize.engine.load_asx_futures_csv",
                                return_value={
                                    "change_bp": -15,
                                    "implied_rate": 4.10,
                                    "data_date": "2026-02-20",
                                    "meeting_date": "2026-04-01",
                                    "probability_cut": 80.0,
                                    "probability_hold": 18.0,
                                    "probability_hike": 2.0,
                                },
                            ):
                                from pipeline.normalize.engine import generate_status

                                status = generate_status()

        assert "asx_futures" in status

    def test_status_json_written_as_valid_json(self, engine_data_dir, monkeypatch):
        """status.json written to tmp_path is valid parseable JSON."""
        import json

        monkeypatch.setattr("pipeline.normalize.engine.datetime", MockDatetime)

        with _mock_generate_status_deps():
            from pipeline.normalize.engine import generate_status

            generate_status()

        json_file = engine_data_dir / "status.json"
        assert json_file.exists()
        with open(json_file) as f:
            parsed = json.load(f)
        assert "overall" in parsed
