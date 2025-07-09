# Admin Guide

## 🛡️ Admin Dashboard Overview

The Agora admin dashboard provides comprehensive management and monitoring capabilities for workspace administrators.

## 🔑 Admin Access

### Prerequisites
- Admin role in Slack workspace
- Admin permissions in Agora application
- Access to admin dashboard URL

### Login Process
1. Navigate to `https://your-domain.com/admin`
2. Click "Sign in with Slack"
3. Authorize admin permissions
4. Access admin dashboard

## 📊 Dashboard Features

### System Overview
- **Active Polls**: Currently running polls across workspace
- **User Activity**: Real-time user engagement metrics
- **System Health**: Application and database status
- **Performance Metrics**: Response times and error rates

### Poll Management
- **All Polls**: Complete list of workspace polls
- **Active Monitoring**: Real-time poll status updates
- **Moderation Tools**: Ability to end or delete inappropriate polls
- **Analytics**: Detailed voting patterns and engagement data

### User Management
- **User List**: All workspace users and their activity
- **Role Assignment**: Promote users to admin status
- **Permission Control**: Manage user capabilities
- **Activity Monitoring**: Track user engagement and behavior

## 📋 Poll Administration

### Managing Active Polls

```bash
# View all active polls
GET /api/admin/polls?status=active

# End a poll
POST /api/admin/polls/{poll_id}/end

# Delete inappropriate poll
DELETE /api/admin/polls/{poll_id}
```

### Poll Moderation

#### Content Guidelines
- No offensive or inappropriate content
- No spam or irrelevant polls
- Compliance with workplace policies
- Respect for anonymity settings

#### Moderation Actions
- **Warning**: Notify poll creator of policy violation
- **Edit**: Modify poll content if necessary
- **End**: Terminate poll early
- **Delete**: Remove poll and all associated data

### Bulk Operations

```python
# Python admin script example
from agora_admin import AdminClient

admin = AdminClient(token="admin-token")

# Get all polls from last week
polls = admin.polls.list(
    start_date="2025-01-08",
    end_date="2025-01-15"
)

# Export all poll data
for poll in polls:
    admin.polls.export(poll.id, format="csv")
```

## 👥 User Management

### User Roles

#### Standard User
- Create and vote on polls
- View poll results
- Export own poll data

#### Admin User
- All standard user capabilities
- Manage workspace polls
- View all user activity
- Export all workspace data
- Manage user roles

#### Super Admin
- All admin capabilities
- System configuration
- Database management
- Security settings

### Role Assignment

```bash
# Promote user to admin
POST /api/admin/users/{user_id}/role
{
  "role": "admin"
}

# Revoke admin access
POST /api/admin/users/{user_id}/role
{
  "role": "user"
}
```

### User Activity Monitoring

- **Login Activity**: Track user access patterns
- **Poll Creation**: Monitor poll creation frequency
- **Voting Patterns**: Analyze user engagement
- **Export Usage**: Track data export requests

## 📊 Analytics & Reporting

### Workspace Analytics

```json
{
  "workspace_stats": {
    "total_users": 250,
    "active_users_today": 45,
    "polls_created_today": 12,
    "votes_cast_today": 156,
    "engagement_rate": 78.5
  },
  "trending_topics": [
    "lunch decisions",
    "meeting scheduling",
    "feature prioritization"
  ],
  "peak_usage_hours": [9, 12, 15]
}
```

### Custom Reports

```python
# Generate custom report
report = admin.reports.generate(
    type="engagement",
    start_date="2025-01-01",
    end_date="2025-01-31",
    filters={
        "channels": ["#general", "#random"],
        "poll_types": ["single_choice"]
    }
)
```

### Export Capabilities

- **CSV Export**: Spreadsheet-compatible format
- **JSON Export**: API-friendly structured data
- **Excel Export**: Advanced formatting and charts
- **PDF Reports**: Executive summaries and visualizations

## 🔒 Security Administration

### Access Control

```yaml
# Security settings
security:
  admin_approval_required: true
  max_poll_duration: 168h  # 1 week
  rate_limiting:
    polls_per_user_per_hour: 10
    votes_per_user_per_minute: 5
```

### Audit Logging

```json
{
  "timestamp": "2025-01-15T14:30:00Z",
  "action": "poll_deleted",
  "admin_user": "admin@company.com",
  "target_poll": "poll_123",
  "reason": "inappropriate_content",
  "ip_address": "192.168.1.100"
}
```

### Security Monitoring

- **Failed Login Attempts**: Monitor authentication failures
- **Unusual Activity**: Detect abnormal usage patterns
- **Data Access**: Track sensitive data access
- **Permission Changes**: Log role modifications

## 📊 System Monitoring

### Health Checks

```bash
# System health endpoint
GET /api/admin/health

{
  "status": "healthy",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "slack_api": "healthy"
  },
  "metrics": {
    "response_time_avg": 120,
    "error_rate": 0.01,
    "uptime": "99.9%"
  }
}
```

### Performance Metrics

- **Response Times**: API endpoint performance
- **Database Performance**: Query execution times
- **Cache Hit Rates**: Redis cache effectiveness
- **Memory Usage**: Application resource consumption

### Alert Configuration

```yaml
# Alert thresholds
alerts:
  response_time_threshold: 500ms
  error_rate_threshold: 5%
  failed_login_threshold: 10
  disk_usage_threshold: 85%
```

## 🚫 Troubleshooting

### Common Admin Issues

#### User Can't Access Admin Dashboard
```bash
# Check user role
GET /api/admin/users/{user_id}

# Verify permissions
GET /api/admin/users/{user_id}/permissions

# Grant admin access
POST /api/admin/users/{user_id}/role
{
  "role": "admin"
}
```

#### Poll Data Not Loading
```bash
# Check database connectivity
GET /api/admin/health

# Verify poll exists
GET /api/admin/polls/{poll_id}

# Check user permissions
GET /api/admin/users/{user_id}/permissions
```

#### Export Failures
```bash
# Check export service status
GET /api/admin/services/export

# Retry export
POST /api/admin/polls/{poll_id}/export
{
  "format": "csv",
  "retry": true
}
```

### System Maintenance

#### Database Maintenance
```bash
# Database backup
docker exec agora_postgres_1 pg_dump -U agora_user agora > backup.sql

# Clean old data
POST /api/admin/maintenance/cleanup
{
  "older_than": "30d",
  "types": ["ended_polls", "old_logs"]
}
```

#### Cache Management
```bash
# Clear Redis cache
POST /api/admin/cache/clear

# Warm cache
POST /api/admin/cache/warm
```

## 📚 Best Practices

### Admin Responsibilities

1. **Regular Monitoring**: Check dashboard daily
2. **Policy Enforcement**: Ensure compliance with guidelines
3. **User Support**: Help users with issues
4. **Data Security**: Protect sensitive information
5. **Performance Optimization**: Monitor and improve system performance

### Security Best Practices

- **Regular Audits**: Review access logs and permissions
- **Principle of Least Privilege**: Grant minimum required permissions
- **Two-Factor Authentication**: Enable 2FA for admin accounts
- **Regular Backups**: Maintain current data backups
- **Incident Response**: Have procedures for security incidents

## See Also

- [Security Guide](security.md)
- [Configuration Guide](configuration.md)
- [API Documentation](api.md)
- [Monitoring Guide](monitoring.md)
