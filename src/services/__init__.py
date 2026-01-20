"""
Service layer initialization.

Services encapsulate business logic and orchestrate operations across multiple repositories.
They provide a clean separation between business rules and data access.
"""

from .grading_service import GradingService

__all__ = [
    'GradingService',
]
