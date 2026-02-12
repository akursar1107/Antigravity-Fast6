"""
ELO Rating System Service

Implements ELO-based team strength ratings including:
- Overall team ELO ratings
- Offensive and defensive ratings
- Weekly rating updates
- Power rankings
- Matchup difficulty assessment
- Rating trends (rising/falling/stable)

Usage:
    from backend.services.elo_rating_service import update_team_ratings, get_power_rankings
    
    # Update ratings after game results
    update_team_ratings(season=2025, week=1)
    
    # Get current power rankings
    rankings = get_power_rankings(season=2025, week=5)
"""

import sqlite3
import pandas as pd
import numpy as np
from typing import Optional, Dict, List, Tuple
from backend.database import get_db_context
from backend.analytics.nfl_data import load_data, get_game_schedule
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# ELO Configuration
K_FACTOR = 25  # Sensitivity to game results (higher = more volatile)
INITIAL_RATING = 1500  # Starting rating for all teams
HOME_ADVANTAGE = 50  # Points added to home team
REVERSION_RATE = 0.3  # Regression to mean between seasons


def calculate_expected_score(rating_a: float, rating_b: float) -> float:
    """
    Calculate expected score for team A against team B.
    Returns value between 0 and 1 (probability of winning).
    
    Args:
        rating_a: Team A's ELO rating
        rating_b: Team B's ELO rating
    
    Returns:
        Expected score (0-1)
    """
    return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))


def update_elo_rating(
    rating: float,
    expected: float,
    actual: float,
    k_factor: float = K_FACTOR
) -> float:
    """
    Update ELO rating based on game result.
    
    Args:
        rating: Current ELO rating
        expected: Expected score (0-1)
        actual: Actual score (1 for win, 0.5 for tie, 0 for loss)
        k_factor: K-factor for update sensitivity
    
    Returns:
        New ELO rating
    """
    return rating + k_factor * (actual - expected)


def initialize_team_ratings(season: int, week: int = 1) -> None:
    """
    Initialize ELO ratings for all teams at start of season.
    If previous season exists, regress ratings toward mean.
    
    Args:
        season: NFL season
        week: Week number (default 1)
    """
    with get_db_context() as conn:
        cursor = conn.cursor()
        
        # Check if ratings already exist for this season/week
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM team_ratings
            WHERE season = ? AND week = ?
        """, (season, week))
        
        if cursor.fetchone()['count'] > 0:
            logger.info(f"Ratings already initialized for {season} Week {week}")
            return
        
        # Get previous season's final ratings
        cursor.execute("""
            SELECT team, elo_rating
            FROM team_ratings
            WHERE season = ?
            ORDER BY week DESC
            LIMIT 32
        """, (season - 1,))
        
        prev_ratings = {row['team']: row['elo_rating'] for row in cursor.fetchall()}
        
        # Initialize ratings for all 32 teams
        import backend.config
        teams = list(config.TEAM_MAP.keys())
        
        for team in teams:
            # Regress previous rating toward mean, or use initial rating
            if team in prev_ratings:
                new_rating = INITIAL_RATING + REVERSION_RATE * (prev_ratings[team] - INITIAL_RATING)
            else:
                new_rating = INITIAL_RATING
            
            cursor.execute("""
                INSERT INTO team_ratings (
                    team, season, week, elo_rating, 
                    offensive_rating, defensive_rating,
                    games_played, wins, losses, 
                    points_for, points_against, rating_trend
                ) VALUES (?, ?, ?, ?, ?, ?, 0, 0, 0, 0, 0, 'STABLE')
            """, (team, season, week, new_rating, INITIAL_RATING, INITIAL_RATING))
        
        conn.commit()
        logger.info(f"Initialized ratings for {len(teams)} teams in {season} Week {week}")


def update_team_ratings(season: int, week: int) -> Dict[str, int]:
    """
    Update team ELO ratings based on game results for a specific week.
    
    Args:
        season: NFL season
        week: Week number to process
    
    Returns:
        Dict with update statistics
    """
    stats = {'games_processed': 0, 'ratings_updated': 0, 'errors': 0}
    
    try:
        # Load game data
        df = load_data(season)
        
        if df.empty:
            logger.warning(f"No data available for season {season}")
            return stats
        
        # Filter to completed games for this week
        week_df = df[
            (df['week'] == week) &
            (df['game_seconds_remaining'] == 0)  # Game completed
        ].copy()
        
        if week_df.empty:
            logger.warning(f"No completed games found for {season} Week {week}")
            return stats
        
        # Get final scores by game
        game_results = week_df.groupby('game_id').agg({
            'home_team': 'first',
            'away_team': 'first',
            'home_score': 'last',
            'away_score': 'last'
        }).reset_index()
        
        with get_db_context() as conn:
            cursor = conn.cursor()
            
            # Ensure previous week's ratings exist
            if week == 1:
                initialize_team_ratings(season, week)
            
            # Get current ratings (from previous week or initialization)
            prev_week = week - 1 if week > 1 else week
            cursor.execute("""
                SELECT team, elo_rating, offensive_rating, defensive_rating,
                       games_played, wins, losses, points_for, points_against
                FROM team_ratings
                WHERE season = ? AND week = ?
            """, (season, prev_week))
            
            ratings = {
                row['team']: {
                    'elo': row['elo_rating'],
                    'off': row['offensive_rating'],
                    'def': row['defensive_rating'],
                    'games': row['games_played'],
                    'wins': row['wins'],
                    'losses': row['losses'],
                    'pf': row['points_for'],
                    'pa': row['points_against']
                }
                for row in cursor.fetchall()
            }
            
            # Process each game
            for _, game in game_results.iterrows():
                home_team = game['home_team']
                away_team = game['away_team']
                home_score = game['home_score']
                away_score = game['away_score']
                
                if home_team not in ratings or away_team not in ratings:
                    logger.warning(f"Missing ratings for {home_team} vs {away_team}")
                    continue
                
                # Get current ratings
                home_rating = ratings[home_team]['elo']
                away_rating = ratings[away_team]['elo']
                
                # Calculate expected scores (with home advantage)
                home_expected = calculate_expected_score(
                    home_rating + HOME_ADVANTAGE,
                    away_rating
                )
                away_expected = 1 - home_expected
                
                # Determine actual scores (1 for win, 0.5 for tie, 0 for loss)
                if home_score > away_score:
                    home_actual, away_actual = 1.0, 0.0
                    home_win, away_win = 1, 0
                elif away_score > home_score:
                    home_actual, away_actual = 0.0, 1.0
                    home_win, away_win = 0, 1
                else:
                    home_actual, away_actual = 0.5, 0.5
                    home_win, away_win = 0, 0
                
                # Update ELO ratings
                new_home_rating = update_elo_rating(home_rating, home_expected, home_actual)
                new_away_rating = update_elo_rating(away_rating, away_expected, away_actual)
                
                # Update offensive/defensive ratings (simplified)
                home_off_rating = ratings[home_team]['off'] + (home_score - 24) * 2
                away_off_rating = ratings[away_team]['off'] + (away_score - 24) * 2
                home_def_rating = ratings[home_team]['def'] - (away_score - 24) * 2
                away_def_rating = ratings[away_team]['def'] - (home_score - 24) * 2
                
                # Update stats
                ratings[home_team].update({
                    'elo': new_home_rating,
                    'off': home_off_rating,
                    'def': home_def_rating,
                    'games': ratings[home_team]['games'] + 1,
                    'wins': ratings[home_team]['wins'] + home_win,
                    'losses': ratings[home_team]['losses'] + (1 - home_win),
                    'pf': ratings[home_team]['pf'] + home_score,
                    'pa': ratings[home_team]['pa'] + away_score
                })
                
                ratings[away_team].update({
                    'elo': new_away_rating,
                    'off': away_off_rating,
                    'def': away_def_rating,
                    'games': ratings[away_team]['games'] + 1,
                    'wins': ratings[away_team]['wins'] + away_win,
                    'losses': ratings[away_team]['losses'] + (1 - away_win),
                    'pf': ratings[away_team]['pf'] + away_score,
                    'pa': ratings[away_team]['pa'] + home_score
                })
                
                stats['games_processed'] += 1
            
            # Calculate trends and save updated ratings
            for team, data in ratings.items():
                # Determine trend
                if week > 1:
                    cursor.execute("""
                        SELECT elo_rating
                        FROM team_ratings
                        WHERE team = ? AND season = ? AND week = ?
                    """, (team, season, week - 1))
                    prev = cursor.fetchone()
                    if prev:
                        diff = data['elo'] - prev['elo_rating']
                        if diff > 10:
                            trend = 'RISING'
                        elif diff < -10:
                            trend = 'FALLING'
                        else:
                            trend = 'STABLE'
                    else:
                        trend = 'STABLE'
                else:
                    trend = 'STABLE'
                
                # Insert new rating
                cursor.execute("""
                    INSERT INTO team_ratings (
                        team, season, week, elo_rating,
                        offensive_rating, defensive_rating,
                        games_played, wins, losses,
                        points_for, points_against, rating_trend
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    team, season, week, data['elo'],
                    data['off'], data['def'],
                    data['games'], data['wins'], data['losses'],
                    data['pf'], data['pa'], trend
                ))
                
                stats['ratings_updated'] += 1
            
            conn.commit()
            logger.info(f"Updated ratings for {stats['ratings_updated']} teams after {stats['games_processed']} games")
    
    except Exception as e:
        logger.error(f"Error updating team ratings: {e}")
        stats['errors'] = 1
    
    return stats


def get_power_rankings(season: int, week: Optional[int] = None) -> pd.DataFrame:
    """
    Get current power rankings for all teams.
    
    Args:
        season: NFL season
        week: Week number (None for latest)
    
    Returns:
        DataFrame with power rankings
    """
    with get_db_context() as conn:
        if week is None:
            # Get latest week
            cursor = conn.cursor()
            cursor.execute("""
                SELECT MAX(week) as max_week
                FROM team_ratings
                WHERE season = ?
            """, (season,))
            result = cursor.fetchone()
            week = result['max_week'] if result and result['max_week'] else 1
        
        query = """
            SELECT 
                team,
                elo_rating,
                offensive_rating,
                defensive_rating,
                games_played,
                wins,
                losses,
                points_for,
                points_against,
                rating_trend,
                RANK() OVER (ORDER BY elo_rating DESC) as power_rank
            FROM team_ratings
            WHERE season = ? AND week = ?
            ORDER BY elo_rating DESC
        """
        
        df = pd.read_sql_query(query, conn, params=(season, week))
        
        if not df.empty:
            df['win_pct'] = df['wins'] / df['games_played'].replace(0, 1)
            df['ppg'] = df['points_for'] / df['games_played'].replace(0, 1)
            df['papg'] = df['points_against'] / df['games_played'].replace(0, 1)
        
        return df


def get_team_rating_history(team: str, season: int) -> pd.DataFrame:
    """
    Get ELO rating history for a team over the season.
    
    Args:
        team: Team abbreviation
        season: NFL season
    
    Returns:
        DataFrame with weekly ratings
    """
    with get_db_context() as conn:
        query = """
            SELECT 
                week,
                elo_rating,
                offensive_rating,
                defensive_rating,
                wins,
                losses,
                rating_trend
            FROM team_ratings
            WHERE team = ? AND season = ?
            ORDER BY week
        """
        
        df = pd.read_sql_query(query, conn, params=(team, season))
        return df


def get_matchup_prediction(
    home_team: str,
    away_team: str,
    season: int,
    week: int
) -> Dict[str, any]:
    """
    Predict matchup outcome based on ELO ratings.
    
    Args:
        home_team: Home team abbreviation
        away_team: Away team abbreviation
        season: NFL season
        week: Week number
    
    Returns:
        Dict with prediction details
    """
    with get_db_context() as conn:
        cursor = conn.cursor()
        
        # Get current ratings
        cursor.execute("""
            SELECT team, elo_rating, offensive_rating, defensive_rating
            FROM team_ratings
            WHERE season = ? AND week = ? AND team IN (?, ?)
        """, (season, week, home_team, away_team))
        
        ratings = {row['team']: dict(row) for row in cursor.fetchall()}
        
        if home_team not in ratings or away_team not in ratings:
            return {
                'error': 'Ratings not available for one or both teams',
                'home_win_prob': 0.5,
                'away_win_prob': 0.5
            }
        
        # Calculate win probabilities
        home_rating = ratings[home_team]['elo_rating']
        away_rating = ratings[away_team]['elo_rating']
        
        home_win_prob = calculate_expected_score(
            home_rating + HOME_ADVANTAGE,
            away_rating
        )
        away_win_prob = 1 - home_win_prob
        
        # Estimate point spread (very simplified)
        rating_diff = (home_rating + HOME_ADVANTAGE) - away_rating
        estimated_spread = rating_diff / 25  # Rough conversion
        
        return {
            'home_team': home_team,
            'away_team': away_team,
            'home_rating': home_rating,
            'away_rating': away_rating,
            'home_win_prob': home_win_prob * 100,
            'away_win_prob': away_win_prob * 100,
            'estimated_spread': estimated_spread,
            'favorite': home_team if estimated_spread > 0 else away_team,
            'matchup_quality': abs(rating_diff)  # Closer to 0 = more competitive
        }


def get_strongest_weakest_teams(season: int, week: int, limit: int = 5) -> Dict[str, pd.DataFrame]:
    """
    Get strongest and weakest teams by ELO rating.
    
    Args:
        season: NFL season
        week: Week number
        limit: Number of teams to return
    
    Returns:
        Dict with 'strongest' and 'weakest' DataFrames
    """
    rankings = get_power_rankings(season, week)
    
    if rankings.empty:
        return {'strongest': pd.DataFrame(), 'weakest': pd.DataFrame()}
    
    return {
        'strongest': rankings.head(limit),
        'weakest': rankings.tail(limit)
    }


def get_rating_trend_emoji(trend: str) -> str:
    """Get emoji for rating trend."""
    trends = {
        'RISING': '📈',
        'FALLING': '📉',
        'STABLE': '→'
    }
    return trends.get(trend, '→')
