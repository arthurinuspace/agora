"""
Database module for database configuration and management.
"""

from .config import DatabaseConfig, get_db_config, get_db_session, get_db

# Import init_database from the root database.py file
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
try:
    import importlib.util
    spec = importlib.util.spec_from_file_location("db_module", os.path.join(os.path.dirname(os.path.dirname(__file__)), "database.py"))
    db_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(db_module)
    init_database = db_module.init_database
except:
    def init_database():
        """Fallback init function"""
        from sqlalchemy import create_engine
        from models import Base
        from config import Config
        engine = create_engine(Config.DATABASE_URL)
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully")

__all__ = ['DatabaseConfig', 'get_db_config', 'get_db_session', 'get_db', 'init_database']