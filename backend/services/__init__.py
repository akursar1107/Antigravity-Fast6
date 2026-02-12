"""
Services Package
Business logic layer for Fast6 application.

Core Services:
- performance_service.py: User performance metrics and calculations

Analytics Services (Phase 5):
- analytics/player_stats.py: Player performance tracking
- analytics/roi_trends.py: ROI and profitability analysis
- analytics/elo_ratings.py: Team power rankings
- analytics/defense_analysis.py: Defensive matchup analysis
"""

# Core services
from .performance_service import PickerPerformanceService

# Analytics services (Phase 5) - re-export everything
from .analytics import *

__all__ = [
    # Core services
    'PickerPerformanceService',
    # Analytics exports (from backend.analytics package)
    # Player Stats
    'update_player_stats',
    'get_player_form',
    'get_hot_players',
    'get_player_stats_detail',
    'get_position_leaders',
    'get_team_top_scorers',
    'get_player_comparison',
    'get_form_badge_emoji',
    'get_player_summary_text',
    # ROI Trends
    'get_user_roi_trend',
    'get_weekly_roi_all_users',
    'get_best_worst_picks',
    'get_roi_by_position',
    'get_roi_by_odds_range',
    'get_pick_difficulty_analysis',
    'get_profitability_summary',
    'get_user_rank_by_roi',
    # ELO Ratings
    'initialize_team_ratings',
    'update_team_ratings',
    'get_power_rankings',
    'get_team_rating_history',
    'get_matchup_prediction',
    'get_strongest_weakest_teams',
    'get_rating_trend_emoji',
    # Defense Analysis
    'analyze_defensive_performance',
    'get_worst_defenses',
    'get_best_defenses',
    'get_position_matchups',
    'get_red_zone_defense',
    'get_defensive_trends',
    'get_matchup_recommendations',
    'get_defense_vs_position_matrix',
    'get_defense_difficulty_score',
]
