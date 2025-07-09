# SOLID Architecture Guidelines

## 🎯 Core Principles

- **SOLID Architecture**: 嚴格遵循 SOLID 原則，使用依賴注入和服務抽象
- **Strategy Pattern**: 新功能優先考慮策略模式，確保可擴展性
- **Testing First**: 新功能必須包含完整測試（單元、集成、錯誤處理）
- **Service Separation**: 按業務領域分離服務，避免跨域依賴

## 🏗️ Service Layer (services/)

```
services/
├── abstractions.py      # 13 service interfaces (DatabaseService, CacheService, etc.)
├── implementations.py   # Concrete implementations (SQLAlchemy, Redis, Simple)
├── container.py        # Dependency injection container with override support
├── factory.py          # Service factory with environment-specific configurations
└── __init__.py         # Clean service exports
```

## 🎯 Strategy Patterns (strategies/)

```
strategies/
├── validation.py       # 5 validation strategies (question, options, security, etc.)
├── export.py          # 3 export strategies (CSV, JSON, Excel)
└── __init__.py        # Strategy context managers
```

## 🔗 API Modules (api/)

```
api/
├── auth.py            # Authentication & authorization endpoints
├── polls.py           # Poll CRUD operations & statistics
├── admin.py           # Admin dashboard & system management
└── __init__.py        # Router exports
```

## 🏗️ SOLID Architecture Guidelines

### Service Development

```python
# ✅ 正確：使用依賴注入
from services import get_service, PollRepository

poll_repo = get_service(PollRepository)
polls = poll_repo.get_polls(team_id="T123")

# ❌ 錯誤：直接實例化具體類
from services.implementations import SQLAlchemyPollRepository
poll_repo = SQLAlchemyPollRepository(db_service)  # 違反DIP原則
```

### API Development

```python
# ✅ 正確：使用模組化路由
from api.polls import router as polls_router
from api.auth import get_current_user

@polls_router.get("/")
async def get_polls(current_user = Depends(get_current_user)):
    poll_repo = get_service(PollRepository)
    return poll_repo.get_polls(current_user['team_id'])
```

### Strategy Pattern Usage

```python
# ✅ 新增驗證策略
from strategies.validation import ValidationStrategy, ValidationContext

class CustomValidationStrategy(ValidationStrategy):
    def validate(self, data: Dict[str, Any]) -> List[ValidationResult]:
        # 實現自定義驗證邏輯
        pass

# 註冊策略
validation_context = ValidationContext()
validation_context.add_strategy(CustomValidationStrategy())
```

## 📊 Architecture Metrics (Current Status - 2025-07)

- **SOLID Compliance**: 8.8/10 (從6.2提升42%)
- **Service Abstractions**: 13個核心接口
- **API Modules**: 3個專門化模組 (auth, polls, admin)
- **Strategy Patterns**: 驗證(5種) + 導出(3種)

## Core Architecture Files

- [`services/abstractions.py:15`](../../services/abstractions.py) - DatabaseService interface
- [`services/container.py:45`](../../services/container.py) - ServiceContainer.get() method
- [`services/factory.py:298`](../../services/factory.py) - configure_services() function
- [`app_factory.py:25`](../../app_factory.py) - create_test_app() function

## Strategy Pattern Files

- [`strategies/validation.py:85`](../../strategies/validation.py) - ValidationContext class
- [`strategies/export.py:95`](../../strategies/export.py) - ExportContext class

## See Also

- [Development Workflow](../development/workflow.md)
- [Testing Guidelines](../testing/guidelines.md)
- [Deployment Guide](../deployment/production.md)