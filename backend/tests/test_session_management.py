"""
Tests for session management and timeout controls.

Tests session lifecycle, timeout enforcement, concurrent session limiting, and token revocation.
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch

from app.models.session import UserSession, RevokedToken
from app.models.user import User, UserRole
from app.utils.session import (
    create_session,
    get_active_sessions,
    get_session_by_jti,
    validate_session,
    update_session_activity,
    revoke_session,
    revoke_all_user_sessions,
    cleanup_expired_sessions,
    is_token_revoked,
)
from app.utils.auth import create_access_token, create_refresh_token


class TestSessionCreation:
    """Test session creation and tracking"""

    @pytest.mark.unit
    def test_create_session_basic(self, db_session, student_user):
        """Test basic session creation"""
        refresh_jti = "test-jti-123"

        session = create_session(
            db=db_session,
            user=student_user,
            refresh_token_jti=refresh_jti,
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0 Test Browser",
        )

        assert session.id is not None
        assert session.user_id == student_user.id
        assert session.refresh_token_jti == refresh_jti
        assert session.ip_address == "192.168.1.1"
        assert session.is_active is True
        assert session.created_at is not None
        assert session.last_activity_at is not None
        assert session.expires_at is not None

    @pytest.mark.unit
    def test_session_expiration_time(self, db_session, student_user):
        """Test session has correct expiration time (8 hours)"""
        session = create_session(
            db=db_session,
            user=student_user,
            refresh_token_jti="test-jti",
            ip_address="192.168.1.1",
        )

        expected_expiry = session.created_at + timedelta(hours=8)
        time_diff = abs((session.expires_at - expected_expiry).total_seconds())

        # Allow 1 second difference for processing time
        assert time_diff < 1

    @pytest.mark.integration
    def test_concurrent_session_limit(self, db_session, student_user):
        """Test max 3 concurrent sessions - oldest revoked when exceeded"""
        # Create 3 sessions
        sessions = []
        for i in range(3):
            session = create_session(
                db=db_session,
                user=student_user,
                refresh_token_jti=f"jti-{i}",
                ip_address=f"192.168.1.{i}",
            )
            sessions.append(session)
            db_session.commit()

        # All 3 should be active
        active = get_active_sessions(db_session, student_user.id)
        assert len(active) == 3

        # Create 4th session - should revoke oldest
        new_session = create_session(
            db=db_session,
            user=student_user,
            refresh_token_jti="jti-4",
            ip_address="192.168.1.4",
        )

        # Should now have 3 active sessions (oldest revoked)
        active = get_active_sessions(db_session, student_user.id)
        assert len(active) == 3
        assert new_session.id in [s.id for s in active]
        assert sessions[0].id not in [s.id for s in active]


class TestSessionValidation:
    """Test session validation and timeout enforcement"""

    @pytest.mark.unit
    def test_validate_active_session(self, db_session, student_user):
        """Test validating an active session"""
        session = create_session(
            db=db_session,
            user=student_user,
            refresh_token_jti="test-jti",
            ip_address="192.168.1.1",
        )

        is_valid, error_message = validate_session(db_session, session)

        assert is_valid is True
        assert error_message is None

    @pytest.mark.unit
    def test_validate_revoked_session(self, db_session, student_user):
        """Test validating a revoked session"""
        session = create_session(
            db=db_session,
            user=student_user,
            refresh_token_jti="test-jti",
            ip_address="192.168.1.1",
        )

        # Revoke session
        session.is_active = False
        db_session.commit()

        is_valid, error_message = validate_session(db_session, session)

        assert is_valid is False
        assert "revoked" in error_message.lower()

    @pytest.mark.unit
    def test_validate_idle_timeout(self, db_session, student_user):
        """Test idle timeout (15 minutes)"""
        session = create_session(
            db=db_session,
            user=student_user,
            refresh_token_jti="test-jti",
            ip_address="192.168.1.1",
        )

        # Simulate 16 minutes of inactivity
        session.last_activity_at = datetime.utcnow() - timedelta(minutes=16)
        db_session.commit()

        is_valid, error_message = validate_session(db_session, session)

        assert is_valid is False
        assert "idle" in error_message.lower()

    @pytest.mark.unit
    def test_validate_absolute_timeout(self, db_session, student_user):
        """Test absolute timeout (8 hours)"""
        session = create_session(
            db=db_session,
            user=student_user,
            refresh_token_jti="test-jti",
            ip_address="192.168.1.1",
        )

        # Simulate 9 hours since creation
        session.created_at = datetime.utcnow() - timedelta(hours=9)
        session.expires_at = datetime.utcnow() - timedelta(hours=1)
        db_session.commit()

        is_valid, error_message = validate_session(db_session, session)

        assert is_valid is False
        assert "expired" in error_message.lower()

    @pytest.mark.unit
    def test_validate_within_idle_timeout(self, db_session, student_user):
        """Test session valid within idle timeout"""
        session = create_session(
            db=db_session,
            user=student_user,
            refresh_token_jti="test-jti",
            ip_address="192.168.1.1",
        )

        # Simulate 10 minutes of inactivity (still valid)
        session.last_activity_at = datetime.utcnow() - timedelta(minutes=10)
        db_session.commit()

        is_valid, error_message = validate_session(db_session, session)

        assert is_valid is True


class TestSessionActivity:
    """Test session activity tracking"""

    @pytest.mark.unit
    def test_update_session_activity(self, db_session, student_user):
        """Test updating session activity timestamp"""
        session = create_session(
            db=db_session,
            user=student_user,
            refresh_token_jti="test-jti",
            ip_address="192.168.1.1",
        )

        original_activity = session.last_activity_at

        # Simulate time passing
        import time
        time.sleep(0.1)

        update_session_activity(db_session, session)

        assert session.last_activity_at > original_activity

    @pytest.mark.integration
    def test_activity_prevents_idle_timeout(self, db_session, student_user):
        """Test that activity updates prevent idle timeout"""
        session = create_session(
            db=db_session,
            user=student_user,
            refresh_token_jti="test-jti",
            ip_address="192.168.1.1",
        )

        # Simulate 14 minutes of inactivity
        session.last_activity_at = datetime.utcnow() - timedelta(minutes=14)
        db_session.commit()

        # Update activity before 15-minute idle timeout
        update_session_activity(db_session, session)

        # Should still be valid
        is_valid, _ = validate_session(db_session, session)
        assert is_valid is True


class TestSessionRevocation:
    """Test session and token revocation"""

    @pytest.mark.unit
    def test_revoke_session(self, db_session, student_user):
        """Test revoking a specific session"""
        session = create_session(
            db=db_session,
            user=student_user,
            refresh_token_jti="test-jti",
            ip_address="192.168.1.1",
        )

        assert session.is_active is True

        revoke_session(db_session, session)

        assert session.is_active is False
        assert session.revoked_at is not None

    @pytest.mark.integration
    def test_revoke_all_user_sessions(self, db_session, student_user):
        """Test revoking all sessions for a user"""
        # Create 3 sessions
        sessions = []
        for i in range(3):
            session = create_session(
                db=db_session,
                user=student_user,
                refresh_token_jti=f"jti-{i}",
                ip_address=f"192.168.1.{i}",
            )
            sessions.append(session)

        # All should be active
        active = get_active_sessions(db_session, student_user.id)
        assert len(active) == 3

        # Revoke all
        count = revoke_all_user_sessions(db_session, student_user.id)

        assert count == 3

        # No active sessions
        active = get_active_sessions(db_session, student_user.id)
        assert len(active) == 0

    @pytest.mark.unit
    def test_token_revocation_tracking(self, db_session):
        """Test revoking tokens creates revoked_tokens entry"""
        jti = "test-jti-123"
        expires_at = datetime.utcnow() + timedelta(hours=1)

        revoked_token = RevokedToken(
            jti=jti,
            token_type="access",
            expires_at=expires_at,
            revoked_at=datetime.utcnow(),
        )
        db_session.add(revoked_token)
        db_session.commit()

        # Check token is marked as revoked
        assert is_token_revoked(db_session, jti) is True

    @pytest.mark.unit
    def test_non_revoked_token(self, db_session):
        """Test checking a non-revoked token"""
        jti = "valid-token-jti"

        assert is_token_revoked(db_session, jti) is False


class TestSessionQueries:
    """Test session querying and filtering"""

    @pytest.mark.integration
    def test_get_active_sessions(self, db_session, student_user):
        """Test getting all active sessions for a user"""
        # Create 2 active sessions
        for i in range(2):
            create_session(
                db=db_session,
                user=student_user,
                refresh_token_jti=f"jti-{i}",
                ip_address=f"192.168.1.{i}",
            )

        # Create 1 revoked session
        revoked_session = create_session(
            db=db_session,
            user=student_user,
            refresh_token_jti="jti-revoked",
            ip_address="192.168.1.99",
        )
        revoke_session(db_session, revoked_session)

        # Should only get 2 active sessions
        active = get_active_sessions(db_session, student_user.id)
        assert len(active) == 2

    @pytest.mark.integration
    def test_get_session_by_jti(self, db_session, student_user):
        """Test retrieving session by refresh token JTI"""
        jti = "test-unique-jti"
        session = create_session(
            db=db_session,
            user=student_user,
            refresh_token_jti=jti,
            ip_address="192.168.1.1",
        )

        found_session = get_session_by_jti(db_session, jti)

        assert found_session is not None
        assert found_session.id == session.id
        assert found_session.refresh_token_jti == jti

    @pytest.mark.unit
    def test_get_session_by_jti_not_found(self, db_session):
        """Test retrieving non-existent session"""
        found_session = get_session_by_jti(db_session, "non-existent-jti")

        assert found_session is None


class TestSessionCleanup:
    """Test expired session cleanup"""

    @pytest.mark.integration
    def test_cleanup_expired_sessions(self, db_session, student_user):
        """Test cleanup removes expired sessions"""
        # Create expired session (9 hours old)
        expired_session = create_session(
            db=db_session,
            user=student_user,
            refresh_token_jti="expired-jti",
            ip_address="192.168.1.1",
        )
        expired_session.created_at = datetime.utcnow() - timedelta(hours=9)
        expired_session.expires_at = datetime.utcnow() - timedelta(hours=1)
        db_session.commit()

        # Create active session
        active_session = create_session(
            db=db_session,
            user=student_user,
            refresh_token_jti="active-jti",
            ip_address="192.168.1.2",
        )

        # Run cleanup
        deleted_count = cleanup_expired_sessions(db_session)

        assert deleted_count == 1

        # Verify expired session removed
        found_expired = get_session_by_jti(db_session, "expired-jti")
        assert found_expired is None

        # Verify active session still exists
        found_active = get_session_by_jti(db_session, "active-jti")
        assert found_active is not None

    @pytest.mark.integration
    def test_cleanup_idle_sessions(self, db_session, student_user):
        """Test cleanup removes idle sessions (15+ min inactive)"""
        # Create idle session (20 minutes inactive)
        idle_session = create_session(
            db=db_session,
            user=student_user,
            refresh_token_jti="idle-jti",
            ip_address="192.168.1.1",
        )
        idle_session.last_activity_at = datetime.utcnow() - timedelta(minutes=20)
        db_session.commit()

        # Create recently active session
        active_session = create_session(
            db=db_session,
            user=student_user,
            refresh_token_jti="active-jti",
            ip_address="192.168.1.2",
        )

        # Run cleanup
        deleted_count = cleanup_expired_sessions(db_session)

        assert deleted_count == 1


class TestSessionSecurity:
    """Test session security features"""

    @pytest.mark.integration
    def test_different_users_isolated_sessions(self, db_session, student_user, admin_user):
        """Test users can only see their own sessions"""
        # Create sessions for student
        create_session(
            db=db_session,
            user=student_user,
            refresh_token_jti="student-jti",
            ip_address="192.168.1.1",
        )

        # Create sessions for admin
        create_session(
            db=db_session,
            user=admin_user,
            refresh_token_jti="admin-jti",
            ip_address="192.168.1.2",
        )

        # Each user should only see their own sessions
        student_sessions = get_active_sessions(db_session, student_user.id)
        admin_sessions = get_active_sessions(db_session, admin_user.id)

        assert len(student_sessions) == 1
        assert len(admin_sessions) == 1
        assert student_sessions[0].user_id == student_user.id
        assert admin_sessions[0].user_id == admin_user.id

    @pytest.mark.unit
    def test_session_tracks_device_info(self, db_session, student_user):
        """Test session tracks IP and user agent"""
        ip = "203.0.113.42"
        user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0)"

        session = create_session(
            db=db_session,
            user=student_user,
            refresh_token_jti="test-jti",
            ip_address=ip,
            user_agent=user_agent,
        )

        assert session.ip_address == ip
        assert session.user_agent == user_agent


@pytest.mark.compliance
class TestComplianceRequirements:
    """Test session management compliance requirements"""

    def test_soc2_cc61_session_timeout(self, db_session, student_user):
        """Test SOC 2 CC6.1 - Automatic session timeout"""
        session = create_session(
            db=db_session,
            user=student_user,
            refresh_token_jti="test-jti",
            ip_address="192.168.1.1",
        )

        # Verify idle timeout configured
        session.last_activity_at = datetime.utcnow() - timedelta(minutes=16)
        db_session.commit()

        is_valid, error = validate_session(db_session, session)
        assert is_valid is False
        assert "idle" in error.lower()

    def test_iso27001_a823_session_controls(self, db_session, student_user):
        """Test ISO 27001 A.8.23 - Session management controls"""
        # Test concurrent session limiting
        sessions = []
        for i in range(4):
            session = create_session(
                db=db_session,
                user=student_user,
                refresh_token_jti=f"jti-{i}",
                ip_address=f"192.168.1.{i}",
            )
            sessions.append(session)
            db_session.commit()

        # Should enforce max 3 concurrent sessions
        active = get_active_sessions(db_session, student_user.id)
        assert len(active) <= 3

    def test_nist_prac6_session_termination(self, db_session, student_user):
        """Test NIST PR.AC-6 - Session termination capabilities"""
        session = create_session(
            db=db_session,
            user=student_user,
            refresh_token_jti="test-jti",
            ip_address="192.168.1.1",
        )

        # Test immediate termination capability
        revoke_session(db_session, session)

        # Verify session immediately invalid
        is_valid, _ = validate_session(db_session, session)
        assert is_valid is False
        assert session.revoked_at is not None


class TestSessionAPIIntegration:
    """Test session management API integration"""

    @pytest.mark.api
    def test_login_creates_session(self, client: TestClient, db_session):
        """Test login endpoint creates session"""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "sessiontest",
                "email": "session@test.com",
                "password": "SecurePass123!",
                "role": "student"
            }
        )
        assert response.status_code == 201

        # Login
        response = client.post(
            "/api/auth/login",
            json={
                "username": "sessiontest",
                "password": "SecurePass123!"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

        # Check session created
        user_id = data["user"]["id"]
        sessions = get_active_sessions(db_session, user_id)
        assert len(sessions) == 1

    @pytest.mark.api
    def test_logout_revokes_session(self, client: TestClient, db_session):
        """Test logout endpoint revokes session"""
        # Register and login
        client.post(
            "/api/auth/register",
            json={
                "username": "logouttest",
                "email": "logout@test.com",
                "password": "SecurePass123!",
                "role": "student"
            }
        )

        login_response = client.post(
            "/api/auth/login",
            json={
                "username": "logouttest",
                "password": "SecurePass123!"
            }
        )

        access_token = login_response.json()["access_token"]
        user_id = login_response.json()["user"]["id"]

        # Verify session exists
        sessions_before = get_active_sessions(db_session, user_id)
        assert len(sessions_before) == 1

        # Logout
        response = client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200

        # Verify session revoked
        sessions_after = get_active_sessions(db_session, user_id)
        assert len(sessions_after) == 0
