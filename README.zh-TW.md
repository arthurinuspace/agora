# 🗳️ Agora - 適用於 Slack 的企業級匿名投票系統

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com)
[![SOLID](https://img.shields.io/badge/Architecture-SOLID-yellow.svg)](./SOLID_ARCHITECTURE.md)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)

**Agora** 是一個生產就緒的企業級 Slack 工作空間應用程式，提供全面的匿名投票工具供團隊決策使用。採用 SOLID 架構原則建構，提供進階分析、角色管理、排程自動化和網頁管理控制台。

## 📚 文件說明

本專案文件已完全模組化，請參閱以下專門文件：

### 🎯 核心文件
- **[概覽](docs/overview.md)** - 專案概述與核心功能
- **[快速開始](docs/quick-start.md)** - 快速開始指南
- **[安裝說明](docs/installation.md)** - 詳細安裝指南
- **[組態設定](docs/configuration.md)** - 組態設定說明
- **[使用指南](docs/usage.md)** - 使用指南與範例

### 🏗️ 架構文件
- **[SOLID 架構](SOLID_ARCHITECTURE.md)** - 完整架構文件
- **[技術堆疊](docs/architecture/tech-stack.md)** - 技術堆疊說明
- **[API 文件](docs/api.md)** - RESTful API 參考

### 🔧 開發與部署
- **[開發環境設置](docs/development/setup.md)** - 開發環境設置
- **[Docker 部署](docs/deployment/docker.md)** - Docker 部署指南
- **[生產環境部署](DEPLOYMENT.md)** - 生產環境部署

### 🛡️ 安全性與管理
- **[安全性指南](docs/security.md)** - 安全性最佳實務
- **[管理員指南](docs/admin.md)** - 管理員指南
- **[監控](docs/monitoring.md)** - 監控與記錄

### 🧪 測試與品質
- **[測試指南](TEST_SUMMARY.md)** - 測試指南
- **[測試準則](docs/testing/guidelines.md)** - 測試要求
- **[效能測試](docs/testing/performance.md)** - 效能測試

## ✨ 主要功能

詳細功能說明請參閱 [概覽](docs/overview.md) 文件。

### 🗳️ 核心投票功能
- **🔒 完全匿名**: 投票者身份與選擇完全分離
- **📊 多種投票類型**: 單選、多選、排名投票
- **⏰ 即時更新**: 投票結果即時更新
- **🛡️ 重複投票防護**: 可組態的防重複投票機制

### 📈 進階分析與洞察
- **📊 豐富資料視覺化**: 互動式圖表和圖形
- **📋 匯出功能**: CSV、JSON、Excel 格式匯出
- **🎯 參與分析**: 追蹤參與度和回應模式
- **📈 趨勢分析**: 歷史投票模式和洞察

### 🏗️ 企業級架構
- **🎯 SOLID 合規**: 8.8/10 架構得分 (提升 42%)
- **🔧 相依性注入**: 完整服務容器系統
- **📦 模組化設計**: 13 個服務介面與策略模式
- **🧪 全面測試**: 單元、整合、效能測試

## 🚀 快速開始

完整快速開始指南請參閱 [快速開始指南](docs/quick-start.md)。

### 基本要求
- **Python 3.12+**
- **Docker & Docker Compose** (生產環境)
- **Slack App** 機器人權限
- **ngrok** (本地開發)

### 快速安裝
```bash
# 複製儲存庫
git clone https://github.com/arthurinuspace/agora.git
cd agora

# 設置虛擬環境
python3 -m venv venv
source venv/bin/activate

# 安裝相依性
pip install -r requirements.txt

# 組態環境變數
cp .env.example .env
# 編輯 .env 填入 Slack 憑證

# 初始化資料庫
python database.py

# 啟動應用程式
python start_slack_app.py
```

詳細安裝指南請參閱：
- [安裝指南](docs/installation.md) - 詳細安裝說明
- [組態指南](docs/configuration.md) - 組態設定

## 📱 Slack 組態

完整組態指南請參閱 [組態指南](docs/configuration.md)。

### 必要的機器人權限
```
commands          # 斜線命令
chat:write        # 傳送訊息
chat:write.public # 公開頻道傳送
users:read        # 讀取使用者資訊
channels:read     # 讀取頻道資訊
```

### 斜線命令組態
- **命令**: `/agora`
- **請求 URL**: `https://your-domain.com/slack/events`
- **描述**: 建立和管理匿名投票

## 💡 使用範例

詳細使用指南請參閱 [使用指南](docs/usage.md)。

### 建立基本投票
```
/agora 我們午餐要吃什麼？
```

### 建立多選投票
```
/agora 我們應該優先開發哪些功能？（多選）
```

### 使用模態介面
1. 使用 `/agora` 加上任何問題
2. 開啟模態視窗，可以：
   - 編輯投票問題
   - 新增多個選項（每行一個）
   - 選擇投票類型（單選/多選）
   - 設定排程選項
   - 組態匿名設定

## 🏗️ 架構概覽

完整架構說明請參閱 [SOLID 架構](SOLID_ARCHITECTURE.md) 文件。

### 技術堆疊
- **後端**: FastAPI (Python 3.12+)
- **資料庫**: SQLite (開發) / PostgreSQL (生產)
- **快取**: Redis 用於連線階段和效能
- **前端**: HTML/CSS/JavaScript 響應式設計
- **部署**: Docker 容器配 Nginx 反向代理
- **測試**: pytest 全面測試套件

### SOLID 架構設計
```
agora/
├── services/              # 相依性注入服務層
│   ├── abstractions.py   # 13 個服務介面
│   ├── implementations.py # 具體實作
│   ├── container.py      # DI 容器
│   └── factory.py        # 服務工廠
├── strategies/            # 策略模式
│   ├── validation.py     # 5 種驗證策略
│   └── export.py         # 3 種匯出策略
├── api/                  # 模組化 API 端點
│   ├── auth.py          # 身份驗證
│   ├── polls.py         # 投票操作
│   └── admin.py         # 管理控制台
└── database/             # 資料庫層
```

詳細架構說明請參閱：
- [技術堆疊](docs/architecture/tech-stack.md) - 技術堆疊詳解
- [SOLID 原則](docs/architecture/solid-principles.md) - SOLID 原則實作

## 🧪 開發

完整開發指南請參閱 [開發環境設置](docs/development/setup.md)。

### 執行測試
```bash
# 啟動虛擬環境
source venv/bin/activate

# 執行所有測試
python -m pytest -v

# 執行 SOLID 架構測試
python -m pytest test_solid_architecture.py -v

# 執行完整測試套件
python -m pytest test_enhanced_*.py test_integration_*.py -v
```

### 開發命令
```bash
# 啟動開發伺服器
python -m uvicorn main:app --reload --port 8000

# 執行資料庫遷移
python database.py

# 健康檢查
curl http://localhost:8000/health
```

詳細開發指南請參閱：
- [開發流程](docs/development/workflow.md) - 開發流程
- [程式碼標準](docs/development/standards.md) - 程式碼標準
- [測試準則](docs/testing/guidelines.md) - 測試指南

## 🐳 Docker 部署

完整部署指南請參閱 [Docker 部署](docs/deployment/docker.md)。

### 開發環境
```bash
# 啟動所有服務
docker-compose up -d

# 查看記錄
docker-compose logs -f agora
```

### 生產環境
```bash
# 生產部署配 SSL
docker-compose -f docker-compose.prod.yml up -d

# 擴展服務
docker-compose -f docker-compose.prod.yml up -d --scale agora=3
```

### Docker 服務
- **agora**: 主應用程式伺服器
- **postgres**: PostgreSQL 資料庫（生產）
- **redis**: Redis 快取和連線階段
- **nginx**: 反向代理配 SSL（生產）

詳細部署指南請參閱：
- [生產環境部署](DEPLOYMENT.md) - 生產環境部署
- [Docker 部署](docs/deployment/docker.md) - Docker 部署詳解

## 📊 監控與分析

完整監控指南請參閱 [監控指南](docs/monitoring.md)。

### 內建監控功能
- **健康檢查**: `/health` 端點提供服務狀態
- **指標**: `/metrics` 端點提供 Prometheus 相容指標
- **效能**: 請求時間和資源使用情況
- **錯誤追蹤**: 全面的錯誤記錄和警報

### 網頁控制台
造訪 `https://your-domain.com/admin` 管理控制台：
- 即時投票監控
- 使用者參與度分析
- 系統健康和效能指標
- 匯出和報告工具

## 🤝 貢獻

歡迎貢獻！請查看我們的 [貢獻準則](./CONTRIBUTING.md) 了解詳情。

### 開發設置
1. Fork 儲存庫
2. 建立功能分支: `git checkout -b feature/amazing-feature`
3. 遵循 SOLID 原則進行變更
4. 新增全面測試
5. 確保所有測試通過: `python -m pytest`
6. 提交 pull request

### 程式碼標準
- 遵循 PEP 8 樣式指南
- 維護 SOLID 架構原則
- 撰寫全面測試 (>80% 覆蓋率)
- 記錄所有公開 API
- 使用型別提示

## 🔒 安全性

完整安全性指南請參閱 [安全性指南](docs/security.md)。

- **請求驗證**: 所有 Slack 請求都經過驗證
- **環境變數**: 所有敏感資料使用環境變數
- **SQL 注入保護**: SQLAlchemy ORM 與參數化查詢
- **速率限制**: API 端點內建速率限制
- **稽核記錄**: 完整的動作稽核追蹤

## 📄 文件

### 主要文件
- **[SOLID 架構](./SOLID_ARCHITECTURE.md)**: 詳細架構文件
- **[部署指南](./DEPLOYMENT.md)**: 完整部署指南
- **[測試指南](./TEST_SUMMARY.md)**: 全面測試文件
- **[貢獻準則](./CONTRIBUTING.md)**: 貢獻者指南

### 完整文件系統
請參閱本 README 頂部的 [📚 文件說明](#-文件說明) 部分，包含所有模組化文件的連結。

## 📝 授權

本專案採用 MIT 授權條款 - 請查看 [LICENSE](./LICENSE) 檔案了解詳情。

## 🎯 支援與社群

- **問題回報**: [GitHub Issues](https://github.com/arthurinuspace/agora/issues)
- **討論**: [GitHub Discussions](https://github.com/arthurinuspace/agora/discussions)
- **文件**: [Wiki](https://github.com/arthurinuspace/agora/wiki)

## 🏆 致謝

- 使用 [FastAPI](https://fastapi.tiangolo.com/) 和 [Slack Bolt](https://slack.dev/bolt-python/) 建構
- 受民主決策原則啟發
- 架構遵循 SOLID 原則以確保可維護性和可擴展性

---

**Made with ❤️ for better team collaboration**

*Agora - 每個聲音都很重要，匿名進行。*