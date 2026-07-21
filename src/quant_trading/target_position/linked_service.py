"""Target-owned child preview service for an exact standardized-state input."""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID, uuid4

from quant_trading.error_codes import ErrorCode
from quant_trading.run_history import (
    AlgorithmRunService,
    AlgorithmRunType,
    RunBindingType,
    RunStageName,
    SoftwareIdentity,
    StartRunRequest,
)

from .engine import TargetPositionEngine
from .errors import TargetPositionValidationError
from .interfaces import TargetPositionStore
from .linked_models import (
    LinkedTargetPositionOperationAttempt,
    LinkedTargetPositionOperationStatus,
    LinkedTargetPositionPreviewCommand,
    LinkedTargetPositionPreviewResult,
    StandardizedStateTargetInput,
    StandardizedStateTargetPositionLink,
)
from .models import (
    TargetPositionDefinitionStatus,
    TargetPositionEvidenceBinding,
    TargetPositionEvidenceKind,
    TargetPositionOperationAttempt,
    TargetPositionOperationStatus,
    TargetPositionOperationType,
    decimal_text,
    required_text,
)


logger = logging.getLogger(__name__)


class LinkedTargetPositionService:
    """Calculate one child Target Position preview without changing its engine."""

    def __init__(
        self,
        store: TargetPositionStore,
        run_service: AlgorithmRunService,
        software: SoftwareIdentity,
        *,
        engine: TargetPositionEngine | None = None,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
        id_factory: Callable[[], UUID] = uuid4,
    ) -> None:
        self._store = store
        self._run_service = run_service
        self._software = software
        self._engine = engine or TargetPositionEngine()
        self._clock = clock
        self._id_factory = id_factory

    def preview(
        self,
        command: LinkedTargetPositionPreviewCommand,
        source: StandardizedStateTargetInput,
        *,
        parent_run_id: UUID,
        parent_source_stage_id: UUID,
        parent_target_stage_id: UUID,
        requested_at_utc: datetime,
    ) -> LinkedTargetPositionPreviewResult:
        if command.operation_id is None:
            raise TargetPositionValidationError(
                "linked preview requires a coordinator-assigned operation ID"
            )
        operation_id = command.operation_id
        child_run = self._run_service.start_run(
            StartRunRequest(
                AlgorithmRunType.TARGET_POSITION_PREVIEW,
                command.session_id,
                command.request_id,
                source.as_of_utc,
                (source.symbol,),
                "linked_standardized_state_target_position",
                command.created_by,
                self._software,
                parent_run_id=parent_run_id,
                notes="Calculate Target Position from one exact persisted standardized-state result",
            )
        )
        child_stage = self._run_service.start_stage(
            child_run.run_id, RunStageName.TARGET_POSITION, 1
        )
        evidence = (
            TargetPositionEvidenceBinding(
                TargetPositionEvidenceKind.FACTOR_CALCULATION,
                str(source.source_calculation_id),
                source.source_component,
                str(source.source_definition_version),
            ),
        )
        definition = None
        try:
            if self._store.get_first_operation(operation_id) is not None:
                raise TargetPositionValidationError(
                    "operation ID is already recorded by Target Position"
                )
            definition = self._store.get_definition(
                command.target_position_definition_id
            )
            if definition is None:
                raise TargetPositionValidationError(
                    "target-position definition does not exist"
                )
            if definition.status is not TargetPositionDefinitionStatus.AVAILABLE:
                raise TargetPositionValidationError(
                    "archived definition cannot be previewed"
                )
            capital_basis = decimal_text(
                command.research_capital_basis_usd,
                "research_capital_basis_usd",
            )
            current_position = decimal_text(
                command.current_position_value_usd,
                "current_position_value_usd",
            )
            if capital_basis < 0 or current_position < 0:
                raise TargetPositionValidationError(
                    "capital basis and current position must be non-negative"
                )
            reason = required_text(command.reason, "linked preview reason")
            calculation_id = self._id_factory()
            completed_at = self._clock()
            result = self._engine.calculate(
                definition,
                calculation_id=calculation_id,
                operation_id=operation_id,
                run_id=child_run.run_id,
                stage_id=child_stage.stage_id,
                as_of_utc=source.as_of_utc,
                research_state_value=source.standardized_state,
                research_capital_basis_usd=capital_basis,
                current_position_value_usd=current_position,
                evidence_bindings=evidence,
                created_at_utc=completed_at,
                created_by=command.created_by,
                reason=reason,
            )
            target_attempt = self._target_attempt(
                command,
                source,
                child_run.run_id,
                child_stage.stage_id,
                requested_at_utc,
                TargetPositionOperationStatus.COMPLETED,
                resolved_definition_id=definition.definition_id,
                result_calculation_id=calculation_id,
                evidence=evidence,
            )
            linked_attempt = self._linked_attempt(
                command,
                source,
                parent_run_id,
                parent_source_stage_id,
                parent_target_stage_id,
                child_run.run_id,
                child_stage.stage_id,
                requested_at_utc,
                LinkedTargetPositionOperationStatus.COMPLETED,
                resolved_target_definition_id=definition.definition_id,
                resolved_target_definition_version=definition.definition_version,
                target_result_calculation_id=calculation_id,
            )
            link = StandardizedStateTargetPositionLink(
                self._id_factory(),
                operation_id,
                parent_run_id,
                parent_source_stage_id,
                parent_target_stage_id,
                child_run.run_id,
                child_stage.stage_id,
                source.source_calculation_id,
                source.source_run_id,
                source.source_stage_id,
                source.source_definition_id,
                source.source_definition_version,
                source.symbol,
                source.as_of_utc,
                source.standardized_state,
                calculation_id,
                definition.definition_id,
                definition.definition_version,
                completed_at,
                command.created_by,
                reason,
            )
            self._bind_definitions(parent_run_id, child_run.run_id, definition, source)
            self._store.save_linked_preview(
                result, target_attempt, linked_attempt, link
            )
            self._run_service.complete_stage(
                child_stage,
                result_type="target_position_result",
                result_id=str(calculation_id),
            )
            self._run_service.complete_run(child_run.run_id)
            return LinkedTargetPositionPreviewResult(
                linked_attempt.attempt_id,
                operation_id,
                parent_run_id,
                LinkedTargetPositionOperationStatus.COMPLETED,
                (
                    f"Linked preview for {source.symbol}: state={source.standardized_state}; "
                    f"target={result.target_position_value_usd} USD; "
                    f"current={result.current_position_value_usd} USD; "
                    f"difference={result.adjustment_value_usd} USD "
                    f"({result.adjustment_direction.value}); no TradeIntent or order was created."
                ),
                source.source_run_id,
                child_run.run_id,
                calculation_id,
            )
        except (TargetPositionValidationError, ValueError) as exc:
            return self._failure(
                command,
                source,
                parent_run_id,
                parent_source_stage_id,
                parent_target_stage_id,
                child_run.run_id,
                child_stage,
                requested_at_utc,
                definition,
                evidence,
                exc,
                invalid=True,
            )
        except Exception as exc:
            logger.exception(
                "Linked Target Position child preview failed run_id=%s",
                child_run.run_id,
            )
            return self._failure(
                command,
                source,
                parent_run_id,
                parent_source_stage_id,
                parent_target_stage_id,
                child_run.run_id,
                child_stage,
                requested_at_utc,
                definition,
                evidence,
                exc,
                invalid=False,
            )

    def _bind_definitions(self, parent_run_id, child_run_id, definition, source) -> None:
        for run_id in (parent_run_id, child_run_id):
            self._run_service.bind(
                run_id,
                RunBindingType.CONFIGURATION,
                str(definition.definition_id),
                str(definition.definition_version),
                source_reference="target_position.definition.v1",
            )
        self._run_service.bind(
            child_run_id,
            RunBindingType.FACTOR_DEFINITION,
            str(source.source_definition_id),
            str(source.source_definition_version),
            source_reference=str(source.source_calculation_id),
        )

    def _failure(
        self,
        command,
        source,
        parent_run_id,
        parent_source_stage_id,
        parent_target_stage_id,
        child_run_id,
        child_stage,
        requested_at_utc,
        definition,
        evidence,
        exc,
        *,
        invalid,
    ) -> LinkedTargetPositionPreviewResult:
        linked_status = (
            LinkedTargetPositionOperationStatus.INVALID_INPUT
            if invalid
            else LinkedTargetPositionOperationStatus.FAILED
        )
        target_status = (
            TargetPositionOperationStatus.INVALID_INPUT
            if invalid
            else TargetPositionOperationStatus.FAILED
        )
        error_code = (
            ErrorCode.LINKED_TARGET_POSITION.value
            if invalid
            else ErrorCode.LINKED_TARGET_POSITION_STORAGE.value
        )
        summary = str(exc) or "linked target-position preview failed"
        target_attempt = self._target_attempt(
            command,
            source,
            child_run_id,
            child_stage.stage_id,
            requested_at_utc,
            target_status,
            resolved_definition_id=(definition.definition_id if definition else None),
            evidence=evidence,
            error_code=error_code,
            error_summary=summary,
        )
        linked_attempt = self._linked_attempt(
            command,
            source,
            parent_run_id,
            parent_source_stage_id,
            parent_target_stage_id,
            child_run_id,
            child_stage.stage_id,
            requested_at_utc,
            linked_status,
            resolved_target_definition_id=(definition.definition_id if definition else None),
            resolved_target_definition_version=(
                definition.definition_version if definition else None
            ),
            error_code=error_code,
            error_summary=summary,
        )
        try:
            self._store.save_linked_failure(target_attempt, linked_attempt)
        except Exception:
            logger.exception(
                "Could not persist failed linked Target Position attempt run_id=%s",
                child_run_id,
            )
        self._run_service.fail_stage(
            child_stage, error_code=error_code, error_summary=summary
        )
        self._run_service.fail_run(
            child_run_id,
            error_code=error_code,
            error_summary=summary,
            invalid_input=invalid,
        )
        return LinkedTargetPositionPreviewResult(
            linked_attempt.attempt_id,
            command.operation_id,
            parent_run_id,
            linked_status,
            summary,
            source.source_run_id,
            child_run_id,
            error_code=error_code,
        )

    def _target_attempt(
        self,
        command,
        source,
        child_run_id,
        child_stage_id,
        requested_at_utc,
        status,
        *,
        resolved_definition_id=None,
        result_calculation_id=None,
        evidence=(),
        error_code=None,
        error_summary=None,
    ) -> TargetPositionOperationAttempt:
        return TargetPositionOperationAttempt(
            attempt_id=self._id_factory(),
            operation_id=command.operation_id,
            run_id=child_run_id,
            stage_id=child_stage_id,
            operation_type=TargetPositionOperationType.PREVIEW,
            status=status,
            requested_at_utc=requested_at_utc,
            completed_at_utc=self._clock(),
            created_by=command.created_by,
            reason=command.reason,
            requested_definition_id=command.target_position_definition_id,
            resolved_definition_id=resolved_definition_id,
            research_state_value_text=str(source.standardized_state),
            research_capital_basis_usd_text=command.research_capital_basis_usd,
            current_position_value_usd_text=command.current_position_value_usd,
            as_of_utc=source.as_of_utc,
            evidence_bindings=evidence,
            result_calculation_id=result_calculation_id,
            error_code=error_code,
            error_summary=error_summary,
        )

    def _linked_attempt(
        self,
        command,
        source,
        parent_run_id,
        source_stage_id,
        target_stage_id,
        child_run_id,
        child_stage_id,
        requested_at_utc,
        status,
        *,
        resolved_target_definition_id=None,
        resolved_target_definition_version=None,
        target_result_calculation_id=None,
        error_code=None,
        error_summary=None,
    ) -> LinkedTargetPositionOperationAttempt:
        return LinkedTargetPositionOperationAttempt(
            self._id_factory(),
            command.operation_id,
            parent_run_id,
            source_stage_id,
            target_stage_id,
            child_run_id,
            child_stage_id,
            status,
            requested_at_utc,
            self._clock(),
            command.standardized_state_calculation_id,
            command.target_position_definition_id,
            command.research_capital_basis_usd,
            command.current_position_value_usd,
            command.session_id,
            command.request_id,
            command.created_by,
            command.reason,
            source.source_run_id,
            source.source_stage_id,
            source.source_definition_id,
            source.source_definition_version,
            source.symbol,
            source.as_of_utc,
            str(source.standardized_state),
            resolved_target_definition_id,
            resolved_target_definition_version,
            target_result_calculation_id,
            error_code,
            error_summary,
        )


__all__ = ["LinkedTargetPositionService"]
