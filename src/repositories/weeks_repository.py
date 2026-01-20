"""
Weeks repository - encapsulates season/week data access operations.

Handles CRUD operations for weeks table with season/week management.
"""

import sqlite3
import logging
from typing import Optional, List, Dict
from datetime import datetime

from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class WeeksRepository(BaseRepository):
    """Repository for week/season data access operations."""
    
    def add(self, season: int, week: int, started_at: Optional[datetime] = None,
            ended_at: Optional[datetime] = None) -> int:
        """
        Add a season/week entry.
        
        Args:
            season: Season year (e.g., 2024)
            week: Week number (1-18 for regular season, 19+ for playoffs)
            started_at: When week started (optional)
            ended_at: When week ended (optional)
            
        Returns:
            ID of newly created week, or existing week ID if already exists
        """
        try:
            week_id = self._execute_write("""
                INSERT INTO weeks (season, week, started_at, ended_at)
                VALUES (?, ?, ?, ?)
            """, (season, week, started_at, ended_at))
            logger.info(f"Week added: Season {season}, Week {week} (ID: {week_id})")
            return week_id
        except sqlite3.IntegrityError:
            # Week already exists, return existing ID
            logger.warning(f"Week already exists: Season {season}, Week {week}")
            existing = self.get_by_season_week(season, week)
            return existing['id'] if existing else -1
    
    def get_by_id(self, week_id: int) -> Optional[Dict]:
        """
        Get week by ID.
        
        Args:
            week_id: Week ID to retrieve
            
        Returns:
            Week dictionary or None if not found
        """
        return self._execute_one("SELECT * FROM weeks WHERE id = ?", (week_id,))
    
    def get_by_season_week(self, season: int, week: int) -> Optional[Dict]:
        """
        Get week by season and week number.
        
        Args:
            season: Season year
            week: Week number
            
        Returns:
            Week dictionary or None if not found
        """
        return self._execute_one(
            "SELECT * FROM weeks WHERE season = ? AND week = ?",
            (season, week)
        )
    
    def get_all(self, season: Optional[int] = None) -> List[Dict]:
        """
        Get all weeks, optionally filtered by season.
        
        Args:
            season: Filter by season year (optional)
            
        Returns:
            List of week dictionaries, ordered by season DESC, week DESC
        """
        if season:
            return self._execute_many(
                "SELECT * FROM weeks WHERE season = ? ORDER BY season DESC, week DESC",
                (season,)
            )
        return self._execute_many("SELECT * FROM weeks ORDER BY season DESC, week DESC")
    
    def get_seasons(self) -> List[int]:
        """
        Get all distinct seasons that have weeks.
        
        Returns:
            List of season years, ordered DESC
        """
        results = self._execute_many("SELECT DISTINCT season FROM weeks ORDER BY season DESC")
        return [r['season'] for r in results]
    
    def get_weeks_for_season(self, season: int) -> List[int]:
        """
        Get all week numbers for a given season.
        
        Args:
            season: Season year
            
        Returns:
            List of week numbers, ordered ASC
        """
        results = self._execute_many(
            "SELECT week FROM weeks WHERE season = ? ORDER BY week ASC",
            (season,)
        )
        return [r['week'] for r in results]
    
    def get_latest_week(self) -> Optional[Dict]:
        """
        Get the most recent week entry.
        
        Returns:
            Week dictionary or None if no weeks exist
        """
        return self._execute_one(
            "SELECT * FROM weeks ORDER BY season DESC, week DESC LIMIT 1"
        )
    
    def update_timestamps(self, week_id: int, started_at: Optional[datetime] = None,
                         ended_at: Optional[datetime] = None) -> bool:
        """
        Update week start/end timestamps.
        
        Args:
            week_id: ID of week to update
            started_at: New start timestamp (optional)
            ended_at: New end timestamp (optional)
            
        Returns:
            True if week was updated, False if not found
        """
        updates = []
        params = []
        
        if started_at is not None:
            updates.append("started_at = ?")
            params.append(started_at)
        if ended_at is not None:
            updates.append("ended_at = ?")
            params.append(ended_at)
        
        if not updates:
            return False
        
        params.append(week_id)
        query = f"UPDATE weeks SET {', '.join(updates)} WHERE id = ?"
        
        affected = self._execute_write(query, tuple(params))
        if affected > 0:
            logger.info(f"Week timestamps updated: ID {week_id}")
        return affected > 0
    
    def exists(self, season: int, week: int) -> bool:
        """
        Check if a season/week entry exists.
        
        Args:
            season: Season year
            week: Week number
            
        Returns:
            True if week exists, False otherwise
        """
        result = self._execute_one(
            "SELECT 1 FROM weeks WHERE season = ? AND week = ?",
            (season, week)
        )
        return result is not None
    
    def count(self, season: Optional[int] = None) -> int:
        """
        Get count of weeks, optionally filtered by season.
        
        Args:
            season: Filter by season year (optional)
            
        Returns:
            Count of weeks
        """
        if season:
            result = self._execute_one(
                "SELECT COUNT(*) as count FROM weeks WHERE season = ?",
                (season,)
            )
        else:
            result = self._execute_one("SELECT COUNT(*) as count FROM weeks")
        return result['count'] if result else 0
