"""Decision-owned service for durable target-adjustment preview evidence."""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID, uuid4

from quant_trading.error_codes import ErrorCode
from quant_trading.run_history import SoftwareIdentity

from .errors import DecisionContractError
from .target_adjustment_engine import TargetAdjustmentDecisionEngine
from .target_adjustment_interfaces import TargetAdjustmentDecisionStore
from .target_adjustment_models import (
    LinkedTargetDecisionInput,
    TargetAdjustmentDecisionOperationAttempt,
    TargetAdjustmentDecisionPreviewCommand,
    TargetAdjustmentDecisionPreviewResult,
    TargetAdjustmentDecisionSourceLink,
    TargetAdjustmentDecisionStatus,
)


logger = logging.getLogger(__name__)


class TargetAdjustmentDecisionService:
    """Create one typed Decision result without resolving Target Position sources."""

    def __init__(
        self,
        store: TargetAdjustmentDecisionStore,
        software: SoftwareIdentity,
        *,
        engine: TargetAdjustmentDecisionEngine | None = None,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
        id_factory: Callable[[], UUID] = uuid4,
    ) -> None:
        self._store = store
        self._software = software
        self._engine = engine or TargetAdjustmentDecisionEngine()
        self._clock = clock
        self._id_factory = id_factory

    def preview(
        self,
        command: TargetAdjustmentDecisionPreviewCommand,
        source: LinkedTargetDecisionInput,
        *,
        run_id: UUID,
        target_stage_id: UUID,
        decision_stage_id: UUID,
        requested_at_utc: datetime,
    ) -> TargetAdjustmentDecisionPreviewResult:
        if command.operation_id is None:
            raise DecisionContractError("target-adjustment preview requires an operation ID")
        try:
            created = self._clock()
            result = self._engine.evaluate(
                source,
                decision_result_id=self._id_factory(),
                intent_id=self._id_factory(),
                operation_id=command.operation_id,
                run_id=run_id,
                stage_id=decision_stage_id,
                created_at_utc=created,
                created_by=command.created_by,
                reason=command.reason,
                software=self._software,
            )
            operation = TargetAdjustmentDecisionOperationAttempt(
                self._id_factory(),
                command.operation_id,
                run_id,
                target_stage_id,
                decision_stage_id,
                result.status,
                requested_at_utc,
                created,
                command.target_position_link_id,
                command.session_id,
                command.request_id,
                command.created_by,
                command.reason,
                source,
                result.decision_result_id,
            )
            source_link = TargetAdjustmentDecisionSourceLink(
                self._id_factory(),
                command.operation_id,
                result.decision_result_id,
                run_id,
                decision_stage_id,
                source.target_position_link_id,
                source.linked_target_operation_id,
                source.linked_parent_run_id,
                source.target_child_run_id,
                source.standardized_state_run_id,
                source.target_calculation_id,
                source.standardized_state_calculation_id,
                created,
            )
            self._store.save_completed(result, operation, source_link)
            intent_id = result.intents[0].intent_id if result.intents else None
            return TargetAdjustmentDecisionPreviewResult(
                operation.attempt_id,
                operation.operation_id,
                run_id,
                result.status,
                (
                    f"{source.symbol}: action={result.action.value}; "
                    f"current={source.current_position_value_usd} USD; "
                    f"target={source.target_position_value_usd} USD; "
                    f"difference={source.adjustment_value_usd} USD; "
                    f"requested_notional="
                    f"{result.intents[0].requested_notional_usd if result.intents else 'none'}; "
                    "research only, no Risk approval or order."
                ),
                source.linked_parent_run_id,
                source.target_child_run_id,
                source.standardized_state_run_id,
                result.decision_result_id,
                intent_id,
            )
        except (DecisionContractError, ValueError) as exc:
            return self._failure(
                command,
                source,
                run_id,
                target_stage_id,
                decision_stage_id,
                requested_at_utc,
                exc,
                invalid=True,
            )
        except Exception as exc:
            logger.exception("Target-adjustment Decision preview failed run_id=%s", run_id)
            return self._failure(
                command,
                source,
                run_id,
                target_stage_id,
                decision_stage_id,
                requested_at_utc,
                exc,
                invalid=False,
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
    ) -> TargetAdjustmentDecisionPreviewResult:
        status = TargetAdjustmentDecisionStatus.INVALID_INPUT if invalid else TargetAdjustmentDecisionStatus.FAILED
        error_code = (
            ErrorCode.TARGET_ADJUSTMENT_DECISION.value
            if invalid
            else ErrorCode.TARGET_ADJUSTMENT_DECISION_STORAGE.value
        )
        summary = str(exc) or "target-adjustment Decision preview failed"
        operation = TargetAdjustmentDecisionOperationAttempt(
            self._id_factory(),
            command.operation_id,
            run_id,
            target_stage_id,
            decision_stage_id,
            status,
            requested_at_utc,
            self._clock(),
            command.target_position_link_id,
            command.session_id,
            command.request_id,
            command.created_by,
            command.reason,
            source,
            error_code=error_code,
            error_summary=summary,
        )
        try:
            self._store.save_operation(operation)
        except Exception:
            logger.exception("Could not persist failed target-adjustment Decision operation")
        return TargetAdjustmentDecisionPreviewResult(
            operation.attempt_id,
            operation.operation_id,
            run_id,
            status,
            summary,
            source.linked_parent_run_id,
            source.target_child_run_id,
            source.standardized_state_run_id,
            error_code=error_code,
        )


__all__ = ["TargetAdjustmentDecisionService"]
