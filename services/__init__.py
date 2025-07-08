"""
Services module for dependency injection and service abstractions.
"""

from .abstractions import (
    DatabaseService, CacheService, PollRepository, EventPublisher,
    NotificationService, SearchService, ExportService, ValidationService,
    AuthenticationService, SchedulerService, TemplateService,
    ConfigurationService, MonitoringService,
    PollData, UserData, NotificationData, ExportOptions
)

from .implementations import (
    SQLAlchemyDatabaseService, RedisCacheService, SQLAlchemyPollRepository,
    SimpleEventPublisher, SimpleNotificationService, SimpleValidationService,
    SimpleAuthenticationService, SimpleConfigurationService, SimpleMonitoringService
)

from .container import (
    ServiceContainer, ServiceRegistry, ServiceNotFoundError,
    get_container, inject, get_service, get_optional_service,
    has_service, service_initializer, service_scope
)

from .factory import configure_services

__all__ = [
    # Abstractions
    'DatabaseService', 'CacheService', 'PollRepository', 'EventPublisher',
    'NotificationService', 'SearchService', 'ExportService', 'ValidationService',
    'AuthenticationService', 'SchedulerService', 'TemplateService',
    'ConfigurationService', 'MonitoringService',
    'PollData', 'UserData', 'NotificationData', 'ExportOptions',
    
    # Implementations
    'SQLAlchemyDatabaseService', 'RedisCacheService', 'SQLAlchemyPollRepository',
    'SimpleEventPublisher', 'SimpleNotificationService', 'SimpleValidationService',
    'SimpleAuthenticationService', 'SimpleConfigurationService', 'SimpleMonitoringService',
    
    # Container
    'ServiceContainer', 'ServiceRegistry', 'ServiceNotFoundError',
    'get_container', 'inject', 'get_service', 'get_optional_service',
    'has_service', 'service_initializer', 'service_scope',
    
    # Factory
    'configure_services'
]