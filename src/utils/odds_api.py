"""
Odds API Integration
Fetch First TD odds from The Odds API service
"""

import streamlit as st
import requests
import logging
import os
import time
from typing import Dict, Tuple, Optional
from src import config
from src.utils.error_handling import log_exception, APIError, handle_exception
from src.utils.observability import log_event
from src.utils.resilience import CircuitBreakerOpen, get_circuit_breaker, request_with_retry

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
    
    from src.utils.team_utils import get_team_abbr
    
    # 1. Get Events
    events_url = f'{config.ODDS_API_BASE_URL}/sports/{config.ODDS_API_SPORT}/events?apiKey={api_key}'
    try:
        events_start = time.perf_counter()
        log_event("api.odds.events.request", endpoint="events")
        breaker = get_circuit_breaker(
            "odds_api",
            config.API_BREAKER_FAILURE_THRESHOLD,
            config.API_BREAKER_COOLDOWN_SECONDS,
        )
        r = request_with_retry(
            lambda: requests.get(events_url, timeout=30),
            breaker=breaker,
            retries=config.API_RETRY_RETRIES,
            backoff_base=config.API_RETRY_BACKOFF_BASE,
            backoff_factor=config.API_RETRY_BACKOFF_FACTOR,
            jitter=config.API_RETRY_JITTER,
            retry_on_statuses=(429, 500, 502, 503, 504),
            get_status=lambda resp: getattr(resp, "status_code", None),
        )
        events_duration = int((time.perf_counter() - events_start) * 1000)
        if r.status_code != 200:
            log_event("api.odds.events.response", endpoint="events", status_code=r.status_code, duration_ms=events_duration)
            context = {"endpoint": "events", "status_code": r.status_code}
            log_exception(Exception(r.text), "odds_api_events_fetch", context, severity="warning")
            st.error(f"❌ Error fetching events from Odds API. Please try again.")
            return {}
        events = r.json()
        log_event("api.odds.events.response", endpoint="events", status_code=r.status_code, duration_ms=events_duration, event_count=len(events))
    except CircuitBreakerOpen:
        log_event("api.odds.events.error", endpoint="events", error="circuit_open")
        st.error("⚠️ Odds API temporarily unavailable. Please try again shortly.")
        return {}
    except requests.exceptions.Timeout as e:
        events_duration = int((time.perf_counter() - events_start) * 1000)
        log_event("api.odds.events.error", endpoint="events", error=type(e).__name__, duration_ms=events_duration)
        log_exception(e, "odds_api_events_timeout", {"endpoint": "events"}, severity="warning")
        st.error("⏱️ Odds API request timed out. Please try again.")
        return {}
    except requests.exceptions.RequestException as e:
        events_duration = int((time.perf_counter() - events_start) * 1000)
        log_event("api.odds.events.error", endpoint="events", error=type(e).__name__, duration_ms=events_duration)
        log_exception(e, "odds_api_events_request_error", {"endpoint": "events"}, severity="warning")
        st.error("🔗 Network error connecting to Odds API. Please check your connection.")
        return {}
    except (ValueError, KeyError) as e:
        events_duration = int((time.perf_counter() - events_start) * 1000)
        log_event("api.odds.events.error", endpoint="events", error=type(e).__name__, duration_ms=events_duration)
        log_exception(e, "odds_api_events_parse_error", {"endpoint": "events"}, severity="warning")
        st.error("📋 Error parsing Odds API response. Please try again.")
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
            odds_start = time.perf_counter()
            log_event("api.odds.odds.request", event_id=event_id)
            breaker = get_circuit_breaker(
                "odds_api",
                config.API_BREAKER_FAILURE_THRESHOLD,
                config.API_BREAKER_COOLDOWN_SECONDS,
            )
            r_odds = request_with_retry(
                lambda: requests.get(odds_url, timeout=30),
                breaker=breaker,
                retries=config.API_RETRY_RETRIES,
                backoff_base=config.API_RETRY_BACKOFF_BASE,
                backoff_factor=config.API_RETRY_BACKOFF_FACTOR,
                jitter=config.API_RETRY_JITTER,
                retry_on_statuses=(429, 500, 502, 503, 504),
                get_status=lambda resp: getattr(resp, "status_code", None),
            )
            odds_duration = int((time.perf_counter() - odds_start) * 1000)
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
                log_event("api.odds.odds.response", event_id=event_id, status_code=r_odds.status_code, duration_ms=odds_duration, player_count=len(game_odds))

            else:
                # Log warning for failed odds request
                logger.warning(f"Failed to get odds for event {event_id}: HTTP {r_odds.status_code}")
                log_event("api.odds.odds.response", event_id=event_id, status_code=r_odds.status_code, duration_ms=odds_duration)
        except CircuitBreakerOpen:
            log_event("api.odds.odds.error", event_id=event_id, error="circuit_open")
        except requests.exceptions.Timeout as e:
            odds_duration = int((time.perf_counter() - odds_start) * 1000)
            log_event("api.odds.odds.error", event_id=event_id, error=type(e).__name__, duration_ms=odds_duration)
            context = {"event_id": event_id, "timeout": 30}
            log_exception(e, "odds_api_odds_timeout", context, severity="warning")
        except requests.exceptions.RequestException as e:
            odds_duration = int((time.perf_counter() - odds_start) * 1000)
            log_event("api.odds.odds.error", event_id=event_id, error=type(e).__name__, duration_ms=odds_duration)
            context = {"event_id": event_id}
            log_exception(e, "odds_api_odds_request_error", context, severity="warning")
        except (KeyError, ValueError) as e:
            odds_duration = int((time.perf_counter() - odds_start) * 1000)
            log_event("api.odds.odds.error", event_id=event_id, error=type(e).__name__, duration_ms=odds_duration)
            context = {"event_id": event_id, "error_type": type(e).__name__}
            log_exception(e, "odds_api_odds_parse_error", context, severity="warning")
        except Exception as e:
            odds_duration = int((time.perf_counter() - odds_start) * 1000)
            log_event("api.odds.odds.error", event_id=event_id, error=type(e).__name__, duration_ms=odds_duration)
            context = {"event_id": event_id}
            log_exception(e, "odds_api_odds_unexpected_error", context, severity="error")
            
    return odds_data
