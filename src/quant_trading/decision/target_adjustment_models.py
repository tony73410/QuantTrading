"""Type-distinct contracts for linked Target Position adjustment research."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from .errors import DecisionContractError
from .models import DecisionAction


TARGET_ADJUSTMENT_DECISION_SCHEMA_VERSION = 1
TARGET_ADJUSTMENT_POLICY_ID = "decision.target_adjustment_preview"
TARGET_ADJUSTMENT_POLICY_VERSION = "1.0.0"
USD = "USD"
DIMENSIONLESS = "dimensionless"
ZERO = Decimal("0")
ONE = Decimal("1")


def _utc(value: datetime, name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise DecisionContractError(f"{name} must include a timezone")
    return value.astimezone(UTC)


def _text(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DecisionContractError(f"{name} must not be empty")
    return value.strip()


def _decimal(value: Decimal, name: str) -> Decimal:
    if not isinstance(value, Decimal) or not value.is_finite():
        raise DecisionContractError(f"{name} must be a finite Decimal")
    return value


def _symbol(value: str) -> str:
    normalized = _text(value, "symbol").upper()
    if len(normalized) > 32 or any(character.isspace() for character in normalized):
        raise DecisionContractError("symbol is invalid")
    return normalized


class TargetAdjustmentDecisionStatus(StrEnum):
    INTENT_CREATED = "intent_created"
    HOLD = "hold"
    INVALID_INPUT = "invalid_input"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class TargetAdjustmentDecisionPreviewCommand:
    target_position_link_id: UUID
    reason: str
    session_id: str
    request_id: str
    created_by: str
    operation_id: UUID | None = None

    def __post_init__(self) -> None:
        for name in ("reason", "session_id", "request_id", "created_by"):
            object.__setattr__(self, name, _text(getattr(self, name), name))


@dataclass(frozen=True, slots=True)
class LinkedTargetDecisionInput:
    target_position_link_id: UUID
    linked_target_operation_id: UUID
    linked_parent_run_id: UUID
    linked_source_stage_id: UUID
    linked_target_stage_id: UUID
    target_child_run_id: UUID
    target_child_stage_id: UUID
    standardized_state_calculation_id: UUID
    standardized_state_run_id: UUID
    standardized_state_stage_id: UUID
    standardized_state_definition_id: UUID
    standardized_state_definition_version: int
    standardized_state_created_at_utc: datetime
    target_calculation_id: UUID
    target_definition_id: UUID
    target_definition_version: int
    target_created_at_utc: datetime
    symbol: str
    as_of_utc: datetime
    standardized_state: Decimal
    research_capital_basis_usd: Decimal
    current_position_value_usd: Decimal
    target_fraction: Decimal
    target_position_value_usd: Decimal
    adjustment_value_usd: Decimal
    source_direction: str
    link_created_at_utc: datetime
    source_schema_version: int = 1
    target_schema_version: int = 1
    link_schema_version: int = 1
    currency: str = USD
    state_unit: str = DIMENSIONLESS
    schema_version: int = TARGET_ADJUSTMENT_DECISION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.standardized_state_definition_version < 1 or self.target_definition_version < 1:
            raise DecisionContractError("source definition versions must be positive")
        if (
            self.source_schema_version != 1
            or self.target_schema_version != 1
            or self.link_schema_version != 1
            or self.schema_version != TARGET_ADJUSTMENT_DECISION_SCHEMA_VERSION
        ):
            raise DecisionContractError("unsupported linked target Decision schema")
        if self.currency != USD or self.state_unit != DIMENSIONLESS:
            raise DecisionContractError("linked target Decision units are invalid")
        object.__setattr__(self, "symbol", _symbol(self.symbol))
        for name in (
            "as_of_utc",
            "standardized_state_created_at_utc",
            "target_created_at_utc",
            "link_created_at_utc",
        ):
            object.__setattr__(self, name, _utc(getattr(self, name), name))
        for name in (
            "standardized_state",
            "research_capital_basis_usd",
            "current_position_value_usd",
            "target_fraction",
            "target_position_value_usd",
            "adjustment_value_usd",
        ):
            object.__setattr__(self, name, _decimal(getattr(self, name), name))
        if self.research_capital_basis_usd < ZERO or self.current_position_value_usd < ZERO:
            raise DecisionContractError("capital basis and current position must be non-negative")
        if not ZERO <= self.target_fraction <= ONE:
            raise DecisionContractError("target fraction must be within [0, 1]")
        expected_target = self.research_capital_basis_usd * self.target_fraction
        expected_adjustment = expected_target - self.current_position_value_usd
        if (
            self.target_position_value_usd != expected_target
            or self.adjustment_value_usd != expected_adjustment
        ):
            raise DecisionContractError("linked target notional evidence is inconsistent")
        expected_direction = (
            "none"
            if expected_adjustment == ZERO
            else "increase"
            if expected_adjustment > ZERO
            else "decrease"
        )
        if self.source_direction != expected_direction:
            raise DecisionContractError("linked target direction is inconsistent")


@dataclass(frozen=True, slots=True)
class TargetAdjustmentTradeIntent:
    intent_id: UUID
    decision_result_id: UUID
    operation_id: UUID
    run_id: UUID
    stage_id: UUID
    target_position_link_id: UUID
    target_calculation_id: UUID
    symbol: str
    as_of_utc: datetime
    action: DecisionAction
    current_exposure_usd: Decimal
    target_exposure_usd: Decimal
    desired_change_usd: Decimal
    requested_notional_usd: Decimal
    reason_codes: tuple[str, ...]
    created_at_utc: datetime
    policy_id: str = TARGET_ADJUSTMENT_POLICY_ID
    policy_version: str = TARGET_ADJUSTMENT_POLICY_VERSION
    currency: str = USD
    schema_version: int = TARGET_ADJUSTMENT_DECISION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.action not in {DecisionAction.INCREASE, DecisionAction.DECREASE}:
            raise DecisionContractError("target-adjustment intent must increase or decrease")
        if self.schema_version != TARGET_ADJUSTMENT_DECISION_SCHEMA_VERSION:
            raise DecisionContractError("unsupported target-adjustment intent schema")
        if self.policy_id != TARGET_ADJUSTMENT_POLICY_ID or self.policy_version != TARGET_ADJUSTMENT_POLICY_VERSION:
            raise DecisionContractError("target-adjustment policy identity is invalid")
        if self.currency != USD:
            raise DecisionContractError("target-adjustment intent currency must be USD")
        object.__setattr__(self, "symbol", _symbol(self.symbol))
        object.__setattr__(self, "as_of_utc", _utc(self.as_of_utc, "as_of_utc"))
        object.__setattr__(self, "created_at_utc", _utc(self.created_at_utc, "created_at_utc"))
        for name in (
            "current_exposure_usd",
            "target_exposure_usd",
            "desired_change_usd",
            "requested_notional_usd",
        ):
            object.__setattr__(self, name, _decimal(getattr(self, name), name))
        if self.current_exposure_usd < ZERO or self.target_exposure_usd < ZERO:
            raise DecisionContractError("target-adjustment exposures must be non-negative")
        if self.desired_change_usd != self.target_exposure_usd - self.current_exposure_usd:
            raise DecisionContractError("target-adjustment desired change is inconsistent")
        if self.requested_notional_usd != abs(self.desired_change_usd) or self.requested_notional_usd <= ZERO:
            raise DecisionContractError("requested notional must be the positive absolute change")
        expected_action = DecisionAction.INCREASE if self.desired_change_usd > ZERO else DecisionAction.DECREASE
        if self.action is not expected_action:
            raise DecisionContractError("target-adjustment action is inconsistent")
        if self.reason_codes != ("TARGET_POSITION_DIFFERENCE",):
            raise DecisionContractError("target-adjustment intent reason is invalid")


@dataclass(frozen=True, slots=True)
class TargetAdjustmentDecisionResult:
    decision_result_id: UUID
    operation_id: UUID
    run_id: UUID
    stage_id: UUID
    source: LinkedTargetDecisionInput
    status: TargetAdjustmentDecisionStatus
    action: DecisionAction
    intents: tuple[TargetAdjustmentTradeIntent, ...]
    reason_codes: tuple[str, ...]
    created_at_utc: datetime
    created_by: str
    reason: str
    software_version: str
    source_revision: str | None
    worktree_state: str
    policy_id: str = TARGET_ADJUSTMENT_POLICY_ID
    policy_version: str = TARGET_ADJUSTMENT_POLICY_VERSION
    schema_version: int = TARGET_ADJUSTMENT_DECISION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != TARGET_ADJUSTMENT_DECISION_SCHEMA_VERSION:
            raise DecisionContractError("unsupported target-adjustment result schema")
        if self.policy_id != TARGET_ADJUSTMENT_POLICY_ID or self.policy_version != TARGET_ADJUSTMENT_POLICY_VERSION:
            raise DecisionContractError("target-adjustment policy identity is invalid")
        if self.status not in {TargetAdjustmentDecisionStatus.INTENT_CREATED, TargetAdjustmentDecisionStatus.HOLD}:
            raise DecisionContractError("accepted target-adjustment result status is invalid")
        expected_action = (
            DecisionAction.HOLD
            if self.source.adjustment_value_usd == ZERO
            else DecisionAction.INCREASE
            if self.source.adjustment_value_usd > ZERO
            else DecisionAction.DECREASE
        )
        expected_status = (
            TargetAdjustmentDecisionStatus.HOLD
            if expected_action is DecisionAction.HOLD
            else TargetAdjustmentDecisionStatus.INTENT_CREATED
        )
        if self.action is not expected_action or self.status is not expected_status:
            raise DecisionContractError("target-adjustment result mapping is inconsistent")
        if expected_action is DecisionAction.HOLD and self.intents:
            raise DecisionContractError("HOLD target-adjustment result cannot contain an intent")
        if expected_action is not DecisionAction.HOLD and len(self.intents) != 1:
            raise DecisionContractError("non-zero target adjustment requires exactly one intent")
        for intent in self.intents:
            if (
                intent.decision_result_id != self.decision_result_id
                or intent.operation_id != self.operation_id
                or intent.run_id != self.run_id
                or intent.stage_id != self.stage_id
                or intent.target_position_link_id != self.source.target_position_link_id
                or intent.target_calculation_id != self.source.target_calculation_id
                or intent.symbol != self.source.symbol
                or intent.as_of_utc != self.source.as_of_utc
                or intent.current_exposure_usd != self.source.current_position_value_usd
                or intent.target_exposure_usd != self.source.target_position_value_usd
                or intent.desired_change_usd != self.source.adjustment_value_usd
            ):
                raise DecisionContractError("target-adjustment result contains a mismatched intent")
        expected_reasons = (
            ("TARGET_POSITION_EQUAL_CURRENT",)
            if expected_action is DecisionAction.HOLD
            else ("TARGET_POSITION_DIFFERENCE",)
        )
        if self.reason_codes != expected_reasons:
            raise DecisionContractError("target-adjustment result reasons are inconsistent")
        object.__setattr__(self, "created_at_utc", _utc(self.created_at_utc, "created_at_utc"))
        for name in ("created_by", "reason", "software_version", "worktree_state"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        if self.source_revision is not None:
            object.__setattr__(self, "source_revision", _text(self.source_revision, "source_revision"))


@dataclass(frozen=True, slots=True)
class TargetAdjustmentDecisionOperationAttempt:
    attempt_id: UUID
    operation_id: UUID
    run_id: UUID
    target_stage_id: UUID
    decision_stage_id: UUID | None
    status: TargetAdjustmentDecisionStatus
    requested_at_utc: datetime
    completed_at_utc: datetime
    requested_target_position_link_id: UUID
    session_id: str
    request_id: str
    created_by: str
    reason: str
    resolved_source: LinkedTargetDecisionInput | None = None
    decision_result_id: UUID | None = None
    error_code: str | None = None
    error_summary: str | None = None
    schema_version: int = TARGET_ADJUSTMENT_DECISION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != TARGET_ADJUSTMENT_DECISION_SCHEMA_VERSION:
            raise DecisionContractError("unsupported target-adjustment operation schema")
        if not isinstance(self.status, TargetAdjustmentDecisionStatus):
            raise DecisionContractError("target-adjustment operation status is invalid")
        completed = self.status in {TargetAdjustmentDecisionStatus.INTENT_CREATED, TargetAdjustmentDecisionStatus.HOLD}
        if completed:
            if self.resolved_source is None or self.decision_stage_id is None or self.decision_result_id is None:
                raise DecisionContractError("completed target-adjustment operation requires result identity")
            if self.error_code is not None or self.error_summary is not None:
                raise DecisionContractError("completed target-adjustment operation cannot contain an error")
        elif not self.error_code or not self.error_summary:
            raise DecisionContractError("failed target-adjustment operation requires code and summary")
        if self.resolved_source is not None and self.resolved_source.target_position_link_id != self.requested_target_position_link_id:
            raise DecisionContractError("resolved source does not match requested target link")
        object.__setattr__(self, "requested_at_utc", _utc(self.requested_at_utc, "requested_at_utc"))
        object.__setattr__(self, "completed_at_utc", _utc(self.completed_at_utc, "completed_at_utc"))
        for name in ("session_id", "request_id", "created_by", "reason"):
            object.__setattr__(self, name, _text(getattr(self, name), name))

    def matches_command(self, command: TargetAdjustmentDecisionPreviewCommand) -> bool:
        return (
            self.requested_target_position_link_id == command.target_position_link_id
            and self.session_id == command.session_id
            and self.request_id == command.request_id
            and self.created_by == command.created_by
            and self.reason == command.reason
        )


@dataclass(frozen=True, slots=True)
class TargetAdjustmentDecisionSourceLink:
    source_link_id: UUID
    operation_id: UUID
    decision_result_id: UUID
    decision_run_id: UUID
    decision_stage_id: UUID
    target_position_link_id: UUID
    linked_target_operation_id: UUID
    linked_parent_run_id: UUID
    target_child_run_id: UUID
    standardized_state_run_id: UUID
    target_calculation_id: UUID
    standardized_state_calculation_id: UUID
    created_at_utc: datetime
    schema_version: int = TARGET_ADJUSTMENT_DECISION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != TARGET_ADJUSTMENT_DECISION_SCHEMA_VERSION:
            raise DecisionContractError("unsupported target-adjustment source-link schema")
        object.__setattr__(self, "created_at_utc", _utc(self.created_at_utc, "created_at_utc"))


@dataclass(frozen=True, slots=True)
class TargetAdjustmentDecisionPreviewResult:
    attempt_id: UUID
    operation_id: UUID
    run_id: UUID
    status: TargetAdjustmentDecisionStatus
    summary: str
    parent_run_id: UUID | None = None
    target_child_run_id: UUID | None = None
    standardized_state_run_id: UUID | None = None
    decision_result_id: UUID | None = None
    intent_id: UUID | None = None
    error_code: str | None = None


@dataclass(frozen=True, slots=True)
class TargetAdjustmentDecisionQuery:
    symbol: str | None = None
    action: DecisionAction | None = None
    status: TargetAdjustmentDecisionStatus | None = None
    target_definition_id: UUID | None = None
    target_definition_version: int | None = None
    target_position_link_id: UUID | None = None
    as_of_from_utc: datetime | None = None
    as_of_to_utc: datetime | None = None
    limit: int = 500

    def __post_init__(self) -> None:
        if not 1 <= self.limit <= 5000:
            raise DecisionContractError("target-adjustment query limit must be within 1..5000")
        if self.symbol is not None:
            object.__setattr__(self, "symbol", _symbol(self.symbol))
        if self.action is not None and self.action not in {DecisionAction.INCREASE, DecisionAction.DECREASE, DecisionAction.HOLD}:
            raise DecisionContractError("target-adjustment query action is invalid")
        if self.target_definition_version is not None:
            if self.target_definition_version < 1 or self.target_definition_id is None:
                raise DecisionContractError("target definition version requires an ID")
        for name in ("as_of_from_utc", "as_of_to_utc"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, _utc(value, name))
        if self.as_of_from_utc is not None and self.as_of_to_utc is not None and self.as_of_from_utc >= self.as_of_to_utc:
            raise DecisionContractError("target-adjustment query start must precede end")


__all__ = [
    name
    for name in globals()
    if name.startswith("TargetAdjustment")
    or name.startswith("LinkedTarget")
    or name.startswith("TARGET_ADJUSTMENT")
]
