#!/usr/bin/env python3
"""
Ensure weeks 1-18 exist for a season. Use when the weeks table is the source of truth
and the public Stubs page needs a full week list.

Usage:
  python -m backend.scripts.ensure_weeks
  python -m backend.scripts.ensure_weeks --season 2026
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.database import add_week, get_week_by_season_week


def main() -> None:
    parser = argparse.ArgumentParser(description="Ensure weeks 1-18 exist for a season")
    parser.add_argument("--season", type=int, default=2025, help="Season year (default: 2025)")
    args = parser.parse_args()

    season = args.season
    added = 0
    for week in range(1, 19):
        existing = get_week_by_season_week(season, week)
        if not existing:
            add_week(season, week)
            added += 1
            print(f"  Added week {season} W{week}")

    if added == 0:
        print(f"  All weeks 1-18 for season {season} already exist.")
    else:
        print(f"  Added {added} week(s) for season {season}.")


if __name__ == "__main__":
    main()
