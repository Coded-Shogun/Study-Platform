"""
Session management utilities for user session tracking and token revocation.

Implements session timeout, concurrent session control, and token blacklisting.
"""

from typing import Optional, Tuple
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from fastapi import Request
import uuid
import jwt

from app.models.session import UserSession, RevokedToken
from app.models.user import User
from app.config import settings


# Session configuration
IDLE_TIMEOUT_MINUTES = 15  # Idle timeout: 15 minutes
ABSOLUTE_TIMEOUT_HOURS = 8  # Absolute timeout: 8 hours
MAX_CONCURRENT_SESSIONS = 3  # Maximum concurrent sessions per user


def generate_session_id() -> str:
    """Generate a unique session ID"""
    return str(uuid.uuid4())


def generate_jti() -> str:
    """Generate a unique JWT ID for token tracking"""
    return str(uuid.uuid4())


def create_session(
    db: Session,
    user: User,
    refresh_token_jti: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> UserSession:
    """
    Create a new user session.

    Args:
        db: Database session
        user: User object
        refresh_token_jti: JWT ID from refresh token
        ip_address: Client IP address
        user_agent: Client user agent

    Returns:
        Created UserSession instance
    """
    # Check concurrent session limit
    active_sessions = db.query(UserSession).filter(
        UserSession.user_id == user.id,
        UserSession.is_active == True
    ).count()

    if active_sessions >= MAX_CONCURRENT_SESSIONS:
        # Revoke oldest session
        oldest_session = db.query(UserSession).filter(
            UserSession.user_id == user.id,
            UserSession.is_active == True
        ).order_by(UserSession.created_at.asc()).first()

        if oldest_session:
            oldest_session.revoke(reason="Maximum concurrent sessions reached")
            db.commit()

    # Create new session
    session = UserSession(
        user_id=user.id,
        username=user.username,
        session_id=generate_session_id(),
        refresh_token_jti=refresh_token_jti,
        created_at=datetime.utcnow(),
        last_activity_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(hours=ABSOLUTE_TIMEOUT_HOURS),
        ip_address=ip_address,
        user_agent=user_agent,
        is_active=True
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    return session


def get_session_by_jti(db: Session, jti: str) -> Optional[UserSession]:
    """Get session by refresh token JTI"""
    return db.query(UserSession).filter(
        UserSession.refresh_token_jti == jti,
        UserSession.is_active == True
    ).first()


def get_session_by_id(db: Session, session_id: str) -> Optional[UserSession]:
    """Get session by session ID"""
    return db.query(UserSession).filter(
        UserSession.session_id == session_id,
        UserSession.is_active == True
    ).first()


def validate_session(db: Session, session: UserSession) -> Tuple[bool, Optional[str]]:
    """
    Validate session is still active and not expired.

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not session.is_active:
        return False, "Session has been revoked"

    if session.is_expired():
        session.revoke(reason="Session expired (absolute timeout)")
        db.commit()
        return False, "Session expired"

    if session.is_idle_timeout(IDLE_TIMEOUT_MINUTES):
        session.revoke(reason="Session expired (idle timeout)")
        db.commit()
        return False, "Session expired due to inactivity"

    return True, None


def update_session_activity(db: Session, session: UserSession):
    """Update session last activity timestamp"""
    session.update_activity()
    db.commit()


def revoke_session(
    db: Session,
    session: UserSession,
    reason: str = "User logout"
):
    """Revoke a user session"""
    session.revoke(reason=reason)
    db.commit()


def revoke_all_user_sessions(
    db: Session,
    user_id: int,
    reason: str = "All sessions revoked"
):
    """Revoke all sessions for a user"""
    sessions = db.query(UserSession).filter(
        UserSession.user_id == user_id,
        UserSession.is_active == True
    ).all()

    for session in sessions:
        session.revoke(reason=reason)

    db.commit()
    return len(sessions)


def cleanup_expired_sessions(db: Session) -> int:
    """
    Clean up expired sessions.

    Returns:
        Number of sessions cleaned up
    """
    now = datetime.utcnow()
    idle_threshold = now - timedelta(minutes=IDLE_TIMEOUT_MINUTES)

    # Find expired sessions (either absolute timeout or idle timeout)
    expired_sessions = db.query(UserSession).filter(
        UserSession.is_active == True
    ).filter(
        (UserSession.expires_at < now) |
        (UserSession.last_activity_at < idle_threshold)
    ).all()

    count = 0
    for session in expired_sessions:
        if session.is_expired():
            session.revoke(reason="Automatic cleanup: absolute timeout")
        elif session.is_idle_timeout(IDLE_TIMEOUT_MINUTES):
            session.revoke(reason="Automatic cleanup: idle timeout")
        count += 1

    if count > 0:
        db.commit()

    return count


# ==================== Token Revocation ====================

def revoke_token(
    db: Session,
    jti: str,
    token_type: str,
    user_id: int,
    expires_at: datetime,
    reason: str = "User logout",
    ip_address: Optional[str] = None,
) -> RevokedToken:
    """
    Add token to revocation list.

    Args:
        db: Database session
        jti: JWT ID
        token_type: 'access' or 'refresh'
        user_id: User ID
        expires_at: Token expiration time
        reason: Reason for revocation
        ip_address: Client IP address

    Returns:
        Created RevokedToken instance
    """
    revoked = RevokedToken(
        jti=jti,
        token_type=token_type,
        user_id=user_id,
        revoked_at=datetime.utcnow(),
        expires_at=expires_at,
        reason=reason,
        ip_address=ip_address
    )

    db.add(revoked)
    db.commit()
    db.refresh(revoked)

    return revoked


def is_token_revoked(db: Session, jti: str) -> bool:
    """Check if a token has been revoked"""
    revoked = db.query(RevokedToken).filter(
        RevokedToken.jti == jti
    ).first()

    return revoked is not None


def cleanup_expired_tokens(db: Session) -> int:
    """
    Clean up revoked tokens that are past their expiration.

    Returns:
        Number of tokens cleaned up
    """
    now = datetime.utcnow()

    # Delete revoked tokens that have expired
    result = db.query(RevokedToken).filter(
        RevokedToken.expires_at < now
    ).delete()

    db.commit()
    return result


def get_active_sessions(db: Session, user_id: int) -> list:
    """Get all active sessions for a user"""
    return db.query(UserSession).filter(
        UserSession.user_id == user_id,
        UserSession.is_active == True
    ).order_by(UserSession.last_activity_at.desc()).all()


def get_session_count(db: Session, user_id: int) -> int:
    """Get count of active sessions for a user"""
    return db.query(UserSession).filter(
        UserSession.user_id == user_id,
        UserSession.is_active == True
    ).count()


# ==================== JWT Integration ====================

def extract_jti_from_token(token: str) -> Optional[str]:
    """Extract JTI from JWT token without validation"""
    try:
        # Decode without verification to extract JTI
        payload = jwt.decode(token, options={"verify_signature": False})
        return payload.get("jti")
    except Exception:
        return None


def extract_exp_from_token(token: str) -> Optional[datetime]:
    """Extract expiration time from JWT token"""
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        exp_timestamp = payload.get("exp")
        if exp_timestamp:
            return datetime.fromtimestamp(exp_timestamp)
    except Exception:
        return None

    return None
