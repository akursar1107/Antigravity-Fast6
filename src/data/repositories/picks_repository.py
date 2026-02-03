"""Picks repository - implements PickRepository port"""

from typing import List, Optional
from src.core.picks.entities import Pick, PickStatus
from src.core.picks.ports import PickRepository
from src.data.repositories.base import BaseRepository


class SQLitePickRepository(BaseRepository, PickRepository):
    """SQLite implementation of PickRepository"""
    
    def save(self, pick: Pick) -> int:
        """Save pick to database"""
        query = """
            INSERT INTO picks (user_id, week_id, game_id, team, player_name, odds, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.execute(query, (
            pick.user_id,
            pick.week_id,
            pick.game_id,
            pick.team,
            pick.player_name,
            pick.odds,
            pick.status.value,
            pick.created_at,
        ))
        self.commit()
        return self.get_last_row_id()
    
    def get_by_id(self, pick_id: int) -> Optional[Pick]:
        """Get pick by ID"""
        query = "SELECT * FROM picks WHERE id = ?"
        row = self.execute(query, (pick_id,)).fetchone()
        if not row:
            return None
        return self._row_to_pick(row)
    
    def get_user_picks(self, user_id: int, week_id: Optional[int] = None) -> List[Pick]:
        """Get all picks for user"""
        if week_id:
            query = "SELECT * FROM picks WHERE user_id = ? AND week_id = ?"
            rows = self.execute(query, (user_id, week_id)).fetchall()
        else:
            query = "SELECT * FROM picks WHERE user_id = ?"
            rows = self.execute(query, (user_id,)).fetchall()
        
        return [self._row_to_pick(row) for row in rows]
    
    def update(self, pick_id: int, **kwargs) -> Pick:
        """Update pick fields"""
        allowed_fields = {"status", "player_name", "odds"}
        fields_to_update = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not fields_to_update:
            return self.get_by_id(pick_id)
        
        set_clause = ", ".join(f"{k} = ?" for k in fields_to_update.keys())
        query = f"UPDATE picks SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
        
        params = list(fields_to_update.values()) + [pick_id]
        self.execute(query, params)
        self.commit()
        
        return self.get_by_id(pick_id)
    
    def delete(self, pick_id: int) -> bool:
        """Delete pick"""
        query = "DELETE FROM picks WHERE id = ?"
        self.execute(query, (pick_id,))
        self.commit()
        return self.cursor.rowcount > 0
    
    def _row_to_pick(self, row: tuple) -> Pick:
        """Convert database row to Pick entity"""
        return Pick(
            id=row[0],
            user_id=row[1],
            week_id=row[2],
            game_id=row[3],
            team=row[4],
            player_name=row[5],
            odds=row[6],
            status=PickStatus(row[7]) if row[7] else PickStatus.PENDING,
            created_at=row[8],
            updated_at=row[9] if len(row) > 9 else None,
        )
