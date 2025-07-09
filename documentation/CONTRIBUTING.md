# 🤝 Contributing to Agora

We love your input! We want to make contributing to Agora as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## 🚀 Development Process

We use GitHub to host code, to track issues and feature requests, as well as accept pull requests.

### 1. Fork the Repository

1. Fork the repo on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/arthurinuspace/agora.git
   cd agora
   ```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-cov black flake8 mypy

# Set up pre-commit hooks (optional but recommended)
pip install pre-commit
pre-commit install
```

### 3. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

## 🏗️ Architecture Guidelines

### SOLID Principles

Agora follows SOLID architecture principles. When contributing:

1. **Single Responsibility**: Each class/function should have one reason to change
2. **Open/Closed**: Open for extension, closed for modification
3. **Liskov Substitution**: Derived classes must be substitutable for base classes
4. **Interface Segregation**: Clients shouldn't depend on interfaces they don't use
5. **Dependency Inversion**: Depend on abstractions, not concretions

### Service Layer Pattern

```python
# ✅ Correct: Use dependency injection
from services import get_service, PollRepository

poll_repo = get_service(PollRepository)
polls = poll_repo.get_polls(team_id="T123")

# ❌ Incorrect: Direct instantiation
from services.implementations import SQLAlchemyPollRepository
poll_repo = SQLAlchemyPollRepository(db_service)
```

### Strategy Pattern Usage

When adding new validation or export functionality:

```python
# Add new validation strategy
from strategies.validation import ValidationStrategy

class CustomValidationStrategy(ValidationStrategy):
    def validate(self, data: Dict[str, Any]) -> List[ValidationResult]:
        # Implementation here
        pass

# Register in validation context
```

## 🧪 Testing Requirements

### Test Categories (All Required)

1. **Unit Tests**: Test individual functions and classes
2. **Integration Tests**: Test service interactions
3. **Error Handling Tests**: Test various error scenarios
4. **Performance Tests**: Test critical performance metrics
5. **SOLID Compliance Tests**: Ensure architectural principles

### Running Tests

```bash
# Run all tests
python -m pytest -v

# Run specific test categories
python -m pytest test_enhanced_*.py -v
python -m pytest test_integration_*.py -v

# Run with coverage (minimum 80% required)
python -m pytest --cov=. --cov-report=html --cov-fail-under=80

# Run SOLID architecture validation
python -c "
from services import ServiceContainer, configure_services
container = ServiceContainer()
configure_services(container)
print('✅ SOLID architecture validated')
"
```

### Writing Tests

Every new feature must include:

```python
# Unit tests for the feature
def test_feature_functionality():
    # Test normal operation
    pass

def test_feature_error_handling():
    # Test error scenarios
    pass

def test_feature_edge_cases():
    # Test boundary conditions
    pass

# Integration tests
def test_feature_integration():
    # Test with other services
    pass
```

## 💻 Code Style

### Python Style Guide

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use type hints for all function signatures
- Maximum line length: 88 characters (Black default)
- Use meaningful variable and function names

### Code Formatting

```bash
# Format code with Black
black .

# Check style with flake8
flake8 .

# Type checking with mypy
mypy .
```

### Example Code Style

```python
from typing import List, Optional, Dict, Any
from datetime import datetime

def create_poll(
    question: str,
    options: List[str],
    team_id: str,
    user_id: str,
    is_multiple_choice: bool = False,
    expires_at: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Create a new poll with the specified parameters.
    
    Args:
        question: The poll question
        options: List of poll options
        team_id: Slack team ID
        user_id: User creating the poll
        is_multiple_choice: Whether multiple selections are allowed
        expires_at: Optional expiration time
        
    Returns:
        Dictionary containing poll data
        
    Raises:
        ValidationError: If question or options are invalid
    """
    # Implementation here
    pass
```

## 📝 Commit Guidelines

### Commit Message Format

```
type(scope): brief description

Detailed explanation of the change (if needed)

- List of changes
- Breaking changes noted

Closes #123
```

### Commit Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples

```bash
feat(polls): add scheduled poll functionality

- Add start_time and end_time fields to Poll model
- Implement scheduler service for automatic poll management
- Add validation for time-based constraints

Closes #45

fix(auth): resolve token validation edge case

- Handle expired tokens gracefully
- Add proper error messaging for authentication failures
- Update tests for new error scenarios

Closes #67
```

## 🔄 Pull Request Process

### Before Submitting

1. **Update Documentation**: Update README, docstrings, and comments
2. **Add Tests**: Ensure your changes are covered by tests
3. **Run Test Suite**: All tests must pass
4. **Code Quality**: Run linting and type checking
5. **SOLID Compliance**: Verify architectural principles are maintained

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix (non-breaking change)
- [ ] New feature (non-breaking change)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] All tests pass
- [ ] Test coverage maintained (>80%)

## SOLID Compliance
- [ ] Single Responsibility Principle maintained
- [ ] Open/Closed Principle followed
- [ ] Liskov Substitution Principle respected
- [ ] Interface Segregation applied
- [ ] Dependency Inversion implemented

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added and passing
- [ ] No breaking changes (or properly documented)
```

## 🐛 Reporting Bugs

### Bug Report Template

**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected behavior**
A clear and concise description of what you expected to happen.

**Screenshots**
If applicable, add screenshots to help explain your problem.

**Environment:**
- OS: [e.g. macOS, Ubuntu]
- Python Version: [e.g. 3.12.1]
- Agora Version: [e.g. 1.2.3]
- Slack Workspace: [e.g. Enterprise, Free]

**Additional context**
Add any other context about the problem here.

## 💡 Feature Requests

### Feature Request Template

**Is your feature request related to a problem? Please describe.**
A clear and concise description of what the problem is.

**Describe the solution you'd like**
A clear and concise description of what you want to happen.

**Describe alternatives you've considered**
A clear and concise description of any alternative solutions or features you've considered.

**Additional context**
Add any other context or screenshots about the feature request here.

**SOLID Design Considerations**
How would this feature fit into the current SOLID architecture?

## 🏷️ Issue Labels

- `bug`: Something isn't working
- `enhancement`: New feature or request
- `documentation`: Documentation improvements
- `good first issue`: Good for newcomers
- `help wanted`: Extra attention is needed
- `question`: Further information is requested
- `architecture`: Related to SOLID architecture
- `testing`: Related to testing improvements

## 🎯 Development Focus Areas

We're especially interested in contributions in these areas:

1. **SOLID Architecture Improvements**: Further enhancing architectural compliance
2. **Performance Optimization**: Improving response times and resource usage
3. **Security Enhancements**: Additional security measures and audit logging
4. **Analytics Features**: Enhanced data visualization and reporting
5. **Testing Coverage**: Expanding test coverage and adding edge cases
6. **Documentation**: Improving developer and user documentation

## 📖 Resources

- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Slack Bolt Framework](https://slack.dev/bolt-python/)
- [pytest Documentation](https://docs.pytest.org/)
- [PEP 8 Style Guide](https://www.python.org/dev/peps/pep-0008/)

## 🤔 Questions?

Feel free to ask questions by:
- Opening a [GitHub Discussion](https://github.com/arthurinuspace/agora/discussions)
- Creating an issue with the `question` label
- Reaching out to maintainers

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to Agora! 🎉**

*Together, we make team decision-making better.*