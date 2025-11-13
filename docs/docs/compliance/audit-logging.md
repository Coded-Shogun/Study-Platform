---
sidebar_position: 4
---

# Audit Logging Guide

Comprehensive audit logging for compliance, security, and incident investigation.

## 📋 Overview

Study Platform implements **comprehensive audit logging** that tracks all security-relevant events for compliance and incident response.

**Coverage**: 100% of security events
**Retention**: Minimum 1 year
**Standards Met**: SOC 2 (CC6.3), ISO 27001 (A.8.15), NIST (DE.CM-1)

## 🎯 What Gets Logged

### Authentication Events
- ✅ User login (success/failure)
- ✅ User logout
- ✅ User registration
- ✅ Password changes
- ✅ Token refresh
- ✅ Failed login attempts (brute force detection)

### Admin Actions
- ✅ Subject creation/update/deletion
- ✅ Category creation/update/deletion
- ✅ Question creation/update/deletion
- ✅ Bulk operations
- ✅ User management actions

### Data Operations
- ✅ Data exports (GDPR)
- ✅ Data deletions (GDPR)
- ✅ Consent given/withdrawn
- ✅ Profile updates

### Security Events
- ✅ Brute force attempts
- ✅ Rate limit violations
- ✅ Unauthorized access attempts
- ✅ Token revocations
- ✅ Session expirations

## 📊 Audit Log Structure

Each log entry contains:

```json
{
  "id": 12345,
  "timestamp": "2024-01-15T14:30:00Z",
  "event_type": "LOGIN",
  "event_category": "AUTH",
  "action": "User logged in successfully",
  "result": "SUCCESS",
  "user_id": 42,
  "username": "student123",
  "user_role": "student",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "resource_type": null,
  "resource_id": null,
  "old_values": null,
  "new_values": null,
  "description": "User logged in successfully",
  "metadata": {
    "session_id": "abc123..."
  }
}
```

## 🔍 Query Audit Logs

### View All Logs (Admin)

```http
GET /api/compliance/audit-logs?skip=0&limit=100
```

### Filter by Event Type

```http
GET /api/compliance/audit-logs?event_type=LOGIN
```

### Filter by Category

```http
GET /api/compliance/audit-logs?event_category=ADMIN
```

### Filter by User

```http
GET /api/compliance/audit-logs?user_id=42
```

### Filter by Date Range

```http
GET /api/compliance/audit-logs?start_date=2024-01-01&end_date=2024-01-31
```

### Filter by Result

```http
GET /api/compliance/audit-logs?result=FAILURE
```

## 📈 Audit Statistics

Get aggregated statistics:

```http
GET /api/compliance/audit-logs/stats?days=7
```

**Response**:
```json
{
  "total_logs": 15234,
  "logs_by_category": {
    "AUTH": 8500,
    "ADMIN": 2300,
    "DATA": 1200,
    "SECURITY": 234
  },
  "logs_by_result": {
    "SUCCESS": 14800,
    "FAILURE": 434
  },
  "top_users": [
    {
      "user_id": 1,
      "username": "admin",
      "activity_count": 1250
    },
    {
      "user_id": 42,
      "username": "teacher1",
      "activity_count": 890
    }
  ],
  "recent_failures": 34
}
```

## 👤 View Your Activity

As a user, view your own activity:

```http
GET /api/compliance/my-activity?days=30
```

**Shows**:
- All your logins
- Your data exports
- Your profile changes
- Your quiz activity
- Your consent history

## 🚨 Security Events

High-priority security events are tracked separately:

```http
GET /api/compliance/security-events?severity=HIGH
```

**Severity levels**:
- **CRITICAL**: Immediate action required
- **HIGH**: Urgent investigation needed
- **MEDIUM**: Monitor closely
- **LOW**: Informational

**Event types**:
- BRUTE_FORCE_ATTEMPT
- UNAUTHORIZED_ACCESS
- RATE_LIMIT_EXCEEDED
- SUSPICIOUS_ACTIVITY

## 🔐 Data Protection

### PII in Audit Logs

Sensitive data is **redacted** in audit logs:
- ❌ Passwords (never logged)
- ❌ Credit cards
- ❌ API keys
- ❌ Tokens
- ✅ IP addresses (anonymized after retention period)
- ✅ Usernames (kept for investigation)

### Retention

- **Security logs**: 1 year minimum
- **Compliance logs**: 7 years (legal requirement)
- **Personal data**: Anonymized after retention

## 📊 Common Use Cases

### 1. Investigate Failed Logins

```http
GET /api/compliance/audit-logs?event_type=LOGIN_FAILED&days=1
```

### 2. Track Admin Changes

```http
GET /api/compliance/audit-logs?event_category=ADMIN&days=7
```

### 3. Monitor Specific User

```http
GET /api/compliance/audit-logs/user/42?days=30
```

### 4. Detect Brute Force

```http
GET /api/compliance/security-events?event_type=BRUTE_FORCE_ATTEMPT
```

### 5. Compliance Audit

```http
GET /api/compliance/audit-logs?start_date=2024-01-01&end_date=2024-12-31
```

## 📄 Export Audit Logs

For compliance audits:

```bash
# Export to JSON
curl "https://api.studyplatform.com/api/compliance/audit-logs?start_date=2024-01-01&limit=10000" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  > audit-logs-2024.json
```

## 🎯 Compliance Mapping

| Standard | Requirement | Implementation |
|----------|-------------|----------------|
| **SOC 2** | CC6.3 - Event logging | ✅ All events logged |
| **ISO 27001** | A.8.15 - Logging | ✅ Comprehensive logs |
| **GDPR** | Art. 5 - Accountability | ✅ Full audit trail |
| **NIST** | DE.CM-1 - Network monitoring | ✅ Activity detection |

## 📚 Related Documentation

- [Compliance Overview](./overview)
- [GDPR Compliance](./gdpr-compliance)
- [Session Management](./session-management)
- [API Reference](../api/compliance)

---

**For audit support**: Contact your compliance officer or review detailed logs via the API.
