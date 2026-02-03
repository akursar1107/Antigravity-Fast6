"""
Unified Caching Layer

Provides consistent caching patterns across the application with clear TTL configuration.
Supports both Streamlit caching (production) and manual caching (testing/offline).

Features:
- Centralized TTL configuration
- Conditional Streamlit integration
- Cache invalidation triggers
- Decorator-based caching
- Cache statistics tracking
"""

import logging
import time
from typing import Optional, Callable, Any, Dict, TypeVar, Tuple
from functools import wraps
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import config

logger = logging.getLogger(__name__)

try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False

T = TypeVar('T')


# ============= CACHE TTL CONFIGURATION =============
# All cache TTLs in seconds - centralized for easy adjustment
class CacheTTL:
    """Cache time-to-live constants (in seconds)."""
    # Data layer caches
    LEADERBOARD = 300  # 5 minutes - high-traffic, low-change data
    USER_STATS = 300  # 5 minutes
    WEEKLY_SUMMARY = 300  # 5 minutes
    SCHEDULE = 3600  # 1 hour - stable data
    PLAYER_STATS = 1800  # 30 minutes
    TEAM_RATINGS = 1800  # 30 minutes
    
    # API caches
    ODDS_API = config.ODDS_API_CACHE_TTL if hasattr(config, 'ODDS_API_CACHE_TTL') else 3600
    POLYMARKET = config.POLYMARKET_CACHE_TTL if hasattr(config, 'POLYMARKET_CACHE_TTL') else 3600
    KALSHI = config.KALSHI_CACHE_TTL if hasattr(config, 'KALSHI_CACHE_TTL') else 3600
    
    # NFL data caches
    NFL_PBP = 3600  # 1 hour - play-by-play data (stable)
    NFL_SCHEDULE = 3600  # 1 hour
    NFL_ROSTERS = 3600  # 1 hour


@dataclass
class CacheStats:
    """Track cache performance metrics."""
    hits: int = 0
    misses: int = 0
    clears: int = 0
    last_cleared: Optional[datetime] = None
    creation_time: datetime = field(default_factory=datetime.now)
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate percentage."""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0
    
    def __str__(self) -> str:
        """Pretty print cache stats."""
        uptime = datetime.now() - self.creation_time
        return f"Hits: {self.hits} | Misses: {self.misses} | Rate: {self.hit_rate:.1f}% | Uptime: {uptime}"


# Global cache statistics tracker
_cache_stats: Dict[str, CacheStats] = {}


def get_cache_stats(cache_name: str) -> CacheStats:
    """Get or create cache statistics."""
    if cache_name not in _cache_stats:
        _cache_stats[cache_name] = CacheStats()
    return _cache_stats[cache_name]


def clear_all_caches() -> None:
    """Clear all caches (for testing/refresh)."""
    if HAS_STREAMLIT:
        try:
            st.cache_data.clear()
            logger.info("Cleared all Streamlit data caches")
            for stats in _cache_stats.values():
                stats.clears += 1
                stats.last_cleared = datetime.now()
        except Exception as e:
            logger.warning(f"Could not clear Streamlit cache: {e}")


def invalidate_cache(cache_name: str) -> None:
    """Invalidate a specific cache by name."""
    if cache_name in _cache_stats:
        _cache_stats[cache_name].clears += 1
        _cache_stats[cache_name].last_cleared = datetime.now()
    logger.debug(f"Invalidated cache: {cache_name}")


# ============= CACHE INVALIDATION TRIGGERS =============

def invalidate_on_pick_change() -> None:
    """Called when picks are added/updated/deleted."""
    invalidate_cache("leaderboard")
    invalidate_cache("user_stats")
    invalidate_cache("weekly_summary")
    if HAS_STREAMLIT:
        try:
            # Clear specific cached functions
            from database.stats import get_leaderboard, get_user_stats, get_weekly_summary
            get_leaderboard.clear()
            get_user_stats.clear()
            get_weekly_summary.clear()
            logger.debug("Invalidated pick-related caches")
        except Exception as e:
            logger.debug(f"Could not clear specific caches: {e}")


def invalidate_on_result_change() -> None:
    """Called when results are added/updated."""
    invalidate_cache("leaderboard")
    invalidate_cache("user_stats")
    invalidate_cache("weekly_summary")
    if HAS_STREAMLIT:
        try:
            from database.stats import get_leaderboard, get_user_stats, get_weekly_summary
            get_leaderboard.clear()
            get_user_stats.clear()
            get_weekly_summary.clear()
            logger.debug("Invalidated result-related caches")
        except Exception as e:
            logger.debug(f"Could not clear specific caches: {e}")


def invalidate_on_grading_complete() -> None:
    """Called after grading completes."""
    invalidate_on_result_change()
    invalidate_cache("player_stats")
    invalidate_cache("team_ratings")


def invalidate_on_player_stats_update() -> None:
    """Called when player stats are updated."""
    invalidate_cache("player_stats")
    invalidate_cache("leaderboard")


def invalidate_on_team_ratings_update() -> None:
    """Called when team ELO ratings are updated."""
    invalidate_cache("team_ratings")


# ============= CACHING DECORATORS =============

def cached(ttl: int, cache_name: Optional[str] = None):
    """
    Decorator for caching function results using Streamlit or manual caching.
    
    Args:
        ttl: Time to live in seconds
        cache_name: Optional name for cache tracking/invalidation
        
    Example:
        @cached(ttl=CacheTTL.USER_STATS, cache_name="user_stats")
        def get_user_score(user_id: int) -> int:
            # Expensive computation
            return compute_score(user_id)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        cache_key = cache_name or func.__name__
        stats = get_cache_stats(cache_key)
        
        if HAS_STREAMLIT:
            # Use Streamlit's caching in production
            try:
                cached_func = st.cache_data(ttl=ttl, show_spinner=False)(func)
                
                @wraps(func)
                def wrapper(*args, **kwargs) -> T:
                    stats.hits += 1
                    return cached_func(*args, **kwargs)
                
                return wrapper
            except RuntimeError:
                # Not in Streamlit context, fall back to manual caching
                pass
        
        # Manual caching for non-Streamlit contexts
        _manual_cache: Dict[Tuple, Tuple[datetime, Any]] = {}
        
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # Create cache key from args/kwargs
            cache_key_tuple = (func.__name__, args, tuple(sorted(kwargs.items())))
            
            if cache_key_tuple in _manual_cache:
                cached_time, cached_result = _manual_cache[cache_key_tuple]
                if (datetime.now() - cached_time).total_seconds() < ttl:
                    stats.hits += 1
                    return cached_result
                else:
                    # Expired
                    del _manual_cache[cache_key_tuple]
            
            # Cache miss
            stats.misses += 1
            result = func(*args, **kwargs)
            _manual_cache[cache_key_tuple] = (datetime.now(), result)
            
            return result
        
        return wrapper
    
    return decorator


def cache_if_streamlit(func: Callable[..., T], ttl: int = 3600) -> Callable[..., T]:
    """
    Decorator that applies caching if Streamlit is available.
    Falls back to original function if not in Streamlit context.
    
    Args:
        func: Function to potentially cache
        ttl: Time to live in seconds
        
    Example:
        @cache_if_streamlit
        def expensive_operation():
            return compute_something()
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> T:
        if HAS_STREAMLIT:
            try:
                cached_func = st.cache_data(ttl=ttl, show_spinner=False)(func)
                return cached_func(*args, **kwargs)
            except RuntimeError:
                # Not in Streamlit context
                return func(*args, **kwargs)
        else:
            return func(*args, **kwargs)
    
    return wrapper


# ============= LEGACY COMPATIBILITY =============

def _cache_if_streamlit(func):
    """
    Legacy decorator for backward compatibility.
    Deprecated - use @cached() or @cache_if_streamlit instead.
    """
    logger.warning(f"Using deprecated _cache_if_streamlit for {func.__name__}. Use @cached() instead.")
    return cache_if_streamlit(func, ttl=300)


def clear_leaderboard_cache() -> None:
    """
    Clear only the leaderboard-related caches when results are updated.
    
    Deprecated - use invalidate_on_result_change() instead.
    This function is kept for backward compatibility.
    """
    invalidate_on_result_change()


# ============= CACHE REPORTING =============

def get_all_cache_stats() -> Dict[str, str]:
    """Get statistics for all caches."""
    return {name: str(stats) for name, stats in _cache_stats.items()}


def log_cache_stats() -> None:
    """Log all cache statistics."""
    logger.info("=== Cache Statistics ===")
    for name, stats in _cache_stats.items():
        logger.info(f"{name}: {stats}")
    logger.info("=======================")
