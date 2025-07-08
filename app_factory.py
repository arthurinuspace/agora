"""
Application factory implementing dependency injection and SOLID principles.
"""

import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from services import get_container, configure_services
from services.factory import configure_services
from services.container import ServiceRegistry
from api import auth_router, polls_router, admin_router
from config import Config

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting up Agora application...")
    
    # Configure services
    container = get_container()
    configure_services(container)
    container.initialize()
    
    # Initialize database
    from services import DatabaseService
    db_service = container.get(DatabaseService)
    
    try:
        db_service.create_tables()
        logger.info("Database tables created/verified")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    
    # Health check services
    health_checks = []
    try:
        if db_service.health_check():
            health_checks.append("✓ Database")
        else:
            health_checks.append("✗ Database")
    except Exception:
        health_checks.append("✗ Database")
    
    try:
        from services import CacheService
        cache_service = container.get(CacheService)
        if cache_service.health_check():
            health_checks.append("✓ Cache")
        else:
            health_checks.append("✗ Cache")
    except Exception:
        health_checks.append("✗ Cache")
    
    logger.info(f"Service health checks: {', '.join(health_checks)}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Agora application...")


def create_app(config_override: dict = None) -> FastAPI:
    """Create FastAPI application with SOLID architecture."""
    
    app = FastAPI(
        title="Agora - Anonymous Voting for Slack Teams",
        description="Enterprise-grade anonymous voting application with advanced analytics and management features",
        version="2.0.0",
        docs_url="/docs" if Config.DEBUG else None,
        redoc_url="/redoc" if Config.DEBUG else None,
        lifespan=lifespan
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if Config.DEBUG else [Config.FRONTEND_URL],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API routers
    app.include_router(auth_router)
    app.include_router(polls_router)
    app.include_router(admin_router)
    
    # Static files for dashboard
    app.mount("/static", StaticFiles(directory="static"), name="static")
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Application health check."""
        try:
            from services import DatabaseService, CacheService
            container = get_container()
            
            # Check database
            db_service = container.get_optional(DatabaseService)
            db_healthy = db_service.health_check() if db_service else False
            
            # Check cache
            cache_service = container.get_optional(CacheService)
            cache_healthy = cache_service.health_check() if cache_service else False
            
            return {
                "status": "healthy" if db_healthy and cache_healthy else "degraded",
                "database": "healthy" if db_healthy else "unhealthy",
                "cache": "healthy" if cache_healthy else "unhealthy",
                "version": "2.0.0"
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "version": "2.0.0"
            }
    
    # Dashboard endpoint
    @app.get("/")
    async def dashboard():
        """Serve admin dashboard."""
        from fastapi.responses import FileResponse
        return FileResponse("templates/admin_dashboard.html")
    
    # Legacy API compatibility (if needed)
    @app.get("/api/dashboard/health")
    async def legacy_health():
        """Legacy health endpoint for backward compatibility."""
        return await health_check()
    
    # Add Slack integration
    try:
        from slack_bolt import App
        from slack_bolt.adapter.fastapi import SlackRequestHandler
        from slack_handlers import register_handlers
        from fastapi import Request
        
        # Create Slack app
        slack_app = App(
            token=Config.SLACK_BOT_TOKEN,
            signing_secret=Config.SLACK_SIGNING_SECRET,
            process_before_response=True
        )
        
        # Register Slack handlers
        register_handlers(slack_app)
        
        # Create FastAPI handler
        handler = SlackRequestHandler(slack_app)
        
        # Add Slack events endpoint
        @app.post("/slack/events")
        async def slack_events(request: Request):
            """Handle Slack events."""
            try:
                return await handler.handle(request)
            except Exception as e:
                logger.error(f"Error handling Slack event: {e}", exc_info=True)
                return {"error": "Internal server error"}
        
        logger.info("Slack integration added successfully")
        
    except Exception as e:
        logger.warning(f"Slack integration not available: {e}")
    
    logger.info("Agora application created with SOLID architecture")
    return app


# Factory function for different environments
def create_development_app() -> FastAPI:
    """Create app for development environment."""
    return create_app({
        'debug': True,
        'database_url': Config.DATABASE_URL,
        'redis_url': Config.REDIS_URL
    })


def create_production_app() -> FastAPI:
    """Create app for production environment."""
    return create_app({
        'debug': False,
        'database_url': Config.DATABASE_URL,
        'redis_url': Config.REDIS_URL
    })


def create_test_app() -> FastAPI:
    """Create app for testing."""
    from services.factory import create_test_services
    
    app = FastAPI(title="Agora Test")
    
    # Configure test services
    container = get_container()
    create_test_services(container)
    container.initialize()
    
    # Include routers for testing
    app.include_router(auth_router)
    app.include_router(polls_router)
    app.include_router(admin_router)
    
    return app


# Application instance (for backward compatibility)
app = create_app()