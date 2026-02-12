"""
Seed games table for development. Prefer running seed_all.py which seeds everything.
Usage: python -m backend.scripts.seed_games
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import sqlite3

from backend.database.connection import get_db_path

db_path = get_db_path()
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Sample data for Season 2025 Week 1 (Current context)
games = [
    {
        "id": "2025_01_KC_BAL",
        "season": 2025,
        "week": 1,
        "game_date": "2025-09-05",
        "home_team": "KC",
        "away_team": "BAL",
        "home_score": 24,
        "away_score": 21,
        "status": "in_progress" # For Live Action demo
    },
    {
        "id": "2025_01_PHI_GB",
        "season": 2025,
        "week": 1,
        "game_date": "2025-09-06",
        "home_team": "PHI",
        "away_team": "GB",
        "home_score": None,
        "away_score": None,
        "status": "scheduled"
    },
     {
        "id": "2025_01_CLE_DAL",
        "season": 2025,
        "week": 1,
        "game_date": "2025-09-08",
        "home_team": "CLE",
        "away_team": "DAL",
        "home_score": None,
        "away_score": None,
        "status": "scheduled"
    }
]

print(f"Seeding {len(games)} games...")

for g in games:
    try:
        cursor.execute(
            """INSERT OR REPLACE INTO games 
               (id, season, week, game_date, home_team, away_team, home_score, away_score, status) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (g["id"], g["season"], g["week"], g["game_date"], 
             g["home_team"], g["away_team"], g["home_score"], g["away_score"], g["status"])
        )
        print(f"Seeded {g['id']}")
    except Exception as e:
        print(f"Error seeding {g['id']}: {e}")

conn.commit()
conn.close()
print("Seeding complete.")
