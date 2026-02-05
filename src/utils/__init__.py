"""
Utils Module Init
Exports main utility functions for easy importing.
"""

try:
    from src.utils.nfl_data import (
        load_data,
        get_game_schedule,
        get_touchdowns,
        get_first_tds,
        load_rosters,
        process_game_type
    )
except ImportError:
    pass

try:
    from src.utils.name_matching import (
        names_match,
        normalize_player_name,
        extract_last_name
    )
except ImportError:
    pass

try:
    from src.utils.grading_logic import (
        auto_grade_season,
        grade_any_time_td_only
    )
except ImportError:
    pass

try:
    from src.utils.analytics import (
        get_team_first_td_counts,
        get_player_first_td_counts,
        get_position_first_td_counts
    )
except ImportError:
    pass

# Database operations - Now in database package
# Note: These imports are delayed to avoid circular imports with database modules
try:
    from database import (
        # Connection
        get_db_connection,
        get_db_context,
        init_db,
        DB_PATH,
        # Migrations
        run_migrations,
        get_current_version,
        get_migration_history,
        # Users
        add_user,
        get_user,
        get_user_by_name,
        get_all_users,
        delete_user,
        # Weeks
        add_week,
        get_week,
        get_week_by_season_week,
        get_all_weeks,
        # Picks
        add_pick,
        add_picks_batch,
        get_pick,
        get_user_week_picks,
        get_week_all_picks,
        get_user_all_picks,
        delete_pick,
        get_ungraded_picks,
        dedupe_picks_for_user_week,
        create_unique_picks_index,
        dedupe_all_picks,
        backfill_theoretical_return_from_odds,
        update_pick_player_name,
        get_graded_picks,
        # Stats
        add_result,
        add_results_batch,
        get_result,
        get_result_for_pick,
        delete_season_data,
        clear_grading_results,
        get_leaderboard,
        get_user_stats,
        get_weekly_summary,
        get_user_picks_with_results
    )
except ImportError:
    # Will be available after database package is fully initialized
    pass

# Type utilities
from src.utils.type_utils import (
    safe_int,
    safe_str,
    safe_float,
    safe_bool
)

__all__ = [
    # NFL Data
    'load_data',
    'get_game_schedule',
    'get_touchdowns',
    'get_first_tds',
    'load_rosters',
    'process_game_type',
    # Name Matching
    'names_match',
    'normalize_player_name',
    'extract_last_name',
    # Grading
    'auto_grade_season',
    'grade_any_time_td_only',
    # Analytics
    'get_team_first_td_counts',
    'get_player_first_td_counts',
    'get_position_first_td_counts',
    # Database - Connection
    'get_db_connection',
    'init_db',
    'ensure_game_id_column',
    'ensure_any_time_td_column',
    'DB_PATH',
    # Database - Users
    'add_user',
    'get_user',
    'get_user_by_name',
    'get_all_users',
    'delete_user',
    # Database - Weeks
    'add_week',
    'get_week',
    'get_week_by_season_week',
    'get_all_weeks',
    # Database - Picks
    'add_pick',
    'add_picks_batch',
    'get_pick',
    'get_user_week_picks',
    'get_week_all_picks',
    'get_user_all_picks',
    'delete_pick',
    'get_ungraded_picks',
    'dedupe_picks_for_user_week',
    'create_unique_picks_index',
    'dedupe_all_picks',
    'backfill_theoretical_return_from_odds',
    'update_pick_player_name',
    'get_graded_picks',
    # Database - Results & Stats
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
    # Type utilities
    'safe_int',
    'safe_str',
    'safe_float',
    'safe_bool',
]
