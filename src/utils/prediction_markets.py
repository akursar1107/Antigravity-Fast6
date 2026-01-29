"""
Unified Prediction Market Interface
Aggregates data from Polymarket and Kalshi with a common interface.
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

import config
from .polymarket_api import (
    PolymarketClient,
    get_polymarket_first_td_odds,
    probability_to_american_odds as pm_prob_to_odds
)
from .kalshi_api import (
    KalshiClient,
    get_kalshi_first_td_odds,
    probability_to_american_odds as kalshi_prob_to_odds
)

logger = logging.getLogger(__name__)


@dataclass
class MarketOddsRecord:
    """Unified market odds record from any source."""
    source: str  # "polymarket" or "kalshi"
    player_name: str
    implied_probability: float
    american_odds: int
    volume: Optional[float]
    last_update: datetime
    market_id: str  # Source-specific identifier (condition_id or ticker)
    raw_price: float  # Original price format
    team: Optional[str] = None


class PredictionMarketAggregator:
    """Aggregates prediction market data from multiple sources."""

    def __init__(self):
        self.enabled_sources = config.PREDICTION_MARKETS_ENABLED_SOURCES

        # Initialize clients if enabled
        self._polymarket_client = None
        self._kalshi_client = None

        if 'polymarket' in self.enabled_sources and config.POLYMARKET_ENABLED:
            self._polymarket_client = PolymarketClient()

        if 'kalshi' in self.enabled_sources and config.KALSHI_ENABLED:
            self._kalshi_client = KalshiClient(api_key=config.KALSHI_API_KEY)

    def get_first_td_odds(
        self,
        week_start_date: str,
        week_end_date: str,
        sources: Optional[List[str]] = None
    ) -> Dict[Tuple[str, str], List[MarketOddsRecord]]:
        """
        Get aggregated First TD odds from all configured sources.

        Args:
            week_start_date: Start date (YYYY-MM-DD)
            week_end_date: End date (YYYY-MM-DD)
            sources: List of sources to query (default: all enabled)

        Returns:
            Dict mapping (home_team, away_team) to list of MarketOddsRecord
        """
        if sources is None:
            sources = self.enabled_sources

        all_odds: Dict[Tuple[str, str], List[MarketOddsRecord]] = {}
        now = datetime.utcnow()

        # Fetch from Polymarket
        if 'polymarket' in sources and config.POLYMARKET_ENABLED:
            try:
                pm_odds = get_polymarket_first_td_odds(week_start_date, week_end_date)
                for game_key, players in pm_odds.items():
                    if game_key not in all_odds:
                        all_odds[game_key] = []

                    for player_name, odds_info in players.items():
                        all_odds[game_key].append(MarketOddsRecord(
                            source='polymarket',
                            player_name=player_name,
                            implied_probability=odds_info.get('implied_probability', 0),
                            american_odds=odds_info.get('american_odds', 0),
                            volume=odds_info.get('volume'),
                            last_update=now,
                            market_id=odds_info.get('condition_id', ''),
                            raw_price=odds_info.get('price', 0)
                        ))
            except Exception as e:
                logger.error(f"Error fetching Polymarket odds: {e}")

        # Fetch from Kalshi
        if 'kalshi' in sources and config.KALSHI_ENABLED:
            try:
                kalshi_odds = get_kalshi_first_td_odds(week_start_date, week_end_date)
                for game_key, players in kalshi_odds.items():
                    if game_key not in all_odds:
                        all_odds[game_key] = []

                    for player_name, odds_info in players.items():
                        all_odds[game_key].append(MarketOddsRecord(
                            source='kalshi',
                            player_name=player_name,
                            implied_probability=odds_info.get('implied_probability', 0),
                            american_odds=odds_info.get('american_odds', 0),
                            volume=odds_info.get('volume'),
                            last_update=now,
                            market_id=odds_info.get('ticker', ''),
                            raw_price=odds_info.get('price', 0)
                        ))
            except Exception as e:
                logger.error(f"Error fetching Kalshi odds: {e}")

        return all_odds

    def get_odds_for_game(
        self,
        home_team: str,
        away_team: str,
        week_start_date: str,
        week_end_date: str
    ) -> Dict[str, List[MarketOddsRecord]]:
        """
        Get odds for a specific game, grouped by player.

        Returns:
            {player_name: [MarketOddsRecord from each source]}
        """
        all_odds = self.get_first_td_odds(week_start_date, week_end_date)

        # Try both orderings of teams
        game_key = (home_team, away_team)
        alt_game_key = (away_team, home_team)

        records = all_odds.get(game_key, []) + all_odds.get(alt_game_key, [])

        # Group by player
        by_player: Dict[str, List[MarketOddsRecord]] = {}
        for record in records:
            if record.player_name not in by_player:
                by_player[record.player_name] = []
            by_player[record.player_name].append(record)

        return by_player

    @staticmethod
    def probability_to_american_odds(prob: float) -> int:
        """Convert implied probability to American odds."""
        if prob <= 0 or prob >= 1:
            return 0
        if prob >= 0.5:
            return int(-100 * prob / (1 - prob))
        else:
            return int(100 * (1 - prob) / prob)

    @staticmethod
    def american_to_probability(odds: int) -> float:
        """Convert American odds to implied probability."""
        if odds == 0:
            return 0.5
        if odds > 0:
            return 100 / (odds + 100)
        else:
            return abs(odds) / (abs(odds) + 100)

    @staticmethod
    def find_arbitrage_opportunities(
        odds_by_player: Dict[str, List[MarketOddsRecord]]
    ) -> List[Dict]:
        """
        Find potential arbitrage opportunities where prices differ significantly.

        Returns:
            List of {player, source1, source2, prob_diff, potential_edge}
        """
        opportunities = []

        for player_name, records in odds_by_player.items():
            if len(records) < 2:
                continue

            # Compare all pairs
            for i, r1 in enumerate(records):
                for r2 in records[i+1:]:
                    prob_diff = abs(r1.implied_probability - r2.implied_probability)

                    # Significant difference threshold (e.g., 5%)
                    if prob_diff > 0.05:
                        opportunities.append({
                            'player': player_name,
                            'source1': r1.source,
                            'source2': r2.source,
                            'prob1': r1.implied_probability,
                            'prob2': r2.implied_probability,
                            'prob_diff': prob_diff,
                            'potential_edge': prob_diff * 100  # As percentage
                        })

        return sorted(opportunities, key=lambda x: x['prob_diff'], reverse=True)


def link_odds_to_first_td_results(
    season: int,
    week: Optional[int] = None
) -> Dict[str, int]:
    """
    Link stored market odds to actual first TD results.

    Process:
    1. Get all games with market odds for the season/week
    2. For each game, get the actual first TD scorer from play-by-play
    3. Match player names using fuzzy matching
    4. Update market_outcomes with actual results
    5. Calculate accuracy metrics

    Returns:
        {
            games_processed: int,
            odds_linked: int,
            matches_found: int,
            accuracy_rate: float
        }
    """
    from database.market_odds import (
        get_market_odds_for_week,
        add_market_outcome,
        get_latest_odds_snapshot
    )

    try:
        from utils.name_matching import names_match
    except ImportError:
        # Fallback to simple matching
        def names_match(name1: str, name2: str, threshold: float = 0.75) -> bool:
            return name1.lower().strip() == name2.lower().strip()

    # Try to get first TD data from the grading module
    try:
        from utils.grading_logic import get_first_td_scorers
        first_td_map = get_first_td_scorers(season, week)
    except ImportError:
        logger.warning("grading_logic not available, skipping result linking")
        return {
            'games_processed': 0,
            'odds_linked': 0,
            'matches_found': 0,
            'favorites_correct': 0,
            'accuracy_rate': 0.0
        }

    stats = {
        'games_processed': 0,
        'odds_linked': 0,
        'matches_found': 0,
        'favorites_correct': 0
    }

    for game_id, first_td_info in first_td_map.items():
        actual_scorer = first_td_info.get('player')
        if not actual_scorer:
            continue

        stats['games_processed'] += 1

        # Get all odds for this game
        latest_odds = get_latest_odds_snapshot(game_id)

        if not latest_odds:
            continue

        # Find the favorite (highest implied probability)
        favorite_name = None
        favorite_prob = 0

        for player_name, odds_data in latest_odds.items():
            if odds_data['implied_probability'] > favorite_prob:
                favorite_prob = odds_data['implied_probability']
                favorite_name = player_name

        # Check each player's odds
        for player_name, odds_data in latest_odds.items():
            is_match = names_match(player_name, actual_scorer)

            add_market_outcome(
                source=odds_data['source'],
                game_id=game_id,
                market_id=odds_data.get('market_id', ''),
                player_name=player_name,
                resolved_outcome='yes' if is_match else 'no',
                actual_first_td_scorer=actual_scorer
            )

            stats['odds_linked'] += 1

            if is_match:
                stats['matches_found'] += 1
                if player_name == favorite_name:
                    stats['favorites_correct'] += 1

    if stats['games_processed'] > 0:
        stats['accuracy_rate'] = stats['favorites_correct'] / stats['games_processed']
    else:
        stats['accuracy_rate'] = 0.0

    return stats


def get_enabled_sources() -> List[str]:
    """Get list of enabled prediction market sources."""
    sources = []
    if 'polymarket' in config.PREDICTION_MARKETS_ENABLED_SOURCES and config.POLYMARKET_ENABLED:
        sources.append('polymarket')
    if 'kalshi' in config.PREDICTION_MARKETS_ENABLED_SOURCES and config.KALSHI_ENABLED:
        sources.append('kalshi')
    return sources


def test_connections() -> Dict[str, bool]:
    """Test connections to all enabled prediction market APIs."""
    results = {}

    if config.POLYMARKET_ENABLED:
        try:
            client = PolymarketClient()
            tags = client.get_all_tags()
            results['polymarket'] = len(tags) > 0
        except Exception as e:
            logger.error(f"Polymarket connection test failed: {e}")
            results['polymarket'] = False

    if config.KALSHI_ENABLED:
        try:
            client = KalshiClient()
            markets, _ = client.get_markets(limit=1)
            results['kalshi'] = len(markets) > 0
        except Exception as e:
            logger.error(f"Kalshi connection test failed: {e}")
            results['kalshi'] = False

    return results
