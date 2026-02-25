#!/usr/bin/env python3
"""
Per-module coverage enforcement for pipeline/ modules.

Reads .coverage.json (written by pytest-cov) and checks that every pipeline/
module meets the specified minimum coverage threshold. Designed for use in
CI scripts and pre-push hooks.

Usage:
    python scripts/check_coverage.py --min 85
    python scripts/check_coverage.py --min 0   # always passes (sanity check)

Exit codes:
    0 — All modules at or above threshold.
    1 — At least one module below threshold, or .coverage.json missing.
"""

import argparse
import json
import os
import sys
from pathlib import Path


def _is_tty() -> bool:
    """Check if stdout is a terminal (for ANSI color output)."""
    return sys.stdout.isatty()


# ANSI color codes — only used when outputting to a terminal.
_RED = "\033[91m" if _is_tty() else ""
_GREEN = "\033[92m" if _is_tty() else ""
_BOLD = "\033[1m" if _is_tty() else ""
_RESET = "\033[0m" if _is_tty() else ""


def load_coverage(coverage_path: Path) -> dict:
    """Load and return the .coverage.json data."""
    if not coverage_path.exists():
        print(
            f"{_RED}ERROR: {coverage_path} not found. "
            f"Run pytest first.{_RESET}",
            file=sys.stderr,
        )
        sys.exit(1)

    with open(coverage_path) as f:
        return json.load(f)


def get_pipeline_modules(data: dict) -> list[dict]:
    """
    Extract per-module coverage for pipeline/ files.

    Filters to files starting with 'pipeline/' that have at least one
    executable statement (excludes empty __init__.py files).
    """
    modules = []
    for filepath, info in data.get("files", {}).items():
        if not filepath.startswith("pipeline/"):
            continue
        summary = info.get("summary", {})
        num_statements = summary.get("num_statements", 0)
        if num_statements == 0:
            continue
        modules.append(
            {
                "path": filepath,
                "name": os.path.basename(filepath),
                "percent": summary.get("percent_covered", 0.0),
                "statements": num_statements,
            }
        )
    # Sort by module name for stable output
    modules.sort(key=lambda m: m["name"])
    return modules


def print_failure_table(modules: list[dict], threshold: float) -> None:
    """Print a diff table showing modules below the threshold."""
    failing = [m for m in modules if m["percent"] < threshold]
    if not failing:
        return

    print(f"\n{_RED}{_BOLD}Coverage below {threshold:.0f}% threshold:{_RESET}\n")
    print(
        f"  {'Module':<42} {'Actual':>7}  {'Target':>7}  {'Gap':>7}"
    )
    print(f"  {'-' * 42} {'-' * 7}  {'-' * 7}  {'-' * 7}")

    for m in failing:
        gap = m["percent"] - threshold
        print(
            f"  {_RED}{m['name']:<42} {m['percent']:>6.0f}%  "
            f"{threshold:>6.0f}%  {gap:>+6.0f}%{_RESET}"
        )

    print()


def print_success_table(modules: list[dict], threshold: float) -> None:
    """Print a summary table showing all modules at or above threshold."""
    print(
        f"\n{_GREEN}{_BOLD}All pipeline/ modules at or above "
        f"{threshold:.0f}%:{_RESET}\n"
    )
    for m in modules:
        print(f"  {_GREEN}{m['name']:<42} {m['percent']:>6.0f}%{_RESET}")
    print()


def main() -> None:
    """Entry point: parse args, load coverage, check threshold, report."""
    parser = argparse.ArgumentParser(
        description="Check per-module coverage for pipeline/ modules."
    )
    parser.add_argument(
        "--min",
        type=float,
        default=85.0,
        dest="threshold",
        help="Minimum coverage percentage per module (default: 85)",
    )
    args = parser.parse_args()

    # Find .coverage.json at project root
    # Walk up from script location to find project root
    project_root = Path(__file__).resolve().parent.parent
    coverage_path = project_root / ".coverage.json"

    data = load_coverage(coverage_path)
    modules = get_pipeline_modules(data)

    if not modules:
        print(
            f"{_RED}ERROR: No pipeline/ modules found in "
            f"{coverage_path}{_RESET}",
            file=sys.stderr,
        )
        sys.exit(1)

    # Check threshold
    failing = [m for m in modules if m["percent"] < args.threshold]

    if failing:
        print_failure_table(modules, args.threshold)
        sys.exit(1)
    else:
        print_success_table(modules, args.threshold)
        sys.exit(0)


if __name__ == "__main__":
    main()
