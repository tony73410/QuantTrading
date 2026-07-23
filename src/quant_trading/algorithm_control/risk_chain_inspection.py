"""Read-only presentation adapter for persisted Phase 6A-6D Risk evidence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Callable, TypeAlias
from uuid import UUID

from quant_trading.risk.exposure_cap_interfaces import ExposureCapQueryService
from quant_trading.risk.exposure_cap_models import (
    ExposureCapSourceLink,
    TargetAdjustmentExposureCapPreviewResult,
)
from quant_trading.risk.research_asset_cash_interfaces import (
    ResearchAssetCashQueryService,
)
from quant_trading.risk.research_asset_cash_models import (
    ResearchAssetCashResultQuery,
    ResearchAssetCashSourceLink,
    TargetAdjustmentResearchAssetCashPreviewResult,
)
from quant_trading.risk.research_cash_floor_interfaces import (
    ResearchCashFloorQueryService,
)
from quant_trading.risk.research_cash_floor_models import (
    ResearchCashFloorSourceLink,
    TargetAdjustmentResearchCashFloorPreviewResult,
)
from quant_trading.risk.target_adjustment_interfaces import (
    TargetAdjustmentRiskQueryService,
)
from quant_trading.risk.target_adjustment_models import (
    TargetAdjustmentRiskReviewResult,
    TargetAdjustmentRiskSourceLink,
)


class RiskChainInspectionError(RuntimeError):
    """Raised when persisted Risk evidence is missing or internally inconsistent."""


ComparisonValue: TypeAlias = (
    Decimal | datetime | UUID | str | bool | int | tuple[str, ...] | None
)


@dataclass(frozen=True, slots=True)
class TargetAdjustmentRiskChainView:
    """Exact persisted Phase 6A-6D records and their immutable source links."""

    phase6a: TargetAdjustmentRiskReviewResult
    phase6a_source_link: TargetAdjustmentRiskSourceLink
    phase6b: TargetAdjustmentExposureCapPreviewResult
    phase6b_source_link: ExposureCapSourceLink
    phase6c: TargetAdjustmentResearchCashFloorPreviewResult
    phase6c_source_link: ResearchCashFloorSourceLink
    phase6d: TargetAdjustmentResearchAssetCashPreviewResult
    phase6d_source_link: ResearchAssetCashSourceLink
    schema_version: int = 1

    @property
    def preview_result_id(self) -> UUID:
        return self.phase6d.preview_result_id

    @property
    def symbol(self) -> str:
        return self.phase6d.source.symbol

    @property
    def action(self) -> str:
        return self.phase6d.rule.action

    @property
    def as_of_utc(self) -> datetime:
        return self.phase6d.source.as_of_utc

    @property
    def created_at_utc(self) -> datetime:
        return self.phase6d.created_at_utc


@dataclass(frozen=True, slots=True)
class RiskChainComparisonField:
    label: str
    left_value: ComparisonValue
    right_value: ComparisonValue
    matches: bool


@dataclass(frozen=True, slots=True)
class TargetAdjustmentRiskChainComparison:
    left_preview_result_id: UUID
    right_preview_result_id: UUID
    fields: tuple[RiskChainComparisonField, ...]
    schema_version: int = 1


class RiskChainInspectionService:
    """Resolve and compare stored chains without recalculating financial results."""

    def __init__(
        self,
        phase6a_queries: TargetAdjustmentRiskQueryService,
        phase6b_queries: ExposureCapQueryService,
        phase6c_queries: ResearchCashFloorQueryService,
        phase6d_queries: ResearchAssetCashQueryService,
    ) -> None:
        self._phase6a_queries = phase6a_queries
        self._phase6b_queries = phase6b_queries
        self._phase6c_queries = phase6c_queries
        self._phase6d_queries = phase6d_queries

    def list_chains(
        self, query: ResearchAssetCashResultQuery = ResearchAssetCashResultQuery()
    ) -> tuple[TargetAdjustmentRiskChainView, ...]:
        return tuple(
            self._resolve(result)
            for result in self._phase6d_queries.list_research_asset_cash_results(query)
        )

    def get_chain(self, preview_result_id: UUID) -> TargetAdjustmentRiskChainView:
        result = self._phase6d_queries.get_research_asset_cash_result(preview_result_id)
        if result is None:
            raise RiskChainInspectionError(
                f"Phase 6D result is missing: {preview_result_id}"
            )
        return self._resolve(result)

    def compare(
        self, left_preview_result_id: UUID, right_preview_result_id: UUID
    ) -> TargetAdjustmentRiskChainComparison:
        left = self.get_chain(left_preview_result_id)
        right = self.get_chain(right_preview_result_id)
        fields = []
        for label, getter in _COMPARISON_FIELDS:
            left_value = getter(left)
            right_value = getter(right)
            fields.append(
                RiskChainComparisonField(
                    label, left_value, right_value, left_value == right_value
                )
            )
        return TargetAdjustmentRiskChainComparison(
            left_preview_result_id=left_preview_result_id,
            right_preview_result_id=right_preview_result_id,
            fields=tuple(fields),
        )

    def _resolve(
        self, phase6d: TargetAdjustmentResearchAssetCashPreviewResult
    ) -> TargetAdjustmentRiskChainView:
        phase6d_link = self._required(
            "Phase 6D source link",
            phase6d.preview_result_id,
            self._phase6d_queries.get_research_asset_cash_source_link(
                phase6d.preview_result_id
            ),
        )
        phase6c_id = phase6d.source.phase6c_result.preview_result_id
        phase6c = self._required(
            "Phase 6C result",
            phase6c_id,
            self._phase6c_queries.get_research_cash_floor_result(phase6c_id),
        )
        phase6c_link = self._required(
            "Phase 6C source link",
            phase6c_id,
            self._phase6c_queries.get_research_cash_floor_source_link(phase6c_id),
        )
        phase6b_id = phase6c.source.phase6b_result.preview_result_id
        phase6b = self._required(
            "Phase 6B result",
            phase6b_id,
            self._phase6b_queries.get_exposure_cap_result(phase6b_id),
        )
        phase6b_link = self._required(
            "Phase 6B source link",
            phase6b_id,
            self._phase6b_queries.get_exposure_cap_source_link(phase6b_id),
        )
        phase6a_id = phase6b.source.phase6a_review_result_id
        phase6a = self._required(
            "Phase 6A result",
            phase6a_id,
            self._phase6a_queries.get_target_adjustment_risk_result(phase6a_id),
        )
        phase6a_link = self._required(
            "Phase 6A source link",
            phase6a_id,
            self._phase6a_queries.get_target_adjustment_risk_source_link(phase6a_id),
        )

        if phase6d.source.phase6c_result != phase6c:
            self._inconsistent("Phase 6D embedded Phase 6C result")
        if phase6d.source.phase6c_source_link != phase6c_link:
            self._inconsistent("Phase 6D embedded Phase 6C source link")
        if phase6c.source.phase6b_result != phase6b:
            self._inconsistent("Phase 6C embedded Phase 6B result")
        if phase6c.source.phase6b_source_link != phase6b_link:
            self._inconsistent("Phase 6C embedded Phase 6B source link")
        self._validate_phase6a(phase6a, phase6a_link, phase6b, phase6b_link)
        self._validate_link_chain(
            phase6a, phase6a_link, phase6b, phase6b_link,
            phase6c, phase6c_link, phase6d, phase6d_link,
        )
        return TargetAdjustmentRiskChainView(
            phase6a=phase6a,
            phase6a_source_link=phase6a_link,
            phase6b=phase6b,
            phase6b_source_link=phase6b_link,
            phase6c=phase6c,
            phase6c_source_link=phase6c_link,
            phase6d=phase6d,
            phase6d_source_link=phase6d_link,
        )

    @staticmethod
    def _required(label: str, identity: UUID, value):
        if value is None:
            raise RiskChainInspectionError(f"{label} is missing: {identity}")
        return value

    @staticmethod
    def _inconsistent(label: str) -> None:
        raise RiskChainInspectionError(f"Persisted Risk chain is inconsistent: {label}")

    @classmethod
    def _validate_phase6a(cls, phase6a, phase6a_link, phase6b, phase6b_link) -> None:
        source = phase6b.source
        evidence = tuple(
            (rule.rule_id, rule.rule_version, rule.status.value) for rule in phase6a.rules
        )
        if (
            source.phase6a_review_result_id != phase6a.review_result_id
            or source.phase6a_operation_id != phase6a.operation_id
            or source.phase6a_run_id != phase6a.run_id
            or source.phase6a_stage_id != phase6a.stage_id
            or source.phase6a_gate_id != phase6a.gate_id
            or source.phase6a_gate_version != phase6a.gate_version
            or source.phase6a_source != phase6a.source
            or source.phase6a_safety_snapshot != phase6a.safety_snapshot
            or source.phase6a_rule_evidence != evidence
            or phase6b_link.phase6a_review_result_id != phase6a.review_result_id
            or phase6b_link.phase6a_run_id != phase6a.run_id
            or phase6b_link.phase6a_stage_id != phase6a.stage_id
            or phase6a_link.review_result_id != phase6a.review_result_id
            or phase6a_link.operation_id != phase6a.operation_id
            or phase6a_link.risk_run_id != phase6a.run_id
            or phase6a_link.risk_stage_id != phase6a.stage_id
            or phase6a_link.decision_result_id != phase6a.source.decision_result_id
            or phase6a_link.intent_id != phase6a.source.intent_id
            or phase6a_link.decision_run_id != phase6a.source.decision_run_id
            or phase6a_link.linked_parent_run_id != phase6a.source.linked_parent_run_id
            or phase6a_link.target_child_run_id != phase6a.source.target_child_run_id
            or phase6a_link.standardized_state_run_id
            != phase6a.source.standardized_state_run_id
            or phase6a_link.target_position_link_id
            != phase6a.source.target_position_link_id
            or phase6a_link.target_calculation_id
            != phase6a.source.target_calculation_id
            or phase6a_link.standardized_state_calculation_id
            != phase6a.source.standardized_state_calculation_id
        ):
            cls._inconsistent("Phase 6A evidence")

    @classmethod
    def _validate_link_chain(
        cls, phase6a, phase6a_link, phase6b, phase6b_link,
        phase6c, phase6c_link, phase6d, phase6d_link,
    ) -> None:
        if (
            phase6b_link.preview_result_id != phase6b.preview_result_id
            or phase6b_link.operation_id != phase6b.operation_id
            or phase6b_link.exposure_cap_run_id != phase6b.run_id
            or phase6b_link.exposure_cap_stage_id != phase6b.stage_id
            or phase6c_link.preview_result_id != phase6c.preview_result_id
            or phase6c_link.operation_id != phase6c.operation_id
            or phase6c_link.cash_floor_run_id != phase6c.run_id
            or phase6c_link.cash_floor_stage_id != phase6c.stage_id
            or phase6c_link.phase6b_preview_result_id != phase6b.preview_result_id
            or phase6c_link.phase6b_run_id != phase6b.run_id
            or phase6c_link.phase6b_stage_id != phase6b.stage_id
            or phase6c_link.phase6a_review_result_id != phase6a.review_result_id
            or phase6c_link.phase6a_run_id != phase6a.run_id
            or phase6c_link.phase6a_stage_id != phase6a.stage_id
            or phase6d_link.preview_result_id != phase6d.preview_result_id
            or phase6d_link.operation_id != phase6d.operation_id
            or phase6d_link.asset_cash_run_id != phase6d.run_id
            or phase6d_link.asset_cash_stage_id != phase6d.stage_id
            or phase6d_link.phase6c_preview_result_id != phase6c.preview_result_id
            or phase6d_link.phase6c_run_id != phase6c.run_id
            or phase6d_link.phase6c_stage_id != phase6c.stage_id
            or phase6d_link.phase6b_run_id != phase6b.run_id
            or phase6d_link.phase6a_run_id != phase6a.run_id
            or phase6d_link.capital_plan_id != phase6d.source.capital_plan_id
            or phase6d_link.capital_snapshot_id != phase6d.source.capital_snapshot_id
            or phase6d_link.capital_snapshot_run_id != phase6d.source.capital_snapshot_run_id
            or phase6d_link.asset_cash_bucket_id != phase6d.source.asset_cash_bucket_id
        ):
            cls._inconsistent("Phase 6A-6D source-link identities")
        upstream = (
            phase6a_link.decision_run_id,
            phase6a_link.linked_parent_run_id,
            phase6a_link.target_child_run_id,
            phase6a_link.standardized_state_run_id,
        )
        for link in (phase6b_link, phase6c_link, phase6d_link):
            if (
                link.decision_run_id,
                link.linked_parent_run_id,
                link.target_child_run_id,
                link.standardized_state_run_id,
            ) != upstream:
                cls._inconsistent("upstream Run IDs")
        for link in (phase6b_link, phase6c_link):
            if (
                link.decision_result_id != phase6a_link.decision_result_id
                or link.intent_id != phase6a_link.intent_id
                or link.target_position_link_id
                != phase6a_link.target_position_link_id
                or link.target_calculation_id != phase6a_link.target_calculation_id
                or link.standardized_state_calculation_id
                != phase6a_link.standardized_state_calculation_id
            ):
                cls._inconsistent("upstream result/calculation IDs")


Getter: TypeAlias = Callable[[TargetAdjustmentRiskChainView], ComparisonValue]

_COMPARISON_FIELDS: tuple[tuple[str, Getter], ...] = (
    ("Symbol", lambda chain: chain.symbol),
    ("Action", lambda chain: chain.action),
    ("As of UTC", lambda chain: chain.as_of_utc),
    ("Requested notional USD", lambda chain: chain.phase6a.source.requested_notional_usd),
    ("Current exposure USD", lambda chain: chain.phase6a.source.current_exposure_usd),
    ("Target exposure USD", lambda chain: chain.phase6a.source.target_exposure_usd),
    ("Phase 6A status", lambda chain: chain.phase6a.status.value),
    ("Rule 1 version", lambda chain: chain.phase6b.rule.rule_version),
    ("Rule 1 cap USD", lambda chain: chain.phase6b.rule.max_target_exposure_usd),
    ("Rule 1 output USD", lambda chain: chain.phase6b.rule.cap_constrained_candidate_notional_usd),
    ("Rule 1 reduction USD", lambda chain: chain.phase6b.rule.reduction_usd),
    ("Rule 1 outcome", lambda chain: chain.phase6b.rule.outcome.value),
    ("Rule 2 version", lambda chain: chain.phase6c.rule.rule_version),
    ("Rule 2 basis USD", lambda chain: chain.phase6c.rule.research_capital_basis_usd),
    ("Rule 2 floor USD", lambda chain: chain.phase6c.rule.minimum_research_asset_cash_usd),
    ("Rule 2 output USD", lambda chain: chain.phase6c.rule.cash_floor_constrained_candidate_notional_usd),
    ("Rule 2 reduction USD", lambda chain: chain.phase6c.rule.reduction_usd),
    ("Rule 2 outcome", lambda chain: chain.phase6c.rule.outcome.value),
    ("Rule 3 version", lambda chain: chain.phase6d.rule.rule_version),
    ("Capital plan ID", lambda chain: chain.phase6d.source.capital_plan_id),
    ("Capital plan version", lambda chain: chain.phase6d.source.capital_plan_version),
    ("Capital snapshot ID", lambda chain: chain.phase6d.source.capital_snapshot_id),
    ("Selected asset cash USD", lambda chain: chain.phase6d.rule.selected_asset_cash_balance_usd),
    ("Rule 3 output USD", lambda chain: chain.phase6d.rule.asset_cash_constrained_candidate_notional_usd),
    ("Rule 3 reduction USD", lambda chain: chain.phase6d.rule.reduction_usd),
    ("Rule 3 outcome", lambda chain: chain.phase6d.rule.outcome.value),
    ("Final disposition", lambda chain: chain.phase6d.disposition.value),
    ("Research cash reserved", lambda chain: chain.phase6d.research_cash_reserved),
)


__all__ = [
    "RiskChainComparisonField",
    "RiskChainInspectionError",
    "RiskChainInspectionService",
    "TargetAdjustmentRiskChainComparison",
    "TargetAdjustmentRiskChainView",
]
