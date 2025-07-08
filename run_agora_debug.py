#!/usr/bin/env python3
"""
Debug version of Agora startup with detailed logging
"""

import sys
import os
import logging
from pathlib import Path

# 設置詳細日誌
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('agora_debug.log')
    ]
)
logger = logging.getLogger(__name__)

def main():
    try:
        # 添加當前目錄到 Python 路徑
        current_dir = Path(__file__).parent.absolute()
        sys.path.insert(0, str(current_dir))
        
        logger.info(f"🚀 Starting Agora DEBUG mode from: {current_dir}")
        
        # 初始化數據庫
        logger.info("📊 Initializing database...")
        from database import init_database
        init_database()
        
        # 創建應用程式
        logger.info("🎯 Creating application...")
        from app_factory import create_development_app
        app = create_development_app()
        
        # 啟動服務器
        logger.info("🌐 Starting server in DEBUG mode...")
        import uvicorn
        from config import Config
        
        logger.info(f"🤖 Slack Bot Token: {Config.SLACK_BOT_TOKEN[:20]}...")
        logger.info(f"🔐 Slack Signing Secret: {Config.SLACK_SIGNING_SECRET[:10]}...")
        logger.info(f"📍 Server starting on: http://0.0.0.0:{Config.PORT}")
        logger.info(f"📖 API Docs: http://localhost:{Config.PORT}/docs")
        logger.info("🔍 Debug logs will be shown in real-time")
        
        # 設置 Slack Bolt 的日誌級別
        logging.getLogger("slack_bolt").setLevel(logging.DEBUG)
        logging.getLogger("slack_sdk").setLevel(logging.DEBUG)
        
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=Config.PORT, 
            reload=False,
            log_level="debug",
            access_log=True
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to start Agora: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()