#!/usr/bin/env python3
"""
Seed development database with users, weeks, games, picks, and results.
Use this to populate the site with sample data for local testing.

Usage: python -m backend.scripts.seed_all

Prerequisites:
- Run migrations first (happens automatically on backend startup)
- Backend does not need to be running for this script
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.database import (
    add_user,
    get_user_by_name,
    add_week,
    get_week_by_season_week,
    add_pick,
    add_result,
    get_db_context,
)


def seed_users() -> dict:
    """Create test users. Returns mapping of name -> user_id."""
    users = {}
    for name, email, is_admin in [
        ("Phil", None, True),
        ("Alice", "alice@example.com", False),
        ("Bob", "bob@example.com", False),
    ]:
        existing = get_user_by_name(name)
        if existing:
            users[name] = existing["id"]
            print(f"  User '{name}' exists (ID: {users[name]})")
        else:
            users[name] = add_user(name, email, is_admin)
            print(f"  Added user '{name}' (ID: {users[name]})")
    return users


def seed_weeks() -> dict:
    """Create weeks 1-18 for season 2025. Returns mapping of (season, week) -> week_id."""
    weeks = {}
    for week in range(1, 19):
        season, w = 2025, week
        existing = get_week_by_season_week(season, w)
        if existing:
            weeks[(season, w)] = existing["id"]
            if week <= 2:
                print(f"  Week {season} W{w} exists (ID: {weeks[(season, w)]})")
        else:
            weeks[(season, w)] = add_week(season, w)
            print(f"  Added week {season} W{w} (ID: {weeks[(season, w)]})")
    if len(weeks) > 2:
        print(f"  ... {len(weeks)} weeks total for season 2025")
    return weeks


def seed_games() -> None:
    """Insert sample games if games table exists."""
    games = [
        ("2025_01_KC_BAL", 2025, 1, "2025-09-05", "KC", "BAL", 24, 21, "final"),
        ("2025_01_PHI_GB", 2025, 1, "2025-09-06", "PHI", "GB", None, None, "scheduled"),
        ("2025_01_CLE_DAL", 2025, 1, "2025-09-08", "CLE", "DAL", None, None, "scheduled"),
        ("2025_02_KC_CIN", 2025, 2, "2025-09-12", "KC", "CIN", None, None, "scheduled"),
    ]
    with get_db_context() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='games'")
            if not cursor.fetchone():
                print("  Games table not found, skipping")
                return
        except Exception:
            print("  Games table not found, skipping")
            return

        for g in games:
            try:
                cursor.execute(
                    """INSERT OR IGNORE INTO games
                       (id, season, week, game_date, home_team, away_team, home_score, away_score, status)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    g,
                )
                if cursor.rowcount > 0:
                    print(f"  Added game {g[0]}")
            except Exception as e:
                print(f"  Skip game {g[0]}: {e}")
    print("  Games seeded")


def seed_picks_and_results(users: dict, weeks: dict) -> None:
    """Create picks and grade them with results."""
    # (username, season, week, team, player, odds, game_id, is_correct, any_time_td)
    picks_data = [
        ("Phil", 2025, 1, "KC", "Patrick Mahomes", 150, "2025_01_KC_BAL", True, False),
        ("Phil", 2025, 1, "PHI", "Jalen Hurts", 200, "2025_01_PHI_GB", None, None),
        ("Alice", 2025, 1, "KC", "Patrick Mahomes", 150, "2025_01_KC_BAL", True, False),
        ("Alice", 2025, 1, "BAL", "Lamar Jackson", 250, "2025_01_KC_BAL", False, True),
        ("Bob", 2025, 1, "SF", "Jauan Jennings", 300, "2025_01_KC_BAL", False, False),
        ("Bob", 2025, 1, "CLE", "Deshaun Watson", 220, "2025_01_CLE_DAL", None, None),
        ("Phil", 2025, 2, "KC", "Travis Kelce", 180, "2025_02_KC_CIN", None, None),
        ("Alice", 2025, 2, "CIN", "Ja'Marr Chase", 200, "2025_02_KC_CIN", None, None),
    ]

    for row in picks_data:
        username, season, week, team, player, odds, game_id, is_correct, any_time_td = row
        if username not in users or (season, week) not in weeks:
            continue
        user_id = users[username]
        week_id = weeks[(season, week)]

        with get_db_context() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM picks WHERE user_id = ? AND week_id = ? AND team = ? AND player_name = ?",
                (user_id, week_id, team, player),
            )
            existing = cursor.fetchone()

        if existing:
            pick_id = existing[0]
            print(f"  Pick exists: {username} {player} W{week}")
        else:
            pick_id = add_pick(user_id, week_id, team, player, odds, game_id=game_id)
            print(f"  Added pick: {username} {player} @ {odds} (ID: {pick_id})")

        if is_correct is not None and any_time_td is not None:
            with get_db_context() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM results WHERE pick_id = ?", (pick_id,))
                has_result = cursor.fetchone()
            if not has_result:
                # actual_return: loss = -stake, win = stake * (odds/100) profit
                from backend.config import config
                stake = config.ROI_STAKE
                actual_return = stake * (odds / 100.0) if is_correct else -stake
                add_result(pick_id, player, is_correct, actual_return, any_time_td)
                print(f"    Graded: correct={is_correct}, any_time={any_time_td}")


def main() -> None:
    print("Seeding Fast6 development database...")
    print("\n1. Users:")
    users = seed_users()
    print("\n2. Weeks:")
    weeks = seed_weeks()
    print("\n3. Games:")
    seed_games()
    print("\n4. Picks & Results:")
    seed_picks_and_results(users, weeks)
    print("\nSeed complete. Start the backend and visit the site to see data.")


if __name__ == "__main__":
    main()
