"""
Name Matching Utilities
Handles player name matching with fuzzy logic for grading.
"""

import difflib
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


def names_match(picked_name: str, actual_name: str, threshold: float = 0.75) -> bool:
    """
    Compare two player names with fuzzy matching.
    Handles variations like "CMC" vs "Christian McCaffrey", "Penix Jr" vs "Michael Penix Jr", 
    "Puka Nacua" vs "P.Nacua", etc.
    
    Args:
        picked_name: Name as picked by user
        actual_name: Actual player name from play-by-play data
        threshold: Similarity threshold (0-1, default 0.75)
        
    Returns:
        True if names match or are similar enough
    """
    if not picked_name or not actual_name:
        return False
    
    p = str(picked_name).strip().lower()
    a = str(actual_name).strip().lower()
    
    # Exact match
    if p == a:
        return True
    
    # Check if one contains the other (handles "Penix Jr" in "Michael Penix Jr")
    if p in a or a in p:
        return True
    
    # Split by space and check partial matches
    p_parts = p.split()
    a_parts = a.split()
    
    # Extract last name more intelligently (handle "P.Nacua" -> "Nacua")
    def get_last_name(parts):
        if not parts:
            return ""
        last_part = parts[-1]
        # If last part contains a period (e.g., "p.nacua"), extract after the period
        if '.' in last_part:
            # Split by period and take the last non-empty part
            period_parts = [part for part in last_part.split('.') if part]
            return period_parts[-1] if period_parts else last_part
        return last_part
    
    p_last = get_last_name(p_parts)
    a_last = get_last_name(a_parts)
    
    # Check if last names match
    if p_last and a_last and p_last == a_last:
        return True
    
    # Fuzzy matching using SequenceMatcher
    ratio = difflib.SequenceMatcher(None, p, a).ratio()
    return ratio >= threshold


def normalize_player_name(name: str) -> str:
    """
    Normalize player name for consistent matching.
    Removes extra spaces, converts to lowercase.
    
    Args:
        name: Player name to normalize
        
    Returns:
        Normalized name string
    """
    if not name:
        return ""
    return " ".join(str(name).strip().lower().split())


def extract_last_name(full_name: str) -> str:
    """
    Extract last name from full name.
    
    Args:
        full_name: Full player name
        
    Returns:
        Last name
    """
    if not full_name:
        return ""
    parts = str(full_name).strip().split()
    return parts[-1].lower() if parts else ""
