"""
Polymarket API Integration
Fetch NFL First TD prediction market odds from Polymarket.

Polymarket is a crypto-based prediction market platform.
API Documentation: https://docs.polymarket.com

APIs:
- Gamma API (https://gamma-api.polymarket.com): Market discovery & metadata
- CLOB API (https://clob.polymarket.com): Current prices & orderbook
- Data API (https://data-api.polymarket.com): Historical price data

Public endpoints don't require authentication.
"""

import streamlit as st
import requests
import logging
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import json

import config
from utils.error_handling import log_exception, APIError
from utils.observability import log_event
from utils.resilience import CircuitBreakerOpen, get_circuit_breaker, request_with_retry

logger = logging.getLogger(__name__)


@dataclass
class PolymarketMarket:
    """Represents a Polymarket market."""
    condition_id: str
    question: str
    slug: str
    outcome_prices: List[float]  # [YES price, NO price]
    token_ids: List[str]
    volume: float
    end_date: Optional[datetime]
    active: bool
    closed: bool
    tags: List[str]
    event_slug: Optional[str] = None


def build_market_slug(
    away_team: str,
    home_team: str,
    game_date: str,
    player_name: str,
    prop_type: str = "first-td"
) -> str:
    """
    Build a Polymarket market slug from game/player info.

    Polymarket uses a predictable slug format for NFL player props:
    nfl-{away}-{home}-{YYYY-MM-DD}-{prop-type}-{player-name}

    Args:
        away_team: Away team abbreviation (e.g., "SEA")
        home_team: Home team abbreviation (e.g., "NE")
        game_date: Game date in YYYY-MM-DD format
        player_name: Player name (e.g., "Stefon Diggs")
        prop_type: Prop type ("first-td" or "anytime-td")

    Returns:
        Market slug string
    """
    # Normalize player name: lowercase, replace spaces with hyphens
    player_slug = player_name.lower().replace(' ', '-').replace('.', '').replace("'", '')

    # Build slug
    slug = f"nfl-{away_team.lower()}-{home_team.lower()}-{game_date}-{prop_type}-{player_slug}"

    return slug


class PolymarketClient:
    """Client for Polymarket APIs."""

    GAMMA_BASE_URL = "https://gamma-api.polymarket.com"
    CLOB_BASE_URL = "https://clob.polymarket.com"
    DATA_BASE_URL = "https://data-api.polymarket.com"

    def __init__(self, cache_ttl: int = 3600):
        self.cache_ttl = cache_ttl
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })

    def _make_request(
        self,
        base_url: str,
        endpoint: str,
        params: Optional[Dict] = None,
        timeout: int = 30
    ) -> Optional[Dict]:
        """Make a GET request to Polymarket APIs."""
        url = f"{base_url}/{endpoint}" if endpoint else base_url
        try:
            request_start = time.perf_counter()
            log_event("api.polymarket.request", endpoint=endpoint or "root")
            breaker = get_circuit_breaker(
                "polymarket",
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
            log_event("api.polymarket.response", endpoint=endpoint or "root", status_code=response.status_code, duration_ms=duration_ms)
            return response.json()
        except CircuitBreakerOpen:
            log_event("api.polymarket.error", endpoint=endpoint or "root", error="circuit_open")
            return None
        except requests.exceptions.Timeout:
            duration_ms = int((time.perf_counter() - request_start) * 1000)
            log_event("api.polymarket.error", endpoint=endpoint or "root", error="Timeout", duration_ms=duration_ms)
            logger.error(f"Timeout fetching {url}")
            return None
        except requests.exceptions.HTTPError as e:
            duration_ms = int((time.perf_counter() - request_start) * 1000)
            # 404 is expected for non-existent slugs, don't log as error
            if response.status_code == 404:
                logger.debug(f"Market not found: {url}")
            else:
                logger.error(f"HTTP error fetching {url}: {e}")
            log_event("api.polymarket.response", endpoint=endpoint or "root", status_code=response.status_code, duration_ms=duration_ms)
            return None
        except requests.exceptions.RequestException as e:
            duration_ms = int((time.perf_counter() - request_start) * 1000)
            log_event("api.polymarket.error", endpoint=endpoint or "root", error=type(e).__name__, duration_ms=duration_ms)
            logger.error(f"Request error fetching {url}: {e}")
            return None
        except ValueError as e:
            duration_ms = int((time.perf_counter() - request_start) * 1000)
            log_event("api.polymarket.error", endpoint=endpoint or "root", error=type(e).__name__, duration_ms=duration_ms)
            logger.error(f"JSON decode error for {url}: {e}")
            return None

    def get_market_by_slug(self, slug: str) -> Optional[Dict]:
        """
        Get market data by slug.

        This is the key method for the reverse-engineering approach:
        construct the slug from known game/player info, then fetch the market.

        Args:
            slug: Market slug (e.g., "nfl-sea-ne-2026-02-08-first-td-stefon-diggs")

        Returns:
            Market data dict with clobTokenIds, or None if not found
        """
        data = self._make_request(self.GAMMA_BASE_URL, f'markets/slug/{slug}')
        return data

    def get_sports_tags(self) -> List[Dict]:
        """Get available sports tags and metadata."""
        data = self._make_request(self.GAMMA_BASE_URL, 'sports')
        return data if isinstance(data, list) else []

    def get_all_tags(self) -> List[Dict]:
        """Get all available tags."""
        data = self._make_request(self.GAMMA_BASE_URL, 'tags')
        return data if isinstance(data, list) else []

    def get_markets(
        self,
        tag_id: Optional[int] = None,
        closed: bool = False,
        active: bool = True,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict]:
        """
        Get markets from Gamma API.

        Args:
            tag_id: Filter by tag ID (e.g., NFL tag)
            closed: Include closed markets
            active: Only active markets
            limit: Results per page
            offset: Pagination offset

        Returns:
            List of market dictionaries
        """
        params = {
            'limit': limit,
            'offset': offset,
            'closed': str(closed).lower(),
            'active': str(active).lower()
        }
        if tag_id:
            params['tag_id'] = tag_id

        data = self._make_request(self.GAMMA_BASE_URL, 'markets', params)
        return data if isinstance(data, list) else []

    def get_events(
        self,
        tag_id: Optional[int] = None,
        closed: bool = False,
        limit: int = 100,
        offset: int = 0,
        order: str = 'id',
        ascending: bool = False
    ) -> List[Dict]:
        """
        Get events from Gamma API.

        Events contain their associated markets, so this is efficient
        for bulk retrieval.
        """
        params = {
            'limit': limit,
            'offset': offset,
            'closed': str(closed).lower(),
            'order': order,
            'ascending': str(ascending).lower()
        }
        if tag_id:
            params['tag_id'] = tag_id

        data = self._make_request(self.GAMMA_BASE_URL, 'events', params)
        return data if isinstance(data, list) else []

    def search_text(self, query: str, limit: int = 50) -> List[Dict]:
        """Search markets by text query."""
        params = {'_q': query, '_limit': limit}
        data = self._make_request(self.GAMMA_BASE_URL, 'markets', params)
        return data if isinstance(data, list) else []

    def get_price_history(
        self,
        token_id: str,
        interval: str = "1h",
        fidelity: int = 1,
        start_ts: Optional[int] = None,
        end_ts: Optional[int] = None
    ) -> List[Dict]:
        """
        Get historical price data for a token.

        Endpoint: clob.polymarket.com/prices-history?interval=1h&market={tokenId}&fidelity=1

        Args:
            token_id: The token ID (from market's clobTokenIds)
            interval: Time interval ("1m", "5m", "1h", "1d")
            fidelity: Data fidelity level (1 = highest)
            start_ts: Start timestamp (Unix seconds)
            end_ts: End timestamp (Unix seconds)

        Returns:
            List of {t: timestamp, p: price} records
        """
        params = {
            'market': token_id,
            'interval': interval,
            'fidelity': fidelity
        }
        if start_ts:
            params['startTs'] = start_ts
        if end_ts:
            params['endTs'] = end_ts

        data = self._make_request(self.CLOB_BASE_URL, 'prices-history', params)

        # Response format: {"history": [{"t": timestamp, "p": price}, ...]}
        if data and isinstance(data, dict):
            return data.get('history', [])
        return []

    def search_nfl_first_td_markets(
        self,
        include_closed: bool = False
    ) -> List[PolymarketMarket]:
        """
        Search for NFL First TD markets.

        Searches using keywords since Polymarket may not have a specific
        NFL sports tag.
        """
        markets = []
        keywords = config.POLYMARKET_KEYWORDS

        # Search for each keyword
        seen_conditions = set()

        for keyword in keywords:
            results = self.search_text(f"NFL {keyword}", limit=100)

            for m in results:
                condition_id = m.get('conditionId', '')
                if not condition_id or condition_id in seen_conditions:
                    continue
                seen_conditions.add(condition_id)

                # Check if it's related to first TD
                question = (m.get('question') or '').lower()
                is_first_td = any(
                    kw.lower() in question
                    for kw in ['first touchdown', 'first td', '1st td', 'first to score']
                )

                if not is_first_td:
                    continue

                # Parse outcome prices (usually stringified JSON)
                outcome_prices = m.get('outcomePrices', [])
                if isinstance(outcome_prices, str):
                    try:
                        outcome_prices = json.loads(outcome_prices)
                    except (json.JSONDecodeError, TypeError):
                        outcome_prices = []

                # Parse token IDs
                token_ids = m.get('clobTokenIds', [])
                if isinstance(token_ids, str):
                    try:
                        token_ids = json.loads(token_ids)
                    except (json.JSONDecodeError, TypeError):
                        token_ids = []

                # Parse end date
                end_date = None
                end_date_str = m.get('endDate') or m.get('endDateIso')
                if end_date_str:
                    try:
                        end_date = datetime.fromisoformat(
                            end_date_str.replace('Z', '+00:00')
                        )
                    except (ValueError, TypeError):
                        pass

                # Get tags
                tags = []
                if m.get('tags'):
                    tags = [t.get('label', '') for t in m.get('tags', []) if t.get('label')]

                markets.append(PolymarketMarket(
                    condition_id=condition_id,
                    question=m.get('question', ''),
                    slug=m.get('slug', ''),
                    outcome_prices=[float(p) for p in outcome_prices] if outcome_prices else [],
                    token_ids=token_ids,
                    volume=float(m.get('volume', 0) or 0),
                    end_date=end_date,
                    active=m.get('active', False),
                    closed=m.get('closed', False),
                    tags=tags,
                    event_slug=m.get('eventSlug')
                ))

        if not include_closed:
            markets = [m for m in markets if not m.closed]

        logger.info(f"Found {len(markets)} NFL first TD markets on Polymarket")
        return markets


def probability_to_american_odds(prob: float) -> int:
    """Convert implied probability to American odds."""
    if prob <= 0 or prob >= 1:
        return 0
    if prob >= 0.5:
        return int(-100 * prob / (1 - prob))
    else:
        return int(100 * (1 - prob) / prob)


def extract_player_from_question(question: str) -> Optional[str]:
    """
    Extract player name from Polymarket market question.

    Example questions:
    - "Will Patrick Mahomes score the first TD in Chiefs vs Bills?"
    - "First touchdown scorer: Travis Kelce?"
    """
    question_lower = question.lower()

    # Pattern: "Will [Player] score..."
    if question_lower.startswith('will '):
        rest = question[5:]  # Remove "Will "
        action_words = ['score', 'get', 'have', 'be the']
        for word in action_words:
            if word in rest.lower():
                idx = rest.lower().index(word)
                name = rest[:idx].strip()
                if name:
                    return name

    # Pattern: "First touchdown scorer: [Player]?"
    if 'scorer:' in question_lower or 'scorer -' in question_lower:
        for sep in [':', '-']:
            if sep in question:
                parts = question.split(sep)
                if len(parts) >= 2:
                    name = parts[1].strip().rstrip('?')
                    if name:
                        return name

    # Pattern: "[Player] to score first TD"
    if 'to score' in question_lower:
        idx = question_lower.index('to score')
        name = question[:idx].strip()
        if name:
            return name

    return None


def extract_teams_from_question(question: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract team names/abbreviations from market question.

    Example: "...in Chiefs vs Bills game"
    """
    import re

    # Common patterns
    vs_patterns = [
        r'(\w+)\s+vs\.?\s+(\w+)',  # "Chiefs vs Bills"
        r'(\w+)\s+@\s+(\w+)',       # "Chiefs @ Bills"
        r'(\w+)\s+at\s+(\w+)',      # "Chiefs at Bills"
    ]

    for pattern in vs_patterns:
        match = re.search(pattern, question, re.IGNORECASE)
        if match:
            return match.group(1), match.group(2)

    return None, None


@st.cache_data(ttl=3600)
def get_polymarket_first_td_odds(
    week_start_date: str,
    week_end_date: str
) -> Dict[Tuple[str, str], Dict[str, Dict]]:
    """
    Fetch First TD odds from Polymarket for a given week.

    Args:
        week_start_date: Start date (YYYY-MM-DD)
        week_end_date: End date (YYYY-MM-DD)

    Returns:
        Dict mapping (team1, team2) to {player_name: {price, probability, volume, condition_id}}
    """
    if not config.POLYMARKET_ENABLED:
        logger.debug("Polymarket API disabled in config")
        return {}

    client = PolymarketClient(cache_ttl=config.POLYMARKET_CACHE_TTL)

    # Search for NFL first TD markets
    markets = client.search_nfl_first_td_markets(include_closed=False)

    if not markets:
        logger.info("No NFL first TD markets found on Polymarket")
        return {}

    # Filter by date range
    start_date = datetime.strptime(week_start_date, '%Y-%m-%d')
    end_date = datetime.strptime(week_end_date, '%Y-%m-%d') + timedelta(days=1)

    odds_data = {}

    for market in markets:
        # Check if market is within date range
        if market.end_date:
            if not (start_date <= market.end_date.replace(tzinfo=None) <= end_date):
                continue

        # Extract player name from question
        player_name = extract_player_from_question(market.question)
        if not player_name:
            continue

        # Extract teams from question
        team1, team2 = extract_teams_from_question(market.question)
        if not team1 or not team2:
            continue

        # Get YES price (probability of player scoring first TD)
        # outcome_prices is typically [YES_price, NO_price]
        if market.outcome_prices and len(market.outcome_prices) >= 1:
            yes_price = market.outcome_prices[0]
        else:
            yes_price = 0.5  # Default if no price available

        probability = yes_price  # Already a probability (0-1)
        american_odds = probability_to_american_odds(probability)

        game_key = (team1.upper(), team2.upper())
        if game_key not in odds_data:
            odds_data[game_key] = {}

        odds_data[game_key][player_name] = {
            'price': yes_price,
            'implied_probability': probability,
            'american_odds': american_odds,
            'volume': market.volume,
            'condition_id': market.condition_id,
            'slug': market.slug,
            'active': market.active
        }

    logger.info(f"Fetched Polymarket odds for {len(odds_data)} games")
    return odds_data


@st.cache_data(ttl=3600)
def get_polymarket_historical_odds(
    condition_id: str,
    token_id: str,
    lookback_days: int = 7
) -> List[Dict]:
    """
    Get historical price data for a specific market.

    Args:
        condition_id: Market condition ID
        token_id: Token ID for the YES outcome
        lookback_days: Number of days to look back

    Returns:
        List of {timestamp, price} records
    """
    if not config.POLYMARKET_ENABLED:
        return []

    client = PolymarketClient()

    start_ts = int((datetime.now() - timedelta(days=lookback_days)).timestamp())
    end_ts = int(datetime.now().timestamp())

    history = client.get_price_history(token_id, start_ts=start_ts, end_ts=end_ts)

    # Convert to simpler format
    result = []
    for h in history:
        timestamp = h.get('t') or h.get('timestamp')
        price = h.get('p') or h.get('price')
        if timestamp and price:
            if isinstance(timestamp, (int, float)):
                timestamp = datetime.fromtimestamp(timestamp)
            result.append({
                'timestamp': timestamp,
                'price': float(price)
            })

    return result


def get_polymarket_odds_by_slug(
    away_team: str,
    home_team: str,
    game_date: str,
    player_names: List[str],
    prop_type: str = "first-td"
) -> Dict[str, Dict]:
    """
    Fetch Polymarket odds for specific players using slug-based lookup.

    This uses the reverse-engineering approach:
    1. Build slug from known game/player info
    2. Fetch market by slug to get token IDs
    3. Current price is in the market data

    Args:
        away_team: Away team abbreviation (e.g., "SEA")
        home_team: Home team abbreviation (e.g., "NE")
        game_date: Game date in YYYY-MM-DD format
        player_names: List of player names to look up
        prop_type: "first-td" or "anytime-td"

    Returns:
        Dict mapping player_name to odds data
    """
    if not config.POLYMARKET_ENABLED:
        return {}

    client = PolymarketClient()
    results = {}

    for player_name in player_names:
        slug = build_market_slug(away_team, home_team, game_date, player_name, prop_type)
        market = client.get_market_by_slug(slug)

        if not market:
            logger.debug(f"No Polymarket market found for slug: {slug}")
            continue

        # Parse outcome prices
        outcome_prices = market.get('outcomePrices', [])
        if isinstance(outcome_prices, str):
            try:
                outcome_prices = json.loads(outcome_prices)
            except (json.JSONDecodeError, TypeError):
                outcome_prices = []

        # Parse token IDs (needed for price history)
        token_ids = market.get('clobTokenIds', [])
        if isinstance(token_ids, str):
            try:
                token_ids = json.loads(token_ids)
            except (json.JSONDecodeError, TypeError):
                token_ids = []

        # YES price is typically first element
        yes_price = float(outcome_prices[0]) if outcome_prices else 0
        probability = yes_price  # Already 0-1 scale
        american_odds = probability_to_american_odds(probability)

        results[player_name] = {
            'price': yes_price,
            'implied_probability': probability,
            'american_odds': american_odds,
            'volume': float(market.get('volume', 0) or 0),
            'condition_id': market.get('conditionId', ''),
            'slug': slug,
            'token_ids': token_ids,
            'active': market.get('active', False),
            'closed': market.get('closed', False)
        }

        logger.debug(f"Found Polymarket odds for {player_name}: {probability:.1%}")

    logger.info(f"Fetched Polymarket odds for {len(results)}/{len(player_names)} players")
    return results


def get_polymarket_price_history_for_player(
    away_team: str,
    home_team: str,
    game_date: str,
    player_name: str,
    lookback_days: int = 7,
    prop_type: str = "first-td"
) -> List[Dict]:
    """
    Get historical price data for a specific player's market.

    Args:
        away_team: Away team abbreviation
        home_team: Home team abbreviation
        game_date: Game date (YYYY-MM-DD)
        player_name: Player name
        lookback_days: Days of history to fetch
        prop_type: "first-td" or "anytime-td"

    Returns:
        List of {timestamp, price} records
    """
    if not config.POLYMARKET_ENABLED:
        return []

    client = PolymarketClient()

    # Build slug and fetch market
    slug = build_market_slug(away_team, home_team, game_date, player_name, prop_type)
    market = client.get_market_by_slug(slug)

    if not market:
        logger.debug(f"No market found for price history: {slug}")
        return []

    # Get token IDs
    token_ids = market.get('clobTokenIds', [])
    if isinstance(token_ids, str):
        try:
            token_ids = json.loads(token_ids)
        except (json.JSONDecodeError, TypeError):
            return []

    if not token_ids:
        return []

    # First token is YES outcome
    yes_token_id = token_ids[0]

    # Fetch price history
    start_ts = int((datetime.now() - timedelta(days=lookback_days)).timestamp())
    end_ts = int(datetime.now().timestamp())

    history = client.get_price_history(yes_token_id, start_ts=start_ts, end_ts=end_ts)

    # Convert to standard format
    result = []
    for h in history:
        ts = h.get('t')
        price = h.get('p')
        if ts and price:
            result.append({
                'timestamp': datetime.fromtimestamp(ts) if isinstance(ts, (int, float)) else ts,
                'price': float(price)
            })

    return result
