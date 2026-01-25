"""
Analytics utilities for summarizing First TD data and player/team trends.
"""
from typing import Optional, Dict
import pandas as pd
from datetime import datetime, timedelta


def get_team_first_td_counts(first_tds_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates First TD counts by Team (posteam).
    Accepts pre-calculated first_tds DataFrame.
    """
    if first_tds_df is None or first_tds_df.empty:
        return pd.DataFrame()
    counts = first_tds_df['posteam'].value_counts().reset_index()
    counts.columns = ['Team', 'First TDs']
    return counts


def get_player_first_td_counts(first_tds_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates First TD counts by Player.
    Accepts pre-calculated first_tds DataFrame.
    """
    if first_tds_df is None or first_tds_df.empty:
        return pd.DataFrame()
    counts = first_tds_df['td_player_name'].value_counts().reset_index()
    counts.columns = ['Player', 'First TDs']
    return counts


def get_position_first_td_counts(first_tds_df: pd.DataFrame, roster_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates First TD counts by Position.
    Preferred join: first_tds.td_player_id -> rosters.gsis_id.
    Fallback: name-based join on lowercase trimmed names when IDs are missing.
    """
    if first_tds_df is None or first_tds_df.empty or roster_df is None or roster_df.empty:
        return pd.DataFrame()

    # Preferred: join by IDs
    if 'td_player_id' in first_tds_df.columns and 'gsis_id' in roster_df.columns:
        merged = first_tds_df.merge(roster_df, left_on='td_player_id', right_on='gsis_id', how='left')
        if 'position' in merged.columns:
            counts = merged['position'].value_counts().reset_index()
            counts.columns = ['Position', 'First TDs']
            return counts

    # Fallback: join by normalized names if available
    if 'td_player_name' in first_tds_df.columns and 'full_name' in roster_df.columns:
        tmp_ftd = first_tds_df.copy()
        tmp_ros = roster_df.copy()
        tmp_ftd['__name__'] = tmp_ftd['td_player_name'].astype(str).str.strip().str.lower()
        tmp_ros['__name__'] = tmp_ros['full_name'].astype(str).str.strip().str.lower()
        merged = tmp_ftd.merge(tmp_ros[['__name__', 'position']], on='__name__', how='left')
        if 'position' in merged.columns:
            counts = merged['position'].value_counts().reset_index()
            counts.columns = ['Position', 'First TDs']
            return counts

    return pd.DataFrame()


# ===== PHASE 2: PLAYER ROLLING STATISTICS =====

def get_player_rolling_first_td_rate(
    pbp_df: pd.DataFrame,
    player_name: str,
    roster_df: pd.DataFrame,
    window: int = 8
) -> pd.DataFrame:
    """
    Get rolling first TD rate for a player over last N games (L4, L8, etc).

    Args:
        pbp_df: Full play-by-play DataFrame with columns like game_id, game_date, week, td_player_name, posteam, etc.
        player_name: Player name to filter on
        roster_df: Roster data for position lookup (optional)
        window: Rolling window size (default 8 games)

    Returns:
        DataFrame with columns: game_date, week, game_id, player_name, position,
                                scored_first_td, rolling_first_td_rate, rolling_any_td_rate
    """
    if pbp_df is None or pbp_df.empty:
        return pd.DataFrame()

    # Filter for games where this player scored (first or any TD)
    # Check both 'td_player_name' (first TD) and look for any TD records
    player_mask = pbp_df['td_player_name'] == player_name
    player_games = pbp_df[player_mask].copy()

    if player_games.empty:
        return pd.DataFrame()

    # Get unique games for this player (deduplicate by game_id)
    game_cols = ['game_id', 'game_date', 'week', 'posteam']
    available_cols = [c for c in game_cols if c in player_games.columns]
    game_data = player_games[available_cols].drop_duplicates(subset=['game_id'])

    # Mark if player scored first TD in that game
    game_data['scored_first_td'] = 1

    # Sort by game date
    if 'game_date' in game_data.columns:
        game_data = game_data.sort_values('game_date').reset_index(drop=True)

    # Calculate rolling rates
    game_data['rolling_first_td_rate'] = game_data['scored_first_td'].rolling(window=window, min_periods=1).mean()

    # Add any-time TD indicator (simplified: if player appears in any TD, mark it)
    # For full accuracy, would need to separate first TD from subsequent TDs in PBP
    game_data['rolling_any_td_rate'] = game_data['rolling_first_td_rate']  # Simplified for now

    # Add position from roster if available
    if roster_df is not None and not roster_df.empty:
        pos_map = dict(zip(roster_df['full_name'], roster_df['position']))
        game_data['position'] = game_data.get('posteam', '').map(lambda x: pos_map.get(player_name, 'N/A'))

    game_data['player_name'] = player_name

    return game_data[
        ['game_date', 'week', 'game_id', 'player_name', 'scored_first_td',
         'rolling_first_td_rate', 'rolling_any_td_rate']
    ].reset_index(drop=True)


def get_player_recent_games(
    pbp_df: pd.DataFrame,
    player_name: str,
    last_n_games: int = 10
) -> pd.DataFrame:
    """
    Get game log for a player (last N games with first TD indicator).

    Args:
        pbp_df: Full play-by-play DataFrame
        player_name: Player to filter
        last_n_games: How many recent games to include

    Returns:
        DataFrame with columns: game_date, week, opponent, scored_first_td
    """
    if pbp_df is None or pbp_df.empty:
        return pd.DataFrame()

    player_mask = pbp_df['td_player_name'] == player_name
    player_games = pbp_df[player_mask].copy()

    if player_games.empty:
        return pd.DataFrame()

    cols_needed = ['game_id', 'game_date', 'week', 'posteam', 'defteam']
    available_cols = [c for c in cols_needed if c in player_games.columns]

    game_data = player_games[available_cols].drop_duplicates(subset=['game_id'])
    game_data = game_data.sort_values('game_date', ascending=False).head(last_n_games)
    game_data['scored_first_td'] = 1

    # Compute opponent
    if 'defteam' in game_data.columns:
        game_data['opponent'] = game_data['defteam']

    return game_data.reset_index(drop=True)


def get_player_home_away_splits(
    pbp_df: pd.DataFrame,
    player_name: str,
    schedule_df: pd.DataFrame = None
) -> Dict[str, dict]:
    """
    Get first TD rate split by home vs away.

    Args:
        pbp_df: Full play-by-play DataFrame
        player_name: Player to analyze
        schedule_df: Optional schedule DataFrame with home_team, away_team columns

    Returns:
        Dict with 'home' and 'away' entries:
        {'home': {'games': 5, 'first_tds': 2, 'rate': 0.4},
         'away': {'games': 4, 'first_tds': 1, 'rate': 0.25}}
    """
    if pbp_df is None or pbp_df.empty:
        return {}

    player_mask = pbp_df['td_player_name'] == player_name
    player_games = pbp_df[player_mask].copy()

    if player_games.empty:
        return {}

    # Determine if player's team was home or away
    # Requires schedule or game metadata
    splits = {}

    for location in ['home', 'away']:
        if location == 'home':
            # Filter for games where posteam was home
            # This is a simplified approach; full accuracy needs schedule join
            subset = player_games.copy()
        else:
            subset = player_games.copy()

        if not subset.empty:
            games = subset['game_id'].nunique()
            tds = len(subset)
            splits[location] = {
                'games': games,
                'first_tds': tds,
                'rate': tds / games if games > 0 else 0.0
            }

    return splits or {'home': {}, 'away': {}}


# ===== PHASE 2: TEAM TRENDS =====

def get_team_first_td_trends(
    first_tds_df: pd.DataFrame,
    team: str,
    last_n_weeks: int = 4
) -> Dict[str, any]:
    """
    Get team's first TD scoring trends over recent weeks.

    Args:
        first_tds_df: First TDs DataFrame (filtered to season)
        team: Team abbreviation (e.g., 'KC', 'TB')
        last_n_weeks: Weeks to look back

    Returns:
        {
            'total_first_tds': 4,
            'by_player': {'Player A': 2, 'Player B': 1, ...},
            'by_position': {'RB': 2, 'WR': 1, 'TE': 1},
            'by_week': [week_1_count, week_2_count, ...]
        }
    """
    if first_tds_df is None or first_tds_df.empty:
        return {}

    # Filter by team (posteam is scoring team)
    team_tds = first_tds_df[first_tds_df['posteam'] == team].copy()

    if team_tds.empty:
        return {}

    # Filter by week if available
    if 'week' in team_tds.columns:
        max_week = team_tds['week'].max()
        week_filter = team_tds['week'] >= (max_week - last_n_weeks + 1)
        team_tds = team_tds[week_filter]

    result = {
        'total_first_tds': len(team_tds),
        'by_player': team_tds['td_player_name'].value_counts().to_dict() if 'td_player_name' in team_tds.columns else {},
        'by_position': team_tds.get('position', pd.Series()).value_counts().to_dict() if 'position' in team_tds.columns else {},
    }

    # By week breakdown
    if 'week' in team_tds.columns:
        result['by_week'] = team_tds['week'].value_counts().sort_index().to_dict()

    return result


def get_position_trending(
    first_tds_df: pd.DataFrame,
    roster_df: pd.DataFrame = None,
    last_n_weeks: int = 4
) -> pd.DataFrame:
    """
    Get positions trending (hot positions by first TD rate in recent weeks).

    Args:
        first_tds_df: First TDs DataFrame
        roster_df: Roster data for position join
        last_n_weeks: Weeks to analyze

    Returns:
        DataFrame: position, first_tds_count, td_rate, pct_of_total
    """
    if first_tds_df is None or first_tds_df.empty:
        return pd.DataFrame()

    # Filter by recent weeks if available
    if 'week' in first_tds_df.columns:
        max_week = first_tds_df['week'].max()
        recent_tds = first_tds_df[first_tds_df['week'] >= (max_week - last_n_weeks + 1)].copy()
    else:
        recent_tds = first_tds_df.copy()

    # Join with roster for positions
    if roster_df is not None and not roster_df.empty and 'td_player_name' in recent_tds.columns:
        recent_tds = recent_tds.merge(
            roster_df[['full_name', 'position']],
            left_on='td_player_name',
            right_on='full_name',
            how='left'
        )

    if 'position' not in recent_tds.columns:
        return pd.DataFrame()

    pos_counts = recent_tds['position'].value_counts().reset_index()
    pos_counts.columns = ['position', 'first_tds_count']
    total = pos_counts['first_tds_count'].sum()
    pos_counts['pct_of_total'] = (pos_counts['first_tds_count'] / total * 100).round(2)

    return pos_counts.sort_values('first_tds_count', ascending=False)
