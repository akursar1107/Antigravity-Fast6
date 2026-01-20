"""
Pick model - represents a user's First TD prediction.

Provides type-safe representation of pick entity with all attributes.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Pick:
    """
    Represents a user's pick for first touchdown scorer.
    
    Attributes:
        id: Unique pick identifier
        user_id: ID of user who made the pick
        week_id: ID of week for this pick
        team: Team abbreviation (e.g., 'KC', 'PHI')
        player_name: Name of predicted first TD scorer
        odds: Betting odds for the pick (optional)
        theoretical_return: Expected return if correct (optional)
        game_id: NFL game identifier (optional)
        created_at: Timestamp when pick was created
        
        # Joined fields (not in picks table)
        user_name: User's name (from join)
        season: Season year (from join)
        week: Week number (from join)
    """
    id: int
    user_id: int
    week_id: int
    team: str
    player_name: str
    odds: Optional[float] = None
    theoretical_return: Optional[float] = None
    game_id: Optional[str] = None
    created_at: Optional[datetime] = None
    
    # Joined fields (optional, from database joins)
    user_name: Optional[str] = None
    season: Optional[int] = None
    week: Optional[int] = None
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Pick':
        """
        Create Pick from dictionary (e.g., from database row).
        
        Args:
            data: Dictionary with pick data
            
        Returns:
            Pick instance
        """
        return cls(
            id=data['id'],
            user_id=data['user_id'],
            week_id=data['week_id'],
            team=data['team'],
            player_name=data['player_name'],
            odds=data.get('odds'),
            theoretical_return=data.get('theoretical_return'),
            game_id=data.get('game_id'),
            created_at=data.get('created_at'),
            user_name=data.get('user_name'),
            season=data.get('season'),
            week=data.get('week')
        )
    
    def to_dict(self) -> dict:
        """
        Convert Pick to dictionary (e.g., for JSON serialization).
        
        Returns:
            Dictionary representation
        """
        result = {
            'id': self.id,
            'user_id': self.user_id,
            'week_id': self.week_id,
            'team': self.team,
            'player_name': self.player_name,
            'odds': self.odds,
            'theoretical_return': self.theoretical_return,
            'game_id': self.game_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        # Add joined fields if present
        if self.user_name:
            result['user_name'] = self.user_name
        if self.season:
            result['season'] = self.season
        if self.week:
            result['week'] = self.week
        
        return result
    
    @property
    def display_name(self) -> str:
        """Get display string for pick."""
        return f"{self.team} {self.player_name}"
    
    @property
    def has_odds(self) -> bool:
        """Check if pick has odds information."""
        return self.odds is not None and self.theoretical_return is not None
    
    def __str__(self) -> str:
        """String representation of Pick."""
        odds_str = f" (+{int(self.odds)})" if self.odds else ""
        user_str = f" by {self.user_name}" if self.user_name else ""
        return f"{self.display_name}{odds_str}{user_str}"
    
    def __repr__(self) -> str:
        """Developer-friendly representation of Pick."""
        return f"Pick(id={self.id}, user_id={self.user_id}, player='{self.player_name}')"
