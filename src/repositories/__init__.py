"""
Repository pattern implementation for Fast6 data access layer.

This package provides a clean separation between data access and business logic.
Each repository encapsulates database operations for a specific entity.

Usage:
    from repositories import UsersRepository, PicksRepository
    
    with get_db_context() as conn:
        users_repo = UsersRepository(conn)
        user = users_repo.get_by_id(1)
"""

from .base_repository import BaseRepository
from .users_repository import UsersRepository
from .weeks_repository import WeeksRepository
from .picks_repository import PicksRepository
from .results_repository import ResultsRepository

__all__ = [
    'BaseRepository',
    'UsersRepository',
    'WeeksRepository',
    'PicksRepository',
    'ResultsRepository',
]
