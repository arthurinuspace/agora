#!/bin/bash

# Agora Deployment Script
# This script helps deploy the Agora Slack app using Docker

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if required environment variables are set
check_env_vars() {
    print_status "Checking required environment variables..."
    
    if [ -z "$SLACK_BOT_TOKEN" ]; then
        print_error "SLACK_BOT_TOKEN is not set"
        exit 1
    fi
    
    if [ -z "$SLACK_SIGNING_SECRET" ]; then
        print_error "SLACK_SIGNING_SECRET is not set"
        exit 1
    fi
    
    print_success "All required environment variables are set"
}

# Function to build Docker image
build_image() {
    print_status "Building Docker image..."
    docker build -t agora:latest .
    print_success "Docker image built successfully"
}

# Function to run development environment
run_dev() {
    print_status "Starting development environment..."
    check_env_vars
    build_image
    docker-compose -f docker-compose.yml up -d
    print_success "Development environment started"
    print_status "Access the application at http://localhost:8000/health"
}

# Function to run production environment
run_prod() {
    print_status "Starting production environment..."
    check_env_vars
    
    if [ -z "$POSTGRES_PASSWORD" ]; then
        print_error "POSTGRES_PASSWORD is required for production"
        exit 1
    fi
    
    build_image
    docker-compose -f docker-compose.prod.yml up -d
    print_success "Production environment started"
    print_status "Access the application at https://your-domain.com"
}

# Function to stop services
stop_services() {
    print_status "Stopping services..."
    docker-compose -f docker-compose.yml down 2>/dev/null || true
    docker-compose -f docker-compose.prod.yml down 2>/dev/null || true
    print_success "Services stopped"
}

# Function to view logs
view_logs() {
    local service=${1:-agora}
    print_status "Viewing logs for service: $service"
    docker-compose logs -f "$service"
}

# Function to run database migration
migrate_db() {
    print_status "Running database migration..."
    docker-compose exec agora python database.py
    print_success "Database migration completed"
}

# Function to backup database
backup_db() {
    local backup_file="agora_backup_$(date +%Y%m%d_%H%M%S).sql"
    print_status "Creating database backup: $backup_file"
    
    if docker-compose ps postgres >/dev/null 2>&1; then
        docker-compose exec postgres pg_dump -U agora agora > "$backup_file"
        print_success "Database backup created: $backup_file"
    else
        print_warning "PostgreSQL not running, backing up SQLite database..."
        docker-compose exec agora cp /app/data/agora.db "/app/data/$backup_file"
        print_success "SQLite backup created in container"
    fi
}

# Function to show health status
health_check() {
    print_status "Checking application health..."
    
    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
        print_success "Application is healthy"
    else
        print_error "Application health check failed"
        exit 1
    fi
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  dev        Start development environment"
    echo "  prod       Start production environment"
    echo "  stop       Stop all services"
    echo "  logs       View application logs"
    echo "  migrate    Run database migration"
    echo "  backup     Create database backup"
    echo "  health     Check application health"
    echo "  build      Build Docker image only"
    echo "  help       Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 dev                 # Start development environment"
    echo "  $0 prod                # Start production environment"
    echo "  $0 logs agora          # View logs for agora service"
    echo "  $0 stop                # Stop all services"
}

# Main script logic
case "${1:-help}" in
    "dev")
        run_dev
        ;;
    "prod")
        run_prod
        ;;
    "stop")
        stop_services
        ;;
    "logs")
        view_logs "$2"
        ;;
    "migrate")
        migrate_db
        ;;
    "backup")
        backup_db
        ;;
    "health")
        health_check
        ;;
    "build")
        build_image
        ;;
    "help"|*)
        show_usage
        ;;
esac