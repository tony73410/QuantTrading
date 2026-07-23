"""Type-distinct second-rule Risk preview contracts for research cash floors."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from uuid import UUID

from .errors import RiskContractError
from .exposure_cap_models import (
    ExposureCapDisposition,
    ExposureCapRuleOutcome,
    ExposureCapSourceLink,
    TargetAdjustmentExposureCapPreviewResult,
)
from .target_adjustment_models import RiskSafetyStateSnapshot


RESEARCH_CASH_FLOOR_SCHEMA_VERSION = 1
RESEARCH_CASH_FLOOR_COMPONENT_ID = (
    "risk.target_adjustment_research_asset_cash_floor_preview"
)
RESEARCH_CASH_FLOOR_COMPONENT_VERSION = "1.0.0"
RESEARCH_CASH_FLOOR_RULE_ID = "MIN_RESEARCH_ASSET_CASH_USD"
RESEARCH_CASH_FLOOR_RULE_VERSION = "1"
RESEARCH_CASH_FLOOR_RULE_ORDER = 2
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


def cash_floor_decimal_text(value: str, name: str) -> Decimal:
    if not isinstance(value, str) or not value.strip():
        raise RiskContractError(f"{name} must be a Decimal text value")
    try:
        parsed = Decimal(value.strip())
    except InvalidOperation as exc:
        raise RiskContractError(f"{name} must be valid Decimal text") from exc
    return _decimal(parsed, name)


class ResearchCashFloorDefinitionStatus(StrEnum):
    SAVED = "saved"
    ARCHIVED = "archived"


class ResearchCashFloorOperationType(StrEnum):
    DEFINITION_SAVE = "definition_save"
    DEFINITION_ARCHIVE = "definition_archive"
    PREVIEW = "preview"


class ResearchCashFloorOperationStatus(StrEnum):
    COMPLETED = "completed"
    BLOCKED = "blocked"
    INVALID_INPUT = "invalid_input"
    FAILED = "failed"


class ResearchCashFloorRuleOutcome(StrEnum):
    PASSED_AT_OR_ABOVE_CASH_FLOOR = "passed_at_or_above_cash_floor"
    REDUCED_TO_CASH_FLOOR = "reduced_to_cash_floor"
    BLOCKED_NO_RESEARCH_CASH_CAPACITY = "blocked_no_research_cash_capacity"
    PRESERVED_RESEARCH_CASH_INCREASING_DIRECTION = (
        "preserved_research_cash_increasing_direction"
    )


class ResearchCashFloorDisposition(StrEnum):
    MANUAL_REVIEW_REQUIRED = "manual_review_required"
    BLOCKED_BY_RESEARCH_CASH_FLOOR = "blocked_by_research_cash_floor"


@dataclass(frozen=True, slots=True)
class SaveResearchAssetCashFloorDefinitionCommand:
    symbol: str
    minimum_research_asset_cash_usd: str
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
        for name in (
            "minimum_research_asset_cash_usd",
            "reason",
            "session_id",
            "request_id",
            "created_by",
        ):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        object.__setattr__(
            self, "requested_at_utc", _utc(self.requested_at_utc, "requested_at_utc")
        )
        if (self.definition_id is None) != (self.predecessor_version is None):
            raise RiskContractError(
                "definition_id and predecessor_version must be supplied together"
            )
        if self.predecessor_version is not None and self.predecessor_version < 1:
            raise RiskContractError("predecessor_version must be positive")


@dataclass(frozen=True, slots=True)
class ArchiveResearchAssetCashFloorDefinitionCommand:
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
        object.__setattr__(
            self, "requested_at_utc", _utc(self.requested_at_utc, "requested_at_utc")
        )


@dataclass(frozen=True, slots=True)
class TargetAdjustmentResearchCashFloorPreviewCommand:
    target_adjustment_exposure_cap_preview_result_id: UUID
    research_cash_floor_definition_id: UUID
    research_cash_floor_definition_version: int
    reason: str
    session_id: str
    request_id: str
    created_by: str
    requested_at_utc: datetime
    operation_id: UUID | None = None

    def __post_init__(self) -> None:
        if self.research_cash_floor_definition_version < 1:
            raise RiskContractError(
                "research_cash_floor_definition_version must be positive"
            )
        for name in ("reason", "session_id", "request_id", "created_by"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        object.__setattr__(
            self, "requested_at_utc", _utc(self.requested_at_utc, "requested_at_utc")
        )


@dataclass(frozen=True, slots=True)
class ResearchAssetCashFloorDefinitionVersion:
    definition_id: UUID
    definition_version: int
    predecessor_version: int | None
    symbol: str
    minimum_research_asset_cash_usd: Decimal
    status: ResearchCashFloorDefinitionStatus
    reason: str
    created_by: str
    created_at_utc: datetime
    software_version: str
    currency: str = "USD"
    schema_version: int = RESEARCH_CASH_FLOOR_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != RESEARCH_CASH_FLOOR_SCHEMA_VERSION or self.currency != "USD":
            raise RiskContractError(
                "unsupported research cash-floor definition schema or currency"
            )
        if self.definition_version < 1:
            raise RiskContractError("definition_version must be positive")
        expected_predecessor = (
            None if self.definition_version == 1 else self.definition_version - 1
        )
        if self.predecessor_version != expected_predecessor:
            raise RiskContractError("definition predecessor/version chain is invalid")
        if not isinstance(self.status, ResearchCashFloorDefinitionStatus):
            raise RiskContractError("definition status is invalid")
        object.__setattr__(self, "symbol", _text(self.symbol, "symbol").upper())
        floor = _decimal(
            self.minimum_research_asset_cash_usd,
            "minimum_research_asset_cash_usd",
        )
        if floor < ZERO:
            raise RiskContractError(
                "minimum_research_asset_cash_usd must be non-negative"
            )
        object.__setattr__(self, "minimum_research_asset_cash_usd", floor)
        for name in ("reason", "created_by", "software_version"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        object.__setattr__(
            self, "created_at_utc", _utc(self.created_at_utc, "created_at_utc")
        )


@dataclass(frozen=True, slots=True)
class LinkedResearchCashFloorPreviewInput:
    phase6b_result: TargetAdjustmentExposureCapPreviewResult
    phase6b_source_link: ExposureCapSourceLink
    research_capital_basis_usd: Decimal
    target_result_created_at_utc: datetime
    target_result_schema_version: int
    definition: ResearchAssetCashFloorDefinitionVersion
    current_safety_snapshot: RiskSafetyStateSnapshot
    schema_version: int = RESEARCH_CASH_FLOOR_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != RESEARCH_CASH_FLOOR_SCHEMA_VERSION:
            raise RiskContractError("unsupported research cash-floor linked-input schema")
        if self.phase6b_result.disposition is not ExposureCapDisposition.MANUAL_REVIEW_REQUIRED:
            raise RiskContractError(
                "only a Phase 6B MANUAL_REVIEW_REQUIRED result is eligible"
            )
        if self.phase6b_result.cap_constrained_candidate_notional_usd <= ZERO:
            raise RiskContractError("Phase 6B candidate must be positive")
        link = self.phase6b_source_link
        if (
            link.preview_result_id != self.phase6b_result.preview_result_id
            or link.operation_id != self.phase6b_result.operation_id
            or link.exposure_cap_run_id != self.phase6b_result.run_id
            or link.exposure_cap_stage_id != self.phase6b_result.stage_id
            or link.target_calculation_id
            != self.phase6b_result.source.phase6a_source.target_calculation_id
        ):
            raise RiskContractError("Phase 6B result/source-link identity is inconsistent")
        basis = _decimal(self.research_capital_basis_usd, "research_capital_basis_usd")
        if basis < ZERO:
            raise RiskContractError("research_capital_basis_usd must be non-negative")
        object.__setattr__(self, "research_capital_basis_usd", basis)
        if self.target_result_schema_version != 1:
            raise RiskContractError("unsupported Target Position result schema")
        object.__setattr__(
            self,
            "target_result_created_at_utc",
            _utc(self.target_result_created_at_utc, "target_result_created_at_utc"),
        )
        if self.definition.status is not ResearchCashFloorDefinitionStatus.SAVED:
            raise RiskContractError("archived cash-floor definition cannot be previewed")
        if self.definition.symbol != self.symbol:
            raise RiskContractError(
                "cash-floor definition symbol does not match Phase 6B source"
            )

    @property
    def symbol(self) -> str:
        return self.phase6b_result.source.symbol

    @property
    def action(self) -> str:
        return self.phase6b_result.rule.action

    @property
    def as_of_utc(self) -> datetime:
        return self.phase6b_result.source.as_of_utc

    @property
    def phase6b_candidate_notional_usd(self) -> Decimal:
        return self.phase6b_result.cap_constrained_candidate_notional_usd


@dataclass(frozen=True, slots=True)
class ResearchCashFloorRuleResult:
    rule_result_id: UUID
    preview_result_id: UUID
    run_id: UUID
    stage_id: UUID
    action: str
    research_capital_basis_usd: Decimal
    current_exposure_usd: Decimal
    phase6b_candidate_notional_usd: Decimal
    minimum_research_asset_cash_usd: Decimal
    pre_action_research_cash_usd: Decimal
    cash_capacity_usd: Decimal
    cash_floor_constrained_candidate_notional_usd: Decimal
    post_action_research_cash_usd: Decimal
    remaining_shortfall_usd: Decimal
    reduction_usd: Decimal
    outcome: ResearchCashFloorRuleOutcome
    reason_codes: tuple[str, ...]
    evaluated_at_utc: datetime
    stop_processing: bool = True
    rule_id: str = RESEARCH_CASH_FLOOR_RULE_ID
    rule_version: str = RESEARCH_CASH_FLOOR_RULE_VERSION
    evaluation_order: int = RESEARCH_CASH_FLOOR_RULE_ORDER
    schema_version: int = RESEARCH_CASH_FLOOR_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if (
            self.schema_version != RESEARCH_CASH_FLOOR_SCHEMA_VERSION
            or self.rule_id != RESEARCH_CASH_FLOOR_RULE_ID
            or self.rule_version != RESEARCH_CASH_FLOOR_RULE_VERSION
            or self.evaluation_order != RESEARCH_CASH_FLOOR_RULE_ORDER
            or not self.stop_processing
        ):
            raise RiskContractError("research cash-floor rule identity/order is invalid")
        if self.action not in {"increase", "decrease"}:
            raise RiskContractError("research cash-floor action is invalid")
        for name in (
            "research_capital_basis_usd",
            "current_exposure_usd",
            "phase6b_candidate_notional_usd",
            "minimum_research_asset_cash_usd",
            "pre_action_research_cash_usd",
            "cash_capacity_usd",
            "cash_floor_constrained_candidate_notional_usd",
            "post_action_research_cash_usd",
            "remaining_shortfall_usd",
            "reduction_usd",
        ):
            object.__setattr__(self, name, _decimal(getattr(self, name), name))
        basis = self.research_capital_basis_usd
        current = self.current_exposure_usd
        source_candidate = self.phase6b_candidate_notional_usd
        floor = self.minimum_research_asset_cash_usd
        candidate = self.cash_floor_constrained_candidate_notional_usd
        if basis < ZERO or current < ZERO or source_candidate <= ZERO or floor < ZERO:
            raise RiskContractError("research cash-floor money inputs are invalid")
        expected_pre = basis - current
        expected_capacity = max(expected_pre - floor, ZERO)
        if self.action == "increase":
            expected_candidate = min(source_candidate, expected_capacity)
            expected_post = basis - (current + expected_candidate)
            if source_candidate <= expected_capacity:
                expected_outcome = (
                    ResearchCashFloorRuleOutcome.PASSED_AT_OR_ABOVE_CASH_FLOOR
                )
            elif expected_capacity > ZERO:
                expected_outcome = ResearchCashFloorRuleOutcome.REDUCED_TO_CASH_FLOOR
            else:
                expected_outcome = (
                    ResearchCashFloorRuleOutcome.BLOCKED_NO_RESEARCH_CASH_CAPACITY
                )
        else:
            expected_candidate = source_candidate
            expected_post = basis - (current - expected_candidate)
            expected_outcome = (
                ResearchCashFloorRuleOutcome.PRESERVED_RESEARCH_CASH_INCREASING_DIRECTION
            )
        expected_shortfall = max(floor - expected_post, ZERO)
        if (
            self.pre_action_research_cash_usd != expected_pre
            or self.cash_capacity_usd != expected_capacity
            or candidate != expected_candidate
            or self.post_action_research_cash_usd != expected_post
            or self.remaining_shortfall_usd != expected_shortfall
            or self.reduction_usd != source_candidate - expected_candidate
            or self.outcome is not expected_outcome
        ):
            raise RiskContractError(
                "research cash-floor rule output is inconsistent with the locked formula"
            )
        if not ZERO <= candidate <= source_candidate:
            raise RiskContractError("research cash-floor rule violates non-expansion")
        if not self.reason_codes:
            raise RiskContractError("research cash-floor rule requires reason codes")
        object.__setattr__(
            self, "evaluated_at_utc", _utc(self.evaluated_at_utc, "evaluated_at_utc")
        )


@dataclass(frozen=True, slots=True)
class TargetAdjustmentResearchCashFloorPreviewResult:
    preview_result_id: UUID
    operation_id: UUID
    run_id: UUID
    stage_id: UUID
    source: LinkedResearchCashFloorPreviewInput
    rule: ResearchCashFloorRuleResult
    disposition: ResearchCashFloorDisposition
    reason_codes: tuple[str, ...]
    warnings: tuple[str, ...]
    created_at_utc: datetime
    created_by: str
    reason: str
    software_version: str
    component_id: str = RESEARCH_CASH_FLOOR_COMPONENT_ID
    component_version: str = RESEARCH_CASH_FLOOR_COMPONENT_VERSION
    schema_version: int = RESEARCH_CASH_FLOOR_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if (
            self.schema_version != RESEARCH_CASH_FLOOR_SCHEMA_VERSION
            or self.component_id != RESEARCH_CASH_FLOOR_COMPONENT_ID
            or self.component_version != RESEARCH_CASH_FLOOR_COMPONENT_VERSION
        ):
            raise RiskContractError("unsupported research cash-floor preview identity")
        if (
            self.rule.preview_result_id != self.preview_result_id
            or self.rule.run_id != self.run_id
            or self.rule.stage_id != self.stage_id
        ):
            raise RiskContractError("cash-floor rule/result parent identity is inconsistent")
        candidate = self.rule.cash_floor_constrained_candidate_notional_usd
        expected = (
            ResearchCashFloorDisposition.BLOCKED_BY_RESEARCH_CASH_FLOOR
            if candidate == ZERO
            else ResearchCashFloorDisposition.MANUAL_REVIEW_REQUIRED
        )
        if self.disposition is not expected:
            raise RiskContractError("research cash-floor final disposition is inconsistent")
        if (
            candidate == ZERO
            and self.rule.outcome
            is not ResearchCashFloorRuleOutcome.BLOCKED_NO_RESEARCH_CASH_CAPACITY
        ):
            raise RiskContractError("only an increase without cash capacity can be zero")
        if not self.reason_codes:
            raise RiskContractError("research cash-floor result requires reason codes")
        for name in ("created_by", "reason", "software_version"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        object.__setattr__(
            self, "created_at_utc", _utc(self.created_at_utc, "created_at_utc")
        )

    @property
    def cash_floor_constrained_candidate_notional_usd(self) -> Decimal:
        return self.rule.cash_floor_constrained_candidate_notional_usd


@dataclass(frozen=True, slots=True)
class ResearchCashFloorOperationAttempt:
    attempt_id: UUID
    operation_id: UUID
    operation_type: ResearchCashFloorOperationType
    status: ResearchCashFloorOperationStatus
    run_id: UUID
    stage_id: UUID
    requested_at_utc: datetime
    completed_at_utc: datetime
    session_id: str
    request_id: str
    created_by: str
    reason: str
    requested_phase6b_result_id: UUID | None = None
    requested_definition_id: UUID | None = None
    requested_definition_version: int | None = None
    requested_symbol: str | None = None
    requested_minimum_research_asset_cash_usd_text: str | None = None
    resolved_definition_id: UUID | None = None
    resolved_definition_version: int | None = None
    resolved_source: LinkedResearchCashFloorPreviewInput | None = None
    current_safety_snapshot: RiskSafetyStateSnapshot | None = None
    preview_result_id: UUID | None = None
    disposition: ResearchCashFloorDisposition | None = None
    error_code: str | None = None
    error_summary: str | None = None
    schema_version: int = RESEARCH_CASH_FLOOR_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != RESEARCH_CASH_FLOOR_SCHEMA_VERSION:
            raise RiskContractError("unsupported research cash-floor operation schema")
        if not isinstance(
            self.operation_type, ResearchCashFloorOperationType
        ) or not isinstance(self.status, ResearchCashFloorOperationStatus):
            raise RiskContractError("research cash-floor operation type/status is invalid")
        if self.status is ResearchCashFloorOperationStatus.COMPLETED:
            if self.error_code is not None or self.error_summary is not None:
                raise RiskContractError("completed operation cannot contain an error")
            if self.operation_type is ResearchCashFloorOperationType.PREVIEW:
                if None in (self.resolved_source, self.preview_result_id, self.disposition):
                    raise RiskContractError("completed preview requires result evidence")
            elif None in (self.resolved_definition_id, self.resolved_definition_version):
                raise RiskContractError("completed definition operation requires a version")
        else:
            if not self.error_code or not self.error_summary:
                raise RiskContractError("non-completed operation requires error evidence")
            if self.preview_result_id is not None or self.disposition is not None:
                raise RiskContractError(
                    "non-completed operation cannot contain preview result evidence"
                )
        for name in ("requested_at_utc", "completed_at_utc"):
            object.__setattr__(self, name, _utc(getattr(self, name), name))
        for name in ("session_id", "request_id", "created_by", "reason"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        if self.requested_symbol is not None:
            object.__setattr__(
                self, "requested_symbol", _text(self.requested_symbol, "requested_symbol").upper()
            )

    def matches_command(self, command: object) -> bool:
        common = (
            self.session_id == getattr(command, "session_id", None)
            and self.request_id == getattr(command, "request_id", None)
            and self.created_by == getattr(command, "created_by", None)
            and self.reason == getattr(command, "reason", None)
        )
        if isinstance(command, SaveResearchAssetCashFloorDefinitionCommand):
            return common and self.operation_type is ResearchCashFloorOperationType.DEFINITION_SAVE and (
                self.requested_definition_id == command.definition_id
                and self.requested_definition_version == command.predecessor_version
                and self.requested_symbol == command.symbol
                and self.requested_minimum_research_asset_cash_usd_text
                == command.minimum_research_asset_cash_usd
            )
        if isinstance(command, ArchiveResearchAssetCashFloorDefinitionCommand):
            return common and self.operation_type is ResearchCashFloorOperationType.DEFINITION_ARCHIVE and (
                self.requested_definition_id == command.definition_id
                and self.requested_definition_version == command.predecessor_version
            )
        if isinstance(command, TargetAdjustmentResearchCashFloorPreviewCommand):
            return common and self.operation_type is ResearchCashFloorOperationType.PREVIEW and (
                self.requested_phase6b_result_id
                == command.target_adjustment_exposure_cap_preview_result_id
                and self.requested_definition_id
                == command.research_cash_floor_definition_id
                and self.requested_definition_version
                == command.research_cash_floor_definition_version
            )
        return False


@dataclass(frozen=True, slots=True)
class ResearchCashFloorSourceLink:
    source_link_id: UUID
    operation_id: UUID
    preview_result_id: UUID
    cash_floor_run_id: UUID
    cash_floor_stage_id: UUID
    phase6b_preview_result_id: UUID
    phase6b_run_id: UUID
    phase6b_stage_id: UUID
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
    schema_version: int = RESEARCH_CASH_FLOOR_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != RESEARCH_CASH_FLOOR_SCHEMA_VERSION:
            raise RiskContractError("unsupported research cash-floor source-link schema")
        object.__setattr__(
            self, "created_at_utc", _utc(self.created_at_utc, "created_at_utc")
        )


@dataclass(frozen=True, slots=True)
class ResearchCashFloorOperationOutcome:
    attempt_id: UUID
    operation_id: UUID
    run_id: UUID
    status: ResearchCashFloorOperationStatus
    summary: str
    definition_id: UUID | None = None
    definition_version: int | None = None
    preview_result_id: UUID | None = None
    disposition: ResearchCashFloorDisposition | None = None
    phase6b_run_id: UUID | None = None
    phase6a_run_id: UUID | None = None
    decision_run_id: UUID | None = None
    linked_parent_run_id: UUID | None = None
    target_child_run_id: UUID | None = None
    standardized_state_run_id: UUID | None = None
    error_code: str | None = None


@dataclass(frozen=True, slots=True)
class ResearchCashFloorDefinitionQuery:
    symbol: str | None = None
    status: ResearchCashFloorDefinitionStatus | None = None
    current_only: bool = False
    limit: int = 500

    def __post_init__(self) -> None:
        if not 1 <= self.limit <= 5000:
            raise RiskContractError("definition query limit must be within 1..5000")
        if self.symbol is not None:
            object.__setattr__(self, "symbol", _text(self.symbol, "symbol").upper())


@dataclass(frozen=True, slots=True)
class ResearchCashFloorResultQuery:
    symbol: str | None = None
    action: str | None = None
    definition_id: UUID | None = None
    definition_version: int | None = None
    disposition: ResearchCashFloorDisposition | None = None
    phase6b_rule_outcome: ExposureCapRuleOutcome | None = None
    rule_outcome: ResearchCashFloorRuleOutcome | None = None
    has_warnings: bool | None = None
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
class ResearchCashFloorOperationQuery:
    operation_type: ResearchCashFloorOperationType | None = None
    status: ResearchCashFloorOperationStatus | None = None
    symbol: str | None = None
    has_error: bool | None = None
    limit: int = 500

    def __post_init__(self) -> None:
        if not 1 <= self.limit <= 5000:
            raise RiskContractError("operation query limit must be within 1..5000")
        if self.symbol is not None:
            object.__setattr__(self, "symbol", _text(self.symbol, "symbol").upper())


__all__ = [
    name
    for name in globals()
    if name.startswith("ResearchCash")
    or name.startswith("ResearchAsset")
    or name.startswith("SaveResearch")
    or name.startswith("ArchiveResearch")
    or name.startswith("TargetAdjustmentResearch")
    or name.startswith("LinkedResearch")
    or name.startswith("RESEARCH_CASH")
]
