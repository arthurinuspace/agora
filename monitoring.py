"""
Comprehensive logging and monitoring system for Agora Slack app.
Includes structured logging, metrics collection, health checks, and alerting.
"""

import logging
import logging.handlers
import time
import json
import threading
import psutil
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from functools import wraps
from contextlib import contextmanager
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import prometheus_client
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest
import redis
from config import Config

# Configure structured logging
class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'team_id'):
            log_data['team_id'] = record.team_id
        if hasattr(record, 'poll_id'):
            log_data['poll_id'] = record.poll_id
        if hasattr(record, 'duration'):
            log_data['duration'] = record.duration
        if hasattr(record, 'error_type'):
            log_data['error_type'] = record.error_type
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)

def setup_logging(log_level: str = "INFO", log_file: str = "agora.log"):
    """Setup comprehensive logging configuration."""
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Console handler with JSON formatting
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JSONFormatter())
    logger.addHandler(console_handler)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(JSONFormatter())
    logger.addHandler(file_handler)
    
    # Error file handler for errors only
    error_handler = logging.handlers.RotatingFileHandler(
        "agora_errors.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(JSONFormatter())
    logger.addHandler(error_handler)
    
    return logger

# Metrics registry
registry = CollectorRegistry()

# Define metrics
REQUEST_COUNT = Counter(
    'agora_requests_total',
    'Total number of requests',
    ['method', 'endpoint', 'status_code'],
    registry=registry
)

REQUEST_DURATION = Histogram(
    'agora_request_duration_seconds',
    'Request duration in seconds',
    ['method', 'endpoint'],
    registry=registry
)

POLL_OPERATIONS = Counter(
    'agora_poll_operations_total',
    'Total number of poll operations',
    ['operation', 'team_id'],
    registry=registry
)

VOTE_COUNT = Counter(
    'agora_votes_total',
    'Total number of votes cast',
    ['team_id', 'poll_type'],
    registry=registry
)

ACTIVE_POLLS = Gauge(
    'agora_active_polls',
    'Number of currently active polls',
    ['team_id'],
    registry=registry
)

ERROR_COUNT = Counter(
    'agora_errors_total',
    'Total number of errors',
    ['error_type', 'severity'],
    registry=registry
)

SLACK_API_CALLS = Counter(
    'agora_slack_api_calls_total',
    'Total number of Slack API calls',
    ['method', 'status'],
    registry=registry
)

SYSTEM_METRICS = Gauge(
    'agora_system_metrics',
    'System resource metrics',
    ['metric_type'],
    registry=registry
)

DATABASE_OPERATIONS = Counter(
    'agora_database_operations_total',
    'Total number of database operations',
    ['operation', 'table'],
    registry=registry
)

CACHE_OPERATIONS = Counter(
    'agora_cache_operations_total',
    'Cache hit/miss statistics',
    ['operation', 'result'],
    registry=registry
)

@dataclass
class HealthStatus:
    """Health check status data class."""
    status: str
    timestamp: datetime
    checks: Dict[str, Dict[str, Any]]
    version: str = "1.0.0"
    uptime: float = 0.0

class MetricsCollector:
    """Collect and manage application metrics."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.start_time = time.time()
    
    def record_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record HTTP request metrics."""
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
        REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)
    
    def record_poll_operation(self, operation: str, team_id: str):
        """Record poll operation metrics."""
        POLL_OPERATIONS.labels(operation=operation, team_id=team_id).inc()
    
    def record_vote(self, team_id: str, poll_type: str):
        """Record vote metrics."""
        VOTE_COUNT.labels(team_id=team_id, poll_type=poll_type).inc()
    
    def update_active_polls(self, team_id: str, count: int):
        """Update active polls gauge."""
        ACTIVE_POLLS.labels(team_id=team_id).set(count)
    
    def record_error(self, error_type: str, severity: str = "error"):
        """Record error metrics."""
        ERROR_COUNT.labels(error_type=error_type, severity=severity).inc()
    
    def record_slack_api_call(self, method: str, status: str):
        """Record Slack API call metrics."""
        SLACK_API_CALLS.labels(method=method, status=status).inc()
    
    def record_database_operation(self, operation: str, table: str):
        """Record database operation metrics."""
        DATABASE_OPERATIONS.labels(operation=operation, table=table).inc()
    
    def record_cache_operation(self, operation: str, result: str):
        """Record cache operation metrics."""
        CACHE_OPERATIONS.labels(operation=operation, result=result).inc()
    
    def update_system_metrics(self):
        """Update system resource metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            SYSTEM_METRICS.labels(metric_type='cpu_percent').set(cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            SYSTEM_METRICS.labels(metric_type='memory_percent').set(memory.percent)
            SYSTEM_METRICS.labels(metric_type='memory_used_mb').set(memory.used / 1024 / 1024)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            SYSTEM_METRICS.labels(metric_type='disk_percent').set(disk.percent)
            SYSTEM_METRICS.labels(metric_type='disk_used_gb').set(disk.used / 1024 / 1024 / 1024)
            
            # Network I/O
            network = psutil.net_io_counters()
            SYSTEM_METRICS.labels(metric_type='network_bytes_sent').set(network.bytes_sent)
            SYSTEM_METRICS.labels(metric_type='network_bytes_recv').set(network.bytes_recv)
            
            # Application uptime
            uptime = time.time() - self.start_time
            SYSTEM_METRICS.labels(metric_type='uptime_seconds').set(uptime)
            
        except Exception as e:
            self.logger.error(f"Error updating system metrics: {e}")
    
    def get_metrics(self) -> str:
        """Get Prometheus metrics in text format."""
        return generate_latest(registry).decode('utf-8')

class HealthChecker:
    """Perform health checks on various system components."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.redis_client = None
        
        # Initialize Redis client for health checks
        try:
            if hasattr(Config, 'REDIS_URL') and Config.REDIS_URL:
                self.redis_client = redis.from_url(Config.REDIS_URL)
            else:
                self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
        except Exception as e:
            self.logger.warning(f"Redis client initialization failed: {e}")
    
    def check_database(self) -> Dict[str, Any]:
        """Check database connectivity and performance."""
        try:
            from models import engine
            
            start_time = time.time()
            
            # Test connection
            with engine.connect() as conn:
                result = conn.execute("SELECT 1").fetchone()
                if result[0] != 1:
                    raise Exception("Database query returned unexpected result")
            
            duration = time.time() - start_time
            
            return {
                'status': 'healthy',
                'response_time': duration,
                'message': 'Database connection successful'
            }
            
        except Exception as e:
            self.logger.error(f"Database health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'message': 'Database connection failed'
            }
    
    def check_redis(self) -> Dict[str, Any]:
        """Check Redis connectivity and performance."""
        if not self.redis_client:
            return {
                'status': 'disabled',
                'message': 'Redis not configured'
            }
        
        try:
            start_time = time.time()
            
            # Test connection
            self.redis_client.ping()
            
            # Test set/get
            test_key = "health_check"
            test_value = "ok"
            self.redis_client.set(test_key, test_value, ex=60)
            retrieved_value = self.redis_client.get(test_key)
            
            if retrieved_value.decode('utf-8') != test_value:
                raise Exception("Redis set/get test failed")
            
            duration = time.time() - start_time
            
            return {
                'status': 'healthy',
                'response_time': duration,
                'message': 'Redis connection successful'
            }
            
        except Exception as e:
            self.logger.error(f"Redis health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'message': 'Redis connection failed'
            }
    
    def check_slack_api(self) -> Dict[str, Any]:
        """Check Slack API connectivity."""
        try:
            # This would test actual Slack API connectivity
            # For now, we'll check if credentials are configured
            
            if not hasattr(Config, 'SLACK_BOT_TOKEN') or not Config.SLACK_BOT_TOKEN:
                return {
                    'status': 'unhealthy',
                    'message': 'Slack bot token not configured'
                }
            
            if not hasattr(Config, 'SLACK_SIGNING_SECRET') or not Config.SLACK_SIGNING_SECRET:
                return {
                    'status': 'unhealthy',
                    'message': 'Slack signing secret not configured'
                }
            
            return {
                'status': 'healthy',
                'message': 'Slack API credentials configured'
            }
            
        except Exception as e:
            self.logger.error(f"Slack API health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'message': 'Slack API check failed'
            }
    
    def check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            # Determine overall status
            status = 'healthy'
            warnings = []
            
            if cpu_percent > 80:
                status = 'warning'
                warnings.append(f"High CPU usage: {cpu_percent}%")
            
            if memory.percent > 80:
                status = 'warning'
                warnings.append(f"High memory usage: {memory.percent}%")
            
            if disk.percent > 80:
                status = 'warning'
                warnings.append(f"High disk usage: {disk.percent}%")
            
            return {
                'status': status,
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'disk_percent': disk.percent,
                'warnings': warnings,
                'message': 'System resources checked'
            }
            
        except Exception as e:
            self.logger.error(f"System resources health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'message': 'System resources check failed'
            }
    
    def get_health_status(self) -> HealthStatus:
        """Get comprehensive health status."""
        checks = {
            'database': self.check_database(),
            'redis': self.check_redis(),
            'slack_api': self.check_slack_api(),
            'system_resources': self.check_system_resources()
        }
        
        # Determine overall status
        overall_status = 'healthy'
        for check_name, check_result in checks.items():
            if check_result['status'] == 'unhealthy':
                overall_status = 'unhealthy'
                break
            elif check_result['status'] == 'warning' and overall_status == 'healthy':
                overall_status = 'warning'
        
        # Calculate uptime
        uptime = time.time() - (getattr(self, 'start_time', time.time()))
        
        return HealthStatus(
            status=overall_status,
            timestamp=datetime.utcnow(),
            checks=checks,
            uptime=uptime
        )

class AlertManager:
    """Manage alerts and notifications."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.alert_thresholds = {
            'error_rate': 10,  # errors per minute
            'response_time': 5.0,  # seconds
            'memory_usage': 80,  # percentage
            'disk_usage': 80,  # percentage
        }
        self.alert_history = deque(maxlen=1000)
    
    def check_error_rate(self) -> Optional[Dict[str, Any]]:
        """Check if error rate exceeds threshold."""
        # This would check actual error rate from metrics
        # For now, return None (no alert)
        return None
    
    def check_response_time(self) -> Optional[Dict[str, Any]]:
        """Check if response time exceeds threshold."""
        # This would check actual response times from metrics
        # For now, return None (no alert)
        return None
    
    def send_alert(self, alert_type: str, severity: str, message: str, details: Dict[str, Any] = None):
        """Send alert notification."""
        alert = {
            'type': alert_type,
            'severity': severity,
            'message': message,
            'details': details or {},
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.alert_history.append(alert)
        
        # Log the alert
        self.logger.error(
            f"ALERT: {alert_type} - {message}",
            extra={
                'alert_type': alert_type,
                'severity': severity,
                'alert_details': details
            }
        )
        
        # In production, you would send to external alerting systems
        # (PagerDuty, Slack, email, etc.)

# Global instances
metrics_collector = MetricsCollector()
health_checker = HealthChecker()
alert_manager = AlertManager()

# Decorators for monitoring
def monitor_requests(func):
    """Decorator to monitor HTTP requests."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        method = "unknown"
        endpoint = "unknown"
        status_code = 200
        
        try:
            # Extract request info if available
            if args and hasattr(args[0], 'method'):
                method = args[0].method
                endpoint = args[0].url.path
            
            result = await func(*args, **kwargs)
            
            # Extract status code if available
            if hasattr(result, 'status_code'):
                status_code = result.status_code
            
            return result
            
        except Exception as e:
            status_code = 500
            metrics_collector.record_error(type(e).__name__)
            raise
        
        finally:
            duration = time.time() - start_time
            metrics_collector.record_request(method, endpoint, status_code, duration)
    
    return wrapper

def monitor_database_operations(operation: str, table: str):
    """Decorator to monitor database operations."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                metrics_collector.record_database_operation(operation, table)
                return result
            except Exception as e:
                metrics_collector.record_error(f"database_{operation}")
                raise
        return wrapper
    return decorator

def monitor_slack_operations(operation: str):
    """Decorator to monitor Slack operations."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                result = await func(*args, **kwargs)
                metrics_collector.record_slack_api_call(operation, "success")
                return result
            except Exception as e:
                metrics_collector.record_slack_api_call(operation, "error")
                metrics_collector.record_error(f"slack_{operation}")
                raise
        return wrapper
    return decorator

@contextmanager
def log_context(**kwargs):
    """Context manager for adding context to logs."""
    old_factory = logging.getLogRecordFactory()
    
    def record_factory(*args, **factory_kwargs):
        record = old_factory(*args, **factory_kwargs)
        for key, value in kwargs.items():
            setattr(record, key, value)
        return record
    
    logging.setLogRecordFactory(record_factory)
    try:
        yield
    finally:
        logging.setLogRecordFactory(old_factory)

# System monitoring thread
class SystemMonitor(threading.Thread):
    """Background thread for system monitoring."""
    
    def __init__(self, interval: int = 60):
        super().__init__(daemon=True)
        self.interval = interval
        self.running = True
        self.logger = logging.getLogger(__name__)
    
    def run(self):
        """Run monitoring loop."""
        while self.running:
            try:
                # Update system metrics
                metrics_collector.update_system_metrics()
                
                # Check for alerts
                # This would implement actual alerting logic
                
                time.sleep(self.interval)
                
            except Exception as e:
                self.logger.error(f"System monitor error: {e}")
                time.sleep(self.interval)
    
    def stop(self):
        """Stop monitoring."""
        self.running = False

# Initialize monitoring
def initialize_monitoring():
    """Initialize the monitoring system."""
    # Setup logging
    setup_logging(
        log_level=getattr(Config, 'LOG_LEVEL', 'INFO'),
        log_file=getattr(Config, 'LOG_FILE', 'agora.log')
    )
    
    # Start system monitor
    system_monitor = SystemMonitor(interval=60)
    system_monitor.start()
    
    logger = logging.getLogger(__name__)
    logger.info("Monitoring system initialized")
    
    return system_monitor

# Export functions for use in other modules
def get_metrics() -> str:
    """Get Prometheus metrics."""
    return metrics_collector.get_metrics()

def get_health() -> Dict[str, Any]:
    """Get health status."""
    health_status = health_checker.get_health_status()
    return asdict(health_status)

def log_with_context(**context):
    """Create log context."""
    return log_context(**context)