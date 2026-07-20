"""Immutable contracts for bounded, manual target-position research previews."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from uuid import UUID

from .errors import TargetPositionValidationError


TARGET_POSITION_CONTRACT_SCHEMA_VERSION = 1
ZERO = Decimal("0")
ONE = Decimal("1")


def utc(value: datetime, name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise TargetPositionValidationError(f"{name} must include a timezone")
    return value.astimezone(UTC)


def required_text(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TargetPositionValidationError(f"{name} must not be empty")
    return value.strip()


def optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def decimal_text(value: str, name: str) -> Decimal:
    if not isinstance(value, str) or not value.strip():
        raise TargetPositionValidationError(f"{name} must be a Decimal text value")
    try:
        parsed = Decimal(value.strip())
    except InvalidOperation as exc:
        raise TargetPositionValidationError(f"{name} must be valid Decimal text") from exc
    if not parsed.is_finite():
        raise TargetPositionValidationError(f"{name} must be finite")
    return parsed


def canonical_decimal(value: Decimal, name: str) -> Decimal:
    if not isinstance(value, Decimal) or not value.is_finite():
        raise TargetPositionValidationError(f"{name} must be a finite Decimal")
    return value


class TargetPositionDefinitionStatus(StrEnum):
    AVAILABLE = "available"
    ARCHIVED = "archived"


class TargetPositionDirection(StrEnum):
    NON_INCREASING = "non_increasing"
    NON_DECREASING = "non_decreasing"


class TargetPositionAdjustmentDirection(StrEnum):
    NONE = "none"
    INCREASE = "increase"
    DECREASE = "decrease"


class TargetPositionEvaluationMode(StrEnum):
    LOWER_ENDPOINT = "lower_endpoint"
    EXACT_KNOT = "exact_knot"
    INTERPOLATED = "interpolated"
    UPPER_ENDPOINT = "upper_endpoint"


class TargetPositionEvidenceKind(StrEnum):
    ALGORITHM_RUN = "algorithm_run"
    FACTOR_CALCULATION = "factor_calculation"


class TargetPositionOperationType(StrEnum):
    DEFINITION_SAVE = "definition_save"
    PREVIEW = "preview"


class TargetPositionOperationStatus(StrEnum):
    COMPLETED = "completed"
    INVALID_INPUT = "invalid_input"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class TargetPositionKnotInput:
    state_value: str
    target_fraction: str

    def __post_init__(self) -> None:
        if not isinstance(self.state_value, str) or not isinstance(self.target_fraction, str):
            raise TypeError("knot inputs must be strings")


@dataclass(frozen=True, slots=True)
class TargetPositionEvidenceBinding:
    evidence_kind: TargetPositionEvidenceKind
    evidence_id: str
    source_component: str | None = None
    source_version: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.evidence_kind, TargetPositionEvidenceKind):
            raise TargetPositionValidationError("evidence_kind must use TargetPositionEvidenceKind")
        object.__setattr__(self, "evidence_id", required_text(self.evidence_id, "evidence_id"))
        object.__setattr__(self, "source_component", optional_text(self.source_component))
        object.__setattr__(self, "source_version", optional_text(self.source_version))
        if self.source_version is not None and self.source_component is None:
            raise TargetPositionValidationError("source_version requires source_component")


@dataclass(frozen=True, slots=True)
class CreateTargetPositionDefinitionCommand:
    name: str
    reason: str
    direction: TargetPositionDirection
    minimum_fraction: str
    neutral_fraction: str
    maximum_fraction: str
    knots: tuple[TargetPositionKnotInput, ...]
    session_id: str
    request_id: str
    created_by: str
    predecessor_definition_id: UUID | None = None
    operation_id: UUID | None = None

    def __post_init__(self) -> None:
        for name in ("name", "reason", "minimum_fraction", "neutral_fraction", "maximum_fraction"):
            if not isinstance(getattr(self, name), str):
                raise TypeError(f"{name} must be a string")
        if not isinstance(self.direction, TargetPositionDirection):
            raise TypeError("direction must use TargetPositionDirection")
        for name in ("session_id", "request_id", "created_by"):
            object.__setattr__(self, name, required_text(getattr(self, name), name))


@dataclass(frozen=True, slots=True)
class PreviewTargetPositionCommand:
    definition_id: UUID
    research_state_value: str
    research_capital_basis_usd: str
    current_position_value_usd: str
    as_of_utc: datetime
    reason: str
    session_id: str
    request_id: str
    created_by: str
    evidence_bindings: tuple[TargetPositionEvidenceBinding, ...] = ()
    operation_id: UUID | None = None

    def __post_init__(self) -> None:
        for name in (
            "research_state_value",
            "research_capital_basis_usd",
            "current_position_value_usd",
            "reason",
        ):
            if not isinstance(getattr(self, name), str):
                raise TypeError(f"{name} must be a string")
        for name in ("session_id", "request_id", "created_by"):
            object.__setattr__(self, name, required_text(getattr(self, name), name))
        object.__setattr__(self, "as_of_utc", utc(self.as_of_utc, "as_of_utc"))


@dataclass(frozen=True, slots=True)
class TargetPositionKnot:
    ordinal: int
    state_value: Decimal
    target_fraction: Decimal

    def __post_init__(self) -> None:
        if self.ordinal < 0:
            raise TargetPositionValidationError("knot ordinal must not be negative")
        object.__setattr__(self, "state_value", canonical_decimal(self.state_value, "state_value"))
        fraction = canonical_decimal(self.target_fraction, "target_fraction")
        if not ZERO <= fraction <= ONE:
            raise TargetPositionValidationError("target_fraction must be within [0, 1]")
        object.__setattr__(self, "target_fraction", fraction)


@dataclass(frozen=True, slots=True)
class TargetPositionCurveDefinition:
    definition_id: UUID
    definition_version: int
    predecessor_definition_id: UUID | None
    name: str
    reason: str
    direction: TargetPositionDirection
    minimum_fraction: Decimal
    neutral_fraction: Decimal
    maximum_fraction: Decimal
    knots: tuple[TargetPositionKnot, ...]
    status: TargetPositionDefinitionStatus
    created_at_utc: datetime
    created_by: str
    schema_version: int = TARGET_POSITION_CONTRACT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.definition_version < 1:
            raise TargetPositionValidationError("definition_version must be positive")
        if self.predecessor_definition_id == self.definition_id:
            raise TargetPositionValidationError("a definition cannot be its own predecessor")
        if not isinstance(self.direction, TargetPositionDirection):
            raise TargetPositionValidationError("direction must use TargetPositionDirection")
        if not isinstance(self.status, TargetPositionDefinitionStatus):
            raise TargetPositionValidationError("status must use TargetPositionDefinitionStatus")
        if self.schema_version != TARGET_POSITION_CONTRACT_SCHEMA_VERSION:
            raise TargetPositionValidationError("unsupported target-position schema version")
        minimum = canonical_decimal(self.minimum_fraction, "minimum_fraction")
        neutral = canonical_decimal(self.neutral_fraction, "neutral_fraction")
        maximum = canonical_decimal(self.maximum_fraction, "maximum_fraction")
        if not ZERO <= minimum <= neutral <= maximum <= ONE:
            raise TargetPositionValidationError(
                "fractions must satisfy 0 <= minimum <= neutral <= maximum <= 1"
            )
        if len(self.knots) < 3:
            raise TargetPositionValidationError("a curve definition requires at least three knots")
        if tuple(item.ordinal for item in self.knots) != tuple(range(len(self.knots))):
            raise TargetPositionValidationError("knot ordinals must be contiguous from zero")
        states = tuple(item.state_value for item in self.knots)
        if any(left >= right for left, right in zip(states, states[1:])):
            raise TargetPositionValidationError("knot state values must be strictly increasing")
        if not states[0] < ZERO < states[-1]:
            raise TargetPositionValidationError("knot state values must straddle zero")
        zero_knots = tuple(item for item in self.knots if item.state_value == ZERO)
        if len(zero_knots) != 1 or zero_knots[0].target_fraction != neutral:
            raise TargetPositionValidationError(
                "exactly one zero knot is required and its target must equal neutral_fraction"
            )
        targets = tuple(item.target_fraction for item in self.knots)
        if any(not minimum <= value <= maximum for value in targets):
            raise TargetPositionValidationError("all knot targets must remain within min/max")
        if self.direction is TargetPositionDirection.NON_INCREASING:
            if any(left < right for left, right in zip(targets, targets[1:])):
                raise TargetPositionValidationError("targets must be non-increasing")
            expected_endpoints = (maximum, minimum)
        else:
            if any(left > right for left, right in zip(targets, targets[1:])):
                raise TargetPositionValidationError("targets must be non-decreasing")
            expected_endpoints = (minimum, maximum)
        if (targets[0], targets[-1]) != expected_endpoints:
            raise TargetPositionValidationError("curve endpoints must cover the declared min/max")
        object.__setattr__(self, "name", required_text(self.name, "name"))
        object.__setattr__(self, "reason", required_text(self.reason, "reason"))
        object.__setattr__(self, "created_by", required_text(self.created_by, "created_by"))
        object.__setattr__(self, "created_at_utc", utc(self.created_at_utc, "created_at_utc"))


@dataclass(frozen=True, slots=True)
class TargetPositionCalculationTrace:
    evaluation_mode: TargetPositionEvaluationMode
    lower_knot_ordinal: int
    upper_knot_ordinal: int
    lower_state_value: Decimal
    upper_state_value: Decimal
    lower_target_fraction: Decimal
    upper_target_fraction: Decimal
    interpolation_numerator: Decimal
    interpolation_denominator: Decimal
    interpolation_weight: Decimal

    def __post_init__(self) -> None:
        if not isinstance(self.evaluation_mode, TargetPositionEvaluationMode):
            raise TargetPositionValidationError("evaluation_mode is invalid")
        if self.lower_knot_ordinal < 0 or self.upper_knot_ordinal < self.lower_knot_ordinal:
            raise TargetPositionValidationError("trace knot ordinals are invalid")
        for name in (
            "lower_state_value", "upper_state_value", "lower_target_fraction",
            "upper_target_fraction", "interpolation_numerator",
            "interpolation_denominator", "interpolation_weight",
        ):
            object.__setattr__(self, name, canonical_decimal(getattr(self, name), name))


@dataclass(frozen=True, slots=True)
class TargetPositionResult:
    calculation_id: UUID
    operation_id: UUID
    run_id: UUID
    stage_id: UUID
    definition_id: UUID
    definition_version: int
    as_of_utc: datetime
    research_state_value: Decimal
    research_capital_basis_usd: Decimal
    current_position_value_usd: Decimal
    target_fraction: Decimal
    target_position_value_usd: Decimal
    adjustment_value_usd: Decimal
    adjustment_direction: TargetPositionAdjustmentDirection
    trace: TargetPositionCalculationTrace
    evidence_bindings: tuple[TargetPositionEvidenceBinding, ...]
    created_at_utc: datetime
    created_by: str
    reason: str
    schema_version: int = TARGET_POSITION_CONTRACT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.definition_version < 1:
            raise TargetPositionValidationError("definition_version must be positive")
        if not isinstance(self.adjustment_direction, TargetPositionAdjustmentDirection):
            raise TargetPositionValidationError("adjustment_direction is invalid")
        if self.schema_version != TARGET_POSITION_CONTRACT_SCHEMA_VERSION:
            raise TargetPositionValidationError("unsupported result schema version")
        for name in (
            "research_state_value", "research_capital_basis_usd", "current_position_value_usd",
            "target_fraction", "target_position_value_usd", "adjustment_value_usd",
        ):
            object.__setattr__(self, name, canonical_decimal(getattr(self, name), name))
        if self.research_capital_basis_usd < ZERO or self.current_position_value_usd < ZERO:
            raise TargetPositionValidationError("capital basis and current position must be non-negative")
        if not ZERO <= self.target_fraction <= ONE:
            raise TargetPositionValidationError("target fraction must be within [0, 1]")
        expected_target = self.research_capital_basis_usd * self.target_fraction
        expected_adjustment = expected_target - self.current_position_value_usd
        if self.target_position_value_usd != expected_target or self.adjustment_value_usd != expected_adjustment:
            raise TargetPositionValidationError("result notional fields are inconsistent")
        expected_direction = (
            TargetPositionAdjustmentDirection.NONE if expected_adjustment == ZERO
            else TargetPositionAdjustmentDirection.INCREASE if expected_adjustment > ZERO
            else TargetPositionAdjustmentDirection.DECREASE
        )
        if self.adjustment_direction is not expected_direction:
            raise TargetPositionValidationError("adjustment direction is inconsistent")
        object.__setattr__(self, "as_of_utc", utc(self.as_of_utc, "as_of_utc"))
        object.__setattr__(self, "created_at_utc", utc(self.created_at_utc, "created_at_utc"))
        object.__setattr__(self, "created_by", required_text(self.created_by, "created_by"))
        object.__setattr__(self, "reason", required_text(self.reason, "reason"))

    @property
    def current_position_fraction(self) -> Decimal | None:
        """Return a typed derived display value; zero basis has no defined ratio."""

        if self.research_capital_basis_usd == ZERO:
            return None
        return self.current_position_value_usd / self.research_capital_basis_usd


@dataclass(frozen=True, slots=True)
class TargetPositionOperationAttempt:
    attempt_id: UUID
    operation_id: UUID
    run_id: UUID
    stage_id: UUID
    operation_type: TargetPositionOperationType
    status: TargetPositionOperationStatus
    requested_at_utc: datetime
    completed_at_utc: datetime
    created_by: str
    reason: str
    definition_name: str | None = None
    direction: str | None = None
    minimum_fraction_text: str | None = None
    neutral_fraction_text: str | None = None
    maximum_fraction_text: str | None = None
    knot_inputs: tuple[TargetPositionKnotInput, ...] = ()
    predecessor_definition_id: UUID | None = None
    requested_definition_id: UUID | None = None
    resolved_definition_id: UUID | None = None
    research_state_value_text: str | None = None
    research_capital_basis_usd_text: str | None = None
    current_position_value_usd_text: str | None = None
    as_of_utc: datetime | None = None
    evidence_bindings: tuple[TargetPositionEvidenceBinding, ...] = ()
    result_calculation_id: UUID | None = None
    error_code: str | None = None
    error_summary: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.operation_type, TargetPositionOperationType):
            raise TargetPositionValidationError("operation_type is invalid")
        if not isinstance(self.status, TargetPositionOperationStatus):
            raise TargetPositionValidationError("operation status is invalid")
        if self.status is TargetPositionOperationStatus.COMPLETED:
            if self.error_code is not None or self.error_summary is not None:
                raise TargetPositionValidationError("completed operation cannot contain an error")
        elif not self.error_code or not self.error_summary:
            raise TargetPositionValidationError("failed operation requires code and summary")
        object.__setattr__(self, "requested_at_utc", utc(self.requested_at_utc, "requested_at_utc"))
        object.__setattr__(self, "completed_at_utc", utc(self.completed_at_utc, "completed_at_utc"))
        object.__setattr__(self, "as_of_utc", utc(self.as_of_utc, "as_of_utc") if self.as_of_utc else None)
        object.__setattr__(self, "created_by", required_text(self.created_by, "created_by"))


@dataclass(frozen=True, slots=True)
class TargetPositionOperationResult:
    attempt_id: UUID
    operation_id: UUID
    run_id: UUID
    stage_id: UUID
    status: TargetPositionOperationStatus
    summary: str
    definition_id: UUID | None = None
    calculation_id: UUID | None = None
    error_code: str | None = None


@dataclass(frozen=True, slots=True)
class TargetPositionDefinitionQuery:
    name_text: str | None = None
    status: TargetPositionDefinitionStatus | None = None
    limit: int = 200

    def __post_init__(self) -> None:
        if self.limit < 1 or self.limit > 5000:
            raise TargetPositionValidationError("definition query limit must be within 1..5000")


@dataclass(frozen=True, slots=True)
class TargetPositionResultQuery:
    definition_id: UUID | None = None
    direction: TargetPositionAdjustmentDirection | None = None
    limit: int = 500

    def __post_init__(self) -> None:
        if self.limit < 1 or self.limit > 5000:
            raise TargetPositionValidationError("result query limit must be within 1..5000")


@dataclass(frozen=True, slots=True)
class TargetPositionOperationQuery:
    status: TargetPositionOperationStatus | None = None
    operation_type: TargetPositionOperationType | None = None
    limit: int = 500

    def __post_init__(self) -> None:
        if self.limit < 1 or self.limit > 5000:
            raise TargetPositionValidationError("operation query limit must be within 1..5000")


__all__ = [name for name in globals() if name.startswith("TargetPosition") or name.startswith("Create") or name.startswith("Preview") or name == "TARGET_POSITION_CONTRACT_SCHEMA_VERSION"]
