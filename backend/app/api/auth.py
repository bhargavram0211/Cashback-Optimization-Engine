"""
GetCardIQ - Authentication API
Sprint 2: Password-based authentication with session management
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from sqlmodel import Session, select
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID
import bcrypt

from app.models.models import User
from app.core.database import get_session
from app.core.session import get_session_store, SessionStore

router = APIRouter(prefix="/auth", tags=["authentication"])


# Request/Response Models
class SignupRequest(BaseModel):
    """User signup request"""
    email: EmailStr
    password: str = Field(min_length=8, description="Password (minimum 8 characters)")
    name: Optional[str] = Field(default=None, description="Display name")


class LoginRequest(BaseModel):
    """User login request"""
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    """Authentication response"""
    user_id: str
    email: str
    name: Optional[str]
    session_token: str
    onboarding_completed: bool
    message: str


class UserInfoResponse(BaseModel):
    """Current user information"""
    user_id: str
    email: str
    name: Optional[str]
    onboarding_completed: bool


# Dependency: Get current user from session token
def get_current_user(
    authorization: Optional[str] = Header(None),
    session: Session = Depends(get_session),
    session_store: SessionStore = Depends(get_session_store)
) -> User:
    """
    Dependency to get current authenticated user.
    
    Expects Authorization header: Bearer <session_token>
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Parse Bearer token
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    # Get user_id from session
    user_id = session_store.get_user_id(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    # Get user from database
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user


# Helper functions
def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    # bcrypt requires bytes
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)


# Endpoints
@router.post("/signup", response_model=AuthResponse, status_code=201)
def signup(
    signup_data: SignupRequest,
    session: Session = Depends(get_session),
    session_store: SessionStore = Depends(get_session_store)
):
    """
    Create a new user account.
    
    Args:
        signup_data: Email, password, and optional name
        
    Returns:
        User info and session token
        
    Raises:
        409: Email already registered
        422: Validation error (password too short, invalid email)
    """
    # Check if user already exists
    existing_user = session.exec(
        select(User).where(User.email == signup_data.email)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=409,
            detail=f"Email {signup_data.email} is already registered"
        )
    
    # Hash password
    password_hash = hash_password(signup_data.password)
    
    # Create user
    user = User(
        email=signup_data.email,
        password_hash=password_hash,
        name=signup_data.name,
        onboarding_completed=False
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    
    # Create session
    session_token = session_store.create_session(user.id)
    
    return AuthResponse(
        user_id=str(user.id),
        email=user.email,
        name=user.name,
        session_token=session_token,
        onboarding_completed=user.onboarding_completed,
        message="Account created successfully"
    )


@router.post("/login", response_model=AuthResponse)
def login(
    login_data: LoginRequest,
    session: Session = Depends(get_session),
    session_store: SessionStore = Depends(get_session_store)
):
    """
    Login with email and password.
    
    Args:
        login_data: Email and password
        
    Returns:
        User info and session token
        
    Raises:
        401: Invalid credentials
    """
    # Get user by email
    user = session.exec(
        select(User).where(User.email == login_data.email)
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )
    
    # Create session
    session_token = session_store.create_session(user.id)
    
    return AuthResponse(
        user_id=str(user.id),
        email=user.email,
        name=user.name,
        session_token=session_token,
        onboarding_completed=user.onboarding_completed,
        message="Login successful"
    )


@router.get("/me", response_model=UserInfoResponse)
def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user's information.
    
    Requires: Authorization header with Bearer token
    
    Returns:
        User info
    """
    return UserInfoResponse(
        user_id=str(current_user.id),
        email=current_user.email,
        name=current_user.name,
        onboarding_completed=current_user.onboarding_completed
    )


@router.post("/logout")
def logout(
    authorization: Optional[str] = Header(None),
    session_store: SessionStore = Depends(get_session_store)
):
    """
    Logout (delete session).
    
    Requires: Authorization header with Bearer token
    
    Returns:
        Success message
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Parse Bearer token
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    # Delete session
    deleted = session_store.delete_session(token)
    
    if not deleted:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    return {"message": "Logout successful"}


@router.patch("/onboarding-complete")
def mark_onboarding_complete(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Mark user's onboarding as completed.
    
    Requires: Authorization header with Bearer token
    
    Returns:
        Success message
    """
    current_user.onboarding_completed = True
    session.add(current_user)
    session.commit()
    
    return {"message": "Onboarding marked as complete", "onboarding_completed": True}
