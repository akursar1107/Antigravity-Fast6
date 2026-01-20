"""
Week model - represents an NFL season week.

Provides type-safe representation of season/week entity.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Week:
    """
    Represents a season/week in the NFL calendar.
    
    Attributes:
        id: Unique week identifier
        season: NFL season year (e.g., 2025)
        week: Week number (1-18 regular season, 19+ playoffs)
        started_at: When week started (optional)
        ended_at: When week ended (optional)
        created_at: Timestamp when record was created
    """
    id: int
    season: int
    week: int
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Week':
        """
        Create Week from dictionary (e.g., from database row).
        
        Args:
            data: Dictionary with week data
            
        Returns:
            Week instance
        """
        return cls(
            id=data['id'],
            season=data['season'],
            week=data['week'],
            started_at=data.get('started_at'),
            ended_at=data.get('ended_at'),
            created_at=data.get('created_at')
        )
    
    def to_dict(self) -> dict:
        """
        Convert Week to dictionary (e.g., for JSON serialization).
        
        Returns:
            Dictionary representation
        """
        return {
            'id': self.id,
            'season': self.season,
            'week': self.week,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @property
    def is_playoff(self) -> bool:
        """Check if this is a playoff week."""
        return self.week >= 19
    
    @property
    def display_name(self) -> str:
        """Get display name for week (e.g., 'Week 1' or 'Wild Card')."""
        if self.week >= 22:
            return "Super Bowl"
        elif self.week == 21:
            return "Conference Championships"
        elif self.week == 20:
            return "Divisional Round"
        elif self.week == 19:
            return "Wild Card"
        else:
            return f"Week {self.week}"
    
    def __str__(self) -> str:
        """String representation of Week."""
        return f"{self.season} {self.display_name}"
    
    def __repr__(self) -> str:
        """Developer-friendly representation of Week."""
        return f"Week(id={self.id}, season={self.season}, week={self.week})"
