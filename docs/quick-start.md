# Quick Start Guide

## 📚 Prerequisites
- **Python 3.12+**
- **Docker & Docker Compose** (for production)
- **Slack App** with bot permissions
- **ngrok** (for local development)

## 🚀 Installation

### 1. Clone Repository
```bash
# Clone the repository
git clone https://github.com/arthurinuspace/agora.git
cd agora

# Set up virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your Slack app credentials
# Required variables:
# SLACK_BOT_TOKEN=xoxb-your-slack-bot-token-here
# SLACK_SIGNING_SECRET=your-slack-signing-secret-here
```

### 3. Database Setup
```bash
# Initialize the database
python database.py
```

### 4. Run Application

#### Development Mode
```bash
# Start the development server
python start_slack_app.py

# In another terminal, expose with ngrok
ngrok http 8000
```

#### Production Mode (Docker)
```bash
# Set production environment variables
export POSTGRES_PASSWORD="your-secure-password"
export REDIS_PASSWORD="your-redis-password"

# Deploy with Docker
./deploy.sh prod
```

## 📱 Slack Configuration

### Required Bot Token Scopes
```
commands          # For slash commands
chat:write        # Send messages
chat:write.public # Send to public channels
users:read        # Read user information
channels:read     # Read channel information
```

### Slash Commands
- **Command**: `/agora`
- **Request URL**: `https://your-domain.com/slack/events`
- **Description**: Create and manage anonymous polls

### Event Subscriptions & Interactive Components
- **Request URL**: `https://your-domain.com/slack/events`

## See Also

- [Installation Guide](installation.md)
- [Configuration Guide](configuration.md)
- [Development Setup](development/setup.md)
- [Docker Deployment](deployment/docker.md)
