"""
Defensive Matchup Analysis Service

Analyzes defensive performance to help identify favorable matchups:
- TDs allowed by defense
- Position-specific defensive weaknesses
- Red zone defense efficiency
- Trending defensive performance
- Matchup recommendations

Usage:
    from services.defense_analysis_service import get_worst_defenses, get_position_matchups
    
    # Get worst defenses against TDs
    weak_defenses = get_worst_defenses(season=2025, limit=10)
    
    # Get position-specific matchups
    wr_matchups = get_position_matchups(season=2025, position='WR')
"""

import sqlite3
import pandas as pd
import numpy as np
from typing import Optional, Dict, List, Tuple
from utils.db_connection import get_db_context
from utils.nfl_data import load_data
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def analyze_defensive_performance(season: int) -> pd.DataFrame:
    """
    Analyze defensive performance for all teams.
    Calculates TDs allowed, points allowed, and defensive efficiency.
    
    Args:
        season: NFL season
    
    Returns:
        DataFrame with defensive statistics
    """
    try:
        # Load play-by-play data
        df = load_data(season)
        
        if df.empty:
            logger.warning(f"No data available for season {season}")
            return pd.DataFrame()
        
        # Filter to touchdowns only
        td_df = df[df['touchdown'] == 1].copy()
        
        if td_df.empty:
            return pd.DataFrame()
        
        # Analyze TDs allowed by defense (defteam)
        defense_stats = td_df.groupby('defteam').agg({
            'game_id': 'nunique',  # Games played
            'play_id': 'count',     # Total TDs allowed
            'td_player_name': lambda x: x.nunique()  # Unique TD scorers
        }).reset_index()
        
        defense_stats.columns = ['team', 'games_played', 'tds_allowed', 'unique_scorers']
        
        # Calculate per-game averages
        defense_stats['tds_per_game'] = defense_stats['tds_allowed'] / defense_stats['games_played']
        
        # Get first TD data if available
        if 'first_td_team' in df.columns:
            first_td_df = df[df['first_td_team'].notna()].copy()
            first_td_allowed = first_td_df.groupby('defteam').size().reset_index(name='first_tds_allowed')
            
            # Merge with main stats
            defense_stats = defense_stats.merge(
                first_td_allowed,
                left_on='team',
                right_on='defteam',
                how='left'
            ).drop('defteam', axis=1, errors='ignore')
            
            defense_stats['first_tds_allowed'] = defense_stats['first_tds_allowed'].fillna(0)
            defense_stats['first_td_rate'] = defense_stats['first_tds_allowed'] / defense_stats['games_played']
        else:
            # If first_td_team not available, set defaults
            defense_stats['first_tds_allowed'] = 0
            defense_stats['first_td_rate'] = 0.0
        
        # Rank defenses (higher rank = worse defense)
        defense_stats['rank'] = defense_stats['tds_per_game'].rank(ascending=False)
        
        return defense_stats.sort_values('tds_per_game', ascending=False)
    
    except Exception as e:
        logger.error(f"Error analyzing defensive performance: {e}")
        return pd.DataFrame()


def get_worst_defenses(season: int, limit: int = 10) -> pd.DataFrame:
    """
    Get the worst defenses (most TDs allowed).
    
    Args:
        season: NFL season
        limit: Number of defenses to return
    
    Returns:
        DataFrame with worst defenses
    """
    defense_stats = analyze_defensive_performance(season)
    
    if defense_stats.empty:
        return pd.DataFrame()
    
    return defense_stats.head(limit)


def get_best_defenses(season: int, limit: int = 10) -> pd.DataFrame:
    """
    Get the best defenses (fewest TDs allowed).
    
    Args:
        season: NFL season
        limit: Number of defenses to return
    
    Returns:
        DataFrame with best defenses
    """
    defense_stats = analyze_defensive_performance(season)
    
    if defense_stats.empty:
        return pd.DataFrame()
    
    return defense_stats.tail(limit).sort_values('tds_per_game')


def get_position_matchups(season: int, position: str) -> pd.DataFrame:
    """
    Analyze defensive performance against specific positions.
    
    Args:
        season: NFL season
        position: Position code (QB, RB, WR, TE)
    
    Returns:
        DataFrame with position-specific defensive stats
    """
    try:
        df = load_data(season)
        
        if df.empty:
            return pd.DataFrame()
        
        # Filter to TDs by position
        td_df = df[df['touchdown'] == 1].copy()
        
        # We need to join with player positions (from player_stats if available)
        with get_db_context() as conn:
            # Get player positions
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT player_name, position
                FROM player_stats
                WHERE season = ?
            """, (season,))
            
            position_map = {row['player_name']: row['position'] for row in cursor.fetchall()}
        
        # Add positions to TD data
        td_df['position'] = td_df['td_player_name'].map(position_map)
        
        # Filter to specific position
        pos_td_df = td_df[td_df['position'] == position].copy()
        
        if pos_td_df.empty:
            return pd.DataFrame()
        
        # Group by defense
        pos_defense = pos_td_df.groupby('defteam').agg({
            'game_id': 'nunique',
            'play_id': 'count',
            'td_player_name': lambda x: x.nunique()
        }).reset_index()
        
        pos_defense.columns = ['team', 'games_played', f'{position}_tds_allowed', 'unique_scorers']
        pos_defense[f'{position}_tds_per_game'] = pos_defense[f'{position}_tds_allowed'] / pos_defense['games_played']
        
        return pos_defense.sort_values(f'{position}_tds_per_game', ascending=False)
    
    except Exception as e:
        logger.error(f"Error analyzing position matchups: {e}")
        return pd.DataFrame()


def get_red_zone_defense(season: int) -> pd.DataFrame:
    """
    Analyze red zone defensive performance.
    
    Args:
        season: NFL season
    
    Returns:
        DataFrame with red zone defensive stats
    """
    try:
        df = load_data(season)
        
        if df.empty:
            return pd.DataFrame()
        
        # Filter to red zone plays (inside 20 yard line)
        rz_df = df[df['yardline_100'] <= 20].copy()
        
        # Get red zone TDs
        rz_td_df = rz_df[rz_df['touchdown'] == 1].copy()
        
        # Analyze by defense
        rz_defense = rz_td_df.groupby('defteam').agg({
            'game_id': 'nunique',
            'play_id': 'count'
        }).reset_index()
        
        rz_defense.columns = ['team', 'games_played', 'rz_tds_allowed']
        rz_defense['rz_tds_per_game'] = rz_defense['rz_tds_allowed'] / rz_defense['games_played']
        
        # Get red zone plays (opportunities)
        rz_plays = rz_df.groupby('defteam').size().reset_index(name='rz_plays')
        
        rz_defense = rz_defense.merge(rz_plays, left_on='team', right_on='defteam', how='left').drop('defteam', axis=1)
        rz_defense['rz_td_rate'] = (rz_defense['rz_tds_allowed'] / rz_defense['rz_plays']) * 100
        
        return rz_defense.sort_values('rz_td_rate', ascending=False)
    
    except Exception as e:
        logger.error(f"Error analyzing red zone defense: {e}")
        return pd.DataFrame()


def get_defensive_trends(season: int, team: str, weeks: int = 5) -> Dict[str, any]:
    """
    Analyze recent defensive trends for a team.
    
    Args:
        season: NFL season
        team: Team abbreviation
        weeks: Number of recent weeks to analyze
    
    Returns:
        Dict with trend analysis
    """
    try:
        df = load_data(season)
        
        if df.empty:
            return {'error': 'No data available'}
        
        # Filter to team's defensive plays
        team_def = df[df['defteam'] == team].copy()
        
        if team_def.empty:
            return {'error': f'No defensive data for {team}'}
        
        # Get TDs allowed by week
        td_by_week = team_def[team_def['touchdown'] == 1].groupby('week').size().reset_index(name='tds_allowed')
        
        # Get recent weeks
        recent_weeks = td_by_week.tail(weeks)
        
        if recent_weeks.empty:
            return {
                'team': team,
                'recent_tds_allowed': 0,
                'avg_tds_per_game': 0,
                'trend': 'STABLE'
            }
        
        recent_avg = recent_weeks['tds_allowed'].mean()
        overall_avg = td_by_week['tds_allowed'].mean()
        
        # Determine trend
        if recent_avg > overall_avg * 1.2:
            trend = 'DECLINING'  # Allowing more TDs
        elif recent_avg < overall_avg * 0.8:
            trend = 'IMPROVING'  # Allowing fewer TDs
        else:
            trend = 'STABLE'
        
        return {
            'team': team,
            'recent_tds_allowed': int(recent_weeks['tds_allowed'].sum()),
            'avg_tds_per_game': recent_avg,
            'overall_avg': overall_avg,
            'trend': trend,
            'weeks_analyzed': len(recent_weeks)
        }
    
    except Exception as e:
        logger.error(f"Error analyzing defensive trends: {e}")
        return {'error': str(e)}


def get_matchup_recommendations(season: int, week: int, limit: int = 5) -> List[Dict]:
    """
    Get recommended matchups based on defensive weaknesses.
    
    Args:
        season: NFL season
        week: Current week
        limit: Number of recommendations
    
    Returns:
        List of matchup recommendations
    """
    try:
        # Get worst defenses
        worst_defenses = get_worst_defenses(season, limit=limit)
        
        if worst_defenses.empty:
            return []
        
        recommendations = []
        
        for _, defense in worst_defenses.iterrows():
            team = defense['team']
            
            # Get recent trend
            trend = get_defensive_trends(season, team, weeks=3)
            
            rec = {
                'defense': team,
                'tds_allowed': int(defense['tds_allowed']),
                'tds_per_game': round(defense['tds_per_game'], 2),
                'first_td_rate': round(defense['first_td_rate'], 2),
                'trend': trend.get('trend', 'UNKNOWN'),
                'recommendation': _generate_recommendation(defense, trend)
            }
            
            recommendations.append(rec)
        
        return recommendations
    
    except Exception as e:
        logger.error(f"Error generating matchup recommendations: {e}")
        return []


def _generate_recommendation(defense_stats: pd.Series, trend: Dict) -> str:
    """Generate human-readable recommendation."""
    team = defense_stats['team']
    tds_per_game = defense_stats['tds_per_game']
    trend_status = trend.get('trend', 'STABLE')
    
    if tds_per_game >= 4.0:
        strength = "very weak"
    elif tds_per_game >= 3.5:
        strength = "weak"
    elif tds_per_game >= 3.0:
        strength = "below average"
    else:
        strength = "average"
    
    trend_text = {
        'DECLINING': "and trending worse",
        'IMPROVING': "but showing improvement",
        'STABLE': "with consistent performance"
    }.get(trend_status, "")
    
    return f"{team} has a {strength} defense ({tds_per_game:.1f} TDs/game) {trend_text}. Target offensive players against this defense."


def get_defense_vs_position_matrix(season: int) -> pd.DataFrame:
    """
    Create a matrix showing which defenses are weak against which positions.
    
    Args:
        season: NFL season
    
    Returns:
        DataFrame with defense vs position matchup matrix
    """
    positions = ['QB', 'RB', 'WR', 'TE']
    matrix_data = []
    
    for position in positions:
        pos_matchups = get_position_matchups(season, position)
        
        if not pos_matchups.empty:
            for _, row in pos_matchups.iterrows():
                matrix_data.append({
                    'team': row['team'],
                    'position': position,
                    'tds_allowed': row[f'{position}_tds_allowed'],
                    'tds_per_game': row[f'{position}_tds_per_game']
                })
    
    if not matrix_data:
        return pd.DataFrame()
    
    matrix_df = pd.DataFrame(matrix_data)
    
    # Pivot to create matrix
    pivot_df = matrix_df.pivot(index='team', columns='position', values='tds_per_game')
    
    return pivot_df.fillna(0)


def get_defense_difficulty_score(team: str, season: int) -> float:
    """
    Calculate a difficulty score for picking against a defense.
    Lower score = easier matchup (weaker defense).
    
    Args:
        team: Defense team abbreviation
        season: NFL season
    
    Returns:
        Difficulty score (0-100, lower is easier)
    """
    defense_stats = analyze_defensive_performance(season)
    
    if defense_stats.empty or team not in defense_stats['team'].values:
        return 50.0  # Default to average
    
    team_stats = defense_stats[defense_stats['team'] == team].iloc[0]
    
    # Normalize TDs per game to 0-100 scale
    # Assume 2.0 TDs/game is best (0), 5.0 TDs/game is worst (100)
    tds_per_game = team_stats['tds_per_game']
    
    if tds_per_game <= 2.0:
        score = 0
    elif tds_per_game >= 5.0:
        score = 100
    else:
        score = ((tds_per_game - 2.0) / 3.0) * 100
    
    # Invert so lower = easier
    return 100 - score
