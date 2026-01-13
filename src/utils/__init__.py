"""
Utils Module Init
Exports main utility functions for easy importing.
"""

try:
    from utils.nfl_data import (
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
    from utils.name_matching import (
        names_match,
        normalize_player_name,
        extract_last_name
    )
except ImportError:
    pass

try:
    from utils.grading_logic import (
        auto_grade_season,
        grade_any_time_td_only
    )
except ImportError:
    pass

try:
    from utils.analytics import (
        get_team_first_td_counts,
        get_player_first_td_counts,
        get_position_first_td_counts
    )
except ImportError:
    pass

# Database operations - These should always work
from utils.db_connection import (
    get_db_connection,
    init_db,
    ensure_game_id_column,
    ensure_any_time_td_column,
    DB_PATH
)

from utils.db_users import (
    add_user,
    get_user,
    get_user_by_name,
    get_all_users,
    delete_user
)

from utils.db_weeks import (
    add_week,
    get_week,
    get_week_by_season_week,
    get_all_weeks
)

from utils.db_picks import (
    add_pick,
    get_pick,
    get_user_week_picks,
    get_week_all_picks,
    get_user_all_picks,
    delete_pick,
    get_ungraded_picks,
    dedupe_picks_for_user_week,
    create_unique_picks_index,
    dedupe_all_picks,
    backfill_theoretical_return_from_odds
)

from utils.db_stats import (
    add_result,
    get_result,
    get_result_for_pick,
    delete_season_data,
    clear_grading_results,
    get_leaderboard,
    get_user_stats,
    get_weekly_summary
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
    # Database - Results & Stats
    'add_result',
    'get_result',
    'get_result_for_pick',
    'delete_season_data',
    'clear_grading_results',
    'get_leaderboard',
    'get_user_stats',
    'get_weekly_summary',
]
