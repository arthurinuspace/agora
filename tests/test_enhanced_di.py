"""
增強的依賴注入測試
測試依賴注入容器的進階功能和邊界情況
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import threading
import time
from typing import Dict, Any, Optional

from services import (
    ServiceContainer, DatabaseService, CacheService, PollRepository,
    ValidationService, ExportService, AuthenticationService,
    NotificationService, EventPublisher, MonitoringService,
    ConfigurationService, SearchService, get_service, get_container
)
from services.factory import ServiceFactory, configure_services
from services.implementations import (
    SQLAlchemyDatabaseService, RedisCacheService, SimpleCacheService,
    SQLAlchemyPollRepository, CompositeValidationService,
    JSONExportService, SimpleAuthenticationService,
    SimpleNotificationService, SimpleEventPublisher,
    SimpleMonitoringService, SimpleConfigurationService,
    SimpleSearchService
)


class TestAdvancedDependencyInjection:
    """進階依賴注入測試"""
    
    def test_service_container_lifecycle(self):
        """測試服務容器生命週期管理"""
        container = ServiceContainer()
        
        # 測試服務初始化
        mock_service = Mock()
        container.register_singleton(DatabaseService, mock_service)
        
        # 測試多次獲取返回同一實例
        service1 = container.get(DatabaseService)
        service2 = container.get(DatabaseService)
        assert service1 is service2
        assert service1 is mock_service
    
    def test_service_container_optional_get(self):
        """測試可選服務獲取"""
        container = ServiceContainer()
        
        # 測試獲取未註冊的服務
        service = container.get_optional(DatabaseService)
        assert service is None
        
        # 測試獲取已註冊的服務
        mock_service = Mock()
        container.register_singleton(DatabaseService, mock_service)
        service = container.get_optional(DatabaseService)
        assert service is mock_service
    
    def test_service_container_clear(self):
        """測試服務容器清理"""
        container = ServiceContainer()
        
        # 註冊服務
        mock_service = Mock()
        container.register_singleton(DatabaseService, mock_service)
        
        # 驗證服務存在
        assert container.get_optional(DatabaseService) is not None
        
        # 清理容器
        container.clear()
        
        # 驗證服務被清理
        assert container.get_optional(DatabaseService) is None
    
    def test_service_container_nested_overrides(self):
        """測試嵌套服務覆寫"""
        container = ServiceContainer()
        
        original_service = Mock()
        override_service1 = Mock()
        override_service2 = Mock()
        
        container.register_singleton(DatabaseService, original_service)
        
        # 測試嵌套覆寫
        with container.override(DatabaseService, override_service1):
            assert container.get(DatabaseService) is override_service1
            
            with container.override(DatabaseService, override_service2):
                assert container.get(DatabaseService) is override_service2
            
            # 內層覆寫結束後，應該回到第一層覆寫
            assert container.get(DatabaseService) is override_service1
        
        # 所有覆寫結束後，應該回到原始服務
        assert container.get(DatabaseService) is original_service
    
    def test_service_container_thread_safety(self):
        """測試服務容器線程安全"""
        container = ServiceContainer()
        
        # 創建一個需要初始化的服務
        class SlowInitService:
            def __init__(self):
                time.sleep(0.1)  # 模擬慢初始化
                self.initialized = True
        
        container.register_factory(DatabaseService, SlowInitService)
        
        # 多線程同時獲取服務
        results = []
        threads = []
        
        def get_service_thread():
            service = container.get(DatabaseService)
            results.append(service)
        
        # 啟動多個線程
        for _ in range(5):
            thread = threading.Thread(target=get_service_thread)
            threads.append(thread)
            thread.start()
        
        # 等待所有線程完成
        for thread in threads:
            thread.join()
        
        # 每個線程應該都獲得了服務實例
        assert len(results) == 5
        for service in results:
            assert hasattr(service, 'initialized')
            assert service.initialized is True
    
    def test_service_factory_configuration(self):
        """測試服務工廠配置"""
        config = {
            'database': {'url': 'sqlite:///test.db'},
            'cache': {'url': 'redis://localhost:6379'},
            'environment': 'test'
        }
        
        factory = ServiceFactory(config)
        
        # 測試數據庫服務創建
        db_service = factory.create_database_service()
        assert isinstance(db_service, SQLAlchemyDatabaseService)
        
        # 測試緩存服務創建
        cache_service = factory.create_cache_service()
        assert isinstance(cache_service, (RedisCacheService, SimpleCacheService))
        
        # 測試投票倉庫創建
        poll_repo = factory.create_poll_repository()
        assert isinstance(poll_repo, SQLAlchemyPollRepository)
    
    def test_service_factory_environment_specific(self):
        """測試環境特定的服務創建"""
        # 測試開發環境
        dev_config = {'environment': 'development'}
        dev_factory = ServiceFactory(dev_config)
        
        dev_cache = dev_factory.create_cache_service()
        assert isinstance(dev_cache, SimpleCacheService)
        
        # 測試生產環境
        prod_config = {
            'environment': 'production',
            'cache': {'url': 'redis://localhost:6379'}
        }
        with patch('redis.from_url'):
            prod_factory = ServiceFactory(prod_config)
            prod_cache = prod_factory.create_cache_service()
            assert isinstance(prod_cache, RedisCacheService)
    
    def test_service_dependencies_resolution(self):
        """測試服務依賴解析"""
        container = ServiceContainer()
        
        # 創建依賴鏈：PollRepository -> DatabaseService
        mock_db_service = Mock()
        container.register_singleton(DatabaseService, mock_db_service)
        
        # 創建需要數據庫服務的投票倉庫
        poll_repo = SQLAlchemyPollRepository(mock_db_service)
        container.register_singleton(PollRepository, poll_repo)
        
        # 獲取投票倉庫，應該正確注入數據庫服務
        retrieved_repo = container.get(PollRepository)
        assert retrieved_repo is poll_repo
        assert retrieved_repo.db_service is mock_db_service
    
    def test_service_container_error_handling(self):
        """測試服務容器錯誤處理"""
        container = ServiceContainer()
        
        # 測試獲取未註冊的服務
        with pytest.raises(Exception) as exc_info:
            container.get(DatabaseService)
        assert "not found" in str(exc_info.value).lower()
        
        # 測試註冊None服務
        with pytest.raises(ValueError):
            container.register_singleton(DatabaseService, None)
        
        # 測試工廠函數拋出異常
        def failing_factory():
            raise RuntimeError("Factory failed")
        
        container.register_factory(CacheService, failing_factory)
        
        with pytest.raises(RuntimeError):
            container.get(CacheService)
    
    def test_service_container_validation(self):
        """測試服務容器驗證"""
        container = ServiceContainer()
        
        # 測試驗證空容器
        validation_result = container.validate()
        assert validation_result is not None
        
        # 配置基本服務
        configure_services(container)
        
        # 測試驗證配置完成的容器
        validation_result = container.validate()
        assert validation_result is not None
        
        # 驗證必需服務都已註冊
        required_services = [DatabaseService, CacheService, PollRepository]
        for service_type in required_services:
            service = container.get_optional(service_type)
            assert service is not None, f"Required service {service_type.__name__} not found"


class TestServiceImplementations:
    """服務實現測試"""
    
    def test_sqlalchemy_database_service(self):
        """測試SQLAlchemy數據庫服務"""
        service = SQLAlchemyDatabaseService("sqlite:///test.db")
        
        # 測試健康檢查
        health = service.health_check()
        assert isinstance(health, dict)
        assert 'database' in health
        
        # 測試會話創建
        session = service.get_session()
        assert session is not None
        session.close()
    
    def test_redis_cache_service(self):
        """測試Redis緩存服務"""
        with patch('redis.from_url') as mock_redis:
            mock_client = Mock()
            mock_redis.return_value = mock_client
            
            service = RedisCacheService("redis://localhost:6379")
            
            # 測試設置值
            service.set("key1", "value1")
            mock_client.set.assert_called_once()
            
            # 測試獲取值
            mock_client.get.return_value = b"value1"
            value = service.get("key1")
            assert value == "value1"
            
            # 測試刪除值
            service.delete("key1")
            mock_client.delete.assert_called_once()
            
            # 測試健康檢查
            mock_client.ping.return_value = True
            health = service.health_check()
            assert health['redis']['status'] == 'healthy'
    
    def test_simple_cache_service(self):
        """測試簡單緩存服務"""
        service = SimpleCacheService()
        
        # 測試設置和獲取
        service.set("key1", "value1")
        value = service.get("key1")
        assert value == "value1"
        
        # 測試獲取不存在的鍵
        value = service.get("nonexistent")
        assert value is None
        
        # 測試刪除
        service.delete("key1")
        value = service.get("key1")
        assert value is None
        
        # 測試存在性檢查
        service.set("key2", "value2")
        assert service.exists("key2") is True
        assert service.exists("nonexistent") is False
    
    def test_composite_validation_service(self):
        """測試複合驗證服務"""
        from strategies.validation import ValidationContext
        
        context = ValidationContext()
        service = CompositeValidationService(context)
        
        # 測試有效數據驗證
        valid_data = {
            'question': 'What is your favorite color?',
            'options': ['Red', 'Blue', 'Green'],
            'vote_type': 'single'
        }
        
        result = service.validate(valid_data)
        assert result['valid'] is True
        assert len(result['errors']) == 0
        
        # 測試無效數據驗證
        invalid_data = {
            'question': 'Hi?',  # 太短
            'options': ['Yes'],  # 選項太少
            'vote_type': 'single'
        }
        
        result = service.validate(invalid_data)
        assert result['valid'] is False
        assert len(result['errors']) > 0
    
    def test_json_export_service(self):
        """測試JSON導出服務"""
        from strategies.export import ExportContext
        
        context = ExportContext()
        service = JSONExportService(context)
        
        # 測試單個投票導出
        poll_data = {
            'id': 1,
            'question': 'Test question?',
            'options': [{'text': 'Option 1', 'vote_count': 3}]
        }
        
        result = service.export_poll(1, 'json', poll_data=poll_data)
        assert isinstance(result, bytes)
        
        # 測試多個投票導出
        polls_data = [poll_data, poll_data]
        result = service.export_multiple_polls([1, 2], 'json', polls_data=polls_data)
        assert isinstance(result, bytes)
    
    def test_simple_authentication_service(self):
        """測試簡單認證服務"""
        service = SimpleAuthenticationService()
        
        # 測試用戶認證
        user = service.authenticate_user("valid_token")
        assert user is not None
        assert 'user_id' in user
        
        # 測試無效token
        user = service.authenticate_user("invalid_token")
        assert user is None
        
        # 測試獲取用戶角色
        roles = service.get_user_roles("user123", "team123")
        assert isinstance(roles, list)
        
        # 測試權限檢查
        has_permission = service.check_permissions("user123", "polls", "create")
        assert isinstance(has_permission, bool)
    
    def test_simple_monitoring_service(self):
        """測試簡單監控服務"""
        service = SimpleMonitoringService()
        
        # 測試健康檢查
        health = service.health_check()
        assert isinstance(health, dict)
        assert 'system' in health
        
        # 測試獲取指標
        metrics = service.get_metrics()
        assert isinstance(metrics, dict)
        assert 'cpu_usage' in metrics
        
        # 測試記錄指標
        service.record_metric("test_metric", 42)
        # 驗證指標被記錄（簡單實現可能不持久化）


class TestServiceErrorHandling:
    """服務錯誤處理測試"""
    
    def test_database_service_connection_error(self):
        """測試數據庫服務連接錯誤"""
        # 使用無效的數據庫URL
        service = SQLAlchemyDatabaseService("invalid://url")
        
        # 健康檢查應該返回錯誤狀態
        health = service.health_check()
        assert health['database']['status'] == 'unhealthy'
    
    def test_cache_service_connection_error(self):
        """測試緩存服務連接錯誤"""
        with patch('redis.from_url') as mock_redis:
            # 模擬Redis連接失敗
            mock_redis.side_effect = Exception("Connection failed")
            
            with pytest.raises(Exception):
                RedisCacheService("redis://invalid:6379")
    
    def test_service_factory_invalid_config(self):
        """測試服務工廠無效配置"""
        # 測試空配置
        factory = ServiceFactory({})
        
        # 應該使用默認配置
        db_service = factory.create_database_service()
        assert isinstance(db_service, SQLAlchemyDatabaseService)
        
        # 測試無效配置
        invalid_config = {'database': {'url': 'invalid://url'}}
        factory = ServiceFactory(invalid_config)
        
        # 創建服務時應該處理錯誤
        db_service = factory.create_database_service()
        assert db_service is not None
    
    def test_service_container_circular_dependency(self):
        """測試服務容器循環依賴"""
        container = ServiceContainer()
        
        # 創建循環依賴的服務
        class ServiceA:
            def __init__(self, service_b):
                self.service_b = service_b
        
        class ServiceB:
            def __init__(self, service_a):
                self.service_a = service_a
        
        # 註冊循環依賴的工廠
        container.register_factory(ServiceA, lambda: ServiceA(container.get(ServiceB)))
        container.register_factory(ServiceB, lambda: ServiceB(container.get(ServiceA)))
        
        # 獲取服務應該檢測到循環依賴
        with pytest.raises(RecursionError):
            container.get(ServiceA)


class TestServiceIntegration:
    """服務集成測試"""
    
    def test_full_service_stack(self):
        """測試完整服務堆棧"""
        container = ServiceContainer()
        configure_services(container)
        
        # 測試獲取所有主要服務
        db_service = container.get(DatabaseService)
        cache_service = container.get(CacheService)
        poll_repo = container.get(PollRepository)
        validation_service = container.get(ValidationService)
        export_service = container.get(ExportService)
        
        # 驗證服務類型
        assert isinstance(db_service, DatabaseService)
        assert isinstance(cache_service, CacheService)
        assert isinstance(poll_repo, PollRepository)
        assert isinstance(validation_service, ValidationService)
        assert isinstance(export_service, ExportService)
        
        # 測試服務之間的依賴
        assert poll_repo.db_service is db_service
    
    def test_service_health_monitoring(self):
        """測試服務健康監控"""
        container = ServiceContainer()
        configure_services(container)
        
        # 獲取監控服務
        monitoring_service = container.get(MonitoringService)
        
        # 執行健康檢查
        health = monitoring_service.health_check()
        assert isinstance(health, dict)
        
        # 檢查系統狀態
        assert 'system' in health
        assert health['system']['status'] in ['healthy', 'unhealthy']
    
    def test_service_configuration_update(self):
        """測試服務配置更新"""
        container = ServiceContainer()
        configure_services(container)
        
        # 獲取配置服務
        config_service = container.get(ConfigurationService)
        
        # 測試配置設置
        success = config_service.set_config("test_key", "test_value")
        assert success is True
        
        # 測試配置獲取
        value = config_service.get_config("test_key")
        assert value == "test_value"
        
        # 測試配置驗證
        validation = config_service.validate_config()
        assert isinstance(validation, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
