"""Picks Router - Pick Creation, Listing, and Deletion"""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Dict, Any, Optional
import logging
import sqlite3

from src.api.fastapi_models import PickCreate, PickResponse, PickUpdate
from src.api.fastapi_dependencies import get_current_user, get_current_admin_user, get_db_async

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/picks", tags=["picks"])


@router.get("", response_model=List[PickResponse])
async def list_picks(
    week_id: Optional[int] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db_async)
) -> List[PickResponse]:
    """
    List picks (own picks for regular users, all picks for admin).
    
    Query Parameters:
        week_id: Optional filter by week
    """
    cursor = conn.cursor()
    
    # Admin can see all picks, users see only their own
    if current_user["role"] == "admin":
        if week_id:
            cursor.execute(
                "SELECT id, user_id, week_id, team, player_name, position, odds, game_id, created_at "
                "FROM picks WHERE week_id = ? ORDER BY created_at DESC",
                (week_id,)
            )
        else:
            cursor.execute(
                "SELECT id, user_id, week_id, team, player_name, position, odds, game_id, created_at "
                "FROM picks ORDER BY created_at DESC"
            )
    else:
        if week_id:
            cursor.execute(
                "SELECT id, user_id, week_id, team, player_name, position, odds, game_id, created_at "
                "FROM picks WHERE user_id = ? AND week_id = ? ORDER BY created_at DESC",
                (current_user["id"], week_id)
            )
        else:
            cursor.execute(
                "SELECT id, user_id, week_id, team, player_name, position, odds, game_id, created_at "
                "FROM picks WHERE user_id = ? ORDER BY created_at DESC",
                (current_user["id"],)
            )
    
    picks = cursor.fetchall()
    return [
        PickResponse(
            id=p[0], user_id=p[1], week_id=p[2], team=p[3], player_name=p[4],
            position=p[5], odds=p[6], game_id=p[7], created_at=p[8]
        )
        for p in picks
    ]


@router.get("/{pick_id}", response_model=PickResponse)
async def get_pick(
    pick_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db_async)
) -> PickResponse:
    """Get specific pick (own pick or admin can view any)"""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, user_id, week_id, team, player_name, position, odds, game_id, created_at FROM picks WHERE id = ?",
        (pick_id,)
    )
    pick = cursor.fetchone()
    
    if not pick:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pick not found")
    
    # Check authorization
    if pick[1] != current_user["id"] and current_user["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot view other user's picks")
    
    return PickResponse(
        id=pick[0], user_id=pick[1], week_id=pick[2], team=pick[3], player_name=pick[4],
        position=pick[5], odds=pick[6], game_id=pick[7], created_at=pick[8]
    )


@router.post("", response_model=PickResponse, status_code=status.HTTP_201_CREATED)
async def create_pick(
    pick: PickCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db_async)
) -> PickResponse:
    """Create a new pick"""
    cursor = conn.cursor()
    
    # Verify week exists
    cursor.execute("SELECT id FROM weeks WHERE id = ?", (pick.week_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Week not found")
    
    # Check for duplicate (same user, week, player)
    cursor.execute(
        "SELECT id FROM picks WHERE user_id = ? AND week_id = ? AND LOWER(player_name) = LOWER(?)",
        (current_user["id"], pick.week_id, pick.player_name)
    )
    if cursor.fetchone():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have a pick for this player in this week"
        )
    
    # Get player position if not provided (auto-assignment from rosters table)
    position = pick.position
    if not position:
        cursor.execute(
            "SELECT position FROM rosters WHERE LOWER(player_name) = LOWER(?) AND team = ?",
            (pick.player_name, pick.team)
        )
        result = cursor.fetchone()
        position = result[0] if result else None
    
    # Insert pick
    cursor.execute(
        "INSERT INTO picks (user_id, week_id, team, player_name, position, odds, game_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (current_user["id"], pick.week_id, pick.team, pick.player_name, position, pick.odds, pick.game_id)
    )
    conn.commit()
    
    pick_id = cursor.lastrowid
    logger.info(f"Pick created: {current_user['name']} picked {pick.player_name} (ID: {pick_id})")
    
    return PickResponse(
        id=pick_id, user_id=current_user["id"], week_id=pick.week_id, team=pick.team,
        player_name=pick.player_name, position=position, odds=pick.odds, game_id=pick.game_id,
        created_at=__import__('datetime').datetime.utcnow()
    )


@router.patch("/{pick_id}", response_model=PickResponse)
async def update_pick(
    pick_id: int,
    updates: PickUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db_async)
) -> PickResponse:
    """Update pick (only before grading)"""
    cursor = conn.cursor()
    
    # Get existing pick
    cursor.execute(
        "SELECT id, user_id, week_id, team, player_name, position, odds, game_id FROM picks WHERE id = ?",
        (pick_id,)
    )
    pick = cursor.fetchone()
    
    if not pick:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pick not found")
    
    # Check ownership
    if pick[1] != current_user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Can only edit your own picks")
    
    # Check if already graded
    cursor.execute("SELECT id FROM results WHERE pick_id = ?", (pick_id,))
    if cursor.fetchone():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot edit graded picks")
    
    # Prepare update
    update_fields = []
    update_values = []
    
    if updates.team is not None:
        update_fields.append("team = ?")
        update_values.append(updates.team)
    
    if updates.player_name is not None:
        update_fields.append("player_name = ?")
        update_values.append(updates.player_name)
        # Auto-update position when player changes
        cursor.execute(
            "SELECT position FROM rosters WHERE LOWER(player_name) = LOWER(?) AND team = ?",
            (updates.player_name, updates.team or pick[3])
        )
        result = cursor.fetchone()
        if result:
            update_fields.append("position = ?")
            update_values.append(result[0])
    
    if updates.odds is not None:
        update_fields.append("odds = ?")
        update_values.append(updates.odds)
    
    if not update_fields:
        # No updates, return current pick
        return PickResponse(
            id=pick[0], user_id=pick[1], week_id=pick[2], team=pick[3],
            player_name=pick[4], position=pick[5], odds=pick[6], game_id=pick[7],
            created_at=__import__('datetime').datetime.utcnow()
        )
    
    # Execute update
    update_values.append(pick_id)
    query = f"UPDATE picks SET {', '.join(update_fields)} WHERE id = ?"
    cursor.execute(query, update_values)
    conn.commit()
    
    logger.info(f"Pick updated: ID {pick_id}")
    
    # Return updated pick
    cursor.execute(
        "SELECT id, user_id, week_id, team, player_name, position, odds, game_id, created_at FROM picks WHERE id = ?",
        (pick_id,)
    )
    updated = cursor.fetchone()
    
    return PickResponse(
        id=updated[0], user_id=updated[1], week_id=updated[2], team=updated[3],
        player_name=updated[4], position=updated[5], odds=updated[6], game_id=updated[7],
        created_at=updated[8]
    )


@router.delete("/{pick_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pick(
    pick_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db_async)
) -> None:
    """Delete pick (own pick or admin)"""
    cursor = conn.cursor()
    
    # Get pick
    cursor.execute("SELECT user_id FROM picks WHERE id = ?", (pick_id,))
    pick = cursor.fetchone()
    
    if not pick:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pick not found")
    
    # Check authorization
    if pick[0] != current_user["id"] and current_user["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot delete other user's picks")
    
    # Check if already graded
    cursor.execute("SELECT id FROM results WHERE pick_id = ?", (pick_id,))
    if cursor.fetchone():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete graded picks")
    
    cursor.execute("DELETE FROM picks WHERE id = ?", (pick_id,))
    conn.commit()
    
    logger.info(f"Pick deleted: ID {pick_id}")
