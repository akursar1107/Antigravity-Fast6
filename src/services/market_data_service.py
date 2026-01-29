"""
Market Data Service
Orchestrates fetching, storing, and linking prediction market data.

Responsibilities:
- Fetch odds from enabled sources (Polymarket, Kalshi)
- Store snapshots to database
- Link results after games complete
- Provide analytics aggregations
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

import config
from utils.polymarket_api import (
    get_polymarket_first_td_odds,
    get_polymarket_odds_by_slug
)
from utils.kalshi_api import get_kalshi_first_td_odds
from utils.prediction_markets import (
    PredictionMarketAggregator,
    link_odds_to_first_td_results,
    get_enabled_sources
)
from database.market_odds import (
    add_market_odds_batch,
    get_market_odds_for_game,
    get_market_odds_for_week,
    get_latest_odds_snapshot,
    get_market_accuracy_stats
)

logger = logging.getLogger(__name__)


class MarketDataService:
    """
    Service for managing prediction market data workflow.

    Provides a high-level interface for:
    - Fetching odds from multiple sources
    - Storing historical snapshots
    - Linking to actual results
    - Analytics and comparison
    """

    def __init__(self):
        self.aggregator = PredictionMarketAggregator()
        self.enabled_sources = get_enabled_sources()

    def fetch_and_store_week_odds(
        self,
        season: int,
        week: int,
        week_start_date: str,
        week_end_date: str
    ) -> Dict[str, int]:
        """
        Fetch current odds for a week and store snapshot.

        Strategy:
        1. Fetch Kalshi odds first (good discovery API)
        2. Use game/player info from Kalshi to construct Polymarket slugs
        3. Fetch Polymarket odds using slug-based lookups

        Args:
            season: NFL season year
            week: Week number
            week_start_date: Start date (YYYY-MM-DD)
            week_end_date: End date (YYYY-MM-DD)

        Returns:
            {source: records_stored}
        """
        results = {}
        kalshi_odds = {}

        # Fetch Kalshi first (better discovery)
        if 'kalshi' in self.enabled_sources:
            try:
                kalshi_odds = get_kalshi_first_td_odds(
                    week_start_date, week_end_date
                )
                records = self._convert_to_records(
                    kalshi_odds, 'kalshi', season, week
                )
                stored = add_market_odds_batch(records)
                results['kalshi'] = stored
                logger.info(f"Stored {stored} Kalshi odds records")
            except Exception as e:
                logger.error(f"Failed to fetch Kalshi odds: {e}")
                results['kalshi'] = 0

        # Fetch Polymarket using slug-based approach
        if 'polymarket' in self.enabled_sources:
            try:
                polymarket_odds = {}

                # Use Kalshi data to know which games/players to look up
                if kalshi_odds:
                    polymarket_odds = self._fetch_polymarket_from_kalshi_data(
                        kalshi_odds, week_start_date, week_end_date
                    )
                else:
                    # Fallback to search-based approach
                    polymarket_odds = get_polymarket_first_td_odds(
                        week_start_date, week_end_date
                    )

                if polymarket_odds:
                    records = self._convert_to_records(
                        polymarket_odds, 'polymarket', season, week
                    )
                    stored = add_market_odds_batch(records)
                    results['polymarket'] = stored
                    logger.info(f"Stored {stored} Polymarket odds records")
                else:
                    results['polymarket'] = 0

            except Exception as e:
                logger.error(f"Failed to fetch Polymarket odds: {e}")
                results['polymarket'] = 0

        return results

    def _fetch_polymarket_from_kalshi_data(
        self,
        kalshi_odds: Dict,
        week_start_date: str,
        week_end_date: str
    ) -> Dict:
        """
        Fetch Polymarket odds using game/player info from Kalshi.

        Uses slug-based lookup: nfl-{away}-{home}-{date}-first-td-{player}
        """
        polymarket_odds = {}

        # Try multiple date candidates (Polymarket is date-sensitive)
        # Generate dates within the range
        start = datetime.strptime(week_start_date, '%Y-%m-%d')
        end = datetime.strptime(week_end_date, '%Y-%m-%d')

        # For regular weeks, try Sunday (most games) and Thursday/Monday
        date_candidates = []
        current = start
        while current <= end:
            date_candidates.append(current.strftime('%Y-%m-%d'))
            current += timedelta(days=1)

        for (away_team, home_team), player_odds in kalshi_odds.items():
            player_names = list(player_odds.keys())

            # Try each date candidate until we find matches
            for game_date_str in date_candidates:
                pm_odds = get_polymarket_odds_by_slug(
                    away_team=away_team,
                    home_team=home_team,
                    game_date=game_date_str,
                    player_names=player_names,
                    prop_type="first-td"
                )

                if pm_odds:
                    game_key = (away_team, home_team)
                    polymarket_odds[game_key] = pm_odds
                    logger.info(f"Found {len(pm_odds)} Polymarket odds for {away_team}@{home_team} on {game_date_str}")
                    break  # Found matches, stop trying other dates

        return polymarket_odds

    def get_odds_comparison_for_game(
        self,
        game_id: str,
        home_team: str,
        away_team: str
    ) -> Dict[str, Dict]:
        """
        Get odds comparison for a specific game from all sources.

        Returns:
            {player_name: {source: odds_data, ...}, ...}
        """
        # Get stored odds
        stored_odds = get_latest_odds_snapshot(game_id)

        # Organize by player
        by_player: Dict[str, Dict] = {}

        for player_name, odds_data in stored_odds.items():
            if player_name not in by_player:
                by_player[player_name] = {}

            source = odds_data.get('source', 'unknown')
            by_player[player_name][source] = {
                'implied_probability': odds_data.get('implied_probability', 0),
                'american_odds': odds_data.get('american_odds', 0),
                'volume': odds_data.get('volume'),
                'snapshot_time': odds_data.get('snapshot_time')
            }

        return by_player

    def link_week_results(self, season: int, week: int) -> Dict:
        """
        Link stored odds to actual TD results after games complete.

        Returns:
            Statistics about the linking process
        """
        return link_odds_to_first_td_results(season, week)

    def get_season_accuracy_stats(
        self,
        season: int,
        source: Optional[str] = None
    ) -> Dict:
        """
        Get accuracy statistics for market predictions.

        Returns:
            {total_games, favorites_correct, accuracy_rate, avg_winner_probability}
        """
        return get_market_accuracy_stats(season, source)

    def get_value_opportunities(
        self,
        season: int,
        week: int,
        threshold: float = 0.05
    ) -> List[Dict]:
        """
        Find players where prediction market odds differ significantly.

        These differences may represent value opportunities or market
        inefficiencies.

        Args:
            season: Season year
            week: Week number
            threshold: Minimum probability difference (default 5%)

        Returns:
            List of {player, game_id, source1, source2, prob_diff, ...}
        """
        opportunities = []

        week_odds = get_market_odds_for_week(season, week)

        # Group by game and player
        by_game_player: Dict[Tuple[str, str], List[Dict]] = {}

        for odds in week_odds:
            key = (odds['game_id'], odds['player_name'])
            if key not in by_game_player:
                by_game_player[key] = []
            by_game_player[key].append(odds)

        # Find significant differences
        for (game_id, player_name), odds_list in by_game_player.items():
            if len(odds_list) < 2:
                continue

            # Get unique sources
            sources = {}
            for o in odds_list:
                if o['source'] not in sources:
                    sources[o['source']] = o

            if len(sources) < 2:
                continue

            # Compare all pairs
            source_items = list(sources.items())
            for i, (s1, o1) in enumerate(source_items):
                for s2, o2 in source_items[i+1:]:
                    prob_diff = abs(
                        o1['implied_probability'] - o2['implied_probability']
                    )

                    if prob_diff >= threshold:
                        opportunities.append({
                            'game_id': game_id,
                            'player': player_name,
                            'source1': s1,
                            'source2': s2,
                            'prob1': o1['implied_probability'],
                            'prob2': o2['implied_probability'],
                            'prob_diff': prob_diff,
                            'odds1': o1.get('american_odds'),
                            'odds2': o2.get('american_odds')
                        })

        return sorted(opportunities, key=lambda x: x['prob_diff'], reverse=True)

    def _convert_to_records(
        self,
        odds_data: Dict,
        source: str,
        season: int,
        week: int
    ) -> List[Dict]:
        """Convert API response to database record format."""
        records = []
        snapshot_time = datetime.utcnow()

        for (team1, team2), player_odds in odds_data.items():
            # Construct game_id (format: YYYY_WK_TEAM1_TEAM2)
            game_id = f"{season}_{week:02d}_{team1}_{team2}"

            for player_name, odds_info in player_odds.items():
                records.append({
                    'source': source,
                    'game_id': game_id,
                    'season': season,
                    'week': week,
                    'player_name': player_name,
                    'team': odds_info.get('team'),
                    'implied_probability': odds_info.get('implied_probability', 0),
                    'american_odds': odds_info.get('american_odds'),
                    'raw_price': odds_info.get('price'),
                    'volume': odds_info.get('volume'),
                    'market_id': odds_info.get('market_id') or odds_info.get('ticker') or odds_info.get('condition_id'),
                    'snapshot_time': snapshot_time
                })

        return records


def get_week_dates(season: int, week: int) -> Tuple[str, str]:
    """
    Calculate start and end dates for an NFL week.

    NFL weeks typically run Thursday to Monday.
    Playoff weeks (18-22) have special handling.

    Returns:
        Tuple of (start_date, end_date) in YYYY-MM-DD format
    """
    from datetime import date

    # Super Bowl week (Week 22) - first Sunday in February of next year
    if week == 22:
        # Super Bowl is typically first Sunday in February
        # Give a wide range to catch all markets
        sb_year = season + 1
        return f"{sb_year}-02-01", f"{sb_year}-02-15"

    # Conference Championships (Week 21)
    if week == 21:
        sb_year = season + 1
        return f"{sb_year}-01-19", f"{sb_year}-01-26"

    # Divisional Round (Week 20)
    if week == 20:
        sb_year = season + 1
        return f"{sb_year}-01-11", f"{sb_year}-01-19"

    # Wild Card (Week 19)
    if week == 19:
        sb_year = season + 1
        return f"{sb_year}-01-04", f"{sb_year}-01-13"

    # Regular season week 18 (final week)
    if week == 18:
        sb_year = season + 1
        return f"{sb_year}-01-01", f"{sb_year}-01-06"

    # Regular season (weeks 1-17)
    # NFL season typically starts first Thursday after Labor Day
    if season >= 2025:
        season_start = date(season, 9, 4)
    else:
        season_start = date(season, 9, 1)

    # Each week is 7 days
    week_start = season_start + timedelta(days=(week - 1) * 7)
    week_end = week_start + timedelta(days=6)

    return week_start.strftime('%Y-%m-%d'), week_end.strftime('%Y-%m-%d')
