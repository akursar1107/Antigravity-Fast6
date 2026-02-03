"""Picks repository ports (abstract interfaces for dependency injection)"""

from abc import ABC, abstractmethod
from typing import List, Optional
from src.core.picks.entities import Pick


class PickRepository(ABC):
    """Abstract Pick repository - implemented by data layer"""
    
    @abstractmethod
    def save(self, pick: Pick) -> int:
        """Save pick, return pick_id"""
        pass
    
    @abstractmethod
    def get_by_id(self, pick_id: int) -> Optional[Pick]:
        """Get pick by ID"""
        pass
    
    @abstractmethod
    def get_user_picks(self, user_id: int, week_id: Optional[int] = None) -> List[Pick]:
        """Get all picks for user, optionally filtered by week"""
        pass
    
    @abstractmethod
    def update(self, pick_id: int, **kwargs) -> Pick:
        """Update pick fields"""
        pass
    
    @abstractmethod
    def delete(self, pick_id: int) -> bool:
        """Delete pick, return success"""
        pass


class GameRepository(ABC):
    """Abstract Game repository"""
    
    @abstractmethod
    def get_game_info(self, game_id: str) -> Optional[dict]:
        """Get game details by game_id"""
        pass
