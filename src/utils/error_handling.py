"""
Error Handling & Logging Utilities

Provides structured exception handling with context, logging, and user feedback.
Reduces code duplication and ensures consistent error handling patterns.
"""

import logging
import traceback
from typing import Optional, Callable, TypeVar, Any
from functools import wraps
from enum import Enum

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ErrorSeverity(Enum):
    """Error severity levels for user-facing messages."""
    INFO = "ℹ️"
    WARNING = "⚠️"
    ERROR = "❌"
    CRITICAL = "🔴"


class Fast6Error(Exception):
    """Base exception for Fast6-specific errors."""
    def __init__(self, message: str, context: Optional[dict] = None):
        self.message = message
        self.context = context or {}
        super().__init__(message)


class DatabaseError(Fast6Error):
    """Database operation error."""
    pass


class ValidationError(Fast6Error):
    """Data validation error."""
    pass


class APIError(Fast6Error):
    """External API error."""
    pass


def log_exception(
    exception: Exception,
    operation: str,
    context: Optional[dict] = None,
    severity: str = "error"
) -> None:
    """
    Log exception with structured context.
    
    Args:
        exception: The exception to log
        operation: Description of the operation that failed (e.g., "fetch_odds_api")
        context: Dict with additional context (e.g., {"player": "Mahomes", "game_id": "123"})
        severity: Log level ("debug", "info", "warning", "error", "critical")
    """
    context = context or {}
    error_type = type(exception).__name__
    
    log_data = {
        "operation": operation,
        "error_type": error_type,
        "message": str(exception),
        **context
    }
    
    log_msg = f"[{operation}] {error_type}: {exception}"
    if context:
        log_msg += f" | Context: {context}"
    
    getattr(logger, severity.lower(), logger.error)(log_msg, extra=log_data)


def handle_exception(
    exception: Exception,
    operation: str,
    default_return: Any = None,
    context: Optional[dict] = None,
    severity: str = "error",
    raise_on_critical: bool = False
) -> Any:
    """
    Centralized exception handler with logging and context.
    
    Args:
        exception: The exception to handle
        operation: Description of operation (e.g., "grade_picks")
        default_return: Value to return on error (graceful degradation)
        context: Additional context dict
        severity: Log severity level
        raise_on_critical: Re-raise if Critical error type
        
    Returns:
        default_return value (graceful degradation)
        
    Example:
        try:
            result = risky_operation()
        except Exception as e:
            return handle_exception(
                e, 
                "risky_operation",
                default_return=[],
                context={"input": data}
            )
    """
    log_exception(exception, operation, context, severity)
    
    if raise_on_critical and isinstance(exception, Fast6Error):
        raise
    
    return default_return


def auto_log_errors(operation: str, severity: str = "error"):
    """
    Decorator for automatic exception logging on function calls.
    
    Args:
        operation: Description of operation for logging
        severity: Log severity level
        
    Example:
        @auto_log_errors("fetch_player_stats")
        def get_player_stats(player_id: int) -> Dict:
            # Exceptions automatically logged
            pass
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                context = {
                    "function": func.__name__,
                    "args": str(args)[:100],  # Truncate for logging
                    "kwargs": str(kwargs)[:100]
                }
                log_exception(e, operation, context, severity)
                raise
        return wrapper
    return decorator


def safe_execute(
    func: Callable[..., T],
    *args,
    operation: str,
    default_return: Any = None,
    context: Optional[dict] = None,
    **kwargs
) -> T:
    """
    Safely execute function with automatic error handling.
    
    Args:
        func: Function to execute
        operation: Description for logging
        default_return: Return value on error
        context: Additional context
        *args, **kwargs: Arguments for func
        
    Returns:
        Function result or default_return on error
        
    Example:
        result = safe_execute(
            get_odds,
            api_key,
            operation="fetch_odds",
            default_return={}
        )
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        handle_exception(e, operation, default_return, context)
        return default_return


def format_error_message(
    error_type: str,
    operation: str,
    user_friendly: bool = True
) -> str:
    """
    Format error message for user or log output.
    
    Args:
        error_type: Type of error (e.g., "TimeoutError")
        operation: Operation that failed
        user_friendly: If True, return user-safe message; else technical
        
    Returns:
        Formatted error message
    """
    if user_friendly:
        # User-friendly error messages (safe for Streamlit display)
        messages = {
            "TimeoutError": f"⏱️ {operation} took too long. Please try again.",
            "HTTPError": f"🌐 Connection issue during {operation}. Please try again.",
            "RequestException": f"🔗 Network error during {operation}. Check your connection.",
            "ValueError": f"📋 Invalid data received during {operation}. Please try again.",
            "DatabaseError": f"💾 Database error during {operation}. Please try again.",
            "ValidationError": f"✓ Invalid input for {operation}. Please check your data.",
        }
        return messages.get(error_type, f"❌ Error during {operation}. Please try again.")
    else:
        # Technical error message for logs
        return f"[{operation}] {error_type}"
