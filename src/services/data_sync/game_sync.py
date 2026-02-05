"""
Game sync service.
Loads NFL game schedule and populates games table.
"""

import logging
from typing import Dict, Optional
import pandas as pd

logger = logging.getLogger(__name__)

# Import nflreadpy
try:
    import nflreadpy as nfl
    HAS_NFLREADPY = True
except ImportError:
    HAS_NFLREADPY = False
    logger.warning("nflreadpy not available, game sync disabled")

# Import streamlit for caching
try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False


def sync_games_for_season(season: int) -> Dict[str, int]:
    """
    Load NFL games from nflreadpy and populate games table.
    
    Args:
        season: NFL season year (e.g., 2025)
    
    Returns:
        Dict with statistics: {'inserted': N, 'errors': N}
    """
    if not HAS_NFLREADPY:
        logger.error("Cannot sync games: nflreadpy not installed")
        return {'inserted': 0, 'errors': 1}
    
    logger.info(f"Syncing games for season {season}")
    
    stats = {'inserted': 0, 'errors': 0}
    
    try:
        # Import here to avoid circular dependencies
        from database import get_db_connection
        
        # Load schedule from nflreadpy
        schedule_df = nfl.load_schedules(seasons=[int(season)]).to_pandas()
        logger.info(f"Loaded {len(schedule_df)} games from nflreadpy")
        
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='games'"
        )
        if cursor.fetchone() is None:
            logger.error(
                "Game sync skipped: 'games' table is missing. "
                "Run database migrations to create it."
            )
            conn.close()
            stats['errors'] += 1
            return stats
        
        for _, game in schedule_df.iterrows():
            try:
                game_id = game.get('game_id', '')
                week = game.get('week')
                gameday = game.get('gameday')
                home_team = game.get('home_team', '')
                away_team = game.get('away_team', '')
                home_score = game.get('home_score')
                away_score = game.get('away_score')
                
                # Determine game status
                if pd.isna(home_score) or pd.isna(away_score):
                    status = 'scheduled'
                else:
                    status = 'final'
                
                if not game_id or not home_team or not away_team:
                    continue
                
                # Insert into games table
                cursor.execute('''
                    INSERT OR REPLACE INTO games
                    (id, season, week, game_date, home_team, away_team, 
                     home_score, away_score, status, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (game_id, season, week, gameday, home_team, away_team,
                      home_score if not pd.isna(home_score) else None,
                      away_score if not pd.isna(away_score) else None,
                      status))
                
                stats['inserted'] += 1
            
            except Exception as e:
                logger.error(f"Error syncing game {game.get('game_id')}: {e}")
                stats['errors'] += 1
        
        conn.commit()
        conn.close()
        
        logger.info(f"Game sync complete: {stats}")
        return stats
    
    except Exception as e:
        logger.error(f"Error loading games for {season}: {e}")
        stats['errors'] += 1
        return stats


def get_game_id(season: int, week: int, home_team: str, away_team: str) -> Optional[str]:
    """
    Look up game_id from games table.
    
    Args:
        season: NFL season year
        week: NFL week number
        home_team: Home team abbreviation
        away_team: Away team abbreviation
    
    Returns:
        Game ID (e.g., "2025_01_KC_LV") or None if not found
    """
    try:
        from database import get_db_connection
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id FROM games
            WHERE season = ? AND week = ? AND home_team = ? AND away_team = ?
            LIMIT 1
        ''', (season, week, home_team, away_team))
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else None
    
    except Exception as e:
        logger.error(f"Error looking up game: {e}")
        return None


# Streamlit cached version if available
if HAS_STREAMLIT:
    sync_games_for_season = st.cache_data(ttl=3600)(sync_games_for_season)
