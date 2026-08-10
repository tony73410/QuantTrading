"""Run-aware application service for disabled P23-1F research."""

from __future__ import annotations

import hashlib
import json
import logging
from collections.abc import Callable
from datetime import UTC, datetime
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

from .daily_volatility_profile_engine import (
    DailyVolatilityProfileEngine,
    DailyVolatilityProfileValidationError,
)
from .daily_volatility_profile_interfaces import DailyVolatilityProfileStore
from .daily_volatility_profile_models import (
    DailyVolatilityProfileCommand,
    DailyVolatilityProfileDefinition,
    DailyVolatilityProfileOperation,
    DailyVolatilityProfileSourcePoint,
    DailyVolatilityProfileStatus,
)
from .spectral_history_interfaces import SpectralHistoricalStudyQueryService
from .spectral_models import SPECTRAL_COMPONENT_VERSION
from .spectral_interfaces import SpectralVolatilityQueryService


logger = logging.getLogger(__name__)


class DailyVolatilityProfileService:
    """Resolve exact P26 sources and append one auditable profile attempt."""

    def __init__(
        self,
        store: DailyVolatilityProfileStore,
        study_queries: SpectralHistoricalStudyQueryService,
        spectral_queries: SpectralVolatilityQueryService,
        run_service: AlgorithmRunService,
        software: SoftwareIdentity,
        definition: DailyVolatilityProfileDefinition,
        *,
        engine: DailyVolatilityProfileEngine | None = None,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
        id_factory: Callable[[], UUID] = uuid4,
    ) -> None:
        self._store = store
        self._studies = study_queries
        self._spectral = spectral_queries
        self._runs = run_service
        self._software = software
        self._definition = definition
        self._engine = engine or DailyVolatilityProfileEngine()
        self._clock = clock
        self._id_factory = id_factory

    def register_definition(self) -> None:
        self._store.save_definition(self._definition)

    def preview(self, command: DailyVolatilityProfileCommand) -> DailyVolatilityProfileOperation:
        command_fingerprint = self._command_fingerprint(command)
        existing = self._store.get_first_operation(command.operation_id)
        if existing is not None and existing.command_fingerprint == command_fingerprint:
            return existing

        requested_at = self._clock()
        study = self._studies.get_study(command.source_study_id)
        parent_run_id = study.parent_run_id if study is not None else None
        market_data_as_of = (
            max(point.official_close_utc for point in study.points)
            if study is not None and study.points
            else None
        )
        run = self._runs.start_run(StartRunRequest(
            AlgorithmRunType.VOLATILITY_PROFILE_RESEARCH,
            command.session_id,
            command.request_id,
            market_data_as_of,
            (command.symbol,),
            "algorithm_control_daily_volatility_profile",
            command.created_by,
            self._software,
            parent_run_id=parent_run_id,
            notes="P23-1F daily normal-movement profile research; NO EXECUTION",
        ))
        stage = self._runs.start_stage(run.run_id, RunStageName.FACTOR, 1)
        try:
            if existing is not None:
                raise DailyVolatilityProfileValidationError(
                    DailyVolatilityProfileStatus.SOURCE_EVIDENCE_MISMATCH,
                    "operation ID is already recorded with different content",
                )
            if (
                command.definition_id != self._definition.definition_id
                or command.definition_version != self._definition.definition_version
            ):
                raise DailyVolatilityProfileValidationError(
                    DailyVolatilityProfileStatus.SOURCE_VERSION_INCOMPATIBLE,
                    "requested profile definition does not match the locked P27 definition",
                )
            if study is None:
                raise DailyVolatilityProfileValidationError(
                    DailyVolatilityProfileStatus.SOURCE_STUDY_INCOMPLETE,
                    "requested P26 source study does not exist",
                )
            if command.symbol != study.symbol:
                raise DailyVolatilityProfileValidationError(
                    DailyVolatilityProfileStatus.SOURCE_EVIDENCE_MISMATCH,
                    "expected symbol does not match the P26 source study",
                )
            selection = next(
                (
                    item for item in study.definitions
                    if item.definition_id == command.source_definition_id
                    and item.definition_version == command.source_definition_version
                    and item.component_version == SPECTRAL_COMPONENT_VERSION
                ),
                None,
            )
            if selection is None:
                raise DailyVolatilityProfileValidationError(
                    DailyVolatilityProfileStatus.SOURCE_VERSION_INCOMPATIBLE,
                    "requested source is not an exact R1 v1.0.0 definition in this study",
                )
            sources: list[DailyVolatilityProfileSourcePoint] = []
            for point in study.points:
                if point.definition_id != command.source_definition_id:
                    continue
                operation = self._spectral.get_operation(point.attempt_id) if point.attempt_id else None
                if operation is None:
                    raise DailyVolatilityProfileValidationError(
                        DailyVolatilityProfileStatus.SOURCE_POINT_INVALID,
                        f"source operation cannot be reloaded for {point.evaluation_session}",
                    )
                sources.append(DailyVolatilityProfileSourcePoint(point, operation))

            self._bind(run.run_id, command, study, tuple(sources))
            calculated = self._engine.calculate(
                self._definition,
                study,
                tuple(sources),
                source_definition_id=command.source_definition_id,
                source_definition_version=command.source_definition_version,
                created_at_utc=self._clock(),
                software_version=self._software.package_version,
                source_revision=self._software.source_revision,
                worktree_state=self._software.worktree_state.value,
            )
            result = self._store.get_result_by_fingerprint(calculated.calculation_fingerprint)
            if result is None:
                result = calculated
            operation = DailyVolatilityProfileOperation(
                self._id_factory(),
                command.operation_id,
                run.run_id,
                stage.stage_id,
                command_fingerprint,
                self._definition,
                command.source_study_id,
                command.source_definition_id,
                command.source_definition_version,
                command.symbol,
                result.status,
                result,
                requested_at,
                self._clock(),
                command.session_id,
                command.request_id,
                command.created_by,
                command.reason,
                self._software.package_version,
                self._software.source_revision,
                self._software.worktree_state.value,
                result.warnings,
            )
            self._store.save_operation(operation)
            self._runs.complete_stage(
                stage,
                result_type="daily_volatility_profile_result",
                result_id=str(result.result_id),
                with_warnings=bool(result.warnings),
            )
            for warning in result.warnings:
                self._runs.record_message(
                    run.run_id,
                    RunMessageSeverity.WARNING,
                    "QT-VOLATILITY-PROFILE-WARNING",
                    warning,
                    stage_id=stage.stage_id,
                )
            self._runs.complete_run(run.run_id, with_warnings=bool(result.warnings))
            return operation
        except DailyVolatilityProfileValidationError as exc:
            return self._failure(command, command_fingerprint, requested_at, run.run_id, stage, exc, True)
        except (ValueError, TypeError) as exc:
            wrapped = DailyVolatilityProfileValidationError(
                DailyVolatilityProfileStatus.SOURCE_EVIDENCE_MISMATCH, str(exc)
            )
            return self._failure(command, command_fingerprint, requested_at, run.run_id, stage, wrapped, True)
        except Exception as exc:
            logger.exception("daily-volatility profile failed run_id=%s", run.run_id)
            return self._failure(command, command_fingerprint, requested_at, run.run_id, stage, exc, False)

    def _bind(self, run_id, command, study, sources) -> None:
        self._runs.bind(
            run_id,
            RunBindingType.FACTOR_DEFINITION,
            str(self._definition.definition_id),
            str(self._definition.definition_version),
            source_reference=self._definition.component_id,
        )
        self._runs.bind(
            run_id,
            RunBindingType.FACTOR_DEFINITION,
            str(command.source_definition_id),
            str(command.source_definition_version),
            source_reference=SPECTRAL_COMPONENT_VERSION,
        )
        self._runs.bind(
            run_id,
            RunBindingType.CONFIGURATION,
            str(study.study_id),
            "P26-study@1",
            source_reference=study.request_fingerprint,
        )
        for source in sources:
            self._runs.bind(
                run_id,
                RunBindingType.CONFIGURATION,
                str(source.study_point.child_run_id),
                "P26-child-run@1",
                source_reference=source.operation.command_fingerprint,
            )

    def _failure(self, command, fingerprint, requested_at, run_id, stage, exc, invalid):
        status = (
            exc.status
            if isinstance(exc, DailyVolatilityProfileValidationError)
            else DailyVolatilityProfileStatus.FAILED
        )
        message = str(exc) or "daily-volatility profile failed"
        code = (
            f"QT-VOLATILITY-PROFILE-{status.value.upper()}"
            if invalid
            else "QT-VOLATILITY-PROFILE-FAILED"
        )
        operation = DailyVolatilityProfileOperation(
            self._id_factory(),
            command.operation_id,
            run_id,
            stage.stage_id,
            fingerprint,
            self._definition,
            command.source_study_id,
            command.source_definition_id,
            command.source_definition_version,
            command.symbol,
            status if invalid else DailyVolatilityProfileStatus.FAILED,
            None,
            requested_at,
            self._clock(),
            command.session_id,
            command.request_id,
            command.created_by,
            command.reason,
            self._software.package_version,
            self._software.source_revision,
            self._software.worktree_state.value,
            (),
            code,
            message,
        )
        try:
            self._store.save_operation(operation)
        except Exception:
            logger.exception("could not persist failed profile operation run_id=%s", run_id)
        self._runs.fail_stage(stage, error_code=code, error_summary=message)
        self._runs.fail_run(run_id, error_code=code, error_summary=message, invalid_input=invalid)
        return operation

    @staticmethod
    def _command_fingerprint(command: DailyVolatilityProfileCommand) -> str:
        payload = {
            "operation_id": str(command.operation_id),
            "session_id": command.session_id,
            "request_id": command.request_id,
            "symbol": command.symbol,
            "definition_id": str(command.definition_id),
            "definition_version": command.definition_version,
            "source_study_id": str(command.source_study_id),
            "source_definition_id": str(command.source_definition_id),
            "source_definition_version": command.source_definition_version,
            "created_by": command.created_by,
            "reason": command.reason,
            "schema_version": command.schema_version,
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()


__all__ = ["DailyVolatilityProfileService"]
