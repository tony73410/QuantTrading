"""Type-distinct P23-4A contracts for one exact P29 target adjustment."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from .errors import DecisionContractError
from .models import DecisionAction


CYCLE_TARGET_ADJUSTMENT_SCHEMA_VERSION = 1
CYCLE_TARGET_ADJUSTMENT_COMPONENT_ID = "decision.cycle_target_adjustment.p23_4a.v1"
CYCLE_TARGET_ADJUSTMENT_POLICY_ID = CYCLE_TARGET_ADJUSTMENT_COMPONENT_ID
CYCLE_TARGET_ADJUSTMENT_POLICY_VERSION = "1.0.0"
USD = "USD"
ZERO = Decimal("0")
ONE = Decimal("1")
_SOURCE_STATUSES = {
    "valid_linear",
    "valid_linear_clamped",
    "valid_accelerating",
    "valid_saturated",
}
_SOURCE_REGIONS = {"linear", "linear_clamped", "accelerating", "saturated"}


def _text(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DecisionContractError(f"{name} must not be empty")
    return value.strip()


def _optional_text(value: str | None, name: str) -> str | None:
    return None if value is None else _text(value, name)


def _utc(value: datetime, name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise DecisionContractError(f"{name} must include a timezone")
    return value.astimezone(UTC)


def _decimal(value: Decimal, name: str) -> Decimal:
    if not isinstance(value, Decimal) or not value.is_finite():
        raise DecisionContractError(f"{name} must be a finite Decimal")
    return value


def _symbol(value: str) -> str:
    normalized = _text(value, "symbol").upper()
    if len(normalized) > 32 or any(character.isspace() for character in normalized):
        raise DecisionContractError("symbol is invalid")
    return normalized


class CycleTargetAdjustmentOperationStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    INVALID_INPUT = "invalid_input"
    FAILED = "failed"

    @property
    def terminal(self) -> bool:
        return self not in {self.PENDING, self.RUNNING}


class CycleTargetAdjustmentResultStatus(StrEnum):
    INTENT_CREATED = "intent_created"
    HOLD = "hold"


@dataclass(frozen=True, slots=True)
class CycleTargetAdjustmentPreviewCommand:
    source_result_id: UUID
    source_run_id: UUID
    reason: str
    session_id: str
    request_id: str
    created_by: str
    operation_id: UUID | None = None

    def __post_init__(self) -> None:
        for name in ("reason", "session_id", "request_id", "created_by"):
            object.__setattr__(self, name, _text(getattr(self, name), name))

    @property
    def command_fingerprint(self) -> str:
        payload = {
            "source_result_id": str(self.source_result_id),
            "source_run_id": str(self.source_run_id),
            "reason": self.reason,
            "session_id": self.session_id,
            "request_id": self.request_id,
            "created_by": self.created_by,
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()


@dataclass(frozen=True, slots=True)
class CycleTargetDecisionInput:
    source_result_id: UUID
    source_operation_id: UUID
    source_run_id: UUID
    source_state_stage_id: UUID
    source_target_stage_id: UUID
    source_formula_definition_id: UUID
    source_formula_definition_version: int
    source_configuration_id: UUID
    source_configuration_version: int
    source_configuration_fingerprint: str
    source_reversal_result_id: UUID
    source_reversal_run_id: UUID
    source_reversal_step_id: UUID
    source_calculation_fingerprint: str
    symbol: str
    source_session: date
    source_available_at_utc: datetime
    source_region: str
    source_status: str
    target_fraction: Decimal
    research_capital_basis_usd: Decimal
    current_position_value_usd: Decimal
    target_position_value_usd: Decimal
    adjustment_value_usd: Decimal
    source_direction: str
    source_created_at_utc: datetime
    source_execution_allowed: bool = False
    source_live_allowed: bool = False
    source_schema_version: int = 1
    currency: str = USD
    schema_version: int = CYCLE_TARGET_ADJUSTMENT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.source_formula_definition_version < 1 or self.source_configuration_version < 1:
            raise DecisionContractError("P29 source versions must be positive")
        if self.source_schema_version != 1 or self.schema_version != 1:
            raise DecisionContractError("unsupported P29/P31 source schema")
        if self.source_execution_allowed or self.source_live_allowed:
            raise DecisionContractError("P29 source must remain non-executable")
        if self.currency != USD:
            raise DecisionContractError("cycle-target Decision currency must be USD")
        object.__setattr__(self, "symbol", _symbol(self.symbol))
        object.__setattr__(self, "source_available_at_utc", _utc(
            self.source_available_at_utc, "source_available_at_utc"
        ))
        object.__setattr__(self, "source_created_at_utc", _utc(
            self.source_created_at_utc, "source_created_at_utc"
        ))
        for name in ("source_configuration_fingerprint", "source_calculation_fingerprint"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        if self.source_region not in _SOURCE_REGIONS or self.source_status not in _SOURCE_STATUSES:
            raise DecisionContractError("P29 source region/status is not accepted")
        for name in (
            "target_fraction",
            "research_capital_basis_usd",
            "current_position_value_usd",
            "target_position_value_usd",
            "adjustment_value_usd",
        ):
            object.__setattr__(self, name, _decimal(getattr(self, name), name))
        if not ZERO <= self.target_fraction <= ONE:
            raise DecisionContractError("target fraction must be within [0, 1]")
        if self.research_capital_basis_usd < ZERO or self.current_position_value_usd < ZERO:
            raise DecisionContractError("hypothetical USD inputs must be non-negative")
        expected_target = self.research_capital_basis_usd * self.target_fraction
        expected_difference = expected_target - self.current_position_value_usd
        if (
            self.target_position_value_usd != expected_target
            or self.adjustment_value_usd != expected_difference
        ):
            raise DecisionContractError("P29 target arithmetic is inconsistent")
        expected_direction = (
            "none" if expected_difference == ZERO
            else "increase" if expected_difference > ZERO
            else "decrease"
        )
        if self.source_direction != expected_direction:
            raise DecisionContractError("P29 adjustment direction is inconsistent")


@dataclass(frozen=True, slots=True)
class CycleTargetAdjustmentTradeIntent:
    intent_id: UUID
    decision_result_id: UUID
    operation_id: UUID
    run_id: UUID
    decision_stage_id: UUID
    source_result_id: UUID
    source_run_id: UUID
    symbol: str
    source_session: date
    source_available_at_utc: datetime
    action: DecisionAction
    current_exposure_usd: Decimal
    target_exposure_usd: Decimal
    desired_change_usd: Decimal
    requested_notional_usd: Decimal
    reason_codes: tuple[str, ...]
    created_at_utc: datetime
    policy_id: str = CYCLE_TARGET_ADJUSTMENT_POLICY_ID
    policy_version: str = CYCLE_TARGET_ADJUSTMENT_POLICY_VERSION
    currency: str = USD
    execution_allowed: bool = False
    live_allowed: bool = False
    schema_version: int = CYCLE_TARGET_ADJUSTMENT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.action not in {DecisionAction.INCREASE, DecisionAction.DECREASE}:
            raise DecisionContractError("P31 intent must increase or decrease")
        if (
            self.policy_id != CYCLE_TARGET_ADJUSTMENT_POLICY_ID
            or self.policy_version != CYCLE_TARGET_ADJUSTMENT_POLICY_VERSION
            or self.currency != USD
            or self.execution_allowed
            or self.live_allowed
            or self.schema_version != 1
        ):
            raise DecisionContractError("P31 intent identity or safety metadata is invalid")
        object.__setattr__(self, "symbol", _symbol(self.symbol))
        object.__setattr__(self, "source_available_at_utc", _utc(
            self.source_available_at_utc, "source_available_at_utc"
        ))
        object.__setattr__(self, "created_at_utc", _utc(self.created_at_utc, "created_at_utc"))
        for name in (
            "current_exposure_usd", "target_exposure_usd",
            "desired_change_usd", "requested_notional_usd",
        ):
            object.__setattr__(self, name, _decimal(getattr(self, name), name))
        if self.current_exposure_usd < ZERO or self.target_exposure_usd < ZERO:
            raise DecisionContractError("P31 intent exposure must be non-negative")
        if self.desired_change_usd != self.target_exposure_usd - self.current_exposure_usd:
            raise DecisionContractError("P31 intent difference is inconsistent")
        if self.requested_notional_usd != abs(self.desired_change_usd) or self.requested_notional_usd <= ZERO:
            raise DecisionContractError("P31 requested notional must be the positive exact difference")
        expected_action = DecisionAction.INCREASE if self.desired_change_usd > ZERO else DecisionAction.DECREASE
        if self.action is not expected_action or self.reason_codes != ("TARGET_POSITION_DIFFERENCE",):
            raise DecisionContractError("P31 intent mapping is inconsistent")


@dataclass(frozen=True, slots=True)
class CycleTargetAdjustmentDecisionResult:
    decision_result_id: UUID
    operation_id: UUID
    run_id: UUID
    target_stage_id: UUID
    decision_stage_id: UUID
    source: CycleTargetDecisionInput
    status: CycleTargetAdjustmentResultStatus
    action: DecisionAction
    intents: tuple[CycleTargetAdjustmentTradeIntent, ...]
    reason_codes: tuple[str, ...]
    explanation: str
    created_at_utc: datetime
    created_by: str
    reason: str
    software_version: str
    source_revision: str | None
    worktree_state: str
    policy_id: str = CYCLE_TARGET_ADJUSTMENT_POLICY_ID
    policy_version: str = CYCLE_TARGET_ADJUSTMENT_POLICY_VERSION
    execution_allowed: bool = False
    live_allowed: bool = False
    schema_version: int = CYCLE_TARGET_ADJUSTMENT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if (
            self.policy_id != CYCLE_TARGET_ADJUSTMENT_POLICY_ID
            or self.policy_version != CYCLE_TARGET_ADJUSTMENT_POLICY_VERSION
            or self.execution_allowed
            or self.live_allowed
            or self.schema_version != 1
        ):
            raise DecisionContractError("P31 result identity or safety metadata is invalid")
        expected_action = (
            DecisionAction.HOLD if self.source.adjustment_value_usd == ZERO
            else DecisionAction.INCREASE if self.source.adjustment_value_usd > ZERO
            else DecisionAction.DECREASE
        )
        expected_status = (
            CycleTargetAdjustmentResultStatus.HOLD
            if expected_action is DecisionAction.HOLD
            else CycleTargetAdjustmentResultStatus.INTENT_CREATED
        )
        if self.action is not expected_action or self.status is not expected_status:
            raise DecisionContractError("P31 result mapping is inconsistent")
        if expected_action is DecisionAction.HOLD:
            if self.intents or self.reason_codes != ("TARGET_POSITION_EQUAL_CURRENT",):
                raise DecisionContractError("P31 HOLD cardinality/reason is invalid")
        elif len(self.intents) != 1 or self.reason_codes != ("TARGET_POSITION_DIFFERENCE",):
            raise DecisionContractError("P31 nonzero cardinality/reason is invalid")
        for intent in self.intents:
            if (
                intent.decision_result_id != self.decision_result_id
                or intent.operation_id != self.operation_id
                or intent.run_id != self.run_id
                or intent.decision_stage_id != self.decision_stage_id
                or intent.source_result_id != self.source.source_result_id
                or intent.source_run_id != self.source.source_run_id
                or intent.symbol != self.source.symbol
                or intent.source_session != self.source.source_session
                or intent.action is not self.action
                or intent.current_exposure_usd != self.source.current_position_value_usd
                or intent.target_exposure_usd != self.source.target_position_value_usd
                or intent.desired_change_usd != self.source.adjustment_value_usd
            ):
                raise DecisionContractError("P31 result contains a mismatched intent")
        object.__setattr__(self, "explanation", _text(self.explanation, "explanation"))
        object.__setattr__(self, "created_at_utc", _utc(self.created_at_utc, "created_at_utc"))
        for name in ("created_by", "reason", "software_version"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        object.__setattr__(self, "source_revision", _optional_text(
            self.source_revision, "source_revision"
        ))
        if self.worktree_state not in {"clean", "dirty", "unknown"}:
            raise DecisionContractError("P31 worktree state is invalid")


@dataclass(frozen=True, slots=True)
class CycleTargetAdjustmentOperationAttempt:
    attempt_id: UUID
    operation_id: UUID
    run_id: UUID
    target_stage_id: UUID | None
    decision_stage_id: UUID | None
    command_fingerprint: str
    status: CycleTargetAdjustmentOperationStatus
    requested_at_utc: datetime
    completed_at_utc: datetime | None
    requested_source_result_id: UUID
    requested_source_run_id: UUID
    session_id: str
    request_id: str
    created_by: str
    reason: str
    resolved_source: CycleTargetDecisionInput | None = None
    decision_result_id: UUID | None = None
    intent_id: UUID | None = None
    error_code: str | None = None
    error_summary: str | None = None
    software_version: str = "unknown"
    source_revision: str | None = None
    worktree_state: str = "unknown"
    execution_allowed: bool = False
    live_allowed: bool = False
    schema_version: int = CYCLE_TARGET_ADJUSTMENT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if (
            self.execution_allowed or self.live_allowed
            or self.schema_version != 1
            or not isinstance(self.status, CycleTargetAdjustmentOperationStatus)
        ):
            raise DecisionContractError("P31 operation identity or safety metadata is invalid")
        object.__setattr__(self, "command_fingerprint", _text(
            self.command_fingerprint, "command_fingerprint"
        ))
        object.__setattr__(self, "requested_at_utc", _utc(
            self.requested_at_utc, "requested_at_utc"
        ))
        if self.status.terminal:
            if self.completed_at_utc is None:
                raise DecisionContractError("terminal P31 operation requires completion time")
            object.__setattr__(self, "completed_at_utc", _utc(
                self.completed_at_utc, "completed_at_utc"
            ))
        elif self.completed_at_utc is not None:
            raise DecisionContractError("nonterminal P31 operation cannot be completed")
        if self.status is CycleTargetAdjustmentOperationStatus.COMPLETED:
            if self.resolved_source is None or self.decision_stage_id is None or self.decision_result_id is None:
                raise DecisionContractError("completed P31 operation requires accepted result evidence")
            if self.error_code is not None or self.error_summary is not None:
                raise DecisionContractError("completed P31 operation cannot contain an error")
        elif self.status in {
            CycleTargetAdjustmentOperationStatus.INVALID_INPUT,
            CycleTargetAdjustmentOperationStatus.FAILED,
        } and (not self.error_code or not self.error_summary):
            raise DecisionContractError("failed P31 operation requires code and summary")
        if self.resolved_source is not None and (
            self.resolved_source.source_result_id != self.requested_source_result_id
            or self.resolved_source.source_run_id != self.requested_source_run_id
        ):
            raise DecisionContractError("resolved P29 source does not match the request")
        for name in ("session_id", "request_id", "created_by", "reason", "software_version"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        object.__setattr__(self, "source_revision", _optional_text(
            self.source_revision, "source_revision"
        ))
        if self.worktree_state not in {"clean", "dirty", "unknown"}:
            raise DecisionContractError("P31 operation worktree state is invalid")

    def matches_command(self, command: CycleTargetAdjustmentPreviewCommand) -> bool:
        return self.command_fingerprint == command.command_fingerprint


@dataclass(frozen=True, slots=True)
class CycleTargetAdjustmentSourceLink:
    source_link_id: UUID
    operation_id: UUID
    decision_result_id: UUID
    intent_id: UUID | None
    decision_run_id: UUID
    decision_stage_id: UUID
    source_result_id: UUID
    source_operation_id: UUID
    source_run_id: UUID
    source_state_stage_id: UUID
    source_target_stage_id: UUID
    source_formula_definition_id: UUID
    source_configuration_id: UUID
    source_reversal_result_id: UUID
    source_reversal_run_id: UUID
    source_reversal_step_id: UUID
    created_at_utc: datetime
    schema_version: int = CYCLE_TARGET_ADJUSTMENT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise DecisionContractError("unsupported P31 source-link schema")
        object.__setattr__(self, "created_at_utc", _utc(self.created_at_utc, "created_at_utc"))


@dataclass(frozen=True, slots=True)
class CycleTargetAdjustmentPreviewOutcome:
    attempt_id: UUID
    operation_id: UUID
    run_id: UUID
    operation_status: CycleTargetAdjustmentOperationStatus
    summary: str
    source_run_id: UUID | None = None
    source_reversal_run_id: UUID | None = None
    decision_result_id: UUID | None = None
    intent_id: UUID | None = None
    result_status: CycleTargetAdjustmentResultStatus | None = None
    action: DecisionAction | None = None
    error_code: str | None = None


@dataclass(frozen=True, slots=True)
class CycleTargetAdjustmentReplayReport:
    decision_result_id: UUID
    matched: bool
    differences: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CycleTargetAdjustmentQuery:
    symbol: str | None = None
    action: DecisionAction | None = None
    result_status: CycleTargetAdjustmentResultStatus | None = None
    operation_status: CycleTargetAdjustmentOperationStatus | None = None
    source_result_id: UUID | None = None
    source_run_id: UUID | None = None
    formula_definition_id: UUID | None = None
    configuration_id: UUID | None = None
    source_session_from: date | None = None
    source_session_to: date | None = None
    limit: int = 500

    def __post_init__(self) -> None:
        if not 1 <= self.limit <= 5000:
            raise DecisionContractError("P31 query limit must be within 1..5000")
        if self.symbol is not None:
            object.__setattr__(self, "symbol", _symbol(self.symbol))
        if self.action is not None and self.action not in {
            DecisionAction.INCREASE, DecisionAction.DECREASE, DecisionAction.HOLD,
        }:
            raise DecisionContractError("P31 query action is invalid")
        if self.source_session_from and self.source_session_to:
            if self.source_session_from > self.source_session_to:
                raise DecisionContractError("P31 query session range is invalid")


__all__ = [
    name for name in globals()
    if name.startswith("CycleTargetAdjustment")
    or name.startswith("CycleTargetDecision")
    or name.startswith("CYCLE_TARGET_ADJUSTMENT")
]
