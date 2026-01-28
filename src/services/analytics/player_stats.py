"""
Player Statistics Service

Tracks player performance metrics including:
- First TD scoring rates and trends
- Any time TD tracking
- Red zone usage
- Hot/cold player form detection
- Position-based analytics

Usage:
    from services.player_stats_service import update_player_stats, get_player_form
    
    # Update stats after grading
    update_player_stats(season=2025, week=1)
    
    # Get player form badge
    form = get_player_form("Patrick Mahomes", 2025)  # Returns: 'HOT', 'AVERAGE', or 'COLD'
"""

import sqlite3
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from database import get_db_context
from utils.nfl_data import load_data
import logging

logger = logging.getLogger(__name__)


def update_player_stats(season: int, week: Optional[int] = None) -> Dict[str, int]:
    """
    Update player_stats table with latest performance data.
    Calculates TD counts, games played, and recent form.
    
    Args:
        season: NFL season year
        week: Optional specific week to update (None = all weeks)
    
    Returns:
        Dict with statistics: players_updated, new_players, errors
    """
    stats = {'players_updated': 0, 'new_players': 0, 'errors': 0}
    
    try:
        # Load NFL play-by-play data for the season
        df = load_data(season)
        
        if df.empty:
            logger.warning(f"No data available for season {season}")
            return stats
        
        # Filter TDs only
        td_df = df[df['touchdown'] == 1].copy()
        
        if td_df.empty:
            logger.warning(f"No touchdowns found for season {season}")
            return stats
        
        # Infer positions from play type since PBP data doesn't have position column
        def infer_position(row):
            """Infer player position from play type."""
            td_player = row['td_player_name']
            
            # Check if QB (passes the ball or rushes as passer)
            if 'passer_player_name' in row and row.get('passer_player_name') == td_player:
                return 'QB'  # QB rushing TD
            
            # Check if RB (typically rushers)
            if 'rusher_player_name' in row and row.get('rusher_player_name') == td_player:
                # If they're also the passer, they're QB
                if 'passer_player_name' in row and row.get('passer_player_name') == td_player:
                    return 'QB'
                return 'RB'
            
            # Check if WR/TE (receivers)
            if 'receiver_player_name' in row and row.get('receiver_player_name') == td_player:
                # Can't distinguish WR from TE without roster data, default to WR
                return 'WR'
            
            # Check if kicker or punter
            if 'kicker_player_name' in row and row.get('kicker_player_name') == td_player:
                return 'K'
            if 'punter_player_name' in row and row.get('punter_player_name') == td_player:
                return 'P'
            
            # Default: unknown
            return None
        
        # Add inferred position to each TD
        td_df['inferred_position'] = td_df.apply(infer_position, axis=1)
        
        # Group by player and calculate stats
        player_stats_df = td_df.groupby(['td_player_name', 'posteam']).agg({
            'game_id': 'nunique',  # Games played (games where they scored)
            'play_id': 'count',     # Total TDs (any time)
            'inferred_position': lambda x: x.mode()[0] if len(x.mode()) > 0 else None  # Most common position
        }).reset_index()
        
        player_stats_df.columns = ['player_name', 'team', 'games_played', 'any_time_td_count', 'position']
        
        # Get first TD data from your database
        with get_db_context() as conn:
            cursor = conn.cursor()
            
            # Get first TD counts from actual results
            cursor.execute("""
                SELECT 
                    p.player_name,
                    p.team,
                    COUNT(DISTINCT CASE WHEN r.is_correct = 1 THEN p.id END) as first_td_count,
                    MAX(w.week) as last_td_week
                FROM picks p
                JOIN weeks w ON p.week_id = w.id
                LEFT JOIN results r ON r.pick_id = p.id
                WHERE w.season = ?
                GROUP BY p.player_name, p.team
            """, (season,))
            
            first_td_data = cursor.fetchall()
            first_td_dict = {
                (row['player_name'], row['team']): {
                    'first_td_count': row['first_td_count'],
                    'last_td_week': row['last_td_week']
                }
                for row in first_td_data
            }
            
            # Update or insert player stats
            for _, row in player_stats_df.iterrows():
                player_name = row['player_name']
                team = row['team']
                
                if pd.isna(player_name) or not player_name:
                    continue
                
                # Get first TD data if available
                first_td_info = first_td_dict.get((player_name, team), {
                    'first_td_count': 0,
                    'last_td_week': None
                })
                
                # Calculate recent form (based on last 5 weeks)
                recent_form = _calculate_player_form(
                    conn, player_name, season, current_week=week or 18
                )
                
                # Get position for this player
                position = row.get('position', None)
                
                # Try to update existing record
                cursor.execute("""
                    UPDATE player_stats
                    SET games_played = ?,
                        first_td_count = ?,
                        any_time_td_count = ?,
                        last_td_week = ?,
                        recent_form = ?,
                        position = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE player_name = ? AND season = ? AND team = ?
                """, (
                    int(row['games_played']),
                    first_td_info['first_td_count'],
                    int(row['any_time_td_count']),
                    first_td_info['last_td_week'],
                    recent_form,
                    position,
                    player_name,
                    season,
                    team
                ))
                
                if cursor.rowcount == 0:
                    # Insert new record
                    cursor.execute("""
                        INSERT INTO player_stats (
                            player_name, season, team, position, games_played,
                            first_td_count, any_time_td_count, last_td_week, recent_form
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        player_name,
                        season,
                        team,
                        position,
                        int(row['games_played']),
                        first_td_info['first_td_count'],
                        int(row['any_time_td_count']),
                        first_td_info['last_td_week'],
                        recent_form
                    ))
                    stats['new_players'] += 1
                else:
                    stats['players_updated'] += 1
            
            conn.commit()
            logger.info(f"Updated player stats for season {season}: {stats}")
    
    except Exception as e:
        logger.error(f"Error updating player stats: {e}")
        stats['errors'] = 1
    
    return stats


def _calculate_player_form(
    conn: sqlite3.Connection,
    player_name: str,
    season: int,
    current_week: int,
    lookback_weeks: int = 5
) -> str:
    """
    Calculate player's recent form based on TD scoring in last N weeks.
    
    Returns:
        'HOT' - Scored TD in 3+ of last 5 weeks
        'AVERAGE' - Scored TD in 1-2 of last 5 weeks
        'COLD' - No TDs in last 5 weeks
    """
    cursor = conn.cursor()
    
    # Get TD counts in recent weeks
    cursor.execute("""
        SELECT COUNT(DISTINCT w.week) as td_weeks
        FROM picks p
        JOIN weeks w ON p.week_id = w.id
        JOIN results r ON r.pick_id = p.id
        WHERE p.player_name = ?
            AND w.season = ?
            AND w.week > ?
            AND w.week <= ?
            AND (r.is_correct = 1 OR r.any_time_td = 1)
    """, (player_name, season, max(1, current_week - lookback_weeks), current_week))
    
    result = cursor.fetchone()
    td_weeks = result['td_weeks'] if result else 0
    
    if td_weeks >= 3:
        return 'HOT'
    elif td_weeks >= 1:
        return 'AVERAGE'
    else:
        return 'COLD'


def get_player_form(player_name: str, season: int, team: Optional[str] = None) -> str:
    """
    Get player's current form rating.
    
    Args:
        player_name: Player's name
        season: NFL season
        team: Optional team filter
    
    Returns:
        Form string: 'HOT', 'AVERAGE', or 'COLD'
    """
    with get_db_context() as conn:
        cursor = conn.cursor()
        
        query = """
            SELECT recent_form
            FROM player_stats
            WHERE player_name = ? AND season = ?
        """
        params = [player_name, season]
        
        if team:
            query += " AND team = ?"
            params.append(team)
        
        query += " ORDER BY updated_at DESC LIMIT 1"
        
        cursor.execute(query, params)
        result = cursor.fetchone()
        
        return result['recent_form'] if result else 'AVERAGE'


def get_hot_players(season: int, min_tds: int = 2) -> pd.DataFrame:
    """
    Get list of hot players (strong recent performance).
    
    Args:
        season: NFL season
        min_tds: Minimum TD count to be considered
    
    Returns:
        DataFrame with hot players and their stats
    """
    with get_db_context() as conn:
        query = """
            SELECT 
                player_name,
                team,
                position,
                games_played,
                first_td_count,
                any_time_td_count,
                recent_form,
                ROUND(CAST(first_td_count AS FLOAT) / NULLIF(games_played, 0), 3) as first_td_rate,
                ROUND(CAST(any_time_td_count AS FLOAT) / NULLIF(games_played, 0), 3) as any_td_rate
            FROM player_stats
            WHERE season = ?
                AND recent_form = 'HOT'
                AND any_time_td_count >= ?
            ORDER BY any_time_td_count DESC, first_td_count DESC
        """
        
        df = pd.read_sql_query(query, conn, params=(season, min_tds))
        return df


def get_player_stats_detail(player_name: str, season: int) -> Optional[Dict]:
    """
    Get detailed statistics for a specific player.
    
    Args:
        player_name: Player's name
        season: NFL season
    
    Returns:
        Dict with player statistics or None if not found
    """
    with get_db_context() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT *
            FROM player_stats
            WHERE player_name = ? AND season = ?
            ORDER BY updated_at DESC
            LIMIT 1
        """, (player_name, season))
        
        result = cursor.fetchone()
        
        if result:
            return dict(result)
        return None


def get_position_leaders(season: int, position: str, limit: int = 10) -> pd.DataFrame:
    """
    Get top players by position for first TD scoring.
    
    Args:
        season: NFL season
        position: Position code (QB, RB, WR, TE)
        limit: Number of players to return
    
    Returns:
        DataFrame with top performers by position
    """
    with get_db_context() as conn:
        query = """
            SELECT 
                player_name,
                team,
                position,
                games_played,
                first_td_count,
                any_time_td_count,
                recent_form,
                ROUND(CAST(first_td_count AS FLOAT) / NULLIF(games_played, 0), 3) as first_td_rate
            FROM player_stats
            WHERE season = ? AND position = ?
            ORDER BY first_td_count DESC, any_time_td_count DESC
            LIMIT ?
        """
        
        df = pd.read_sql_query(query, conn, params=(season, position, limit))
        return df


def get_team_top_scorers(season: int, team: str, limit: int = 5) -> pd.DataFrame:
    """
    Get top TD scorers for a specific team.
    
    Args:
        season: NFL season
        team: Team abbreviation
        limit: Number of players to return
    
    Returns:
        DataFrame with team's top scorers
    """
    with get_db_context() as conn:
        query = """
            SELECT 
                player_name,
                team,
                position,
                games_played,
                first_td_count,
                any_time_td_count,
                recent_form,
                last_td_week
            FROM player_stats
            WHERE season = ? AND team = ?
            ORDER BY any_time_td_count DESC, first_td_count DESC
            LIMIT ?
        """
        
        df = pd.read_sql_query(query, conn, params=(season, team, limit))
        return df


def get_player_comparison(player_names: List[str], season: int) -> pd.DataFrame:
    """
    Compare statistics for multiple players.
    
    Args:
        player_names: List of player names to compare
        season: NFL season
    
    Returns:
        DataFrame with comparison data
    """
    if not player_names:
        return pd.DataFrame()
    
    with get_db_context() as conn:
        placeholders = ','.join(['?' for _ in player_names])
        query = f"""
            SELECT 
                player_name,
                team,
                position,
                games_played,
                first_td_count,
                any_time_td_count,
                recent_form,
                ROUND(CAST(first_td_count AS FLOAT) / NULLIF(games_played, 0), 3) as first_td_rate,
                ROUND(CAST(any_time_td_count AS FLOAT) / NULLIF(games_played, 0), 3) as any_td_rate
            FROM player_stats
            WHERE season = ? AND player_name IN ({placeholders})
            ORDER BY any_time_td_count DESC
        """
        
        params = [season] + player_names
        df = pd.read_sql_query(query, conn, params=params)
        return df


def get_form_badge_emoji(form: str) -> str:
    """
    Get emoji badge for player form.
    
    Args:
        form: Form rating ('HOT', 'AVERAGE', 'COLD')
    
    Returns:
        Emoji string
    """
    badges = {
        'HOT': '🔥',
        'AVERAGE': '✓',
        'COLD': '❄️'
    }
    return badges.get(form, '✓')


def get_player_summary_text(player_name: str, season: int) -> str:
    """
    Get human-readable summary of player's performance.
    
    Args:
        player_name: Player's name
        season: NFL season
    
    Returns:
        Summary text (e.g., "Patrick Mahomes has scored 5 TDs in last 10 games 🔥")
    """
    stats = get_player_stats_detail(player_name, season)
    
    if not stats:
        return f"{player_name} - No data available"
    
    form_emoji = get_form_badge_emoji(stats['recent_form'])
    td_count = stats['any_time_td_count']
    games = stats['games_played']
    
    return f"{player_name} has scored {td_count} TDs in {games} games {form_emoji}"
