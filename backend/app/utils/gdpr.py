"""
GDPR compliance utilities for data export and deletion.

Implements GDPR Articles 15 (Right of access), 17 (Right to erasure), and 20 (Data portability)
"""

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json
import os
from pathlib import Path

from app.models.user import User
from app.models.quiz import QuizSession, UserAnswer
from app.models.progress import UserProgress, StudySession
from app.models.audit import AuditLog
from app.models.session import UserSession
from app.models.gdpr import (
    ConsentRecord,
    DataExportRequest,
    DataDeletionRequest,
    DataProcessingActivity
)


# Export configuration
EXPORT_DIRECTORY = os.getenv("EXPORT_DIRECTORY", "/tmp/gdpr_exports")
EXPORT_EXPIRY_DAYS = 30  # Export files expire after 30 days


def ensure_export_directory():
    """Ensure export directory exists"""
    Path(EXPORT_DIRECTORY).mkdir(parents=True, exist_ok=True)


# ==================== Data Export (Article 15 & 20) ====================

def collect_user_data(db: Session, user_id: int) -> Dict[str, Any]:
    """
    Collect all user data for GDPR export.

    Returns complete data package including:
    - Personal information
    - Quiz history
    - Progress and achievements
    - Study sessions
    - Audit logs
    - Consent records
    - Active sessions
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError(f"User {user_id} not found")

    # Basic user information
    user_data = {
        "personal_information": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "student_level": user.student_level,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
        },
        "export_metadata": {
            "export_date": datetime.utcnow().isoformat(),
            "export_version": "1.0",
            "data_controller": "Study Platform",
        }
    }

    # Quiz sessions and answers
    quiz_sessions = db.query(QuizSession).filter(QuizSession.user_id == user_id).all()
    user_data["quiz_sessions"] = []

    for session in quiz_sessions:
        session_data = {
            "id": session.id,
            "subject_id": session.subject_id,
            "category_id": session.category_id,
            "difficulty": session.difficulty,
            "total_questions": session.total_questions,
            "correct_answers": session.correct_answers,
            "score": session.score,
            "completed": session.completed,
            "started_at": session.started_at.isoformat() if session.started_at else None,
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
        }

        # Get answers for this session
        answers = db.query(UserAnswer).filter(UserAnswer.quiz_session_id == session.id).all()
        session_data["answers"] = [
            {
                "question_id": answer.question_id,
                "selected_answer": answer.selected_answer,
                "is_correct": answer.is_correct,
                "answered_at": answer.answered_at.isoformat() if answer.answered_at else None,
            }
            for answer in answers
        ]

        user_data["quiz_sessions"].append(session_data)

    # User progress
    progress_records = db.query(UserProgress).filter(UserProgress.user_id == user_id).all()
    user_data["progress"] = [
        {
            "id": p.id,
            "subject_id": p.subject_id,
            "category_id": p.category_id,
            "total_questions_attempted": p.total_questions_attempted,
            "correct_answers": p.correct_answers,
            "accuracy_percentage": p.accuracy_percentage,
            "last_attempt_date": p.last_attempt_date.isoformat() if p.last_attempt_date else None,
        }
        for p in progress_records
    ]

    # Study sessions
    study_sessions = db.query(StudySession).filter(StudySession.user_id == user_id).all()
    user_data["study_sessions"] = [
        {
            "id": s.id,
            "subject_id": s.subject_id,
            "duration_minutes": s.duration_minutes,
            "topics_covered": s.topics_covered,
            "notes": s.notes,
            "session_date": s.session_date.isoformat() if s.session_date else None,
        }
        for s in study_sessions
    ]

    # Audit logs (user's own activities)
    audit_logs = db.query(AuditLog).filter(AuditLog.user_id == user_id).order_by(AuditLog.timestamp.desc()).limit(1000).all()
    user_data["activity_history"] = [
        {
            "id": log.id,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None,
            "event_type": log.event_type,
            "event_category": log.event_category,
            "action": log.action,
            "result": log.result,
            "ip_address": log.ip_address,
            "description": log.description,
        }
        for log in audit_logs
    ]

    # Active sessions
    active_sessions = db.query(UserSession).filter(
        UserSession.user_id == user_id,
        UserSession.is_active == True
    ).all()
    user_data["active_sessions"] = [
        {
            "session_id": s.session_id,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "last_activity_at": s.last_activity_at.isoformat() if s.last_activity_at else None,
            "ip_address": s.ip_address,
            "user_agent": s.user_agent,
        }
        for s in active_sessions
    ]

    # Consent records
    consent_records = db.query(ConsentRecord).filter(ConsentRecord.user_id == user_id).all()
    user_data["consent_records"] = [
        {
            "id": c.id,
            "consent_type": c.consent_type,
            "purpose": c.purpose,
            "consented": c.consented,
            "consented_at": c.consented_at.isoformat() if c.consented_at else None,
            "withdrawn_at": c.withdrawn_at.isoformat() if c.withdrawn_at else None,
            "version": c.version,
            "method": c.method,
        }
        for c in consent_records
    ]

    # Summary statistics
    user_data["statistics"] = {
        "total_quiz_sessions": len(quiz_sessions),
        "total_questions_answered": sum(s.total_questions for s in quiz_sessions),
        "total_correct_answers": sum(s.correct_answers for s in quiz_sessions),
        "average_score": sum(s.score for s in quiz_sessions) / len(quiz_sessions) if quiz_sessions else 0,
        "total_study_time_minutes": sum(s.duration_minutes for s in study_sessions if s.duration_minutes),
        "account_age_days": (datetime.utcnow() - user.created_at).days if user.created_at else 0,
    }

    return user_data


def create_export_file(db: Session, user_id: int, export_format: str = "JSON") -> str:
    """
    Create a data export file for a user.

    Args:
        db: Database session
        user_id: User ID
        export_format: Export format (JSON, CSV)

    Returns:
        Path to the created export file
    """
    ensure_export_directory()

    # Collect user data
    user_data = collect_user_data(db, user_id)

    # Generate filename
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"user_{user_id}_export_{timestamp}.{export_format.lower()}"
    filepath = os.path.join(EXPORT_DIRECTORY, filename)

    # Write to file
    if export_format.upper() == "JSON":
        with open(filepath, 'w') as f:
            json.dump(user_data, f, indent=2, default=str)
    else:
        raise ValueError(f"Unsupported export format: {export_format}")

    return filepath


def process_export_request(db: Session, request_id: int) -> bool:
    """
    Process a data export request.

    Args:
        db: Database session
        request_id: DataExportRequest ID

    Returns:
        True if successful, False otherwise
    """
    export_request = db.query(DataExportRequest).filter(DataExportRequest.id == request_id).first()
    if not export_request:
        return False

    try:
        # Update status
        export_request.status = "PROCESSING"
        export_request.processing_started_at = datetime.utcnow()
        db.commit()

        # Create export file
        filepath = create_export_file(db, export_request.user_id, export_request.export_format)

        # Get file size
        file_size = os.path.getsize(filepath)

        # Update request
        export_request.status = "COMPLETED"
        export_request.completed_at = datetime.utcnow()
        export_request.file_path = filepath
        export_request.file_size_bytes = file_size
        export_request.expires_at = datetime.utcnow() + timedelta(days=EXPORT_EXPIRY_DAYS)
        db.commit()

        return True

    except Exception as e:
        export_request.status = "FAILED"
        export_request.error_message = str(e)
        db.commit()
        return False


# ==================== Data Deletion (Article 17 - Right to Erasure) ====================

def anonymize_user_data(db: Session, user_id: int) -> Dict[str, int]:
    """
    Anonymize user data instead of full deletion (soft delete).

    This approach:
    - Removes PII (email, name, username)
    - Keeps statistical data for analytics
    - Maintains data integrity for related records

    Returns:
        Dictionary with counts of anonymized records
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError(f"User {user_id} not found")

    results = {"user": 0, "audit_logs": 0, "sessions": 0}

    # Anonymize user record
    user.username = f"deleted_user_{user_id}"
    user.email = f"deleted_{user_id}@anonymized.local"
    user.full_name = "Deleted User"
    user.is_active = False
    user.hashed_password = "DELETED"
    results["user"] = 1

    # Anonymize audit logs (keep for compliance, but remove PII)
    audit_logs = db.query(AuditLog).filter(AuditLog.user_id == user_id).all()
    for log in audit_logs:
        log.username = f"deleted_user_{user_id}"
        log.ip_address = "0.0.0.0"
        log.user_agent = "DELETED"
    results["audit_logs"] = len(audit_logs)

    # Revoke all sessions
    sessions = db.query(UserSession).filter(UserSession.user_id == user_id).all()
    for session in sessions:
        session.revoke(reason="Account deleted")
        session.ip_address = "0.0.0.0"
        session.user_agent = "DELETED"
    results["sessions"] = len(sessions)

    db.commit()
    return results


def delete_user_data(db: Session, user_id: int, keep_analytics: bool = True) -> Dict[str, int]:
    """
    Delete user data (hard delete).

    Args:
        db: Database session
        user_id: User ID
        keep_analytics: If True, anonymize instead of delete to keep analytics

    Returns:
        Dictionary with counts of deleted records
    """
    if keep_analytics:
        return anonymize_user_data(db, user_id)

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError(f"User {user_id} not found")

    results = {}

    # Delete quiz sessions and answers (cascades)
    quiz_sessions = db.query(QuizSession).filter(QuizSession.user_id == user_id).all()
    results["quiz_sessions"] = len(quiz_sessions)
    for session in quiz_sessions:
        db.delete(session)

    # Delete progress records
    progress = db.query(UserProgress).filter(UserProgress.user_id == user_id).all()
    results["progress_records"] = len(progress)
    for p in progress:
        db.delete(p)

    # Delete study sessions
    study_sessions = db.query(StudySession).filter(StudySession.user_id == user_id).all()
    results["study_sessions"] = len(study_sessions)
    for s in study_sessions:
        db.delete(s)

    # Delete sessions (cascades via relationship)
    sessions = db.query(UserSession).filter(UserSession.user_id == user_id).all()
    results["sessions"] = len(sessions)
    for session in sessions:
        db.delete(session)

    # Delete consent records
    consents = db.query(ConsentRecord).filter(ConsentRecord.user_id == user_id).all()
    results["consent_records"] = len(consents)
    for c in consents:
        db.delete(c)

    # Keep audit logs for compliance (anonymize instead)
    audit_logs = db.query(AuditLog).filter(AuditLog.user_id == user_id).all()
    for log in audit_logs:
        log.username = f"deleted_user_{user_id}"
        log.user_id = None  # Remove FK reference
        log.ip_address = "0.0.0.0"
        log.user_agent = "DELETED"
    results["audit_logs_anonymized"] = len(audit_logs)

    # Finally, delete the user
    db.delete(user)
    results["user"] = 1

    db.commit()
    return results


def process_deletion_request(db: Session, request_id: int, approved_by_id: Optional[int] = None) -> bool:
    """
    Process a data deletion request.

    Args:
        db: Database session
        request_id: DataDeletionRequest ID
        approved_by_id: Admin user ID who approved (if required)

    Returns:
        True if successful, False otherwise
    """
    deletion_request = db.query(DataDeletionRequest).filter(DataDeletionRequest.id == request_id).first()
    if not deletion_request:
        return False

    try:
        # Update status
        deletion_request.status = "PROCESSING"
        deletion_request.processing_started_at = datetime.utcnow()
        if approved_by_id:
            deletion_request.approved_by = approved_by_id
            deletion_request.approved_at = datetime.utcnow()
        db.commit()

        # Perform deletion
        keep_analytics = (deletion_request.deletion_scope == "ANONYMIZE")
        deleted_data = delete_user_data(db, deletion_request.user_id, keep_analytics=keep_analytics)

        # Update request
        deletion_request.status = "COMPLETED"
        deletion_request.completed_at = datetime.utcnow()
        deletion_request.deleted_data = deleted_data
        db.commit()

        return True

    except Exception as e:
        deletion_request.status = "FAILED"
        deletion_request.error_message = str(e)
        db.commit()
        return False


# ==================== Consent Management (Article 7) ====================

def record_consent(
    db: Session,
    user_id: int,
    consent_type: str,
    purpose: str,
    version: str,
    consented: bool,
    method: str = "explicit_checkbox",
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> ConsentRecord:
    """
    Record user consent.

    Args:
        db: Database session
        user_id: User ID
        consent_type: Type of consent (e.g., "terms_of_service", "privacy_policy")
        purpose: Clear description of data processing purpose
        version: Version of the policy
        consented: Whether user consented
        method: Method of consent collection
        ip_address: User's IP address
        user_agent: User's user agent

    Returns:
        Created ConsentRecord
    """
    consent = ConsentRecord(
        user_id=user_id,
        consent_type=consent_type,
        purpose=purpose,
        version=version,
        consented=consented,
        consented_at=datetime.utcnow() if consented else None,
        method=method,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    db.add(consent)
    db.commit()
    db.refresh(consent)

    return consent


def withdraw_consent(db: Session, user_id: int, consent_type: str) -> bool:
    """
    Withdraw user consent.

    Args:
        db: Database session
        user_id: User ID
        consent_type: Type of consent to withdraw

    Returns:
        True if successful, False if consent not found
    """
    consent = db.query(ConsentRecord).filter(
        ConsentRecord.user_id == user_id,
        ConsentRecord.consent_type == consent_type,
        ConsentRecord.consented == True
    ).order_by(ConsentRecord.created_at.desc()).first()

    if not consent:
        return False

    consent.withdraw()
    db.commit()

    return True


def get_active_consents(db: Session, user_id: int) -> List[ConsentRecord]:
    """Get all active consents for a user"""
    return db.query(ConsentRecord).filter(
        ConsentRecord.user_id == user_id,
        ConsentRecord.consented == True
    ).all()


def has_consent(db: Session, user_id: int, consent_type: str) -> bool:
    """Check if user has active consent for a specific type"""
    consent = db.query(ConsentRecord).filter(
        ConsentRecord.user_id == user_id,
        ConsentRecord.consent_type == consent_type,
        ConsentRecord.consented == True
    ).first()

    return consent is not None
