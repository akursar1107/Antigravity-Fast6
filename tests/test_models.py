"""
Test suite for data models - type safety and dataclass functionality.

Tests that models provide clean typed interfaces and conversion methods.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from models import User, Week, Pick, Result


def test_user_model():
    """Test User model functionality."""
    print("\n=== Testing User Model ===")
    
    # Test creation
    print("✓ Creating User...")
    user = User(
        id=1,
        name="Test User",
        email="test@example.com",
        is_admin=True
    )
    print(f"  User: {user}")
    assert user.name == "Test User"
    assert user.is_admin is True
    
    # Test from_dict
    print("✓ Testing from_dict...")
    data = {
        'id': 2,
        'name': "Dict User",
        'email': "dict@example.com",
        'is_admin': 0
    }
    user2 = User.from_dict(data)
    print(f"  User from dict: {user2}")
    assert user2.name == "Dict User"
    assert user2.is_admin is False
    
    # Test to_dict
    print("✓ Testing to_dict...")
    user_dict = user.to_dict()
    print(f"  Dict keys: {list(user_dict.keys())}")
    assert 'id' in user_dict
    assert 'name' in user_dict
    assert user_dict['is_admin'] is True
    
    # Test __str__ and __repr__
    print("✓ Testing string representations...")
    print(f"  str: {str(user)}")
    print(f"  repr: {repr(user)}")
    assert "Admin" in str(user)
    assert "User(id=" in repr(user)
    
    print("✓ User model tests passed!")


def test_week_model():
    """Test Week model functionality."""
    print("\n=== Testing Week Model ===")
    
    # Test regular season week
    print("✓ Creating regular season Week...")
    week = Week(id=1, season=2025, week=1)
    print(f"  Week: {week}")
    assert week.season == 2025
    assert week.week == 1
    assert week.is_playoff is False
    assert week.display_name == "Week 1"
    
    # Test playoff week
    print("✓ Creating playoff Week...")
    playoff = Week(id=2, season=2025, week=19)
    print(f"  Playoff week: {playoff}")
    assert playoff.is_playoff is True
    assert playoff.display_name == "Wild Card"
    
    # Test Super Bowl
    print("✓ Creating Super Bowl Week...")
    sb = Week(id=3, season=2025, week=22)
    assert sb.display_name == "Super Bowl"
    print(f"  Super Bowl: {sb}")
    
    # Test from_dict
    print("✓ Testing from_dict...")
    data = {'id': 4, 'season': 2025, 'week': 10}
    week2 = Week.from_dict(data)
    assert week2.week == 10
    print(f"  Week from dict: {week2}")
    
    # Test to_dict
    print("✓ Testing to_dict...")
    week_dict = week.to_dict()
    assert 'season' in week_dict
    assert 'week' in week_dict
    print(f"  Dict keys: {list(week_dict.keys())}")
    
    print("✓ Week model tests passed!")


def test_pick_model():
    """Test Pick model functionality."""
    print("\n=== Testing Pick Model ===")
    
    # Test creation
    print("✓ Creating Pick...")
    pick = Pick(
        id=1,
        user_id=1,
        week_id=1,
        team="KC",
        player_name="Patrick Mahomes",
        odds=500.0,
        theoretical_return=15.0,
        game_id="2025_01_KC_PHI"
    )
    print(f"  Pick: {pick}")
    assert pick.player_name == "Patrick Mahomes"
    assert pick.team == "KC"
    assert pick.has_odds is True
    assert pick.display_name == "KC Patrick Mahomes"
    
    # Test pick without odds
    print("✓ Testing pick without odds...")
    pick_no_odds = Pick(
        id=2,
        user_id=1,
        week_id=1,
        team="PHI",
        player_name="Jalen Hurts"
    )
    assert pick_no_odds.has_odds is False
    print(f"  Pick without odds: {pick_no_odds}")
    
    # Test from_dict with joined fields
    print("✓ Testing from_dict with joined data...")
    data = {
        'id': 3,
        'user_id': 1,
        'week_id': 1,
        'team': 'BUF',
        'player_name': 'Josh Allen',
        'game_id': '2025_01_BUF_MIA',
        'user_name': 'Test User',
        'season': 2025,
        'week': 1
    }
    pick2 = Pick.from_dict(data)
    assert pick2.user_name == "Test User"
    assert pick2.season == 2025
    print(f"  Pick with joins: {pick2}")
    
    # Test to_dict
    print("✓ Testing to_dict...")
    pick_dict = pick.to_dict()
    assert 'player_name' in pick_dict
    assert 'team' in pick_dict
    print(f"  Dict keys: {list(pick_dict.keys())}")
    
    print("✓ Pick model tests passed!")


def test_result_model():
    """Test Result model functionality."""
    print("\n=== Testing Result Model ===")
    
    # Test correct result
    print("✓ Creating correct Result...")
    result = Result(
        id=1,
        pick_id=1,
        actual_scorer="Patrick Mahomes",
        is_correct=True,
        actual_return=15.0
    )
    print(f"  Result: {result}")
    assert result.is_correct is True
    assert result.is_graded is True
    assert result.status_text == "Correct"
    assert result.status_emoji == "✅"
    
    # Test incorrect result
    print("✓ Creating incorrect Result...")
    incorrect = Result(
        id=2,
        pick_id=2,
        actual_scorer="Someone Else",
        is_correct=False,
        actual_return=0.0
    )
    print(f"  Incorrect: {incorrect}")
    assert incorrect.status_text == "Incorrect"
    assert incorrect.status_emoji == "❌"
    
    # Test pending result
    print("✓ Creating pending Result...")
    pending = Result(
        id=3,
        pick_id=3,
        is_correct=None
    )
    print(f"  Pending: {pending}")
    assert pending.is_graded is False
    assert pending.status_text == "Pending"
    assert pending.status_emoji == "⏳"
    
    # Test from_dict
    print("✓ Testing from_dict...")
    data = {
        'id': 4,
        'pick_id': 4,
        'actual_scorer': 'Travis Kelce',
        'is_correct': 1,
        'actual_return': 20.0
    }
    result2 = Result.from_dict(data)
    assert result2.is_correct is True
    print(f"  Result from dict: {result2}")
    
    # Test to_dict
    print("✓ Testing to_dict...")
    result_dict = result.to_dict()
    assert 'is_correct' in result_dict
    assert 'actual_scorer' in result_dict
    print(f"  Dict keys: {list(result_dict.keys())}")
    
    print("✓ Result model tests passed!")


def test_type_safety():
    """Test that models provide type safety benefits."""
    print("\n=== Testing Type Safety ===")
    
    # Type hints should be accessible
    print("✓ Checking type annotations...")
    assert hasattr(User, '__annotations__')
    assert hasattr(Week, '__annotations__')
    assert hasattr(Pick, '__annotations__')
    assert hasattr(Result, '__annotations__')
    print("  ✓ All models have type annotations")
    
    # Test dataclass features
    print("✓ Testing dataclass features...")
    user1 = User(id=1, name="User1")
    user2 = User(id=1, name="User1")
    user3 = User(id=2, name="User2")
    assert user1 == user2  # Dataclasses auto-generate __eq__
    assert user1 != user3
    print("  ✓ Equality comparison works")
    
    # Test property access (IDE autocomplete friendly)
    print("✓ Testing property access...")
    pick = Pick(id=1, user_id=1, week_id=1, team="KC", player_name="Test")
    assert hasattr(pick, 'display_name')
    assert hasattr(pick, 'has_odds')
    print("  ✓ Properties accessible")
    
    print("✓ Type safety tests passed!")


def main():
    """Run all model tests."""
    print("Starting Data Model Tests...")
    print("=" * 50)
    
    try:
        test_user_model()
        test_week_model()
        test_pick_model()
        test_result_model()
        test_type_safety()
        
        print("\n" + "=" * 50)
        print("✅ All data model tests passed!")
        print("=" * 50)
        print("\nBenefits of Type-Safe Models:")
        print("  • IDE autocomplete for all attributes")
        print("  • Type checking catches errors early")
        print("  • Self-documenting code with clear types")
        print("  • Easy conversion between dict and objects")
        print("  • Automatic equality comparison")
        print("  • Properties for computed values")
        print("  • Clean string representations")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
