"""
Results repository - encapsulates grading results data access operations.

Handles CRUD operations for results table with grading outcome management.
"""

import sqlite3
import logging
from typing import Optional, List, Dict

from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class ResultsRepository(BaseRepository):
    """Repository for results/grading data access operations."""
    
    def add(self, pick_id: int, actual_scorer: Optional[str] = None,
            is_correct: Optional[bool] = None, actual_return: Optional[float] = None,
            any_time_td: bool = False) -> int:
        """
        Add a grading result for a pick.
        
        Args:
            pick_id: ID of pick being graded
            actual_scorer: Name of actual first TD scorer (optional)
            is_correct: Whether pick was correct (optional)
            actual_return: Actual return amount (optional)
            any_time_td: Whether player scored any-time TD (optional)
            
        Returns:
            ID of newly created result
            
        Raises:
            ValueError: If result already exists for this pick
        """
        try:
            result_id = self._execute_write("""
                INSERT INTO results (pick_id, actual_scorer, is_correct, actual_return)
                VALUES (?, ?, ?, ?)
            """, (pick_id, actual_scorer, is_correct, actual_return))
            logger.info(f"Result added: Pick {pick_id}, Correct={is_correct}")
            return result_id
        except sqlite3.IntegrityError as e:
            logger.error(f"Result already exists for pick {pick_id}")
            raise ValueError(f"Result already exists for pick {pick_id}") from e
    
    def get_by_id(self, result_id: int) -> Optional[Dict]:
        """
        Get result by ID.
        
        Args:
            result_id: Result ID to retrieve
            
        Returns:
            Result dictionary or None if not found
        """
        return self._execute_one("SELECT * FROM results WHERE id = ?", (result_id,))
    
    def get_by_pick_id(self, pick_id: int) -> Optional[Dict]:
        """
        Get result for a specific pick.
        
        Args:
            pick_id: Pick ID to get result for
            
        Returns:
            Result dictionary or None if not graded yet
        """
        return self._execute_one("SELECT * FROM results WHERE pick_id = ?", (pick_id,))
    
    def get_all_results(self, season: Optional[int] = None, 
                       week: Optional[int] = None,
                       user_id: Optional[int] = None) -> List[Dict]:
        """
        Get all results with pick, user, and week details.
        
        Args:
            season: Filter by season (optional)
            week: Filter by week (optional)
            user_id: Filter by user (optional)
            
        Returns:
            List of result dictionaries with joined pick/user/week data
        """
        query = """
            SELECT r.*, p.*, w.season, w.week, u.name as user_name,
                   p.id as pick_id, r.id as result_id
            FROM results r
            JOIN picks p ON r.pick_id = p.id
            JOIN weeks w ON p.week_id = w.id
            JOIN users u ON p.user_id = u.id
            WHERE 1=1
        """
        params = []
        
        if season is not None:
            query += " AND w.season = ?"
            params.append(season)
        
        if week is not None:
            query += " AND w.week = ?"
            params.append(week)
        
        if user_id is not None:
            query += " AND p.user_id = ?"
            params.append(user_id)
        
        query += " ORDER BY w.season DESC, w.week DESC, u.name"
        
        return self._execute_many(query, tuple(params))
    
    def get_correct_picks(self, season: Optional[int] = None,
                         week: Optional[int] = None,
                         user_id: Optional[int] = None) -> List[Dict]:
        """
        Get only correct picks with details.
        
        Args:
            season: Filter by season (optional)
            week: Filter by week (optional)
            user_id: Filter by user (optional)
            
        Returns:
            List of correct result dictionaries
        """
        query = """
            SELECT r.*, p.*, w.season, w.week, u.name as user_name,
                   p.id as pick_id, r.id as result_id
            FROM results r
            JOIN picks p ON r.pick_id = p.id
            JOIN weeks w ON p.week_id = w.id
            JOIN users u ON p.user_id = u.id
            WHERE r.is_correct = 1
        """
        params = []
        
        if season is not None:
            query += " AND w.season = ?"
            params.append(season)
        
        if week is not None:
            query += " AND w.week = ?"
            params.append(week)
        
        if user_id is not None:
            query += " AND p.user_id = ?"
            params.append(user_id)
        
        query += " ORDER BY w.season DESC, w.week DESC"
        
        return self._execute_many(query, tuple(params))
    
    def update(self, result_id: int, actual_scorer: Optional[str] = None,
              is_correct: Optional[bool] = None, 
              actual_return: Optional[float] = None) -> bool:
        """
        Update result information.
        
        Args:
            result_id: ID of result to update
            actual_scorer: New actual scorer (optional)
            is_correct: New correctness flag (optional)
            actual_return: New actual return (optional)
            
        Returns:
            True if result was updated, False if not found
        """
        updates = []
        params = []
        
        if actual_scorer is not None:
            updates.append("actual_scorer = ?")
            params.append(actual_scorer)
        if is_correct is not None:
            updates.append("is_correct = ?")
            params.append(is_correct)
        if actual_return is not None:
            updates.append("actual_return = ?")
            params.append(actual_return)
        
        if not updates:
            return False
        
        params.append(result_id)
        query = f"UPDATE results SET {', '.join(updates)} WHERE id = ?"
        
        affected = self._execute_write(query, tuple(params))
        if affected > 0:
            logger.info(f"Result updated: ID {result_id}")
        return affected > 0
    
    def update_by_pick_id(self, pick_id: int, actual_scorer: Optional[str] = None,
                         is_correct: Optional[bool] = None,
                         actual_return: Optional[float] = None) -> bool:
        """
        Update result by pick ID (more convenient than result ID).
        
        Args:
            pick_id: ID of pick whose result to update
            actual_scorer: New actual scorer (optional)
            is_correct: New correctness flag (optional)
            actual_return: New actual return (optional)
            
        Returns:
            True if result was updated, False if not found
        """
        updates = []
        params = []
        
        if actual_scorer is not None:
            updates.append("actual_scorer = ?")
            params.append(actual_scorer)
        if is_correct is not None:
            updates.append("is_correct = ?")
            params.append(is_correct)
        if actual_return is not None:
            updates.append("actual_return = ?")
            params.append(actual_return)
        
        if not updates:
            return False
        
        params.append(pick_id)
        query = f"UPDATE results SET {', '.join(updates)} WHERE pick_id = ?"
        
        affected = self._execute_write(query, tuple(params))
        if affected > 0:
            logger.info(f"Result updated for pick: ID {pick_id}")
        return affected > 0
    
    def delete(self, result_id: int) -> bool:
        """
        Delete a result.
        
        Args:
            result_id: ID of result to delete
            
        Returns:
            True if result was deleted, False if not found
        """
        affected = self._execute_write("DELETE FROM results WHERE id = ?", (result_id,))
        if affected > 0:
            logger.info(f"Result deleted: ID {result_id}")
        return affected > 0
    
    def delete_by_pick_id(self, pick_id: int) -> bool:
        """
        Delete result by pick ID.
        
        Args:
            pick_id: ID of pick whose result to delete
            
        Returns:
            True if result was deleted, False if not found
        """
        affected = self._execute_write("DELETE FROM results WHERE pick_id = ?", (pick_id,))
        if affected > 0:
            logger.info(f"Result deleted for pick: ID {pick_id}")
        return affected > 0
    
    def delete_season_results(self, season: int, week: Optional[int] = None) -> int:
        """
        Delete all results for a season/week (for re-grading).
        
        Args:
            season: Season year
            week: Week number (optional, deletes all weeks if not specified)
            
        Returns:
            Number of results deleted
        """
        if week is not None:
            query = """
                DELETE FROM results 
                WHERE pick_id IN (
                    SELECT p.id FROM picks p
                    JOIN weeks w ON p.week_id = w.id
                    WHERE w.season = ? AND w.week = ?
                )
            """
            params = (season, week)
        else:
            query = """
                DELETE FROM results 
                WHERE pick_id IN (
                    SELECT p.id FROM picks p
                    JOIN weeks w ON p.week_id = w.id
                    WHERE w.season = ?
                )
            """
            params = (season,)
        
        count = self._execute_write(query, params)
        if count > 0:
            logger.info(f"Deleted {count} results for season {season}" + 
                       (f", week {week}" if week else ""))
        return count
    
    def count(self, is_correct: Optional[bool] = None) -> int:
        """
        Get count of results, optionally filtered by correctness.
        
        Args:
            is_correct: Filter by correct (True) or incorrect (False) picks (optional)
            
        Returns:
            Count of results
        """
        if is_correct is not None:
            result = self._execute_one(
                "SELECT COUNT(*) as count FROM results WHERE is_correct = ?",
                (is_correct,)
            )
        else:
            result = self._execute_one("SELECT COUNT(*) as count FROM results")
        return result['count'] if result else 0
    
    def get_user_stats(self, user_id: int, season: Optional[int] = None) -> Dict:
        """
        Get statistics for a user's picks.
        
        Args:
            user_id: User ID
            season: Filter by season (optional)
            
        Returns:
            Dictionary with total_picks, correct_picks, incorrect_picks, accuracy
        """
        query = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN r.is_correct = 1 THEN 1 ELSE 0 END) as correct,
                SUM(CASE WHEN r.is_correct = 0 THEN 1 ELSE 0 END) as incorrect
            FROM results r
            JOIN picks p ON r.pick_id = p.id
            JOIN weeks w ON p.week_id = w.id
            WHERE p.user_id = ?
        """
        params = [user_id]
        
        if season is not None:
            query += " AND w.season = ?"
            params.append(season)
        
        result = self._execute_one(query, tuple(params))
        
        if not result or result['total'] == 0:
            return {
                'total_picks': 0,
                'correct_picks': 0,
                'incorrect_picks': 0,
                'accuracy': 0.0
            }
        
        return {
            'total_picks': result['total'],
            'correct_picks': result['correct'] or 0,
            'incorrect_picks': result['incorrect'] or 0,
            'accuracy': round((result['correct'] or 0) / result['total'] * 100, 2)
        }
