"""
增強的API測試
測試API路由模組分離和端點功能
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from fastapi import FastAPI
from typing import Dict, Any, Optional

from api.auth import router as auth_router, get_current_user, require_admin
from api.polls import router as polls_router
from api.admin import router as admin_router
from services import ServiceContainer, get_service, get_container
from services.implementations import (
    SimpleAuthenticationService, SQLAlchemyPollRepository,
    CompositeValidationService, JSONExportService,
    SimpleMonitoringService, SimpleConfigurationService
)
from app_factory import create_test_app


class TestAuthAPI:
    """認證API測試"""
    
    def setup_method(self):
        """測試設置"""
        self.app = create_test_app()
        self.client = TestClient(self.app)
        
        # 模擬認證服務
        self.mock_auth_service = Mock(spec=SimpleAuthenticationService)
        
        # 覆寫服務
        container = get_container()
        self.override_context = container.override_context()
        container.register_singleton(SimpleAuthenticationService, self.mock_auth_service)
    
    def teardown_method(self):
        """測試清理"""
        if hasattr(self, 'override_context'):
            self.override_context.__exit__(None, None, None)
    
    def test_login_endpoint(self):
        """測試登入端點"""
        # 模擬成功認證
        self.mock_auth_service.authenticate_user.return_value = {
            'user_id': 'U123',
            'team_id': 'T123',
            'role': 'user'
        }
        self.mock_auth_service.get_user_roles.return_value = ['user']
        
        # 發送登入請求
        response = self.client.post("/api/auth/login", json={
            "token": "valid_token",
            "team_id": "T123"
        })
        
        # 驗證回應
        assert response.status_code == 200
        data = response.json()
        assert data['user_id'] == 'U123'
        assert data['team_id'] == 'T123'
        assert data['authenticated'] is True
    
    def test_login_invalid_token(self):
        """測試無效token登入"""
        # 模擬認證失敗
        self.mock_auth_service.authenticate_user.return_value = None
        
        # 發送登入請求
        response = self.client.post("/api/auth/login", json={
            "token": "invalid_token",
            "team_id": "T123"
        })
        
        # 驗證回應
        assert response.status_code == 401
        assert "Invalid token" in response.json()['detail']
    
    def test_get_current_user_info(self):
        """測試獲取當前用戶信息"""
        # 模擬認證用戶
        mock_user = {
            'user_id': 'U123',
            'team_id': 'T123',
            'role': 'user'
        }
        
        with patch('api.auth.get_current_user', return_value=mock_user):
            self.mock_auth_service.get_user_roles.return_value = ['user']
            
            response = self.client.get("/api/auth/me", headers={
                "Authorization": "Bearer valid_token"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data['user_id'] == 'U123'
            assert data['authenticated'] is True
    
    def test_check_permission(self):
        """測試權限檢查"""
        mock_user = {
            'user_id': 'U123',
            'team_id': 'T123',
            'role': 'user'
        }
        
        with patch('api.auth.get_current_user', return_value=mock_user):
            self.mock_auth_service.check_permissions.return_value = True
            
            response = self.client.post("/api/auth/check-permission", 
                json={
                    "resource": "polls",
                    "action": "create"
                },
                headers={"Authorization": "Bearer valid_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data['has_permission'] is True
            assert data['resource'] == 'polls'
    
    def test_require_admin_decorator(self):
        """測試管理員權限裝飾器"""
        # 測試非管理員用戶
        mock_user = {
            'user_id': 'U123',
            'team_id': 'T123',
            'role': 'user'
        }
        
        with patch('api.auth.get_current_user', return_value=mock_user):
            response = self.client.get("/api/auth/admin/users", headers={
                "Authorization": "Bearer valid_token"
            })
            
            assert response.status_code == 403
            assert "Admin access required" in response.json()['detail']
        
        # 測試管理員用戶
        mock_admin = {
            'user_id': 'U123',
            'team_id': 'T123',
            'role': 'admin'
        }
        
        with patch('api.auth.get_current_user', return_value=mock_admin):
            response = self.client.get("/api/auth/admin/users", headers={
                "Authorization": "Bearer valid_token"
            })
            
            assert response.status_code == 200


class TestPollsAPI:
    """投票API測試"""
    
    def setup_method(self):
        """測試設置"""
        self.app = create_test_app()
        self.client = TestClient(self.app)
        
        # 模擬用戶
        self.mock_user = {
            'user_id': 'U123',
            'team_id': 'T123',
            'role': 'user'
        }
        
        # 模擬服務
        self.mock_poll_repo = Mock(spec=SQLAlchemyPollRepository)
        self.mock_validation_service = Mock(spec=CompositeValidationService)
        self.mock_event_publisher = Mock()
        
        # 覆寫服務
        container = get_container()
        self.override_context = container.override_context()
        container.register_singleton(SQLAlchemyPollRepository, self.mock_poll_repo)
        container.register_singleton(CompositeValidationService, self.mock_validation_service)
        container.register_singleton(Mock, self.mock_event_publisher)  # EventPublisher
    
    def teardown_method(self):
        """測試清理"""
        if hasattr(self, 'override_context'):
            self.override_context.__exit__(None, None, None)
    
    def test_get_polls(self):
        """測試獲取投票列表"""
        # 模擬投票數據
        mock_polls = [
            {
                'id': 1,
                'question': 'Test poll 1?',
                'status': 'active',
                'created_at': datetime.now()
            },
            {
                'id': 2,
                'question': 'Test poll 2?',
                'status': 'ended',
                'created_at': datetime.now() - timedelta(days=1)
            }
        ]
        
        self.mock_poll_repo.get_polls.return_value = mock_polls
        
        with patch('api.polls.get_current_user', return_value=self.mock_user):
            response = self.client.get("/api/polls", headers={
                "Authorization": "Bearer valid_token"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert len(data['polls']) == 2
            assert data['total_count'] == 2
            assert data['page'] == 1
    
    def test_get_polls_with_filters(self):
        """測試帶過濾器的投票列表"""
        self.mock_poll_repo.get_polls.return_value = []
        
        with patch('api.polls.get_current_user', return_value=self.mock_user):
            response = self.client.get("/api/polls?status=active&page=1&limit=10", 
                headers={"Authorization": "Bearer valid_token"}
            )
            
            assert response.status_code == 200
            # 驗證過濾器被正確傳遞
            call_args = self.mock_poll_repo.get_polls.call_args
            assert call_args[0][0] == 'T123'  # team_id
            assert 'status' in call_args[0][1]  # filters
    
    def test_get_single_poll(self):
        """測試獲取單個投票"""
        mock_poll = {
            'id': 1,
            'question': 'Test poll?',
            'team_id': 'T123',
            'status': 'active',
            'options': [{'text': 'Yes', 'vote_count': 3}]
        }
        
        self.mock_poll_repo.get_poll.return_value = mock_poll
        
        with patch('api.polls.get_current_user', return_value=self.mock_user):
            response = self.client.get("/api/polls/1", headers={
                "Authorization": "Bearer valid_token"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data['id'] == 1
            assert data['question'] == 'Test poll?'
    
    def test_get_poll_not_found(self):
        """測試投票不存在"""
        self.mock_poll_repo.get_poll.return_value = None
        
        with patch('api.polls.get_current_user', return_value=self.mock_user):
            response = self.client.get("/api/polls/999", headers={
                "Authorization": "Bearer valid_token"
            })
            
            assert response.status_code == 404
            assert "Poll not found" in response.json()['detail']
    
    def test_create_poll(self):
        """測試創建投票"""
        # 模擬驗證通過
        self.mock_validation_service.validate.return_value = {
            'valid': True,
            'errors': []
        }
        
        # 模擬投票創建成功
        self.mock_poll_repo.create_poll.return_value = 1
        
        with patch('api.polls.get_current_user', return_value=self.mock_user):
            response = self.client.post("/api/polls", 
                json={
                    "question": "What is your favorite color?",
                    "options": ["Red", "Blue", "Green"],
                    "vote_type": "single",
                    "team_id": "T123",
                    "channel_id": "C123"
                },
                headers={"Authorization": "Bearer valid_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data['poll_id'] == 1
            assert "created successfully" in data['message']
    
    def test_create_poll_validation_failed(self):
        """測試創建投票驗證失敗"""
        # 模擬驗證失敗
        self.mock_validation_service.validate.return_value = {
            'valid': False,
            'errors': ['Question is too short']
        }
        
        with patch('api.polls.get_current_user', return_value=self.mock_user):
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
    
    def test_update_poll(self):
        """測試更新投票"""
        mock_poll = {
            'id': 1,
            'creator_id': 'U123',
            'team_id': 'T123'
        }
        
        self.mock_poll_repo.get_poll.return_value = mock_poll
        self.mock_poll_repo.update_poll.return_value = True
        
        with patch('api.polls.get_current_user', return_value=self.mock_user):
            response = self.client.put("/api/polls/1", 
                json={
                    "question": "Updated question?",
                    "status": "ended"
                },
                headers={"Authorization": "Bearer valid_token"}
            )
            
            assert response.status_code == 200
            assert "updated successfully" in response.json()['message']
    
    def test_update_poll_permission_denied(self):
        """測試更新投票權限拒絕"""
        mock_poll = {
            'id': 1,
            'creator_id': 'U999',  # 不同的創建者
            'team_id': 'T123'
        }
        
        self.mock_poll_repo.get_poll.return_value = mock_poll
        
        with patch('api.polls.get_current_user', return_value=self.mock_user):
            response = self.client.put("/api/polls/1", 
                json={"question": "Updated question?"},
                headers={"Authorization": "Bearer valid_token"}
            )
            
            assert response.status_code == 403
            assert "Permission denied" in response.json()['detail']
    
    def test_delete_poll(self):
        """測試刪除投票"""
        mock_poll = {
            'id': 1,
            'creator_id': 'U123',
            'team_id': 'T123'
        }
        
        self.mock_poll_repo.get_poll.return_value = mock_poll
        self.mock_poll_repo.delete_poll.return_value = True
        
        with patch('api.polls.get_current_user', return_value=self.mock_user):
            response = self.client.delete("/api/polls/1", headers={
                "Authorization": "Bearer valid_token"
            })
            
            assert response.status_code == 200
            assert "deleted successfully" in response.json()['message']
    
    def test_duplicate_poll(self):
        """測試複製投票"""
        mock_poll = {
            'id': 1,
            'question': 'Original question?',
            'team_id': 'T123',
            'channel_id': 'C123',
            'vote_type': 'single',
            'options': [{'text': 'Yes'}, {'text': 'No'}]
        }
        
        self.mock_poll_repo.get_poll.return_value = mock_poll
        self.mock_poll_repo.create_poll.return_value = 2
        
        with patch('api.polls.get_current_user', return_value=self.mock_user):
            response = self.client.post("/api/polls/1/duplicate", 
                json={"new_question": "Copy of original question?"},
                headers={"Authorization": "Bearer valid_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data['new_poll_id'] == 2
            assert "duplicated successfully" in data['message']
    
    def test_get_poll_stats(self):
        """測試獲取投票統計"""
        mock_poll = {
            'id': 1,
            'question': 'Test poll?',
            'team_id': 'T123',
            'status': 'active',
            'created_at': datetime.now(),
            'options': [
                {'id': 1, 'text': 'Yes', 'vote_count': 3},
                {'id': 2, 'text': 'No', 'vote_count': 2}
            ]
        }
        
        self.mock_poll_repo.get_poll.return_value = mock_poll
        
        with patch('api.polls.get_current_user', return_value=self.mock_user):
            response = self.client.get("/api/polls/1/stats", headers={
                "Authorization": "Bearer valid_token"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data['total_votes'] == 5
            assert len(data['option_stats']) == 2
            assert data['option_stats'][0]['percentage'] == 60.0  # 3/5 * 100


class TestAdminAPI:
    """管理員API測試"""
    
    def setup_method(self):
        """測試設置"""
        self.app = create_test_app()
        self.client = TestClient(self.app)
        
        # 模擬管理員用戶
        self.mock_admin = {
            'user_id': 'U123',
            'team_id': 'T123',
            'role': 'admin'
        }
        
        # 模擬服務
        self.mock_poll_repo = Mock(spec=SQLAlchemyPollRepository)
        self.mock_export_service = Mock(spec=JSONExportService)
        self.mock_monitoring_service = Mock(spec=SimpleMonitoringService)
        self.mock_config_service = Mock(spec=SimpleConfigurationService)
        
        # 覆寫服務
        container = get_container()
        self.override_context = container.override_context()
        container.register_singleton(SQLAlchemyPollRepository, self.mock_poll_repo)
        container.register_singleton(JSONExportService, self.mock_export_service)
        container.register_singleton(SimpleMonitoringService, self.mock_monitoring_service)
        container.register_singleton(SimpleConfigurationService, self.mock_config_service)
    
    def teardown_method(self):
        """測試清理"""
        if hasattr(self, 'override_context'):
            self.override_context.__exit__(None, None, None)
    
    def test_get_overview_stats(self):
        """測試獲取概覽統計"""
        mock_polls = [
            {'status': 'active', 'total_votes': 10, 'creator_id': 'U123'},
            {'status': 'ended', 'total_votes': 5, 'creator_id': 'U456'},
            {'status': 'active', 'total_votes': 8, 'creator_id': 'U123'}
        ]
        
        self.mock_poll_repo.get_polls.return_value = mock_polls
        
        with patch('api.admin.require_admin', return_value=self.mock_admin):
            response = self.client.get("/api/admin/overview/stats?period=30d", 
                headers={"Authorization": "Bearer admin_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data['total_polls'] == 3
            assert data['total_votes'] == 23
            assert data['active_polls'] == 2
            assert data['active_users'] == 2
            assert data['period'] == '30d'
    
    def test_get_activity_chart(self):
        """測試獲取活動圖表"""
        with patch('api.admin.require_admin', return_value=self.mock_admin):
            response = self.client.get("/api/admin/overview/activity?period=7d", 
                headers={"Authorization": "Bearer admin_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert 'labels' in data
            assert 'polls_created' in data
            assert 'votes_cast' in data
            assert len(data['labels']) == 7  # 7 days
    
    def test_export_polls(self):
        """測試導出投票"""
        # 模擬導出數據
        export_data = b"poll_id,question,status\n1,Test poll?,active\n"
        self.mock_export_service.export_poll.return_value = export_data
        
        with patch('api.admin.require_admin', return_value=self.mock_admin):
            response = self.client.post("/api/admin/export", 
                json={
                    "poll_ids": [1],
                    "format": "csv",
                    "include_analytics": True
                },
                headers={"Authorization": "Bearer admin_token"}
            )
            
            assert response.status_code == 200
            # 驗證導出服務被調用
            self.mock_export_service.export_poll.assert_called_once()
    
    def test_get_system_health(self):
        """測試獲取系統健康狀態"""
        mock_health = {
            'system': {'status': 'healthy'},
            'database': {'status': 'healthy'},
            'cache': {'status': 'healthy'}
        }
        
        self.mock_monitoring_service.health_check.return_value = mock_health
        
        with patch('api.admin.require_admin', return_value=self.mock_admin):
            response = self.client.get("/api/admin/system/health", 
                headers={"Authorization": "Bearer admin_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data['system']['status'] == 'healthy'
    
    def test_get_system_metrics(self):
        """測試獲取系統指標"""
        mock_metrics = {
            'cpu_usage': 45.2,
            'memory_usage': 67.8,
            'disk_usage': 23.1
        }
        
        self.mock_monitoring_service.get_metrics.return_value = mock_metrics
        
        with patch('api.admin.require_admin', return_value=self.mock_admin):
            response = self.client.get("/api/admin/system/metrics", 
                headers={"Authorization": "Bearer admin_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert 'metrics' in data
            assert data['metrics']['cpu_usage'] == 45.2
    
    def test_get_system_config(self):
        """測試獲取系統配置"""
        mock_validation = {
            'status': 'valid',
            'warnings': [],
            'errors': []
        }
        
        self.mock_config_service.validate_config.return_value = mock_validation
        
        with patch('api.admin.require_admin', return_value=self.mock_admin):
            response = self.client.get("/api/admin/system/config", 
                headers={"Authorization": "Bearer admin_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert 'configuration_status' in data
            assert 'timestamp' in data
    
    def test_update_system_config(self):
        """測試更新系統配置"""
        self.mock_config_service.set_config.return_value = True
        
        with patch('api.admin.require_admin', return_value=self.mock_admin):
            response = self.client.post("/api/admin/system/config", 
                json={
                    "key": "max_polls_per_day",
                    "value": 10
                },
                headers={"Authorization": "Bearer admin_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "updated successfully" in data['message']
            assert data['key'] == 'max_polls_per_day'
    
    def test_list_users(self):
        """測試列出用戶"""
        with patch('api.admin.require_admin', return_value=self.mock_admin):
            response = self.client.get("/api/admin/users?page=1&limit=10", 
                headers={"Authorization": "Bearer admin_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert 'users' in data
            assert 'total_count' in data
            assert 'page' in data
            assert 'limit' in data
    
    def test_get_poll_analytics(self):
        """測試獲取投票分析"""
        mock_polls = [
            {'total_votes': 10, 'vote_type': 'single', 'status': 'active'},
            {'total_votes': 5, 'vote_type': 'multiple', 'status': 'ended'},
            {'total_votes': 8, 'vote_type': 'single', 'status': 'active'}
        ]
        
        self.mock_poll_repo.get_polls.return_value = mock_polls
        
        with patch('api.admin.require_admin', return_value=self.mock_admin):
            response = self.client.get("/api/admin/analytics/polls?period=30d", 
                headers={"Authorization": "Bearer admin_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data['total_polls'] == 3
            assert data['avg_votes_per_poll'] == 7.67  # (10+5+8)/3
            assert 'vote_type_distribution' in data
            assert data['vote_type_distribution']['single'] == 2
            assert data['vote_type_distribution']['multiple'] == 1


class TestAPIErrorHandling:
    """API錯誤處理測試"""
    
    def test_authentication_required(self):
        """測試需要認證的端點"""
        app = create_test_app()
        client = TestClient(app)
        
        # 不提供認證頭
        response = client.get("/api/polls")
        assert response.status_code == 403  # FastAPI HTTPBearer預設回應
    
    def test_invalid_json_payload(self):
        """測試無效JSON負載"""
        app = create_test_app()
        client = TestClient(app)
        
        with patch('api.polls.get_current_user', return_value={'user_id': 'U123'}):
            response = client.post("/api/polls", 
                data="invalid json",
                headers={
                    "Authorization": "Bearer valid_token",
                    "Content-Type": "application/json"
                }
            )
            assert response.status_code == 422  # Pydantic validation error
    
    def test_service_unavailable(self):
        """測試服務不可用"""
        app = create_test_app()
        client = TestClient(app)
        
        # 模擬服務異常
        with patch('services.get_service', side_effect=Exception("Service unavailable")):
            with patch('api.polls.get_current_user', return_value={'user_id': 'U123'}):
                response = client.get("/api/polls", headers={
                    "Authorization": "Bearer valid_token"
                })
                assert response.status_code == 500


class TestAPIIntegration:
    """API集成測試"""
    
    def test_complete_poll_workflow(self):
        """測試完整投票工作流程"""
        app = create_test_app()
        client = TestClient(app)
        
        mock_user = {'user_id': 'U123', 'team_id': 'T123', 'role': 'user'}
        
        # 模擬所有必要的服務
        with patch('api.polls.get_current_user', return_value=mock_user), \
             patch('api.polls.get_service') as mock_get_service:
            
            # 配置模擬服務
            mock_validation = Mock()
            mock_validation.validate.return_value = {'valid': True, 'errors': []}
            mock_poll_repo = Mock()
            mock_poll_repo.create_poll.return_value = 1
            mock_poll_repo.get_poll.return_value = {
                'id': 1, 'question': 'Test?', 'team_id': 'T123', 'status': 'active',
                'options': [{'id': 1, 'text': 'Yes', 'vote_count': 0}]
            }
            mock_event_publisher = Mock()
            
            def mock_service_factory(service_type):
                if 'Validation' in str(service_type):
                    return mock_validation
                elif 'Repository' in str(service_type):
                    return mock_poll_repo
                elif 'Publisher' in str(service_type):
                    return mock_event_publisher
                return Mock()
            
            mock_get_service.side_effect = mock_service_factory
            
            # 1. 創建投票
            create_response = client.post("/api/polls", 
                json={
                    "question": "What is your favorite color?",
                    "options": ["Red", "Blue", "Green"],
                    "vote_type": "single",
                    "team_id": "T123",
                    "channel_id": "C123"
                },
                headers={"Authorization": "Bearer valid_token"}
            )
            assert create_response.status_code == 200
            
            # 2. 獲取投票詳情
            get_response = client.get("/api/polls/1", headers={
                "Authorization": "Bearer valid_token"
            })
            assert get_response.status_code == 200
            
            # 3. 獲取投票統計
            stats_response = client.get("/api/polls/1/stats", headers={
                "Authorization": "Bearer valid_token"
            })
            assert stats_response.status_code == 200
    
    def test_cross_module_api_integration(self):
        """測試跨模組API集成"""
        app = create_test_app()
        client = TestClient(app)
        
        # 驗證所有API模組都被包含
        # 檢查路由是否正確註冊
        routes = [route.path for route in app.routes]
        
        # 認證API路由
        auth_routes = [r for r in routes if r.startswith('/api/auth')]
        assert len(auth_routes) > 0
        
        # 投票API路由
        polls_routes = [r for r in routes if r.startswith('/api/polls')]
        assert len(polls_routes) > 0
        
        # 管理員API路由
        admin_routes = [r for r in routes if r.startswith('/api/admin')]
        assert len(admin_routes) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
