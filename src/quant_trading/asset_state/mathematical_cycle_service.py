"""Run-aware application service for disabled P23-2B state."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
import hashlib
import json
import logging
from uuid import UUID, uuid4

from quant_trading.run_history import (
    AlgorithmRunService,
    AlgorithmRunType,
    RunBindingType,
    RunStageName,
    SoftwareIdentity,
    StartRunRequest,
)

from .mathematical_cycle_engine import MathematicalCycleEngine, MathematicalCycleValidationError
from .mathematical_cycle_interfaces import MathematicalCycleStateStore
from .mathematical_cycle_models import (
    MATHEMATICAL_CYCLE_COMPONENT_ID,
    MATHEMATICAL_CYCLE_COMPONENT_VERSION,
    CreateMathematicalCycleDefinitionCommand,
    MathematicalCycleDefinitionStatus,
    MathematicalCycleOperationStatus,
    MathematicalCycleOperationType,
    MathematicalCyclePromotionCommand,
    MathematicalCycleSourceEvidence,
    MathematicalCycleStateDefinition,
    MathematicalCycleStateOperation,
)


logger = logging.getLogger(__name__)


class MathematicalCycleStateService:
    def __init__(
        self,
        store: MathematicalCycleStateStore,
        run_service: AlgorithmRunService,
        software: SoftwareIdentity,
        *,
        engine: MathematicalCycleEngine | None = None,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
        id_factory: Callable[[], UUID] = uuid4,
    ) -> None:
        self._store = store
        self._runs = run_service
        self._software = software
        self._engine = engine or MathematicalCycleEngine()
        self._clock = clock
        self._id_factory = id_factory

    def save_definition(self, command: CreateMathematicalCycleDefinitionCommand) -> MathematicalCycleStateOperation:
        fingerprint = self._hash({
            "type": "save_definition", "operation_id": str(command.operation_id),
            "session_id": command.session_id, "request_id": command.request_id,
            "predecessor": str(command.predecessor_definition_id) if command.predecessor_definition_id else None,
            "created_by": command.created_by, "reason": command.reason,
        })
        existing = self._store.get_first_operation(command.operation_id)
        if existing and existing.command_fingerprint == fingerprint:
            return existing
        requested = self._clock()
        run = self._runs.start_run(StartRunRequest(
            AlgorithmRunType.MATHEMATICAL_CYCLE_STATE_DEFINITION,
            command.session_id, command.request_id, None, (),
            "algorithm_control_mathematical_cycle_definition", command.created_by,
            self._software, notes="P23-2B disabled mathematical-cycle definition; NO EXECUTION",
        ))
        stage = self._runs.start_stage(run.run_id, RunStageName.STATE, 1)
        try:
            if existing:
                raise ValueError("operation ID is already recorded with different content")
            predecessor = self._store.get_definition(command.predecessor_definition_id) if command.predecessor_definition_id else None
            if command.predecessor_definition_id and predecessor is None:
                raise KeyError("predecessor definition does not exist")
            definition = MathematicalCycleStateDefinition(
                self._id_factory(), predecessor.definition_version + 1 if predecessor else 1,
                predecessor.definition_id if predecessor else None,
                MathematicalCycleDefinitionStatus.DISABLED,
                MATHEMATICAL_CYCLE_COMPONENT_ID, MATHEMATICAL_CYCLE_COMPONENT_VERSION,
                "EXACT_CUMULATIVE_P28_PROMOTION",
                "OLD_DIRECTION_THROUGH_CONFIRMATION_CLOSE",
                "NEXT_EXPECTED_SESSION_START", "PRIOR_REVERSAL_EXTREME_REFERENCE",
                "APPEND_ONLY_ATTRIBUTION_RESOLUTION", self._clock(), command.created_by,
                command.reason, self._software.package_version,
                self._software.source_revision, self._software.worktree_state.value,
            )
            operation = self._operation(
                command.operation_id, run.run_id, stage.stage_id,
                MathematicalCycleOperationType.SAVE_DEFINITION, fingerprint,
                definition.definition_id, definition.definition_version,
                None, None, None, None, MathematicalCycleOperationStatus.COMPLETED,
                None, requested, command.session_id, command.request_id,
                command.created_by, command.reason,
            )
            self._store.save_definition(definition, operation)
            self._runs.bind(run.run_id, RunBindingType.CONFIGURATION, str(definition.definition_id), str(definition.definition_version), source_reference=MATHEMATICAL_CYCLE_COMPONENT_ID)
            self._runs.complete_stage(stage, result_type="mathematical_cycle_state_definition", result_id=str(definition.definition_id))
            self._runs.complete_run(run.run_id)
            return operation
        except Exception as exc:
            return self._failure(
                command.operation_id, run.run_id, stage, MathematicalCycleOperationType.SAVE_DEFINITION,
                fingerprint, requested, command.session_id, command.request_id,
                command.created_by, command.reason, exc,
            )

    def promote(
        self,
        command: MathematicalCyclePromotionCommand,
        source: MathematicalCycleSourceEvidence,
    ) -> MathematicalCycleStateOperation:
        fingerprint = self._promotion_fingerprint(command, source)
        existing = self._store.get_first_operation(command.operation_id)
        if existing and existing.command_fingerprint == fingerprint:
            return existing
        requested = self._clock()
        operation_type = (
            MathematicalCycleOperationType.ADVANCE_STREAM
            if command.stream_id else MathematicalCycleOperationType.CREATE_STREAM
        )
        run = self._runs.start_run(StartRunRequest(
            AlgorithmRunType.MATHEMATICAL_CYCLE_STATE_PROMOTION,
            command.session_id, command.request_id,
            max(step.official_close_utc for step in source.steps), (command.symbol,),
            "algorithm_control_mathematical_cycle_promotion", command.created_by,
            self._software, parent_run_id=command.source_run_id,
            notes="P23-2B exact P28 promotion; disabled state only; NO EXECUTION",
        ))
        stage = self._runs.start_stage(run.run_id, RunStageName.STATE, 1)
        try:
            if existing:
                raise ValueError("operation ID is already recorded with different content")
            definition = self._store.get_definition(command.definition_id)
            if definition is None or definition.definition_version != command.definition_version:
                raise KeyError("exact mathematical-cycle definition does not exist")
            if definition.status is not MathematicalCycleDefinitionStatus.DISABLED:
                raise ValueError("only disabled definitions may be used")
            if source.result_id != command.source_result_id or source.run_id != command.source_run_id or source.symbol != command.symbol:
                raise MathematicalCycleValidationError("SOURCE_INCOMPATIBLE", "resolved source does not match exact command")
            prior = self._store.get_stream_detail(command.stream_id) if command.stream_id else None
            if command.stream_id and prior is None:
                raise KeyError("mathematical-cycle stream does not exist")
            if prior and prior.stream.latest_snapshot_id != command.expected_latest_snapshot_id:
                raise MathematicalCycleValidationError("CONCURRENCY_CONFLICT", "latest snapshot changed")
            stream_id = command.stream_id or self._id_factory()
            materialization = self._engine.materialize(
                stream_id=stream_id, stream_name=command.stream_name,
                definition_id=definition.definition_id,
                definition_version=definition.definition_version,
                source=source, created_at_utc=self._clock(),
                created_by=command.created_by, reason=command.reason, prior=prior,
            )
            status = MathematicalCycleOperationStatus.COMPLETED_WITH_WARNINGS if source.warnings else MathematicalCycleOperationStatus.COMPLETED
            operation = self._operation(
                command.operation_id, run.run_id, stage.stage_id, operation_type,
                fingerprint, definition.definition_id, definition.definition_version,
                stream_id, source.result_id, source.run_id,
                command.expected_latest_snapshot_id, status,
                materialization.stream.latest_snapshot_id, requested,
                command.session_id, command.request_id, command.created_by,
                command.reason, warnings=source.warnings,
            )
            self._store.save_materialization(operation, materialization, prior_detail=prior)
            self._runs.bind(run.run_id, RunBindingType.CONFIGURATION, str(definition.definition_id), str(definition.definition_version), source_reference=MATHEMATICAL_CYCLE_COMPONENT_ID)
            self._runs.bind(run.run_id, RunBindingType.STRATEGY_VERSION, str(source.result_id), str(source.definition_version), source_reference=str(source.run_id))
            self._runs.complete_stage(stage, result_type="mathematical_cycle_state_operation", result_id=str(operation.attempt_id), with_warnings=bool(source.warnings))
            self._runs.complete_run(run.run_id, with_warnings=bool(source.warnings))
            return operation
        except Exception as exc:
            return self._failure(
                command.operation_id, run.run_id, stage, operation_type, fingerprint,
                requested, command.session_id, command.request_id, command.created_by,
                command.reason, exc, definition_id=command.definition_id,
                definition_version=command.definition_version, stream_id=command.stream_id,
                source_result_id=command.source_result_id,
                source_run_id=command.source_run_id,
                expected_latest_snapshot_id=command.expected_latest_snapshot_id,
            )

    def record_source_failure(
        self,
        command: MathematicalCyclePromotionCommand,
        exc: Exception,
    ) -> MathematicalCycleStateOperation:
        """Persist an exact-source preflight failure without inventing source evidence."""
        fingerprint = self._hash({
            "type": "source_failure", "operation_id": str(command.operation_id),
            "definition": [str(command.definition_id), command.definition_version],
            "source": [str(command.source_result_id), str(command.source_run_id)],
            "stream": str(command.stream_id) if command.stream_id else None,
            "predecessor": str(command.expected_latest_snapshot_id) if command.expected_latest_snapshot_id else None,
            "symbol": command.symbol, "session_id": command.session_id,
            "request_id": command.request_id, "created_by": command.created_by,
            "reason": command.reason,
        })
        existing = self._store.get_first_operation(command.operation_id)
        if existing and existing.command_fingerprint == fingerprint:
            return existing
        requested = self._clock()
        operation_type = MathematicalCycleOperationType.ADVANCE_STREAM if command.stream_id else MathematicalCycleOperationType.CREATE_STREAM
        run = self._runs.start_run(StartRunRequest(
            AlgorithmRunType.MATHEMATICAL_CYCLE_STATE_PROMOTION,
            command.session_id, command.request_id, None, (command.symbol,),
            "algorithm_control_mathematical_cycle_source_failure", command.created_by,
            self._software,
            notes="P23-2B exact source preflight failed; no state mutation; NO EXECUTION",
        ))
        stage = self._runs.start_stage(run.run_id, RunStageName.STATE, 1)
        return self._failure(
            command.operation_id, run.run_id, stage, operation_type, fingerprint,
            requested, command.session_id, command.request_id, command.created_by,
            command.reason, exc, definition_id=command.definition_id,
            definition_version=command.definition_version, stream_id=command.stream_id,
            source_result_id=command.source_result_id,
            source_run_id=command.source_run_id,
            expected_latest_snapshot_id=command.expected_latest_snapshot_id,
        )

    def _failure(self, operation_id, run_id, stage, operation_type, fingerprint, requested, session_id, request_id, created_by, reason, exc, **identity):
        logger.exception("P37 operation failed run_id=%s", run_id)
        if isinstance(exc, MathematicalCycleValidationError):
            status = MathematicalCycleOperationStatus.__members__.get(exc.code, MathematicalCycleOperationStatus.INVALID_INPUT)
            code = f"QT-MATHEMATICAL-CYCLE-{exc.code.replace('_', '-')}"
        elif isinstance(exc, KeyError):
            status, code = MathematicalCycleOperationStatus.SOURCE_NOT_FOUND, "QT-MATHEMATICAL-CYCLE-SOURCE-NOT-FOUND"
        elif isinstance(exc, ValueError):
            status, code = MathematicalCycleOperationStatus.INVALID_INPUT, "QT-MATHEMATICAL-CYCLE-INVALID-INPUT"
        else:
            status, code = MathematicalCycleOperationStatus.FAILED, "QT-MATHEMATICAL-CYCLE-FAILED"
        operation = self._operation(
            operation_id, run_id, stage.stage_id, operation_type, fingerprint,
            identity.get("definition_id"), identity.get("definition_version"),
            identity.get("stream_id"), identity.get("source_result_id"),
            identity.get("source_run_id"), identity.get("expected_latest_snapshot_id"),
            status, None, requested, session_id, request_id, created_by, reason,
            error_code=code, error_summary=str(exc),
        )
        try:
            self._store.save_operation(operation)
        except Exception:
            logger.exception("could not persist failed P37 operation run_id=%s", run_id)
        self._runs.fail_stage(stage, error_code=code, error_summary=str(exc))
        self._runs.fail_run(run_id, error_code=code, error_summary=str(exc), invalid_input=status is not MathematicalCycleOperationStatus.FAILED)
        return operation

    def _operation(self, operation_id, run_id, stage_id, operation_type, fingerprint, definition_id, definition_version, stream_id, source_result_id, source_run_id, expected_latest_snapshot_id, status, latest_snapshot_id, requested, session_id, request_id, created_by, reason, *, warnings=(), error_code=None, error_summary=None):
        return MathematicalCycleStateOperation(
            self._id_factory(), operation_id, run_id, stage_id, operation_type,
            fingerprint, definition_id, definition_version, stream_id,
            source_result_id, source_run_id, expected_latest_snapshot_id, status,
            latest_snapshot_id, requested, self._clock(), session_id, request_id,
            created_by, reason, self._software.package_version,
            self._software.source_revision, self._software.worktree_state.value,
            tuple(warnings), error_code, error_summary,
        )

    @staticmethod
    def _promotion_fingerprint(command, source) -> str:
        return MathematicalCycleStateService._hash({
            "type": "advance" if command.stream_id else "create",
            "operation_id": str(command.operation_id),
            "definition": [str(command.definition_id), command.definition_version],
            "source": [str(source.result_id), str(source.run_id)],
            "stream": str(command.stream_id) if command.stream_id else None,
            "predecessor": str(command.expected_latest_snapshot_id) if command.expected_latest_snapshot_id else None,
            "stream_name": command.stream_name, "symbol": command.symbol,
            "session_id": command.session_id, "request_id": command.request_id,
            "created_by": command.created_by, "reason": command.reason,
        })

    @staticmethod
    def _hash(payload) -> str:
        return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


__all__ = ["MathematicalCycleStateService"]
