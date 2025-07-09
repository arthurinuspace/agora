# Development Setup

## Environment & Execution

- **Python Environment**: 
  - 因為本專案是 python 相關，請執行每一個 command 前，都要確保在 venv 下
  - `請用 venv 下的 python`
  - 使用 `source venv/bin/activate` 激活虛擬環境

## 📥 Clone & Setup (從 GitHub)

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

## 環境設置

```bash
# 激活虛擬環境
source venv/bin/activate

# 安裝依賴
pip install -r requirements.txt

# 驗證SOLID架構
python -c "from services import ServiceContainer, configure_services; container = ServiceContainer(); configure_services(container); print('✅ SOLID架構配置成功')"
```

## 開發應用程式

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

## See Also

- [Development Workflow](workflow.md)
- [Code Standards](standards.md)
- [Testing Guidelines](../testing/guidelines.md)