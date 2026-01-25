"""
Odds API Integration
Fetch First TD odds from The Odds API service
"""

import streamlit as st
import requests
import logging
import os
from typing import Dict, Tuple, Optional
import config

# Configure logging
logger = logging.getLogger(__name__)


def get_odds_api_key() -> Optional[str]:
    """
    Safely retrieve ODDS_API_KEY from st.secrets or environment.
    Returns None if not found (graceful degradation).
    """
    try:
        return st.secrets.get("ODDS_API_KEY") or os.getenv("ODDS_API_KEY")
    except (AttributeError, FileNotFoundError):
        return os.getenv("ODDS_API_KEY")


@st.cache_data(ttl=3600)
def get_first_td_odds(api_key: str, week_start_date: str, week_end_date: str) -> Dict[Tuple[str, str], Dict[str, float]]:
    """
    Fetches First TD odds from The Odds API.
    Matches games based on date window.
    
    Args:
        api_key: The Odds API key. If None or empty, returns empty dict (graceful degradation).
        week_start_date: Start date in YYYY-MM-DD format
        week_end_date: End date in YYYY-MM-DD format
        
    Returns:
        Dict mapping (home_team_abbr, away_team_abbr) to {player_name: odds_price}.
        Empty dict if api_key is unavailable.
    """
    if not api_key:
        logger.warning("ODDS_API_KEY not available; skipping odds fetch")
        return {}
    
    from utils.team_utils import get_team_abbr
    
    # 1. Get Events
    events_url = f'{config.ODDS_API_BASE_URL}/sports/{config.ODDS_API_SPORT}/events?apiKey={api_key}'
    try:
        r = requests.get(events_url)
        if r.status_code != 200:
            st.error(f"Error fetching events from Odds API: {r.text}")
            logger.error(f"Events API error: HTTP {r.status_code}: {r.text}")
            return {}
        events = r.json()
    except Exception as e:
        st.error(f"Error connecting to Odds API: {e}")
        logger.error(f"Failed to fetch events from Odds API: {e}")
        return {}

    # Filter events for the relevant week
    # We rely on 'commence_time' (ISO format).
    # Simple string comparison might be enough if dates are YYYY-MM-DD
    week_events = []
    
    # week_start_date and week_end_date expect 'YYYY-MM-DD' strings
    for e in events:
        c_time = e['commence_time']  # e.g. 2024-09-08T17:00:00Z
        c_date = c_time.split('T')[0]
        if week_start_date <= c_date <= week_end_date:
            week_events.append(e)

    logger.info(f"Found {len(week_events)} games for week {week_start_date} to {week_end_date}")
    odds_data = {}
    
    for e in week_events:
        event_id = e['id']
        # 2. Get Odds for event
        # Use market from config
        odds_url = f'{config.ODDS_API_BASE_URL}/sports/{config.ODDS_API_SPORT}/events/{event_id}/odds?apiKey={api_key}&regions={config.ODDS_API_REGIONS}&markets={config.ODDS_API_MARKET}&oddsFormat={config.ODDS_API_FORMAT}'
        
        try:
            r_odds = requests.get(odds_url)
            if r_odds.status_code == 200:
                data = r_odds.json()
                # Parse bookmakers
                # We'll take the first avail bookmaker for now
                bookmakers = data.get('bookmakers', [])
                game_odds = {}
                if bookmakers:
                    # Look for configured market
                    for bm in bookmakers:
                        for m in bm.get('markets', []):
                            if m['key'] == config.ODDS_API_MARKET:
                                for outcome in m['outcomes']:
                                    p_name = outcome['description']
                                    price = outcome['price']
                                    game_odds[p_name] = price
                                break  # Use first valid bookmaker
                        if game_odds:
                            break
                
                # Map to team abbreviations for matching with schedule
                h_team = get_team_abbr(e['home_team'])
                a_team = get_team_abbr(e['away_team'])
                odds_data[(h_team, a_team)] = game_odds
                logger.debug(f"Fetched {len(game_odds)} player odds for {h_team} vs {a_team}")

            else:
                # Log warning for failed odds request
                logger.warning(f"Failed to get odds for event {event_id}: HTTP {r_odds.status_code}")
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout fetching odds for event {event_id}: {e}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error fetching odds for event {event_id}: {e}")
        except (KeyError, ValueError) as e:
            logger.error(f"Error parsing odds data for event {event_id}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error processing event {event_id}: {e}")
            
    return odds_data
