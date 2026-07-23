"""Type-distinct numerical Risk preview contracts for one asset exposure cap."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from uuid import UUID

from .errors import RiskContractError
from .target_adjustment_models import (
    GATE_ID,
    GATE_VERSION,
    LOCKED_RULES,
    LinkedTargetRiskReviewInput,
    RiskSafetyStateSnapshot,
)


EXPOSURE_CAP_SCHEMA_VERSION = 1
EXPOSURE_CAP_COMPONENT_ID = "risk.target_adjustment_single_asset_exposure_cap_preview"
EXPOSURE_CAP_COMPONENT_VERSION = "1.0.0"
EXPOSURE_CAP_RULE_ID = "MAX_TARGET_EXPOSURE_USD"
EXPOSURE_CAP_RULE_VERSION = "1"
ZERO = Decimal("0")


def _text(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RiskContractError(f"{name} must not be empty")
    return value.strip()


def _utc(value: datetime, name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise RiskContractError(f"{name} must include a timezone")
    return value.astimezone(UTC)


def _decimal(value: Decimal, name: str) -> Decimal:
    if not isinstance(value, Decimal) or not value.is_finite():
        raise RiskContractError(f"{name} must be a finite Decimal")
    return value


def decimal_text(value: str, name: str) -> Decimal:
    if not isinstance(value, str) or not value.strip():
        raise RiskContractError(f"{name} must be a Decimal text value")
    try:
        parsed = Decimal(value.strip())
    except InvalidOperation as exc:
        raise RiskContractError(f"{name} must be valid Decimal text") from exc
    return _decimal(parsed, name)


class ExposureCapDefinitionStatus(StrEnum):
    SAVED = "saved"
    ARCHIVED = "archived"


class ExposureCapOperationType(StrEnum):
    DEFINITION_SAVE = "definition_save"
    DEFINITION_ARCHIVE = "definition_archive"
    PREVIEW = "preview"


class ExposureCapOperationStatus(StrEnum):
    COMPLETED = "completed"
    BLOCKED = "blocked"
    INVALID_INPUT = "invalid_input"
    FAILED = "failed"


class ExposureCapRuleOutcome(StrEnum):
    PASSED_WITHIN_CAP = "passed_within_cap"
    REDUCED_TO_CAP = "reduced_to_cap"
    BLOCKED_NO_INCREASE_CAPACITY = "blocked_no_increase_capacity"
    PRESERVED_RISK_REDUCING_DIRECTION = "preserved_risk_reducing_direction"


class ExposureCapDisposition(StrEnum):
    MANUAL_REVIEW_REQUIRED = "manual_review_required"
    BLOCKED_BY_EXPOSURE_CAP = "blocked_by_exposure_cap"


@dataclass(frozen=True, slots=True)
class SaveSingleAssetExposureCapDefinitionCommand:
    symbol: str
    max_target_exposure_usd: str
    reason: str
    session_id: str
    request_id: str
    created_by: str
    requested_at_utc: datetime
    definition_id: UUID | None = None
    predecessor_version: int | None = None
    operation_id: UUID | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "symbol", _text(self.symbol, "symbol").upper())
        for name in ("max_target_exposure_usd", "reason", "session_id", "request_id", "created_by"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        object.__setattr__(self, "requested_at_utc", _utc(self.requested_at_utc, "requested_at_utc"))
        if (self.definition_id is None) != (self.predecessor_version is None):
            raise RiskContractError("definition_id and predecessor_version must be supplied together")
        if self.predecessor_version is not None and self.predecessor_version < 1:
            raise RiskContractError("predecessor_version must be positive")


@dataclass(frozen=True, slots=True)
class ArchiveSingleAssetExposureCapDefinitionCommand:
    definition_id: UUID
    predecessor_version: int
    reason: str
    session_id: str
    request_id: str
    created_by: str
    requested_at_utc: datetime
    operation_id: UUID | None = None

    def __post_init__(self) -> None:
        if self.predecessor_version < 1:
            raise RiskContractError("predecessor_version must be positive")
        for name in ("reason", "session_id", "request_id", "created_by"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        object.__setattr__(self, "requested_at_utc", _utc(self.requested_at_utc, "requested_at_utc"))


@dataclass(frozen=True, slots=True)
class TargetAdjustmentExposureCapPreviewCommand:
    target_adjustment_risk_review_result_id: UUID
    exposure_cap_definition_id: UUID
    exposure_cap_definition_version: int
    reason: str
    session_id: str
    request_id: str
    created_by: str
    requested_at_utc: datetime
    operation_id: UUID | None = None

    def __post_init__(self) -> None:
        if self.exposure_cap_definition_version < 1:
            raise RiskContractError("exposure_cap_definition_version must be positive")
        for name in ("reason", "session_id", "request_id", "created_by"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        object.__setattr__(self, "requested_at_utc", _utc(self.requested_at_utc, "requested_at_utc"))


@dataclass(frozen=True, slots=True)
class SingleAssetExposureCapDefinitionVersion:
    definition_id: UUID
    definition_version: int
    predecessor_version: int | None
    symbol: str
    max_target_exposure_usd: Decimal
    status: ExposureCapDefinitionStatus
    reason: str
    created_by: str
    created_at_utc: datetime
    software_version: str
    currency: str = "USD"
    schema_version: int = EXPOSURE_CAP_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != EXPOSURE_CAP_SCHEMA_VERSION or self.currency != "USD":
            raise RiskContractError("unsupported exposure-cap definition schema or currency")
        if self.definition_version < 1:
            raise RiskContractError("definition_version must be positive")
        expected_predecessor = None if self.definition_version == 1 else self.definition_version - 1
        if self.predecessor_version != expected_predecessor:
            raise RiskContractError("definition predecessor/version chain is invalid")
        if not isinstance(self.status, ExposureCapDefinitionStatus):
            raise RiskContractError("definition status is invalid")
        object.__setattr__(self, "symbol", _text(self.symbol, "symbol").upper())
        cap = _decimal(self.max_target_exposure_usd, "max_target_exposure_usd")
        if cap <= ZERO:
            raise RiskContractError("max_target_exposure_usd must be positive")
        object.__setattr__(self, "max_target_exposure_usd", cap)
        for name in ("reason", "created_by", "software_version"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        object.__setattr__(self, "created_at_utc", _utc(self.created_at_utc, "created_at_utc"))


@dataclass(frozen=True, slots=True)
class LinkedExposureCapPreviewInput:
    phase6a_review_result_id: UUID
    phase6a_operation_id: UUID
    phase6a_run_id: UUID
    phase6a_stage_id: UUID
    phase6a_gate_id: str
    phase6a_gate_version: str
    phase6a_created_at_utc: datetime
    phase6a_source: LinkedTargetRiskReviewInput
    phase6a_safety_snapshot: RiskSafetyStateSnapshot
    phase6a_rule_evidence: tuple[tuple[str, str, str], ...]
    definition: SingleAssetExposureCapDefinitionVersion
    current_safety_snapshot: RiskSafetyStateSnapshot
    schema_version: int = EXPOSURE_CAP_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != EXPOSURE_CAP_SCHEMA_VERSION:
            raise RiskContractError("unsupported exposure-cap linked-input schema")
        if self.phase6a_gate_id != GATE_ID or self.phase6a_gate_version != GATE_VERSION:
            raise RiskContractError("Phase 6A gate identity is incompatible")
        expected = (
            (LOCKED_RULES[0][0], "1", "passed"),
            (LOCKED_RULES[1][0], "1", "passed"),
            (LOCKED_RULES[2][0], "1", "manual_review"),
        )
        if self.phase6a_rule_evidence != expected:
            raise RiskContractError("Phase 6A manual-review rule evidence is incompatible")
        if self.definition.status is not ExposureCapDefinitionStatus.SAVED:
            raise RiskContractError("archived exposure-cap definition cannot be previewed")
        if self.definition.symbol != self.phase6a_source.symbol:
            raise RiskContractError("exposure-cap definition symbol does not match Phase 6A source")
        object.__setattr__(self, "phase6a_created_at_utc", _utc(self.phase6a_created_at_utc, "phase6a_created_at_utc"))

    @property
    def symbol(self) -> str:
        return self.phase6a_source.symbol

    @property
    def action(self) -> str:
        return self.phase6a_source.action

    @property
    def as_of_utc(self) -> datetime:
        return self.phase6a_source.as_of_utc


@dataclass(frozen=True, slots=True)
class ExposureCapRuleResult:
    rule_result_id: UUID
    preview_result_id: UUID
    run_id: UUID
    stage_id: UUID
    action: str
    current_exposure_usd: Decimal
    target_exposure_usd: Decimal
    original_requested_notional_usd: Decimal
    max_target_exposure_usd: Decimal
    cap_constrained_candidate_notional_usd: Decimal
    reduction_usd: Decimal
    outcome: ExposureCapRuleOutcome
    reason_codes: tuple[str, ...]
    evaluated_at_utc: datetime
    stop_processing: bool = True
    rule_id: str = EXPOSURE_CAP_RULE_ID
    rule_version: str = EXPOSURE_CAP_RULE_VERSION
    evaluation_order: int = 1
    schema_version: int = EXPOSURE_CAP_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if (
            self.schema_version != EXPOSURE_CAP_SCHEMA_VERSION
            or self.rule_id != EXPOSURE_CAP_RULE_ID
            or self.rule_version != EXPOSURE_CAP_RULE_VERSION
            or self.evaluation_order != 1
        ):
            raise RiskContractError("exposure-cap rule identity/order is invalid")
        if self.action not in {"increase", "decrease"}:
            raise RiskContractError("exposure-cap rule action is invalid")
        for name in (
            "current_exposure_usd", "target_exposure_usd",
            "original_requested_notional_usd", "max_target_exposure_usd",
            "cap_constrained_candidate_notional_usd", "reduction_usd",
        ):
            object.__setattr__(self, name, _decimal(getattr(self, name), name))
        current, target = self.current_exposure_usd, self.target_exposure_usd
        original, cap = self.original_requested_notional_usd, self.max_target_exposure_usd
        candidate, reduction = self.cap_constrained_candidate_notional_usd, self.reduction_usd
        if current < ZERO or target < ZERO or original <= ZERO or cap <= ZERO:
            raise RiskContractError("exposure-cap rule money inputs are invalid")
        if original != abs(target - current):
            raise RiskContractError("original requested notional is inconsistent")
        if not ZERO <= candidate <= original or reduction != original - candidate:
            raise RiskContractError("exposure-cap rule violates non-expansion")
        expected_outcome: ExposureCapRuleOutcome
        expected_candidate: Decimal
        if self.action == "increase":
            if target <= current:
                raise RiskContractError("increase source direction is inconsistent")
            if target <= cap:
                expected_candidate, expected_outcome = original, ExposureCapRuleOutcome.PASSED_WITHIN_CAP
            elif current < cap:
                expected_candidate, expected_outcome = cap - current, ExposureCapRuleOutcome.REDUCED_TO_CAP
            else:
                expected_candidate, expected_outcome = ZERO, ExposureCapRuleOutcome.BLOCKED_NO_INCREASE_CAPACITY
        else:
            if target >= current:
                raise RiskContractError("decrease source direction is inconsistent")
            expected_candidate = original
            expected_outcome = ExposureCapRuleOutcome.PRESERVED_RISK_REDUCING_DIRECTION
        if candidate != expected_candidate or self.outcome is not expected_outcome:
            raise RiskContractError("exposure-cap rule output is inconsistent with the locked formula")
        if not self.reason_codes:
            raise RiskContractError("exposure-cap rule requires reason codes")
        object.__setattr__(self, "evaluated_at_utc", _utc(self.evaluated_at_utc, "evaluated_at_utc"))


@dataclass(frozen=True, slots=True)
class TargetAdjustmentExposureCapPreviewResult:
    preview_result_id: UUID
    operation_id: UUID
    run_id: UUID
    stage_id: UUID
    source: LinkedExposureCapPreviewInput
    rule: ExposureCapRuleResult
    disposition: ExposureCapDisposition
    reason_codes: tuple[str, ...]
    warnings: tuple[str, ...]
    created_at_utc: datetime
    created_by: str
    reason: str
    software_version: str
    component_id: str = EXPOSURE_CAP_COMPONENT_ID
    component_version: str = EXPOSURE_CAP_COMPONENT_VERSION
    schema_version: int = EXPOSURE_CAP_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if (
            self.schema_version != EXPOSURE_CAP_SCHEMA_VERSION
            or self.component_id != EXPOSURE_CAP_COMPONENT_ID
            or self.component_version != EXPOSURE_CAP_COMPONENT_VERSION
        ):
            raise RiskContractError("unsupported exposure-cap preview identity")
        if (
            self.rule.preview_result_id != self.preview_result_id
            or self.rule.run_id != self.run_id
            or self.rule.stage_id != self.stage_id
        ):
            raise RiskContractError("exposure-cap rule/result parent identity is inconsistent")
        candidate = self.rule.cap_constrained_candidate_notional_usd
        expected = (
            ExposureCapDisposition.BLOCKED_BY_EXPOSURE_CAP
            if candidate == ZERO
            else ExposureCapDisposition.MANUAL_REVIEW_REQUIRED
        )
        if self.disposition is not expected:
            raise RiskContractError("exposure-cap final disposition is inconsistent")
        if candidate == ZERO and self.rule.outcome is not ExposureCapRuleOutcome.BLOCKED_NO_INCREASE_CAPACITY:
            raise RiskContractError("only an increase without capacity can produce zero candidate")
        if not self.reason_codes:
            raise RiskContractError("exposure-cap result requires reason codes")
        for name in ("created_by", "reason", "software_version"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        object.__setattr__(self, "created_at_utc", _utc(self.created_at_utc, "created_at_utc"))

    @property
    def cap_constrained_candidate_notional_usd(self) -> Decimal:
        return self.rule.cap_constrained_candidate_notional_usd


@dataclass(frozen=True, slots=True)
class ExposureCapOperationAttempt:
    attempt_id: UUID
    operation_id: UUID
    operation_type: ExposureCapOperationType
    status: ExposureCapOperationStatus
    run_id: UUID
    stage_id: UUID
    requested_at_utc: datetime
    completed_at_utc: datetime
    session_id: str
    request_id: str
    created_by: str
    reason: str
    requested_review_result_id: UUID | None = None
    requested_definition_id: UUID | None = None
    requested_definition_version: int | None = None
    requested_symbol: str | None = None
    requested_max_target_exposure_usd_text: str | None = None
    resolved_definition_id: UUID | None = None
    resolved_definition_version: int | None = None
    resolved_source: LinkedExposureCapPreviewInput | None = None
    current_safety_snapshot: RiskSafetyStateSnapshot | None = None
    preview_result_id: UUID | None = None
    disposition: ExposureCapDisposition | None = None
    error_code: str | None = None
    error_summary: str | None = None
    schema_version: int = EXPOSURE_CAP_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != EXPOSURE_CAP_SCHEMA_VERSION:
            raise RiskContractError("unsupported exposure-cap operation schema")
        if not isinstance(self.operation_type, ExposureCapOperationType) or not isinstance(self.status, ExposureCapOperationStatus):
            raise RiskContractError("exposure-cap operation type/status is invalid")
        if self.status is ExposureCapOperationStatus.COMPLETED:
            if self.error_code is not None or self.error_summary is not None:
                raise RiskContractError("completed exposure-cap operation cannot contain an error")
            if self.operation_type is ExposureCapOperationType.PREVIEW:
                if None in (self.resolved_source, self.preview_result_id, self.disposition):
                    raise RiskContractError("completed preview operation requires result evidence")
            elif None in (self.resolved_definition_id, self.resolved_definition_version):
                raise RiskContractError("completed definition operation requires a definition version")
        else:
            if not self.error_code or not self.error_summary:
                raise RiskContractError("non-completed exposure-cap operation requires error evidence")
            if self.preview_result_id is not None or self.disposition is not None:
                raise RiskContractError("non-completed operation cannot contain preview result evidence")
        for name in ("requested_at_utc", "completed_at_utc"):
            object.__setattr__(self, name, _utc(getattr(self, name), name))
        for name in ("session_id", "request_id", "created_by", "reason"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        if self.requested_symbol is not None:
            object.__setattr__(self, "requested_symbol", _text(self.requested_symbol, "requested_symbol").upper())

    def matches_command(self, command: object) -> bool:
        common = (
            self.session_id == getattr(command, "session_id", None)
            and self.request_id == getattr(command, "request_id", None)
            and self.created_by == getattr(command, "created_by", None)
            and self.reason == getattr(command, "reason", None)
        )
        if isinstance(command, SaveSingleAssetExposureCapDefinitionCommand):
            return common and self.operation_type is ExposureCapOperationType.DEFINITION_SAVE and (
                self.requested_definition_id == command.definition_id
                and self.requested_definition_version == command.predecessor_version
                and self.requested_symbol == command.symbol
                and self.requested_max_target_exposure_usd_text == command.max_target_exposure_usd
            )
        if isinstance(command, ArchiveSingleAssetExposureCapDefinitionCommand):
            return common and self.operation_type is ExposureCapOperationType.DEFINITION_ARCHIVE and (
                self.requested_definition_id == command.definition_id
                and self.requested_definition_version == command.predecessor_version
            )
        if isinstance(command, TargetAdjustmentExposureCapPreviewCommand):
            return common and self.operation_type is ExposureCapOperationType.PREVIEW and (
                self.requested_review_result_id == command.target_adjustment_risk_review_result_id
                and self.requested_definition_id == command.exposure_cap_definition_id
                and self.requested_definition_version == command.exposure_cap_definition_version
            )
        return False


@dataclass(frozen=True, slots=True)
class ExposureCapSourceLink:
    source_link_id: UUID
    operation_id: UUID
    preview_result_id: UUID
    exposure_cap_run_id: UUID
    exposure_cap_stage_id: UUID
    phase6a_review_result_id: UUID
    phase6a_run_id: UUID
    phase6a_stage_id: UUID
    decision_run_id: UUID
    linked_parent_run_id: UUID
    target_child_run_id: UUID
    standardized_state_run_id: UUID
    decision_result_id: UUID
    intent_id: UUID
    target_position_link_id: UUID
    target_calculation_id: UUID
    standardized_state_calculation_id: UUID
    created_at_utc: datetime
    schema_version: int = EXPOSURE_CAP_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != EXPOSURE_CAP_SCHEMA_VERSION:
            raise RiskContractError("unsupported exposure-cap source-link schema")
        object.__setattr__(self, "created_at_utc", _utc(self.created_at_utc, "created_at_utc"))


@dataclass(frozen=True, slots=True)
class ExposureCapOperationOutcome:
    attempt_id: UUID
    operation_id: UUID
    run_id: UUID
    status: ExposureCapOperationStatus
    summary: str
    definition_id: UUID | None = None
    definition_version: int | None = None
    preview_result_id: UUID | None = None
    disposition: ExposureCapDisposition | None = None
    phase6a_run_id: UUID | None = None
    decision_run_id: UUID | None = None
    linked_parent_run_id: UUID | None = None
    target_child_run_id: UUID | None = None
    standardized_state_run_id: UUID | None = None
    error_code: str | None = None


@dataclass(frozen=True, slots=True)
class ExposureCapDefinitionQuery:
    symbol: str | None = None
    status: ExposureCapDefinitionStatus | None = None
    current_only: bool = False
    limit: int = 500

    def __post_init__(self) -> None:
        if not 1 <= self.limit <= 5000:
            raise RiskContractError("definition query limit must be within 1..5000")
        if self.symbol is not None:
            object.__setattr__(self, "symbol", _text(self.symbol, "symbol").upper())


@dataclass(frozen=True, slots=True)
class ExposureCapResultQuery:
    symbol: str | None = None
    action: str | None = None
    definition_id: UUID | None = None
    definition_version: int | None = None
    disposition: ExposureCapDisposition | None = None
    rule_outcome: ExposureCapRuleOutcome | None = None
    as_of_from_utc: datetime | None = None
    as_of_to_utc: datetime | None = None
    limit: int = 500

    def __post_init__(self) -> None:
        if not 1 <= self.limit <= 5000:
            raise RiskContractError("result query limit must be within 1..5000")
        if self.symbol is not None:
            object.__setattr__(self, "symbol", _text(self.symbol, "symbol").upper())
        if self.action is not None and self.action not in {"increase", "decrease"}:
            raise RiskContractError("result query action is invalid")
        if self.definition_version is not None and self.definition_version < 1:
            raise RiskContractError("result query definition version must be positive")
        for name in ("as_of_from_utc", "as_of_to_utc"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, _utc(value, name))


@dataclass(frozen=True, slots=True)
class ExposureCapOperationQuery:
    operation_type: ExposureCapOperationType | None = None
    status: ExposureCapOperationStatus | None = None
    symbol: str | None = None
    limit: int = 500

    def __post_init__(self) -> None:
        if not 1 <= self.limit <= 5000:
            raise RiskContractError("operation query limit must be within 1..5000")
        if self.symbol is not None:
            object.__setattr__(self, "symbol", _text(self.symbol, "symbol").upper())


__all__ = [
    name for name in globals()
    if name.startswith("ExposureCap")
    or name.startswith("SingleAsset")
    or name.startswith("SaveSingle")
    or name.startswith("ArchiveSingle")
    or name.startswith("TargetAdjustmentExposure")
    or name.startswith("LinkedExposure")
    or name.startswith("EXPOSURE_CAP")
]
