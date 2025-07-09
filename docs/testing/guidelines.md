# Testing Guidelines

## 🧪 Testing Requirements

### Test Categories (全部必須涵蓋)

1. **Unit Tests**: 測試個別函數和類別
2. **Integration Tests**: 測試服務間交互
3. **Error Handling Tests**: 測試各種錯誤場景
4. **Performance Tests**: 測試關鍵性能指標
5. **SOLID Compliance Tests**: 確保架構原則合規

### Test Files Structure

```
test_enhanced_di.py         # 依賴注入進階測試
test_enhanced_api.py        # API模組完整測試  
test_enhanced_strategies.py # 策略模式擴展測試
test_integration_complete.py # 完整集成測試
test_error_handling.py      # 錯誤處理測試
test_performance.py         # 效能測試
```

## 測試執行

```bash
# 運行核心SOLID架構測試
python -m pytest test_solid_architecture.py::test_full_solid_architecture -v

# 運行完整測試套件
python -m pytest test_enhanced_*.py test_integration_*.py test_error_*.py test_performance.py -v

# 快速服務驗證
python -c "from services import get_service, DatabaseService; print(f'Database service: {type(get_service(DatabaseService)).__name__}')"
```

### Test Coverage

- **Test Coverage**: 企業級測試套件，10個測試文件

### Test Files

- [`test_solid_architecture.py:370`](../../test_solid_architecture.py) - Full SOLID architecture test
- [`TEST_SUMMARY.md`](../../TEST_SUMMARY.md) - Complete testing documentation

## See Also

- [Development Setup](../development/setup.md)
- [SOLID Architecture](../architecture/solid-principles.md)
- [Performance Testing](performance.md)