"""Version definitions, run manual previews and preserve every attempt."""

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
    RunStage,
    RunStageName,
    SoftwareIdentity,
    StartRunRequest,
)

from .engine import TargetPositionEngine
from .errors import TargetPositionValidationError
from .interfaces import TargetPositionStore
from .models import (
    CreateTargetPositionDefinitionCommand,
    PreviewTargetPositionCommand,
    TargetPositionCurveDefinition,
    TargetPositionDefinitionStatus,
    TargetPositionKnot,
    TargetPositionOperationAttempt,
    TargetPositionOperationResult,
    TargetPositionOperationStatus,
    TargetPositionOperationType,
    decimal_text,
    required_text,
)


logger = logging.getLogger(__name__)


class TargetPositionService:
    """Own target-position research lifecycle; never emit an order or TradeIntent."""

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

    def create_definition(
        self, command: CreateTargetPositionDefinitionCommand
    ) -> TargetPositionOperationResult:
        operation_id = command.operation_id or self._id_factory()
        requested_at = self._clock()
        run, stage = self._start(command, "Save immutable target-position curve definition")
        try:
            if self._store.get_first_operation(operation_id) is not None:
                raise TargetPositionValidationError("operation ID is already recorded")
            predecessor = None
            version = 1
            if command.predecessor_definition_id is not None:
                predecessor = self._store.get_definition(command.predecessor_definition_id)
                if predecessor is None:
                    raise TargetPositionValidationError("predecessor definition does not exist")
                version = predecessor.definition_version + 1
            knots = tuple(
                TargetPositionKnot(
                    ordinal,
                    decimal_text(item.state_value, f"knot[{ordinal}].state_value"),
                    decimal_text(item.target_fraction, f"knot[{ordinal}].target_fraction"),
                )
                for ordinal, item in enumerate(command.knots)
            )
            definition = TargetPositionCurveDefinition(
                self._id_factory(),
                version,
                predecessor.definition_id if predecessor else None,
                required_text(command.name, "definition name"),
                required_text(command.reason, "definition reason"),
                command.direction,
                decimal_text(command.minimum_fraction, "minimum_fraction"),
                decimal_text(command.neutral_fraction, "neutral_fraction"),
                decimal_text(command.maximum_fraction, "maximum_fraction"),
                knots,
                TargetPositionDefinitionStatus.AVAILABLE,
                self._clock(),
                command.created_by,
            )
            attempt = self._definition_attempt(
                command, operation_id, requested_at, run.run_id, stage,
                TargetPositionOperationStatus.COMPLETED,
                resolved_definition_id=definition.definition_id,
            )
            self._bind_definition(run.run_id, definition)
            self._store.create_definition(definition, attempt)
            self._complete(stage, "target_position_definition", definition.definition_id)
            return TargetPositionOperationResult(
                attempt.attempt_id,
                operation_id,
                run.run_id,
                stage.stage_id,
                attempt.status,
                f"Target-position definition saved: {definition.name} v{version}; disabled research use only.",
                definition.definition_id,
            )
        except (TargetPositionValidationError, ValueError) as exc:
            return self._definition_failure(command, operation_id, requested_at, run.run_id, stage, exc, True)
        except Exception as exc:
            logger.exception("Target-position definition save failed run_id=%s", run.run_id)
            return self._definition_failure(command, operation_id, requested_at, run.run_id, stage, exc, False)

    def preview(self, command: PreviewTargetPositionCommand) -> TargetPositionOperationResult:
        operation_id = command.operation_id or self._id_factory()
        requested_at = self._clock()
        run, stage = self._start(command, "Calculate manual target-position research preview")
        try:
            if self._store.get_first_operation(operation_id) is not None:
                raise TargetPositionValidationError("operation ID is already recorded")
            definition = self._store.get_definition(command.definition_id)
            if definition is None:
                raise TargetPositionValidationError("target-position definition does not exist")
            if definition.status is not TargetPositionDefinitionStatus.AVAILABLE:
                raise TargetPositionValidationError("archived definition cannot be previewed")
            state_value = decimal_text(command.research_state_value, "research_state_value")
            capital_basis = decimal_text(
                command.research_capital_basis_usd, "research_capital_basis_usd"
            )
            current_position = decimal_text(
                command.current_position_value_usd, "current_position_value_usd"
            )
            if capital_basis < 0 or current_position < 0:
                raise TargetPositionValidationError(
                    "capital basis and current position must be non-negative"
                )
            reason = required_text(command.reason, "preview reason")
            calculation_id = self._id_factory()
            completed_at = self._clock()
            result = self._engine.calculate(
                definition,
                calculation_id=calculation_id,
                operation_id=operation_id,
                run_id=run.run_id,
                stage_id=stage.stage_id,
                as_of_utc=command.as_of_utc,
                research_state_value=state_value,
                research_capital_basis_usd=capital_basis,
                current_position_value_usd=current_position,
                evidence_bindings=command.evidence_bindings,
                created_at_utc=completed_at,
                created_by=command.created_by,
                reason=reason,
            )
            attempt = self._preview_attempt(
                command,
                operation_id,
                requested_at,
                run.run_id,
                stage,
                TargetPositionOperationStatus.COMPLETED,
                resolved_definition_id=definition.definition_id,
                result_calculation_id=calculation_id,
            )
            self._bind_definition(run.run_id, definition)
            self._store.save_preview(result, attempt)
            self._complete(stage, "target_position_result", calculation_id)
            return TargetPositionOperationResult(
                attempt.attempt_id,
                operation_id,
                run.run_id,
                stage.stage_id,
                attempt.status,
                (
                    f"Manual preview: target={result.target_position_value_usd} USD, "
                    f"current={result.current_position_value_usd} USD, "
                    f"difference={result.adjustment_value_usd} USD ({result.adjustment_direction.value}); "
                    "no TradeIntent or order was created."
                ),
                definition.definition_id,
                calculation_id,
            )
        except (TargetPositionValidationError, ValueError) as exc:
            return self._preview_failure(command, operation_id, requested_at, run.run_id, stage, exc, True)
        except Exception as exc:
            logger.exception("Target-position preview failed run_id=%s", run.run_id)
            return self._preview_failure(command, operation_id, requested_at, run.run_id, stage, exc, False)

    def _start(self, command, notes: str):
        run = self._run_service.start_run(
            StartRunRequest(
                AlgorithmRunType.TARGET_POSITION_PREVIEW,
                command.session_id,
                command.request_id,
                getattr(command, "as_of_utc", None),
                (),
                "algorithm_control_target_position",
                command.created_by,
                self._software,
                notes=notes,
            )
        )
        return run, self._run_service.start_stage(run.run_id, RunStageName.TARGET_POSITION, 1)

    def _complete(self, stage: RunStage, result_type: str, result_id: UUID) -> None:
        self._run_service.complete_stage(stage, result_type=result_type, result_id=str(result_id))
        self._run_service.complete_run(stage.run_id)

    def _bind_definition(self, run_id: UUID, definition: TargetPositionCurveDefinition) -> None:
        self._run_service.bind(
            run_id,
            RunBindingType.CONFIGURATION,
            str(definition.definition_id),
            str(definition.definition_version),
            source_reference="target_position.definition.v1",
        )

    def _definition_attempt(
        self, command, operation_id, requested_at, run_id, stage, status,
        *, resolved_definition_id=None, error_code=None, error_summary=None,
    ) -> TargetPositionOperationAttempt:
        return TargetPositionOperationAttempt(
            self._id_factory(), operation_id, run_id, stage.stage_id,
            TargetPositionOperationType.DEFINITION_SAVE, status,
            requested_at, self._clock(), command.created_by, command.reason,
            definition_name=command.name, direction=command.direction.value,
            minimum_fraction_text=command.minimum_fraction,
            neutral_fraction_text=command.neutral_fraction,
            maximum_fraction_text=command.maximum_fraction,
            knot_inputs=command.knots,
            predecessor_definition_id=command.predecessor_definition_id,
            resolved_definition_id=resolved_definition_id,
            error_code=error_code, error_summary=error_summary,
        )

    def _preview_attempt(
        self, command, operation_id, requested_at, run_id, stage, status,
        *, resolved_definition_id=None, result_calculation_id=None,
        error_code=None, error_summary=None,
    ) -> TargetPositionOperationAttempt:
        return TargetPositionOperationAttempt(
            self._id_factory(), operation_id, run_id, stage.stage_id,
            TargetPositionOperationType.PREVIEW, status,
            requested_at, self._clock(), command.created_by, command.reason,
            requested_definition_id=command.definition_id,
            resolved_definition_id=resolved_definition_id,
            research_state_value_text=command.research_state_value,
            research_capital_basis_usd_text=command.research_capital_basis_usd,
            current_position_value_usd_text=command.current_position_value_usd,
            as_of_utc=command.as_of_utc,
            evidence_bindings=command.evidence_bindings,
            result_calculation_id=result_calculation_id,
            error_code=error_code, error_summary=error_summary,
        )

    def _definition_failure(self, command, operation_id, requested_at, run_id, stage, exc, invalid):
        attempt = self._definition_attempt(
            command, operation_id, requested_at, run_id, stage,
            TargetPositionOperationStatus.INVALID_INPUT if invalid else TargetPositionOperationStatus.FAILED,
            error_code=(ErrorCode.TARGET_POSITION.value if invalid else ErrorCode.TARGET_POSITION_STORAGE.value),
            error_summary=str(exc) or "target-position definition failed",
        )
        return self._terminal_failure(attempt, stage, invalid)

    def _preview_failure(self, command, operation_id, requested_at, run_id, stage, exc, invalid):
        attempt = self._preview_attempt(
            command, operation_id, requested_at, run_id, stage,
            TargetPositionOperationStatus.INVALID_INPUT if invalid else TargetPositionOperationStatus.FAILED,
            error_code=(ErrorCode.TARGET_POSITION.value if invalid else ErrorCode.TARGET_POSITION_STORAGE.value),
            error_summary=str(exc) or "target-position preview failed",
        )
        return self._terminal_failure(attempt, stage, invalid)

    def _terminal_failure(self, attempt, stage, invalid):
        try:
            self._store.save_operation(attempt)
        except Exception:
            logger.exception("Could not persist failed target-position operation run_id=%s", attempt.run_id)
        message = attempt.error_summary or "target-position operation failed"
        self._run_service.fail_stage(stage, error_code=attempt.error_code, error_summary=message)
        self._run_service.fail_run(
            attempt.run_id, error_code=attempt.error_code,
            error_summary=message, invalid_input=invalid,
        )
        return TargetPositionOperationResult(
            attempt.attempt_id, attempt.operation_id, attempt.run_id, attempt.stage_id,
            attempt.status, message, attempt.resolved_definition_id,
            attempt.result_calculation_id, attempt.error_code,
        )


__all__ = ["TargetPositionService"]
