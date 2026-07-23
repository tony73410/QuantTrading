"""Type-distinct order-3 Risk preview contracts for research asset cash."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from .errors import RiskContractError
from .research_cash_floor_models import (
    ResearchCashFloorDisposition,
    ResearchCashFloorSourceLink,
    TargetAdjustmentResearchCashFloorPreviewResult,
)
from .target_adjustment_models import RiskSafetyStateSnapshot


RESEARCH_ASSET_CASH_SCHEMA_VERSION = 1
RESEARCH_ASSET_CASH_COMPONENT_ID = (
    "risk.target_adjustment_research_asset_cash_availability_preview"
)
RESEARCH_ASSET_CASH_COMPONENT_VERSION = "1.0.0"
RESEARCH_ASSET_CASH_RULE_ID = "MAX_RESEARCH_ASSET_CASH_DEPLOYMENT_USD"
RESEARCH_ASSET_CASH_RULE_VERSION = "1"
RESEARCH_ASSET_CASH_RULE_ORDER = 3
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


class ResearchAssetCashOperationStatus(StrEnum):
    COMPLETED = "completed"
    BLOCKED = "blocked"
    INVALID_INPUT = "invalid_input"
    FAILED = "failed"


class ResearchAssetCashRuleOutcome(StrEnum):
    PASSED_WITHIN_RESEARCH_ASSET_CASH = "passed_within_research_asset_cash"
    REDUCED_TO_RESEARCH_ASSET_CASH = "reduced_to_research_asset_cash"
    BLOCKED_NO_RESEARCH_ASSET_CASH = "blocked_no_research_asset_cash"
    PRESERVED_RESEARCH_ASSET_CASH_INCREASING_DIRECTION = (
        "preserved_research_asset_cash_increasing_direction"
    )


class ResearchAssetCashDisposition(StrEnum):
    MANUAL_REVIEW_REQUIRED = "manual_review_required"
    BLOCKED_BY_RESEARCH_ASSET_CASH = "blocked_by_research_asset_cash"


@dataclass(frozen=True, slots=True)
class TargetAdjustmentResearchAssetCashPreviewCommand:
    target_adjustment_research_cash_floor_preview_result_id: UUID
    capital_plan_id: UUID
    capital_snapshot_id: UUID
    reason: str
    session_id: str
    request_id: str
    created_by: str
    requested_at_utc: datetime
    operation_id: UUID | None = None

    def __post_init__(self) -> None:
        for name in ("reason", "session_id", "request_id", "created_by"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        object.__setattr__(
            self, "requested_at_utc", _utc(self.requested_at_utc, "requested_at_utc")
        )


@dataclass(frozen=True, slots=True)
class LinkedResearchAssetCashPreviewInput:
    phase6c_result: TargetAdjustmentResearchCashFloorPreviewResult
    phase6c_source_link: ResearchCashFloorSourceLink
    capital_plan_id: UUID
    capital_plan_version: int
    capital_plan_created_at_utc: datetime
    capital_snapshot_id: UUID
    capital_snapshot_run_id: UUID
    capital_snapshot_created_at_utc: datetime
    account_cash_basis_usd: Decimal
    conservation_expected_total_usd: Decimal
    conservation_actual_total_usd: Decimal
    conservation_difference_usd: Decimal
    locked_reserve_bucket_id: UUID
    locked_reserve_balance_usd: Decimal
    tactical_reserve_bucket_id: UUID
    tactical_reserve_balance_usd: Decimal
    asset_cash_bucket_id: UUID
    asset_cash_balance_usd: Decimal
    current_safety_snapshot: RiskSafetyStateSnapshot
    currency: str = "USD"
    capital_plan_schema_version: int = 1
    capital_snapshot_schema_version: int = 1
    schema_version: int = RESEARCH_ASSET_CASH_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != RESEARCH_ASSET_CASH_SCHEMA_VERSION:
            raise RiskContractError("unsupported research asset-cash linked-input schema")
        if self.phase6c_result.disposition is not ResearchCashFloorDisposition.MANUAL_REVIEW_REQUIRED:
            raise RiskContractError("only a Phase 6C MANUAL_REVIEW_REQUIRED result is eligible")
        if self.phase6c_result.cash_floor_constrained_candidate_notional_usd <= ZERO:
            raise RiskContractError("Phase 6C candidate must be positive")
        link = self.phase6c_source_link
        if (
            link.preview_result_id != self.phase6c_result.preview_result_id
            or link.operation_id != self.phase6c_result.operation_id
            or link.cash_floor_run_id != self.phase6c_result.run_id
            or link.cash_floor_stage_id != self.phase6c_result.stage_id
        ):
            raise RiskContractError("Phase 6C result/source-link identity is inconsistent")
        if self.capital_plan_version < 1:
            raise RiskContractError("capital plan version must be positive")
        if self.currency != "USD" or self.capital_plan_schema_version != 1 or self.capital_snapshot_schema_version != 1:
            raise RiskContractError("unsupported capital plan/snapshot schema or currency")
        for name in (
            "account_cash_basis_usd",
            "conservation_expected_total_usd",
            "conservation_actual_total_usd",
            "locked_reserve_balance_usd",
            "tactical_reserve_balance_usd",
            "asset_cash_balance_usd",
        ):
            value = _decimal(getattr(self, name), name)
            if value < ZERO:
                raise RiskContractError(f"{name} must be non-negative")
            object.__setattr__(self, name, value)
        difference = _decimal(
            self.conservation_difference_usd, "conservation_difference_usd"
        )
        if difference != ZERO:
            raise RiskContractError("selected capital snapshot must conserve exactly")
        if (
            self.conservation_expected_total_usd != self.account_cash_basis_usd
            or self.conservation_actual_total_usd != self.account_cash_basis_usd
        ):
            raise RiskContractError("capital snapshot totals must equal the plan basis")
        if len({self.locked_reserve_bucket_id, self.tactical_reserve_bucket_id, self.asset_cash_bucket_id}) != 3:
            raise RiskContractError("capital bucket identities must be distinct")
        for name in (
            "capital_plan_created_at_utc",
            "capital_snapshot_created_at_utc",
        ):
            object.__setattr__(self, name, _utc(getattr(self, name), name))

    @property
    def symbol(self) -> str:
        return self.phase6c_result.source.symbol

    @property
    def action(self) -> str:
        return self.phase6c_result.rule.action

    @property
    def as_of_utc(self) -> datetime:
        return self.phase6c_result.source.as_of_utc

    @property
    def phase6c_candidate_notional_usd(self) -> Decimal:
        return self.phase6c_result.cash_floor_constrained_candidate_notional_usd


@dataclass(frozen=True, slots=True)
class ResearchAssetCashRuleResult:
    rule_result_id: UUID
    preview_result_id: UUID
    run_id: UUID
    stage_id: UUID
    action: str
    phase6c_candidate_notional_usd: Decimal
    selected_asset_cash_balance_usd: Decimal
    pre_candidate_asset_cash_usd: Decimal
    asset_cash_constrained_candidate_notional_usd: Decimal
    hypothetical_post_candidate_asset_cash_usd: Decimal
    reduction_usd: Decimal
    outcome: ResearchAssetCashRuleOutcome
    reason_codes: tuple[str, ...]
    evaluated_at_utc: datetime
    research_cash_reserved: bool = False
    stop_processing: bool = True
    rule_id: str = RESEARCH_ASSET_CASH_RULE_ID
    rule_version: str = RESEARCH_ASSET_CASH_RULE_VERSION
    evaluation_order: int = RESEARCH_ASSET_CASH_RULE_ORDER
    schema_version: int = RESEARCH_ASSET_CASH_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if (
            self.schema_version != RESEARCH_ASSET_CASH_SCHEMA_VERSION
            or self.rule_id != RESEARCH_ASSET_CASH_RULE_ID
            or self.rule_version != RESEARCH_ASSET_CASH_RULE_VERSION
            or self.evaluation_order != RESEARCH_ASSET_CASH_RULE_ORDER
            or not self.stop_processing
            or self.research_cash_reserved
        ):
            raise RiskContractError("research asset-cash rule identity/safety is invalid")
        if self.action not in {"increase", "decrease"}:
            raise RiskContractError("research asset-cash action is invalid")
        for name in (
            "phase6c_candidate_notional_usd",
            "selected_asset_cash_balance_usd",
            "pre_candidate_asset_cash_usd",
            "asset_cash_constrained_candidate_notional_usd",
            "hypothetical_post_candidate_asset_cash_usd",
            "reduction_usd",
        ):
            object.__setattr__(self, name, _decimal(getattr(self, name), name))
        source = self.phase6c_candidate_notional_usd
        balance = self.selected_asset_cash_balance_usd
        if source <= ZERO or balance < ZERO or self.pre_candidate_asset_cash_usd != balance:
            raise RiskContractError("research asset-cash inputs are invalid")
        if self.action == "increase":
            candidate = min(source, balance)
            post = balance - candidate
            if source <= balance:
                outcome = ResearchAssetCashRuleOutcome.PASSED_WITHIN_RESEARCH_ASSET_CASH
            elif balance > ZERO:
                outcome = ResearchAssetCashRuleOutcome.REDUCED_TO_RESEARCH_ASSET_CASH
            else:
                outcome = ResearchAssetCashRuleOutcome.BLOCKED_NO_RESEARCH_ASSET_CASH
        else:
            candidate = source
            post = balance + candidate
            outcome = (
                ResearchAssetCashRuleOutcome.PRESERVED_RESEARCH_ASSET_CASH_INCREASING_DIRECTION
            )
        if (
            self.asset_cash_constrained_candidate_notional_usd != candidate
            or self.hypothetical_post_candidate_asset_cash_usd != post
            or self.reduction_usd != source - candidate
            or self.outcome is not outcome
        ):
            raise RiskContractError("research asset-cash rule violates the locked formula")
        if not ZERO <= candidate <= source:
            raise RiskContractError("research asset-cash rule violates non-expansion")
        if not self.reason_codes:
            raise RiskContractError("research asset-cash rule requires reason codes")
        object.__setattr__(
            self, "evaluated_at_utc", _utc(self.evaluated_at_utc, "evaluated_at_utc")
        )


@dataclass(frozen=True, slots=True)
class TargetAdjustmentResearchAssetCashPreviewResult:
    preview_result_id: UUID
    operation_id: UUID
    run_id: UUID
    stage_id: UUID
    source: LinkedResearchAssetCashPreviewInput
    rule: ResearchAssetCashRuleResult
    disposition: ResearchAssetCashDisposition
    reason_codes: tuple[str, ...]
    warnings: tuple[str, ...]
    research_cash_reserved: bool
    created_at_utc: datetime
    created_by: str
    reason: str
    software_version: str
    component_id: str = RESEARCH_ASSET_CASH_COMPONENT_ID
    component_version: str = RESEARCH_ASSET_CASH_COMPONENT_VERSION
    schema_version: int = RESEARCH_ASSET_CASH_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if (
            self.schema_version != RESEARCH_ASSET_CASH_SCHEMA_VERSION
            or self.component_id != RESEARCH_ASSET_CASH_COMPONENT_ID
            or self.component_version != RESEARCH_ASSET_CASH_COMPONENT_VERSION
            or self.research_cash_reserved
        ):
            raise RiskContractError("unsupported research asset-cash result identity/safety")
        if (
            self.rule.preview_result_id != self.preview_result_id
            or self.rule.run_id != self.run_id
            or self.rule.stage_id != self.stage_id
            or self.rule.research_cash_reserved
        ):
            raise RiskContractError("research asset-cash rule/result identity is inconsistent")
        candidate = self.rule.asset_cash_constrained_candidate_notional_usd
        expected = (
            ResearchAssetCashDisposition.BLOCKED_BY_RESEARCH_ASSET_CASH
            if candidate == ZERO
            else ResearchAssetCashDisposition.MANUAL_REVIEW_REQUIRED
        )
        if self.disposition is not expected:
            raise RiskContractError("research asset-cash disposition is inconsistent")
        if candidate == ZERO and self.rule.outcome is not ResearchAssetCashRuleOutcome.BLOCKED_NO_RESEARCH_ASSET_CASH:
            raise RiskContractError("only an increase without asset cash can be zero")
        if not self.reason_codes or not self.warnings:
            raise RiskContractError("research asset-cash result requires reasons and warnings")
        for name in ("created_by", "reason", "software_version"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        object.__setattr__(
            self, "created_at_utc", _utc(self.created_at_utc, "created_at_utc")
        )

    @property
    def asset_cash_constrained_candidate_notional_usd(self) -> Decimal:
        return self.rule.asset_cash_constrained_candidate_notional_usd


@dataclass(frozen=True, slots=True)
class ResearchAssetCashOperationAttempt:
    attempt_id: UUID
    operation_id: UUID
    status: ResearchAssetCashOperationStatus
    run_id: UUID
    stage_id: UUID
    requested_at_utc: datetime
    completed_at_utc: datetime
    session_id: str
    request_id: str
    created_by: str
    reason: str
    requested_phase6c_result_id: UUID
    requested_capital_plan_id: UUID
    requested_capital_snapshot_id: UUID
    resolved_source: LinkedResearchAssetCashPreviewInput | None = None
    current_safety_snapshot: RiskSafetyStateSnapshot | None = None
    preview_result_id: UUID | None = None
    disposition: ResearchAssetCashDisposition | None = None
    error_code: str | None = None
    error_summary: str | None = None
    schema_version: int = RESEARCH_ASSET_CASH_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != RESEARCH_ASSET_CASH_SCHEMA_VERSION or not isinstance(self.status, ResearchAssetCashOperationStatus):
            raise RiskContractError("unsupported research asset-cash operation")
        if self.status is ResearchAssetCashOperationStatus.COMPLETED:
            if None in (self.resolved_source, self.preview_result_id, self.disposition):
                raise RiskContractError("completed asset-cash operation requires result evidence")
            if self.error_code is not None or self.error_summary is not None:
                raise RiskContractError("completed asset-cash operation cannot contain error")
        else:
            if not self.error_code or not self.error_summary:
                raise RiskContractError("non-completed asset-cash operation requires error")
            if self.preview_result_id is not None or self.disposition is not None:
                raise RiskContractError("non-completed asset-cash operation cannot contain result")
        for name in ("requested_at_utc", "completed_at_utc"):
            object.__setattr__(self, name, _utc(getattr(self, name), name))
        for name in ("session_id", "request_id", "created_by", "reason"):
            object.__setattr__(self, name, _text(getattr(self, name), name))

    def matches_command(self, command: object) -> bool:
        return isinstance(command, TargetAdjustmentResearchAssetCashPreviewCommand) and (
            self.session_id == command.session_id
            and self.request_id == command.request_id
            and self.created_by == command.created_by
            and self.reason == command.reason
            and self.requested_phase6c_result_id
            == command.target_adjustment_research_cash_floor_preview_result_id
            and self.requested_capital_plan_id == command.capital_plan_id
            and self.requested_capital_snapshot_id == command.capital_snapshot_id
        )


@dataclass(frozen=True, slots=True)
class ResearchAssetCashSourceLink:
    source_link_id: UUID
    operation_id: UUID
    preview_result_id: UUID
    asset_cash_run_id: UUID
    asset_cash_stage_id: UUID
    phase6c_preview_result_id: UUID
    phase6c_run_id: UUID
    phase6c_stage_id: UUID
    phase6b_run_id: UUID
    phase6a_run_id: UUID
    decision_run_id: UUID
    linked_parent_run_id: UUID
    target_child_run_id: UUID
    standardized_state_run_id: UUID
    capital_plan_id: UUID
    capital_snapshot_id: UUID
    capital_snapshot_run_id: UUID
    asset_cash_bucket_id: UUID
    created_at_utc: datetime
    schema_version: int = RESEARCH_ASSET_CASH_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != RESEARCH_ASSET_CASH_SCHEMA_VERSION:
            raise RiskContractError("unsupported research asset-cash source-link schema")
        object.__setattr__(
            self, "created_at_utc", _utc(self.created_at_utc, "created_at_utc")
        )


@dataclass(frozen=True, slots=True)
class ResearchAssetCashOperationOutcome:
    attempt_id: UUID
    operation_id: UUID
    run_id: UUID
    status: ResearchAssetCashOperationStatus
    summary: str
    preview_result_id: UUID | None = None
    disposition: ResearchAssetCashDisposition | None = None
    phase6c_run_id: UUID | None = None
    capital_snapshot_run_id: UUID | None = None
    error_code: str | None = None


@dataclass(frozen=True, slots=True)
class ResearchAssetCashResultQuery:
    symbol: str | None = None
    action: str | None = None
    capital_plan_id: UUID | None = None
    capital_snapshot_id: UUID | None = None
    disposition: ResearchAssetCashDisposition | None = None
    rule_outcome: ResearchAssetCashRuleOutcome | None = None
    has_warnings: bool | None = None
    limit: int = 500
    as_of_from_utc: datetime | None = None
    as_of_to_utc: datetime | None = None

    def __post_init__(self) -> None:
        if not 1 <= self.limit <= 5000:
            raise RiskContractError("result query limit must be within 1..5000")
        if self.symbol is not None:
            object.__setattr__(self, "symbol", _text(self.symbol, "symbol").upper())
        if self.action is not None and self.action not in {"increase", "decrease"}:
            raise RiskContractError("result query action is invalid")
        for name in ("as_of_from_utc", "as_of_to_utc"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, _utc(value, name))
        if (
            self.as_of_from_utc is not None
            and self.as_of_to_utc is not None
            and self.as_of_from_utc > self.as_of_to_utc
        ):
            raise RiskContractError("result query as-of range is invalid")


@dataclass(frozen=True, slots=True)
class ResearchAssetCashOperationQuery:
    status: ResearchAssetCashOperationStatus | None = None
    symbol: str | None = None
    has_error: bool | None = None
    limit: int = 500

    def __post_init__(self) -> None:
        if not 1 <= self.limit <= 5000:
            raise RiskContractError("operation query limit must be within 1..5000")
        if self.symbol is not None:
            object.__setattr__(self, "symbol", _text(self.symbol, "symbol").upper())


__all__ = [name for name in globals() if name.startswith("ResearchAssetCash") or name.startswith("TargetAdjustmentResearchAssetCash") or name.startswith("LinkedResearchAssetCash") or name.startswith("RESEARCH_ASSET_CASH")]
