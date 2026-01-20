"""
Test suite for repository pattern implementation.

Tests CRUD operations for all repositories.
"""

import sqlite3
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from utils.db_connection import get_db_context, get_db_connection
from repositories import UsersRepository, WeeksRepository, PicksRepository, ResultsRepository


def test_users_repository():
    """Test UsersRepository CRUD operations."""
    print("\n=== Testing UsersRepository ===")
    
    with get_db_context() as conn:
        repo = UsersRepository(conn)
        
        # Test add
        print("✓ Adding test user...")
        user_id = repo.add("Test User Repo", "test@repo.com", is_admin=False)
        print(f"  User ID: {user_id}")
        
        # Test get_by_id
        print("✓ Getting user by ID...")
        user = repo.get_by_id(user_id)
        print(f"  User: {user['name']}, Email: {user['email']}")
        
        # Test get_by_name
        print("✓ Getting user by name...")
        user = repo.get_by_name("Test User Repo")
        assert user is not None
        print(f"  Found: {user['name']}")
        
        # Test count
        print("✓ Counting users...")
        count = repo.count()
        print(f"  Total users: {count}")
        
        # Test update
        print("✓ Updating user...")
        success = repo.update(user_id, email="updated@repo.com", is_admin=True)
        assert success
        user = repo.get_by_id(user_id)
        print(f"  Updated email: {user['email']}, Admin: {user['is_admin']}")
        
        # Test delete
        print("✓ Deleting test user...")
        success = repo.delete(user_id)
        assert success
        user = repo.get_by_id(user_id)
        assert user is None
        print("  User deleted successfully")


def test_weeks_repository():
    """Test WeeksRepository CRUD operations."""
    print("\n=== Testing WeeksRepository ===")
    
    with get_db_context() as conn:
        repo = WeeksRepository(conn)
        
        # Test add
        print("✓ Adding test week...")
        week_id = repo.add(2099, 99)
        print(f"  Week ID: {week_id}")
        
        # Test get_by_season_week
        print("✓ Getting week by season/week...")
        week = repo.get_by_season_week(2099, 99)
        assert week is not None
        print(f"  Found: Season {week['season']}, Week {week['week']}")
        
        # Test exists
        print("✓ Checking if week exists...")
        exists = repo.exists(2099, 99)
        assert exists
        print(f"  Exists: {exists}")
        
        # Test get_seasons
        print("✓ Getting all seasons...")
        seasons = repo.get_seasons()
        print(f"  Seasons: {seasons[:3]}...")  # Show first 3
        
        # Clean up
        print("✓ Cleaning up...")
        conn.execute("DELETE FROM weeks WHERE season = 2099")


def test_picks_repository():
    """Test PicksRepository CRUD operations."""
    print("\n=== Testing PicksRepository ===")
    
    with get_db_context() as conn:
        users_repo = UsersRepository(conn)
        weeks_repo = WeeksRepository(conn)
        picks_repo = PicksRepository(conn)
        
        # Create test user and week
        print("✓ Setting up test data...")
        user_id = users_repo.add("Pick Test User", "picktest@repo.com")
        week_id = weeks_repo.add(2099, 99)
        
        # Test add
        print("✓ Adding test pick...")
        pick_id = picks_repo.add(
            user_id=user_id,
            week_id=week_id,
            team="KC",
            player_name="Patrick Mahomes",
            odds=5.0,
            theoretical_return=15.0,
            game_id="2099_99_KC_BUF"
        )
        print(f"  Pick ID: {pick_id}")
        
        # Test get_user_week_picks
        print("✓ Getting user week picks...")
        picks = picks_repo.get_user_week_picks(user_id, week_id)
        assert len(picks) == 1
        print(f"  Found {len(picks)} pick(s)")
        
        # Test get_by_game_id
        print("✓ Getting picks by game ID...")
        game_picks = picks_repo.get_by_game_id("2099_99_KC_BUF")
        assert len(game_picks) == 1
        print(f"  Found {len(game_picks)} pick(s) for game")
        
        # Test count
        print("✓ Counting picks...")
        count = picks_repo.count(user_id=user_id)
        print(f"  User has {count} pick(s)")
        
        # Clean up
        print("✓ Cleaning up...")
        picks_repo.delete(pick_id)
        users_repo.delete(user_id)
        conn.execute("DELETE FROM weeks WHERE season = 2099")


def test_results_repository():
    """Test ResultsRepository CRUD operations."""
    print("\n=== Testing ResultsRepository ===")
    
    with get_db_context() as conn:
        users_repo = UsersRepository(conn)
        weeks_repo = WeeksRepository(conn)
        picks_repo = PicksRepository(conn)
        results_repo = ResultsRepository(conn)
        
        # Create test data
        print("✓ Setting up test data...")
        user_id = users_repo.add("Result Test User", "resulttest@repo.com")
        week_id = weeks_repo.add(2099, 99)
        pick_id = picks_repo.add(
            user_id=user_id,
            week_id=week_id,
            team="KC",
            player_name="Patrick Mahomes",
            game_id="2099_99_KC_BUF"
        )
        
        # Test add
        print("✓ Adding test result...")
        result_id = results_repo.add(
            pick_id=pick_id,
            actual_scorer="Patrick Mahomes",
            is_correct=True,
            actual_return=15.0
        )
        print(f"  Result ID: {result_id}")
        
        # Test get_by_pick_id
        print("✓ Getting result by pick ID...")
        result = results_repo.get_by_pick_id(pick_id)
        assert result is not None
        print(f"  Correct: {result['is_correct']}, Scorer: {result['actual_scorer']}")
        
        # Test get_user_stats
        print("✓ Getting user stats...")
        stats = results_repo.get_user_stats(user_id)
        print(f"  Total: {stats['total_picks']}, Correct: {stats['correct_picks']}, "
              f"Accuracy: {stats['accuracy']}%")
        
        # Test count
        print("✓ Counting results...")
        total = results_repo.count()
        correct = results_repo.count(is_correct=True)
        print(f"  Total: {total}, Correct: {correct}")
        
        # Clean up
        print("✓ Cleaning up...")
        results_repo.delete(result_id)
        picks_repo.delete(pick_id)
        users_repo.delete(user_id)
        conn.execute("DELETE FROM weeks WHERE season = 2099")


def main():
    """Run all repository tests."""
    print("Starting Repository Pattern Tests...")
    print("=" * 50)
    
    try:
        test_users_repository()
        test_weeks_repository()
        test_picks_repository()
        test_results_repository()
        
        print("\n" + "=" * 50)
        print("✅ All repository tests passed!")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
