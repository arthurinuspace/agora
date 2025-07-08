"""
Dependency injection container for service management.
Implements the Dependency Inversion Principle.
"""

from typing import Dict, Type, Any, Optional, Callable
from abc import ABC
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class ServiceContainer:
    """Simple dependency injection container."""
    
    def __init__(self):
        self._services: Dict[Type, Any] = {}
        self._singletons: Dict[Type, Any] = {}
        self._factories: Dict[Type, Callable] = {}
        self._initialized = False
    
    def register_singleton(self, interface: Type, implementation: Any) -> None:
        """Register a singleton service."""
        if self._initialized:
            logger.warning(f"Container already initialized, registering {interface.__name__} may not take effect")
        
        self._singletons[interface] = implementation
        logger.debug(f"Registered singleton: {interface.__name__}")
    
    def register_factory(self, interface: Type, factory: Callable) -> None:
        """Register a factory for creating service instances."""
        if self._initialized:
            logger.warning(f"Container already initialized, registering {interface.__name__} may not take effect")
        
        self._factories[interface] = factory
        logger.debug(f"Registered factory: {interface.__name__}")
    
    def register_instance(self, interface: Type, instance: Any) -> None:
        """Register a specific instance."""
        if self._initialized:
            logger.warning(f"Container already initialized, registering {interface.__name__} may not take effect")
        
        self._services[interface] = instance
        logger.debug(f"Registered instance: {interface.__name__}")
    
    def get(self, interface: Type) -> Any:
        """Get service instance by interface."""
        # Check for registered instances first
        if interface in self._services:
            return self._services[interface]
        
        # Check for singletons
        if interface in self._singletons:
            return self._singletons[interface]
        
        # Check for factories
        if interface in self._factories:
            instance = self._factories[interface]()
            logger.debug(f"Created instance from factory: {interface.__name__}")
            return instance
        
        raise ServiceNotFoundError(f"Service not found: {interface.__name__}")
    
    def get_optional(self, interface: Type) -> Optional[Any]:
        """Get service instance, return None if not found."""
        try:
            return self.get(interface)
        except ServiceNotFoundError:
            return None
    
    def has(self, interface: Type) -> bool:
        """Check if service is registered."""
        return (interface in self._services or 
                interface in self._singletons or 
                interface in self._factories)
    
    def initialize(self) -> None:
        """Initialize the container (lock registration)."""
        self._initialized = True
        logger.info("Service container initialized")
    
    def reset(self) -> None:
        """Reset the container (for testing)."""
        self._services.clear()
        self._singletons.clear()
        self._factories.clear()
        self._initialized = False
        logger.info("Service container reset")
    
    def list_services(self) -> Dict[str, str]:
        """List all registered services."""
        services = {}
        
        for interface in self._services:
            services[interface.__name__] = "instance"
        
        for interface in self._singletons:
            services[interface.__name__] = "singleton"
        
        for interface in self._factories:
            services[interface.__name__] = "factory"
        
        return services
    
    @contextmanager
    def override(self, interface: Type, implementation: Any):
        """Temporarily override a service (for testing)."""
        original = self._services.get(interface)
        self._services[interface] = implementation
        try:
            yield
        finally:
            if original is not None:
                self._services[interface] = original
            else:
                self._services.pop(interface, None)


class ServiceNotFoundError(Exception):
    """Exception raised when a service is not found in the container."""
    pass


class ServiceRegistry:
    """Registry for managing service lifecycle."""
    
    def __init__(self, container: ServiceContainer):
        self.container = container
        self._startup_hooks: list = []
        self._shutdown_hooks: list = []
    
    def add_startup_hook(self, hook: Callable) -> None:
        """Add a startup hook."""
        self._startup_hooks.append(hook)
    
    def add_shutdown_hook(self, hook: Callable) -> None:
        """Add a shutdown hook."""
        self._shutdown_hooks.append(hook)
    
    async def startup(self) -> None:
        """Execute startup hooks."""
        for hook in self._startup_hooks:
            try:
                if hasattr(hook, '__call__'):
                    await hook() if hasattr(hook, '__await__') else hook()
                logger.debug(f"Executed startup hook: {hook.__name__}")
            except Exception as e:
                logger.error(f"Error in startup hook {hook.__name__}: {e}")
                raise
    
    async def shutdown(self) -> None:
        """Execute shutdown hooks."""
        for hook in reversed(self._shutdown_hooks):
            try:
                if hasattr(hook, '__call__'):
                    await hook() if hasattr(hook, '__await__') else hook()
                logger.debug(f"Executed shutdown hook: {hook.__name__}")
            except Exception as e:
                logger.error(f"Error in shutdown hook {hook.__name__}: {e}")


# Global container instance
_container = ServiceContainer()


def get_container() -> ServiceContainer:
    """Get the global service container."""
    return _container


def inject(interface: Type) -> Callable:
    """Decorator for dependency injection."""
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            if interface.__name__.lower() not in kwargs:
                kwargs[interface.__name__.lower()] = _container.get(interface)
            return func(*args, **kwargs)
        return wrapper
    return decorator


# Utility functions for common service access
def get_service(interface: Type) -> Any:
    """Get service from global container."""
    return _container.get(interface)


def get_optional_service(interface: Type) -> Optional[Any]:
    """Get service from global container, return None if not found."""
    return _container.get_optional(interface)


def has_service(interface: Type) -> bool:
    """Check if service is registered in global container."""
    return _container.has(interface)


# Service initialization decorator
def service_initializer(interface: Type):
    """Decorator to mark a function as a service initializer."""
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            instance = func(*args, **kwargs)
            _container.register_singleton(interface, instance)
            return instance
        return wrapper
    return decorator


# Context manager for service scope
@contextmanager
def service_scope():
    """Context manager for service scope."""
    try:
        yield _container
    finally:
        # Cleanup logic if needed
        pass