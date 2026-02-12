"""Base repository class with common CRUD operations"""

import sqlite3
from typing import Optional, List
from abc import ABC


class BaseRepository(ABC):
    """Base repository with common SQLite operations"""
    
    def __init__(self, connection: sqlite3.Connection):
        self.conn = connection
        self.cursor = connection.cursor()
    
    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute SQL query"""
        return self.cursor.execute(query, params)
    
    def execute_many(self, query: str, params: list) -> sqlite3.Cursor:
        """Execute query multiple times"""
        return self.cursor.executemany(query, params)
    
    def commit(self):
        """Commit transaction"""
        self.conn.commit()
    
    def rollback(self):
        """Rollback transaction"""
        self.conn.rollback()
    
    def get_last_row_id(self) -> int:
        """Get last inserted row ID"""
        return self.cursor.lastrowid
