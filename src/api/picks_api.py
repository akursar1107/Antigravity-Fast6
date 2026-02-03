"""Picks API - bridges UI and core picks logic"""

from typing import List, Optional
import sqlite3
from src.core.picks.use_cases import (
    create_pick,
    list_user_picks,
    validate_pick,
    cancel_pick,
)
from src.core.picks.entities import Pick
from src.data.repositories.picks_repository import SQLitePickRepository
from src.lib.observability import log_event
import config


def get_connection() -> sqlite3.Connection:
    """Get database connection"""
    conn = sqlite3.connect(config.DATABASE_PATH)
    return conn


def api_create_pick(
    user_id: int,
    week_id: int,
    game_id: str,
    team: str,
    player_name: str,
    odds: float,
) -> Pick:
    """API: Create a new pick"""
    conn = get_connection()
    pick_repo = SQLitePickRepository(conn)
    
    try:
        pick = create_pick(
            user_id=user_id,
            week_id=week_id,
            game_id=game_id,
            team=team,
            player_name=player_name,
            odds=odds,
            pick_repository=pick_repo,
            game_repository=None,
        )
        return pick
    finally:
        conn.close()


def api_list_user_picks(user_id: int, week_id: int) -> List[Pick]:
    """API: List user's picks"""
    conn = get_connection()
    pick_repo = SQLitePickRepository(conn)
    
    try:
        return list_user_picks(user_id, week_id, pick_repo)
    finally:
        conn.close()


def api_validate_pick(user_id: int, game_id: str) -> dict:
    """API: Validate pick is possible"""
    conn = get_connection()
    pick_repo = SQLitePickRepository(conn)
    
    try:
        return validate_pick(user_id, game_id, None, pick_repo)
    finally:
        conn.close()


def api_cancel_pick(pick_id: int) -> bool:
    """API: Cancel a pick"""
    conn = get_connection()
    pick_repo = SQLitePickRepository(conn)
    
    try:
        return cancel_pick(pick_id, pick_repo)
    finally:
        conn.close()
