"""
Team Utilities
Helper functions for team name and abbreviation mapping
"""

import config


def get_team_abbr(full_name: str) -> str:
    """
    Maps full team names (Odds API format) to abbreviations (nflreadpy format).
    
    Args:
        full_name: Full team name (e.g., "Kansas City Chiefs")
        
    Returns:
        Team abbreviation (e.g., "KC")
    """
    return config.TEAM_ABBR_MAP.get(full_name, full_name)


def get_team_full_name(abbr: str) -> str:
    """
    Maps abbreviation (nflreadpy format) to full team name (Odds API format).
    
    Args:
        abbr: Team abbreviation (e.g., "KC")
        
    Returns:
        Full team name (e.g., "Kansas City Chiefs")
    """
    for name, a in config.TEAM_ABBR_MAP.items():
        if a == abbr:
            return name
    return abbr


def backfill_team_for_picks(season: int) -> dict:
    """
    Auto-fix picks with team='Unknown' by looking up player teams from roster.
    
    Queries the database for picks with Unknown team, looks up each player
    in the NFL roster to find their team, then updates the pick record.
    
    Args:
        season: NFL season year to process picks for
        
    Returns:
        dict with keys:
            - 'updated': number of picks successfully updated
            - 'failed': number of picks that couldn't be resolved
            - 'duplicates': number of duplicate picks removed
            - 'error': error message if operation failed (optional)
            
    Example:
        >>> result = backfill_team_for_picks(2025)
        >>> print(f"Updated {result['updated']} picks")
    """
    import logging
    from .db_connection import get_db_connection
    from .nfl_data import get_rosters
    from fuzzywuzzy import fuzz
    
    logger = logging.getLogger(__name__)
    updated = 0
    failed = 0
    duplicates = 0
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all picks with Unknown team for this season
        cursor.execute("""
            SELECT p.id, p.player_name, p.team, u.name as user_name
            FROM picks p
            JOIN users u ON p.user_id = u.id
            WHERE p.season = ? AND p.team = 'Unknown'
            ORDER BY p.player_name
        """, (season,))
        
        unknown_picks = cursor.fetchall()
        
        if not unknown_picks:
            return {'updated': 0, 'failed': 0, 'duplicates': 0}
        
        # Load NFL rosters for team lookup
        rosters = get_rosters(season)
        
        for pick in unknown_picks:
            pick_id, player_name, _, user_name = pick
            
            # Search for player in rosters to find their team
            found_team = None
            best_match_ratio = 0
            
            for team_abbr, players in rosters.items():
                for roster_player in players:
                    # Get player full name from roster entry
                    roster_full_name = roster_player.get('full_name', '')
                    
                    # Use fuzzy matching to find player (handles nickname variations)
                    match_ratio = fuzz.ratio(player_name.lower(), roster_full_name.lower())
                    
                    if match_ratio > best_match_ratio:
                        best_match_ratio = match_ratio
                        found_team = team_abbr
            
            # Accept matches with >80% confidence
            if found_team and best_match_ratio >= 80:
                try:
                    cursor.execute(
                        "UPDATE picks SET team = ? WHERE id = ?",
                        (found_team, pick_id)
                    )
                    updated += 1
                except Exception as e:
                    logger.error(f"Failed to update pick {pick_id}: {e}")
                    failed += 1
            else:
                failed += 1
                logger.warning(f"Could not find team for {player_name} (user: {user_name})")
        
        # Remove duplicate picks (keep first, delete rest)
        cursor.execute("""
            SELECT id, user_id, week_id, COUNT(*) as count
            FROM picks
            WHERE season = ?
            GROUP BY user_id, week_id, player_name, team
            HAVING count > 1
        """, (season,))
        
        duplicate_groups = cursor.fetchall()
        for group in duplicate_groups:
            # Get all picks in this duplicate group and delete the later ones
            cursor.execute("""
                SELECT id FROM picks
                WHERE season = ? AND player_name = ?
                  AND user_id = ? AND week_id = ?
                ORDER BY created_at DESC
            """, (season, player_name, group[1], group[2]))
            
            picks_to_delete = cursor.fetchall()[1:]  # Keep first, delete rest
            for dup_pick in picks_to_delete:
                cursor.execute("DELETE FROM picks WHERE id = ?", (dup_pick[0],))
                duplicates += 1
        
        conn.commit()
        
        return {
            'updated': updated,
            'failed': failed,
            'duplicates': duplicates
        }
        
    except Exception as e:
        logger.error(f"Error backfilling teams: {e}")
        return {'error': str(e), 'updated': 0, 'failed': 0, 'duplicates': 0}
    finally:
        try:
            conn.close()
        except:
            pass
