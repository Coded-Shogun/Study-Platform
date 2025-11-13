"""
SQLAlchemy custom types for encrypted fields.

Provides transparent encryption/decryption at the ORM layer.
"""

from sqlalchemy.types import TypeDecorator, String, Text
from sqlalchemy.engine import Dialect
from typing import Optional, Any
import logging

from .encryption import get_encryption_service

logger = logging.getLogger(__name__)


class EncryptedString(TypeDecorator):
    """
    SQLAlchemy type for encrypted string fields.

    Automatically encrypts data before storing and decrypts when loading.
    Transparent to application code - use like a regular String column.

    Example:
        class User(Base):
            email = Column(EncryptedString(255), nullable=False)

        # Usage is transparent:
        user = User(email="user@example.com")  # Encrypted automatically
        print(user.email)  # "user@example.com" - Decrypted automatically
    """

    impl = String
    cache_ok = True

    def __init__(self, length: int = 500, *args, **kwargs):
        """
        Initialize encrypted string column.

        Args:
            length: Maximum column length (default 500 to accommodate encrypted data)
                   Note: Encrypted data is longer than plaintext (typically ~1.5x)
        """
        super().__init__(*args, **kwargs)
        self.length = length
        self.impl = String(length)

    def process_bind_param(self, value: Optional[str], dialect: Dialect) -> Optional[str]:
        """
        Encrypt value before storing in database.

        Args:
            value: Plaintext value to encrypt
            dialect: SQL dialect

        Returns:
            Encrypted value
        """
        if value is None or value == "":
            return None

        try:
            encryption_service = get_encryption_service()
            encrypted = encryption_service.encrypt_if_needed(value)
            return encrypted
        except Exception as e:
            logger.error(f"Encryption error in process_bind_param: {e}")
            # In case of error, store as-is (backwards compatibility)
            return value

    def process_result_value(self, value: Optional[str], dialect: Dialect) -> Optional[str]:
        """
        Decrypt value after loading from database.

        Args:
            value: Encrypted value from database
            dialect: SQL dialect

        Returns:
            Decrypted plaintext value
        """
        if value is None or value == "":
            return None

        try:
            encryption_service = get_encryption_service()
            decrypted = encryption_service.decrypt_if_needed(value)
            return decrypted
        except Exception as e:
            logger.error(f"Decryption error in process_result_value: {e}")
            # Return original value if decryption fails (legacy unencrypted data)
            return value


class EncryptedText(TypeDecorator):
    """
    SQLAlchemy type for encrypted text fields (longer content).

    Similar to EncryptedString but for Text columns.

    Example:
        class User(Base):
            notes = Column(EncryptedText, nullable=True)
    """

    impl = Text
    cache_ok = True

    def process_bind_param(self, value: Optional[str], dialect: Dialect) -> Optional[str]:
        """Encrypt value before storing"""
        if value is None or value == "":
            return None

        try:
            encryption_service = get_encryption_service()
            encrypted = encryption_service.encrypt_if_needed(value)
            return encrypted
        except Exception as e:
            logger.error(f"Encryption error in EncryptedText: {e}")
            return value

    def process_result_value(self, value: Optional[str], dialect: Dialect) -> Optional[str]:
        """Decrypt value after loading"""
        if value is None or value == "":
            return None

        try:
            encryption_service = get_encryption_service()
            decrypted = encryption_service.decrypt_if_needed(value)
            return decrypted
        except Exception as e:
            logger.error(f"Decryption error in EncryptedText: {e}")
            return value


# Compatibility aliases
EncryptedStringType = EncryptedString
EncryptedTextField = EncryptedText
