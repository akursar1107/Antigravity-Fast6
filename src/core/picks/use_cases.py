"""Picks use cases - orchestrates business logic"""

from datetime import datetime
from typing import Optional
from src.core.picks.entities import Pick, PickStatus, GameInfo
from src.core.picks.ports import PickRepository, GameRepository
from src.core.picks.errors import (
    PickValidationError,
    GameAlreadyStartedError,
    DuplicatePickError,
)
from src.lib.observability import track_operation, log_event


def create_pick(
    user_id: int,
    week_id: int,
    game_id: str,
    team: str,
    player_name: str,
    odds: float,
    pick_repository: PickRepository,
    game_repository: Optional[GameRepository] = None,
) -> Pick:
    """Use case: User creates a new pick"""
    
    with track_operation("create_pick", {"user_id": user_id, "player": player_name}):
        # Check for duplicates first
        existing = pick_repository.get_user_picks(user_id, week_id)
        if any(p.game_id == game_id for p in existing):
            raise DuplicatePickError(f"User already has a pick for game {game_id}")
        
        # Create and save pick
        pick = Pick(
            user_id=user_id,
            week_id=week_id,
            game_id=game_id,
            team=team,
            player_name=player_name,
            odds=odds,
            status=PickStatus.CONFIRMED,
            created_at=datetime.now(),
        )
        
        pick_id = pick_repository.save(pick)
        pick.id = pick_id
        
        log_event("pick_created", {
            "pick_id": pick_id,
            "user_id": user_id,
            "player": player_name,
            "odds": odds,
        })
        
        return pick


def list_user_picks(
    user_id: int,
    week_id: int,
    pick_repository: PickRepository,
) -> list[Pick]:
    """Use case: List user's picks for a week"""
    return pick_repository.get_user_picks(user_id, week_id)


def validate_pick(
    user_id: int,
    game_id: str,
    game_repository: Optional[GameRepository],
    pick_repository: PickRepository,
) -> dict:
    """Use case: Validate a pick is possible"""
    
    # Check for duplicate
    existing = pick_repository.get_user_picks(user_id)
    if any(p.game_id == game_id for p in existing):
        return {"valid": False, "error": "You already have a pick for this game"}
    
    return {"valid": True}


def cancel_pick(
    pick_id: int,
    pick_repository: PickRepository,
) -> bool:
    """Use case: Cancel a pick"""
    
    with track_operation("cancel_pick", {"pick_id": pick_id}):
        result = pick_repository.delete(pick_id)
        if result:
            log_event("pick_cancelled", {"pick_id": pick_id})
        return result
