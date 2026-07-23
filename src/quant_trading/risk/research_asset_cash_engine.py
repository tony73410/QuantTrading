"""Pure exact-Decimal order-3 research asset-cash Risk preview."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from .research_asset_cash_models import (
    ZERO,
    LinkedResearchAssetCashPreviewInput,
    ResearchAssetCashDisposition,
    ResearchAssetCashRuleOutcome,
    ResearchAssetCashRuleResult,
    TargetAdjustmentResearchAssetCashPreviewResult,
)


class ResearchAssetCashAvailabilityEngine:
    def evaluate(
        self,
        source: LinkedResearchAssetCashPreviewInput,
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
    ) -> TargetAdjustmentResearchAssetCashPreviewResult:
        before = source.phase6c_candidate_notional_usd
        balance = source.asset_cash_balance_usd
        if source.action == "decrease":
            candidate = before
            post = balance + candidate
            outcome = (
                ResearchAssetCashRuleOutcome.PRESERVED_RESEARCH_ASSET_CASH_INCREASING_DIRECTION
            )
            reasons = (
                "RESEARCH_ASSET_CASH_INCREASING_DIRECTION_PRESERVED",
                "NO_CAPITAL_MUTATION_OR_RESERVATION",
            )
        else:
            candidate = min(before, balance)
            post = balance - candidate
            if before <= balance:
                outcome = ResearchAssetCashRuleOutcome.PASSED_WITHIN_RESEARCH_ASSET_CASH
                reasons = ("WITHIN_SELECTED_RESEARCH_ASSET_CASH", "NOT_RESERVED")
            elif balance > ZERO:
                outcome = ResearchAssetCashRuleOutcome.REDUCED_TO_RESEARCH_ASSET_CASH
                reasons = ("REDUCED_TO_SELECTED_RESEARCH_ASSET_CASH", "NOT_RESERVED")
            else:
                outcome = ResearchAssetCashRuleOutcome.BLOCKED_NO_RESEARCH_ASSET_CASH
                reasons = ("NO_SELECTED_RESEARCH_ASSET_CASH", "BLOCKED")
        rule = ResearchAssetCashRuleResult(
            id_factory(),
            preview_result_id,
            run_id,
            stage_id,
            source.action,
            before,
            balance,
            balance,
            candidate,
            post,
            before - candidate,
            outcome,
            reasons,
            created_at_utc,
        )
        disposition = (
            ResearchAssetCashDisposition.BLOCKED_BY_RESEARCH_ASSET_CASH
            if candidate == ZERO
            else ResearchAssetCashDisposition.MANUAL_REVIEW_REQUIRED
        )
        warnings = (
            "Selected research asset cash is planning evidence, not account cash.",
            "No cash is reserved; another preview may reuse the same balance.",
            "Three numerical research rules are not complete Risk approval.",
        )
        return TargetAdjustmentResearchAssetCashPreviewResult(
            preview_result_id,
            operation_id,
            run_id,
            stage_id,
            source,
            rule,
            disposition,
            (disposition.value.upper(), "RESEARCH_CASH_NOT_RESERVED", "NO_EXECUTION"),
            warnings,
            False,
            created_at_utc,
            created_by,
            reason,
            software_version,
        )


__all__ = ["ResearchAssetCashAvailabilityEngine"]
