"""Pure exact-Decimal single-asset exposure-cap Risk preview."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from .exposure_cap_models import (
    ZERO,
    ExposureCapDisposition,
    ExposureCapRuleOutcome,
    ExposureCapRuleResult,
    LinkedExposureCapPreviewInput,
    TargetAdjustmentExposureCapPreviewResult,
)


class SingleAssetExposureCapEngine:
    def evaluate(
        self,
        source: LinkedExposureCapPreviewInput,
        *,
        preview_result_id: UUID,
        operation_id: UUID,
        run_id: UUID,
        stage_id: UUID,
        created_at_utc: datetime,
        created_by: str,
        reason: str,
        software_version: str,
        id_factory,
    ) -> TargetAdjustmentExposureCapPreviewResult:
        evidence = source.phase6a_source
        current = evidence.current_exposure_usd
        target = evidence.target_exposure_usd
        original = evidence.requested_notional_usd
        cap = source.definition.max_target_exposure_usd
        if evidence.action == "decrease":
            candidate = original
            outcome = ExposureCapRuleOutcome.PRESERVED_RISK_REDUCING_DIRECTION
            reasons = ("RISK_REDUCING_DIRECTION_PRESERVED", "CAP_DOES_NOT_ENLARGE_OR_REVERSE")
        elif target <= cap:
            candidate = original
            outcome = ExposureCapRuleOutcome.PASSED_WITHIN_CAP
            reasons = ("TARGET_WITHIN_EXPOSURE_CAP", "MANUAL_REVIEW_STILL_REQUIRED")
        elif current < cap:
            candidate = cap - current
            outcome = ExposureCapRuleOutcome.REDUCED_TO_CAP
            reasons = ("REQUEST_REDUCED_TO_EXPOSURE_CAP", "MANUAL_REVIEW_STILL_REQUIRED")
        else:
            candidate = ZERO
            outcome = ExposureCapRuleOutcome.BLOCKED_NO_INCREASE_CAPACITY
            reasons = ("NO_INCREASE_CAPACITY", "BLOCKED_BY_EXPOSURE_CAP")
        rule = ExposureCapRuleResult(
            id_factory(), preview_result_id, run_id, stage_id, evidence.action,
            current, target, original, cap, candidate, original - candidate,
            outcome, reasons, created_at_utc,
        )
        disposition = (
            ExposureCapDisposition.BLOCKED_BY_EXPOSURE_CAP
            if candidate == ZERO
            else ExposureCapDisposition.MANUAL_REVIEW_REQUIRED
        )
        warnings = (
            ("One exposure-cap rule is not complete Risk approval.",)
            if candidate > ZERO
            else ("Increase blocked because no exposure-cap capacity remains.",)
        )
        return TargetAdjustmentExposureCapPreviewResult(
            preview_result_id, operation_id, run_id, stage_id, source, rule,
            disposition,
            (disposition.value.upper(), "NO_RISK_APPROVAL", "NO_EXECUTION"),
            warnings, created_at_utc, created_by, reason, software_version,
        )


__all__ = ["SingleAssetExposureCapEngine"]
