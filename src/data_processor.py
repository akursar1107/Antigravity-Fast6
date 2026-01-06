import nflreadpy as nfl
import pandas as pd
import streamlit as st
import requests
from typing import Dict, List, Optional, Union, Tuple
import config


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


@st.cache_data(ttl=300)
def load_data(season: int) -> pd.DataFrame:
    """
    Loads NFL play-by-play data for a specific season.
    Uses streamlit caching to avoid reloading on every interaction.
    Refreshes every 5 minutes for database sync compatibility.
    """
    try:
        # years must be a list
        df = nfl.load_pbp(seasons=[int(season)]).to_pandas()
        df = process_game_type(df)
        return df
    except Exception as e:
        st.error(f"Error loading data for season {season}: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=300)
def load_rosters(season: int) -> pd.DataFrame:
    """
    Loads roster data to get player names and teams.
    Refreshes every 5 minutes for database sync compatibility.
    """
    try:
        # years must be a list
        df = nfl.load_rosters(seasons=[int(season)]).to_pandas()
        # Keep gsis_id for linking if available
        cols = ['full_name', 'team', 'position', 'status', 'gsis_id']
        # Filter cols to be safe
        cols = [c for c in cols if c in df.columns]
        return df[cols]
    except Exception as e:
        st.error(f"Error loading rosters for season {season}: {e}")
        return pd.DataFrame()

def get_touchdowns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filters the DataFrame for plays where a touchdown was scored.
    """
    if df.empty:
        return df
    # Filter for touchdown plays
    # nflreadpy has a 'touchdown' column (1.0 for yes, 0.0 for no)
    return df[df['touchdown'] == 1].copy()

def get_first_tds(df: pd.DataFrame) -> pd.DataFrame:
    """
    Identifies the first touchdown scorer for each game.
    """
    if df.empty:
        return df

    # Get all touchdowns first
    tds = get_touchdowns(df)

    # Sort by game_id and play_id (play_id implies chronological order)
    tds_sorted = tds.sort_values(by=['game_id', 'play_id'])

    # Group by game and take the first one
    first_tds = tds_sorted.groupby('game_id').head(1)

    return first_tds

def process_game_type(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a 'game_type' column to the dataframe: 'Main Slate' or 'Standalone'.
    Main Slate: Sunday games starting before 8 PM (20:00).
    Standalone: Everything else.
    """
    if df.empty:
        return df
        
    # Ensure start_time is datetime
    # The format seen is '9/8/24, 13:03:02'
    # We specify the format to avoid the UserWarning and improve performance
    df['start_time_dt'] = pd.to_datetime(df['start_time'], format='%m/%d/%y, %H:%M:%S', errors='coerce')
    
    # Use helper function to classify games
    df['game_type'] = df['start_time_dt'].apply(_classify_game_type)
    return df

def get_game_schedule(pbp_df: pd.DataFrame, season: int) -> pd.DataFrame:
    """
    Aggregates game data to show schedule, scores, and first TD.
    Uses nfl.load_schedules to ensure future games are included.
    """
    try:
        # Load full schedule for the season
        schedule = nfl.load_schedules(seasons=[int(season)]).to_pandas()
    except Exception as e:
        st.error(f"Error loading schedule: {e}")
        return pd.DataFrame()
        
    # Standardize columns
    # We construct a 'start_time' column to match process_game_type expectation if possible
    # load_schedules has 'gameday' (YYYY-MM-DD) and 'gametime' (HH:MM)
    
    # Combine to datetime for game classification
    schedule['start_time_dt'] = pd.to_datetime(schedule['gameday'] + ' ' + schedule['gametime'], errors='coerce')
    
    # Use helper function to classify games
    schedule['game_type'] = schedule['start_time_dt'].apply(_classify_game_type)

    # Select cols
    cols = ['game_id', 'week', 'gameday', 'gametime', 'home_team', 'away_team', 'home_score', 'away_score', 'game_type']
    schedule = schedule[cols].rename(columns={'gameday': 'game_date', 'gametime': 'start_time'})
    
    # Get First TDs from PBP data
    if not pbp_df.empty:
        first_tds = get_first_tds(pbp_df)[['game_id', 'td_player_name', 'posteam']]
        first_tds = first_tds.rename(columns={
            'td_player_name': 'First TD Scorer',
            'posteam': 'First TD Team'
        })
        # Merge
        schedule = schedule.merge(first_tds, on='game_id', how='left')
    else:
        schedule['First TD Scorer'] = None
        schedule['First TD Team'] = None
    
    # Fill NaN
    schedule['First TD Scorer'] = schedule['First TD Scorer'].fillna("None")
    
    return schedule

def get_team_abbr(full_name: str) -> str:
    """
    Maps full team names (Odds API) to abbreviations (nflreadpy).
    """
    return config.TEAM_ABBR_MAP.get(full_name, full_name)

def get_team_full_name(abbr: str) -> str:
    """
    Maps abbreviation (nflreadpy) to full team name (Odds API).
    """
    for name, a in config.TEAM_ABBR_MAP.items():
        if a == abbr:
            return name
    return abbr

@st.cache_data(ttl=3600)
def get_first_td_odds(api_key: str, week_start_date: str, week_end_date: str) -> Dict[Tuple[str, str], Dict[str, float]]:
    """
    Fetches First TD odds from The Odds API.
    Matches games based on date window.
    Returns a dict: {(home_team, away_team): {player_name: price}}
    """
    # 1. Get Events
    events_url = f'https://api.the-odds-api.com/v4/sports/americanfootball_nfl/events?apiKey={api_key}'
    try:
        r = requests.get(events_url)
        if r.status_code != 200:
            st.error(f"Error fetching events from Odds API: {r.text}")
            return {}
        events = r.json()
    except Exception as e:
        st.error(f"Error connecting to Odds API: {e}")
        return {}

    # Filter events for the relevant week
    # We rely on 'commence_time' (ISO format).
    # Simple string comparison might be enough if dates are YYYY-MM-DD
    week_events = []
    
    # week_start_date and week_end_date expect 'YYYY-MM-DD' strings
    for e in events:
        c_time = e['commence_time'] # e.g. 2024-09-08T17:00:00Z
        c_date = c_time.split('T')[0]
        if week_start_date <= c_date <= week_end_date:
            week_events.append(e)

    odds_data = {}
    
    for e in week_events:
        event_id = e['id']
        # 2. Get Odds for event
        # Try player_anytime_td since player_first_td is restricted/unavailable
        odds_url = f'https://api.the-odds-api.com/v4/sports/americanfootball_nfl/events/{event_id}/odds?apiKey={api_key}&regions=us&markets=player_anytime_td&oddsFormat=american'
        
        try:
            r_odds = requests.get(odds_url)
            if r_odds.status_code == 200:
                data = r_odds.json()
                # Parse bookmakers
                # We'll take the first avail bookmaker for now
                bookmakers = data.get('bookmakers', [])
                game_odds = {}
                if bookmakers:
                    # Look for player_first_td market
                    for bm in bookmakers:
                        for m in bm.get('markets', []):
                            if m['key'] == 'player_anytime_td':
                                for outcome in m['outcomes']:
                                    p_name = outcome['description']
                                    price = outcome['price']
                                    game_odds[p_name] = price
                                break # Use first valid bookmaker
                        if game_odds: break
                
                # Map to a key we can match with schedule? 
                # The schedule game_id is like '2024_01_DET_KC'. 
                # The API event has 'home_team' and 'away_team'.
                # We'll use a standardized key: f"{h_team}_{a_team}" or just map by matching team names later
                # For now, let's return map by team names in the event
                h_team = get_team_abbr(e['home_team'])
                a_team = get_team_abbr(e['away_team'])
                odds_data[(h_team, a_team)] = game_odds

            else:
                # Optionally log warning but don't crash
                # print(f"Failed to get odds for {event_id}: {r_odds.text}")
                pass
        except:
            continue
            
    return odds_data

def get_team_first_td_counts(first_tds_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates First TD counts by Team.
    Accepts pre-calculated first_tds DataFrame.
    """
    if first_tds_df.empty: return pd.DataFrame()
    # Count by 'posteam'
    counts = first_tds_df['posteam'].value_counts().reset_index()
    counts.columns = ['Team', 'First TDs']
    return counts

def get_player_first_td_counts(first_tds_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates First TD counts by Player.
    Accepts pre-calculated first_tds DataFrame.
    """
    if first_tds_df.empty: return pd.DataFrame()
    # Count by 'td_player_name'
    counts = first_tds_df['td_player_name'].value_counts().reset_index()
    counts.columns = ['Player', 'First TDs']
    return counts

def get_position_first_td_counts(first_tds_df: pd.DataFrame, roster_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates First TD counts by Position.
    Accepts pre-calculated first_tds DataFrame.
    """
    if first_tds_df.empty or roster_df.empty: return pd.DataFrame()
    
    # Check if we have IDs to link
    if 'td_player_id' in first_tds_df.columns and 'gsis_id' in roster_df.columns:
        # Merge
        merged = first_tds_df.merge(roster_df, left_on='td_player_id', right_on='gsis_id', how='left')
        counts = merged['position'].value_counts().reset_index()
        counts.columns = ['Position', 'First TDs']
        return counts
    
    return pd.DataFrame()

def names_match(pred: str, actual: str) -> bool:
    """
    Fuzzy match logic for comparing predicted names with actual scorer names.
    Handles partial matches, different formats (e.g. 'A.Jones' vs 'Aaron Jones').
    """
    if not pred or not actual: return False
    # Normalize basic
    pred = pred.lower().strip()
    actual = actual.lower().strip()
    
    if pred == actual: return True
    
    # Remove suffixes for cleaner split (Jr, Sr, III, etc)
    suffixes = [' jr', ' sr', ' iii', ' ii', ' iv']
    for s in suffixes:
        pred = pred.replace(s, '')
        actual = actual.replace(s, '')

    # Tokenize: replace dots with spaces to handle "A.Jones" -> "a jones"
    p_parts = pred.replace('.', ' ').split()
    a_parts = actual.replace('.', ' ').split()
    
    if not p_parts or not a_parts: return False
    
    # Check Last Name (last token) match
    if p_parts[-1] != a_parts[-1]:
        return False
        
    # Check First Initial match
    # comparing first char of first token
    if p_parts[0][0] != a_parts[0][0]:
        return False
        
    return True
