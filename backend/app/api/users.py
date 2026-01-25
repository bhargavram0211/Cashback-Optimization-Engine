"""
API endpoints for User management (testing/development)
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID

from app.models.models import User
from app.core.database import get_session
from app.api.auth import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


class UserCreate(BaseModel):
    """Request model for creating a user"""
    email: EmailStr
    
    
class UserResponse(BaseModel):
    """Response model for user data"""
    id: UUID
    email: str
    created_at: datetime
    

@router.post("", response_model=UserResponse, status_code=201)
def create_user(
    user_data: UserCreate,
    session: Session = Depends(get_session)
):
    """
    Create a new user.
    
    For testing/development only. In production, this would require authentication.
    
    Args:
        user_data: Email address for the user
        session: Database session
        
    Returns:
        Created user with ID and timestamps
        
    Example:
        POST /users
        {
            "email": "test@example.com"
        }
        
        Response:
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "email": "test@example.com",
            "created_at": "2026-01-04T12:00:00"
        }
    """
    # Check if user already exists
    existing_user = session.exec(
        select(User).where(User.email == user_data.email)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=409,
            detail=f"User with email {user_data.email} already exists"
        )
    
    # Create new user
    user = User(email=user_data.email)
    session.add(user)
    session.commit()
    session.refresh(user)
    
    return UserResponse(
        id=user.id,
        email=user.email,
        created_at=user.created_at
    )


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Get a user by ID.
    
    Requires: Authorization header with Bearer token
    Users can only view their own profile.
    
    Args:
        user_id: UUID of the user
        current_user: Current authenticated user
        session: Database session
        
    Returns:
        User data
        
    Raises:
        404: User not found
        403: User doesn't have permission to view this profile
    """
    # Verify user can only view their own profile
    if user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to view this user's profile"
        )
    
    user = session.get(User, user_id)
    
    if not user:
        raise HTTPException(
            status_code=404,
            detail=f"User {user_id} not found"
        )
    
    return UserResponse(
        id=user.id,
        email=user.email,
        created_at=user.created_at
    )


@router.get("", response_model=list[UserResponse])
def list_users(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    limit: int = 10
):
    """
    List all users (for testing/development).
    
    Requires: Authorization header with Bearer token
    Note: In production, this endpoint should be restricted to admin users only.
    Currently returns empty list to prevent data leakage.
    
    Args:
        current_user: Current authenticated user
        session: Database session
        limit: Maximum number of users to return (not used)
        
    Returns:
        Empty list (security measure)
    """
    # Security: Don't expose user list in production
    # In a real application, this should check for admin role
    return []

