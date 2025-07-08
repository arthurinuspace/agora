# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Agora is a **完整的企業級 Slack 工作區應用程式**，提供全方位的匿名投票工具，用於團隊決策制定。該專案已從 MVP 演進為功能完整的應用程式，具備進階分析、角色管理、通知系統、排程自動化、Web 管理控制面板和生產級部署能力。

**🎯 核心價值**：
- 🗳️ **完全匿名投票**：確保投票者身份與選擇完全分離
- 📊 **即時分析洞察**：提供豐富的投票數據和視覺化圖表
- 🎨 **現代化 UI/UX**：emoji 豐富的介面和響應式設計
- 🔐 **企業級安全**：多層安全架構和威脅檢測
- 🚀 **生產就緒**：Docker 容器化和自動化部署
- 🏗️ **SOLID 架構**：完全符合 SOLID 原則的企業級架構設計

## 🏆 Recent Major Updates (2025-01)

### SOLID 架構重構完成
- ✅ **依賴注入容器**: 完整的服務容器和工廠模式實現
- ✅ **服務抽象層**: 13個核心服務接口，支援完全解耦
- ✅ **策略模式**: 可擴展的驗證和導出策略系統
- ✅ **模組分離**: API按業務領域分離為3個專門模組
- ✅ **測試覆蓋**: 企業級測試套件，涵蓋功能、錯誤處理、效能測試
- ✅ **SOLID合規**: 從6.2/10提升至8.8/10 (42%改善)

### 🌟 Open Source 發布 (2025-01)
- ✅ **GitHub 儲存庫**: https://github.com/arthurinuspace/agora
- ✅ **完整文檔**: README、CONTRIBUTING、DEPLOYMENT、LICENSE
- ✅ **安全檢查**: 無機密資料洩露，完整 .gitignore 配置
- ✅ **CI/CD 配置**: GitHub Actions 工作流程已配置
- ✅ **程式碼品質**: 75個檔案，24,682行程式碼，企業級品質
- ✅ **MIT License**: 開源友好的授權協議

## Architecture

### Core Technology Stack
- **Backend**: Python 3.12+ with FastAPI framework
- **Architecture**: SOLID-compliant enterprise architecture with dependency injection
- **Slack Integration**: Uses `slack_bolt` SDK for handling Slack API events
- **Database**: SQLite (development) / PostgreSQL (production)
- **Caching**: Redis for session management and performance
- **Reverse Proxy**: Nginx with SSL termination (production)
- **Deployment**: Docker containers with docker-compose orchestration
- **Testing**: pytest with comprehensive unit and integration tests

### SOLID Architecture Components

#### 🏗️ Service Layer (services/)
```
services/
├── abstractions.py      # 13 service interfaces (DatabaseService, CacheService, etc.)
├── implementations.py   # Concrete implementations (SQLAlchemy, Redis, Simple)
├── container.py        # Dependency injection container with override support
├── factory.py          # Service factory with environment-specific configurations
└── __init__.py         # Clean service exports
```

#### 🎯 Strategy Patterns (strategies/)
```
strategies/
├── validation.py       # 5 validation strategies (question, options, security, etc.)
├── export.py          # 3 export strategies (CSV, JSON, Excel)
└── __init__.py        # Strategy context managers
```

#### 🔗 API Modules (api/)
```
api/
├── auth.py            # Authentication & authorization endpoints
├── polls.py           # Poll CRUD operations & statistics
├── admin.py           # Admin dashboard & system management
└── __init__.py        # Router exports
```

#### 🗄️ Database Layer (database/)
```
database/
├── config.py          # Database configuration & health checks
└── __init__.py        # Database utilities export
```

#### 🏭 Application Factory
```
app_factory.py         # Environment-specific app creation with lifespan management
```

### Deployment Environments
- **Development**: Local FastAPI with ngrok for public HTTPS URL
- **Production**: Docker-based deployment with PostgreSQL, Redis, and Nginx

## Development Guidelines

### 🎯 Core Principles
- **SOLID Architecture**: 嚴格遵循 SOLID 原則，使用依賴注入和服務抽象
- **Strategy Pattern**: 新功能優先考慮策略模式，確保可擴展性
- **Testing First**: 新功能必須包含完整測試（單元、集成、錯誤處理）
- **Service Separation**: 按業務領域分離服務，避免跨域依賴

### Environment & Execution
- **Python Environment**: 
  - 因為本專案是 python 相關，請執行每一個 command 前，都要確保在 venv 下
  - `請用 venv 下的 python`
  - 使用 `source venv/bin/activate` 激活虛擬環境

### 🏗️ SOLID Architecture Guidelines

#### Service Development
```python
# ✅ 正確：使用依賴注入
from services import get_service, PollRepository

poll_repo = get_service(PollRepository)
polls = poll_repo.get_polls(team_id="T123")

# ❌ 錯誤：直接實例化具體類
from services.implementations import SQLAlchemyPollRepository
poll_repo = SQLAlchemyPollRepository(db_service)  # 違反DIP原則
```

#### API Development  
```python
# ✅ 正確：使用模組化路由
from api.polls import router as polls_router
from api.auth import get_current_user

@polls_router.get("/")
async def get_polls(current_user = Depends(get_current_user)):
    poll_repo = get_service(PollRepository)
    return poll_repo.get_polls(current_user['team_id'])
```

#### Strategy Pattern Usage
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

### 📋 Code Standards
- **Code Quality**: Follow PEP 8 style guidelines and maintain comprehensive documentation
- **Testing**: All new features must include unit tests with >80% coverage
- **Security**: Never commit sensitive data; use environment variables for all secrets
- **Type Hints**: 使用完整的類型提示，特別是服務接口

### 🧪 Testing Requirements

#### Test Categories (全部必須涵蓋)
1. **Unit Tests**: 測試個別函數和類別
2. **Integration Tests**: 測試服務間交互
3. **Error Handling Tests**: 測試各種錯誤場景
4. **Performance Tests**: 測試關鍵性能指標
5. **SOLID Compliance Tests**: 確保架構原則合規

#### Test Files Structure
```
test_enhanced_di.py         # 依賴注入進階測試
test_enhanced_api.py        # API模組完整測試  
test_enhanced_strategies.py # 策略模式擴展測試
test_integration_complete.py # 完整集成測試
test_error_handling.py      # 錯誤處理測試
test_performance.py         # 效能測試
```

### 🔄 Development Workflow

#### 新功能開發流程
1. **分析需求**: 確定功能屬於哪個服務層/API模組
2. **設計接口**: 如需新服務，先定義抽象接口
3. **實現策略**: 考慮是否需要策略模式支持擴展
4. **寫測試**: 編寫全面的測試用例
5. **實現功能**: 遵循SOLID原則實現
6. **集成測試**: 確保與現有系統整合正常
7. **性能驗證**: 確保符合性能要求

#### 重構指南
- 優先重構違反SOLID原則的代碼
- 使用依賴注入容器的override功能進行測試
- 策略模式優於繼承，組合優於繼承
- 保持接口穩定，變更實現

### 📊 Architecture Metrics (Current Status)
- **SOLID Compliance**: 8.8/10 (從6.2提升42%)
- **Service Abstractions**: 13個核心接口
- **Test Coverage**: 企業級測試套件
- **API Modules**: 3個專門化模組 (auth, polls, admin)
- **Strategy Patterns**: 驗證(5種) + 導出(3種)
- **GitHub Repository**: https://github.com/arthurinuspace/agora
- **Code Quality**: 75個檔案，24,682行程式碼
- **Open Source Status**: ✅ 完全開源，MIT License

## 🚀 Quick Start & Common Operations

### 📥 Clone & Setup (從 GitHub)
```bash
# Clone 儲存庫
git clone https://github.com/arthurinuspace/agora.git
cd agora

# 設置虛擬環境
python3 -m venv venv
source venv/bin/activate

# 安裝依賴
pip install -r requirements.txt

# 配置環境變數
cp .env.example .env
# 編輯 .env 文件，設置你的 Slack credentials
```

### 環境設置
```bash
# 激活虛擬環境
source venv/bin/activate

# 安裝依賴
pip install -r requirements.txt

# 驗證SOLID架構
python -c "from services import ServiceContainer, configure_services; container = ServiceContainer(); configure_services(container); print('✅ SOLID架構配置成功')"
```

### 測試執行
```bash
# 運行核心SOLID架構測試
python -m pytest test_solid_architecture.py::test_full_solid_architecture -v

# 運行完整測試套件
python -m pytest test_enhanced_*.py test_integration_*.py test_error_*.py test_performance.py -v

# 快速服務驗證
python -c "from services import get_service, DatabaseService; print(f'Database service: {type(get_service(DatabaseService)).__name__}')"
```

### 開發應用程式
```bash
# 啟動開發服務器
python -m uvicorn main:app --reload --port 8000

# 啟動測試應用程式
python -c "from app_factory import create_test_app; app = create_test_app(); print('✅ 測試應用程式創建成功')"
```

## 🔧 Troubleshooting & Common Issues

### 依賴注入問題
```python
# ❌ 常見錯誤：服務未找到
# ServiceNotFoundError: Service <class 'services.abstractions.DatabaseService'> not found

# ✅ 解決方案：確保服務已配置
from services import ServiceContainer, configure_services
container = ServiceContainer()
configure_services(container)  # 必須調用此函數
```

### 導入錯誤
```python
# ❌ 常見錯誤：ImportError: cannot import name 'configure_services'
# ✅ 解決方案：確保導入路徑正確
from services import configure_services  # 正確
from services.factory import configure_services  # 也正確
```

### 配置問題
```python
# ❌ 常見錯誤：AttributeError: type object 'Config' has no attribute 'REDIS_URL'
# ✅ 解決方案：檢查 config.py 中是否有所需配置
# config.py 應包含：
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./agora.db")
```

## 📁 Important Files Reference

### Core Architecture Files
- `services/abstractions.py:15` - DatabaseService interface
- `services/container.py:45` - ServiceContainer.get() method  
- `services/factory.py:298` - configure_services() function
- `app_factory.py:25` - create_test_app() function

### Key API Files
- `api/auth.py:41` - get_current_user dependency
- `api/polls.py:115` - create_poll endpoint
- `api/admin.py:38` - admin overview stats

### Strategy Pattern Files
- `strategies/validation.py:85` - ValidationContext class
- `strategies/export.py:95` - ExportContext class

### Test Files
- `test_solid_architecture.py:370` - Full SOLID architecture test
- `TEST_SUMMARY.md` - Complete testing documentation

## 🔗 References & Documentation

### 📚 本地文檔
- **SOLID Architecture Report**: `SOLID_ARCHITECTURE.md` - 完整重構文檔
- **Testing Summary**: `TEST_SUMMARY.md` - 測試套件總結
- **Performance Metrics**: `test_performance.py` - 效能基準測試
- **Deployment Guide**: `DEPLOYMENT.md` - 部署指南
- **Contributing Guide**: `CONTRIBUTING.md` - 貢獻指南

### 🌐 GitHub 資源
- **Main Repository**: https://github.com/arthurinuspace/agora
- **Issues & Bug Reports**: https://github.com/arthurinuspace/agora/issues
- **Discussions**: https://github.com/arthurinuspace/agora/discussions
- **Wiki**: https://github.com/arthurinuspace/agora/wiki
- **Releases**: https://github.com/arthurinuspace/agora/releases

### 🚀 開發與部署
```bash
# 本地開發
git clone https://github.com/arthurinuspace/agora.git
cd agora && source venv/bin/activate && pip install -r requirements.txt

# 創建功能分支
git checkout -b feature/your-feature-name

# 提交變更
git add . && git commit -m "feat: your feature description"
git push origin feature/your-feature-name

# 創建 Pull Request
# 在 GitHub 上創建 PR 到 main 分支
```

---

**🎯 記住**: 所有開發都應遵循SOLID原則，使用依賴注入，並包含完整的測試覆蓋。有問題時，首先檢查服務是否正確配置和依賴注入是否正常工作。

**🌟 Open Source**: 本專案已開源至 GitHub，歡迎社群貢獻！請參閱 CONTRIBUTING.md 了解貢獻指南。