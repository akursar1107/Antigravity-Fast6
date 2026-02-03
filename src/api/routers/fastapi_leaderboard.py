"""Leaderboard Router - Rankings and Scoring Statistics"""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Dict, Any, Optional
import logging
import sqlite3

from src.api.fastapi_dependencies import get_current_user, get_db_async

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/leaderboard", tags=["leaderboard"])


@router.get("/week/{week_id}")
async def get_week_leaderboard(
    week_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db_async)
) -> List[Dict[str, Any]]:
    """Get leaderboard for specific week"""
    cursor = conn.cursor()
    
    # Verify week exists
    cursor.execute("SELECT id FROM weeks WHERE id = ?", (week_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Week not found")
    
    cursor.execute(
        """SELECT 
                u.id, u.name,
                COUNT(p.id) as picks_count,
                SUM(CASE WHEN r.is_correct = 1 THEN 1 ELSE 0 END) as correct_count,
                SUM(CASE WHEN r.is_correct = 1 THEN 3 ELSE 0 END) +
                SUM(CASE WHEN r.any_time_td = 1 THEN 1 ELSE 0 END) as total_points,
                SUM(CASE WHEN p.odds IS NOT NULL THEN CASE WHEN r.is_correct = 1 THEN p.odds ELSE -p.odds END ELSE 0 END) as roi_dollars
           FROM users u
           LEFT JOIN picks p ON u.id = p.user_id AND p.week_id = ?
           LEFT JOIN results r ON p.id = r.pick_id
           WHERE u.id IN (SELECT DISTINCT user_id FROM picks WHERE week_id = ?)
           GROUP BY u.id, u.name
           ORDER BY total_points DESC, correct_count DESC""",
        (week_id, week_id)
    )
    
    results = cursor.fetchall()
    return [
        {
            "rank": idx + 1,
            "user_id": r[0],
            "user_name": r[1],
            "picks_count": r[2] or 0,
            "correct_count": r[3] or 0,
            "total_points": r[4] or 0,
            "roi_dollars": round(r[5] or 0, 2)
        }
        for idx, r in enumerate(results)
    ]


@router.get("/season/{season}")
async def get_season_leaderboard(
    season: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db_async)
) -> List[Dict[str, Any]]:
    """Get overall leaderboard for entire season"""
    cursor = conn.cursor()
    
    cursor.execute(
        """SELECT 
                u.id, u.name,
                COUNT(DISTINCT p.week_id) as weeks_participated,
                COUNT(p.id) as total_picks,
                SUM(CASE WHEN r.is_correct = 1 THEN 1 ELSE 0 END) as correct_picks,
                SUM(CASE WHEN r.is_correct = 1 THEN 3 ELSE 0 END) +
                SUM(CASE WHEN r.any_time_td = 1 THEN 1 ELSE 0 END) as total_points,
                SUM(CASE WHEN p.odds IS NOT NULL THEN CASE WHEN r.is_correct = 1 THEN p.odds ELSE -p.odds END ELSE 0 END) as roi_dollars,
                ROUND(100.0 * SUM(CASE WHEN r.is_correct = 1 THEN 1 ELSE 0 END) / NULLIF(COUNT(p.id), 0), 1) as win_percentage
           FROM users u
           LEFT JOIN picks p ON u.id = p.user_id
           LEFT JOIN weeks w ON p.week_id = w.id
           LEFT JOIN results r ON p.id = r.pick_id
           WHERE w.season = ? OR (w.season IS NULL AND u.id IN (SELECT DISTINCT user_id FROM picks))
           GROUP BY u.id, u.name
           HAVING COUNT(p.id) > 0
           ORDER BY total_points DESC, correct_picks DESC""",
        (season,)
    )
    
    results = cursor.fetchall()
    return [
        {
            "rank": idx + 1,
            "user_id": r[0],
            "user_name": r[1],
            "weeks_participated": r[2] or 0,
            "total_picks": r[3] or 0,
            "correct_picks": r[4] or 0,
            "total_points": r[5] or 0,
            "roi_dollars": round(r[6] or 0, 2),
            "win_percentage": r[7] or 0
        }
        for idx, r in enumerate(results)
    ]


@router.get("/user/{user_id}/stats")
async def get_user_stats(
    user_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db_async)
) -> Dict[str, Any]:
    """Get statistics for specific user (own stats or admin)"""
    # Authorization check - users can only view own stats
    if current_user["id"] != user_id and current_user["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot view other user's stats")
    
    cursor = conn.cursor()
    
    # Verify user exists
    cursor.execute("SELECT name FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    cursor.execute(
        """SELECT 
                COUNT(DISTINCT p.week_id) as weeks_participated,
                COUNT(p.id) as total_picks,
                SUM(CASE WHEN r.is_correct = 1 THEN 1 ELSE 0 END) as correct_picks,
                SUM(CASE WHEN r.is_correct = 1 THEN 3 ELSE 0 END) +
                SUM(CASE WHEN r.any_time_td = 1 THEN 1 ELSE 0 END) as total_points,
                SUM(CASE WHEN p.odds IS NOT NULL THEN CASE WHEN r.is_correct = 1 THEN p.odds ELSE -p.odds END ELSE 0 END) as roi_dollars,
                ROUND(100.0 * SUM(CASE WHEN r.is_correct = 1 THEN 1 ELSE 0 END) / NULLIF(COUNT(p.id), 0), 1) as win_percentage,
                AVG(CASE WHEN r.is_correct = 1 THEN 3.0 ELSE 0 END) as avg_points_per_pick
           FROM picks p
           LEFT JOIN results r ON p.id = r.pick_id
           WHERE p.user_id = ?""",
        (user_id,)
    )
    
    stats = cursor.fetchone()
    
    return {
        "user_id": user_id,
        "user_name": user[0],
        "weeks_participated": stats[0] or 0,
        "total_picks": stats[1] or 0,
        "correct_picks": stats[2] or 0,
        "total_points": stats[3] or 0,
        "roi_dollars": round(stats[4] or 0, 2),
        "win_percentage": stats[5] or 0,
        "avg_points_per_pick": round(stats[6] or 0, 2)
    }


@router.get("/season/{season}/stats")
async def get_season_stats(
    season: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db_async)
) -> Dict[str, Any]:
    """Get season-wide statistics"""
    cursor = conn.cursor()
    
    cursor.execute(
        """SELECT 
                COUNT(DISTINCT u.id) as total_players,
                COUNT(DISTINCT w.id) as total_weeks,
                COUNT(p.id) as total_picks,
                SUM(CASE WHEN r.is_correct = 1 THEN 1 ELSE 0 END) as total_correct,
                ROUND(100.0 * SUM(CASE WHEN r.is_correct = 1 THEN 1 ELSE 0 END) / NULLIF(COUNT(p.id), 0), 1) as overall_accuracy
           FROM weeks w
           LEFT JOIN picks p ON w.id = p.week_id
           LEFT JOIN users u ON p.user_id = u.id
           LEFT JOIN results r ON p.id = r.pick_id
           WHERE w.season = ?""",
        (season,)
    )
    
    stats = cursor.fetchone()
    
    return {
        "season": season,
        "total_players": stats[0] or 0,
        "total_weeks": stats[1] or 0,
        "total_picks": stats[2] or 0,
        "total_correct": stats[3] or 0,
        "overall_accuracy": stats[4] or 0
    }
