"""Users Router - User Management Endpoints"""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Dict, Any
import logging
import sqlite3

from src.api.fastapi_models import UserResponse, UserCreate, UserUpdate
from src.api.fastapi_dependencies import get_current_user, get_current_admin_user, get_db_async

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("", response_model=List[UserResponse])
async def list_users(
    current_user: Dict[str, Any] = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db_async)
) -> List[UserResponse]:
    """List all users (authenticated users only)"""
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, is_admin FROM users ORDER BY name")
    users = cursor.fetchall()
    
    return [
        UserResponse(id=u[0], name=u[1], email=u[2], is_admin=u[3])
        for u in users
    ]


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db_async)
) -> UserResponse:
    """Get specific user (own profile or admin can view any)"""
    # Check authorization
    if current_user["id"] != user_id and current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only view your own profile"
        )
    
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, email, is_admin FROM users WHERE id = ?",
        (user_id,)
    )
    user = cursor.fetchone()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(id=user[0], name=user[1], email=user[2], is_admin=user[3])


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreate,
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
    conn: sqlite3.Connection = Depends(get_db_async)
) -> UserResponse:
    """Create new user (admin only)"""
    cursor = conn.cursor()
    
    # Check if user already exists
    cursor.execute("SELECT id FROM users WHERE LOWER(name) = LOWER(?)", (user.name,))
    if cursor.fetchone():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists"
        )
    
    cursor.execute(
        "INSERT INTO users (name, email, is_admin) VALUES (?, ?, ?)",
        (user.name, user.email, user.is_admin)
    )
    conn.commit()
    
    new_user_id = cursor.lastrowid
    logger.info(f"User created: {user.name} (ID: {new_user_id})")
    
    return UserResponse(
        id=new_user_id,
        name=user.name,
        email=user.email,
        is_admin=user.is_admin
    )


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    updates: UserUpdate,
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
    conn: sqlite3.Connection = Depends(get_db_async)
) -> UserResponse:
    """Update user (admin only)"""
    cursor = conn.cursor()
    
    # Get existing user
    cursor.execute(
        "SELECT id, name, email, is_admin FROM users WHERE id = ?",
        (user_id,)
    )
    user = cursor.fetchone()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prepare update
    update_fields = []
    update_values = []
    
    if updates.name is not None:
        update_fields.append("name = ?")
        update_values.append(updates.name)
    
    if updates.email is not None:
        update_fields.append("email = ?")
        update_values.append(updates.email)
    
    if updates.is_admin is not None:
        update_fields.append("is_admin = ?")
        update_values.append(updates.is_admin)
    
    if not update_fields:
        # No updates provided, return current user
        return UserResponse(id=user[0], name=user[1], email=user[2], is_admin=user[3])
    
    # Execute update
    update_values.append(user_id)
    query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?"
    cursor.execute(query, update_values)
    conn.commit()
    
    logger.info(f"User updated: {user[1]} (ID: {user_id})")
    
    # Return updated user
    cursor.execute(
        "SELECT id, name, email, is_admin FROM users WHERE id = ?",
        (user_id,)
    )
    updated_user = cursor.fetchone()
    
    return UserResponse(
        id=updated_user[0],
        name=updated_user[1],
        email=updated_user[2],
        is_admin=updated_user[3]
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
    conn: sqlite3.Connection = Depends(get_db_async)
) -> None:
    """Delete user (admin only, cannot delete own account)"""
    if current_user["id"] == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    cursor = conn.cursor()
    
    # Check if user exists
    cursor.execute("SELECT name FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    
    logger.info(f"User deleted: {user[0]} (ID: {user_id})")
