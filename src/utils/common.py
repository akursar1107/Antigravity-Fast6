"""
Common utilities shared across the application.

Provides reusable functions for:
- Data normalization and formatting
- Streamlit session state management
- Pick display formatting
"""

from typing import Dict, Optional, Any

try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False

from .type_utils import safe_int
from .odds_utils import american_to_probability


def normalize_week_record(row_dict: Dict) -> Dict:
    """
    Normalize a week/pick record by converting season and week to integers.
    
    This is a common operation needed after fetching records from the database,
    where numeric fields may come back as various types.
    
    Args:
        row_dict: Dictionary containing database record data
        
    Returns:
        The same dictionary with 'season' and 'week' converted to int
        
    Example:
        >>> row = {'season': '2024', 'week': 5.0, 'name': 'John'}
        >>> normalize_week_record(row)
        {'season': 2024, 'week': 5, 'name': 'John'}
    """
    if 'season' in row_dict:
        row_dict['season'] = safe_int(row_dict['season'])
    if 'week' in row_dict:
        row_dict['week'] = safe_int(row_dict['week'])
    return row_dict


def ensure_session_state(key: str, default_value: Any) -> Any:
    """
    Ensure a Streamlit session state key exists with a default value.
    
    A cleaner alternative to repeated if/else checks for session state initialization.
    Returns the current value if it exists, otherwise sets and returns the default.
    
    Args:
        key: Session state key name
        default_value: Value to use if key doesn't exist
        
    Returns:
        The current (or newly set) value
        
    Example:
        >>> selected_week = ensure_session_state('selected_week_id', None)
    """
    if not HAS_STREAMLIT:
        return default_value
    
    if key not in st.session_state:
        st.session_state[key] = default_value
    return st.session_state[key]


def format_odds(odds: Optional[float]) -> str:
    """
    Format American odds for display.
    
    Args:
        odds: American odds as float/int or None
    
    Returns:
        str: Formatted odds string (e.g., "-110", "+150", "N/A")
    
    Handles None values by returning "N/A".
    Converts float odds to integer representation.
    Positive odds get a '+' prefix.
    
    Example:
        >>> format_odds(150)
        '+150'
        >>> format_odds(-110)
        '-110'
        >>> format_odds(None)
        'N/A'
    """
    if odds is None:
        return "N/A"
    if odds >= 0:
        return f"+{int(odds)}"
    return str(int(odds))


def format_currency(value: Optional[float], default: str = "$0.00") -> str:
    """
    Format a value as USD currency.
    
    Args:
        value: Numeric value to format
        default: String to return if value is None/invalid
        
    Returns:
        Formatted currency string (e.g., "$15.00")
    """
    if value is None:
        return default
    try:
        return f"${float(value):.2f}"
    except (ValueError, TypeError):
        return default


def format_implied_probability(odds: Optional[float]) -> str:
    """
    Format the implied probability from American odds.
    
    Args:
        odds: American odds (e.g., +250, -150)
        
    Returns:
        Formatted percentage string (e.g., "28.6%") or "N/A"
    """
    if odds is None:
        return "N/A"
    try:
        prob = american_to_probability(odds)
        return f"{prob:.1%}"
    except (ValueError, ZeroDivisionError):
        return "N/A"


def format_pick_for_display(pick: Dict, result: Optional[Dict] = None) -> Dict:
    """
    Format a pick record for display in a table/dataframe.
    
    Consolidates the repeated pick formatting logic used across multiple views.
    
    Args:
        pick: Pick dictionary from database
        result: Optional result dictionary (from get_result_for_pick)
        
    Returns:
        Dict suitable for display with formatted strings:
        {
            'Team': str,
            'Player': str,
            'Odds': str (formatted),
            'Implied %': str (break-even probability),
            'Theo Return': str (formatted currency),
            'Result': str (emoji + status),
            'Return': str (formatted currency)
        }
    """
    odds = pick.get('odds')
    odds_str = format_odds(odds)
    implied_str = format_implied_probability(odds)
    theo_ret = pick.get('theoretical_return')
    
    # Determine result status
    if result is None:
        result_str = '⏳ Pending'
        actual_return = 0.0
    elif result.get('is_correct') is None:
        result_str = '⏳ Pending'
        actual_return = result.get('actual_return', 0.0) or 0.0
    elif result.get('is_correct'):
        result_str = '✅ Correct'
        actual_return = result.get('actual_return', 0.0) or 0.0
    else:
        result_str = '❌ Incorrect'
        actual_return = result.get('actual_return', 0.0) or 0.0
    
    return {
        'Team': pick.get('team', 'Unknown'),
        'Player': pick.get('player_name', 'Unknown'),
        'Odds': odds_str,
        'Implied %': implied_str,
        'Theo Return': format_currency(theo_ret),
        'Result': result_str,
        'Return': format_currency(actual_return)
    }


def format_pick_for_display_compact(pick: Dict, result: Optional[Dict] = None) -> Dict:
    """
    Format a pick for compact display (shorter result emoji).
    
    Same as format_pick_for_display but uses single emoji for Result column.
    Useful for tables showing many picks where space is limited.
    """
    display = format_pick_for_display(pick, result)
    
    # Shorten result to single emoji
    if '✅' in display['Result']:
        display['Result'] = '✅'
    elif '❌' in display['Result']:
        display['Result'] = '❌'
    else:
        display['Result'] = '⏳'
    
    return display
