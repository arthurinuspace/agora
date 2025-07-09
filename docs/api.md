# API Documentation

## 🔗 RESTful API Overview

Agora provides a comprehensive RESTful API for programmatic access to all polling functionality. The API follows SOLID architecture principles with modular endpoints organized by business domain.

## 🔐 Authentication

### Slack Authentication
```http
POST /auth/slack
Content-Type: application/json

{
  "code": "slack-oauth-code",
  "redirect_uri": "https://your-domain.com/auth/callback"
}
```

### Token Usage
```http
GET /api/polls
Authorization: Bearer slack-user-token
```

## 🗳️ Poll Management API

### Create Poll
```http
POST /api/polls
Content-Type: application/json
Authorization: Bearer slack-user-token

{
  "question": "What should we have for lunch?",
  "options": ["Pizza", "Sushi", "Burgers"],
  "type": "single_choice",
  "anonymous": true,
  "end_time": "2025-01-15T17:00:00Z",
  "channel_id": "C1234567890"
}
```

### Get Poll
```http
GET /api/polls/{poll_id}
Authorization: Bearer slack-user-token

Response:
{
  "id": "poll_123",
  "question": "What should we have for lunch?",
  "options": [
    {"id": "opt_1", "text": "Pizza", "votes": 5},
    {"id": "opt_2", "text": "Sushi", "votes": 3},
    {"id": "opt_3", "text": "Burgers", "votes": 2}
  ],
  "total_votes": 10,
  "status": "active",
  "created_at": "2025-01-15T10:00:00Z",
  "end_time": "2025-01-15T17:00:00Z"
}
```

### Vote on Poll
```http
POST /api/polls/{poll_id}/vote
Content-Type: application/json
Authorization: Bearer slack-user-token

{
  "option_ids": ["opt_1"]
}
```

### End Poll
```http
POST /api/polls/{poll_id}/end
Authorization: Bearer slack-user-token
```

### Delete Poll
```http
DELETE /api/polls/{poll_id}
Authorization: Bearer slack-user-token
```

## 📊 Analytics API

### Get Poll Results
```http
GET /api/polls/{poll_id}/results
Authorization: Bearer slack-user-token

Response:
{
  "poll_id": "poll_123",
  "results": [
    {
      "option_id": "opt_1",
      "option_text": "Pizza",
      "votes": 5,
      "percentage": 50.0
    }
  ],
  "total_votes": 10,
  "participation_rate": 66.7,
  "analytics": {
    "voting_timeline": [...],
    "engagement_metrics": {...}
  }
}
```

### Export Poll Data
```http
GET /api/polls/{poll_id}/export?format=csv
Authorization: Bearer slack-user-token

# Available formats: csv, json, excel
```

### Workspace Analytics
```http
GET /api/analytics/workspace
Authorization: Bearer slack-user-token

Response:
{
  "total_polls": 150,
  "active_polls": 5,
  "total_votes": 2500,
  "participation_trends": [...],
  "popular_poll_types": {...}
}
```

## 📦 Bulk Operations API

### List Polls
```http
GET /api/polls?page=1&limit=20&status=active
Authorization: Bearer slack-user-token

Response:
{
  "polls": [...],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "pages": 8
  }
}
```

### Bulk Export
```http
POST /api/export/bulk
Content-Type: application/json
Authorization: Bearer slack-user-token

{
  "poll_ids": ["poll_123", "poll_456"],
  "format": "csv",
  "include_analytics": true
}
```

## 🕰 Webhook API

### Poll Event Webhooks
```http
POST /api/webhooks/register
Content-Type: application/json
Authorization: Bearer slack-user-token

{
  "url": "https://your-app.com/webhook",
  "events": ["poll.created", "poll.voted", "poll.ended"]
}
```

### Webhook Payload Example
```json
{
  "event": "poll.voted",
  "timestamp": "2025-01-15T12:00:00Z",
  "data": {
    "poll_id": "poll_123",
    "option_id": "opt_1",
    "voter_id": "U1234567890",
    "anonymous": true
  }
}
```

## ⚙️ Admin API

### User Management
```http
GET /api/admin/users
Authorization: Bearer admin-token

POST /api/admin/users/{user_id}/role
Content-Type: application/json
{
  "role": "admin"
}
```

### System Statistics
```http
GET /api/admin/stats
Authorization: Bearer admin-token

Response:
{
  "system_health": "healthy",
  "active_users": 250,
  "polls_today": 15,
  "response_time_avg": 120,
  "error_rate": 0.01
}
```

## 📊 Rate Limiting

### Rate Limits
- **General API**: 100 requests per minute per user
- **Voting API**: 10 votes per minute per user
- **Export API**: 5 requests per hour per user
- **Admin API**: 1000 requests per minute

### Rate Limit Headers
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642248000
```

## 🚫 Error Handling

### Error Response Format
```json
{
  "error": {
    "code": "POLL_NOT_FOUND",
    "message": "The requested poll does not exist",
    "details": {
      "poll_id": "poll_123"
    }
  }
}
```

### Common Error Codes

| Code | Status | Description |
|------|--------|-------------|
| `INVALID_TOKEN` | 401 | Authentication token is invalid |
| `INSUFFICIENT_PERMISSIONS` | 403 | User lacks required permissions |
| `POLL_NOT_FOUND` | 404 | Poll does not exist |
| `POLL_ENDED` | 409 | Cannot vote on ended poll |
| `ALREADY_VOTED` | 409 | User already voted on single-choice poll |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `VALIDATION_ERROR` | 422 | Request data validation failed |

## 📜 API Versioning

### Version Headers
```http
GET /api/polls
Accept: application/vnd.agora.v1+json
```

### Supported Versions
- **v1**: Current stable version
- **v2**: Beta version with enhanced features

## 🔗 SDK and Libraries

### Python SDK
```python
from agora_sdk import AgoraClient

client = AgoraClient(token="your-token")

# Create poll
poll = client.polls.create(
    question="What should we have for lunch?",
    options=["Pizza", "Sushi", "Burgers"],
    anonymous=True
)

# Vote on poll
client.polls.vote(poll.id, option_ids=["opt_1"])

# Get results
results = client.polls.get_results(poll.id)
```

### JavaScript SDK
```javascript
const { AgoraClient } = require('@agora/sdk');

const client = new AgoraClient({ token: 'your-token' });

// Create poll
const poll = await client.polls.create({
  question: 'What should we have for lunch?',
  options: ['Pizza', 'Sushi', 'Burgers'],
  anonymous: true
});

// Vote on poll
await client.polls.vote(poll.id, { optionIds: ['opt_1'] });

// Get results
const results = await client.polls.getResults(poll.id);
```

## See Also

- [Usage Guide](usage.md)
- [Configuration Guide](configuration.md)
- [Development Guide](development/setup.md)
- [Security Guide](security.md)
