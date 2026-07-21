"""Application coordination for one persisted standardized state to one target curve."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime
from uuid import UUID, uuid4

from quant_trading.error_codes import ErrorCode
from quant_trading.factors.standardized_state_interfaces import (
    StandardizedPriceStateQueryService,
)
from quant_trading.run_history import (
    AlgorithmRunService,
    AlgorithmRunType,
    RunBindingType,
    RunStageName,
    SoftwareIdentity,
    StartRunRequest,
)
from quant_trading.target_position import (
    DIMENSIONLESS,
    LinkedTargetPositionOperationAttempt,
    LinkedTargetPositionOperationStatus,
    LinkedTargetPositionPreviewCommand,
    LinkedTargetPositionPreviewResult,
    LinkedTargetPositionService,
    StandardizedStateTargetInput,
    TargetPositionStore,
    TargetPositionValidationError,
)


logger = logging.getLogger(__name__)


class StandardizedStateTargetPositionPreviewCoordinator:
    """Resolve one exact source, coordinate a parent Run, and delegate target math."""

    def __init__(
        self,
        source_queries: StandardizedPriceStateQueryService,
        target_store: TargetPositionStore,
        linked_target_service: LinkedTargetPositionService,
        run_service: AlgorithmRunService,
        software: SoftwareIdentity,
        *,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
        id_factory: Callable[[], UUID] = uuid4,
    ) -> None:
        self._source_queries = source_queries
        self._target_store = target_store
        self._linked_target_service = linked_target_service
        self._run_service = run_service
        self._software = software
        self._clock = clock
        self._id_factory = id_factory

    def preview(
        self, command: LinkedTargetPositionPreviewCommand
    ) -> LinkedTargetPositionPreviewResult:
        operation_id = command.operation_id or self._id_factory()
        command = replace(command, operation_id=operation_id)
        existing = self._target_store.get_first_linked_operation(operation_id)
        if existing is not None and existing.matches_command(command):
            return self._existing_result(existing)

        requested_at = self._clock()
        source_result = None
        source_query_error: Exception | None = None
        try:
            source_result = self._source_queries.get_result(
                command.standardized_state_calculation_id
            )
        except Exception as exc:
            source_query_error = exc
        parent_run = self._run_service.start_run(
            StartRunRequest(
                AlgorithmRunType.STANDARDIZED_TARGET_POSITION_PREVIEW,
                command.session_id,
                command.request_id,
                source_result.as_of_utc if source_result is not None else None,
                (source_result.symbol,) if source_result is not None else (),
                "algorithm_control.linked_target_position",
                command.created_by,
                self._software,
                notes=(
                    "Resolve one exact persisted standardized-state result and delegate "
                    "one Target Position child preview; NO EXECUTION"
                ),
            )
        )
        source_stage = self._run_service.start_stage(
            parent_run.run_id, RunStageName.STANDARDIZED_STATE, 1
        )
        try:
            if existing is not None:
                raise TargetPositionValidationError(
                    "operation ID is already recorded with different linked-preview inputs"
                )
            if source_query_error is not None:
                raise RuntimeError(
                    f"could not resolve standardized-state result: {source_query_error}"
                ) from source_query_error
            if source_result is None:
                raise TargetPositionValidationError(
                    "selected standardized-state result does not exist"
                )
            source = StandardizedStateTargetInput(
                source_result.calculation_id,
                source_result.run_id,
                source_result.stage_id,
                source_result.definition_id,
                source_result.definition_version,
                source_result.symbol,
                source_result.as_of_utc,
                source_result.standardized_state,
                source_result.created_at_utc,
                source_result.trace.output_unit,
                schema_version=source_result.schema_version,
            )
            if source.output_unit != DIMENSIONLESS:
                raise TargetPositionValidationError(
                    "selected standardized-state result is not dimensionless"
                )
            self._run_service.bind(
                parent_run.run_id,
                RunBindingType.FACTOR_DEFINITION,
                str(source.source_definition_id),
                str(source.source_definition_version),
                source_reference=str(source.source_calculation_id),
            )
            self._run_service.complete_stage(
                source_stage,
                result_type="standardized_price_state_result",
                result_id=str(source.source_calculation_id),
            )
            target_stage = self._run_service.start_stage(
                parent_run.run_id, RunStageName.TARGET_POSITION, 2
            )
            outcome = self._linked_target_service.preview(
                command,
                source,
                parent_run_id=parent_run.run_id,
                parent_source_stage_id=source_stage.stage_id,
                parent_target_stage_id=target_stage.stage_id,
                requested_at_utc=requested_at,
            )
            if outcome.status is LinkedTargetPositionOperationStatus.COMPLETED:
                self._run_service.complete_stage(
                    target_stage,
                    result_type="target_position_result",
                    result_id=str(outcome.target_calculation_id),
                )
                self._run_service.complete_run(parent_run.run_id)
            else:
                message = outcome.summary or "linked target-position child failed"
                error_code = outcome.error_code or ErrorCode.LINKED_TARGET_POSITION.value
                self._run_service.fail_stage(
                    target_stage,
                    error_code=error_code,
                    error_summary=message,
                )
                self._run_service.fail_run(
                    parent_run.run_id,
                    error_code=error_code,
                    error_summary=message,
                    invalid_input=(
                        outcome.status
                        is LinkedTargetPositionOperationStatus.INVALID_INPUT
                    ),
                )
            return outcome
        except (TargetPositionValidationError, ValueError) as exc:
            return self._source_failure(
                command,
                parent_run.run_id,
                source_stage,
                requested_at,
                exc,
                invalid=True,
            )
        except Exception as exc:
            logger.exception(
                "Linked standardized-state source resolution failed run_id=%s",
                parent_run.run_id,
            )
            return self._source_failure(
                command,
                parent_run.run_id,
                source_stage,
                requested_at,
                exc,
                invalid=False,
            )

    def _existing_result(
        self, operation: LinkedTargetPositionOperationAttempt
    ) -> LinkedTargetPositionPreviewResult:
        link = self._target_store.get_standardized_state_link(operation.operation_id)
        if (
            operation.status is LinkedTargetPositionOperationStatus.COMPLETED
            and link is None
        ):
            raise RuntimeError(
                "completed linked operation is missing its immutable source/result link"
            )
        return LinkedTargetPositionPreviewResult(
            operation.attempt_id,
            operation.operation_id,
            operation.parent_run_id,
            operation.status,
            (
                "Idempotent linked-preview retry returned the original terminal outcome; "
                "no new Run or calculation was created."
            ),
            link.source_run_id if link else operation.resolved_source_run_id,
            link.child_run_id if link else operation.child_run_id,
            link.target_calculation_id if link else operation.target_result_calculation_id,
            operation.error_code,
        )

    def _source_failure(
        self,
        command,
        parent_run_id,
        source_stage,
        requested_at,
        exc,
        *,
        invalid,
    ) -> LinkedTargetPositionPreviewResult:
        status = (
            LinkedTargetPositionOperationStatus.INVALID_INPUT
            if invalid
            else LinkedTargetPositionOperationStatus.FAILED
        )
        error_code = (
            ErrorCode.LINKED_TARGET_POSITION.value
            if invalid
            else ErrorCode.LINKED_TARGET_POSITION_STORAGE.value
        )
        summary = str(exc) or "linked standardized-state source resolution failed"
        attempt = LinkedTargetPositionOperationAttempt(
            self._id_factory(),
            command.operation_id,
            parent_run_id,
            source_stage.stage_id,
            None,
            None,
            None,
            status,
            requested_at,
            self._clock(),
            command.standardized_state_calculation_id,
            command.target_position_definition_id,
            command.research_capital_basis_usd,
            command.current_position_value_usd,
            command.session_id,
            command.request_id,
            command.created_by,
            command.reason,
            error_code=error_code,
            error_summary=summary,
        )
        try:
            self._target_store.save_linked_operation(attempt)
        except Exception:
            logger.exception(
                "Could not persist failed linked source attempt run_id=%s",
                parent_run_id,
            )
        self._run_service.fail_stage(
            source_stage, error_code=error_code, error_summary=summary
        )
        self._run_service.fail_run(
            parent_run_id,
            error_code=error_code,
            error_summary=summary,
            invalid_input=invalid,
        )
        return LinkedTargetPositionPreviewResult(
            attempt.attempt_id,
            command.operation_id,
            parent_run_id,
            status,
            summary,
            error_code=error_code,
        )


__all__ = ["StandardizedStateTargetPositionPreviewCoordinator"]
