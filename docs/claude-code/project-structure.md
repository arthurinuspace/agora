# Project Structure

## 📁 Project Structure & Important Files

### 📂 Complete Project Structure

```
agora/
├── 📚 Documentation Files
│   ├── README.md                              # 專案主要說明文件
│   ├── CLAUDE.md                              # Claude Code 工作指南
│   ├── CONTRIBUTING.md                        # 貢獻指南
│   ├── DEPLOYMENT.md                          # 部署指南
│   ├── LICENSE                                # MIT 開源授權
│   ├── SOLID_ARCHITECTURE.md                  # SOLID 架構文檔
│   ├── TEST_SUMMARY.md                        # 測試總結文檔
│   ├── SLACK_ERROR_HANDLING_SUMMARY.md        # Slack 錯誤處理文檔
│   └── Agora_MVP_Specification.markdown       # MVP 規格文件
│
├── 🔧 Configuration Files
│   ├── config.py                              # 主要配置文件
│   ├── config_validator.py                    # 配置驗證器
│   ├── pyproject.toml                         # Python 專案配置
│   ├── requirements.txt                       # Python 依賴包
│   ├── Dockerfile                             # Docker 容器配置
│   ├── docker-compose.yml                     # 開發環境 Docker 配置
│   ├── docker-compose.prod.yml                # 生產環境 Docker 配置
│   ├── nginx.conf                             # Nginx 反向代理配置
│   └── Makefile                               # 自動化命令
│
├── 🏗️ Core Architecture (SOLID)
│   ├── 🎯 Application Entry Points
│   │   ├── main.py                            # FastAPI 主應用入口
│   │   ├── app_factory.py                     # 應用工廠（環境特定）
│   │   ├── start_app.py                       # 應用啟動器
│   │   ├── start_slack_app.py                 # Slack 應用啟動器
│   │   ├── start_without_slack.py             # 無 Slack 模式啟動器
│   │   ├── run_agora.py                       # 生產環境運行器
│   │   └── run_agora_debug.py                 # 調試模式運行器
│   │
│   ├── 🏭 services/                           # 依賴注入服務層
│   │   ├── abstractions.py                   # 13 個服務接口定義
│   │   ├── container.py                      # 依賴注入容器
│   │   ├── factory.py                        # 服務工廠
│   │   ├── implementations.py                # 具體服務實現
│   │   └── __init__.py                       # 服務模組導出
│   │
│   ├── 🎯 strategies/                         # 策略模式
│   │   ├── validation.py                     # 5 種驗證策略
│   │   ├── export.py                         # 3 種導出策略
│   │   └── __init__.py                       # 策略模組導出
│   │
│   ├── 🔗 api/                               # API 模組 (按業務領域分離)
│   │   ├── auth.py                           # 認證與授權端點
│   │   ├── polls.py                          # 投票 CRUD 與統計
│   │   ├── admin.py                          # 管理控制面板
│   │   └── __init__.py                       # API 路由導出
│   │
│   └── 🗄️ database/                          # 資料庫層
│       ├── config.py                         # 資料庫配置與健康檢查
│       └── __init__.py                       # 資料庫工具導出
│
├── 🧩 Core Business Logic
│   ├── models.py                              # 資料模型定義
│   ├── database.py                            # 資料庫操作（待重構）
│   ├── slack_handlers.py                      # Slack 事件處理器
│   ├── api_middleware.py                      # API 中介軟體
│   ├── dashboard_api.py                       # 控制面板 API
│   ├── templates.py                           # 模板工具
│   ├── poll_management.py                     # 投票管理邏輯
│   ├── export_utils.py                        # 資料導出工具
│   ├── search_utils.py                        # 搜尋工具
│   ├── security.py                            # 安全功能
│   ├── monitoring.py                          # 監控功能
│   ├── performance.py                         # 效能監控
│   ├── migrations.py                          # 資料庫遷移
│   └── scheduler.py                           # 任務排程器
│
├── 🧪 Testing Files
│   ├── test_solid_architecture.py             # SOLID 架構測試
│   ├── test_enhanced_di.py                    # 依賴注入進階測試
│   ├── test_enhanced_api.py                   # API 模組完整測試
│   ├── test_enhanced_strategies.py            # 策略模式擴展測試
│   ├── test_integration_complete.py           # 完整集成測試
│   ├── test_error_handling.py                 # 錯誤處理測試
│   ├── test_performance.py                    # 效能測試
│   ├── test_agora.py                          # 基礎功能測試
│   ├── test_integration.py                    # 集成測試
│   └── test_new_features.py                   # 新功能測試
│
├── 📊 Static Assets & Templates
│   ├── static/
│   │   ├── css/                               # 樣式文件
│   │   │   ├── components.css                 # 組件樣式
│   │   │   └── dashboard.css                  # 控制面板樣式
│   │   ├── images/                            # 圖片資源
│   │   └── js/                                # 前端 JavaScript
│   │       ├── api.js                         # API 客戶端
│   │       ├── components.js                  # 前端組件
│   │       └── dashboard.js                   # 控制面板 JavaScript
│   │
│   └── templates/
│       └── admin_dashboard.html               # 管理控制面板模板
│
├── 🚀 Deployment & Environment
│   ├── deploy.sh                              # 部署腳本
│   └── venv/                                  # Python 虛擬環境
│
└── 📝 Runtime Files
    ├── agora.db                               # SQLite 資料庫
    ├── test_new_features.db                   # 測試資料庫
    ├── agora.log                              # 主要日誌
    ├── agora_debug.log                        # 調試日誌
    ├── agora_errors.log                       # 錯誤日誌
    └── agora_live.log                         # 實時日誌
```

## 🔧 建議的組織改進

1. **清理重複文件**: `database.py` 與 `database/config.py` 功能重疊，建議整合
2. **日誌文件管理**: 考慮將所有 `.log` 文件移至 `logs/` 目錄
3. **測試文件組織**: 可考慮創建 `tests/` 目錄，按功能模組分組
4. **配置文件集中**: 考慮創建 `config/` 目錄，集中管理配置文件

## See Also

- [Project Overview](project-overview.md)
- [Architecture Overview](../architecture/tech-stack.md)
- [Development Setup](../development/setup.md)