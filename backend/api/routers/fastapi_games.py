"""Games Router - NFL Schedule Management"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Dict, Any, Optional
import logging
import sqlite3
from datetime import datetime

from pydantic import BaseModel, Field
from backend.api.fastapi_dependencies import get_current_user, get_current_admin_user, get_db_async

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/games", tags=["games"])

class GameBase(BaseModel):
    season: int = Field(..., ge=1900, le=2100)
    week: int = Field(..., ge=1, le=22)  # 18 regular + playoffs (19–22)
    game_date: str = Field(..., description="ISO date string YYYY-MM-DD")
    home_team: str = Field(..., min_length=2, max_length=3)
    away_team: str = Field(..., min_length=2, max_length=3)
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    status: str = Field(default="scheduled") # scheduled, in_progress, final

class GameCreate(GameBase):
    id: str # e.g. 2025_01_KC_LV

class GameResponse(GameBase):
    id: str
    created_at: Optional[str] = None
    
    class Config:
        from_attributes = True

@router.get("/weeks")
async def list_game_weeks(
    season: int = Query(..., description="Season year"),
    conn: sqlite3.Connection = Depends(get_db_async)
) -> List[int]:
    """Get distinct week numbers that have games for a season (for schedule selector)."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT DISTINCT week FROM games WHERE season = ? AND deleted_at IS NULL ORDER BY week ASC",
        (season,)
    )
    return [row[0] for row in cursor.fetchall()]


@router.get("", response_model=List[GameResponse])
async def list_games(
    season: int = Query(..., description="Season year"),
    week: Optional[int] = Query(None, description="Week number"),
    status: Optional[str] = Query(None, description="Filter by status"),
    conn: sqlite3.Connection = Depends(get_db_async)
) -> List[GameResponse]:
    """Get games for a specific season/week"""
    cursor = conn.cursor()
    
    query = "SELECT id, season, week, game_date, home_team, away_team, home_score, away_score, status, created_at FROM games WHERE season = ? AND deleted_at IS NULL"
    params = [season]
    
    if week:
        query += " AND week = ?"
        params.append(week)
        
    if status:
        query += " AND status = ?"
        params.append(status)
        
    query += " ORDER BY game_date ASC"
    
    cursor.execute(query, params)
    games = cursor.fetchall()
    
    return [
        GameResponse(
            id=g[0], season=g[1], week=g[2], game_date=g[3],
            home_team=g[4], away_team=g[5], home_score=g[6], away_score=g[7],
            status=g[8], created_at=str(g[9])
        )
        for g in games
    ]

@router.post("", response_model=GameResponse, status_code=status.HTTP_201_CREATED)
async def create_game(
    game: GameCreate,
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
    conn: sqlite3.Connection = Depends(get_db_async)
) -> GameResponse:
    """Create a new game (Admin only)"""
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """INSERT INTO games 
               (id, season, week, game_date, home_team, away_team, home_score, away_score, status) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (game.id, game.season, game.week, game.game_date, 
             game.home_team, game.away_team, game.home_score, game.away_score, game.status)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Game with this ID or Team/Week combination already exists"
        )
        
    return GameResponse(
        id=game.id, season=game.season, week=game.week, game_date=game.game_date,
        home_team=game.home_team, away_team=game.away_team,
        home_score=game.home_score, away_score=game.away_score, status=game.status,
        created_at=str(datetime.utcnow())
    )
