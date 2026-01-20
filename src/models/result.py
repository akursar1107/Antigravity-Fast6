"""
Result model - represents the grading outcome of a pick.

Provides type-safe representation of result entity.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Result:
    """
    Represents the grading result for a pick.
    
    Attributes:
        id: Unique result identifier
        pick_id: ID of pick being graded (unique)
        actual_scorer: Name of actual first TD scorer (optional)
        is_correct: Whether pick was correct (optional until graded)
        actual_return: Actual return amount (optional)
        created_at: Timestamp when result was created
        
        # Joined fields (not in results table)
        pick: Pick object (from join)
        player_name: Predicted player name (from pick join)
        team: Team abbreviation (from pick join)
        user_name: User's name (from pick join)
        season: Season year (from pick join)
        week: Week number (from pick join)
    """
    id: int
    pick_id: int
    actual_scorer: Optional[str] = None
    is_correct: Optional[bool] = None
    actual_return: Optional[float] = None
    created_at: Optional[datetime] = None
    
    # Joined fields (optional, from database joins)
    player_name: Optional[str] = None
    team: Optional[str] = None
    user_name: Optional[str] = None
    season: Optional[int] = None
    week: Optional[int] = None
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Result':
        """
        Create Result from dictionary (e.g., from database row).
        
        Args:
            data: Dictionary with result data
            
        Returns:
            Result instance
        """
        return cls(
            id=data['id'],
            pick_id=data['pick_id'],
            actual_scorer=data.get('actual_scorer'),
            is_correct=bool(data['is_correct']) if data.get('is_correct') is not None else None,
            actual_return=data.get('actual_return'),
            created_at=data.get('created_at'),
            player_name=data.get('player_name'),
            team=data.get('team'),
            user_name=data.get('user_name'),
            season=data.get('season'),
            week=data.get('week')
        )
    
    def to_dict(self) -> dict:
        """
        Convert Result to dictionary (e.g., for JSON serialization).
        
        Returns:
            Dictionary representation
        """
        result = {
            'id': self.id,
            'pick_id': self.pick_id,
            'actual_scorer': self.actual_scorer,
            'is_correct': self.is_correct,
            'actual_return': self.actual_return,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        # Add joined fields if present
        if self.player_name:
            result['player_name'] = self.player_name
        if self.team:
            result['team'] = self.team
        if self.user_name:
            result['user_name'] = self.user_name
        if self.season:
            result['season'] = self.season
        if self.week:
            result['week'] = self.week
        
        return result
    
    @property
    def status_emoji(self) -> str:
        """Get emoji representing result status."""
        if self.is_correct is None:
            return "⏳"  # Pending
        elif self.is_correct:
            return "✅"  # Correct
        else:
            return "❌"  # Incorrect
    
    @property
    def status_text(self) -> str:
        """Get text representing result status."""
        if self.is_correct is None:
            return "Pending"
        elif self.is_correct:
            return "Correct"
        else:
            return "Incorrect"
    
    @property
    def is_graded(self) -> bool:
        """Check if result has been graded."""
        return self.is_correct is not None
    
    def __str__(self) -> str:
        """String representation of Result."""
        if not self.is_graded:
            return f"Result(pick={self.pick_id}, status=Pending)"
        
        status = "✓" if self.is_correct else "✗"
        scorer = f" (actual: {self.actual_scorer})" if self.actual_scorer else ""
        return f"Result(pick={self.pick_id}, {status}{scorer})"
    
    def __repr__(self) -> str:
        """Developer-friendly representation of Result."""
        return f"Result(id={self.id}, pick_id={self.pick_id}, is_correct={self.is_correct})"
