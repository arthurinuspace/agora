#!/usr/bin/env python3
"""
Simple startup script for Agora application
"""

import sys
import os

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import and run database initialization
exec(open('database.py').read())

# Import main application
from main import app
import uvicorn
from config import Config

if __name__ == "__main__":
    print("🚀 Starting Agora application...")
    print(f"📍 Directory: {current_dir}")
    print(f"🌐 Port: {Config.PORT}")
    print(f"🐛 Debug: {Config.DEBUG}")
    
    uvicorn.run(app, host="0.0.0.0", port=Config.PORT, reload=Config.DEBUG)