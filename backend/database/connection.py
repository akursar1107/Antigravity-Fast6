"""
Database connection and initialization module.
Handles SQLite connection pooling, schema setup, and migrations.
"""

import sqlite3
import logging
from pathlib import Path
from typing import Optional, Generator
from datetime import datetime
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Database file location - can be overridden for testing
DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "data" / "fast6.db"
DB_PATH = DEFAULT_DB_PATH  # Alias for backward compatibility
_current_db_path = DEFAULT_DB_PATH

def get_db_path() -> Path:
    """Get the current database file path."""
    return _current_db_path

def set_db_path(path: Path) -> None:
    """Override the database path (primary for testing)."""
    global _current_db_path
    _current_db_path = path
    logger.info(f"Database path set to: {_current_db_path}")

def get_db_connection() -> sqlite3.Connection:
    """Get a database connection with row factory enabled."""
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_db_context() -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager for database connections.
    Automatically handles connection cleanup and commits.
    
    Usage:
        with get_db_context() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users")
            # Connection is automatically committed and closed
    """
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        conn.close()


def init_db() -> None:
    """
    Initialize database schema via migrations. Use run_migrations() directly when possible.
    Schema is defined in database/migrations.py - init_db delegates to migrations for consistency.
    """
    from .migrations import run_migrations
    run_migrations()
    logger.info("Database initialized via migrations")


def ensure_game_id_column() -> None:
    """No-op: game_id is added by migration v2. Use run_migrations() for schema setup."""
    logger.debug("ensure_game_id_column: use run_migrations() instead")


def ensure_any_time_td_column() -> None:
    """No-op: any_time_td is added by migration v3. Use run_migrations() for schema setup."""
    logger.debug("ensure_any_time_td_column: use run_migrations() instead")


if __name__ == "__main__":
    init_db()
    print("Database initialized successfully via migrations")
