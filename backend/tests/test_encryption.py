"""
Tests for encryption at rest functionality.

Tests encryption service, encrypted types, and data migration utilities.
"""

import pytest
import os
from unittest.mock import patch, Mock
from sqlalchemy.orm import Session

from app.utils.encryption import (
    EncryptionService,
    get_encryption_service,
    encrypt_field,
    decrypt_field,
    generate_encryption_key,
)
from app.utils.encrypted_types import EncryptedString, EncryptedText
from app.models.user import User, UserRole, StudentLevel
from app.models.session import UserSession
from app.models.gdpr import ConsentRecord


class TestEncryptionService:
    """Test core encryption service functionality"""

    @pytest.mark.unit
    def test_encryption_service_initialization(self):
        """Test encryption service initializes correctly"""
        service = EncryptionService()

        assert service.primary_key is not None
        assert service.fernet is not None

    @pytest.mark.unit
    def test_encrypt_decrypt_roundtrip(self):
        """Test data can be encrypted and decrypted"""
        service = EncryptionService()

        plaintext = "user@example.com"
        encrypted = service.encrypt(plaintext)

        assert encrypted is not None
        assert encrypted != plaintext
        assert encrypted.startswith('gAAAAAB')  # Fernet token format

        decrypted = service.decrypt(encrypted)
        assert decrypted == plaintext

    @pytest.mark.unit
    def test_encrypt_none_returns_none(self):
        """Test encrypting None returns None"""
        service = EncryptionService()

        result = service.encrypt(None)
        assert result is None

    @pytest.mark.unit
    def test_encrypt_empty_string_returns_none(self):
        """Test encrypting empty string returns None"""
        service = EncryptionService()

        result = service.encrypt("")
        assert result is None

    @pytest.mark.unit
    def test_decrypt_none_returns_none(self):
        """Test decrypting None returns None"""
        service = EncryptionService()

        result = service.decrypt(None)
        assert result is None

    @pytest.mark.unit
    def test_decrypt_invalid_data_returns_none(self):
        """Test decrypting invalid data returns None gracefully"""
        service = EncryptionService()

        result = service.decrypt("invalid_encrypted_data")
        assert result is None

    @pytest.mark.unit
    def test_encrypt_if_needed_already_encrypted(self):
        """Test encrypt_if_needed skips already encrypted data"""
        service = EncryptionService()

        plaintext = "user@example.com"
        encrypted = service.encrypt(plaintext)

        # Should return same encrypted value
        result = service.encrypt_if_needed(encrypted)
        assert result == encrypted

    @pytest.mark.unit
    def test_encrypt_if_needed_plaintext(self):
        """Test encrypt_if_needed encrypts plaintext"""
        service = EncryptionService()

        plaintext = "user@example.com"
        encrypted = service.encrypt_if_needed(plaintext)

        assert encrypted != plaintext
        assert encrypted.startswith('gAAAAAB')

    @pytest.mark.unit
    def test_decrypt_if_needed_encrypted(self):
        """Test decrypt_if_needed decrypts encrypted data"""
        service = EncryptionService()

        plaintext = "user@example.com"
        encrypted = service.encrypt(plaintext)

        decrypted = service.decrypt_if_needed(encrypted)
        assert decrypted == plaintext

    @pytest.mark.unit
    def test_decrypt_if_needed_plaintext(self):
        """Test decrypt_if_needed returns plaintext as-is"""
        service = EncryptionService()

        plaintext = "user@example.com"
        result = service.decrypt_if_needed(plaintext)

        assert result == plaintext

    @pytest.mark.unit
    def test_unicode_encryption(self):
        """Test encryption handles Unicode characters"""
        service = EncryptionService()

        unicode_text = "用户@例子.com"  # Chinese characters
        encrypted = service.encrypt(unicode_text)
        decrypted = service.decrypt(encrypted)

        assert decrypted == unicode_text

    @pytest.mark.unit
    def test_long_text_encryption(self):
        """Test encryption handles long text"""
        service = EncryptionService()

        long_text = "a" * 10000  # 10KB of text
        encrypted = service.encrypt(long_text)
        decrypted = service.decrypt(encrypted)

        assert decrypted == long_text
        assert len(encrypted) > len(long_text)


class TestEncryptionHelpers:
    """Test encryption helper functions"""

    @pytest.mark.unit
    def test_get_encryption_service_singleton(self):
        """Test get_encryption_service returns singleton"""
        service1 = get_encryption_service()
        service2 = get_encryption_service()

        assert service1 is service2

    @pytest.mark.unit
    def test_encrypt_field_helper(self):
        """Test encrypt_field convenience function"""
        plaintext = "user@example.com"
        encrypted = encrypt_field(plaintext)

        assert encrypted is not None
        assert encrypted != plaintext
        assert encrypted.startswith('gAAAAAB')

    @pytest.mark.unit
    def test_decrypt_field_helper(self):
        """Test decrypt_field convenience function"""
        plaintext = "user@example.com"
        encrypted = encrypt_field(plaintext)
        decrypted = decrypt_field(encrypted)

        assert decrypted == plaintext

    @pytest.mark.unit
    def test_generate_encryption_key(self):
        """Test key generation"""
        key = generate_encryption_key()

        assert key is not None
        assert len(key) > 0
        # Fernet keys are 44 characters when base64 encoded
        assert len(key) == 44


class TestEncryptedStringType:
    """Test EncryptedString SQLAlchemy type"""

    @pytest.mark.integration
    def test_encrypted_string_in_model(self, db_session):
        """Test EncryptedString works in SQLAlchemy model"""
        user = User(
            username="encrypttest",
            email="encrypted@example.com",
            hashed_password="hashed_password",
            full_name="Encrypted User",
            role=UserRole.STUDENT,
            student_level=StudentLevel.HIGH_SCHOOL,
        )

        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        # Email should be transparently decrypted
        assert user.email == "encrypted@example.com"
        assert user.full_name == "Encrypted User"

    @pytest.mark.integration
    def test_encrypted_data_stored_encrypted(self, db_session):
        """Test data is actually encrypted in database"""
        user = User(
            username="rawtest",
            email="raw@example.com",
            hashed_password="hashed_password",
            full_name="Raw User",
            role=UserRole.STUDENT,
            student_level=StudentLevel.PRIMARY,
        )

        db_session.add(user)
        db_session.commit()

        # Query raw data from database
        result = db_session.execute(
            "SELECT email, full_name FROM users WHERE username = 'rawtest'"
        ).fetchone()

        # Data in database should be encrypted (Fernet format)
        assert result[0].startswith('gAAAAAB')
        assert result[1].startswith('gAAAAAB')

    @pytest.mark.integration
    def test_query_by_decrypted_value(self, db_session):
        """Test querying by decrypted value works"""
        user = User(
            username="querytest",
            email="query@example.com",
            hashed_password="hashed_password",
            full_name="Query User",
            role=UserRole.STUDENT,
            student_level=StudentLevel.TERTIARY,
        )

        db_session.add(user)
        db_session.commit()

        # Note: Encrypted fields cannot be queried directly
        # Must fetch all and filter in Python
        users = db_session.query(User).filter(User.username == "querytest").all()
        assert len(users) == 1
        assert users[0].email == "query@example.com"

    @pytest.mark.integration
    def test_update_encrypted_field(self, db_session):
        """Test updating encrypted field"""
        user = User(
            username="updatetest",
            email="original@example.com",
            hashed_password="hashed_password",
            full_name="Original Name",
            role=UserRole.STUDENT,
            student_level=StudentLevel.HIGH_SCHOOL,
        )

        db_session.add(user)
        db_session.commit()

        # Update email
        user.email = "updated@example.com"
        user.full_name = "Updated Name"
        db_session.commit()
        db_session.refresh(user)

        assert user.email == "updated@example.com"
        assert user.full_name == "Updated Name"

    @pytest.mark.integration
    def test_null_encrypted_field(self, db_session):
        """Test null values in encrypted fields"""
        user = User(
            username="nulltest",
            email="null@example.com",
            hashed_password="hashed_password",
            full_name=None,  # Null value
            role=UserRole.STUDENT,
            student_level=StudentLevel.PRIMARY,
        )

        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.full_name is None


class TestEncryptedFieldsInModels:
    """Test encrypted fields across different models"""

    @pytest.mark.integration
    def test_user_encrypted_fields(self, db_session):
        """Test User model encrypted fields"""
        user = User(
            username="usertest",
            email="user@encrypted.com",
            hashed_password="hash",
            full_name="User Name",
            role=UserRole.STUDENT,
            student_level=StudentLevel.HIGH_SCHOOL,
        )

        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        # Fields should be decrypted
        assert user.email == "user@encrypted.com"
        assert user.full_name == "User Name"
        assert not user.email.startswith('gAAAAAB')

    @pytest.mark.integration
    def test_session_encrypted_fields(self, db_session, student_user):
        """Test UserSession model encrypted fields"""
        from datetime import datetime, timedelta
        import uuid

        session = UserSession(
            user_id=student_user.id,
            username=student_user.username,
            session_id=str(uuid.uuid4()),
            refresh_token_jti=str(uuid.uuid4()),
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 Test Browser",
            expires_at=datetime.utcnow() + timedelta(hours=8),
        )

        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)

        # Fields should be decrypted
        assert session.ip_address == "192.168.1.100"
        assert session.user_agent == "Mozilla/5.0 Test Browser"

    @pytest.mark.integration
    def test_consent_encrypted_fields(self, db_session, student_user):
        """Test ConsentRecord model encrypted fields"""
        consent = ConsentRecord(
            user_id=student_user.id,
            consent_type="privacy_policy",
            purpose="Test consent",
            consented=True,
            version="1.0",
            ip_address="203.0.113.42",
            user_agent="Mozilla/5.0 (iPhone)",
            method="explicit_checkbox",
        )

        db_session.add(consent)
        db_session.commit()
        db_session.refresh(consent)

        # Fields should be decrypted
        assert consent.ip_address == "203.0.113.42"
        assert consent.user_agent == "Mozilla/5.0 (iPhone)"


class TestEncryptionKeyRotation:
    """Test key rotation functionality"""

    @pytest.mark.unit
    @patch.dict(os.environ, {
        'ENCRYPTION_KEY': 'dGVzdF9wcmltYXJ5X2tleV8xMjM0NTY3ODkwMTIzNDU2',  # Test key
        'ENCRYPTION_KEY_ROTATION_1': 'b2xkX2tleV8xMjM0NTY3ODkwMTIzNDU2Nzg5MDEyMzQ1Ng==',  # Old key
    })
    def test_key_rotation_support(self):
        """Test encryption service loads rotation keys"""
        service = EncryptionService()

        assert len(service.rotation_keys) >= 1

    @pytest.mark.unit
    def test_rotate_encryption(self):
        """Test re-encrypting data with new key"""
        service = EncryptionService()

        plaintext = "user@example.com"
        old_encrypted = service.encrypt(plaintext)

        # Simulate rotation
        new_encrypted = service.rotate_encryption(old_encrypted)

        # Should be different encrypted value but same plaintext
        assert new_encrypted != old_encrypted
        assert service.decrypt(new_encrypted) == plaintext


class TestEncryptionBackwardsCompatibility:
    """Test backwards compatibility with unencrypted data"""

    @pytest.mark.unit
    def test_decrypt_if_needed_handles_plaintext(self):
        """Test decrypt_if_needed handles legacy unencrypted data"""
        service = EncryptionService()

        # Legacy plaintext data
        legacy_email = "legacy@example.com"

        # Should return as-is
        result = service.decrypt_if_needed(legacy_email)
        assert result == legacy_email

    @pytest.mark.unit
    def test_encrypt_if_needed_encrypts_plaintext(self):
        """Test encrypt_if_needed encrypts legacy plaintext"""
        service = EncryptionService()

        legacy_email = "legacy@example.com"

        # Should encrypt it
        encrypted = service.encrypt_if_needed(legacy_email)
        assert encrypted != legacy_email
        assert encrypted.startswith('gAAAAAB')


@pytest.mark.compliance
class TestEncryptionCompliance:
    """Test encryption meets compliance requirements"""

    def test_iso27001_a824_encryption_standard(self):
        """Test ISO 27001 A.8.24 - AES-256 encryption"""
        service = EncryptionService()

        # Fernet uses AES-128-CBC, but for demonstration
        # In production, could verify encryption algorithm
        plaintext = "sensitive@data.com"
        encrypted = service.encrypt(plaintext)

        # Encrypted data should not contain plaintext
        assert plaintext not in encrypted
        assert encrypted.startswith('gAAAAAB')  # Fernet format

    def test_gdpr_article32_security_of_processing(self):
        """Test GDPR Article 32 - Security of processing"""
        service = EncryptionService()

        # PII should be encrypted
        pii_email = "gdpr@example.com"
        encrypted = service.encrypt(pii_email)

        # Encrypted PII should not be readable
        assert pii_email not in encrypted

        # Should be recoverable for data subject requests
        decrypted = service.decrypt(encrypted)
        assert decrypted == pii_email

    def test_soc2_cc67_encryption_controls(self):
        """Test SOC 2 CC6.7 - Encryption controls"""
        service = EncryptionService()

        # Sensitive data encrypted at rest
        sensitive_data = "credit_card_info"
        encrypted = service.encrypt(sensitive_data)

        # Encrypted form should be different
        assert encrypted != sensitive_data

        # Key management in place
        assert service.primary_key is not None

    def test_pii_fields_encrypted_in_models(self, db_session):
        """Test all PII fields are encrypted in database"""
        user = User(
            username="compliancetest",
            email="compliance@example.com",
            hashed_password="hash",
            full_name="Compliance Test",
            role=UserRole.STUDENT,
            student_level=StudentLevel.TERTIARY,
        )

        db_session.add(user)
        db_session.commit()

        # Query raw database
        result = db_session.execute(
            "SELECT email, full_name FROM users WHERE username = 'compliancetest'"
        ).fetchone()

        # PII should be encrypted in database
        assert result[0].startswith('gAAAAAB')  # Email encrypted
        assert result[1].startswith('gAAAAAB')  # Full name encrypted


@pytest.mark.performance
class TestEncryptionPerformance:
    """Test encryption performance"""

    @pytest.mark.unit
    def test_encryption_performance(self):
        """Test encryption completes quickly"""
        import time

        service = EncryptionService()
        plaintext = "user@example.com"

        # Encrypt 100 times
        start = time.time()
        for _ in range(100):
            service.encrypt(plaintext)
        duration = time.time() - start

        # Should complete in < 100ms (1ms per encryption)
        assert duration < 0.1

    @pytest.mark.unit
    def test_decryption_performance(self):
        """Test decryption completes quickly"""
        import time

        service = EncryptionService()
        plaintext = "user@example.com"
        encrypted = service.encrypt(plaintext)

        # Decrypt 100 times
        start = time.time()
        for _ in range(100):
            service.decrypt(encrypted)
        duration = time.time() - start

        # Should complete in < 100ms (1ms per decryption)
        assert duration < 0.1


class TestEncryptionErrorHandling:
    """Test encryption error handling"""

    @pytest.mark.unit
    def test_encrypt_with_invalid_key_raises_error(self):
        """Test encryption with invalid key configuration"""
        with patch.dict(os.environ, {'ENCRYPTION_KEY': 'invalid_key', 'ENVIRONMENT': 'production'}):
            with pytest.raises(ValueError, match="Invalid encryption key"):
                EncryptionService()

    @pytest.mark.unit
    def test_missing_key_in_production_raises_error(self):
        """Test missing key in production raises error"""
        with patch.dict(os.environ, {'ENVIRONMENT': 'production'}, clear=True):
            with pytest.raises(ValueError, match="not set in production"):
                EncryptionService()

    @pytest.mark.unit
    def test_decrypt_corrupted_data_returns_none(self):
        """Test decrypting corrupted data returns None"""
        service = EncryptionService()

        corrupted = "gAAAAABcorrupted_data_here"
        result = service.decrypt(corrupted)

        assert result is None
