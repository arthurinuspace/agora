"""
Service factory for creating and configuring service instances.
Follows the Factory pattern and Service Locator pattern.
"""

import logging
from typing import Dict, Any, Optional
from config import Config
from .abstractions import (
    DatabaseService, CacheService, PollRepository, EventPublisher,
    NotificationService, SearchService, ExportService, ValidationService,
    AuthenticationService, SchedulerService, TemplateService,
    ConfigurationService, MonitoringService
)
from .implementations import (
    SQLAlchemyDatabaseService, RedisCacheService, SQLAlchemyPollRepository,
    SimpleEventPublisher, SimpleNotificationService, SimpleValidationService,
    SimpleAuthenticationService, SimpleConfigurationService, SimpleMonitoringService
)
from .container import ServiceContainer

logger = logging.getLogger(__name__)


class ServiceFactory:
    """Factory for creating service instances."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._created_services: Dict[str, Any] = {}
    
    def create_database_service(self) -> DatabaseService:
        """Create database service instance."""
        if 'database' not in self._created_services:
            database_url = self.config.get('database_url', Config.DATABASE_URL)
            service = SQLAlchemyDatabaseService(database_url)
            self._created_services['database'] = service
            logger.info("Database service created")
        
        return self._created_services['database']
    
    def create_cache_service(self) -> CacheService:
        """Create cache service instance."""
        if 'cache' not in self._created_services:
            redis_url = self.config.get('redis_url', Config.REDIS_URL)
            service = RedisCacheService(redis_url)
            self._created_services['cache'] = service
            logger.info("Cache service created")
        
        return self._created_services['cache']
    
    def create_poll_repository(self) -> PollRepository:
        """Create poll repository instance."""
        if 'poll_repository' not in self._created_services:
            db_service = self.create_database_service()
            service = SQLAlchemyPollRepository(db_service)
            self._created_services['poll_repository'] = service
            logger.info("Poll repository created")
        
        return self._created_services['poll_repository']
    
    def create_event_publisher(self) -> EventPublisher:
        """Create event publisher instance."""
        if 'event_publisher' not in self._created_services:
            service = SimpleEventPublisher()
            self._created_services['event_publisher'] = service
            logger.info("Event publisher created")
        
        return self._created_services['event_publisher']
    
    def create_notification_service(self) -> NotificationService:
        """Create notification service instance."""
        if 'notification' not in self._created_services:
            db_service = self.create_database_service()
            service = SimpleNotificationService(db_service)
            self._created_services['notification'] = service
            logger.info("Notification service created")
        
        return self._created_services['notification']
    
    def create_validation_service(self) -> ValidationService:
        """Create validation service instance."""
        if 'validation' not in self._created_services:
            service = SimpleValidationService()
            self._created_services['validation'] = service
            logger.info("Validation service created")
        
        return self._created_services['validation']
    
    def create_authentication_service(self) -> AuthenticationService:
        """Create authentication service instance."""
        if 'authentication' not in self._created_services:
            db_service = self.create_database_service()
            service = SimpleAuthenticationService(db_service)
            self._created_services['authentication'] = service
            logger.info("Authentication service created")
        
        return self._created_services['authentication']
    
    def create_configuration_service(self) -> ConfigurationService:
        """Create configuration service instance."""
        if 'configuration' not in self._created_services:
            service = SimpleConfigurationService()
            self._created_services['configuration'] = service
            logger.info("Configuration service created")
        
        return self._created_services['configuration']
    
    def create_monitoring_service(self) -> MonitoringService:
        """Create monitoring service instance."""
        if 'monitoring' not in self._created_services:
            service = SimpleMonitoringService()
            self._created_services['monitoring'] = service
            logger.info("Monitoring service created")
        
        return self._created_services['monitoring']
    
    def create_export_service(self) -> ExportService:
        """Create export service instance."""
        if 'export' not in self._created_services:
            # Import here to avoid circular imports
            from export_utils import poll_exporter
            
            class ExportServiceAdapter(ExportService):
                """Adapter to make existing export_utils compatible with service interface."""
                
                def export_poll(self, poll_id: int, format_type: str, options: Dict[str, Any] = None) -> bytes:
                    from export_utils import export_poll_data
                    return export_poll_data(
                        poll_id=poll_id,
                        format_type=format_type,
                        include_voter_ids=options.get('include_voter_ids', False) if options else False,
                        include_analytics=options.get('include_analytics', True) if options else True,
                        anonymize=options.get('anonymize', True) if options else True
                    )
                
                def export_multiple_polls(self, poll_ids: list, format_type: str, options: Dict[str, Any] = None) -> bytes:
                    from export_utils import export_multiple_polls_data
                    return export_multiple_polls_data(
                        poll_ids=poll_ids,
                        format_type=format_type,
                        include_analytics=options.get('include_analytics', True) if options else True,
                        anonymize=options.get('anonymize', True) if options else True
                    )
                
                def get_supported_formats(self) -> list:
                    from export_utils import get_supported_export_formats
                    return get_supported_export_formats()
            
            service = ExportServiceAdapter()
            self._created_services['export'] = service
            logger.info("Export service created")
        
        return self._created_services['export']
    
    def create_search_service(self) -> SearchService:
        """Create search service instance."""
        if 'search' not in self._created_services:
            # Import here to avoid circular imports
            from search_utils import search_engine
            
            class SearchServiceAdapter(SearchService):
                """Adapter to make existing search_utils compatible with service interface."""
                
                def search_polls(self, query: str, filters: Dict[str, Any] = None) -> list:
                    from search_utils import search_polls
                    results, total = search_polls(
                        team_id=filters.get('team_id', '') if filters else '',
                        query=query,
                        search_type=filters.get('search_type', 'all') if filters else 'all',
                        filters=filters or {}
                    )
                    return results
                
                def index_poll(self, poll_id: int, poll_data: Dict[str, Any]) -> bool:
                    # In a real implementation, this would index the poll
                    return True
                
                def remove_from_index(self, poll_id: int) -> bool:
                    # In a real implementation, this would remove from index
                    return True
            
            service = SearchServiceAdapter()
            self._created_services['search'] = service
            logger.info("Search service created")
        
        return self._created_services['search']
    
    def create_template_service(self) -> TemplateService:
        """Create template service instance."""
        if 'template' not in self._created_services:
            # Import here to avoid circular imports
            from templates import template_manager
            
            class TemplateServiceAdapter(TemplateService):
                """Adapter to make existing template system compatible with service interface."""
                
                def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
                    from templates import get_template_by_id
                    template = get_template_by_id(template_id)
                    if template:
                        return {
                            'id': template.id,
                            'name': template.name,
                            'description': template.description,
                            'category': template.category.value,
                            'question': template.question,
                            'options': template.options,
                            'vote_type': template.vote_type,
                            'tags': template.tags,
                            'usage_count': template.usage_count
                        }
                    return None
                
                def get_templates_by_category(self, category: str) -> list:
                    from templates import get_templates_by_category
                    templates = get_templates_by_category(category)
                    return [
                        {
                            'id': t.id,
                            'name': t.name,
                            'description': t.description,
                            'category': t.category.value,
                            'question': t.question,
                            'options': t.options,
                            'vote_type': t.vote_type,
                            'tags': t.tags,
                            'usage_count': t.usage_count
                        }
                        for t in templates
                    ]
                
                def create_template(self, template_data: Dict[str, Any]) -> str:
                    # In a real implementation, this would create a new template
                    return f"template_{hash(str(template_data))}"
            
            service = TemplateServiceAdapter()
            self._created_services['template'] = service
            logger.info("Template service created")
        
        return self._created_services['template']
    
    def create_scheduler_service(self) -> SchedulerService:
        """Create scheduler service instance."""
        if 'scheduler' not in self._created_services:
            # Import here to avoid circular imports
            from scheduler import poll_scheduler
            
            class SchedulerServiceAdapter(SchedulerService):
                """Adapter to make existing scheduler compatible with service interface."""
                
                def schedule_job(self, job_id: str, run_time, job_data: Dict[str, Any]) -> bool:
                    from scheduler import schedule_poll_creation
                    return schedule_poll_creation(
                        schedule_id=job_id,
                        team_id=job_data.get('team_id'),
                        channel_id=job_data.get('channel_id'),
                        creator_id=job_data.get('creator_id'),
                        poll_data=job_data.get('poll_data'),
                        schedule_type='once',
                        scheduled_time=run_time
                    )
                
                def cancel_job(self, job_id: str) -> bool:
                    from scheduler import cancel_scheduled_poll
                    return cancel_scheduled_poll(job_id)
                
                def list_jobs(self, team_id: str = None) -> list:
                    from scheduler import get_scheduled_polls
                    jobs = get_scheduled_polls(team_id)
                    return [
                        {
                            'id': job.id,
                            'team_id': job.team_id,
                            'action': job.action,
                            'scheduled_time': job.scheduled_time,
                            'is_active': job.is_active
                        }
                        for job in jobs
                    ]
            
            service = SchedulerServiceAdapter()
            self._created_services['scheduler'] = service
            logger.info("Scheduler service created")
        
        return self._created_services['scheduler']
    
    def get_created_services(self) -> Dict[str, Any]:
        """Get all created services."""
        return self._created_services.copy()
    
    def reset(self) -> None:
        """Reset factory (for testing)."""
        self._created_services.clear()
        logger.info("Service factory reset")


def configure_services(container: ServiceContainer, config: Optional[Dict[str, Any]] = None) -> None:
    """Configure services in the container."""
    factory = ServiceFactory(config)
    
    # Register services as singletons
    container.register_singleton(DatabaseService, factory.create_database_service())
    container.register_singleton(CacheService, factory.create_cache_service())
    container.register_singleton(PollRepository, factory.create_poll_repository())
    container.register_singleton(EventPublisher, factory.create_event_publisher())
    container.register_singleton(NotificationService, factory.create_notification_service())
    container.register_singleton(ValidationService, factory.create_validation_service())
    container.register_singleton(AuthenticationService, factory.create_authentication_service())
    container.register_singleton(ConfigurationService, factory.create_configuration_service())
    container.register_singleton(MonitoringService, factory.create_monitoring_service())
    container.register_singleton(ExportService, factory.create_export_service())
    container.register_singleton(SearchService, factory.create_search_service())
    container.register_singleton(TemplateService, factory.create_template_service())
    container.register_singleton(SchedulerService, factory.create_scheduler_service())
    
    logger.info("All services configured in container")


def create_test_services(container: ServiceContainer) -> None:
    """Create test services for testing."""
    # Create mock services for testing
    class MockDatabaseService(DatabaseService):
        def get_session(self): pass
        def create_tables(self): pass
        def health_check(self): return True
    
    class MockCacheService(CacheService):
        def get(self, key): return None
        def set(self, key, value, ttl=300): return True
        def delete(self, key): return True
        def exists(self, key): return False
        def health_check(self): return True
    
    # Register mock services
    container.register_singleton(DatabaseService, MockDatabaseService())
    container.register_singleton(CacheService, MockCacheService())
    
    logger.info("Test services configured")