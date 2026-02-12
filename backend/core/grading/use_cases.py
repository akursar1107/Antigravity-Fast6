"""Grading use cases - orchestrate auto-grading logic"""

from backend.core.grading.entities import Result, GradingResult
from backend.core.grading.ports import ResultRepository, PlayByPlayRepository
from backend.core.grading.errors import NoPlayByPlayDataError, NameMatchError
from backend.utils.observability import track_operation, log_event
from typing import Optional


def grade_pick(
    pick: dict,
    pbp_data: dict,
    result_repository: ResultRepository,
    name_match_threshold: float = 0.75,
) -> Optional[Result]:
    """Use case: Grade a single pick against PBP data"""
    
    try:
        # Get first TD scorers for this game
        scorers = pbp_data.get("first_td_scorers", [])
        if not scorers:
            raise NoPlayByPlayDataError(f"No first TD data for game {pick['game_id']}")
        
        # Simple name matching (would use rapidfuzz in production)
        is_correct = any(
            pick["player_name"].lower() in scorer.lower()
            for scorer in scorers
        )
        
        result = Result(
            pick_id=pick["id"],
            actual_scorer=scorers[0] if is_correct else None,
            is_correct=is_correct,
            any_time_td=pick.get("any_time_td", False),
            actual_return=pick["odds"] if is_correct else 0,
        )
        
        result_id = result_repository.save_result(result)
        result.id = result_id
        
        log_event("pick_graded", {
            "pick_id": pick["id"],
            "is_correct": is_correct,
        })
        
        return result
    
    except Exception as e:
        log_event("grading_error", {"pick_id": pick["id"], "error": str(e)})
        raise


def grade_season(
    season: int,
    week: int,
    result_repository: ResultRepository,
    pbp_repository: Optional[PlayByPlayRepository] = None,
    name_match_threshold: float = 0.75,
) -> GradingResult:
    """Use case: Grade all picks for a season week"""
    
    with track_operation("grade_season", {"season": season, "week": week}):
        ungraded = result_repository.get_ungraded_picks(week)
        
        graded_count = 0
        correct_count = 0
        any_time_count = 0
        errors = []
        
        for pick in ungraded:
            try:
                pbp_data = {"first_td_scorers": []}  # Placeholder
                result = grade_pick(
                    pick,
                    pbp_data,
                    result_repository,
                    name_match_threshold,
                )
                graded_count += 1
                if result.is_correct:
                    correct_count += 1
                if result.any_time_td:
                    any_time_count += 1
            except Exception as e:
                errors.append(f"Pick {pick['id']}: {str(e)}")
        
        return GradingResult(
            total_graded=graded_count,
            correct_first_td=correct_count,
            correct_any_time_td=any_time_count,
            failed_matches=len(errors),
            errors=errors,
        )
