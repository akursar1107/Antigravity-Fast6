"""Grading domain entities"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class Result(BaseModel):
    """Graded result for a pick"""
    id: Optional[int] = None
    pick_id: int
    actual_scorer: Optional[str] = None
    is_correct: bool
    any_time_td: bool
    actual_return: float  # Payout amount
    graded_at: Optional[datetime] = None


class GradingResult(BaseModel):
    """Summary of grading operation"""
    total_graded: int
    correct_first_td: int
    correct_any_time_td: int
    failed_matches: int
    errors: list[str]
