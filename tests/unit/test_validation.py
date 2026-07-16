from datetime import UTC, datetime

from quant_trading.error_codes import ErrorCode
from quant_trading.validation import (
    HealthStatus,
    ValidationIssue,
    ValidationRegistry,
    ValidationResult,
    ValidationSeverity,
    ValidationStatus,
)


def issue(severity: ValidationSeverity) -> ValidationIssue:
    return ValidationIssue(
        ErrorCode.CONTRACT_VALIDATION,
        severity,
        "tests.module",
        "test_operation",
        "Input did not satisfy its contract.",
        actual_value="Authorization: Bearer secret-value",
        expected_condition="valid input",
        correlation_id="CORR-1",
        timestamp_utc=datetime(2026, 7, 15, tzinfo=UTC),
    )


def test_validation_result_derives_blocked_status_and_redacts_sensitive_actual_value():
    result = ValidationResult.from_issues("contract", "tests.module", (issue(ValidationSeverity.BLOCKING),))
    assert result.status is ValidationStatus.BLOCKED
    assert "secret-value" not in result.issues[0].actual_value


def test_health_becomes_blocked_and_disallows_automatic_execution():
    registry = ValidationRegistry()
    registry.register("contract", "tests.module", lambda: ValidationResult.from_issues("contract", "tests.module", (issue(ValidationSeverity.BLOCKING),)))
    health = registry.run_all()
    assert health.status is HealthStatus.BLOCKED
    assert not health.allows_automatic_execution


def test_validation_exception_fails_closed_instead_of_approving():
    registry = ValidationRegistry()

    def broken() -> ValidationResult:
        raise RuntimeError("validator failed")

    registry.register("broken", "tests.module", broken)
    health = registry.run_all()
    assert health.status is HealthStatus.CRITICAL
    assert health.validation_results[0].status is ValidationStatus.ERROR
    assert not health.allows_automatic_execution
    assert health.validation_results[0].issues[0].error_code is ErrorCode.INTEGRITY_VALIDATION


def test_no_completed_checks_is_unknown_and_blocks_automatic_execution():
    health = ValidationRegistry().run_all()
    assert health.status is HealthStatus.UNKNOWN
    assert not health.allows_automatic_execution


def test_financial_mismatch_is_reported_without_mutating_values():
    local, external = {"cash": "10.00"}, {"cash": "12.00"}
    result = ValidationResult.from_issues("reconciliation", "portfolio_accounting", (ValidationIssue(
        ErrorCode.CONTRACT_VALIDATION,
        ValidationSeverity.BLOCKING,
        "portfolio_accounting",
        "reconciliation",
        "Local and external cash differ; no correction was applied.",
        actual_value=local["cash"],
        expected_condition=external["cash"],
    ),))
    assert result.status is ValidationStatus.BLOCKED
    assert local == {"cash": "10.00"} and external == {"cash": "12.00"}
