"""P33 structural Risk engine; it cannot approve financial exposure."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from ._structural_manual_review_kernel import evaluate_structural_manual_review_gate
from .cycle_target_risk_models import (
    CycleTargetRiskReviewInput,
    CycleTargetRiskReviewResult,
    CycleTargetRiskStatus,
    CycleTargetStructuralRiskRuleResult,
)
from .target_adjustment_models import (
    RiskSafetyStateSnapshot,
    StructuralRuleSeverity,
    StructuralRuleStatus,
)


class CycleTargetRiskEngine:
    def evaluate(
        self,
        source: CycleTargetRiskReviewInput,
        safety: RiskSafetyStateSnapshot,
        *,
        review_result_id: UUID,
        operation_id: UUID,
        run_id: UUID,
        stage_id: UUID,
        created_at_utc: datetime,
        created_by: str,
        reason: str,
        software_version: str,
        id_factory,
    ) -> CycleTargetRiskReviewResult:
        outcome = evaluate_structural_manual_review_gate(
            source_summary=(
                f"intent={source.intent_id}; decision={source.decision_result_id}; "
                f"cycle_target={source.source_result_id}; reversal={source.source_reversal_result_id}"
            ),
            execution_environment=safety.execution_environment.value,
            live_trading_enabled=safety.live_trading_enabled,
            automatic_submission_enabled=safety.automatic_submission_enabled,
            manual_confirmation_required=safety.manual_confirmation_required,
            execution_capability_implemented=safety.execution_capability_implemented,
        )
        rules = tuple(
            CycleTargetStructuralRiskRuleResult(
                id_factory(), review_result_id, run_id, stage_id, item.rule_id,
                item.rule_version, item.rule_name, item.evaluation_order,
                StructuralRuleStatus(item.status), item.input_summary,
                item.expected_condition, item.reason_codes,
                StructuralRuleSeverity(item.severity), item.stop_processing,
                created_at_utc,
            )
            for item in outcome.rules
        )
        return CycleTargetRiskReviewResult(
            review_result_id, operation_id, run_id, stage_id, source, safety,
            CycleTargetRiskStatus(outcome.status), rules, outcome.reason_codes,
            outcome.warnings, created_at_utc, created_by, reason, software_version,
        )


__all__ = ["CycleTargetRiskEngine"]
