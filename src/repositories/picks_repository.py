"""
Picks repository - encapsulates user pick data access operations.

Handles CRUD operations for picks table with complex querying support.
"""

import sqlite3
import logging
from typing import Optional, List, Dict, Tuple

from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class PicksRepository(BaseRepository):
    """Repository for pick data access operations."""
    
    def add(self, user_id: int, week_id: int, team: str, player_name: str,
            odds: Optional[float] = None, theoretical_return: Optional[float] = None,
            game_id: Optional[str] = None) -> int:
        """
        Add a user's pick for a week.
        
        Args:
            user_id: ID of user making the pick
            week_id: ID of week for the pick
            team: Team abbreviation (e.g., 'KC', 'PHI')
            player_name: Name of player predicted to score
            odds: Betting odds for the pick (optional)
            theoretical_return: Expected return if correct (optional)
            game_id: NFL game ID for the pick (optional)
            
        Returns:
            ID of newly created pick
        """
        pick_id = self._execute_write("""
            INSERT INTO picks (user_id, week_id, team, player_name, odds, 
                             theoretical_return, game_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, week_id, team, player_name, odds, theoretical_return, game_id))
        logger.info(f"Pick added: User {user_id}, Week {week_id}, {team} {player_name}, game_id={game_id}")
        return pick_id
    
    def get_by_id(self, pick_id: int) -> Optional[Dict]:
        """
        Get pick by ID.
        
        Args:
            pick_id: Pick ID to retrieve
            
        Returns:
            Pick dictionary or None if not found
        """
        return self._execute_one("SELECT * FROM picks WHERE id = ?", (pick_id,))
    
    def get_user_week_picks(self, user_id: int, week_id: int) -> List[Dict]:
        """
        Get all picks for a user in a specific week.
        
        Args:
            user_id: User ID
            week_id: Week ID
            
        Returns:
            List of pick dictionaries ordered by creation time
        """
        return self._execute_many("""
            SELECT * FROM picks
            WHERE user_id = ? AND week_id = ?
            ORDER BY created_at
        """, (user_id, week_id))
    
    def get_week_all_picks(self, week_id: int) -> List[Dict]:
        """
        Get all picks for a week (all users) with user names.
        
        Args:
            week_id: Week ID
            
        Returns:
            List of pick dictionaries with user_name field
        """
        return self._execute_many("""
            SELECT p.*, u.name as user_name
            FROM picks p
            JOIN users u ON p.user_id = u.id
            WHERE p.week_id = ?
            ORDER BY u.name, p.created_at
        """, (week_id,))
    
    def get_user_all_picks(self, user_id: int) -> List[Dict]:
        """
        Get all picks for a user across all weeks.
        
        Args:
            user_id: User ID
            
        Returns:
            List of pick dictionaries with season, week, and user_name fields
        """
        return self._execute_many("""
            SELECT p.*, w.season, w.week, u.name as user_name
            FROM picks p
            JOIN weeks w ON p.week_id = w.id
            JOIN users u ON p.user_id = u.id
            WHERE p.user_id = ?
            ORDER BY w.season DESC, w.week DESC
        """, (user_id,))
    
    def get_season_picks(self, season: int, week: Optional[int] = None,
                        user_id: Optional[int] = None) -> List[Dict]:
        """
        Get picks for a season, optionally filtered by week and/or user.
        
        Args:
            season: Season year
            week: Week number (optional filter)
            user_id: User ID (optional filter)
            
        Returns:
            List of pick dictionaries with season, week, and user_name fields
        """
        query = """
            SELECT p.*, w.season, w.week, u.name as user_name
            FROM picks p
            JOIN weeks w ON p.week_id = w.id
            JOIN users u ON p.user_id = u.id
            WHERE w.season = ?
        """
        params = [season]
        
        if week is not None:
            query += " AND w.week = ?"
            params.append(week)
        
        if user_id is not None:
            query += " AND p.user_id = ?"
            params.append(user_id)
        
        query += " ORDER BY w.week DESC, u.name"
        
        return self._execute_many(query, tuple(params))
    
    def get_ungraded_picks(self, season: int, week: Optional[int] = None) -> List[Dict]:
        """
        Get picks that haven't been graded yet.
        
        Args:
            season: Season year
            week: Week number (optional filter)
            
        Returns:
            List of ungraded pick dictionaries
        """
        query = """
            SELECT p.*, w.season, w.week, u.name as user_name
            FROM picks p
            JOIN weeks w ON p.week_id = w.id
            JOIN users u ON p.user_id = u.id
            LEFT JOIN results r ON p.id = r.pick_id
            WHERE w.season = ? AND r.id IS NULL
        """
        params = [season]
        
        if week is not None:
            query += " AND w.week = ?"
            params.append(week)
        
        query += " ORDER BY w.week, u.name"
        
        return self._execute_many(query, tuple(params))
    
    def get_by_game_id(self, game_id: str) -> List[Dict]:
        """
        Get all picks for a specific game.
        
        Args:
            game_id: NFL game ID
            
        Returns:
            List of pick dictionaries for the game
        """
        return self._execute_many("""
            SELECT p.*, u.name as user_name
            FROM picks p
            JOIN users u ON p.user_id = u.id
            WHERE p.game_id = ?
            ORDER BY u.name
        """, (game_id,))
    
    def update(self, pick_id: int, team: Optional[str] = None, 
               player_name: Optional[str] = None, odds: Optional[float] = None,
               theoretical_return: Optional[float] = None, 
               game_id: Optional[str] = None) -> bool:
        """
        Update pick information.
        
        Args:
            pick_id: ID of pick to update
            team: New team (optional)
            player_name: New player name (optional)
            odds: New odds (optional)
            theoretical_return: New theoretical return (optional)
            game_id: New game ID (optional)
            
        Returns:
            True if pick was updated, False if not found
        """
        updates = []
        params = []
        
        if team is not None:
            updates.append("team = ?")
            params.append(team)
        if player_name is not None:
            updates.append("player_name = ?")
            params.append(player_name)
        if odds is not None:
            updates.append("odds = ?")
            params.append(odds)
        if theoretical_return is not None:
            updates.append("theoretical_return = ?")
            params.append(theoretical_return)
        if game_id is not None:
            updates.append("game_id = ?")
            params.append(game_id)
        
        if not updates:
            return False
        
        params.append(pick_id)
        query = f"UPDATE picks SET {', '.join(updates)} WHERE id = ?"
        
        affected = self._execute_write(query, tuple(params))
        if affected > 0:
            logger.info(f"Pick updated: ID {pick_id}")
        return affected > 0
    
    def delete(self, pick_id: int) -> bool:
        """
        Delete a pick (cascades to results).
        
        Args:
            pick_id: ID of pick to delete
            
        Returns:
            True if pick was deleted, False if not found
        """
        affected = self._execute_write("DELETE FROM picks WHERE id = ?", (pick_id,))
        if affected > 0:
            logger.info(f"Pick deleted: ID {pick_id}")
        return affected > 0
    
    def delete_user_week_picks(self, user_id: int, week_id: int) -> int:
        """
        Delete all picks for a user in a specific week.
        
        Args:
            user_id: User ID
            week_id: Week ID
            
        Returns:
            Number of picks deleted
        """
        count = self._execute_write(
            "DELETE FROM picks WHERE user_id = ? AND week_id = ?",
            (user_id, week_id)
        )
        if count > 0:
            logger.info(f"Deleted {count} picks for User {user_id}, Week {week_id}")
        return count
    
    def find_duplicates(self, user_id: int, week_id: int, player_name: str) -> List[Dict]:
        """
        Find duplicate picks for same user/week/player combination.
        
        Args:
            user_id: User ID
            week_id: Week ID
            player_name: Player name to check
            
        Returns:
            List of duplicate pick dictionaries
        """
        return self._execute_many("""
            SELECT * FROM picks
            WHERE user_id = ? AND week_id = ? AND player_name = ?
            ORDER BY created_at
        """, (user_id, week_id, player_name))
    
    def count(self, user_id: Optional[int] = None, week_id: Optional[int] = None) -> int:
        """
        Get count of picks, optionally filtered by user and/or week.
        
        Args:
            user_id: Filter by user ID (optional)
            week_id: Filter by week ID (optional)
            
        Returns:
            Count of picks
        """
        query = "SELECT COUNT(*) as count FROM picks WHERE 1=1"
        params = []
        
        if user_id is not None:
            query += " AND user_id = ?"
            params.append(user_id)
        
        if week_id is not None:
            query += " AND week_id = ?"
            params.append(week_id)
        
        result = self._execute_one(query, tuple(params))
        return result['count'] if result else 0
