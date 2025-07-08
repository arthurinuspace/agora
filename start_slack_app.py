#!/usr/bin/env python3
"""
啟動 Agora Slack 應用程式
"""

import sys
import os
import uvicorn
from config import Config

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import and run database initialization  
exec(open('database.py').read())

# Import the main app with Slack integration
from app_factory import create_development_app

if __name__ == "__main__":
    print("🚀 Starting Agora with Slack integration...")
    print(f"📍 Directory: {current_dir}")
    print(f"🌐 Port: {Config.PORT}")
    print(f"🤖 Slack Bot Token: {'*' * 20}...")
    print(f"🔐 Slack Signing Secret: {'*' * 10}...")
    print(f"📖 API Docs: http://localhost:{Config.PORT}/docs")
    print("🔗 Ready for ngrok tunnel!")
    
    # Use the factory to create app
    app = create_development_app()
    uvicorn.run(app, host="0.0.0.0", port=Config.PORT, reload=False)