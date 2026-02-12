"""Authentication Router - Login and User Info Endpoints"""
from fastapi import APIRouter, HTTPException, status, Depends, Request
from typing import Dict, Any
import logging
import sqlite3

from backend.api.fastapi_models import LoginRequest, TokenResponse
from backend.api.fastapi_security import create_access_token
from backend.api.fastapi_dependencies import get_current_user, get_db_async
from backend.api.rate_limit import limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,
    body: LoginRequest,
    conn: sqlite3.Connection = Depends(get_db_async)
) -> TokenResponse:
    """Login with username and get JWT token (friend group - no password required)"""
    username = body.username.strip()
    
    if not username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username cannot be empty"
        )
    
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, is_admin FROM users WHERE LOWER(name) = LOWER(?)",
        (username,)
    )
    user = cursor.fetchone()
    
    if not user:
        logger.warning(f"Login failed for unknown user: {username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username"
        )
    
    user_id, user_name, is_admin = user
    role = "admin" if is_admin else "user"
    
    token_data = {"sub": str(user_id), "name": user_name, "role": role}
    access_token = create_access_token(data=token_data)
    
    logger.info(f"User logged in: {user_name} (ID: {user_id})")
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user_id,
        username=user_name,
        role=role
    )


@router.get("/me")
async def get_current_user_info(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get current authenticated user information"""
    return {
        "id": current_user["id"],
        "name": current_user["name"],
        "role": current_user["role"]
    }
