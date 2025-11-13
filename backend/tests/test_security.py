"""
Unit tests for security utilities
"""
import pytest
from datetime import datetime, timedelta
from jose import jwt, JWTError

from app.utils.security import (
    verify_password,
    get_password_hash,
    validate_password_strength,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token_type,
)
from app.config import settings


class TestPasswordHashing:
    """Test password hashing functions"""

    @pytest.mark.unit
    def test_password_hashing(self):
        """Test that password hashing works correctly"""
        password = "TestPassword123!"
        hashed = get_password_hash(password)

        # Hash should be different from password
        assert hashed != password

        # Hash should be bcrypt format
        assert hashed.startswith("$2b$")

        # Verification should work
        assert verify_password(password, hashed) is True

        # Wrong password should fail
        assert verify_password("WrongPassword", hashed) is False

    @pytest.mark.unit
    def test_different_hashes_for_same_password(self):
        """Test that same password generates different hashes (salt)"""
        password = "TestPassword123!"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        # Hashes should be different due to salt
        assert hash1 != hash2

        # But both should verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestPasswordValidation:
    """Test password strength validation"""

    @pytest.mark.unit
    def test_valid_password(self):
        """Test that valid passwords pass validation"""
        is_valid, msg = validate_password_strength("ValidPass123!")
        assert is_valid is True
        assert msg == ""

    @pytest.mark.unit
    def test_password_too_short(self):
        """Test that short passwords fail validation"""
        is_valid, msg = validate_password_strength("Short1")
        assert is_valid is False
        assert "at least" in msg.lower()

    @pytest.mark.unit
    def test_password_no_uppercase(self):
        """Test that passwords without uppercase fail"""
        is_valid, msg = validate_password_strength("lowercase123!")
        assert is_valid is False
        assert "uppercase" in msg.lower()

    @pytest.mark.unit
    def test_password_no_lowercase(self):
        """Test that passwords without lowercase fail"""
        is_valid, msg = validate_password_strength("UPPERCASE123!")
        assert is_valid is False
        assert "lowercase" in msg.lower()

    @pytest.mark.unit
    def test_password_no_digit(self):
        """Test that passwords without digits fail"""
        is_valid, msg = validate_password_strength("NoDigitsHere!")
        assert is_valid is False
        assert "digit" in msg.lower()

    @pytest.mark.unit
    def test_minimum_length_password(self):
        """Test password at minimum length"""
        is_valid, msg = validate_password_strength("Valid12!")
        assert is_valid is True


class TestJWTTokens:
    """Test JWT token creation and validation"""

    @pytest.mark.unit
    def test_create_access_token(self):
        """Test access token creation"""
        user_data = {"sub": 1, "role": "student"}
        token = create_access_token(data=user_data)

        # Token should be a string
        assert isinstance(token, str)

        # Should be able to decode it
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        # Should contain our data
        assert payload["sub"] == 1
        assert payload["role"] == "student"
        assert payload["type"] == "access"

        # Should have expiration
        assert "exp" in payload
        assert "iat" in payload

    @pytest.mark.unit
    def test_create_refresh_token(self):
        """Test refresh token creation"""
        user_data = {"sub": 1}
        token = create_refresh_token(data=user_data)

        # Token should be a string
        assert isinstance(token, str)

        # Should be able to decode it
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        # Should contain our data
        assert payload["sub"] == 1
        assert payload["type"] == "refresh"

        # Should have expiration
        assert "exp" in payload

    @pytest.mark.unit
    def test_token_expiration(self):
        """Test that tokens expire"""
        user_data = {"sub": 1}

        # Create token that expires immediately
        expires_delta = timedelta(seconds=-1)
        token = create_access_token(data=user_data, expires_delta=expires_delta)

        # Should raise JWTError when decoding expired token
        with pytest.raises(Exception):
            decode_token(token)

    @pytest.mark.unit
    def test_decode_valid_token(self):
        """Test decoding a valid token"""
        user_data = {"sub": 1, "role": "admin"}
        token = create_access_token(data=user_data)

        # Should decode successfully
        payload = decode_token(token)

        assert payload["sub"] == 1
        assert payload["role"] == "admin"
        assert payload["type"] == "access"

    @pytest.mark.unit
    def test_decode_invalid_token(self):
        """Test decoding an invalid token"""
        invalid_token = "invalid.token.here"

        # Should raise HTTPException
        with pytest.raises(Exception):
            decode_token(invalid_token)

    @pytest.mark.unit
    def test_verify_token_type(self):
        """Test token type verification"""
        user_data = {"sub": 1}
        access_token = create_access_token(data=user_data)
        refresh_token = create_refresh_token(data=user_data)

        # Decode tokens
        access_payload = decode_token(access_token)
        refresh_payload = decode_token(refresh_token)

        # Verify correct types pass
        verify_token_type(access_payload, "access")  # Should not raise
        verify_token_type(refresh_payload, "refresh")  # Should not raise

        # Verify wrong types fail
        with pytest.raises(Exception):
            verify_token_type(access_payload, "refresh")

        with pytest.raises(Exception):
            verify_token_type(refresh_payload, "access")

    @pytest.mark.unit
    def test_token_contains_timestamps(self):
        """Test that tokens contain issued-at and expiration timestamps"""
        user_data = {"sub": 1}
        token = create_access_token(data=user_data)
        payload = decode_token(token)

        assert "iat" in payload  # issued at
        assert "exp" in payload  # expiration

        # Expiration should be in the future
        assert payload["exp"] > payload["iat"]

    @pytest.mark.unit
    def test_custom_expiration(self):
        """Test creating token with custom expiration"""
        user_data = {"sub": 1}
        custom_expiry = timedelta(hours=2)

        token = create_access_token(data=user_data, expires_delta=custom_expiry)
        payload = decode_token(token)

        # Calculate expected expiration (roughly)
        expected_exp = datetime.utcnow() + custom_expiry
        actual_exp = datetime.fromtimestamp(payload["exp"])

        # Should be close (within 10 seconds)
        time_diff = abs((actual_exp - expected_exp).total_seconds())
        assert time_diff < 10


class TestSecurityEdgeCases:
    """Test edge cases and security scenarios"""

    @pytest.mark.unit
    @pytest.mark.security
    def test_empty_password(self):
        """Test that empty passwords fail validation"""
        is_valid, msg = validate_password_strength("")
        assert is_valid is False

    @pytest.mark.unit
    @pytest.mark.security
    def test_null_password(self):
        """Test handling of None as password"""
        with pytest.raises(Exception):
            get_password_hash(None)

    @pytest.mark.unit
    @pytest.mark.security
    def test_very_long_password(self):
        """Test that very long passwords are handled"""
        long_password = "A" * 1000 + "a1!"
        hashed = get_password_hash(long_password)
        assert verify_password(long_password, hashed) is True

    @pytest.mark.unit
    @pytest.mark.security
    def test_special_characters_in_password(self):
        """Test passwords with special characters"""
        password = "Test!@#$%^&*()_+-=[]{}|;:,.<>?123Pass"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    @pytest.mark.unit
    @pytest.mark.security
    def test_unicode_in_password(self):
        """Test passwords with unicode characters"""
        password = "Tëst123!Pässwörd"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    @pytest.mark.unit
    @pytest.mark.security
    def test_token_tampering(self):
        """Test that tampered tokens are rejected"""
        user_data = {"sub": 1, "role": "student"}
        token = create_access_token(data=user_data)

        # Tamper with the token
        parts = token.split('.')
        if len(parts) == 3:
            # Change a character in the payload
            tampered_token = parts[0] + '.' + parts[1][:-1] + 'X.' + parts[2]

            # Should raise exception when decoding
            with pytest.raises(Exception):
                decode_token(tampered_token)
