# Development Workflow

## 🔄 Development Workflow

### 新功能開發流程

1. **分析需求**: 確定功能屬於哪個服務層/API模組
2. **設計接口**: 如需新服務，先定義抽象接口
3. **實現策略**: 考慮是否需要策略模式支持擴展
4. **寫測試**: 編寫全面的測試用例
5. **實現功能**: 遵循SOLID原則實現
6. **集成測試**: 確保與現有系統整合正常
7. **性能驗證**: 確保符合性能要求

### 重構指南

- 優先重構違反SOLID原則的代碼
- 使用依賴注入容器的override功能進行測試
- 策略模式優於繼承，組合優於繼承
- 保持接口穩定，變更實現

## 🚀 開發與部署

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

## See Also

- [Code Standards](standards.md)
- [Testing Guidelines](../testing/guidelines.md)
- [SOLID Architecture](../architecture/solid-principles.md)