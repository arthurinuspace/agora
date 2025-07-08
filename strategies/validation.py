"""
Validation strategies implementing Strategy pattern.
Allows for extensible validation logic following Open/Closed Principle.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import re
import logging

logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """Validation result levels."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationResult:
    """Validation result data structure."""
    level: ValidationLevel
    message: str
    field: str = ""
    code: str = ""


class ValidationStrategy(ABC):
    """Abstract base class for validation strategies."""
    
    @abstractmethod
    def validate(self, data: Dict[str, Any]) -> List[ValidationResult]:
        """Validate data and return list of results."""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get strategy name."""
        pass


class PollQuestionValidationStrategy(ValidationStrategy):
    """Strategy for validating poll questions."""
    
    def __init__(self, min_length: int = 5, max_length: int = 500):
        self.min_length = min_length
        self.max_length = max_length
    
    def validate(self, data: Dict[str, Any]) -> List[ValidationResult]:
        """Validate poll question."""
        results = []
        question = data.get('question', '')
        
        if not question:
            results.append(ValidationResult(
                level=ValidationLevel.ERROR,
                message="Question is required",
                field="question",
                code="QUESTION_REQUIRED"
            ))
            return results
        
        question = question.strip()
        
        # Length validation
        if len(question) < self.min_length:
            results.append(ValidationResult(
                level=ValidationLevel.ERROR,
                message=f"Question must be at least {self.min_length} characters long",
                field="question",
                code="QUESTION_TOO_SHORT"
            ))
        
        if len(question) > self.max_length:
            results.append(ValidationResult(
                level=ValidationLevel.ERROR,
                message=f"Question cannot exceed {self.max_length} characters",
                field="question",
                code="QUESTION_TOO_LONG"
            ))
        
        # Content validation
        if not question.endswith('?'):
            results.append(ValidationResult(
                level=ValidationLevel.WARNING,
                message="Questions typically end with a question mark",
                field="question",
                code="QUESTION_NO_MARK"
            ))
        
        # Profanity check (basic)
        profanity_words = ['spam', 'test123']  # In real app, use comprehensive list
        if any(word in question.lower() for word in profanity_words):
            results.append(ValidationResult(
                level=ValidationLevel.WARNING,
                message="Question may contain inappropriate content",
                field="question",
                code="QUESTION_PROFANITY"
            ))
        
        return results
    
    def get_name(self) -> str:
        return "poll_question_validation"


class PollOptionsValidationStrategy(ValidationStrategy):
    """Strategy for validating poll options."""
    
    def __init__(self, min_options: int = 2, max_options: int = 10, max_option_length: int = 100):
        self.min_options = min_options
        self.max_options = max_options
        self.max_option_length = max_option_length
    
    def validate(self, data: Dict[str, Any]) -> List[ValidationResult]:
        """Validate poll options."""
        results = []
        options = data.get('options', [])
        
        if not options:
            results.append(ValidationResult(
                level=ValidationLevel.ERROR,
                message="Poll options are required",
                field="options",
                code="OPTIONS_REQUIRED"
            ))
            return results
        
        # Count validation
        if len(options) < self.min_options:
            results.append(ValidationResult(
                level=ValidationLevel.ERROR,
                message=f"At least {self.min_options} options are required",
                field="options",
                code="OPTIONS_TOO_FEW"
            ))
        
        if len(options) > self.max_options:
            results.append(ValidationResult(
                level=ValidationLevel.ERROR,
                message=f"Cannot have more than {self.max_options} options",
                field="options",
                code="OPTIONS_TOO_MANY"
            ))
        
        # Individual option validation
        for i, option in enumerate(options):
            if not option or not option.strip():
                results.append(ValidationResult(
                    level=ValidationLevel.ERROR,
                    message=f"Option {i+1} cannot be empty",
                    field=f"options[{i}]",
                    code="OPTION_EMPTY"
                ))
            elif len(option.strip()) > self.max_option_length:
                results.append(ValidationResult(
                    level=ValidationLevel.ERROR,
                    message=f"Option {i+1} cannot exceed {self.max_option_length} characters",
                    field=f"options[{i}]",
                    code="OPTION_TOO_LONG"
                ))
        
        # Duplicate options check
        clean_options = [opt.strip().lower() for opt in options if opt and opt.strip()]
        if len(clean_options) != len(set(clean_options)):
            results.append(ValidationResult(
                level=ValidationLevel.WARNING,
                message="Some options appear to be duplicates",
                field="options",
                code="OPTIONS_DUPLICATE"
            ))
        
        return results
    
    def get_name(self) -> str:
        return "poll_options_validation"


class UserPermissionValidationStrategy(ValidationStrategy):
    """Strategy for validating user permissions."""
    
    def __init__(self, required_permissions: List[str] = None):
        self.required_permissions = required_permissions or []
    
    def validate(self, data: Dict[str, Any]) -> List[ValidationResult]:
        """Validate user permissions."""
        results = []
        user_id = data.get('user_id')
        team_id = data.get('team_id')
        action = data.get('action', 'create_poll')
        
        if not user_id:
            results.append(ValidationResult(
                level=ValidationLevel.ERROR,
                message="User ID is required",
                field="user_id",
                code="USER_ID_REQUIRED"
            ))
            return results
        
        if not team_id:
            results.append(ValidationResult(
                level=ValidationLevel.ERROR,
                message="Team ID is required",
                field="team_id",
                code="TEAM_ID_REQUIRED"
            ))
            return results
        
        # In a real implementation, check actual permissions
        # For now, simulate permission checking
        if action == 'create_poll':
            # Check daily limit (mock)
            daily_polls = data.get('daily_polls_created', 0)
            if daily_polls >= 5:
                results.append(ValidationResult(
                    level=ValidationLevel.ERROR,
                    message="Daily poll creation limit reached",
                    field="user_permissions",
                    code="DAILY_LIMIT_EXCEEDED"
                ))
        
        return results
    
    def get_name(self) -> str:
        return "user_permission_validation"


class TeamSettingsValidationStrategy(ValidationStrategy):
    """Strategy for validating team settings."""
    
    def validate(self, data: Dict[str, Any]) -> List[ValidationResult]:
        """Validate team settings."""
        results = []
        team_id = data.get('team_id')
        
        if not team_id:
            return results
        
        # Mock team settings validation
        # In real implementation, fetch actual team settings
        max_options = data.get('team_max_options', 10)
        options_count = len(data.get('options', []))
        
        if options_count > max_options:
            results.append(ValidationResult(
                level=ValidationLevel.ERROR,
                message=f"Team limit allows maximum {max_options} options per poll",
                field="options",
                code="TEAM_OPTIONS_LIMIT"
            ))
        
        # Check if team allows public polls
        is_public = data.get('is_public', False)
        team_allows_public = data.get('team_allows_public', True)
        
        if is_public and not team_allows_public:
            results.append(ValidationResult(
                level=ValidationLevel.ERROR,
                message="Team settings do not allow public polls",
                field="visibility",
                code="TEAM_PUBLIC_DISABLED"
            ))
        
        return results
    
    def get_name(self) -> str:
        return "team_settings_validation"


class SecurityValidationStrategy(ValidationStrategy):
    """Strategy for security validation."""
    
    def validate(self, data: Dict[str, Any]) -> List[ValidationResult]:
        """Validate security aspects."""
        results = []
        
        # Check for potential XSS in question
        question = data.get('question', '')
        if re.search(r'<script|javascript:|on\w+\s*=', question, re.IGNORECASE):
            results.append(ValidationResult(
                level=ValidationLevel.ERROR,
                message="Question contains potentially harmful content",
                field="question",
                code="SECURITY_XSS_RISK"
            ))
        
        # Check for potential XSS in options
        options = data.get('options', [])
        for i, option in enumerate(options):
            if re.search(r'<script|javascript:|on\w+\s*=', option, re.IGNORECASE):
                results.append(ValidationResult(
                    level=ValidationLevel.ERROR,
                    message=f"Option {i+1} contains potentially harmful content",
                    field=f"options[{i}]",
                    code="SECURITY_XSS_RISK"
                ))
        
        # Check for SQL injection patterns
        dangerous_patterns = ['DROP TABLE', 'DELETE FROM', 'INSERT INTO', 'UPDATE SET']
        for field_name, field_value in data.items():
            if isinstance(field_value, str):
                for pattern in dangerous_patterns:
                    if pattern in field_value.upper():
                        results.append(ValidationResult(
                            level=ValidationLevel.WARNING,
                            message=f"Field {field_name} contains suspicious SQL patterns",
                            field=field_name,
                            code="SECURITY_SQL_RISK"
                        ))
        
        return results
    
    def get_name(self) -> str:
        return "security_validation"


class ValidationContext:
    """Context class for managing validation strategies."""
    
    def __init__(self):
        self.strategies: Dict[str, ValidationStrategy] = {}
        self.default_strategies = [
            PollQuestionValidationStrategy(),
            PollOptionsValidationStrategy(),
            UserPermissionValidationStrategy(),
            TeamSettingsValidationStrategy(),
            SecurityValidationStrategy()
        ]
        
        # Register default strategies
        for strategy in self.default_strategies:
            self.add_strategy(strategy)
    
    def add_strategy(self, strategy: ValidationStrategy) -> None:
        """Add a validation strategy."""
        self.strategies[strategy.get_name()] = strategy
        logger.debug(f"Added validation strategy: {strategy.get_name()}")
    
    def remove_strategy(self, strategy_name: str) -> None:
        """Remove a validation strategy."""
        if strategy_name in self.strategies:
            del self.strategies[strategy_name]
            logger.debug(f"Removed validation strategy: {strategy_name}")
    
    def validate(self, data: Dict[str, Any], strategies: List[str] = None) -> List[ValidationResult]:
        """Run validation using specified strategies or all strategies."""
        results = []
        
        strategies_to_run = strategies or list(self.strategies.keys())
        
        for strategy_name in strategies_to_run:
            if strategy_name in self.strategies:
                try:
                    strategy_results = self.strategies[strategy_name].validate(data)
                    results.extend(strategy_results)
                    logger.debug(f"Validation strategy {strategy_name} returned {len(strategy_results)} results")
                except Exception as e:
                    logger.error(f"Error in validation strategy {strategy_name}: {e}")
                    results.append(ValidationResult(
                        level=ValidationLevel.ERROR,
                        message=f"Validation error in {strategy_name}",
                        code="VALIDATION_STRATEGY_ERROR"
                    ))
        
        return results
    
    def validate_by_level(self, data: Dict[str, Any], max_level: ValidationLevel = ValidationLevel.ERROR) -> Dict[str, Any]:
        """Run validation and filter by level."""
        all_results = self.validate(data)
        
        # Filter by level
        filtered_results = []
        for result in all_results:
            if result.level == ValidationLevel.ERROR and max_level in [ValidationLevel.ERROR]:
                filtered_results.append(result)
            elif result.level == ValidationLevel.WARNING and max_level in [ValidationLevel.ERROR, ValidationLevel.WARNING]:
                filtered_results.append(result)
            elif result.level == ValidationLevel.INFO:
                filtered_results.append(result)
        
        errors = [r for r in filtered_results if r.level == ValidationLevel.ERROR]
        warnings = [r for r in filtered_results if r.level == ValidationLevel.WARNING]
        infos = [r for r in filtered_results if r.level == ValidationLevel.INFO]
        
        return {
            'valid': len(errors) == 0,
            'errors': [{'message': r.message, 'field': r.field, 'code': r.code} for r in errors],
            'warnings': [{'message': r.message, 'field': r.field, 'code': r.code} for r in warnings],
            'infos': [{'message': r.message, 'field': r.field, 'code': r.code} for r in infos],
            'total_issues': len(filtered_results)
        }
    
    def get_strategy_names(self) -> List[str]:
        """Get list of registered strategy names."""
        return list(self.strategies.keys())
    
    def get_strategy(self, name: str) -> ValidationStrategy:
        """Get specific strategy by name."""
        return self.strategies.get(name)