"""
Database connection and initialization module.
Handles SQLite connection pooling, schema setup, and migrations.
"""

import sqlite3
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Database file location
DB_PATH = Path(__file__).parent.parent.parent / "data" / "fast6.db"


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
        # Check if column exists
        cursor.execute("PRAGMA table_info(picks)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'game_id' not in columns:
            cursor.execute("ALTER TABLE picks ADD COLUMN game_id TEXT")
            conn.commit()
            logger.info("Added game_id column to picks table")
    except Exception as e:
        logger.error(f"Error ensuring game_id column: {e}")
    finally:
        conn.close()


def ensure_any_time_td_column() -> None:
    """Add any_time_td column to results table if it doesn't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if column exists
        cursor.execute("PRAGMA table_info(results)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'any_time_td' not in columns:
            cursor.execute("ALTER TABLE results ADD COLUMN any_time_td BOOLEAN DEFAULT NULL")
            conn.commit()
            logger.info("Added any_time_td column to results table")
    except Exception as e:
        logger.error(f"Error ensuring any_time_td column: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    # Initialize database for testing
    init_db()
    ensure_game_id_column()
    ensure_any_time_td_column()
    print("Database initialized successfully!")
