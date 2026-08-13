"""Write-free deterministic replay for accepted P35 admission evidence."""

from __future__ import annotations

from uuid import UUID

from .asset_admission_engine import CycleTargetAssetAdmissionEngine
from .asset_admission_interfaces import CycleTargetAssetAdmissionQueryService
from .asset_admission_models import CycleTargetAssetAdmissionReplayReport


class CycleTargetAssetAdmissionReplayService:
    def __init__(self, queries: CycleTargetAssetAdmissionQueryService, *, engine=None) -> None:
        self._queries = queries
        self._engine = engine or CycleTargetAssetAdmissionEngine()

    def replay(self, result_id: UUID) -> CycleTargetAssetAdmissionReplayReport:
        original = self._queries.get_cycle_target_asset_admission_result(result_id)
        if original is None:
            raise ValueError("P35 admission result does not exist")
        counter = iter(UUID(int=value) for value in range(1, 10))
        replayed = self._engine.evaluate(
            original.source, original.control, result_id=original.result_id,
            operation_id=original.operation_id, run_id=original.run_id,
            stage_id=original.stage_id, created_at_utc=original.created_at_utc,
            created_by=original.created_by, reason=original.reason,
            software_version=original.software_version, id_factory=lambda: next(counter),
        )
        differences: list[str] = []
        for name in ("status", "reason_codes", "warnings", "approved_notional_usd", "risk_approved_intent_id", "execution_allowed", "live_allowed"):
            if getattr(original, name) != getattr(replayed, name): differences.append(name)
        fields = lambda item: (
            item.rule_id, item.rule_version, item.evaluation_order, item.status,
            item.input_summary, item.expected_condition, item.reason_codes,
            item.severity, item.stop_processing,
        )
        if tuple(map(fields, original.rules)) != tuple(map(fields, replayed.rules)):
            differences.append("rules")
        return CycleTargetAssetAdmissionReplayReport(result_id, not differences, tuple(differences))


__all__ = ["CycleTargetAssetAdmissionReplayService"]
