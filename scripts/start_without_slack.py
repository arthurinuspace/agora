#!/usr/bin/env python3
"""
Startup script without Slack authentication for testing
"""

import sys
import os
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import and run database initialization
exec(open('database.py').read())

# Create a simple FastAPI app without Slack
from config import Config
from api_middleware import APIMiddleware, handle_api_errors
from monitoring import initialize_monitoring, get_metrics, get_health
from dashboard_api import router as dashboard_router

# Initialize monitoring system
system_monitor = initialize_monitoring()

# Create FastAPI app
app = FastAPI(
    title="Agora - Anonymous Voting for Slack",
    version="1.0.0",
    description="Ready for Slack integration testing",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add middleware
app.add_middleware(
    APIMiddleware,
    enable_rate_limiting=True,
    enable_logging=True
)

# Include dashboard API routes
app.include_router(dashboard_router)

@app.get("/")
async def root():
    return {"message": "🚀 Agora is ready for Slack integration!", "status": "ready"}

@app.get("/health")
@handle_api_errors
async def health_check():
    """Health check endpoint."""
    health_status = get_health()
    return health_status

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(get_metrics(), media_type="text/plain")

@app.post("/slack/events")
async def slack_events_placeholder():
    """Placeholder for Slack events - ready for real integration."""
    return {"status": "ready", "message": "Ready for Slack integration"}

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Agora application (without Slack)...")
    print(f"📍 Directory: {current_dir}")
    print(f"🌐 Port: {Config.PORT}")
    print(f"📖 API Docs: http://localhost:{Config.PORT}/docs")
    print("🔗 Ready for ngrok tunnel!")
    
    uvicorn.run(app, host="0.0.0.0", port=Config.PORT, reload=True)