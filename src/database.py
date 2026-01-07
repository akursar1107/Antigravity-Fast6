"""
Database module for Fast6 - Handles SQLite operations for users, weeks, picks, and results.
Provides CRUD operations and utility functions for leaderboard tracking.
"""

import sqlite3
import logging
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

# Database file location
DB_PATH = Path(__file__).parent.parent / "data" / "fast6.db"


def get_db_connection() -> sqlite3.Connection:
    """Get a database connection with row factory enabled."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initialize database schema. Create tables if they don't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Users table - group members
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                email TEXT UNIQUE,
                group_id INTEGER DEFAULT 1,
                is_admin BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Weeks table - seasons and weeks
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS weeks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                season INTEGER NOT NULL,
                week INTEGER NOT NULL,
                started_at TIMESTAMP,
                ended_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(season, week)
            )
        """)
        
        # Picks table - user predictions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS picks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                week_id INTEGER NOT NULL,
                team TEXT NOT NULL,
                player_name TEXT NOT NULL,
                odds REAL,
                theoretical_return REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (week_id) REFERENCES weeks(id) ON DELETE CASCADE
            )
        """)
        
        # Results table - actual outcomes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pick_id INTEGER NOT NULL UNIQUE,
                actual_scorer TEXT,
                is_correct BOOLEAN DEFAULT NULL,
                actual_return REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (pick_id) REFERENCES picks(id) ON DELETE CASCADE
            )
        """)
        
        conn.commit()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise
    finally:
        conn.close()


def ensure_game_id_column() -> None:
    """Add game_id column to picks table if it doesn't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if game_id column exists
        cursor.execute("PRAGMA table_info(picks)")
        columns = {row[1] for row in cursor.fetchall()}
        
        if 'game_id' not in columns:
            cursor.execute("ALTER TABLE picks ADD COLUMN game_id TEXT")
            conn.commit()
            logger.info("Added game_id column to picks table")
    except Exception as e:
        logger.error(f"Error adding game_id column: {e}")
    finally:
        conn.close()


def ensure_any_time_td_column() -> None:
    """Add any_time_td column to results table if it doesn't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if any_time_td column exists
        cursor.execute("PRAGMA table_info(results)")
        columns = {row[1] for row in cursor.fetchall()}
        
        if 'any_time_td' not in columns:
            cursor.execute("ALTER TABLE results ADD COLUMN any_time_td BOOLEAN DEFAULT NULL")
            conn.commit()
            logger.info("Added any_time_td column to results table")
    except Exception as e:
        logger.error(f"Error adding any_time_td column: {e}")
    finally:
        conn.close()


# ============= USER OPERATIONS =============

def add_user(name: str, email: Optional[str] = None, is_admin: bool = False) -> int:
    """Add a new user to the group."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO users (name, email, is_admin)
            VALUES (?, ?, ?)
        """, (name, email, is_admin))
        conn.commit()
        user_id = cursor.lastrowid
        logger.info(f"User added: {name} (ID: {user_id})")
        return user_id
    except sqlite3.IntegrityError as e:
        logger.error(f"User already exists: {name}")
        raise ValueError(f"User '{name}' already exists") from e
    except Exception as e:
        logger.error(f"Error adding user: {e}")
        raise
    finally:
        conn.close()


def get_user(user_id: int) -> Optional[Dict]:
    """Get user by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_user_by_name(name: str) -> Optional[Dict]:
    """Get user by name."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM users WHERE name = ?", (name,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_all_users() -> List[Dict]:
    """Get all users in the group."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM users ORDER BY name")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def delete_user(user_id: int) -> bool:
    """Delete a user (cascades to picks and results)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        success = cursor.rowcount > 0
        if success:
            logger.info(f"User deleted: ID {user_id}")
        return success
    finally:
        conn.close()


# ============= WEEK OPERATIONS =============

def add_week(season: int, week: int, started_at: Optional[datetime] = None,
             ended_at: Optional[datetime] = None) -> int:
    """Add a season/week entry."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO weeks (season, week, started_at, ended_at)
            VALUES (?, ?, ?, ?)
        """, (season, week, started_at, ended_at))
        conn.commit()
        week_id = cursor.lastrowid
        logger.info(f"Week added: Season {season}, Week {week} (ID: {week_id})")
        return week_id
    except sqlite3.IntegrityError:
        logger.warning(f"Week already exists: Season {season}, Week {week}")
        # Return existing week ID
        cursor.execute("SELECT id FROM weeks WHERE season = ? AND week = ?", (season, week))
        row = cursor.fetchone()
        return row[0] if row else -1
    finally:
        conn.close()


def get_week(week_id: int) -> Optional[Dict]:
    """Get week by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM weeks WHERE id = ?", (week_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_week_by_season_week(season: int, week: int) -> Optional[Dict]:
    """Get week by season and week number."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM weeks WHERE season = ? AND week = ?", (season, week))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_all_weeks(season: Optional[int] = None) -> List[Dict]:
    """Get all weeks, optionally filtered by season."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if season:
            cursor.execute("SELECT * FROM weeks WHERE season = ? ORDER BY week", (season,))
        else:
            cursor.execute("SELECT * FROM weeks ORDER BY season DESC, week DESC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


# ============= PICK OPERATIONS =============

def add_pick(user_id: int, week_id: int, team: str, player_name: str,
             odds: Optional[float] = None, theoretical_return: Optional[float] = None,
             game_id: Optional[str] = None) -> int:
    """Add a user's pick for a week."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO picks (user_id, week_id, team, player_name, odds, theoretical_return, game_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, week_id, team, player_name, odds, theoretical_return, game_id))
        conn.commit()
        pick_id = cursor.lastrowid
        logger.info(f"Pick added: User {user_id}, Week {week_id}, {team} {player_name}, game_id={game_id}")
        return pick_id
    except Exception as e:
        logger.error(f"Error adding pick: {e}")
        raise
    finally:
        conn.close()


def get_pick(pick_id: int) -> Optional[Dict]:
    """Get pick by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM picks WHERE id = ?", (pick_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_user_week_picks(user_id: int, week_id: int) -> List[Dict]:
    """Get all picks for a user in a specific week."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT * FROM picks
            WHERE user_id = ? AND week_id = ?
            ORDER BY created_at
        """, (user_id, week_id))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_week_all_picks(week_id: int) -> List[Dict]:
    """Get all picks for a week (all users)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT p.*, u.name as user_name
            FROM picks p
            JOIN users u ON p.user_id = u.id
            WHERE p.week_id = ?
            ORDER BY u.name, p.created_at
        """, (week_id,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_user_all_picks(user_id: int) -> List[Dict]:
    """Get all picks for a user across all weeks."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT p.*, w.season, w.week, u.name as user_name
            FROM picks p
            JOIN weeks w ON p.week_id = w.id
            JOIN users u ON p.user_id = u.id
            WHERE p.user_id = ?
            ORDER BY w.season DESC, w.week DESC
        """, (user_id,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def delete_pick(pick_id: int) -> bool:
    """Delete a pick (cascades to results)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM picks WHERE id = ?", (pick_id,))
        conn.commit()
        success = cursor.rowcount > 0
        if success:
            logger.info(f"Pick deleted: ID {pick_id}")
        return success
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


# ============= RESULT OPERATIONS =============

def add_result(pick_id: int, actual_scorer: Optional[str] = None,
               is_correct: Optional[bool] = None, actual_return: Optional[float] = None,
               any_time_td: Optional[bool] = None) -> int:
    """Add result for a pick. Includes tracking for both First TD and Any Time TD."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO results (pick_id, actual_scorer, is_correct, actual_return, any_time_td)
            VALUES (?, ?, ?, ?, ?)
        """, (pick_id, actual_scorer, is_correct, actual_return, any_time_td))
        conn.commit()
        result_id = cursor.lastrowid
        logger.info(f"Result added: Pick {pick_id}, Correct: {is_correct}, Any Time TD: {any_time_td}")
        return result_id
    except sqlite3.IntegrityError:
        logger.warning(f"Result already exists for pick {pick_id}")
        # Update existing result instead
        cursor.execute("""
            UPDATE results
            SET actual_scorer = ?, is_correct = ?, actual_return = ?, any_time_td = ?
            WHERE pick_id = ?
        """, (actual_scorer, is_correct, actual_return, any_time_td, pick_id))
        conn.commit()
        cursor.execute("SELECT id FROM results WHERE pick_id = ?", (pick_id,))
        return cursor.fetchone()[0]
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
        week = dict(cursor.fetchone())
        
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


if __name__ == "__main__":
    # Initialize database for testing
    init_db()
    print("Database initialized successfully!")


# ============= MAINTENANCE / DEDUPE =============

def dedupe_picks_for_user_week(user_id: int, week_id: int) -> Dict[str, int]:
    """
    Remove duplicate picks for a given user and week, keeping the earliest entry
    for each (team, player_name) and deleting the rest. Returns a summary dict.
    Results tied to deleted picks are removed via ON DELETE CASCADE.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
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
            conn.commit()
            deleted = len(to_delete)

        return {"duplicates_removed": deleted, "unique_kept": len(seen)}
    except Exception as e:
        logger.error(f"Error deduping picks: {e}")
        raise
    finally:
        conn.close()


def create_unique_picks_index() -> bool:
    """
    Create a UNIQUE index on picks(user_id, week_id, team, player_name) to prevent
    future duplicates. Returns True on success, False if the index could not be
    created (likely due to existing duplicates).
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS picks_unique_idx
            ON picks(user_id, week_id, team, player_name)
            """
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError as e:
        logger.warning(f"Could not create unique index: {e}")
        return False
    except Exception as e:
        logger.error(f"Error creating unique picks index: {e}")
        return False
    finally:
        conn.close()


def dedupe_all_picks() -> Dict[str, int]:
    """
    Remove duplicate picks across the entire database, keeping the earliest entry
    per (user_id, week_id, team, player_name). Returns a summary dict.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
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
            conn.commit()
            deleted = len(to_delete)

        return {"duplicates_removed": deleted, "unique_kept": len(seen)}
    except Exception as e:
        logger.error(f"Error deduping all picks: {e}")
        raise
    finally:
        conn.close()


def backfill_theoretical_return_from_odds() -> int:
    """
    Populate picks.theoretical_return based on American odds where missing.
    Returns the number of rows updated.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE picks SET theoretical_return = odds/100.0 WHERE theoretical_return IS NULL AND odds > 0")
        updated_pos = cursor.rowcount if cursor.rowcount is not None else 0
        cursor.execute("UPDATE picks SET theoretical_return = 100.0/ABS(odds) WHERE theoretical_return IS NULL AND odds < 0")
        updated_neg = cursor.rowcount if cursor.rowcount is not None else 0
        conn.commit()
        return (updated_pos or 0) + (updated_neg or 0)
    except Exception as e:
        logger.error(f"Error backfilling theoretical returns: {e}")
        raise
    finally:
        conn.close()


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
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
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
        
        # Note: game_id would require joining with schedule or storing game_id in picks
        # For now, we'll filter by team which is stored in picks
        
        query += " ORDER BY w.week, u.name"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()
