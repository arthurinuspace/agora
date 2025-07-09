# Docker Deployment Guide

## 🐳 Docker Overview

Agora supports containerized deployment using Docker and Docker Compose for both development and production environments.

## 📚 Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- 2GB+ available RAM
- 10GB+ available storage

## 🚪 Development Environment

### Quick Start

```bash
# Clone repository
git clone https://github.com/arthurinuspace/agora.git
cd agora

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f agora

# Stop services
docker-compose down
```

### Services in Development

```yaml
# docker-compose.yml
services:
  agora:          # Main application
    build: .
    ports:
      - "8000:8000"
    volumes:
      - .:/app
    depends_on:
      - redis

  redis:          # Cache and sessions
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

## 🚀 Production Environment

### Production Setup

```bash
# Set environment variables
export POSTGRES_PASSWORD="your-secure-password"
export REDIS_PASSWORD="your-redis-password"
export DOMAIN="your-domain.com"

# Deploy with production compose
docker-compose -f docker-compose.prod.yml up -d

# Scale application
docker-compose -f docker-compose.prod.yml up -d --scale agora=3
```

### Production Services

```yaml
# docker-compose.prod.yml
services:
  agora:          # Application servers
    image: agora:latest
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M

  postgres:       # Database
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: agora
      POSTGRES_USER: agora_user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:          # Cache
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data

  nginx:          # Reverse proxy
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - agora
```

## 🔧 Custom Docker Build

### Build Image

```bash
# Build production image
docker build -t agora:latest .

# Build with specific tag
docker build -t agora:v1.0.0 .

# Build with build args
docker build --build-arg PYTHON_VERSION=3.12 -t agora:latest .
```

### Multi-stage Dockerfile

```dockerfile
# Build stage
FROM python:3.12-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Production stage
FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
CMD ["python", "start_slack_app.py"]
```

## 🔍 Health Checks

### Application Health

```bash
# Check application health
curl http://localhost:8000/health

# Check database connectivity
docker exec agora_agora_1 python -c "from database import engine; print(engine.execute('SELECT 1').scalar())"

# Check Redis connectivity
docker exec agora_redis_1 redis-cli ping
```

### Docker Health Checks

```dockerfile
# In Dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
```

## 📊 Monitoring

### Container Metrics

```bash
# View resource usage
docker stats

# View logs
docker-compose logs -f agora
docker-compose logs -f postgres
docker-compose logs -f redis

# Follow specific service
docker-compose logs -f --tail=100 agora
```

### Log Management

```yaml
# docker-compose.prod.yml
services:
  agora:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## 🔄 Updates & Maintenance

### Application Updates

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose build agora
docker-compose up -d agora

# Zero-downtime rolling update
docker-compose -f docker-compose.prod.yml up -d --no-deps --scale agora=6 agora
docker-compose -f docker-compose.prod.yml up -d --no-deps --scale agora=3 agora
```

### Database Maintenance

```bash
# Backup database
docker exec agora_postgres_1 pg_dump -U agora_user agora > backup.sql

# Restore database
docker exec -i agora_postgres_1 psql -U agora_user agora < backup.sql

# Run migrations
docker exec agora_agora_1 python migrations.py
```

## 🚫 Troubleshooting

### Common Issues

#### Port Already in Use
```bash
# Find process using port
sudo lsof -i :8000

# Kill process
sudo kill -9 <PID>

# Use different port
docker-compose up -d --scale agora=1 -p 8001:8000
```

#### Container Won't Start
```bash
# Check logs
docker-compose logs agora

# Check configuration
docker-compose config

# Rebuild without cache
docker-compose build --no-cache agora
```

#### Database Connection Issues
```bash
# Check PostgreSQL logs
docker-compose logs postgres

# Test connection
docker exec agora_agora_1 python -c "from database import engine; print('Database connected')"

# Reset database
docker-compose down -v
docker-compose up -d postgres
```

### Performance Optimization

```bash
# Optimize Docker build
docker build --build-arg BUILDKIT_INLINE_CACHE=1 -t agora:latest .

# Use multi-stage builds
# Add .dockerignore file
# Use specific base image versions
# Clean up layers
```

### Security Considerations

```yaml
# docker-compose.prod.yml
services:
  agora:
    user: "1000:1000"  # Non-root user
    read_only: true     # Read-only filesystem
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    security_opt:
      - no-new-privileges:true
```

## See Also

- [Production Deployment](production.md)
- [Configuration Guide](../configuration.md)
- [Monitoring Guide](../monitoring.md)
- [Security Guide](../security.md)
