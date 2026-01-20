"""
User model - represents a Fast6 group member.

Provides type-safe representation of user entity with all attributes.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    """
    Represents a user in the Fast6 group.
    
    Attributes:
        id: Unique user identifier
        name: User's display name (unique)
        email: User's email address (optional, unique)
        group_id: Group identifier (default: 1)
        is_admin: Whether user has admin privileges
        created_at: Timestamp when user was created
    """
    id: int
    name: str
    email: Optional[str] = None
    group_id: int = 1
    is_admin: bool = False
    created_at: Optional[datetime] = None
    
    @classmethod
    def from_dict(cls, data: dict) -> 'User':
        """
        Create User from dictionary (e.g., from database row).
        
        Args:
            data: Dictionary with user data
            
        Returns:
            User instance
        """
        return cls(
            id=data['id'],
            name=data['name'],
            email=data.get('email'),
            group_id=data.get('group_id', 1),
            is_admin=bool(data.get('is_admin', False)),
            created_at=data.get('created_at')
        )
    
    def to_dict(self) -> dict:
        """
        Convert User to dictionary (e.g., for JSON serialization).
        
        Returns:
            Dictionary representation
        """
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'group_id': self.group_id,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __str__(self) -> str:
        """String representation of User."""
        admin_str = " (Admin)" if self.is_admin else ""
        return f"{self.name}{admin_str}"
    
    def __repr__(self) -> str:
        """Developer-friendly representation of User."""
        return f"User(id={self.id}, name='{self.name}', is_admin={self.is_admin})"
