"""
Prediction Market Odds Repository
CRUD operations for market_odds and market_outcomes tables.
Stores historical odds from Polymarket and Kalshi prediction markets.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

from .connection import get_db_context
from src.utils.types import MarketOdds

logger = logging.getLogger(__name__)


def add_market_odds_batch(records: List[Dict]) -> int:
    """
    Insert multiple market odds records in a batch.

    Args:
        records: List of dicts with keys:
            source, game_id, season, week, player_name, team,
            implied_probability, american_odds, raw_price, volume,
            market_id, snapshot_time

    Returns:
        Number of records inserted
    """
    if not records:
        return 0

    with get_db_context() as conn:
        cursor = conn.cursor()

        insert_data = [
            (
                r['source'],
                r['game_id'],
                r['season'],
                r['week'],
                r['player_name'],
                r.get('team'),
                r['implied_probability'],
                r.get('american_odds'),
                r.get('raw_price'),
                r.get('volume'),
                r.get('market_id'),
                r['snapshot_time']
            )
            for r in records
        ]

        cursor.executemany("""
            INSERT OR IGNORE INTO market_odds
            (source, game_id, season, week, player_name, team,
             implied_probability, american_odds, raw_price, volume,
             market_id, snapshot_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, insert_data)

        inserted = cursor.rowcount
        logger.info(f"Inserted {inserted} market odds records")
        return inserted


def add_market_odds(
    source: str,
    game_id: str,
    season: int,
    week: int,
    player_name: str,
    implied_probability: float,
    snapshot_time: datetime,
    team: Optional[str] = None,
    american_odds: Optional[int] = None,
    raw_price: Optional[float] = None,
    volume: Optional[float] = None,
    market_id: Optional[str] = None
) -> int:
    """Add a single market odds record."""
    with get_db_context() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO market_odds
            (source, game_id, season, week, player_name, team,
             implied_probability, american_odds, raw_price, volume,
             market_id, snapshot_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (source, game_id, season, week, player_name, team,
              implied_probability, american_odds, raw_price, volume,
              market_id, snapshot_time))
        return cursor.lastrowid


def get_market_odds_for_game(
    game_id: str,
    source: Optional[str] = None
) -> List[MarketOdds]:
    """Get all market odds for a specific game."""
    with get_db_context() as conn:
        cursor = conn.cursor()

        if source:
            cursor.execute("""
                SELECT * FROM market_odds
                WHERE game_id = ? AND source = ?
                ORDER BY snapshot_time DESC
            """, (game_id, source))
        else:
            cursor.execute("""
                SELECT * FROM market_odds
                WHERE game_id = ?
                ORDER BY source, snapshot_time DESC
            """, (game_id,))

        return [dict(row) for row in cursor.fetchall()]


def get_market_odds_for_player(
    player_name: str,
    season: int,
    week: Optional[int] = None
) -> List[MarketOdds]:
    """Get all market odds for a player across games."""
    with get_db_context() as conn:
        cursor = conn.cursor()

        if week:
            cursor.execute("""
                SELECT * FROM market_odds
                WHERE player_name = ? AND season = ? AND week = ?
                ORDER BY snapshot_time DESC
            """, (player_name, season, week))
        else:
            cursor.execute("""
                SELECT * FROM market_odds
                WHERE player_name = ? AND season = ?
                ORDER BY week, snapshot_time DESC
            """, (player_name, season))

        return [dict(row) for row in cursor.fetchall()]


def get_market_odds_for_week(
    season: int,
    week: int,
    source: Optional[str] = None
) -> List[MarketOdds]:
    """Get all market odds for a specific week."""
    with get_db_context() as conn:
        cursor = conn.cursor()

        if source:
            cursor.execute("""
                SELECT * FROM market_odds
                WHERE season = ? AND week = ? AND source = ?
                ORDER BY game_id, player_name, snapshot_time DESC
            """, (season, week, source))
        else:
            cursor.execute("""
                SELECT * FROM market_odds
                WHERE season = ? AND week = ?
                ORDER BY source, game_id, player_name, snapshot_time DESC
            """, (season, week))

        return [dict(row) for row in cursor.fetchall()]


def get_latest_odds_snapshot(
    game_id: str,
    source: Optional[str] = None
) -> Dict[str, Dict]:
    """
    Get the most recent odds for each player in a game.

    Returns:
        {player_name: {source, implied_probability, american_odds, ...}}
    """
    with get_db_context() as conn:
        cursor = conn.cursor()

        if source:
            cursor.execute("""
                SELECT mo.* FROM market_odds mo
                INNER JOIN (
                    SELECT player_name, MAX(snapshot_time) as max_time
                    FROM market_odds
                    WHERE game_id = ? AND source = ?
                    GROUP BY player_name
                ) latest ON mo.player_name = latest.player_name
                    AND mo.snapshot_time = latest.max_time
                WHERE mo.game_id = ? AND mo.source = ?
            """, (game_id, source, game_id, source))
        else:
            cursor.execute("""
                SELECT mo.* FROM market_odds mo
                INNER JOIN (
                    SELECT player_name, source, MAX(snapshot_time) as max_time
                    FROM market_odds
                    WHERE game_id = ?
                    GROUP BY player_name, source
                ) latest ON mo.player_name = latest.player_name
                    AND mo.source = latest.source
                    AND mo.snapshot_time = latest.max_time
                WHERE mo.game_id = ?
            """, (game_id, game_id))

        rows = cursor.fetchall()
        return {row['player_name']: dict(row) for row in rows}


def add_market_outcome(
    source: str,
    game_id: str,
    market_id: str,
    player_name: str,
    resolved_outcome: str,
    actual_first_td_scorer: Optional[str] = None,
    resolution_time: Optional[datetime] = None
) -> int:
    """Record a market outcome/resolution."""
    with get_db_context() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO market_outcomes
            (source, game_id, market_id, player_name, resolved_outcome,
             actual_first_td_scorer, resolution_time)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (source, game_id, market_id, player_name, resolved_outcome,
              actual_first_td_scorer, resolution_time))
        return cursor.lastrowid


def get_market_outcomes_for_game(game_id: str) -> List[Dict]:
    """Get all market outcomes for a specific game."""
    with get_db_context() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM market_outcomes
            WHERE game_id = ?
            ORDER BY source, player_name
        """, (game_id,))
        return [dict(row) for row in cursor.fetchall()]


def get_market_accuracy_stats(
    season: int,
    source: Optional[str] = None
) -> Dict:
    """
    Calculate accuracy statistics for market predictions.

    Returns:
        {
            total_games: int,
            favorites_correct: int,  # Market favorite scored first TD
            accuracy_rate: float,
            avg_winner_probability: float,
        }
    """
    with get_db_context() as conn:
        cursor = conn.cursor()

        # Get games where we have both odds and outcomes
        if source:
            cursor.execute("""
                SELECT DISTINCT mo.game_id, mo.actual_first_td_scorer
                FROM market_outcomes mo
                JOIN market_odds odds ON mo.game_id = odds.game_id AND mo.source = odds.source
                WHERE odds.season = ? AND mo.source = ? AND mo.actual_first_td_scorer IS NOT NULL
            """, (season, source))
        else:
            cursor.execute("""
                SELECT DISTINCT mo.game_id, mo.actual_first_td_scorer
                FROM market_outcomes mo
                JOIN market_odds odds ON mo.game_id = odds.game_id
                WHERE odds.season = ? AND mo.actual_first_td_scorer IS NOT NULL
            """, (season,))

        games = cursor.fetchall()

        total_games = len(games)
        favorites_correct = 0
        winner_probs = []

        for game in games:
            game_id = game['game_id']
            actual_scorer = game['actual_first_td_scorer']

            # Get the favorite (highest probability player) for this game
            cursor.execute("""
                SELECT player_name, implied_probability
                FROM market_odds
                WHERE game_id = ?
                ORDER BY implied_probability DESC
                LIMIT 1
            """, (game_id,))

            favorite = cursor.fetchone()
            if favorite:
                # Check if favorite was the actual scorer (fuzzy match would be better)
                if favorite['player_name'].lower() == actual_scorer.lower():
                    favorites_correct += 1

                # Get the actual winner's probability
                cursor.execute("""
                    SELECT implied_probability
                    FROM market_odds
                    WHERE game_id = ? AND LOWER(player_name) = LOWER(?)
                    ORDER BY snapshot_time DESC
                    LIMIT 1
                """, (game_id, actual_scorer))

                winner_odds = cursor.fetchone()
                if winner_odds:
                    winner_probs.append(winner_odds['implied_probability'])

        return {
            'total_games': total_games,
            'favorites_correct': favorites_correct,
            'accuracy_rate': favorites_correct / total_games if total_games > 0 else 0.0,
            'avg_winner_probability': sum(winner_probs) / len(winner_probs) if winner_probs else 0.0
        }


def get_odds_comparison(game_id: str) -> Dict[str, List[Dict]]:
    """
    Get odds from all sources for a game, grouped by player.

    Returns:
        {player_name: [{source, implied_probability, american_odds, ...}, ...]}
    """
    with get_db_context() as conn:
        cursor = conn.cursor()

        # Get latest odds per player per source
        cursor.execute("""
            SELECT mo.* FROM market_odds mo
            INNER JOIN (
                SELECT player_name, source, MAX(snapshot_time) as max_time
                FROM market_odds
                WHERE game_id = ?
                GROUP BY player_name, source
            ) latest ON mo.player_name = latest.player_name
                AND mo.source = latest.source
                AND mo.snapshot_time = latest.max_time
            WHERE mo.game_id = ?
            ORDER BY mo.player_name, mo.source
        """, (game_id, game_id))

        rows = cursor.fetchall()

        result = {}
        for row in rows:
            player = row['player_name']
            if player not in result:
                result[player] = []
            result[player].append(dict(row))

        return result


def delete_market_odds_for_game(game_id: str, source: Optional[str] = None) -> int:
    """Delete market odds for a game (useful for re-fetching)."""
    with get_db_context() as conn:
        cursor = conn.cursor()

        if source:
            cursor.execute(
                "DELETE FROM market_odds WHERE game_id = ? AND source = ?",
                (game_id, source)
            )
        else:
            cursor.execute(
                "DELETE FROM market_odds WHERE game_id = ?",
                (game_id,)
            )

        deleted = cursor.rowcount
        logger.info(f"Deleted {deleted} market odds records for game {game_id}")
        return deleted
