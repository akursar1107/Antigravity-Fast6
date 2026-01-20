"""
Grading Logic Module
Handles auto-grading of picks against actual play-by-play data.
"""

import logging
from typing import Dict, Optional
import pandas as pd
from utils.nfl_data import load_data, get_game_schedule, get_first_tds, get_touchdowns, load_rosters
from utils.name_matching import names_match
from utils import db_picks, db_stats
from utils.db_connection import get_db_connection, get_db_context
import config

logger = logging.getLogger(__name__)


def auto_grade_season(season: int, week: Optional[int] = None) -> Dict:
    """
    Automatically grade all ungraded picks for a season (or specific week) 
    against the actual play-by-play data.
    
    For each ungraded pick:
    - Checks if player scored the FIRST TD in the game (is_correct)
    - Checks if player scored ANY TD in the game (any_time_td)
    - Calculates actual return based on pick odds
    
    Args:
        season: NFL season year
        week: Optional specific week to grade (if None, grades entire season)
        
    Returns:
        Dict with grading summary
    """
    logger.info(f"Starting auto-grade for season {season}" + (f" week {week}" if week else ""))
    
    # Load data
    df = load_data(season)
    if df.empty:
        logger.warning(f"No play-by-play data found for season {season}")
        return {'error': 'No data found', 'graded_picks': 0}
    
    # Get first TDs and all TDs
    first_tds = get_first_tds(df)
    all_tds = get_touchdowns(df)
    
    if first_tds.empty:
        logger.warning(f"No first TD data found for season {season}")
        return {'error': 'No TD data found', 'graded_picks': 0}
    
    # Load rosters for name matching
    rosters = load_rosters(season)
    
    # Get ungraded picks
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if week:
        cursor.execute("""
            SELECT p.id, p.user_id, p.week_id, p.team, p.player_name, 
                   p.odds, p.theoretical_return, p.game_id, w.week, w.season
            FROM picks p
            JOIN weeks w ON p.week_id = w.id
            WHERE w.season = ? AND w.week = ?
            AND NOT EXISTS (SELECT 1 FROM results r WHERE r.pick_id = p.id)
            ORDER BY p.week_id, p.id
        """, (season, week))
    else:
        cursor.execute("""
            SELECT p.id, p.user_id, p.week_id, p.team, p.player_name, 
                   p.odds, p.theoretical_return, p.game_id, w.week, w.season
            FROM picks p
            JOIN weeks w ON p.week_id = w.id
            WHERE w.season = ?
            AND NOT EXISTS (SELECT 1 FROM results r WHERE r.pick_id = p.id)
            ORDER BY p.week_id, p.id
        """, (season,))
    
    ungraded_picks = cursor.fetchall()
    conn.close()
    
    if not ungraded_picks:
        logger.info(f"No ungraded picks found for season {season}")
        return {'graded_picks': 0, 'message': 'No ungraded picks'}
    
    logger.info(f"Found {len(ungraded_picks)} ungraded picks to grade")
    
    # Grade each pick
    stats = {
        'graded_picks': 0,
        'correct_first_td': 0,
        'any_time_td': 0,
        'failed_to_match': 0,
        'total_return': 0.0,
        'details': []
    }
    
    for pick in ungraded_picks:
        pick_id, user_id, week_id, team, player_name, odds, theo_return, pick_game_id, pick_week, pick_season = pick
        
        try:
            # Normalize team name to abbreviation
            team_abbr = config.TEAM_ABBR_MAP.get(team, team)
            
            # Determine game_id: prefer stored pick.game_id, else match by team/week
            if pick_game_id:
                game_id = pick_game_id
            else:
                week_schedule = get_game_schedule(df, pick_season)
                if week_schedule.empty:
                    stats['failed_to_match'] += 1
                    continue
                game_week_data = week_schedule[week_schedule['week'] == pick_week]
                if game_week_data.empty:
                    stats['failed_to_match'] += 1
                    continue
                matching_games = game_week_data[
                    (game_week_data['home_team'] == team_abbr) | 
                    (game_week_data['away_team'] == team_abbr)
                ]
                if matching_games.empty:
                    stats['failed_to_match'] += 1
                    continue
                game_id = matching_games.iloc[0]['game_id']
            
            # Check first TD
            first_td_match = first_tds[first_tds['game_id'] == game_id]
            is_correct = False
            actual_first_td_scorer = None  # Track who actually scored the first TD
            
            if not first_td_match.empty:
                actual_first_td_scorer = str(first_td_match.iloc[0]['td_player_name']).strip()
                is_correct = names_match(player_name, actual_first_td_scorer)
            
            # Check any time TD - only in the specific game that was picked
            # NOTE: If player scored first TD, they automatically scored an any time TD
            any_time_td = is_correct  # Start with First TD status
            
            if not any_time_td:  # Only check if not already true from first TD
                td_row = all_tds[all_tds['game_id'] == game_id]
                if not td_row.empty:
                    # Filter to only TDs by the picked team
                    td_row_team_filtered = td_row[td_row['posteam'] == team_abbr]
                    logger.debug(f"Checking Any Time TD for {player_name} ({team_abbr}) in game {game_id}")
                    logger.debug(f"Found {len(td_row_team_filtered)} TDs by {team_abbr} in this game")
                    
                    if not td_row_team_filtered.empty:
                        for _, td in td_row_team_filtered.iterrows():
                            td_player = str(td.get('td_player_name', '')).strip()
                            match = names_match(player_name, td_player)
                            logger.debug(f"  Comparing '{player_name}' vs '{td_player}': {match}")
                            if match:
                                any_time_td = True
                                logger.info(f"✓ Any Time TD match: {player_name} = {td_player}")
                                break
                        
                        if not any_time_td:
                            logger.debug(f"✗ No Any Time TD match for {player_name} in {len(td_row_team_filtered)} TDs")
                    else:
                        logger.debug(f"No TDs found by team {team_abbr} in game {game_id} (checked {len(td_row)} total TDs)")
                else:
                    logger.debug(f"No touchdown data for game {game_id}")
            
            # Ensure any_time_td is always a boolean (not None)
            any_time_td = bool(any_time_td)
            
            # Calculate actual return
            actual_return = theo_return if is_correct else 0.0
            
            # Save result - use the actual first TD scorer, not the picked player
            db_stats.add_result(
                pick_id=pick_id,
                actual_scorer=actual_first_td_scorer,  # Who actually scored first TD (or None if no TD)
                is_correct=is_correct,
                actual_return=actual_return,
                any_time_td=any_time_td
            )
            
            stats['graded_picks'] += 1
            if is_correct:
                stats['correct_first_td'] += 1
            if any_time_td:
                stats['any_time_td'] += 1
            stats['total_return'] += actual_return
            
            # Log detailed result
            logger.info(
                f"✓ Pick {pick_id}: {player_name} ({team_abbr}) game {game_id} - "
                f"First TD: {is_correct}, Any Time TD: {any_time_td}, Return: ${actual_return:.2f}"
            )
            
            stats['details'].append({
                'player': player_name,
                'team': team,
                'week': pick_week,
                'first_td': is_correct,
                'any_time_td': any_time_td,
                'return': actual_return
            })
            
        except Exception as e:
            logger.warning(f"Error grading pick {pick_id}: {str(e)}")
            stats['failed_to_match'] += 1
    
    logger.info(f"Auto-grade complete: {stats['graded_picks']} graded, "
                f"{stats['correct_first_td']} first TD wins, "
                f"{stats['any_time_td']} any time TD wins")
    
    return stats


def grade_any_time_td_only(season: int, week: Optional[int] = None) -> Dict:
    """
    Grade picks for ANY TIME TD only (ignore first TD results).
    Updates any_time_td field without touching is_correct.
    Useful for re-grading when first TD data might be incomplete.
    
    Args:
        season: NFL season year
        week: Optional specific week to grade
        
    Returns:
        Dict with grading summary
    """
    logger.info(f"Starting any-time TD grading for season {season}" + (f" week {week}" if week else ""))
    
    # Load data
    df = load_data(season)
    if df.empty:
        logger.warning(f"No play-by-play data found for season {season}")
        return {'error': 'No data found', 'graded_picks': 0}
    
    # Get all TDs
    all_tds = get_touchdowns(df)
    if all_tds.empty:
        logger.warning(f"No TD data found for season {season}")
        return {'error': 'No TD data found', 'graded_picks': 0}
    
    # Load rosters for name matching
    rosters = load_rosters(season)
    
    # Get ungraded picks (where any_time_td is NULL)
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if week:
        cursor.execute("""
            SELECT p.id, p.user_id, p.week_id, p.team, p.player_name, 
                   p.odds, p.theoretical_return, p.game_id, w.week, w.season
            FROM picks p
            JOIN weeks w ON p.week_id = w.id
            WHERE w.season = ? AND w.week = ?
            AND NOT EXISTS (SELECT 1 FROM results r WHERE r.pick_id = p.id AND r.any_time_td IS NOT NULL)
            ORDER BY p.week_id, p.id
        """, (season, week))
    else:
        cursor.execute("""
            SELECT p.id, p.user_id, p.week_id, p.team, p.player_name, 
                   p.odds, p.theoretical_return, p.game_id, w.week, w.season
            FROM picks p
            JOIN weeks w ON p.week_id = w.id
            WHERE w.season = ?
            AND NOT EXISTS (SELECT 1 FROM results r WHERE r.pick_id = p.id AND r.any_time_td IS NOT NULL)
            ORDER BY p.week_id, p.id
        """, (season,))
    
    ungraded_picks = cursor.fetchall()
    conn.close()
    
    if not ungraded_picks:
        logger.info(f"No picks needing any-time TD grading for season {season}")
        return {'graded_picks': 0, 'message': 'No picks need any-time TD grading'}
    
    logger.info(f"Found {len(ungraded_picks)} picks to grade for any-time TD")
    
    # Grade each pick for any-time TD
    stats = {
        'graded_picks': 0,
        'any_time_td_wins': 0,
        'failed_to_match': 0,
        'details': []
    }
    
    for pick in ungraded_picks:
        pick_id, user_id, week_id, team, player_name, odds, theo_return, pick_game_id, pick_week, pick_season = pick
        
        try:
            # Normalize team name to abbreviation
            team_abbr = config.TEAM_ABBR_MAP.get(team, team)
            
            # Determine game_id: prefer stored pick.game_id, else match by team/week
            if pick_game_id:
                game_id = pick_game_id
            else:
                week_schedule = get_game_schedule(df, pick_season)
                if week_schedule.empty:
                    stats['failed_to_match'] += 1
                    continue
                game_week_data = week_schedule[week_schedule['week'] == pick_week]
                if game_week_data.empty:
                    stats['failed_to_match'] += 1
                    continue
                matching_games = game_week_data[
                    (game_week_data['home_team'] == team_abbr) | 
                    (game_week_data['away_team'] == team_abbr)
                ]
                if matching_games.empty:
                    stats['failed_to_match'] += 1
                    continue
                game_id = matching_games.iloc[0]['game_id']
            
            # Check any time TD
            any_time_td = False
            td_row = all_tds[all_tds['game_id'] == game_id]
            
            if not td_row.empty:
                # Filter to only TDs by the picked team
                td_row_team_filtered = td_row[td_row['posteam'] == team_abbr]
                logger.debug(f"Checking Any Time TD for {player_name} ({team_abbr}) in game {game_id}")
                logger.debug(f"Found {len(td_row_team_filtered)} TDs by {team_abbr} in this game")
                
                if not td_row_team_filtered.empty:
                    for _, td in td_row_team_filtered.iterrows():
                        td_player = str(td.get('td_player_name', '')).strip()
                        match = names_match(player_name, td_player)
                        logger.debug(f"  Comparing '{player_name}' vs '{td_player}': {match}")
                        if match:
                            any_time_td = True
                            logger.info(f"✓ Any Time TD match: {player_name} = {td_player}")
                            break
                    
                    if not any_time_td:
                        logger.debug(f"✗ No Any Time TD match for {player_name} in {len(td_row_team_filtered)} TDs")
                else:
                    logger.debug(f"No TDs found by team {team_abbr} in game {game_id} (checked {len(td_row)} total TDs)")
            else:
                logger.debug(f"No touchdown data for game {game_id}")
            
            # Ensure any_time_td is always a boolean
            any_time_td = bool(any_time_td)
            
            # Update the any_time_td field without changing is_correct
            with get_db_context() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE results
                    SET any_time_td = ?
                    WHERE pick_id = ?
                """, (any_time_td, pick_id))
                
                # If no result exists yet, create one
                if cursor.rowcount == 0:
                    cursor.execute("""
                        INSERT INTO results (pick_id, any_time_td)
                        VALUES (?, ?)
                    """, (pick_id, any_time_td))
            
            stats['graded_picks'] += 1
            if any_time_td:
                stats['any_time_td_wins'] += 1
            
            logger.info(
                f"✓ Pick {pick_id}: {player_name} ({team_abbr}) - Any Time TD: {any_time_td}"
            )
            
            stats['details'].append({
                'player': player_name,
                'team': team,
                'week': pick_week,
                'any_time_td': any_time_td
            })
            
        except Exception as e:
            logger.warning(f"Error grading pick {pick_id} for any-time TD: {str(e)}")
            stats['failed_to_match'] += 1
    
    logger.info(f"Any-time TD grading complete: {stats['graded_picks']} graded, "
                f"{stats['any_time_td_wins']} any time TD wins")
    
    # Clear leaderboard cache if any picks were graded
    if stats['graded_picks'] > 0:
        try:
            from .db_stats import clear_leaderboard_cache
            clear_leaderboard_cache()
        except Exception as e:
            logger.debug(f"Could not clear cache: {e}")
    
    return stats
