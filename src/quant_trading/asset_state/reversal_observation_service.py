"""Run-aware application service for disabled P23-2 research."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
import hashlib
import json
import logging
import math
from uuid import UUID, uuid4

from quant_trading.run_history import (
    AlgorithmRunService,
    AlgorithmRunType,
    RunBindingType,
    RunMessageSeverity,
    RunStageName,
    SoftwareIdentity,
    StartRunRequest,
)

from .reversal_observation_engine import (
    ReversalObservationEngine,
    ReversalObservationValidationError,
)
from .reversal_observation_interfaces import ReversalObservationStore
from .reversal_observation_models import (
    REVERSAL_OBSERVATION_COMPONENT_ID,
    REVERSAL_OBSERVATION_COMPONENT_VERSION,
    CreateReversalObservationDefinitionCommand,
    ReversalFloatEvidence,
    ReversalObservationCommand,
    ReversalObservationDefinition,
    ReversalObservationDefinitionStatus,
    ReversalObservationMarketEvidence,
    ReversalObservationOperation,
    ReversalObservationOperationStatus,
    ReversalObservationOperationType,
    ReversalObservationProfileEvidence,
    ReversalObservationResultStatus,
)


logger = logging.getLogger(__name__)


class ReversalObservationService:
    """Persist exact definitions and evaluate resolved evidence only."""

    def __init__(
        self,
        store: ReversalObservationStore,
        run_service: AlgorithmRunService,
        software: SoftwareIdentity,
        *,
        engine: ReversalObservationEngine | None = None,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
        id_factory: Callable[[], UUID] = uuid4,
    ) -> None:
        self._store = store
        self._runs = run_service
        self._software = software
        self._engine = engine or ReversalObservationEngine()
        self._clock = clock
        self._id_factory = id_factory

    def save_definition(
        self, command: CreateReversalObservationDefinitionCommand
    ) -> ReversalObservationOperation:
        fingerprint = self._definition_fingerprint(command)
        existing = self._store.get_first_operation(command.operation_id)
        if existing is not None and existing.command_fingerprint == fingerprint:
            return existing
        requested_at = self._clock()
        run = self._start_run(
            command.session_id, command.request_id, command.created_by,
            (), None, "algorithm_control_reversal_definition",
            "P23-2 immutable symmetric reversal definition; NO EXECUTION",
        )
        stage = self._runs.start_stage(run.run_id, RunStageName.STATE, 1)
        try:
            if existing is not None:
                raise ValueError("operation ID is already recorded with different content")
            try:
                multiplier = float(command.shared_multiplier_input_text)
            except ValueError as exc:
                raise ValueError("shared multiplier must be a number") from exc
            if not math.isfinite(multiplier) or multiplier <= 0:
                raise ValueError("shared multiplier must be positive and finite")
            predecessor = (
                self._store.get_definition(command.predecessor_definition_id)
                if command.predecessor_definition_id is not None
                else None
            )
            if command.predecessor_definition_id is not None and predecessor is None:
                raise KeyError("predecessor definition does not exist")
            definition = ReversalObservationDefinition(
                self._id_factory(),
                predecessor.definition_version + 1 if predecessor else 1,
                predecessor.definition_id if predecessor else None,
                ReversalObservationDefinitionStatus.DISABLED,
                command.shared_multiplier_input_text,
                ReversalFloatEvidence(multiplier),
                REVERSAL_OBSERVATION_COMPONENT_ID,
                REVERSAL_OBSERVATION_COMPONENT_VERSION,
                "T=M*k", 2, "INCLUSIVE_GREATER_THAN_OR_EQUAL",
                "NEXT_EXPECTED_SESSION_START", "COMMIT_FROM_PRIOR_REVERSAL_EXTREME",
                "DISCARD_NEW_CYCLE_ATTRIBUTION_ONLY", "FORWARD_FROZEN_PROFILE",
                self._clock(), command.created_by, command.reason,
                self._software.package_version, self._software.source_revision,
                self._software.worktree_state.value,
            )
            operation = self._operation(
                command.operation_id, run.run_id, stage.stage_id,
                ReversalObservationOperationType.SAVE_DEFINITION, fingerprint,
                definition.definition_id, definition.definition_version, None, None,
                ReversalObservationOperationStatus.COMPLETED, None, requested_at,
                command.session_id, command.request_id, command.created_by, command.reason,
            )
            self._store.save_definition(definition, operation)
            self._runs.bind(
                run.run_id, RunBindingType.CONFIGURATION, str(definition.definition_id),
                str(definition.definition_version), source_reference=REVERSAL_OBSERVATION_COMPONENT_ID,
            )
            self._runs.complete_stage(
                stage, result_type="reversal_observation_definition",
                result_id=str(definition.definition_id),
            )
            self._runs.complete_run(run.run_id)
            return operation
        except Exception as exc:
            return self._failure(
                ReversalObservationOperationType.SAVE_DEFINITION, command.operation_id,
                fingerprint, run.run_id, stage, requested_at, command.session_id,
                command.request_id, command.created_by, command.reason, exc,
                invalid=isinstance(exc, (ValueError, KeyError)),
            )

    def preview(
        self,
        command: ReversalObservationCommand,
        profile: ReversalObservationProfileEvidence,
        market: ReversalObservationMarketEvidence,
    ) -> ReversalObservationOperation:
        fingerprint = self._command_fingerprint(command, profile, market)
        existing = self._store.get_first_operation(command.operation_id)
        if existing is not None and existing.command_fingerprint == fingerprint:
            return existing
        requested_at = self._clock()
        run = self._start_run(
            command.session_id, command.request_id, command.created_by,
            (command.symbol,), max(
                (item.official_close_utc for item in market.observations),
                default=market.seed_observation.official_close_utc,
            ),
            "algorithm_control_reversal_observation",
            "P23-2 symmetric reversal observation; formal state unchanged; NO EXECUTION",
            parent_run_id=profile.result_run_id,
        )
        stage = self._runs.start_stage(run.run_id, RunStageName.STATE, 1)
        try:
            if existing is not None:
                raise ReversalObservationValidationError(
                    ReversalObservationResultStatus.SOURCE_EVIDENCE_MISMATCH,
                    "operation ID is already recorded with different content",
                )
            definition = self._store.get_definition(command.definition_id)
            if definition is None:
                raise KeyError("requested reversal definition does not exist")
            self._bind(run.run_id, definition, profile, market)
            calculated = self._engine.calculate(
                definition, command, profile, market,
                created_at_utc=self._clock(),
                software_version=self._software.package_version,
                source_revision=self._software.source_revision,
                worktree_state=self._software.worktree_state.value,
            )
            result = self._store.get_result_by_fingerprint(calculated.calculation_fingerprint) or calculated
            status = (
                ReversalObservationOperationStatus.COMPLETED_WITH_WARNINGS
                if result.warnings else ReversalObservationOperationStatus.COMPLETED
            )
            operation = self._operation(
                command.operation_id, run.run_id, stage.stage_id,
                ReversalObservationOperationType.PREVIEW, fingerprint,
                definition.definition_id, definition.definition_version,
                profile.result_id, command.symbol, status, result, requested_at,
                command.session_id, command.request_id, command.created_by, command.reason,
                warnings=result.warnings,
            )
            self._store.save_operation(operation)
            self._runs.complete_stage(
                stage, result_type="reversal_observation_result",
                result_id=str(result.result_id), with_warnings=bool(result.warnings),
            )
            for warning in result.warnings:
                self._runs.record_message(
                    run.run_id, RunMessageSeverity.WARNING,
                    "QT-REVERSAL-OBSERVATION-WARNING", warning, stage_id=stage.stage_id,
                )
            self._runs.complete_run(run.run_id, with_warnings=bool(result.warnings))
            return operation
        except Exception as exc:
            invalid = isinstance(exc, (ValueError, KeyError, ReversalObservationValidationError))
            return self._failure(
                ReversalObservationOperationType.PREVIEW, command.operation_id, fingerprint,
                run.run_id, stage, requested_at, command.session_id, command.request_id,
                command.created_by, command.reason, exc, invalid=invalid,
                definition_id=command.definition_id,
                definition_version=command.definition_version,
                profile_result_id=command.profile_result_id,
                expected_symbol=command.symbol,
            )

    def _start_run(
        self, session_id, request_id, created_by, symbols, market_as_of,
        trigger, notes, *, parent_run_id=None,
    ):
        return self._runs.start_run(StartRunRequest(
            AlgorithmRunType.REVERSAL_OBSERVATION_RESEARCH,
            session_id, request_id, market_as_of, symbols, trigger, created_by,
            self._software, parent_run_id=parent_run_id, notes=notes,
        ))

    def _bind(self, run_id, definition, profile, market) -> None:
        self._runs.bind(run_id, RunBindingType.CONFIGURATION, str(definition.definition_id),
                        str(definition.definition_version), source_reference=definition.component_id)
        self._runs.bind(run_id, RunBindingType.FACTOR_DEFINITION, str(profile.result_id),
                        profile.component_version, source_reference=profile.calculation_fingerprint)
        self._runs.bind(run_id, RunBindingType.MARKET_DATA, str(market.evidence_id), "1",
                        source_reference=market.content_fingerprint)

    def _operation(
        self, operation_id, run_id, stage_id, operation_type, fingerprint,
        definition_id, definition_version, profile_result_id, symbol, status, result,
        requested_at, session_id, request_id, created_by, reason, *, warnings=(),
        error_code=None, error_summary=None,
    ) -> ReversalObservationOperation:
        return ReversalObservationOperation(
            self._id_factory(), operation_id, run_id, stage_id, operation_type,
            fingerprint, definition_id, definition_version, profile_result_id, symbol,
            status, result, requested_at, self._clock(), session_id, request_id,
            created_by, reason, self._software.package_version,
            self._software.source_revision, self._software.worktree_state.value,
            tuple(warnings), error_code, error_summary,
        )

    def _failure(
        self, operation_type, operation_id, fingerprint, run_id, stage,
        requested_at, session_id, request_id, created_by, reason, exc, *, invalid,
        definition_id=None, definition_version=None, profile_result_id=None,
        expected_symbol=None,
    ) -> ReversalObservationOperation:
        logger.exception("P28 operation failed run_id=%s", run_id)
        if isinstance(exc, KeyError):
            status = ReversalObservationOperationStatus.SOURCE_NOT_FOUND
            code = "QT-REVERSAL-SOURCE-NOT-FOUND"
        elif isinstance(exc, ReversalObservationValidationError) and (
            exc.status is ReversalObservationResultStatus.SOURCE_VERSION_INCOMPATIBLE
        ):
            status = ReversalObservationOperationStatus.SOURCE_INCOMPATIBLE
            code = "QT-REVERSAL-SOURCE-INCOMPATIBLE"
        elif invalid:
            status = ReversalObservationOperationStatus.INVALID_INPUT
            code = "QT-REVERSAL-INVALID-INPUT"
        else:
            status = ReversalObservationOperationStatus.FAILED
            code = "QT-REVERSAL-FAILED"
        operation = self._operation(
            operation_id, run_id, stage.stage_id, operation_type, fingerprint,
            definition_id, definition_version, profile_result_id, expected_symbol,
            status, None, requested_at, session_id, request_id, created_by, reason,
            error_code=code, error_summary=str(exc),
        )
        try:
            self._store.save_operation(operation)
        except Exception:
            logger.exception("could not persist failed P28 operation run_id=%s", run_id)
        self._runs.fail_stage(stage, error_code=code, error_summary=str(exc))
        self._runs.fail_run(run_id, error_code=code, error_summary=str(exc), invalid_input=invalid)
        return operation

    @staticmethod
    def _definition_fingerprint(command) -> str:
        return ReversalObservationService._hash({
            "type": "save_definition", "operation_id": str(command.operation_id),
            "session_id": command.session_id, "request_id": command.request_id,
            "multiplier_text": command.shared_multiplier_input_text,
            "predecessor": str(command.predecessor_definition_id) if command.predecessor_definition_id else None,
            "created_by": command.created_by, "reason": command.reason,
        })

    @staticmethod
    def _command_fingerprint(command, profile, market) -> str:
        return ReversalObservationService._hash({
            "type": "preview", "operation_id": str(command.operation_id),
            "definition": [str(command.definition_id), command.definition_version],
            "profile": [str(profile.result_id), profile.calculation_fingerprint],
            "market": [str(market.evidence_id), market.content_fingerprint],
            "direction": command.initial_direction.value,
            "seed": [command.seed_session.isoformat(), command.seed_observation_id,
                     command.seed_split_close.value.ieee_hex],
            "end": command.final_evaluation_session.isoformat(),
            "session_id": command.session_id, "request_id": command.request_id,
            "created_by": command.created_by, "reason": command.reason,
        })

    @staticmethod
    def _hash(payload) -> str:
        return hashlib.sha256(json.dumps(
            payload, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")).hexdigest()


__all__ = ["ReversalObservationService"]
