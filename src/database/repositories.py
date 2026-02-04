"""
Specialized Repository Classes
Entity-specific repositories that extend BaseRepository with domain-specific logic.

Benefits:
- Reduces code duplication across database modules
- Standardizes CRUD operations per entity
- Centralized query logic for each table
- Type-safe with TypedDict definitions
"""

from typing import Optional, List, Dict, Any
import sqlite3
import logging
from datetime import datetime

from .base_repository import BaseRepository
from .connection import get_db_context
from src.utils.types import User, Week, Pick, Result, KickoffDecision, MarketOdds
from src.utils.error_handling import log_exception
from src.utils.caching import invalidate_on_pick_change, invalidate_on_result_change, invalidate_on_grading_complete

logger = logging.getLogger(__name__)


# ============= USER REPOSITORY =============

class UserRepository(BaseRepository):
    """Repository for user management operations."""
    
    table_name = 'users'
    
    def find_by_name(self, name: str) -> Optional[User]:
        """Find a user by name."""
        results = self.find_where({'name': name})
        return dict(results[0]) if results else None
    
    def find_by_email(self, email: str) -> Optional[User]:
        """Find a user by email."""
        results = self.find_where({'email': email})
        return dict(results[0]) if results else None
    
    def find_all_admins(self) -> List[User]:
        """Find all admin users."""
        results = self.find_where({'is_admin': 1})
        return [dict(row) for row in results]
    
    def find_all_by_group(self, group_id: int) -> List[User]:
        """Find all users in a specific group."""
        results = self.find_where({'group_id': group_id}, order_by='name')
        return [dict(row) for row in results]
    
    def create(self, name: str, email: Optional[str] = None, is_admin: bool = False, 
               group_id: Optional[int] = None) -> int:
        """Create a new user and return the user ID."""
        data = {
            'name': name,
            'email': email,
            'is_admin': 1 if is_admin else 0,
            'group_id': group_id
        }
        user_id = self.insert(data)
        logger.info(f"User created: {name} (ID: {user_id})")
        return user_id
    
    def delete_by_id(self, user_id: int) -> bool:
        """Delete a user and invalidate related caches."""
        success = self.delete(user_id)
        if success:
            logger.info(f"User deleted: ID {user_id}")
            invalidate_on_pick_change()
        return success


# ============= WEEK REPOSITORY =============

class WeekRepository(BaseRepository):
    """Repository for season/week management operations."""
    
    table_name = 'weeks'
    
    def find_by_season_and_week(self, season: int, week: int) -> Optional[Week]:
        """Find a week by season and week number."""
        results = self.find_where({'season': season, 'week': week})
        if results:
            row = dict(results[0])
            # Ensure integer conversion
            row['season'] = int(row['season'])
            row['week'] = int(row['week'])
            return row
        return None
    
    def find_by_season(self, season: int) -> List[Week]:
        """Find all weeks in a specific season."""
        results = self.find_where({'season': season}, order_by='week')
        output = []
        for row in results:
            w = dict(row)
            w['season'] = int(w['season'])
            w['week'] = int(w['week'])
            output.append(w)
        return output
    
    def find_current_week(self, season: int) -> Optional[Week]:
        """
        Find the current/latest week for a season.
        Assumes the week with the highest number is current.
        """
        query = f"SELECT * FROM {self.table_name} WHERE season = ? ORDER BY week DESC LIMIT 1"
        with get_db_context() as conn:
            cursor = conn.execute(query, (season,))
            result = cursor.fetchone()
            if result:
                row = dict(result)
                row['season'] = int(row['season'])
                row['week'] = int(row['week'])
                return row
        return None
    
    def create(self, season: int, week: int, started_at: Optional[datetime] = None,
               ended_at: Optional[datetime] = None) -> int:
        """Create a new season/week entry and return the week ID."""
        data = {
            'season': season,
            'week': week,
            'started_at': started_at,
            'ended_at': ended_at
        }
        week_id = self.insert(data)
        logger.info(f"Week created: Season {season}, Week {week} (ID: {week_id})")
        return week_id


# ============= PICK REPOSITORY =============

class PickRepository(BaseRepository):
    """Repository for user pick management operations."""
    
    table_name = 'picks'
    
    def find_by_user_and_week(self, user_id: int, week_id: int) -> List[Pick]:
        """Find all picks for a user in a specific week."""
        query = f"SELECT * FROM {self.table_name} WHERE user_id = ? AND week_id = ? ORDER BY created_at"
        with get_db_context() as conn:
            cursor = conn.execute(query, (user_id, week_id))
            return [dict(row) for row in cursor.fetchall()]
    
    def find_by_week(self, week_id: int) -> List[Pick]:
        """Find all picks for a specific week (all users)."""
        query = """
            SELECT p.*, u.name as user_name
            FROM picks p
            JOIN users u ON p.user_id = u.id
            WHERE p.week_id = ?
            ORDER BY u.name, p.created_at
        """
        with get_db_context() as conn:
            cursor = conn.execute(query, (week_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def find_by_user(self, user_id: int) -> List[Pick]:
        """Find all picks for a user across all weeks."""
        query = """
            SELECT p.*, w.season, w.week, u.name as user_name
            FROM picks p
            JOIN weeks w ON p.week_id = w.id
            JOIN users u ON p.user_id = u.id
            WHERE p.user_id = ?
            ORDER BY w.season DESC, w.week DESC
        """
        with get_db_context() as conn:
            cursor = conn.execute(query, (user_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def find_ungraded(self, season: int, week: Optional[int] = None) -> List[Pick]:
        """Find ungraded picks for a season (optionally filtered by week)."""
        query = """
            SELECT p.*, u.name as user_name, w.season, w.week
            FROM picks p
            JOIN users u ON p.user_id = u.id
            JOIN weeks w ON p.week_id = w.id
            LEFT JOIN results r ON p.id = r.pick_id
            WHERE w.season = ?
            AND (r.id IS NULL OR r.is_correct IS NULL)
        """
        params = [season]
        
        if week is not None:
            query += " AND w.week = ?"
            params.append(week)
        
        query += " ORDER BY w.week, u.name"
        
        with get_db_context() as conn:
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def create(self, user_id: int, week_id: int, team: str, player_name: str,
               odds: Optional[float] = None, theoretical_return: Optional[float] = None,
               game_id: Optional[str] = None) -> int:
        """Create a new pick and return the pick ID."""
        data = {
            'user_id': user_id,
            'week_id': week_id,
            'team': team,
            'player_name': player_name,
            'odds': odds,
            'theoretical_return': theoretical_return,
            'game_id': game_id
        }
        pick_id = self.insert(data)
        logger.info(f"Pick created: User {user_id}, Week {week_id}, {team} {player_name}")
        return pick_id
    
    def delete_by_id(self, pick_id: int) -> bool:
        """Delete a pick and invalidate related caches."""
        success = self.delete(pick_id)
        if success:
            logger.info(f"Pick deleted: ID {pick_id}")
            invalidate_on_pick_change()
        return success
    
    def count_for_user_week(self, user_id: int, week_id: int) -> int:
        """Count picks for a user in a specific week."""
        return self.count({'user_id': user_id, 'week_id': week_id})


# ============= RESULT REPOSITORY =============

class ResultRepository(BaseRepository):
    """Repository for pick result management operations."""
    
    table_name = 'results'
    
    def find_by_pick(self, pick_id: int) -> Optional[Result]:
        """Find the result for a specific pick."""
        results = self.find_where({'pick_id': pick_id})
        return dict(results[0]) if results else None
    
    def find_by_week(self, week_id: int) -> List[Result]:
        """Find all results for picks in a specific week."""
        query = """
            SELECT r.* FROM results r
            JOIN picks p ON r.pick_id = p.id
            WHERE p.week_id = ?
            ORDER BY p.created_at
        """
        with get_db_context() as conn:
            cursor = conn.execute(query, (week_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def find_by_user_week(self, user_id: int, week_id: int) -> List[Result]:
        """Find all results for picks by a user in a specific week."""
        query = """
            SELECT r.* FROM results r
            JOIN picks p ON r.pick_id = p.id
            WHERE p.user_id = ? AND p.week_id = ?
            ORDER BY p.created_at
        """
        with get_db_context() as conn:
            cursor = conn.execute(query, (user_id, week_id))
            return [dict(row) for row in cursor.fetchall()]
    
    def find_correct_picks(self, user_id: int, week_id: int) -> List[Result]:
        """Find correct picks for a user in a specific week."""
        query = """
            SELECT r.* FROM results r
            JOIN picks p ON r.pick_id = p.id
            WHERE p.user_id = ? AND p.week_id = ? AND r.is_correct = 1
            ORDER BY p.created_at
        """
        with get_db_context() as conn:
            cursor = conn.execute(query, (user_id, week_id))
            return [dict(row) for row in cursor.fetchall()]
    
    def find_any_time_tds(self, user_id: int, week_id: int) -> List[Result]:
        """Find any-time TD results for a user in a specific week."""
        query = """
            SELECT r.* FROM results r
            JOIN picks p ON r.pick_id = p.id
            WHERE p.user_id = ? AND p.week_id = ? AND r.any_time_td = 1
            ORDER BY p.created_at
        """
        with get_db_context() as conn:
            cursor = conn.execute(query, (user_id, week_id))
            return [dict(row) for row in cursor.fetchall()]
    
    def create(self, pick_id: int, is_correct: bool, actual_scorer: str,
               any_time_td: bool = False, actual_return: Optional[float] = None) -> int:
        """Create a new result and return the result ID."""
        data = {
            'pick_id': pick_id,
            'is_correct': 1 if is_correct else 0,
            'actual_scorer': actual_scorer,
            'any_time_td': 1 if any_time_td else 0,
            'actual_return': actual_return
        }
        result_id = self.insert(data)
        logger.info(f"Result created for pick {pick_id}: {actual_scorer} (correct={is_correct})")
        invalidate_on_result_change()
        invalidate_on_grading_complete()
        return result_id
    
    def count_correct_for_user_week(self, user_id: int, week_id: int) -> int:
        """Count correct picks for a user in a specific week."""
        query = """
            SELECT COUNT(*) FROM results r
            JOIN picks p ON r.pick_id = p.id
            WHERE p.user_id = ? AND p.week_id = ? AND r.is_correct = 1
        """
        with get_db_context() as conn:
            cursor = conn.execute(query, (user_id, week_id))
            return cursor.fetchone()[0]
    
    def count_any_time_tds_for_user_week(self, user_id: int, week_id: int) -> int:
        """Count any-time TDs for a user in a specific week."""
        query = """
            SELECT COUNT(*) FROM results r
            JOIN picks p ON r.pick_id = p.id
            WHERE p.user_id = ? AND p.week_id = ? AND r.any_time_td = 1
        """
        with get_db_context() as conn:
            cursor = conn.execute(query, (user_id, week_id))
            return cursor.fetchone()[0]


# ============= KICKOFF REPOSITORY =============

class KickoffRepository(BaseRepository):
    """Repository for kickoff decision management operations."""
    
    table_name = 'kickoff_decisions'
    
    def find_by_game(self, game_id: str) -> List[KickoffDecision]:
        """Find all kickoff decisions for a specific game."""
        results = self.find_where({'game_id': game_id})
        return [dict(row) for row in results]
    
    def find_by_team(self, team: str) -> List[KickoffDecision]:
        """Find all kickoff decisions made by a specific team."""
        results = self.find_where({'team': team}, order_by='created_at DESC')
        return [dict(row) for row in results]
    
    def find_by_game_and_team(self, game_id: str, team: str) -> Optional[KickoffDecision]:
        """Find the kickoff decision for a specific team in a specific game."""
        results = self.find_where({'game_id': game_id, 'team': team})
        return dict(results[0]) if results else None
    
    def create(self, game_id: str, team: str, decision: str, 
               result: Optional[str] = None) -> int:
        """Create a new kickoff decision record."""
        data = {
            'game_id': game_id,
            'team': team,
            'decision': decision,
            'result': result
        }
        return self.insert(data)
    
    def update_result(self, game_id: str, team: str, result: str) -> bool:
        """Update the result of a kickoff decision."""
        return self.update_where(
            {'game_id': game_id, 'team': team},
            {'result': result}
        ) > 0


# ============= MARKET ODDS REPOSITORY =============

class MarketOddsRepository(BaseRepository):
    """Repository for prediction market odds management operations."""
    
    table_name = 'market_odds'
    
    def find_for_game(self, game_id: str, source: Optional[str] = None) -> List[MarketOdds]:
        """Find market odds for a specific game."""
        if source:
            results = self.find_where({'game_id': game_id, 'source': source}, 
                                     order_by='timestamp DESC')
        else:
            query = f"SELECT * FROM {self.table_name} WHERE game_id = ? ORDER BY source, timestamp DESC"
            with get_db_context() as conn:
                cursor = conn.execute(query, (game_id,))
                results = cursor.fetchall()
        
        return [dict(row) for row in results]
    
    def find_for_player(self, player_name: str, season: int, 
                       week: Optional[int] = None) -> List[MarketOdds]:
        """Find market odds for a specific player."""
        if week:
            query = f"""
                SELECT * FROM {self.table_name}
                WHERE player_name = ? AND season = ? AND week = ?
                ORDER BY timestamp DESC
            """
            params = (player_name, season, week)
        else:
            query = f"""
                SELECT * FROM {self.table_name}
                WHERE player_name = ? AND season = ?
                ORDER BY week DESC, timestamp DESC
            """
            params = (player_name, season)
        
        with get_db_context() as conn:
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def find_for_week(self, season: int, week: int, 
                     source: Optional[str] = None) -> List[MarketOdds]:
        """Find market odds for a specific week."""
        if source:
            results = self.find_where(
                {'season': season, 'week': week, 'source': source},
                order_by='game_id, player_name, timestamp DESC'
            )
        else:
            query = f"""
                SELECT * FROM {self.table_name}
                WHERE season = ? AND week = ?
                ORDER BY source, game_id, player_name, timestamp DESC
            """
            with get_db_context() as conn:
                cursor = conn.execute(query, (season, week))
                results = cursor.fetchall()
        
        return [dict(row) for row in results]
    
    def find_latest_for_player_game(self, game_id: str, player_name: str, 
                                    source: str) -> Optional[MarketOdds]:
        """Find the latest odds for a player in a specific game from a source."""
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE game_id = ? AND player_name = ? AND source = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """
        with get_db_context() as conn:
            cursor = conn.execute(query, (game_id, player_name, source))
            result = cursor.fetchone()
            return dict(result) if result else None
    
    def create(self, game_id: str, player_name: str, source: str, odds: float,
               season: int, week: int, timestamp: datetime) -> int:
        """Create a new market odds record."""
        data = {
            'game_id': game_id,
            'player_name': player_name,
            'source': source,
            'odds': odds,
            'season': season,
            'week': week,
            'timestamp': timestamp
        }
        return self.insert(data)


# ============= SINGLETON INSTANCES =============
# Create singleton instances for easy access throughout the application

user_repo = UserRepository()
week_repo = WeekRepository()
pick_repo = PickRepository()
result_repo = ResultRepository()
kickoff_repo = KickoffRepository()
market_odds_repo = MarketOddsRepository()


__all__ = [
    'UserRepository',
    'WeekRepository',
    'PickRepository',
    'ResultRepository',
    'KickoffRepository',
    'MarketOddsRepository',
    'user_repo',
    'week_repo',
    'pick_repo',
    'result_repo',
    'kickoff_repo',
    'market_odds_repo',
]
