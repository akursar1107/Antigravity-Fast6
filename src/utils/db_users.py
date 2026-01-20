"""
User CRUD operations for the database.
Handles user management: add, retrieve, delete operations.
"""

import sqlite3
import logging
from typing import Optional, List, Dict

from .db_connection import get_db_connection, get_db_context

logger = logging.getLogger(__name__)


def add_user(name: str, email: Optional[str] = None, is_admin: bool = False) -> int:
    """Add a new user to the group."""
    try:
        with get_db_context() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (name, email, is_admin)
                VALUES (?, ?, ?)
            """, (name, email, is_admin))
            user_id = cursor.lastrowid
            logger.info(f"User added: {name} (ID: {user_id})")
            return user_id
    except sqlite3.IntegrityError as e:
        logger.error(f"User already exists: {name}")
        raise ValueError(f"User '{name}' already exists") from e


def get_user(user_id: int) -> Optional[Dict]:
    """Get user by ID."""
    with get_db_context() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_user_by_name(name: str) -> Optional[Dict]:
    """Get user by name."""
    with get_db_context() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE name = ?", (name,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_all_users() -> List[Dict]:
    """Get all users in the group."""
    with get_db_context() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users ORDER BY name")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def delete_user(user_id: int) -> bool:
    """Delete a user (cascades to picks and results). Clears leaderboard cache."""
    with get_db_context() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        success = cursor.rowcount > 0
        if success:
            logger.info(f"User deleted: ID {user_id}")
            # Clear leaderboard cache since user was deleted
            from .db_stats import clear_leaderboard_cache
            clear_leaderboard_cache()
        return success
