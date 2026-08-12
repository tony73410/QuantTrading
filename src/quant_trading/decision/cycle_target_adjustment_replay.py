"""Read-only deterministic recalculation replay for P23-4A Decision results."""

from __future__ import annotations

from uuid import UUID

from quant_trading.run_history import SoftwareIdentity, WorktreeState

from .cycle_target_adjustment_engine import CycleTargetAdjustmentDecisionEngine
from .cycle_target_adjustment_interfaces import CycleTargetAdjustmentDecisionQueryService
from .cycle_target_adjustment_models import (
    CycleTargetAdjustmentDecisionResult,
    CycleTargetAdjustmentReplayReport,
)


def replay_cycle_target_adjustment_decision(
    historical: CycleTargetAdjustmentDecisionResult,
    *,
    engine: CycleTargetAdjustmentDecisionEngine | None = None,
) -> CycleTargetAdjustmentDecisionResult:
    """Recalculate from immutable P31 evidence without creating new history."""
    intent_id = historical.intents[0].intent_id if historical.intents else UUID(int=0)
    recalculated = (engine or CycleTargetAdjustmentDecisionEngine()).evaluate(
        historical.source,
        decision_result_id=historical.decision_result_id,
        intent_id=intent_id,
        operation_id=historical.operation_id,
        run_id=historical.run_id,
        target_stage_id=historical.target_stage_id,
        decision_stage_id=historical.decision_stage_id,
        created_at_utc=historical.created_at_utc,
        created_by=historical.created_by,
        reason=historical.reason,
        software=SoftwareIdentity(
            historical.software_version,
            historical.source_revision,
            WorktreeState(historical.worktree_state),
        ),
    )
    if recalculated != historical:
        raise ValueError("P31 recalculation replay differs from immutable history")
    return recalculated


class CycleTargetAdjustmentDecisionReplayService:
    """Reload and verify one persisted P31 result without database writes."""

    def __init__(
        self,
        queries: CycleTargetAdjustmentDecisionQueryService,
        *,
        engine: CycleTargetAdjustmentDecisionEngine | None = None,
    ) -> None:
        self._queries = queries
        self._engine = engine or CycleTargetAdjustmentDecisionEngine()

    def recalculate(self, decision_result_id: UUID) -> CycleTargetAdjustmentDecisionResult:
        historical = self._require_result(decision_result_id)
        return replay_cycle_target_adjustment_decision(historical, engine=self._engine)

    def verify(self, decision_result_id: UUID) -> CycleTargetAdjustmentReplayReport:
        historical = self._require_result(decision_result_id)
        try:
            self.recalculate(decision_result_id)
        except ValueError as exc:
            return CycleTargetAdjustmentReplayReport(
                historical.decision_result_id,
                False,
                (str(exc),),
            )
        return CycleTargetAdjustmentReplayReport(
            historical.decision_result_id,
            True,
            (),
        )

    def _require_result(self, decision_result_id: UUID) -> CycleTargetAdjustmentDecisionResult:
        result = self._queries.get_cycle_target_adjustment_result(decision_result_id)
        if result is None:
            raise KeyError("P31 Decision result does not exist")
        return result


__all__ = [
    "CycleTargetAdjustmentDecisionReplayService",
    "replay_cycle_target_adjustment_decision",
]
