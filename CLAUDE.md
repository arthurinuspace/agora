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

### 📊 Architecture Metrics (Current Status - 2025-07)
- **SOLID Compliance**: 8.8/10 (從6.2提升42%)
- **Service Abstractions**: 13個核心接口
- **Test Coverage**: 企業級測試套件，10個測試文件
- **API Modules**: 3個專門化模組 (auth, polls, admin)
- **Strategy Patterns**: 驗證(5種) + 導出(3種)
- **GitHub Repository**: https://github.com/arthurinuspace/agora
- **Code Quality**: 75個檔案，24,682行程式碼
- **Open Source Status**: ✅ 完全開源，MIT License
- **Project Structure**: 清晰的分層架構，包含7個主要目錄類別
- **Documentation**: 9個技術文檔文件，涵蓋架構、部署、測試

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

**🎯 記住**: 所有開發都應遵循SOLID原則，使用依賴注入，並包含完整的測試覆蓋。有問題時，首先檢查服務是否正確配置和依賴注入是否正常工作。

**🌟 Open Source**: 本專案已開源至 GitHub，歡迎社群貢獻！請參閱 CONTRIBUTING.md 了解貢獻指南。