"""Version definitions and preserve manual standardized-state preview attempts."""

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

from .errors import StandardizedPriceStateValidationError
from .standardized_state_engine import StandardizedPriceStateEngine
from .standardized_state_interfaces import StandardizedPriceStateStore
from .standardized_state_models import (
    DIMENSIONLESS,
    STANDARDIZED_PRICE_STATE_FORMULA_ID,
    USD,
    CreateStandardizedPriceStateDefinitionCommand,
    PreviewStandardizedPriceStateCommand,
    StandardizedPriceStateDefinition,
    StandardizedPriceStateDefinitionStatus,
    StandardizedPriceStateInputSource,
    StandardizedPriceStateOperationAttempt,
    StandardizedPriceStateOperationResult,
    StandardizedPriceStateOperationStatus,
    StandardizedPriceStateOperationType,
    decimal_text,
    normalized_symbol,
    required_text,
)


logger = logging.getLogger(__name__)


class StandardizedPriceStateService:
    """Own manual Factor-state history without publishing a generic FactorSnapshot."""

    def __init__(
        self,
        store: StandardizedPriceStateStore,
        run_service: AlgorithmRunService,
        software: SoftwareIdentity,
        *,
        engine: StandardizedPriceStateEngine | None = None,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
        id_factory: Callable[[], UUID] = uuid4,
    ) -> None:
        self._store = store
        self._run_service = run_service
        self._software = software
        self._engine = engine or StandardizedPriceStateEngine()
        self._clock = clock
        self._id_factory = id_factory

    def create_definition(
        self, command: CreateStandardizedPriceStateDefinitionCommand
    ) -> StandardizedPriceStateOperationResult:
        operation_id = command.operation_id or self._id_factory()
        requested_at = self._clock()
        run, stage = self._start(
            command,
            "Save immutable manual standardized-price-state definition",
            (),
        )
        try:
            if self._store.get_first_operation(operation_id) is not None:
                raise StandardizedPriceStateValidationError(
                    "operation ID is already recorded"
                )
            predecessor = None
            version = 1
            if command.predecessor_definition_id is not None:
                predecessor = self._store.get_definition(
                    command.predecessor_definition_id
                )
                if predecessor is None:
                    raise StandardizedPriceStateValidationError(
                        "predecessor definition does not exist"
                    )
                version = predecessor.definition_version + 1
            definition = StandardizedPriceStateDefinition(
                self._id_factory(),
                version,
                predecessor.definition_id if predecessor else None,
                required_text(command.name, "definition name"),
                required_text(command.reason, "definition reason"),
                STANDARDIZED_PRICE_STATE_FORMULA_ID,
                USD,
                DIMENSIONLESS,
                StandardizedPriceStateInputSource.MANUAL_RESEARCH,
                StandardizedPriceStateInputSource.MANUAL_RESEARCH,
                StandardizedPriceStateInputSource.MANUAL_RESEARCH,
                StandardizedPriceStateDefinitionStatus.AVAILABLE,
                self._clock(),
                command.created_by,
            )
            attempt = self._definition_attempt(
                command,
                operation_id,
                requested_at,
                run.run_id,
                stage,
                StandardizedPriceStateOperationStatus.COMPLETED,
                resolved_definition_id=definition.definition_id,
            )
            self._bind_definition(run.run_id, definition)
            self._store.create_definition(definition, attempt)
            self._complete(
                stage,
                "standardized_price_state_definition",
                definition.definition_id,
            )
            return StandardizedPriceStateOperationResult(
                attempt.attempt_id,
                operation_id,
                run.run_id,
                stage.stage_id,
                attempt.status,
                (
                    f"Standardized-state definition saved: {definition.name} "
                    f"v{version}; manual Factor research only."
                ),
                definition.definition_id,
            )
        except (StandardizedPriceStateValidationError, ValueError) as exc:
            return self._definition_failure(
                command, operation_id, requested_at, run.run_id, stage, exc, True
            )
        except Exception as exc:
            logger.exception(
                "Standardized-state definition save failed run_id=%s", run.run_id
            )
            return self._definition_failure(
                command, operation_id, requested_at, run.run_id, stage, exc, False
            )

    def preview(
        self, command: PreviewStandardizedPriceStateCommand
    ) -> StandardizedPriceStateOperationResult:
        operation_id = command.operation_id or self._id_factory()
        requested_at = self._clock()
        symbols = (command.symbol.strip().upper(),) if command.symbol.strip() else ()
        run, stage = self._start(
            command,
            "Calculate manual standardized-price-state research preview",
            symbols,
        )
        try:
            if self._store.get_first_operation(operation_id) is not None:
                raise StandardizedPriceStateValidationError(
                    "operation ID is already recorded"
                )
            definition = self._store.get_definition(command.definition_id)
            if definition is None:
                raise StandardizedPriceStateValidationError(
                    "standardized-state definition does not exist"
                )
            if definition.status is not StandardizedPriceStateDefinitionStatus.AVAILABLE:
                raise StandardizedPriceStateValidationError(
                    "archived definition cannot be previewed"
                )
            symbol = normalized_symbol(command.symbol)
            price = decimal_text(command.manual_price_usd, "manual_price_usd")
            reference = decimal_text(
                command.manual_reference_price_usd,
                "manual_reference_price_usd",
            )
            scale = decimal_text(
                command.manual_risk_scale_usd,
                "manual_risk_scale_usd",
            )
            if price <= 0 or reference <= 0 or scale <= 0:
                raise StandardizedPriceStateValidationError(
                    "manual price, reference and risk scale must be positive"
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
                symbol=symbol,
                as_of_utc=command.as_of_utc,
                manual_price_usd=price,
                manual_reference_price_usd=reference,
                manual_risk_scale_usd=scale,
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
                StandardizedPriceStateOperationStatus.COMPLETED,
                resolved_definition_id=definition.definition_id,
                result_calculation_id=calculation_id,
            )
            self._bind_definition(run.run_id, definition)
            self._store.save_preview(result, attempt)
            self._complete(stage, "standardized_price_state_result", calculation_id)
            return StandardizedPriceStateOperationResult(
                attempt.attempt_id,
                operation_id,
                run.run_id,
                stage.stage_id,
                attempt.status,
                (
                    f"{symbol}: deviation={result.price_deviation_usd} USD; "
                    f"standardized state={result.standardized_state}. "
                    "No Target Position, TradeIntent, Risk approval or order was created."
                ),
                definition.definition_id,
                calculation_id,
            )
        except (StandardizedPriceStateValidationError, ValueError) as exc:
            return self._preview_failure(
                command, operation_id, requested_at, run.run_id, stage, exc, True
            )
        except Exception as exc:
            logger.exception(
                "Standardized-state preview failed run_id=%s", run.run_id
            )
            return self._preview_failure(
                command, operation_id, requested_at, run.run_id, stage, exc, False
            )

    def _start(self, command, notes: str, symbols: tuple[str, ...]):
        run = self._run_service.start_run(
            StartRunRequest(
                AlgorithmRunType.STANDARDIZED_STATE_PREVIEW,
                command.session_id,
                command.request_id,
                None,
                symbols,
                "algorithm_control_standardized_state",
                command.created_by,
                self._software,
                notes=notes,
            )
        )
        return run, self._run_service.start_stage(
            run.run_id, RunStageName.STANDARDIZED_STATE, 1
        )

    def _complete(self, stage: RunStage, result_type: str, result_id: UUID) -> None:
        self._run_service.complete_stage(
            stage, result_type=result_type, result_id=str(result_id)
        )
        self._run_service.complete_run(stage.run_id)

    def _bind_definition(
        self, run_id: UUID, definition: StandardizedPriceStateDefinition
    ) -> None:
        self._run_service.bind(
            run_id,
            RunBindingType.FACTOR_DEFINITION,
            str(definition.definition_id),
            str(definition.definition_version),
            source_reference="factor.standardized_price_state.definition.v1",
        )

    def _definition_attempt(
        self,
        command,
        operation_id,
        requested_at,
        run_id,
        stage,
        status,
        *,
        resolved_definition_id=None,
        error_code=None,
        error_summary=None,
    ) -> StandardizedPriceStateOperationAttempt:
        return StandardizedPriceStateOperationAttempt(
            self._id_factory(),
            operation_id,
            run_id,
            stage.stage_id,
            StandardizedPriceStateOperationType.DEFINITION_SAVE,
            status,
            requested_at,
            self._clock(),
            command.created_by,
            command.reason,
            definition_name=command.name,
            predecessor_definition_id=command.predecessor_definition_id,
            resolved_definition_id=resolved_definition_id,
            error_code=error_code,
            error_summary=error_summary,
        )

    def _preview_attempt(
        self,
        command,
        operation_id,
        requested_at,
        run_id,
        stage,
        status,
        *,
        resolved_definition_id=None,
        result_calculation_id=None,
        error_code=None,
        error_summary=None,
    ) -> StandardizedPriceStateOperationAttempt:
        return StandardizedPriceStateOperationAttempt(
            self._id_factory(),
            operation_id,
            run_id,
            stage.stage_id,
            StandardizedPriceStateOperationType.PREVIEW,
            status,
            requested_at,
            self._clock(),
            command.created_by,
            command.reason,
            requested_definition_id=command.definition_id,
            resolved_definition_id=resolved_definition_id,
            symbol=(
                normalized_symbol(command.symbol)
                if status is StandardizedPriceStateOperationStatus.COMPLETED
                else command.symbol.strip().upper() or None
            ),
            manual_price_usd_text=command.manual_price_usd,
            manual_reference_price_usd_text=command.manual_reference_price_usd,
            manual_risk_scale_usd_text=command.manual_risk_scale_usd,
            as_of_utc=command.as_of_utc,
            evidence_bindings=command.evidence_bindings,
            result_calculation_id=result_calculation_id,
            error_code=error_code,
            error_summary=error_summary,
        )

    def _definition_failure(
        self, command, operation_id, requested_at, run_id, stage, exc, invalid
    ):
        attempt = self._definition_attempt(
            command,
            operation_id,
            requested_at,
            run_id,
            stage,
            StandardizedPriceStateOperationStatus.INVALID_INPUT
            if invalid
            else StandardizedPriceStateOperationStatus.FAILED,
            error_code=(
                ErrorCode.STANDARDIZED_STATE.value
                if invalid
                else ErrorCode.STANDARDIZED_STATE_STORAGE.value
            ),
            error_summary=str(exc) or "standardized-state definition failed",
        )
        return self._terminal_failure(attempt, stage, invalid)

    def _preview_failure(
        self, command, operation_id, requested_at, run_id, stage, exc, invalid
    ):
        attempt = self._preview_attempt(
            command,
            operation_id,
            requested_at,
            run_id,
            stage,
            StandardizedPriceStateOperationStatus.INVALID_INPUT
            if invalid
            else StandardizedPriceStateOperationStatus.FAILED,
            error_code=(
                ErrorCode.STANDARDIZED_STATE.value
                if invalid
                else ErrorCode.STANDARDIZED_STATE_STORAGE.value
            ),
            error_summary=str(exc) or "standardized-state preview failed",
        )
        return self._terminal_failure(attempt, stage, invalid)

    def _terminal_failure(self, attempt, stage, invalid):
        try:
            self._store.save_operation(attempt)
        except Exception:
            logger.exception(
                "Could not persist failed standardized-state operation run_id=%s",
                attempt.run_id,
            )
        message = attempt.error_summary or "standardized-state operation failed"
        self._run_service.fail_stage(
            stage, error_code=attempt.error_code, error_summary=message
        )
        self._run_service.fail_run(
            attempt.run_id,
            error_code=attempt.error_code,
            error_summary=message,
            invalid_input=invalid,
        )
        return StandardizedPriceStateOperationResult(
            attempt.attempt_id,
            attempt.operation_id,
            attempt.run_id,
            attempt.stage_id,
            attempt.status,
            message,
            attempt.resolved_definition_id,
            attempt.result_calculation_id,
            attempt.error_code,
        )


__all__ = ["StandardizedPriceStateService"]
