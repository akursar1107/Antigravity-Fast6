"""
Database operations for kickoff decisions table.
"""

import sqlite3
from typing import Optional, List, Dict
from .db_connection import get_db_connection, get_db_context


def add_kickoff_decision(game_id: str, team: str, decision: str, result: Optional[str] = None) -> int:
    """Insert a kickoff decision record."""
    with get_db_context() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO kickoff_decisions (game_id, team, decision, result)
            VALUES (?, ?, ?, ?)
            """,
            (game_id, team, decision, result)
        )
        return cursor.lastrowid


def get_kickoff_decisions(game_id: Optional[str] = None, team: Optional[str] = None) -> List[Dict]:
    """Retrieve kickoff decisions, optionally filtered by game or team."""
    with get_db_context() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM kickoff_decisions WHERE 1=1"
        params = []
        if game_id:
            query += " AND game_id = ?"
            params.append(game_id)
        if team:
            query += " AND team = ?"
            params.append(team)
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
