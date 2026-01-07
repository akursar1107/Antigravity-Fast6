"""
Utils Module Init
Exports main utility functions for easy importing.
"""

from utils.nfl_data import (
    load_data,
    get_game_schedule,
    get_touchdowns,
    get_first_tds,
    load_rosters,
    process_game_type
)

from utils.name_matching import (
    names_match,
    normalize_player_name,
    extract_last_name
)

from utils.grading_logic import (
    auto_grade_season
)

from utils.analytics import (
    get_team_first_td_counts,
    get_player_first_td_counts,
    get_position_first_td_counts
)

__all__ = [
    'load_data',
    'get_game_schedule',
    'get_touchdowns',
    'get_first_tds',
    'load_rosters',
    'process_game_type',
    'names_match',
    'normalize_player_name',
    'extract_last_name',
    'auto_grade_season'
]

__all__ += [
    'get_team_first_td_counts',
    'get_player_first_td_counts',
    'get_position_first_td_counts'
]
