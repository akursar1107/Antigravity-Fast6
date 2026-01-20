"""
Data models for Fast6 application.

Provides typed dataclass models for all entities, replacing dict-based returns.
Enables better IDE support, type checking, and self-documenting code.
"""

from .user import User
from .week import Week
from .pick import Pick
from .result import Result

__all__ = [
    'User',
    'Week',
    'Pick',
    'Result',
]
