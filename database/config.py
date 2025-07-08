"""
Database configuration module.
Separated from models.py to follow Single Responsibility Principle.
"""

import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from config import Config

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Database configuration and connection management."""
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or Config.DATABASE_URL
        self.engine = None
        self.session_factory = None
        self._initialize_engine()
    
    def _initialize_engine(self):
        """Initialize database engine with appropriate settings."""
        engine_kwargs = {
            'pool_pre_ping': True,  # Validate connections before use
            'pool_recycle': 3600,   # Recycle connections after 1 hour
            'echo': Config.DEBUG,   # Log SQL queries in debug mode
        }
        
        # SQLite specific configuration
        if self.database_url.startswith('sqlite'):
            engine_kwargs.update({
                'poolclass': StaticPool,
                'connect_args': {
                    'check_same_thread': False,
                    'timeout': 30,
                    'isolation_level': None,  # Use autocommit mode
                }
            })
        
        # PostgreSQL specific configuration
        elif self.database_url.startswith('postgresql'):
            engine_kwargs.update({
                'pool_size': 10,
                'max_overflow': 20,
                'pool_timeout': 30,
            })
        
        # MySQL specific configuration
        elif self.database_url.startswith('mysql'):
            engine_kwargs.update({
                'pool_size': 10,
                'max_overflow': 20,
                'pool_timeout': 30,
                'connect_args': {
                    'charset': 'utf8mb4',
                    'use_unicode': True,
                }
            })
        
        self.engine = create_engine(self.database_url, **engine_kwargs)
        self.session_factory = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        logger.info(f"Database engine initialized for: {self.database_url}")
    
    @contextmanager
    def get_session(self) -> Session:
        """Get database session with automatic cleanup."""
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def create_tables(self) -> None:
        """Create all database tables."""
        from models import Base
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created")
    
    def drop_tables(self) -> None:
        """Drop all database tables."""
        from models import Base
        Base.metadata.drop_all(bind=self.engine)
        logger.info("Database tables dropped")
    
    def health_check(self) -> bool:
        """Check database connectivity."""
        try:
            with self.get_session() as session:
                session.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    def get_connection_info(self) -> dict:
        """Get database connection information."""
        return {
            'url': self.database_url,
            'driver': self.engine.driver,
            'pool_size': getattr(self.engine.pool, 'size', None),
            'checked_out': getattr(self.engine.pool, 'checkedout', None),
            'overflow': getattr(self.engine.pool, 'overflow', None),
        }


# Global database configuration instance
_db_config = None


def get_db_config() -> DatabaseConfig:
    """Get the global database configuration."""
    global _db_config
    if _db_config is None:
        _db_config = DatabaseConfig()
    return _db_config


def get_db_session() -> Session:
    """Get database session (legacy function for backward compatibility)."""
    return get_db_config().session_factory()


def get_db():
    """Dependency injection compatible database session generator."""
    config = get_db_config()
    session = config.session_factory()
    try:
        yield session
    finally:
        session.close()