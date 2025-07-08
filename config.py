import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
    SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")
    SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./agora.db")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    PORT = int(os.getenv("PORT", 8000))
    NGROK_URL = os.getenv("NGROK_URL")
    
    @classmethod
    def validate(cls):
        required_vars = ["SLACK_BOT_TOKEN", "SLACK_SIGNING_SECRET"]
        missing_vars = [var for var in required_vars if not getattr(cls, var)]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True