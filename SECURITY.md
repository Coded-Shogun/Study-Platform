# Security Features & Production Deployment Guide

This document outlines the security features implemented in the Study Platform and provides guidelines for secure production deployment.

## 🔒 Implemented Security Features

### 1. Password Security

**BCrypt Hashing**
- All passwords are hashed using bcrypt with automatic salt generation
- Configurable work factor for computational cost
- Protection against rainbow table and brute force attacks

**Password Policy** (Configurable via environment variables)
- Minimum length: 8 characters (default)
- Requires uppercase letters
- Requires lowercase letters
- Requires digits
- Optional special characters requirement

**Location**: `backend/app/utils/security.py`

### 2. JWT Authentication

**Access Tokens**
- Short-lived tokens (30 minutes default)
- Contains user ID and role
- Signed using HS256 algorithm
- Includes issued-at (iat) and expiration (exp) claims

**Refresh Tokens**
- Long-lived tokens (7 days default)
- Used to obtain new access tokens
- Separate token type verification

**Token Security**
- Bearer token authentication
- Type verification (access vs refresh)
- User existence and active status validation
- Automatic expiration handling

**Location**: `backend/app/utils/security.py`, `backend/app/utils/auth.py`

### 3. Role-Based Access Control (RBAC)

**User Roles**
- **Student**: Read-only access to appropriate content
- **Teacher**: Content creation and management
- **Admin**: Full system access

**Protection Mechanisms**
- `get_current_user()` - Validates JWT token
- `get_admin_user()` - Requires admin role
- `get_admin_or_teacher()` - Requires admin or teacher role
- `require_role(*roles)` - Flexible role checking

**Location**: `backend/app/utils/auth.py`

### 4. Rate Limiting

**Implementation**
- Using slowapi library (built on limits)
- Default: 60 requests per minute per IP
- Configurable via `RATE_LIMIT_PER_MINUTE`
- Can be enabled/disabled via `RATE_LIMIT_ENABLED`

**Protected Endpoints**
- All endpoints respect global rate limit
- Health check: 100/minute
- Can be customized per endpoint using `@limiter.limit()`

**Location**: `backend/app/middleware.py`, `backend/app/main.py`

### 5. CORS Configuration

**Settings**
- Configurable allowed origins via environment variable
- Credentials support enabled
- Specific HTTP methods allowed (GET, POST, PUT, DELETE, OPTIONS)
- Preflight request caching (10 minutes)

**Default Origins** (Development)
- http://localhost:3000
- http://127.0.0.1:3000
- http://localhost:5173 (Vite)
- http://127.0.0.1:5173

**Location**: `backend/app/main.py`, `backend/app/config.py`

### 6. Security Headers

**Implemented Headers**
```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
Referrer-Policy: strict-origin-when-cross-origin
Content-Security-Policy: default-src 'self'; ...
Permissions-Policy: geolocation=(), microphone=(), camera=()
```

**Protection Against**
- MIME-type sniffing attacks
- Clickjacking
- Cross-site scripting (XSS)
- Man-in-the-middle attacks
- Information leakage

**Location**: `backend/app/middleware.py`

### 7. Input Validation

**Pydantic Validators**
- Username validation (length, characters)
- Email validation (EmailStr type)
- Password strength validation
- Role and student level validation
- Automatic data sanitization

**Prevents**
- SQL injection (via ORM)
- Code injection
- Invalid data types
- Malformed requests

**Location**: `backend/app/api/auth.py`, `backend/app/api/admin.py`

### 8. Error Handling

**Production Mode**
- Generic error messages (hides internal details)
- Prevents information disclosure
- Logs detailed errors server-side (future enhancement)

**Development Mode**
- Detailed error messages for debugging
- Error type information

**Location**: `backend/app/main.py`

## 🚀 Production Deployment Checklist

### 1. Environment Configuration

Create a `.env` file in `backend/` directory:

```bash
cp backend/.env.example backend/.env
```

**Critical Settings for Production:**

```env
DEBUG=False
SECRET_KEY=<generate-new-key>
ALLOWED_ORIGINS=https://yourdomain.com
DATABASE_URL=postgresql://user:pass@host/dbname
USE_REDIS=True
REDIS_URL=redis://redis-host:6379
RATE_LIMIT_ENABLED=True
RATE_LIMIT_PER_MINUTE=30
```

**Generate Secure Secret Key:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2. Database Setup

**Use PostgreSQL in Production** (not SQLite)

```bash
# Install PostgreSQL driver
pip install psycopg2-binary

# Update DATABASE_URL
DATABASE_URL=postgresql://user:password@localhost:5432/studyplatform
```

**Run Migrations:**
```bash
cd backend
python scripts/init_db.py
```

### 3. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 4. Redis Setup (Recommended)

Redis improves rate limiting and can be used for token blacklisting.

```bash
# Install Redis
sudo apt-get install redis-server  # Ubuntu/Debian
brew install redis                  # macOS

# Start Redis
redis-server

# Update .env
USE_REDIS=True
REDIS_URL=redis://localhost:6379
```

### 5. HTTPS/TLS Configuration

**Never run in production without HTTPS!**

**Option A: Using Nginx Reverse Proxy**

```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Strong SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Option B: Using Uvicorn with SSL**

```bash
uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --ssl-keyfile /path/to/key.pem \
    --ssl-certfile /path/to/cert.pem
```

### 6. Firewall Configuration

```bash
# Allow only necessary ports
sudo ufw allow 80/tcp    # HTTP (redirects to HTTPS)
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

### 7. Process Management

**Using Systemd (Linux)**

Create `/etc/systemd/system/studyplatform.service`:

```ini
[Unit]
Description=Study Platform API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/studyplatform/backend
Environment="PATH=/var/www/studyplatform/venv/bin"
ExecStart=/var/www/studyplatform/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable studyplatform
sudo systemctl start studyplatform
```

**Using Supervisor**

```ini
[program:studyplatform]
command=/path/to/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
directory=/path/to/studyplatform/backend
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/studyplatform/err.log
stdout_logfile=/var/log/studyplatform/out.log
```

### 8. Monitoring & Logging

**Add Logging** (Future Enhancement)

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/studyplatform/app.log'),
        logging.StreamHandler()
    ]
)
```

**Monitor**
- Application logs
- Database connections
- Redis connections
- Rate limit violations
- Failed authentication attempts

### 9. Backup Strategy

**Database Backups**
```bash
# Automated daily backups
0 2 * * * pg_dump studyplatform > /backups/db_$(date +\%Y\%m\%d).sql
```

**Retention Policy**
- Daily backups: 7 days
- Weekly backups: 4 weeks
- Monthly backups: 12 months

### 10. Security Hardening

**Additional Measures:**

1. **Disable API Documentation in Production**
   - Already configured: docs disabled when `DEBUG=False`

2. **Rate Limit Adjustments**
   - Reduce `RATE_LIMIT_PER_MINUTE` to 30 or lower
   - Add stricter limits on auth endpoints

3. **Database User Permissions**
   - Use dedicated database user with minimal privileges
   - No DROP, CREATE USER permissions

4. **Regular Updates**
   ```bash
   pip list --outdated
   pip install --upgrade <package>
   ```

5. **Security Scanning**
   ```bash
   pip install safety
   safety check
   ```

6. **Failed Login Attempt Tracking** (Future Enhancement)
   - Implement account lockout after N failed attempts
   - Use Redis to track attempts

7. **Token Blacklisting** (Future Enhancement)
   - Implement token revocation
   - Store blacklisted tokens in Redis with TTL

## 🔐 Default User Credentials

**After initialization, change these immediately!**

| Username | Password | Role |
|----------|----------|------|
| admin | Admin123! | Admin |
| teacher | Teacher123! | Teacher |
| primary_student | Student123! | Student |
| highschool_student | Student123! | Student |
| university_student | Student123! | Student |

## 📋 Security Incident Response

**If you suspect a security breach:**

1. **Immediate Actions**
   - Rotate SECRET_KEY immediately
   - Revoke all active tokens (requires token blacklisting feature)
   - Check access logs for suspicious activity
   - Temporarily increase rate limits restrictions

2. **Investigation**
   - Review application logs
   - Check database for unauthorized changes
   - Audit user accounts

3. **Recovery**
   - Force password reset for all users
   - Update security policies
   - Patch vulnerabilities

## 📚 Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [bcrypt Explained](https://en.wikipedia.org/wiki/Bcrypt)

## ✅ Security Compliance

This implementation follows:
- OWASP Security Best Practices
- JWT RFC 8725 Recommendations
- CWE Top 25 Mitigation Strategies
- Industry-standard authentication patterns

## 🆘 Support

For security issues, please report to: security@yourdomain.com

**Do not disclose security vulnerabilities publicly!**
