"""
Audit logging models for compliance and security tracking.
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.utils.database import Base


class AuditLog(Base):
    """
    Comprehensive audit log for tracking all security-relevant events.

    Supports SOC 2 (CC6.3), ISO 27001 (A.8.15), GDPR (Art. 5), NIST (DE.CM-1)
    """
    __tablename__ = "audit_logs"

    # Primary identification
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Event information
    event_type = Column(String(50), nullable=False, index=True)  # LOGIN, LOGOUT, CREATE, UPDATE, DELETE, ACCESS, etc.
    event_category = Column(String(30), nullable=False, index=True)  # AUTH, ADMIN, DATA, SECURITY
    action = Column(String(100), nullable=False)  # Specific action taken
    result = Column(String(20), nullable=False, index=True)  # SUCCESS, FAILURE, ERROR

    # Actor information
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    username = Column(String(100), nullable=True)  # Denormalized for retention after user deletion
    user_role = Column(String(20), nullable=True)
    ip_address = Column(String(45), nullable=True, index=True)  # IPv4 or IPv6
    user_agent = Column(String(500), nullable=True)

    # Resource information
    resource_type = Column(String(50), nullable=True, index=True)  # USER, SUBJECT, QUESTION, etc.
    resource_id = Column(String(100), nullable=True, index=True)
    resource_name = Column(String(200), nullable=True)

    # Change tracking
    old_values = Column(JSON, nullable=True)  # State before change
    new_values = Column(JSON, nullable=True)  # State after change

    # Additional context
    description = Column(Text, nullable=True)
    additional_metadata = Column(JSON, nullable=True)  # Additional contextual data

    # Security & integrity
    request_id = Column(String(50), nullable=True, index=True)  # For correlating related events
    session_id = Column(String(100), nullable=True, index=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="audit_logs")

    # Indexes for performance
    __table_args__ = (
        Index('idx_audit_timestamp_user', 'timestamp', 'user_id'),
        Index('idx_audit_event_result', 'event_type', 'result'),
        Index('idx_audit_resource', 'resource_type', 'resource_id'),
        Index('idx_audit_category_timestamp', 'event_category', 'timestamp'),
    )

    def __repr__(self):
        return f"<AuditLog {self.id}: {self.event_type} by {self.username} at {self.timestamp}>"


class SecurityEvent(Base):
    """
    High-priority security events requiring immediate attention.

    Separate from audit logs for real-time alerting and monitoring.
    """
    __tablename__ = "security_events"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Event classification
    severity = Column(String(20), nullable=False, index=True)  # CRITICAL, HIGH, MEDIUM, LOW
    event_type = Column(String(50), nullable=False, index=True)  # BRUTE_FORCE, UNAUTHORIZED_ACCESS, etc.
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)

    # Context
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    username = Column(String(100), nullable=True)
    ip_address = Column(String(45), nullable=True, index=True)
    user_agent = Column(String(500), nullable=True)

    # Response tracking
    status = Column(String(20), nullable=False, default="OPEN", index=True)  # OPEN, INVESTIGATING, RESOLVED
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    resolution_notes = Column(Text, nullable=True)

    # Alert tracking
    alert_sent = Column(DateTime, nullable=True)
    alert_recipients = Column(JSON, nullable=True)

    # Additional data
    additional_metadata = Column(JSON, nullable=True)
    related_audit_log_id = Column(Integer, ForeignKey("audit_logs.id"), nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="security_events")
    resolver = relationship("User", foreign_keys=[resolved_by])

    __table_args__ = (
        Index('idx_security_severity_status', 'severity', 'status'),
        Index('idx_security_timestamp_severity', 'timestamp', 'severity'),
    )

    def __repr__(self):
        return f"<SecurityEvent {self.id}: {self.severity} - {self.title}>"
