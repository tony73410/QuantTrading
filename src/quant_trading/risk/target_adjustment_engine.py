"""Locked structural Risk gate; it never approves financial exposure."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from ._structural_manual_review_kernel import evaluate_structural_manual_review_gate
from .target_adjustment_models import (
    LinkedTargetRiskReviewInput,
    RiskSafetyStateSnapshot,
    StructuralRuleSeverity,
    StructuralRuleStatus,
    TargetAdjustmentRiskReviewResult,
    TargetAdjustmentRiskStatus,
    TargetAdjustmentStructuralRuleResult,
)


class TargetAdjustmentRiskEngine:
    def evaluate(self, source: LinkedTargetRiskReviewInput, safety: RiskSafetyStateSnapshot, *, review_result_id: UUID, operation_id: UUID, run_id: UUID, stage_id: UUID, created_at_utc: datetime, created_by: str, reason: str, software_version: str, id_factory) -> TargetAdjustmentRiskReviewResult:
        outcome = evaluate_structural_manual_review_gate(
            source_summary=f"intent={source.intent_id}; decision={source.decision_result_id}",
            execution_environment=safety.execution_environment.value,
            live_trading_enabled=safety.live_trading_enabled,
            automatic_submission_enabled=safety.automatic_submission_enabled,
            manual_confirmation_required=safety.manual_confirmation_required,
            execution_capability_implemented=safety.execution_capability_implemented,
        )
        rules = tuple(
            self._rule(
                id_factory(), review_result_id, run_id, stage_id, item.rule_id,
                item.rule_name, item.evaluation_order, StructuralRuleStatus(item.status),
                item.input_summary, item.expected_condition, item.reason_codes,
                StructuralRuleSeverity(item.severity), item.stop_processing, created_at_utc,
            )
            for item in outcome.rules
        )
        return TargetAdjustmentRiskReviewResult(
            review_result_id, operation_id, run_id, stage_id, source, safety,
            TargetAdjustmentRiskStatus(outcome.status), rules, outcome.reason_codes,
            outcome.warnings, created_at_utc, created_by, reason, software_version,
        )

    @staticmethod
    def _rule(rule_result_id, review_result_id, run_id, stage_id, rule_id, name, order, status, input_summary, expected, reasons, severity, stop, evaluated):
        return TargetAdjustmentStructuralRuleResult(rule_result_id, review_result_id, run_id, stage_id, rule_id, "1", name, order, status, input_summary, expected, reasons, severity, stop, evaluated)


__all__ = ["TargetAdjustmentRiskEngine"]
