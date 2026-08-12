"""Resolve one exact P29 result/Run and coordinate a P23-4A Decision preview."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from uuid import UUID, uuid4

from quant_trading.decision import (
    CycleTargetAdjustmentDecisionQueryService,
    CycleTargetAdjustmentDecisionService,
    CycleTargetAdjustmentDecisionStore,
    CycleTargetAdjustmentOperationAttempt,
    CycleTargetAdjustmentOperationStatus,
    CycleTargetAdjustmentPreviewCommand,
    CycleTargetAdjustmentPreviewOutcome,
    CycleTargetDecisionInput,
)
from quant_trading.decision.errors import DecisionContractError
from quant_trading.error_codes import ErrorCode
from quant_trading.run_history import (
    AlgorithmRunService,
    AlgorithmRunType,
    RunBindingType,
    RunStageName,
    SoftwareIdentity,
    StartRunRequest,
)
from quant_trading.target_position import CycleTargetPositionQueryService


logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class CycleTargetAdjustmentDecisionPreflight:
    """Read-only proof that one explicit P29 Result/Run is admissible to P31."""

    command_fingerprint: str
    source: CycleTargetDecisionInput
    summary: str


class CycleTargetAdjustmentDecisionPreviewCoordinator:
    """Resolve exact public P29 evidence; never calculate a target or Decision action."""

    def __init__(
        self,
        cycle_target_queries: CycleTargetPositionQueryService,
        decision_store: CycleTargetAdjustmentDecisionStore,
        decision_queries: CycleTargetAdjustmentDecisionQueryService,
        decision_service: CycleTargetAdjustmentDecisionService,
        run_service: AlgorithmRunService,
        software: SoftwareIdentity,
        *,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
        id_factory: Callable[[], UUID] = uuid4,
    ) -> None:
        self._cycle_targets = cycle_target_queries
        self._decision_store = decision_store
        self._decision_queries = decision_queries
        self._decision_service = decision_service
        self._runs = run_service
        self._software = software
        self._clock = clock
        self._id_factory = id_factory

    def preflight(
        self, command: CycleTargetAdjustmentPreviewCommand
    ) -> CycleTargetAdjustmentDecisionPreflight:
        """Resolve and validate one exact source without creating a Run or result."""

        result = self._cycle_targets.get_result(command.source_result_id)
        if result is None:
            raise DecisionContractError("selected accepted P29 Result does not exist")
        source = self._resolve_input(command, result)
        return CycleTargetAdjustmentDecisionPreflight(
            command.command_fingerprint,
            source,
            (
                f"Validated exact P29 Result {source.source_result_id} / Run "
                f"{source.source_run_id}; target {source.target_position_value_usd} USD, "
                f"current {source.current_position_value_usd} USD, signed difference "
                f"{source.adjustment_value_usd} USD. No Run or P31 result was written."
            ),
        )

    def preview(
        self, command: CycleTargetAdjustmentPreviewCommand
    ) -> CycleTargetAdjustmentPreviewOutcome:
        operation_id = command.operation_id or self._id_factory()
        command = replace(command, operation_id=operation_id)
        existing = self._decision_store.get_first_operation(operation_id)
        if existing is not None and existing.matches_command(command):
            return self._existing_outcome(existing)

        requested_at = self._clock()
        source_result = None
        source_error: Exception | None = None
        try:
            source_result = self._cycle_targets.get_result(command.source_result_id)
        except Exception as exc:
            source_error = exc
        valid_parent = (
            source_result.run_id
            if source_result is not None and source_result.run_id == command.source_run_id
            else None
        )
        run = self._runs.start_run(StartRunRequest(
            AlgorithmRunType.CYCLE_TARGET_DECISION_PREVIEW,
            command.session_id,
            command.request_id,
            source_result.source.available_at_utc if source_result is not None else None,
            (source_result.source.symbol,) if source_result is not None else (),
            "algorithm_control.cycle_target_adjustment_decision",
            command.created_by,
            self._software,
            parent_run_id=valid_parent,
            notes=(
                "Resolve one explicit accepted P29 target and apply the shared exact "
                "Decision difference mapping; NO EXECUTION, no Risk review"
            ),
        ))
        target_stage = self._runs.start_stage(run.run_id, RunStageName.TARGET_POSITION, 1)
        try:
            if existing is not None:
                raise DecisionContractError(
                    "operation ID is already recorded with different P31 inputs"
                )
            if source_error is not None:
                raise RuntimeError(f"could not resolve exact P29 result: {source_error}") from source_error
            if source_result is None:
                raise DecisionContractError("selected accepted P29 Result does not exist")
            source = self._resolve_input(command, source_result)
            self._bind_sources(run.run_id, source)
            self._runs.complete_stage(
                target_stage,
                result_type="cycle_target_position_result",
                result_id=str(source.source_result_id),
            )
            decision_stage = self._runs.start_stage(run.run_id, RunStageName.DECISION, 2)
            outcome = self._decision_service.preview(
                command,
                source,
                run_id=run.run_id,
                target_stage_id=target_stage.stage_id,
                decision_stage_id=decision_stage.stage_id,
                requested_at_utc=requested_at,
            )
            if outcome.operation_status is CycleTargetAdjustmentOperationStatus.COMPLETED:
                self._runs.complete_stage(
                    decision_stage,
                    result_type="cycle_target_adjustment_decision_result",
                    result_id=str(outcome.decision_result_id),
                )
                self._runs.complete_run(run.run_id)
            else:
                error_code = outcome.error_code or ErrorCode.CYCLE_TARGET_ADJUSTMENT_DECISION.value
                self._runs.fail_stage(
                    decision_stage, error_code=error_code, error_summary=outcome.summary
                )
                self._runs.fail_run(
                    run.run_id,
                    error_code=error_code,
                    error_summary=outcome.summary,
                    invalid_input=(
                        outcome.operation_status
                        is CycleTargetAdjustmentOperationStatus.INVALID_INPUT
                    ),
                )
            return outcome
        except (DecisionContractError, ValueError, KeyError) as exc:
            return self._source_failure(
                command, run.run_id, target_stage, requested_at, exc, invalid=True
            )
        except Exception as exc:
            logger.exception("P31 source resolution failed run_id=%s", run.run_id)
            return self._source_failure(
                command, run.run_id, target_stage, requested_at, exc, invalid=False
            )

    def _resolve_input(self, command, result) -> CycleTargetDecisionInput:
        if result.result_id != command.source_result_id or result.run_id != command.source_run_id:
            raise DecisionContractError("P29 Result/Run identity is inconsistent")
        if result.execution_allowed or result.live_allowed or result.schema_version != 1:
            raise DecisionContractError("P29 result safety/schema metadata is incompatible")
        formula = self._cycle_targets.get_formula_definition(result.formula_definition_id)
        configuration = self._cycle_targets.get_configuration(result.configuration_id)
        if formula is None or configuration is None:
            raise DecisionContractError("P29 result is missing formula/configuration versions")
        if (
            formula.formula_definition_id != result.formula_definition_id
            or formula.definition_version != result.formula_definition_version
            or formula.execution_allowed or formula.live_allowed or formula.schema_version != 1
        ):
            raise DecisionContractError("P29 formula identity or safety metadata is inconsistent")
        if (
            configuration.configuration_id != result.configuration_id
            or configuration.configuration_version != result.configuration_version
            or configuration.formula_definition_id != result.formula_definition_id
            or configuration.formula_definition_version != result.formula_definition_version
            or configuration.symbol != result.source.symbol
            or configuration.execution_allowed or configuration.live_allowed
            or configuration.schema_version != 1
        ):
            raise DecisionContractError("P29 configuration identity or safety metadata is inconsistent")
        return CycleTargetDecisionInput(
            source_result_id=result.result_id,
            source_operation_id=result.operation_id,
            source_run_id=result.run_id,
            source_state_stage_id=result.state_stage_id,
            source_target_stage_id=result.target_stage_id,
            source_formula_definition_id=result.formula_definition_id,
            source_formula_definition_version=result.formula_definition_version,
            source_configuration_id=result.configuration_id,
            source_configuration_version=result.configuration_version,
            source_configuration_fingerprint=configuration.constraint_fingerprint,
            source_reversal_result_id=result.source.source_result_id,
            source_reversal_run_id=result.source.source_run_id,
            source_reversal_step_id=result.source.source_step_id,
            source_calculation_fingerprint=result.calculation_fingerprint,
            symbol=result.source.symbol,
            source_session=result.source.session,
            source_available_at_utc=result.source.available_at_utc,
            source_region=result.region.value,
            source_status=result.status.value,
            target_fraction=result.target_fraction,
            research_capital_basis_usd=result.research_capital_basis_usd,
            current_position_value_usd=result.current_position_value_usd,
            target_position_value_usd=result.target_position_value_usd,
            adjustment_value_usd=result.adjustment_value_usd,
            source_direction=result.adjustment_direction.value,
            source_created_at_utc=result.created_at_utc,
            source_execution_allowed=result.execution_allowed,
            source_live_allowed=result.live_allowed,
            source_schema_version=result.schema_version,
        )

    def _bind_sources(self, run_id, source: CycleTargetDecisionInput) -> None:
        self._runs.bind(
            run_id, RunBindingType.STRATEGY_VERSION,
            str(source.source_formula_definition_id),
            str(source.source_formula_definition_version),
            source_reference=str(source.source_result_id),
        )
        self._runs.bind(
            run_id, RunBindingType.CONFIGURATION,
            str(source.source_configuration_id),
            str(source.source_configuration_version),
            source_reference=source.source_configuration_fingerprint,
        )
        self._runs.bind(
            run_id, RunBindingType.DECISION_DEFINITION,
            "decision.cycle_target_adjustment.p23_4a.v1",
            "1.0.0",
            source_reference=str(source.source_result_id),
        )

    def _existing_outcome(self, operation) -> CycleTargetAdjustmentPreviewOutcome:
        result = (
            self._decision_queries.get_cycle_target_adjustment_result(
                operation.decision_result_id
            )
            if operation.decision_result_id is not None else None
        )
        if operation.status is CycleTargetAdjustmentOperationStatus.COMPLETED and result is None:
            raise RuntimeError("completed P31 operation is missing its immutable result")
        source = operation.resolved_source
        return CycleTargetAdjustmentPreviewOutcome(
            operation.attempt_id,
            operation.operation_id,
            operation.run_id,
            operation.status,
            "Idempotent P31 retry returned the original terminal outcome; no new Run, result or intent was created.",
            source.source_run_id if source else None,
            source.source_reversal_run_id if source else None,
            operation.decision_result_id,
            operation.intent_id,
            result.status if result else None,
            result.action if result else None,
            operation.error_code,
        )

    def _source_failure(self, command, run_id, target_stage, requested_at, exc, *, invalid):
        status = (
            CycleTargetAdjustmentOperationStatus.INVALID_INPUT
            if invalid else CycleTargetAdjustmentOperationStatus.FAILED
        )
        error_code = (
            ErrorCode.CYCLE_TARGET_ADJUSTMENT_DECISION.value
            if invalid else ErrorCode.CYCLE_TARGET_ADJUSTMENT_DECISION_STORAGE.value
        )
        summary = str(exc) or "P31 source resolution failed"
        operation = CycleTargetAdjustmentOperationAttempt(
            attempt_id=self._id_factory(), operation_id=command.operation_id,
            run_id=run_id, target_stage_id=target_stage.stage_id, decision_stage_id=None,
            command_fingerprint=command.command_fingerprint, status=status,
            requested_at_utc=requested_at, completed_at_utc=self._clock(),
            requested_source_result_id=command.source_result_id,
            requested_source_run_id=command.source_run_id,
            session_id=command.session_id, request_id=command.request_id,
            created_by=command.created_by, reason=command.reason,
            error_code=error_code, error_summary=summary,
            software_version=self._software.package_version,
            source_revision=self._software.source_revision,
            worktree_state=self._software.worktree_state.value,
        )
        try:
            self._decision_store.save_operation(operation)
        except Exception:
            logger.exception("Could not persist failed P31 source attempt")
        self._runs.fail_stage(target_stage, error_code=error_code, error_summary=summary)
        self._runs.fail_run(
            run_id, error_code=error_code, error_summary=summary, invalid_input=invalid
        )
        return CycleTargetAdjustmentPreviewOutcome(
            operation.attempt_id, operation.operation_id, run_id, operation.status,
            summary, error_code=error_code,
        )


__all__ = [
    "CycleTargetAdjustmentDecisionPreflight",
    "CycleTargetAdjustmentDecisionPreviewCoordinator",
]
