#!/usr/bin/env python3
"""
Import picks from First TD Master.csv into the Fast6 database.

CSV format: Week, Gameday, Picker, Vistor, Home, Player, 1st TD Odds
- Handles "Vistor" typo (renamed to Visitor)
- Maps "WC" week to 19 (wildcard)
- Normalizes team names (San Fran->SF, Detriot->DET, etc.)

Usage: python -m backend.scripts.import_first_td_csv [path/to/First TD Master.csv]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pandas as pd
from backend.database import (
    add_user,
    get_all_users,
    add_week,
    get_week_by_season_week,
    add_pick,
    get_db_connection,
)
from backend.config import TEAM_ABBR_MAP

# Extra team name mappings for CSV variants
TEAM_ALIASES = {
    "vistor": None,  # typo - will use Visitor column
    "san fran": "SF",
    "san francisco": "SF",
    "detriot": "DET",
    "detroit": "DET",
    "la chargers": "LAC",
    "la rams": "LA",
    "ny giants": "NYG",
    "ny jets": "NYJ",
    "new england": "NE",
    "green bay": "GB",
    "kansas city": "KC",
    "las vegas": "LV",
    "tampa bay": "TB",
    "jacksonville": "JAX",
    "washington": "WAS",
    "indianapolis": "IND",
    "houston": "HOU",
    "texans": "HOU",
    "seattle": "SEA",
    "arizona": "ARI",
    "minnesota": "MIN",
    "chicago": "CHI",
    "philadelphia": "PHI",
    "pittsburgh": "PIT",
    "cincinnati": "CIN",
    "baltimore": "BAL",
    "buffalo": "BUF",
    "miami": "MIA",
    "atlanta": "ATL",
    "dallas": "DAL",
    "denver": "DEN",
    "carolina": "CAR",
}

VALID_TEAMS = set(TEAM_ABBR_MAP.values())


def normalize_team(raw: str) -> str | None:
    """Normalize team name to abbreviation."""
    if pd.isna(raw) or not raw:
        return None
    s = str(raw).strip().lower()
    if s in TEAM_ALIASES:
        return TEAM_ALIASES[s]
    # Check full names
    for full_name, abbr in TEAM_ABBR_MAP.items():
        if s == full_name.lower():
            return abbr
        if s in full_name.lower() or full_name.lower().startswith(s):
            return abbr
    # Already abbr?
    if s.upper() in VALID_TEAMS:
        return s.upper()
    return None


def parse_week(val) -> int | None:
    """Parse week: 1-18 or 'WC' -> 19."""
    if pd.isna(val):
        return None
    s = str(val).strip().upper()
    if s == "WC":
        return 19
    try:
        w = int(float(s))
        if 1 <= w <= 22:
            return w
    except (ValueError, TypeError):
        pass
    return None


def parse_odds(val) -> float:
    """Parse American odds."""
    if pd.isna(val) or val == "":
        return -110.0
    try:
        return float(val)
    except (ValueError, TypeError):
        return -110.0


def main() -> None:
    season = 2025
    csv_path = sys.argv[1] if len(sys.argv) > 1 else Path(__file__).parent.parent.parent / "archive/data/First TD Master.csv"

    if not Path(csv_path).exists():
        print(f"Error: CSV not found: {csv_path}")
        sys.exit(1)

    df = pd.read_csv(csv_path)
    # Fix column name
    if "Vistor" in df.columns and "Visitor" not in df.columns:
        df = df.rename(columns={"Vistor": "Visitor"})

    required = ["Week", "Picker", "Visitor", "Home", "Player"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        print(f"Error: Missing columns: {missing}")
        sys.exit(1)

    users_by_name = {u["name"].lower(): u for u in get_all_users()}
    inserted = 0
    skipped = 0
    errors = []

    for idx, row in df.iterrows():
        row_num = idx + 2
        week = parse_week(row.get("Week"))
        if week is None:
            errors.append(f"Row {row_num}: Invalid week {row.get('Week')}")
            continue

        picker = str(row.get("Picker", "")).strip()
        if not picker:
            errors.append(f"Row {row_num}: Missing picker")
            continue

        visitor = normalize_team(row.get("Visitor"))
        home = normalize_team(row.get("Home"))
        if not visitor or not home:
            errors.append(f"Row {row_num}: Invalid teams Visitor={row.get('Visitor')} Home={row.get('Home')}")
            continue

        player = str(row.get("Player", "")).strip()
        if not player:
            errors.append(f"Row {row_num}: Missing player")
            continue

        odds = parse_odds(row.get("1st TD Odds"))
        game_id = f"{season}_{week:02d}_{visitor}_{home}"

        # Player team: use home as default (CSV doesn't specify; leaderboard/analytics still work)
        player_team = home

        # Get or create user
        picker_lower = picker.lower()
        if picker_lower in users_by_name:
            user_id = users_by_name[picker_lower]["id"]
        else:
            try:
                user_id = add_user(picker, None, False)
                users_by_name[picker_lower] = {"id": user_id, "name": picker}
                print(f"  Created user: {picker}")
            except ValueError:
                # User exists, fetch
                users_by_name[picker_lower] = next(u for u in get_all_users() if u["name"].lower() == picker_lower)
                user_id = users_by_name[picker_lower]["id"]

        # Get or create week
        week_rec = get_week_by_season_week(season, week)
        if not week_rec:
            week_id = add_week(season, week)
        else:
            week_id = week_rec["id"]

        # Check duplicate
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM picks WHERE user_id = ? AND week_id = ? AND player_name = ?",
            (user_id, week_id, player),
        )
        if cursor.fetchone()[0] > 0:
            skipped += 1
            conn.close()
            continue
        conn.close()

        # Insert pick
        add_pick(user_id, week_id, player_team, player, odds, game_id=game_id)
        inserted += 1
        print(f"  Row {row_num}: {picker} - {player} ({visitor}@{home}) W{week} @ {odds}")

    print(f"\nDone. Inserted {inserted}, skipped {skipped} duplicates.")
    if errors:
        print(f"Errors ({len(errors)}):")
        for e in errors[:15]:
            print(f"  {e}")
        if len(errors) > 15:
            print(f"  ... and {len(errors) - 15} more")


if __name__ == "__main__":
    main()
