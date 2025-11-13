"""
Tests for audit logging functionality.

Tests comprehensive audit logging for compliance (SOC 2, ISO 27001, NIST).
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.audit import AuditLog, SecurityEvent
from app.models.user import User, UserRole
from app.utils.audit import (
    log_audit_event,
    log_auth_event,
    log_admin_action,
    log_failed_login_attempt,
    log_security_event,
    sanitize_for_audit,
    EventType,
    EventCategory,
    EventResult,
    SecuritySeverity,
)


class TestAuditLogCreation:
    """Test audit log entry creation"""

    @pytest.mark.unit
    def test_log_audit_event_basic(self, db_session, mock_request):
        """Test basic audit log creation"""
        log = log_audit_event(
            db=db_session,
            event_type=EventType.LOGIN,
            event_category=EventCategory.AUTH,
            result=EventResult.SUCCESS,
            action="User logged in",
            user_id=1,
            username="testuser",
            ip_address="192.168.1.1",
        )

        assert log.id is not None
        assert log.event_type == EventType.LOGIN
        assert log.event_category == EventCategory.AUTH
        assert log.result == EventResult.SUCCESS
        assert log.username == "testuser"
        assert log.ip_address == "192.168.1.1"
        assert log.timestamp is not None

    @pytest.mark.unit
    def test_log_auth_event(self, db_session, student_user, mock_request):
        """Test authentication event logging"""
        log = log_auth_event(
            db=db_session,
            request=mock_request,
            event_type=EventType.LOGIN,
            result=EventResult.SUCCESS,
            user=student_user,
            description="Successful login"
        )

        assert log.event_category == EventCategory.AUTH
        assert log.user_id == student_user.id
        assert log.username == student_user.username
        assert log.user_role == student_user.role

    @pytest.mark.unit
    def test_log_admin_action(self, db_session, admin_user, mock_request):
        """Test admin action logging"""
        log = log_admin_action(
            db=db_session,
            request=mock_request,
            current_user=admin_user,
            action="Created subject 'Mathematics'",
            resource_type="SUBJECT",
            resource_id=1,
            resource_name="Mathematics",
            new_values={"name": "Mathematics", "code": "MATH101"}
        )

        assert log.event_category == EventCategory.ADMIN
        assert log.resource_type == "SUBJECT"
        assert log.resource_id == "1"
        assert log.new_values["name"] == "Mathematics"

    @pytest.mark.unit
    def test_log_with_change_tracking(self, db_session, admin_user, mock_request):
        """Test logging with before/after values"""
        old_values = {"name": "Math", "code": "MATH"}
        new_values = {"name": "Mathematics", "code": "MATH101"}

        log = log_admin_action(
            db=db_session,
            request=mock_request,
            current_user=admin_user,
            action="Updated subject",
            resource_type="SUBJECT",
            resource_id=1,
            old_values=old_values,
            new_values=new_values
        )

        assert log.old_values["name"] == "Math"
        assert log.new_values["name"] == "Mathematics"


class TestFailedLoginTracking:
    """Test failed login attempt tracking and brute force detection"""

    @pytest.mark.integration
    def test_log_failed_login(self, db_session, mock_request):
        """Test failed login logging"""
        log_failed_login_attempt(
            db=db_session,
            request=mock_request,
            username="testuser",
            reason="Invalid password"
        )

        # Check audit log created
        log = db_session.query(AuditLog).filter(
            AuditLog.event_type == EventType.LOGIN_FAILED
        ).first()

        assert log is not None
        assert log.result == EventResult.FAILURE
        assert log.username == "testuser"

    @pytest.mark.integration
    def test_brute_force_detection(self, db_session, mock_request):
        """Test brute force detection after 5+ failures"""
        # Log 5 failed attempts
        for i in range(5):
            log_failed_login_attempt(
                db=db_session,
                request=mock_request,
                username="targetuser",
                reason="Invalid password"
            )

        # Check security event created
        security_event = db_session.query(SecurityEvent).filter(
            SecurityEvent.event_type == "BRUTE_FORCE_ATTEMPT"
        ).first()

        assert security_event is not None
        assert security_event.severity == SecuritySeverity.HIGH
        assert "targetuser" in security_event.title

    @pytest.mark.integration
    def test_brute_force_time_window(self, db_session, mock_request):
        """Test brute force only triggers within 15min window"""
        # Create old failed attempts (16 minutes ago)
        old_time = datetime.utcnow() - timedelta(minutes=16)

        for i in range(3):
            log = AuditLog(
                timestamp=old_time,
                event_type=EventType.LOGIN_FAILED,
                event_category=EventCategory.AUTH,
                result=EventResult.FAILURE,
                action="Failed login",
                username="testuser",
                ip_address="192.168.1.1"
            )
            db_session.add(log)
        db_session.commit()

        # Add 2 recent failures (should not trigger - only 2 in last 15min)
        for i in range(2):
            log_failed_login_attempt(
                db=db_session,
                request=mock_request,
                username="testuser"
            )

        # Should not create security event
        security_event = db_session.query(SecurityEvent).filter(
            SecurityEvent.username == "testuser"
        ).first()

        assert security_event is None


class TestSecurityEvents:
    """Test security event creation and management"""

    @pytest.mark.unit
    def test_create_security_event(self, db_session, mock_request):
        """Test security event creation"""
        event = log_security_event(
            db=db_session,
            request=mock_request,
            severity=SecuritySeverity.HIGH,
            event_type="UNAUTHORIZED_ACCESS",
            title="Unauthorized admin access attempt",
            description="User attempted to access admin endpoint without permission"
        )

        assert event.id is not None
        assert event.severity == SecuritySeverity.HIGH
        assert event.status == "OPEN"
        assert event.related_audit_log_id is not None

    @pytest.mark.unit
    def test_security_event_with_user(self, db_session, student_user, mock_request):
        """Test security event with user info"""
        event = log_security_event(
            db=db_session,
            request=mock_request,
            severity=SecuritySeverity.MEDIUM,
            event_type="SUSPICIOUS_ACTIVITY",
            title="Suspicious activity detected",
            description="Multiple rapid requests",
            user=student_user
        )

        assert event.user_id == student_user.id
        assert event.username == student_user.username

    @pytest.mark.unit
    def test_auto_alert_high_severity(self, db_session, mock_request):
        """Test auto-alert for high severity events"""
        event = log_security_event(
            db=db_session,
            request=mock_request,
            severity=SecuritySeverity.CRITICAL,
            event_type="CRITICAL_SECURITY_EVENT",
            title="Critical security breach",
            description="Immediate action required",
            auto_alert=True
        )

        # Alert should be marked as sent
        assert event.alert_sent is not None


class TestAuditLogQueries:
    """Test audit log querying and filtering"""

    @pytest.mark.integration
    def test_query_by_user(self, db_session, student_user, mock_request):
        """Test querying logs by user"""
        # Create logs for different users
        log_audit_event(
            db=db_session,
            event_type=EventType.LOGIN,
            event_category=EventCategory.AUTH,
            result=EventResult.SUCCESS,
            action="Login",
            user_id=student_user.id,
            username=student_user.username
        )

        log_audit_event(
            db=db_session,
            event_type=EventType.LOGIN,
            event_category=EventCategory.AUTH,
            result=EventResult.SUCCESS,
            action="Login",
            user_id=999,
            username="otheruser"
        )

        # Query logs for specific user
        user_logs = db_session.query(AuditLog).filter(
            AuditLog.user_id == student_user.id
        ).all()

        assert len(user_logs) == 1
        assert user_logs[0].username == student_user.username

    @pytest.mark.integration
    def test_query_by_event_type(self, db_session):
        """Test querying logs by event type"""
        log_audit_event(
            db=db_session,
            event_type=EventType.LOGIN,
            event_category=EventCategory.AUTH,
            result=EventResult.SUCCESS,
            action="Login"
        )

        log_audit_event(
            db=db_session,
            event_type=EventType.LOGOUT,
            event_category=EventCategory.AUTH,
            result=EventResult.SUCCESS,
            action="Logout"
        )

        login_logs = db_session.query(AuditLog).filter(
            AuditLog.event_type == EventType.LOGIN
        ).all()

        assert len(login_logs) == 1

    @pytest.mark.integration
    def test_query_by_date_range(self, db_session):
        """Test querying logs by date range"""
        # Create log yesterday
        yesterday = datetime.utcnow() - timedelta(days=1)
        old_log = AuditLog(
            timestamp=yesterday,
            event_type=EventType.LOGIN,
            event_category=EventCategory.AUTH,
            result=EventResult.SUCCESS,
            action="Old login"
        )
        db_session.add(old_log)

        # Create log today
        log_audit_event(
            db=db_session,
            event_type=EventType.LOGIN,
            event_category=EventCategory.AUTH,
            result=EventResult.SUCCESS,
            action="Recent login"
        )

        db_session.commit()

        # Query only today's logs
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0)
        recent_logs = db_session.query(AuditLog).filter(
            AuditLog.timestamp >= today_start
        ).all()

        assert len(recent_logs) == 1
        assert "Recent" in recent_logs[0].action


class TestDataSanitization:
    """Test sensitive data sanitization in audit logs"""

    @pytest.mark.unit
    def test_sanitize_password(self):
        """Test password is redacted"""
        data = {
            "username": "testuser",
            "password": "secret123",
            "email": "test@example.com"
        }

        sanitized = sanitize_for_audit(data)

        assert sanitized["username"] == "testuser"
        assert sanitized["password"] == "***REDACTED***"
        assert sanitized["email"] == "test@example.com"

    @pytest.mark.unit
    def test_sanitize_nested_data(self):
        """Test nested sensitive data is redacted"""
        data = {
            "user": {
                "username": "test",
                "password": "secret"
            },
            "settings": {
                "api_key": "abc123"
            }
        }

        sanitized = sanitize_for_audit(data)

        assert sanitized["user"]["password"] == "***REDACTED***"
        assert sanitized["settings"]["api_key"] == "***REDACTED***"

    @pytest.mark.unit
    def test_sanitize_list_of_dicts(self):
        """Test sanitization of list containing dicts"""
        data = {
            "users": [
                {"username": "user1", "password": "pass1"},
                {"username": "user2", "password": "pass2"}
            ]
        }

        sanitized = sanitize_for_audit(data)

        assert all(u["password"] == "***REDACTED***" for u in sanitized["users"])


class TestAuditLogRetention:
    """Test audit log retention policies"""

    @pytest.mark.integration
    def test_old_logs_queryable(self, db_session):
        """Test old logs (1 year) are still queryable"""
        # Create log from 11 months ago
        old_time = datetime.utcnow() - timedelta(days=330)
        old_log = AuditLog(
            timestamp=old_time,
            event_type=EventType.LOGIN,
            event_category=EventCategory.AUTH,
            result=EventResult.SUCCESS,
            action="Old login",
            username="testuser"
        )
        db_session.add(old_log)
        db_session.commit()

        # Should still be queryable
        found = db_session.query(AuditLog).filter(
            AuditLog.username == "testuser"
        ).first()

        assert found is not None
        assert found.action == "Old login"


class TestAuditLogStatistics:
    """Test audit log statistics and aggregations"""

    @pytest.mark.integration
    def test_count_by_category(self, db_session):
        """Test counting logs by category"""
        # Create logs of different categories
        for i in range(3):
            log_audit_event(
                db=db_session,
                event_type=EventType.LOGIN,
                event_category=EventCategory.AUTH,
                result=EventResult.SUCCESS,
                action="Login"
            )

        for i in range(2):
            log_audit_event(
                db=db_session,
                event_type=EventType.ADMIN_CREATE,
                event_category=EventCategory.ADMIN,
                result=EventResult.SUCCESS,
                action="Create"
            )

        # Count by category
        auth_count = db_session.query(AuditLog).filter(
            AuditLog.event_category == EventCategory.AUTH
        ).count()

        admin_count = db_session.query(AuditLog).filter(
            AuditLog.event_category == EventCategory.ADMIN
        ).count()

        assert auth_count == 3
        assert admin_count == 2

    @pytest.mark.integration
    def test_count_failures(self, db_session):
        """Test counting failed operations"""
        # Create success and failure logs
        log_audit_event(
            db=db_session,
            event_type=EventType.LOGIN,
            event_category=EventCategory.AUTH,
            result=EventResult.SUCCESS,
            action="Success login"
        )

        log_audit_event(
            db=db_session,
            event_type=EventType.LOGIN_FAILED,
            event_category=EventCategory.AUTH,
            result=EventResult.FAILURE,
            action="Failed login"
        )

        log_audit_event(
            db=db_session,
            event_type=EventType.LOGIN_FAILED,
            event_category=EventCategory.AUTH,
            result=EventResult.FAILURE,
            action="Failed login"
        )

        # Count failures
        failure_count = db_session.query(AuditLog).filter(
            AuditLog.result == EventResult.FAILURE
        ).count()

        assert failure_count == 2


@pytest.mark.compliance
class TestComplianceRequirements:
    """Test compliance-specific requirements"""

    def test_soc2_cc63_audit_logging(self, db_session, student_user, mock_request):
        """Test SOC 2 CC6.3 - System operations are logged"""
        # All significant events should be logged
        log_auth_event(
            db=db_session,
            request=mock_request,
            event_type=EventType.LOGIN,
            result=EventResult.SUCCESS,
            user=student_user
        )

        logs = db_session.query(AuditLog).all()
        assert len(logs) > 0

        # Verify required fields
        log = logs[0]
        assert log.timestamp is not None
        assert log.user_id is not None
        assert log.action is not None
        assert log.result is not None

    def test_iso27001_a815_logging_requirements(self, db_session):
        """Test ISO 27001 A.8.15 - Logging requirements"""
        # Must log: user IDs, dates, times, device IDs, events
        log = log_audit_event(
            db=db_session,
            event_type=EventType.LOGIN,
            event_category=EventCategory.AUTH,
            result=EventResult.SUCCESS,
            action="User login",
            user_id=1,
            username="testuser",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0..."
        )

        # Verify all required fields present
        assert log.user_id is not None  # User ID
        assert log.timestamp is not None  # Date and time
        assert log.ip_address is not None  # Device identifier
        assert log.event_type is not None  # Event type
        assert log.result is not None  # Success/failure

    def test_gdpr_article5_accountability(self, db_session, student_user):
        """Test GDPR Article 5 - Accountability through audit logs"""
        # Must be able to demonstrate compliance through logs
        log_audit_event(
            db=db_session,
            event_type=EventType.EXPORT,
            event_category=EventCategory.DATA,
            result=EventResult.SUCCESS,
            action="Data export requested",
            user_id=student_user.id,
            username=student_user.username,
            description="User exercised right of access"
        )

        # Should be able to query and prove compliance
        gdpr_logs = db_session.query(AuditLog).filter(
            AuditLog.event_category == EventCategory.DATA
        ).all()

        assert len(gdpr_logs) > 0
        assert gdpr_logs[0].description is not None
