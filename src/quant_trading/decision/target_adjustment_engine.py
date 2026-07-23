"""Pure exact-sign mapper for target-adjustment Decision previews."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from quant_trading.run_history import SoftwareIdentity

from .models import DecisionAction
from .target_adjustment_models import (
    LinkedTargetDecisionInput,
    TargetAdjustmentDecisionResult,
    TargetAdjustmentDecisionStatus,
    TargetAdjustmentTradeIntent,
    ZERO,
)


class TargetAdjustmentDecisionEngine:
    """Map the exact copied difference; no threshold, rounding, EXIT, or Risk."""

    def evaluate(
        self,
        source: LinkedTargetDecisionInput,
        *,
        decision_result_id: UUID,
        intent_id: UUID,
        operation_id: UUID,
        run_id: UUID,
        stage_id: UUID,
        created_at_utc: datetime,
        created_by: str,
        reason: str,
        software: SoftwareIdentity,
    ) -> TargetAdjustmentDecisionResult:
        difference = source.adjustment_value_usd
        if difference == ZERO:
            action = DecisionAction.HOLD
            status = TargetAdjustmentDecisionStatus.HOLD
            intents: tuple[TargetAdjustmentTradeIntent, ...] = ()
            reasons = ("TARGET_POSITION_EQUAL_CURRENT",)
        else:
            action = DecisionAction.INCREASE if difference > ZERO else DecisionAction.DECREASE
            status = TargetAdjustmentDecisionStatus.INTENT_CREATED
            reasons = ("TARGET_POSITION_DIFFERENCE",)
            intents = (
                TargetAdjustmentTradeIntent(
                    intent_id,
                    decision_result_id,
                    operation_id,
                    run_id,
                    stage_id,
                    source.target_position_link_id,
                    source.target_calculation_id,
                    source.symbol,
                    source.as_of_utc,
                    action,
                    source.current_position_value_usd,
                    source.target_position_value_usd,
                    difference,
                    abs(difference),
                    reasons,
                    created_at_utc,
                ),
            )
        return TargetAdjustmentDecisionResult(
            decision_result_id,
            operation_id,
            run_id,
            stage_id,
            source,
            status,
            action,
            intents,
            reasons,
            created_at_utc,
            created_by,
            reason,
            software.package_version,
            software.source_revision,
            software.worktree_state.value,
        )


__all__ = ["TargetAdjustmentDecisionEngine"]
