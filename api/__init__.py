"""
API module with separated routers following Single Responsibility Principle.
"""

from .auth import router as auth_router
from .polls import router as polls_router
from .admin import router as admin_router

__all__ = ['auth_router', 'polls_router', 'admin_router']