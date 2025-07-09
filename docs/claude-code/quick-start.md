# Quick Start & Common Operations

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

## See Also

- [Development Setup](../development/setup.md)
- [Development Workflow](../development/workflow.md)
- [Testing Guidelines](../testing/guidelines.md)