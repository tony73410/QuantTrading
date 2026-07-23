"""Resolve one exact Phase 5C link and coordinate a Decision-only preview."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime
from uuid import UUID, uuid4

from quant_trading.decision import (
    LinkedTargetDecisionInput,
    TargetAdjustmentDecisionOperationAttempt,
    TargetAdjustmentDecisionPreviewCommand,
    TargetAdjustmentDecisionPreviewResult,
    TargetAdjustmentDecisionQueryService,
    TargetAdjustmentDecisionService,
    TargetAdjustmentDecisionStatus,
    TargetAdjustmentDecisionStore,
)
from quant_trading.decision.errors import DecisionContractError
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
from quant_trading.target_position import TargetPositionQueryService


logger = logging.getLogger(__name__)


class TargetAdjustmentDecisionPreviewCoordinator:
    """Own source resolution and Run order, never target or Decision mathematics."""

    def __init__(
        self,
        standardized_state_queries: StandardizedPriceStateQueryService,
        target_position_queries: TargetPositionQueryService,
        decision_store: TargetAdjustmentDecisionStore,
        decision_queries: TargetAdjustmentDecisionQueryService,
        decision_service: TargetAdjustmentDecisionService,
        run_service: AlgorithmRunService,
        software: SoftwareIdentity,
        *,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
        id_factory: Callable[[], UUID] = uuid4,
    ) -> None:
        self._standardized_state_queries = standardized_state_queries
        self._target_position_queries = target_position_queries
        self._decision_store = decision_store
        self._decision_queries = decision_queries
        self._decision_service = decision_service
        self._run_service = run_service
        self._software = software
        self._clock = clock
        self._id_factory = id_factory

    def preview(
        self, command: TargetAdjustmentDecisionPreviewCommand
    ) -> TargetAdjustmentDecisionPreviewResult:
        operation_id = command.operation_id or self._id_factory()
        command = replace(command, operation_id=operation_id)
        existing = self._decision_store.get_first_operation(operation_id)
        if existing is not None and existing.matches_command(command):
            return self._existing_result(existing)

        requested_at = self._clock()
        source_link = None
        source_query_error: Exception | None = None
        try:
            source_link = self._target_position_queries.get_standardized_state_link_by_id(
                command.target_position_link_id
            )
        except Exception as exc:
            source_query_error = exc
        run = self._run_service.start_run(
            StartRunRequest(
                AlgorithmRunType.TARGET_ADJUSTMENT_DECISION_PREVIEW,
                command.session_id,
                command.request_id,
                source_link.source_as_of_utc if source_link is not None else None,
                (source_link.symbol,) if source_link is not None else (),
                "algorithm_control.target_adjustment_decision",
                command.created_by,
                self._software,
                parent_run_id=(source_link.parent_run_id if source_link is not None else None),
                notes=(
                    "Resolve one exact completed Phase 5C linked target and map its "
                    "difference in Decision; NO EXECUTION"
                ),
            )
        )
        target_stage = self._run_service.start_stage(
            run.run_id, RunStageName.TARGET_POSITION, 1
        )
        try:
            if existing is not None:
                raise DecisionContractError(
                    "operation ID is already recorded with different target-adjustment inputs"
                )
            if source_query_error is not None:
                raise RuntimeError(
                    f"could not resolve target-position link: {source_query_error}"
                ) from source_query_error
            if source_link is None:
                raise DecisionContractError(
                    "selected completed Phase 5C target-position link does not exist"
                )
            target = self._target_position_queries.get_result(
                source_link.target_calculation_id
            )
            source = self._standardized_state_queries.get_result(
                source_link.source_calculation_id
            )
            if target is None or source is None:
                raise DecisionContractError(
                    "selected Phase 5C link is missing its persisted source or target result"
                )
            resolved = self._resolve_input(source_link, source, target)
            self._bind_sources(run.run_id, resolved)
            self._run_service.complete_stage(
                target_stage,
                result_type="target_position_result",
                result_id=str(resolved.target_calculation_id),
            )
            decision_stage = self._run_service.start_stage(
                run.run_id, RunStageName.DECISION, 2
            )
            outcome = self._decision_service.preview(
                command,
                resolved,
                run_id=run.run_id,
                target_stage_id=target_stage.stage_id,
                decision_stage_id=decision_stage.stage_id,
                requested_at_utc=requested_at,
            )
            if outcome.status in {
                TargetAdjustmentDecisionStatus.INTENT_CREATED,
                TargetAdjustmentDecisionStatus.HOLD,
            }:
                self._run_service.complete_stage(
                    decision_stage,
                    result_type="target_adjustment_decision_result",
                    result_id=str(outcome.decision_result_id),
                )
                self._run_service.complete_run(run.run_id)
            else:
                error_code = outcome.error_code or ErrorCode.TARGET_ADJUSTMENT_DECISION.value
                self._run_service.fail_stage(
                    decision_stage,
                    error_code=error_code,
                    error_summary=outcome.summary,
                )
                self._run_service.fail_run(
                    run.run_id,
                    error_code=error_code,
                    error_summary=outcome.summary,
                    invalid_input=(
                        outcome.status is TargetAdjustmentDecisionStatus.INVALID_INPUT
                    ),
                )
            return outcome
        except (DecisionContractError, ValueError) as exc:
            return self._source_failure(
                command,
                run.run_id,
                target_stage.stage_id,
                target_stage,
                requested_at,
                exc,
                invalid=True,
            )
        except Exception as exc:
            logger.exception(
                "Target-adjustment source resolution failed run_id=%s", run.run_id
            )
            return self._source_failure(
                command,
                run.run_id,
                target_stage.stage_id,
                target_stage,
                requested_at,
                exc,
                invalid=False,
            )

    @staticmethod
    def _resolve_input(link, source, target) -> LinkedTargetDecisionInput:
        if (
            target.operation_id != link.operation_id
            or target.run_id != link.child_run_id
            or target.stage_id != link.child_stage_id
            or target.definition_id != link.target_definition_id
            or target.definition_version != link.target_definition_version
            or target.calculation_id != link.target_calculation_id
            or target.as_of_utc != link.source_as_of_utc
        ):
            raise DecisionContractError("Phase 5C target result identity is inconsistent")
        if (
            source.calculation_id != link.source_calculation_id
            or source.run_id != link.source_run_id
            or source.stage_id != link.source_result_stage_id
            or source.definition_id != link.source_definition_id
            or source.definition_version != link.source_definition_version
            or source.symbol != link.symbol
            or source.as_of_utc != link.source_as_of_utc
            or source.standardized_state != link.standardized_state
        ):
            raise DecisionContractError("Phase 5C standardized-state identity is inconsistent")
        return LinkedTargetDecisionInput(
            link.link_id,
            link.operation_id,
            link.parent_run_id,
            link.source_stage_id,
            link.target_stage_id,
            link.child_run_id,
            link.child_stage_id,
            source.calculation_id,
            source.run_id,
            source.stage_id,
            source.definition_id,
            source.definition_version,
            source.created_at_utc,
            target.calculation_id,
            target.definition_id,
            target.definition_version,
            target.created_at_utc,
            link.symbol,
            link.source_as_of_utc,
            link.standardized_state,
            target.research_capital_basis_usd,
            target.current_position_value_usd,
            target.target_fraction,
            target.target_position_value_usd,
            target.adjustment_value_usd,
            target.adjustment_direction.value,
            link.created_at_utc,
            source.schema_version,
            target.schema_version,
            link.schema_version,
            state_unit=source.trace.output_unit,
        )

    def _bind_sources(self, run_id, source: LinkedTargetDecisionInput) -> None:
        self._run_service.bind(
            run_id,
            RunBindingType.FACTOR_DEFINITION,
            str(source.standardized_state_definition_id),
            str(source.standardized_state_definition_version),
            source_reference=str(source.standardized_state_calculation_id),
        )
        self._run_service.bind(
            run_id,
            RunBindingType.CONFIGURATION,
            str(source.target_definition_id),
            str(source.target_definition_version),
            source_reference=str(source.target_calculation_id),
        )
        self._run_service.bind(
            run_id,
            RunBindingType.DECISION_DEFINITION,
            "decision.target_adjustment_preview",
            "1.0.0",
            source_reference=str(source.target_position_link_id),
        )

    def _existing_result(
        self, operation: TargetAdjustmentDecisionOperationAttempt
    ) -> TargetAdjustmentDecisionPreviewResult:
        result = (
            self._decision_queries.get_target_adjustment_result(
                operation.decision_result_id
            )
            if operation.decision_result_id is not None
            else None
        )
        if operation.status in {
            TargetAdjustmentDecisionStatus.INTENT_CREATED,
            TargetAdjustmentDecisionStatus.HOLD,
        } and result is None:
            raise RuntimeError(
                "completed target-adjustment operation is missing its immutable result"
            )
        source = operation.resolved_source
        return TargetAdjustmentDecisionPreviewResult(
            operation.attempt_id,
            operation.operation_id,
            operation.run_id,
            operation.status,
            "Idempotent target-adjustment retry returned the original terminal outcome; no new Run or result was created.",
            source.linked_parent_run_id if source else None,
            source.target_child_run_id if source else None,
            source.standardized_state_run_id if source else None,
            operation.decision_result_id,
            result.intents[0].intent_id if result and result.intents else None,
            operation.error_code,
        )

    def _source_failure(
        self,
        command,
        run_id,
        target_stage_id,
        target_stage,
        requested_at,
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
        summary = str(exc) or "target-adjustment source resolution failed"
        attempt = TargetAdjustmentDecisionOperationAttempt(
            self._id_factory(),
            command.operation_id,
            run_id,
            target_stage_id,
            None,
            status,
            requested_at,
            self._clock(),
            command.target_position_link_id,
            command.session_id,
            command.request_id,
            command.created_by,
            command.reason,
            error_code=error_code,
            error_summary=summary,
        )
        try:
            self._decision_store.save_operation(attempt)
        except Exception:
            logger.exception("Could not persist failed target-adjustment source attempt")
        self._run_service.fail_stage(
            target_stage, error_code=error_code, error_summary=summary
        )
        self._run_service.fail_run(
            run_id,
            error_code=error_code,
            error_summary=summary,
            invalid_input=invalid,
        )
        return TargetAdjustmentDecisionPreviewResult(
            attempt.attempt_id,
            attempt.operation_id,
            run_id,
            status,
            summary,
            error_code=error_code,
        )


__all__ = ["TargetAdjustmentDecisionPreviewCoordinator"]
