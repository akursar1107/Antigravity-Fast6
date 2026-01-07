"""
Grading Logic Module
Handles auto-grading of picks against actual play-by-play data.
"""

import logging
from typing import Dict, Optional
import pandas as pd
from utils.nfl_data import load_data, get_game_schedule, get_first_tds, get_touchdowns, load_rosters
from utils.name_matching import names_match
import database
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
    conn = database.get_db_connection()
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
            if not first_td_match.empty:
                actual_first_td_player = str(first_td_match.iloc[0]['td_player_name']).strip()
                is_correct = names_match(player_name, actual_first_td_player)
            
            # Check any time TD - only in the specific game that was picked
            any_time_td = False
            td_row = all_tds[all_tds['game_id'] == game_id]
            if not td_row.empty:
                # Filter to only TDs by the picked team
                td_row_team_filtered = td_row[td_row['posteam'] == team_abbr]
                for _, td in td_row_team_filtered.iterrows():
                    td_player = str(td.get('td_player_name', '')).strip()
                    if names_match(player_name, td_player):
                        any_time_td = True
                        break
            
            # Calculate actual return
            actual_return = theo_return if is_correct else 0.0
            
            # Save result
            database.add_result(
                pick_id=pick_id,
                actual_scorer=player_name,
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
