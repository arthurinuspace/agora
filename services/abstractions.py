"""
Service abstractions for dependency injection.
Implements interfaces following SOLID principles.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from sqlalchemy.orm import Session
from dataclasses import dataclass


# Database Service Abstraction
class DatabaseService(ABC):
    """Abstract database service interface."""
    
    @abstractmethod
    def get_session(self) -> Session:
        """Get database session."""
        pass
    
    @abstractmethod
    def create_tables(self) -> None:
        """Create database tables."""
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """Check database health."""
        pass


# Cache Service Abstraction
class CacheService(ABC):
    """Abstract cache service interface."""
    
    @abstractmethod
    def get(self, key: str) -> Any:
        """Get value from cache."""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set value in cache."""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """Check cache health."""
        pass


# Poll Repository Abstraction
class PollRepository(ABC):
    """Abstract poll repository interface."""
    
    @abstractmethod
    def get_poll(self, poll_id: int) -> Optional[Dict[str, Any]]:
        """Get poll by ID."""
        pass
    
    @abstractmethod
    def get_polls(self, team_id: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get polls with filters."""
        pass
    
    @abstractmethod
    def create_poll(self, poll_data: Dict[str, Any]) -> int:
        """Create new poll."""
        pass
    
    @abstractmethod
    def update_poll(self, poll_id: int, updates: Dict[str, Any]) -> bool:
        """Update poll."""
        pass
    
    @abstractmethod
    def delete_poll(self, poll_id: int) -> bool:
        """Delete poll."""
        pass


# Event Publisher Abstraction
class EventPublisher(ABC):
    """Abstract event publisher interface."""
    
    @abstractmethod
    def publish(self, event_type: str, data: Dict[str, Any]) -> None:
        """Publish event."""
        pass
    
    @abstractmethod
    def subscribe(self, event_type: str, handler: callable) -> None:
        """Subscribe to event."""
        pass


# Notification Service Abstraction
class NotificationService(ABC):
    """Abstract notification service interface."""
    
    @abstractmethod
    def send_notification(self, user_id: str, message: str, notification_type: str) -> bool:
        """Send notification to user."""
        pass
    
    @abstractmethod
    def send_bulk_notifications(self, notifications: List[Dict[str, Any]]) -> bool:
        """Send bulk notifications."""
        pass


# Search Service Abstraction
class SearchService(ABC):
    """Abstract search service interface."""
    
    @abstractmethod
    def search_polls(self, query: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Search polls."""
        pass
    
    @abstractmethod
    def index_poll(self, poll_id: int, poll_data: Dict[str, Any]) -> bool:
        """Index poll for search."""
        pass
    
    @abstractmethod
    def remove_from_index(self, poll_id: int) -> bool:
        """Remove poll from search index."""
        pass


# Export Service Abstraction
class ExportService(ABC):
    """Abstract export service interface."""
    
    @abstractmethod
    def export_poll(self, poll_id: int, format_type: str, options: Dict[str, Any] = None) -> bytes:
        """Export single poll."""
        pass
    
    @abstractmethod
    def export_multiple_polls(self, poll_ids: List[int], format_type: str, options: Dict[str, Any] = None) -> bytes:
        """Export multiple polls."""
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """Get supported export formats."""
        pass


# Validation Service Abstraction
class ValidationService(ABC):
    """Abstract validation service interface."""
    
    @abstractmethod
    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data."""
        pass
    
    @abstractmethod
    def get_validation_rules(self) -> Dict[str, Any]:
        """Get validation rules."""
        pass


# Authentication Service Abstraction
class AuthenticationService(ABC):
    """Abstract authentication service interface."""
    
    @abstractmethod
    def authenticate_user(self, token: str) -> Optional[Dict[str, Any]]:
        """Authenticate user by token."""
        pass
    
    @abstractmethod
    def check_permissions(self, user_id: str, resource: str, action: str) -> bool:
        """Check user permissions."""
        pass
    
    @abstractmethod
    def get_user_roles(self, user_id: str, team_id: str) -> List[str]:
        """Get user roles."""
        pass


# Scheduler Service Abstraction
class SchedulerService(ABC):
    """Abstract scheduler service interface."""
    
    @abstractmethod
    def schedule_job(self, job_id: str, run_time: datetime, job_data: Dict[str, Any]) -> bool:
        """Schedule a job."""
        pass
    
    @abstractmethod
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a scheduled job."""
        pass
    
    @abstractmethod
    def list_jobs(self, team_id: str = None) -> List[Dict[str, Any]]:
        """List scheduled jobs."""
        pass


# Template Service Abstraction
class TemplateService(ABC):
    """Abstract template service interface."""
    
    @abstractmethod
    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get template by ID."""
        pass
    
    @abstractmethod
    def get_templates_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get templates by category."""
        pass
    
    @abstractmethod
    def create_template(self, template_data: Dict[str, Any]) -> str:
        """Create new template."""
        pass


# Configuration Service Abstraction
class ConfigurationService(ABC):
    """Abstract configuration service interface."""
    
    @abstractmethod
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        pass
    
    @abstractmethod
    def set_config(self, key: str, value: Any) -> bool:
        """Set configuration value."""
        pass
    
    @abstractmethod
    def validate_config(self) -> Dict[str, Any]:
        """Validate configuration."""
        pass


# Monitoring Service Abstraction
class MonitoringService(ABC):
    """Abstract monitoring service interface."""
    
    @abstractmethod
    def record_metric(self, metric_name: str, value: float, tags: Dict[str, str] = None) -> None:
        """Record metric."""
        pass
    
    @abstractmethod
    def get_metrics(self, metric_name: str = None) -> Dict[str, Any]:
        """Get metrics."""
        pass
    
    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Get health check status."""
        pass


# Data Transfer Objects
@dataclass
class PollData:
    """Poll data transfer object."""
    question: str
    options: List[str]
    vote_type: str
    team_id: str
    channel_id: str
    creator_id: str
    status: str = "active"


@dataclass
class UserData:
    """User data transfer object."""
    user_id: str
    team_id: str
    role: str
    permissions: List[str]


@dataclass
class NotificationData:
    """Notification data transfer object."""
    user_id: str
    message: str
    notification_type: str
    title: str = ""
    data: Dict[str, Any] = None


@dataclass
class ExportOptions:
    """Export options data transfer object."""
    include_voter_ids: bool = False
    include_analytics: bool = True
    anonymize: bool = True
    include_timestamps: bool = True