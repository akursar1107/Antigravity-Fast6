"""
User CRUD operations for the database.
Handles user management: add, retrieve, delete operations.
"""

import sqlite3
import logging
from typing import Optional, List, Dict

from .db_connection import get_db_connection

logger = logging.getLogger(__name__)


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
    """Delete a user (cascades to picks and results). Clears leaderboard cache."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        success = cursor.rowcount > 0
        if success:
            logger.info(f"User deleted: ID {user_id}")
            # Clear leaderboard cache since user was deleted
            from .db_stats import clear_leaderboard_cache
            clear_leaderboard_cache()
        return success
    finally:
        conn.close()
