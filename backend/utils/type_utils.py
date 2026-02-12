"""
Type conversion utilities shared across database modules.

Provides safe conversion functions for handling various data types,
including legacy byte-encoded data from backend.database conversions.
"""

import struct
import logging

logger = logging.getLogger(__name__)


def safe_int(value) -> int:
    """
    Safely convert any value to int, handling multiple data types.
    
    Handles:
    - None → 0
    - bytes → unpacks little-endian int or decodes to string
    - str → converts to int
    - int → returns as-is
    - Invalid values → 0
    
    Args:
        value: Value to convert (any type)
        
    Returns:
        int: Converted value, or 0 if conversion fails
        
    Examples:
        >>> safe_int(42)
        42
        >>> safe_int("123")
        123
        >>> safe_int(None)
        0
        >>> safe_int(b'\\x2a\\x00\\x00\\x00')  # Little-endian 42
        42
    """
    if value is None:
        return 0
    
    if isinstance(value, bytes):
        # Try to unpack as little-endian integer
        try:
            return struct.unpack('<i', value[:4])[0] if len(value) >= 4 else 0
        except (struct.error, TypeError):
            try:
                return int(value.decode('utf-8', errors='ignore'))
            except (ValueError, AttributeError):
                return 0
    
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0


def safe_str(value) -> str:
    """
    Safely convert any value to string.
    
    Handles:
    - None → ""
    - bytes → decodes to UTF-8
    - Other types → str()
    
    Args:
        value: Value to convert
        
    Returns:
        str: Converted value, or "" if conversion fails
    """
    if value is None:
        return ""
    
    if isinstance(value, bytes):
        try:
            return value.decode('utf-8', errors='ignore')
        except (AttributeError, UnicodeDecodeError):
            return str(value)
    
    return str(value)


def safe_float(value) -> float:
    """
    Safely convert any value to float.
    
    Args:
        value: Value to convert
        
    Returns:
        float: Converted value, or 0.0 if conversion fails
    """
    if value is None:
        return 0.0
    
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0


def safe_bool(value) -> bool:
    """
    Safely convert any value to bool.
    
    Treats 0, "0", False, None, "" as False.
    All other values are True.
    
    Args:
        value: Value to convert
        
    Returns:
        bool: Converted value
    """
    if value is None:
        return False
    
    if isinstance(value, str):
        return value.lower() not in ('0', 'false', 'no', '')
    
    return bool(value)
