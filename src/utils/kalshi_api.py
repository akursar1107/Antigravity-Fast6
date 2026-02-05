"""
Kalshi API Integration
Fetch NFL First TD prediction market odds from Kalshi.

Kalshi is a regulated US prediction market exchange.
API Documentation: https://docs.kalshi.com

Public endpoints are available without authentication.
"""

import streamlit as st
import requests
import logging
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

from src import config
from src.utils.error_handling import log_exception, APIError
from src.utils.observability import log_event
from src.utils.resilience import CircuitBreakerOpen, get_circuit_breaker, request_with_retry

logger = logging.getLogger(__name__)

# Public API base URL (works without auth for market data)
PUBLIC_BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"


@dataclass
class KalshiMarket:
    """Represents a Kalshi market."""
    ticker: str
    title: str
    event_ticker: str
    yes_bid: float  # In cents
    yes_ask: float
    last_price: float
    volume: int
    close_time: Optional[datetime]
    status: str  # open, closed, settled
    result: Optional[str]  # yes, no (after settlement)
    subtitle: Optional[str] = None


class KalshiClient:
    """Client for Kalshi REST API."""

    # Series ticker for NFL First TD markets
    NFL_FIRST_TD_SERIES = "KXNFLFIRSTTD"

    def __init__(self, api_key: Optional[str] = None, cache_ttl: int = 3600):
        self.api_key = api_key
        self.cache_ttl = cache_ttl
        self.session = requests.Session()
        self.base_url = PUBLIC_BASE_URL

        # Set headers
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'
        self.session.headers.update(headers)

    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
        timeout: int = 30
    ) -> Optional[Dict]:
        """Make a GET request to the Kalshi API."""
        url = f"{self.base_url}/{endpoint}"
        try:
            request_start = time.perf_counter()
            log_event("api.kalshi.request", endpoint=endpoint)
            breaker = get_circuit_breaker(
                "kalshi",
                config.API_BREAKER_FAILURE_THRESHOLD,
                config.API_BREAKER_COOLDOWN_SECONDS,
            )
            response = request_with_retry(
                lambda: self.session.get(url, params=params, timeout=timeout),
                breaker=breaker,
                retries=config.API_RETRY_RETRIES,
                backoff_base=config.API_RETRY_BACKOFF_BASE,
                backoff_factor=config.API_RETRY_BACKOFF_FACTOR,
                jitter=config.API_RETRY_JITTER,
                retry_on_statuses=(429, 500, 502, 503, 504),
                get_status=lambda resp: getattr(resp, "status_code", None),
            )
            duration_ms = int((time.perf_counter() - request_start) * 1000)
            response.raise_for_status()
            log_event("api.kalshi.response", endpoint=endpoint, status_code=response.status_code, duration_ms=duration_ms)
            return response.json()
        except CircuitBreakerOpen:
            log_event("api.kalshi.error", endpoint=endpoint, error="circuit_open")
            return None
        except requests.exceptions.Timeout as e:
            duration_ms = int((time.perf_counter() - request_start) * 1000)
            log_event("api.kalshi.error", endpoint=endpoint, error=type(e).__name__, duration_ms=duration_ms)
            context = {"endpoint": endpoint, "timeout": timeout}
            log_exception(e, "kalshi_api_timeout", context, severity="warning")
            return None
        except requests.exceptions.HTTPError as e:
            duration_ms = int((time.perf_counter() - request_start) * 1000)
            log_event("api.kalshi.response", endpoint=endpoint, status_code=getattr(e.response, 'status_code', 'unknown'), duration_ms=duration_ms)
            context = {"endpoint": endpoint, "status_code": getattr(e.response, 'status_code', 'unknown')}
            log_exception(e, "kalshi_api_http_error", context, severity="warning")
            return None
        except requests.exceptions.RequestException as e:
            duration_ms = int((time.perf_counter() - request_start) * 1000)
            log_event("api.kalshi.error", endpoint=endpoint, error=type(e).__name__, duration_ms=duration_ms)
            context = {"endpoint": endpoint, "url": url}
            log_exception(e, "kalshi_api_request_error", context, severity="warning")
            return None
        except ValueError as e:
            duration_ms = int((time.perf_counter() - request_start) * 1000)
            log_event("api.kalshi.error", endpoint=endpoint, error=type(e).__name__, duration_ms=duration_ms)
            context = {"endpoint": endpoint}
            log_exception(e, "kalshi_api_json_decode_error", context, severity="warning")
            return None

    def get_markets(
        self,
        status: Optional[str] = None,
        tickers: Optional[List[str]] = None,
        limit: int = 100,
        cursor: Optional[str] = None
    ) -> Tuple[List[Dict], Optional[str]]:
        """
        Get markets from Kalshi.

        Args:
            status: Filter by status (unopened, open, closed, settled)
            tickers: Filter by specific tickers
            limit: Number of results per page (1-1000)
            cursor: Pagination cursor

        Returns:
            Tuple of (list of market dicts, next cursor or None)
        """
        params = {'limit': limit}
        if status:
            params['status'] = status
        if tickers:
            params['tickers'] = ','.join(tickers)
        if cursor:
            params['cursor'] = cursor

        data = self._make_request('markets', params)
        if not data:
            return [], None

        markets = data.get('markets', [])
        next_cursor = data.get('cursor')
        return markets, next_cursor

    def get_market(self, ticker: str) -> Optional[Dict]:
        """Get a specific market by ticker."""
        data = self._make_request(f'markets/{ticker}')
        return data.get('market') if data else None

    def search_nfl_first_td_markets(
        self,
        status: str = "open"
    ) -> List[KalshiMarket]:
        """
        Search for NFL First TD markets.

        Kalshi has confirmed NFL player prop bets including:
        - First TD scorer
        - Next TD scorer
        - Anytime TD scorer
        """
        markets = []
        cursor = None

        # Keywords to identify first TD markets
        first_td_keywords = ['first touchdown', 'first td', '1st td', 'first to score']

        while True:
            batch, cursor = self.get_markets(status=status, limit=200, cursor=cursor)
            if not batch:
                break

            for m in batch:
                title = (m.get('title') or '').lower()
                subtitle = (m.get('subtitle') or '').lower()
                event_ticker = (m.get('event_ticker') or '').lower()

                # Check if it's an NFL first TD market
                is_nfl = 'nfl' in event_ticker or 'football' in event_ticker
                is_first_td = any(kw in title or kw in subtitle for kw in first_td_keywords)

                if is_nfl and is_first_td:
                    close_time = None
                    if m.get('close_time'):
                        try:
                            close_time = datetime.fromisoformat(
                                m['close_time'].replace('Z', '+00:00')
                            )
                        except (ValueError, TypeError):
                            pass

                    markets.append(KalshiMarket(
                        ticker=m.get('ticker', ''),
                        title=m.get('title', ''),
                        event_ticker=m.get('event_ticker', ''),
                        yes_bid=m.get('yes_bid', 0),
                        yes_ask=m.get('yes_ask', 0),
                        last_price=m.get('last_price', 0),
                        volume=m.get('volume', 0),
                        close_time=close_time,
                        status=m.get('status', ''),
                        result=m.get('result'),
                        subtitle=m.get('subtitle')
                    ))

            # Stop if no more pages
            if not cursor:
                break

        logger.info(f"Found {len(markets)} NFL first TD markets on Kalshi")
        return markets

    def get_market_candlesticks(
        self,
        ticker: str,
        start_ts: Optional[int] = None,
        end_ts: Optional[int] = None,
        period_interval: int = 60  # 1-min (60), 1-hour (3600), 1-day (86400)
    ) -> List[Dict]:
        """
        Get historical price candlestick data.

        Args:
            ticker: Market ticker
            start_ts: Start timestamp (Unix seconds)
            end_ts: End timestamp (Unix seconds)
            period_interval: Interval in seconds (60, 3600, or 86400)

        Returns:
            List of {timestamp, open, high, low, close, volume}
        """
        params = {'period_interval': period_interval}
        if start_ts:
            params['start_ts'] = start_ts
        if end_ts:
            params['end_ts'] = end_ts

        data = self._make_request(f'markets/{ticker}/candlesticks', params)
        if not data:
            return []

        return data.get('candlesticks', [])

    def get_trades(
        self,
        ticker: Optional[str] = None,
        limit: int = 100,
        cursor: Optional[str] = None
    ) -> Tuple[List[Dict], Optional[str]]:
        """Get recent trades, optionally filtered by ticker."""
        params = {'limit': limit}
        if ticker:
            params['ticker'] = ticker
        if cursor:
            params['cursor'] = cursor

        data = self._make_request('trades', params)
        if not data:
            return [], None

        return data.get('trades', []), data.get('cursor')

    def get_event(self, event_ticker: str) -> Optional[Dict]:
        """
        Get a specific event with all its markets.

        Args:
            event_ticker: The event ticker (e.g., KXNFLFIRSTTD-26FEB08SEANE)

        Returns:
            Dict with 'event' and 'markets' keys
        """
        data = self._make_request(f'events/{event_ticker}')
        return data

    def get_events(
        self,
        series_ticker: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        cursor: Optional[str] = None
    ) -> Tuple[List[Dict], Optional[str]]:
        """
        Get events, optionally filtered by series.

        Args:
            series_ticker: Filter by series (e.g., KXNFLFIRSTTD)
            status: Filter by status
            limit: Results per page
            cursor: Pagination cursor

        Returns:
            Tuple of (list of events, next cursor)
        """
        params = {'limit': limit}
        if series_ticker:
            params['series_ticker'] = series_ticker
        if status:
            params['status'] = status
        if cursor:
            params['cursor'] = cursor

        data = self._make_request('events', params)
        if not data:
            return [], None

        return data.get('events', []), data.get('cursor')

    def get_nfl_first_td_events(self, status: str = "open") -> List[Dict]:
        """
        Get all NFL First TD events.

        Returns:
            List of event dicts with their markets
        """
        events = []
        cursor = None

        while True:
            batch, cursor = self.get_events(
                series_ticker=self.NFL_FIRST_TD_SERIES,
                status=status,
                limit=100,
                cursor=cursor
            )

            if not batch:
                break

            # Fetch full event data with markets for each
            for event_summary in batch:
                event_ticker = event_summary.get('event_ticker')
                if event_ticker:
                    full_event = self.get_event(event_ticker)
                    if full_event:
                        events.append(full_event)

            if not cursor:
                break

        logger.info(f"Found {len(events)} NFL First TD events on Kalshi")
        return events


def probability_to_american_odds(prob: float) -> int:
    """Convert implied probability to American odds."""
    if prob <= 0 or prob >= 1:
        return 0
    if prob >= 0.5:
        return int(-100 * prob / (1 - prob))
    else:
        return int(100 * (1 - prob) / prob)


def cents_to_probability(cents: float) -> float:
    """Convert Kalshi price (in cents, 0-100) to probability (0-1)."""
    return cents / 100.0


def extract_player_from_title(title: str) -> Optional[str]:
    """
    Extract player name from Kalshi market title.

    Example titles:
    - "Patrick Mahomes: First TD Scorer"
    - "Will Travis Kelce score the first touchdown?"
    """
    # Try pattern: "Player Name: First TD"
    if ':' in title:
        parts = title.split(':')
        return parts[0].strip()

    # Try pattern: "Will Player Name score..."
    title_lower = title.lower()
    if title_lower.startswith('will '):
        # Remove "Will " and try to extract name before action words
        rest = title[5:]  # Remove "Will "
        action_words = ['score', 'get', 'have', 'be']
        for word in action_words:
            if word in rest.lower():
                idx = rest.lower().index(word)
                name = rest[:idx].strip()
                if name:
                    return name

    return None


def extract_teams_from_event(event_ticker: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract team abbreviations from event ticker.

    Example event tickers:
    - "NFL-KC-BUF-2025-01-26"
    - "KXNFL-KC-BUF"
    """
    # Try to find team abbreviations (2-3 uppercase letters)
    import re
    teams = re.findall(r'\b([A-Z]{2,3})\b', event_ticker.upper())

    # Filter out common non-team patterns
    non_teams = {'NFL', 'TD', 'KX', 'KXNFL'}
    teams = [t for t in teams if t not in non_teams]

    if len(teams) >= 2:
        return teams[0], teams[1]
    return None, None


def parse_event_subtitle(subtitle: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Parse team abbreviations from event subtitle.

    Example: "SEA at NE (Feb 8)" -> ("SEA", "NE")
    """
    if not subtitle:
        return None, None

    # Pattern: "AWAY at HOME (date)"
    import re
    match = re.match(r'(\w+)\s+at\s+(\w+)', subtitle)
    if match:
        return match.group(1).upper(), match.group(2).upper()

    return None, None


@st.cache_data(ttl=3600)
def get_kalshi_first_td_odds(
    week_start_date: str,
    week_end_date: str
) -> Dict[Tuple[str, str], Dict[str, Dict]]:
    """
    Fetch First TD odds from Kalshi for a given week.

    Uses the KXNFLFIRSTTD series to find NFL First TD events.

    Args:
        week_start_date: Start date (YYYY-MM-DD)
        week_end_date: End date (YYYY-MM-DD)

    Returns:
        Dict mapping (away_team, home_team) to {player_name: {price, probability, volume, ticker}}
    """
    if not config.KALSHI_ENABLED:
        logger.debug("Kalshi API disabled in config")
        return {}

    client = KalshiClient(api_key=config.KALSHI_API_KEY)

    # Get NFL First TD events
    events = client.get_nfl_first_td_events(status="open")

    if not events:
        logger.info("No NFL first TD events found on Kalshi")
        return {}

    # Filter by date range
    start_date = datetime.strptime(week_start_date, '%Y-%m-%d')
    end_date = datetime.strptime(week_end_date, '%Y-%m-%d') + timedelta(days=1)

    odds_data = {}

    for event_data in events:
        event = event_data.get('event', {})
        markets = event_data.get('markets', [])

        # Parse teams from subtitle (e.g., "SEA at NE (Feb 8)")
        subtitle = event.get('sub_title', '')
        away_team, home_team = parse_event_subtitle(subtitle)

        if not away_team or not home_team:
            logger.debug(f"Could not parse teams from: {subtitle}")
            continue

        game_key = (away_team, home_team)

        # Process each player market
        for market in markets:
            # Get player name from yes_sub_title
            player_name = market.get('yes_sub_title', '')
            if not player_name or player_name == 'No Touchdown':
                continue

            # Skip D/ST markets if desired (they're valid though)
            # if 'D/ST' in player_name:
            #     continue

            # Check if market is within date range based on expected expiration
            exp_time_str = market.get('expected_expiration_time')
            if exp_time_str:
                try:
                    exp_time = datetime.fromisoformat(exp_time_str.replace('Z', '+00:00'))
                    if not (start_date <= exp_time.replace(tzinfo=None) <= end_date):
                        continue
                except (ValueError, TypeError):
                    pass

            # Get prices (in cents)
            yes_ask = market.get('yes_ask', 0)
            yes_bid = market.get('yes_bid', 0)
            last_price = market.get('last_price', 0)

            # Use ask price for probability (what you'd pay)
            price_cents = yes_ask if yes_ask > 0 else last_price
            probability = cents_to_probability(price_cents)
            american_odds = probability_to_american_odds(probability)

            if game_key not in odds_data:
                odds_data[game_key] = {}

            odds_data[game_key][player_name] = {
                'price': price_cents,
                'implied_probability': probability,
                'american_odds': american_odds,
                'volume': market.get('volume', 0),
                'ticker': market.get('ticker', ''),
                'status': market.get('status', ''),
                'yes_bid': yes_bid,
                'yes_ask': yes_ask
            }

    logger.info(f"Fetched Kalshi odds for {len(odds_data)} games with {sum(len(v) for v in odds_data.values())} player markets")
    return odds_data


@st.cache_data(ttl=3600)
def get_kalshi_historical_odds(
    ticker: str,
    lookback_days: int = 7
) -> List[Dict]:
    """
    Get historical price data for a specific market.

    Args:
        ticker: Market ticker
        lookback_days: Number of days to look back

    Returns:
        List of {timestamp, price, volume} records
    """
    if not config.KALSHI_ENABLED:
        return []

    client = KalshiClient(api_key=config.KALSHI_API_KEY)

    end_ts = int(datetime.now().timestamp())
    start_ts = int((datetime.now() - timedelta(days=lookback_days)).timestamp())

    candlesticks = client.get_market_candlesticks(
        ticker,
        start_ts=start_ts,
        end_ts=end_ts,
        period_interval=3600  # 1-hour intervals
    )

    # Convert to simpler format
    result = []
    for c in candlesticks:
        result.append({
            'timestamp': datetime.fromtimestamp(c.get('start_ts', 0)),
            'price': c.get('close', 0),
            'volume': c.get('volume', 0),
            'high': c.get('high', 0),
            'low': c.get('low', 0)
        })

    return result
