"""
Results and statistics operations for the database.
Handles result management, leaderboards, and user statistics tracking.
"""

import sqlite3
import logging
import struct
from typing import Optional, List, Dict

from .db_connection import get_db_connection

logger = logging.getLogger(__name__)


def _safe_int(value) -> int:
    """Safely convert any value to int, handling bytes."""
    if value is None:
        return 0
    if isinstance(value, bytes):
        # Try to unpack as little-endian integer
        try:
            return struct.unpack('<i', value[:4])[0] if len(value) >= 4 else 0
        except (struct.error, TypeError):
            try:
                return int(value.decode('utf-8', errors='ignore'))
            except (ValueError, AttributeError):
                return 0
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0


# ============= RESULT OPERATIONS =============

def add_result(pick_id: int, actual_scorer: Optional[str] = None,
               is_correct: Optional[bool] = None, actual_return: Optional[float] = None,
               any_time_td: Optional[bool] = None) -> int:
    """Add or update result for a pick. Idempotent and quiet when already present."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # If a result already exists, update instead of raising an integrity error
        cursor.execute("SELECT id FROM results WHERE pick_id = ?", (pick_id,))
        existing = cursor.fetchone()
        if existing:
            result_id = existing[0]
            cursor.execute(
                """
                UPDATE results
                SET actual_scorer = ?, is_correct = ?, actual_return = ?, any_time_td = ?
                WHERE pick_id = ?
                """,
                (actual_scorer, is_correct, actual_return, any_time_td, pick_id)
            )
            conn.commit()
            return result_id

        cursor.execute(
            """
            INSERT INTO results (pick_id, actual_scorer, is_correct, actual_return, any_time_td)
            VALUES (?, ?, ?, ?, ?)
            """,
            (pick_id, actual_scorer, is_correct, actual_return, any_time_td)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_result(result_id: int) -> Optional[Dict]:
    """Get result by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM results WHERE id = ?", (result_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_result_for_pick(pick_id: int) -> Optional[Dict]:
    """Get result for a specific pick."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM results WHERE pick_id = ?", (pick_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def delete_season_data(season: int) -> Dict[str, int]:
    """
    Delete all picks and results for a specific season.
    Returns counts of deleted items.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Count picks to be deleted
        cursor.execute("""
            SELECT COUNT(*) FROM picks p
            JOIN weeks w ON p.week_id = w.id
            WHERE w.season = ?
        """, (season,))
        picks_count = cursor.fetchone()[0]
        
        # Count results to be deleted (cascading)
        cursor.execute("""
            SELECT COUNT(*) FROM results r
            JOIN picks p ON r.pick_id = p.id
            JOIN weeks w ON p.week_id = w.id
            WHERE w.season = ?
        """, (season,))
        results_count = cursor.fetchone()[0]
        
        # Delete picks (results cascade automatically via foreign key)
        cursor.execute("""
            DELETE FROM picks
            WHERE week_id IN (SELECT id FROM weeks WHERE season = ?)
        """, (season,))
        
        # Optionally delete weeks for this season if empty
        cursor.execute("""
            DELETE FROM weeks
            WHERE season = ? AND id NOT IN (SELECT DISTINCT week_id FROM picks)
        """, (season,))
        weeks_deleted = cursor.rowcount
        
        conn.commit()
        
        logger.info(f"Season {season} data deleted: {picks_count} picks, {results_count} results, {weeks_deleted} weeks")
        
        return {
            'picks_deleted': picks_count,
            'results_deleted': results_count,
            'weeks_deleted': weeks_deleted
        }
    except Exception as e:
        conn.rollback()
        logger.error(f"Error deleting season {season} data: {e}")
        raise
    finally:
        conn.close()


def clear_grading_results(season: int, week: Optional[int] = None) -> Dict[str, int]:
    """
    Clear all grading results for a season (optionally filtered by week).
    Deletes results but keeps picks intact - allows re-grading.
    Used sparingly for override grading when needed.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if week:
            # Clear results for specific week
            cursor.execute("""
                SELECT COUNT(*) FROM results r
                JOIN picks p ON r.pick_id = p.id
                JOIN weeks w ON p.week_id = w.id
                WHERE w.season = ? AND w.week = ?
            """, (season, week))
            results_count = cursor.fetchone()[0]
            
            cursor.execute("""
                DELETE FROM results
                WHERE pick_id IN (
                    SELECT p.id FROM picks p
                    JOIN weeks w ON p.week_id = w.id
                    WHERE w.season = ? AND w.week = ?
                )
            """, (season, week))
            
            logger.info(f"Cleared grading for Season {season} Week {week}: {results_count} results deleted")
        else:
            # Clear results for entire season
            cursor.execute("""
                SELECT COUNT(*) FROM results r
                JOIN picks p ON r.pick_id = p.id
                JOIN weeks w ON p.week_id = w.id
                WHERE w.season = ?
            """, (season,))
            results_count = cursor.fetchone()[0]
            
            cursor.execute("""
                DELETE FROM results
                WHERE pick_id IN (
                    SELECT p.id FROM picks p
                    JOIN weeks w ON p.week_id = w.id
                    WHERE w.season = ?
                )
            """, (season,))
            
            logger.info(f"Cleared grading for Season {season}: {results_count} results deleted")
        
        conn.commit()
        
        return {
            'results_cleared': results_count,
            'picks_remaining': cursor.execute(
                "SELECT COUNT(*) FROM picks p JOIN weeks w ON p.week_id = w.id WHERE w.season = ?", 
                (season,)
            ).fetchone()[0] if not week else cursor.execute(
                "SELECT COUNT(*) FROM picks p JOIN weeks w ON p.week_id = w.id WHERE w.season = ? AND w.week = ?",
                (season, week)
            ).fetchone()[0]
        }
    except Exception as e:
        conn.rollback()
        logger.error(f"Error clearing grading results: {e}")
        raise
    finally:
        conn.close()


# ============= LEADERBOARD & STATISTICS =============

def get_leaderboard(week_id: Optional[int] = None) -> List[Dict]:
    """
    Get leaderboard stats for all users.
    If week_id provided, returns stats only for that week.
    Otherwise returns cumulative stats.
    Includes both First TD wins and Any Time TD wins.
    Points: 3 for First TD, 1 for Any Time TD
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if week_id:
            # Single week leaderboard
            cursor.execute("""
                SELECT
                    u.id,
                    u.name,
                    COUNT(p.id) as total_picks,
                    SUM(CASE WHEN r.is_correct = 1 THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN r.is_correct = 0 THEN 1 ELSE 0 END) as losses,
                    SUM(CASE WHEN r.any_time_td = 1 THEN 1 ELSE 0 END) as any_time_td_wins,
                    SUM(CASE WHEN r.is_correct = 1 THEN 3 WHEN r.any_time_td = 1 THEN 1 ELSE 0 END) as points,
                    ROUND(COALESCE(SUM(r.actual_return), 0), 2) as total_return,
                    ROUND(COALESCE(AVG(r.actual_return), 0), 2) as avg_return,
                    ROUND(COALESCE(AVG(p.odds), 0), 0) as avg_odds,
                    ROUND(COALESCE(SUM(p.theoretical_return), 0), 2) as total_theoretical_return
                FROM users u
                LEFT JOIN picks p ON u.id = p.user_id AND p.week_id = ?
                LEFT JOIN results r ON p.id = r.pick_id
                GROUP BY u.id, u.name
                ORDER BY points DESC, total_return DESC
            """, (week_id,))
        else:
            # Cumulative leaderboard
            cursor.execute("""
                SELECT
                    u.id,
                    u.name,
                    COUNT(p.id) as total_picks,
                    SUM(CASE WHEN r.is_correct = 1 THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN r.is_correct = 0 THEN 1 ELSE 0 END) as losses,
                    SUM(CASE WHEN r.any_time_td = 1 THEN 1 ELSE 0 END) as any_time_td_wins,
                    SUM(CASE WHEN r.is_correct = 1 THEN 3 WHEN r.any_time_td = 1 THEN 1 ELSE 0 END) as points,
                    ROUND(COALESCE(SUM(r.actual_return), 0), 2) as total_return,
                    ROUND(COALESCE(AVG(r.actual_return), 0), 2) as avg_return,
                    ROUND(COALESCE(AVG(p.odds), 0), 0) as avg_odds,
                    ROUND(COALESCE(SUM(p.theoretical_return), 0), 2) as total_theoretical_return
                FROM users u
                LEFT JOIN picks p ON u.id = p.user_id
                LEFT JOIN results r ON p.id = r.pick_id
                GROUP BY u.id, u.name
                ORDER BY points DESC, total_return DESC
            """)
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_user_stats(user_id: int, week_id: Optional[int] = None) -> Optional[Dict]:
    """Get stats for a specific user. Includes First TD and Any Time TD stats. Points: 3 for First TD, 1 for Any Time TD."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if week_id:
            cursor.execute("""
                SELECT
                    u.id,
                    u.name,
                    COUNT(p.id) as total_picks,
                    SUM(CASE WHEN r.is_correct = 1 THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN r.is_correct = 0 THEN 1 ELSE 0 END) as losses,
                    SUM(CASE WHEN r.any_time_td = 1 THEN 1 ELSE 0 END) as any_time_td_wins,
                    SUM(CASE WHEN r.is_correct = 1 THEN 3 WHEN r.any_time_td = 1 THEN 1 ELSE 0 END) as points,
                    ROUND(COALESCE(SUM(r.actual_return), 0), 2) as total_return,
                    ROUND(COALESCE(AVG(r.actual_return), 0), 2) as avg_return,
                    ROUND(COALESCE(AVG(p.odds), 0), 0) as avg_odds,
                    ROUND(COALESCE(SUM(p.theoretical_return), 0), 2) as total_theoretical_return
                FROM users u
                LEFT JOIN picks p ON u.id = p.user_id AND p.week_id = ?
                LEFT JOIN results r ON p.id = r.pick_id
                WHERE u.id = ?
                GROUP BY u.id, u.name
            """, (week_id, user_id))
        else:
            cursor.execute("""
                SELECT
                    u.id,
                    u.name,
                    COUNT(p.id) as total_picks,
                    SUM(CASE WHEN r.is_correct = 1 THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN r.is_correct = 0 THEN 1 ELSE 0 END) as losses,
                    SUM(CASE WHEN r.any_time_td = 1 THEN 1 ELSE 0 END) as any_time_td_wins,
                    SUM(CASE WHEN r.is_correct = 1 THEN 3 WHEN r.any_time_td = 1 THEN 1 ELSE 0 END) as points,
                    ROUND(COALESCE(SUM(r.actual_return), 0), 2) as total_return,
                    ROUND(COALESCE(AVG(r.actual_return), 0), 2) as avg_return,
                    ROUND(COALESCE(AVG(p.odds), 0), 0) as avg_odds,
                    ROUND(COALESCE(SUM(p.theoretical_return), 0), 2) as total_theoretical_return
                FROM users u
                LEFT JOIN picks p ON u.id = p.user_id
                LEFT JOIN results r ON p.id = r.pick_id
                WHERE u.id = ?
                GROUP BY u.id, u.name
            """, (user_id,))
        
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_weekly_summary(week_id: int) -> Dict:
    """Get summary stats for a week."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Week info
        cursor.execute("SELECT * FROM weeks WHERE id = ?", (week_id,))
        week_row = cursor.fetchone()
        week = dict(week_row) if week_row else {}
        # Ensure integer conversion for season and week
        if 'season' in week:
            week['season'] = _safe_int(week['season'])
        if 'week' in week:
            week['week'] = _safe_int(week['week'])
        
        # Pick counts
        cursor.execute("""
            SELECT
                COUNT(*) as total_picks,
                COUNT(DISTINCT user_id) as users_with_picks
            FROM picks WHERE week_id = ?
        """, (week_id,))
        counts = dict(cursor.fetchone())
        
        # Results summary
        cursor.execute("""
            SELECT
                SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN is_correct = 0 THEN 1 ELSE 0 END) as losses,
                SUM(CASE WHEN is_correct IS NULL THEN 1 ELSE 0 END) as pending,
                ROUND(COALESCE(SUM(actual_return), 0), 2) as total_return
            FROM results r
            JOIN picks p ON r.pick_id = p.id
            WHERE p.week_id = ?
        """, (week_id,))
        results = dict(cursor.fetchone())
        
        return {**week, **counts, **results}
    finally:
        conn.close()
