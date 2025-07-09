# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 📚 Documentation Structure

本專案文檔已模組化，請參閱以下專門文檔：

### 🎯 核心文檔
- **[Project Overview](docs/claude-code/project-overview.md)** - 專案概述與核心價值
- **[Project Structure](docs/claude-code/project-structure.md)** - 完整專案結構與組織
- **[Quick Start](docs/claude-code/quick-start.md)** - 快速開始指南
- **[References](docs/claude-code/references.md)** - 參考資料與 GitHub 連結

### 🏗️ 架構文檔
- **[SOLID Architecture](docs/architecture/solid-principles.md)** - SOLID 原則實現指南
- **[Technology Stack](docs/architecture/tech-stack.md)** - 技術棧說明

### 🔧 開發文檔
- **[Development Setup](docs/development/setup.md)** - 開發環境設置
- **[Development Workflow](docs/development/workflow.md)** - 開發流程
- **[Code Standards](docs/development/standards.md)** - 程式碼標準

### 🧪 測試文檔
- **[Testing Guidelines](docs/testing/guidelines.md)** - 測試指南
- **[Performance Testing](docs/testing/performance.md)** - 效能測試

### 🚀 部署文檔
- **[Production Deployment](docs/deployment/production.md)** - 生產環境部署
- **[Docker Deployment](docs/deployment/docker.md)** - Docker 容器化部署

### 🛡️ 安全與管理文檔
- **[Security Guide](docs/security.md)** - 安全最佳實踐
- **[Admin Guide](docs/admin.md)** - 管理員指南
- **[Monitoring](docs/monitoring.md)** - 監控與日誌

### 📖 用戶文檔
- **[Overview](docs/overview.md)** - 專案概述與核心功能
- **[Installation](docs/installation.md)** - 詳細安裝指南
- **[Configuration](docs/configuration.md)** - 配置設定說明
- **[Usage Guide](docs/usage.md)** - 使用指南與範例
- **[API Documentation](docs/api.md)** - RESTful API 參考

## 🏆 Recent Major Updates (2025-07)

### 📚 文檔系統模組化完成 (2025-07-09)
- ✅ **完整文檔重構**: README.md 和 CLAUDE.md 模組化為 22 個專門文檔
- ✅ **清晰導航系統**: 5大類別文檔 (核心、架構、開發、測試、部署)
- ✅ **交叉引用系統**: 每個文檔都有完整的 "See Also" 交叉引用
- ✅ **中英文混合**: 本地化導航配合國際化技術內容
- ✅ **用戶體驗提升**: 從概述到詳細實現的漸進式學習路徑
- ✅ **維護友善**: 模組化結構便於更新和維護特定主題
- ✅ **多語言支援**: 新增 Traditional Chinese (zh-TW) 和 Japanese (ja) 版本 README

### 🏗️ SOLID 架構重構完成 (2025-01)
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
- ✅ **CI/CD 配置**: GitHub Actions 工作流程已配置 (目前暫時停用)
- ✅ **程式碼品質**: 75個檔案，24,682行程式碼，企業級品質
- ✅ **MIT License**: 開源友好的授權協議

## Architecture

詳細架構說明請參閱專門文檔：
- **[SOLID Architecture](docs/architecture/solid-principles.md)** - SOLID 原則實現詳解
- **[Technology Stack](docs/architecture/tech-stack.md)** - 完整技術棧說明

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

### 📊 Architecture Metrics (Current Status - 2025-07-09)
- **SOLID Compliance**: 8.8/10 (從6.2提升42%)
- **Service Abstractions**: 13個核心接口
- **Test Coverage**: 企業級測試套件，42個測試文件
- **API Modules**: 3個專門化模組 (auth, polls, admin)
- **Strategy Patterns**: 驗證(5種) + 導出(3種)
- **GitHub Repository**: https://github.com/arthurinuspace/agora
- **Code Quality**: 33個核心 Python 文件，17,691行程式碼
- **Documentation System**: 22個模組化文檔，完整交叉引用系統
- **Internationalization**: 3個語言版本 (EN, zh-TW, ja)
- **Open Source Status**: ✅ 完全開源，MIT License
- **Project Structure**: 清晰的分層架構，包含7個主要目錄類別
- **Documentation Coverage**: 完整涵蓋從安裝到部署的全生命週期
- **CI/CD Status**: 暫時停用 (檔案重命名為 .disabled)

### 詳細開發指南
詳細的開發指南請參閱：
- **[Development Setup](docs/development/setup.md)** - 開發環境設置與故障排除
- **[Development Workflow](docs/development/workflow.md)** - 完整開發流程
- **[Code Standards](docs/development/standards.md)** - 程式碼標準
- **[SOLID Architecture](docs/architecture/solid-principles.md)** - SOLID 原則實現詳解
- **[Testing Guidelines](docs/testing/guidelines.md)** - 測試要求與結構

## 🚀 Quick Start & Common Operations

快速開始指南請參閱：
- **[Quick Start](docs/claude-code/quick-start.md)** - 完整的快速開始指南
- **[Development Setup](docs/development/setup.md)** - 開發環境設置與故障排除

## 📁 Project Structure & Important Files

完整專案結構請參閱：
- **[Project Structure](docs/claude-code/project-structure.md)** - 完整專案結構與組織說明

## 🔗 References & Documentation

完整參考資料請參閱：
- **[References](docs/claude-code/references.md)** - 所有參考資料與 GitHub 連結

---

## 🎯 核心開發提醒

### SOLID 原則優先
- 所有開發都應遵循 SOLID 原則，使用依賴注入
- 新功能優先考慮策略模式，確保可擴展性
- 包含完整的測試覆蓋（單元、集成、錯誤處理）

### 故障排除
- 有問題時，首先檢查服務是否正確配置
- 確認依賴注入是否正常工作
- 參閱 [Development Setup](docs/development/setup.md) 進行故障排除

### 文檔維護
- 更新代碼時，同步更新相關文檔
- 新功能必須包含文檔說明
- 使用模組化文檔結構，更新對應專門文檔

**🌟 Open Source**: 本專案已開源至 GitHub，歡迎社群貢獻！請參閱 [CONTRIBUTING.md](CONTRIBUTING.md) 了解貢獻指南。

**📚 完整文檔系統**: 已建立 22 個模組化文檔，提供從概述到實現的完整指南。使用本文檔頂部的導航系統快速找到所需資訊。

## 🌐 國際化支援 (2025-07-09)

### 📖 多語言 README 版本
- **English**: [README.md](README.md) - 主要英文版本
- **繁體中文**: [README.zh-TW.md](README.zh-TW.md) - 傳統中文版本
- **日本語**: [README.ja.md](README.ja.md) - 日文版本

### 🔧 維護說明
- 所有版本保持內容同步，包括功能描述、安裝指南、使用範例
- 技術術語使用各語言標準專業詞彙
- 程式碼範例和命令保持完全一致
- 連結和 GitHub 參考保持統一

## ⚙️ 開發環境配置提醒

### CI/CD 狀態
- **GitHub Actions**: 目前暫時停用 (`.github/workflows/ci-cd.yml.disabled`)
- **重新啟用**: 將檔案重命名為 `ci-cd.yml` 即可恢復
- **配置**: 包含測試、代碼檢查、Docker 構建、部署流程

### 虛擬環境
- **啟動**: `source venv/bin/activate`
- **Python 版本**: 3.12+
- **依賴管理**: 使用 `requirements.txt`