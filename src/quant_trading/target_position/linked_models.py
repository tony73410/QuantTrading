"""Typed contracts for one exact standardized-state to target-position link."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from .errors import TargetPositionValidationError
from .models import canonical_decimal, decimal_text, required_text, utc


LINKED_TARGET_POSITION_SCHEMA_VERSION = 1
STANDARDIZED_STATE_SOURCE_COMPONENT = "factor.standardized_price_state.manual"
DIMENSIONLESS = "dimensionless"


def _normalized_symbol(value: str) -> str:
    symbol = required_text(value, "symbol").upper()
    if len(symbol) > 32 or any(character.isspace() for character in symbol):
        raise TargetPositionValidationError("symbol is invalid")
    return symbol


class LinkedTargetPositionOperationStatus(StrEnum):
    COMPLETED = "completed"
    INVALID_INPUT = "invalid_input"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class LinkedTargetPositionPreviewCommand:
    standardized_state_calculation_id: UUID
    target_position_definition_id: UUID
    research_capital_basis_usd: str
    current_position_value_usd: str
    reason: str
    session_id: str
    request_id: str
    created_by: str
    operation_id: UUID | None = None

    def __post_init__(self) -> None:
        for name in (
            "research_capital_basis_usd",
            "current_position_value_usd",
            "reason",
        ):
            if not isinstance(getattr(self, name), str):
                raise TypeError(f"{name} must be a string")
        for name in ("session_id", "request_id", "created_by"):
            object.__setattr__(self, name, required_text(getattr(self, name), name))


@dataclass(frozen=True, slots=True)
class StandardizedStateTargetInput:
    source_calculation_id: UUID
    source_run_id: UUID
    source_stage_id: UUID
    source_definition_id: UUID
    source_definition_version: int
    symbol: str
    as_of_utc: datetime
    standardized_state: Decimal
    source_created_at_utc: datetime
    output_unit: str
    source_component: str = STANDARDIZED_STATE_SOURCE_COMPONENT
    schema_version: int = LINKED_TARGET_POSITION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.source_definition_version < 1:
            raise TargetPositionValidationError("source definition version must be positive")
        if self.source_component != STANDARDIZED_STATE_SOURCE_COMPONENT:
            raise TargetPositionValidationError("unsupported standardized-state source component")
        if self.output_unit != DIMENSIONLESS:
            raise TargetPositionValidationError("linked source output must be dimensionless")
        if self.schema_version != LINKED_TARGET_POSITION_SCHEMA_VERSION:
            raise TargetPositionValidationError("unsupported linked source schema version")
        object.__setattr__(self, "symbol", _normalized_symbol(self.symbol))
        object.__setattr__(self, "as_of_utc", utc(self.as_of_utc, "source as_of_utc"))
        object.__setattr__(
            self,
            "source_created_at_utc",
            utc(self.source_created_at_utc, "source created_at_utc"),
        )
        object.__setattr__(
            self,
            "standardized_state",
            canonical_decimal(self.standardized_state, "standardized_state"),
        )


@dataclass(frozen=True, slots=True)
class LinkedTargetPositionOperationAttempt:
    attempt_id: UUID
    operation_id: UUID
    parent_run_id: UUID
    source_stage_id: UUID
    target_stage_id: UUID | None
    child_run_id: UUID | None
    child_stage_id: UUID | None
    status: LinkedTargetPositionOperationStatus
    requested_at_utc: datetime
    completed_at_utc: datetime
    requested_source_calculation_id: UUID
    requested_target_definition_id: UUID
    research_capital_basis_usd_text: str
    current_position_value_usd_text: str
    session_id: str
    request_id: str
    created_by: str
    reason: str
    resolved_source_run_id: UUID | None = None
    resolved_source_stage_id: UUID | None = None
    resolved_source_definition_id: UUID | None = None
    resolved_source_definition_version: int | None = None
    resolved_symbol: str | None = None
    resolved_source_as_of_utc: datetime | None = None
    resolved_standardized_state_text: str | None = None
    resolved_target_definition_id: UUID | None = None
    resolved_target_definition_version: int | None = None
    target_result_calculation_id: UUID | None = None
    error_code: str | None = None
    error_summary: str | None = None
    schema_version: int = LINKED_TARGET_POSITION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.status, LinkedTargetPositionOperationStatus):
            raise TargetPositionValidationError("linked operation status is invalid")
        if self.schema_version != LINKED_TARGET_POSITION_SCHEMA_VERSION:
            raise TargetPositionValidationError("unsupported linked operation schema version")
        if self.status is LinkedTargetPositionOperationStatus.COMPLETED:
            required = (
                self.target_stage_id,
                self.child_run_id,
                self.child_stage_id,
                self.resolved_source_run_id,
                self.resolved_source_stage_id,
                self.resolved_source_definition_id,
                self.resolved_source_definition_version,
                self.resolved_symbol,
                self.resolved_source_as_of_utc,
                self.resolved_standardized_state_text,
                self.resolved_target_definition_id,
                self.resolved_target_definition_version,
                self.target_result_calculation_id,
            )
            if any(item is None for item in required):
                raise TargetPositionValidationError(
                    "completed linked operation requires complete source/target identity"
                )
            if self.error_code is not None or self.error_summary is not None:
                raise TargetPositionValidationError(
                    "completed linked operation cannot contain an error"
                )
        elif not self.error_code or not self.error_summary:
            raise TargetPositionValidationError(
                "failed linked operation requires code and summary"
            )
        if (
            self.resolved_source_definition_version is not None
            and self.resolved_source_definition_version < 1
        ):
            raise TargetPositionValidationError(
                "resolved source definition version must be positive"
            )
        if (
            self.resolved_target_definition_version is not None
            and self.resolved_target_definition_version < 1
        ):
            raise TargetPositionValidationError(
                "resolved target definition version must be positive"
            )
        if self.resolved_symbol is not None:
            object.__setattr__(self, "resolved_symbol", _normalized_symbol(self.resolved_symbol))
        if self.resolved_standardized_state_text is not None:
            decimal_text(self.resolved_standardized_state_text, "resolved_standardized_state")
        object.__setattr__(self, "requested_at_utc", utc(self.requested_at_utc, "requested_at_utc"))
        object.__setattr__(self, "completed_at_utc", utc(self.completed_at_utc, "completed_at_utc"))
        if self.resolved_source_as_of_utc is not None:
            object.__setattr__(
                self,
                "resolved_source_as_of_utc",
                utc(self.resolved_source_as_of_utc, "resolved_source_as_of_utc"),
            )
        for name in ("session_id", "request_id", "created_by"):
            object.__setattr__(self, name, required_text(getattr(self, name), name))

    def matches_command(self, command: LinkedTargetPositionPreviewCommand) -> bool:
        return (
            self.requested_source_calculation_id == command.standardized_state_calculation_id
            and self.requested_target_definition_id == command.target_position_definition_id
            and self.research_capital_basis_usd_text == command.research_capital_basis_usd
            and self.current_position_value_usd_text == command.current_position_value_usd
            and self.session_id == command.session_id
            and self.request_id == command.request_id
            and self.created_by == command.created_by
            and self.reason == command.reason
        )


@dataclass(frozen=True, slots=True)
class StandardizedStateTargetPositionLink:
    link_id: UUID
    operation_id: UUID
    parent_run_id: UUID
    source_stage_id: UUID
    target_stage_id: UUID
    child_run_id: UUID
    child_stage_id: UUID
    source_calculation_id: UUID
    source_run_id: UUID
    source_result_stage_id: UUID
    source_definition_id: UUID
    source_definition_version: int
    symbol: str
    source_as_of_utc: datetime
    standardized_state: Decimal
    target_calculation_id: UUID
    target_definition_id: UUID
    target_definition_version: int
    created_at_utc: datetime
    created_by: str
    reason: str
    schema_version: int = LINKED_TARGET_POSITION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.source_definition_version < 1 or self.target_definition_version < 1:
            raise TargetPositionValidationError("linked definition versions must be positive")
        if self.schema_version != LINKED_TARGET_POSITION_SCHEMA_VERSION:
            raise TargetPositionValidationError("unsupported target link schema version")
        object.__setattr__(self, "symbol", _normalized_symbol(self.symbol))
        object.__setattr__(self, "source_as_of_utc", utc(self.source_as_of_utc, "source_as_of_utc"))
        object.__setattr__(self, "created_at_utc", utc(self.created_at_utc, "created_at_utc"))
        object.__setattr__(
            self,
            "standardized_state",
            canonical_decimal(self.standardized_state, "standardized_state"),
        )
        object.__setattr__(self, "created_by", required_text(self.created_by, "created_by"))
        object.__setattr__(self, "reason", required_text(self.reason, "reason"))


@dataclass(frozen=True, slots=True)
class LinkedTargetPositionPreviewResult:
    attempt_id: UUID
    operation_id: UUID
    parent_run_id: UUID
    status: LinkedTargetPositionOperationStatus
    summary: str
    source_run_id: UUID | None = None
    child_run_id: UUID | None = None
    target_calculation_id: UUID | None = None
    error_code: str | None = None


@dataclass(frozen=True, slots=True)
class LinkedTargetPositionQuery:
    symbol: str | None = None
    source_definition_id: UUID | None = None
    target_definition_id: UUID | None = None
    status: LinkedTargetPositionOperationStatus | None = None
    as_of_from_utc: datetime | None = None
    as_of_to_utc: datetime | None = None
    limit: int = 500

    def __post_init__(self) -> None:
        if self.limit < 1 or self.limit > 5000:
            raise TargetPositionValidationError("linked query limit must be within 1..5000")
        if self.symbol is not None:
            object.__setattr__(self, "symbol", _normalized_symbol(self.symbol))
        for name in ("as_of_from_utc", "as_of_to_utc"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, utc(value, name))
        if (
            self.as_of_from_utc is not None
            and self.as_of_to_utc is not None
            and self.as_of_from_utc >= self.as_of_to_utc
        ):
            raise TargetPositionValidationError("linked query start must precede end")


__all__ = [
    "DIMENSIONLESS",
    "LINKED_TARGET_POSITION_SCHEMA_VERSION",
    "STANDARDIZED_STATE_SOURCE_COMPONENT",
    "LinkedTargetPositionOperationAttempt",
    "LinkedTargetPositionOperationStatus",
    "LinkedTargetPositionPreviewCommand",
    "LinkedTargetPositionPreviewResult",
    "LinkedTargetPositionQuery",
    "StandardizedStateTargetInput",
    "StandardizedStateTargetPositionLink",
]
