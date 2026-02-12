"""
Integration Tests - Critical Workflows

Tests for end-to-end workflows in Fast6:
- CSV import pipeline (parsing -> validation -> database storage)
- Grading pipeline (load data -> fuzzy matching -> calculate returns -> save results)
- Batch operations (bulk insert/update)
- Cache invalidation on data changes
- Analytics computations

Run with: python -m pytest tests/test_workflows_integration.py -v
"""

import unittest
import tempfile
import sqlite3
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional
import logging
import unittest.mock

# Setup paths

import backend.config as config
from backend.utils.caching import clear_all_caches
from backend.database import (
    add_user, get_all_users, delete_user,
    add_pick, add_picks_batch, get_pick, get_user_week_picks,
    add_week, get_week_by_season_week,
    add_result, add_results_batch, get_leaderboard, get_user_stats,
    get_db_context
    # DB_PATH removed to avoid accidental usage
)
from backend.database.picks import dedupe_all_picks
from backend.utils.caching import invalidate_on_pick_change, get_cache_stats, CacheTTL
from backend.utils.error_handling import Fast6Error, DatabaseError

logger = logging.getLogger(__name__)


class BaseWorkflowTest(unittest.TestCase):
    """Base class for integration tests with isolated DB."""
    
    def setUp(self):
        """Set up isolated test database."""
        clear_all_caches()
        os.environ["FAST6_DISABLE_CACHING"] = "1"
        # Create temp DB file
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_path = self.temp_db.name
        self.temp_db.close()
        
        # Set database path to the temp file
        from backend.database.connection import set_db_path
        set_db_path(Path(self.db_path))
        
        # Initialize schema via migrations
        from backend.database.migrations import run_migrations
        run_migrations()
        
    def tearDown(self):
        """Clean up."""
        os.environ.pop("FAST6_DISABLE_CACHING", None)
        from backend.database.connection import set_db_path, DEFAULT_DB_PATH
        set_db_path(DEFAULT_DB_PATH)
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except:
                pass


class TestCSVImportWorkflow(BaseWorkflowTest):
    """Test CSV import pipeline: validation -> database storage."""
    
    def test_import_workflow_basic_picks(self):
        """Test basic CSV import workflow: user add -> week add -> pick add."""
        # Step 1: Add users
        user1_id = add_user("John Doe", "john@example.com")
        user2_id = add_user("Jane Smith", "jane@example.com")
        
        # Verify users exist
        users = get_all_users()
        self.assertEqual(len(users), 2)
        
        # Step 2: Add week
        week_id = add_week(2025, 1)
        self.assertIsNotNone(week_id)
        
        # Step 3: Add picks (simulating CSV import)
        picks_data = [
            {
                'user_id': user1_id,
                'week_id': week_id,
                'team': 'KC',
                'player_name': 'Patrick Mahomes',
                'odds': 150,
                'game_id': 'game_001'
            },
            {
                'user_id': user1_id,
                'week_id': week_id,
                'team': 'SF',
                'player_name': 'Jauan Jennings',
                'odds': 300,
                'game_id': 'game_002'
            },
            {
                'user_id': user2_id,
                'week_id': week_id,
                'team': 'KC',
                'player_name': 'Patrick Mahomes',
                'odds': 150,
                'game_id': 'game_001'
            }
        ]
        
        count = add_picks_batch(picks_data)
        self.assertEqual(count, 3)
        
        # Step 4: Verify picks were stored correctly
        user1_picks = get_user_week_picks(user1_id, week_id)
        self.assertEqual(len(user1_picks), 2)
        player_names = {p['player_name'] for p in user1_picks}
        self.assertIn('Patrick Mahomes', player_names)
        self.assertIn('Jauan Jennings', player_names)
        teams = {p['team'] for p in user1_picks}
        self.assertIn('KC', teams)
        self.assertIn('SF', teams)
        
        user2_picks = get_user_week_picks(user2_id, week_id)
        self.assertEqual(len(user2_picks), 1)
        self.assertEqual(user2_picks[0]['player_name'], 'Patrick Mahomes')
    
    def test_import_workflow_with_game_id_matching(self):
        """Test that game_id is properly stored and retrievable."""
        user_id = add_user("Test User", "test@example.com")
        week_id = add_week(2025, 1)
        
        pick_id = add_pick(
            user_id=user_id,
            week_id=week_id,
            team='KC',
            player_name='Patrick Mahomes',
            odds=150,
            game_id='gid_20250209_KC_SF'
        )
        
        pick = get_pick(pick_id)
        self.assertEqual(pick['game_id'], 'gid_20250209_KC_SF')
    
    def test_import_handles_duplicate_picks(self):
        """Test that duplicate picks are rejected by UNIQUE constraint (migration v11)."""
        user_id = add_user("Test User", "test@example.com")
        week_id = add_week(2025, 1)
        
        # Add first pick
        pick1 = add_pick(user_id, week_id, 'KC', 'Patrick Mahomes', 150, game_id='gid_1')
        self.assertIsNotNone(pick1)
        
        # Second identical pick should raise ValueError (UNIQUE constraint)
        with self.assertRaises(ValueError) as ctx:
            add_pick(user_id, week_id, 'KC', 'Patrick Mahomes', 150, game_id='gid_1')
        self.assertIn("already exists", str(ctx.exception))
        
        # Verify only one pick exists
        picks = get_user_week_picks(user_id, week_id)
        self.assertEqual(len(picks), 1)


class TestGradingWorkflow(BaseWorkflowTest):
    """Test grading pipeline: load data -> fuzzy matching -> save results."""
    
    def test_grading_workflow_add_results_batch(self):
        """Test batch result insertion (core of grading pipeline)."""
        # Setup: Create picks
        user_id = add_user("Test User", "test@example.com")
        week_id = add_week(2025, 1)
        pick1 = add_pick(user_id, week_id, 'KC', 'Patrick Mahomes', 150, game_id='gid_1')
        pick2 = add_pick(user_id, week_id, 'SF', 'Jauan Jennings', 300, game_id='gid_2')
        
        # Grade: Add results for picks
        results_data = [
            {
                'pick_id': pick1,
                'actual_scorer': 'Patrick Mahomes',
                'is_correct': True,
                'any_time_td': True,
                'actual_return': 1.50
            },
            {
                'pick_id': pick2,
                'actual_scorer': 'Jauan Jennings',
                'is_correct': False,
                'any_time_td': True,
                'actual_return': 1.00
            }
        ]
        
        result = add_results_batch(results_data)
        self.assertEqual(result['inserted'], 2)
        
        # Verify results
        picks = get_user_week_picks(user_id, week_id)
        self.assertEqual(len(picks), 2)
        # Both picks should now have results
        for pick in picks:
            self.assertIsNotNone(pick.get('is_correct'))
    
    def test_grading_workflow_partial_grading(self):
        """Test partial grading (some picks graded, others not)."""
        user_id = add_user("Test User", "test@example.com")
        week_id = add_week(2025, 1)
        pick1 = add_pick(user_id, week_id, 'KC', 'Mahomes', 150, game_id='gid_1')
        pick2 = add_pick(user_id, week_id, 'SF', 'Jennings', 300, game_id='gid_2')
        
        # Grade only first pick
        add_result(pick1, 'Patrick Mahomes', True, 1.50, True)
        
        # Verify grading state
        picks = get_user_week_picks(user_id, week_id)
        graded_count = sum(1 for p in picks if p.get('is_correct') is not None)
        self.assertEqual(graded_count, 1)
        
        # Now grade second pick
        add_result(pick2, 'Jauan Jennings', False, 0.00, False)
        
        # Verify both now graded
        picks = get_user_week_picks(user_id, week_id)
        graded_count = sum(1 for p in picks if p.get('is_correct') is not None)
        self.assertEqual(graded_count, 2)


class TestBatchOperations(BaseWorkflowTest):
    """Test batch operations for performance and correctness."""
    
    def test_batch_insert_picks_performance(self):
        """Test batch insert is efficient and correct."""
        user_id = add_user("Test User", "test@example.com")
        week_id = add_week(2025, 1)
        
        # Create large batch
        picks_data = [
            {
                'user_id': user_id,
                'week_id': week_id,
                'team': f'TEAM_{i}',
                'player_name': f'Player_{i}',
                'odds': 100 + i,
                'game_id': f'gid_{i}'
            }
            for i in range(100)
        ]
        
        count = add_picks_batch(picks_data)
        self.assertEqual(count, 100)
        
        # Verify all picks exist
        picks = get_user_week_picks(user_id, week_id)
        self.assertEqual(len(picks), 100)
    
    def test_batch_insert_results_performance(self):
        """Test batch result insertion."""
        user_id = add_user("Test User", "test@example.com")
        week_id = add_week(2025, 1)
        
        # Create picks
        picks_data = [
            {
                'user_id': user_id,
                'week_id': week_id,
                'team': f'TEAM_{i}',
                'player_name': f'Player_{i}',
                'odds': 100 + i,
                'game_id': f'gid_{i}'
            }
            for i in range(50)
        ]
        add_picks_batch(picks_data)
        picks = get_user_week_picks(user_id, week_id)
        pick_ids = [p['id'] for p in picks]
        
        # Create results for all picks
        results_data = [
            {
                'pick_id': pid,
                'actual_scorer': f'Player_{i}',
                'is_correct': i % 2 == 0,
                'any_time_td': True,
                'actual_return': 1.0 + (i * 0.1)
            }
            for i, pid in enumerate(pick_ids)
        ]
        
        result = add_results_batch(results_data)
        self.assertEqual(result['inserted'], 50)


class TestCacheInvalidation(BaseWorkflowTest):
    """Test cache invalidation on data changes."""
    
    def test_cache_invalidation_on_pick_change(self):
        """Test cache is invalidated when picks change."""
        user_id = add_user("Test User", "test@example.com")
        week_id = add_week(2025, 1)
        
        # Add pick and trigger cache invalidation
        add_pick(user_id, week_id, 'KC', 'Mahomes', 150)
        invalidate_on_pick_change()
        
        # Check cache stats
        stats = get_cache_stats("leaderboard")
        self.assertGreater(stats.clears, 0)
    
    def test_cache_ttl_configuration(self):
        """Test cache TTL values are configured correctly."""
        self.assertEqual(CacheTTL.LEADERBOARD, 300)  # 5 minutes
        self.assertEqual(CacheTTL.USER_STATS, 300)  # 5 minutes
        self.assertEqual(CacheTTL.WEEKLY_SUMMARY, 300)  # 5 minutes
        self.assertEqual(CacheTTL.NFL_PBP, 3600)  # 1 hour
        self.assertGreater(CacheTTL.ODDS_API, 0)  # Configured value


class TestErrorHandling(BaseWorkflowTest):
    """Test error handling in critical workflows."""
    
    def test_invalid_user_reference_caught(self):
        """Test error handling for invalid user IDs."""
        week_id = add_week(2025, 1)
        
        # Try to add pick for non-existent user
        try:
            add_pick(9999, week_id, 'KC', 'Mahomes', 150)
            # Should raise foreign key constraint error
            self.fail("Expected database error for invalid user_id")
        except Exception as e:
            # Expected - should be caught and logged
            self.assertIn('FOREIGN KEY', str(e).upper())
    
    def test_invalid_week_reference_caught(self):
        """Test error handling for invalid week IDs."""
        user_id = add_user("Test User", "test@example.com")
        
        # Try to add pick for non-existent week
        try:
            add_pick(user_id, 9999, 'KC', 'Mahomes', 150)
            self.fail("Expected database error for invalid week_id")
        except Exception as e:
            self.assertIn('FOREIGN KEY', str(e).upper())
    
    def test_duplicate_user_raises_error(self):
        """Test error handling for duplicate users."""
        add_user("John Doe", "john@example.com")
        
        # Try to add same user again
        with self.assertRaises(ValueError):
            add_user("John Doe", "john@example.com")


class TestLeaderboardComputation(BaseWorkflowTest):
    """Test leaderboard calculation with various data patterns."""
    
    def test_leaderboard_calculation_first_td_wins(self):
        """Test leaderboard correctly awards first TD wins."""
        # Setup users
        user1_id = add_user("Alice", "alice@example.com")
        user2_id = add_user("Bob", "bob@example.com")
        week_id = add_week(2025, 1)
        
        # Alice picks correct first TD (3 points)
        pick1 = add_pick(user1_id, week_id, 'KC', 'Mahomes', 150)
        add_result(pick1, 'Patrick Mahomes', True, 1.50, False)
        
        # Bob picks any time TD but not first (1 point)
        pick2 = add_pick(user2_id, week_id, 'KC', 'Mahomes', 300)
        add_result(pick2, 'Patrick Mahomes', False, 0.0, True)
        
        # Check leaderboard
        leaderboard = get_leaderboard(week_id)
        self.assertEqual(len(leaderboard), 2)
        # Alice should be first (3 points)
        # Note: Order depends on implementation, but sorting should be by points
        # Assuming get_leaderboard returns list sorted by points desc
        self.assertEqual(leaderboard[0]['name'], 'Alice')
        self.assertEqual(leaderboard[0]['points'], 3)
        self.assertEqual(leaderboard[1]['name'], 'Bob')
        self.assertEqual(leaderboard[1]['points'], 1)
    
    def test_leaderboard_empty_week(self):
        """Test leaderboard handles weeks with no results."""
        add_user("Alice", "alice@example.com")
        week_id = add_week(2025, 1)
    
        # No picks or results added - leaderboard shows all users with 0 points
        leaderboard = get_leaderboard(week_id)
        self.assertGreaterEqual(len(leaderboard), 1)
        alice = next((e for e in leaderboard if e['name'] == 'Alice'), None)
        self.assertIsNotNone(alice)
        self.assertEqual(alice['points'], 0)


class TestDataIntegrity(BaseWorkflowTest):
    """Test data integrity and constraints."""
    
    def test_cascade_delete_picks_on_user_delete(self):
        """Test that deleting user cascades to picks."""
        user_id = add_user("Test User", "test@example.com")
        week_id = add_week(2025, 1)
        add_pick(user_id, week_id, 'KC', 'Mahomes', 150)
        
        # Verify pick exists
        picks_before = get_user_week_picks(user_id, week_id)
        self.assertEqual(len(picks_before), 1)
        
        # Delete user
        delete_user(user_id)
        
        # Verify picks are deleted
        picks_after = get_user_week_picks(user_id, week_id)
        self.assertEqual(len(picks_after), 0)
    
    def test_cascade_delete_results_on_pick_delete(self):
        """Test that deleting pick cascades to results."""
        user_id = add_user("Test User", "test@example.com")
        week_id = add_week(2025, 1)
        pick_id = add_pick(user_id, week_id, 'KC', 'Mahomes', 150)
        
        # Add result
        add_result(pick_id, 'Patrick Mahomes', True, 1.50, True)
        
        # Delete pick
        from backend.database.picks import delete_pick
        delete_pick(pick_id)
        
        # Verify result is deleted
        from backend.database.stats import get_result_for_pick
        result = get_result_for_pick(pick_id)
        self.assertIsNone(result)


if __name__ == '__main__':
    # Setup logging
    logging.basicConfig(level=logging.DEBUG)
    
    # Run tests
    unittest.main(verbosity=2)
