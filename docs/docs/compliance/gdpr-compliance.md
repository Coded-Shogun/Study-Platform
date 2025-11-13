---
sidebar_position: 2
---

# GDPR Compliance Guide

Complete guide to GDPR (General Data Protection Regulation) compliance features in Study Platform.

## 🇪🇺 GDPR Compliance: 85%

Study Platform is **85% GDPR compliant**, implementing all essential data subject rights and privacy protections required for EU operations.

## 📜 Your Data Rights

Under GDPR, you have the following rights regarding your personal data:

### 1. Right of Access (Article 15) ✅
**What it means**: You can see all data we hold about you.

**How to exercise**:
```http
GET /api/gdpr/my-data
```

**What you'll get**:
- Personal information (username, email, name)
- Quiz history and answers
- Progress and achievements
- Study sessions
- Activity history
- Active sessions
- Consent records
- Summary statistics

**Response time**: Immediate (preview) or up to 30 days (formal export)

---

### 2. Right to Erasure / Right to be Forgotten (Article 17) ✅
**What it means**: You can request deletion of your personal data.

**How to exercise**:
```http
POST /api/gdpr/deletion-request
{
  "deletion_scope": "ANONYMIZE",  // or "FULL"
  "confirm_deletion": true,
  "reason": "No longer need the service"
}
```

**Deletion options**:
- **ANONYMIZE** (Recommended): Removes personal information but keeps statistical data
  - Username becomes `deleted_user_123`
  - Email becomes `deleted_123@anonymized.local`
  - Full name removed
  - IP addresses anonymized
  - Quiz data preserved for analytics

- **FULL**: Complete deletion of all data
  - All quiz sessions deleted
  - All progress records deleted
  - All study sessions deleted
  - Account completely removed
  - Requires admin approval

**Processing time**:
- ANONYMIZE: Immediate
- FULL: Up to 30 days (requires approval)

---

### 3. Right to Data Portability (Article 20) ✅
**What it means**: You can get your data in a machine-readable format to transfer to another service.

**How to exercise**:
```http
POST /api/gdpr/export-request
{
  "export_format": "JSON"
}
```

**Export process**:
1. Submit export request
2. System processes your data (usually < 1 minute)
3. Download link available for 30 days
4. Download your data file

**Download**:
```http
GET /api/gdpr/export-requests/{request_id}/download
```

**File format**: JSON (structured, machine-readable)
**File size**: Typically < 1MB
**Expiration**: 30 days after creation

---

### 4. Right to Withdraw Consent (Article 7) ✅
**What it means**: You can withdraw consent for data processing at any time.

**Consent types**:
- Terms of Service
- Privacy Policy
- Marketing Communications
- Analytics

**How to withdraw**:
```http
DELETE /api/gdpr/consent/{consent_type}
```

**Effect**: Immediate. We stop processing your data for that purpose.

---

### 5. Right to Rectification ✅
**What it means**: You can correct inaccurate personal data.

**How to exercise**: Update your profile through the UI or:
```http
PUT /api/auth/profile
{
  "email": "newemail@example.com",
  "full_name": "Corrected Name"
}
```

---

## 🔐 Data We Collect

### Personal Data
- **Account Information**: Username, email address, full name (optional)
- **Authentication Data**: Hashed password (never stored in plain text)
- **Role Information**: User role (Student, Teacher, Admin)
- **Student Level**: Education level (Primary, High School, Tertiary)

### Usage Data
- **Quiz Activity**: Questions answered, scores, time spent
- **Progress Data**: Subject progress, accuracy, achievements
- **Study Sessions**: Duration, topics covered, notes
- **Activity Logs**: Login times, actions performed, IP addresses
- **Session Data**: Active sessions, devices used, last activity

### Technical Data
- **IP Addresses**: For security and audit purposes
- **User Agents**: Browser/device information
- **Session IDs**: For session management
- **Timestamps**: When actions occurred

## 🎯 Lawful Basis for Processing

We process your data based on:

1. **Consent** (Article 6(1)(a))
   - Creating an account
   - Marketing communications
   - Analytics cookies

2. **Contract** (Article 6(1)(b))
   - Providing educational services
   - Managing your account
   - Processing quiz results

3. **Legitimate Interest** (Article 6(1)(f))
   - Security and fraud prevention
   - Service improvement
   - System maintenance

## 📋 How We Use Your Data

| Purpose | Data Used | Legal Basis | Retention |
|---------|-----------|-------------|-----------|
| Account Management | Username, email, password | Contract | Until deletion |
| Learning Services | Quiz data, progress | Contract | Until deletion |
| Security | Audit logs, sessions | Legitimate Interest | 1 year |
| Compliance | Audit logs | Legal Obligation | 7 years |
| Analytics | Usage statistics | Consent | Until withdrawal |
| Marketing | Email | Consent | Until withdrawal |

## 🛡️ Data Protection Measures

### Technical Measures
- ✅ **Encryption in Transit**: TLS 1.3 for all connections
- ✅ **Encryption at Rest**: Planned for PII fields
- ✅ **Password Hashing**: BCrypt with cost factor 12
- ✅ **Session Security**: 15-minute idle, 8-hour absolute timeout
- ✅ **Access Controls**: Role-based permissions
- ✅ **Audit Logging**: All data access tracked

### Organizational Measures
- ✅ **Privacy by Design**: Built-in privacy protections
- ✅ **Data Minimization**: Only collect necessary data
- ✅ **Purpose Limitation**: Data used only for stated purposes
- ✅ **Access Restrictions**: Need-to-know basis
- ✅ **Staff Training**: Security awareness program
- ✅ **Incident Response**: 72-hour breach notification

## 📊 Consent Management

### View Your Consents
```http
GET /api/gdpr/consent
```

**Response**:
```json
[
  {
    "id": 1,
    "consent_type": "privacy_policy",
    "purpose": "Consent to Privacy Policy for processing personal data",
    "consented": true,
    "consented_at": "2024-01-15T10:30:00Z",
    "version": "1.0",
    "method": "explicit_checkbox"
  },
  {
    "consent_type": "marketing",
    "consented": false,
    "withdrawn_at": "2024-02-01T14:20:00Z"
  }
]
```

### Give Consent
```http
POST /api/gdpr/consent
{
  "consent_type": "marketing",
  "consented": true,
  "version": "1.0"
}
```

### Withdraw Consent
```http
DELETE /api/gdpr/consent/marketing
```

## 📝 Data Retention Policy

| Data Type | Retention Period | Reason |
|-----------|------------------|--------|
| Account Data | Until deletion requested | Service provision |
| Quiz Results | Until deletion requested | Service provision |
| Audit Logs (Security) | 1 year | Security monitoring |
| Audit Logs (Compliance) | 7 years | Legal requirement |
| Session Data | Until session expires | Security |
| Consent Records | 7 years after withdrawal | Proof of compliance |
| Deleted User Data | Anonymized permanently | Analytics |

## 🚨 Data Breach Notification

In the event of a data breach:

1. **We notify you within 72 hours** if your data is affected
2. **We notify authorities** as required by GDPR
3. **We provide details** of what data was affected
4. **We explain measures taken** to protect you
5. **We offer remediation** (e.g., password reset)

## 👥 Data Sharing

We **DO NOT**:
- ❌ Sell your personal data
- ❌ Share data with third parties for marketing
- ❌ Transfer data outside EU/EEA without safeguards

We **MAY** share with:
- ✅ Cloud hosting providers (with DPA in place)
- ✅ Security service providers
- ✅ Legal authorities (when required by law)

All third-party processors are GDPR compliant with Data Processing Agreements.

## 🌍 International Transfers

If data is transferred outside EU/EEA:

- ✅ **Standard Contractual Clauses** (SCCs) in place
- ✅ **Adequacy decision** (transfers to approved countries)
- ✅ **Additional safeguards** (encryption, access controls)
- ✅ **User notification** (transparent about transfers)

## 📞 Data Protection Contact

**Data Protection Officer (DPO)**:
- Email: dpo@studyplatform.com
- Response time: 48 hours

**User Rights Requests**:
- Via UI: Use GDPR features in your account
- Via API: See API endpoints above
- Via Email: dpo@studyplatform.com

**Complaints**:
If unsatisfied with our response, you can file a complaint with your local Data Protection Authority.

## 🔍 Compliance Audit Trail

Every GDPR action is logged:

```http
GET /api/compliance/my-activity?event_category=DATA
```

**Logged events**:
- Data exports requested/downloaded
- Deletion requests submitted
- Consent given/withdrawn
- Profile updates
- Data access

**Audit log includes**:
- Timestamp
- Action performed
- IP address
- Result (success/failure)

## 📚 User Guide: Step-by-Step

### How to Export Your Data

1. **Log in** to your account
2. **Navigate** to Settings → Privacy
3. **Click** "Export My Data"
4. **Wait** for processing (usually < 1 minute)
5. **Download** your data file
6. **File expires** in 30 days

Or via API:
```bash
# Request export
curl -X POST https://api.studyplatform.com/api/gdpr/export-request \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"export_format": "JSON"}'

# Check status
curl https://api.studyplatform.com/api/gdpr/export-requests \
  -H "Authorization: Bearer YOUR_TOKEN"

# Download
curl https://api.studyplatform.com/api/gdpr/export-requests/1/download \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o my-data.json
```

### How to Delete Your Account

1. **Log in** to your account
2. **Navigate** to Settings → Privacy
3. **Click** "Delete My Account"
4. **Choose deletion type**:
   - Anonymize (recommended): Remove personal info, keep learning data
   - Full deletion: Remove everything (requires approval)
5. **Confirm** by checking the box
6. **Submit** request
7. **Wait** for processing
   - Anonymize: Immediate
   - Full: Up to 30 days

Or via API:
```bash
curl -X POST https://api.studyplatform.com/api/gdpr/deletion-request \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "deletion_scope": "ANONYMIZE",
    "confirm_deletion": true,
    "reason": "No longer need the service"
  }'
```

### How to Manage Consent

1. **Log in** to your account
2. **Navigate** to Settings → Privacy → Consent
3. **View** all your consent records
4. **Toggle** individual consents on/off
5. **Changes** take effect immediately

Or via API:
```bash
# View consents
curl https://api.studyplatform.com/api/gdpr/consent \
  -H "Authorization: Bearer YOUR_TOKEN"

# Withdraw consent
curl -X DELETE https://api.studyplatform.com/api/gdpr/consent/marketing \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 🎓 For Administrators

### Approve Deletion Requests

```http
GET /api/gdpr/admin/deletion-requests?status_filter=PENDING
```

```http
POST /api/gdpr/admin/deletion-requests/{request_id}/approve
```

### Privacy Policy Management

Create new policy version:
```http
POST /api/admin/privacy-policies
{
  "document_type": "privacy_policy",
  "version": "2.0",
  "title": "Privacy Policy v2.0",
  "content": "...",
  "effective_date": "2024-06-01T00:00:00Z"
}
```

### Monitor GDPR Compliance

```http
GET /api/compliance/audit-logs?event_type=EXPORT
GET /api/compliance/audit-logs?event_type=DELETE
GET /api/compliance/audit-logs?event_type=CONSENT_GIVEN
```

## ✅ GDPR Checklist

Use this checklist to ensure GDPR compliance:

- [x] **Privacy Policy** published and accessible
- [x] **Cookie consent** implemented
- [x] **Data export** functionality available
- [x] **Data deletion** functionality available
- [x] **Consent management** system in place
- [x] **Audit logging** for all data processing
- [x] **DPO appointed** and contact info published
- [x] **Data breach procedures** documented
- [x] **User rights** clearly communicated
- [x] **Retention policies** defined and enforced
- [ ] **Encryption at rest** for all PII (planned)
- [ ] **Anonymization** for analytics (planned)
- [ ] **Data transfer mechanisms** fully documented

## 📖 Related Documentation

- [Compliance Overview](./overview) - Overall compliance status
- [Audit Logging Guide](./audit-logging) - How activity is tracked
- [Session Management](./session-management) - How sessions work
- [API Reference](../api/gdpr) - Complete API documentation

---

**Questions about GDPR?** Contact your Data Protection Officer or review the [full compliance assessment](https://github.com/Coded-Shogun/Study-Platform/blob/main/COMPLIANCE_ASSESSMENT.md).
