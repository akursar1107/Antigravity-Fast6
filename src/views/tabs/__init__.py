"""
Public Dashboard Tabs Module
Subpackage for individual tab views in the public dashboard.
"""

from .leaderboard import show_leaderboard_tab
from .schedule import show_schedule_tab
from .week_picks import show_week_picks_tab
from .team_analysis import show_team_analysis_tab
from .player_performance import show_player_performance_tab
from .roi_trends import show_roi_trends_tab
from .power_rankings import show_power_rankings_tab
from .defense_matchups import show_defense_matchups_tab
from .market_comparison import show_market_comparison_tab

# Archived tabs (moved to archive/ folder - no longer used):
# - game_analysis.py (placeholder with no content)
# - league_analysis.py (redundant with team_analysis)
# - analysis.py (never used in dashboard)
# - touchdown_explorer.py (never used in dashboard)
# - trends_explorer.py (never used in dashboard)
# - opening_drive_analysis.py (never used in dashboard)

__all__ = [
    'show_leaderboard_tab',
    'show_schedule_tab',
    'show_week_picks_tab',
    'show_team_analysis_tab',
    'show_player_performance_tab',
    'show_roi_trends_tab',
    'show_power_rankings_tab',
    'show_defense_matchups_tab',
    'show_market_comparison_tab',
]
