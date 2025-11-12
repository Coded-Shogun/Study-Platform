"""
Session management models for tracking user sessions and token revocation.
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from app.utils.database import Base


class UserSession(Base):
    """
    Track active user sessions for timeout management and concurrent session control.

    Supports SOC 2 (CC6.1), ISO 27001 (A.8.23)
    """
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)

    # User information
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    username = Column(String(100), nullable=False)

    # Session identification
    session_id = Column(String(100), unique=True, nullable=False, index=True)  # Unique session identifier
    refresh_token_jti = Column(String(100), unique=True, nullable=False, index=True)  # JWT ID from refresh token

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_activity_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)  # Absolute session expiration

    # Session metadata
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)

    # Session state
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    revoked_at = Column(DateTime, nullable=True)
    revoked_reason = Column(String(200), nullable=True)

    # Relationships
    user = relationship("User", back_populates="sessions")

    # Indexes for performance
    __table_args__ = (
        Index('idx_session_user_active', 'user_id', 'is_active'),
        Index('idx_session_expiry', 'expires_at', 'is_active'),
        Index('idx_session_activity', 'last_activity_at', 'is_active'),
    )

    def is_expired(self) -> bool:
        """Check if session is expired (absolute timeout)"""
        return datetime.utcnow() > self.expires_at

    def is_idle_timeout(self, idle_minutes: int = 15) -> bool:
        """Check if session has exceeded idle timeout"""
        idle_threshold = datetime.utcnow() - timedelta(minutes=idle_minutes)
        return self.last_activity_at < idle_threshold

    def should_expire(self, idle_minutes: int = 15) -> bool:
        """Check if session should be expired (idle or absolute timeout)"""
        return self.is_expired() or self.is_idle_timeout(idle_minutes)

    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity_at = datetime.utcnow()

    def revoke(self, reason: str = "User logout"):
        """Revoke the session"""
        self.is_active = False
        self.revoked_at = datetime.utcnow()
        self.revoked_reason = reason

    def __repr__(self):
        return f"<UserSession {self.id}: User {self.user_id} - {'Active' if self.is_active else 'Revoked'}>"


class RevokedToken(Base):
    """
    Track revoked access tokens (for logout and security).

    Uses Redis-like pattern in database for token blacklisting.
    In production, consider using Redis for better performance.
    """
    __tablename__ = "revoked_tokens"

    id = Column(Integer, primary_key=True, index=True)

    # Token identification
    jti = Column(String(100), unique=True, nullable=False, index=True)  # JWT ID
    token_type = Column(String(20), nullable=False)  # 'access' or 'refresh'

    # Revocation info
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    revoked_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)  # When token would have expired
    reason = Column(String(200), nullable=True)

    # Metadata
    ip_address = Column(String(45), nullable=True)

    # Index for performance
    __table_args__ = (
        Index('idx_revoked_expiry', 'expires_at'),
        Index('idx_revoked_jti_type', 'jti', 'token_type'),
    )

    def is_cleanup_ready(self) -> bool:
        """Check if this revoked token record can be cleaned up (past expiration)"""
        return datetime.utcnow() > self.expires_at

    def __repr__(self):
        return f"<RevokedToken {self.jti}: {self.token_type}>"
