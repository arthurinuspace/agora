# Agora Deployment Guide

This guide covers deploying the Agora Slack app using Docker for both development and production environments.

## Prerequisites

### Required Software
- Docker (20.10 or later)
- Docker Compose (2.0 or later)
- curl (for health checks)

### Required Environment Variables
- `SLACK_BOT_TOKEN`: Your Slack app bot token (starts with `xoxb-`)
- `SLACK_SIGNING_SECRET`: Your Slack app signing secret
- `POSTGRES_PASSWORD`: Database password for production (optional for dev)
- `REDIS_PASSWORD`: Redis password for production (optional)

## Quick Start

### Development Environment

1. **Set up environment variables:**
   ```bash
   export SLACK_BOT_TOKEN="xoxb-your-bot-token"
   export SLACK_SIGNING_SECRET="your-signing-secret"
   ```

2. **Start the development environment:**
   ```bash
   ./deploy.sh dev
   ```

3. **Verify the deployment:**
   ```bash
   ./deploy.sh health
   ```

The application will be available at `http://localhost:8000`

### Production Environment

1. **Set up environment variables:**
   ```bash
   export SLACK_BOT_TOKEN="xoxb-your-bot-token"
   export SLACK_SIGNING_SECRET="your-signing-secret"
   export POSTGRES_PASSWORD="your-secure-password"
   export REDIS_PASSWORD="your-redis-password"
   ```

2. **Start the production environment:**
   ```bash
   ./deploy.sh prod
   ```

3. **Configure SSL certificates** (see SSL Configuration section)

## Architecture

### Development Stack
- **Application**: Python 3.12 with FastAPI
- **Database**: SQLite (file-based)
- **Caching**: Optional Redis
- **Reverse Proxy**: None (direct access)

### Production Stack
- **Application**: Python 3.12 with FastAPI
- **Database**: PostgreSQL 15
- **Caching**: Redis 7
- **Reverse Proxy**: Nginx with SSL termination
- **Monitoring**: Container health checks

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SLACK_BOT_TOKEN` | Yes | - | Slack bot token |
| `SLACK_SIGNING_SECRET` | Yes | - | Slack signing secret |
| `DATABASE_URL` | No | SQLite | Database connection URL |
| `DEBUG` | No | False | Enable debug mode |
| `PORT` | No | 8000 | Application port |
| `POSTGRES_PASSWORD` | Prod | - | PostgreSQL password |
| `REDIS_PASSWORD` | Prod | - | Redis password |

### Database Configuration

#### Development (SQLite)
- File location: `/app/data/agora.db`
- Automatically created on first run
- Persistent via Docker volume

#### Production (PostgreSQL)
- Host: `postgres` (Docker service)
- Port: `5432`
- Database: `agora`
- User: `agora`
- Password: `${POSTGRES_PASSWORD}`

## SSL Configuration

For production deployment, you need SSL certificates:

1. **Obtain SSL certificates** (Let's Encrypt recommended):
   ```bash
   # Using certbot
   certbot certonly --standalone -d yourdomain.com
   ```

2. **Copy certificates to ssl directory:**
   ```bash
   mkdir ssl
   cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ssl/cert.pem
   cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ssl/key.pem
   ```

3. **Update nginx configuration** if needed

## Management Commands

### Deployment Commands
```bash
./deploy.sh dev      # Start development environment
./deploy.sh prod     # Start production environment
./deploy.sh stop     # Stop all services
./deploy.sh build    # Build Docker image only
```

### Maintenance Commands
```bash
./deploy.sh logs     # View application logs
./deploy.sh health   # Check application health
./deploy.sh migrate  # Run database migration
./deploy.sh backup   # Create database backup
```

### Manual Docker Commands
```bash
# View running containers
docker-compose ps

# Execute commands in container
docker-compose exec agora python database.py

# View container logs
docker-compose logs -f agora

# Restart specific service
docker-compose restart agora
```

## Monitoring and Troubleshooting

### Health Checks
- **Endpoint**: `GET /health`
- **Expected Response**: `{"status": "healthy"}`
- **Container Health**: Automatic Docker health checks every 30s

### Log Locations
- **Application logs**: `docker-compose logs agora`
- **Nginx logs**: `docker-compose logs nginx` (production)
- **PostgreSQL logs**: `docker-compose logs postgres` (production)

### Common Issues

#### Application Won't Start
1. Check environment variables are set correctly
2. Verify Slack tokens are valid
3. Check container logs: `docker-compose logs agora`

#### Database Connection Issues
1. Ensure PostgreSQL is running: `docker-compose ps postgres`
2. Check database credentials
3. Verify network connectivity between containers

#### SSL Certificate Issues
1. Verify certificate files exist in `ssl/` directory
2. Check certificate validity: `openssl x509 -in ssl/cert.pem -text -noout`
3. Ensure nginx can read certificate files

### Performance Tuning

#### Resource Limits
Add resource limits to docker-compose files:
```yaml
services:
  agora:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
```

#### Database Optimization
For high-volume deployments:
- Increase PostgreSQL shared_buffers
- Enable connection pooling
- Configure appropriate work_mem settings

## Scaling

### Horizontal Scaling
To run multiple application instances:
1. Use an external load balancer
2. Configure session management with Redis
3. Ensure database can handle concurrent connections

### Vertical Scaling
- Increase container resource limits
- Optimize database configuration
- Monitor memory and CPU usage

## Security Considerations

### Network Security
- Use Docker networks for service isolation
- Configure firewall rules appropriately
- Limit exposed ports

### Application Security
- Slack signature verification is enabled by default
- Environment variables protect sensitive data
- Non-root user in containers

### Data Security
- Database encryption at rest (PostgreSQL)
- SSL/TLS for all external communications
- Regular security updates

## Backup and Recovery

### Database Backups
```bash
# Automatic backup
./deploy.sh backup

# Manual PostgreSQL backup
docker-compose exec postgres pg_dump -U agora agora > backup.sql

# Restore from backup
docker-compose exec -T postgres psql -U agora agora < backup.sql
```

### Volume Backups
```bash
# Backup Docker volumes
docker run --rm -v agora_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data
```

## Updates and Maintenance

### Application Updates
1. Stop the current deployment: `./deploy.sh stop`
2. Pull latest code changes
3. Rebuild and restart: `./deploy.sh prod`

### Security Updates
1. Regularly update base Docker images
2. Update application dependencies
3. Apply OS security patches

### Database Migrations
```bash
# Run migrations
./deploy.sh migrate

# Verify migration
./deploy.sh health
```

## Support

For deployment issues:
1. Check the troubleshooting section above
2. Review container logs
3. Verify configuration settings
4. Test with development environment first