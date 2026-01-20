"""
Grading Service - Business logic for pick grading operations.

Separates grading business rules from data access and NFL data fetching.
Uses repositories for data access and provides pure business logic.
"""

import logging
from typing import Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime
import pandas as pd

from repositories import PicksRepository, ResultsRepository, WeeksRepository
from utils.name_matching import names_match
from utils.grading_logic import get_td_lookup_cache
import config

logger = logging.getLogger(__name__)


@dataclass
class GradeResult:
    """Result of grading a single pick."""
    pick_id: int
    is_correct: bool
    any_time_td: bool
    actual_return: float
    actual_scorer: Optional[str] = None
    error: Optional[str] = None


@dataclass
class GradingSummary:
    """Summary statistics for a grading operation."""
    total_picks: int
    graded_picks: int
    correct_first_td: int
    any_time_td_count: int
    failed_to_match: int
    total_return: float
    details: List[Dict]


class GradingService:
    """
    Service for grading picks against actual NFL play-by-play data.
    
    Encapsulates all business logic for:
    - Determining if a pick was correct (first TD)
    - Checking if player scored any-time TD
    - Calculating actual returns
    - Name matching and validation
    """
    
    def __init__(self, picks_repo: PicksRepository, results_repo: ResultsRepository):
        """
        Initialize grading service with repositories.
        
        Args:
            picks_repo: Repository for pick data access
            results_repo: Repository for results data access
        """
        self.picks_repo = picks_repo
        self.results_repo = results_repo
    
    def grade_pick(self, pick: Dict, td_cache) -> GradeResult:
        """
        Grade a single pick against actual TD data.
        
        This is pure business logic - no database or API calls.
        
        Args:
            pick: Pick dictionary with keys: id, player_name, team, game_id, odds, theoretical_return
            td_cache: TDLookupCache with pre-loaded TD data
            
        Returns:
            GradeResult with grading outcome
        """
        pick_id = pick['id']
        player_name = pick['player_name']
        team = pick['team']
        game_id = pick.get('game_id')
        theoretical_return = pick.get('theoretical_return', 0.0)
        
        # Validate game_id
        if not game_id:
            return GradeResult(
                pick_id=pick_id,
                is_correct=False,
                any_time_td=False,
                actual_return=0.0,
                error=f"Missing game_id for pick {pick_id}"
            )
        
        # Normalize team to abbreviation
        team_abbr = config.TEAM_ABBR_MAP.get(team, team)
        
        # Check first TD
        is_correct = False
        actual_first_td_scorer = None
        
        first_td_data = td_cache.get_first_td_for_game(game_id)
        if first_td_data is not None and not first_td_data.empty:
            actual_first_td_scorer = str(first_td_data.iloc[0]['td_player_name']).strip()
            is_correct = names_match(player_name, actual_first_td_scorer)
            logger.debug(f"First TD check: {player_name} vs {actual_first_td_scorer} = {is_correct}")
        
        # Check any-time TD (automatically true if first TD was correct)
        any_time_td = is_correct
        
        if not any_time_td:
            all_tds_data = td_cache.get_all_tds_for_game(game_id)
            if all_tds_data is not None and not all_tds_data.empty:
                # Filter to team's TDs only
                team_tds = all_tds_data[all_tds_data['posteam'] == team_abbr]
                
                for _, td in team_tds.iterrows():
                    td_player = str(td.get('td_player_name', '')).strip()
                    if names_match(player_name, td_player):
                        any_time_td = True
                        logger.info(f"✓ Any-time TD match: {player_name} = {td_player}")
                        break
        
        # Calculate actual return
        actual_return = theoretical_return if is_correct else 0.0
        
        return GradeResult(
            pick_id=pick_id,
            is_correct=is_correct,
            any_time_td=bool(any_time_td),
            actual_return=actual_return,
            actual_scorer=actual_first_td_scorer
        )
    
    def grade_season(self, season: int, week: Optional[int] = None) -> GradingSummary:
        """
        Grade all ungraded picks for a season or specific week.
        
        Args:
            season: NFL season year
            week: Optional week number to filter
            
        Returns:
            GradingSummary with grading statistics
        """
        logger.info(f"Grading season {season}" + (f" week {week}" if week else ""))
        
        # Load TD data cache
        td_cache = get_td_lookup_cache(season)
        
        if not td_cache.first_tds_by_game:
            logger.warning(f"No TD data for season {season}")
            return GradingSummary(
                total_picks=0,
                graded_picks=0,
                correct_first_td=0,
                any_time_td_count=0,
                failed_to_match=0,
                total_return=0.0,
                details=[{'error': 'No TD data found'}]
            )
        
        # Get ungraded picks
        ungraded_picks = self.picks_repo.get_ungraded_picks(season, week)
        
        if not ungraded_picks:
            logger.info(f"No ungraded picks for season {season}")
            return GradingSummary(
                total_picks=0,
                graded_picks=0,
                correct_first_td=0,
                any_time_td_count=0,
                failed_to_match=0,
                total_return=0.0,
                details=[{'message': 'No ungraded picks'}]
            )
        
        logger.info(f"Grading {len(ungraded_picks)} picks")
        
        # Grade each pick
        stats = {
            'graded': 0,
            'correct': 0,
            'any_time': 0,
            'failed': 0,
            'total_return': 0.0,
            'details': []
        }
        
        for pick in ungraded_picks:
            # Grade the pick (pure business logic)
            result = self.grade_pick(pick, td_cache)
            
            if result.error:
                stats['failed'] += 1
                stats['details'].append({
                    'pick_id': pick['id'],
                    'player': pick['player_name'],
                    'error': result.error
                })
                continue
            
            # Save result to database
            try:
                self.results_repo.add(
                    pick_id=result.pick_id,
                    actual_scorer=result.actual_scorer,
                    is_correct=result.is_correct,
                    actual_return=result.actual_return
                )
                
                stats['graded'] += 1
                if result.is_correct:
                    stats['correct'] += 1
                if result.any_time_td:
                    stats['any_time'] += 1
                stats['total_return'] += result.actual_return
                
                stats['details'].append({
                    'pick_id': result.pick_id,
                    'player': pick['player_name'],
                    'team': pick['team'],
                    'correct': result.is_correct,
                    'any_time_td': result.any_time_td,
                    'return': result.actual_return
                })
                
            except Exception as e:
                logger.error(f"Failed to save result for pick {result.pick_id}: {e}")
                stats['failed'] += 1
                stats['details'].append({
                    'pick_id': result.pick_id,
                    'player': pick['player_name'],
                    'error': str(e)
                })
        
        logger.info(f"Grading complete: {stats['graded']} graded, {stats['correct']} correct")
        
        return GradingSummary(
            total_picks=len(ungraded_picks),
            graded_picks=stats['graded'],
            correct_first_td=stats['correct'],
            any_time_td_count=stats['any_time'],
            failed_to_match=stats['failed'],
            total_return=stats['total_return'],
            details=stats['details']
        )
    
    def regrade_pick(self, pick_id: int) -> GradeResult:
        """
        Re-grade a specific pick (deletes old result and creates new one).
        
        Args:
            pick_id: ID of pick to re-grade
            
        Returns:
            GradeResult with new grading outcome
        """
        # Get pick
        pick = self.picks_repo.get_by_id(pick_id)
        if not pick:
            return GradeResult(
                pick_id=pick_id,
                is_correct=False,
                any_time_td=False,
                actual_return=0.0,
                error=f"Pick {pick_id} not found"
            )
        
        # Get season from pick
        season = pick.get('season')
        if not season:
            # Need to fetch week to get season
            from repositories import WeeksRepository
            weeks_repo = WeeksRepository(self.picks_repo.conn)
            week_data = weeks_repo.get_by_id(pick['week_id'])
            season = week_data['season'] if week_data else None
        
        if not season:
            return GradeResult(
                pick_id=pick_id,
                is_correct=False,
                any_time_td=False,
                actual_return=0.0,
                error="Could not determine season for pick"
            )
        
        # Load TD cache
        td_cache = get_td_lookup_cache(season)
        
        # Delete existing result
        self.results_repo.delete_by_pick_id(pick_id)
        
        # Grade pick
        result = self.grade_pick(pick, td_cache)
        
        if not result.error:
            # Save new result
            self.results_repo.add(
                pick_id=result.pick_id,
                actual_scorer=result.actual_scorer,
                is_correct=result.is_correct,
                actual_return=result.actual_return
            )
        
        return result
    
    def get_user_accuracy(self, user_id: int, season: Optional[int] = None) -> Dict:
        """
        Calculate user's picking accuracy.
        
        Args:
            user_id: User ID
            season: Optional season filter
            
        Returns:
            Dictionary with accuracy statistics
        """
        return self.results_repo.get_user_stats(user_id, season)
    
    def validate_pick(self, player_name: str, team: str, game_id: str) -> Dict:
        """
        Validate a pick before submission (business rule checking).
        
        Args:
            player_name: Player name
            team: Team abbreviation
            game_id: Game ID
            
        Returns:
            Dictionary with validation result and any warnings
        """
        warnings = []
        
        # Check if player name is reasonable length
        if len(player_name.strip()) < 3:
            warnings.append("Player name seems very short")
        
        # Check if team is valid
        team_abbr = config.TEAM_ABBR_MAP.get(team, team)
        if team_abbr not in config.TEAM_ABBR_MAP.values():
            warnings.append(f"Unknown team: {team}")
        
        # Check game_id format (basic)
        if not game_id or '_' not in game_id:
            warnings.append("Invalid game_id format")
        
        return {
            'valid': len(warnings) == 0,
            'warnings': warnings,
            'normalized_team': team_abbr
        }
