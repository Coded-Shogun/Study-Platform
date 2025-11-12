"""
Encryption utilities for protecting sensitive data at rest.

Implements field-level encryption for PII compliance (GDPR, ISO 27001 A.8.24).
Uses Fernet symmetric encryption with key rotation support.
"""

import os
import base64
from typing import Optional, Union
from cryptography.fernet import Fernet, MultiFernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend
import logging

logger = logging.getLogger(__name__)


class EncryptionService:
    """
    Service for encrypting and decrypting sensitive data at rest.

    Features:
    - AES-256 encryption via Fernet
    - Key rotation support
    - Transparent encryption/decryption
    - Secure key derivation

    Compliance:
    - ISO 27001 A.8.24 (Encryption)
    - GDPR Article 32 (Security of processing)
    - SOC 2 CC6.7 (Encryption)
    """

    def __init__(self):
        """Initialize encryption service with keys from environment"""
        self.primary_key = self._get_or_create_key("ENCRYPTION_KEY")
        self.rotation_keys = self._load_rotation_keys()
        self.fernet = self._create_fernet_instance()

    def _get_or_create_key(self, env_var: str) -> bytes:
        """
        Get encryption key from environment or generate new one.

        Args:
            env_var: Environment variable name

        Returns:
            Encryption key as bytes

        Note:
            In production, keys should NEVER be auto-generated.
            They should be managed via a key management service (KMS).
        """
        key_b64 = os.getenv(env_var)

        if key_b64:
            try:
                return base64.urlsafe_b64decode(key_b64)
            except Exception as e:
                logger.error(f"Invalid key in {env_var}: {e}")
                raise ValueError(f"Invalid encryption key in {env_var}")

        # Development fallback - NEVER use in production
        if os.getenv("ENVIRONMENT") == "production":
            raise ValueError(
                f"{env_var} not set in production environment. "
                "Encryption keys MUST be explicitly configured."
            )

        logger.warning(
            f"⚠️  {env_var} not set. Generating temporary key for development. "
            "DO NOT use in production!"
        )
        return Fernet.generate_key()

    def _load_rotation_keys(self) -> list:
        """
        Load historical encryption keys for key rotation.

        Supports graceful key rotation by maintaining old keys for decryption
        while using the primary key for encryption.

        Returns:
            List of historical encryption keys
        """
        keys = []

        # Load up to 5 rotation keys
        for i in range(1, 6):
            key_b64 = os.getenv(f"ENCRYPTION_KEY_ROTATION_{i}")
            if key_b64:
                try:
                    keys.append(base64.urlsafe_b64decode(key_b64))
                except Exception as e:
                    logger.warning(f"Invalid rotation key {i}: {e}")

        return keys

    def _create_fernet_instance(self) -> Union[Fernet, MultiFernet]:
        """
        Create Fernet instance supporting multiple keys.

        MultiFernet tries decryption with each key in order,
        allowing seamless key rotation.

        Returns:
            Fernet or MultiFernet instance
        """
        if self.rotation_keys:
            # Primary key first, then rotation keys
            all_keys = [self.primary_key] + self.rotation_keys
            return MultiFernet([Fernet(key) for key in all_keys])
        else:
            return Fernet(self.primary_key)

    def encrypt(self, plaintext: Optional[str]) -> Optional[str]:
        """
        Encrypt plaintext string.

        Args:
            plaintext: String to encrypt

        Returns:
            Base64-encoded encrypted string, or None if input is None

        Example:
            >>> service = EncryptionService()
            >>> encrypted = service.encrypt("user@example.com")
            >>> print(encrypted)
            'gAAAAABkX...'
        """
        if plaintext is None or plaintext == "":
            return None

        try:
            plaintext_bytes = plaintext.encode('utf-8')
            encrypted_bytes = self.fernet.encrypt(plaintext_bytes)
            return encrypted_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"Encryption error: {e}")
            raise ValueError(f"Failed to encrypt data: {str(e)}")

    def decrypt(self, ciphertext: Optional[str]) -> Optional[str]:
        """
        Decrypt ciphertext string.

        Args:
            ciphertext: Base64-encoded encrypted string

        Returns:
            Decrypted plaintext string, or None if input is None

        Example:
            >>> service = EncryptionService()
            >>> decrypted = service.decrypt('gAAAAABkX...')
            >>> print(decrypted)
            'user@example.com'
        """
        if ciphertext is None or ciphertext == "":
            return None

        try:
            ciphertext_bytes = ciphertext.encode('utf-8')
            decrypted_bytes = self.fernet.decrypt(ciphertext_bytes)
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            # Return None on decryption failure (data may be unencrypted legacy data)
            return None

    def encrypt_if_needed(self, value: Optional[str]) -> Optional[str]:
        """
        Encrypt value only if not already encrypted.

        Detects Fernet-encrypted strings by checking for 'gAAAAAB' prefix.

        Args:
            value: String to conditionally encrypt

        Returns:
            Encrypted string or original if already encrypted
        """
        if value is None or value == "":
            return None

        # Check if already encrypted (Fernet tokens start with 'gAAAAAB')
        if value.startswith('gAAAAAB'):
            return value

        return self.encrypt(value)

    def decrypt_if_needed(self, value: Optional[str]) -> Optional[str]:
        """
        Decrypt value only if encrypted.

        Detects Fernet-encrypted strings and decrypts them,
        otherwise returns the original value.

        Args:
            value: String to conditionally decrypt

        Returns:
            Decrypted string or original if not encrypted
        """
        if value is None or value == "":
            return None

        # Check if encrypted (Fernet tokens start with 'gAAAAAB')
        if value.startswith('gAAAAAB'):
            decrypted = self.decrypt(value)
            # If decryption fails, return original
            return decrypted if decrypted is not None else value

        return value

    def rotate_encryption(self, old_ciphertext: str) -> str:
        """
        Re-encrypt data with current primary key.

        Used for key rotation: decrypt with old key, encrypt with new key.

        Args:
            old_ciphertext: Data encrypted with old key

        Returns:
            Data re-encrypted with primary key
        """
        plaintext = self.decrypt(old_ciphertext)
        if plaintext is None:
            raise ValueError("Failed to decrypt data for rotation")

        # Encrypt with primary key only
        fernet_primary = Fernet(self.primary_key)
        encrypted_bytes = fernet_primary.encrypt(plaintext.encode('utf-8'))
        return encrypted_bytes.decode('utf-8')


# Global encryption service instance
_encryption_service: Optional[EncryptionService] = None


def get_encryption_service() -> EncryptionService:
    """
    Get global encryption service instance (singleton pattern).

    Returns:
        EncryptionService instance
    """
    global _encryption_service

    if _encryption_service is None:
        _encryption_service = EncryptionService()

    return _encryption_service


def encrypt_field(value: Optional[str]) -> Optional[str]:
    """
    Convenience function to encrypt a field value.

    Args:
        value: Plaintext value

    Returns:
        Encrypted value
    """
    service = get_encryption_service()
    return service.encrypt_if_needed(value)


def decrypt_field(value: Optional[str]) -> Optional[str]:
    """
    Convenience function to decrypt a field value.

    Args:
        value: Encrypted value

    Returns:
        Decrypted plaintext value
    """
    service = get_encryption_service()
    return service.decrypt_if_needed(value)


# Key generation utility
def generate_encryption_key() -> str:
    """
    Generate a new Fernet encryption key.

    Returns:
        Base64-encoded encryption key

    Example:
        >>> key = generate_encryption_key()
        >>> print(f"ENCRYPTION_KEY={key}")
        ENCRYPTION_KEY=jKFDkw3...

    Usage:
        Run this function once to generate keys, then store them securely:

        1. Generate keys:
           python -c "from app.utils.encryption import generate_encryption_key; print(generate_encryption_key())"

        2. Store in environment:
           export ENCRYPTION_KEY="<generated_key>"

        3. For key rotation, store old key:
           export ENCRYPTION_KEY_ROTATION_1="<old_key>"
    """
    key = Fernet.generate_key()
    return key.decode('utf-8')


def derive_key_from_password(password: str, salt: Optional[bytes] = None) -> tuple:
    """
    Derive encryption key from password using PBKDF2.

    Args:
        password: Master password
        salt: Optional salt (generated if not provided)

    Returns:
        Tuple of (key_b64, salt_b64)

    Example:
        >>> key, salt = derive_key_from_password("my_secure_password")
        >>> print(f"ENCRYPTION_KEY={key}")
        >>> print(f"ENCRYPTION_SALT={salt}")

    Note:
        NOT recommended for production. Use a proper KMS instead.
    """
    if salt is None:
        salt = os.urandom(16)

    kdf = PBKDF2(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )

    key = base64.urlsafe_b64encode(kdf.derive(password.encode('utf-8')))
    salt_b64 = base64.urlsafe_b64encode(salt).decode('utf-8')

    return key.decode('utf-8'), salt_b64


# CLI utilities for key management
if __name__ == "__main__":
    """
    Command-line utilities for key management.

    Usage:
        python -m app.utils.encryption generate
        python -m app.utils.encryption derive <password>
    """
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python -m app.utils.encryption generate")
        print("  python -m app.utils.encryption derive <password>")
        sys.exit(1)

    command = sys.argv[1]

    if command == "generate":
        key = generate_encryption_key()
        print(f"\n🔑 Generated Encryption Key:")
        print(f"ENCRYPTION_KEY={key}")
        print(f"\n⚠️  Store this key securely! Never commit to version control.")
        print(f"   Add to .env file or environment variables.")

    elif command == "derive":
        if len(sys.argv) < 3:
            print("Error: Password required")
            print("Usage: python -m app.utils.encryption derive <password>")
            sys.exit(1)

        password = sys.argv[2]
        key, salt = derive_key_from_password(password)

        print(f"\n🔑 Derived Encryption Key:")
        print(f"ENCRYPTION_KEY={key}")
        print(f"ENCRYPTION_SALT={salt}")
        print(f"\n⚠️  Store both values securely!")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
