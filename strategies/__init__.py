"""
Strategies module implementing Strategy pattern for extensible functionality.
"""

from .validation import (
    ValidationStrategy, ValidationContext, ValidationResult, ValidationLevel,
    PollQuestionValidationStrategy, PollOptionsValidationStrategy,
    UserPermissionValidationStrategy, TeamSettingsValidationStrategy,
    SecurityValidationStrategy
)

from .export import (
    ExportStrategy, ExportContext,
    CSVExportStrategy, JSONExportStrategy, ExcelExportStrategy
)

__all__ = [
    # Validation
    'ValidationStrategy', 'ValidationContext', 'ValidationResult', 'ValidationLevel',
    'PollQuestionValidationStrategy', 'PollOptionsValidationStrategy',
    'UserPermissionValidationStrategy', 'TeamSettingsValidationStrategy',
    'SecurityValidationStrategy',
    
    # Export
    'ExportStrategy', 'ExportContext',
    'CSVExportStrategy', 'JSONExportStrategy', 'ExcelExportStrategy'
]