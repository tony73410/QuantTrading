"""Decision-owned service for durable P23-4A cycle-target previews."""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID, uuid4

from quant_trading.error_codes import ErrorCode
from quant_trading.run_history import SoftwareIdentity

from .cycle_target_adjustment_engine import CycleTargetAdjustmentDecisionEngine
from .cycle_target_adjustment_interfaces import CycleTargetAdjustmentDecisionStore
from .cycle_target_adjustment_models import (
    CycleTargetAdjustmentOperationAttempt,
    CycleTargetAdjustmentOperationStatus,
    CycleTargetAdjustmentPreviewCommand,
    CycleTargetAdjustmentPreviewOutcome,
    CycleTargetAdjustmentSourceLink,
    CycleTargetDecisionInput,
)
from .errors import DecisionContractError


logger = logging.getLogger(__name__)


class CycleTargetAdjustmentDecisionService:
    """Create one typed P31 result without resolving the P29 source."""

    def __init__(
        self,
        store: CycleTargetAdjustmentDecisionStore,
        software: SoftwareIdentity,
        *,
        engine: CycleTargetAdjustmentDecisionEngine | None = None,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
        id_factory: Callable[[], UUID] = uuid4,
    ) -> None:
        self._store = store
        self._software = software
        self._engine = engine or CycleTargetAdjustmentDecisionEngine()
        self._clock = clock
        self._id_factory = id_factory

    def preview(
        self,
        command: CycleTargetAdjustmentPreviewCommand,
        source: CycleTargetDecisionInput,
        *,
        run_id: UUID,
        target_stage_id: UUID,
        decision_stage_id: UUID,
        requested_at_utc: datetime,
    ) -> CycleTargetAdjustmentPreviewOutcome:
        if command.operation_id is None:
            raise DecisionContractError("P31 preview requires an operation ID")
        try:
            created = self._clock()
            result = self._engine.evaluate(
                source,
                decision_result_id=self._id_factory(),
                intent_id=self._id_factory(),
                operation_id=command.operation_id,
                run_id=run_id,
                target_stage_id=target_stage_id,
                decision_stage_id=decision_stage_id,
                created_at_utc=created,
                created_by=command.created_by,
                reason=command.reason,
                software=self._software,
            )
            intent_id = result.intents[0].intent_id if result.intents else None
            operation = CycleTargetAdjustmentOperationAttempt(
                attempt_id=self._id_factory(),
                operation_id=command.operation_id,
                run_id=run_id,
                target_stage_id=target_stage_id,
                decision_stage_id=decision_stage_id,
                command_fingerprint=command.command_fingerprint,
                status=CycleTargetAdjustmentOperationStatus.COMPLETED,
                requested_at_utc=requested_at_utc,
                completed_at_utc=created,
                requested_source_result_id=command.source_result_id,
                requested_source_run_id=command.source_run_id,
                session_id=command.session_id,
                request_id=command.request_id,
                created_by=command.created_by,
                reason=command.reason,
                resolved_source=source,
                decision_result_id=result.decision_result_id,
                intent_id=intent_id,
                software_version=self._software.package_version,
                source_revision=self._software.source_revision,
                worktree_state=self._software.worktree_state.value,
            )
            source_link = CycleTargetAdjustmentSourceLink(
                source_link_id=self._id_factory(),
                operation_id=command.operation_id,
                decision_result_id=result.decision_result_id,
                intent_id=intent_id,
                decision_run_id=run_id,
                decision_stage_id=decision_stage_id,
                source_result_id=source.source_result_id,
                source_operation_id=source.source_operation_id,
                source_run_id=source.source_run_id,
                source_state_stage_id=source.source_state_stage_id,
                source_target_stage_id=source.source_target_stage_id,
                source_formula_definition_id=source.source_formula_definition_id,
                source_configuration_id=source.source_configuration_id,
                source_reversal_result_id=source.source_reversal_result_id,
                source_reversal_run_id=source.source_reversal_run_id,
                source_reversal_step_id=source.source_reversal_step_id,
                created_at_utc=created,
            )
            self._store.save_completed(result, operation, source_link)
            return CycleTargetAdjustmentPreviewOutcome(
                attempt_id=operation.attempt_id,
                operation_id=operation.operation_id,
                run_id=run_id,
                operation_status=operation.status,
                summary=result.explanation,
                source_run_id=source.source_run_id,
                source_reversal_run_id=source.source_reversal_run_id,
                decision_result_id=result.decision_result_id,
                intent_id=intent_id,
                result_status=result.status,
                action=result.action,
            )
        except (DecisionContractError, ValueError) as exc:
            return self._failure(
                command, source, run_id, target_stage_id, decision_stage_id,
                requested_at_utc, exc, invalid=True,
            )
        except Exception as exc:
            logger.exception("P31 cycle-target Decision preview failed run_id=%s", run_id)
            return self._failure(
                command, source, run_id, target_stage_id, decision_stage_id,
                requested_at_utc, exc, invalid=False,
            )

    def _failure(
        self,
        command,
        source,
        run_id,
        target_stage_id,
        decision_stage_id,
        requested_at_utc,
        exc,
        *,
        invalid,
    ) -> CycleTargetAdjustmentPreviewOutcome:
        status = (
            CycleTargetAdjustmentOperationStatus.INVALID_INPUT
            if invalid else CycleTargetAdjustmentOperationStatus.FAILED
        )
        error_code = (
            ErrorCode.CYCLE_TARGET_ADJUSTMENT_DECISION.value
            if invalid else ErrorCode.CYCLE_TARGET_ADJUSTMENT_DECISION_STORAGE.value
        )
        summary = str(exc) or "P31 cycle-target Decision preview failed"
        operation = CycleTargetAdjustmentOperationAttempt(
            attempt_id=self._id_factory(),
            operation_id=command.operation_id,
            run_id=run_id,
            target_stage_id=target_stage_id,
            decision_stage_id=decision_stage_id,
            command_fingerprint=command.command_fingerprint,
            status=status,
            requested_at_utc=requested_at_utc,
            completed_at_utc=self._clock(),
            requested_source_result_id=command.source_result_id,
            requested_source_run_id=command.source_run_id,
            session_id=command.session_id,
            request_id=command.request_id,
            created_by=command.created_by,
            reason=command.reason,
            resolved_source=source,
            error_code=error_code,
            error_summary=summary,
            software_version=self._software.package_version,
            source_revision=self._software.source_revision,
            worktree_state=self._software.worktree_state.value,
        )
        try:
            self._store.save_operation(operation)
        except Exception:
            logger.exception("Could not persist failed P31 Decision operation")
        return CycleTargetAdjustmentPreviewOutcome(
            operation.attempt_id,
            operation.operation_id,
            run_id,
            operation.status,
            summary,
            source.source_run_id,
            source.source_reversal_run_id,
            error_code=error_code,
        )


__all__ = ["CycleTargetAdjustmentDecisionService"]
