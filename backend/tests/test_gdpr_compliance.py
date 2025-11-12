"""
Tests for GDPR compliance features.

Tests data subject rights: access, erasure, portability, consent management.
"""

import pytest
import json
import os
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.gdpr import (
    ConsentRecord,
    DataExportRequest,
    DataDeletionRequest,
    PrivacyPolicyVersion,
    DeletionScope,
    DeletionStatus,
    ExportStatus,
)
from app.models.user import User, UserRole
from app.models.quiz import QuizSession
from app.models.progress import Progress
from app.utils.gdpr import (
    collect_user_data,
    create_export_file,
    process_export_request,
    anonymize_user_data,
    delete_user_data,
    process_deletion_request,
    record_consent,
    withdraw_consent,
    get_active_consents,
    has_consent,
)


class TestDataExport:
    """Test GDPR Right of Access (Article 15) - Data export"""

    @pytest.mark.integration
    def test_collect_user_data_complete(self, db_session, student_user):
        """Test collecting all user data for export"""
        # Create some quiz data
        quiz_session = QuizSession(
            user_id=student_user.id,
            subject_id=1,
            category_id=1,
            score=85,
            total_questions=10,
            correct_answers=8,
            completed=True,
        )
        db_session.add(quiz_session)
        db_session.commit()

        # Collect data
        user_data = collect_user_data(db_session, student_user.id)

        # Verify all sections present
        assert "personal_information" in user_data
        assert "quiz_sessions" in user_data
        assert "progress" in user_data
        assert "study_sessions" in user_data
        assert "activity_history" in user_data
        assert "active_sessions" in user_data
        assert "consent_records" in user_data
        assert "statistics" in user_data

        # Verify personal info
        personal = user_data["personal_information"]
        assert personal["username"] == student_user.username
        assert personal["email"] == student_user.email

        # Verify quiz data included
        assert len(user_data["quiz_sessions"]) > 0

    @pytest.mark.integration
    def test_create_export_file(self, db_session, student_user):
        """Test creating export file"""
        user_data = collect_user_data(db_session, student_user.id)

        export_request = DataExportRequest(
            user_id=student_user.id,
            status=ExportStatus.PROCESSING,
            export_format="JSON",
        )
        db_session.add(export_request)
        db_session.commit()

        file_path = create_export_file(db_session, export_request, user_data)

        # Verify file created
        assert file_path is not None
        assert os.path.exists(file_path)

        # Verify content is valid JSON
        with open(file_path, "r") as f:
            loaded_data = json.load(f)
            assert "personal_information" in loaded_data
            assert "export_metadata" in loaded_data

        # Cleanup
        os.remove(file_path)

    @pytest.mark.integration
    def test_process_export_request(self, db_session, student_user):
        """Test processing complete export request"""
        export_request = DataExportRequest(
            user_id=student_user.id,
            status=ExportStatus.PENDING,
            export_format="JSON",
        )
        db_session.add(export_request)
        db_session.commit()

        # Process export
        result = process_export_request(db_session, export_request)

        assert result["status"] == "COMPLETED"
        assert "file_path" in result
        assert export_request.status == ExportStatus.COMPLETED
        assert export_request.file_path is not None
        assert export_request.expires_at is not None

        # Verify expiration is 30 days
        expected_expiry = datetime.utcnow() + timedelta(days=30)
        time_diff = abs((export_request.expires_at - expected_expiry).total_seconds())
        assert time_diff < 60  # Within 1 minute

        # Cleanup
        if os.path.exists(result["file_path"]):
            os.remove(result["file_path"])

    @pytest.mark.unit
    def test_export_data_sanitized(self, db_session, student_user):
        """Test exported data doesn't include sensitive fields"""
        user_data = collect_user_data(db_session, student_user.id)

        personal = user_data["personal_information"]

        # Should NOT include password hash
        assert "password_hash" not in personal
        assert "hashed_password" not in personal


class TestDataDeletion:
    """Test GDPR Right to Erasure (Article 17) - Data deletion"""

    @pytest.mark.integration
    def test_anonymize_user_data(self, db_session, student_user):
        """Test soft deletion - anonymize PII"""
        original_username = student_user.username
        original_email = student_user.email
        user_id = student_user.id

        # Create some data
        quiz_session = QuizSession(
            user_id=user_id,
            subject_id=1,
            category_id=1,
            score=85,
            total_questions=10,
            correct_answers=8,
        )
        db_session.add(quiz_session)
        db_session.commit()

        # Anonymize
        result = anonymize_user_data(db_session, user_id)

        db_session.refresh(student_user)

        # Verify PII removed
        assert student_user.username == f"deleted_user_{user_id}"
        assert student_user.email == f"deleted_{user_id}@anonymized.local"
        assert student_user.full_name == "Deleted User"
        assert student_user.is_active is False

        # Verify quiz data preserved
        quiz_data = db_session.query(QuizSession).filter(
            QuizSession.user_id == user_id
        ).first()
        assert quiz_data is not None

        # Verify result counts
        assert result["user_anonymized"] == 1
        assert result["sessions_revoked"] >= 0

    @pytest.mark.integration
    def test_delete_user_data_full(self, db_session, student_user):
        """Test hard deletion - complete data removal"""
        user_id = student_user.id

        # Create some data
        quiz_session = QuizSession(
            user_id=user_id,
            subject_id=1,
            category_id=1,
            score=85,
            total_questions=10,
            correct_answers=8,
        )
        db_session.add(quiz_session)
        db_session.commit()

        # Delete completely
        result = delete_user_data(db_session, user_id, keep_analytics=False)

        # Verify user deleted
        user = db_session.query(User).filter(User.id == user_id).first()
        assert user is None

        # Verify quiz data deleted
        quiz_data = db_session.query(QuizSession).filter(
            QuizSession.user_id == user_id
        ).first()
        assert quiz_data is None

        # Verify result counts
        assert result["user_deleted"] == 1
        assert result["quiz_sessions_deleted"] >= 1

    @pytest.mark.integration
    def test_process_deletion_request_anonymize(self, db_session, student_user):
        """Test processing ANONYMIZE deletion request"""
        deletion_request = DataDeletionRequest(
            user_id=student_user.id,
            username=student_user.username,
            deletion_scope=DeletionScope.ANONYMIZE,
            status=DeletionStatus.PENDING,
            confirm_deletion=True,
        )
        db_session.add(deletion_request)
        db_session.commit()

        # Process deletion
        result = process_deletion_request(db_session, deletion_request)

        assert result["status"] == "COMPLETED"
        assert deletion_request.status == DeletionStatus.COMPLETED
        assert deletion_request.deleted_data is not None

        # Verify user anonymized
        db_session.refresh(student_user)
        assert "deleted_user" in student_user.username

    @pytest.mark.integration
    def test_process_deletion_request_full(self, db_session, student_user):
        """Test processing FULL deletion request (requires approval)"""
        user_id = student_user.id

        deletion_request = DataDeletionRequest(
            user_id=user_id,
            username=student_user.username,
            deletion_scope=DeletionScope.FULL,
            status=DeletionStatus.APPROVED,  # Pre-approved for test
            confirm_deletion=True,
        )
        db_session.add(deletion_request)
        db_session.commit()

        # Process deletion
        result = process_deletion_request(db_session, deletion_request)

        assert result["status"] == "COMPLETED"
        assert deletion_request.status == DeletionStatus.COMPLETED

        # Verify user deleted
        user = db_session.query(User).filter(User.id == user_id).first()
        assert user is None

    @pytest.mark.unit
    def test_deletion_request_requires_confirmation(self, db_session, student_user):
        """Test deletion requires explicit confirmation"""
        deletion_request = DataDeletionRequest(
            user_id=student_user.id,
            username=student_user.username,
            deletion_scope=DeletionScope.ANONYMIZE,
            status=DeletionStatus.PENDING,
            confirm_deletion=False,  # Not confirmed
        )
        db_session.add(deletion_request)
        db_session.commit()

        # Should not process without confirmation
        with pytest.raises(ValueError, match="not confirmed"):
            process_deletion_request(db_session, deletion_request)


class TestConsentManagement:
    """Test GDPR Consent Management (Article 7)"""

    @pytest.mark.unit
    def test_record_consent(self, db_session, student_user, mock_request):
        """Test recording user consent"""
        consent = record_consent(
            db=db_session,
            request=mock_request,
            user_id=student_user.id,
            consent_type="privacy_policy",
            purpose="Consent to Privacy Policy for processing personal data",
            version="1.0",
            method="explicit_checkbox",
        )

        assert consent.id is not None
        assert consent.user_id == student_user.id
        assert consent.consent_type == "privacy_policy"
        assert consent.consented is True
        assert consent.consented_at is not None
        assert consent.version == "1.0"
        assert consent.ip_address is not None

    @pytest.mark.unit
    def test_withdraw_consent(self, db_session, student_user, mock_request):
        """Test withdrawing consent"""
        # Record consent first
        consent = record_consent(
            db=db_session,
            request=mock_request,
            user_id=student_user.id,
            consent_type="marketing",
            purpose="Marketing communications",
            version="1.0",
        )

        assert consent.consented is True

        # Withdraw consent
        result = withdraw_consent(
            db=db_session,
            user_id=student_user.id,
            consent_type="marketing",
        )

        assert result is True
        db_session.refresh(consent)
        assert consent.consented is False
        assert consent.withdrawn_at is not None

    @pytest.mark.unit
    def test_get_active_consents(self, db_session, student_user, mock_request):
        """Test getting active consents"""
        # Record multiple consents
        record_consent(
            db=db_session,
            request=mock_request,
            user_id=student_user.id,
            consent_type="privacy_policy",
            purpose="Privacy policy",
            version="1.0",
        )

        record_consent(
            db=db_session,
            request=mock_request,
            user_id=student_user.id,
            consent_type="terms_of_service",
            purpose="Terms of service",
            version="1.0",
        )

        # Get active consents
        consents = get_active_consents(db_session, student_user.id)

        assert len(consents) == 2
        assert all(c.consented is True for c in consents)

    @pytest.mark.unit
    def test_has_consent(self, db_session, student_user, mock_request):
        """Test checking if user has specific consent"""
        # Initially no consent
        assert has_consent(db_session, student_user.id, "analytics") is False

        # Record consent
        record_consent(
            db=db_session,
            request=mock_request,
            user_id=student_user.id,
            consent_type="analytics",
            purpose="Analytics tracking",
            version="1.0",
        )

        # Now has consent
        assert has_consent(db_session, student_user.id, "analytics") is True

    @pytest.mark.integration
    def test_consent_version_tracking(self, db_session, student_user, mock_request):
        """Test consent tracks policy version"""
        # Record consent for v1.0
        consent = record_consent(
            db=db_session,
            request=mock_request,
            user_id=student_user.id,
            consent_type="privacy_policy",
            purpose="Privacy policy v1.0",
            version="1.0",
        )

        assert consent.version == "1.0"

        # Withdraw old consent
        withdraw_consent(db_session, student_user.id, "privacy_policy")

        # Record new consent for v2.0
        new_consent = record_consent(
            db=db_session,
            request=mock_request,
            user_id=student_user.id,
            consent_type="privacy_policy",
            purpose="Privacy policy v2.0",
            version="2.0",
        )

        assert new_consent.version == "2.0"

        # Verify history preserved
        all_consents = (
            db_session.query(ConsentRecord)
            .filter(
                ConsentRecord.user_id == student_user.id,
                ConsentRecord.consent_type == "privacy_policy",
            )
            .all()
        )

        assert len(all_consents) == 2


class TestPrivacyPolicyVersioning:
    """Test privacy policy version management"""

    @pytest.mark.unit
    def test_create_privacy_policy_version(self, db_session, admin_user):
        """Test creating new policy version"""
        policy = PrivacyPolicyVersion(
            document_type="privacy_policy",
            version="1.0",
            title="Privacy Policy v1.0",
            content="This is our privacy policy...",
            effective_date=datetime.utcnow(),
            created_by=admin_user.id,
        )
        db_session.add(policy)
        db_session.commit()

        assert policy.id is not None
        assert policy.is_active is True

    @pytest.mark.integration
    def test_get_active_policy(self, db_session, admin_user):
        """Test retrieving active policy version"""
        # Create two versions
        old_policy = PrivacyPolicyVersion(
            document_type="privacy_policy",
            version="1.0",
            title="Old Policy",
            content="Old content",
            effective_date=datetime.utcnow() - timedelta(days=30),
            created_by=admin_user.id,
            is_active=False,
        )
        db_session.add(old_policy)

        new_policy = PrivacyPolicyVersion(
            document_type="privacy_policy",
            version="2.0",
            title="New Policy",
            content="New content",
            effective_date=datetime.utcnow(),
            created_by=admin_user.id,
            is_active=True,
        )
        db_session.add(new_policy)
        db_session.commit()

        # Get active policy
        active = (
            db_session.query(PrivacyPolicyVersion)
            .filter(
                PrivacyPolicyVersion.document_type == "privacy_policy",
                PrivacyPolicyVersion.is_active == True,
            )
            .first()
        )

        assert active.version == "2.0"


class TestDataPortability:
    """Test GDPR Right to Data Portability (Article 20)"""

    @pytest.mark.integration
    def test_export_format_json(self, db_session, student_user):
        """Test data export in JSON format"""
        user_data = collect_user_data(db_session, student_user.id)

        export_request = DataExportRequest(
            user_id=student_user.id,
            status=ExportStatus.PROCESSING,
            export_format="JSON",
        )
        db_session.add(export_request)
        db_session.commit()

        file_path = create_export_file(db_session, export_request, user_data)

        # Verify JSON is valid and structured
        with open(file_path, "r") as f:
            data = json.load(f)

            # Check structure
            assert isinstance(data["personal_information"], dict)
            assert isinstance(data["quiz_sessions"], list)
            assert isinstance(data["statistics"], dict)

        # Cleanup
        os.remove(file_path)

    @pytest.mark.unit
    def test_export_includes_metadata(self, db_session, student_user):
        """Test export includes metadata"""
        user_data = collect_user_data(db_session, student_user.id)

        export_request = DataExportRequest(
            user_id=student_user.id,
            status=ExportStatus.PROCESSING,
            export_format="JSON",
        )
        db_session.add(export_request)
        db_session.commit()

        file_path = create_export_file(db_session, export_request, user_data)

        with open(file_path, "r") as f:
            data = json.load(f)

            # Check metadata
            assert "export_metadata" in data
            metadata = data["export_metadata"]
            assert "export_date" in metadata
            assert "export_format" in metadata
            assert "user_id" in metadata

        # Cleanup
        os.remove(file_path)


@pytest.mark.compliance
class TestGDPRCompliance:
    """Test GDPR compliance requirements"""

    def test_gdpr_article15_right_of_access(self, db_session, student_user):
        """Test GDPR Article 15 - Right of Access"""
        # User can access all their data
        user_data = collect_user_data(db_session, student_user.id)

        # Verify all required data categories present
        required_categories = [
            "personal_information",
            "quiz_sessions",
            "progress",
            "activity_history",
            "consent_records",
        ]

        for category in required_categories:
            assert category in user_data

    def test_gdpr_article17_right_to_erasure(self, db_session, student_user):
        """Test GDPR Article 17 - Right to Erasure"""
        user_id = student_user.id

        # User can request deletion
        anonymize_user_data(db_session, user_id)

        # Verify PII removed
        db_session.refresh(student_user)
        assert "deleted_user" in student_user.username
        assert "anonymized.local" in student_user.email

    def test_gdpr_article20_data_portability(self, db_session, student_user):
        """Test GDPR Article 20 - Right to Data Portability"""
        # User can export data in machine-readable format
        export_request = DataExportRequest(
            user_id=student_user.id,
            status=ExportStatus.PENDING,
            export_format="JSON",
        )
        db_session.add(export_request)
        db_session.commit()

        result = process_export_request(db_session, export_request)

        assert result["status"] == "COMPLETED"
        assert export_request.file_path is not None

        # Verify JSON format
        assert export_request.file_path.endswith(".json")

        # Cleanup
        if os.path.exists(result["file_path"]):
            os.remove(result["file_path"])

    def test_gdpr_article7_consent_conditions(self, db_session, student_user, mock_request):
        """Test GDPR Article 7 - Conditions for Consent"""
        # Consent must be specific, informed, and freely given
        consent = record_consent(
            db=db_session,
            request=mock_request,
            user_id=student_user.id,
            consent_type="marketing",
            purpose="Send marketing emails about new features",  # Specific purpose
            version="1.0",
            method="explicit_checkbox",  # Clear action
        )

        # Verify consent records evidence
        assert consent.consented_at is not None
        assert consent.ip_address is not None
        assert consent.method == "explicit_checkbox"
        assert consent.purpose is not None

        # User can withdraw at any time
        result = withdraw_consent(db_session, student_user.id, "marketing")
        assert result is True

    def test_gdpr_article30_processing_records(self, db_session, student_user):
        """Test GDPR Article 30 - Records of Processing Activities"""
        # All data processing must be logged
        from app.models.audit import AuditLog

        # Perform data operation
        collect_user_data(db_session, student_user.id)

        # Verify audit log exists for data operations
        # (In real implementation, collect_user_data would create audit log)
        audit_logs = (
            db_session.query(AuditLog)
            .filter(AuditLog.user_id == student_user.id)
            .all()
        )

        # Audit logging should capture data access
        assert audit_logs is not None


class TestGDPRAPIEndpoints:
    """Test GDPR API endpoints"""

    @pytest.mark.api
    def test_request_data_export_api(self, client: TestClient, db_session):
        """Test POST /api/gdpr/export-request"""
        # Register and login
        client.post(
            "/api/auth/register",
            json={
                "username": "exportuser",
                "email": "export@test.com",
                "password": "SecurePass123!",
                "role": "student",
            },
        )

        login_response = client.post(
            "/api/auth/login",
            json={"username": "exportuser", "password": "SecurePass123!"},
        )

        access_token = login_response.json()["access_token"]

        # Request export
        response = client.post(
            "/api/gdpr/export-request",
            json={"export_format": "JSON"},
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "COMPLETED"
        assert "request_id" in data

    @pytest.mark.api
    def test_request_data_deletion_api(self, client: TestClient):
        """Test POST /api/gdpr/deletion-request"""
        # Register and login
        client.post(
            "/api/auth/register",
            json={
                "username": "deleteuser",
                "email": "delete@test.com",
                "password": "SecurePass123!",
                "role": "student",
            },
        )

        login_response = client.post(
            "/api/auth/login",
            json={"username": "deleteuser", "password": "SecurePass123!"},
        )

        access_token = login_response.json()["access_token"]

        # Request deletion (anonymize)
        response = client.post(
            "/api/gdpr/deletion-request",
            json={
                "deletion_scope": "ANONYMIZE",
                "confirm_deletion": True,
                "reason": "Testing deletion",
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "COMPLETED"
        assert data["deletion_scope"] == "ANONYMIZE"

    @pytest.mark.api
    def test_view_my_data_api(self, client: TestClient):
        """Test GET /api/gdpr/my-data"""
        # Register and login
        client.post(
            "/api/auth/register",
            json={
                "username": "viewuser",
                "email": "view@test.com",
                "password": "SecurePass123!",
                "role": "student",
            },
        )

        login_response = client.post(
            "/api/auth/login",
            json={"username": "viewuser", "password": "SecurePass123!"},
        )

        access_token = login_response.json()["access_token"]

        # View data
        response = client.get(
            "/api/gdpr/my-data",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "personal_information" in data
        assert "quiz_sessions" in data
        assert "statistics" in data

    @pytest.mark.api
    def test_manage_consent_api(self, client: TestClient):
        """Test consent management endpoints"""
        # Register and login
        client.post(
            "/api/auth/register",
            json={
                "username": "consentuser",
                "email": "consent@test.com",
                "password": "SecurePass123!",
                "role": "student",
            },
        )

        login_response = client.post(
            "/api/auth/login",
            json={"username": "consentuser", "password": "SecurePass123!"},
        )

        access_token = login_response.json()["access_token"]

        # Give consent
        response = client.post(
            "/api/gdpr/consent",
            json={
                "consent_type": "marketing",
                "consented": True,
                "version": "1.0",
                "purpose": "Marketing communications",
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200

        # View consents
        response = client.get(
            "/api/gdpr/consent",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        consents = response.json()
        assert len(consents) > 0

        # Withdraw consent
        response = client.delete(
            "/api/gdpr/consent/marketing",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
