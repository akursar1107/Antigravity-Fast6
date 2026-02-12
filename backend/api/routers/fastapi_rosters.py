"""Rosters Router - Player lookup by team"""
from fastapi import APIRouter, Depends, Query
from typing import List, Dict, Any
import logging
import sqlite3

from backend.api.fastapi_dependencies import get_current_user, get_db_async

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rosters", tags=["rosters"])


@router.get("")
async def list_roster_players(
    team: str = Query(..., description="Team abbreviation (e.g. KC, BUF)"),
    season: int = Query(..., description="Season year"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db_async)
) -> List[Dict[str, Any]]:
    """Get players for a team from the rosters table."""
    cursor = conn.cursor()
    cursor.execute(
        """SELECT player_name, team, position
           FROM rosters
           WHERE team = ? AND season = ?
           ORDER BY position, player_name""",
        (team.upper(), season)
    )
    rows = cursor.fetchall()
    return [
        {"player_name": r[0], "team": r[1], "position": r[2] or "Unknown"}
        for r in rows
    ]
