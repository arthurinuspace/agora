from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from slack_bolt import App
from slack_bolt.adapter.fastapi import SlackRequestHandler
from config import Config
import importlib.util
spec = importlib.util.spec_from_file_location("database_module", "database.py")
database_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(database_module)
init_database = database_module.init_database
from slack_handlers import register_handlers
from api_middleware import APIMiddleware, handle_api_errors
from monitoring import initialize_monitoring, get_metrics, get_health, monitor_requests
from dashboard_api import router as dashboard_router
import logging
import os

# Initialize monitoring system
system_monitor = initialize_monitoring()
logger = logging.getLogger(__name__)

try:
    Config.validate()
    init_database()
    logger.info("Application startup successful")
except Exception as e:
    logger.error(f"Application startup failed: {e}")
    raise

slack_app = App(
    token=Config.SLACK_BOT_TOKEN,
    signing_secret=Config.SLACK_SIGNING_SECRET,
    process_before_response=True
)

register_handlers(slack_app)

# Create FastAPI app with enhanced configuration
app = FastAPI(
    title="Agora - Anonymous Voting for Slack",
    version="1.0.0",
    description="Production-ready enterprise Slack workspace application for anonymous voting",
    docs_url="/docs" if Config.DEBUG else None,
    redoc_url="/redoc" if Config.DEBUG else None
)

# Add middleware
app.add_middleware(
    APIMiddleware,
    enable_rate_limiting=True,
    enable_logging=True
)

# Mount static files for dashboard
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Include dashboard API routes
app.include_router(dashboard_router)

handler = SlackRequestHandler(slack_app)

@app.get("/health")
@handle_api_errors
async def health_check():
    """Enhanced health check with detailed system status."""
    health_status = get_health()
    
    if health_status['status'] == 'healthy':
        return health_status
    elif health_status['status'] == 'warning':
        return JSONResponse(status_code=200, content=health_status)
    else:
        return JSONResponse(status_code=503, content=health_status)

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return PlainTextResponse(get_metrics(), media_type="text/plain")

@app.get("/status")
@handle_api_errors
async def system_status():
    """Detailed system status for monitoring."""
    health_status = get_health()
    
    return {
        "application": "Agora",
        "version": "1.0.0",
        "environment": "production" if not Config.DEBUG else "development",
        "health": health_status,
        "uptime": health_status.get('uptime', 0)
    }

@app.get("/admin")
async def admin_dashboard():
    """Serve admin dashboard."""
    template_path = os.path.join(os.path.dirname(__file__), "templates", "admin_dashboard.html")
    if os.path.exists(template_path):
        return FileResponse(template_path)
    else:
        raise HTTPException(status_code=404, detail="Dashboard not found")

@app.post("/slack/events")
@handle_api_errors
@monitor_requests
async def slack_events(request: Request):
    """Handle Slack events with monitoring and error handling."""
    try:
        return await handler.handle(request)
    except Exception as e:
        logger.error(f"Error handling Slack event: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info("Agora application started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("Agora application shutting down")
    if system_monitor:
        system_monitor.stop()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=Config.PORT)