"""Pure P23-4A Decision mapper over one validated source-neutral P29 input."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from quant_trading.run_history import SoftwareIdentity

from .cycle_target_adjustment_models import (
    CycleTargetAdjustmentDecisionResult,
    CycleTargetAdjustmentResultStatus,
    CycleTargetAdjustmentTradeIntent,
    CycleTargetDecisionInput,
)
from .exact_target_difference import map_exact_target_difference
from .models import DecisionAction


class CycleTargetAdjustmentDecisionEngine:
    """Apply the shared exact-difference rule; never resolve sources or perform Risk."""

    def evaluate(
        self,
        source: CycleTargetDecisionInput,
        *,
        decision_result_id: UUID,
        intent_id: UUID,
        operation_id: UUID,
        run_id: UUID,
        target_stage_id: UUID,
        decision_stage_id: UUID,
        created_at_utc: datetime,
        created_by: str,
        reason: str,
        software: SoftwareIdentity,
    ) -> CycleTargetAdjustmentDecisionResult:
        mapping = map_exact_target_difference(source.adjustment_value_usd)
        if mapping.action is DecisionAction.HOLD:
            status = CycleTargetAdjustmentResultStatus.HOLD
            intents: tuple[CycleTargetAdjustmentTradeIntent, ...] = ()
        else:
            status = CycleTargetAdjustmentResultStatus.INTENT_CREATED
            intents = (
                CycleTargetAdjustmentTradeIntent(
                    intent_id=intent_id,
                    decision_result_id=decision_result_id,
                    operation_id=operation_id,
                    run_id=run_id,
                    decision_stage_id=decision_stage_id,
                    source_result_id=source.source_result_id,
                    source_run_id=source.source_run_id,
                    symbol=source.symbol,
                    source_session=source.source_session,
                    source_available_at_utc=source.source_available_at_utc,
                    action=mapping.action,
                    current_exposure_usd=source.current_position_value_usd,
                    target_exposure_usd=source.target_position_value_usd,
                    desired_change_usd=source.adjustment_value_usd,
                    requested_notional_usd=mapping.requested_notional_usd,
                    reason_codes=(mapping.result_reason_code,),
                    created_at_utc=created_at_utc,
                ),
            )
        requested = intents[0].requested_notional_usd if intents else "none"
        explanation = (
            f"{source.symbol} {source.source_session}: P29 target "
            f"{source.target_position_value_usd} USD minus current "
            f"{source.current_position_value_usd} USD equals exact difference "
            f"{source.adjustment_value_usd} USD; action={mapping.action.value}; "
            f"requested_notional={requested}; NO EXECUTION, no Risk review."
        )
        return CycleTargetAdjustmentDecisionResult(
            decision_result_id=decision_result_id,
            operation_id=operation_id,
            run_id=run_id,
            target_stage_id=target_stage_id,
            decision_stage_id=decision_stage_id,
            source=source,
            status=status,
            action=mapping.action,
            intents=intents,
            reason_codes=(mapping.result_reason_code,),
            explanation=explanation,
            created_at_utc=created_at_utc,
            created_by=created_by,
            reason=reason,
            software_version=software.package_version,
            source_revision=software.source_revision,
            worktree_state=software.worktree_state.value,
        )


__all__ = ["CycleTargetAdjustmentDecisionEngine"]
