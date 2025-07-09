# 🗳️ Agora - Enterprise Anonymous Voting for Slack

> **🌐 Language**: [English](README.md) | [繁體中文](README.zh-TW.md) | [日本語](README.ja.md)

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com)
[![SOLID](https://img.shields.io/badge/Architecture-SOLID-yellow.svg)](./documentation/SOLID_ARCHITECTURE.md)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)

**Agora** is a production-ready, enterprise-grade Slack workspace application that provides comprehensive anonymous voting tools for team decision-making. Built with SOLID architecture principles, it offers advanced analytics, role management, scheduling automation, and a web management dashboard.

## 📚 Documentation

本專案文檔已完全模組化，請參閱以下專門文檔：

### 🎯 核心文檔
- **[Overview](docs/overview.md)** - 專案概述與核心功能
- **[Quick Start](docs/quick-start.md)** - 快速開始指南
- **[Installation](docs/installation.md)** - 詳細安裝指南
- **[Configuration](docs/configuration.md)** - 配置設定說明
- **[Usage Guide](docs/usage.md)** - 使用指南與範例

### 🏗️ 架構文檔
- **[SOLID Architecture](SOLID_ARCHITECTURE.md)** - 完整架構文檔
- **[Technology Stack](docs/architecture/tech-stack.md)** - 技術棧說明
- **[API Documentation](docs/api.md)** - RESTful API 參考

### 🔧 開發與部署
- **[Development Setup](docs/development/setup.md)** - 開發環境設置
- **[Docker Deployment](docs/deployment/docker.md)** - Docker 部署指南
- **[Production Deployment](DEPLOYMENT.md)** - 生產環境部署

### 🛡️ 安全與管理
- **[Security Guide](docs/security.md)** - 安全最佳實踐
- **[Admin Guide](docs/admin.md)** - 管理員指南
- **[Monitoring](docs/monitoring.md)** - 監控與日誌

### 🧪 測試與品質
- **[Testing Guide](TEST_SUMMARY.md)** - 測試指南
- **[Testing Guidelines](docs/testing/guidelines.md)** - 測試要求
- **[Performance Testing](docs/testing/performance.md)** - 效能測試

## ✨ Key Features

詳細功能說明請參閱 [Overview](docs/overview.md) 文檔。

### 🗳️ 核心投票功能
- **🔒 完全匿名**: 投票者身份與選擇完全分離
- **📊 多種投票類型**: 單選、多選、排名投票
- **⏰ 即時更新**: 投票結果即時更新
- **🛡️ 重複投票防護**: 可配置的防重複投票機制

### 📈 進階分析與洞察
- **📊 豐富數據視覺化**: 互動式圖表和圖形
- **📋 導出功能**: CSV、JSON、Excel 格式導出
- **🎯 參與分析**: 追蹤參與度和回應模式
- **📈 趨勢分析**: 歷史投票模式和洞察

### 🏗️ 企業級架構
- **🎯 SOLID 合規**: 8.8/10 架構得分 (提升 42%)
- **🔧 依賴注入**: 完整服務容器系統
- **📦 模組化設計**: 13 個服務接口與策略模式
- **🧪 全面測試**: 單元、集成、效能測試

## 🚀 Quick Start

完整快速開始指南請參閱 [Quick Start Guide](docs/quick-start.md)。

### 基本要求
- **Python 3.12+**
- **Docker & Docker Compose** (生產環境)
- **Slack App** 機器人權限
- **ngrok** (本地開發)

### 快速安裝
```bash
# 克隆儲存庫
git clone https://github.com/arthurinuspace/agora.git
cd agora

# 設置虛擬環境
python3 -m venv venv
source venv/bin/activate

# 安裝依賴
pip install -r requirements.txt

# 配置環境變數
cp .env.example .env
# 編輯 .env 填入 Slack 憑證

# 初始化資料庫
python database.py

# 啟動應用程式
python start_slack_app.py
```

詳細安裝指南請參閱：
- [Installation Guide](docs/installation.md) - 詳細安裝說明
- [Configuration Guide](docs/configuration.md) - 配置設定

## 📱 Slack 配置

完整配置指南請參閱 [Configuration Guide](docs/configuration.md)。

### 必要的機器人權限
```
commands          # 斜線命令
chat:write        # 發送消息
chat:write.public # 公開頻道發送
users:read        # 讀取用戶資訊
channels:read     # 讀取頻道資訊
```

### 斜線命令配置
- **命令**: `/agora`
- **請求 URL**: `https://your-domain.com/slack/events`
- **描述**: 創建和管理匿名投票

## 💡 使用範例

詳細使用指南請參閱 [Usage Guide](docs/usage.md)。

### 創建基本投票
```
/agora What should we have for lunch?
```

### 創建多選投票
```
/agora Which features should we prioritize? (multiple choice)
```

### 使用模態介面
1. 使用 `/agora` 加上任何問題
2. 打開模態視窗，可以：
   - 編輯投票問題
   - 添加多個選項（每行一個）
   - 選擇投票類型（單選/多選）
   - 設置排程選項
   - 配置匿名設定

## 🏗️ 架構概覽

完整架構說明請參閱 [SOLID Architecture](SOLID_ARCHITECTURE.md) 文檔。

### 技術棧
- **後端**: FastAPI (Python 3.12+)
- **資料庫**: SQLite (開發) / PostgreSQL (生產)
- **緩存**: Redis 用於會話和效能
- **前端**: HTML/CSS/JavaScript 響應式設計
- **部署**: Docker 容器配 Nginx 反向代理
- **測試**: pytest 全面測試套件

### SOLID 架構設計
```
agora/
├── services/              # 依賴注入服務層
│   ├── abstractions.py   # 13 個服務接口
│   ├── implementations.py # 具體實現
│   ├── container.py      # DI 容器
│   └── factory.py        # 服務工廠
├── strategies/            # 策略模式
│   ├── validation.py     # 5 種驗證策略
│   └── export.py         # 3 種導出策略
├── api/                  # 模組化 API 端點
│   ├── auth.py          # 身份驗證
│   ├── polls.py         # 投票操作
│   └── admin.py         # 管理控制台
└── database/             # 資料庫層
```

詳細架構說明請參閱：
- [Technology Stack](docs/architecture/tech-stack.md) - 技術棧詳解
- [SOLID Principles](docs/architecture/solid-principles.md) - SOLID 原則實現

## 🧪 開發

完整開發指南請參閱 [Development Setup](docs/development/setup.md)。

### 執行測試
```bash
# 激活虛擬環境
source venv/bin/activate

# 運行所有測試
python -m pytest -v

# 運行 SOLID 架構測試
python -m pytest test_solid_architecture.py -v

# 運行完整測試套件
python -m pytest test_enhanced_*.py test_integration_*.py -v
```

### 開發命令
```bash
# 啟動開發服務器
python -m uvicorn main:app --reload --port 8000

# 運行資料庫遷移
python database.py

# 健康檢查
curl http://localhost:8000/health
```

詳細開發指南請參閱：
- [Development Workflow](docs/development/workflow.md) - 開發流程
- [Code Standards](docs/development/standards.md) - 程式碼標準
- [Testing Guidelines](docs/testing/guidelines.md) - 測試指南

## 🐳 Docker 部署

完整部署指南請參閱 [Docker Deployment](docs/deployment/docker.md)。

### 開發環境
```bash
# 啟動所有服務
docker-compose up -d

# 查看日誌
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
- **agora**: 主應用程式服務器
- **postgres**: PostgreSQL 資料庫（生產）
- **redis**: Redis 緩存和會話
- **nginx**: 反向代理配 SSL（生產）

詳細部署指南請參閱：
- [Production Deployment](DEPLOYMENT.md) - 生產環境部署
- [Docker Deployment](docs/deployment/docker.md) - Docker 部署詳解

## 📊 監控與分析

完整監控指南請參閱 [Monitoring Guide](docs/monitoring.md)。

### 內建監控功能
- **健康檢查**: `/health` 端點提供服務狀態
- **指標**: `/metrics` 端點提供 Prometheus 兼容指標
- **效能**: 請求時間和資源使用情況
- **錯誤追蹤**: 全面的錯誤日誌和警報

### Web 控制台
訪問 `https://your-domain.com/admin` 管理控制台：
- 即時投票監控
- 用戶參與度分析
- 系統健康和效能指標
- 導出和報告工具

## 🤝 貢獻

歡迎貢獻！請查看我們的 [Contributing Guidelines](./CONTRIBUTING.md) 了解詳情。

### 開發設置
1. Fork 儲存庫
2. 創建功能分支: `git checkout -b feature/amazing-feature`
3. 遵循 SOLID 原則進行更改
4. 添加全面測試
5. 確保所有測試通過: `python -m pytest`
6. 提交 pull request

### 程式碼標準
- 遵循 PEP 8 樣式指南
- 維護 SOLID 架構原則
- 編寫全面測試 (>80% 覆蓋率)
- 記錄所有公共 API
- 使用類型提示

## 🔒 安全

完整安全指南請參閱 [Security Guide](docs/security.md)。

- **請求驗證**: 所有 Slack 請求都經過驗證
- **環境變數**: 所有敏感資料使用環境變數
- **SQL 注入保護**: SQLAlchemy ORM 與參數化查詢
- **速率限制**: API 端點內建速率限制
- **審計日誌**: 完整的行動審計跟踪

## 📄 文檔

### 主要文檔
- **[SOLID Architecture](./SOLID_ARCHITECTURE.md)**: 詳細架構文檔
- **[Deployment Guide](./DEPLOYMENT.md)**: 完整部署指南
- **[Testing Guide](./TEST_SUMMARY.md)**: 全面測試文檔
- **[Contributing](./CONTRIBUTING.md)**: 貢獻者指南

### 完整文檔系統
請參閱本 README 頂部的 [📚 Documentation](#-documentation) 部分，包含所有模組化文檔的連結。

## 📝 License

本專案採用 MIT License - 請查看 [LICENSE](./LICENSE) 文件了解詳情。

## 🎯 支援與社群

- **Issues**: [GitHub Issues](https://github.com/arthurinuspace/agora/issues)
- **Discussions**: [GitHub Discussions](https://github.com/arthurinuspace/agora/discussions)
- **Documentation**: [Wiki](https://github.com/arthurinuspace/agora/wiki)

## 🏆 致謝

- 使用 [FastAPI](https://fastapi.tiangolo.com/) 和 [Slack Bolt](https://slack.dev/bolt-python/) 構建
- 受民主決策原則啟發
- 架構遵循 SOLID 原則以確保可維護性和可擴展性

---

**Made with ❤️ for better team collaboration**

*Agora - Where every voice matters, anonymously.*