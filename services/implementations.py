"""
Concrete implementations of service abstractions.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import redis
from contextlib import contextmanager

from .abstractions import (
    DatabaseService, CacheService, PollRepository, EventPublisher,
    NotificationService, SearchService, ExportService, ValidationService,
    AuthenticationService, SchedulerService, TemplateService,
    ConfigurationService, MonitoringService
)
from config import Config

logger = logging.getLogger(__name__)


class SQLAlchemyDatabaseService(DatabaseService):
    """SQLAlchemy implementation of database service."""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = None
        self.session_factory = None
        self._initialize_engine()
    
    def _initialize_engine(self):
        """Initialize database engine."""
        engine_kwargs = {
            'pool_pre_ping': True,
            'pool_recycle': 3600,
            'echo': Config.DEBUG,
        }
        
        if self.database_url.startswith('sqlite'):
            engine_kwargs.update({
                'connect_args': {
                    'check_same_thread': False,
                    'timeout': 30,
                }
            })
        
        self.engine = create_engine(self.database_url, **engine_kwargs)
        self.session_factory = sessionmaker(bind=self.engine)
    
    @contextmanager
    def get_session(self) -> Session:
        """Get database session with context manager."""
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
        """Create database tables."""
        from models import Base
        Base.metadata.create_all(bind=self.engine)
    
    def health_check(self) -> bool:
        """Check database health."""
        try:
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


class RedisCacheService(CacheService):
    """Redis implementation of cache service."""
    
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.client = redis.from_url(redis_url, decode_responses=True)
    
    def get(self, key: str) -> Any:
        """Get value from cache."""
        try:
            value = self.client.get(key)
            if value is None:
                return None
            return json.loads(value)
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set value in cache."""
        try:
            serialized = json.dumps(value, default=str)
            return self.client.setex(key, ttl, serialized)
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            return bool(self.client.delete(key))
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            return bool(self.client.exists(key))
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    def health_check(self) -> bool:
        """Check cache health."""
        try:
            return self.client.ping()
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return False


class SimpleCacheService(CacheService):
    """Simple in-memory cache service for testing."""
    
    def __init__(self):
        self._cache = {}
    
    def get(self, key: str) -> Any:
        """Get value from cache."""
        if not key:
            raise ValueError("Key cannot be empty")
        return self._cache.get(key)
    
    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set value in cache."""
        if not key:
            raise ValueError("Key cannot be empty")
        if key is None:
            raise ValueError("Key cannot be None")
        self._cache[key] = value
        return True
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not key:
            return False
        return self._cache.pop(key, None) is not None
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not key:
            return False
        return key in self._cache
    
    def health_check(self) -> Dict[str, Any]:
        """Check cache health."""
        return {
            'cache': {
                'status': 'healthy',
                'type': 'simple',
                'entries': len(self._cache)
            }
        }


class SQLAlchemyPollRepository(PollRepository):
    """SQLAlchemy implementation of poll repository."""
    
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
    
    def get_poll(self, poll_id: int) -> Optional[Dict[str, Any]]:
        """Get poll by ID."""
        with self.db_service.get_session() as session:
            from models import Poll
            poll = session.query(Poll).filter(Poll.id == poll_id).first()
            if not poll:
                return None
            
            return {
                'id': poll.id,
                'question': poll.question,
                'team_id': poll.team_id,
                'channel_id': poll.channel_id,
                'creator_id': poll.creator_id,
                'vote_type': poll.vote_type,
                'status': poll.status,
                'created_at': poll.created_at,
                'ended_at': poll.ended_at,
                'options': [
                    {
                        'id': opt.id,
                        'text': opt.text,
                        'vote_count': opt.vote_count,
                        'order_index': opt.order_index
                    }
                    for opt in poll.options
                ]
            }
    
    def get_polls(self, team_id: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get polls with filters."""
        with self.db_service.get_session() as session:
            from models import Poll
            query = session.query(Poll).filter(Poll.team_id == team_id)
            
            if filters:
                if 'status' in filters:
                    query = query.filter(Poll.status == filters['status'])
                if 'creator_id' in filters:
                    query = query.filter(Poll.creator_id == filters['creator_id'])
                if 'date_from' in filters:
                    query = query.filter(Poll.created_at >= filters['date_from'])
                if 'date_to' in filters:
                    query = query.filter(Poll.created_at <= filters['date_to'])
            
            polls = query.order_by(Poll.created_at.desc()).all()
            
            return [
                {
                    'id': poll.id,
                    'question': poll.question,
                    'team_id': poll.team_id,
                    'channel_id': poll.channel_id,
                    'creator_id': poll.creator_id,
                    'vote_type': poll.vote_type,
                    'status': poll.status,
                    'created_at': poll.created_at,
                    'ended_at': poll.ended_at,
                    'total_votes': sum(opt.vote_count for opt in poll.options)
                }
                for poll in polls
            ]
    
    def create_poll(self, poll_data: Dict[str, Any]) -> int:
        """Create new poll."""
        with self.db_service.get_session() as session:
            from models import Poll, PollOption
            
            poll = Poll(
                question=poll_data['question'],
                team_id=poll_data['team_id'],
                channel_id=poll_data['channel_id'],
                creator_id=poll_data['creator_id'],
                vote_type=poll_data.get('vote_type', 'single'),
                status=poll_data.get('status', 'active')
            )
            
            session.add(poll)
            session.flush()  # Get the ID
            
            # Add options
            for i, option_text in enumerate(poll_data['options']):
                option = PollOption(
                    poll_id=poll.id,
                    text=option_text,
                    order_index=i
                )
                session.add(option)
            
            return poll.id
    
    def update_poll(self, poll_id: int, updates: Dict[str, Any]) -> bool:
        """Update poll."""
        with self.db_service.get_session() as session:
            from models import Poll
            
            poll = session.query(Poll).filter(Poll.id == poll_id).first()
            if not poll:
                return False
            
            for key, value in updates.items():
                if hasattr(poll, key):
                    setattr(poll, key, value)
            
            return True
    
    def delete_poll(self, poll_id: int) -> bool:
        """Delete poll."""
        with self.db_service.get_session() as session:
            from models import Poll, PollOption, UserVote, VotedUser
            
            # Delete related records
            session.query(UserVote).filter(UserVote.poll_id == poll_id).delete()
            session.query(VotedUser).filter(VotedUser.poll_id == poll_id).delete()
            session.query(PollOption).filter(PollOption.poll_id == poll_id).delete()
            
            # Delete poll
            deleted = session.query(Poll).filter(Poll.id == poll_id).delete()
            
            return deleted > 0


class SimpleEventPublisher(EventPublisher):
    """Simple in-memory event publisher."""
    
    def __init__(self):
        self._handlers: Dict[str, List[callable]] = {}
    
    def publish(self, event_type: str, data: Dict[str, Any]) -> None:
        """Publish event."""
        if event_type in self._handlers:
            for handler in self._handlers[event_type]:
                try:
                    handler(data)
                except Exception as e:
                    logger.error(f"Error in event handler for {event_type}: {e}")
    
    def subscribe(self, event_type: str, handler: callable) -> None:
        """Subscribe to event."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)


class SimpleNotificationService(NotificationService):
    """Simple notification service implementation."""
    
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
    
    def send_notification(self, user_id: str, message: str, notification_type: str) -> bool:
        """Send notification to user."""
        with self.db_service.get_session() as session:
            from models import Notification
            
            notification = Notification(
                user_id=user_id,
                team_id="",  # Would be populated from context
                notification_type=notification_type,
                title=notification_type.title(),
                message=message
            )
            
            session.add(notification)
            return True
    
    def send_bulk_notifications(self, notifications: List[Dict[str, Any]]) -> bool:
        """Send bulk notifications."""
        with self.db_service.get_session() as session:
            from models import Notification
            
            for notif_data in notifications:
                notification = Notification(
                    user_id=notif_data['user_id'],
                    team_id=notif_data.get('team_id', ''),
                    notification_type=notif_data['notification_type'],
                    title=notif_data.get('title', ''),
                    message=notif_data['message']
                )
                session.add(notification)
            
            return True


class SimpleValidationService(ValidationService):
    """Simple validation service implementation."""
    
    def __init__(self):
        self._rules = {}
    
    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data."""
        errors = []
        warnings = []
        
        # Basic validation logic
        if 'question' in data:
            if not data['question'] or len(data['question'].strip()) < 5:
                errors.append("Question must be at least 5 characters long")
        
        if 'options' in data:
            if not data['options'] or len(data['options']) < 2:
                errors.append("At least 2 options are required")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def get_validation_rules(self) -> Dict[str, Any]:
        """Get validation rules."""
        return self._rules


class SimpleAuthenticationService(AuthenticationService):
    """Simple authentication service implementation."""
    
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
    
    def authenticate_user(self, token: str) -> Optional[Dict[str, Any]]:
        """Authenticate user by token."""
        # Simple mock implementation
        if token:
            return {
                'user_id': 'authenticated_user',
                'team_id': 'authenticated_team',
                'role': 'user'
            }
        return None
    
    def check_permissions(self, user_id: str, resource: str, action: str) -> bool:
        """Check user permissions."""
        # Simple mock implementation
        return True
    
    def get_user_roles(self, user_id: str, team_id: str) -> List[str]:
        """Get user roles."""
        with self.db_service.get_session() as session:
            from models import UserRole
            
            roles = session.query(UserRole).filter(
                UserRole.user_id == user_id,
                UserRole.team_id == team_id,
                UserRole.is_active == True
            ).all()
            
            return [role.role for role in roles]


class SimpleConfigurationService(ConfigurationService):
    """Simple configuration service implementation."""
    
    def __init__(self):
        self._config = {}
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self._config.get(key, default)
    
    def set_config(self, key: str, value: Any) -> bool:
        """Set configuration value."""
        self._config[key] = value
        return True
    
    def validate_config(self) -> Dict[str, Any]:
        """Validate configuration."""
        return {'valid': True, 'errors': [], 'warnings': []}


class SimpleMonitoringService(MonitoringService):
    """Simple monitoring service implementation."""
    
    def __init__(self):
        self._metrics = {}
    
    def record_metric(self, metric_name: str, value: float, tags: Dict[str, str] = None) -> None:
        """Record metric."""
        self._metrics[metric_name] = {
            'value': value,
            'tags': tags or {},
            'timestamp': datetime.now()
        }
    
    def get_metrics(self, metric_name: str = None) -> Dict[str, Any]:
        """Get metrics."""
        if metric_name:
            return self._metrics.get(metric_name, {})
        return self._metrics.copy()
    
    def health_check(self) -> Dict[str, Any]:
        """Get health check status."""
        return {
            'system': {
                'status': 'healthy',
                'timestamp': datetime.now(),
                'metrics_count': len(self._metrics)
            }
        }


class CompositeValidationService(ValidationService):
    """Composite validation service using validation context."""
    
    def __init__(self, validation_context):
        self.validation_context = validation_context
    
    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data using validation context."""
        try:
            if data is None:
                return {'valid': False, 'errors': ['Data cannot be None']}
            
            if not isinstance(data, dict):
                return {'valid': False, 'errors': ['Data must be a dictionary']}
            
            results = self.validation_context.validate(data)
            
            errors = []
            warnings = []
            
            for result in results:
                if result.level.value == 'error':
                    errors.append(result.message)
                elif result.level.value == 'warning':
                    warnings.append(result.message)
            
            return {
                'valid': len(errors) == 0,
                'errors': errors,
                'warnings': warnings
            }
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return {'valid': False, 'errors': [f'Validation failed: {str(e)}']}


class JSONExportService(ExportService):
    """JSON export service using export context."""
    
    def __init__(self, export_context):
        self.export_context = export_context
    
    def export_poll(self, poll_id: int, format_type: str, poll_data: Dict[str, Any] = None, options: Dict[str, Any] = None) -> bytes:
        """Export single poll."""
        try:
            data = {'poll_data': poll_data} if poll_data else {}
            return self.export_context.export(data, format_type, options)
        except Exception as e:
            logger.error(f"Export poll error: {e}")
            return b'{"error": "Export failed"}'
    
    def export_multiple_polls(self, poll_ids: List[int], format_type: str, polls_data: List[Dict[str, Any]] = None, options: Dict[str, Any] = None) -> bytes:
        """Export multiple polls."""
        try:
            data = {'polls_data': polls_data} if polls_data else {}
            return self.export_context.export(data, format_type, options)
        except Exception as e:
            logger.error(f"Export multiple polls error: {e}")
            return b'{"error": "Export failed"}'


class SimpleSearchService(SearchService):
    """Simple search service implementation."""
    
    def __init__(self):
        self._indexed_data = {}
    
    def index_data(self, document_id: str, content: Dict[str, Any]) -> bool:
        """Index data for search."""
        self._indexed_data[document_id] = content
        return True
    
    def search(self, query: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Search indexed data."""
        results = []
        query_lower = query.lower()
        
        for doc_id, content in self._indexed_data.items():
            # Simple text search in content
            content_str = str(content).lower()
            if query_lower in content_str:
                result = content.copy()
                result['document_id'] = doc_id
                results.append(result)
        
        return results
    
    def delete_document(self, document_id: str) -> bool:
        """Delete document from index."""
        return self._indexed_data.pop(document_id, None) is not None