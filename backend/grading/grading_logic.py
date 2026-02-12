"""
Grading Logic Module
Handles auto-grading of picks against actual play-by-play data.
"""

import logging
import time
from typing import Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime
import pandas as pd
from backend.analytics.nfl_data import load_data, get_game_schedule, get_first_tds, get_touchdowns, load_rosters
from backend.utils.name_matching import names_match
from backend.utils.caching import cached, CacheTTL, invalidate_on_grading_complete
from backend.utils.types import Result, GradingResult
from backend.utils.observability import track_operation, log_event
from backend.database import get_db_connection, get_db_context, add_results_batch
import backend.config as config

logger = logging.getLogger(__name__)


@dataclass
class TDLookupCache:
    """
    Pre-computed touchdown lookup tables organized by game_id for fast access.
    Reduces memory usage and lookup time by avoiding repeated processing of full season data.
    """
    first_tds_by_game: Dict[str, pd.DataFrame]
    all_tds_by_game: Dict[str, pd.DataFrame]
    season: int
    cached_at: datetime
    
    def get_first_td_for_game(self, game_id: str) -> Optional[pd.DataFrame]:
        """Get first TD data for a specific game."""
        return self.first_tds_by_game.get(game_id)
    
    def get_all_tds_for_game(self, game_id: str) -> Optional[pd.DataFrame]:
        """Get all TD data for a specific game."""
        return self.all_tds_by_game.get(game_id)


def _build_td_lookup_cache(season: int) -> TDLookupCache:
    """
    Build TD lookup cache for fast game-specific TD lookups.
    This function is called internally for building TD lookup caches.
    
    Args:
        season: NFL season year
        
    Returns:
        TDLookupCache with pre-computed TD data organized by game_id
    """
    logger.info(f"Building TD lookup cache for season {season}")
    
    # Load full season data
    df = load_data(season)
    if df.empty:
        logger.warning(f"No play-by-play data for season {season}")
        return TDLookupCache(
            first_tds_by_game={},
            all_tds_by_game={},
            season=season,
            cached_at=datetime.now()
        )
    
    # Get first TDs and all TDs
    first_tds = get_first_tds(df)
    all_tds = get_touchdowns(df)
    
    # Organize by game_id
    first_tds_by_game = {}
    all_tds_by_game = {}
    
    if not first_tds.empty and 'game_id' in first_tds.columns:
        for game_id, group in first_tds.groupby('game_id'):
            first_tds_by_game[game_id] = group
    
    if not all_tds.empty and 'game_id' in all_tds.columns:
        for game_id, group in all_tds.groupby('game_id'):
            all_tds_by_game[game_id] = group
    
    logger.info(f"Built TD cache: {len(first_tds_by_game)} games with first TDs, {len(all_tds_by_game)} games with all TDs")
    
    return TDLookupCache(
        first_tds_by_game=first_tds_by_game,
        all_tds_by_game=all_tds_by_game,
        season=season,
        cached_at=datetime.now()
    )

@cached(ttl=CacheTTL.NFL_PBP, cache_name="td_lookup_cache")
def get_td_lookup_cache(season: int) -> TDLookupCache:
    """
    Get cached TD lookup data for a season using the unified caching layer.
    Cache TTL: 1 hour.
    
    Args:
        season: NFL season year
        
    Returns:
        TDLookupCache with TD data organized by game_id for fast lookups
    """
    return _build_td_lookup_cache(season)


def auto_grade_season(season: int, week: Optional[int] = None) -> GradingResult:
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

    with track_operation("grading.auto_grade_season", season=season, week=week) as obs:
        # Get TD lookup cache for this season
        td_cache = get_td_lookup_cache(season)

        if not td_cache.first_tds_by_game:
            logger.warning(f"No first TD data found for season {season}")
            obs["result"] = "no_td_data"
            obs["graded_picks"] = 0
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
            obs["result"] = "no_ungraded_picks"
            obs["graded_picks"] = 0
            return {'graded_picks': 0, 'message': 'No ungraded picks'}

        logger.info(f"Found {len(ungraded_picks)} ungraded picks to grade")

        # Grade each pick - collect results for batch insert
        stats = {
            'graded_picks': 0,
            'correct_first_td': 0,
            'any_time_td': 0,
            'failed_to_match': 0,
            'total_return': 0.0,
            'details': []
        }

        # Collect results for batch insert
        results_to_save = []

        # Pre-fetch user base_bet for each user
        conn = get_db_connection()
        cursor = conn.cursor()
        user_ids = list({p[1] for p in ungraded_picks})
        cursor.execute(
            "SELECT id, COALESCE(base_bet, ?) FROM users WHERE id IN ({})".format(
                ",".join("?" * len(user_ids))
            ),
            [config.ROI_STAKE] + user_ids
        )
        stake_by_user = {r[0]: r[1] for r in cursor.fetchall()}
        conn.close()

        for pick in ungraded_picks:
            pick_id, user_id, week_id, team, player_name, odds, theo_return, pick_game_id, pick_week, pick_season = pick
            stake = stake_by_user.get(user_id, config.ROI_STAKE)

            try:
                # Normalize team name to abbreviation
                team_abbr = config.TEAM_ABBR_MAP.get(team, team)

                # Determine game_id: prefer stored pick.game_id, else skip (requires game_id)
                if not pick_game_id:
                    logger.warning(f"Pick {pick_id} missing game_id, skipping (player: {player_name}, team: {team})")
                    stats['failed_to_match'] += 1
                    continue

                game_id = pick_game_id

                # Check first TD using cached data
                first_td_match = td_cache.get_first_td_for_game(game_id)
                is_correct = False
                actual_first_td_scorer = None  # Track who actually scored the first TD

                if first_td_match is not None and not first_td_match.empty:
                    actual_first_td_scorer = str(first_td_match.iloc[0]['td_player_name']).strip()
                    is_correct = names_match(player_name, actual_first_td_scorer)

                # Check any time TD - only in the specific game that was picked
                # NOTE: If player scored first TD, they automatically scored an any time TD
                any_time_td = is_correct  # Start with First TD status

                if not any_time_td:  # Only check if not already true from first TD
                    td_row = td_cache.get_all_tds_for_game(game_id)
                    if td_row is not None and not td_row.empty:
                        # Filter to only TDs by the picked team (use td_scorer_team for return TDs)
                        team_col = 'td_scorer_team' if 'td_scorer_team' in td_row.columns else 'posteam'
                        td_row_team_filtered = td_row[td_row[team_col] == team_abbr]
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

                # Calculate actual return: loss = -stake, win = stake * (odds/100) profit
                if is_correct and odds is not None and odds != 0:
                    actual_return = float(stake) * (odds / 100.0)
                else:
                    actual_return = -float(stake) if not is_correct else 0.0

                # Collect result for batch insert (instead of individual db call)
                results_to_save.append({
                    'pick_id': pick_id,
                    'actual_scorer': actual_first_td_scorer,
                    'is_correct': is_correct,
                    'actual_return': actual_return,
                    'any_time_td': any_time_td
                })

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

        # Batch save all results in a single transaction
        if results_to_save:
            batch_result = add_results_batch(results_to_save)
            logger.info(f"Batch saved {batch_result['inserted']} new results, {batch_result['updated']} updated")

        logger.info(f"Auto-grade complete: {stats['graded_picks']} graded, "
                    f"{stats['correct_first_td']} first TD wins, "
                    f"{stats['any_time_td']} any time TD wins")

        obs["graded_picks"] = stats['graded_picks']
        obs["correct_first_td"] = stats['correct_first_td']
        obs["any_time_td"] = stats['any_time_td']
        obs["failed_to_match"] = stats['failed_to_match']

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
    start_time = time.perf_counter()
    log_event("grading.any_time_td_only.start", season=season, week=week)

    # Get TD lookup cache for this season
    td_cache = get_td_lookup_cache(season)

    if not td_cache.all_tds_by_game:
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        logger.warning(f"No TD data found for season {season}")
        log_event("grading.any_time_td_only.end", season=season, week=week, result="no_td_data", graded_picks=0, duration_ms=duration_ms)
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
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        log_event(
            "grading.any_time_td_only.end",
            season=season,
            week=week,
            result="no_picks",
            graded_picks=0,
            duration_ms=duration_ms,
        )
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
            
            # Determine game_id: prefer stored pick.game_id, else skip (requires game_id)
            if not pick_game_id:
                logger.warning(f"Pick {pick_id} missing game_id, skipping (player: {player_name}, team: {team})")
                stats['failed_to_match'] += 1
                continue
            
            game_id = pick_game_id
            
            # Check any time TD
            any_time_td = False
            td_row = td_cache.get_all_tds_for_game(game_id)
            
            if td_row is not None and not td_row.empty:
                # Filter to only TDs by the picked team
                team_col = 'td_scorer_team' if 'td_scorer_team' in td_row.columns else 'posteam'
                td_row_team_filtered = td_row[td_row[team_col] == team_abbr]
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

    duration_ms = int((time.perf_counter() - start_time) * 1000)
    log_event(
        "grading.any_time_td_only.end",
        season=season,
        week=week,
        graded_picks=stats['graded_picks'],
        any_time_td_wins=stats['any_time_td_wins'],
        failed_to_match=stats['failed_to_match'],
        duration_ms=duration_ms,
    )
    
    # Clear leaderboard cache if any picks were graded
    if stats['graded_picks'] > 0:
        try:
            from backend.database import clear_leaderboard_cache
            clear_leaderboard_cache()
        except Exception as e:
            logger.debug(f"Could not clear cache: {e}")
    
    return stats
