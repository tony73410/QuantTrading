"""Write-free deterministic replay for accepted P33 evidence."""

from __future__ import annotations

from uuid import UUID

from .cycle_target_risk_engine import CycleTargetRiskEngine
from .cycle_target_risk_interfaces import CycleTargetRiskQueryService
from .cycle_target_risk_models import CycleTargetRiskReplayReport


class CycleTargetRiskReplayService:
    def __init__(self, queries: CycleTargetRiskQueryService, *, engine: CycleTargetRiskEngine | None = None) -> None:
        self._queries = queries
        self._engine = engine or CycleTargetRiskEngine()

    def replay(self, review_result_id: UUID) -> CycleTargetRiskReplayReport:
        original = self._queries.get_cycle_target_risk_result(review_result_id)
        if original is None:
            raise ValueError("P33 review result does not exist")
        counter = iter(UUID(int=value) for value in range(1, 10))
        replayed = self._engine.evaluate(
            original.source, original.safety_snapshot,
            review_result_id=original.review_result_id,
            operation_id=original.operation_id, run_id=original.run_id,
            stage_id=original.stage_id, created_at_utc=original.created_at_utc,
            created_by=original.created_by, reason=original.reason,
            software_version=original.software_version, id_factory=lambda: next(counter),
        )
        differences: list[str] = []
        for name in ("status", "reason_codes", "warnings", "approved_notional_usd", "risk_approved_intent_id", "execution_allowed", "live_allowed"):
            if getattr(original, name) != getattr(replayed, name):
                differences.append(name)
        original_rules = tuple((x.rule_id, x.rule_version, x.evaluation_order, x.status, x.input_summary, x.expected_condition, x.reason_codes, x.severity, x.stop_processing) for x in original.rules)
        replayed_rules = tuple((x.rule_id, x.rule_version, x.evaluation_order, x.status, x.input_summary, x.expected_condition, x.reason_codes, x.severity, x.stop_processing) for x in replayed.rules)
        if original_rules != replayed_rules:
            differences.append("rules")
        return CycleTargetRiskReplayReport(review_result_id, not differences, tuple(differences))


__all__ = ["CycleTargetRiskReplayService"]
