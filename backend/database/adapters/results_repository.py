"""Results repository - implements ResultRepository port"""

from typing import List, Optional
from backend.core.grading.entities import Result
from backend.core.grading.ports import ResultRepository
from backend.database.adapters.base import BaseRepository


class SQLiteResultRepository(BaseRepository, ResultRepository):
    """SQLite implementation of ResultRepository"""
    
    def save_result(self, result: Result) -> int:
        """Save grading result"""
        query = """
            INSERT INTO results (pick_id, actual_scorer, is_correct, any_time_td, actual_return, graded_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        self.execute(query, (
            result.pick_id,
            result.actual_scorer,
            result.is_correct,
            result.any_time_td,
            result.actual_return,
            result.graded_at,
        ))
        self.commit()
        return self.get_last_row_id()
    
    def get_results_by_pick(self, pick_id: int) -> Optional[Result]:
        """Get result for a pick"""
        query = "SELECT * FROM results WHERE pick_id = ?"
        row = self.execute(query, (pick_id,)).fetchone()
        if not row:
            return None
        return self._row_to_result(row)
    
    def get_ungraded_picks(self, week_id: int) -> List[dict]:
        """Get all ungraded picks for a week"""
        query = """
            SELECT p.* FROM picks p
            LEFT JOIN results r ON p.id = r.pick_id
            WHERE p.week_id = ? AND r.id IS NULL
        """
        rows = self.execute(query, (week_id,)).fetchall()
        return [self._row_to_dict(row) for row in rows]
    
    def _row_to_result(self, row: tuple) -> Result:
        """Convert database row to Result entity"""
        return Result(
            id=row[0],
            pick_id=row[1],
            actual_scorer=row[2],
            is_correct=bool(row[3]),
            any_time_td=bool(row[4]),
            actual_return=row[5],
            graded_at=row[6],
        )
    
    def _row_to_dict(self, row: tuple) -> dict:
        """Convert pick row to dict"""
        return {
            "id": row[0],
            "user_id": row[1],
            "week_id": row[2],
            "game_id": row[3],
            "team": row[4],
            "player_name": row[5],
            "odds": row[6],
        }
