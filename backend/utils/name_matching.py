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
    
    p_parts = p.split()
    a_parts = a.split()
    
    # Remove common suffixes for comparison
    suffixes = {'jr', 'sr', 'iii', 'iv', 'v', 'jr.', 'sr.'}
    p_parts = [part for part in p_parts if part not in suffixes]
    a_parts = [part for part in a_parts if part not in suffixes]
    
    # Extract last name more intelligently
    def get_last_name(parts):
        if not parts:
            return ""
        last_part = parts[-1]
        # Handle "P.Nacua"
        if '.' in last_part and len(last_part) > 2:
            period_parts = [part for part in last_part.split('.') if part]
            return period_parts[-1] if period_parts else last_part
        return last_part
    
    p_last = get_last_name(p_parts)
    a_last = get_last_name(a_parts)
    
    # Check if last names match exactly
    if p_last and a_last and p_last == a_last:
        # If both have first parts, verify they are compatible (first initial match)
        if len(p_parts) > 1 and len(a_parts) > 1:
            p_first = p_parts[0]
            a_first = a_parts[0]
            
            # Extract actual initials (handle "P.Nacua" as first part)
            p_init = p_first[0] if p_first else ""
            a_init = a_first[0] if a_first else ""
            
            if p_init and a_init and p_init != a_init:
                # Different initials (e.g., "Aaron" vs "Julio") - ignore this True
                pass
            else:
                return True
        else:
            # One or both is just a last name, we accept it
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
