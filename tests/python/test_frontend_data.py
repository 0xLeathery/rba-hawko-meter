"""
Unit tests for pipeline.normalize.frontend_data.
"""

from datetime import date, datetime
from zoneinfo import ZoneInfo

from pipeline.normalize.frontend_data import (
    generate_frontend_data,
    generate_meetings_json,
    generate_rates_json,
    get_first_tuesday,
)

SYDNEY = ZoneInfo("Australia/Sydney")


class TestGetFirstTuesday:
    def test_known_date(self):
        # 2026-08-01 is Saturday → first Tuesday is 4 Aug
        assert get_first_tuesday(2026, 8) == date(2026, 8, 4)

    def test_month_starts_on_tuesday(self):
        # 2026-09-01 is Tuesday
        assert get_first_tuesday(2026, 9) == date(2026, 9, 1)


class TestGenerateMeetingsJson:
    def test_next_meeting_is_in_the_future(self, tmp_path):
        # Mid-July 2026 → next board meeting first Tue of August = 4 Aug 2026
        today = date(2026, 7, 18)
        now = datetime(2026, 7, 18, 12, 0, tzinfo=SYDNEY)
        result = generate_meetings_json(
            public_data_dir=tmp_path, today=today, now=now
        )

        nm = result["next_meeting"]
        assert nm["date"].startswith("2026-08-04")
        assert "August 2026" in nm["display_date"]
        assert datetime.fromisoformat(nm["date"]) > now

        out = tmp_path / "meetings.json"
        assert out.exists()
        assert "meetings_2026" in result
        assert "meetings_2027" in result

    def test_after_meeting_day_selects_following_month(self, tmp_path):
        # After 4 Aug 2026 14:30 Sydney → next is Sept
        now = datetime(2026, 8, 4, 15, 0, tzinfo=SYDNEY)
        result = generate_meetings_json(
            public_data_dir=tmp_path,
            today=date(2026, 8, 4),
            now=now,
        )
        assert result["next_meeting"]["date"].startswith("2026-09-01")

    def test_does_not_freeze_on_march_2026(self, tmp_path):
        now = datetime(2026, 7, 18, 12, 0, tzinfo=SYDNEY)
        result = generate_meetings_json(
            public_data_dir=tmp_path, today=date(2026, 7, 18), now=now
        )
        assert not result["next_meeting"]["date"].startswith("2026-03-03")


class TestGenerateRatesJson:
    def test_builds_rates_from_csv(self, tmp_path):
        data_dir = tmp_path / "data"
        public_dir = tmp_path / "public"
        data_dir.mkdir()
        (data_dir / "rba_cash_rate.csv").write_text(
            "date,value,source\n"
            "2026-02-04,3.85,RBA\n"
            "2026-03-18,4.10,RBA\n"
            "2026-05-06,4.35,RBA\n",
            encoding="utf-8",
        )

        result = generate_rates_json(data_dir=data_dir, public_data_dir=public_dir)
        assert result is not None
        assert result["current_rate"] == 4.35
        assert result["last_updated"] == "2026-05-06"
        assert len(result["rate_changes"]) == 2
        assert (public_dir / "rates.json").exists()

    def test_missing_csv_returns_none(self, tmp_path):
        result = generate_rates_json(
            data_dir=tmp_path / "missing",
            public_data_dir=tmp_path / "public",
        )
        assert result is None


class TestGenerateFrontendData:
    def test_meetings_only_skips_rates(self, tmp_path):
        result = generate_frontend_data(
            public_data_dir=tmp_path, meetings_only=True
        )
        assert "meetings" in result
        assert "rates" not in result
        assert (tmp_path / "meetings.json").exists()
        assert not (tmp_path / "rates.json").exists()
