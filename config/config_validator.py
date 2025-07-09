"""
Configuration validation module for Agora Slack app.
Validates configuration settings and environment variables.
"""

import os
import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json

logger = logging.getLogger(__name__)

class ValidationLevel(Enum):
    """Validation severity levels."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

@dataclass
class ValidationResult:
    """Configuration validation result."""
    level: ValidationLevel
    key: str
    message: str
    suggestion: Optional[str] = None

class ConfigValidator:
    """Validates application configuration."""
    
    def __init__(self):
        self.required_vars = {
            'SLACK_BOT_TOKEN': {
                'pattern': r'^xoxb-[0-9]+-[0-9]+-[a-zA-Z0-9]+$',
                'description': 'Slack bot token for API access'
            },
            'SLACK_SIGNING_SECRET': {
                'pattern': r'^[a-f0-9]{64}$',
                'description': 'Slack signing secret for request verification'
            },
            'DATABASE_URL': {
                'pattern': r'^(sqlite:///|postgresql://)',
                'description': 'Database connection URL'
            }
        }
        
        self.optional_vars = {
            'REDIS_URL': {
                'pattern': r'^redis://.*$',
                'description': 'Redis connection URL for caching'
            },
            'SECRET_KEY': {
                'min_length': 32,
                'description': 'Secret key for encryption'
            },
            'LOG_LEVEL': {
                'allowed_values': ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                'description': 'Logging level'
            },
            'PORT': {
                'pattern': r'^[0-9]+$',
                'description': 'Application port number'
            },
            'DEBUG': {
                'allowed_values': ['True', 'False', 'true', 'false', '1', '0'],
                'description': 'Debug mode flag'
            }
        }
        
        self.security_checks = {
            'weak_secret_patterns': [
                r'password',
                r'secret',
                r'123456',
                r'admin',
                r'test',
                r'default'
            ],
            'production_warnings': [
                'DEBUG',
                'development',
                'localhost'
            ]
        }
    
    def validate_all(self) -> List[ValidationResult]:
        """Validate all configuration settings."""
        results = []
        
        # Validate required environment variables
        results.extend(self._validate_required_vars())
        
        # Validate optional environment variables
        results.extend(self._validate_optional_vars())
        
        # Security validations
        results.extend(self._validate_security())
        
        # Database configuration
        results.extend(self._validate_database_config())
        
        # Slack configuration
        results.extend(self._validate_slack_config())
        
        # Production readiness
        results.extend(self._validate_production_readiness())
        
        return results
    
    def _validate_required_vars(self) -> List[ValidationResult]:
        """Validate required environment variables."""
        results = []
        
        for var_name, config in self.required_vars.items():
            value = os.environ.get(var_name)
            
            if not value:
                results.append(ValidationResult(
                    level=ValidationLevel.ERROR,
                    key=var_name,
                    message=f"Required environment variable '{var_name}' is not set",
                    suggestion=f"Set {var_name} to a valid {config['description']}"
                ))
                continue
            
            # Validate pattern if specified
            if 'pattern' in config:
                if not re.match(config['pattern'], value):
                    results.append(ValidationResult(
                        level=ValidationLevel.ERROR,
                        key=var_name,
                        message=f"Environment variable '{var_name}' has invalid format",
                        suggestion=f"Ensure {var_name} matches the expected pattern for {config['description']}"
                    ))
            
            # Validate minimum length if specified
            if 'min_length' in config:
                if len(value) < config['min_length']:
                    results.append(ValidationResult(
                        level=ValidationLevel.ERROR,
                        key=var_name,
                        message=f"Environment variable '{var_name}' is too short (minimum {config['min_length']} characters)",
                        suggestion=f"Use a longer value for {var_name}"
                    ))
        
        return results
    
    def _validate_optional_vars(self) -> List[ValidationResult]:
        """Validate optional environment variables."""
        results = []
        
        for var_name, config in self.optional_vars.items():
            value = os.environ.get(var_name)
            
            if not value:
                continue  # Optional variables can be missing
            
            # Validate pattern if specified
            if 'pattern' in config:
                if not re.match(config['pattern'], value):
                    results.append(ValidationResult(
                        level=ValidationLevel.WARNING,
                        key=var_name,
                        message=f"Optional environment variable '{var_name}' has invalid format",
                        suggestion=f"Ensure {var_name} matches the expected pattern for {config['description']}"
                    ))
            
            # Validate allowed values if specified
            if 'allowed_values' in config:
                if value not in config['allowed_values']:
                    results.append(ValidationResult(
                        level=ValidationLevel.WARNING,
                        key=var_name,
                        message=f"Environment variable '{var_name}' has invalid value '{value}'",
                        suggestion=f"Use one of: {', '.join(config['allowed_values'])}"
                    ))
            
            # Validate minimum length if specified
            if 'min_length' in config:
                if len(value) < config['min_length']:
                    results.append(ValidationResult(
                        level=ValidationLevel.WARNING,
                        key=var_name,
                        message=f"Environment variable '{var_name}' is too short (minimum {config['min_length']} characters)",
                        suggestion=f"Use a longer value for {var_name}"
                    ))
        
        return results
    
    def _validate_security(self) -> List[ValidationResult]:
        """Validate security-related configuration."""
        results = []
        
        # Check for weak secrets
        secret_vars = ['SECRET_KEY', 'SLACK_SIGNING_SECRET', 'POSTGRES_PASSWORD', 'REDIS_PASSWORD']
        
        for var_name in secret_vars:
            value = os.environ.get(var_name)
            if not value:
                continue
            
            # Check for weak patterns
            value_lower = value.lower()
            for pattern in self.security_checks['weak_secret_patterns']:
                if pattern in value_lower:
                    results.append(ValidationResult(
                        level=ValidationLevel.ERROR,
                        key=var_name,
                        message=f"Security risk: '{var_name}' contains weak pattern '{pattern}'",
                        suggestion=f"Use a strong, randomly generated value for {var_name}"
                    ))
                    break
            
            # Check minimum complexity
            if len(value) < 16:
                results.append(ValidationResult(
                    level=ValidationLevel.WARNING,
                    key=var_name,
                    message=f"Security warning: '{var_name}' is shorter than recommended (16+ characters)",
                    suggestion=f"Use a longer, more complex value for {var_name}"
                ))
        
        # Check for production warnings in values
        for var_name, value in os.environ.items():
            if not value:
                continue
            
            value_lower = value.lower()
            for warning_pattern in self.security_checks['production_warnings']:
                if warning_pattern.lower() in value_lower:
                    results.append(ValidationResult(
                        level=ValidationLevel.WARNING,
                        key=var_name,
                        message=f"Production warning: '{var_name}' contains development pattern '{warning_pattern}'",
                        suggestion=f"Review {var_name} for production deployment"
                    ))
                    break
        
        return results
    
    def _validate_database_config(self) -> List[ValidationResult]:
        """Validate database configuration."""
        results = []
        
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            return results  # Already handled in required vars
        
        # Check database type
        if database_url.startswith('sqlite:///'):
            results.append(ValidationResult(
                level=ValidationLevel.INFO,
                key='DATABASE_URL',
                message="Using SQLite database (suitable for development)",
                suggestion="Consider PostgreSQL for production deployment"
            ))
            
            # Check SQLite file path
            db_path = database_url.replace('sqlite:///', '')
            if not db_path or db_path == ':memory:':
                results.append(ValidationResult(
                    level=ValidationLevel.WARNING,
                    key='DATABASE_URL',
                    message="Using in-memory SQLite database (data will be lost on restart)",
                    suggestion="Use a file-based SQLite database or PostgreSQL"
                ))
        
        elif database_url.startswith('postgresql://'):
            results.append(ValidationResult(
                level=ValidationLevel.INFO,
                key='DATABASE_URL',
                message="Using PostgreSQL database (recommended for production)",
                suggestion=None
            ))
            
            # Check SSL mode for PostgreSQL
            if 'sslmode=' not in database_url:
                results.append(ValidationResult(
                    level=ValidationLevel.WARNING,
                    key='DATABASE_URL',
                    message="PostgreSQL connection does not specify SSL mode",
                    suggestion="Add '?sslmode=require' to DATABASE_URL for secure connections"
                ))
        
        else:
            results.append(ValidationResult(
                level=ValidationLevel.ERROR,
                key='DATABASE_URL',
                message="Unsupported database type in DATABASE_URL",
                suggestion="Use SQLite (sqlite:///) or PostgreSQL (postgresql://)"
            ))
        
        return results
    
    def _validate_slack_config(self) -> List[ValidationResult]:
        """Validate Slack-specific configuration."""
        results = []
        
        bot_token = os.environ.get('SLACK_BOT_TOKEN')
        if bot_token:
            # Check token format
            if not bot_token.startswith('xoxb-'):
                results.append(ValidationResult(
                    level=ValidationLevel.ERROR,
                    key='SLACK_BOT_TOKEN',
                    message="SLACK_BOT_TOKEN does not appear to be a bot token",
                    suggestion="Ensure you're using a bot token (starts with 'xoxb-')"
                ))
            
            # Check token structure
            parts = bot_token.split('-')
            if len(parts) != 4:
                results.append(ValidationResult(
                    level=ValidationLevel.WARNING,
                    key='SLACK_BOT_TOKEN',
                    message="SLACK_BOT_TOKEN has unexpected format",
                    suggestion="Verify the token format from Slack app configuration"
                ))
        
        signing_secret = os.environ.get('SLACK_SIGNING_SECRET')
        if signing_secret:
            # Check signing secret length and format
            if len(signing_secret) != 64:
                results.append(ValidationResult(
                    level=ValidationLevel.ERROR,
                    key='SLACK_SIGNING_SECRET',
                    message="SLACK_SIGNING_SECRET should be exactly 64 characters",
                    suggestion="Copy the signing secret exactly from Slack app configuration"
                ))
            
            if not re.match(r'^[a-f0-9]+$', signing_secret):
                results.append(ValidationResult(
                    level=ValidationLevel.ERROR,
                    key='SLACK_SIGNING_SECRET',
                    message="SLACK_SIGNING_SECRET should contain only lowercase hex characters",
                    suggestion="Verify the signing secret from Slack app configuration"
                ))
        
        return results
    
    def _validate_production_readiness(self) -> List[ValidationResult]:
        """Validate production readiness."""
        results = []
        
        # Check debug mode
        debug = os.environ.get('DEBUG', 'False').lower()
        if debug in ['true', '1', 'yes']:
            results.append(ValidationResult(
                level=ValidationLevel.WARNING,
                key='DEBUG',
                message="Debug mode is enabled",
                suggestion="Set DEBUG=False for production deployment"
            ))
        
        # Check log level
        log_level = os.environ.get('LOG_LEVEL', 'INFO')
        if log_level == 'DEBUG':
            results.append(ValidationResult(
                level=ValidationLevel.INFO,
                key='LOG_LEVEL',
                message="Log level is set to DEBUG",
                suggestion="Consider using INFO or WARNING for production"
            ))
        
        # Check for localhost URLs
        url_vars = ['DATABASE_URL', 'REDIS_URL']
        for var_name in url_vars:
            value = os.environ.get(var_name)
            if value and 'localhost' in value:
                results.append(ValidationResult(
                    level=ValidationLevel.WARNING,
                    key=var_name,
                    message=f"{var_name} points to localhost",
                    suggestion=f"Use appropriate production URL for {var_name}"
                ))
        
        # Check for required production variables
        prod_vars = ['SECRET_KEY']
        for var_name in prod_vars:
            value = os.environ.get(var_name)
            if not value:
                results.append(ValidationResult(
                    level=ValidationLevel.WARNING,
                    key=var_name,
                    message=f"Production variable '{var_name}' is not set",
                    suggestion=f"Set {var_name} for production deployment"
                ))
        
        return results
    
    def validate_config_file(self, file_path: str) -> List[ValidationResult]:
        """Validate configuration from a JSON file."""
        results = []
        
        try:
            with open(file_path, 'r') as f:
                config = json.load(f)
            
            # Validate structure
            if not isinstance(config, dict):
                results.append(ValidationResult(
                    level=ValidationLevel.ERROR,
                    key='config_file',
                    message="Configuration file must contain a JSON object",
                    suggestion="Ensure the file contains valid JSON object"
                ))
                return results
            
            # Validate known configuration keys
            known_keys = set(self.required_vars.keys()) | set(self.optional_vars.keys())
            unknown_keys = set(config.keys()) - known_keys
            
            if unknown_keys:
                results.append(ValidationResult(
                    level=ValidationLevel.INFO,
                    key='config_file',
                    message=f"Unknown configuration keys: {', '.join(unknown_keys)}",
                    suggestion="Remove unknown keys or verify they are needed"
                ))
            
            # Validate each configuration value
            for key, value in config.items():
                if key in self.required_vars:
                    var_config = self.required_vars[key]
                elif key in self.optional_vars:
                    var_config = self.optional_vars[key]
                else:
                    continue
                
                # Validate pattern
                if 'pattern' in var_config and not re.match(var_config['pattern'], str(value)):
                    results.append(ValidationResult(
                        level=ValidationLevel.ERROR,
                        key=key,
                        message=f"Configuration value for '{key}' has invalid format",
                        suggestion=f"Ensure {key} matches the expected pattern"
                    ))
                
                # Validate allowed values
                if 'allowed_values' in var_config and str(value) not in var_config['allowed_values']:
                    results.append(ValidationResult(
                        level=ValidationLevel.ERROR,
                        key=key,
                        message=f"Configuration value for '{key}' is not allowed",
                        suggestion=f"Use one of: {', '.join(var_config['allowed_values'])}"
                    ))
        
        except FileNotFoundError:
            results.append(ValidationResult(
                level=ValidationLevel.ERROR,
                key='config_file',
                message=f"Configuration file not found: {file_path}",
                suggestion="Create the configuration file or check the path"
            ))
        
        except json.JSONDecodeError as e:
            results.append(ValidationResult(
                level=ValidationLevel.ERROR,
                key='config_file',
                message=f"Invalid JSON in configuration file: {e}",
                suggestion="Fix JSON syntax errors in the configuration file"
            ))
        
        except Exception as e:
            results.append(ValidationResult(
                level=ValidationLevel.ERROR,
                key='config_file',
                message=f"Error reading configuration file: {e}",
                suggestion="Check file permissions and format"
            ))
        
        return results
    
    def generate_report(self, results: List[ValidationResult]) -> str:
        """Generate a human-readable validation report."""
        if not results:
            return "✅ All configuration validation checks passed!"
        
        # Group results by severity
        errors = [r for r in results if r.level == ValidationLevel.ERROR]
        warnings = [r for r in results if r.level == ValidationLevel.WARNING]
        info = [r for r in results if r.level == ValidationLevel.INFO]
        
        report = []
        
        if errors:
            report.append("🚨 ERRORS (must be fixed):")
            for error in errors:
                report.append(f"  ❌ {error.key}: {error.message}")
                if error.suggestion:
                    report.append(f"     💡 {error.suggestion}")
            report.append("")
        
        if warnings:
            report.append("⚠️ WARNINGS (should be addressed):")
            for warning in warnings:
                report.append(f"  ⚠️ {warning.key}: {warning.message}")
                if warning.suggestion:
                    report.append(f"     💡 {warning.suggestion}")
            report.append("")
        
        if info:
            report.append("ℹ️ INFORMATION:")
            for info_item in info:
                report.append(f"  ℹ️ {info_item.key}: {info_item.message}")
                if info_item.suggestion:
                    report.append(f"     💡 {info_item.suggestion}")
            report.append("")
        
        # Summary
        report.append(f"Summary: {len(errors)} errors, {len(warnings)} warnings, {len(info)} info items")
        
        return "\n".join(report)

# Global validator instance
config_validator = ConfigValidator()

# Utility functions
def validate_configuration() -> Tuple[bool, str]:
    """Validate configuration and return success status with report."""
    results = config_validator.validate_all()
    
    # Check if there are any errors
    has_errors = any(r.level == ValidationLevel.ERROR for r in results)
    
    # Generate report
    report = config_validator.generate_report(results)
    
    return not has_errors, report

def validate_config_file(file_path: str) -> Tuple[bool, str]:
    """Validate configuration file and return success status with report."""
    results = config_validator.validate_config_file(file_path)
    
    # Check if there are any errors
    has_errors = any(r.level == ValidationLevel.ERROR for r in results)
    
    # Generate report
    report = config_validator.generate_report(results)
    
    return not has_errors, report

def get_configuration_status() -> Dict[str, Any]:
    """Get configuration validation status as structured data."""
    results = config_validator.validate_all()
    
    return {
        'valid': not any(r.level == ValidationLevel.ERROR for r in results),
        'errors': [{'key': r.key, 'message': r.message, 'suggestion': r.suggestion} 
                  for r in results if r.level == ValidationLevel.ERROR],
        'warnings': [{'key': r.key, 'message': r.message, 'suggestion': r.suggestion} 
                    for r in results if r.level == ValidationLevel.WARNING],
        'info': [{'key': r.key, 'message': r.message, 'suggestion': r.suggestion} 
                for r in results if r.level == ValidationLevel.INFO],
        'total_issues': len(results)
    }