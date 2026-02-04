"""
Data validation rules and pipeline.
Validates incoming data against configurable rules.
"""
from datetime import datetime, date
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import re
from loguru import logger


class ValidationLevel(str, Enum):
    """Validation severity levels."""
    ERROR = "error"      # Blocks the operation
    WARNING = "warning"  # Logs but allows operation
    INFO = "info"        # Informational only


@dataclass
class ValidationResult:
    """Result of a validation check."""
    valid: bool
    level: ValidationLevel
    field: str
    message: str
    rule_name: str
    value: Any = None


@dataclass
class ValidationRule:
    """A single validation rule."""
    name: str
    field: str
    check: Callable[[Any, Dict[str, Any]], bool]
    message: str
    level: ValidationLevel = ValidationLevel.ERROR
    enabled: bool = True


class DataValidator:
    """Validates data against configurable rules."""

    def __init__(self):
        self._rules: List[ValidationRule] = []
        self._setup_default_rules()

    def _setup_default_rules(self):
        """Setup default validation rules for data records."""

        # Type validation
        self.add_rule(
            name="type_required",
            field="type",
            check=lambda v, d: v is not None and len(str(v).strip()) > 0,
            message="Type is required",
            level=ValidationLevel.ERROR
        )

        self.add_rule(
            name="type_valid_format",
            field="type",
            check=lambda v, d: v is None or re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*$', str(v)),
            message="Type must start with a letter and contain only alphanumeric characters, underscores, and hyphens",
            level=ValidationLevel.ERROR
        )

        self.add_rule(
            name="type_max_length",
            field="type",
            check=lambda v, d: v is None or len(str(v)) <= 50,
            message="Type must not exceed 50 characters",
            level=ValidationLevel.ERROR
        )

        # Symbol validation
        self.add_rule(
            name="symbol_required",
            field="symbol",
            check=lambda v, d: v is not None and len(str(v).strip()) > 0,
            message="Symbol is required",
            level=ValidationLevel.ERROR
        )

        self.add_rule(
            name="symbol_valid_format",
            field="symbol",
            check=lambda v, d: v is None or re.match(r'^[A-Z0-9._-]+$', str(v).upper()),
            message="Symbol must contain only uppercase letters, numbers, dots, underscores, and hyphens",
            level=ValidationLevel.WARNING
        )

        self.add_rule(
            name="symbol_max_length",
            field="symbol",
            check=lambda v, d: v is None or len(str(v)) <= 50,
            message="Symbol must not exceed 50 characters",
            level=ValidationLevel.ERROR
        )

        # Execute date validation
        self.add_rule(
            name="execute_date_required",
            field="execute_date",
            check=lambda v, d: v is not None,
            message="Execute date is required",
            level=ValidationLevel.ERROR
        )

        self.add_rule(
            name="execute_date_not_future",
            field="execute_date",
            check=lambda v, d: v is None or (isinstance(v, date) and v <= date.today()),
            message="Execute date cannot be in the future",
            level=ValidationLevel.WARNING
        )

        self.add_rule(
            name="execute_date_reasonable",
            field="execute_date",
            check=lambda v, d: v is None or (isinstance(v, date) and v.year >= 2000),
            message="Execute date must be after year 2000",
            level=ValidationLevel.WARNING
        )

        # Strategy ID validation
        self.add_rule(
            name="strategy_id_required",
            field="strategy_id",
            check=lambda v, d: v is not None and len(str(v).strip()) > 0,
            message="Strategy ID is required",
            level=ValidationLevel.ERROR
        )

        self.add_rule(
            name="strategy_id_valid_format",
            field="strategy_id",
            check=lambda v, d: v is None or re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*$', str(v)),
            message="Strategy ID must start with a letter and contain only valid characters",
            level=ValidationLevel.ERROR
        )

        # Description validation
        self.add_rule(
            name="description_max_length",
            field="description",
            check=lambda v, d: v is None or len(str(v)) <= 1000,
            message="Description must not exceed 1000 characters",
            level=ValidationLevel.WARNING
        )

        # Payload validation
        self.add_rule(
            name="payload_max_size",
            field="payload",
            check=lambda v, d: v is None or len(str(v)) <= 65535,
            message="Payload is too large (max 64KB)",
            level=ValidationLevel.ERROR
        )

    def add_rule(
        self,
        name: str,
        field: str,
        check: Callable[[Any, Dict[str, Any]], bool],
        message: str,
        level: ValidationLevel = ValidationLevel.ERROR,
        enabled: bool = True
    ):
        """Add a validation rule."""
        rule = ValidationRule(
            name=name,
            field=field,
            check=check,
            message=message,
            level=level,
            enabled=enabled
        )
        self._rules.append(rule)

    def remove_rule(self, name: str):
        """Remove a validation rule by name."""
        self._rules = [r for r in self._rules if r.name != name]

    def enable_rule(self, name: str):
        """Enable a validation rule."""
        for rule in self._rules:
            if rule.name == name:
                rule.enabled = True
                break

    def disable_rule(self, name: str):
        """Disable a validation rule."""
        for rule in self._rules:
            if rule.name == name:
                rule.enabled = False
                break

    def validate(self, data: Dict[str, Any]) -> List[ValidationResult]:
        """
        Validate data against all rules.

        Returns a list of validation results (including failures).
        """
        results = []

        for rule in self._rules:
            if not rule.enabled:
                continue

            value = data.get(rule.field)

            try:
                is_valid = rule.check(value, data)

                if not is_valid:
                    results.append(ValidationResult(
                        valid=False,
                        level=rule.level,
                        field=rule.field,
                        message=rule.message,
                        rule_name=rule.name,
                        value=value
                    ))
            except Exception as e:
                logger.error(f"Validation rule {rule.name} failed with error: {e}")
                results.append(ValidationResult(
                    valid=False,
                    level=ValidationLevel.ERROR,
                    field=rule.field,
                    message=f"Validation error: {str(e)}",
                    rule_name=rule.name,
                    value=value
                ))

        return results

    def is_valid(self, data: Dict[str, Any]) -> bool:
        """Check if data passes all ERROR-level validations."""
        results = self.validate(data)
        return not any(r.level == ValidationLevel.ERROR and not r.valid for r in results)

    def get_errors(self, data: Dict[str, Any]) -> List[ValidationResult]:
        """Get only ERROR-level validation failures."""
        results = self.validate(data)
        return [r for r in results if r.level == ValidationLevel.ERROR]

    def get_warnings(self, data: Dict[str, Any]) -> List[ValidationResult]:
        """Get only WARNING-level validation failures."""
        results = self.validate(data)
        return [r for r in results if r.level == ValidationLevel.WARNING]


class StrategyValidator(DataValidator):
    """Validator specific to strategy data."""

    def __init__(self):
        super().__init__()
        self._rules = []  # Clear default rules
        self._setup_strategy_rules()

    def _setup_strategy_rules(self):
        """Setup validation rules for strategies."""
        self.add_rule(
            name="strategy_id_required",
            field="strategy_id",
            check=lambda v, d: v is not None and len(str(v).strip()) > 0,
            message="Strategy ID is required",
            level=ValidationLevel.ERROR
        )

        self.add_rule(
            name="strategy_id_format",
            field="strategy_id",
            check=lambda v, d: v is None or re.match(r'^[a-z][a-z0-9_]{2,49}$', str(v)),
            message="Strategy ID must be 3-50 lowercase letters, numbers, and underscores",
            level=ValidationLevel.ERROR
        )

        self.add_rule(
            name="name_required",
            field="name",
            check=lambda v, d: v is not None and len(str(v).strip()) > 0,
            message="Strategy name is required",
            level=ValidationLevel.ERROR
        )

        self.add_rule(
            name="name_length",
            field="name",
            check=lambda v, d: v is None or 2 <= len(str(v)) <= 200,
            message="Strategy name must be 2-200 characters",
            level=ValidationLevel.ERROR
        )


# Global validator instances
data_validator = DataValidator()
strategy_validator = StrategyValidator()
