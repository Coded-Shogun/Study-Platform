from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime

from ..utils.database import get_db
from ..utils.security import (
    verify_password,
    get_password_hash,
    validate_password_strength,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token_type
)
from ..utils.auth import get_current_user, get_current_active_user
from ..utils.audit import (
    log_auth_event,
    log_audit_event,
    log_failed_login_attempt,
    EventType,
    EventCategory,
    EventResult,
)
from ..models.user import User, UserRole, StudentLevel
from ..config import settings

router = APIRouter()

# ==================== Pydantic Schemas ====================

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    role: Optional[str] = "student"
    student_level: Optional[str] = None

    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters long')
        if len(v) > 50:
            raise ValueError('Username must be less than 50 characters')
        if not v.replace('_', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, and underscores')
        return v.lower()

    @validator('password')
    def validate_password(cls, v):
        is_valid, error_message = validate_password_strength(v)
        if not is_valid:
            raise ValueError(error_message)
        return v

    @validator('role')
    def validate_role(cls, v):
        valid_roles = ["admin", "teacher", "student"]
        if v not in valid_roles:
            raise ValueError(f"Invalid role. Must be one of: {', '.join(valid_roles)}")
        return v

    @validator('student_level')
    def validate_student_level(cls, v, values):
        if values.get('role') == 'student' and not v:
            raise ValueError("Student level is required for student accounts")
        if v:
            valid_levels = ["primary", "high_school", "tertiary"]
            if v not in valid_levels:
                raise ValueError(f"Invalid student level. Must be one of: {', '.join(valid_levels)}")
        return v


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]
    role: str
    student_level: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

    @validator('new_password')
    def validate_new_password(cls, v):
        is_valid, error_message = validate_password_strength(v)
        if not is_valid:
            raise ValueError(error_message)
        return v


# ==================== Auth Endpoints ====================

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, request: Request, db: Session = Depends(get_db)):
    """
    Register a new user with hashed password
    """
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.username == user.username.lower()) | (User.email == user.email.lower())
    ).first()

    if existing_user:
        # Log failed registration attempt
        log_auth_event(
            db=db,
            request=request,
            event_type=EventType.REGISTER,
            result=EventResult.FAILURE,
            username=user.username.lower(),
            description="Registration failed: username or email already exists"
        )

        if existing_user.username == user.username.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

    # Hash password
    hashed_password = get_password_hash(user.password)

    # Create new user
    db_user = User(
        username=user.username.lower(),
        email=user.email.lower(),
        hashed_password=hashed_password,
        full_name=user.full_name,
        role=user.role,
        student_level=user.student_level
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Log successful registration
    log_auth_event(
        db=db,
        request=request,
        event_type=EventType.REGISTER,
        result=EventResult.SUCCESS,
        user=db_user,
        description=f"New user registered with role: {db_user.role}",
        metadata={"role": db_user.role, "student_level": db_user.student_level}
    )

    return db_user


@router.post("/login", response_model=TokenResponse)
async def login(login_data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """
    Login user and return JWT tokens
    """
    # Find user
    user = db.query(User).filter(User.username == login_data.username.lower()).first()

    # Verify user exists and password is correct
    if not user or not verify_password(login_data.password, user.hashed_password):
        # Log failed login attempt (includes brute force detection)
        log_failed_login_attempt(
            db=db,
            request=request,
            username=login_data.username.lower(),
            reason="Invalid credentials"
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        # Log failed login - inactive account
        log_auth_event(
            db=db,
            request=request,
            event_type=EventType.LOGIN_FAILED,
            result=EventResult.FAILURE,
            user=user,
            description="Login failed: account inactive"
        )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Please contact support."
        )

    # Create tokens
    access_token = create_access_token(data={"sub": user.id, "role": user.role})
    refresh_token = create_refresh_token(data={"sub": user.id})

    # Log successful login
    log_auth_event(
        db=db,
        request=request,
        event_type=EventType.LOGIN,
        result=EventResult.SUCCESS,
        user=user,
        description="User logged in successfully"
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user
    }


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(token_request: RefreshTokenRequest, request: Request, db: Session = Depends(get_db)):
    """
    Refresh access token using refresh token
    """
    # Decode refresh token
    payload = decode_token(token_request.refresh_token)
    verify_token_type(payload, "refresh")

    # Get user ID from token
    user_id: Optional[int] = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    # Create new tokens
    access_token = create_access_token(data={"sub": user.id, "role": user.role})
    new_refresh_token = create_refresh_token(data={"sub": user.id})

    # Log token refresh
    log_auth_event(
        db=db,
        request=request,
        event_type=EventType.TOKEN_REFRESH,
        result=EventResult.SUCCESS,
        user=user,
        description="Access token refreshed"
    )

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "user": user
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """
    Get current authenticated user information
    """
    return current_user


@router.post("/change-password")
async def change_password(
    password_data: PasswordChangeRequest,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Change user password
    """
    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        # Log failed password change attempt
        log_auth_event(
            db=db,
            request=request,
            event_type=EventType.PASSWORD_CHANGE,
            result=EventResult.FAILURE,
            user=current_user,
            description="Password change failed: incorrect current password"
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # Check new password is different
    if verify_password(password_data.new_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password"
        )

    # Update password
    current_user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()

    # Log successful password change
    log_auth_event(
        db=db,
        request=request,
        event_type=EventType.PASSWORD_CHANGE,
        result=EventResult.SUCCESS,
        user=current_user,
        description="Password changed successfully"
    )

    return {"message": "Password changed successfully"}


@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Logout user (client should discard tokens)
    """
    # Log logout event
    log_auth_event(
        db=db,
        request=request,
        event_type=EventType.LOGOUT,
        result=EventResult.SUCCESS,
        user=current_user,
        description="User logged out"
    )

    # In a production app, you might want to:
    # 1. Add token to blacklist in Redis
    # 2. Track logout timestamp
    # For now, just return success - client will discard tokens
    return {"message": "Logged out successfully"}
