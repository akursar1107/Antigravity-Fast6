"""
Users repository - encapsulates all user data access operations.

Handles CRUD operations for users table with business-friendly interface.
"""

import sqlite3
import logging
from typing import Optional, List, Dict

from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class UsersRepository(BaseRepository):
    """Repository for user data access operations."""
    
    def add(self, name: str, email: Optional[str] = None, is_admin: bool = False) -> int:
        """
        Add a new user to the group.
        
        Args:
            name: User's display name (must be unique)
            email: User's email address (optional, unique)
            is_admin: Whether user has admin privileges
            
        Returns:
            ID of newly created user
            
        Raises:
            ValueError: If user with same name already exists
        """
        try:
            user_id = self._execute_write("""
                INSERT INTO users (name, email, is_admin)
                VALUES (?, ?, ?)
            """, (name, email, is_admin))
            logger.info(f"User added: {name} (ID: {user_id})")
            return user_id
        except sqlite3.IntegrityError as e:
            logger.error(f"User already exists: {name}")
            raise ValueError(f"User '{name}' already exists") from e
    
    def get_by_id(self, user_id: int) -> Optional[Dict]:
        """
        Get user by ID.
        
        Args:
            user_id: User ID to retrieve
            
        Returns:
            User dictionary or None if not found
        """
        return self._execute_one("SELECT * FROM users WHERE id = ?", (user_id,))
    
    def get_by_name(self, name: str) -> Optional[Dict]:
        """
        Get user by name (case-sensitive).
        
        Args:
            name: User name to search for
            
        Returns:
            User dictionary or None if not found
        """
        return self._execute_one("SELECT * FROM users WHERE name = ?", (name,))
    
    def get_all(self) -> List[Dict]:
        """
        Get all users in the group, ordered by name.
        
        Returns:
            List of user dictionaries
        """
        return self._execute_many("SELECT * FROM users ORDER BY name")
    
    def get_admins(self) -> List[Dict]:
        """
        Get all users with admin privileges.
        
        Returns:
            List of admin user dictionaries
        """
        return self._execute_many("SELECT * FROM users WHERE is_admin = 1 ORDER BY name")
    
    def update(self, user_id: int, name: Optional[str] = None, 
               email: Optional[str] = None, is_admin: Optional[bool] = None) -> bool:
        """
        Update user information.
        
        Args:
            user_id: ID of user to update
            name: New name (optional)
            email: New email (optional)
            is_admin: New admin status (optional)
            
        Returns:
            True if user was updated, False if not found
        """
        # Build dynamic UPDATE query based on provided fields
        updates = []
        params = []
        
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if email is not None:
            updates.append("email = ?")
            params.append(email)
        if is_admin is not None:
            updates.append("is_admin = ?")
            params.append(is_admin)
        
        if not updates:
            return False  # Nothing to update
        
        params.append(user_id)
        query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
        
        affected = self._execute_write(query, tuple(params))
        if affected > 0:
            logger.info(f"User updated: ID {user_id}")
        return affected > 0
    
    def delete(self, user_id: int) -> bool:
        """
        Delete a user (cascades to picks and results).
        
        Args:
            user_id: ID of user to delete
            
        Returns:
            True if user was deleted, False if not found
        """
        affected = self._execute_write("DELETE FROM users WHERE id = ?", (user_id,))
        if affected > 0:
            logger.info(f"User deleted: ID {user_id}")
        return affected > 0
    
    def exists(self, user_id: int) -> bool:
        """
        Check if user exists.
        
        Args:
            user_id: User ID to check
            
        Returns:
            True if user exists, False otherwise
        """
        result = self._execute_one("SELECT 1 FROM users WHERE id = ?", (user_id,))
        return result is not None
    
    def count(self) -> int:
        """
        Get total number of users.
        
        Returns:
            Count of all users
        """
        result = self._execute_one("SELECT COUNT(*) as count FROM users")
        return result['count'] if result else 0
