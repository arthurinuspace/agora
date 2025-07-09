# Monitoring Guide

## 📊 Monitoring Overview

Agora provides comprehensive monitoring capabilities including health checks, performance metrics, and alerting systems.

## 🔍 Health Checks

### Application Health

```python
# Health check endpoint
from fastapi import FastAPI
from services import get_service, DatabaseService

@app.get("/health")
async def health_check():
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {}
    }
    
    # Check database connectivity
    try:
        db_service = get_service(DatabaseService)
        db_service.health_check()
        health_status["services"]["database"] = "healthy"
    except Exception as e:
        health_status["services"]["database"] = "unhealthy"
        health_status["status"] = "degraded"
    
    # Check Redis connectivity
    try:
        redis_client.ping()
        health_status["services"]["redis"] = "healthy"
    except Exception as e:
        health_status["services"]["redis"] = "unhealthy"
        health_status["status"] = "degraded"
    
    return health_status
```

### Database Health

```python
class DatabaseHealthCheck:
    def __init__(self, db_session):
        self.db_session = db_session
    
    def check_connectivity(self) -> bool:
        try:
            self.db_session.execute("SELECT 1")
            return True
        except Exception:
            return False
    
    def check_performance(self) -> dict:
        start_time = time.time()
        try:
            self.db_session.execute("SELECT COUNT(*) FROM polls")
            response_time = time.time() - start_time
            return {
                "status": "healthy",
                "response_time_ms": response_time * 1000
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
```

## 📊 Performance Metrics

### Application Metrics

```python
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
request_count = Counter(
    'agora_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status_code']
)

request_duration = Histogram(
    'agora_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

active_polls = Gauge(
    'agora_active_polls',
    'Number of currently active polls'
)

# Middleware to collect metrics
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    # Record metrics
    request_count.labels(
        method=request.method,
        endpoint=request.url.path,
        status_code=response.status_code
    ).inc()
    
    request_duration.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(time.time() - start_time)
    
    return response
```

### Custom Business Metrics

```python
class BusinessMetrics:
    def __init__(self):
        self.polls_created = Counter(
            'agora_polls_created_total',
            'Total polls created',
            ['poll_type', 'anonymous']
        )
        
        self.votes_cast = Counter(
            'agora_votes_cast_total',
            'Total votes cast',
            ['poll_type']
        )
        
        self.user_engagement = Gauge(
            'agora_user_engagement_rate',
            'User engagement rate percentage'
        )
    
    def record_poll_creation(self, poll_type: str, anonymous: bool):
        self.polls_created.labels(
            poll_type=poll_type,
            anonymous=str(anonymous)
        ).inc()
    
    def record_vote(self, poll_type: str):
        self.votes_cast.labels(poll_type=poll_type).inc()
```

## 📊 Logging

### Structured Logging

```python
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add extra fields
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'poll_id'):
            log_entry['poll_id'] = record.poll_id
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        
        return json.dumps(log_entry)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[
        logging.FileHandler('agora.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('agora')
logger.handlers[0].setFormatter(JSONFormatter())
```

### Log Aggregation

```python
class LogAggregator:
    def __init__(self, elasticsearch_client):
        self.es_client = elasticsearch_client
    
    def send_logs(self, log_entries: list):
        for entry in log_entries:
            self.es_client.index(
                index=f"agora-logs-{datetime.now().strftime('%Y-%m')}",
                body=entry
            )
    
    def search_logs(self, query: dict, start_time: datetime, end_time: datetime):
        search_body = {
            "query": {
                "bool": {
                    "must": [query],
                    "filter": [
                        {
                            "range": {
                                "timestamp": {
                                    "gte": start_time.isoformat(),
                                    "lte": end_time.isoformat()
                                }
                            }
                        }
                    ]
                }
            }
        }
        
        return self.es_client.search(
            index="agora-logs-*",
            body=search_body
        )
```

## 🚨 Alerting

### Alert Configuration

```python
class AlertManager:
    def __init__(self):
        self.alert_rules = {
            'high_error_rate': {
                'threshold': 0.05,  # 5% error rate
                'window': 300,      # 5 minutes
                'severity': 'critical'
            },
            'slow_response_time': {
                'threshold': 1.0,   # 1 second
                'window': 180,      # 3 minutes
                'severity': 'warning'
            },
            'database_connection_failure': {
                'threshold': 1,     # Any failure
                'window': 60,       # 1 minute
                'severity': 'critical'
            }
        }
    
    def check_alerts(self):
        for rule_name, rule_config in self.alert_rules.items():
            if self.evaluate_rule(rule_name, rule_config):
                self.fire_alert(rule_name, rule_config)
    
    def fire_alert(self, rule_name: str, rule_config: dict):
        alert_payload = {
            'alert_name': rule_name,
            'severity': rule_config['severity'],
            'timestamp': datetime.utcnow().isoformat(),
            'description': self.get_alert_description(rule_name)
        }
        
        # Send to notification channels
        self.send_slack_alert(alert_payload)
        self.send_email_alert(alert_payload)
```

### Slack Integration for Alerts

```python
from slack_sdk import WebClient

class SlackAlerter:
    def __init__(self, bot_token: str, channel: str):
        self.client = WebClient(token=bot_token)
        self.channel = channel
    
    def send_alert(self, alert: dict):
        color = {
            'critical': 'danger',
            'warning': 'warning',
            'info': 'good'
        }.get(alert['severity'], 'warning')
        
        self.client.chat_postMessage(
            channel=self.channel,
            text=f"Alert: {alert['alert_name']}",
            attachments=[
                {
                    'color': color,
                    'title': alert['alert_name'],
                    'text': alert['description'],
                    'fields': [
                        {
                            'title': 'Severity',
                            'value': alert['severity'],
                            'short': True
                        },
                        {
                            'title': 'Timestamp',
                            'value': alert['timestamp'],
                            'short': True
                        }
                    ]
                }
            ]
        )
```

## 📊 Dashboard Setup

### Grafana Configuration

```json
{
  "dashboard": {
    "title": "Agora Application Dashboard",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(agora_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(agora_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "Active Polls",
        "type": "singlestat",
        "targets": [
          {
            "expr": "agora_active_polls",
            "legendFormat": "Active Polls"
          }
        ]
      }
    ]
  }
}
```

### Custom Dashboard

```python
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/dashboard')
def dashboard():
    metrics = {
        'active_polls': get_active_polls_count(),
        'total_votes_today': get_votes_today(),
        'error_rate': get_error_rate(),
        'response_time': get_avg_response_time(),
        'user_activity': get_user_activity_stats()
    }
    
    return render_template('dashboard.html', metrics=metrics)

def get_active_polls_count():
    return db.query(Poll).filter(Poll.status == 'active').count()

def get_votes_today():
    today = datetime.now().date()
    return db.query(Vote).filter(
        Vote.created_at >= today
    ).count()
```

## 🔍 Monitoring Tools Integration

### Prometheus Integration

```python
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

@app.get('/metrics')
async def metrics():
    return Response(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
```

### New Relic Integration

```python
import newrelic.agent

@newrelic.agent.function_trace()
def create_poll(poll_data: dict):
    # Custom metrics
    newrelic.agent.add_custom_attribute('poll_type', poll_data['type'])
    newrelic.agent.add_custom_attribute('anonymous', poll_data['anonymous'])
    
    # Business logic
    poll = Poll(**poll_data)
    db.session.add(poll)
    db.session.commit()
    
    # Record custom event
    newrelic.agent.record_custom_event(
        'PollCreated',
        {
            'poll_id': poll.id,
            'type': poll.type,
            'anonymous': poll.anonymous
        }
    )
```

## 📊 Performance Monitoring

### Database Performance

```python
class DatabaseMonitor:
    def __init__(self, db_session):
        self.db_session = db_session
    
    def monitor_slow_queries(self):
        slow_queries = self.db_session.execute(
            """
            SELECT query, mean_time, calls, total_time
            FROM pg_stat_statements
            WHERE mean_time > 100  -- queries taking > 100ms
            ORDER BY mean_time DESC
            LIMIT 10
            """
        ).fetchall()
        
        for query in slow_queries:
            logger.warning(
                "Slow query detected",
                extra={
                    'query': query.query,
                    'mean_time': query.mean_time,
                    'calls': query.calls
                }
            )
    
    def monitor_connections(self):
        connection_stats = self.db_session.execute(
            """
            SELECT state, count(*) as count
            FROM pg_stat_activity
            GROUP BY state
            """
        ).fetchall()
        
        for stat in connection_stats:
            gauge = Gauge(
                f'postgres_connections_{stat.state}',
                f'PostgreSQL connections in {stat.state} state'
            )
            gauge.set(stat.count)
```

### Memory and CPU Monitoring

```python
import psutil

class SystemMonitor:
    def __init__(self):
        self.cpu_usage = Gauge('system_cpu_usage_percent', 'CPU usage percentage')
        self.memory_usage = Gauge('system_memory_usage_percent', 'Memory usage percentage')
        self.disk_usage = Gauge('system_disk_usage_percent', 'Disk usage percentage')
    
    def collect_metrics(self):
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        self.cpu_usage.set(cpu_percent)
        
        # Memory usage
        memory = psutil.virtual_memory()
        self.memory_usage.set(memory.percent)
        
        # Disk usage
        disk = psutil.disk_usage('/')
        self.disk_usage.set(disk.percent)
        
        # Log if thresholds exceeded
        if cpu_percent > 80:
            logger.warning(f"High CPU usage: {cpu_percent}%")
        if memory.percent > 85:
            logger.warning(f"High memory usage: {memory.percent}%")
        if disk.percent > 90:
            logger.warning(f"High disk usage: {disk.percent}%")
```

## 🚫 Troubleshooting

### Common Monitoring Issues

#### Metrics Not Appearing
```python
# Check if metrics endpoint is accessible
import requests

response = requests.get('http://localhost:8000/metrics')
if response.status_code == 200:
    print("Metrics endpoint is working")
else:
    print(f"Metrics endpoint error: {response.status_code}")
```

#### High Memory Usage
```python
# Memory profiling
import tracemalloc

tracemalloc.start()

# Your application code here

current, peak = tracemalloc.get_traced_memory()
print(f"Current memory usage: {current / 1024 / 1024:.1f} MB")
print(f"Peak memory usage: {peak / 1024 / 1024:.1f} MB")
```

#### Database Connection Issues
```python
# Connection pool monitoring
from sqlalchemy import event

@event.listens_for(engine, 'connect')
def receive_connect(dbapi_connection, connection_record):
    logger.info("Database connection established")

@event.listens_for(engine, 'close')
def receive_close(dbapi_connection, connection_record):
    logger.info("Database connection closed")
```

## See Also

- [Configuration Guide](configuration.md)
- [Security Guide](security.md)
- [Admin Guide](admin.md)
- [Performance Testing](testing/performance.md)
