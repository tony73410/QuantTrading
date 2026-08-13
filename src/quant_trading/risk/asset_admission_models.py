"""P23-4C1 contracts for frozen-asset admission of one exact P33 review."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from .target_adjustment_models import StructuralRuleSeverity, StructuralRuleStatus


ASSET_ADMISSION_SCHEMA_VERSION = 1
ASSET_ADMISSION_COMPONENT_ID = "risk.cycle_target_asset_admission.p23_4c1.v1"
ASSET_ADMISSION_COMPONENT_VERSION = "1.0.0"
ASSET_ADMISSION_CONTROL_COMPONENT_ID = "asset_state.trading_control.p23_4c1.v1"
ASSET_ADMISSION_CONTROL_COMPONENT_VERSION = "1.0.0"
ASSET_ADMISSION_CONTROL_CALENDAR_DEFINITION_ID = "US_EQUITIES_REGULAR_V1"
ASSET_ADMISSION_LOCKED_RULES = (
    ("P33_STRUCTURAL_REVIEW_INTEGRITY", 1),
    ("ASSET_TRADING_CONTROL_AVAILABILITY", 2),
    ("FROZEN_ASSET_BLOCK", 3),
)


def _text(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must not be empty")
    return value.strip()


def _utc(value: datetime, name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must include a timezone")
    return value.astimezone(UTC)


class CycleTargetAssetAdmissionStatus(StrEnum):
    MANUAL_REVIEW_REQUIRED = "manual_review_required"
    BLOCKED_FROZEN_ASSET = "blocked_frozen_asset"
    BLOCKED_MISSING_TRADING_CONTROL = "blocked_missing_trading_control"
    BLOCKED_INVALID_SOURCE = "blocked_invalid_source"
    INVALID_INPUT = "invalid_input"
    FAILED = "failed"

    @property
    def accepted(self) -> bool:
        return self not in {self.INVALID_INPUT, self.FAILED}

    @property
    def blocked(self) -> bool:
        return self in {
            self.BLOCKED_FROZEN_ASSET, self.BLOCKED_MISSING_TRADING_CONTROL,
            self.BLOCKED_INVALID_SOURCE,
        }


@dataclass(frozen=True, slots=True)
class CycleTargetAssetAdmissionReviewCommand:
    p33_result_id: UUID
    p33_run_id: UUID
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
        payload = {
            "p33_result_id": str(self.p33_result_id), "p33_run_id": str(self.p33_run_id),
            "reason": self.reason, "session_id": self.session_id,
            "request_id": self.request_id, "created_by": self.created_by,
            "requested_at_utc": self.requested_at_utc.isoformat(),
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class CycleTargetAssetAdmissionSource:
    p33_result_id: UUID
    p33_operation_id: UUID
    p33_run_id: UUID
    p33_stage_id: UUID
    p33_status: str
    p33_gate_id: str
    p33_gate_version: str
    p33_created_at_utc: datetime
    p33_reason_codes: tuple[str, ...]
    p31_decision_result_id: UUID
    p31_intent_id: UUID
    p31_run_id: UUID
    p29_result_id: UUID
    p29_run_id: UUID
    p28_result_id: UUID
    p28_run_id: UUID
    p28_step_id: UUID
    symbol: str
    source_session: date
    action: str
    requested_notional_usd: Decimal
    execution_allowed: bool = False
    live_allowed: bool = False
    schema_version: int = ASSET_ADMISSION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != 1 or self.execution_allowed or self.live_allowed:
            raise ValueError("P35 source must remain non-executable schema v1")
        for name in ("p33_status", "p33_gate_id", "p33_gate_version", "symbol", "action"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        object.__setattr__(self, "symbol", self.symbol.upper())
        if self.action not in {"increase", "decrease"}:
            raise ValueError("P35 source action is invalid")
        if not isinstance(self.requested_notional_usd, Decimal) or not self.requested_notional_usd.is_finite() or self.requested_notional_usd <= 0:
            raise ValueError("P35 source requested notional must be a positive Decimal")
        object.__setattr__(self, "p33_created_at_utc", _utc(self.p33_created_at_utc, "p33_created_at_utc"))


@dataclass(frozen=True, slots=True)
class AssetTradingControlEvidence:
    event_id: UUID
    operation_id: UUID
    run_id: UUID
    stage_id: UUID
    predecessor_event_id: UUID | None
    symbol: str
    status: str
    requested_at_utc: datetime
    effective_at_utc: datetime
    effective_session: date
    component_id: str
    component_version: str
    mapping_id: UUID
    mapping_version: int
    calendar_definition_id: str
    calendar_snapshot_id: UUID
    schedule_fingerprint: str
    execution_allowed: bool = False
    live_allowed: bool = False
    schema_version: int = ASSET_ADMISSION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != 1 or self.execution_allowed or self.live_allowed:
            raise ValueError("P35 trading-control evidence must remain non-executable v1")
        for name in ("symbol", "status", "component_id", "component_version", "calendar_definition_id", "schedule_fingerprint"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        object.__setattr__(self, "symbol", self.symbol.upper())
        if self.status not in {"eligible", "frozen"}:
            raise ValueError("P35 control status is invalid")
        if self.mapping_version < 1:
            raise ValueError("P35 mapping version must be positive")
        for name in ("requested_at_utc", "effective_at_utc"):
            object.__setattr__(self, name, _utc(getattr(self, name), name))


@dataclass(frozen=True, slots=True)
class CycleTargetAssetAdmissionRuleResult:
    rule_result_id: UUID
    result_id: UUID
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
    schema_version: int = ASSET_ADMISSION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != 1 or dict(ASSET_ADMISSION_LOCKED_RULES).get(self.rule_id) != self.evaluation_order or self.rule_version != "1":
            raise ValueError("P35 locked rule identity/order is invalid")
        for name in ("rule_name", "input_summary", "expected_condition"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        if not self.reason_codes:
            raise ValueError("P35 rule requires reason codes")
        object.__setattr__(self, "evaluated_at_utc", _utc(self.evaluated_at_utc, "evaluated_at_utc"))


@dataclass(frozen=True, slots=True)
class CycleTargetAssetAdmissionReviewResult:
    result_id: UUID
    operation_id: UUID
    run_id: UUID
    stage_id: UUID
    source: CycleTargetAssetAdmissionSource
    control: AssetTradingControlEvidence | None
    status: CycleTargetAssetAdmissionStatus
    rules: tuple[CycleTargetAssetAdmissionRuleResult, ...]
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
    gate_id: str = ASSET_ADMISSION_COMPONENT_ID
    gate_version: str = ASSET_ADMISSION_COMPONENT_VERSION
    schema_version: int = ASSET_ADMISSION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if (
            self.schema_version != 1 or self.gate_id != ASSET_ADMISSION_COMPONENT_ID
            or self.gate_version != ASSET_ADMISSION_COMPONENT_VERSION
            or self.execution_allowed or self.live_allowed
            or self.approved_notional_usd is not None or self.risk_approved_intent_id is not None
            or not self.status.accepted
        ):
            raise ValueError("P35 cannot emit approved/executable evidence")
        if self.status is CycleTargetAssetAdmissionStatus.BLOCKED_INVALID_SOURCE:
            expected_count = len(self.rules)
            if expected_count not in {1, 2}:
                raise ValueError("invalid-source P35 result must stop at rule 1 or rule 2")
        else:
            expected_count = {
                CycleTargetAssetAdmissionStatus.BLOCKED_MISSING_TRADING_CONTROL: 2,
                CycleTargetAssetAdmissionStatus.BLOCKED_FROZEN_ASSET: 3,
                CycleTargetAssetAdmissionStatus.MANUAL_REVIEW_REQUIRED: 3,
            }[self.status]
        if tuple(rule.rule_id for rule in self.rules) != tuple(name for name, _ in ASSET_ADMISSION_LOCKED_RULES[:expected_count]):
            raise ValueError("P35 result does not contain the expected locked rule prefix")
        if any((rule.result_id, rule.run_id, rule.stage_id) != (self.result_id, self.run_id, self.stage_id) for rule in self.rules):
            raise ValueError("P35 rule parent identity is inconsistent")
        if not self.reason_codes:
            raise ValueError("P35 result requires reason codes")
        for name in ("created_by", "reason", "software_version"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        object.__setattr__(self, "created_at_utc", _utc(self.created_at_utc, "created_at_utc"))


@dataclass(frozen=True, slots=True)
class CycleTargetAssetAdmissionOperationAttempt:
    attempt_id: UUID
    operation_id: UUID
    run_id: UUID
    state_stage_id: UUID
    risk_stage_id: UUID | None
    command_fingerprint: str
    requested_p33_result_id: UUID
    requested_p33_run_id: UUID
    status: CycleTargetAssetAdmissionStatus
    requested_at_utc: datetime
    completed_at_utc: datetime
    session_id: str
    request_id: str
    created_by: str
    reason: str
    resolved_symbol: str | None = None
    result_id: UUID | None = None
    error_code: str | None = None
    error_summary: str | None = None
    execution_allowed: bool = False
    live_allowed: bool = False
    schema_version: int = ASSET_ADMISSION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != 1 or self.execution_allowed or self.live_allowed:
            raise ValueError("P35 operation safety metadata is invalid")
        if self.status.accepted:
            if self.risk_stage_id is None or self.result_id is None or self.resolved_symbol is None or self.error_code is not None or self.error_summary is not None:
                raise ValueError("completed P35 operation requires result evidence")
        elif self.result_id is not None or not self.error_code or not self.error_summary:
            raise ValueError("failed P35 operation requires error evidence")
        object.__setattr__(self, "command_fingerprint", _text(self.command_fingerprint, "command_fingerprint"))
        if self.resolved_symbol is not None:
            object.__setattr__(self, "resolved_symbol", _text(self.resolved_symbol, "resolved_symbol").upper())
        for name in ("requested_at_utc", "completed_at_utc"):
            object.__setattr__(self, name, _utc(getattr(self, name), name))
        for name in ("session_id", "request_id", "created_by", "reason"):
            object.__setattr__(self, name, _text(getattr(self, name), name))

    def matches_command(self, command: CycleTargetAssetAdmissionReviewCommand) -> bool:
        return self.command_fingerprint == command.command_fingerprint


@dataclass(frozen=True, slots=True)
class CycleTargetAssetAdmissionSourceLink:
    source_link_id: UUID
    operation_id: UUID
    result_id: UUID
    admission_run_id: UUID
    admission_stage_id: UUID
    p33_result_id: UUID
    p33_run_id: UUID
    p31_decision_result_id: UUID
    p31_intent_id: UUID
    p29_result_id: UUID
    p28_result_id: UUID
    control_event_id: UUID | None
    control_run_id: UUID | None
    created_at_utc: datetime
    schema_version: int = ASSET_ADMISSION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != 1 or (self.control_event_id is None) != (self.control_run_id is None):
            raise ValueError("P35 source-link control identity is invalid")
        object.__setattr__(self, "created_at_utc", _utc(self.created_at_utc, "created_at_utc"))


@dataclass(frozen=True, slots=True)
class CycleTargetAssetAdmissionOutcome:
    attempt_id: UUID
    operation_id: UUID
    run_id: UUID
    status: CycleTargetAssetAdmissionStatus
    summary: str
    result_id: UUID | None = None
    p33_run_id: UUID | None = None
    control_run_id: UUID | None = None
    error_code: str | None = None


@dataclass(frozen=True, slots=True)
class CycleTargetAssetAdmissionQuery:
    symbol: str | None = None
    status: CycleTargetAssetAdmissionStatus | None = None
    p33_result_id: UUID | None = None
    p33_run_id: UUID | None = None
    control_event_id: UUID | None = None
    created_from_utc: datetime | None = None
    created_to_utc: datetime | None = None
    limit: int = 500

    def __post_init__(self) -> None:
        if not 1 <= self.limit <= 5000:
            raise ValueError("P35 query limit must be within 1..5000")
        if self.symbol is not None:
            object.__setattr__(self, "symbol", _text(self.symbol, "symbol").upper())
        for name in ("created_from_utc", "created_to_utc"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, _utc(value, name))


@dataclass(frozen=True, slots=True)
class CycleTargetAssetAdmissionReplayReport:
    result_id: UUID
    matched: bool
    differences: tuple[str, ...]


__all__ = [name for name in globals() if name.startswith("CycleTargetAsset") or name.startswith("AssetTrading") or name.startswith("ASSET_ADMISSION")]
