"""Application-wide validation results and fail-closed health aggregation.

Business validation rules remain owned by their modules. This module only
standardizes results, runs registered checks, and summarizes system health.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field as dataclass_field
from datetime import UTC, datetime
from enum import StrEnum
import logging

from .error_codes import ErrorCode
from .observability import log_exception, redact_text


logger = logging.getLogger(__name__)


class ValidationSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    BLOCKING = "blocking"
    CRITICAL = "critical"


class ValidationStatus(StrEnum):
    PASS = "pass"
    WARNING = "warning"
    BLOCKED = "blocked"
    ERROR = "error"


class HealthStatus(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    BLOCKED = "blocked"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    error_code: ErrorCode
    severity: ValidationSeverity
    module: str
    operation: str
    message: str
    technical_detail: str | None = None
    field: str | None = None
    actual_value: str | None = None
    expected_condition: str | None = None
    suggested_action: str | None = None
    correlation_id: str | None = None
    timestamp_utc: datetime = dataclass_field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if not isinstance(self.error_code, ErrorCode):
            raise ValueError("validation issue must use centralized ErrorCode")
        if not isinstance(self.severity, ValidationSeverity):
            raise ValueError("validation issue must use ValidationSeverity")
        if self.timestamp_utc.tzinfo is None or self.timestamp_utc.utcoffset() is None:
            raise ValueError("validation timestamp must include a timezone")
        object.__setattr__(self, "timestamp_utc", self.timestamp_utc.astimezone(UTC))
        for name in ("module", "operation", "message"):
            value = getattr(self, name).strip()
            if not value:
                raise ValueError(f"{name} must not be empty")
            object.__setattr__(self, name, redact_text(value))
        for name in ("technical_detail", "field", "actual_value", "expected_condition", "suggested_action", "correlation_id"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, redact_text(value))


@dataclass(frozen=True, slots=True)
class InvariantViolation:
    invariant: str
    issue: ValidationIssue


@dataclass(frozen=True, slots=True)
class ValidationResult:
    validator_name: str
    module: str
    status: ValidationStatus
    issues: tuple[ValidationIssue, ...] = ()
    checked_at_utc: datetime = dataclass_field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if not self.validator_name.strip() or not self.module.strip():
            raise ValueError("validator identity must not be empty")
        if self.checked_at_utc.tzinfo is None or self.checked_at_utc.utcoffset() is None:
            raise ValueError("validation checked_at must include a timezone")
        object.__setattr__(self, "checked_at_utc", self.checked_at_utc.astimezone(UTC))
        expected = _validation_status(self.issues)
        if self.status is not expected:
            raise ValueError(f"validation status must be {expected.value} for its issues")

    @classmethod
    def from_issues(
        cls,
        validator_name: str,
        module: str,
        issues: tuple[ValidationIssue, ...] = (),
    ) -> "ValidationResult":
        return cls(validator_name, module, _validation_status(issues), issues)


@dataclass(frozen=True, slots=True)
class HealthCheckResult:
    status: HealthStatus
    validation_results: tuple[ValidationResult, ...]
    checked_at_utc: datetime = dataclass_field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if not isinstance(self.status, HealthStatus):
            raise ValueError("health result must use HealthStatus")
        if self.checked_at_utc.tzinfo is None or self.checked_at_utc.utcoffset() is None:
            raise ValueError("health checked_at must include a timezone")
        object.__setattr__(self, "checked_at_utc", self.checked_at_utc.astimezone(UTC))

    @property
    def allows_automatic_execution(self) -> bool:
        return self.status in {HealthStatus.HEALTHY, HealthStatus.DEGRADED}


Validator = Callable[[], ValidationResult]


class ValidationRegistry:
    """Small validator registry; validator exceptions become CRITICAL results."""

    def __init__(self) -> None:
        self._validators: dict[str, tuple[str, Validator]] = {}

    def register(self, name: str, module: str, validator: Validator) -> None:
        normalized = name.strip()
        if not normalized or not module.strip():
            raise ValueError("validator name and module must not be empty")
        if normalized in self._validators:
            raise ValueError(f"validator already registered: {normalized}")
        self._validators[normalized] = (module.strip(), validator)

    def run_all(self) -> HealthCheckResult:
        if not self._validators:
            return HealthCheckResult(HealthStatus.UNKNOWN, ())
        results: list[ValidationResult] = []
        for name, (module, validator) in self._validators.items():
            try:
                result = validator()
                if result.validator_name != name or result.module != module:
                    raise ValueError("validator returned mismatched identity")
            except Exception as exc:
                log_exception(
                    logger,
                    exc,
                    message="Registered validation check failed closed",
                    error_code=ErrorCode.INTEGRITY_VALIDATION,
                    context={"operation": "validation", "validator": name, "validation_module": module},
                )
                issue = ValidationIssue(
                    ErrorCode.INTEGRITY_VALIDATION,
                    ValidationSeverity.CRITICAL,
                    module,
                    "validation",
                    "Validation check failed; the affected operation is blocked.",
                    technical_detail=type(exc).__name__,
                    suggested_action="Inspect the technical error log before retrying.",
                )
                result = ValidationResult.from_issues(name, module, (issue,))
            results.append(result)
        return HealthCheckResult(_health_status(tuple(results)), tuple(results))


def _validation_status(issues: tuple[ValidationIssue, ...]) -> ValidationStatus:
    severities = {issue.severity for issue in issues}
    if ValidationSeverity.CRITICAL in severities:
        return ValidationStatus.ERROR
    if ValidationSeverity.BLOCKING in severities:
        return ValidationStatus.BLOCKED
    if ValidationSeverity.WARNING in severities:
        return ValidationStatus.WARNING
    return ValidationStatus.PASS


def _health_status(results: tuple[ValidationResult, ...]) -> HealthStatus:
    statuses = {result.status for result in results}
    if ValidationStatus.ERROR in statuses:
        return HealthStatus.CRITICAL
    if ValidationStatus.BLOCKED in statuses:
        return HealthStatus.BLOCKED
    if ValidationStatus.WARNING in statuses:
        return HealthStatus.DEGRADED
    return HealthStatus.HEALTHY
