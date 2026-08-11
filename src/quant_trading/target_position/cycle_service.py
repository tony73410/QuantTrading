"""Version and execute disabled P23-3A research without downstream authority."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
import hashlib
import json
import logging
import math
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

from .cycle_engine import CycleTargetPositionEngine
from .cycle_interfaces import CycleTargetPositionStore
from .cycle_models import (
    CYCLE_TARGET_ACCELERATION_FORMULA,
    CYCLE_TARGET_COMPONENT_ID,
    CYCLE_TARGET_COMPONENT_VERSION,
    CYCLE_TARGET_LINEAR_FORMULA,
    CYCLE_TARGET_NUMERIC_POLICY,
    CYCLE_TARGET_REGION_POLICY,
    CYCLE_TARGET_SOLVER_ID,
    CYCLE_TARGET_SOLVER_MAX_ITERATIONS,
    CYCLE_TARGET_SOLVER_TOLERANCE,
    CYCLE_TARGET_STATE_FORMULA,
    AssetCycleTargetConfiguration,
    CreateAssetCycleTargetConfigurationCommand,
    CreateCycleTargetFormulaCommand,
    CycleTargetDefinitionStatus,
    CycleTargetFloatEvidence,
    CycleTargetFormulaDefinition,
    CycleTargetOperation,
    CycleTargetOperationStatus,
    CycleTargetOperationType,
    CycleTargetPreviewCommand,
    CycleTargetResponseDirection,
    ReversalObservationTargetInput,
)
from .errors import TargetPositionValidationError


logger = logging.getLogger(__name__)


class CycleTargetPositionService:
    """Own P29 formula/config/result lifecycle; never emit Decision or order objects."""

    def __init__(
        self,
        store: CycleTargetPositionStore,
        run_service: AlgorithmRunService,
        software: SoftwareIdentity,
        *,
        engine: CycleTargetPositionEngine | None = None,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
        id_factory: Callable[[], UUID] = uuid4,
    ) -> None:
        self._store = store
        self._runs = run_service
        self._software = software
        self._engine = engine or CycleTargetPositionEngine()
        self._clock = clock
        self._id_factory = id_factory

    def save_formula_definition(
        self, command: CreateCycleTargetFormulaCommand
    ) -> CycleTargetOperation:
        fingerprint = self._fingerprint({
            "type": "save_formula", "name": command.name, "reason": command.reason,
            "predecessor": str(command.predecessor_formula_definition_id),
            "component": CYCLE_TARGET_COMPONENT_ID,
        })
        existing = self._store.get_first_operation(command.operation_id)
        if existing is not None and existing.command_fingerprint == fingerprint:
            return existing
        requested_at = self._clock()
        run, stage = self._start(
            command.session_id, command.request_id, command.created_by, (), None, None,
            "algorithm_control_cycle_target_formula",
            "Save immutable P23-3A formula definition; DISABLED / NO EXECUTION",
        )
        try:
            if existing is not None:
                raise TargetPositionValidationError("operation ID is already recorded with different content")
            predecessor = None
            if command.predecessor_formula_definition_id is not None:
                predecessor = self._store.get_formula_definition(
                    command.predecessor_formula_definition_id
                )
                if predecessor is None:
                    raise TargetPositionValidationError("predecessor formula definition does not exist")
            definition = CycleTargetFormulaDefinition(
                self._id_factory(),
                predecessor.definition_version + 1 if predecessor else 1,
                predecessor.formula_definition_id if predecessor else None,
                CycleTargetDefinitionStatus.DISABLED,
                command.name,
                command.reason,
                CYCLE_TARGET_COMPONENT_ID,
                CYCLE_TARGET_COMPONENT_VERSION,
                CycleTargetResponseDirection.LOWER_PRICE_HIGHER_TARGET,
                CYCLE_TARGET_STATE_FORMULA,
                CYCLE_TARGET_LINEAR_FORMULA,
                CYCLE_TARGET_ACCELERATION_FORMULA,
                CYCLE_TARGET_REGION_POLICY,
                CYCLE_TARGET_NUMERIC_POLICY,
                CYCLE_TARGET_SOLVER_ID,
                CycleTargetFloatEvidence.calculated(CYCLE_TARGET_SOLVER_TOLERANCE),
                CYCLE_TARGET_SOLVER_MAX_ITERATIONS,
                self._clock(),
                command.created_by,
                self._software.package_version,
                self._software.source_revision,
                self._software.worktree_state.value,
            )
            operation = self._operation(
                command, run.run_id, None, stage.stage_id,
                CycleTargetOperationType.SAVE_FORMULA, fingerprint,
                CycleTargetOperationStatus.COMPLETED,
                requested_at,
                requested_formula_id=command.predecessor_formula_definition_id,
                resolved_formula=definition,
            )
            self._bind_formula(run.run_id, definition)
            self._store.save_formula_definition(definition, operation)
            self._runs.complete_stage(
                stage, result_type="cycle_target_formula_definition",
                result_id=str(definition.formula_definition_id),
            )
            self._runs.complete_run(run.run_id)
            return operation
        except Exception as exc:
            return self._failure(
                command, run.run_id, None, stage, CycleTargetOperationType.SAVE_FORMULA,
                fingerprint, requested_at, exc,
                invalid=isinstance(exc, (TargetPositionValidationError, ValueError, KeyError)),
                requested_formula_id=command.predecessor_formula_definition_id,
            )

    def save_configuration(
        self, command: CreateAssetCycleTargetConfigurationCommand
    ) -> CycleTargetOperation:
        fingerprint = self._fingerprint({
            "type": "save_configuration", "symbol": command.symbol,
            "formula": [str(command.formula_definition_id), command.formula_definition_version],
            "values": [command.minimum_fraction, command.neutral_fraction, command.maximum_fraction,
                       command.linear_slope_per_scale, command.acceleration_start_scales,
                       command.saturation_scales],
            "predecessor": str(command.predecessor_configuration_id), "reason": command.reason,
        })
        existing = self._store.get_first_operation(command.operation_id)
        if existing is not None and existing.command_fingerprint == fingerprint:
            return existing
        requested_at = self._clock()
        run, stage = self._start(
            command.session_id, command.request_id, command.created_by,
            (command.symbol,), None, None, "algorithm_control_cycle_target_configuration",
            "Save immutable per-symbol P23-3A configuration; DISABLED / NO EXECUTION",
        )
        try:
            if existing is not None:
                raise TargetPositionValidationError("operation ID is already recorded with different content")
            formula = self._store.get_formula_definition(command.formula_definition_id)
            if formula is None:
                raise TargetPositionValidationError("formula definition does not exist")
            if formula.definition_version != command.formula_definition_version:
                raise TargetPositionValidationError("formula definition version does not match")
            if formula.status is not CycleTargetDefinitionStatus.DISABLED:
                raise TargetPositionValidationError("archived formula definition cannot be configured")
            predecessor = None
            if command.predecessor_configuration_id is not None:
                predecessor = self._store.get_configuration(command.predecessor_configuration_id)
                if predecessor is None:
                    raise TargetPositionValidationError("predecessor configuration does not exist")
                if predecessor.symbol != command.symbol:
                    raise TargetPositionValidationError("configuration predecessor symbol differs")
            values = tuple(self._input_float(item, name) for item, name in (
                (command.minimum_fraction, "minimum_fraction"),
                (command.neutral_fraction, "neutral_fraction"),
                (command.maximum_fraction, "maximum_fraction"),
                (command.linear_slope_per_scale, "linear_slope_per_scale"),
                (command.acceleration_start_scales, "acceleration_start_scales"),
                (command.saturation_scales, "saturation_scales"),
            ))
            constraint_fingerprint = self._fingerprint({
                "formula": [str(formula.formula_definition_id), formula.definition_version],
                "symbol": command.symbol,
                "values_hex": [item.ieee_hex for item in values],
            })
            configuration = AssetCycleTargetConfiguration(
                self._id_factory(),
                predecessor.configuration_version + 1 if predecessor else 1,
                predecessor.configuration_id if predecessor else None,
                formula.formula_definition_id,
                formula.definition_version,
                command.symbol,
                CycleTargetDefinitionStatus.DISABLED,
                command.minimum_fraction, values[0],
                command.neutral_fraction, values[1],
                command.maximum_fraction, values[2],
                command.linear_slope_per_scale, values[3],
                command.acceleration_start_scales, values[4],
                command.saturation_scales, values[5],
                constraint_fingerprint,
                self._clock(), command.created_by, command.reason,
                self._software.package_version, self._software.source_revision,
                self._software.worktree_state.value,
            )
            operation = self._operation(
                command, run.run_id, None, stage.stage_id,
                CycleTargetOperationType.SAVE_CONFIGURATION, fingerprint,
                CycleTargetOperationStatus.COMPLETED, requested_at,
                requested_formula_id=command.formula_definition_id,
                requested_formula_version=command.formula_definition_version,
                requested_configuration_id=command.predecessor_configuration_id,
                requested_symbol=command.symbol,
                input_values=self._configuration_inputs(command),
                resolved_formula=formula,
                resolved_configuration=configuration,
            )
            self._bind_formula(run.run_id, formula)
            self._bind_configuration(run.run_id, configuration)
            self._store.save_configuration(configuration, operation)
            self._runs.complete_stage(
                stage, result_type="cycle_target_asset_configuration",
                result_id=str(configuration.configuration_id),
            )
            self._runs.complete_run(run.run_id)
            return operation
        except Exception as exc:
            return self._failure(
                command, run.run_id, None, stage,
                CycleTargetOperationType.SAVE_CONFIGURATION, fingerprint,
                requested_at, exc,
                invalid=isinstance(exc, (TargetPositionValidationError, ValueError, KeyError)),
                requested_formula_id=command.formula_definition_id,
                requested_formula_version=command.formula_definition_version,
                requested_configuration_id=command.predecessor_configuration_id,
                requested_symbol=command.symbol,
                input_values=self._configuration_inputs(command),
            )

    def preview(
        self,
        command: CycleTargetPreviewCommand,
        source: ReversalObservationTargetInput,
    ) -> CycleTargetOperation:
        fingerprint = self._preview_fingerprint(command, source)
        existing = self._store.get_first_operation(command.operation_id)
        if existing is not None and existing.command_fingerprint == fingerprint:
            return existing
        requested_at = self._clock()
        run = self._runs.start_run(StartRunRequest(
            AlgorithmRunType.CYCLE_TARGET_POSITION_RESEARCH,
            command.session_id,
            command.request_id,
            source.official_close_utc,
            (source.symbol,),
            "algorithm_control_cycle_target_position",
            command.created_by,
            self._software,
            parent_run_id=source.source_run_id,
            notes="Exact P28 step to bounded P23-3A target; DISABLED / NO EXECUTION",
        ))
        state_stage = self._runs.start_stage(run.run_id, RunStageName.STATE, 1)
        target_stage = None
        state_stage_completed = False
        try:
            if existing is not None:
                raise TargetPositionValidationError("operation ID is already recorded with different content")
            self._validate_source_command(command, source)
            self._runs.complete_stage(
                state_stage, result_type="reversal_observation_daily_step",
                result_id=str(source.source_step_id),
            )
            state_stage_completed = True
            target_stage = self._runs.start_stage(run.run_id, RunStageName.TARGET_POSITION, 2)
            formula, configuration = self._resolve_configuration(command)
            basis = self._decimal(command.research_capital_basis_usd, "research_capital_basis_usd")
            current = self._decimal(command.current_position_value_usd, "current_position_value_usd")
            result = self._engine.calculate(
                formula, configuration, source,
                result_id=self._id_factory(), operation_id=command.operation_id,
                run_id=run.run_id, state_stage_id=state_stage.stage_id,
                target_stage_id=target_stage.stage_id,
                research_capital_basis_usd=basis,
                current_position_value_usd=current,
                created_at_utc=self._clock(), created_by=command.created_by,
                reason=command.reason, software_version=self._software.package_version,
                source_revision=self._software.source_revision,
                worktree_state=self._software.worktree_state.value,
            )
            status = (
                CycleTargetOperationStatus.COMPLETED_WITH_WARNINGS
                if result.warnings else CycleTargetOperationStatus.COMPLETED
            )
            operation = self._operation(
                command, run.run_id, state_stage.stage_id, target_stage.stage_id,
                CycleTargetOperationType.PREVIEW, fingerprint, status, requested_at,
                requested_formula_id=formula.formula_definition_id,
                requested_formula_version=formula.definition_version,
                requested_configuration_id=command.configuration_id,
                requested_configuration_version=command.configuration_version,
                requested_source_result_id=command.source_reversal_result_id,
                requested_source_step_id=command.source_reversal_step_id,
                requested_source_run_id=command.source_reversal_run_id,
                requested_symbol=source.symbol,
                input_values=(
                    ("research_capital_basis_usd", command.research_capital_basis_usd),
                    ("current_position_value_usd", command.current_position_value_usd),
                ),
                resolved_formula=formula,
                resolved_configuration=configuration,
                result=result,
                warnings=result.warnings,
            )
            self._bind_formula(run.run_id, formula)
            self._bind_configuration(run.run_id, configuration)
            self._runs.bind(
                run.run_id, RunBindingType.CONFIGURATION,
                str(source.source_result_id), "1",
                source_reference=str(source.source_step_id),
            )
            self._store.save_preview(result, operation)
            self._runs.complete_stage(
                target_stage, result_type="cycle_target_position_result",
                result_id=str(result.result_id), with_warnings=bool(result.warnings),
            )
            self._runs.complete_run(run.run_id, with_warnings=bool(result.warnings))
            return operation
        except Exception as exc:
            stage = target_stage or state_stage
            return self._failure(
                command, run.run_id, state_stage.stage_id, stage,
                CycleTargetOperationType.PREVIEW, fingerprint, requested_at, exc,
                invalid=isinstance(exc, (TargetPositionValidationError, ValueError, KeyError)),
                requested_configuration_id=command.configuration_id,
                requested_configuration_version=command.configuration_version,
                requested_source_result_id=command.source_reversal_result_id,
                requested_source_step_id=command.source_reversal_step_id,
                requested_source_run_id=command.source_reversal_run_id,
                requested_symbol=source.symbol,
                input_values=(
                    ("research_capital_basis_usd", command.research_capital_basis_usd),
                    ("current_position_value_usd", command.current_position_value_usd),
                ),
                source_stage=state_stage,
                source_stage_completed=state_stage_completed,
            )

    def record_source_failure(
        self,
        command: CycleTargetPreviewCommand,
        error: Exception,
        *,
        source_not_found: bool,
    ) -> CycleTargetOperation:
        fingerprint = self._fingerprint({
            "type": "preview_source_failure", "configuration": str(command.configuration_id),
            "configuration_version": command.configuration_version,
            "source_result": str(command.source_reversal_result_id),
            "source_step": str(command.source_reversal_step_id),
            "source_run": str(command.source_reversal_run_id),
            "basis": command.research_capital_basis_usd, "current": command.current_position_value_usd,
        })
        existing = self._store.get_first_operation(command.operation_id)
        if existing is not None and existing.command_fingerprint == fingerprint:
            return existing
        requested_at = self._clock()
        run = self._runs.start_run(StartRunRequest(
            AlgorithmRunType.CYCLE_TARGET_POSITION_RESEARCH, command.session_id,
            command.request_id, None, (), "algorithm_control_cycle_target_position",
            command.created_by, self._software,
            notes="P23-3A source validation failed closed; NO EXECUTION",
        ))
        state_stage = self._runs.start_stage(run.run_id, RunStageName.STATE, 1)
        status = (
            CycleTargetOperationStatus.SOURCE_NOT_FOUND
            if source_not_found else CycleTargetOperationStatus.SOURCE_INCOMPATIBLE
        )
        operation = self._operation(
            command, run.run_id, state_stage.stage_id, None,
            CycleTargetOperationType.PREVIEW, fingerprint, status, requested_at,
            requested_configuration_id=command.configuration_id,
            requested_configuration_version=command.configuration_version,
            requested_source_result_id=command.source_reversal_result_id,
            requested_source_step_id=command.source_reversal_step_id,
            requested_source_run_id=command.source_reversal_run_id,
            input_values=(
                ("research_capital_basis_usd", command.research_capital_basis_usd),
                ("current_position_value_usd", command.current_position_value_usd),
            ),
            error_code=ErrorCode.CYCLE_TARGET_POSITION_SOURCE.value,
            error_summary=str(error) or "P28 source validation failed",
        )
        self._store.save_operation(operation)
        self._runs.fail_stage(
            state_stage, error_code=operation.error_code,
            error_summary=operation.error_summary or "P28 source validation failed",
        )
        self._runs.fail_run(
            run.run_id, error_code=operation.error_code,
            error_summary=operation.error_summary or "P28 source validation failed",
            invalid_input=True,
        )
        return operation

    def _resolve_configuration(self, command):
        configuration = self._store.get_configuration(command.configuration_id)
        if configuration is None:
            raise TargetPositionValidationError("cycle-target configuration does not exist")
        if configuration.configuration_version != command.configuration_version:
            raise TargetPositionValidationError("cycle-target configuration version does not match")
        if configuration.status is not CycleTargetDefinitionStatus.DISABLED:
            raise TargetPositionValidationError("archived configuration cannot be previewed")
        formula = self._store.get_formula_definition(configuration.formula_definition_id)
        if formula is None:
            raise TargetPositionValidationError("configuration formula cannot be reloaded")
        return formula, configuration

    def _start(self, session_id, request_id, created_by, symbols, as_of, parent, trigger, notes):
        run = self._runs.start_run(StartRunRequest(
            AlgorithmRunType.CYCLE_TARGET_POSITION_RESEARCH, session_id, request_id,
            as_of, symbols, trigger, created_by, self._software,
            parent_run_id=parent, notes=notes,
        ))
        return run, self._runs.start_stage(run.run_id, RunStageName.TARGET_POSITION, 1)

    def _failure(
        self, command, run_id, state_stage_id, stage, operation_type, fingerprint,
        requested_at, exc, *, invalid, source_stage=None,
        source_stage_completed=False, **kwargs,
    ):
        status = CycleTargetOperationStatus.INVALID_INPUT if invalid else CycleTargetOperationStatus.FAILED
        code = (
            ErrorCode.CYCLE_TARGET_POSITION.value
            if invalid else ErrorCode.CYCLE_TARGET_POSITION_STORAGE.value
        )
        summary = str(exc) or "cycle-target operation failed"
        operation = self._operation(
            command, run_id, state_stage_id,
            stage.stage_id if stage is not source_stage else None,
            operation_type, fingerprint, status, requested_at,
            error_code=code, error_summary=summary, **kwargs,
        )
        try:
            self._store.save_operation(operation)
        except Exception:
            logger.exception("Could not persist failed P29 operation run_id=%s", run_id)
        try:
            if not (stage is source_stage and source_stage_completed):
                self._runs.fail_stage(stage, error_code=code, error_summary=summary)
            self._runs.fail_run(run_id, error_code=code, error_summary=summary, invalid_input=invalid)
        except Exception:
            logger.exception("Could not finalize failed P29 Run run_id=%s", run_id)
        return operation

    def _operation(
        self, command, run_id, state_stage_id, target_stage_id, operation_type,
        fingerprint, status, requested_at, *, requested_formula_id=None,
        requested_formula_version=None, requested_configuration_id=None,
        requested_configuration_version=None, requested_source_result_id=None,
        requested_source_step_id=None, requested_source_run_id=None,
        requested_symbol=None, input_values=(), resolved_formula=None,
        resolved_configuration=None, result=None, warnings=(), error_code=None,
        error_summary=None,
    ) -> CycleTargetOperation:
        return CycleTargetOperation(
            self._id_factory(), command.operation_id, run_id, state_stage_id,
            target_stage_id, operation_type, fingerprint, status,
            requested_at, self._clock(), command.session_id, command.request_id,
            command.created_by, command.reason,
            requested_formula_id, requested_formula_version,
            requested_configuration_id, requested_configuration_version,
            requested_source_result_id, requested_source_step_id, requested_source_run_id,
            requested_symbol, tuple(input_values),
            resolved_formula.formula_definition_id if resolved_formula else None,
            resolved_formula.definition_version if resolved_formula else None,
            resolved_configuration.configuration_id if resolved_configuration else None,
            resolved_configuration.configuration_version if resolved_configuration else None,
            result, tuple(warnings), error_code, error_summary,
            self._software.package_version, self._software.source_revision,
            self._software.worktree_state.value,
        )

    def _bind_formula(self, run_id, formula):
        self._runs.bind(
            run_id, RunBindingType.CONFIGURATION,
            str(formula.formula_definition_id), str(formula.definition_version),
            source_reference=CYCLE_TARGET_COMPONENT_ID,
        )

    def _bind_configuration(self, run_id, configuration):
        self._runs.bind(
            run_id, RunBindingType.CONFIGURATION,
            str(configuration.configuration_id), str(configuration.configuration_version),
            source_reference="target_position.asset_cycle_configuration.v1",
        )

    @staticmethod
    def _input_float(value: str, name: str) -> CycleTargetFloatEvidence:
        try:
            numeric = float(value.strip())
        except (AttributeError, ValueError) as exc:
            raise TargetPositionValidationError(f"{name} must be a binary64 number") from exc
        if not math.isfinite(numeric):
            raise TargetPositionValidationError(f"{name} must be finite")
        return CycleTargetFloatEvidence(value.strip(), numeric)

    @staticmethod
    def _decimal(value: str, name: str) -> Decimal:
        try:
            parsed = Decimal(value.strip())
        except (AttributeError, InvalidOperation) as exc:
            raise TargetPositionValidationError(f"{name} must be Decimal text") from exc
        if not parsed.is_finite() or parsed < 0:
            raise TargetPositionValidationError(f"{name} must be finite and non-negative")
        return parsed

    @staticmethod
    def _validate_source_command(command, source):
        if command.source_reversal_result_id != source.source_result_id:
            raise TargetPositionValidationError("selected P28 result does not match resolved source")
        if command.source_reversal_step_id != source.source_step_id:
            raise TargetPositionValidationError("selected P28 daily step does not match resolved source")
        if command.source_reversal_run_id != source.source_run_id:
            raise TargetPositionValidationError("selected P28 Run does not match resolved source")

    @staticmethod
    def _configuration_inputs(command):
        return (
            ("minimum_fraction", command.minimum_fraction),
            ("neutral_fraction", command.neutral_fraction),
            ("maximum_fraction", command.maximum_fraction),
            ("linear_slope_per_scale", command.linear_slope_per_scale),
            ("acceleration_start_scales", command.acceleration_start_scales),
            ("saturation_scales", command.saturation_scales),
        )

    @classmethod
    def _preview_fingerprint(cls, command, source):
        return cls._fingerprint({
            "type": "preview", "configuration": [str(command.configuration_id), command.configuration_version],
            "source": [str(source.source_result_id), str(source.source_step_id), str(source.source_run_id),
                       source.source_calculation_fingerprint, source.split_close.value.ieee_hex,
                       source.cycle_reference_price.value.ieee_hex, source.profile_log_scale.ieee_hex],
            "basis": command.research_capital_basis_usd,
            "current": command.current_position_value_usd,
            "reason": command.reason,
        })

    @staticmethod
    def _fingerprint(payload) -> str:
        return hashlib.sha256(json.dumps(
            payload, sort_keys=True, separators=(",", ":"), default=str
        ).encode("utf-8")).hexdigest()


__all__ = ["CycleTargetPositionService"]
