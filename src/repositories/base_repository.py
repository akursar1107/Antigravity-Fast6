"""
Base repository with common database operations.

Provides shared functionality for all repositories including
row-to-dict conversion and common query patterns.
"""

import sqlite3
import logging
from typing import Optional, List, Dict, Any
from abc import ABC

logger = logging.getLogger(__name__)


class BaseRepository(ABC):
    """Base class for all repositories providing common database operations."""
    
    def __init__(self, conn: sqlite3.Connection):
        """
        Initialize repository with database connection.
        
        Args:
            conn: SQLite database connection (should be from get_db_context())
        """
        self.conn = conn
        self.cursor = conn.cursor()
    
    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """
        Convert SQLite Row object to dictionary.
        
        Args:
            row: SQLite Row object
            
        Returns:
            Dictionary with column names as keys
        """
        return dict(row) if row else None
    
    def _rows_to_dicts(self, rows: List[sqlite3.Row]) -> List[Dict[str, Any]]:
        """
        Convert list of SQLite Row objects to list of dictionaries.
        
        Args:
            rows: List of SQLite Row objects
            
        Returns:
            List of dictionaries with column names as keys
        """
        return [dict(row) for row in rows]
    
    def _execute_one(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """
        Execute query and return single result as dictionary.
        
        Args:
            query: SQL query string
            params: Query parameters tuple
            
        Returns:
            Dictionary or None if no result
        """
        self.cursor.execute(query, params)
        row = self.cursor.fetchone()
        return self._row_to_dict(row)
    
    def _execute_many(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """
        Execute query and return all results as list of dictionaries.
        
        Args:
            query: SQL query string
            params: Query parameters tuple
            
        Returns:
            List of dictionaries
        """
        self.cursor.execute(query, params)
        rows = self.cursor.fetchall()
        return self._rows_to_dicts(rows)
    
    def _execute_write(self, query: str, params: tuple = ()) -> int:
        """
        Execute write operation (INSERT, UPDATE, DELETE) and return lastrowid or rowcount.
        
        Args:
            query: SQL query string
            params: Query parameters tuple
            
        Returns:
            Last inserted row ID for INSERT, or number of affected rows for UPDATE/DELETE
        """
        self.cursor.execute(query, params)
        # Return lastrowid for INSERT operations, rowcount for UPDATE/DELETE
        return self.cursor.lastrowid if self.cursor.lastrowid > 0 else self.cursor.rowcount
