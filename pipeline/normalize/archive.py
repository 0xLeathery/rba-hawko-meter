"""
Snapshot archival and temporal delta injection for the data pipeline.

Provides three functions:
  - save_snapshot: Archive current status dict as a dated JSON file
  - read_previous_snapshot: Load the most recent eligible prior snapshot
  - inject_deltas: Enrich status dict with delta fields from prior snapshot

All functions use Python standard library only (json, pathlib, datetime).
"""

import json
from datetime import UTC, datetime
from pathlib import Path


def save_snapshot(status_dict, snapshots_dir, max_entries=52):
    """
    Save a dated snapshot of the status dict and maintain a rolling index.

    Creates the snapshots directory if it doesn't exist. Writes the status
    dict to a file named YYYY-MM-DD.json. Updates index.json with an ordered
    list of snapshot dates. Enforces a rolling cap by deleting the oldest
    entries when the count exceeds max_entries.

    Args:
        status_dict: The complete status.json dict to archive.
        snapshots_dir: Path to the snapshots directory.
        max_entries: Maximum number of snapshots to retain (default 52).
    """
    snapshots_dir = Path(snapshots_dir)
    snapshots_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.now(UTC).strftime("%Y-%m-%d")
    snapshot_path = snapshots_dir / f"{today}.json"

    # Write snapshot file
    with open(snapshot_path, "w") as f:
        json.dump(status_dict, f, indent=2)

    # Load or create index
    index_path = snapshots_dir / "index.json"
    if index_path.exists():
        with open(index_path) as f:
            index = json.load(f)
    else:
        index = {"snapshots": []}

    # Add today if not already present (idempotent)
    if today not in index["snapshots"]:
        index["snapshots"].append(today)
        index["snapshots"].sort()

    # Enforce rolling cap — delete oldest entries
    while len(index["snapshots"]) > max_entries:
        oldest = index["snapshots"].pop(0)
        oldest_path = snapshots_dir / f"{oldest}.json"
        if oldest_path.exists():
            oldest_path.unlink()

    # Write updated index
    with open(index_path, "w") as f:
        json.dump(index, f, indent=2)


def read_previous_snapshot(snapshots_dir, min_age_days=5):
    """
    Read the most recent snapshot that is at least min_age_days old.

    Walks backwards through the sorted index to find the newest snapshot
    that qualifies. Skips entries whose files are missing on disk.

    Returns None if no index exists, the index is empty, or no snapshot
    meets the minimum age requirement.

    Args:
        snapshots_dir: Path to the snapshots directory.
        min_age_days: Minimum age in days for a snapshot to be eligible.

    Returns:
        The parsed snapshot dict, or None if no eligible snapshot found.
    """
    snapshots_dir = Path(snapshots_dir)
    index_path = snapshots_dir / "index.json"

    if not index_path.exists():
        return None

    with open(index_path) as f:
        index = json.load(f)

    snapshots = index.get("snapshots", [])
    if not snapshots:
        return None

    today = datetime.now(UTC).date()

    # Walk backwards through sorted dates to find most recent eligible
    for date_str in reversed(snapshots):
        snap_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        age = (today - snap_date).days
        if age >= min_age_days:
            snap_path = snapshots_dir / f"{date_str}.json"
            if snap_path.exists():
                with open(snap_path) as f:
                    return json.load(f)

    return None


def inject_deltas(status_dict, previous_snapshot):
    """
    Inject delta fields into the status dict by comparing with a prior snapshot.

    When previous_snapshot is None (first run), this is a no-op — no delta
    fields are added, and the frontend handles their absence gracefully.

    Adds to overall block: previous_hawk_score, hawk_score_delta.
    Adds to each gauge: previous_value, delta, direction (up/down/unchanged).

    All deltas are rounded to 1 decimal place.

    Args:
        status_dict: The current status dict to enrich (modified in place).
        previous_snapshot: The prior snapshot dict, or None if first run.
    """
    if previous_snapshot is None:
        return

    # Overall block deltas
    prev_overall = previous_snapshot.get("overall", {})
    prev_score = prev_overall.get("hawk_score")
    if prev_score is not None:
        curr_score = status_dict["overall"]["hawk_score"]
        status_dict["overall"]["previous_hawk_score"] = prev_score
        status_dict["overall"]["hawk_score_delta"] = round(
            curr_score - prev_score, 1
        )

    # Per-gauge deltas
    prev_gauges = previous_snapshot.get("gauges", {})
    for name, gauge in status_dict.get("gauges", {}).items():
        prev_gauge = prev_gauges.get(name)
        if prev_gauge is None:
            continue  # New indicator — no previous value available

        prev_value = prev_gauge.get("value")
        if prev_value is None:
            continue  # Previous gauge has no value — skip

        curr_value = gauge["value"]
        delta = round(curr_value - prev_value, 1)

        gauge["previous_value"] = prev_value
        gauge["delta"] = delta

        # Use delta_direction (not direction) to avoid collision with
        # business_confidence's existing direction field (RISING/FALLING/STEADY)
        if delta > 0:
            gauge["delta_direction"] = "up"
        elif delta < 0:
            gauge["delta_direction"] = "down"
        else:
            gauge["delta_direction"] = "unchanged"
