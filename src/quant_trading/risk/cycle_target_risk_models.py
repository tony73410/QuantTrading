"""P23-4B contracts for structural review of one exact P31 intent."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from .target_adjustment_models import (
    LOCKED_RULES,
    RiskSafetyStateSnapshot,
    StructuralRuleSeverity,
    StructuralRuleStatus,
)


CYCLE_TARGET_RISK_SCHEMA_VERSION = 1
CYCLE_TARGET_RISK_COMPONENT_ID = "risk.cycle_target_manual_review_gate.p23_4b.v1"
CYCLE_TARGET_RISK_COMPONENT_VERSION = "1.0.0"
CYCLE_TARGET_RISK_GATE_ID = CYCLE_TARGET_RISK_COMPONENT_ID
CYCLE_TARGET_RISK_GATE_VERSION = CYCLE_TARGET_RISK_COMPONENT_VERSION
P31_POLICY_ID = "decision.cycle_target_adjustment.p23_4a.v1"
P31_POLICY_VERSION = "1.0.0"


def _text(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must not be empty")
    return value.strip()


def _utc(value: datetime, name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must include a timezone")
    return value.astimezone(UTC)


def _decimal(value: Decimal, name: str) -> Decimal:
    if not isinstance(value, Decimal) or not value.is_finite():
        raise ValueError(f"{name} must be a finite Decimal")
    return value


class CycleTargetRiskStatus(StrEnum):
    MANUAL_REVIEW_REQUIRED = "manual_review_required"
    BLOCKED = "blocked"
    INVALID_INPUT = "invalid_input"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class CycleTargetRiskReviewCommand:
    intent_id: UUID
    decision_result_id: UUID
    decision_run_id: UUID
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

    @property
    def command_fingerprint(self) -> str:
        value = {
            "intent_id": str(self.intent_id), "decision_result_id": str(self.decision_result_id),
            "decision_run_id": str(self.decision_run_id), "reason": self.reason,
            "session_id": self.session_id, "request_id": self.request_id,
            "created_by": self.created_by,
        }
        return hashlib.sha256(
            json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()


@dataclass(frozen=True, slots=True)
class CycleTargetRiskReviewInput:
    decision_result_id: UUID
    decision_operation_id: UUID
    decision_run_id: UUID
    decision_target_stage_id: UUID
    decision_stage_id: UUID
    intent_id: UUID
    decision_policy_id: str
    decision_policy_version: str
    decision_result_schema_version: int
    intent_schema_version: int
    decision_created_at_utc: datetime
    intent_created_at_utc: datetime
    decision_software_version: str
    decision_source_revision: str | None
    decision_worktree_state: str
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
    current_exposure_usd: Decimal
    target_exposure_usd: Decimal
    desired_change_usd: Decimal
    requested_notional_usd: Decimal
    action: str
    source_created_at_utc: datetime
    source_execution_allowed: bool = False
    source_live_allowed: bool = False
    decision_execution_allowed: bool = False
    decision_live_allowed: bool = False
    intent_execution_allowed: bool = False
    intent_live_allowed: bool = False
    source_schema_version: int = 1
    currency: str = "USD"
    schema_version: int = CYCLE_TARGET_RISK_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if (
            self.schema_version != 1 or self.source_schema_version != 1
            or self.decision_result_schema_version != 1 or self.intent_schema_version != 1
            or self.currency != "USD"
        ):
            raise ValueError("unsupported P33 source schema or currency")
        if self.decision_policy_id != P31_POLICY_ID or self.decision_policy_version != P31_POLICY_VERSION:
            raise ValueError("P33 requires the exact approved P31 policy")
        if any((self.source_execution_allowed, self.source_live_allowed,
                self.decision_execution_allowed, self.decision_live_allowed,
                self.intent_execution_allowed, self.intent_live_allowed)):
            raise ValueError("P33 source chain must remain non-executable")
        if self.source_formula_definition_version < 1 or self.source_configuration_version < 1:
            raise ValueError("P29 source versions must be positive")
        for name in (
            "decision_policy_id", "decision_policy_version", "decision_software_version",
            "decision_worktree_state", "source_configuration_fingerprint",
            "source_calculation_fingerprint", "symbol", "source_region", "source_status", "action",
        ):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        object.__setattr__(self, "symbol", self.symbol.upper())
        if self.decision_source_revision is not None:
            object.__setattr__(self, "decision_source_revision", _text(self.decision_source_revision, "decision_source_revision"))
        if self.decision_worktree_state not in {"clean", "dirty", "unknown"}:
            raise ValueError("P31 worktree state is invalid")
        if self.action not in {"increase", "decrease"}:
            raise ValueError("P33 accepts only a nonzero P31 action")
        if self.source_region not in {"linear", "linear_clamped", "accelerating", "saturated"}:
            raise ValueError("P29 source region is invalid")
        if self.source_status not in {"valid_linear", "valid_linear_clamped", "valid_accelerating", "valid_saturated"}:
            raise ValueError("P29 source status is invalid")
        for name in (
            "decision_created_at_utc", "intent_created_at_utc", "source_available_at_utc",
            "source_created_at_utc",
        ):
            object.__setattr__(self, name, _utc(getattr(self, name), name))
        for name in (
            "target_fraction", "research_capital_basis_usd", "current_exposure_usd",
            "target_exposure_usd", "desired_change_usd", "requested_notional_usd",
        ):
            object.__setattr__(self, name, _decimal(getattr(self, name), name))
        if not Decimal("0") <= self.target_fraction <= Decimal("1"):
            raise ValueError("P29 target fraction is outside [0, 1]")
        if self.research_capital_basis_usd < 0 or self.current_exposure_usd < 0 or self.target_exposure_usd < 0:
            raise ValueError("P33 source amounts must be non-negative")
        if self.target_exposure_usd != self.research_capital_basis_usd * self.target_fraction:
            raise ValueError("P29 target arithmetic is inconsistent")
        if self.desired_change_usd != self.target_exposure_usd - self.current_exposure_usd:
            raise ValueError("P31 signed difference is inconsistent")
        if self.requested_notional_usd <= 0 or self.requested_notional_usd != abs(self.desired_change_usd):
            raise ValueError("P31 requested notional is inconsistent")
        expected = "increase" if self.desired_change_usd > 0 else "decrease"
        if self.action != expected:
            raise ValueError("P31 action is inconsistent")


@dataclass(frozen=True, slots=True)
class CycleTargetStructuralRiskRuleResult:
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
    schema_version: int = CYCLE_TARGET_RISK_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != 1 or dict(LOCKED_RULES).get(self.rule_id) != self.evaluation_order or self.rule_version != "1":
            raise ValueError("P33 structural rule identity/order is invalid")
        for name in ("rule_name", "input_summary", "expected_condition"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        if not self.reason_codes:
            raise ValueError("P33 rule requires reason codes")
        object.__setattr__(self, "evaluated_at_utc", _utc(self.evaluated_at_utc, "evaluated_at_utc"))


@dataclass(frozen=True, slots=True)
class CycleTargetRiskReviewResult:
    review_result_id: UUID
    operation_id: UUID
    run_id: UUID
    stage_id: UUID
    source: CycleTargetRiskReviewInput
    safety_snapshot: RiskSafetyStateSnapshot
    status: CycleTargetRiskStatus
    rules: tuple[CycleTargetStructuralRiskRuleResult, ...]
    reason_codes: tuple[str, ...]
    warnings: tuple[str, ...]
    created_at_utc: datetime
    created_by: str
    reason: str
    software_version: str
    approved_notional_usd: None = None
    risk_approved_intent_id: None = None
    execution_allowed: bool = False
    live_allowed: bool = False
    gate_id: str = CYCLE_TARGET_RISK_GATE_ID
    gate_version: str = CYCLE_TARGET_RISK_GATE_VERSION
    schema_version: int = CYCLE_TARGET_RISK_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if (
            self.schema_version != 1 or self.gate_id != CYCLE_TARGET_RISK_GATE_ID
            or self.gate_version != CYCLE_TARGET_RISK_GATE_VERSION
            or self.execution_allowed or self.live_allowed
            or self.approved_notional_usd is not None or self.risk_approved_intent_id is not None
        ):
            raise ValueError("P33 cannot emit approved or executable evidence")
        expected = [name for name, _ in LOCKED_RULES]
        actual = [rule.rule_id for rule in self.rules]
        if self.status is CycleTargetRiskStatus.MANUAL_REVIEW_REQUIRED:
            if actual != expected or self.rules[-1].status is not StructuralRuleStatus.MANUAL_REVIEW:
                raise ValueError("P33 manual-review result requires three locked rules")
        elif self.status is CycleTargetRiskStatus.BLOCKED:
            if actual != expected[:2] or self.rules[-1].status is not StructuralRuleStatus.BLOCKED:
                raise ValueError("P33 blocked result requires two locked rules")
        else:
            raise ValueError("accepted P33 result must be manual-review or blocked")
        if any((rule.review_result_id, rule.run_id, rule.stage_id) != (self.review_result_id, self.run_id, self.stage_id) for rule in self.rules):
            raise ValueError("P33 rule parent identity is inconsistent")
        if not self.reason_codes:
            raise ValueError("P33 result requires reason codes")
        for name in ("created_by", "reason", "software_version"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        object.__setattr__(self, "created_at_utc", _utc(self.created_at_utc, "created_at_utc"))


@dataclass(frozen=True, slots=True)
class CycleTargetRiskOperationAttempt:
    attempt_id: UUID
    operation_id: UUID
    run_id: UUID
    decision_stage_id: UUID
    risk_stage_id: UUID | None
    command_fingerprint: str
    requested_intent_id: UUID
    requested_decision_result_id: UUID
    requested_decision_run_id: UUID
    status: CycleTargetRiskStatus
    requested_at_utc: datetime
    completed_at_utc: datetime
    session_id: str
    request_id: str
    created_by: str
    reason: str
    resolved_source: CycleTargetRiskReviewInput | None = None
    safety_snapshot: RiskSafetyStateSnapshot | None = None
    review_result_id: UUID | None = None
    error_code: str | None = None
    error_summary: str | None = None
    execution_allowed: bool = False
    live_allowed: bool = False
    schema_version: int = CYCLE_TARGET_RISK_SCHEMA_VERSION

    def __post_init__(self) -> None:
        accepted = self.status in {CycleTargetRiskStatus.MANUAL_REVIEW_REQUIRED, CycleTargetRiskStatus.BLOCKED}
        if self.schema_version != 1 or self.execution_allowed or self.live_allowed:
            raise ValueError("P33 operation safety metadata is invalid")
        if accepted:
            if None in (self.risk_stage_id, self.resolved_source, self.safety_snapshot, self.review_result_id):
                raise ValueError("completed P33 operation requires resolved evidence")
            if self.error_code is not None or self.error_summary is not None:
                raise ValueError("completed P33 operation cannot contain an error")
        elif not self.error_code or not self.error_summary:
            raise ValueError("failed P33 operation requires error evidence")
        if self.resolved_source is not None and (
            self.resolved_source.intent_id != self.requested_intent_id
            or self.resolved_source.decision_result_id != self.requested_decision_result_id
            or self.resolved_source.decision_run_id != self.requested_decision_run_id
        ):
            raise ValueError("resolved P33 source does not match requested IDs")
        object.__setattr__(self, "command_fingerprint", _text(self.command_fingerprint, "command_fingerprint"))
        for name in ("requested_at_utc", "completed_at_utc"):
            object.__setattr__(self, name, _utc(getattr(self, name), name))
        for name in ("session_id", "request_id", "created_by", "reason"):
            object.__setattr__(self, name, _text(getattr(self, name), name))

    def matches_command(self, command: CycleTargetRiskReviewCommand) -> bool:
        return self.command_fingerprint == command.command_fingerprint


@dataclass(frozen=True, slots=True)
class CycleTargetRiskSourceLink:
    source_link_id: UUID
    operation_id: UUID
    review_result_id: UUID
    risk_run_id: UUID
    risk_stage_id: UUID
    decision_result_id: UUID
    intent_id: UUID
    decision_run_id: UUID
    source_result_id: UUID
    source_run_id: UUID
    source_reversal_result_id: UUID
    source_reversal_run_id: UUID
    source_reversal_step_id: UUID
    source_formula_definition_id: UUID
    source_configuration_id: UUID
    created_at_utc: datetime
    schema_version: int = CYCLE_TARGET_RISK_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("unsupported P33 source-link schema")
        object.__setattr__(self, "created_at_utc", _utc(self.created_at_utc, "created_at_utc"))


@dataclass(frozen=True, slots=True)
class CycleTargetRiskReviewOutcome:
    attempt_id: UUID
    operation_id: UUID
    run_id: UUID
    status: CycleTargetRiskStatus
    summary: str
    decision_run_id: UUID | None = None
    source_run_id: UUID | None = None
    source_reversal_run_id: UUID | None = None
    review_result_id: UUID | None = None
    error_code: str | None = None


@dataclass(frozen=True, slots=True)
class CycleTargetRiskQuery:
    symbol: str | None = None
    action: str | None = None
    status: CycleTargetRiskStatus | None = None
    intent_id: UUID | None = None
    decision_result_id: UUID | None = None
    decision_run_id: UUID | None = None
    source_result_id: UUID | None = None
    source_run_id: UUID | None = None
    source_session_from: date | None = None
    source_session_to: date | None = None
    created_from_utc: datetime | None = None
    created_to_utc: datetime | None = None
    limit: int = 500

    def __post_init__(self) -> None:
        if not 1 <= self.limit <= 5000:
            raise ValueError("P33 query limit must be within 1..5000")
        if self.symbol is not None:
            object.__setattr__(self, "symbol", _text(self.symbol, "symbol").upper())
        if self.action is not None and self.action not in {"increase", "decrease"}:
            raise ValueError("P33 query action is invalid")
        for name in ("created_from_utc", "created_to_utc"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, _utc(value, name))


@dataclass(frozen=True, slots=True)
class CycleTargetRiskReplayReport:
    review_result_id: UUID
    matched: bool
    differences: tuple[str, ...]


__all__ = [name for name in globals() if name.startswith("CycleTarget") or name.startswith("CYCLE_TARGET")]
