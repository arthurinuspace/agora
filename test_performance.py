"""
效能測試
測試SOLID架構的效能和可擴展性
"""

import pytest
import time
import threading
import concurrent.futures
import psutil
import os
from unittest.mock import Mock, patch
from typing import Dict, Any, List

from app_factory import create_test_app, create_development_app
from services import (
    ServiceContainer, DatabaseService, CacheService, PollRepository,
    ValidationService, ExportService, get_service, get_container
)
from services.factory import configure_services
from strategies import ValidationContext, ExportContext


class TestServicePerformance:
    """服務效能測試"""
    
    def test_service_container_performance(self):
        """測試服務容器效能"""
        container = ServiceContainer()
        configure_services(container)
        
        # 測試服務獲取效能
        start_time = time.time()
        
        for _ in range(1000):
            db_service = container.get(DatabaseService)
            cache_service = container.get(CacheService)
            poll_repo = container.get(PollRepository)
        
        elapsed_time = time.time() - start_time
        
        # 1000次服務獲取應該在1秒內完成
        assert elapsed_time < 1.0, f"Service retrieval too slow: {elapsed_time}s"
        
        # 測試並發服務獲取
        def get_services():
            for _ in range(100):
                container.get(DatabaseService)
                container.get(CacheService)
        
        start_time = time.time()
        
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=get_services)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        concurrent_time = time.time() - start_time
        
        # 並發獲取應該在合理時間內完成
        assert concurrent_time < 5.0, f"Concurrent service access too slow: {concurrent_time}s"
    
    def test_service_container_memory_usage(self):
        """測試服務容器內存使用"""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # 創建多個服務容器
        containers = []
        for _ in range(10):
            container = ServiceContainer()
            configure_services(container)
            containers.append(container)
        
        # 獲取大量服務
        for container in containers:
            for _ in range(50):
                container.get(DatabaseService)
                container.get(CacheService)
                container.get(PollRepository)
        
        peak_memory = process.memory_info().rss
        memory_increase = peak_memory - initial_memory
        
        # 清理容器
        for container in containers:
            container.clear()
        
        final_memory = process.memory_info().rss
        
        # 內存增長應該在合理範圍內（<50MB）
        memory_mb = memory_increase / (1024 * 1024)
        assert memory_mb < 50, f"Memory usage too high: {memory_mb}MB"
        
        # 清理後內存應該釋放
        cleanup_memory = final_memory - initial_memory
        cleanup_mb = cleanup_memory / (1024 * 1024)
        assert cleanup_mb < memory_mb, "Memory not properly released after cleanup"
    
    def test_service_initialization_performance(self):
        """測試服務初始化效能"""
        # 測試服務容器初始化時間
        start_time = time.time()
        
        container = ServiceContainer()
        configure_services(container)
        
        initialization_time = time.time() - start_time
        
        # 服務容器初始化應該在短時間內完成
        assert initialization_time < 2.0, f"Service initialization too slow: {initialization_time}s"
        
        # 測試首次服務獲取時間
        start_time = time.time()
        
        db_service = container.get(DatabaseService)
        cache_service = container.get(CacheService)
        poll_repo = container.get(PollRepository)
        validation_service = container.get(ValidationService)
        export_service = container.get(ExportService)
        
        first_access_time = time.time() - start_time
        
        # 首次獲取所有服務應該在短時間內完成
        assert first_access_time < 1.0, f"First service access too slow: {first_access_time}s"
        
        # 測試後續獲取時間（應該更快）
        start_time = time.time()
        
        for _ in range(100):
            container.get(DatabaseService)
            container.get(CacheService)
        
        subsequent_access_time = time.time() - start_time
        
        assert subsequent_access_time < 0.1, f"Subsequent access too slow: {subsequent_access_time}s"
        assert subsequent_access_time < first_access_time, "Subsequent access should be faster than first access"


class TestValidationPerformance:
    """驗證效能測試"""
    
    def test_validation_context_performance(self):
        """測試驗證上下文效能"""
        validation_context = ValidationContext()
        
        # 測試單個驗證效能
        test_data = {
            'question': 'What is your favorite programming language?',
            'options': ['Python', 'JavaScript', 'Java', 'Go', 'Rust'],
            'vote_type': 'single',
            'user_id': 'U123456',
            'team_id': 'T123456'
        }
        
        start_time = time.time()
        
        for _ in range(1000):
            validation_context.validate(test_data)
        
        single_validation_time = time.time() - start_time
        
        # 1000次驗證應該在5秒內完成
        assert single_validation_time < 5.0, f"Validation too slow: {single_validation_time}s"
        
        # 測試批量驗證效能
        batch_data = [test_data.copy() for _ in range(100)]
        
        start_time = time.time()
        
        for data in batch_data:
            validation_context.validate(data)
        
        batch_validation_time = time.time() - start_time
        
        # 批量驗證應該在2秒內完成
        assert batch_validation_time < 2.0, f"Batch validation too slow: {batch_validation_time}s"
    
    def test_validation_with_large_data(self):
        """測試大數據驗證效能"""
        validation_context = ValidationContext()
        
        # 創建大量數據
        large_data = {
            'question': 'What is your favorite option from this extensive list?' * 10,
            'options': [f'Option {i} with detailed description' for i in range(20)],
            'vote_type': 'multiple',
            'user_id': 'U123456',
            'team_id': 'T123456',
            'additional_data': {
                'metadata': {f'key_{i}': f'value_{i}' for i in range(100)}
            }
        }
        
        start_time = time.time()
        
        for _ in range(100):
            result = validation_context.validate(large_data)
            assert isinstance(result, list)
        
        large_data_time = time.time() - start_time
        
        # 大數據驗證應該在3秒內完成
        assert large_data_time < 3.0, f"Large data validation too slow: {large_data_time}s"
    
    def test_concurrent_validation_performance(self):
        """測試並發驗證效能"""
        validation_context = ValidationContext()
        
        test_data = {
            'question': 'What is your favorite color?',
            'options': ['Red', 'Blue', 'Green', 'Yellow'],
            'vote_type': 'single',
            'user_id': 'U123456',
            'team_id': 'T123456'
        }
        
        def validate_worker():
            for _ in range(50):
                validation_context.validate(test_data)
        
        start_time = time.time()
        
        # 創建10個並發線程
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(validate_worker) for _ in range(10)]
            concurrent.futures.wait(futures)
        
        concurrent_validation_time = time.time() - start_time
        
        # 並發驗證應該在合理時間內完成
        assert concurrent_validation_time < 10.0, f"Concurrent validation too slow: {concurrent_validation_time}s"


class TestExportPerformance:
    """導出效能測試"""
    
    def test_export_context_performance(self):
        """測試導出上下文效能"""
        export_context = ExportContext()
        
        # 測試單個投票導出效能
        poll_data = {
            'poll_data': {
                'id': 1,
                'question': 'What is your favorite programming language?',
                'vote_type': 'single',
                'status': 'active',
                'options': [
                    {'text': 'Python', 'vote_count': 150},
                    {'text': 'JavaScript', 'vote_count': 120},
                    {'text': 'Java', 'vote_count': 80},
                    {'text': 'Go', 'vote_count': 50}
                ]
            }
        }
        
        # 測試不同格式的導出效能
        formats = ['csv', 'json']
        
        for format_name in formats:
            start_time = time.time()
            
            for _ in range(100):
                result = export_context.export(poll_data, format_name)
                assert isinstance(result, bytes)
                assert len(result) > 0
            
            export_time = time.time() - start_time
            
            # 每種格式100次導出應該在2秒內完成
            assert export_time < 2.0, f"{format_name} export too slow: {export_time}s"
    
    def test_large_dataset_export_performance(self):
        """測試大數據集導出效能"""
        export_context = ExportContext()
        
        # 創建大量投票數據
        large_polls_data = {
            'polls_data': [
                {
                    'id': i,
                    'question': f'Poll {i}: What is your opinion on topic {i}?',
                    'vote_type': 'single',
                    'status': 'active' if i % 2 == 0 else 'ended',
                    'options': [
                        {'text': f'Option A for poll {i}', 'vote_count': i * 10},
                        {'text': f'Option B for poll {i}', 'vote_count': i * 5},
                        {'text': f'Option C for poll {i}', 'vote_count': i * 3}
                    ],
                    'total_votes': i * 18
                }
                for i in range(1, 501)  # 500個投票
            ]
        }
        
        # 測試JSON導出大數據集
        start_time = time.time()
        json_result = export_context.export(large_polls_data, 'json')
        json_export_time = time.time() - start_time
        
        assert isinstance(json_result, bytes)
        assert len(json_result) > 0
        
        # 500個投票的JSON導出應該在10秒內完成
        assert json_export_time < 10.0, f"Large JSON export too slow: {json_export_time}s"
        
        # 測試CSV導出大數據集
        start_time = time.time()
        csv_result = export_context.export(large_polls_data, 'csv')
        csv_export_time = time.time() - start_time
        
        assert isinstance(csv_result, bytes)
        assert len(csv_result) > 0
        
        # 500個投票的CSV導出應該在10秒內完成
        assert csv_export_time < 10.0, f"Large CSV export too slow: {csv_export_time}s"
    
    def test_concurrent_export_performance(self):
        """測試並發導出效能"""
        export_context = ExportContext()
        
        poll_data = {
            'poll_data': {
                'id': 1,
                'question': 'Concurrent export test?',
                'options': [{'text': 'Yes', 'vote_count': 10}]
            }
        }
        
        def export_worker(format_name):
            results = []
            for _ in range(20):
                result = export_context.export(poll_data, format_name)
                results.append(result)
            return results
        
        start_time = time.time()
        
        # 並發導出不同格式
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            futures = [
                executor.submit(export_worker, 'csv'),
                executor.submit(export_worker, 'json'),
                executor.submit(export_worker, 'csv'),
                executor.submit(export_worker, 'json'),
                executor.submit(export_worker, 'csv'),
                executor.submit(export_worker, 'json')
            ]
            
            results = [future.result() for future in futures]
        
        concurrent_export_time = time.time() - start_time
        
        # 驗證所有結果
        for worker_results in results:
            assert len(worker_results) == 20
            for result in worker_results:
                assert isinstance(result, bytes)
                assert len(result) > 0
        
        # 並發導出應該在合理時間內完成
        assert concurrent_export_time < 15.0, f"Concurrent export too slow: {concurrent_export_time}s"


class TestAPIPerformance:
    """API效能測試"""
    
    def test_application_startup_performance(self):
        """測試應用程序啟動效能"""
        # 測試測試應用程序啟動時間
        start_time = time.time()
        test_app = create_test_app()
        test_startup_time = time.time() - start_time
        
        assert test_startup_time < 3.0, f"Test app startup too slow: {test_startup_time}s"
        
        # 測試開發應用程序啟動時間
        start_time = time.time()
        dev_app = create_development_app()
        dev_startup_time = time.time() - start_time
        
        assert dev_startup_time < 5.0, f"Dev app startup too slow: {dev_startup_time}s"
    
    def test_api_endpoint_performance(self):
        """測試API端點效能"""
        from fastapi.testclient import TestClient
        
        app = create_test_app()
        client = TestClient(app)
        
        mock_user = {'user_id': 'U123', 'team_id': 'T123', 'role': 'user'}
        
        with patch('api.polls.get_current_user', return_value=mock_user), \
             patch('services.get_service') as mock_get_service:
            
            # 模擬快速服務
            mock_poll_repo = Mock()
            mock_poll_repo.get_polls.return_value = []
            mock_get_service.return_value = mock_poll_repo
            
            # 測試單個請求效能
            start_time = time.time()
            
            response = client.get("/api/polls", headers={
                "Authorization": "Bearer valid_token"
            })
            
            single_request_time = time.time() - start_time
            
            assert response.status_code == 200
            assert single_request_time < 1.0, f"Single API request too slow: {single_request_time}s"
            
            # 測試連續請求效能
            start_time = time.time()
            
            for _ in range(50):
                response = client.get("/api/polls", headers={
                    "Authorization": "Bearer valid_token"
                })
                assert response.status_code == 200
            
            sequential_requests_time = time.time() - start_time
            
            # 50個連續請求應該在5秒內完成
            assert sequential_requests_time < 5.0, f"Sequential requests too slow: {sequential_requests_time}s"
    
    def test_concurrent_api_performance(self):
        """測試並發API效能"""
        from fastapi.testclient import TestClient
        
        app = create_test_app()
        client = TestClient(app)
        
        mock_user = {'user_id': 'U123', 'team_id': 'T123', 'role': 'user'}
        
        with patch('api.polls.get_current_user', return_value=mock_user), \
             patch('services.get_service') as mock_get_service:
            
            mock_poll_repo = Mock()
            mock_poll_repo.get_polls.return_value = []
            mock_get_service.return_value = mock_poll_repo
            
            def make_requests():
                results = []
                for _ in range(10):
                    response = client.get("/api/polls", headers={
                        "Authorization": "Bearer valid_token"
                    })
                    results.append(response.status_code)
                return results
            
            start_time = time.time()
            
            # 使用10個並發線程，每個發遐10個請求
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(make_requests) for _ in range(10)]
                all_results = [future.result() for future in futures]
            
            concurrent_api_time = time.time() - start_time
            
            # 驗證所有請求成功
            for results in all_results:
                assert len(results) == 10
                for status_code in results:
                    assert status_code == 200
            
            # 100個並發請求應該在10秒內完成
            assert concurrent_api_time < 10.0, f"Concurrent API requests too slow: {concurrent_api_time}s"


class TestScalabilityPerformance:
    """可擴展性效能測試"""
    
    def test_service_container_scalability(self):
        """測試服務容器可擴展性"""
        # 測試創建多個服務容器的效能
        start_time = time.time()
        
        containers = []
        for _ in range(20):
            container = ServiceContainer()
            configure_services(container)
            containers.append(container)
        
        creation_time = time.time() - start_time
        
        # 20個服務容器的創建應該在10秒內完成
        assert creation_time < 10.0, f"Container creation too slow: {creation_time}s"
        
        # 測試在多個容器中獲取服務的效能
        start_time = time.time()
        
        for container in containers:
            for _ in range(10):
                container.get(DatabaseService)
                container.get(CacheService)
                container.get(PollRepository)
        
        service_access_time = time.time() - start_time
        
        # 在多個容器中獲取服務應該在合理時間內完成
        assert service_access_time < 5.0, f"Multi-container service access too slow: {service_access_time}s"
        
        # 清理所有容器
        for container in containers:
            container.clear()
    
    def test_strategy_pattern_scalability(self):
        """測試策略模式可擴展性"""
        validation_context = ValidationContext()
        export_context = ExportContext()
        
        # 測試添加大量自定義策略
        from strategies.validation import ValidationStrategy, ValidationResult, ValidationLevel
        from strategies.export import ExportStrategy
        
        # 創建多個自定義驗證策略
        class CustomValidationStrategy(ValidationStrategy):
            def __init__(self, strategy_id):
                self.strategy_id = strategy_id
            
            def validate(self, data):
                return [ValidationResult(
                    level=ValidationLevel.INFO,
                    message=f"Custom validation {self.strategy_id}",
                    field="custom"
                )]
            
            def get_name(self):
                return f"custom_validation_{self.strategy_id}"
        
        start_time = time.time()
        
        # 添加50個自定義驗證策略
        for i in range(50):
            validation_context.add_strategy(CustomValidationStrategy(i))
        
        strategy_addition_time = time.time() - start_time
        
        # 策略添加應該在短時間內完成
        assert strategy_addition_time < 2.0, f"Strategy addition too slow: {strategy_addition_time}s"
        
        # 測試在大量策略下的驗證效能
        test_data = {
            'question': 'Scalability test?',
            'options': ['Yes', 'No']
        }
        
        start_time = time.time()
        
        for _ in range(100):
            result = validation_context.validate(test_data)
            assert isinstance(result, list)
        
        validation_with_many_strategies_time = time.time() - start_time
        
        # 即使有大量策略，驗證也應該在合理時間內完成
        assert validation_with_many_strategies_time < 10.0, f"Validation with many strategies too slow: {validation_with_many_strategies_time}s"
    
    def test_memory_efficiency_under_load(self):
        """測試高負載下的內存效率"""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # 模擬高負載情況
        validation_context = ValidationContext()
        export_context = ExportContext()
        
        large_datasets = []
        
        # 創建多個大數據集
        for i in range(10):
            large_data = {
                'question': f'Large dataset test {i}?' * 50,
                'options': [f'Option {j} for dataset {i}' * 20 for j in range(50)],
                'vote_type': 'multiple',
                'metadata': {f'key_{k}': f'value_{k}' * 100 for k in range(100)}
            }
            large_datasets.append(large_data)
        
        # 測試高負載操作
        start_time = time.time()
        
        for _ in range(5):
            for data in large_datasets:
                # 驗證操作
                validation_result = validation_context.validate(data)
                assert isinstance(validation_result, list)
                
                # 導出操作
                export_data = {'poll_data': data}
                csv_result = export_context.export(export_data, 'csv')
                json_result = export_context.export(export_data, 'json')
                
                assert isinstance(csv_result, bytes)
                assert isinstance(json_result, bytes)
        
        high_load_time = time.time() - start_time
        peak_memory = process.memory_info().rss
        
        # 高負載操作應該在合理時間內完成
        assert high_load_time < 30.0, f"High load operations too slow: {high_load_time}s"
        
        # 內存增長應該在可接受範圍內
        memory_increase = (peak_memory - initial_memory) / (1024 * 1024)
        assert memory_increase < 200, f"Memory usage too high under load: {memory_increase}MB"


class TestPerformanceRegression:
    """效能退化測試"""
    
    def test_baseline_performance_metrics(self):
        """測試基線效能指標"""
        # 這些測試可以用來建立效能基線，並在未來的版本中檢測退化
        
        metrics = {}
        
        # 1. 服務容器初始化時間
        start_time = time.time()
        container = ServiceContainer()
        configure_services(container)
        metrics['container_init_time'] = time.time() - start_time
        
        # 2. 服務獲取時間
        start_time = time.time()
        for _ in range(100):
            container.get(DatabaseService)
        metrics['service_access_time'] = time.time() - start_time
        
        # 3. 驗證時間
        validation_context = ValidationContext()
        test_data = {
            'question': 'Baseline test?',
            'options': ['Yes', 'No'],
            'user_id': 'U123',
            'team_id': 'T123'
        }
        
        start_time = time.time()
        for _ in range(100):
            validation_context.validate(test_data)
        metrics['validation_time'] = time.time() - start_time
        
        # 4. 導出時間
        export_context = ExportContext()
        export_data = {'poll_data': test_data}
        
        start_time = time.time()
        for _ in range(100):
            export_context.export(export_data, 'json')
        metrics['export_time'] = time.time() - start_time
        
        # 驗證所有指標都在可接受範圍內
        assert metrics['container_init_time'] < 2.0
        assert metrics['service_access_time'] < 0.5
        assert metrics['validation_time'] < 3.0
        assert metrics['export_time'] < 2.0
        
        # 輸出效能指標供後續比較
        print(f"\nPerformance Baseline Metrics:")
        for metric, value in metrics.items():
            print(f"  {metric}: {value:.4f}s")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
