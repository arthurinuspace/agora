"""
Tests for SOLID architecture implementation.
"""

import pytest
from unittest.mock import Mock, patch
from services import (
    ServiceContainer, DatabaseService, CacheService, PollRepository,
    ValidationService, ExportService, get_container
)
from services.factory import ServiceFactory, configure_services
from strategies import ValidationContext, ExportContext
from api import auth_router, polls_router, admin_router
from app_factory import create_test_app


class TestDependencyInjection:
    """Test dependency injection container."""
    
    def test_service_container_registration(self):
        """Test service registration in container."""
        container = ServiceContainer()
        
        # Test singleton registration
        mock_service = Mock()
        container.register_singleton(DatabaseService, mock_service)
        
        retrieved = container.get(DatabaseService)
        assert retrieved is mock_service
    
    def test_service_container_factory(self):
        """Test factory registration in container."""
        container = ServiceContainer()
        
        def create_mock_service():
            return Mock()
        
        container.register_factory(CacheService, create_mock_service)
        
        service1 = container.get(CacheService)
        service2 = container.get(CacheService)
        
        # Factory should create new instances
        assert service1 is not service2
    
    def test_service_not_found(self):
        """Test service not found error."""
        container = ServiceContainer()
        
        with pytest.raises(Exception):  # ServiceNotFoundError
            container.get(DatabaseService)
    
    def test_service_override(self):
        """Test service override for testing."""
        container = ServiceContainer()
        original_service = Mock()
        override_service = Mock()
        
        container.register_singleton(DatabaseService, original_service)
        
        with container.override(DatabaseService, override_service):
            assert container.get(DatabaseService) is override_service
        
        assert container.get(DatabaseService) is original_service


class TestServiceAbstractions:
    """Test service abstractions."""
    
    def test_database_service_interface(self):
        """Test database service follows interface."""
        from services.implementations import SQLAlchemyDatabaseService
        
        service = SQLAlchemyDatabaseService("sqlite:///test.db")
        
        # Test interface methods exist
        assert hasattr(service, 'get_session')
        assert hasattr(service, 'create_tables')
        assert hasattr(service, 'health_check')
    
    def test_cache_service_interface(self):
        """Test cache service follows interface."""
        from services.implementations import RedisCacheService
        
        # Mock Redis for testing
        with patch('redis.from_url') as mock_redis:
            mock_client = Mock()
            mock_redis.return_value = mock_client
            
            service = RedisCacheService("redis://localhost")
            
            # Test interface methods exist
            assert hasattr(service, 'get')
            assert hasattr(service, 'set')
            assert hasattr(service, 'delete')
            assert hasattr(service, 'exists')
            assert hasattr(service, 'health_check')
    
    def test_poll_repository_interface(self):
        """Test poll repository follows interface."""
        from services.implementations import SQLAlchemyPollRepository
        
        mock_db_service = Mock()
        service = SQLAlchemyPollRepository(mock_db_service)
        
        # Test interface methods exist
        assert hasattr(service, 'get_poll')
        assert hasattr(service, 'get_polls')
        assert hasattr(service, 'create_poll')
        assert hasattr(service, 'update_poll')
        assert hasattr(service, 'delete_poll')


class TestValidationStrategies:
    """Test validation strategies."""
    
    def test_validation_context(self):
        """Test validation context management."""
        context = ValidationContext()
        
        # Test default strategies are loaded
        strategy_names = context.get_strategy_names()
        assert 'poll_question_validation' in strategy_names
        assert 'poll_options_validation' in strategy_names
        assert 'security_validation' in strategy_names
    
    def test_poll_question_validation(self):
        """Test poll question validation strategy."""
        from strategies.validation import PollQuestionValidationStrategy
        
        strategy = PollQuestionValidationStrategy()
        
        # Test valid question
        results = strategy.validate({'question': 'What is your favorite color?'})
        errors = [r for r in results if r.level.value == 'error']
        assert len(errors) == 0
        
        # Test invalid question (too short)
        results = strategy.validate({'question': 'Hi?'})
        errors = [r for r in results if r.level.value == 'error']
        assert len(errors) > 0
        assert any('too short' in r.message.lower() for r in errors)
    
    def test_poll_options_validation(self):
        """Test poll options validation strategy."""
        from strategies.validation import PollOptionsValidationStrategy
        
        strategy = PollOptionsValidationStrategy()
        
        # Test valid options
        results = strategy.validate({'options': ['Yes', 'No', 'Maybe']})
        errors = [r for r in results if r.level.value == 'error']
        assert len(errors) == 0
        
        # Test invalid options (too few)
        results = strategy.validate({'options': ['Yes']})
        errors = [r for r in results if r.level.value == 'error']
        assert len(errors) > 0
        assert any('at least' in r.message.lower() for r in errors)
    
    def test_security_validation(self):
        """Test security validation strategy."""
        from strategies.validation import SecurityValidationStrategy
        
        strategy = SecurityValidationStrategy()
        
        # Test safe content
        results = strategy.validate({
            'question': 'What is your favorite color?',
            'options': ['Red', 'Blue', 'Green']
        })
        errors = [r for r in results if r.level.value == 'error']
        assert len(errors) == 0
        
        # Test potentially harmful content
        results = strategy.validate({
            'question': 'Click here: <script>alert("xss")</script>',
            'options': ['Yes', 'No']
        })
        errors = [r for r in results if r.level.value == 'error']
        assert len(errors) > 0
        assert any('harmful' in r.message.lower() for r in errors)


class TestExportStrategies:
    """Test export strategies."""
    
    def test_export_context(self):
        """Test export context management."""
        context = ExportContext()
        
        # Test default strategies are loaded
        formats = context.get_supported_formats()
        format_names = [f['name'] for f in formats]
        assert 'CSV' in format_names
        assert 'JSON' in format_names
        assert 'Excel' in format_names
    
    def test_csv_export_strategy(self):
        """Test CSV export strategy."""
        from strategies.export import CSVExportStrategy
        
        strategy = CSVExportStrategy()
        
        # Test single poll export
        data = {
            'poll_data': {
                'id': 1,
                'question': 'Test question?',
                'vote_type': 'single',
                'status': 'active',
                'options': [
                    {'text': 'Option 1', 'vote_count': 5},
                    {'text': 'Option 2', 'vote_count': 3}
                ]
            }
        }
        
        result = strategy.export(data)
        assert isinstance(result, bytes)
        
        # Check CSV content
        csv_content = result.decode('utf-8')
        assert 'Test question?' in csv_content
        assert 'Option 1' in csv_content
        assert 'Option 2' in csv_content
    
    def test_json_export_strategy(self):
        """Test JSON export strategy."""
        from strategies.export import JSONExportStrategy
        import json
        
        strategy = JSONExportStrategy()
        
        # Test single poll export
        data = {
            'poll_data': {
                'id': 1,
                'question': 'Test question?',
                'vote_type': 'single',
                'options': [
                    {'text': 'Option 1', 'vote_count': 5}
                ]
            }
        }
        
        result = strategy.export(data)
        assert isinstance(result, bytes)
        
        # Check JSON structure
        json_data = json.loads(result.decode('utf-8'))
        assert 'poll' in json_data
        assert 'exported_at' in json_data
        assert json_data['poll']['question'] == 'Test question?'


class TestAPIModules:
    """Test API module separation."""
    
    def test_auth_router_exists(self):
        """Test auth router is properly separated."""
        assert auth_router is not None
        assert auth_router.prefix == "/api/auth"
    
    def test_polls_router_exists(self):
        """Test polls router is properly separated."""
        assert polls_router is not None
        assert polls_router.prefix == "/api/polls"
    
    def test_admin_router_exists(self):
        """Test admin router is properly separated."""
        assert admin_router is not None
        assert admin_router.prefix == "/api/admin"


class TestApplicationFactory:
    """Test application factory."""
    
    def test_create_test_app(self):
        """Test test application creation."""
        app = create_test_app()
        
        assert app is not None
        assert app.title == "Agora Test"
    
    def test_app_routes_included(self):
        """Test that all routes are included in app."""
        app = create_test_app()
        
        # Get all route paths
        routes = [route.path for route in app.routes]
        
        # Check that API routes are included
        api_routes = [r for r in routes if r.startswith('/api/')]
        assert len(api_routes) > 0
        
        # Check specific route patterns
        auth_routes = [r for r in routes if r.startswith('/api/auth')]
        polls_routes = [r for r in routes if r.startswith('/api/polls')]
        admin_routes = [r for r in routes if r.startswith('/api/admin')]
        
        assert len(auth_routes) > 0
        assert len(polls_routes) > 0
        assert len(admin_routes) > 0


class TestSOLIDPrinciples:
    """Test SOLID principles compliance."""
    
    def test_single_responsibility(self):
        """Test modules follow Single Responsibility Principle."""
        # Each API module should handle only its specific domain
        from api.auth import router as auth_router
        from api.polls import router as polls_router
        from api.admin import router as admin_router
        
        # Check route prefixes indicate focused responsibility
        assert auth_router.prefix == "/api/auth"
        assert polls_router.prefix == "/api/polls"
        assert admin_router.prefix == "/api/admin"
    
    def test_open_closed_principle(self):
        """Test system is open for extension, closed for modification."""
        # Validation strategies can be added without modifying existing code
        context = ValidationContext()
        initial_count = len(context.get_strategy_names())
        
        # Add custom strategy
        class CustomValidationStrategy:
            def validate(self, data):
                return []
            def get_name(self):
                return "custom_validation"
        
        context.add_strategy(CustomValidationStrategy())
        assert len(context.get_strategy_names()) == initial_count + 1
        
        # Export strategies can be added without modifying existing code
        export_context = ExportContext()
        initial_formats = len(export_context.get_supported_formats())
        
        # Add custom export strategy
        class CustomExportStrategy:
            def export(self, data, options=None):
                return b"custom format"
            def get_format_name(self):
                return "CUSTOM"
            def get_file_extension(self):
                return "custom"
            def get_mime_type(self):
                return "application/custom"
        
        export_context.add_strategy(CustomExportStrategy())
        assert len(export_context.get_supported_formats()) == initial_formats + 1
    
    def test_dependency_inversion(self):
        """Test high-level modules depend on abstractions."""
        # Service factory creates concrete implementations
        # but returns abstract interfaces
        factory = ServiceFactory()
        
        db_service = factory.create_database_service()
        assert isinstance(db_service, DatabaseService)  # Abstract interface
        
        cache_service = factory.create_cache_service()
        assert isinstance(cache_service, CacheService)  # Abstract interface


# Integration test
def test_full_solid_architecture():
    """Test complete SOLID architecture integration."""
    # Create container and configure services
    container = ServiceContainer()
    configure_services(container)
    
    # Test that all services are properly configured
    services_to_test = [
        DatabaseService, CacheService, PollRepository,
        ValidationService, ExportService
    ]
    
    for service_type in services_to_test:
        service = container.get_optional(service_type)
        assert service is not None, f"Service {service_type.__name__} not configured"
    
    # Test validation with strategies
    validation_context = ValidationContext()
    validation_result = validation_context.validate({
        'question': 'What is your favorite programming language?',
        'options': ['Python', 'JavaScript', 'Java', 'Go'],
        'vote_type': 'single',
        'user_id': 'test_user',
        'team_id': 'test_team'
    })
    
    # Should pass validation
    errors = [r for r in validation_result if r.level.value == 'error']
    assert len(errors) == 0
    
    # Test export with strategies
    export_context = ExportContext()
    test_data = {
        'poll_data': {
            'id': 1,
            'question': 'Test poll?',
            'options': [{'text': 'Yes', 'vote_count': 1}]
        }
    }
    
    # Should be able to export in all supported formats
    for format_info in export_context.get_supported_formats():
        format_name = format_info['name']
        result = export_context.export(test_data, format_name.lower())
        assert isinstance(result, bytes)
        assert len(result) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])