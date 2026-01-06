"""Quick test of database functionality"""

from src.database import *

# Clean up any existing test data
import os
from pathlib import Path
db_file = Path(__file__).parent / "data" / "fast6.db"
if db_file.exists():
    db_file.unlink()

# Initialize fresh database
init_db()

# Test adding users
user1_id = add_user('John', 'john@example.com', is_admin=True)
user2_id = add_user('Mike', 'mike@example.com')
user3_id = add_user('Sarah', 'sarah@example.com')

# Test adding week
week_id = add_week(2025, 1)

# Test adding picks
pick1 = add_pick(user1_id, week_id, 'KC', 'Travis Kelce', odds=120.0, theoretical_return=120.0)
pick2 = add_pick(user2_id, week_id, 'BUF', 'Stefon Diggs', odds=100.0, theoretical_return=100.0)
pick3 = add_pick(user3_id, week_id, 'KC', 'Patrick Mahomes', odds=150.0, theoretical_return=150.0)

# Test adding results
add_result(pick1, 'Travis Kelce', True, 120.0)
add_result(pick2, 'Stefon Diggs', True, 100.0)
add_result(pick3, 'Patrick Mahomes', False, 0.0)

# Test leaderboard
leaderboard = get_leaderboard(week_id)

print('\n✅ DATABASE TEST SUCCESSFUL')
print(f'Users: {len(get_all_users())}')
print(f'Weeks: {len(get_all_weeks())}')
print(f'Picks for week {week_id}: {len(get_week_all_picks(week_id))}')
print('\nLeaderboard (Week 1, Season 2025):')
for user in leaderboard:
    print(f"  {user['name']}: {user['wins']} wins, ${user['total_return']}")

# Test getting individual stats
print('\nUser Stats:')
john_stats = get_user_stats(user1_id)
print(f"  John: {john_stats['wins']} wins, ${john_stats['total_return']}")
