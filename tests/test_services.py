"""
Test suite for service layer - business logic separation.

Tests that services properly orchestrate business logic using repositories.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from utils.db_connection import get_db_context
from repositories import UsersRepository, WeeksRepository, PicksRepository, ResultsRepository
from services import GradingService


def test_grading_service():
    """Test GradingService business logic."""
    print("\n=== Testing GradingService ===")
    
    with get_db_context() as conn:
        # Create repositories
        users_repo = UsersRepository(conn)
        weeks_repo = WeeksRepository(conn)
        picks_repo = PicksRepository(conn)
        results_repo = ResultsRepository(conn)
        
        # Create service
        grading_service = GradingService(picks_repo, results_repo)
        
        # Test pick validation
        print("✓ Testing pick validation...")
        validation = grading_service.validate_pick(
            player_name="Patrick Mahomes",
            team="KC",
            game_id="2025_01_KC_PHI"
        )
        print(f"  Valid: {validation['valid']}")
        print(f"  Warnings: {validation['warnings']}")
        print(f"  Normalized team: {validation['normalized_team']}")
        assert validation['valid'] is True
        assert validation['normalized_team'] == 'KC'
        
        # Test invalid pick validation
        print("✓ Testing invalid pick validation...")
        validation = grading_service.validate_pick(
            player_name="PM",  # Too short
            team="INVALID",
            game_id="bad"
        )
        print(f"  Valid: {validation['valid']}")
        print(f"  Warnings: {validation['warnings']}")
        assert validation['valid'] is False
        assert len(validation['warnings']) > 0
        
        # Test get_user_accuracy
        print("✓ Testing user accuracy calculation...")
        # Create test user with pick and result
        user_id = users_repo.add("Accuracy Test User", "accuracy@test.com")
        week_id = weeks_repo.add(2025, 1)
        pick_id = picks_repo.add(
            user_id=user_id,
            week_id=week_id,
            team="KC",
            player_name="Test Player",
            game_id="2025_01_KC_PHI"
        )
        results_repo.add(
            pick_id=pick_id,
            is_correct=True,
            actual_return=15.0
        )
        
        accuracy = grading_service.get_user_accuracy(user_id, season=2025)
        print(f"  Total picks: {accuracy['total_picks']}")
        print(f"  Correct: {accuracy['correct_picks']}")
        print(f"  Accuracy: {accuracy['accuracy']}%")
        assert accuracy['total_picks'] == 1
        assert accuracy['correct_picks'] == 1
        assert accuracy['accuracy'] == 100.0
        
        # Clean up
        print("✓ Cleaning up...")
        results_repo.delete_by_pick_id(pick_id)
        picks_repo.delete(pick_id)
        users_repo.delete(user_id)
        conn.execute("DELETE FROM weeks WHERE season = 2025 AND week = 1")
        
        print("✓ GradingService tests passed!")


def test_service_separation():
    """Test that service properly separates business logic from data access."""
    print("\n=== Testing Service Layer Separation ===")
    
    with get_db_context() as conn:
        picks_repo = PicksRepository(conn)
        results_repo = ResultsRepository(conn)
        grading_service = GradingService(picks_repo, results_repo)
        
        # Verify service doesn't directly access database
        print("✓ Service uses repositories (not direct DB access)...")
        assert hasattr(grading_service, 'picks_repo')
        assert hasattr(grading_service, 'results_repo')
        assert not hasattr(grading_service, 'conn')
        assert not hasattr(grading_service, 'cursor')
        print("  ✓ Service properly encapsulates business logic")
        
        # Verify business logic methods exist
        print("✓ Checking business logic methods...")
        assert hasattr(grading_service, 'grade_pick')
        assert hasattr(grading_service, 'grade_season')
        assert hasattr(grading_service, 'regrade_pick')
        assert hasattr(grading_service, 'get_user_accuracy')
        assert hasattr(grading_service, 'validate_pick')
        print("  ✓ All business logic methods present")
        
        print("✓ Service layer properly separated!")


def main():
    """Run all service tests."""
    print("Starting Service Layer Tests...")
    print("=" * 50)
    
    try:
        test_grading_service()
        test_service_separation()
        
        print("\n" + "=" * 50)
        print("✅ All service layer tests passed!")
        print("=" * 50)
        print("\nBenefits of Service Layer:")
        print("  • Business logic separated from data access")
        print("  • Pure functions testable without database")
        print("  • Repositories handle all database operations")
        print("  • Easy to mock services for testing views")
        print("  • Clear separation of concerns")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
