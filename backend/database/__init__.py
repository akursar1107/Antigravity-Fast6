"""
Database Package
Centralized database access layer for Fast6.

All database operations are organized here:
- connection.py: Database connection management
- migrations.py: Schema versioning and migrations
- base_repository.py: Base class for repository pattern
- users.py: User CRUD operations
- picks.py: Pick CRUD operations
- stats.py: Results and statistics
- weeks.py: Week/Season management
- kickoff.py: Kickoff-specific operations
"""

# Connection management
from .connection import (
    get_db_connection,
    get_db_context,
    get_db_path,
    set_db_path,
    init_db,
    ensure_game_id_column,
    ensure_any_time_td_column,
    DB_PATH,
)

# Base Repository Pattern
from .base_repository import BaseRepository

# Specialized Repositories
from .repositories import (
    UserRepository,
    WeekRepository,
    PickRepository,
    ResultRepository,
    KickoffRepository,
    MarketOddsRepository,
    user_repo,
    week_repo,
    pick_repo,
    result_repo,
    kickoff_repo,
    market_odds_repo,
)

# Migrations
from .migrations import (
    run_migrations,
    get_current_version,
    get_migration_history
)

# Users
from .users import (
    add_user,
    get_user,
    get_user_by_name,
    get_all_users,
    delete_user
)

# Picks
from .picks import (
    add_pick,
    add_picks_batch,
    get_pick,
    get_user_week_picks,
    get_week_all_picks,
    get_user_all_picks,
    get_all_picks,
    delete_pick,
    update_pick,
    get_ungraded_picks,
    dedupe_picks_for_user_week,
    create_unique_picks_index,
    dedupe_all_picks,
    backfill_theoretical_return_from_odds,
    update_pick_player_name,
    get_graded_picks
)

# Stats and Results
from .stats import (
    add_result,
    add_results_batch,
    get_result,
    get_result_for_pick,
    delete_season_data,
    clear_grading_results,
    get_leaderboard,
    get_user_stats,
    get_weekly_summary,
    get_user_picks_with_results,
    clear_leaderboard_cache
)

# Weeks
from .weeks import (
    add_week,
    get_week,
    get_week_by_season_week,
    get_all_weeks
)

__all__ = [
    # Connection
    'get_db_connection',
    'get_db_context',
    'init_db',
    'ensure_game_id_column',
    'ensure_any_time_td_column',
    'DB_PATH',
    # Base Repository
    'BaseRepository',
    # Specialized Repositories
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
    # Migrations
    'run_migrations',
    'get_current_version',
    'get_migration_history',
    # Users
    'add_user',
    'get_user',
    'get_user_by_name',
    'get_all_users',
    'delete_user',
    # Picks
    'add_pick',
    'add_picks_batch',
    'get_pick',
    'get_user_week_picks',
    'get_week_all_picks',
    'get_user_all_picks',
    'get_all_picks',
    'delete_pick',
    'update_pick',
    'get_ungraded_picks',
    'dedupe_picks_for_user_week',
    'create_unique_picks_index',
    'dedupe_all_picks',
    'backfill_theoretical_return_from_odds',
    'update_pick_player_name',
    'get_graded_picks',
    # Stats
    'add_result',
    'add_results_batch',
    'get_result',
    'get_result_for_pick',
    'delete_season_data',
    'clear_grading_results',
    'get_leaderboard',
    'get_user_stats',
    'get_weekly_summary',
    'get_user_picks_with_results',
    'clear_leaderboard_cache',
    # Weeks
    'add_week',
    'get_week',
    'get_week_by_season_week',
    'get_all_weeks',
]
