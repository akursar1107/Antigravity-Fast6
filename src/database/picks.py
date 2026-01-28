"""
Pick CRUD operations and management for the database.
Handles user predictions, picks retrieval, deletion, and deduplication.
"""

import sqlite3
import logging
from typing import Optional, List, Dict, Tuple

from .connection import get_db_connection, get_db_context
from utils.type_utils import safe_int as _safe_int

logger = logging.getLogger(__name__)


def add_pick(user_id: int, week_id: int, team: str, player_name: str,
             odds: Optional[float] = None, theoretical_return: Optional[float] = None,
             game_id: Optional[str] = None) -> int:
    """Add a user's pick for a week."""
    with get_db_context() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO picks (user_id, week_id, team, player_name, odds, theoretical_return, game_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, week_id, team, player_name, odds, theoretical_return, game_id))
        pick_id = cursor.lastrowid
        logger.info(f"Pick added: User {user_id}, Week {week_id}, {team} {player_name}, game_id={game_id}")
        return pick_id


def add_picks_batch(picks: List[Dict]) -> int:
    """
    Add multiple picks in a single transaction.
    Much more efficient than calling add_pick() in a loop.
    
    Args:
        picks: List of dicts with keys: user_id, week_id, team, player_name, 
               and optionally: odds, theoretical_return, game_id
               
    Returns:
        Number of picks inserted
    """
    if not picks:
        return 0
    
    with get_db_context() as conn:
        cursor = conn.cursor()
        
        # Prepare data for batch insert
        insert_data = [
            (
                p['user_id'],
                p['week_id'],
                p['team'],
                p['player_name'],
                p.get('odds'),
                p.get('theoretical_return'),
                p.get('game_id')
            )
            for p in picks
        ]
        
        cursor.executemany("""
            INSERT INTO picks (user_id, week_id, team, player_name, odds, theoretical_return, game_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, insert_data)
        
        inserted = len(insert_data)
        logger.info(f"Batch inserted {inserted} picks")
        return inserted


def get_pick(pick_id: int) -> Optional[Dict]:
    """Get pick by ID."""
    with get_db_context() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM picks WHERE id = ?", (pick_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_user_week_picks(user_id: int, week_id: int) -> List[Dict]:
    """Get all picks for a user in a specific week."""
    with get_db_context() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM picks
            WHERE user_id = ? AND week_id = ?
            ORDER BY created_at
        """, (user_id, week_id))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_week_all_picks(week_id: int) -> List[Dict]:
    """Get all picks for a week (all users)."""
    with get_db_context() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.*, u.name as user_name
            FROM picks p
            JOIN users u ON p.user_id = u.id
            WHERE p.week_id = ?
            ORDER BY u.name, p.created_at
        """, (week_id,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_user_all_picks(user_id: int) -> List[Dict]:
    """Get all picks for a user across all weeks."""
    with get_db_context() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.*, w.season, w.week, u.name as user_name
            FROM picks p
            JOIN weeks w ON p.week_id = w.id
            JOIN users u ON p.user_id = u.id
            WHERE p.user_id = ?
            ORDER BY w.season DESC, w.week DESC
        """, (user_id,))
        rows = cursor.fetchall()
        result = []
        for row in rows:
            row_dict = dict(row)
            # Ensure integer conversion for season and week
            if 'season' in row_dict:
                row_dict['season'] = _safe_int(row_dict['season'])
            if 'week' in row_dict:
                row_dict['week'] = _safe_int(row_dict['week'])
            result.append(row_dict)
        return result


def delete_pick(pick_id: int) -> bool:
    """Delete a pick (cascades to results). Clears leaderboard cache."""
    with get_db_context() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM picks WHERE id = ?", (pick_id,))
        success = cursor.rowcount > 0
        if success:
            logger.info(f"Pick deleted: ID {pick_id}")
            # Clear leaderboard cache when a pick is deleted
            from .db_stats import clear_leaderboard_cache
            clear_leaderboard_cache()
        return success


def get_ungraded_picks(season: int, week: Optional[int] = None, game_id: Optional[str] = None) -> List[Dict]:
    """
    Fetch picks that haven't been graded yet (no result or result is NULL).
    Filters by season and optionally by week and/or game_id.
    
    Args:
        season: Season year
        week: Optional week number
        game_id: Optional game_id to filter specific game
        
    Returns:
        List of pick dictionaries with user and week info
    """
    with get_db_context() as conn:
        cursor = conn.cursor()
        query = """
            SELECT p.*, u.name as user_name, w.season, w.week
            FROM picks p
            JOIN users u ON p.user_id = u.id
            JOIN weeks w ON p.week_id = w.id
            LEFT JOIN results r ON p.id = r.pick_id
            WHERE w.season = ?
            AND (r.id IS NULL OR r.is_correct IS NULL)
        """
        params = [season]
        
        if week is not None:
            query += " AND w.week = ?"
            params.append(week)
        
        query += " ORDER BY w.week, u.name"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        result = []
        for row in rows:
            row_dict = dict(row)
            # Ensure integer conversion for season and week
            if 'season' in row_dict:
                row_dict['season'] = _safe_int(row_dict['season'])
            if 'week' in row_dict:
                row_dict['week'] = _safe_int(row_dict['week'])
            result.append(row_dict)
        return result


# ============= MAINTENANCE / DEDUPE =============

def dedupe_picks_for_user_week(user_id: int, week_id: int) -> Dict[str, int]:
    """
    Remove duplicate picks for a given user and week, keeping the earliest entry
    for each (team, player_name) and deleting the rest. Returns a summary dict.
    Results tied to deleted picks are removed via ON DELETE CASCADE.
    """
    with get_db_context() as conn:
        cursor = conn.cursor()
        # Fetch picks ordered by canonical fields
        cursor.execute(
            """
            SELECT id, team, player_name, created_at
            FROM picks
            WHERE user_id = ? AND week_id = ?
            ORDER BY team, player_name, created_at, id
            """,
            (user_id, week_id)
        )
        rows = cursor.fetchall()
        to_delete: List[int] = []
        seen: Dict[Tuple[str, str], int] = {}

        for row in rows:
            rid = row[0]
            team = row[1]
            player = row[2]
            key = (team, player)
            if key in seen:
                # Already have a canonical pick; mark this one for deletion
                to_delete.append(rid)
            else:
                seen[key] = rid

        deleted = 0
        if to_delete:
            # Delete duplicates; results will cascade
            cursor.executemany("DELETE FROM picks WHERE id = ?", [(pid,) for pid in to_delete])
            deleted = len(to_delete)

        return {"duplicates_removed": deleted, "unique_kept": len(seen)}


def create_unique_picks_index() -> bool:
    """
    Create a UNIQUE index on picks(user_id, week_id, team, player_name) to prevent
    future duplicates. Returns True on success, False if the index could not be
    created (likely due to existing duplicates).
    """
    try:
        with get_db_context() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS picks_unique_idx
                ON picks(user_id, week_id, team, player_name)
                """
            )
            return True
    except sqlite3.IntegrityError as e:
        logger.warning(f"Could not create unique index: {e}")
        return False


def dedupe_all_picks() -> Dict[str, int]:
    """
    Remove duplicate picks across the entire database, keeping the earliest entry
    per (user_id, week_id, team, player_name). Returns a summary dict.
    """
    with get_db_context() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, user_id, week_id, team, player_name, created_at
            FROM picks
            ORDER BY user_id, week_id, team, player_name, created_at, id
            """
        )
        rows = cursor.fetchall()
        to_delete: List[int] = []
        seen: Dict[Tuple[int, int, str, str], int] = {}

        for row in rows:
            rid = row[0]
            user_id = row[1]
            week_id = row[2]
            team = row[3]
            player = row[4]
            key = (user_id, week_id, team, player)
            if key in seen:
                to_delete.append(rid)
            else:
                seen[key] = rid

        deleted = 0
        if to_delete:
            cursor.executemany("DELETE FROM picks WHERE id = ?", [(pid,) for pid in to_delete])
            deleted = len(to_delete)
            # Clear leaderboard cache since picks were modified
            from .db_stats import clear_leaderboard_cache
            clear_leaderboard_cache()

        return {"duplicates_removed": deleted, "unique_kept": len(seen)}


def backfill_theoretical_return_from_odds() -> int:
    """
    Populate picks.theoretical_return based on American odds where missing.
    Returns the number of rows updated.
    """
    with get_db_context() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE picks SET theoretical_return = odds/100.0 WHERE theoretical_return IS NULL AND odds > 0")
        updated_pos = cursor.rowcount if cursor.rowcount is not None else 0
        cursor.execute("UPDATE picks SET theoretical_return = 100.0/ABS(odds) WHERE theoretical_return IS NULL AND odds < 0")
        updated_neg = cursor.rowcount if cursor.rowcount is not None else 0
        return (updated_pos or 0) + (updated_neg or 0)


def update_pick_player_name(pick_id: int, player_name: str) -> bool:
    """
    Update the player name for a specific pick.
    
    Args:
        pick_id: ID of the pick to update
        player_name: New player name
        
    Returns:
        True if update was successful, False otherwise
    """
    with get_db_context() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE picks SET player_name = ? WHERE id = ?",
            (player_name, pick_id)
        )
        success = cursor.rowcount > 0
        if success:
            logger.info(f"Updated pick {pick_id} player_name to '{player_name}'")
        return success


def get_graded_picks(season: int, week: Optional[int] = None) -> List[Dict]:
    """
    Get all graded picks (with results) for a season, optionally filtered by week.
    Used for verification/display in admin UI.
    
    Args:
        season: Season year
        week: Optional week number to filter
        
    Returns:
        List of dicts with pick info, user name, and result data
    """
    with get_db_context() as conn:
        cursor = conn.cursor()
        
        if week:
            cursor.execute("""
                SELECT 
                    p.id, p.player_name, p.team, u.name as user_name,
                    r.is_correct, r.any_time_td, r.actual_scorer,
                    w.week, w.season
                FROM picks p
                JOIN users u ON p.user_id = u.id
                JOIN weeks w ON p.week_id = w.id
                LEFT JOIN results r ON p.id = r.pick_id
                WHERE w.season = ? AND w.week = ? AND r.id IS NOT NULL
                ORDER BY w.week, u.name
            """, (season, week))
        else:
            cursor.execute("""
                SELECT 
                    p.id, p.player_name, p.team, u.name as user_name,
                    r.is_correct, r.any_time_td, r.actual_scorer,
                    w.week, w.season
                FROM picks p
                JOIN users u ON p.user_id = u.id
                JOIN weeks w ON p.week_id = w.id
                LEFT JOIN results r ON p.id = r.pick_id
                WHERE w.season = ? AND r.id IS NOT NULL
                ORDER BY w.week, u.name
            """, (season,))
        
        rows = cursor.fetchall()
        result = []
        for row in rows:
            result.append({
                'pick_id': row[0],
                'player_name': row[1],
                'team': row[2],
                'user_name': row[3],
                'is_correct': bool(row[4]) if row[4] is not None else None,
                'any_time_td': bool(row[5]) if row[5] is not None else None,
                'actual_scorer': row[6],
                'week': _safe_int(row[7]),
                'season': _safe_int(row[8])
            })
        return result
