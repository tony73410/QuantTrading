"""Type-distinct, non-approving Risk contracts for target adjustments."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from quant_trading.application_settings import ExecutionEnvironment


SCHEMA_VERSION = 1
GATE_ID = "risk.target_adjustment_manual_review_gate"
GATE_VERSION = "1.0.0"
LOCKED_RULES = (
    ("SOURCE_CHAIN_INTEGRITY", 1),
    ("NON_EXECUTION_SAFETY_STATE", 2),
    ("NUMERICAL_RISK_POLICY_AVAILABILITY", 3),
)


def _text(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must not be empty")
    return value.strip()


def _utc(value: datetime, name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must include a timezone")
    return value.astimezone(UTC)


def _money(value: Decimal, name: str) -> Decimal:
    if not isinstance(value, Decimal) or not value.is_finite():
        raise ValueError(f"{name} must be a finite Decimal")
    return value


class TargetAdjustmentRiskStatus(StrEnum):
    MANUAL_REVIEW_REQUIRED = "manual_review_required"
    BLOCKED = "blocked"
    INVALID_INPUT = "invalid_input"
    FAILED = "failed"


class StructuralRuleStatus(StrEnum):
    PASSED = "passed"
    MANUAL_REVIEW = "manual_review"
    BLOCKED = "blocked"


class StructuralRuleSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass(frozen=True, slots=True)
class TargetAdjustmentRiskReviewCommand:
    target_adjustment_trade_intent_id: UUID
    reason: str
    session_id: str
    request_id: str
    created_by: str
    requested_at_utc: datetime
    operation_id: UUID | None = None

    def __post_init__(self) -> None:
        for name in ("reason", "session_id", "request_id", "created_by"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        object.__setattr__(self, "requested_at_utc", _utc(self.requested_at_utc, "requested_at_utc"))


@dataclass(frozen=True, slots=True)
class LinkedTargetRiskReviewInput:
    decision_result_id: UUID
    decision_operation_id: UUID
    decision_run_id: UUID
    decision_stage_id: UUID
    intent_id: UUID
    decision_policy_id: str
    decision_policy_version: str
    decision_schema_version: int
    intent_schema_version: int
    target_position_link_id: UUID
    linked_target_operation_id: UUID
    linked_parent_run_id: UUID
    target_child_run_id: UUID
    standardized_state_run_id: UUID
    target_calculation_id: UUID
    target_definition_id: UUID
    target_definition_version: int
    standardized_state_calculation_id: UUID
    standardized_state_definition_id: UUID
    standardized_state_definition_version: int
    target_position_link_created_at_utc: datetime
    target_position_link_schema_version: int
    target_result_created_at_utc: datetime
    target_result_schema_version: int
    standardized_state_created_at_utc: datetime
    standardized_state_schema_version: int
    symbol: str
    as_of_utc: datetime
    action: str
    current_exposure_usd: Decimal
    target_exposure_usd: Decimal
    desired_change_usd: Decimal
    requested_notional_usd: Decimal
    decision_created_at_utc: datetime
    intent_created_at_utc: datetime
    currency: str = "USD"
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION or self.currency != "USD":
            raise ValueError("unsupported target-adjustment Risk source schema or currency")
        if self.target_definition_version < 1 or self.standardized_state_definition_version < 1:
            raise ValueError("source definition versions must be positive")
        if any(
            version != 1
            for version in (
                self.decision_schema_version,
                self.intent_schema_version,
                self.target_position_link_schema_version,
                self.target_result_schema_version,
                self.standardized_state_schema_version,
            )
        ):
            raise ValueError("unsupported upstream source schema version")
        for name in ("decision_policy_id", "decision_policy_version", "symbol", "action"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        object.__setattr__(self, "symbol", self.symbol.upper())
        if self.action not in {"increase", "decrease"}:
            raise ValueError("Risk source action must be increase or decrease")
        for name in (
            "as_of_utc", "decision_created_at_utc", "intent_created_at_utc",
            "target_position_link_created_at_utc", "target_result_created_at_utc",
            "standardized_state_created_at_utc",
        ):
            object.__setattr__(self, name, _utc(getattr(self, name), name))
        for name in ("current_exposure_usd", "target_exposure_usd", "desired_change_usd", "requested_notional_usd"):
            object.__setattr__(self, name, _money(getattr(self, name), name))
        if self.current_exposure_usd < 0 or self.target_exposure_usd < 0:
            raise ValueError("source exposures must be non-negative")
        if self.desired_change_usd != self.target_exposure_usd - self.current_exposure_usd:
            raise ValueError("source desired change is inconsistent")
        if self.requested_notional_usd <= 0 or self.requested_notional_usd != abs(self.desired_change_usd):
            raise ValueError("source requested notional is inconsistent")
        expected = "increase" if self.desired_change_usd > 0 else "decrease"
        if self.action != expected:
            raise ValueError("source action is inconsistent")


@dataclass(frozen=True, slots=True)
class RiskSafetyStateSnapshot:
    snapshot_id: UUID
    execution_environment: ExecutionEnvironment
    live_trading_enabled: bool
    automatic_submission_enabled: bool
    manual_confirmation_required: bool
    execution_capability_implemented: bool
    configuration_version: str
    software_version: str
    source_revision: str | None
    worktree_state: str
    captured_at_utc: datetime
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION or not isinstance(self.execution_environment, ExecutionEnvironment):
            raise ValueError("unsupported Risk safety snapshot")
        for name in ("configuration_version", "software_version", "worktree_state"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        if self.source_revision is not None:
            object.__setattr__(self, "source_revision", _text(self.source_revision, "source_revision"))
        object.__setattr__(self, "captured_at_utc", _utc(self.captured_at_utc, "captured_at_utc"))

    @property
    def is_non_executing(self) -> bool:
        return (
            self.execution_environment is not ExecutionEnvironment.ALPACA_LIVE
            and not self.live_trading_enabled
            and not self.automatic_submission_enabled
            and self.manual_confirmation_required
            and not self.execution_capability_implemented
        )


@dataclass(frozen=True, slots=True)
class TargetAdjustmentStructuralRuleResult:
    rule_result_id: UUID
    review_result_id: UUID
    run_id: UUID
    stage_id: UUID
    rule_id: str
    rule_version: str
    rule_name: str
    evaluation_order: int
    status: StructuralRuleStatus
    input_summary: str
    expected_condition: str
    reason_codes: tuple[str, ...]
    severity: StructuralRuleSeverity
    stop_processing: bool
    evaluated_at_utc: datetime
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError("unsupported structural rule schema")
        expected = {name: order for name, order in LOCKED_RULES}
        if expected.get(self.rule_id) != self.evaluation_order or self.rule_version != "1":
            raise ValueError("structural rule identity/order is not locked")
        for name in ("rule_name", "input_summary", "expected_condition"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        if not self.reason_codes or any(not str(code).strip() for code in self.reason_codes):
            raise ValueError("structural rule requires reason codes")
        object.__setattr__(self, "evaluated_at_utc", _utc(self.evaluated_at_utc, "evaluated_at_utc"))


@dataclass(frozen=True, slots=True)
class TargetAdjustmentRiskReviewResult:
    review_result_id: UUID
    operation_id: UUID
    run_id: UUID
    stage_id: UUID
    source: LinkedTargetRiskReviewInput
    safety_snapshot: RiskSafetyStateSnapshot
    status: TargetAdjustmentRiskStatus
    rules: tuple[TargetAdjustmentStructuralRuleResult, ...]
    reason_codes: tuple[str, ...]
    warnings: tuple[str, ...]
    created_at_utc: datetime
    created_by: str
    reason: str
    software_version: str
    approved_notional_usd: None = None
    risk_approved_intent_id: None = None
    gate_id: str = GATE_ID
    gate_version: str = GATE_VERSION
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION or self.gate_id != GATE_ID or self.gate_version != GATE_VERSION:
            raise ValueError("unsupported target-adjustment Risk gate identity")
        if self.status not in {TargetAdjustmentRiskStatus.MANUAL_REVIEW_REQUIRED, TargetAdjustmentRiskStatus.BLOCKED}:
            raise ValueError("accepted Risk result must be manual-review or blocked")
        if self.approved_notional_usd is not None or self.risk_approved_intent_id is not None:
            raise ValueError("manual-review gate cannot emit approved Risk evidence")
        expected_ids = [name for name, _ in LOCKED_RULES]
        actual_ids = [rule.rule_id for rule in self.rules]
        if self.status is TargetAdjustmentRiskStatus.MANUAL_REVIEW_REQUIRED:
            if actual_ids != expected_ids or self.rules[-1].status is not StructuralRuleStatus.MANUAL_REVIEW:
                raise ValueError("manual-review result requires all three locked gates")
        elif actual_ids != expected_ids[:2] or self.rules[-1].status is not StructuralRuleStatus.BLOCKED:
            raise ValueError("blocked result requires source and safety gates")
        if any(rule.review_result_id != self.review_result_id or rule.run_id != self.run_id or rule.stage_id != self.stage_id for rule in self.rules):
            raise ValueError("rule result parent identity is inconsistent")
        if not self.reason_codes:
            raise ValueError("Risk result requires reason codes")
        for name in ("created_by", "reason", "software_version"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        object.__setattr__(self, "created_at_utc", _utc(self.created_at_utc, "created_at_utc"))


@dataclass(frozen=True, slots=True)
class TargetAdjustmentRiskOperationAttempt:
    attempt_id: UUID
    operation_id: UUID
    run_id: UUID
    decision_stage_id: UUID
    risk_stage_id: UUID | None
    requested_intent_id: UUID
    status: TargetAdjustmentRiskStatus
    requested_at_utc: datetime
    completed_at_utc: datetime
    session_id: str
    request_id: str
    created_by: str
    reason: str
    resolved_source: LinkedTargetRiskReviewInput | None = None
    safety_snapshot: RiskSafetyStateSnapshot | None = None
    review_result_id: UUID | None = None
    error_code: str | None = None
    error_summary: str | None = None
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        accepted = self.status in {TargetAdjustmentRiskStatus.MANUAL_REVIEW_REQUIRED, TargetAdjustmentRiskStatus.BLOCKED}
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError("unsupported Risk operation schema")
        if accepted:
            if None in (self.risk_stage_id, self.resolved_source, self.safety_snapshot, self.review_result_id):
                raise ValueError("completed Risk operation requires resolved evidence")
            if self.error_code is not None or self.error_summary is not None:
                raise ValueError("completed Risk operation cannot contain an error")
        elif not self.error_code or not self.error_summary:
            raise ValueError("failed Risk operation requires error evidence")
        if self.resolved_source is not None and self.resolved_source.intent_id != self.requested_intent_id:
            raise ValueError("resolved Risk source does not match requested intent")
        for name in ("requested_at_utc", "completed_at_utc"):
            object.__setattr__(self, name, _utc(getattr(self, name), name))
        for name in ("session_id", "request_id", "created_by", "reason"):
            object.__setattr__(self, name, _text(getattr(self, name), name))

    def matches_command(self, command: TargetAdjustmentRiskReviewCommand) -> bool:
        return (
            self.requested_intent_id == command.target_adjustment_trade_intent_id
            and self.session_id == command.session_id
            and self.request_id == command.request_id
            and self.created_by == command.created_by
            and self.reason == command.reason
        )


@dataclass(frozen=True, slots=True)
class TargetAdjustmentRiskSourceLink:
    source_link_id: UUID
    operation_id: UUID
    review_result_id: UUID
    risk_run_id: UUID
    risk_stage_id: UUID
    decision_result_id: UUID
    intent_id: UUID
    decision_run_id: UUID
    linked_parent_run_id: UUID
    target_child_run_id: UUID
    standardized_state_run_id: UUID
    target_position_link_id: UUID
    target_calculation_id: UUID
    standardized_state_calculation_id: UUID
    created_at_utc: datetime
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError("unsupported Risk source-link schema")
        object.__setattr__(self, "created_at_utc", _utc(self.created_at_utc, "created_at_utc"))


@dataclass(frozen=True, slots=True)
class TargetAdjustmentRiskReviewOutcome:
    attempt_id: UUID
    operation_id: UUID
    run_id: UUID
    status: TargetAdjustmentRiskStatus
    summary: str
    decision_run_id: UUID | None = None
    linked_parent_run_id: UUID | None = None
    target_child_run_id: UUID | None = None
    standardized_state_run_id: UUID | None = None
    review_result_id: UUID | None = None
    error_code: str | None = None


@dataclass(frozen=True, slots=True)
class TargetAdjustmentRiskQuery:
    symbol: str | None = None
    action: str | None = None
    status: TargetAdjustmentRiskStatus | None = None
    as_of_from_utc: datetime | None = None
    as_of_to_utc: datetime | None = None
    limit: int = 500

    def __post_init__(self) -> None:
        if not 1 <= self.limit <= 5000:
            raise ValueError("Risk query limit must be within 1..5000")
        if self.symbol is not None:
            object.__setattr__(self, "symbol", _text(self.symbol, "symbol").upper())
        if self.action is not None and self.action not in {"increase", "decrease"}:
            raise ValueError("Risk query action is invalid")
        for name in ("as_of_from_utc", "as_of_to_utc"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, _utc(value, name))


__all__ = [name for name in globals() if name.startswith("TargetAdjustment") or name.startswith("RiskSafety") or name.startswith("Structural") or name in {"GATE_ID", "GATE_VERSION", "LOCKED_RULES"}]
