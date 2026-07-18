"""
CLI entry for frontend JSON generation.

Canonical implementation lives in pipeline.normalize.frontend_data.
"""

from pipeline.normalize.frontend_data import (
    generate_frontend_data,
    generate_meetings_json,
    generate_rates_json,
)

__all__ = [
    "generate_frontend_data",
    "generate_meetings_json",
    "generate_rates_json",
]


def main():
    print("Generating frontend data files...\n")
    generate_frontend_data()
    print("\nDone.")


if __name__ == "__main__":
    main()
