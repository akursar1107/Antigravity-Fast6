"""
Touchdown sync service.
Materializes TD scorers from nflreadpy PBP into touchdowns table for final games.
"""

import logging
from typing import Dict, List
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    import nflreadpy as nfl
    HAS_NFLREADPY = True
except ImportError:
    HAS_NFLREADPY = False
    logger.warning("nflreadpy not available, TD sync disabled")


def _validate_game_id(game_id: str) -> bool:
    """Validate game_id format: season_week_away_home (e.g. 2025_01_TB_ATL)."""
    if not game_id or not isinstance(game_id, str):
        return False
    parts = game_id.split("_")
    if len(parts) < 4:
        return False
    try:
        year = int(parts[0])
        week = int(parts[1])
        if year < 1999 or year > 2100 or week < 1 or week > 22:
            return False
    except (ValueError, IndexError):
        return False
    return True


def sync_touchdowns_for_season(season: int) -> Dict[str, int]:
    """
    Sync touchdown scorers for all final games in a season.
    Loads PBP from nflreadpy, derives TDs, upserts into touchdowns table.

    Returns:
        Dict with: inserted, updated, games_synced, errors
    """
    if not HAS_NFLREADPY:
        logger.error("Cannot sync touchdowns: nflreadpy not installed")
        return {"inserted": 0, "updated": 0, "games_synced": 0, "errors": 1}

    stats = {"inserted": 0, "updated": 0, "games_synced": 0, "errors": 0}

    try:
        from backend.database import get_db_connection
        from backend.analytics.nfl_data import load_data, get_touchdowns

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='touchdowns'"
        )
        if not cursor.fetchone():
            logger.error("touchdowns table missing. Run migrations.")
            conn.close()
            stats["errors"] += 1
            return stats

        cursor.execute(
            "SELECT id FROM games WHERE season = ? AND status = 'final'",
            (season,),
        )
        final_game_ids = [row[0] for row in cursor.fetchall()]

        if not final_game_ids:
            logger.info(f"No final games for season {season}, skipping TD sync")
            conn.close()
            return stats

        df = load_data(season)
        if df.empty:
            logger.warning(f"No PBP data for season {season}")
            conn.close()
            return stats

        tds = get_touchdowns(df)
        if tds.empty or "game_id" not in tds.columns:
            logger.warning(f"No TD data for season {season}")
            conn.close()
            return stats

        team_col = "td_scorer_team" if "td_scorer_team" in tds.columns else "posteam"

        for game_id in final_game_ids:
            if not _validate_game_id(game_id):
                logger.warning(f"Invalid game_id format, skipping: {game_id}")
                stats["errors"] += 1
                continue

            game_tds = tds[tds["game_id"] == game_id]
            if game_tds.empty:
                cursor.execute("DELETE FROM touchdowns WHERE game_id = ?", (game_id,))
                conn.commit()
                continue

            cursor.execute("DELETE FROM touchdowns WHERE game_id = ?", (game_id,))
            deleted = cursor.rowcount

            first_play_id = None
            if "play_id" in game_tds.columns:
                first_row = game_tds.sort_values("play_id").iloc[0]
                first_play_id = first_row.get("play_id")

            for _, row in game_tds.iterrows():
                player_name = str(row.get("td_player_name") or "Unknown").strip()
                team = str(row.get(team_col) or "").strip()
                play_id = row.get("play_id")
                is_first = 1 if (play_id is not None and play_id == first_play_id) else 0

                cursor.execute(
                    """INSERT INTO touchdowns (game_id, player_name, team, is_first_td, play_id, season)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (game_id, player_name, team, is_first, play_id, season),
                )
                stats["inserted"] += 1

            stats["games_synced"] += 1

        conn.commit()

        try:
            cursor.execute(
                """INSERT OR REPLACE INTO sync_metadata (target, season, last_sync_at, rows_affected, status)
                   VALUES ('touchdowns', ?, ?, ?, 'success')""",
                (season, datetime.utcnow().isoformat(), stats["inserted"]),
            )
            conn.commit()
        except Exception:
            pass  # sync_metadata may not exist yet
        conn.close()

        logger.info(f"TD sync complete for {season}: {stats['games_synced']} games, {stats['inserted']} TDs")
        return stats

    except Exception as e:
        logger.exception(f"Error syncing touchdowns for {season}: {e}")
        stats["errors"] += 1
        return stats
