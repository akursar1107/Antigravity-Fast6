"""
Configuration and Constants

Loads settings from config.json with support for environment variable overrides.
For sensitive values like API keys, st.secrets is checked first, then environment variables.
"""

import json
import os
from pathlib import Path
import logging

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

# ===== APP CONFIGURATION =====
APP_NAME = _CONFIG.get("app", {}).get("name", "Fast6")
APP_VERSION = _CONFIG.get("app", {}).get("version", "1.0.0")
CURRENT_SEASON = _CONFIG.get("app", {}).get("current_season", 2025)
DATABASE_PATH = _CONFIG.get("app", {}).get("database_path", "data/fast6.db")

# ===== SEASONS =====
SEASONS = _CONFIG.get("seasons", [2025, 2024, 2023, 2022, 2021, 2020])

# ===== SCORING CONFIGURATION =====
SCORING_FIRST_TD = _CONFIG.get("scoring", {}).get("first_td_win", 3)
SCORING_ANY_TIME = _CONFIG.get("scoring", {}).get("any_time_td", 1)
NAME_MATCH_THRESHOLD = _CONFIG.get("scoring", {}).get("name_match_threshold", 0.75)
AUTO_GRADE_ENABLED = _CONFIG.get("scoring", {}).get("auto_grade_enabled", True)

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
_api_config = _CONFIG.get("api", {}).get("odds_api", {})

# For API key: check st.secrets first, then environment variables, then fallback
ODDS_API_KEY = ""
try:
    import streamlit as st
    try:
        # Try to access secrets - will fail if no secrets file exists
        ODDS_API_KEY = st.secrets.get("odds_api_key", "") if st.secrets else ""
    except Exception:
        # Secrets file doesn't exist or can't be parsed
        pass
except (ImportError, AttributeError, RuntimeError):
    # st module not available (e.g., in tests or non-streamlit context)
    pass

# Fallback to environment variable if not found in secrets
if not ODDS_API_KEY:
    ODDS_API_KEY = os.getenv("ODDS_API_KEY", "")

if not ODDS_API_KEY:
    logger.warning("ODDS_API_KEY not found in st.secrets or environment variables")

ODDS_API_BASE_URL = _api_config.get("base_url", "https://api.the-odds-api.com/v4")
ODDS_API_SPORT = _api_config.get("sport", "americanfootball_nfl")
ODDS_API_MARKET = _api_config.get("market", "player_anytime_td")
ODDS_API_REGIONS = _api_config.get("regions", "us")
ODDS_API_FORMAT = _api_config.get("format", "american")
ODDS_API_CACHE_TTL = _api_config.get("cache_ttl", 3600)

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
