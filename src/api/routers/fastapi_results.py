"""Results Router - Pick Grading and Results"""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Dict, Any, Optional
import logging
import sqlite3
from datetime import datetime

from src.api.fastapi_models import ResultCreate, ResultResponse
from src.api.fastapi_dependencies import get_current_user, get_current_admin_user, get_db_async

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/results", tags=["grading"])


@router.get("", response_model=List[ResultResponse])
async def list_results(
    pick_id: Optional[int] = None,
    week_id: Optional[int] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db_async)
) -> List[ResultResponse]:
    """
    List results/graded picks.
    
    Query Parameters:
        pick_id: Filter by specific pick
        week_id: Filter by week
    """
    cursor = conn.cursor()
    
    if pick_id:
        cursor.execute(
            """SELECT r.id, r.pick_id, r.actual_scorer, r.is_correct, r.any_time_td, 
                      r.payout, r.created_at
               FROM results r
               JOIN picks p ON r.pick_id = p.id
               WHERE r.pick_id = ?""",
            (pick_id,)
        )
    elif week_id:
        # Filter by week - admin sees all, users see own only
        if current_user["role"] == "admin":
            cursor.execute(
                """SELECT r.id, r.pick_id, r.actual_scorer, r.is_correct, r.any_time_td, 
                          r.payout, r.created_at
                   FROM results r
                   JOIN picks p ON r.pick_id = p.id
                   WHERE p.week_id = ?
                   ORDER BY r.created_at DESC""",
                (week_id,)
            )
        else:
            cursor.execute(
                """SELECT r.id, r.pick_id, r.actual_scorer, r.is_correct, r.any_time_td, 
                          r.payout, r.created_at
                   FROM results r
                   JOIN picks p ON r.pick_id = p.id
                   WHERE p.week_id = ? AND p.user_id = ?
                   ORDER BY r.created_at DESC""",
                (week_id, current_user["id"])
            )
    else:
        # Default: show user's own results
        cursor.execute(
            """SELECT r.id, r.pick_id, r.actual_scorer, r.is_correct, r.any_time_td, 
                      r.payout, r.created_at
               FROM results r
               JOIN picks p ON r.pick_id = p.id
               WHERE p.user_id = ?
               ORDER BY r.created_at DESC""",
            (current_user["id"],)
        )
    
    results = cursor.fetchall()
    return [
        ResultResponse(
            id=r[0], pick_id=r[1], actual_scorer=r[2], is_correct=r[3],
            any_time_td=r[4], payout=r[5], graded_at=r[6]
        )
        for r in results
    ]


@router.get("/ungraded/list")
async def list_ungraded_picks(
    week_id: Optional[int] = None,
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
    conn: sqlite3.Connection = Depends(get_db_async)
) -> List[Dict[str, Any]]:
    """Get list of ungraded picks (admin only)"""
    cursor = conn.cursor()
    
    if week_id:
        cursor.execute(
            """SELECT p.id, p.user_id, u.name, p.week_id, p.team, p.player_name, p.odds
               FROM picks p
               JOIN users u ON p.user_id = u.id
               WHERE p.week_id = ? AND p.id NOT IN (SELECT pick_id FROM results)
               ORDER BY p.created_at""",
            (week_id,)
        )
    else:
        cursor.execute(
            """SELECT p.id, p.user_id, u.name, p.week_id, p.team, p.player_name, p.odds
               FROM picks p
               JOIN users u ON p.user_id = u.id
               WHERE p.id NOT IN (SELECT pick_id FROM results)
               ORDER BY p.created_at DESC"""
        )
    
    picks = cursor.fetchall()
    return [
        {
            "pick_id": p[0],
            "user_id": p[1],
            "user_name": p[2],
            "week_id": p[3],
            "team": p[4],
            "player_name": p[5],
            "odds": p[6]
        }
        for p in picks
    ]


@router.get("/{result_id}", response_model=ResultResponse)
async def get_result(
    result_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db_async)
) -> ResultResponse:
    """Get specific result"""
    cursor = conn.cursor()
    cursor.execute(
        """SELECT r.id, r.pick_id, r.actual_scorer, r.is_correct, r.any_time_td, 
                  r.payout, r.created_at
           FROM results r
           JOIN picks p ON r.pick_id = p.id
           WHERE r.id = ?""",
        (result_id,)
    )
    result = cursor.fetchone()
    
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Result not found")
    
    # Check authorization - users can only view own results
    if current_user["role"] != "admin":
        cursor.execute("SELECT user_id FROM picks WHERE id = ?", (result[1],))
        pick = cursor.fetchone()
        if pick[0] != current_user["id"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot view other's results")
    
    return ResultResponse(
        id=result[0], pick_id=result[1], actual_scorer=result[2], is_correct=result[3],
        any_time_td=result[4], payout=result[5], graded_at=result[6]
    )


@router.post("", response_model=ResultResponse, status_code=status.HTTP_201_CREATED)
async def create_result(
    result: ResultCreate,
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
    conn: sqlite3.Connection = Depends(get_db_async)
) -> ResultResponse:
    """Create grading result (admin only)"""
    cursor = conn.cursor()
    
    # Verify pick exists
    cursor.execute("SELECT id FROM picks WHERE id = ?", (result.pick_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pick not found")
    
    # Check if already graded
    cursor.execute("SELECT id FROM results WHERE pick_id = ?", (result.pick_id,))
    if cursor.fetchone():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Pick already graded")
    
    # Insert result
    cursor.execute(
        """INSERT INTO results (pick_id, actual_scorer, is_correct, any_time_td, payout)
           VALUES (?, ?, ?, ?, ?)""",
        (result.pick_id, result.actual_scorer, result.is_correct, result.any_time_td, 
         result.payout)
    )
    conn.commit()
    
    result_id = cursor.lastrowid
    logger.info(f"Result created for pick {result.pick_id}: correct={result.is_correct}")
    
    return ResultResponse(
        id=result_id, pick_id=result.pick_id, actual_scorer=result.actual_scorer,
        is_correct=result.is_correct, any_time_td=result.any_time_td,
        payout=result.payout, graded_at=datetime.utcnow()
    )
