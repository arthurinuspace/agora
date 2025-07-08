"""
錯誤處理測試
測試系統的錯誤處理和強健性
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
import tempfile
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi.testclient import TestClient
from fastapi import HTTPException

from app_factory import create_test_app
from services import (
    ServiceContainer, DatabaseService, CacheService, PollRepository,
    ValidationService, ExportService, AuthenticationService,
    get_service, get_container
)
from services.factory import configure_services
from services.implementations import (
    SQLAlchemyDatabaseService, RedisCacheService, SimpleCacheService,
    SQLAlchemyPollRepository, CompositeValidationService
)
from strategies import ValidationContext, ExportContext
from strategies.validation import ValidationResult, ValidationLevel
from database.config import DatabaseConfig


class TestServiceErrorHandling:
    """服務錯誤處理測試"""
    
    def test_database_service_connection_failures(self):
        """測試數據庫服務連接失敗"""
        # 測試無效數據庫URL
        invalid_db_service = SQLAlchemyDatabaseService("invalid://database/url")
        
        # 健康檢查應該返回不健康狀態
        health = invalid_db_service.health_check()
        assert health['database']['status'] == 'unhealthy'
        assert 'error' in health['database']
        
        # 測試獲取會話時的錯誤處理
        with pytest.raises(Exception):
            invalid_db_service.get_session()
    
    def test_database_service_query_failures(self):
        """測試數據庫查詢失敗"""
        # 使用臨時數據庫
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            temp_db_path = temp_db.name
        
        try:
            db_service = SQLAlchemyDatabaseService(f"sqlite:///{temp_db_path}")
            
            # 在沒有創建表的情況下查詢
            session = db_service.get_session()
            
            # 模擬查詢不存在的表
            with pytest.raises(Exception):
                session.execute("SELECT * FROM non_existent_table")
            
            session.close()
            
        finally:
            if os.path.exists(temp_db_path):
                os.unlink(temp_db_path)
    
    def test_cache_service_connection_failures(self):
        """測試緩存服務連接失敗"""
        # 模擬Redis連接失敗
        with patch('redis.from_url') as mock_redis:
            mock_redis.side_effect = ConnectionError("Redis connection failed")
            
            with pytest.raises(ConnectionError):
                RedisCacheService("redis://invalid:6379")
        
        # 測試Redis操作失敗
        with patch('redis.from_url') as mock_redis:
            mock_client = Mock()
            mock_client.ping.side_effect = ConnectionError("Connection lost")
            mock_client.get.side_effect = ConnectionError("Connection lost")
            mock_client.set.side_effect = ConnectionError("Connection lost")
            mock_redis.return_value = mock_client
            
            cache_service = RedisCacheService("redis://localhost:6379")
            
            # 健康檢查應該返回不健康狀態
            health = cache_service.health_check()
            assert health['redis']['status'] == 'unhealthy'
            
            # 操作應該失敗
            with pytest.raises(ConnectionError):
                cache_service.get("test_key")
            
            with pytest.raises(ConnectionError):
                cache_service.set("test_key", "test_value")
    
    def test_simple_cache_service_edge_cases(self):
        """測試簡單緩存服務邊界情況"""
        cache_service = SimpleCacheService()
        
        # 測試None值處理
        cache_service.set("null_key", None)
        value = cache_service.get("null_key")
        assert value is None
        
        # 測試空字串鍵
        with pytest.raises(ValueError):
            cache_service.set("", "value")
        
        # 測試None鍵
        with pytest.raises(ValueError):
            cache_service.set(None, "value")
        
        # 測試大量數據
        large_data = "x" * 1000000  # 1MB的數據
        cache_service.set("large_key", large_data)
        retrieved_data = cache_service.get("large_key")
        assert retrieved_data == large_data
    
    def test_service_container_error_scenarios(self):
        """測試服務容器錯誤情況"""
        container = ServiceContainer()
        
        # 測試獲取未註冊的服務
        with pytest.raises(Exception) as exc_info:
            container.get(DatabaseService)
        assert "not found" in str(exc_info.value).lower()
        
        # 測試註冊None服務
        with pytest.raises(ValueError):
            container.register_singleton(DatabaseService, None)
        
        # 測試註冊無效類型
        with pytest.raises(TypeError):
            container.register_singleton("invalid_type", Mock())
        
        # 測試工廠函數失敗
        def failing_factory():
            raise RuntimeError("Factory initialization failed")
        
        container.register_factory(CacheService, failing_factory)
        
        with pytest.raises(RuntimeError):
            container.get(CacheService)
        
        # 測試循環依賴
        class ServiceA:
            def __init__(self):
                self.service_b = container.get(ServiceB)
        
        class ServiceB:
            def __init__(self):
                self.service_a = container.get(ServiceA)
        
        container.register_factory(ServiceA, ServiceA)
        container.register_factory(ServiceB, ServiceB)
        
        with pytest.raises(RecursionError):
            container.get(ServiceA)
    
    def test_poll_repository_error_handling(self):
        """測試投票倉庫錯誤處理"""
        # 模擬數據庫連接失敗
        mock_db_service = Mock(spec=DatabaseService)
        mock_session = Mock()
        mock_session.query.side_effect = Exception("Database connection lost")
        mock_db_service.get_session.return_value = mock_session
        
        poll_repo = SQLAlchemyPollRepository(mock_db_service)
        
        # 查詢應該失敗
        with pytest.raises(Exception):
            poll_repo.get_polls("T123")
        
        # 測試無效參數
        with pytest.raises(ValueError):
            poll_repo.get_polls("")  # 空團隊ID
        
        with pytest.raises(ValueError):
            poll_repo.get_polls(None)  # None團隊ID
    
    def test_validation_service_error_handling(self):
        """測試驗證服務錯誤處理"""
        validation_context = ValidationContext()
        validation_service = CompositeValidationService(validation_context)
        
        # 測試None數據
        result = validation_service.validate(None)
        assert result['valid'] is False
        assert len(result['errors']) > 0
        
        # 測試空數據
        result = validation_service.validate({})
        assert result['valid'] is False
        assert len(result['errors']) > 0
        
        # 測試無效數據類型
        result = validation_service.validate("invalid_data_type")
        assert result['valid'] is False
        assert len(result['errors']) > 0
        
        # 測試內含異常數據的驗證
        problematic_data = {
            'question': None,  # None值
            'options': [1, 2, 3],  # 錯誤類型
            'vote_type': {'invalid': 'structure'},  # 錯誤結構
            'user_id': [],  # 錯誤類型
            'team_id': 12345  # 錯誤類型
        }
        
        result = validation_service.validate(problematic_data)
        assert result['valid'] is False
        assert len(result['errors']) > 0


class TestAPIErrorHandling:
    """API錯誤處理測試"""
    
    def setup_method(self):
        """測試設置"""
        self.app = create_test_app()
        self.client = TestClient(self.app)
    
    def test_authentication_errors(self):
        """測試認證錯誤"""
        # 測試缺少認證頭
        response = self.client.get("/api/polls")
        assert response.status_code == 403
        
        # 測試無效認證頭格式
        response = self.client.get("/api/polls", headers={
            "Authorization": "Invalid token"
        })
        assert response.status_code == 403
        
        # 測試空認證token
        response = self.client.get("/api/polls", headers={
            "Authorization": "Bearer "
        })
        assert response.status_code == 422  # 驗證錯誤
        
        # 測試認證服務失敗
        with patch('services.get_service') as mock_get_service:
            mock_auth_service = Mock()
            mock_auth_service.authenticate_user.side_effect = Exception("Auth service failed")
            mock_get_service.return_value = mock_auth_service
            
            response = self.client.get("/api/polls", headers={
                "Authorization": "Bearer valid_token"
            })
            assert response.status_code == 500
    
    def test_authorization_errors(self):
        """測試權限錯誤"""
        # 模擬一般用戶
        regular_user = {
            'user_id': 'U123',
            'team_id': 'T123',
            'role': 'user'
        }
        
        # 測試訪問管理員端點
        with patch('api.auth.get_current_user', return_value=regular_user):
            response = self.client.get("/api/admin/overview/stats", headers={
                "Authorization": "Bearer user_token"
            })
            assert response.status_code == 403
            assert "admin" in response.json()['detail'].lower()
    
    def test_validation_errors(self):
        """測試驗證錯誤"""
        mock_user = {'user_id': 'U123', 'team_id': 'T123', 'role': 'user'}
        
        with patch('api.polls.get_current_user', return_value=mock_user), \
             patch('services.get_service') as mock_get_service:
            
            # 模擬驗證失敗
            mock_validation = Mock()
            mock_validation.validate.return_value = {
                'valid': False,
                'errors': ['Question is too short', 'Not enough options']
            }
            mock_get_service.return_value = mock_validation
            
            response = self.client.post("/api/polls", 
                json={
                    "question": "Hi?",
                    "options": ["Yes"],
                    "vote_type": "single",
                    "team_id": "T123",
                    "channel_id": "C123"
                },
                headers={"Authorization": "Bearer valid_token"}
            )
            
            assert response.status_code == 400
            assert "Validation failed" in response.json()['detail']
    
    def test_malformed_request_errors(self):
        """測試格式錯誤的請求"""
        mock_user = {'user_id': 'U123', 'team_id': 'T123', 'role': 'user'}
        
        with patch('api.polls.get_current_user', return_value=mock_user):
            # 測試無效JSON
            response = self.client.post("/api/polls", 
                data="{invalid json}",
                headers={
                    "Authorization": "Bearer valid_token",
                    "Content-Type": "application/json"
                }
            )
            assert response.status_code == 422
            
            # 測試缺少必要欄位
            response = self.client.post("/api/polls", 
                json={
                    "question": "What is your favorite color?"
                    # 缺少options, vote_type等
                },
                headers={"Authorization": "Bearer valid_token"}
            )
            assert response.status_code == 422
            
            # 測試錯誤的數據類型
            response = self.client.post("/api/polls", 
                json={
                    "question": "What is your favorite color?",
                    "options": "Red,Blue,Green",  # 應該是陣列
                    "vote_type": "single",
                    "team_id": "T123",
                    "channel_id": "C123"
                },
                headers={"Authorization": "Bearer valid_token"}
            )
            assert response.status_code == 422
    
    def test_resource_not_found_errors(self):
        """測試資源不存在錯誤"""
        mock_user = {'user_id': 'U123', 'team_id': 'T123', 'role': 'user'}
        
        with patch('api.polls.get_current_user', return_value=mock_user), \
             patch('services.get_service') as mock_get_service:
            
            # 模擬投票不存在
            mock_poll_repo = Mock()
            mock_poll_repo.get_poll.return_value = None
            mock_get_service.return_value = mock_poll_repo
            
            response = self.client.get("/api/polls/999", headers={
                "Authorization": "Bearer valid_token"
            })
            
            assert response.status_code == 404
            assert "not found" in response.json()['detail'].lower()
    
    def test_service_unavailable_errors(self):
        """測試服務不可用錯誤"""
        mock_user = {'user_id': 'U123', 'team_id': 'T123', 'role': 'user'}
        
        with patch('api.polls.get_current_user', return_value=mock_user):
            # 模擬服務完全不可用
            with patch('services.get_service', side_effect=Exception("Service temporarily unavailable")):
                response = self.client.get("/api/polls", headers={
                    "Authorization": "Bearer valid_token"
                })
                assert response.status_code == 500
            
            # 模擬特定服務失敗
            with patch('services.get_service') as mock_get_service:
                mock_poll_repo = Mock()
                mock_poll_repo.get_polls.side_effect = Exception("Database connection failed")
                mock_get_service.return_value = mock_poll_repo
                
                response = self.client.get("/api/polls", headers={
                    "Authorization": "Bearer valid_token"
                })
                assert response.status_code == 500
    
    def test_concurrent_request_errors(self):
        """測試並發請求錯誤"""
        import concurrent.futures
        import threading
        
        mock_user = {'user_id': 'U123', 'team_id': 'T123', 'role': 'user'}
        
        # 模擬服務在高負載下的行為
        with patch('api.polls.get_current_user', return_value=mock_user), \
             patch('services.get_service') as mock_get_service:
            
            call_count = 0
            lock = threading.Lock()
            
            def failing_service():
                nonlocal call_count
                with lock:
                    call_count += 1
                    if call_count > 5:  # 模擬在高負載下失敗
                        raise Exception("Service overloaded")
                
                mock_repo = Mock()
                mock_repo.get_polls.return_value = []
                return mock_repo
            
            mock_get_service.side_effect = failing_service
            
            def make_request():
                return self.client.get("/api/polls", headers={
                    "Authorization": "Bearer valid_token"
                })
            
            # 發送多個並發請求
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(make_request) for _ in range(10)]
                responses = [future.result() for future in futures]
            
            # 部分請求應該成功，部分失敗
            success_count = sum(1 for r in responses if r.status_code == 200)
            error_count = sum(1 for r in responses if r.status_code == 500)
            
            assert success_count > 0
            assert error_count > 0


class TestValidationErrorHandling:
    """驗證錯誤處理測試"""
    
    def test_validation_strategy_failures(self):
        """測試驗證策略失敗"""
        validation_context = ValidationContext()
        
        # 測試驗證策略內部失敗
        from strategies.validation import ValidationStrategy, ValidationResult, ValidationLevel
        
        class FailingValidationStrategy(ValidationStrategy):
            def validate(self, data):
                raise Exception("Validation strategy internal error")
            
            def get_name(self):
                return "failing_validation"
        
        validation_context.add_strategy(FailingValidationStrategy())
        
        # 驗證應該繼續，但記錄錯誤
        result = validation_context.validate({
            'question': 'Test question?',
            'options': ['Yes', 'No']
        })
        
        # 應該有錯誤結果
        errors = [r for r in result if r.level == ValidationLevel.ERROR]
        assert len(errors) > 0
    
    def test_validation_with_malformed_data(self):
        """測試格式錯誤數據的驗證"""
        validation_context = ValidationContext()
        
        malformed_data_cases = [
            None,  # None數據
            "",  # 空字串
            [],  # 空陣列
            123,  # 數字
            {"invalid": {"nested": {"structure": None}}},  # 嵌套結構
            {"question": None, "options": None},  # None值
            {"question": "", "options": []},  # 空值
            {"question": [1, 2, 3], "options": {"a": "b"}},  # 錯誤類型
        ]
        
        for malformed_data in malformed_data_cases:
            result = validation_context.validate(malformed_data)
            
            # 所有格式錯誤的數據都應該被捕獲並處理
            assert isinstance(result, list)
            
            # 應該有錯誤結果
            errors = [r for r in result if r.level == ValidationLevel.ERROR]
            assert len(errors) > 0, f"Failed to handle malformed data: {malformed_data}"
    
    def test_security_validation_edge_cases(self):
        """測試安全驗證邊界情況"""
        from strategies.validation import SecurityValidationStrategy
        
        strategy = SecurityValidationStrategy()
        
        # 測試各種惡意輸入
        malicious_inputs = [
            {
                'question': '<script>alert("XSS")</script>',
                'options': ['Normal', '<img src=x onerror=alert(1)>']
            },
            {
                'question': "'; DROP TABLE users; --",
                'options': ['SQL', 'Injection']
            },
            {
                'question': '{{7*7}}',  # 模板注入
                'options': ['Template', 'Injection']
            },
            {
                'question': 'file:///etc/passwd',  # 檔案包含
                'options': ['File', 'Inclusion']
            },
            {
                'question': 'javascript:alert(1)',  # JavaScript URL
                'options': ['URL', 'Injection']
            },
            {
                'question': '<iframe src="javascript:alert(1)"></iframe>',
                'options': ['iframe', 'injection']
            }
        ]
        
        for malicious_input in malicious_inputs:
            result = strategy.validate(malicious_input)
            
            # 應該檢測到安全問題
            security_issues = [
                r for r in result 
                if r.level in [ValidationLevel.ERROR, ValidationLevel.WARNING]
                and any(keyword in r.message.lower() for keyword in ['script', 'harmful', 'injection', 'malicious'])
            ]
            
            assert len(security_issues) > 0, f"Failed to detect security issue in: {malicious_input}"


class TestExportErrorHandling:
    """導出錯誤處理測試"""
    
    def test_export_strategy_failures(self):
        """測試導出策略失敗"""
        export_context = ExportContext()
        
        # 測試不支持的格式
        with pytest.raises(ValueError):
            export_context.export({}, 'unsupported_format')
        
        # 測試空格式名稱
        with pytest.raises(ValueError):
            export_context.export({}, '')
        
        # 測試None格式
        with pytest.raises(ValueError):
            export_context.export({}, None)
    
    def test_export_with_corrupted_data(self):
        """測試損壞數據的導出"""
        from strategies.export import CSVExportStrategy, JSONExportStrategy
        
        csv_strategy = CSVExportStrategy()
        json_strategy = JSONExportStrategy()
        
        corrupted_data_cases = [
            {},  # 空數據
            {'invalid_key': 'invalid_value'},  # 無效結構
            {'poll_data': None},  # None投票數據
            {'poll_data': {}},  # 空投票數據
            {'poll_data': {'id': None, 'question': None}},  # None值
            {'poll_data': {'options': 'invalid_options'}},  # 錯誤類型
            {'polls_data': 'should_be_array'},  # 錯誤類型
        ]
        
        for corrupted_data in corrupted_data_cases:
            # CSV導出應該處理錯誤且不崩潰
            csv_result = csv_strategy.export(corrupted_data)
            assert isinstance(csv_result, bytes)
            
            # JSON導出應該處理錯誤且不崩潰
            json_result = json_strategy.export(corrupted_data)
            assert isinstance(json_result, bytes)
            
            # 結果應該可以解析
            try:
                json.loads(json_result.decode('utf-8'))
            except json.JSONDecodeError:
                pytest.fail(f"Invalid JSON produced for corrupted data: {corrupted_data}")
    
    def test_export_memory_limits(self):
        """測試導出內存限制"""
        from strategies.export import JSONExportStrategy
        
        strategy = JSONExportStrategy()
        
        # 創建大量數據
        large_poll_data = {
            'poll_data': {
                'id': 1,
                'question': 'Large data test?' * 1000,  # 長問題
                'options': [
                    {'text': f'Option {i}' * 100, 'vote_count': i}
                    for i in range(1000)  # 大量選項
                ]
            }
        }
        
        # 導出應該成功且不耗盡內存
        result = strategy.export(large_poll_data)
        assert isinstance(result, bytes)
        assert len(result) > 0
    
    def test_export_encoding_errors(self):
        """測試導出編碼錯誤"""
        from strategies.export import CSVExportStrategy, JSONExportStrategy
        
        csv_strategy = CSVExportStrategy()
        json_strategy = JSONExportStrategy()
        
        # 包含特殊字元的數據
        unicode_data = {
            'poll_data': {
                'id': 1,
                'question': '你好世界! 🌍 🚀',  # 中文和emoji
                'options': [
                    {'text': '選項一 😊', 'vote_count': 5},
                    {'text': '選項二 😎', 'vote_count': 3},
                    {'text': 'αβγδεζηθ', 'vote_count': 2},  # 希臘字母
                    {'text': 'العربية', 'vote_count': 1}  # 阿拉伯文
                ]
            }
        }
        
        # 導出應該正確處理Unicode字元
        csv_result = csv_strategy.export(unicode_data)
        assert isinstance(csv_result, bytes)
        
        json_result = json_strategy.export(unicode_data)
        assert isinstance(json_result, bytes)
        
        # 驗證可以正確解碼
        csv_text = csv_result.decode('utf-8')
        json_text = json_result.decode('utf-8')
        
        assert '你好世界' in csv_text
        assert '你好世界' in json_text


class TestSystemResilience:
    """系統彈性測試"""
    
    def test_graceful_degradation(self):
        """測試優雅降級"""
        container = ServiceContainer()
        
        # 模擬部分服務失敗
        with patch.object(container, 'get') as mock_get:
            def selective_failure(service_type):
                if service_type == CacheService:
                    raise Exception("Cache service unavailable")
                return Mock()
            
            mock_get.side_effect = selective_failure
            
            # 系統應該能夠在緩存服務不可用時繼續運行
            with pytest.raises(Exception):
                container.get(CacheService)
            
            # 但其他服務應該正常
            db_service = container.get(DatabaseService)
            assert db_service is not None
    
    def test_recovery_mechanisms(self):
        """測試恢復機制"""
        # 模擬服務恢復
        container = ServiceContainer()
        
        # 模擬暫時失敗然後恢復的服務
        failure_count = 0
        
        def intermittent_service():
            nonlocal failure_count
            failure_count += 1
            if failure_count <= 2:
                raise Exception("Temporary service failure")
            return Mock()
        
        container.register_factory(DatabaseService, intermittent_service)
        
        # 前兩次應該失敗
        with pytest.raises(Exception):
            container.get(DatabaseService)
        
        with pytest.raises(Exception):
            container.get(DatabaseService)
        
        # 第三次應該成功
        service = container.get(DatabaseService)
        assert service is not None
    
    def test_resource_cleanup(self):
        """測試資源清理"""
        container = ServiceContainer()
        
        # 模擬需要清理的資源
        cleanup_called = False
        
        class ResourceIntensiveService:
            def __init__(self):
                self.resource = "allocated"
            
            def cleanup(self):
                nonlocal cleanup_called
                cleanup_called = True
                self.resource = "cleaned"
        
        container.register_singleton(DatabaseService, ResourceIntensiveService())
        
        # 獲取服務
        service = container.get(DatabaseService)
        assert service.resource == "allocated"
        
        # 清理資源
        service.cleanup()
        assert cleanup_called
        assert service.resource == "cleaned"
        
        # 清理容器
        container.clear()
        
        # 驗證服務被清理
        assert container.get_optional(DatabaseService) is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
