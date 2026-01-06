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
             odds: Optional[float] = None, theoretical_return: Optional[float] = None) -> int:
    """Add a user's pick for a week."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO picks (user_id, week_id, team, player_name, odds, theoretical_return)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, week_id, team, player_name, odds, theoretical_return))
        conn.commit()
        pick_id = cursor.lastrowid
        logger.info(f"Pick added: User {user_id}, Week {week_id}, {team} {player_name}")
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


# ============= RESULT OPERATIONS =============

def add_result(pick_id: int, actual_scorer: Optional[str] = None,
               is_correct: Optional[bool] = None, actual_return: Optional[float] = None) -> int:
    """Add result for a pick."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO results (pick_id, actual_scorer, is_correct, actual_return)
            VALUES (?, ?, ?, ?)
        """, (pick_id, actual_scorer, is_correct, actual_return))
        conn.commit()
        result_id = cursor.lastrowid
        logger.info(f"Result added: Pick {pick_id}, Correct: {is_correct}")
        return result_id
    except sqlite3.IntegrityError:
        logger.warning(f"Result already exists for pick {pick_id}")
        # Update existing result instead
        cursor.execute("""
            UPDATE results
            SET actual_scorer = ?, is_correct = ?, actual_return = ?
            WHERE pick_id = ?
        """, (actual_scorer, is_correct, actual_return, pick_id))
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
                    ROUND(COALESCE(SUM(r.actual_return), 0), 2) as total_return,
                    ROUND(COALESCE(AVG(r.actual_return), 0), 2) as avg_return
                FROM users u
                LEFT JOIN picks p ON u.id = p.user_id AND p.week_id = ?
                LEFT JOIN results r ON p.id = r.pick_id
                GROUP BY u.id, u.name
                ORDER BY total_return DESC
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
                    ROUND(COALESCE(SUM(r.actual_return), 0), 2) as total_return,
                    ROUND(COALESCE(AVG(r.actual_return), 0), 2) as avg_return
                FROM users u
                LEFT JOIN picks p ON u.id = p.user_id
                LEFT JOIN results r ON p.id = r.pick_id
                GROUP BY u.id, u.name
                ORDER BY total_return DESC
            """)
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_user_stats(user_id: int, week_id: Optional[int] = None) -> Optional[Dict]:
    """Get stats for a specific user."""
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
                    ROUND(COALESCE(SUM(r.actual_return), 0), 2) as total_return,
                    ROUND(COALESCE(AVG(r.actual_return), 0), 2) as avg_return
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
                    ROUND(COALESCE(SUM(r.actual_return), 0), 2) as total_return,
                    ROUND(COALESCE(AVG(r.actual_return), 0), 2) as avg_return
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
