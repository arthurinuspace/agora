# Technology Stack

## Core Technology Stack

- **Backend**: Python 3.12+ with FastAPI framework
- **Architecture**: SOLID-compliant enterprise architecture with dependency injection
- **Slack Integration**: Uses `slack_bolt` SDK for handling Slack API events
- **Database**: SQLite (development) / PostgreSQL (production)
- **Caching**: Redis for session management and performance
- **Reverse Proxy**: Nginx with SSL termination (production)
- **Deployment**: Docker containers with docker-compose orchestration
- **Testing**: pytest with comprehensive unit and integration tests

## 🗄️ Database Layer (database/)

```
database/
├── config.py          # Database configuration & health checks
└── __init__.py        # Database utilities export
```

## 🏭 Application Factory

```
app_factory.py         # Environment-specific app creation with lifespan management
```

## Deployment Environments

- **Development**: Local FastAPI with ngrok for public HTTPS URL
- **Production**: Docker-based deployment with PostgreSQL, Redis, and Nginx

## See Also

- [SOLID Architecture](solid-principles.md)
- [Development Setup](../development/setup.md)
- [Deployment Guide](../deployment/production.md)