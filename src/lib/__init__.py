"""Shared infrastructure utilities - no business logic, no Streamlit coupling"""

from src.lib.observability import log_event, track_operation
from src.lib.resilience import CircuitBreaker, request_with_retry, get_circuit_breaker
from src.lib.caching import cached, invalidate_cache, clear_all_caches, cache_if_streamlit, CacheTTL
from src.lib.error_handling import (
    Fast6Error, DatabaseError, ValidationError, APIError, 
    log_exception, handle_exception, auto_log_errors, safe_execute
)
from src.lib.types import *
from src.lib.theming import apply_global_theme, generate_theme_css

__all__ = [
    # Observability
    "log_event",
    "track_operation",
    # Resilience
    "CircuitBreaker",
    "request_with_retry",
    "get_circuit_breaker",
    # Caching
    "cached",
    "invalidate_cache",
    "clear_all_caches",
    "cache_if_streamlit",
    "CacheTTL",
    # Error Handling
    "Fast6Error",
    "DatabaseError", 
    "ValidationError",
    "APIError",
    "log_exception",
    "handle_exception",
    "auto_log_errors",
    "safe_execute",
    # UI
    "apply_global_theme",
    "generate_theme_css",
]
