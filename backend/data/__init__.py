"""Data access layer - repository implementations.

Note: Prefer database.picks, database.stats, etc. for most operations.
These adapters (SQLitePickRepository, SQLiteResultRepository) implement
the core/picks and core/grading ports but are not wired to the API.
"""

from backend.database.adapters.base import BaseRepository
from backend.database.adapters.picks_repository import SQLitePickRepository
from backend.database.adapters.results_repository import SQLiteResultRepository

__all__ = [
    "BaseRepository",
    "SQLitePickRepository",
    "SQLiteResultRepository",
]
