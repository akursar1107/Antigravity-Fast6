"""
Results and statistics operations for the database.
Handles result management, leaderboards, and user statistics tracking.
"""

import sqlite3
import logging
from typing import Optional, List, Dict
from src import config

from .connection import get_db_connection, get_db_context
from src.utils.type_utils import safe_int as _safe_int
from src.utils.caching import cached, CacheTTL, invalidate_on_result_change
from src.utils.types import Result, LeaderboardEntry, WeekSummary, PickWithResult, BatchOperationResult

logger = logging.getLogger(__name__)


# Remove old caching decorator - now using unified caching module


def clear_leaderboard_cache() -> None:
    """
    Clear only the leaderboard-related caches when results are updated.
    Now uses the unified caching layer invalidation.
    """
    invalidate_on_result_change()


# ============= RESULT OPERATIONS =============

def add_result(pick_id: int, actual_scorer: Optional[str] = None,
               is_correct: Optional[bool] = None, actual_return: Optional[float] = None,
               any_time_td: Optional[bool] = None) -> int:
    """Add or update result for a pick. Idempotent and quiet when already present."""
    # Clear leaderboard cache when a result is added/updated
    clear_leaderboard_cache()
    with get_db_context() as conn:
        cursor = conn.cursor()
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
            return result_id

        cursor.execute(
            """
            INSERT INTO results (pick_id, actual_scorer, is_correct, actual_return, any_time_td)
            VALUES (?, ?, ?, ?, ?)
            """,
            (pick_id, actual_scorer, is_correct, actual_return, any_time_td)
        )
        return cursor.lastrowid


def add_results_batch(results: List[Dict]) -> BatchOperationResult:
    """
    Add or update multiple results in a single transaction.
    Much more efficient than calling add_result() in a loop.
    
    Args:
        results: List of dicts with keys: pick_id, actual_scorer, is_correct, actual_return, any_time_td
        
    Returns:
        Dict with counts: {'inserted': n, 'updated': m}
    """
    if not results:
        return {'inserted': 0, 'updated': 0}
    
    inserted = 0
    updated = 0
    
    with get_db_context() as conn:
        cursor = conn.cursor()
        
        # Get all existing result pick_ids in one query
        pick_ids = [r['pick_id'] for r in results]
        placeholders = ','.join('?' * len(pick_ids))
        cursor.execute(f"SELECT pick_id FROM results WHERE pick_id IN ({placeholders})", pick_ids)
        existing_pick_ids = {row[0] for row in cursor.fetchall()}
        
        # Separate into inserts and updates
        to_insert = []
        to_update = []
        
        for r in results:
            row = (
                r['pick_id'],
                r.get('actual_scorer'),
                r.get('is_correct'),
                r.get('actual_return'),
                r.get('any_time_td')
            )
            if r['pick_id'] in existing_pick_ids:
                # Reorder for UPDATE: values first, then pick_id for WHERE
                to_update.append((row[1], row[2], row[3], row[4], row[0]))
            else:
                to_insert.append(row)
        
        # Batch insert
        if to_insert:
            cursor.executemany(
                """
                INSERT INTO results (pick_id, actual_scorer, is_correct, actual_return, any_time_td)
                VALUES (?, ?, ?, ?, ?)
                """,
                to_insert
            )
            inserted = len(to_insert)
        
        # Batch update
        if to_update:
            cursor.executemany(
                """
                UPDATE results
                SET actual_scorer = ?, is_correct = ?, actual_return = ?, any_time_td = ?
                WHERE pick_id = ?
                """,
                to_update
            )
            updated = len(to_update)
    
    # Clear cache once after all operations
    if inserted > 0 or updated > 0:
        clear_leaderboard_cache()
    
    logger.info(f"Batch add_results: {inserted} inserted, {updated} updated")
    return {'inserted': inserted, 'updated': updated}


def get_result(result_id: int) -> Optional[Dict]:
    """Get result by ID."""
    with get_db_context() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM results WHERE id = ?", (result_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_result_for_pick(pick_id: int) -> Optional[Dict]:
    """Get result for a specific pick."""
    with get_db_context() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM results WHERE pick_id = ?", (pick_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def delete_season_data(season: int) -> Dict[str, int]:
    """
    Delete all picks and results for a specific season.
    Returns counts of deleted items.
    """
    try:
        with get_db_context() as conn:
            cursor = conn.cursor()
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
            
            logger.info(f"Season {season} data deleted: {picks_count} picks, {results_count} results, {weeks_deleted} weeks")
            
            return {
                'picks_deleted': picks_count,
                'results_deleted': results_count,
                'weeks_deleted': weeks_deleted
            }
    except Exception as e:
        logger.error(f"Error deleting season {season} data: {e}")
        raise


def clear_grading_results(season: int, week: Optional[int] = None) -> Dict[str, int]:
    """
    Clear all grading results for a season (optionally filtered by week).
    Deletes results but keeps picks intact - allows re-grading.
    Used sparingly for override grading when needed.
    """
    # Clear leaderboard cache when clearing grading results
    clear_leaderboard_cache()
    try:
        with get_db_context() as conn:
            cursor = conn.cursor()
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
        logger.error(f"Error clearing grading results: {e}")
        raise


# ============= LEADERBOARD & STATISTICS =============

def _build_stats_select_clause() -> str:
    """
    Build the common SELECT clause for leaderboard/user stats queries.
    
    This is extracted to avoid duplicating the complex scoring/aggregation logic
    across get_leaderboard() and get_user_stats().
    
    Returns:
        SQL SELECT clause string with config-based scoring values
    """
    return f"""
        SELECT
            u.id,
            u.name,
            COUNT(p.id) as total_picks,
            SUM(CASE WHEN r.is_correct = 1 THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN COALESCE(r.is_correct, 0) = 0 AND p.id IS NOT NULL THEN 1 ELSE 0 END) as losses,
            SUM(CASE WHEN COALESCE(r.any_time_td, 0) = 1 THEN 1 ELSE 0 END) as any_time_td_wins,
            SUM(CASE WHEN r.is_correct = 1 THEN {config.SCORING_FIRST_TD} ELSE 0 END + CASE WHEN COALESCE(r.any_time_td, 0) = 1 THEN {config.SCORING_ANY_TIME} ELSE 0 END) as points,
            ROUND(COALESCE(SUM(r.actual_return), 0), 2) as total_return,
            ROUND(COALESCE(AVG(r.actual_return), 0), 2) as avg_return,
            ROUND(COALESCE(AVG(p.odds), 0), 0) as avg_odds,
            ROUND(COALESCE(SUM(p.theoretical_return), 0), 2) as total_theoretical_return
        FROM users u
    """


@cached(ttl=CacheTTL.LEADERBOARD, cache_name="leaderboard")
def get_leaderboard(week_id: Optional[int] = None) -> List[LeaderboardEntry]:
    """
    Get leaderboard stats for all users.
    If week_id provided, returns stats only for that week.
    Otherwise returns cumulative stats.
    Includes both First TD wins and Any Time TD wins.
    Points: 3 for First TD, 1 for Any Time TD
    """
    select_clause = _build_stats_select_clause()
    
    with get_db_context() as conn:
        cursor = conn.cursor()
        if week_id:
            # Single week leaderboard
            query = select_clause + """
                LEFT JOIN picks p ON u.id = p.user_id AND p.week_id = ?
                LEFT JOIN results r ON p.id = r.pick_id
                GROUP BY u.id, u.name
                ORDER BY points DESC, total_return DESC
            """
            cursor.execute(query, (week_id,))
        else:
            # Cumulative leaderboard
            query = select_clause + """
                LEFT JOIN picks p ON u.id = p.user_id
                LEFT JOIN results r ON p.id = r.pick_id
                GROUP BY u.id, u.name
                ORDER BY points DESC, total_return DESC
            """
            cursor.execute(query)
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


@cached(ttl=CacheTTL.USER_STATS, cache_name="user_stats")
def get_user_stats(user_id: int, week_id: Optional[int] = None) -> Optional[LeaderboardEntry]:
    """Get stats for a specific user. Includes First TD and Any Time TD stats. Points: 3 for First TD, 1 for Any Time TD."""
    select_clause = _build_stats_select_clause()
    
    with get_db_context() as conn:
        cursor = conn.cursor()
        if week_id:
            query = select_clause + """
                LEFT JOIN picks p ON u.id = p.user_id AND p.week_id = ?
                LEFT JOIN results r ON p.id = r.pick_id
                WHERE u.id = ?
                GROUP BY u.id, u.name
            """
            cursor.execute(query, (week_id, user_id))
        else:
            query = select_clause + """
                LEFT JOIN picks p ON u.id = p.user_id
                LEFT JOIN results r ON p.id = r.pick_id
                WHERE u.id = ?
                GROUP BY u.id, u.name
            """
            cursor.execute(query, (user_id,))
        
        row = cursor.fetchone()
        return dict(row) if row else None


@cached(ttl=CacheTTL.WEEKLY_SUMMARY, cache_name="weekly_summary")
def get_weekly_summary(week_id: int) -> Dict:
    """Get summary stats for a week."""
    with get_db_context() as conn:
        cursor = conn.cursor()
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


def get_user_picks_with_results(user_id: int, season: int) -> List[Dict]:
    """
    Get all picks for a user in a season with result data joined.
    
    Args:
        user_id: User ID
        season: NFL season
        
    Returns:
        List of pick dictionaries with joined result fields (odds, is_correct, actual_return, etc.)
    """
    with get_db_context() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                p.*,
                w.season,
                w.week,
                r.id as result_id,
                r.actual_scorer,
                r.is_correct,
                r.actual_return,
                r.any_time_td
            FROM picks p
            JOIN weeks w ON p.week_id = w.id
            LEFT JOIN results r ON p.id = r.pick_id
            WHERE p.user_id = ? AND w.season = ?
            ORDER BY w.season DESC, w.week DESC
        """, (user_id, season))
        
        rows = cursor.fetchall()
        result = []
        for row in rows:
            row_dict = dict(row)
            # Ensure integer conversion
            if 'season' in row_dict:
                row_dict['season'] = _safe_int(row_dict['season'])
            if 'week' in row_dict:
                row_dict['week'] = _safe_int(row_dict['week'])
            result.append(row_dict)
        
        return result
