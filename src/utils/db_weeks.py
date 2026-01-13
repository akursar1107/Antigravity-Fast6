"""
Week CRUD operations for the database.
Handles season/week management: add, retrieve operations.
"""

import sqlite3
import logging
from typing import Optional, List, Dict
from datetime import datetime

from .db_connection import get_db_connection
from .type_utils import safe_int as _safe_int

logger = logging.getLogger(__name__)


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
        if not row:
            return None
        return {
            'id': row['id'],
            'season': _safe_int(row['season']),
            'week': _safe_int(row['week']),
            'started_at': row['started_at'],
            'ended_at': row['ended_at'],
            'created_at': row['created_at']
        }
    finally:
        conn.close()


def get_week_by_season_week(season: int, week: int) -> Optional[Dict]:
    """Get week by season and week number."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM weeks WHERE season = ? AND week = ?", (season, week))
        row = cursor.fetchone()
        if not row:
            return None
        return {
            'id': row['id'],
            'season': _safe_int(row['season']),
            'week': _safe_int(row['week']),
            'started_at': row['started_at'],
            'ended_at': row['ended_at'],
            'created_at': row['created_at']
        }
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
        # Ensure integer conversion for season and week
        return [
            {
                'id': row['id'],
                'season': _safe_int(row['season']),
                'week': _safe_int(row['week']),
                'started_at': row['started_at'],
                'ended_at': row['ended_at'],
                'created_at': row['created_at']
            }
            for row in rows
        ]
    finally:
        conn.close()
