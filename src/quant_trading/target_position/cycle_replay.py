"""Stored-view and deterministic recalculation replay for P23-3A."""

from __future__ import annotations

from .cycle_engine import CycleTargetPositionEngine
from .cycle_interfaces import CycleTargetPositionQueryService
from .cycle_models import CycleTargetPositionResult, CycleTargetReplayReport


def replay_cycle_target_position(
    historical: CycleTargetPositionResult,
    formula,
    configuration,
    *,
    engine: CycleTargetPositionEngine | None = None,
) -> CycleTargetPositionResult:
    """Recalculate from immutable P29 evidence without changing history."""
    recalculated = (engine or CycleTargetPositionEngine()).calculate(
        formula,
        configuration,
        historical.source,
        result_id=historical.result_id,
        operation_id=historical.operation_id,
        run_id=historical.run_id,
        state_stage_id=historical.state_stage_id,
        target_stage_id=historical.target_stage_id,
        research_capital_basis_usd=historical.research_capital_basis_usd,
        current_position_value_usd=historical.current_position_value_usd,
        created_at_utc=historical.created_at_utc,
        created_by=historical.created_by,
        reason=historical.reason,
        software_version=historical.software_version,
        source_revision=historical.source_revision,
        worktree_state=historical.worktree_state,
    )
    if recalculated != historical:
        raise ValueError("P29 recalculation replay differs from immutable history")
    return recalculated


class CycleTargetPositionReplayService:
    def __init__(
        self,
        queries: CycleTargetPositionQueryService,
        *,
        engine: CycleTargetPositionEngine | None = None,
    ) -> None:
        self._queries = queries
        self._engine = engine or CycleTargetPositionEngine()

    def recalculate(self, result_id) -> CycleTargetPositionResult:
        historical = self._require_result(result_id)
        formula = self._queries.get_formula_definition(historical.formula_definition_id)
        configuration = self._queries.get_configuration(historical.configuration_id)
        if formula is None:
            raise KeyError("P29 formula definition cannot be reloaded")
        if configuration is None:
            raise KeyError("P29 asset configuration cannot be reloaded")
        return replay_cycle_target_position(
            historical, formula, configuration, engine=self._engine
        )

    def verify(self, result_id) -> CycleTargetReplayReport:
        historical = self._require_result(result_id)
        try:
            recalculated = self.recalculate(result_id)
        except ValueError as exc:
            return CycleTargetReplayReport(
                historical.result_id,
                historical.calculation_fingerprint,
                "mismatch",
                False,
                (str(exc),),
            )
        return CycleTargetReplayReport(
            historical.result_id,
            historical.calculation_fingerprint,
            recalculated.calculation_fingerprint,
            True,
            (),
        )

    def compare(self, left_id, right_id) -> tuple[str, ...]:
        left = self._require_result(left_id)
        right = self._require_result(right_id)
        if left.source.symbol != right.source.symbol:
            raise ValueError("P29 comparison requires the same symbol")
        return (
            f"source P28 step: {left.source.source_step_id} → {right.source.source_step_id}",
            f"formula/config: v{left.formula_definition_version}/v{left.configuration_version} "
            f"→ v{right.formula_definition_version}/v{right.configuration_version}",
            f"region: {left.region.value} → {right.region.value}",
            f"x: {left.trace.normalized_state.decimal_text} → "
            f"{right.trace.normalized_state.decimal_text}",
            f"target fraction: {left.target_fraction} → {right.target_fraction}",
            f"adjustment USD: {left.adjustment_value_usd} → {right.adjustment_value_usd}",
            f"fingerprint equal: "
            f"{left.calculation_fingerprint == right.calculation_fingerprint}",
        )

    def _require_result(self, result_id) -> CycleTargetPositionResult:
        result = self._queries.get_result(result_id)
        if result is None:
            raise KeyError("P29 result does not exist")
        return result


__all__ = ["CycleTargetPositionReplayService", "replay_cycle_target_position"]
