"""
Roster ingestion service.
Loads NFL rosters from nflreadpy and populates rosters table.
"""

import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Import nflreadpy
try:
    import nflreadpy as nfl
    HAS_NFLREADPY = True
except ImportError:
    HAS_NFLREADPY = False
    logger.warning("nflreadpy not available, roster sync disabled")


def sync_rosters(season: int) -> Dict[str, int]:
    """
    Load NFL rosters from nflreadpy and populate rosters table.
    
    Args:
        season: NFL season year (e.g., 2025)
    
    Returns:
        Dict with statistics: {'inserted': N, 'updated': N, 'errors': N}
    """
    if not HAS_NFLREADPY:
        logger.error("Cannot sync rosters: nflreadpy not installed")
        return {'inserted': 0, 'updated': 0, 'errors': 1}
    
    logger.info(f"Syncing rosters for season {season}")
    
    stats = {'inserted': 0, 'updated': 0, 'errors': 0}
    
    try:
        # Import here to avoid circular dependencies
        from database import get_db_connection
        
        # Load rosters from nflreadpy
        rosters_df = nfl.load_rosters(seasons=[int(season)]).to_pandas()
        logger.info(f"Loaded {len(rosters_df)} roster entries from nflreadpy")
        
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='rosters'"
        )
        if cursor.fetchone() is None:
            logger.error(
                "Roster sync skipped: 'rosters' table is missing. "
                "Run database migrations to create it."
            )
            conn.close()
            stats['errors'] += 1
            return stats
        
        for _, player in rosters_df.iterrows():
            try:
                player_name = player.get('full_name', '')
                team = player.get('team', '')
                position = player.get('position', 'Unknown')
                jersey = player.get('jersey_number')
                player_id = player.get('player_id')
                
                if not player_name or not team:
                    continue
                
                # Upsert into rosters table
                cursor.execute('''
                    INSERT OR REPLACE INTO rosters 
                    (season, player_name, team, position, jersey_number, nflreadpy_id, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (season, player_name, team, position, jersey, player_id))
                
                stats['inserted'] += 1
            
            except Exception as e:
                logger.error(f"Error syncing {player.get('full_name')}: {e}")
                stats['errors'] += 1
        
        conn.commit()
        conn.close()
        
        logger.info(f"Roster sync complete: {stats}")
        return stats
    
    except Exception as e:
        logger.error(f"Error loading rosters for {season}: {e}")
        stats['errors'] += 1
        return stats


def get_player_position(player_name: str, team: str, season: int) -> str:
    """
    Look up player position from rosters table.
    
    Args:
        player_name: Player name (e.g., "Patrick Mahomes")
        team: Team abbreviation (e.g., "KC")
        season: NFL season year
    
    Returns:
        Position (e.g., "QB") or "Unknown" if not found
    """
    try:
        from database import get_db_connection
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT position FROM rosters
            WHERE player_name = ? AND team = ? AND season = ?
            LIMIT 1
        ''', (player_name, team, season))
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else 'Unknown'
    
    except Exception as e:
        logger.error(f"Error looking up position for {player_name}: {e}")
        return 'Unknown'
