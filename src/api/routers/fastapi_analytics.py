"""Analytics Router - Player and Team Analytics"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Dict, Any
import logging
import sqlite3

from src.api.fastapi_dependencies import get_current_user, get_db_async

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/player-stats")
async def get_player_stats(
    season: int = Query(..., description="NFL season"),
    limit: int = Query(50, ge=1, le=500),
    current_user: Dict[str, Any] = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db_async)
) -> List[Dict[str, Any]]:
    """Get top performing players for the season"""
    cursor = conn.cursor()
    
    cursor.execute(
        """SELECT 
                p.player_name,
                p.team,
                COUNT(DISTINCT ps.player_name) as first_td_count,
                ROUND(SUM(CASE WHEN r.any_time_td = 1 THEN 1 ELSE 0 END) / NULLIF(COUNT(DISTINCT p.id), 0) * 100, 1) as any_time_td_rate,
                ROUND(100.0 * COUNT(CASE WHEN r.is_correct = 1 THEN 1 END) / NULLIF(COUNT(DISTINCT p.id), 0), 1) as accuracy
           FROM picks p
           LEFT JOIN weeks w ON p.week_id = w.id
           LEFT JOIN results r ON p.id = r.pick_id
           LEFT JOIN player_stats ps ON p.player_name = ps.player_name AND ps.season = w.season
           WHERE w.season = ?
           GROUP BY p.player_name, p.team
           ORDER BY first_td_count DESC, accuracy DESC
           LIMIT ?""",
        (season, limit)
    )
    
    results = cursor.fetchall()
    return [
        {
            "player_name": r[0],
            "team": r[1],
            "first_td_count": r[2] or 0,
            "any_time_td_rate": r[3] or 0,
            "accuracy": r[4] or 0
        }
        for r in results
    ]


@router.get("/team-defense")
async def get_team_defense_stats(
    season: int = Query(..., description="NFL season"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db_async)
) -> List[Dict[str, Any]]:
    """Get defensive matchup statistics - which teams allow most TDs"""
    cursor = conn.cursor()
    
    cursor.execute(
        """SELECT 
                p.team as team_picked,
                COUNT(p.id) as total_picks,
                SUM(CASE WHEN r.is_correct = 1 THEN 1 ELSE 0 END) as correct_picks,
                ROUND(100.0 * SUM(CASE WHEN r.is_correct = 1 THEN 1 ELSE 0 END) / NULLIF(COUNT(p.id), 0), 1) as accuracy
           FROM picks p
           LEFT JOIN weeks w ON p.week_id = w.id
           LEFT JOIN results r ON p.id = r.pick_id
           WHERE w.season = ?
           GROUP BY p.team
           ORDER BY accuracy DESC""",
        (season,)
    )
    
    results = cursor.fetchall()
    return [
        {
            "team": r[0],
            "total_picks": r[1] or 0,
            "correct_picks": r[2] or 0,
            "accuracy": r[3] or 0
        }
        for r in results
    ]


@router.get("/roi-trends")
async def get_roi_trends(
    season: int = Query(..., description="NFL season"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db_async)
) -> List[Dict[str, Any]]:
    """Get ROI trends by week"""
    cursor = conn.cursor()
    
    cursor.execute(
        """SELECT 
                w.week,
                COUNT(p.id) as picks_count,
                SUM(CASE WHEN r.is_correct = 1 THEN 1 ELSE 0 END) as correct_count,
                ROUND(100.0 * SUM(CASE WHEN r.is_correct = 1 THEN 1 ELSE 0 END) / NULLIF(COUNT(p.id), 0), 1) as accuracy,
                SUM(CASE WHEN p.odds IS NOT NULL THEN CASE WHEN r.is_correct = 1 THEN p.odds ELSE -p.odds END ELSE 0 END) as roi_dollars
           FROM weeks w
           LEFT JOIN picks p ON w.id = p.week_id
           LEFT JOIN results r ON p.id = r.pick_id
           WHERE w.season = ?
           GROUP BY w.week
           ORDER BY w.week""",
        (season,)
    )
    
    results = cursor.fetchall()
    return [
        {
            "week": r[0],
            "picks_count": r[1] or 0,
            "correct_count": r[2] or 0,
            "accuracy": r[3] or 0,
            "roi_dollars": round(r[4] or 0, 2)
        }
        for r in results
    ]


@router.get("/odds-accuracy")
async def get_odds_accuracy(
    season: int = Query(..., description="NFL season"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db_async)
) -> List[Dict[str, Any]]:
    """Get accuracy grouped by odds ranges"""
    cursor = conn.cursor()
    
    cursor.execute(
        """SELECT 
                CASE
                    WHEN p.odds < 100 THEN '<100'
                    WHEN p.odds < 200 THEN '100-200'
                    WHEN p.odds < 500 THEN '200-500'
                    WHEN p.odds < 1000 THEN '500-1000'
                    ELSE '1000+'
                END as odds_range,
                COUNT(p.id) as picks_count,
                SUM(CASE WHEN r.is_correct = 1 THEN 1 ELSE 0 END) as correct_count,
                ROUND(100.0 * SUM(CASE WHEN r.is_correct = 1 THEN 1 ELSE 0 END) / NULLIF(COUNT(p.id), 0), 1) as accuracy,
                ROUND(AVG(p.odds), 0) as avg_odds
           FROM picks p
           LEFT JOIN weeks w ON p.week_id = w.id
           LEFT JOIN results r ON p.id = r.pick_id
           WHERE w.season = ? AND p.odds IS NOT NULL
           GROUP BY odds_range
           ORDER BY avg_odds""",
        (season,)
    )
    
    results = cursor.fetchall()
    return [
        {
            "odds_range": r[0],
            "picks_count": r[1] or 0,
            "correct_count": r[2] or 0,
            "accuracy": r[3] or 0,
            "avg_odds": int(r[4] or 0)
        }
        for r in results
    ]


@router.get("/grading-status")
async def get_grading_status(
    season: int = Query(..., description="NFL season"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db_async)
) -> Dict[str, Any]:
    """Get grading progress for season"""
    cursor = conn.cursor()
    
    cursor.execute(
        """SELECT 
                COUNT(DISTINCT p.id) as total_picks,
                SUM(CASE WHEN r.id IS NOT NULL THEN 1 ELSE 0 END) as graded_picks,
                SUM(CASE WHEN r.id IS NULL THEN 1 ELSE 0 END) as ungraded_picks
           FROM picks p
           LEFT JOIN weeks w ON p.week_id = w.id
           LEFT JOIN results r ON p.id = r.pick_id
           WHERE w.season = ?""",
        (season,)
    )
    
    stats = cursor.fetchone()
    total = stats[0] or 0
    graded = stats[1] or 0
    ungraded = stats[2] or 0
    
    return {
        "season": season,
        "total_picks": total,
        "graded_picks": graded,
        "ungraded_picks": ungraded,
        "grading_progress": round(100.0 * graded / max(total, 1), 1)
    }


@router.get("/matchup/{game_id}")
async def get_game_matchup_data(
    game_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db_async)
) -> Dict[str, Any]:
    """Get analytics for specific game matchup"""
    cursor = conn.cursor()
    
    cursor.execute(
        """SELECT 
                p.team,
                COUNT(p.id) as picks_count,
                SUM(CASE WHEN r.is_correct = 1 THEN 1 ELSE 0 END) as correct_count,
                ROUND(100.0 * SUM(CASE WHEN r.is_correct = 1 THEN 1 ELSE 0 END) / NULLIF(COUNT(p.id), 0), 1) as accuracy
           FROM picks p
           LEFT JOIN results r ON p.id = r.pick_id
           WHERE p.game_id = ?
           GROUP BY p.team
           ORDER BY picks_count DESC""",
        (game_id,)
    )
    
    results = cursor.fetchall()
    if not results:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No picks found for this game")
    
    return {
        "game_id": game_id,
        "teams": [
            {
                "team": r[0],
                "picks_count": r[1] or 0,
                "correct_count": r[2] or 0,
                "accuracy": r[3] or 0
            }
            for r in results
        ]
    }
