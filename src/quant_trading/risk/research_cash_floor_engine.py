"""Pure exact-Decimal second-rule research cash-floor Risk preview."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from .research_cash_floor_models import (
    ZERO,
    LinkedResearchCashFloorPreviewInput,
    ResearchCashFloorDisposition,
    ResearchCashFloorRuleOutcome,
    ResearchCashFloorRuleResult,
    TargetAdjustmentResearchCashFloorPreviewResult,
)


class ResearchAssetCashFloorEngine:
    def evaluate(
        self,
        source: LinkedResearchCashFloorPreviewInput,
        *,
        preview_result_id: UUID,
        operation_id: UUID,
        run_id: UUID,
        stage_id: UUID,
        created_at_utc: datetime,
        created_by: str,
        reason: str,
        software_version: str,
        id_factory,
    ) -> TargetAdjustmentResearchCashFloorPreviewResult:
        phase6b = source.phase6b_result
        current = phase6b.rule.current_exposure_usd
        candidate_before = phase6b.cap_constrained_candidate_notional_usd
        basis = source.research_capital_basis_usd
        floor = source.definition.minimum_research_asset_cash_usd
        pre_cash = basis - current
        capacity = max(pre_cash - floor, ZERO)
        if source.action == "decrease":
            candidate = candidate_before
            post_cash = basis - (current - candidate)
            outcome = (
                ResearchCashFloorRuleOutcome.PRESERVED_RESEARCH_CASH_INCREASING_DIRECTION
            )
            reasons = (
                "RESEARCH_CASH_INCREASING_DIRECTION_PRESERVED",
                "CASH_FLOOR_DOES_NOT_ENLARGE_OR_REVERSE",
            )
        else:
            candidate = min(candidate_before, capacity)
            post_cash = basis - (current + candidate)
            if candidate_before <= capacity:
                outcome = (
                    ResearchCashFloorRuleOutcome.PASSED_AT_OR_ABOVE_CASH_FLOOR
                )
                reasons = (
                    "POST_ACTION_RESEARCH_CASH_AT_OR_ABOVE_FLOOR",
                    "MANUAL_REVIEW_STILL_REQUIRED",
                )
            elif capacity > ZERO:
                outcome = ResearchCashFloorRuleOutcome.REDUCED_TO_CASH_FLOOR
                reasons = (
                    "REQUEST_REDUCED_TO_RESEARCH_CASH_FLOOR",
                    "MANUAL_REVIEW_STILL_REQUIRED",
                )
            else:
                outcome = (
                    ResearchCashFloorRuleOutcome.BLOCKED_NO_RESEARCH_CASH_CAPACITY
                )
                reasons = (
                    "NO_RESEARCH_CASH_CAPACITY",
                    "BLOCKED_BY_RESEARCH_CASH_FLOOR",
                )
        shortfall = max(floor - post_cash, ZERO)
        rule = ResearchCashFloorRuleResult(
            id_factory(),
            preview_result_id,
            run_id,
            stage_id,
            source.action,
            basis,
            current,
            candidate_before,
            floor,
            pre_cash,
            capacity,
            candidate,
            post_cash,
            shortfall,
            candidate_before - candidate,
            outcome,
            reasons,
            created_at_utc,
        )
        disposition = (
            ResearchCashFloorDisposition.BLOCKED_BY_RESEARCH_CASH_FLOOR
            if candidate == ZERO
            else ResearchCashFloorDisposition.MANUAL_REVIEW_REQUIRED
        )
        warnings = (
            (
                "Two numerical research rules are not complete Risk approval.",
                "Research cash is hypothetical Phase 5C evidence, not account cash.",
            )
            if candidate > ZERO
            else (
                "Increase blocked because no hypothetical research cash capacity remains.",
            )
        )
        return TargetAdjustmentResearchCashFloorPreviewResult(
            preview_result_id,
            operation_id,
            run_id,
            stage_id,
            source,
            rule,
            disposition,
            (disposition.value.upper(), "NO_RISK_APPROVAL", "NO_EXECUTION"),
            warnings,
            created_at_utc,
            created_by,
            reason,
            software_version,
        )


__all__ = ["ResearchAssetCashFloorEngine"]
