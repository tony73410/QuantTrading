"""Pure exact-sign mapper for target-adjustment Decision previews."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from quant_trading.run_history import SoftwareIdentity

from .exact_target_difference import map_exact_target_difference
from .models import DecisionAction
from .target_adjustment_models import (
    LinkedTargetDecisionInput,
    TargetAdjustmentDecisionResult,
    TargetAdjustmentDecisionStatus,
    TargetAdjustmentTradeIntent,
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
        mapping = map_exact_target_difference(difference)
        action = mapping.action
        if action is DecisionAction.HOLD:
            status = TargetAdjustmentDecisionStatus.HOLD
            intents: tuple[TargetAdjustmentTradeIntent, ...] = ()
            reasons = (mapping.result_reason_code,)
        else:
            status = TargetAdjustmentDecisionStatus.INTENT_CREATED
            reasons = (mapping.result_reason_code,)
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
                    mapping.requested_notional_usd,
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
