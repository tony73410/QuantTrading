"""Immutable contracts for manual standardized-price-state Factor research."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from uuid import UUID

from .errors import StandardizedPriceStateValidationError


STANDARDIZED_PRICE_STATE_SCHEMA_VERSION = 1
STANDARDIZED_PRICE_STATE_FORMULA_ID = "price_minus_reference_over_positive_scale"
USD = "USD"
DIMENSIONLESS = "dimensionless"
ZERO = Decimal("0")


def utc(value: datetime, name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise StandardizedPriceStateValidationError(f"{name} must include a timezone")
    return value.astimezone(UTC)


def required_text(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise StandardizedPriceStateValidationError(f"{name} must not be empty")
    return value.strip()


def optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def decimal_text(value: str, name: str) -> Decimal:
    if not isinstance(value, str) or not value.strip():
        raise StandardizedPriceStateValidationError(
            f"{name} must be a Decimal text value"
        )
    try:
        parsed = Decimal(value.strip())
    except InvalidOperation as exc:
        raise StandardizedPriceStateValidationError(
            f"{name} must be valid Decimal text"
        ) from exc
    if not parsed.is_finite():
        raise StandardizedPriceStateValidationError(f"{name} must be finite")
    return parsed


def finite_decimal(value: Decimal, name: str) -> Decimal:
    if not isinstance(value, Decimal) or not value.is_finite():
        raise StandardizedPriceStateValidationError(
            f"{name} must be a finite Decimal"
        )
    return value


def normalized_symbol(value: str) -> str:
    symbol = required_text(value, "symbol").upper()
    if len(symbol) > 32 or any(character.isspace() for character in symbol):
        raise StandardizedPriceStateValidationError("symbol is invalid")
    return symbol


class StandardizedPriceStateDefinitionStatus(StrEnum):
    AVAILABLE = "available"
    ARCHIVED = "archived"


class StandardizedPriceStateInputSource(StrEnum):
    MANUAL_RESEARCH = "manual_research"


class StandardizedPriceStateEvidenceKind(StrEnum):
    ALGORITHM_RUN = "algorithm_run"
    FACTOR_CALCULATION = "factor_calculation"


class StandardizedPriceStateOperationType(StrEnum):
    DEFINITION_SAVE = "definition_save"
    PREVIEW = "preview"


class StandardizedPriceStateOperationStatus(StrEnum):
    COMPLETED = "completed"
    INVALID_INPUT = "invalid_input"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class StandardizedPriceStateEvidenceBinding:
    evidence_kind: StandardizedPriceStateEvidenceKind
    evidence_id: str
    source_component: str | None = None
    source_version: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.evidence_kind, StandardizedPriceStateEvidenceKind):
            raise StandardizedPriceStateValidationError(
                "evidence_kind must use StandardizedPriceStateEvidenceKind"
            )
        object.__setattr__(self, "evidence_id", required_text(self.evidence_id, "evidence_id"))
        object.__setattr__(self, "source_component", optional_text(self.source_component))
        object.__setattr__(self, "source_version", optional_text(self.source_version))
        if self.source_version is not None and self.source_component is None:
            raise StandardizedPriceStateValidationError(
                "source_version requires source_component"
            )


@dataclass(frozen=True, slots=True)
class CreateStandardizedPriceStateDefinitionCommand:
    name: str
    reason: str
    session_id: str
    request_id: str
    created_by: str
    predecessor_definition_id: UUID | None = None
    operation_id: UUID | None = None

    def __post_init__(self) -> None:
        for name in ("name", "reason"):
            if not isinstance(getattr(self, name), str):
                raise TypeError(f"{name} must be a string")
        for name in ("session_id", "request_id", "created_by"):
            object.__setattr__(self, name, required_text(getattr(self, name), name))


@dataclass(frozen=True, slots=True)
class PreviewStandardizedPriceStateCommand:
    definition_id: UUID
    symbol: str
    manual_price_usd: str
    manual_reference_price_usd: str
    manual_risk_scale_usd: str
    as_of_utc: datetime
    reason: str
    session_id: str
    request_id: str
    created_by: str
    evidence_bindings: tuple[StandardizedPriceStateEvidenceBinding, ...] = ()
    operation_id: UUID | None = None

    def __post_init__(self) -> None:
        for name in (
            "symbol",
            "manual_price_usd",
            "manual_reference_price_usd",
            "manual_risk_scale_usd",
            "reason",
        ):
            if not isinstance(getattr(self, name), str):
                raise TypeError(f"{name} must be a string")
        for name in ("session_id", "request_id", "created_by"):
            object.__setattr__(self, name, required_text(getattr(self, name), name))
        object.__setattr__(self, "as_of_utc", utc(self.as_of_utc, "as_of_utc"))


@dataclass(frozen=True, slots=True)
class StandardizedPriceStateDefinition:
    definition_id: UUID
    definition_version: int
    predecessor_definition_id: UUID | None
    name: str
    reason: str
    formula_id: str
    price_currency: str
    output_unit: str
    price_source: StandardizedPriceStateInputSource
    reference_source: StandardizedPriceStateInputSource
    risk_scale_source: StandardizedPriceStateInputSource
    status: StandardizedPriceStateDefinitionStatus
    created_at_utc: datetime
    created_by: str
    schema_version: int = STANDARDIZED_PRICE_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.definition_version < 1:
            raise StandardizedPriceStateValidationError(
                "definition_version must be positive"
            )
        if self.predecessor_definition_id == self.definition_id:
            raise StandardizedPriceStateValidationError(
                "a definition cannot be its own predecessor"
            )
        if self.formula_id != STANDARDIZED_PRICE_STATE_FORMULA_ID:
            raise StandardizedPriceStateValidationError(
                "unsupported standardized-price-state formula"
            )
        if self.price_currency != USD or self.output_unit != DIMENSIONLESS:
            raise StandardizedPriceStateValidationError(
                "Phase 5B requires USD inputs and a dimensionless output"
            )
        for name in ("price_source", "reference_source", "risk_scale_source"):
            if getattr(self, name) is not StandardizedPriceStateInputSource.MANUAL_RESEARCH:
                raise StandardizedPriceStateValidationError(
                    "Phase 5B accepts manual research inputs only"
                )
        if not isinstance(self.status, StandardizedPriceStateDefinitionStatus):
            raise StandardizedPriceStateValidationError("definition status is invalid")
        if self.schema_version != STANDARDIZED_PRICE_STATE_SCHEMA_VERSION:
            raise StandardizedPriceStateValidationError(
                "unsupported standardized-price-state schema version"
            )
        object.__setattr__(self, "name", required_text(self.name, "name"))
        object.__setattr__(self, "reason", required_text(self.reason, "reason"))
        object.__setattr__(self, "created_by", required_text(self.created_by, "created_by"))
        object.__setattr__(self, "created_at_utc", utc(self.created_at_utc, "created_at_utc"))


@dataclass(frozen=True, slots=True)
class StandardizedPriceStateTrace:
    formula_id: str
    price_currency: str
    output_unit: str
    price_source: StandardizedPriceStateInputSource
    reference_source: StandardizedPriceStateInputSource
    risk_scale_source: StandardizedPriceStateInputSource
    manual_price_usd: Decimal
    manual_reference_price_usd: Decimal
    price_deviation_usd: Decimal
    manual_risk_scale_usd: Decimal
    standardized_state: Decimal

    def __post_init__(self) -> None:
        if self.formula_id != STANDARDIZED_PRICE_STATE_FORMULA_ID:
            raise StandardizedPriceStateValidationError("trace formula is invalid")
        if self.price_currency != USD or self.output_unit != DIMENSIONLESS:
            raise StandardizedPriceStateValidationError("trace units are invalid")
        for name in ("price_source", "reference_source", "risk_scale_source"):
            if getattr(self, name) is not StandardizedPriceStateInputSource.MANUAL_RESEARCH:
                raise StandardizedPriceStateValidationError("trace sources must be manual research")
        for name in (
            "manual_price_usd",
            "manual_reference_price_usd",
            "price_deviation_usd",
            "manual_risk_scale_usd",
            "standardized_state",
        ):
            object.__setattr__(self, name, finite_decimal(getattr(self, name), name))
        if self.manual_price_usd <= ZERO or self.manual_reference_price_usd <= ZERO:
            raise StandardizedPriceStateValidationError(
                "manual price and reference must be positive"
            )
        if self.manual_risk_scale_usd <= ZERO:
            raise StandardizedPriceStateValidationError(
                "manual risk scale must be positive"
            )
        deviation = self.manual_price_usd - self.manual_reference_price_usd
        state = deviation / self.manual_risk_scale_usd
        if self.price_deviation_usd != deviation or self.standardized_state != state:
            raise StandardizedPriceStateValidationError(
                "trace arithmetic is inconsistent"
            )


@dataclass(frozen=True, slots=True)
class StandardizedPriceStateResult:
    calculation_id: UUID
    operation_id: UUID
    run_id: UUID
    stage_id: UUID
    definition_id: UUID
    definition_version: int
    symbol: str
    as_of_utc: datetime
    manual_price_usd: Decimal
    manual_reference_price_usd: Decimal
    manual_risk_scale_usd: Decimal
    price_deviation_usd: Decimal
    standardized_state: Decimal
    trace: StandardizedPriceStateTrace
    evidence_bindings: tuple[StandardizedPriceStateEvidenceBinding, ...]
    created_at_utc: datetime
    created_by: str
    reason: str
    schema_version: int = STANDARDIZED_PRICE_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.definition_version < 1:
            raise StandardizedPriceStateValidationError(
                "definition_version must be positive"
            )
        if self.schema_version != STANDARDIZED_PRICE_STATE_SCHEMA_VERSION:
            raise StandardizedPriceStateValidationError("result schema version is invalid")
        symbol = normalized_symbol(self.symbol)
        for name in (
            "manual_price_usd",
            "manual_reference_price_usd",
            "manual_risk_scale_usd",
            "price_deviation_usd",
            "standardized_state",
        ):
            object.__setattr__(self, name, finite_decimal(getattr(self, name), name))
        if (
            self.trace.manual_price_usd != self.manual_price_usd
            or self.trace.manual_reference_price_usd != self.manual_reference_price_usd
            or self.trace.manual_risk_scale_usd != self.manual_risk_scale_usd
            or self.trace.price_deviation_usd != self.price_deviation_usd
            or self.trace.standardized_state != self.standardized_state
        ):
            raise StandardizedPriceStateValidationError(
                "result and structured trace are inconsistent"
            )
        object.__setattr__(self, "symbol", symbol)
        object.__setattr__(self, "as_of_utc", utc(self.as_of_utc, "as_of_utc"))
        object.__setattr__(self, "created_at_utc", utc(self.created_at_utc, "created_at_utc"))
        object.__setattr__(self, "created_by", required_text(self.created_by, "created_by"))
        object.__setattr__(self, "reason", required_text(self.reason, "reason"))


@dataclass(frozen=True, slots=True)
class StandardizedPriceStateOperationAttempt:
    attempt_id: UUID
    operation_id: UUID
    run_id: UUID
    stage_id: UUID
    operation_type: StandardizedPriceStateOperationType
    status: StandardizedPriceStateOperationStatus
    requested_at_utc: datetime
    completed_at_utc: datetime
    created_by: str
    reason: str
    definition_name: str | None = None
    predecessor_definition_id: UUID | None = None
    requested_definition_id: UUID | None = None
    resolved_definition_id: UUID | None = None
    symbol: str | None = None
    manual_price_usd_text: str | None = None
    manual_reference_price_usd_text: str | None = None
    manual_risk_scale_usd_text: str | None = None
    as_of_utc: datetime | None = None
    evidence_bindings: tuple[StandardizedPriceStateEvidenceBinding, ...] = ()
    result_calculation_id: UUID | None = None
    error_code: str | None = None
    error_summary: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.operation_type, StandardizedPriceStateOperationType):
            raise StandardizedPriceStateValidationError("operation type is invalid")
        if not isinstance(self.status, StandardizedPriceStateOperationStatus):
            raise StandardizedPriceStateValidationError("operation status is invalid")
        if self.status is StandardizedPriceStateOperationStatus.COMPLETED:
            if self.error_code is not None or self.error_summary is not None:
                raise StandardizedPriceStateValidationError(
                    "completed operation cannot contain an error"
                )
        elif not self.error_code or not self.error_summary:
            raise StandardizedPriceStateValidationError(
                "failed operation requires an error code and summary"
            )
        object.__setattr__(self, "requested_at_utc", utc(self.requested_at_utc, "requested_at_utc"))
        object.__setattr__(self, "completed_at_utc", utc(self.completed_at_utc, "completed_at_utc"))
        object.__setattr__(self, "as_of_utc", utc(self.as_of_utc, "as_of_utc") if self.as_of_utc else None)
        object.__setattr__(self, "created_by", required_text(self.created_by, "created_by"))


@dataclass(frozen=True, slots=True)
class StandardizedPriceStateOperationResult:
    attempt_id: UUID
    operation_id: UUID
    run_id: UUID
    stage_id: UUID
    status: StandardizedPriceStateOperationStatus
    summary: str
    definition_id: UUID | None = None
    calculation_id: UUID | None = None
    error_code: str | None = None


@dataclass(frozen=True, slots=True)
class StandardizedPriceStateDefinitionQuery:
    name_text: str | None = None
    status: StandardizedPriceStateDefinitionStatus | None = None
    limit: int = 200

    def __post_init__(self) -> None:
        if self.limit < 1 or self.limit > 5000:
            raise StandardizedPriceStateValidationError(
                "definition query limit must be within 1..5000"
            )


@dataclass(frozen=True, slots=True)
class StandardizedPriceStateResultQuery:
    symbol: str | None = None
    definition_id: UUID | None = None
    as_of_from_utc: datetime | None = None
    as_of_to_utc: datetime | None = None
    limit: int = 500

    def __post_init__(self) -> None:
        if self.limit < 1 or self.limit > 5000:
            raise StandardizedPriceStateValidationError(
                "result query limit must be within 1..5000"
            )
        if self.symbol is not None:
            object.__setattr__(self, "symbol", normalized_symbol(self.symbol))
        for name in ("as_of_from_utc", "as_of_to_utc"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, utc(value, name))
        if (
            self.as_of_from_utc is not None
            and self.as_of_to_utc is not None
            and self.as_of_from_utc >= self.as_of_to_utc
        ):
            raise StandardizedPriceStateValidationError(
                "result query start must precede end"
            )


@dataclass(frozen=True, slots=True)
class StandardizedPriceStateOperationQuery:
    symbol: str | None = None
    status: StandardizedPriceStateOperationStatus | None = None
    operation_type: StandardizedPriceStateOperationType | None = None
    limit: int = 500

    def __post_init__(self) -> None:
        if self.limit < 1 or self.limit > 5000:
            raise StandardizedPriceStateValidationError(
                "operation query limit must be within 1..5000"
            )
        if self.symbol is not None:
            object.__setattr__(self, "symbol", normalized_symbol(self.symbol))


__all__ = [
    name
    for name in globals()
    if name.startswith("Standardized")
    or name.startswith("CreateStandardized")
    or name.startswith("PreviewStandardized")
    or name.startswith("STANDARDIZED_PRICE_STATE")
]
