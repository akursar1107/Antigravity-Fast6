"""Picks repository - implements PickRepository port (schema aligns with migration v11)"""

from typing import List, Optional
from backend.core.picks.entities import Pick, PickStatus
from backend.core.picks.ports import PickRepository
from backend.database.adapters.base import BaseRepository


class SQLitePickRepository(BaseRepository, PickRepository):
    """SQLite implementation of PickRepository - uses picks table schema (no status/updated_at)"""
    
    def save(self, pick: Pick) -> int:
        """Save pick to database - columns: user_id, week_id, team, player_name, odds, theoretical_return, game_id"""
        query = """
            INSERT INTO picks (user_id, week_id, team, player_name, odds, theoretical_return, game_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        self.execute(query, (
            pick.user_id,
            pick.week_id,
            pick.team,
            pick.player_name,
            pick.odds,
            pick.theoretical_return,
            pick.game_id,
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
        """Update pick fields - only persisting schema columns (player_name, odds, theoretical_return, team)"""
        allowed_fields = {"player_name", "odds", "theoretical_return", "team"}
        fields_to_update = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not fields_to_update:
            return self.get_by_id(pick_id)
        
        set_clause = ", ".join(f"{k} = ?" for k in fields_to_update.keys())
        query = f"UPDATE picks SET {set_clause} WHERE id = ?"
        
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
    
    def _row_to_pick(self, row) -> Pick:
        """Convert database row to Pick entity - schema: id, user_id, week_id, team, player_name, odds, theoretical_return, game_id, created_at"""
        if hasattr(row, 'keys'):
            d = dict(row)
        else:
            d = {'id': row[0], 'user_id': row[1], 'week_id': row[2], 'team': row[3],
                 'player_name': row[4], 'odds': row[5], 'theoretical_return': row[6] if len(row) > 6 else None,
                 'game_id': row[7] if len(row) > 7 else None, 'created_at': row[8] if len(row) > 8 else None}
        return Pick(
            id=d.get('id'),
            user_id=d.get('user_id'),
            week_id=d.get('week_id'),
            team=d.get('team'),
            player_name=d.get('player_name'),
            odds=d.get('odds') or 0.0,
            theoretical_return=d.get('theoretical_return'),
            status=PickStatus.CONFIRMED,
            created_at=d.get('created_at'),
        )
