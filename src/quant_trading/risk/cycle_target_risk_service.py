"""Risk-owned durable service for one P33 structural review."""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID, uuid4

from quant_trading.error_codes import ErrorCode
from quant_trading.run_history import SoftwareIdentity

from .cycle_target_risk_engine import CycleTargetRiskEngine
from .cycle_target_risk_interfaces import CycleTargetRiskStore
from .cycle_target_risk_models import (
    CycleTargetRiskOperationAttempt,
    CycleTargetRiskReviewCommand,
    CycleTargetRiskReviewInput,
    CycleTargetRiskReviewOutcome,
    CycleTargetRiskSourceLink,
    CycleTargetRiskStatus,
)
from .target_adjustment_models import RiskSafetyStateSnapshot

logger = logging.getLogger(__name__)


class CycleTargetRiskService:
    def __init__(self, store: CycleTargetRiskStore, software: SoftwareIdentity, *, engine: CycleTargetRiskEngine | None = None, clock: Callable[[], datetime] = lambda: datetime.now(UTC), id_factory: Callable[[], UUID] = uuid4) -> None:
        self._store, self._software = store, software
        self._engine, self._clock, self._id_factory = engine or CycleTargetRiskEngine(), clock, id_factory

    def review(self, command: CycleTargetRiskReviewCommand, source: CycleTargetRiskReviewInput, safety: RiskSafetyStateSnapshot, *, run_id: UUID, decision_stage_id: UUID, risk_stage_id: UUID) -> CycleTargetRiskReviewOutcome:
        if command.operation_id is None:
            raise ValueError("P33 review requires an operation ID")
        try:
            created, result_id = self._clock(), self._id_factory()
            result = self._engine.evaluate(
                source, safety, review_result_id=result_id, operation_id=command.operation_id,
                run_id=run_id, stage_id=risk_stage_id, created_at_utc=created,
                created_by=command.created_by, reason=command.reason,
                software_version=self._software.package_version, id_factory=self._id_factory,
            )
            operation = CycleTargetRiskOperationAttempt(
                self._id_factory(), command.operation_id, run_id, decision_stage_id,
                risk_stage_id, command.command_fingerprint, command.intent_id,
                command.decision_result_id, command.decision_run_id, result.status,
                command.requested_at_utc, created, command.session_id, command.request_id,
                command.created_by, command.reason, source, safety, result.review_result_id,
            )
            link = CycleTargetRiskSourceLink(
                self._id_factory(), command.operation_id, result.review_result_id, run_id,
                risk_stage_id, source.decision_result_id, source.intent_id,
                source.decision_run_id, source.source_result_id, source.source_run_id,
                source.source_reversal_result_id, source.source_reversal_run_id,
                source.source_reversal_step_id, source.source_formula_definition_id,
                source.source_configuration_id, created,
            )
            self._store.save_completed(result, operation, link)
            return CycleTargetRiskReviewOutcome(
                operation.attempt_id, operation.operation_id, run_id, result.status,
                f"{source.symbol}: {result.status.value}; requested {source.requested_notional_usd} USD remains unapproved; NO EXECUTION.",
                source.decision_run_id, source.source_run_id, source.source_reversal_run_id,
                result.review_result_id,
            )
        except (ValueError, TypeError) as exc:
            return self._failure(command, run_id, decision_stage_id, source, safety, exc, invalid=True)
        except Exception as exc:
            logger.exception("P33 Risk review failed run_id=%s", run_id)
            return self._failure(command, run_id, decision_stage_id, source, safety, exc, invalid=False)

    def _failure(self, command, run_id, decision_stage_id, source, safety, exc, *, invalid):
        status = CycleTargetRiskStatus.INVALID_INPUT if invalid else CycleTargetRiskStatus.FAILED
        code = ErrorCode.CYCLE_TARGET_RISK.value if invalid else ErrorCode.CYCLE_TARGET_RISK_STORAGE.value
        summary = str(exc) or "P33 cycle-target Risk review failed"
        operation = CycleTargetRiskOperationAttempt(
            self._id_factory(), command.operation_id, run_id, decision_stage_id, None,
            command.command_fingerprint, command.intent_id, command.decision_result_id,
            command.decision_run_id, status, command.requested_at_utc, self._clock(),
            command.session_id, command.request_id, command.created_by, command.reason,
            source, safety, error_code=code, error_summary=summary,
        )
        try:
            self._store.save_operation(operation)
        except Exception:
            logger.exception("Could not persist failed P33 Risk operation")
        return CycleTargetRiskReviewOutcome(
            operation.attempt_id, operation.operation_id, run_id, status, summary,
            source.decision_run_id, source.source_run_id, source.source_reversal_run_id,
            error_code=code,
        )


__all__ = ["CycleTargetRiskService"]
