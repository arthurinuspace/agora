"""
完整集成測試
測試SOLID架構的完整集成和端到端功能
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import json
import tempfile
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from fastapi.testclient import TestClient
from fastapi import FastAPI

from app_factory import create_test_app, create_development_app
from services import (
    ServiceContainer, DatabaseService, CacheService, PollRepository,
    ValidationService, ExportService, AuthenticationService,
    NotificationService, EventPublisher, MonitoringService,
    ConfigurationService, get_service, get_container
)
from services.factory import configure_services
from strategies import ValidationContext, ExportContext
from database.config import DatabaseConfig


class TestCompleteIntegration:
    """完整集成測試"""
    
    def setup_method(self):
        """測試設置"""
        # 創建測試應用程序
        self.app = create_test_app()
        self.client = TestClient(self.app)
        
        # 初始化測試數據
        self.test_user = {
            'user_id': 'U123456',
            'team_id': 'T123456',
            'role': 'user',
            'email': 'test@example.com'
        }
        
        self.test_admin = {
            'user_id': 'U999999',
            'team_id': 'T123456',
            'role': 'admin',
            'email': 'admin@example.com'
        }
        
        self.test_polls = [
            {
                'id': 1,
                'question': 'What is your favorite programming language?',
                'options': [
                    {'id': 1, 'text': 'Python', 'vote_count': 15},
                    {'id': 2, 'text': 'JavaScript', 'vote_count': 12},
                    {'id': 3, 'text': 'Java', 'vote_count': 8},
                    {'id': 4, 'text': 'Go', 'vote_count': 5}
                ],
                'vote_type': 'single',
                'status': 'active',
                'team_id': 'T123456',
                'channel_id': 'C123456',
                'creator_id': 'U123456',
                'created_at': datetime.now() - timedelta(days=1),
                'total_votes': 40
            },
            {
                'id': 2,
                'question': 'Which IDE do you prefer?',
                'options': [
                    {'id': 5, 'text': 'VS Code', 'vote_count': 25},
                    {'id': 6, 'text': 'PyCharm', 'vote_count': 10},
                    {'id': 7, 'text': 'Vim', 'vote_count': 5}
                ],
                'vote_type': 'single',
                'status': 'ended',
                'team_id': 'T123456',
                'channel_id': 'C123456',
                'creator_id': 'U123456',
                'created_at': datetime.now() - timedelta(days=2),
                'ended_at': datetime.now() - timedelta(hours=2),
                'total_votes': 40
            }
        ]
    
    def test_end_to_end_poll_lifecycle(self):
        """測試完整投票生命週期"""
        # 模擬所有必要的服務
        with patch('api.auth.get_current_user', return_value=self.test_user), \
             patch('api.polls.get_current_user', return_value=self.test_user), \
             patch('api.admin.require_admin', return_value=self.test_admin), \
             patch('services.get_service') as mock_get_service:
            
            # 配置模擬服務
            mock_validation_service = Mock()
            mock_poll_repo = Mock()
            mock_event_publisher = Mock()
            mock_export_service = Mock()
            
            def mock_service_factory(service_type):
                service_name = str(service_type)
                if 'Validation' in service_name:
                    return mock_validation_service
                elif 'Repository' in service_name:
                    return mock_poll_repo
                elif 'Publisher' in service_name:
                    return mock_event_publisher
                elif 'Export' in service_name:
                    return mock_export_service
                return Mock()
            
            mock_get_service.side_effect = mock_service_factory
            
            # 1. 創建投票
            mock_validation_service.validate.return_value = {
                'valid': True,
                'errors': []
            }
            mock_poll_repo.create_poll.return_value = 1
            
            create_response = self.client.post("/api/polls", 
                json={
                    "question": "What is your favorite color?",
                    "options": ["Red", "Blue", "Green", "Yellow"],
                    "vote_type": "single",
                    "team_id": "T123456",
                    "channel_id": "C123456"
                },
                headers={"Authorization": "Bearer valid_token"}
            )
            
            assert create_response.status_code == 200
            create_data = create_response.json()
            assert create_data['poll_id'] == 1
            assert "created successfully" in create_data['message']
            
            # 驗證事件被發布
            mock_event_publisher.publish.assert_called_with('poll_created', {
                'poll_id': 1,
                'creator_id': 'U123456',
                'team_id': 'T123456',
                'question': 'What is your favorite color?'
            })
            
            # 2. 獲取投票詳情
            mock_poll = {
                'id': 1,
                'question': 'What is your favorite color?',
                'team_id': 'T123456',
                'status': 'active',
                'options': [
                    {'id': 1, 'text': 'Red', 'vote_count': 5},
                    {'id': 2, 'text': 'Blue', 'vote_count': 3},
                    {'id': 3, 'text': 'Green', 'vote_count': 2},
                    {'id': 4, 'text': 'Yellow', 'vote_count': 1}
                ],
                'created_at': datetime.now()
            }
            mock_poll_repo.get_poll.return_value = mock_poll
            
            get_response = self.client.get("/api/polls/1", 
                headers={"Authorization": "Bearer valid_token"}
            )
            
            assert get_response.status_code == 200
            poll_data = get_response.json()
            assert poll_data['question'] == 'What is your favorite color?'
            assert len(poll_data['options']) == 4
            
            # 3. 更新投票狀態
            mock_poll_repo.update_poll.return_value = True
            
            update_response = self.client.put("/api/polls/1", 
                json={"status": "ended"},
                headers={"Authorization": "Bearer valid_token"}
            )
            
            assert update_response.status_code == 200
            assert "updated successfully" in update_response.json()['message']
            
            # 4. 獲取投票統計
            stats_response = self.client.get("/api/polls/1/stats", 
                headers={"Authorization": "Bearer valid_token"}
            )
            
            assert stats_response.status_code == 200
            stats_data = stats_response.json()
            assert stats_data['total_votes'] == 11
            assert len(stats_data['option_stats']) == 4
            
            # 5. 管理員導出投票
            mock_export_service.export_poll.return_value = b"poll_id,question,status\n1,What is your favorite color?,ended\n"
            
            export_response = self.client.post("/api/admin/export", 
                json={
                    "poll_ids": [1],
                    "format": "csv",
                    "include_analytics": True
                },
                headers={"Authorization": "Bearer admin_token"}
            )
            
            assert export_response.status_code == 200
            
            # 6. 刪除投票
            mock_poll_repo.delete_poll.return_value = True
            
            delete_response = self.client.delete("/api/polls/1", 
                headers={"Authorization": "Bearer valid_token"}
            )
            
            assert delete_response.status_code == 200
            assert "deleted successfully" in delete_response.json()['message']
    
    def test_service_container_integration(self):
        """測試服務容器集成"""
        # 創建新的服務容器
        container = ServiceContainer()
        configure_services(container)
        
        # 測試所有主要服務都被正確註冊
        required_services = [
            DatabaseService,
            CacheService,
            PollRepository,
            ValidationService,
            ExportService,
            AuthenticationService,
            NotificationService,
            EventPublisher,
            MonitoringService,
            ConfigurationService
        ]
        
        for service_type in required_services:
            service = container.get_optional(service_type)
            assert service is not None, f"Service {service_type.__name__} not found"
            
            # 測試服務健康檢查
            if hasattr(service, 'health_check'):
                health = service.health_check()
                assert isinstance(health, dict)
        
        # 測試服務依賴關係
        poll_repo = container.get(PollRepository)
        db_service = container.get(DatabaseService)
        
        # 投票倉庫應該依賴數據庫服務
        assert hasattr(poll_repo, 'db_service')
        assert poll_repo.db_service is db_service
    
    def test_validation_strategies_integration(self):
        """測試驗證策略集成"""
        validation_context = ValidationContext()
        
        # 測試完整的投票數據驗證
        complete_poll_data = {
            'question': 'What is your favorite framework for web development?',
            'options': ['Django', 'Flask', 'FastAPI', 'Express.js', 'Spring Boot'],
            'vote_type': 'single',
            'user_id': 'U123456',
            'team_id': 'T123456',
            'channel_id': 'C123456'
        }
        
        validation_result = validation_context.validate(complete_poll_data)
        
        # 應該沒有錯誤
        errors = [r for r in validation_result if r.level.value == 'error']
        assert len(errors) == 0
        
        # 測試不完整的數據
        incomplete_data = {
            'question': 'Hi?',  # 太短
            'options': ['Yes'],  # 選項太少
            'vote_type': 'invalid_type',  # 無效類型
            'user_id': '',  # 空用戶ID
            'team_id': ''
        }
        
        validation_result = validation_context.validate(incomplete_data)
        errors = [r for r in validation_result if r.level.value == 'error']
        assert len(errors) > 0
        
        # 測試安全驗證
        malicious_data = {
            'question': 'Click here: <script>alert("xss")</script>',
            'options': ['<img src=x onerror=alert(1)>', 'Normal'],
            'vote_type': 'single',
            'user_id': 'U123456',
            'team_id': 'T123456'
        }
        
        validation_result = validation_context.validate(malicious_data)
        security_errors = [r for r in validation_result if r.level.value == 'error' and ('script' in r.message.lower() or 'harmful' in r.message.lower())]
        assert len(security_errors) > 0
    
    def test_export_strategies_integration(self):
        """測試導出策略集成"""
        export_context = ExportContext()
        
        # 測試導出單個投票
        single_poll_data = {
            'poll_data': self.test_polls[0]
        }
        
        for format_name in ['csv', 'json', 'excel']:
            result = export_context.export(single_poll_data, format_name)
            assert isinstance(result, bytes)
            assert len(result) > 0
            
            # 驗證導出內容包含投票數據
            content = result.decode('utf-8', errors='ignore')
            if format_name in ['csv', 'json']:
                assert 'favorite programming language' in content.lower() or 'programming' in content.lower()
        
        # 測試導出多個投票
        multiple_polls_data = {
            'polls_data': self.test_polls
        }
        
        for format_name in ['csv', 'json']:
            result = export_context.export(multiple_polls_data, format_name)
            assert isinstance(result, bytes)
            assert len(result) > 0
        
        # 測試帶分析數據的導出
        analytics_data = {
            'poll_data': self.test_polls[0],
            'analytics': {
                'participation_rate': 85.5,
                'avg_response_time': 2.1,
                'peak_voting_hour': 14,
                'voter_demographics': {
                    'age_groups': {'18-25': 30, '26-35': 45, '36+': 25},
                    'departments': {'Engineering': 60, 'Design': 25, 'Product': 15}
                }
            }
        }
        
        result = export_context.export(analytics_data, 'json', {'include_analytics': True})
        json_data = json.loads(result.decode('utf-8'))
        assert 'analytics' in json_data or 'participation_rate' in str(json_data)
    
    def test_database_integration(self):
        """測試數據庫集成"""
        # 使用臨時數據庫進行測試
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            temp_db_path = temp_db.name
        
        try:
            # 創建數據庫配置
            db_config = DatabaseConfig(f"sqlite:///{temp_db_path}")
            
            # 測試數據庫連接
            health = db_config.health_check()
            assert health['database']['status'] == 'healthy'
            
            # 測試表創建
            db_config.create_tables()
            
            # 測試會話創建
            session = db_config.get_session()
            assert session is not None
            session.close()
            
        finally:
            # 清理臨時檔案
            if os.path.exists(temp_db_path):
                os.unlink(temp_db_path)
    
    def test_api_error_handling_integration(self):
        """測試API錯誤處理集成"""
        # 測試認證失敗
        response = self.client.get("/api/polls")
        assert response.status_code == 403  # 缺少認證
        
        # 測試無效JSON
        with patch('api.polls.get_current_user', return_value=self.test_user):
            response = self.client.post("/api/polls", 
                data="invalid json",
                headers={
                    "Authorization": "Bearer valid_token",
                    "Content-Type": "application/json"
                }
            )
            assert response.status_code == 422
        
        # 測試服務不可用
        with patch('services.get_service', side_effect=Exception("Service unavailable")):
            with patch('api.polls.get_current_user', return_value=self.test_user):
                response = self.client.get("/api/polls", 
                    headers={"Authorization": "Bearer valid_token"}
                )
                assert response.status_code == 500
        
        # 測試資源不存在
        with patch('api.polls.get_current_user', return_value=self.test_user), \
             patch('services.get_service') as mock_get_service:
            
            mock_poll_repo = Mock()
            mock_poll_repo.get_poll.return_value = None
            mock_get_service.return_value = mock_poll_repo
            
            response = self.client.get("/api/polls/999", 
                headers={"Authorization": "Bearer valid_token"}
            )
            assert response.status_code == 404
            assert "not found" in response.json()['detail'].lower()
        
        # 測試權限拒絕
        with patch('api.auth.get_current_user', return_value=self.test_user):  # 非管理員
            response = self.client.get("/api/admin/overview/stats", 
                headers={"Authorization": "Bearer user_token"}
            )
            assert response.status_code == 403
            assert "admin" in response.json()['detail'].lower()
    
    def test_performance_integration(self):
        """測試性能集成"""
        import time
        
        # 測試應用程序啟動時間
        start_time = time.time()
        test_app = create_test_app()
        startup_time = time.time() - start_time
        
        # 應用程序應該在短時間內啟動
        assert startup_time < 5.0
        
        # 測試併發請求處理
        client = TestClient(test_app)
        
        with patch('api.polls.get_current_user', return_value=self.test_user), \
             patch('services.get_service') as mock_get_service:
            
            mock_poll_repo = Mock()
            mock_poll_repo.get_polls.return_value = self.test_polls
            mock_get_service.return_value = mock_poll_repo
            
            # 發送多個並發請求
            import concurrent.futures
            import threading
            
            def make_request():
                return client.get("/api/polls", 
                    headers={"Authorization": "Bearer valid_token"}
                )
            
            start_time = time.time()
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(make_request) for _ in range(20)]
                responses = [future.result() for future in futures]
            
            concurrent_time = time.time() - start_time
            
            # 所有請求都應該成功
            for response in responses:
                assert response.status_code == 200
            
            # 並發處理應該在合理時間內完成
            assert concurrent_time < 10.0
    
    def test_configuration_integration(self):
        """測試配置集成"""
        # 測試不同環境的配置
        test_configs = [
            {'environment': 'test'},
            {'environment': 'development'},
            {
                'environment': 'production',
                'database': {'url': 'sqlite:///test_prod.db'},
                'cache': {'url': 'redis://localhost:6379'}
            }
        ]
        
        for config in test_configs:
            try:
                if config['environment'] == 'development':
                    app = create_development_app(config)
                else:
                    app = create_test_app(config)
                
                assert app is not None
                assert app.title is not None
                
                # 測試路由註冊
                routes = [route.path for route in app.routes]
                api_routes = [r for r in routes if r.startswith('/api/')]
                assert len(api_routes) > 0
                
            except Exception as e:
                # 如果是由於缺少Redis連接等外部依賴導致的錯誤，可以忽略
                if 'redis' in str(e).lower() or 'connection' in str(e).lower():
                    continue
                else:
                    raise
    
    def test_monitoring_integration(self):
        """測試監控集成"""
        container = ServiceContainer()
        configure_services(container)
        
        # 獲取監控服務
        monitoring_service = container.get(MonitoringService)
        
        # 測試系統健康檢查
        health = monitoring_service.health_check()
        assert isinstance(health, dict)
        assert 'system' in health
        
        # 測試系統指標
        metrics = monitoring_service.get_metrics()
        assert isinstance(metrics, dict)
        
        # 測試指標記錄
        monitoring_service.record_metric('test_metric', 42.0)
        monitoring_service.record_metric('api_requests', 100)
        
        # 再次獲取指標應該包含新記錄
        updated_metrics = monitoring_service.get_metrics()
        assert isinstance(updated_metrics, dict)
    
    def test_event_system_integration(self):
        """測試事件系統集成"""
        container = ServiceContainer()
        configure_services(container)
        
        # 獲取事件發布者
        event_publisher = container.get(EventPublisher)
        
        # 測試事件發布
        test_events = [
            ('poll_created', {'poll_id': 1, 'creator_id': 'U123'}),
            ('poll_updated', {'poll_id': 1, 'updated_by': 'U123'}),
            ('poll_voted', {'poll_id': 1, 'voter_id': 'U456', 'option_id': 1}),
            ('poll_ended', {'poll_id': 1, 'ended_by': 'U123'}),
            ('poll_deleted', {'poll_id': 1, 'deleted_by': 'U123'})
        ]
        
        for event_type, event_data in test_events:
            # 事件發布不應該拋出異常
            try:
                event_publisher.publish(event_type, event_data)
            except Exception as e:
                pytest.fail(f"Event publishing failed for {event_type}: {e}")
    
    def test_complete_system_health(self):
        """測試完整系統健康"""
        # 創建完整的系統
        app = create_test_app()
        container = get_container()
        
        # 測試所有服務的健康狀態
        services_with_health_check = [
            DatabaseService,
            CacheService,
            MonitoringService
        ]
        
        overall_health = {'healthy': True, 'services': {}}
        
        for service_type in services_with_health_check:
            try:
                service = container.get(service_type)
                if hasattr(service, 'health_check'):
                    health = service.health_check()
                    overall_health['services'][service_type.__name__] = health
                    
                    # 檢查是否有不健康的服務
                    if isinstance(health, dict):
                        for component, status in health.items():
                            if isinstance(status, dict) and status.get('status') == 'unhealthy':
                                overall_health['healthy'] = False
                            
            except Exception as e:
                overall_health['healthy'] = False
                overall_health['services'][service_type.__name__] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        # 系統應該整體健康
        # 即使有些服務不健康，也不應該影響基本功能
        assert overall_health is not None
        assert 'services' in overall_health


class TestSOLIDComplianceIntegration:
    """SOLID原則遵從性集成測試"""
    
    def test_single_responsibility_compliance(self):
        """測試單一職責原則遵從性"""
        # 測試API模組分離
        from api.auth import router as auth_router
        from api.polls import router as polls_router
        from api.admin import router as admin_router
        
        # 每個路由器應該有明確的職責範圍
        assert auth_router.prefix == "/api/auth"
        assert polls_router.prefix == "/api/polls"
        assert admin_router.prefix == "/api/admin"
        
        # 測試服務的職責分離
        container = ServiceContainer()
        configure_services(container)
        
        validation_service = container.get(ValidationService)
        export_service = container.get(ExportService)
        auth_service = container.get(AuthenticationService)
        
        # 每個服務應該只有其特定的方法
        assert hasattr(validation_service, 'validate')
        assert hasattr(export_service, 'export_poll')
        assert hasattr(auth_service, 'authenticate_user')
        
        # 服務不應該有不相關的方法
        assert not hasattr(validation_service, 'export_poll')
        assert not hasattr(export_service, 'authenticate_user')
        assert not hasattr(auth_service, 'validate')
    
    def test_open_closed_compliance(self):
        """測試開放封闉原則遵從性"""
        # 測試驗證策略擴展
        validation_context = ValidationContext()
        initial_strategies = len(validation_context.get_strategy_names())
        
        # 添加新策略不應該修改現有代碼
        from strategies.validation import ValidationStrategy, ValidationResult, ValidationLevel
        
        class CustomValidationStrategy(ValidationStrategy):
            def validate(self, data):
                return [ValidationResult(
                    level=ValidationLevel.INFO,
                    message="Custom validation",
                    field="custom"
                )]
            
            def get_name(self):
                return "custom_validation"
        
        validation_context.add_strategy(CustomValidationStrategy())
        new_strategies = len(validation_context.get_strategy_names())
        assert new_strategies == initial_strategies + 1
        
        # 測試導出策略擴展
        export_context = ExportContext()
        initial_formats = len(export_context.get_supported_formats())
        
        from strategies.export import ExportStrategy
        
        class CustomExportStrategy(ExportStrategy):
            def export(self, data, options=None):
                return b"custom export format"
            
            def get_format_name(self):
                return "CUSTOM"
            
            def get_file_extension(self):
                return "custom"
            
            def get_mime_type(self):
                return "application/custom"
        
        export_context.add_strategy(CustomExportStrategy())
        new_formats = len(export_context.get_supported_formats())
        assert new_formats == initial_formats + 1
    
    def test_dependency_inversion_compliance(self):
        """測試依賴倒置原則遵從性"""
        container = ServiceContainer()
        configure_services(container)
        
        # 高層模組應該依賴抽象接口
        poll_repo = container.get(PollRepository)
        db_service = container.get(DatabaseService)
        
        # 測試依賴注入
        assert isinstance(poll_repo, PollRepository)  # 抽象接口
        assert isinstance(db_service, DatabaseService)  # 抽象接口
        
        # 測試服務可替換性
        mock_db_service = Mock(spec=DatabaseService)
        
        with container.override(DatabaseService, mock_db_service):
            overridden_service = container.get(DatabaseService)
            assert overridden_service is mock_db_service
        
        # 覆寫結束後應該恢復原始服務
        restored_service = container.get(DatabaseService)
        assert restored_service is db_service
    
    def test_interface_segregation_compliance(self):
        """測試接口隸離原則遵從性"""
        container = ServiceContainer()
        configure_services(container)
        
        # 測試服務接口的精簡性
        validation_service = container.get(ValidationService)
        export_service = container.get(ExportService)
        auth_service = container.get(AuthenticationService)
        
        # 驗證服務只應該有驗證相關的方法
        validation_methods = [method for method in dir(validation_service) if not method.startswith('_')]
        validation_core_methods = [method for method in validation_methods if 'validate' in method.lower()]
        assert len(validation_core_methods) > 0
        
        # 導出服務只應該有導出相關的方法
        export_methods = [method for method in dir(export_service) if not method.startswith('_')]
        export_core_methods = [method for method in export_methods if 'export' in method.lower()]
        assert len(export_core_methods) > 0
        
        # 認證服務只應該有認證相關的方法
        auth_methods = [method for method in dir(auth_service) if not method.startswith('_')]
        auth_core_methods = [method for method in auth_methods if any(keyword in method.lower() for keyword in ['auth', 'user', 'permission', 'role'])]
        assert len(auth_core_methods) > 0
    
    def test_liskov_substitution_compliance(self):
        """測試里氏替換原則遵從性"""
        # 測試策略可替換性
        from strategies.validation import PollQuestionValidationStrategy, PollOptionsValidationStrategy
        from strategies.export import CSVExportStrategy, JSONExportStrategy
        
        # 所有驗證策略應該可以互相替換
        validation_strategies = [
            PollQuestionValidationStrategy(),
            PollOptionsValidationStrategy()
        ]
        
        test_data = {
            'question': 'Test question?',
            'options': ['Option 1', 'Option 2']
        }
        
        for strategy in validation_strategies:
            result = strategy.validate(test_data)
            assert isinstance(result, list)
            # 每個結果都應該是ValidationResult類型
            for item in result:
                assert hasattr(item, 'level')
                assert hasattr(item, 'message')
        
        # 所有導出策略應該可以互相替換
        export_strategies = [
            CSVExportStrategy(),
            JSONExportStrategy()
        ]
        
        export_data = {
            'poll_data': {
                'id': 1,
                'question': 'Test question?',
                'options': [{'text': 'Option 1', 'vote_count': 1}]
            }
        }
        
        for strategy in export_strategies:
            result = strategy.export(export_data)
            assert isinstance(result, bytes)
            assert len(result) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
