"""
Type Definitions for Fast6

Provides TypedDict definitions and generic types for better type safety across the application.
This enables IDE autocomplete, better type checking with mypy, and clearer API contracts.

Usage:
    from src.utils.types import Pick, User, Result, Leaderboard
    
    def get_picks(user_id: int) -> List[Pick]:
        return database.get_user_picks(user_id)
"""

from typing import TypedDict, Optional, List, Dict, Any, Tuple, Generic, TypeVar
try:
    from typing import NotRequired
except ImportError:
    from typing_extensions import NotRequired
from datetime import datetime


# ============= DATABASE TYPES =============

class User(TypedDict):
    """User in the Fast6 group."""
    id: int
    name: str
    email: Optional[str]
    group_id: int
    is_admin: bool
    created_at: datetime


class Week(TypedDict):
    """Week/season information."""
    id: int
    season: int
    week: int
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    created_at: datetime


class Pick(TypedDict):
    """User's prediction for a week."""
    id: int
    user_id: int
    week_id: int
    team: str
    player_name: str
    odds: Optional[float]
    theoretical_return: Optional[float]
    game_id: Optional[str]
    created_at: datetime


class Result(TypedDict):
    """Actual outcome of a pick."""
    id: int
    pick_id: int
    actual_scorer: Optional[str]
    is_correct: Optional[bool]
    actual_return: Optional[float]
    any_time_td: Optional[bool]
    created_at: datetime


class PickWithResult(TypedDict):
    """Pick combined with its result."""
    id: int
    user_id: int
    week_id: int
    team: str
    player_name: str
    odds: Optional[float]
    theoretical_return: Optional[float]
    game_id: Optional[str]
    is_correct: Optional[bool]
    actual_scorer: Optional[str]
    actual_return: Optional[float]
    any_time_td: Optional[bool]


class LeaderboardEntry(TypedDict):
    """Single entry in the leaderboard."""
    id: int
    name: str
    points: int
    total_return: Optional[float]
    first_td_wins: int
    any_time_tds: int


class WeekSummary(TypedDict):
    """Summary statistics for a week."""
    week_id: int
    season: int
    week: int
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    total_picks: int
    graded_picks: int
    correct_picks: int


class KickoffDecision(TypedDict):
    """Team kickoff decision and result."""
    id: int
    game_id: str
    team: str
    decision: str  # 'receive' or 'defer'
    result: Optional[str]  # Outcome of the decision
    created_at: datetime


class MarketOdds(TypedDict):
    """Prediction market odds from Polymarket or Kalshi."""
    id: int
    game_id: str
    player_name: str
    source: str  # 'polymarket' or 'kalshi'
    odds: float
    timestamp: datetime
    created_at: datetime


# ============= API TYPES =============

class OddsData(TypedDict):
    """Odds for a single player."""
    player_name: str
    price: float
    source: str


class GameOdds(TypedDict):
    """Odds for all players in a game."""
    home_team: str
    away_team: str
    game_id: Optional[str]
    timestamp: datetime
    odds: Dict[str, float]  # {player_name: price}


class PolymarketMarketData(TypedDict):
    """Polymarket market data."""
    condition_id: str
    question: str
    slug: str
    outcome_prices: List[float]
    token_ids: List[str]
    volume: float
    end_date: Optional[datetime]
    active: bool
    closed: bool


class KalshiMarketData(TypedDict):
    """Kalshi market data."""
    id: str
    title: str
    subtitle: str
    last_price: Optional[float]
    status: str


# ============= CONFIGURATION TYPES =============

class ScoringConfig(TypedDict):
    """Scoring rule configuration."""
    first_td_win: int
    any_time_td: int
    name_match_threshold: float
    auto_grade_enabled: bool


class APIConfig(TypedDict):
    """API configuration."""
    enabled: bool
    cache_ttl: int
    timeout: int


class OddsAPIConfig(APIConfig):
    """Odds API specific configuration."""
    base_url: str
    sport: str
    market: str
    regions: str
    format: str


class UIThemeConfig(TypedDict):
    """UI theme colors and styles."""
    primary_color: str
    secondary_color: str
    background_color: str
    text_color: str
    success_color: str
    error_color: str
    warning_color: str
    info_color: str
    border_radius: str
    font_family: str


# ============= OPERATION RESULT TYPES =============

class OperationResult(TypedDict):
    """Result of a database operation."""
    success: bool
    message: str
    error: NotRequired[str]
    data: NotRequired[Dict[str, Any]]


class ImportResult(TypedDict):
    """Result of a CSV import operation."""
    success_count: int
    error_count: int
    warning_count: int
    errors: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]


class GradingResult(TypedDict):
    """Result of a grading operation."""
    graded_count: int
    correct_count: int
    any_time_td_count: int
    errors: NotRequired[List[str]]


class BatchOperationResult(TypedDict):
    """Result of a batch operation."""
    inserted: int
    updated: int
    deleted: int
    errors: NotRequired[List[str]]


# ============= GENERIC TYPES =============

T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')


class CachedValue(Generic[T]):
    """Generic cached value with metadata."""
    def __init__(self, value: T, ttl_seconds: int, created_at: datetime):
        self.value: T = value
        self.ttl_seconds: int = ttl_seconds
        self.created_at: datetime = created_at
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        from datetime import datetime as dt
        elapsed = (dt.now() - self.created_at).total_seconds()
        return elapsed > self.ttl_seconds


class Repository(Generic[T]):
    """Generic repository base class for CRUD operations."""
    def __init__(self, entity_type: type):
        self.entity_type = entity_type
    
    def find_by_id(self, id_value: int) -> Optional[T]:
        """Find entity by ID."""
        raise NotImplementedError
    
    def find_all(self) -> List[T]:
        """Find all entities."""
        raise NotImplementedError
    
    def create(self, entity: T) -> int:
        """Create new entity."""
        raise NotImplementedError
    
    def update(self, entity: T) -> bool:
        """Update entity."""
        raise NotImplementedError
    
    def delete(self, id_value: int) -> bool:
        """Delete entity."""
        raise NotImplementedError


# ============= QUERY TYPES =============

class QueryFilter(TypedDict):
    """Filter for database queries."""
    field: str
    operator: str  # 'eq', 'lt', 'gt', 'in', 'like'
    value: Any


class QueryResult(Generic[T]):
    """Generic query result with pagination."""
    def __init__(self, items: List[T], total: int, offset: int, limit: int):
        self.items: List[T] = items
        self.total: int = total
        self.offset: int = offset
        self.limit: int = limit
    
    @property
    def has_more(self) -> bool:
        """Check if there are more results."""
        return self.offset + self.limit < self.total
    
    @property
    def page_count(self) -> int:
        """Calculate total number of pages."""
        return (self.total + self.limit - 1) // self.limit
    
    @property
    def current_page(self) -> int:
        """Calculate current page number (1-indexed)."""
        return (self.offset // self.limit) + 1


# ============= VALIDATION TYPES =============

class ValidationError(TypedDict):
    """Single validation error."""
    field: str
    message: str
    value: NotRequired[Any]


class ValidationResult(TypedDict):
    """Result of data validation."""
    valid: bool
    errors: List[ValidationError]


# ============= ANALYTICS TYPES =============

class PlayerStats(TypedDict):
    """Player performance statistics."""
    player_name: str
    season: int
    team: str
    position: Optional[str]
    first_td_count: int
    any_time_td_count: int
    recent_form: Optional[str]  # 'hot', 'cold', 'neutral'
    accuracy_rate: Optional[float]


class TeamRating(TypedDict):
    """Team ELO rating."""
    team: str
    season: int
    week: int
    overall_rating: float
    offensive_rating: float
    defensive_rating: float


class PlayerPerformance(TypedDict):
    """Player's performance in predictions."""
    user_name: str
    total_picks: int
    correct_picks: int
    any_time_tds: int
    accuracy_rate: float
    roi: Optional[float]
    trend: str  # 'up', 'down', 'stable'


class ROITrend(TypedDict):
    """ROI trend over time."""
    user_name: str
    week: int
    roi: float
    cumulative_roi: float
    picks_count: int


# ============= HELPER FUNCTIONS =============

def pick_from_dict(data: Dict[str, Any]) -> Pick:
    """Create Pick TypedDict from dictionary."""
    return Pick(
        id=data['id'],
        user_id=data['user_id'],
        week_id=data['week_id'],
        team=data['team'],
        player_name=data['player_name'],
        odds=data.get('odds'),
        theoretical_return=data.get('theoretical_return'),
        game_id=data.get('game_id'),
        created_at=data.get('created_at', datetime.now())
    )


def user_from_dict(data: Dict[str, Any]) -> User:
    """Create User TypedDict from dictionary."""
    return User(
        id=data['id'],
        name=data['name'],
        email=data.get('email'),
        group_id=data.get('group_id', 1),
        is_admin=data.get('is_admin', False),
        created_at=data.get('created_at', datetime.now())
    )


def leaderboard_entry_from_dict(data: Dict[str, Any]) -> LeaderboardEntry:
    """Create LeaderboardEntry TypedDict from dictionary."""
    return LeaderboardEntry(
        id=data['id'],
        name=data['name'],
        points=data.get('points', 0),
        total_return=data.get('total_return'),
        first_td_wins=data.get('first_td_wins', 0),
        any_time_tds=data.get('any_time_tds', 0)
    )
