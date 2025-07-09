# Configuration Guide

## 🔐 Environment Variables

### Required Variables

```bash
# Slack Integration
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token-here
SLACK_SIGNING_SECRET=your-slack-signing-secret-here

# Database Configuration
DATABASE_URL=sqlite:///agora.db  # Development
# DATABASE_URL=postgresql://user:password@localhost/agora  # Production

# Application Settings
APP_ENV=development  # or production
DEBUG=true          # Set to false in production
```

### Optional Variables

```bash
# Redis Configuration (for production)
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=your-redis-password

# Security Settings
SECRET_KEY=your-secret-key-here
CORS_ORIGINS=*  # Set specific origins in production

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
LOG_FILE=agora.log

# Performance
WORKERS=4  # Number of worker processes
MAX_CONNECTIONS=100
```

## 📱 Slack App Configuration

### 1. Create Slack App

1. Go to [Slack API](https://api.slack.com/apps)
2. Click "Create New App"
3. Choose "From scratch"
4. Enter app name: "Agora"
5. Select your workspace

### 2. Configure Bot Token Scopes

**OAuth & Permissions** → **Bot Token Scopes**:
```
commands          # For slash commands
chat:write        # Send messages
chat:write.public # Send to public channels
users:read        # Read user information
channels:read     # Read channel information
```

### 3. Install App to Workspace

1. Go to **OAuth & Permissions**
2. Click "Install to Workspace"
3. Authorize the app
4. Copy the **Bot User OAuth Token** (starts with `xoxb-`)

### 4. Configure Event Subscriptions

**Event Subscriptions** → **Enable Events**:
- **Request URL**: `https://your-domain.com/slack/events`
- **Subscribe to bot events**: `app_mention`, `message.channels`

### 5. Configure Slash Commands

**Slash Commands** → **Create New Command**:
- **Command**: `/agora`
- **Request URL**: `https://your-domain.com/slack/events`
- **Short Description**: "Create anonymous polls"
- **Usage Hint**: `What should we have for lunch?`

### 6. Configure Interactive Components

**Interactivity & Shortcuts** → **Interactivity**:
- **Request URL**: `https://your-domain.com/slack/events`

### 7. Get Signing Secret

**Basic Information** → **App Credentials**:
- Copy **Signing Secret**

## 💾 Database Configuration

### SQLite (Development)

```bash
# Automatic setup
DATABASE_URL=sqlite:///agora.db

# Initialize database
python database.py
```

### PostgreSQL (Production)

```bash
# Install PostgreSQL
sudo apt-get install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql
CREATE DATABASE agora;
CREATE USER agora_user WITH PASSWORD 'your-password';
GRANT ALL PRIVILEGES ON DATABASE agora TO agora_user;
\q

# Configure environment
DATABASE_URL=postgresql://agora_user:your-password@localhost/agora
```

## 📊 Redis Configuration (Optional)

### Installation

```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS
brew install redis

# Start Redis
sudo systemctl start redis
```

### Configuration

```bash
# Environment variables
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=your-redis-password

# Test connection
redis-cli ping
```

## 🔧 Application Configuration

### Development Settings

```python
# config.py
class DevelopmentConfig:
    DEBUG = True
    TESTING = False
    DATABASE_URL = "sqlite:///agora.db"
    LOG_LEVEL = "DEBUG"
    CORS_ORIGINS = ["*"]
```

### Production Settings

```python
# config.py
class ProductionConfig:
    DEBUG = False
    TESTING = False
    DATABASE_URL = "postgresql://..."
    LOG_LEVEL = "INFO"
    CORS_ORIGINS = ["https://your-domain.com"]
    SECRET_KEY = "your-production-secret-key"
```

## 🚫 Troubleshooting

### Common Configuration Issues

#### Invalid Slack Token
```bash
# Test token validity
curl -H "Authorization: Bearer xoxb-your-token" \
     https://slack.com/api/auth.test
```

#### Database Connection Issues
```bash
# Test database connection
python -c "from database import engine; print(engine.execute('SELECT 1').scalar())"
```

#### Environment Variables Not Loading
```bash
# Check .env file location
ls -la .env

# Test loading
python -c "from config import settings; print(settings.SLACK_BOT_TOKEN)"
```

### Security Checklist

- [ ] Use environment variables for all secrets
- [ ] Set `DEBUG=false` in production
- [ ] Configure specific CORS origins
- [ ] Use strong SECRET_KEY
- [ ] Enable HTTPS in production
- [ ] Restrict database access
- [ ] Set up proper logging

## See Also

- [Quick Start Guide](quick-start.md)
- [Installation Guide](installation.md)
- [Development Setup](development/setup.md)
- [Security Guide](security.md)
