"""Weeks Router - Season and Week Management"""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Dict, Any, Optional
import logging
import sqlite3
from datetime import datetime

from src.api.fastapi_models import WeekCreate, WeekResponse
from src.api.fastapi_dependencies import get_current_user, get_current_admin_user, get_db_async

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/weeks", tags=["weeks"])


@router.get("", response_model=List[WeekResponse])
async def list_weeks(
    season: Optional[int] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db_async)
) -> List[WeekResponse]:
    """List all weeks/seasons"""
    cursor = conn.cursor()
    
    if season:
        cursor.execute(
            "SELECT id, season, week, started_at, ended_at, created_at FROM weeks "
            "WHERE season = ? ORDER BY season DESC, week ASC",
            (season,)
        )
    else:
        cursor.execute(
            "SELECT id, season, week, started_at, ended_at, created_at FROM weeks "
            "ORDER BY season DESC, week DESC"
        )
    
    weeks = cursor.fetchall()
    return [
        WeekResponse(
            id=w[0], season=w[1], week=w[2], started_at=w[3], ended_at=w[4], created_at=w[5]
        )
        for w in weeks
    ]


@router.get("/{week_id}", response_model=WeekResponse)
async def get_week(
    week_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db_async)
) -> WeekResponse:
    """Get specific week"""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, season, week, started_at, ended_at, created_at FROM weeks WHERE id = ?",
        (week_id,)
    )
    week = cursor.fetchone()
    
    if not week:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Week not found")
    
    return WeekResponse(
        id=week[0], season=week[1], week=week[2], started_at=week[3], ended_at=week[4], created_at=week[5]
    )


@router.post("", response_model=WeekResponse, status_code=status.HTTP_201_CREATED)
async def create_week(
    week: WeekCreate,
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
    conn: sqlite3.Connection = Depends(get_db_async)
) -> WeekResponse:
    """Create new week/season (admin only)"""
    cursor = conn.cursor()
    
    # Check for duplicate
    cursor.execute(
        "SELECT id FROM weeks WHERE season = ? AND week = ?",
        (week.season, week.week)
    )
    if cursor.fetchone():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Week {week.week} of season {week.season} already exists"
        )
    
    # Validate dates
    if week.started_at >= week.ended_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start time must be before end time"
        )
    
    # Insert week
    cursor.execute(
        "INSERT INTO weeks (season, week, started_at, ended_at) VALUES (?, ?, ?, ?)",
        (week.season, week.week, week.started_at, week.ended_at)
    )
    conn.commit()
    
    week_id = cursor.lastrowid
    logger.info(f"Week created: Season {week.season}, Week {week.week} (ID: {week_id})")
    
    return WeekResponse(
        id=week_id, season=week.season, week=week.week,
        started_at=week.started_at, ended_at=week.ended_at, created_at=datetime.utcnow()
    )


@router.get("/season/{season}/current")
async def get_current_week(
    season: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db_async)
) -> WeekResponse:
    """Get current active week for season"""
    cursor = conn.cursor()
    now = datetime.utcnow()
    
    cursor.execute(
        """SELECT id, season, week, started_at, ended_at, created_at
           FROM weeks 
           WHERE season = ? AND started_at <= ? AND ended_at >= ?
           LIMIT 1""",
        (season, now, now)
    )
    week = cursor.fetchone()
    
    if not week:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active week found for season {season}"
        )
    
    return WeekResponse(
        id=week[0], season=week[1], week=week[2],
        started_at=week[3], ended_at=week[4], created_at=week[5]
    )


@router.get("/season/{season}/weeks")
async def list_weeks_for_season(
    season: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db_async)
) -> List[WeekResponse]:
    """Get all weeks for specific season"""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, season, week, started_at, ended_at, created_at FROM weeks "
        "WHERE season = ? ORDER BY week ASC",
        (season,)
    )
    
    weeks = cursor.fetchall()
    if not weeks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No weeks found for season {season}"
        )
    
    return [
        WeekResponse(
            id=w[0], season=w[1], week=w[2], started_at=w[3], ended_at=w[4], created_at=w[5]
        )
        for w in weeks
    ]


@router.get("/{week_id}/stats")
async def get_week_stats(
    week_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db_async)
) -> Dict[str, Any]:
    """Get statistics for a week (picks count, graded count, etc)"""
    cursor = conn.cursor()
    
    # Verify week exists
    cursor.execute("SELECT season, week FROM weeks WHERE id = ?", (week_id,))
    week_info = cursor.fetchone()
    if not week_info:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Week not found")
    
    # Get stats
    cursor.execute(
        """SELECT COUNT(*) as total_picks, 
                  SUM(CASE WHEN results.id IS NOT NULL THEN 1 ELSE 0 END) as graded_picks,
                  SUM(CASE WHEN results.is_correct = 1 THEN 1 ELSE 0 END) as correct_picks
           FROM picks p
           LEFT JOIN results ON p.id = results.pick_id
           WHERE p.week_id = ?""",
        (week_id,)
    )
    stats = cursor.fetchone()
    
    return {
        "week_id": week_id,
        "season": week_info[0],
        "week": week_info[1],
        "total_picks": stats[0] or 0,
        "graded_picks": stats[1] or 0,
        "correct_picks": stats[2] or 0,
        "pending_picks": (stats[0] or 0) - (stats[1] or 0)
    }
