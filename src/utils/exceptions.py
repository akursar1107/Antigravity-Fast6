"""
Custom exception types for Fast6 application.
Provides user-friendly error messages for common failure scenarios.
"""


class Fast6Error(Exception):
    """Base exception for all Fast6 application errors."""
    pass


class DatabaseError(Fast6Error):
    """Database operation failed."""
    def __init__(self, message: str = "Database operation failed", original_error: Exception = None):
        self.original_error = original_error
        super().__init__(message)


class ValidationError(Fast6Error):
    """Data validation failed."""
    pass


class PickValidationError(ValidationError):
    """Pick data is invalid or incomplete."""
    pass


class UserValidationError(ValidationError):
    """User data is invalid."""
    pass


class WeekValidationError(ValidationError):
    """Week data is invalid."""
    pass


class DataNotFoundError(Fast6Error):
    """Expected data not found."""
    pass


class NFLDataError(DataNotFoundError):
    """NFL play-by-play data not available."""
    def __init__(self, season: int = None, week: int = None):
        self.season = season
        self.week = week
        msg = f"NFL data not found"
        if season:
            msg += f" for season {season}"
        if week:
            msg += f" week {week}"
        super().__init__(msg)


class GradingError(Fast6Error):
    """Pick grading operation failed."""
    pass


class ImportError(Fast6Error):
    """CSV import operation failed."""
    pass


class CacheError(Fast6Error):
    """Cache operation failed."""
    pass


class ConfigurationError(Fast6Error):
    """Application configuration is invalid or missing."""
    pass
