"""Picks domain entities - pure Pydantic models, no Streamlit/DB coupling"""

from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from typing import Optional


class PickStatus(str, Enum):
    """Pick status lifecycle"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    GRADED = "graded"


class Pick(BaseModel):
    """Core pick entity - aligns with picks table schema (migration v11)"""
    id: Optional[int] = None
    user_id: int
    week_id: int
    game_id: str  # NFL game identifier
    team: str  # Betting team
    player_name: str
    odds: float
    theoretical_return: Optional[float] = None
    status: PickStatus = PickStatus.PENDING  # Derived, not persisted
    created_at: Optional[datetime] = None

    class Config:
        use_enum_values = False


class GameInfo(BaseModel):
    """Game context for validation"""
    game_id: str
    home_team: str
    away_team: str
    kickoff_time: datetime
    week: int
    season: int
