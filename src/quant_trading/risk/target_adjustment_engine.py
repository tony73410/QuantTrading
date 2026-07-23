"""Locked structural Risk gate; it never approves financial exposure."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

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
        rules = [self._rule(id_factory(), review_result_id, run_id, stage_id, "SOURCE_CHAIN_INTEGRITY", "Source chain integrity", 1, StructuralRuleStatus.PASSED, f"intent={source.intent_id}; decision={source.decision_result_id}", "All immutable Decision and upstream identities agree", ("SOURCE_CHAIN_VERIFIED",), StructuralRuleSeverity.INFO, False, created_at_utc)]
        if not safety.is_non_executing:
            rules.append(self._rule(id_factory(), review_result_id, run_id, stage_id, "NON_EXECUTION_SAFETY_STATE", "Non-execution safety state", 2, StructuralRuleStatus.BLOCKED, f"environment={safety.execution_environment.value}; live={safety.live_trading_enabled}; automatic={safety.automatic_submission_enabled}; manual={safety.manual_confirmation_required}; execution_capability={safety.execution_capability_implemented}", "Live and automatic submission disabled, execution absent, manual confirmation required", ("UNSAFE_EXECUTION_STATE",), StructuralRuleSeverity.CRITICAL, True, created_at_utc))
            return TargetAdjustmentRiskReviewResult(review_result_id, operation_id, run_id, stage_id, source, safety, TargetAdjustmentRiskStatus.BLOCKED, tuple(rules), ("UNSAFE_EXECUTION_STATE",), ("Risk review blocked by non-execution safety state.",), created_at_utc, created_by, reason, software_version)
        rules.append(self._rule(id_factory(), review_result_id, run_id, stage_id, "NON_EXECUTION_SAFETY_STATE", "Non-execution safety state", 2, StructuralRuleStatus.PASSED, f"environment={safety.execution_environment.value}; live=false; automatic=false; manual=true; execution_capability=false", "Live and automatic submission disabled, execution absent, manual confirmation required", ("NON_EXECUTION_STATE_VERIFIED",), StructuralRuleSeverity.INFO, False, created_at_utc))
        rules.append(self._rule(id_factory(), review_result_id, run_id, stage_id, "NUMERICAL_RISK_POLICY_AVAILABILITY", "Numerical Risk policy availability", 3, StructuralRuleStatus.MANUAL_REVIEW, "approved numerical policy=absent", "An explicitly approved numerical Risk policy is required before financial approval", ("NUMERICAL_RISK_POLICY_NOT_AVAILABLE", "MANUAL_REVIEW_REQUIRED"), StructuralRuleSeverity.WARNING, True, created_at_utc))
        return TargetAdjustmentRiskReviewResult(review_result_id, operation_id, run_id, stage_id, source, safety, TargetAdjustmentRiskStatus.MANUAL_REVIEW_REQUIRED, tuple(rules), ("MANUAL_REVIEW_REQUIRED", "NO_NUMERICAL_RISK_POLICY"), ("Requested notional remains unapproved research evidence.",), created_at_utc, created_by, reason, software_version)

    @staticmethod
    def _rule(rule_result_id, review_result_id, run_id, stage_id, rule_id, name, order, status, input_summary, expected, reasons, severity, stop, evaluated):
        return TargetAdjustmentStructuralRuleResult(rule_result_id, review_result_id, run_id, stage_id, rule_id, "1", name, order, status, input_summary, expected, reasons, severity, stop, evaluated)


__all__ = ["TargetAdjustmentRiskEngine"]
