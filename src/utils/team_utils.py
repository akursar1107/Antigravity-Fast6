"""
Team Utilities
Helper functions for team name and abbreviation mapping
"""

import config


def get_team_abbr(full_name: str) -> str:
    """
    Maps full team names (Odds API format) to abbreviations (nflreadpy format).
    
    Args:
        full_name: Full team name (e.g., "Kansas City Chiefs")
        
    Returns:
        Team abbreviation (e.g., "KC")
    """
    return config.TEAM_ABBR_MAP.get(full_name, full_name)


def get_team_full_name(abbr: str) -> str:
    """
    Maps abbreviation (nflreadpy format) to full team name (Odds API format).
    
    Args:
        abbr: Team abbreviation (e.g., "KC")
        
    Returns:
        Full team name (e.g., "Kansas City Chiefs")
    """
    for name, a in config.TEAM_ABBR_MAP.items():
        if a == abbr:
            return name
    return abbr
