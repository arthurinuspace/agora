"""
增強的策略模式測試
測試驗證和導出策略的進階功能
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
import csv
import io
from datetime import datetime
from typing import Dict, Any, List, Optional

from strategies.validation import (
    ValidationContext, ValidationStrategy, ValidationResult, ValidationLevel,
    PollQuestionValidationStrategy, PollOptionsValidationStrategy,
    SecurityValidationStrategy, UserPermissionValidationStrategy,
    TeamSettingsValidationStrategy
)
from strategies.export import (
    ExportContext, ExportStrategy,
    CSVExportStrategy, JSONExportStrategy, ExcelExportStrategy
)


class TestValidationStrategiesAdvanced:
    """進階驗證策略測試"""
    
    def test_validation_context_strategy_management(self):
        """測試驗證上下文策略管理"""
        context = ValidationContext()
        
        # 測試添加自定義策略
        class CustomValidationStrategy(ValidationStrategy):
            def validate(self, data: Dict[str, Any]) -> List[ValidationResult]:
                return [ValidationResult(
                    level=ValidationLevel.INFO,
                    message="Custom validation passed",
                    field="custom"
                )]
            
            def get_name(self) -> str:
                return "custom_validation"
        
        custom_strategy = CustomValidationStrategy()
        context.add_strategy(custom_strategy)
        
        # 驗證策略被添加
        strategy_names = context.get_strategy_names()
        assert "custom_validation" in strategy_names
        
        # 測試移除策略
        context.remove_strategy("custom_validation")
        strategy_names = context.get_strategy_names()
        assert "custom_validation" not in strategy_names
    
    def test_validation_context_selective_execution(self):
        """測試選擇性執行驗證策略"""
        context = ValidationContext()
        
        # 測試只執行特定策略
        result = context.validate(
            {
                'question': 'What is your favorite color?',
                'options': ['Red', 'Blue', 'Green']
            },
            strategy_names=['poll_question_validation']
        )
        
        # 應該只有問題驗證的結果
        assert len(result) > 0
        # 驗證結果中不應該有選項驗證的錯誤
    
    def test_validation_context_error_aggregation(self):
        """測試驗證錯誤聚合"""
        context = ValidationContext()
        
        # 測試多個錯誤的数據
        invalid_data = {
            'question': 'Hi?',  # 太短
            'options': ['Yes'],  # 選項太少
            'user_id': '',  # 空用戶ID
            'team_id': ''
        }
        
        result = context.validate(invalid_data)
        
        # 應該有多個錯誤
        errors = [r for r in result if r.level == ValidationLevel.ERROR]
        assert len(errors) > 1
        
        # 測試錯誤統計
        error_summary = context.get_error_summary(result)
        assert error_summary['error_count'] > 0
        assert error_summary['warning_count'] >= 0
    
    def test_poll_question_validation_edge_cases(self):
        """測試問題驗證邊界情況"""
        strategy = PollQuestionValidationStrategy()
        
        # 測試空問題
        result = strategy.validate({'question': ''})
        errors = [r for r in result if r.level == ValidationLevel.ERROR]
        assert len(errors) > 0
        assert any('empty' in r.message.lower() for r in errors)
        
        # 測試只有空格的問題
        result = strategy.validate({'question': '   '})
        errors = [r for r in result if r.level == ValidationLevel.ERROR]
        assert len(errors) > 0
        
        # 測試太長的問題
        long_question = 'What is your favorite ' + 'very ' * 100 + 'long question?'
        result = strategy.validate({'question': long_question})
        warnings = [r for r in result if r.level == ValidationLevel.WARNING]
        assert len(warnings) > 0
        
        # 測試包含特殊字元的問題
        result = strategy.validate({'question': 'What\'s your "favorite" color? 🎨'})
        errors = [r for r in result if r.level == ValidationLevel.ERROR]
        assert len(errors) == 0  # 應該允許合理的特殊字元
    
    def test_poll_options_validation_edge_cases(self):
        """測試選項驗證邊界情況"""
        strategy = PollOptionsValidationStrategy()
        
        # 測試空選項列表
        result = strategy.validate({'options': []})
        errors = [r for r in result if r.level == ValidationLevel.ERROR]
        assert len(errors) > 0
        
        # 測試包含空字串的選項
        result = strategy.validate({'options': ['Yes', '', 'No']})
        errors = [r for r in result if r.level == ValidationLevel.ERROR]
        assert len(errors) > 0
        
        # 測試重複的選項
        result = strategy.validate({'options': ['Yes', 'No', 'Yes']})
        warnings = [r for r in result if r.level == ValidationLevel.WARNING]
        assert len(warnings) > 0
        
        # 測試過多的選項
        too_many_options = [f'Option {i}' for i in range(1, 21)]  # 20個選項
        result = strategy.validate({'options': too_many_options})
        warnings = [r for r in result if r.level == ValidationLevel.WARNING]
        assert len(warnings) > 0
        
        # 測試過長的選項文字
        long_option = 'This is a very ' + 'very ' * 20 + 'long option text'
        result = strategy.validate({'options': ['Short', long_option]})
        warnings = [r for r in result if r.level == ValidationLevel.WARNING]
        assert len(warnings) > 0
    
    def test_security_validation_comprehensive(self):
        """測試安全驗證綜合功能"""
        strategy = SecurityValidationStrategy()
        
        # 測試XSS攻擊
        xss_data = {
            'question': 'Click here: <script>alert("xss")</script>',
            'options': ['<img src=x onerror=alert(1)>', 'Normal option']
        }
        result = strategy.validate(xss_data)
        errors = [r for r in result if r.level == ValidationLevel.ERROR]
        assert len(errors) > 0
        assert any('script' in r.message.lower() or 'harmful' in r.message.lower() for r in errors)
        
        # 測試SQL注入
        sql_injection_data = {
            'question': "What's your name'; DROP TABLE users; --",
            'options': ['Option 1', 'Option 2']
        }
        result = strategy.validate(sql_injection_data)
        warnings = [r for r in result if r.level == ValidationLevel.WARNING]
        assert len(warnings) > 0
        
        # 測試惡意鏈接
        malicious_link_data = {
            'question': 'Click here: http://malicious-site.com/phishing',
            'options': ['Yes', 'No']
        }
        result = strategy.validate(malicious_link_data)
        warnings = [r for r in result if r.level == ValidationLevel.WARNING]
        # 可能會有警告，但不一定有錯誤
        
        # 測試安全的內容
        safe_data = {
            'question': 'What is your favorite programming language?',
            'options': ['Python', 'JavaScript', 'Java', 'Go']
        }
        result = strategy.validate(safe_data)
        errors = [r for r in result if r.level == ValidationLevel.ERROR]
        assert len(errors) == 0
    
    def test_user_permission_validation(self):
        """測試用戶權限驗證"""
        strategy = UserPermissionValidationStrategy()
        
        # 測試缺少用戶信息
        result = strategy.validate({})
        errors = [r for r in result if r.level == ValidationLevel.ERROR]
        assert len(errors) > 0
        
        # 測試無效用戶ID
        result = strategy.validate({'user_id': '', 'team_id': 'T123'})
        errors = [r for r in result if r.level == ValidationLevel.ERROR]
        assert len(errors) > 0
        
        # 測試有效用戶信息
        result = strategy.validate({
            'user_id': 'U123',
            'team_id': 'T123',
            'channel_id': 'C123'
        })
        errors = [r for r in result if r.level == ValidationLevel.ERROR]
        assert len(errors) == 0
    
    def test_team_settings_validation(self):
        """測試團隊設定驗證"""
        strategy = TeamSettingsValidationStrategy()
        
        # 測試缺少團隊ID
        result = strategy.validate({})
        errors = [r for r in result if r.level == ValidationLevel.ERROR]
        assert len(errors) > 0
        
        # 測試有效團隊設定
        result = strategy.validate({
            'team_id': 'T123',
            'channel_id': 'C123'
        })
        errors = [r for r in result if r.level == ValidationLevel.ERROR]
        assert len(errors) == 0
    
    def test_validation_result_properties(self):
        """測試驗證結果屬性"""
        result = ValidationResult(
            level=ValidationLevel.ERROR,
            message="Test error message",
            field="test_field",
            code="TEST_001"
        )
        
        assert result.level == ValidationLevel.ERROR
        assert result.message == "Test error message"
        assert result.field == "test_field"
        assert result.code == "TEST_001"
        
        # 測試字串表示
        str_repr = str(result)
        assert "ERROR" in str_repr
        assert "Test error message" in str_repr
    
    def test_validation_level_enum(self):
        """測試驗證級別枚舉"""
        assert ValidationLevel.ERROR.value == "error"
        assert ValidationLevel.WARNING.value == "warning"
        assert ValidationLevel.INFO.value == "info"
        
        # 測試級別排序
        levels = [ValidationLevel.INFO, ValidationLevel.ERROR, ValidationLevel.WARNING]
        sorted_levels = sorted(levels, key=lambda x: x.value)
        assert sorted_levels[0] == ValidationLevel.ERROR


class TestExportStrategiesAdvanced:
    """進階導出策略測試"""
    
    def test_export_context_format_management(self):
        """測試導出上下文格式管理"""
        context = ExportContext()
        
        # 測試獲取支持的格式
        formats = context.get_supported_formats()
        format_names = [f['name'] for f in formats]
        assert 'CSV' in format_names
        assert 'JSON' in format_names
        assert 'Excel' in format_names
        
        # 測試添加自定義格式
        class CustomExportStrategy(ExportStrategy):
            def export(self, data: Dict[str, Any], options: Dict[str, Any] = None) -> bytes:
                return b"custom format data"
            
            def get_format_name(self) -> str:
                return "CUSTOM"
            
            def get_file_extension(self) -> str:
                return "custom"
            
            def get_mime_type(self) -> str:
                return "application/custom"
        
        custom_strategy = CustomExportStrategy()
        context.add_strategy(custom_strategy)
        
        # 驗證自定義格式被添加
        updated_formats = context.get_supported_formats()
        updated_format_names = [f['name'] for f in updated_formats]
        assert 'CUSTOM' in updated_format_names
    
    def test_csv_export_comprehensive(self):
        """測試CSV導出綜合功能"""
        strategy = CSVExportStrategy()
        
        # 測試單個投票導出
        single_poll_data = {
            'poll_data': {
                'id': 1,
                'question': 'What is your favorite color?',
                'vote_type': 'single',
                'status': 'active',
                'created_at': datetime.now(),
                'options': [
                    {'text': 'Red', 'vote_count': 5},
                    {'text': 'Blue', 'vote_count': 3},
                    {'text': 'Green', 'vote_count': 2}
                ],
                'total_votes': 10
            }
        }
        
        result = strategy.export(single_poll_data)
        assert isinstance(result, bytes)
        
        # 驗證CSV內容
        csv_content = result.decode('utf-8')
        assert 'What is your favorite color?' in csv_content
        assert 'Red' in csv_content
        assert '5' in csv_content
        
        # 測試多個投票導出
        multiple_polls_data = {
            'polls_data': [
                single_poll_data['poll_data'],
                {
                    'id': 2,
                    'question': 'Best programming language?',
                    'vote_type': 'multiple',
                    'status': 'ended',
                    'options': [{'text': 'Python', 'vote_count': 8}],
                    'total_votes': 8
                }
            ]
        }
        
        result = strategy.export(multiple_polls_data)
        csv_content = result.decode('utf-8')
        assert 'What is your favorite color?' in csv_content
        assert 'Best programming language?' in csv_content
        
        # 測試包含分析數據的導出
        analytics_data = {
            'poll_data': single_poll_data['poll_data'],
            'analytics': {
                'participation_rate': 75.5,
                'avg_response_time': 2.3,
                'peak_voting_hour': 14
            }
        }
        
        result = strategy.export(analytics_data, {'include_analytics': True})
        csv_content = result.decode('utf-8')
        assert '75.5' in csv_content or 'participation_rate' in csv_content
    
    def test_json_export_comprehensive(self):
        """測試JSON導出綜合功能"""
        strategy = JSONExportStrategy()
        
        # 測試單個投票導出
        poll_data = {
            'poll_data': {
                'id': 1,
                'question': 'Test question?',
                'vote_type': 'single',
                'status': 'active',
                'created_at': datetime.now().isoformat(),
                'options': [
                    {'text': 'Option 1', 'vote_count': 3},
                    {'text': 'Option 2', 'vote_count': 2}
                ]
            }
        }
        
        result = strategy.export(poll_data)
        assert isinstance(result, bytes)
        
        # 驗證JSON結構
        json_data = json.loads(result.decode('utf-8'))
        assert 'poll' in json_data
        assert 'exported_at' in json_data
        assert 'format' in json_data
        assert json_data['format'] == 'JSON'
        assert json_data['poll']['question'] == 'Test question?'
        
        # 測試包含匿名化選項
        result = strategy.export(poll_data, {'anonymize': True})
        json_data = json.loads(result.decode('utf-8'))
        assert 'anonymized' in json_data
        assert json_data['anonymized'] is True
        
        # 測試多個投票導出
        multiple_data = {
            'polls_data': [poll_data['poll_data'], poll_data['poll_data']]
        }
        
        result = strategy.export(multiple_data)
        json_data = json.loads(result.decode('utf-8'))
        assert 'polls' in json_data
        assert len(json_data['polls']) == 2
    
    def test_excel_export_functionality(self):
        """測試Excel導出功能"""
        strategy = ExcelExportStrategy()
        
        poll_data = {
            'poll_data': {
                'id': 1,
                'question': 'Test Excel export?',
                'vote_type': 'single',
                'status': 'active',
                'options': [
                    {'text': 'Yes', 'vote_count': 10},
                    {'text': 'No', 'vote_count': 5}
                ]
            }
        }
        
        result = strategy.export(poll_data)
        assert isinstance(result, bytes)
        assert len(result) > 0
        
        # 驗證Excel檔案簡單特徵（不需要完整解析）
        # Excel檔案通常以PK開頭（ZIP格式）
        assert result[:2] == b'PK' or len(result) > 100  # 簡單檢查
    
    def test_export_strategy_metadata(self):
        """測試導出策略元數據"""
        csv_strategy = CSVExportStrategy()
        json_strategy = JSONExportStrategy()
        excel_strategy = ExcelExportStrategy()
        
        # 測試CSV元數據
        assert csv_strategy.get_format_name() == "CSV"
        assert csv_strategy.get_file_extension() == "csv"
        assert csv_strategy.get_mime_type() == "text/csv"
        
        # 測試JSON元數據
        assert json_strategy.get_format_name() == "JSON"
        assert json_strategy.get_file_extension() == "json"
        assert json_strategy.get_mime_type() == "application/json"
        
        # 測試Excel元數據
        assert excel_strategy.get_format_name() == "Excel"
        assert excel_strategy.get_file_extension() == "xlsx"
        assert excel_strategy.get_mime_type() == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    
    def test_export_options_handling(self):
        """測試導出選項處理"""
        strategy = JSONExportStrategy()
        
        poll_data = {
            'poll_data': {
                'id': 1,
                'question': 'Test options?',
                'options': [{'text': 'Yes', 'vote_count': 1}]
            }
        }
        
        # 測試不同的導出選項
        options_to_test = [
            {'include_analytics': True},
            {'anonymize': True},
            {'include_voter_ids': False},
            {'format_pretty': True},
            {'include_metadata': True}
        ]
        
        for options in options_to_test:
            result = strategy.export(poll_data, options)
            assert isinstance(result, bytes)
            assert len(result) > 0
            
            # 驗證JSON格式正確
            json_data = json.loads(result.decode('utf-8'))
            assert isinstance(json_data, dict)
    
    def test_export_error_handling(self):
        """測試導出錯誤處理"""
        strategy = CSVExportStrategy()
        
        # 測試空數據
        empty_data = {}
        result = strategy.export(empty_data)
        assert isinstance(result, bytes)
        
        # 測試無效數據結構
        invalid_data = {'invalid_key': 'invalid_value'}
        result = strategy.export(invalid_data)
        assert isinstance(result, bytes)
        
        # 測試缺少關鍵欄位的數據
        incomplete_data = {
            'poll_data': {
                'id': 1
                # 缺少question和options
            }
        }
        result = strategy.export(incomplete_data)
        assert isinstance(result, bytes)
    
    def test_export_context_error_scenarios(self):
        """測試導出上下文錯誤情況"""
        context = ExportContext()
        
        # 測試不支持的格式
        with pytest.raises(ValueError):
            context.export({}, 'unsupported_format')
        
        # 測試空格式名稱
        with pytest.raises(ValueError):
            context.export({}, '')
        
        # 測試None格式名稱
        with pytest.raises(ValueError):
            context.export({}, None)


class TestStrategyPatternsIntegration:
    """策略模式集成測試"""
    
    def test_validation_and_export_workflow(self):
        """測試驗證和導出工作流程"""
        # 1. 驗證數據
        validation_context = ValidationContext()
        
        poll_data = {
            'question': 'What is your favorite programming language?',
            'options': ['Python', 'JavaScript', 'Java', 'Go'],
            'vote_type': 'single',
            'user_id': 'U123',
            'team_id': 'T123'
        }
        
        validation_result = validation_context.validate(poll_data)
        errors = [r for r in validation_result if r.level == ValidationLevel.ERROR]
        assert len(errors) == 0  # 數據應該通過驗證
        
        # 2. 模擬投票創建和投票
        created_poll = {
            'id': 1,
            'question': poll_data['question'],
            'vote_type': poll_data['vote_type'],
            'status': 'active',
            'created_at': datetime.now(),
            'options': [
                {'text': 'Python', 'vote_count': 15},
                {'text': 'JavaScript', 'vote_count': 12},
                {'text': 'Java', 'vote_count': 8},
                {'text': 'Go', 'vote_count': 5}
            ],
            'total_votes': 40
        }
        
        # 3. 導出投票結果
        export_context = ExportContext()
        
        export_data = {
            'poll_data': created_poll,
            'analytics': {
                'participation_rate': 80.0,
                'avg_response_time': 1.5
            }
        }
        
        # 測試不同格式的導出
        for format_name in ['csv', 'json', 'excel']:
            result = export_context.export(export_data, format_name)
            assert isinstance(result, bytes)
            assert len(result) > 0
    
    def test_custom_strategy_extension(self):
        """測試自定義策略擴展"""
        # 創建自定義驗證策略
        class BusinessRuleValidationStrategy(ValidationStrategy):
            def validate(self, data: Dict[str, Any]) -> List[ValidationResult]:
                results = []
                
                # 檢查是否在工作時間內創建投票
                current_hour = datetime.now().hour
                if current_hour < 9 or current_hour > 17:
                    results.append(ValidationResult(
                        level=ValidationLevel.WARNING,
                        message="Poll created outside business hours",
                        field="created_at",
                        code="BUSINESS_HOURS"
                    ))
                
                return results
            
            def get_name(self) -> str:
                return "business_rule_validation"
        
        # 創建自定義導出策略
        class XMLExportStrategy(ExportStrategy):
            def export(self, data: Dict[str, Any], options: Dict[str, Any] = None) -> bytes:
                # 簡單的XML導出
                xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n<poll>\n'
                
                if 'poll_data' in data:
                    poll = data['poll_data']
                    xml_content += f'  <id>{poll.get("id", "unknown")}</id>\n'
                    xml_content += f'  <question>{poll.get("question", "")}</question>\n'
                    xml_content += '  <options>\n'
                    
                    for option in poll.get('options', []):
                        xml_content += f'    <option votes="{option.get("vote_count", 0)}">{option.get("text", "")}</option>\n'
                    
                    xml_content += '  </options>\n'
                
                xml_content += '</poll>'
                return xml_content.encode('utf-8')
            
            def get_format_name(self) -> str:
                return "XML"
            
            def get_file_extension(self) -> str:
                return "xml"
            
            def get_mime_type(self) -> str:
                return "application/xml"
        
        # 測試自定義策略集成
        validation_context = ValidationContext()
        validation_context.add_strategy(BusinessRuleValidationStrategy())
        
        export_context = ExportContext()
        export_context.add_strategy(XMLExportStrategy())
        
        # 測試使用自定義驗證策略
        test_data = {
            'question': 'Test question?',
            'options': ['Yes', 'No'],
            'user_id': 'U123',
            'team_id': 'T123'
        }
        
        validation_result = validation_context.validate(test_data)
        # 可能有工作時間警告
        
        # 測試使用自定義導出策略
        export_data = {
            'poll_data': {
                'id': 1,
                'question': 'Test XML export?',
                'options': [{'text': 'Yes', 'vote_count': 3}]
            }
        }
        
        xml_result = export_context.export(export_data, 'xml')
        assert isinstance(xml_result, bytes)
        xml_content = xml_result.decode('utf-8')
        assert '<?xml' in xml_content
        assert '<poll>' in xml_content
        assert 'Test XML export?' in xml_content
    
    def test_strategy_performance(self):
        """測試策略性能"""
        import time
        
        validation_context = ValidationContext()
        export_context = ExportContext()
        
        # 測試大量數據驗證
        large_data = {
            'question': 'What is your favorite color?' * 10,
            'options': [f'Option {i}' for i in range(10)],
            'user_id': 'U123',
            'team_id': 'T123'
        }
        
        start_time = time.time()
        for _ in range(100):
            validation_context.validate(large_data)
        validation_time = time.time() - start_time
        
        # 驗證應該在合理時間內完成
        assert validation_time < 5.0  # 100次驗證應該在5秒內完成
        
        # 測試大量數據導出
        large_export_data = {
            'polls_data': [
                {
                    'id': i,
                    'question': f'Poll {i}?',
                    'options': [{'text': f'Option {j}', 'vote_count': j} for j in range(5)]
                }
                for i in range(100)
            ]
        }
        
        start_time = time.time()
        result = export_context.export(large_export_data, 'json')
        export_time = time.time() - start_time
        
        # 導出應該在合理時間內完成
        assert export_time < 10.0  # 100個投票的導出應該在10秒內完成
        assert len(result) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
