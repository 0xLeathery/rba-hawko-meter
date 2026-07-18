"""
Generate frontend-consumable JSON from pipeline CSVs.

- public/data/rates.json — RBA cash rate history + change annotations
- public/data/meetings.json — RBA Board schedule with computed next_meeting
"""

from __future__ import annotations

import csv
import json
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from pipeline.config import DATA_DIR, STATUS_OUTPUT

PUBLIC_DATA_DIR = STATUS_OUTPUT.parent
SYDNEY_TZ = ZoneInfo("Australia/Sydney")


def get_first_tuesday(year: int, month: int) -> date:
    """Return the first Tuesday of the given month/year."""
    d = date(year, month, 1)
    days_until_tuesday = (1 - d.weekday()) % 7
    return d + timedelta(days=days_until_tuesday)


def generate_rates_json(
    data_dir: Path | None = None,
    public_data_dir: Path | None = None,
) -> dict | None:
    """Transform rba_cash_rate.csv into public/data/rates.json."""
    data_dir = data_dir or DATA_DIR
    public_data_dir = public_data_dir or PUBLIC_DATA_DIR
    csv_path = Path(data_dir) / "rba_cash_rate.csv"

    if not csv_path.exists():
        print(f"WARNING: {csv_path} not found. Skipping rates.json generation.")
        return None

    rows = []
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                "date": row["date"],
                "value": float(row["value"]),
                "source": row["source"],
            })

    rows.sort(key=lambda r: r["date"])

    if not rows:
        print("WARNING: rba_cash_rate.csv is empty. Skipping rates.json.")
        return None

    dates = [r["date"] for r in rows]
    rates = [round(r["value"], 2) for r in rows]

    rate_changes = []
    for i in range(1, len(rows)):
        prev_rate = round(rows[i - 1]["value"], 2)
        curr_rate = round(rows[i]["value"], 2)
        if prev_rate != curr_rate:
            change = round(curr_rate - prev_rate, 2)
            rate_changes.append({
                "date": rows[i]["date"],
                "from": prev_rate,
                "to": curr_rate,
                "direction": "up" if change > 0 else "down",
                "amount": round(abs(change), 2),
            })

    result = {
        "last_updated": dates[-1],
        "current_rate": rates[-1],
        "source": "RBA",
        "history": {"dates": dates, "rates": rates},
        "rate_changes": rate_changes,
    }

    public_data_dir = Path(public_data_dir)
    public_data_dir.mkdir(parents=True, exist_ok=True)
    output_path = public_data_dir / "rates.json"
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    print(f"Created {output_path}")
    print(f"  Current rate: {result['current_rate']}%")
    print(f"  Data points: {len(dates)}")
    print(f"  Rate changes: {len(rate_changes)}")
    return result


def generate_meetings_json(
    public_data_dir: Path | None = None,
    *,
    today: date | None = None,
    now: datetime | None = None,
) -> dict:
    """Generate RBA Board meeting schedule as public/data/meetings.json.

    next_meeting is the first scheduled meeting strictly after ``now``
    (Sydney). RBA Board meets first Tuesday of each month except January.
    """
    public_data_dir = Path(public_data_dir or PUBLIC_DATA_DIR)
    today = today or date.today()
    now_sydney = now or datetime.now(SYDNEY_TZ)
    if now_sydney.tzinfo is None:
        now_sydney = now_sydney.replace(tzinfo=SYDNEY_TZ)

    current_year = today.year
    next_year = current_year + 1
    meeting_months = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

    all_meetings = []
    for year in [current_year, next_year]:
        for month in meeting_months:
            meeting_date = get_first_tuesday(year, month)
            meeting_dt = datetime(
                meeting_date.year,
                meeting_date.month,
                meeting_date.day,
                14,
                30,
                0,
                tzinfo=SYDNEY_TZ,
            )
            utc_offset = meeting_dt.utcoffset()
            if utc_offset and utc_offset.total_seconds() == 11 * 3600:
                tz_label = "AEDT"
            else:
                tz_label = "AEST"

            all_meetings.append({
                "date": meeting_dt.isoformat(),
                "display_date": meeting_dt.strftime("%-d %B %Y"),
                "display_time": f"2:30pm {tz_label}",
            })

    next_meeting = None
    for m in all_meetings:
        meeting_dt = datetime.fromisoformat(m["date"])
        if meeting_dt > now_sydney:
            next_meeting = m
            break
    if next_meeting is None:
        next_meeting = all_meetings[-1]

    result = {
        "next_meeting": next_meeting,
        f"meetings_{current_year}": [
            m for m in all_meetings
            if datetime.fromisoformat(m["date"]).year == current_year
        ],
        f"meetings_{next_year}": [
            m for m in all_meetings
            if datetime.fromisoformat(m["date"]).year == next_year
        ],
    }

    public_data_dir.mkdir(parents=True, exist_ok=True)
    output_path = public_data_dir / "meetings.json"
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    print(f"Created {output_path}")
    print(f"  Next meeting: {next_meeting['display_date']}")
    return result


def generate_frontend_data(
    data_dir: Path | None = None,
    public_data_dir: Path | None = None,
    *,
    meetings_only: bool = False,
) -> dict:
    """Generate rates + meetings (or meetings only for the daily job)."""
    public_data_dir = Path(public_data_dir or PUBLIC_DATA_DIR)
    public_data_dir.mkdir(parents=True, exist_ok=True)

    result: dict = {}
    if not meetings_only:
        result["rates"] = generate_rates_json(data_dir, public_data_dir)
    result["meetings"] = generate_meetings_json(public_data_dir)
    return result
