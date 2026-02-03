"""Grading API - bridges UI and core grading logic"""

import sqlite3
from src.core.grading.use_cases import (
    grade_season,
    grade_pick,
)
from src.core.grading.entities import GradingResult
from src.data.repositories.results_repository import SQLiteResultRepository
from src.lib.observability import log_event
from typing import Optional
import config


def get_connection() -> sqlite3.Connection:
    """Get database connection"""
    conn = sqlite3.connect(config.DATABASE_PATH)
    return conn


def api_grade_season(season: int, week: int) -> GradingResult:
    """API: Grade all picks for a season week"""
    conn = get_connection()
    result_repo = SQLiteResultRepository(conn)
    
    try:
        result = grade_season(
            season=season,
            week=week,
            result_repository=result_repo,
            pbp_repository=None,
        )
        return result
    finally:
        conn.close()


def api_grade_pick(pick_id: int, pbp_data: dict) -> dict:
    """API: Grade a single pick"""
    conn = get_connection()
    result_repo = SQLiteResultRepository(conn)
    
    try:
        pick = {"id": pick_id}  # Placeholder
        result = grade_pick(pick, pbp_data, result_repo)
        return result.dict()
    finally:
        conn.close()
