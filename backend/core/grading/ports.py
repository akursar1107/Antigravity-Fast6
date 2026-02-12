"""Grading repository ports"""

from abc import ABC, abstractmethod
from typing import Optional, List
from backend.core.grading.entities import Result


class ResultRepository(ABC):
    """Abstract Result repository"""
    
    @abstractmethod
    def save_result(self, result: Result) -> int:
        """Save grading result"""
        pass
    
    @abstractmethod
    def get_results_by_pick(self, pick_id: int) -> Optional[Result]:
        """Get result for a pick"""
        pass
    
    @abstractmethod
    def get_ungraded_picks(self, week_id: int) -> List[dict]:
        """Get all ungraded picks for a week"""
        pass


class PlayByPlayRepository(ABC):
    """Abstract PBP data repository"""
    
    @abstractmethod
    def get_week_pbp(self, season: int, week: int) -> dict:
        """Get play-by-play data for week"""
        pass
    
    @abstractmethod
    def get_first_td_scorers(self, game_id: str) -> List[str]:
        """Get first TD scorers for a game"""
        pass
