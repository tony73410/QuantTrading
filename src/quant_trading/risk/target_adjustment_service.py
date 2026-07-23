"""Risk-owned service for one durable target-adjustment structural review."""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID, uuid4

from quant_trading.error_codes import ErrorCode
from quant_trading.run_history import SoftwareIdentity

from .target_adjustment_engine import TargetAdjustmentRiskEngine
from .target_adjustment_interfaces import TargetAdjustmentRiskStore
from .target_adjustment_models import (
    LinkedTargetRiskReviewInput,
    RiskSafetyStateSnapshot,
    TargetAdjustmentRiskOperationAttempt,
    TargetAdjustmentRiskReviewCommand,
    TargetAdjustmentRiskReviewOutcome,
    TargetAdjustmentRiskSourceLink,
    TargetAdjustmentRiskStatus,
)

logger = logging.getLogger(__name__)


class TargetAdjustmentRiskService:
    def __init__(self, store: TargetAdjustmentRiskStore, software: SoftwareIdentity, *, engine: TargetAdjustmentRiskEngine | None = None, clock: Callable[[], datetime] = lambda: datetime.now(UTC), id_factory: Callable[[], UUID] = uuid4) -> None:
        self._store, self._software = store, software
        self._engine, self._clock, self._id_factory = engine or TargetAdjustmentRiskEngine(), clock, id_factory

    def review(self, command: TargetAdjustmentRiskReviewCommand, source: LinkedTargetRiskReviewInput, safety: RiskSafetyStateSnapshot, *, run_id: UUID, decision_stage_id: UUID, risk_stage_id: UUID) -> TargetAdjustmentRiskReviewOutcome:
        if command.operation_id is None:
            raise ValueError("target-adjustment Risk review requires an operation ID")
        try:
            created, result_id = self._clock(), self._id_factory()
            result = self._engine.evaluate(source, safety, review_result_id=result_id, operation_id=command.operation_id, run_id=run_id, stage_id=risk_stage_id, created_at_utc=created, created_by=command.created_by, reason=command.reason, software_version=self._software.package_version, id_factory=self._id_factory)
            operation = TargetAdjustmentRiskOperationAttempt(self._id_factory(), command.operation_id, run_id, decision_stage_id, risk_stage_id, command.target_adjustment_trade_intent_id, result.status, command.requested_at_utc, created, command.session_id, command.request_id, command.created_by, command.reason, source, safety, result.review_result_id)
            link = TargetAdjustmentRiskSourceLink(self._id_factory(), command.operation_id, result.review_result_id, run_id, risk_stage_id, source.decision_result_id, source.intent_id, source.decision_run_id, source.linked_parent_run_id, source.target_child_run_id, source.standardized_state_run_id, source.target_position_link_id, source.target_calculation_id, source.standardized_state_calculation_id, created)
            self._store.save_completed(result, operation, link)
            return TargetAdjustmentRiskReviewOutcome(operation.attempt_id, operation.operation_id, run_id, result.status, f"{source.symbol}: {result.status.value}; requested {source.requested_notional_usd} USD remains unapproved; NO EXECUTION.", source.decision_run_id, source.linked_parent_run_id, source.target_child_run_id, source.standardized_state_run_id, result.review_result_id)
        except (ValueError, TypeError) as exc:
            return self._failure(command, run_id, decision_stage_id, source, safety, exc, invalid=True)
        except Exception as exc:
            logger.exception("Target-adjustment Risk review failed run_id=%s", run_id)
            return self._failure(command, run_id, decision_stage_id, source, safety, exc, invalid=False)

    def _failure(self, command, run_id, decision_stage_id, source, safety, exc, *, invalid):
        status = TargetAdjustmentRiskStatus.INVALID_INPUT if invalid else TargetAdjustmentRiskStatus.FAILED
        code = ErrorCode.TARGET_ADJUSTMENT_RISK.value if invalid else ErrorCode.TARGET_ADJUSTMENT_RISK_STORAGE.value
        summary = str(exc) or "target-adjustment Risk review failed"
        operation = TargetAdjustmentRiskOperationAttempt(self._id_factory(), command.operation_id, run_id, decision_stage_id, None, command.target_adjustment_trade_intent_id, status, command.requested_at_utc, self._clock(), command.session_id, command.request_id, command.created_by, command.reason, source, safety, error_code=code, error_summary=summary)
        try: self._store.save_operation(operation)
        except Exception: logger.exception("Could not persist failed target-adjustment Risk operation")
        return TargetAdjustmentRiskReviewOutcome(operation.attempt_id, operation.operation_id, run_id, status, summary, source.decision_run_id, source.linked_parent_run_id, source.target_child_run_id, source.standardized_state_run_id, error_code=code)


__all__ = ["TargetAdjustmentRiskService"]
