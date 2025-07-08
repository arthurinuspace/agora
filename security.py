"""
Security audit and implementation module for Agora Slack app.
Includes security validation, threat detection, and protection mechanisms.
"""

import hashlib
import hmac
import secrets
import time
import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import json
from dataclasses import dataclass
from config import Config

logger = logging.getLogger(__name__)

@dataclass
class SecurityEvent:
    """Security event data structure."""
    event_type: str
    severity: str
    description: str
    source_ip: str
    user_id: Optional[str]
    team_id: Optional[str]
    timestamp: datetime
    details: Dict[str, Any]

class SecurityValidator:
    """Validates security aspects of requests and data."""
    
    @staticmethod
    def validate_slack_signature(body: bytes, timestamp: str, signature: str) -> bool:
        """Validate Slack request signature."""
        try:
            if not Config.SLACK_SIGNING_SECRET:
                logger.error("Slack signing secret not configured")
                return False
            
            # Check timestamp freshness (prevent replay attacks)
            current_time = int(time.time())
            request_time = int(timestamp)
            
            if abs(current_time - request_time) > 300:  # 5 minutes
                logger.warning(f"Request timestamp too old: {request_time}")
                return False
            
            # Verify signature
            version = 'v0'
            basestring = f"{version}:{timestamp}:{body.decode('utf-8')}"
            
            computed_signature = 'v0=' + hmac.new(
                Config.SLACK_SIGNING_SECRET.encode(),
                basestring.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(computed_signature, signature)
            
        except Exception as e:
            logger.error(f"Signature validation error: {e}")
            return False
    
    @staticmethod
    def validate_input_data(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate input data for security issues."""
        errors = []
        
        # Check for SQL injection patterns
        sql_patterns = [
            r"('|(\\'))|(;|--|/\\*|\\*/)",
            r"(union|select|insert|update|delete|drop|create|alter)",
            r"(script|javascript|vbscript|onload|onerror)"
        ]
        
        def check_value(value: Any, key: str = ""):
            if isinstance(value, str):
                for pattern in sql_patterns:
                    if re.search(pattern, value, re.IGNORECASE):
                        errors.append(f"Potential injection attempt in field '{key}': {pattern}")
                
                # Check for XSS patterns
                xss_patterns = [
                    r"<script",
                    r"javascript:",
                    r"on\w+\s*=",
                    r"<iframe",
                    r"<object",
                    r"<embed"
                ]
                
                for pattern in xss_patterns:
                    if re.search(pattern, value, re.IGNORECASE):
                        errors.append(f"Potential XSS attempt in field '{key}': {pattern}")
            
            elif isinstance(value, dict):
                for k, v in value.items():
                    check_value(v, f"{key}.{k}" if key else k)
            
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    check_value(item, f"{key}[{i}]" if key else f"[{i}]")
        
        check_value(data)
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_user_permissions(user_id: str, team_id: str, required_permission: str) -> bool:
        """Validate user permissions for requested action."""
        try:
            from performance import OptimizedQueries
            from models import SessionLocal
            
            with SessionLocal() as db:
                user_role = OptimizedQueries.get_user_role(db, user_id, team_id)
                
                # Define permission hierarchy
                permissions = {
                    'viewer': ['view_polls'],
                    'user': ['view_polls', 'create_polls', 'vote'],
                    'admin': ['view_polls', 'create_polls', 'vote', 'manage_users', 'manage_settings', 'delete_polls']
                }
                
                user_permissions = permissions.get(user_role, permissions['user'])
                return required_permission in user_permissions
                
        except Exception as e:
            logger.error(f"Permission validation error: {e}")
            return False
    
    @staticmethod
    def sanitize_input(data: str) -> str:
        """Sanitize input data to prevent injection attacks."""
        if not isinstance(data, str):
            return data
        
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>&"\']', '', data)
        
        # Limit length
        if len(sanitized) > 10000:
            sanitized = sanitized[:10000]
        
        return sanitized.strip()

class EncryptionManager:
    """Handles encryption and decryption of sensitive data."""
    
    def __init__(self):
        self.key = self._derive_key()
        self.cipher = Fernet(self.key)
    
    def _derive_key(self) -> bytes:
        """Derive encryption key from configuration."""
        # Use a combination of secret key and salt
        password = getattr(Config, 'SECRET_KEY', 'default-secret-key').encode()
        salt = b'agora-salt-2024'  # In production, use random salt stored securely
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        return base64.urlsafe_b64encode(kdf.derive(password))
    
    def encrypt(self, data: str) -> str:
        """Encrypt sensitive data."""
        try:
            encrypted = self.cipher.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Encryption error: {e}")
            raise
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt sensitive data."""
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self.cipher.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            raise

class ThreatDetector:
    """Detects and analyzes security threats."""
    
    def __init__(self):
        self.failed_attempts = {}  # IP -> count
        self.suspicious_patterns = []
        self.rate_limits = {}  # IP -> last request time
    
    def detect_brute_force(self, ip_address: str, success: bool) -> bool:
        """Detect brute force attacks."""
        if success:
            # Reset counter on successful authentication
            self.failed_attempts.pop(ip_address, None)
            return False
        
        # Increment failed attempts
        attempts = self.failed_attempts.get(ip_address, 0) + 1
        self.failed_attempts[ip_address] = attempts
        
        # Check threshold
        if attempts >= 5:  # 5 failed attempts
            logger.warning(f"Brute force detected from IP: {ip_address}")
            return True
        
        return False
    
    def detect_rate_limiting_abuse(self, ip_address: str, current_time: float) -> bool:
        """Detect rate limiting abuse."""
        last_request = self.rate_limits.get(ip_address, 0)
        
        # Check if requests are too frequent (less than 1 second apart)
        if current_time - last_request < 1.0:
            logger.warning(f"Rate limiting abuse detected from IP: {ip_address}")
            return True
        
        self.rate_limits[ip_address] = current_time
        return False
    
    def detect_suspicious_patterns(self, request_data: Dict[str, Any]) -> List[str]:
        """Detect suspicious patterns in request data."""
        threats = []
        
        # Check for common attack patterns
        data_str = json.dumps(request_data).lower()
        
        suspicious_patterns = [
            ('sql_injection', r'(union|select|insert|update|delete).*(from|where)'),
            ('xss_attempt', r'<script|javascript:|on\w+\s*='),
            ('path_traversal', r'\.\./|\.\.\\\|%2e%2e'),
            ('command_injection', r'[;&|`$(){}[\]]'),
            ('ldap_injection', r'[()&|!*]'),
        ]
        
        for threat_type, pattern in suspicious_patterns:
            if re.search(pattern, data_str):
                threats.append(threat_type)
                logger.warning(f"Suspicious pattern detected: {threat_type}")
        
        return threats
    
    def analyze_request_anomalies(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze request for anomalies."""
        anomalies = {
            'unusual_size': False,
            'unusual_fields': False,
            'suspicious_content': False
        }
        
        # Check request size
        data_size = len(json.dumps(request_data))
        if data_size > 50000:  # 50KB
            anomalies['unusual_size'] = True
        
        # Check for unusual fields
        expected_fields = ['type', 'user', 'team', 'channel', 'text', 'token']
        unexpected_fields = set(request_data.keys()) - set(expected_fields)
        if len(unexpected_fields) > 5:
            anomalies['unusual_fields'] = True
        
        # Check for suspicious content
        threats = self.detect_suspicious_patterns(request_data)
        if threats:
            anomalies['suspicious_content'] = True
        
        return anomalies

class SecurityAuditor:
    """Performs security audits and generates reports."""
    
    def __init__(self):
        self.security_events = []
        self.encryption_manager = EncryptionManager()
        self.threat_detector = ThreatDetector()
    
    def log_security_event(self, event: SecurityEvent):
        """Log a security event."""
        self.security_events.append(event)
        
        # Log to application logs
        logger.warning(
            f"Security Event: {event.event_type} - {event.description}",
            extra={
                'security_event': True,
                'event_type': event.event_type,
                'severity': event.severity,
                'source_ip': event.source_ip,
                'user_id': event.user_id,
                'team_id': event.team_id
            }
        )
    
    def audit_configuration(self) -> Dict[str, Any]:
        """Audit application configuration for security issues."""
        findings = {
            'critical': [],
            'high': [],
            'medium': [],
            'low': []
        }
        
        # Check for missing security configurations
        if not hasattr(Config, 'SLACK_SIGNING_SECRET') or not Config.SLACK_SIGNING_SECRET:
            findings['critical'].append('Slack signing secret not configured')
        
        if not hasattr(Config, 'SECRET_KEY') or Config.SECRET_KEY == 'default-secret-key':
            findings['high'].append('Default secret key being used')
        
        if getattr(Config, 'DEBUG', False):
            findings['medium'].append('Debug mode enabled in production')
        
        if not getattr(Config, 'DATABASE_URL', '').startswith('postgresql'):
            findings['low'].append('Not using PostgreSQL in production')
        
        # Check environment variables
        sensitive_vars = ['SLACK_BOT_TOKEN', 'SLACK_SIGNING_SECRET', 'DATABASE_URL']
        for var in sensitive_vars:
            if not os.environ.get(var):
                findings['medium'].append(f'Sensitive variable {var} not in environment')
        
        return findings
    
    def audit_database_security(self) -> Dict[str, Any]:
        """Audit database security configuration."""
        findings = {
            'critical': [],
            'high': [],
            'medium': [],
            'low': []
        }
        
        try:
            from models import engine
            
            # Check database connection encryption
            if not Config.DATABASE_URL.startswith('postgresql'):
                findings['medium'].append('Database not using PostgreSQL')
            elif 'sslmode=require' not in Config.DATABASE_URL:
                findings['high'].append('Database connection not using SSL')
            
            # Check for weak passwords (if we can access them)
            # Note: In production, passwords shouldn't be accessible
            
            return findings
            
        except Exception as e:
            logger.error(f"Database security audit error: {e}")
            findings['critical'].append(f'Database audit failed: {e}')
            return findings
    
    def audit_api_security(self) -> Dict[str, Any]:
        """Audit API security implementation."""
        findings = {
            'critical': [],
            'high': [],
            'medium': [],
            'low': []
        }
        
        # Check for security headers implementation
        # This would be checked during runtime
        
        # Check for rate limiting
        try:
            from api_middleware import RateLimiter
            findings['low'].append('Rate limiting implemented')
        except ImportError:
            findings['high'].append('Rate limiting not implemented')
        
        # Check for input validation
        try:
            from api_middleware import RequestValidator
            findings['low'].append('Input validation implemented')
        except ImportError:
            findings['high'].append('Input validation not implemented')
        
        return findings
    
    def generate_security_report(self) -> Dict[str, Any]:
        """Generate comprehensive security audit report."""
        report = {
            'audit_timestamp': datetime.utcnow().isoformat(),
            'configuration_audit': self.audit_configuration(),
            'database_audit': self.audit_database_security(),
            'api_audit': self.audit_api_security(),
            'recent_events': [
                {
                    'event_type': event.event_type,
                    'severity': event.severity,
                    'description': event.description,
                    'timestamp': event.timestamp.isoformat()
                }
                for event in self.security_events[-50:]  # Last 50 events
            ],
            'recommendations': self._generate_recommendations()
        }
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate security recommendations based on audit findings."""
        recommendations = [
            "Regularly rotate API keys and secrets",
            "Enable database connection encryption",
            "Implement comprehensive input validation",
            "Monitor for suspicious activity patterns",
            "Keep dependencies updated to latest secure versions",
            "Implement proper session management",
            "Use secure headers in HTTP responses",
            "Regularly backup encrypted data",
            "Implement proper error handling to avoid information disclosure",
            "Use environment variables for all sensitive configuration"
        ]
        
        return recommendations

class SecurityMiddleware:
    """Security middleware for request processing."""
    
    def __init__(self):
        self.validator = SecurityValidator()
        self.auditor = SecurityAuditor()
        self.threat_detector = ThreatDetector()
    
    def process_request(self, request_data: Dict[str, Any], source_ip: str) -> Tuple[bool, List[str]]:
        """Process request through security checks."""
        issues = []
        
        # Validate input data
        is_valid, validation_errors = self.validator.validate_input_data(request_data)
        if not is_valid:
            issues.extend(validation_errors)
        
        # Detect threats
        threats = self.threat_detector.detect_suspicious_patterns(request_data)
        if threats:
            issues.extend([f"Threat detected: {threat}" for threat in threats])
        
        # Check for brute force
        if self.threat_detector.detect_brute_force(source_ip, is_valid):
            issues.append("Brute force attack detected")
        
        # Check for rate limiting abuse
        if self.threat_detector.detect_rate_limiting_abuse(source_ip, time.time()):
            issues.append("Rate limiting abuse detected")
        
        # Log security event if issues found
        if issues:
            event = SecurityEvent(
                event_type="security_violation",
                severity="high" if any("injection" in issue.lower() for issue in issues) else "medium",
                description=f"Security issues detected: {', '.join(issues[:3])}",
                source_ip=source_ip,
                user_id=request_data.get('user_id'),
                team_id=request_data.get('team_id'),
                timestamp=datetime.utcnow(),
                details={'issues': issues, 'request_data': request_data}
            )
            self.auditor.log_security_event(event)
        
        return len(issues) == 0, issues
    
    def sanitize_response(self, response_data: Any) -> Any:
        """Sanitize response data to prevent information disclosure."""
        if isinstance(response_data, dict):
            # Remove sensitive fields
            sensitive_fields = ['password', 'secret', 'token', 'key', 'private']
            sanitized = {}
            
            for key, value in response_data.items():
                if any(sensitive in key.lower() for sensitive in sensitive_fields):
                    sanitized[key] = "***REDACTED***"
                else:
                    sanitized[key] = self.sanitize_response(value)
            
            return sanitized
        
        elif isinstance(response_data, list):
            return [self.sanitize_response(item) for item in response_data]
        
        else:
            return response_data

# Global security instances
security_middleware = SecurityMiddleware()
security_auditor = SecurityAuditor()
encryption_manager = EncryptionManager()

# Security utility functions
def validate_slack_signature(body: bytes, timestamp: str, signature: str) -> bool:
    """Validate Slack request signature."""
    return SecurityValidator.validate_slack_signature(body, timestamp, signature)

def check_user_permissions(user_id: str, team_id: str, permission: str) -> bool:
    """Check user permissions."""
    return SecurityValidator.validate_user_permissions(user_id, team_id, permission)

def sanitize_input(data: str) -> str:
    """Sanitize input data."""
    return SecurityValidator.sanitize_input(data)

def encrypt_sensitive_data(data: str) -> str:
    """Encrypt sensitive data."""
    return encryption_manager.encrypt(data)

def decrypt_sensitive_data(encrypted_data: str) -> str:
    """Decrypt sensitive data."""
    return encryption_manager.decrypt(encrypted_data)

def generate_security_report() -> Dict[str, Any]:
    """Generate security audit report."""
    return security_auditor.generate_security_report()

def process_request_security(request_data: Dict[str, Any], source_ip: str) -> Tuple[bool, List[str]]:
    """Process request through security middleware."""
    return security_middleware.process_request(request_data, source_ip)

# Import os for environment variable checking
import os