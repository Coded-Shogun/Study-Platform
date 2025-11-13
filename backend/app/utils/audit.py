"""
Audit logging utilities for compliance and security tracking.

Provides functions to log security events, user actions, and data changes.
"""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
from fastapi import Request
import uuid
import json

from app.models.audit import AuditLog, SecurityEvent
from app.models.user import User


# Event type constants
class EventType:
    """Standard event types for audit logging"""
    # Authentication
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    LOGIN_FAILED = "LOGIN_FAILED"
    REGISTER = "REGISTER"
    TOKEN_REFRESH = "TOKEN_REFRESH"
    PASSWORD_CHANGE = "PASSWORD_CHANGE"
    PASSWORD_RESET = "PASSWORD_RESET"

    # Authorization
    ACCESS_DENIED = "ACCESS_DENIED"
    PERMISSION_CHECK = "PERMISSION_CHECK"

    # Data operations
    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    EXPORT = "EXPORT"

    # Admin operations
    ADMIN_CREATE = "ADMIN_CREATE"
    ADMIN_UPDATE = "ADMIN_UPDATE"
    ADMIN_DELETE = "ADMIN_DELETE"
    ADMIN_ACCESS = "ADMIN_ACCESS"

    # Security events
    RATE_LIMIT_HIT = "RATE_LIMIT_HIT"
    SUSPICIOUS_ACTIVITY = "SUSPICIOUS_ACTIVITY"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    SESSION_TIMEOUT = "SESSION_TIMEOUT"
    TOKEN_REVOKED = "TOKEN_REVOKED"


class EventCategory:
    """Event categories for filtering and reporting"""
    AUTH = "AUTH"
    ADMIN = "ADMIN"
    DATA = "DATA"
    SECURITY = "SECURITY"
    SYSTEM = "SYSTEM"


class EventResult:
    """Event result status"""
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    ERROR = "ERROR"


class SecuritySeverity:
    """Security event severity levels"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


def get_client_ip(request: Request) -> str:
    """Extract client IP address from request, handling proxies"""
    # Check for forwarded header (behind proxy/load balancer)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()

    # Check for real IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # Fall back to direct client
    if request.client:
        return request.client.host

    return "unknown"


def get_user_agent(request: Request) -> str:
    """Extract user agent from request"""
    return request.headers.get("User-Agent", "unknown")[:500]


def generate_request_id() -> str:
    """Generate unique request ID for correlation"""
    return str(uuid.uuid4())


def log_audit_event(
    db: Session,
    event_type: str,
    event_category: str,
    result: str,
    action: str,
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    user_role: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    resource_name: Optional[str] = None,
    old_values: Optional[Dict[str, Any]] = None,
    new_values: Optional[Dict[str, Any]] = None,
    description: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None,
    session_id: Optional[str] = None,
) -> AuditLog:
    """
    Create an audit log entry.

    Args:
        db: Database session
        event_type: Type of event (use EventType constants)
        event_category: Category of event (use EventCategory constants)
        result: Result of the event (use EventResult constants)
        action: Human-readable description of the action
        user_id: ID of the user performing the action
        username: Username (denormalized for retention)
        user_role: Role of the user
        ip_address: IP address of the client
        user_agent: User agent string
        resource_type: Type of resource affected
        resource_id: ID of the resource
        resource_name: Name of the resource
        old_values: Previous state (for updates)
        new_values: New state (for updates)
        description: Additional description
        metadata: Additional contextual data
        request_id: Request correlation ID
        session_id: Session correlation ID

    Returns:
        Created AuditLog instance
    """
    audit_log = AuditLog(
        timestamp=datetime.utcnow(),
        event_type=event_type,
        event_category=event_category,
        action=action,
        result=result,
        user_id=user_id,
        username=username,
        user_role=user_role,
        ip_address=ip_address,
        user_agent=user_agent,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id else None,
        resource_name=resource_name,
        old_values=old_values,
        new_values=new_values,
        description=description,
        metadata=metadata,
        request_id=request_id,
        session_id=session_id,
    )

    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)

    return audit_log


def log_auth_event(
    db: Session,
    request: Request,
    event_type: str,
    result: str,
    user: Optional[User] = None,
    username: Optional[str] = None,
    description: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> AuditLog:
    """
    Log an authentication event.

    Convenience wrapper for authentication-related audit logs.
    """
    return log_audit_event(
        db=db,
        event_type=event_type,
        event_category=EventCategory.AUTH,
        result=result,
        action=f"User {event_type.lower().replace('_', ' ')}",
        user_id=user.id if user else None,
        username=username or (user.username if user else None),
        user_role=user.role if user else None,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        description=description,
        metadata=metadata,
    )


def log_admin_action(
    db: Session,
    request: Request,
    current_user: User,
    action: str,
    resource_type: str,
    resource_id: Optional[int] = None,
    resource_name: Optional[str] = None,
    old_values: Optional[Dict[str, Any]] = None,
    new_values: Optional[Dict[str, Any]] = None,
    description: Optional[str] = None,
) -> AuditLog:
    """
    Log an admin action.

    Tracks all administrative operations for compliance.
    """
    # Determine event type based on action
    if "create" in action.lower():
        event_type = EventType.ADMIN_CREATE
    elif "update" in action.lower() or "edit" in action.lower():
        event_type = EventType.ADMIN_UPDATE
    elif "delete" in action.lower():
        event_type = EventType.ADMIN_DELETE
    else:
        event_type = EventType.ADMIN_ACCESS

    return log_audit_event(
        db=db,
        event_type=event_type,
        event_category=EventCategory.ADMIN,
        result=EventResult.SUCCESS,
        action=action,
        user_id=current_user.id,
        username=current_user.username,
        user_role=current_user.role,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        resource_type=resource_type,
        resource_id=resource_id,
        resource_name=resource_name,
        old_values=old_values,
        new_values=new_values,
        description=description,
    )


def log_data_access(
    db: Session,
    request: Request,
    current_user: User,
    resource_type: str,
    resource_id: Optional[int] = None,
    action: str = "Data accessed",
) -> AuditLog:
    """
    Log data access event.

    Tracks when users access sensitive data.
    """
    return log_audit_event(
        db=db,
        event_type=EventType.READ,
        event_category=EventCategory.DATA,
        result=EventResult.SUCCESS,
        action=action,
        user_id=current_user.id,
        username=current_user.username,
        user_role=current_user.role,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        resource_type=resource_type,
        resource_id=resource_id,
    )


def log_security_event(
    db: Session,
    request: Request,
    severity: str,
    event_type: str,
    title: str,
    description: str,
    user: Optional[User] = None,
    username: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    auto_alert: bool = True,
) -> SecurityEvent:
    """
    Log a security event that may require attention.

    These are separate from regular audit logs for alerting purposes.

    Args:
        db: Database session
        request: FastAPI request object
        severity: Event severity (use SecuritySeverity constants)
        event_type: Type of security event
        title: Short title/summary
        description: Detailed description
        user: User object if available
        username: Username if user object not available
        metadata: Additional contextual data
        auto_alert: Whether to trigger alerts automatically

    Returns:
        Created SecurityEvent instance
    """
    security_event = SecurityEvent(
        timestamp=datetime.utcnow(),
        severity=severity,
        event_type=event_type,
        title=title,
        description=description,
        user_id=user.id if user else None,
        username=username or (user.username if user else None),
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        status="OPEN",
        metadata=metadata,
    )

    db.add(security_event)

    # Also create audit log for correlation
    audit_log = log_audit_event(
        db=db,
        event_type=event_type,
        event_category=EventCategory.SECURITY,
        result=EventResult.SUCCESS,
        action=title,
        user_id=user.id if user else None,
        username=username or (user.username if user else None),
        user_role=user.role if user else None,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        description=description,
        metadata=metadata,
    )

    security_event.related_audit_log_id = audit_log.id

    db.commit()
    db.refresh(security_event)

    # TODO: Implement alerting based on severity and auto_alert
    # For CRITICAL/HIGH severity events, send immediate alerts
    if auto_alert and severity in [SecuritySeverity.CRITICAL, SecuritySeverity.HIGH]:
        # Placeholder for alert implementation
        security_event.alert_sent = datetime.utcnow()
        db.commit()

    return security_event


def log_failed_login_attempt(
    db: Session,
    request: Request,
    username: str,
    reason: str = "Invalid credentials",
) -> None:
    """
    Log failed login attempt and check for brute force.

    Creates audit log and checks if this constitutes a security event.
    """
    # Log the failed login
    log_auth_event(
        db=db,
        request=request,
        event_type=EventType.LOGIN_FAILED,
        result=EventResult.FAILURE,
        username=username,
        description=reason,
    )

    # Check for brute force (5+ failures in last 15 minutes)
    from datetime import timedelta
    threshold_time = datetime.utcnow() - timedelta(minutes=15)

    recent_failures = db.query(AuditLog).filter(
        AuditLog.event_type == EventType.LOGIN_FAILED,
        AuditLog.username == username,
        AuditLog.timestamp >= threshold_time,
    ).count()

    if recent_failures >= 5:
        log_security_event(
            db=db,
            request=request,
            severity=SecuritySeverity.HIGH,
            event_type="BRUTE_FORCE_ATTEMPT",
            title=f"Brute force attempt detected for user {username}",
            description=f"User {username} has {recent_failures} failed login attempts in the last 15 minutes",
            username=username,
            metadata={"failed_attempts": recent_failures, "threshold_minutes": 15},
        )


def sanitize_for_audit(data: Dict[str, Any], sensitive_fields: list = None) -> Dict[str, Any]:
    """
    Sanitize data for audit logging by removing/masking sensitive fields.

    Args:
        data: Dictionary to sanitize
        sensitive_fields: List of field names to mask (default: common sensitive fields)

    Returns:
        Sanitized dictionary
    """
    if sensitive_fields is None:
        sensitive_fields = [
            "password",
            "hashed_password",
            "secret",
            "secret_key",
            "api_key",
            "token",
            "access_token",
            "refresh_token",
            "credit_card",
            "ssn",
        ]

    sanitized = {}
    for key, value in data.items():
        if any(sensitive in key.lower() for sensitive in sensitive_fields):
            sanitized[key] = "***REDACTED***"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_for_audit(value, sensitive_fields)
        elif isinstance(value, list) and value and isinstance(value[0], dict):
            sanitized[key] = [sanitize_for_audit(item, sensitive_fields) for item in value]
        else:
            sanitized[key] = value

    return sanitized


def get_model_changes(old_obj: Any, new_obj: Any, exclude_fields: list = None) -> tuple:
    """
    Compare two model instances and extract changes.

    Args:
        old_obj: Original object state
        new_obj: New object state
        exclude_fields: Fields to exclude from comparison

    Returns:
        Tuple of (old_values, new_values) dictionaries with only changed fields
    """
    if exclude_fields is None:
        exclude_fields = ["updated_at", "last_modified", "_sa_instance_state"]

    old_values = {}
    new_values = {}

    # Get all columns from the model
    if hasattr(new_obj, "__table__"):
        columns = [c.name for c in new_obj.__table__.columns if c.name not in exclude_fields]

        for column in columns:
            old_val = getattr(old_obj, column, None)
            new_val = getattr(new_obj, column, None)

            if old_val != new_val:
                old_values[column] = str(old_val) if old_val is not None else None
                new_values[column] = str(new_val) if new_val is not None else None

    return sanitize_for_audit(old_values), sanitize_for_audit(new_values)
