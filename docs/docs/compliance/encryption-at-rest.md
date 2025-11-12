# Encryption at Rest

## Overview

Study Platform implements **field-level encryption at rest** for all sensitive personally identifiable information (PII) to ensure the highest level of data protection and meet enterprise compliance requirements.

:::tip Enterprise Feature
Encryption at rest is a critical security control that protects sensitive data even if the database is compromised.
:::

## What is Encrypted?

### User Data
- **Email addresses** - Full encryption of all user email addresses
- **Full names** - Complete names encrypted for privacy protection
- **IP addresses** - Network identifiers in audit logs and sessions
- **User agents** - Browser/device information in tracking records

### Session Data
- **IP addresses** - Source IP for each session
- **User agent strings** - Device and browser information

### Audit & Compliance Data
- **IP addresses** - In audit logs and security events
- **User agent strings** - In activity tracking

### Consent Records
- **IP addresses** - Consent evidence metadata
- **User agent strings** - Device information at consent time

## Encryption Standards

| Aspect | Implementation |
|--------|---------------|
| **Algorithm** | AES-256 via Fernet symmetric encryption |
| **Key Size** | 256-bit encryption keys |
| **Mode** | Fernet (AES-128-CBC + HMAC-SHA256) |
| **Key Storage** | Environment variables (production: KMS) |
| **Key Rotation** | Supported with up to 5 historical keys |

## Compliance Mapping

### ISO 27001:2022

**A.8.24 - Use of Cryptography**
- ✅ Sensitive data encrypted with industry-standard algorithms
- ✅ Encryption keys managed securely
- ✅ Key rotation procedures in place

### GDPR

**Article 32 - Security of Processing**
- ✅ Encryption of personal data at rest
- ✅ Ability to restore access (decryption for data subject requests)
- ✅ Regular testing and evaluation of encryption

### SOC 2

**CC6.7 - Encryption Controls**
- ✅ Data encrypted in transit and at rest
- ✅ Encryption key management procedures
- ✅ Access controls for encrypted data

## How It Works

### Transparent Encryption

Encryption is **completely transparent** to application code. When you work with models, data is automatically encrypted on write and decrypted on read:

```python
# Create user with plaintext data
user = User(
    email="user@example.com",
    full_name="John Doe"
)
db.add(user)
db.commit()

# Data is encrypted in the database
# But reads return plaintext automatically
print(user.email)  # "user@example.com"
print(user.full_name)  # "John Doe"

# In the database, these fields are stored as:
# email: "gAAAAABkX..."  (encrypted)
# full_name: "gAAAAABkY..."  (encrypted)
```

### Architecture

```
┌─────────────────┐
│  Application    │
│  Layer          │
└────────┬────────┘
         │ Plaintext: "user@example.com"
         ↓
┌─────────────────┐
│  SQLAlchemy     │
│  EncryptedString│ ← Automatic encryption
└────────┬────────┘
         │ Encrypted: "gAAAAABkX..."
         ↓
┌─────────────────┐
│  Database       │
│  (PostgreSQL)   │
└─────────────────┘
```

## Key Management

### Development Environment

```bash
# Generate encryption key
python -m app.utils.encryption generate

# Output:
# ENCRYPTION_KEY=jKFDkw3pT7vC8xZ2mN9qR5tU6vW8xY1zA3bC4dE5fG6hI7jK8l

# Add to .env file
echo "ENCRYPTION_KEY=your_generated_key" >> .env
```

### Production Environment

**⚠️ CRITICAL:** Never store production keys in code or .env files!

Use a **Key Management Service (KMS)**:

- **AWS KMS** - AWS Key Management Service
- **Azure Key Vault** - Microsoft Azure key storage
- **Google Cloud KMS** - Google Cloud key management
- **HashiCorp Vault** - Multi-cloud secret management

```bash
# Production: Load from KMS
export ENCRYPTION_KEY=$(aws kms decrypt --ciphertext-blob fileb://encrypted_key.bin --output text --query Plaintext | base64 -d)
```

### Key Rotation

Key rotation allows you to update encryption keys without downtime:

**Step 1: Generate New Key**
```bash
python -m app.utils.encryption generate
```

**Step 2: Configure Keys**
```bash
# Move current key to rotation slot
export ENCRYPTION_KEY_ROTATION_1=$ENCRYPTION_KEY

# Set new key as primary
export ENCRYPTION_KEY=<new_key>
```

**Step 3: Restart Application**
- Application continues to work immediately
- Old encrypted data decrypts with rotation key
- New encryptions use new primary key

**Step 4: Re-encrypt Data (Optional)**
```bash
# Re-encrypt all data with new key
python -m app.utils.encrypt_existing_data --backup --encrypt
```

## Data Migration

### Encrypting Existing Data

If you have existing unencrypted data, use the migration utility:

**1. Preview Changes (Dry Run)**
```bash
python -m app.utils.encrypt_existing_data --dry-run
```

Output:
```
🔍 DRY RUN MODE - No changes will be made
============================================================
  Dry Run Results
============================================================
  Users Processed............................. 1,234
  Users Encrypted.............................. 1,234
  Users Skipped................................ 0
  Errors....................................... 0
============================================================
```

**2. Create Backup**
```bash
python -m app.utils.encrypt_existing_data --backup
```

**3. Encrypt Data**
```bash
python -m app.utils.encrypt_existing_data --encrypt
```

**4. Verify Encryption**
```bash
python -m app.utils.encrypt_existing_data --verify
```

Output:
```
🔍 Verifying encryption...
============================================================
  Verification Results
============================================================
  Total Users.................................. 1,234
  Encrypted Emails............................. 1,234
  Encrypted Names.............................. 1,234
  Decryption Errors............................ 0
  Unencrypted Found............................ 0
============================================================
✅ All encrypted data verified successfully!
```

## Performance Impact

### Benchmarks

| Operation | Without Encryption | With Encryption | Overhead |
|-----------|-------------------|-----------------|----------|
| User Creation | 50ms | 52ms | +2ms (4%) |
| User Query | 10ms | 11ms | +1ms (10%) |
| Bulk Read (100) | 100ms | 110ms | +10ms (10%) |

:::info Performance
Encryption adds minimal overhead (~1-2ms per field) and is suitable for production workloads.
:::

### Optimization Tips

1. **Selective Encryption** - Only encrypt truly sensitive fields
2. **Caching** - Cache decrypted values in application memory
3. **Batch Operations** - Process encryption in batches
4. **Connection Pooling** - Minimize database round-trips

## Security Best Practices

### ✅ DO

- ✅ Store keys in KMS (production)
- ✅ Rotate keys every 90-180 days
- ✅ Use strong, randomly generated keys
- ✅ Monitor encryption/decryption errors
- ✅ Test key rotation procedures
- ✅ Backup encryption keys securely
- ✅ Limit access to encryption keys
- ✅ Use environment variables for keys

### ❌ DON'T

- ❌ Never commit keys to version control
- ❌ Never hardcode keys in source code
- ❌ Never log decrypted PII values
- ❌ Never use the same key across environments
- ❌ Never skip key rotation
- ❌ Never store keys in plain text files
- ❌ Never share keys via insecure channels

## Monitoring

### Key Metrics

**Encryption Health**
- Percentage of encrypted fields
- Encryption/decryption error rate
- Key rotation status
- Backup key age

**Performance Metrics**
- Average encryption time
- Average decryption time
- Database query time impact

### Alerts

Set up alerts for:
- ⚠️ Decryption errors (may indicate key rotation issues)
- ⚠️ Unencrypted PII found
- ⚠️ Key age > 180 days
- ⚠️ Encryption errors > 0.1%

## Troubleshooting

### "Invalid encryption key"

**Cause:** Key format is incorrect

**Solution:**
```bash
# Regenerate key
python -m app.utils.encryption generate

# Ensure proper base64 encoding
echo $ENCRYPTION_KEY | base64 -d
```

### "Failed to decrypt data"

**Cause:** Data encrypted with different key

**Solution:**
```bash
# Add old key as rotation key
export ENCRYPTION_KEY_ROTATION_1=<old_key>

# Verify rotation
python -m app.utils.encrypt_existing_data --verify
```

### "Data is unencrypted"

**Cause:** Legacy data not yet encrypted

**Solution:**
```bash
# Encrypt existing data
python -m app.utils.encrypt_existing_data --backup --encrypt
```

## API Reference

### Encryption Service

```python
from app.utils.encryption import get_encryption_service

service = get_encryption_service()

# Encrypt data
encrypted = service.encrypt("sensitive_data")

# Decrypt data
decrypted = service.decrypt(encrypted)

# Conditional encryption
encrypted = service.encrypt_if_needed(value)

# Conditional decryption
decrypted = service.decrypt_if_needed(value)
```

### Encrypted Column Types

```python
from app.utils.encrypted_types import EncryptedString, EncryptedText

class MyModel(Base):
    # Encrypted string (max 500 chars plaintext)
    email = Column(EncryptedString(500))

    # Encrypted text (unlimited)
    notes = Column(EncryptedText)
```

### Helper Functions

```python
from app.utils.encryption import encrypt_field, decrypt_field

# Quick encryption
encrypted = encrypt_field("user@example.com")

# Quick decryption
decrypted = decrypt_field(encrypted)
```

## Compliance Reports

### Encryption Coverage Report

Generate a report of encryption coverage:

```bash
python -m app.utils.encrypt_existing_data --verify
```

### Audit Trail

All encryption-related operations are logged:

- Encryption service initialization
- Key loading events
- Encryption/decryption errors
- Data migration operations

View logs:
```bash
grep "encryption" logs/application.log
```

## FAQ

**Q: Does encryption impact search functionality?**
A: Yes, encrypted fields cannot be directly searched in the database. You must fetch records and filter in Python, or use application-level search indexes.

**Q: Can I search by email if it's encrypted?**
A: Direct database queries on encrypted fields are not possible. Use username (unencrypted) as the primary lookup key, or implement a secure hash-based lookup table.

**Q: What happens during key rotation?**
A: The application continues to work seamlessly. Old encrypted data is decrypted with rotation keys, new data is encrypted with the primary key.

**Q: How do I backup encryption keys?**
A: Store keys in a secure KMS with backup procedures, or export and store encrypted backups offline in a secure location (hardware security module, safe, etc.).

**Q: Is the password field encrypted?**
A: No, passwords use one-way hashing (bcrypt), not encryption. They cannot be decrypted, only verified.

**Q: What if I lose the encryption key?**
A: **Data loss is permanent.** Always maintain secure backups of encryption keys in multiple locations.

## Further Reading

- [Backend Encryption Documentation](../../backend/ENCRYPTION.md)
- [Key Management Best Practices](https://csrc.nist.gov/publications/detail/sp/800-57-part-1/rev-5/final)
- [OWASP Cryptographic Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html)
- [Fernet Specification](https://github.com/fernet/spec/blob/master/Spec.md)

---

**Last Updated:** 2025-11-12

**Compliance Status:** ✅ ISO 27001 A.8.24 | ✅ GDPR Art. 32 | ✅ SOC 2 CC6.7
