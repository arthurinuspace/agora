# Security Guide

## 🛡️ Security Overview

Agora implements enterprise-grade security measures to protect user data, ensure privacy, and maintain system integrity.

## 🔒 Authentication & Authorization

### Slack OAuth Integration

```python
# OAuth flow implementation
from slack_sdk.oauth import OAuthFlow

# Initialize OAuth flow
oauth_flow = OAuthFlow(
    client_id="your-client-id",
    client_secret="your-client-secret",
    scopes=["commands", "chat:write", "users:read"]
)

# Handle authorization
token_response = oauth_flow.run_flow(
    authorization_code=auth_code,
    redirect_uri="https://your-domain.com/auth/callback"
)
```

### Token Management

- **Secure Storage**: All tokens encrypted at rest
- **Token Rotation**: Automatic refresh of expired tokens
- **Scope Limitation**: Minimal required permissions
- **Revocation**: Immediate token invalidation on logout

### Role-Based Access Control (RBAC)

```python
# Role definitions
class UserRole(enum.Enum):
    USER = "user"        # Basic poll creation and voting
    ADMIN = "admin"      # Workspace management
    SUPER_ADMIN = "super_admin"  # System administration

# Permission checking
def require_permission(permission: str):
    def decorator(func):
        def wrapper(current_user, *args, **kwargs):
            if not current_user.has_permission(permission):
                raise PermissionError("Insufficient permissions")
            return func(current_user, *args, **kwargs)
        return wrapper
    return decorator
```

## 🔐 Data Protection

### Encryption

#### Data at Rest
```python
# Database encryption
from cryptography.fernet import Fernet

class EncryptedField:
    def __init__(self, key: bytes):
        self.cipher = Fernet(key)
    
    def encrypt(self, data: str) -> str:
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        return self.cipher.decrypt(encrypted_data.encode()).decode()
```

#### Data in Transit
- **TLS 1.3**: All API communications encrypted
- **Certificate Pinning**: Prevent man-in-the-middle attacks
- **HSTS**: Force HTTPS connections

### Anonymity Protection

```python
# Anonymous voting implementation
class AnonymousVote:
    def __init__(self, poll_id: str, option_id: str):
        self.poll_id = poll_id
        self.option_id = option_id
        self.vote_hash = self._generate_hash()
        # No user_id stored for anonymous votes
    
    def _generate_hash(self) -> str:
        # Generate unique hash without user identification
        return hashlib.sha256(
            f"{self.poll_id}:{self.option_id}:{time.time()}".encode()
        ).hexdigest()
```

## 🚨 Request Validation

### Slack Request Verification

```python
import hmac
import hashlib
from datetime import datetime

def verify_slack_request(request_body: str, headers: dict) -> bool:
    """Verify Slack request signature"""
    slack_signature = headers.get('X-Slack-Signature')
    slack_timestamp = headers.get('X-Slack-Request-Timestamp')
    
    # Check timestamp (prevent replay attacks)
    if abs(datetime.now().timestamp() - int(slack_timestamp)) > 300:
        return False
    
    # Verify signature
    expected_signature = 'v0=' + hmac.new(
        SLACK_SIGNING_SECRET.encode(),
        f"v0:{slack_timestamp}:{request_body}".encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected_signature, slack_signature)
```

### Input Validation

```python
from pydantic import BaseModel, validator

class PollCreateRequest(BaseModel):
    question: str
    options: list[str]
    anonymous: bool = True
    
    @validator('question')
    def validate_question(cls, v):
        if len(v) < 5 or len(v) > 500:
            raise ValueError('Question must be 5-500 characters')
        return v
    
    @validator('options')
    def validate_options(cls, v):
        if len(v) < 2 or len(v) > 20:
            raise ValueError('Must have 2-20 options')
        return v
```

## 🛡️ Security Measures

### Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

# Rate limiting configuration
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute", "1000/hour"]
)

# Apply to endpoints
@app.post("/api/polls")
@limiter.limit("10/minute")
async def create_poll(request: Request, poll_data: PollCreateRequest):
    # Poll creation logic
    pass
```

### SQL Injection Prevention

```python
from sqlalchemy import text

# Use parameterized queries
def get_poll_by_id(poll_id: str) -> Poll:
    query = text("SELECT * FROM polls WHERE id = :poll_id")
    result = db.execute(query, {"poll_id": poll_id})
    return result.fetchone()

# ORM usage (automatically parameterized)
def get_user_polls(user_id: str) -> list[Poll]:
    return db.query(Poll).filter(Poll.creator_id == user_id).all()
```

### Cross-Site Scripting (XSS) Prevention

```python
import html
from markupsafe import Markup

def sanitize_input(user_input: str) -> str:
    """Sanitize user input to prevent XSS"""
    # HTML escape
    escaped = html.escape(user_input)
    
    # Remove dangerous patterns
    dangerous_patterns = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*='
    ]
    
    for pattern in dangerous_patterns:
        escaped = re.sub(pattern, '', escaped, flags=re.IGNORECASE)
    
    return escaped
```

## 🔍 Security Monitoring

### Audit Logging

```python
import logging
from datetime import datetime

# Security audit logger
security_logger = logging.getLogger('agora.security')

def log_security_event(event_type: str, user_id: str, details: dict):
    """Log security-related events"""
    security_logger.info(
        f"Security Event: {event_type}",
        extra={
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "event_type": event_type,
            "details": details,
            "ip_address": get_client_ip()
        }
    )
```

### Intrusion Detection

```python
class SecurityMonitor:
    def __init__(self):
        self.failed_attempts = defaultdict(int)
        self.suspicious_patterns = {
            'rapid_voting': 10,  # votes per minute
            'bulk_poll_creation': 5,  # polls per hour
            'failed_auth': 5  # failed attempts per hour
        }
    
    def check_suspicious_activity(self, user_id: str, action: str):
        key = f"{user_id}:{action}"
        self.failed_attempts[key] += 1
        
        if self.failed_attempts[key] > self.suspicious_patterns.get(action, 10):
            self.trigger_security_alert(user_id, action)
```

## 📊 Compliance & Privacy

### GDPR Compliance

```python
class GDPRManager:
    def export_user_data(self, user_id: str) -> dict:
        """Export all user data for GDPR compliance"""
        return {
            'user_profile': self.get_user_profile(user_id),
            'polls_created': self.get_user_polls(user_id),
            'votes_cast': self.get_user_votes(user_id, anonymous=False),
            'activity_logs': self.get_user_activity(user_id)
        }
    
    def delete_user_data(self, user_id: str):
        """Delete all user data (right to be forgotten)"""
        # Anonymize votes (keep poll data integrity)
        self.anonymize_user_votes(user_id)
        
        # Delete personal data
        self.delete_user_profile(user_id)
        self.delete_user_polls(user_id)
        self.delete_user_activity(user_id)
```

### Data Retention

```python
class DataRetentionManager:
    def __init__(self):
        self.retention_periods = {
            'polls': 365,  # days
            'votes': 365,
            'audit_logs': 1095,  # 3 years
            'access_logs': 90
        }
    
    def cleanup_expired_data(self):
        """Remove data past retention period"""
        for data_type, days in self.retention_periods.items():
            cutoff_date = datetime.now() - timedelta(days=days)
            self.delete_old_data(data_type, cutoff_date)
```

## 🚫 Incident Response

### Security Incident Handling

```python
class IncidentResponse:
    def handle_security_incident(self, incident_type: str, details: dict):
        """Handle security incidents"""
        # 1. Log incident
        self.log_incident(incident_type, details)
        
        # 2. Assess severity
        severity = self.assess_severity(incident_type, details)
        
        # 3. Take immediate action
        if severity == 'HIGH':
            self.lockdown_affected_accounts(details.get('user_ids', []))
        
        # 4. Notify administrators
        self.notify_admins(incident_type, severity, details)
        
        # 5. Start investigation
        self.initiate_investigation(incident_type, details)
```

### Disaster Recovery

```yaml
# Backup strategy
backup_strategy:
  database:
    frequency: daily
    retention: 30d
    encryption: AES-256
    location: encrypted_s3_bucket
  
  application_data:
    frequency: hourly
    retention: 7d
    type: incremental
  
  configuration:
    frequency: on_change
    retention: 365d
    versioning: enabled
```

## 🔧 Security Configuration

### Environment Variables

```bash
# Security-related environment variables
SLACK_SIGNING_SECRET=your-slack-signing-secret
SECRET_KEY=your-application-secret-key
ENCRYPTION_KEY=your-data-encryption-key

# Database security
DATABASE_SSL_MODE=require
DATABASE_SSL_CERT=/path/to/client-cert.pem

# Rate limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_STORAGE=redis://localhost:6379

# CORS settings
CORS_ORIGINS=https://your-domain.com,https://slack.com
CORS_METHODS=GET,POST,PUT,DELETE
```

### Security Headers

```python
# Security headers middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    expose_headers=["X-RateLimit-Remaining"]
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["your-domain.com", "*.your-domain.com"]
)
```

## 📚 Security Best Practices

### Development Guidelines

1. **Input Validation**: Always validate and sanitize user input
2. **Principle of Least Privilege**: Grant minimum required permissions
3. **Defense in Depth**: Implement multiple security layers
4. **Fail Securely**: Default to secure behavior on errors
5. **Regular Updates**: Keep dependencies and libraries updated

### Deployment Security

```dockerfile
# Secure Dockerfile practices
FROM python:3.12-slim

# Create non-root user
RUN groupadd -r agora && useradd -r -g agora agora

# Install security updates
RUN apt-get update && apt-get upgrade -y

# Set secure file permissions
COPY --chown=agora:agora . /app
USER agora

# Run with limited capabilities
RUN setcap 'cap_net_bind_service=+ep' /usr/local/bin/python
```

## See Also

- [Configuration Guide](configuration.md)
- [Admin Guide](admin.md)
- [API Documentation](api.md)
- [Development Setup](development/setup.md)
