"""
Public Dashboard Tabs Module
Subpackage for individual tab views in the public dashboard.
"""

from .first_td import show_first_td_tab
from .leaderboard import show_leaderboard_tab
from .all_touchdowns import show_all_touchdowns_tab
from .schedule import show_schedule_tab
from .analysis import show_analysis_tab
from .week_picks import show_week_picks_tab

__all__ = [
    'show_first_td_tab',
    'show_leaderboard_tab',
    'show_all_touchdowns_tab',
    'show_schedule_tab',
    'show_analysis_tab',
    'show_week_picks_tab',
]
