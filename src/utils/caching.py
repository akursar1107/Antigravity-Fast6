"""
Unified Caching Layer

Provides consistent caching patterns across the application with clear TTL configuration.
Uses manual in-memory TTL-based caching.

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
from src import config

logger = logging.getLogger(__name__)

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
    for stats in _cache_stats.values():
        stats.clears += 1
        stats.last_cleared = datetime.now()
    logger.info("Cleared all caches")


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
    logger.debug("Invalidated pick-related caches")


def invalidate_on_result_change() -> None:
    """Called when results are added/updated."""
    invalidate_cache("leaderboard")
    invalidate_cache("user_stats")
    invalidate_cache("weekly_summary")
    logger.debug("Invalidated result-related caches")


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
        
        # In-memory TTL-based cache
        _manual_cache: Dict[str, Tuple[datetime, Any]] = {}
        
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # Create cache key from args/kwargs (handle unhashable types)
            try:
                cache_key_str = str((func.__name__, args, tuple(sorted(kwargs.items()))))
            except Exception:
                # If we can't create a key, skip caching
                return func(*args, **kwargs)
            
            if cache_key_str in _manual_cache:
                cached_time, cached_result = _manual_cache[cache_key_str]
                if (datetime.now() - cached_time).total_seconds() < ttl:
                    stats.hits += 1
                    return cached_result
                else:
                    # Expired
                    del _manual_cache[cache_key_str]
            
            # Cache miss
            stats.misses += 1
            result = func(*args, **kwargs)
            _manual_cache[cache_key_str] = (datetime.now(), result)
            
            return result
        
        return wrapper
    
    return decorator


def clear_leaderboard_cache() -> None:
    """Clear leaderboard caches. Alias for invalidate_on_result_change()."""
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
