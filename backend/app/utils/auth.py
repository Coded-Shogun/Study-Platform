"""
Authentication dependencies for FastAPI routes
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional

from .database import get_db
from .security import decode_token, verify_token_type
from ..models import User, UserRole

# Security scheme for JWT bearer tokens
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get the current authenticated user from JWT token
    """
    token = credentials.credentials

    # Decode and verify token
    payload = decode_token(token)
    verify_token_type(payload, "access")

    # Extract user ID from token
    user_id: Optional[int] = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Get current active user (additional check)
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def require_role(*allowed_roles: UserRole):
    """
    Dependency factory to require specific user roles
    Usage: Depends(require_role(UserRole.ADMIN, UserRole.TEACHER))
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join([r.value for r in allowed_roles])}"
            )
        return current_user
    return role_checker


def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Require admin role
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


def get_admin_or_teacher(current_user: User = Depends(get_current_user)) -> User:
    """
    Require admin or teacher role
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.TEACHER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or Teacher access required"
        )
    return current_user


# Optional authentication (allows anonymous access but provides user if authenticated)
def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get current user if authenticated, otherwise return None
    """
    if not credentials:
        return None

    try:
        token = credentials.credentials
        payload = decode_token(token)
        verify_token_type(payload, "access")

        user_id: Optional[int] = payload.get("sub")
        if user_id is None:
            return None

        user = db.query(User).filter(User.id == user_id).first()
        return user if user and user.is_active else None

    except HTTPException:
        return None
