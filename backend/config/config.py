"""
Configuration and Constants

Loads settings from backend.config.json with support for environment variable overrides.
For sensitive values like API keys, environment variables are used.
"""

import json
import os
from pathlib import Path
import logging
from typing import List

logger = logging.getLogger(__name__)

# Load configuration from JSON
_config_path = Path(__file__).parent / "config.json"
try:
    with open(_config_path) as f:
        _CONFIG = json.load(f)
    logger.info(f"Loaded configuration from {_config_path}")
except Exception as e:
    logger.error(f"Failed to load configuration from {_config_path}: {e}")
    _CONFIG = {}


def _validate_config(config: dict) -> List[str]:
    """Validate configuration structure and values. Returns list of warnings."""
    warnings: List[str] = []

    app = config.get("app", {})
    seasons = config.get("seasons", [])
    scoring = config.get("scoring", {})
    analytics = config.get("analytics", {})
    teams = config.get("teams", {})
    api = config.get("api", {})
    theme = config.get("ui_theme", {})

    # App config validation
    if not app.get("name"):
        warnings.append("app.name is missing or empty")
    if not isinstance(app.get("current_season", None), int):
        warnings.append("app.current_season should be an integer")

    # Seasons validation
    if not isinstance(seasons, list) or not seasons:
        warnings.append("seasons should be a non-empty list")
    else:
        if not all(isinstance(s, int) for s in seasons):
            warnings.append("seasons should contain only integers")
        if seasons != sorted(seasons, reverse=True):
            warnings.append("seasons should be in descending order (newest first)")
        if isinstance(app.get("current_season", None), int) and app.get("current_season") not in seasons:
            warnings.append("app.current_season is not present in seasons list")

    # Scoring validation
    first_td = scoring.get("first_td_win", None)
    any_time = scoring.get("any_time_td", None)
    threshold = scoring.get("name_match_threshold", None)

    if not isinstance(first_td, int) or first_td < 0:
        warnings.append("scoring.first_td_win should be a non-negative integer")
    if not isinstance(any_time, int) or any_time < 0:
        warnings.append("scoring.any_time_td should be a non-negative integer")
    if isinstance(first_td, int) and isinstance(any_time, int) and first_td < any_time:
        warnings.append("scoring.first_td_win should be >= scoring.any_time_td")
    if not isinstance(threshold, (int, float)) or not (0 <= threshold <= 1):
        warnings.append("scoring.name_match_threshold should be between 0 and 1")

    # Analytics validation
    buckets = analytics.get("odds_buckets", [])
    if buckets:
        for bucket in buckets:
            if not isinstance(bucket, dict):
                warnings.append("analytics.odds_buckets should contain dict items")
                break
            if "min" not in bucket or "max" not in bucket or "label" not in bucket:
                warnings.append("analytics.odds_buckets items must include min, max, label")
                break
            if not isinstance(bucket.get("min"), int) or not isinstance(bucket.get("max"), int):
                warnings.append("analytics.odds_buckets min/max should be integers")
                break
            if bucket.get("min") >= bucket.get("max"):
                warnings.append("analytics.odds_buckets min must be < max")
                break

    # Teams validation
    if not isinstance(teams, dict) or not teams:
        warnings.append("teams should be a non-empty dictionary")

    # API validation
    odds_api = api.get("odds_api", {})
    if odds_api.get("enabled", True) and not odds_api.get("base_url"):
        warnings.append("api.odds_api.base_url is missing while odds_api is enabled")
    if not isinstance(odds_api.get("cache_ttl", 0), int) or odds_api.get("cache_ttl", 0) <= 0:
        warnings.append("api.odds_api.cache_ttl should be a positive integer")

    # Theme validation (basic)
    if theme and not theme.get("primary_color"):
        warnings.append("ui_theme.primary_color is missing")

    return warnings

# ===== APP CONFIGURATION =====
APP_NAME = _CONFIG.get("app", {}).get("name", "Fast6")
APP_VERSION = _CONFIG.get("app", {}).get("version", "1.0.0")
CURRENT_SEASON = _CONFIG.get("app", {}).get("current_season", 2025)
CURRENT_WEEK = _CONFIG.get("app", {}).get("current_week", 1)  # Default to week 1
DATABASE_PATH = _CONFIG.get("app", {}).get("database_path", "data/fast6.db")

# ===== SEASONS =====
SEASONS = _CONFIG.get("seasons", [2025, 2024, 2023, 2022, 2021, 2020])

# ===== SCORING CONFIGURATION =====
SCORING_FIRST_TD = _CONFIG.get("scoring", {}).get("first_td_win", 3)
SCORING_ANY_TIME = _CONFIG.get("scoring", {}).get("any_time_td", 1)
NAME_MATCH_THRESHOLD = _CONFIG.get("scoring", {}).get("name_match_threshold", 0.75)
AUTO_GRADE_ENABLED = _CONFIG.get("scoring", {}).get("auto_grade_enabled", True)

# ===== ANALYTICS CONFIGURATION =====
_analytics = _CONFIG.get("analytics", {})
DEFAULT_ODDS = _analytics.get("default_odds", 250)
ROI_STAKE = _analytics.get("roi_stake", 1)  # Default bet per pick ($) for ROI calculation
# Convert JSON format to tuple format: [(min, max, label), ...]
_buckets_config = _analytics.get("odds_buckets", [
    {"min": 100, "max": 300, "label": "Favorites"},
    {"min": 300, "max": 500, "label": "Moderate"},
    {"min": 500, "max": 700, "label": "Longshots"},
    {"min": 700, "max": 1000, "label": "Heavy Longshots"},
    {"min": 1000, "max": 5000, "label": "Extreme Longshots"}
])
ODDS_BUCKETS = [(b["min"], b["max"], b["label"]) for b in _buckets_config]

# ===== TEAM CONFIGURATION =====
_teams_config = _CONFIG.get("teams", {})
TEAM_MAP = {abbr: info.get("full_name", "") for abbr, info in _teams_config.items()}

# Build reverse map: full name -> abbreviation
TEAM_ABBR_MAP = {
    info.get("full_name"): abbr for abbr, info in _teams_config.items()
}

# Add short city name mappings for CSV compatibility
_short_names = {
    "Arizona": "ARI", "Atlanta": "ATL", "Baltimore": "BAL", "Buffalo": "BUF",
    "Carolina": "CAR", "Chicago": "CHI", "Cincinnati": "CIN", "Cleveland": "CLE",
    "Dallas": "DAL", "Denver": "DEN", "Detroit": "DET", "Green Bay": "GB",
    "Houston": "HOU", "Indianapolis": "IND", "Jacksonville": "JAX", "Kansas City": "KC",
    "Las Vegas": "LV", "LA Chargers": "LAC", "LA Rams": "LA", "Miami": "MIA",
    "Minnesota": "MIN", "New England": "NE", "New Orleans": "NO", "NY Giants": "NYG",
    "NY Jets": "NYJ", "Philadelphia": "PHI", "Pittsburgh": "PIT", "San Francisco": "SF",
    "Seattle": "SEA", "Tampa Bay": "TB", "Tennessee": "TEN", "Washington": "WAS"
}
TEAM_ABBR_MAP.update(_short_names)

# ===== API CONFIGURATION =====
_api_root = _CONFIG.get("api", {})
_api_config = _api_root.get("odds_api", {})

# For API key: check environment variables
ODDS_API_KEY = os.getenv("ODDS_API_KEY", "")

# Only warn if odds features are explicitly enabled and key is missing
# This allows graceful degradation when odds API is not configured
if not ODDS_API_KEY and _api_config.get("enabled", True):
    logger.debug("ODDS_API_KEY not configured; odds features will be unavailable")

ODDS_API_BASE_URL = _api_config.get("base_url", "https://api.the-odds-api.com/v4")
ODDS_API_SPORT = _api_config.get("sport", "americanfootball_nfl")
ODDS_API_MARKET = _api_config.get("market", "player_anytime_td")
ODDS_API_REGIONS = _api_config.get("regions", "us")
ODDS_API_FORMAT = _api_config.get("format", "american")
ODDS_API_CACHE_TTL = _api_config.get("cache_ttl", 3600)

# ===== API RESILIENCE CONFIGURATION =====
_retry_config = _api_root.get("retry", {})
API_RETRY_RETRIES = _retry_config.get("retries", 3)
API_RETRY_BACKOFF_BASE = _retry_config.get("backoff_base_seconds", 0.5)
API_RETRY_BACKOFF_FACTOR = _retry_config.get("backoff_factor", 2.0)
API_RETRY_JITTER = _retry_config.get("jitter_seconds", 0.1)

_breaker_config = _api_root.get("circuit_breaker", {})
API_BREAKER_FAILURE_THRESHOLD = _breaker_config.get("failure_threshold", 5)
API_BREAKER_COOLDOWN_SECONDS = _breaker_config.get("cooldown_seconds", 60)

# ===== POLYMARKET API CONFIGURATION =====
_polymarket_config = _CONFIG.get("api", {}).get("polymarket", {})
POLYMARKET_ENABLED = _polymarket_config.get("enabled", False)
POLYMARKET_GAMMA_URL = _polymarket_config.get("gamma_base_url", "https://gamma-api.polymarket.com")
POLYMARKET_CLOB_URL = _polymarket_config.get("clob_base_url", "https://clob.polymarket.com")
POLYMARKET_DATA_URL = _polymarket_config.get("data_base_url", "https://data-api.polymarket.com")
POLYMARKET_CACHE_TTL = _polymarket_config.get("cache_ttl", 3600)
POLYMARKET_KEYWORDS = _polymarket_config.get("search_keywords", ["NFL", "first touchdown"])

# ===== KALSHI API CONFIGURATION =====
_kalshi_config = _CONFIG.get("api", {}).get("kalshi", {})
KALSHI_ENABLED = _kalshi_config.get("enabled", False)
KALSHI_BASE_URL = _kalshi_config.get("base_url", "https://trading-api.kalshi.com/trade-api/v2")
KALSHI_CACHE_TTL = _kalshi_config.get("cache_ttl", 3600)
KALSHI_EVENT_CATEGORIES = _kalshi_config.get("event_categories", ["NFL", "football"])

# Kalshi API key (optional - public endpoints work without auth)
KALSHI_API_KEY = os.getenv("KALSHI_API_KEY", "")

# ===== PREDICTION MARKETS CONFIGURATION =====
_pm_config = _CONFIG.get("api", {}).get("prediction_markets", {})
PREDICTION_MARKETS_ENABLED_SOURCES = _pm_config.get("enabled_sources", [])
PREDICTION_MARKETS_AUTO_LINK = _pm_config.get("auto_link_results", True)

# ===== UI THEME CONFIGURATION =====
_theme = _CONFIG.get("ui_theme", {})
THEME = {
    "primary_color": _theme.get("primary_color", "#667eea"),
    "secondary_color": _theme.get("secondary_color", "#764ba2"),
    "accent_color": _theme.get("accent_color", "#f093fb"),
    "success_color": _theme.get("success_color", "#48bb78"),
    "error_color": _theme.get("error_color", "#f56565"),
    "warning_color": _theme.get("warning_color", "#ed8936"),
    "info_color": _theme.get("info_color", "#4299e1"),
    "font_family": _theme.get("font_family", "Inter, sans-serif"),
    "border_radius": _theme.get("border_radius", "20px")
}

# ===== POSITIONS =====
POSITIONS = _CONFIG.get("positions", ["QB", "RB", "WR", "TE", "FB", "K", "D/ST"])

# ===== FEATURE FLAGS =====
_features = _CONFIG.get("features", {})
FEATURES = {
    "auto_grading": _features.get("auto_grading", True),
    "csv_import": _features.get("csv_import", True),
    "admin_panel": _features.get("admin_panel", True),
    "multi_group_support": _features.get("multi_group_support", False),
    "user_self_management": _features.get("user_self_management", False)
}

# ===== CONFIG VALIDATION =====
_config_warnings = _validate_config(_CONFIG)
if _config_warnings:
    for warning in _config_warnings:
        logger.warning(f"Config validation warning: {warning}")
