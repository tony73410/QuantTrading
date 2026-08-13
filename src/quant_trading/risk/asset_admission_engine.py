"""Locked structural/frozen-state gate for P23-4C1."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from uuid import UUID, uuid4

from .asset_admission_models import (
    ASSET_ADMISSION_CONTROL_CALENDAR_DEFINITION_ID,
    ASSET_ADMISSION_CONTROL_COMPONENT_ID,
    ASSET_ADMISSION_CONTROL_COMPONENT_VERSION,
    AssetTradingControlEvidence,
    CycleTargetAssetAdmissionReviewResult,
    CycleTargetAssetAdmissionRuleResult,
    CycleTargetAssetAdmissionSource,
    CycleTargetAssetAdmissionStatus,
)
from .target_adjustment_models import StructuralRuleSeverity, StructuralRuleStatus


class CycleTargetAssetAdmissionEngine:
    def evaluate(self, source: CycleTargetAssetAdmissionSource, control: AssetTradingControlEvidence | None, *, result_id: UUID, operation_id: UUID, run_id: UUID, stage_id: UUID, created_at_utc: datetime, created_by: str, reason: str, software_version: str, id_factory: Callable[[], UUID] = uuid4) -> CycleTargetAssetAdmissionReviewResult:
        rules: list[CycleTargetAssetAdmissionRuleResult] = []

        def rule(rule_id, name, order, status, summary, expected, codes, severity, stop=False):
            rules.append(CycleTargetAssetAdmissionRuleResult(
                id_factory(), result_id, run_id, stage_id, rule_id, "1", name, order,
                status, summary, expected, tuple(codes), severity, stop, created_at_utc,
            ))

        if source.p33_status != "manual_review_required" or source.execution_allowed or source.live_allowed:
            rule("P33_STRUCTURAL_REVIEW_INTEGRITY", "P33 structural review integrity", 1,
                 StructuralRuleStatus.BLOCKED, f"P33 status={source.p33_status}",
                 "exact P33 result must be structurally valid, manual-review-only and non-executable",
                 ("P35_INVALID_P33_SOURCE",), StructuralRuleSeverity.CRITICAL, True)
            return self._result(source, control, CycleTargetAssetAdmissionStatus.BLOCKED_INVALID_SOURCE,
                                rules, ("P35_INVALID_P33_SOURCE",), result_id, operation_id, run_id,
                                stage_id, created_at_utc, created_by, reason, software_version)
        rule("P33_STRUCTURAL_REVIEW_INTEGRITY", "P33 structural review integrity", 1,
             StructuralRuleStatus.PASSED, f"P33 result {source.p33_result_id} is manual-review-only",
             "exact P33 result must be structurally valid and non-executable",
             ("P35_P33_SOURCE_VALID",), StructuralRuleSeverity.INFO)

        if control is None:
            rule("ASSET_TRADING_CONTROL_AVAILABILITY", "Trading-control evidence availability", 2,
                 StructuralRuleStatus.BLOCKED, f"No effective control event exists for {source.symbol}",
                 "one exact effective ELIGIBLE/FROZEN event must exist",
                 ("P35_MISSING_TRADING_CONTROL",), StructuralRuleSeverity.CRITICAL, True)
            return self._result(source, None, CycleTargetAssetAdmissionStatus.BLOCKED_MISSING_TRADING_CONTROL,
                                rules, ("P35_MISSING_TRADING_CONTROL",), result_id, operation_id, run_id,
                                stage_id, created_at_utc, created_by, reason, software_version)
        if (
            control.symbol != source.symbol
            or control.effective_at_utc > created_at_utc
            or control.execution_allowed
            or control.live_allowed
            or control.component_id != ASSET_ADMISSION_CONTROL_COMPONENT_ID
            or control.component_version != ASSET_ADMISSION_CONTROL_COMPONENT_VERSION
            or control.mapping_version != 1
            or control.calendar_definition_id != ASSET_ADMISSION_CONTROL_CALENDAR_DEFINITION_ID
        ):
            rule("ASSET_TRADING_CONTROL_AVAILABILITY", "Trading-control evidence availability", 2,
                 StructuralRuleStatus.BLOCKED, "Control identity/time/safety does not match the P33 symbol and review time",
                 "exact effective non-executable control evidence must match the P33 symbol",
                 ("P35_INVALID_TRADING_CONTROL",), StructuralRuleSeverity.CRITICAL, True)
            return self._result(source, control, CycleTargetAssetAdmissionStatus.BLOCKED_INVALID_SOURCE,
                                rules, ("P35_INVALID_TRADING_CONTROL",), result_id, operation_id, run_id,
                                stage_id, created_at_utc, created_by, reason, software_version)
        rule("ASSET_TRADING_CONTROL_AVAILABILITY", "Trading-control evidence availability", 2,
             StructuralRuleStatus.PASSED, f"Effective event {control.event_id} says {control.status}",
             "one exact effective ELIGIBLE/FROZEN event must exist",
             ("P35_TRADING_CONTROL_AVAILABLE",), StructuralRuleSeverity.INFO)

        if control.status == "frozen":
            rule("FROZEN_ASSET_BLOCK", "Frozen asset admission block", 3,
                 StructuralRuleStatus.BLOCKED, f"{source.symbol} is FROZEN; {source.action} is blocked",
                 "both increase and decrease suggestions require ELIGIBLE status",
                 ("P35_FROZEN_ASSET",), StructuralRuleSeverity.CRITICAL, True)
            status, codes = CycleTargetAssetAdmissionStatus.BLOCKED_FROZEN_ASSET, ("P35_FROZEN_ASSET",)
        else:
            rule("FROZEN_ASSET_BLOCK", "Frozen asset admission block", 3,
                 StructuralRuleStatus.MANUAL_REVIEW, f"{source.symbol} is ELIGIBLE; numerical Risk remains absent",
                 "eligible evidence may proceed only to manual review",
                 ("P35_ELIGIBLE_MANUAL_REVIEW",), StructuralRuleSeverity.WARNING)
            status, codes = CycleTargetAssetAdmissionStatus.MANUAL_REVIEW_REQUIRED, ("P35_ELIGIBLE_MANUAL_REVIEW",)
        return self._result(source, control, status, rules, codes, result_id, operation_id, run_id,
                            stage_id, created_at_utc, created_by, reason, software_version)

    @staticmethod
    def _result(source, control, status, rules, codes, result_id, operation_id, run_id, stage_id, created, created_by, reason, software_version):
        return CycleTargetAssetAdmissionReviewResult(
            result_id, operation_id, run_id, stage_id, source, control, status,
            tuple(rules), tuple(codes), (), created, created_by, reason, software_version,
        )


__all__ = ["CycleTargetAssetAdmissionEngine"]
