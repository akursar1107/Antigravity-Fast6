"""FastAPI Dependency Injection for Authentication and Database"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Optional, Dict, Any
import logging
import sqlite3

from src.api.fastapi_security import verify_token
from src.api.fastapi_config import settings
from src.database.connection import get_db_connection

logger = logging.getLogger(__name__)

# OAuth2 security scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """
    Get current authenticated user from JWT token.
    
    Args:
        token: JWT token from Authorization header
    
    Returns:
        User dict with id, name, role
    
    Raises:
        HTTPException: 401 if token invalid or expired
    """
    payload = verify_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    username = payload.get("name")
    role = payload.get("role", "user")
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return {
        "id": int(user_id),
        "name": username,
        "role": role
    }


async def get_current_admin_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get current user and verify they are admin.
    
    Args:
        current_user: Current authenticated user
    
    Returns:
        User dict if admin
    
    Raises:
        HTTPException: 403 if user is not admin
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


def get_db() -> sqlite3.Connection:
    """
    Get database connection.
    
    Yields:
        Database connection
    """
    conn = get_db_connection()
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        conn.close()


async def get_db_async() -> sqlite3.Connection:
    """Async version of get_db for FastAPI async endpoints"""
    conn = get_db_connection()
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        conn.close()
