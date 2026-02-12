"""Results Router - Pick Grading and Results"""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Dict, Any, Optional
import logging
import sqlite3
from datetime import datetime

from backend.api.fastapi_models import ResultCreate, ResultResponse, ResultUpdate
from backend.api.fastapi_dependencies import get_current_user, get_current_admin_user, get_db_async

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/results", tags=["grading"])


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
                      r.actual_return, r.created_at
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
                          r.actual_return, r.created_at
                   FROM results r
                   JOIN picks p ON r.pick_id = p.id
                   WHERE p.week_id = ?
                   ORDER BY r.created_at DESC""",
                (week_id,)
            )
        else:
            cursor.execute(
                """SELECT r.id, r.pick_id, r.actual_scorer, r.is_correct, r.any_time_td, 
                          r.actual_return, r.created_at
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
                      r.actual_return, r.created_at
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


@router.patch("/by-pick/{pick_id}", response_model=ResultResponse)
async def update_result_by_pick(
    pick_id: int,
    updates: ResultUpdate,
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
    conn: sqlite3.Connection = Depends(get_db_async)
) -> ResultResponse:
    """Update grading result for a pick (admin only). Changes win/loss and recalculates actual_return."""
    cursor = conn.cursor()
    cursor.execute("SELECT id, is_correct FROM results WHERE pick_id = ?", (pick_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pick not graded")
    result_id, _ = row

    from backend.config import config
    cursor.execute(
        """SELECT p.odds, COALESCE(u.base_bet, ?) FROM picks p
           JOIN users u ON p.user_id = u.id WHERE p.id = ?""",
        (config.ROI_STAKE, pick_id)
    )
    pick_row = cursor.fetchone()
    odds = pick_row[0] if pick_row else None
    stake = pick_row[1] if pick_row and len(pick_row) > 1 else config.ROI_STAKE
    if updates.is_correct and odds is not None and odds != 0:
        actual_return = stake * (odds / 100.0)  # profit = stake * odds/100
    else:
        actual_return = -stake if not updates.is_correct else 0.0  # loss = -stake

    cursor.execute(
        "UPDATE results SET is_correct = ?, actual_return = ? WHERE pick_id = ?",
        (int(updates.is_correct), actual_return, pick_id)
    )
    conn.commit()

    from backend.database.stats import clear_leaderboard_cache
    clear_leaderboard_cache()

    cursor.execute(
        """SELECT r.id, r.pick_id, r.actual_scorer, r.is_correct, r.any_time_td, 
                  r.actual_return, r.created_at
           FROM results r WHERE r.pick_id = ?""",
        (pick_id,)
    )
    r = cursor.fetchone()
    logger.info(f"Admin {current_user['name']} updated result for pick {pick_id}: is_correct={updates.is_correct}")
    return ResultResponse(
        id=r[0], pick_id=r[1], actual_scorer=r[2], is_correct=bool(r[3]),
        any_time_td=bool(r[4]) if r[4] is not None else None,
        payout=r[5], graded_at=r[6]
    )


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
                  r.actual_return, r.created_at
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
        """INSERT INTO results (pick_id, actual_scorer, is_correct, any_time_td, actual_return)
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
