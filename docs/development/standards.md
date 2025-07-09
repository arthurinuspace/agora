# Code Standards

## 📋 Code Standards

- **Code Quality**: Follow PEP 8 style guidelines and maintain comprehensive documentation
- **Testing**: All new features must include unit tests with >80% coverage
- **Security**: Never commit sensitive data; use environment variables for all secrets
- **Type Hints**: 使用完整的類型提示，特別是服務接口

## Key API Files

- [`api/auth.py:41`](../../api/auth.py) - get_current_user dependency
- [`api/polls.py:115`](../../api/polls.py) - create_poll endpoint
- [`api/admin.py:38`](../../api/admin.py) - admin overview stats

## See Also

- [Development Setup](setup.md)
- [Development Workflow](workflow.md)
- [SOLID Architecture](../architecture/solid-principles.md)