"""Picks Router - Pick Creation, Listing, and Deletion"""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import sqlite3

from backend.api.fastapi_models import PickCreate, PickResponse, PickUpdate
from backend.api.fastapi_dependencies import get_current_user
from backend.database import (
    add_pick,
    get_pick,
    get_user_week_picks,
    get_user_all_picks,
    get_all_picks,
    delete_pick,
    update_pick as db_update_pick,
)
from backend.database.weeks import get_week
from backend.database.stats import get_result_for_pick

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/picks", tags=["picks"])


def _to_pick_response(p: Dict[str, Any]) -> PickResponse:
    """Convert database pick dict to PickResponse."""
    return PickResponse(
        id=p["id"],
        user_id=p["user_id"],
        week_id=p["week_id"],
        team=p["team"],
        player_name=p["player_name"],
        odds=p.get("odds"),
        game_id=p.get("game_id"),
        created_at=p.get("created_at") or datetime.utcnow(),
    )


@router.get("", response_model=List[PickResponse])
async def list_picks(
    week_id: Optional[int] = None,
    user_id: Optional[int] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> List[PickResponse]:
    """
    List picks (own picks for regular users, all picks for admin).

    Query Parameters:
        week_id: Optional filter by week
        user_id: Optional filter by user (admin only)
    """
    if current_user["role"] == "admin":
        if user_id is not None:
            picks = get_user_all_picks(user_id)
        else:
            picks = get_all_picks(week_id=week_id)
    else:
        if user_id is not None and user_id != current_user["id"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot list other user's picks")
        if week_id:
            picks = get_user_week_picks(current_user["id"], week_id)
        else:
            picks = get_user_all_picks(current_user["id"])
    return [_to_pick_response(p) for p in picks]


@router.get("/{pick_id}", response_model=PickResponse)
async def get_pick_endpoint(
    pick_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> PickResponse:
    """Get specific pick (own pick or admin can view any)"""
    pick = get_pick(pick_id)
    if not pick:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pick not found")
    if pick["user_id"] != current_user["id"] and current_user["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot view other user's picks")
    return _to_pick_response(pick)


@router.post("", response_model=PickResponse, status_code=status.HTTP_201_CREATED)
async def create_pick(
    pick: PickCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> PickResponse:
    """Create a new pick"""
    if not get_week(pick.week_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Week not found")

    existing = get_user_week_picks(current_user["id"], pick.week_id)
    if any(
        p.get("player_name", "").lower() == pick.player_name.lower()
        for p in existing
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have a pick for this player in this week",
        )

    try:
        pick_id = add_pick(
            user_id=current_user["id"],
            week_id=pick.week_id,
            team=pick.team,
            player_name=pick.player_name,
            odds=pick.odds,
            game_id=pick.game_id,
        )
    except ValueError as e:
        if "already exists" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You already have a pick for this player in this week",
            )
        raise

    created = get_pick(pick_id)
    logger.info(f"Pick created: {current_user['name']} picked {pick.player_name} (ID: {pick_id})")
    return _to_pick_response(created)


@router.patch("/{pick_id}", response_model=PickResponse)
async def update_pick(
    pick_id: int,
    updates: PickUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> PickResponse:
    """Update pick (only before grading)"""
    pick = get_pick(pick_id)
    if not pick:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pick not found")
    if pick["user_id"] != current_user["id"] and current_user["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Can only edit your own picks")
    if get_result_for_pick(pick_id) and current_user["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot edit graded picks")

    if updates.team is not None or updates.player_name is not None or updates.odds is not None:
        try:
            db_update_pick(
                pick_id,
                team=updates.team,
                player_name=updates.player_name,
                odds=updates.odds,
            )
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed" in str(e) and "picks" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="You already have a pick for this player in this week",
                ) from e
            raise

    updated = get_pick(pick_id)
    logger.info(f"Pick updated: ID {pick_id}")
    return _to_pick_response(updated)


@router.delete("/{pick_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pick_endpoint(
    pick_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> None:
    """Delete pick (own pick or admin)"""
    pick = get_pick(pick_id)
    if not pick:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pick not found")
    if pick["user_id"] != current_user["id"] and current_user["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot delete other user's picks")
    if get_result_for_pick(pick_id) and current_user["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete graded picks")

    delete_pick(pick_id)
    logger.info(f"Pick deleted: ID {pick_id}")
