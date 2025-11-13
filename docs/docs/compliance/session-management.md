---
sidebar_position: 3
---

# Session Management Guide

Complete guide to session management, timeout controls, and multi-device security features.

## 🔐 Session Security

Study Platform implements enterprise-grade session management with automatic timeout controls and multi-device tracking for enhanced security.

## 📊 Session Overview

### What is a Session?

A **session** represents an authenticated connection between you and Study Platform. Each time you log in from a device or browser, a new session is created.

**Session includes**:
- Unique session ID
- Creation timestamp
- Last activity timestamp
- Expiration time
- IP address
- User agent (browser/device info)
- Active status

### Why Session Management Matters

- **Security**: Prevents unauthorized access from abandoned sessions
- **Compliance**: Meets SOC 2 and ISO 27001 requirements
- **Multi-device**: Track and manage sessions across devices
- **Accountability**: Know which devices accessed your account

## ⏰ Timeout Controls

### 1. Idle Timeout (15 minutes)
**What it is**: Session expires after 15 minutes of inactivity.

**How it works**:
- Every API request updates "last activity" timestamp
- If no requests for 15 minutes, session expires
- Next request requires re-authentication

**Example**:
```
10:00 AM - Login (session created)
10:05 AM - Take quiz (activity updated)
10:20 AM - Session expires (no activity since 10:05)
10:21 AM - Request rejected, must login again
```

**Why**: Protects accounts left open on shared or public computers.

---

### 2. Absolute Timeout (8 hours)
**What it is**: Session expires after 8 hours regardless of activity.

**How it works**:
- Session has maximum lifetime of 8 hours
- Even if actively used, session expires after 8 hours
- User must re-authenticate

**Example**:
```
9:00 AM - Login (expires at 5:00 PM)
...continuous activity all day...
5:00 PM - Session expires (8 hours passed)
5:01 PM - Must login again
```

**Why**: Limits exposure window for compromised tokens.

---

### 3. Concurrent Session Limit (3 sessions)
**What it is**: Maximum 3 active sessions per user.

**How it works**:
- You can be logged in on up to 3 devices simultaneously
- 4th login automatically logs out oldest session
- Prevents excessive session accumulation

**Example**:
```
Device 1: Desktop browser (Session created: 9:00 AM)
Device 2: Laptop browser (Session created: 10:00 AM)
Device 3: Mobile browser (Session created: 11:00 AM)
Device 4: Tablet (logs in at 2:00 PM)
  → Desktop session (oldest) automatically revoked
```

**Why**: Prevents account sharing while allowing legitimate multi-device use.

---

## 📱 Multi-Device Sessions

### View Your Sessions

See all active sessions across your devices:

```http
GET /api/auth/sessions
```

**Response**:
```json
{
  "total_sessions": 2,
  "sessions": [
    {
      "session_id": "abc123...",
      "created_at": "2024-01-15T09:00:00Z",
      "last_activity_at": "2024-01-15T14:30:00Z",
      "expires_at": "2024-01-15T17:00:00Z",
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
      "is_current": true
    },
    {
      "session_id": "def456...",
      "created_at": "2024-01-15T08:00:00Z",
      "last_activity_at": "2024-01-15T13:00:00Z",
      "expires_at": "2024-01-15T16:00:00Z",
      "ip_address": "192.168.1.105",
      "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) Safari/604.1",
      "is_current": false
    }
  ]
}
```

**Session info includes**:
- **Session ID**: Unique identifier
- **Created**: When you logged in
- **Last Activity**: Last API request time
- **Expires**: When session will timeout
- **IP Address**: Device IP address
- **User Agent**: Browser and device type
- **Is Current**: Whether this is your current session

---

### Remote Session Revocation

Log out from other devices remotely:

```http
DELETE /api/auth/sessions/{session_id}
```

**Use cases**:
- Lost or stolen device
- Public computer (forgot to logout)
- Suspicious activity
- Device you no longer use

**Effect**: Immediate. That device must login again.

---

## 🔑 Token Types

### Access Token
- **Purpose**: Authenticate API requests
- **Lifetime**: 30 minutes
- **Storage**: Memory (not persisted)
- **Contains**: User ID, role, JTI
- **Usage**: Sent with every API request

### Refresh Token
- **Purpose**: Get new access tokens
- **Lifetime**: 7 days
- **Storage**: Secure storage (HttpOnly cookie recommended)
- **Contains**: User ID, JTI (linked to session)
- **Usage**: Only for token refresh endpoint

### JWT ID (JTI)
- **Purpose**: Unique token identifier for revocation
- **Format**: UUID v4
- **Usage**: Links token to session, enables blacklisting
- **Tracking**: Stored in `user_sessions` table

---

## 🛡️ Session Lifecycle

### 1. Login (Session Creation)

```http
POST /api/auth/login
{
  "username": "student123",
  "password": "SecurePass123!"
}
```

**Backend process**:
1. Validate credentials
2. Generate access token (30min) with JTI
3. Generate refresh token (7 days) with JTI
4. Create session record:
   - Link to refresh token JTI
   - Store IP and user agent
   - Set expiry times (15min idle, 8hr absolute)
   - Check concurrent session limit
5. Return tokens

**Response**:
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer",
  "user": { ...user info... }
}
```

---

### 2. Token Refresh (Session Validation)

```http
POST /api/auth/refresh
{
  "refresh_token": "eyJhbGc..."
}
```

**Backend process**:
1. Decode refresh token
2. Extract JTI, find session
3. **Validate session**:
   - Check if active
   - Check idle timeout (< 15min since last activity)
   - Check absolute timeout (< 8hr since creation)
4. If valid:
   - Update last activity timestamp
   - Generate new access token
   - Return new tokens
5. If invalid:
   - Revoke session
   - Return 401 Unauthorized

**Success response**:
```json
{
  "access_token": "eyJhbGc...",  // New 30min token
  "refresh_token": "eyJhbGc...",  // Same JTI, updated
  "token_type": "bearer",
  "user": { ...user info... }
}
```

**Failure response** (session expired):
```json
{
  "detail": "Session expired due to inactivity"
}
```

---

### 3. Logout (Session Revocation)

**Single session logout**:
```http
POST /api/auth/logout
{
  "refresh_token": "eyJhbGc..."
}
```
- Revokes only the session for that refresh token
- Other sessions remain active

**All sessions logout**:
```http
POST /api/auth/logout
```
- Revokes all active sessions for the user
- Must login again on all devices

**Response**:
```json
{
  "message": "Logged out successfully",
  "sessions_revoked": 1
}
```

---

## 🚨 Security Features

### 1. Automatic Session Cleanup

**Background task** (runs periodically):
```python
cleanup_expired_sessions(db)
```

**Cleans up**:
- Sessions past absolute timeout (8 hours)
- Sessions past idle timeout (15 minutes)

**Effect**: Expired sessions can't be used, even with valid token.

---

### 2. Token Revocation Checking

**Every authenticated request**:
1. Extract JWT and decode
2. Extract JTI from token
3. Check if JTI is in revoked_tokens table
4. If revoked: **401 Unauthorized**
5. If valid: Process request

**Revocation triggers**:
- User logout
- Admin force-logout
- Suspicious activity detection
- Account deletion
- Password change (optional)

---

### 3. Brute Force Protection

**Integrated with audit logging**:
- Tracks failed login attempts
- 5+ failures in 15 minutes = Security event
- Account temporarily locked (optional)
- Notification sent to user

---

### 4. Session Monitoring

**Admin capabilities**:
- View all active sessions system-wide
- Force-logout any session
- Monitor suspicious activity (same user, different locations)
- Session analytics (peak usage times, device breakdown)

---

## 📊 Session Statistics

### View Session Activity

```http
GET /api/compliance/my-activity?event_category=AUTH
```

**Shows**:
- Login events (timestamps, IP addresses)
- Logout events
- Token refreshes
- Failed login attempts
- Session expirations

---

## 🎯 Best Practices

### For Users

1. **Always logout** on shared computers
2. **Review active sessions** regularly
3. **Revoke unknown sessions** immediately
4. **Use different passwords** for different devices
5. **Enable 2FA** (when available)

### For Developers

1. **Store tokens securely**:
   - Access token: Memory only
   - Refresh token: HttpOnly cookie or secure storage
2. **Handle token expiry**:
   - Catch 401 errors
   - Attempt token refresh
   - Redirect to login if refresh fails
3. **Update activity**:
   - Send requests regularly if user is active
   - Don't let session idle unintentionally
4. **Implement logout everywhere**:
   - Clear all stored tokens
   - Redirect to login page

### For Admins

1. **Monitor session statistics**
2. **Review security events** daily
3. **Investigate unusual patterns**:
   - Same user, multiple countries
   - Excessive session creation
   - Many expired sessions
4. **Adjust timeouts** if needed (via config)
5. **Run cleanup tasks** regularly

---

## 🔧 Configuration

Session timeouts are configurable (requires server restart):

```python
# app/utils/session.py

IDLE_TIMEOUT_MINUTES = 15  # Idle timeout
ABSOLUTE_TIMEOUT_HOURS = 8  # Maximum session lifetime
MAX_CONCURRENT_SESSIONS = 3  # Sessions per user
```

**Production recommendations**:
- **High security**: 5min idle, 4hr absolute, 1 concurrent
- **Balanced** (default): 15min idle, 8hr absolute, 3 concurrent
- **Convenience**: 30min idle, 24hr absolute, 5 concurrent

---

## 🚀 Implementation Example

### Frontend (React)

```typescript
// Login
const login = async (username: string, password: string) => {
  const response = await fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });

  const data = await response.json();

  // Store tokens
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('refresh_token', data.refresh_token);

  return data.user;
};

// Auto-refresh tokens
const refreshToken = async () => {
  const refresh_token = localStorage.getItem('refresh_token');

  const response = await fetch('/api/auth/refresh', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token })
  });

  if (!response.ok) {
    // Session expired, redirect to login
    window.location.href = '/login';
    return null;
  }

  const data = await response.json();
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('refresh_token', data.refresh_token);

  return data.access_token;
};

// Axios interceptor for automatic token refresh
axios.interceptors.response.use(
  response => response,
  async error => {
    if (error.response?.status === 401) {
      const newToken = await refreshToken();
      if (newToken) {
        error.config.headers.Authorization = `Bearer ${newToken}`;
        return axios(error.config);
      }
    }
    return Promise.reject(error);
  }
);

// Logout
const logout = async () => {
  const refresh_token = localStorage.getItem('refresh_token');

  await fetch('/api/auth/logout', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ refresh_token })
  });

  // Clear tokens
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');

  // Redirect
  window.location.href = '/login';
};
```

---

## 📈 Monitoring Dashboard (Coming Soon)

Planned features:
- Real-time session count
- Geographic session map
- Device breakdown (desktop, mobile, tablet)
- Session duration analytics
- Timeout reason breakdown
- Concurrent session trends

---

## ❓ Troubleshooting

### "Session expired" error

**Possible causes**:
1. **Idle for > 15 minutes** - Solution: Login again
2. **Session > 8 hours old** - Solution: Login again
3. **Logged in on 4th device** - Solution: Use existing session or login
4. **Manual logout from another device** - Solution: Login again

### Can't refresh token

**Possible causes**:
1. **Refresh token expired** (> 7 days) - Solution: Login again
2. **Session revoked** - Solution: Login again
3. **Token blacklisted** - Solution: Login again

### Too many sessions

**Possible causes**:
1. **Not logging out properly** - Solution: Logout on each device
2. **Multiple browsers/devices** - Solution: Revoke old sessions
3. **Concurrent limit too low** - Solution: Contact admin

---

## 📚 Related Documentation

- [Compliance Overview](./overview) - Overall security features
- [GDPR Compliance](./gdpr-compliance) - Privacy features
- [Audit Logging](./audit-logging) - Activity tracking
- [API Reference](../api/authentication) - Auth API docs

---

**Need help?** Review the [API documentation](../api/authentication) or contact support.
