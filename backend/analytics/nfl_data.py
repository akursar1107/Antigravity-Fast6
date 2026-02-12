"""
NFL Data Loading Module
Handles loading and processing play-by-play data from nflreadpy.
"""

import nflreadpy as nfl
import pandas as pd
import logging
from typing import Optional
from backend.utils.caching import cached, CacheTTL

logger = logging.getLogger(__name__)


def _classify_game_type(start_time_dt: pd.Timestamp) -> str:
    """
    Classify a game as 'Main Slate' or 'Standalone' based on start time.
    
    Main Slate: Sunday games starting before 8 PM (20:00)
    Standalone: Everything else (or if time is missing)
    
    Args:
        start_time_dt: Pandas Timestamp of game start time
        
    Returns:
        str: 'Main Slate' or 'Standalone'
    """
    if pd.isna(start_time_dt):
        return "Standalone"
    
    is_sunday = start_time_dt.weekday() == 6
    is_before_8pm = start_time_dt.hour < 20
    
    if is_sunday and is_before_8pm:
        return "Main Slate"
    return "Standalone"


@cached(ttl=300)
def load_data(season: int) -> pd.DataFrame:
    """
    Loads NFL play-by-play data for a specific season.
    Uses TTL-based caching to avoid reloading on every request.
    Refreshes every 5 minutes for database sync compatibility.
    """
    try:
        df = nfl.load_pbp(seasons=[int(season)]).to_pandas()
        df = process_game_type(df)
        return df
    except Exception as e:
        logger.error(f"Error loading play-by-play data for {season}: {e}")
        return pd.DataFrame()


def process_game_type(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add game_type column to dataframe (Main Slate or Standalone).
    Tries multiple timestamp sources gracefully.
    """
    if df.empty:
        return df

    try:
        ts = None
        if 'game_datetime' in df.columns:
            ts = pd.to_datetime(df['game_datetime'], errors='coerce', utc=True, format='mixed')
        elif 'start_time' in df.columns:
            # Normalize strings and allow mixed formats without warnings
            ts = pd.to_datetime(df['start_time'].astype(str), errors='coerce', utc=True, format='mixed')
        elif 'game_date' in df.columns:
            ts = pd.to_datetime(df['game_date'], errors='coerce', utc=True, format='mixed')

        if ts is not None:
            df = df.copy()
            df['game_type'] = ts.apply(_classify_game_type)
        return df
    except Exception as e:
        logger.error(f"Error processing game type: {e}")
        return df


@cached(ttl=300)
def get_game_schedule(df: pd.DataFrame, season: int) -> pd.DataFrame:
    """
    Load season schedule from nflreadpy (more reliable than PBP-derived),
    and classify game_type using gameday + gametime.
    Returns: game_id, week, game_date, start_time, home_team, away_team, (optional scores), game_type
    """
    try:
        import nflreadpy as nfl
        schedule = nfl.load_schedules(seasons=[int(season)]).to_pandas()
        schedule['start_time_dt'] = pd.to_datetime(schedule['gameday'] + ' ' + schedule['gametime'], errors='coerce')
        schedule['game_type'] = schedule['start_time_dt'].apply(_classify_game_type)
        cols = ['game_id', 'week', 'gameday', 'gametime', 'home_team', 'away_team', 'home_score', 'away_score', 'game_type']
        cols = [c for c in cols if c in schedule.columns]
        schedule = schedule[cols].rename(columns={'gameday': 'game_date', 'gametime': 'start_time'})
        return schedule
    except Exception as e:
        logger.error(f"Error getting schedule: {e}")
        return pd.DataFrame()


@cached(ttl=300)
def get_touchdowns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract all touchdown plays from play-by-play data.
    Returns DataFrame with touchdown info including player name and team.
    Uses correct scorer for return TDs (INT, fumble, punt/kick) to avoid
    attributing to passer (QB who threw INT or fumbled).
    """
    if df.empty:
        return pd.DataFrame()
    
    try:
        tds = df[df['touchdown'] == 1].copy()
        
        def _td_name(row):
            # Return TDs: use returner/fumble recovery. Never use passer - that's
            # the QB who threw the INT or fumbled, not the scorer.
            rt = row.get('return_touchdown')
            if rt == 1:
                return (
                    row.get('returner_player_name')
                    or row.get('fumble_recovery_1_player_name')
                    or row.get('lateral_receiver_player_name')
                    or 'Unknown'
                )
            # Offensive TDs: receiver (pass), rusher (rush), passer (QB sneak)
            return (
                row.get('receiver_player_name')
                or row.get('rusher_player_name')
                or row.get('passer_player_name')
                or 'Unknown'
            )

        def _td_id(row):
            rt = row.get('return_touchdown')
            if rt == 1:
                return (
                    row.get('returner_player_id')
                    or row.get('fumble_recovery_1_player_id')
                    or row.get('lateral_receiver_player_id')
                    or None
                )
            return (
                row.get('receiver_player_id')
                or row.get('rusher_player_id')
                or row.get('passer_player_id')
                or None
            )

        def _td_team(row):
            """Scorer's team: for return TDs use defteam (scoring team), else posteam."""
            rt = row.get('return_touchdown')
            if rt == 1:
                return row.get('defteam') or row.get('posteam') or ''
            return row.get('posteam') or ''

        tds['td_player_name'] = tds.apply(_td_name, axis=1)
        tds['td_player_id'] = tds.apply(_td_id, axis=1)
        tds['td_scorer_team'] = tds.apply(_td_team, axis=1)
        return tds
    except Exception as e:
        logger.error(f"Error extracting touchdowns: {e}")
        return pd.DataFrame()


@cached(ttl=300)
def get_first_tds(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract first touchdown per game from play-by-play data.
    Returns one row per game with first TD scorer info.
    """
    if df.empty:
        return pd.DataFrame()
    
    try:
        tds = get_touchdowns(df)
        if tds.empty:
            return pd.DataFrame()
        
        first_tds = tds.sort_values('play_id').groupby('game_id').first().reset_index()
        cols = ['game_id', 'week', 'home_team', 'away_team', 'td_player_name', 'td_player_id', 'play_id', 'posteam', 'qtr', 'desc']
        existing_cols = [c for c in cols if c in first_tds.columns]
        return first_tds[existing_cols]
    except Exception as e:
        logger.error(f"Error extracting first TDs: {e}")
        return pd.DataFrame()


@cached(ttl=300)
def load_rosters(season: int) -> pd.DataFrame:
    """
    Load NFL player rosters for a season.
    Returns DataFrame with player info including full_name, team, position, etc.
    """
    try:
        rosters = nfl.load_rosters(seasons=[int(season)]).to_pandas()
        return rosters
    except Exception as e:
        logger.error(f"Error loading rosters for {season}: {e}")
        return pd.DataFrame()
