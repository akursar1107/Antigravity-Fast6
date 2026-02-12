"""
Base Repository Pattern
Provides common database operations to reduce code duplication.

All database repositories can inherit from BaseRepository to get:
- Standard CRUD operations
- Transaction management
- Error handling
- Query building utilities
"""

from typing import Optional, List, Dict, Any, Tuple
import sqlite3
import logging
from contextlib import contextmanager
from .connection import get_db_connection, get_db_context
from backend.utils.error_handling import log_exception, DatabaseError

logger = logging.getLogger(__name__)


class BaseRepository:
    """
    Base repository class providing common database operations.
    
    Subclasses should define:
    - table_name: str - The database table name
    - id_column: str - The primary key column name (default: 'id')
    """
    
    table_name: str = None
    id_column: str = 'id'
    
    def __init__(self):
        if not self.table_name:
            raise ValueError(f"{self.__class__.__name__} must define table_name")
    
    # ========== READ OPERATIONS ==========
    
    def find_by_id(self, id_value: Any) -> Optional[sqlite3.Row]:
        """Find a single record by ID."""
        with get_db_context() as conn:
            cursor = conn.execute(
                f"SELECT * FROM {self.table_name} WHERE {self.id_column} = ?",
                (id_value,)
            )
            return cursor.fetchone()
    
    def find_all(self, limit: Optional[int] = None, offset: int = 0) -> List[sqlite3.Row]:
        """Find all records with optional pagination."""
        query = f"SELECT * FROM {self.table_name}"
        params = []
        
        if limit:
            query += " LIMIT ? OFFSET ?"
            params = [limit, offset]
        
        with get_db_context() as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchall()
    
    def find_where(
        self, 
        conditions: Dict[str, Any], 
        order_by: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[sqlite3.Row]:
        """
        Find records matching conditions.
        
        Args:
            conditions: Dict of column: value pairs (AND logic)
            order_by: Optional ORDER BY clause (e.g., "created_at DESC")
            limit: Optional limit on results
            
        Example:
            repo.find_where({'season': 2024, 'week': 1}, order_by='score DESC', limit=10)
        """
        where_clause = " AND ".join([f"{col} = ?" for col in conditions.keys()])
        query = f"SELECT * FROM {self.table_name} WHERE {where_clause}"
        
        if order_by:
            query += f" ORDER BY {order_by}"
        if limit:
            query += f" LIMIT {limit}"
        
        with get_db_context() as conn:
            cursor = conn.execute(query, list(conditions.values()))
            return cursor.fetchall()
    
    def count(self, conditions: Optional[Dict[str, Any]] = None) -> int:
        """Count records, optionally with conditions."""
        query = f"SELECT COUNT(*) FROM {self.table_name}"
        params = []
        
        if conditions:
            where_clause = " AND ".join([f"{col} = ?" for col in conditions.keys()])
            query += f" WHERE {where_clause}"
            params = list(conditions.values())
        
        with get_db_context() as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchone()[0]
    
    def exists(self, conditions: Dict[str, Any]) -> bool:
        """Check if a record exists matching conditions."""
        return self.count(conditions) > 0
    
    # ========== WRITE OPERATIONS ==========
    
    def insert(self, data: Dict[str, Any]) -> int:
        """
        Insert a new record and return the inserted ID.
        
        Args:
            data: Dict of column: value pairs
            
        Returns:
            The ID of the inserted record
        """
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?" for _ in data])
        query = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"
        
        with get_db_context() as conn:
            cursor = conn.execute(query, list(data.values()))
            conn.commit()
            return cursor.lastrowid
    
    def insert_many(self, records: List[Dict[str, Any]]) -> int:
        """
        Insert multiple records in a single transaction.
        
        Returns:
            Number of records inserted
        """
        if not records:
            return 0
        
        columns = ", ".join(records[0].keys())
        placeholders = ", ".join(["?" for _ in records[0]])
        query = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"
        
        with get_db_context() as conn:
            values_list = [list(record.values()) for record in records]
            conn.executemany(query, values_list)
            conn.commit()
            return len(records)
    
    def update(self, id_value: Any, data: Dict[str, Any]) -> bool:
        """
        Update a record by ID.
        
        Returns:
            True if a record was updated, False otherwise
        """
        set_clause = ", ".join([f"{col} = ?" for col in data.keys()])
        query = f"UPDATE {self.table_name} SET {set_clause} WHERE {self.id_column} = ?"
        
        with get_db_context() as conn:
            cursor = conn.execute(query, list(data.values()) + [id_value])
            conn.commit()
            return cursor.rowcount > 0
    
    def update_where(self, conditions: Dict[str, Any], data: Dict[str, Any]) -> int:
        """
        Update records matching conditions.
        
        Returns:
            Number of records updated
        """
        set_clause = ", ".join([f"{col} = ?" for col in data.keys()])
        where_clause = " AND ".join([f"{col} = ?" for col in conditions.keys()])
        query = f"UPDATE {self.table_name} SET {set_clause} WHERE {where_clause}"
        
        with get_db_context() as conn:
            cursor = conn.execute(query, list(data.values()) + list(conditions.values()))
            conn.commit()
            return cursor.rowcount
    
    def delete(self, id_value: Any) -> bool:
        """
        Delete a record by ID.
        
        Returns:
            True if a record was deleted, False otherwise
        """
        query = f"DELETE FROM {self.table_name} WHERE {self.id_column} = ?"
        
        with get_db_context() as conn:
            cursor = conn.execute(query, (id_value,))
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_where(self, conditions: Dict[str, Any]) -> int:
        """
        Delete records matching conditions.
        
        Returns:
            Number of records deleted
        """
        where_clause = " AND ".join([f"{col} = ?" for col in conditions.keys()])
        query = f"DELETE FROM {self.table_name} WHERE {where_clause}"
        
        with get_db_context() as conn:
            cursor = conn.execute(query, list(conditions.values()))
            conn.commit()
            return cursor.rowcount
    
    # ========== UTILITY METHODS ==========
    
    def execute_query(self, query: str, params: Tuple = ()) -> List[sqlite3.Row]:
        """Execute a custom query and return results."""
        with get_db_context() as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchall()
    
    def execute_update(self, query: str, params: Tuple = ()) -> int:
        """
        Execute a custom UPDATE/DELETE query.
        
        Returns:
            Number of rows affected
        """
        with get_db_context() as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor.rowcount
    
    @contextmanager
    def transaction(self):
        """
        Context manager for explicit transaction control.
        
        Example:
            with repo.transaction() as conn:
                conn.execute("UPDATE ...")
                conn.execute("INSERT ...")
                # Auto-commits on success, rolls back on exception
        """
        conn = get_db_connection()
        try:
            yield conn
            conn.commit()
        except sqlite3.IntegrityError as e:
            conn.rollback()
            log_exception(e, f"{self.table_name}_transaction", context={"operation": "commit"}, severity="warning")
            raise DatabaseError(f"Integrity constraint violation in {self.table_name}", context={"error": str(e)})
        except sqlite3.OperationalError as e:
            conn.rollback()
            log_exception(e, f"{self.table_name}_transaction", context={"operation": "commit"}, severity="error")
            raise DatabaseError(f"Database operational error in {self.table_name}", context={"error": str(e)})
        except Exception as e:
            conn.rollback()
            log_exception(e, f"{self.table_name}_transaction", context={"operation": "commit"}, severity="error")
            raise
        finally:
            conn.close()
