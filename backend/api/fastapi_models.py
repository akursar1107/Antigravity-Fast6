"""Pydantic Models for FastAPI Request/Response Validation"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ============================================================================
# Authentication Models
# ============================================================================

class LoginRequest(BaseModel):
    """User login request (username-based for friend group)"""
    username: str = Field(..., min_length=1, description="Username to login")


class TokenResponse(BaseModel):
    """JWT token response after successful login"""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    user_id: int = Field(..., description="Authenticated user ID")
    username: str = Field(..., description="Authenticated username")
    role: str = Field(..., description="User role (admin/user)")


class UserResponse(BaseModel):
    """User information response"""
    id: int = Field(..., description="User ID")
    name: str = Field(..., description="User display name")
    email: Optional[str] = Field(None, description="User email")
    is_admin: bool = Field(default=False, description="Admin status")
    base_bet: Optional[float] = Field(None, description="User's default bet amount for ROI")
    created_at: Optional[datetime] = Field(None, description="User creation date")
    
    class Config:
        from_attributes = True


# ============================================================================
# User Management Models
# ============================================================================

class UserCreate(BaseModel):
    """Create new user (admin only)"""
    name: str = Field(..., min_length=1, max_length=100, description="Display name")
    email: Optional[str] = Field(None, description="Email address")
    is_admin: bool = Field(default=False, description="Admin privilege")


class UserUpdate(BaseModel):
    """Update user profile (admin only, except base_bet which users can set for themselves)"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[str] = Field(None)
    is_admin: Optional[bool] = Field(None)
    base_bet: Optional[float] = Field(None, ge=0.1, le=10000, description="Default bet amount")


class BaseBetUpdate(BaseModel):
    """Update user's base bet (own profile only)"""
    base_bet: float = Field(..., ge=0.1, le=10000, description="Default bet amount per pick")


# ============================================================================
# Week/Season Models
# ============================================================================

class WeekCreate(BaseModel):
    """Create a new week/season"""
    season: int = Field(..., ge=1900, le=2100, description="NFL season year")
    week: int = Field(..., ge=1, le=18, description="Week number (1-18)")
    started_at: datetime = Field(..., description="Week start time")
    ended_at: datetime = Field(..., description="Week end time")


class WeekResponse(BaseModel):
    """Week information response"""
    id: int
    season: int
    week: int
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ============================================================================
# Pick Models
# ============================================================================

class PickCreate(BaseModel):
    """Create a new pick"""
    week_id: int = Field(..., description="Week ID")
    team: str = Field(..., min_length=1, max_length=50, description="Team abbreviation")
    player_name: str = Field(..., min_length=1, max_length=100, description="Player name")
    odds: Optional[float] = Field(None, description="Betting odds")
    game_id: Optional[str] = Field(None, description="NFL game ID")


class AdminPickCreate(BaseModel):
    """Create a pick for a user (admin only)"""
    user_id: int = Field(..., description="User ID")
    week_id: int = Field(..., description="Week ID")
    team: str = Field(..., min_length=1, max_length=50, description="Team abbreviation")
    player_name: str = Field(..., min_length=1, max_length=100, description="Player name")
    odds: Optional[float] = Field(None, description="Betting odds")
    game_id: Optional[str] = Field(None, description="NFL game ID")


class PickResponse(BaseModel):
    """Pick information response"""
    id: int
    user_id: int
    week_id: int
    team: str
    player_name: str
    odds: Optional[float] = None
    game_id: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class PickUpdate(BaseModel):
    """Update pick (before grading)"""
    team: Optional[str] = None
    player_name: Optional[str] = None
    odds: Optional[float] = None


# ============================================================================
# Result Models (Grading)
# ============================================================================

class ResultCreate(BaseModel):
    """Create a grading result"""
    pick_id: int = Field(..., description="Pick ID being graded")
    actual_scorer: Optional[str] = Field(None, description="Actual scorer name")
    is_correct: bool = Field(..., description="Whether pick was correct")
    any_time_td: Optional[bool] = Field(None, description="Any-time TD occurred")
    payout: Optional[float] = Field(None, description="Payout value")


class ResultUpdate(BaseModel):
    """Update grading result (admin only)"""
    is_correct: bool = Field(..., description="Whether pick was correct (win/loss)")


class ResultResponse(BaseModel):
    """Result/Grading information response"""
    id: int
    pick_id: int
    actual_scorer: Optional[str] = None
    is_correct: bool
    any_time_td: Optional[bool] = None
    payout: Optional[float] = None
    graded_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# Leaderboard Models
# ============================================================================

class LeaderboardEntry(BaseModel):
    """Leaderboard entry for a user in a week"""
    user_id: int = Field(..., description="User ID")
    username: str = Field(..., description="User display name")
    picks_count: int = Field(..., description="Number of picks")
    correct_count: int = Field(..., description="Number correct")
    total_points: float = Field(..., description="Total points scored")
    roi: Optional[float] = Field(None, description="Return on investment")
    
    class Config:
        from_attributes = True


# ============================================================================
# Error Models
# ============================================================================

class ErrorResponse(BaseModel):
    """Standardized error response"""
    error: str = Field(..., description="Error type/message")
    detail: Optional[str] = Field(None, description="Error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = Field(None, description="Request tracking ID")
