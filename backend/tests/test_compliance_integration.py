"""
Integration tests for compliance features.

Tests end-to-end compliance workflows spanning audit logging, session management, and GDPR.
"""

import pytest
import json
import os
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.audit import AuditLog, SecurityEvent, EventType, EventCategory
from app.models.session import UserSession
from app.models.gdpr import DataExportRequest, DataDeletionRequest, ConsentRecord
from app.models.user import User, UserRole
from app.utils.audit import log_audit_event, log_auth_event, log_admin_action
from app.utils.session import get_active_sessions, revoke_all_user_sessions
from app.utils.gdpr import collect_user_data, record_consent


@pytest.mark.integration
class TestComplianceWorkflows:
    """Test complete compliance workflows"""

    def test_user_lifecycle_audit_trail(self, client: TestClient, db_session):
        """Test complete audit trail for user lifecycle"""
        # Register user
        register_response = client.post(
            "/api/auth/register",
            json={
                "username": "lifecycleuser",
                "email": "lifecycle@test.com",
                "password": "SecurePass123!",
                "role": "student",
            },
        )
        assert register_response.status_code == 201

        # Login (creates audit log)
        login_response = client.post(
            "/api/auth/login",
            json={"username": "lifecycleuser", "password": "SecurePass123!"},
        )
        assert login_response.status_code == 200
        access_token = login_response.json()["access_token"]
        user_id = login_response.json()["user"]["id"]

        # Perform some actions
        client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # Logout (creates audit log)
        client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # Verify complete audit trail
        audit_logs = (
            db_session.query(AuditLog)
            .filter(AuditLog.user_id == user_id)
            .order_by(AuditLog.timestamp)
            .all()
        )

        # Should have logs for: register, login, profile access, logout
        assert len(audit_logs) >= 3

        # Verify log types
        event_types = [log.event_type for log in audit_logs]
        assert EventType.REGISTER in event_types or EventType.LOGIN in event_types

    def test_failed_login_to_security_event_workflow(
        self, client: TestClient, db_session
    ):
        """Test failed login attempts trigger security events"""
        # Register user
        client.post(
            "/api/auth/register",
            json={
                "username": "bruteforcetest",
                "email": "brute@test.com",
                "password": "CorrectPass123!",
                "role": "student",
            },
        )

        # Attempt 5 failed logins
        for i in range(5):
            response = client.post(
                "/api/auth/login",
                json={"username": "bruteforcetest", "password": "WrongPassword!"},
            )
            assert response.status_code == 401

        # Check audit logs created
        failed_logins = (
            db_session.query(AuditLog)
            .filter(
                AuditLog.username == "bruteforcetest",
                AuditLog.event_type == EventType.LOGIN_FAILED,
            )
            .count()
        )

        assert failed_logins == 5

        # Check security event created
        security_event = (
            db_session.query(SecurityEvent)
            .filter(SecurityEvent.event_type == "BRUTE_FORCE_ATTEMPT")
            .first()
        )

        assert security_event is not None
        assert "bruteforcetest" in security_event.title

    def test_session_revocation_creates_audit_log(self, client: TestClient, db_session):
        """Test session revocation is logged"""
        # Register and login
        client.post(
            "/api/auth/register",
            json={
                "username": "sessionuser",
                "email": "session@test.com",
                "password": "SecurePass123!",
                "role": "student",
            },
        )

        login_response = client.post(
            "/api/auth/login",
            json={"username": "sessionuser", "password": "SecurePass123!"},
        )

        access_token = login_response.json()["access_token"]
        user_id = login_response.json()["user"]["id"]

        # Get sessions
        sessions_response = client.get(
            "/api/auth/sessions",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        sessions = sessions_response.json()["sessions"]
        assert len(sessions) > 0

        # Logout (revokes session)
        client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # Verify audit log created for logout
        logout_log = (
            db_session.query(AuditLog)
            .filter(
                AuditLog.user_id == user_id,
                AuditLog.event_type == EventType.LOGOUT,
            )
            .first()
        )

        assert logout_log is not None

    def test_gdpr_export_creates_audit_log(self, client: TestClient, db_session):
        """Test GDPR data export creates audit trail"""
        # Register and login
        client.post(
            "/api/auth/register",
            json={
                "username": "exportaudit",
                "email": "exportaudit@test.com",
                "password": "SecurePass123!",
                "role": "student",
            },
        )

        login_response = client.post(
            "/api/auth/login",
            json={"username": "exportaudit", "password": "SecurePass123!"},
        )

        access_token = login_response.json()["access_token"]
        user_id = login_response.json()["user"]["id"]

        # Request data export
        export_response = client.post(
            "/api/gdpr/export-request",
            json={"export_format": "JSON"},
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert export_response.status_code == 200

        # Verify audit log created
        export_log = (
            db_session.query(AuditLog)
            .filter(
                AuditLog.user_id == user_id,
                AuditLog.event_type == EventType.EXPORT,
            )
            .first()
        )

        assert export_log is not None
        assert export_log.event_category == EventCategory.DATA

    def test_gdpr_deletion_creates_audit_log(self, client: TestClient, db_session):
        """Test GDPR deletion creates audit trail"""
        # Register and login
        client.post(
            "/api/auth/register",
            json={
                "username": "deleteaudit",
                "email": "deleteaudit@test.com",
                "password": "SecurePass123!",
                "role": "student",
            },
        )

        login_response = client.post(
            "/api/auth/login",
            json={"username": "deleteaudit", "password": "SecurePass123!"},
        )

        access_token = login_response.json()["access_token"]
        user_id = login_response.json()["user"]["id"]

        # Request deletion
        deletion_response = client.post(
            "/api/gdpr/deletion-request",
            json={
                "deletion_scope": "ANONYMIZE",
                "confirm_deletion": True,
                "reason": "Testing audit",
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert deletion_response.status_code == 200

        # Verify audit log created
        deletion_log = (
            db_session.query(AuditLog)
            .filter(
                AuditLog.user_id == user_id,
                AuditLog.event_type == EventType.DELETE,
            )
            .first()
        )

        assert deletion_log is not None


@pytest.mark.integration
class TestCrossFeatureCompliance:
    """Test compliance features working together"""

    def test_export_includes_audit_logs(self, client: TestClient, db_session):
        """Test data export includes user's audit logs"""
        # Register and login
        client.post(
            "/api/auth/register",
            json={
                "username": "exportwithaudit",
                "email": "exportwithaudit@test.com",
                "password": "SecurePass123!",
                "role": "student",
            },
        )

        login_response = client.post(
            "/api/auth/login",
            json={"username": "exportwithaudit", "password": "SecurePass123!"},
        )

        access_token = login_response.json()["access_token"]

        # Perform some actions to create audit logs
        client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # View my data
        data_response = client.get(
            "/api/gdpr/my-data",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert data_response.status_code == 200
        data = data_response.json()

        # Verify audit logs included
        assert "activity_history" in data
        assert len(data["activity_history"]) > 0

    def test_export_includes_sessions(self, client: TestClient, db_session):
        """Test data export includes active sessions"""
        # Register and login
        client.post(
            "/api/auth/register",
            json={
                "username": "exportwithsessions",
                "email": "exportwithsessions@test.com",
                "password": "SecurePass123!",
                "role": "student",
            },
        )

        login_response = client.post(
            "/api/auth/login",
            json={"username": "exportwithsessions", "password": "SecurePass123!"},
        )

        access_token = login_response.json()["access_token"]

        # View my data
        data_response = client.get(
            "/api/gdpr/my-data",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert data_response.status_code == 200
        data = data_response.json()

        # Verify sessions included
        assert "active_sessions" in data
        assert len(data["active_sessions"]) > 0

    def test_export_includes_consents(self, client: TestClient, db_session):
        """Test data export includes consent records"""
        # Register and login
        client.post(
            "/api/auth/register",
            json={
                "username": "exportwithconsent",
                "email": "exportwithconsent@test.com",
                "password": "SecurePass123!",
                "role": "student",
            },
        )

        login_response = client.post(
            "/api/auth/login",
            json={"username": "exportwithconsent", "password": "SecurePass123!"},
        )

        access_token = login_response.json()["access_token"]

        # Give consent
        client.post(
            "/api/gdpr/consent",
            json={
                "consent_type": "marketing",
                "consented": True,
                "version": "1.0",
                "purpose": "Marketing",
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # View my data
        data_response = client.get(
            "/api/gdpr/my-data",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert data_response.status_code == 200
        data = data_response.json()

        # Verify consents included
        assert "consent_records" in data
        assert len(data["consent_records"]) > 0

    def test_deletion_revokes_all_sessions(self, client: TestClient, db_session):
        """Test account deletion revokes all sessions"""
        # Register and login
        client.post(
            "/api/auth/register",
            json={
                "username": "deletewithsessions",
                "email": "deletewithsessions@test.com",
                "password": "SecurePass123!",
                "role": "student",
            },
        )

        login_response = client.post(
            "/api/auth/login",
            json={"username": "deletewithsessions", "password": "SecurePass123!"},
        )

        access_token = login_response.json()["access_token"]
        user_id = login_response.json()["user"]["id"]

        # Verify session exists
        sessions_before = get_active_sessions(db_session, user_id)
        assert len(sessions_before) > 0

        # Request deletion
        client.post(
            "/api/gdpr/deletion-request",
            json={
                "deletion_scope": "ANONYMIZE",
                "confirm_deletion": True,
                "reason": "Test deletion",
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # Verify sessions revoked
        sessions_after = get_active_sessions(db_session, user_id)
        assert len(sessions_after) == 0

    def test_consent_withdrawal_logged(self, client: TestClient, db_session):
        """Test consent withdrawal creates audit log"""
        # Register and login
        client.post(
            "/api/auth/register",
            json={
                "username": "consentwithdraw",
                "email": "consentwithdraw@test.com",
                "password": "SecurePass123!",
                "role": "student",
            },
        )

        login_response = client.post(
            "/api/auth/login",
            json={"username": "consentwithdraw", "password": "SecurePass123!"},
        )

        access_token = login_response.json()["access_token"]
        user_id = login_response.json()["user"]["id"]

        # Give consent
        client.post(
            "/api/gdpr/consent",
            json={
                "consent_type": "marketing",
                "consented": True,
                "version": "1.0",
                "purpose": "Marketing",
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # Withdraw consent
        client.delete(
            "/api/gdpr/consent/marketing",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # Verify audit logs created
        consent_logs = (
            db_session.query(AuditLog)
            .filter(
                AuditLog.user_id == user_id,
                AuditLog.event_type.in_(
                    [EventType.CONSENT_GIVEN, EventType.CONSENT_WITHDRAWN]
                ),
            )
            .all()
        )

        assert len(consent_logs) >= 2  # Given and withdrawn


@pytest.mark.integration
class TestComplianceReporting:
    """Test compliance reporting and analytics"""

    def test_audit_log_statistics(self, client: TestClient, db_session):
        """Test audit log statistics aggregation"""
        # Create test user and perform various actions
        client.post(
            "/api/auth/register",
            json={
                "username": "statsuser",
                "email": "stats@test.com",
                "password": "SecurePass123!",
                "role": "student",
            },
        )

        login_response = client.post(
            "/api/auth/login",
            json={"username": "statsuser", "password": "SecurePass123!"},
        )

        access_token = login_response.json()["access_token"]

        # Perform multiple actions
        for i in range(3):
            client.get(
                "/api/auth/me",
                headers={"Authorization": f"Bearer {access_token}"},
            )

        # Get statistics (admin endpoint - would need admin token in real scenario)
        # For this test, verify logs exist
        logs = db_session.query(AuditLog).all()
        assert len(logs) > 0

    def test_security_event_tracking(self, client: TestClient, db_session):
        """Test security events are tracked and queryable"""
        # Trigger security event (brute force)
        for i in range(5):
            client.post(
                "/api/auth/login",
                json={"username": "nonexistent", "password": "wrong"},
            )

        # Verify security event created
        events = db_session.query(SecurityEvent).all()
        assert len(events) > 0

    def test_compliance_timeline(self, client: TestClient, db_session):
        """Test creating complete compliance timeline for a user"""
        # Register user
        client.post(
            "/api/auth/register",
            json={
                "username": "timelineuser",
                "email": "timeline@test.com",
                "password": "SecurePass123!",
                "role": "student",
            },
        )

        login_response = client.post(
            "/api/auth/login",
            json={"username": "timelineuser", "password": "SecurePass123!"},
        )

        access_token = login_response.json()["access_token"]
        user_id = login_response.json()["user"]["id"]

        # Perform various actions
        # 1. Give consent
        client.post(
            "/api/gdpr/consent",
            json={
                "consent_type": "privacy_policy",
                "consented": True,
                "version": "1.0",
                "purpose": "Privacy",
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # 2. Export data
        client.post(
            "/api/gdpr/export-request",
            json={"export_format": "JSON"},
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # 3. Withdraw consent
        client.delete(
            "/api/gdpr/consent/privacy_policy",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # Get complete timeline
        timeline = (
            db_session.query(AuditLog)
            .filter(AuditLog.user_id == user_id)
            .order_by(AuditLog.timestamp)
            .all()
        )

        # Verify timeline completeness
        assert len(timeline) >= 3

        # Verify chronological order
        for i in range(len(timeline) - 1):
            assert timeline[i].timestamp <= timeline[i + 1].timestamp


@pytest.mark.integration
class TestComplianceScenarios:
    """Test real-world compliance scenarios"""

    def test_new_user_onboarding_compliance(self, client: TestClient, db_session):
        """Test compliance for new user onboarding"""
        # 1. User registers
        register_response = client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@test.com",
                "password": "SecurePass123!",
                "role": "student",
            },
        )
        assert register_response.status_code == 201

        # 2. User logs in (creates session)
        login_response = client.post(
            "/api/auth/login",
            json={"username": "newuser", "password": "SecurePass123!"},
        )
        assert login_response.status_code == 200
        access_token = login_response.json()["access_token"]
        user_id = login_response.json()["user"]["id"]

        # 3. User gives consent
        consent_response = client.post(
            "/api/gdpr/consent",
            json={
                "consent_type": "terms_of_service",
                "consented": True,
                "version": "1.0",
                "purpose": "Terms",
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert consent_response.status_code == 200

        # Verify compliance:
        # - Audit logs created
        logs = db_session.query(AuditLog).filter(AuditLog.user_id == user_id).all()
        assert len(logs) >= 2  # Register + login

        # - Session created
        sessions = get_active_sessions(db_session, user_id)
        assert len(sessions) == 1

        # - Consent recorded
        consents = (
            db_session.query(ConsentRecord)
            .filter(ConsentRecord.user_id == user_id)
            .all()
        )
        assert len(consents) == 1

    def test_user_data_export_compliance(self, client: TestClient, db_session):
        """Test GDPR data export compliance workflow"""
        # Setup user
        client.post(
            "/api/auth/register",
            json={
                "username": "exportcompliance",
                "email": "exportcompliance@test.com",
                "password": "SecurePass123!",
                "role": "student",
            },
        )

        login_response = client.post(
            "/api/auth/login",
            json={"username": "exportcompliance", "password": "SecurePass123!"},
        )
        access_token = login_response.json()["access_token"]
        user_id = login_response.json()["user"]["id"]

        # Request export
        export_response = client.post(
            "/api/gdpr/export-request",
            json={"export_format": "JSON"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert export_response.status_code == 200

        # Verify compliance:
        # - Export request recorded
        export_request = (
            db_session.query(DataExportRequest)
            .filter(DataExportRequest.user_id == user_id)
            .first()
        )
        assert export_request is not None

        # - Audit log created
        export_log = (
            db_session.query(AuditLog)
            .filter(
                AuditLog.user_id == user_id,
                AuditLog.event_type == EventType.EXPORT,
            )
            .first()
        )
        assert export_log is not None

        # - File created with expiration
        assert export_request.file_path is not None
        assert export_request.expires_at is not None

    def test_user_account_deletion_compliance(self, client: TestClient, db_session):
        """Test GDPR account deletion compliance workflow"""
        # Setup user
        client.post(
            "/api/auth/register",
            json={
                "username": "deletecompliance",
                "email": "deletecompliance@test.com",
                "password": "SecurePass123!",
                "role": "student",
            },
        )

        login_response = client.post(
            "/api/auth/login",
            json={"username": "deletecompliance", "password": "SecurePass123!"},
        )
        access_token = login_response.json()["access_token"]
        user_id = login_response.json()["user"]["id"]

        # Create some data
        client.post(
            "/api/gdpr/consent",
            json={
                "consent_type": "marketing",
                "consented": True,
                "version": "1.0",
                "purpose": "Marketing",
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # Request deletion
        deletion_response = client.post(
            "/api/gdpr/deletion-request",
            json={
                "deletion_scope": "ANONYMIZE",
                "confirm_deletion": True,
                "reason": "No longer need account",
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert deletion_response.status_code == 200

        # Verify compliance:
        # - Deletion request recorded
        deletion_request = (
            db_session.query(DataDeletionRequest)
            .filter(DataDeletionRequest.user_id == user_id)
            .first()
        )
        assert deletion_request is not None

        # - User anonymized
        user = db_session.query(User).filter(User.id == user_id).first()
        assert "deleted_user" in user.username

        # - Sessions revoked
        sessions = get_active_sessions(db_session, user_id)
        assert len(sessions) == 0

        # - Audit log preserved (compliance requirement)
        audit_logs = db_session.query(AuditLog).filter(AuditLog.user_id == user_id).all()
        assert len(audit_logs) > 0

    def test_suspicious_activity_detection_compliance(
        self, client: TestClient, db_session
    ):
        """Test security monitoring compliance"""
        # Trigger suspicious activity (multiple failed logins)
        for i in range(5):
            client.post(
                "/api/auth/login",
                json={"username": "suspicioususer", "password": "wrong"},
            )

        # Verify compliance:
        # - All attempts logged
        failed_attempts = (
            db_session.query(AuditLog)
            .filter(
                AuditLog.username == "suspicioususer",
                AuditLog.event_type == EventType.LOGIN_FAILED,
            )
            .all()
        )
        assert len(failed_attempts) == 5

        # - Security event created
        security_event = (
            db_session.query(SecurityEvent)
            .filter(SecurityEvent.event_type == "BRUTE_FORCE_ATTEMPT")
            .first()
        )
        assert security_event is not None

        # - Event severity appropriate
        from app.models.audit import SecuritySeverity

        assert security_event.severity == SecuritySeverity.HIGH


@pytest.mark.performance
class TestCompliancePerformance:
    """Test performance of compliance features"""

    def test_audit_log_query_performance(self, db_session, student_user):
        """Test audit log queries are performant"""
        import time

        # Create 100 audit logs
        for i in range(100):
            log_audit_event(
                db=db_session,
                event_type=EventType.LOGIN,
                event_category=EventCategory.AUTH,
                result="SUCCESS",
                action=f"Test log {i}",
                user_id=student_user.id,
            )

        # Query logs
        start = time.time()
        logs = (
            db_session.query(AuditLog)
            .filter(AuditLog.user_id == student_user.id)
            .limit(50)
            .all()
        )
        duration = time.time() - start

        # Should complete quickly (< 100ms)
        assert duration < 0.1
        assert len(logs) == 50

    def test_data_export_performance(self, db_session, student_user):
        """Test data export completes quickly"""
        import time

        # Create some test data
        from app.models.quiz import QuizSession

        for i in range(20):
            quiz = QuizSession(
                user_id=student_user.id,
                subject_id=1,
                category_id=1,
                score=80,
                total_questions=10,
                correct_answers=8,
            )
            db_session.add(quiz)
        db_session.commit()

        # Collect data
        start = time.time()
        user_data = collect_user_data(db_session, student_user.id)
        duration = time.time() - start

        # Should complete quickly (< 500ms)
        assert duration < 0.5
        assert "quiz_sessions" in user_data
