"""
Compliance and Audit Logging API Endpoints

Provides access to audit logs and security events for compliance reporting and incident investigation.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta

from ..utils.database import get_db
from ..utils.auth import get_current_user, get_admin_or_teacher
from ..models import AuditLog, SecurityEvent, User, UserRole

router = APIRouter(prefix="/api/compliance", tags=["compliance"])


# ==================== Pydantic Schemas ====================

class AuditLogResponse(BaseModel):
    id: int
    timestamp: datetime
    event_type: str
    event_category: str
    action: str
    result: str
    user_id: Optional[int]
    username: Optional[str]
    user_role: Optional[str]
    ip_address: Optional[str]
    resource_type: Optional[str]
    resource_id: Optional[str]
    resource_name: Optional[str]
    description: Optional[str]

    class Config:
        from_attributes = True


class SecurityEventResponse(BaseModel):
    id: int
    timestamp: datetime
    severity: str
    event_type: str
    title: str
    description: str
    user_id: Optional[int]
    username: Optional[str]
    ip_address: Optional[str]
    status: str
    resolved_at: Optional[datetime]

    class Config:
        from_attributes = True


class AuditLogDetailResponse(AuditLogResponse):
    """Detailed audit log with change history"""
    old_values: Optional[dict]
    new_values: Optional[dict]
    metadata: Optional[dict]
    user_agent: Optional[str]
    request_id: Optional[str]
    session_id: Optional[str]

    class Config:
        from_attributes = True


class SecurityEventDetailResponse(SecurityEventResponse):
    """Detailed security event with resolution info"""
    resolved_by: Optional[int]
    resolution_notes: Optional[str]
    alert_sent: Optional[datetime]
    metadata: Optional[dict]

    class Config:
        from_attributes = True


class AuditLogStats(BaseModel):
    """Statistics for audit log overview"""
    total_logs: int
    logs_by_category: dict
    logs_by_result: dict
    top_users: List[dict]
    recent_failures: int


# ==================== Audit Log Endpoints ====================

@router.get("/audit-logs", response_model=List[AuditLogResponse])
def get_audit_logs(
    event_type: Optional[str] = None,
    event_category: Optional[str] = None,
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    result: Optional[str] = None,
    resource_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_or_teacher)
):
    """
    Get audit logs with optional filters.

    Requires admin or teacher role.
    """
    query = db.query(AuditLog)

    # Apply filters
    if event_type:
        query = query.filter(AuditLog.event_type == event_type)
    if event_category:
        query = query.filter(AuditLog.event_category == event_category)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if username:
        query = query.filter(AuditLog.username == username)
    if result:
        query = query.filter(AuditLog.result == result)
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    if start_date:
        query = query.filter(AuditLog.timestamp >= start_date)
    if end_date:
        query = query.filter(AuditLog.timestamp <= end_date)

    # Order by timestamp descending (most recent first)
    query = query.order_by(AuditLog.timestamp.desc())

    # Paginate
    audit_logs = query.offset(skip).limit(limit).all()

    return audit_logs


@router.get("/audit-logs/{audit_log_id}", response_model=AuditLogDetailResponse)
def get_audit_log_detail(
    audit_log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_or_teacher)
):
    """
    Get detailed audit log entry including change history.

    Requires admin or teacher role.
    """
    audit_log = db.query(AuditLog).filter(AuditLog.id == audit_log_id).first()
    if not audit_log:
        raise HTTPException(status_code=404, detail="Audit log not found")

    return audit_log


@router.get("/audit-logs/user/{user_id}", response_model=List[AuditLogResponse])
def get_user_audit_logs(
    user_id: int,
    event_category: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_or_teacher)
):
    """
    Get all audit logs for a specific user.

    Requires admin or teacher role.
    """
    query = db.query(AuditLog).filter(AuditLog.user_id == user_id)

    if event_category:
        query = query.filter(AuditLog.event_category == event_category)
    if start_date:
        query = query.filter(AuditLog.timestamp >= start_date)
    if end_date:
        query = query.filter(AuditLog.timestamp <= end_date)

    query = query.order_by(AuditLog.timestamp.desc())
    audit_logs = query.offset(skip).limit(limit).all()

    return audit_logs


@router.get("/audit-logs/stats", response_model=AuditLogStats)
def get_audit_log_stats(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_or_teacher)
):
    """
    Get audit log statistics for the specified number of days.

    Requires admin or teacher role.
    """
    since = datetime.utcnow() - timedelta(days=days)

    # Total logs
    total_logs = db.query(AuditLog).filter(AuditLog.timestamp >= since).count()

    # Logs by category
    logs_by_category = {}
    categories = db.query(
        AuditLog.event_category,
        db.func.count(AuditLog.id)
    ).filter(
        AuditLog.timestamp >= since
    ).group_by(AuditLog.event_category).all()

    for category, count in categories:
        logs_by_category[category] = count

    # Logs by result
    logs_by_result = {}
    results = db.query(
        AuditLog.result,
        db.func.count(AuditLog.id)
    ).filter(
        AuditLog.timestamp >= since
    ).group_by(AuditLog.result).all()

    for result, count in results:
        logs_by_result[result] = count

    # Top users by activity
    top_users = []
    user_activity = db.query(
        AuditLog.user_id,
        AuditLog.username,
        db.func.count(AuditLog.id).label('count')
    ).filter(
        AuditLog.timestamp >= since,
        AuditLog.user_id.isnot(None)
    ).group_by(
        AuditLog.user_id,
        AuditLog.username
    ).order_by(
        db.func.count(AuditLog.id).desc()
    ).limit(10).all()

    for user_id, username, count in user_activity:
        top_users.append({
            "user_id": user_id,
            "username": username,
            "activity_count": count
        })

    # Recent failures
    recent_failures = db.query(AuditLog).filter(
        AuditLog.timestamp >= since,
        AuditLog.result == "FAILURE"
    ).count()

    return {
        "total_logs": total_logs,
        "logs_by_category": logs_by_category,
        "logs_by_result": logs_by_result,
        "top_users": top_users,
        "recent_failures": recent_failures
    }


# ==================== Security Event Endpoints ====================

@router.get("/security-events", response_model=List[SecurityEventResponse])
def get_security_events(
    severity: Optional[str] = None,
    event_type: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_or_teacher)
):
    """
    Get security events with optional filters.

    Requires admin or teacher role.
    """
    query = db.query(SecurityEvent)

    # Apply filters
    if severity:
        query = query.filter(SecurityEvent.severity == severity)
    if event_type:
        query = query.filter(SecurityEvent.event_type == event_type)
    if status:
        query = query.filter(SecurityEvent.status == status)
    if start_date:
        query = query.filter(SecurityEvent.timestamp >= start_date)
    if end_date:
        query = query.filter(SecurityEvent.timestamp <= end_date)

    # Order by timestamp descending (most recent first)
    query = query.order_by(SecurityEvent.timestamp.desc())

    # Paginate
    security_events = query.offset(skip).limit(limit).all()

    return security_events


@router.get("/security-events/{event_id}", response_model=SecurityEventDetailResponse)
def get_security_event_detail(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_or_teacher)
):
    """
    Get detailed security event including resolution information.

    Requires admin or teacher role.
    """
    security_event = db.query(SecurityEvent).filter(SecurityEvent.id == event_id).first()
    if not security_event:
        raise HTTPException(status_code=404, detail="Security event not found")

    return security_event


@router.put("/security-events/{event_id}/resolve")
def resolve_security_event(
    event_id: int,
    resolution_notes: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_or_teacher)
):
    """
    Resolve a security event.

    Requires admin or teacher role.
    """
    security_event = db.query(SecurityEvent).filter(SecurityEvent.id == event_id).first()
    if not security_event:
        raise HTTPException(status_code=404, detail="Security event not found")

    if security_event.status == "RESOLVED":
        raise HTTPException(
            status_code=400,
            detail="Security event is already resolved"
        )

    # Update security event
    security_event.status = "RESOLVED"
    security_event.resolved_at = datetime.utcnow()
    security_event.resolved_by = current_user.id
    security_event.resolution_notes = resolution_notes

    db.commit()
    db.refresh(security_event)

    return {
        "message": "Security event resolved successfully",
        "event": security_event
    }


@router.get("/security-events/open/count")
def get_open_security_events_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_or_teacher)
):
    """
    Get count of open security events by severity.

    Requires admin or teacher role.
    """
    open_events = db.query(SecurityEvent).filter(SecurityEvent.status == "OPEN")

    critical = open_events.filter(SecurityEvent.severity == "CRITICAL").count()
    high = open_events.filter(SecurityEvent.severity == "HIGH").count()
    medium = open_events.filter(SecurityEvent.severity == "MEDIUM").count()
    low = open_events.filter(SecurityEvent.severity == "LOW").count()

    return {
        "critical": critical,
        "high": high,
        "medium": medium,
        "low": low,
        "total": critical + high + medium + low
    }


# ==================== My Activity ====================

@router.get("/my-activity", response_model=List[AuditLogResponse])
def get_my_activity(
    event_category: Optional[str] = None,
    days: int = Query(30, ge=1, le=90),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's audit log activity.

    Any authenticated user can view their own activity.
    """
    since = datetime.utcnow() - timedelta(days=days)

    query = db.query(AuditLog).filter(
        AuditLog.user_id == current_user.id,
        AuditLog.timestamp >= since
    )

    if event_category:
        query = query.filter(AuditLog.event_category == event_category)

    query = query.order_by(AuditLog.timestamp.desc())
    audit_logs = query.offset(skip).limit(limit).all()

    return audit_logs
