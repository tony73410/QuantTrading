"""P23-1E-B single-symbol historical spectral research coordination.

This module owns call order only. Market History resolves/fetches evidence,
Factors calculates each point, Run History owns lifecycle, and Persistence owns
durable storage.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Protocol
from uuid import UUID, uuid4, uuid5

from quant_trading.factors import (
    SPECTRAL_COMPONENT_VERSION_INCLUSIVE,
    SpectralHistoricalDefinitionSelection,
    SpectralHistoricalPointStatus,
    SpectralHistoricalStudy,
    SpectralHistoricalStudyPoint,
    SpectralHistoricalStudyStatus,
    SpectralOperationStatus,
    SpectralVolatilityDefinition,
    SpectralVolatilityPreviewCommand,
    SpectralVolatilityService,
    SpectralVolatilityStore,
)
from quant_trading.market_history import (
    ResearchEvidenceMode,
    SpectralEvidenceAcquisitionMode,
    SpectralEvidencePreparationError,
    SpectralHistoricalEvidencePreparationRequest,
    SpectralHistoricalEvidencePreparationService,
    SpectralHistoricalStudyPlan,
)
from quant_trading.run_history import (
    AlgorithmRunService,
    AlgorithmRunType,
    RunBindingType,
    RunMessageSeverity,
    RunStageName,
    SoftwareIdentity,
    StartRunRequest,
)


def _utc(value: datetime, name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must include a timezone")
    return value.astimezone(UTC)


def _text(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must not be empty")
    return value.strip()


@dataclass(frozen=True, slots=True)
class SpectralHistoricalDefinitionReference:
    definition_id: UUID
    definition_version: int

    def __post_init__(self) -> None:
        if self.definition_version < 1:
            raise ValueError("definition version must be positive")


@dataclass(frozen=True, slots=True)
class SpectralHistoricalStudyRequest:
    study_id: UUID
    session_id: str
    request_id: str
    symbol: str
    evaluation_start_session: date
    evaluation_end_session: date
    definitions: tuple[SpectralHistoricalDefinitionReference, ...]
    acquisition_mode: SpectralEvidenceAcquisitionMode
    requested_at_utc: datetime
    created_by: str
    reason: str
    schema_version: int = 1

    def __post_init__(self) -> None:
        symbol = self.symbol.strip().upper()
        if (
            not symbol or len(symbol) > 15 or not symbol[0].isalpha()
            or any(not (character.isalnum() or character in ".-") for character in symbol)
        ):
            raise ValueError("symbol is malformed")
        if self.evaluation_start_session > self.evaluation_end_session:
            raise ValueError("evaluation range is reversed")
        if not 1 <= len(self.definitions) <= 2:
            raise ValueError("historical research requires one or two definitions")
        if len({item.definition_id for item in self.definitions}) != len(self.definitions):
            raise ValueError("historical research definitions cannot be duplicated")
        if self.schema_version != 1:
            raise ValueError("historical research request schema version must be 1")
        object.__setattr__(self, "symbol", symbol)
        object.__setattr__(self, "session_id", _text(self.session_id, "session_id"))
        object.__setattr__(self, "request_id", _text(self.request_id, "request_id"))
        object.__setattr__(self, "created_by", _text(self.created_by, "created_by"))
        object.__setattr__(self, "reason", _text(self.reason, "reason"))
        object.__setattr__(self, "requested_at_utc", _utc(self.requested_at_utc, "requested_at_utc"))
        object.__setattr__(self, "acquisition_mode", SpectralEvidenceAcquisitionMode(self.acquisition_mode))


@dataclass(frozen=True, slots=True)
class SpectralHistoricalStudyDisclosure:
    evaluation_session_count: int
    definition_count: int
    child_operation_count: int
    source_session_count: int
    evaluation_start_session: date
    evaluation_end_session: date


class SpectralHistoricalStudyRunner(Protocol):
    def plan(self, request: SpectralHistoricalStudyRequest) -> SpectralHistoricalStudyDisclosure: ...

    def run(
        self,
        request: SpectralHistoricalStudyRequest,
        *,
        progress_callback: Callable[[int, int], None] | None = None,
        cancellation_requested: Callable[[], bool] | None = None,
    ) -> SpectralHistoricalStudy: ...


class SpectralHistoricalStudyCoordinator:
    """Create one parent Run and an exact chronological child-operation grid."""

    def __init__(
        self,
        study_store,
        definition_store: SpectralVolatilityStore,
        evidence_preparation: SpectralHistoricalEvidencePreparationService,
        factor_service: SpectralVolatilityService,
        run_service: AlgorithmRunService,
        software: SoftwareIdentity,
        *,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
        id_factory: Callable[[], UUID] = uuid4,
    ) -> None:
        self._studies = study_store
        self._definitions = definition_store
        self._evidence = evidence_preparation
        self._factors = factor_service
        self._runs = run_service
        self._software = software
        self._clock = clock
        self._id_factory = id_factory

    def plan(self, request: SpectralHistoricalStudyRequest) -> SpectralHistoricalStudyDisclosure:
        self._resolve_definitions(request)
        plan = self._evidence.plan(self._evidence_request(request))
        return SpectralHistoricalStudyDisclosure(
            len(plan.evaluation_sessions), len(request.definitions),
            len(plan.evaluation_sessions) * len(request.definitions),
            len(plan.source_sessions), plan.evaluation_start_session,
            plan.evaluation_end_session,
        )

    def run(
        self,
        request: SpectralHistoricalStudyRequest,
        *,
        progress_callback: Callable[[int, int], None] | None = None,
        cancellation_requested: Callable[[], bool] | None = None,
    ) -> SpectralHistoricalStudy:
        fingerprint = self._request_fingerprint(request)
        existing = self._studies.get_study(request.study_id)
        if existing is not None:
            if existing.request_fingerprint != fingerprint:
                raise ValueError("study ID is already recorded with different content")
            return existing
        definitions = self._resolve_definitions(request)
        plan = self._evidence.plan(self._evidence_request(request))
        started = self._clock()
        parent = self._runs.start_run(StartRunRequest(
            AlgorithmRunType.SPECTRAL_HISTORY_RESEARCH,
            request.session_id,
            request.request_id,
            plan.evaluation_sessions[-1].close_utc,
            (request.symbol,),
            "spectral_history_research",
            request.created_by,
            self._software,
            notes="P23-1E-B historical descriptive research; RETROSPECTIVE_ADJUSTED; NO EXECUTION",
        ))
        market_stage = self._runs.start_stage(parent.run_id, RunStageName.MARKET_DATA, 1)
        try:
            prepared = self._evidence.prepare(self._evidence_request(request))
            self._studies.save_evidence_set(prepared.evidence_set)
            self._runs.bind(
                parent.run_id, RunBindingType.MARKET_DATA,
                str(prepared.evidence_set.evidence_set_id), "historical-evidence@1",
                source_reference=prepared.evidence_set.content_fingerprint,
            )
            for definition in definitions:
                self._runs.bind(
                    parent.run_id, RunBindingType.FACTOR_DEFINITION,
                    str(definition.definition_id), str(definition.definition_version),
                    source_reference=definition.component_id,
                )
            self._runs.complete_stage(
                market_stage,
                result_type="spectral_historical_evidence_set",
                result_id=str(prepared.evidence_set.evidence_set_id),
                with_warnings=True,
            )
        except SpectralEvidencePreparationError as exc:
            self._runs.fail_stage(market_stage, error_code=exc.code.value, error_summary=str(exc))
            self._runs.fail_run(
                parent.run_id, error_code=exc.code.value, error_summary=str(exc),
                invalid_input=exc.invalid_input,
            )
            study = self._failed_study(
                request, fingerprint, parent.run_id, definitions, plan, started,
                exc.code.value, str(exc),
            )
            self._studies.save_study(study)
            return study

        factor_stage = self._runs.start_stage(parent.run_id, RunStageName.FACTOR, 2)
        selections = tuple(
            SpectralHistoricalDefinitionSelection(
                ordinal, definition.definition_id, definition.definition_version,
                definition.component_id, definition.component_version,
            )
            for ordinal, definition in enumerate(definitions, 1)
        )
        total = len(plan.evaluation_sessions) * len(definitions)
        points: list[SpectralHistoricalStudyPoint] = []
        cancelled = False
        global_error: tuple[str, str] | None = None
        for evaluation_ordinal, session in enumerate(plan.evaluation_sessions, 1):
            for definition_ordinal, definition in enumerate(definitions, 1):
                if cancellation_requested is not None and cancellation_requested():
                    cancelled = True
                if cancelled or global_error is not None:
                    status = (
                        SpectralHistoricalPointStatus.CANCELLED
                        if cancelled else SpectralHistoricalPointStatus.NOT_RUN
                    )
                    points.append(SpectralHistoricalStudyPoint(
                        request.study_id, evaluation_ordinal, session.session_date,
                        session.close_utc, definition_ordinal, definition.definition_id,
                        definition.definition_version, definition.component_version, status,
                        error_code=global_error[0] if global_error else None,
                        error_summary=global_error[1] if global_error else None,
                    ))
                    if progress_callback is not None:
                        progress_callback(len(points), total)
                    continue
                try:
                    include_session = (
                        definition.component_version == SPECTRAL_COMPONENT_VERSION_INCLUSIVE
                    )
                    bundle_id = uuid5(
                        request.study_id,
                        f"bundle:{evaluation_ordinal}:{definition_ordinal}",
                    )
                    bundle = prepared.evidence_set.bundle_for(
                        session.session_date,
                        include_evaluation_session=include_session,
                        bundle_id=bundle_id,
                        created_at_utc=self._clock(),
                    )
                    operation_id = uuid5(
                        request.study_id,
                        f"operation:{evaluation_ordinal}:{definition_ordinal}",
                    )
                    operation = self._factors.preview(
                        SpectralVolatilityPreviewCommand(
                            operation_id, request.session_id,
                            f"{request.request_id}:{evaluation_ordinal}:{definition_ordinal}",
                            request.symbol, session.close_utc, definition.definition_id,
                            definition.definition_version, bundle.bundle_id,
                            request.created_by,
                            f"{request.reason}; historical point {evaluation_ordinal}/{definition_ordinal}",
                        ),
                        definition,
                        bundle,
                        parent_run_id=parent.run_id,
                    )
                    point_status = {
                        SpectralOperationStatus.COMPLETED: SpectralHistoricalPointStatus.COMPLETED,
                        SpectralOperationStatus.COMPLETED_WITH_WARNINGS:
                            SpectralHistoricalPointStatus.COMPLETED_WITH_WARNINGS,
                        SpectralOperationStatus.INVALID_INPUT:
                            SpectralHistoricalPointStatus.INVALID_INPUT,
                        SpectralOperationStatus.FAILED: SpectralHistoricalPointStatus.FAILED,
                    }[operation.status]
                    points.append(SpectralHistoricalStudyPoint(
                        request.study_id, evaluation_ordinal, session.session_date,
                        session.close_utc, definition_ordinal, definition.definition_id,
                        definition.definition_version, definition.component_version, point_status,
                        operation.run_id, operation.operation_id, operation.attempt_id,
                        operation.evidence_bundle.bundle_id, operation.warnings,
                        operation.error_code, operation.error_summary,
                    ))
                except Exception as exc:
                    global_error = (
                        "QT-SPECTRAL-HISTORY-EVIDENCE-CORRUPT",
                        str(exc) or "historical child evidence failed",
                    )
                    points.append(SpectralHistoricalStudyPoint(
                        request.study_id, evaluation_ordinal, session.session_date,
                        session.close_utc, definition_ordinal, definition.definition_id,
                        definition.definition_version, definition.component_version,
                        SpectralHistoricalPointStatus.NOT_RUN,
                        error_code=global_error[0], error_summary=global_error[1],
                    ))
                if progress_callback is not None:
                    progress_callback(len(points), total)

        warnings = ("RETROSPECTIVE_ADJUSTED",)
        if cancelled:
            status = SpectralHistoricalStudyStatus.CANCELLED
            error_code, error_summary = "QT-SPECTRAL-HISTORY-CANCELLED", "用户在子计算之间取消了历史研究。"
        elif global_error is not None:
            status = SpectralHistoricalStudyStatus.FAILED
            error_code, error_summary = global_error
        elif any(item.status is not SpectralHistoricalPointStatus.COMPLETED for item in points):
            status = SpectralHistoricalStudyStatus.COMPLETED_WITH_WARNINGS
            error_code = error_summary = None
        else:
            status = SpectralHistoricalStudyStatus.COMPLETED
            error_code = error_summary = None
        study = SpectralHistoricalStudy(
            request.study_id, parent.run_id, fingerprint, request.session_id,
            request.request_id, request.symbol, request.evaluation_start_session,
            request.evaluation_end_session, request.acquisition_mode.value,
            ResearchEvidenceMode.RETROSPECTIVE_ADJUSTED.value,
            prepared.evidence_set.evidence_set_id, selections, tuple(points), status,
            request.requested_at_utc, started, self._clock(), request.created_by,
            request.reason, self._software.package_version, self._software.source_revision,
            self._software.worktree_state.value, warnings, error_code, error_summary,
        )
        self._studies.save_study(study)
        if status is SpectralHistoricalStudyStatus.FAILED:
            self._runs.fail_stage(factor_stage, error_code=error_code or "QT-SPECTRAL-HISTORY-FAILED", error_summary=error_summary or "failed")
            self._runs.fail_run(parent.run_id, error_code=error_code or "QT-SPECTRAL-HISTORY-FAILED", error_summary=error_summary or "failed")
        else:
            self._runs.complete_stage(
                factor_stage, result_type="spectral_historical_study",
                result_id=str(study.study_id), with_warnings=study.has_warning_or_failure,
            )
            if cancelled:
                self._runs.cancel_run(parent.run_id, reason=error_summary or "cancelled")
            else:
                self._runs.record_message(
                    parent.run_id, RunMessageSeverity.WARNING,
                    "QT-SPECTRAL-HISTORY-RETROSPECTIVE",
                    "RETROSPECTIVE_ADJUSTED：该历史研究不是时点安全回测。",
                    stage_id=factor_stage.stage_id,
                )
                self._runs.complete_run(parent.run_id, with_warnings=study.has_warning_or_failure)
        return study

    def _resolve_definitions(
        self, request: SpectralHistoricalStudyRequest
    ) -> tuple[SpectralVolatilityDefinition, ...]:
        output: list[SpectralVolatilityDefinition] = []
        for reference in request.definitions:
            definition = self._definitions.get_definition(reference.definition_id)
            if definition is None or definition.definition_version != reference.definition_version:
                raise ValueError("selected spectral definition/version is unavailable")
            output.append(definition)
        return tuple(output)

    @staticmethod
    def _evidence_request(request: SpectralHistoricalStudyRequest):
        return SpectralHistoricalEvidencePreparationRequest(
            request.symbol, request.evaluation_start_session,
            request.evaluation_end_session, request.acquisition_mode,
            request.requested_at_utc,
        )

    def _failed_study(
        self, request, fingerprint, parent_run_id, definitions, plan, started, code, summary
    ) -> SpectralHistoricalStudy:
        selections = tuple(
            SpectralHistoricalDefinitionSelection(
                ordinal, definition.definition_id, definition.definition_version,
                definition.component_id, definition.component_version,
            )
            for ordinal, definition in enumerate(definitions, 1)
        )
        points = tuple(
            SpectralHistoricalStudyPoint(
                request.study_id, evaluation_ordinal, session.session_date,
                session.close_utc, definition_ordinal, definition.definition_id,
                definition.definition_version, definition.component_version,
                SpectralHistoricalPointStatus.NOT_RUN,
                error_code=code, error_summary=summary,
            )
            for evaluation_ordinal, session in enumerate(plan.evaluation_sessions, 1)
            for definition_ordinal, definition in enumerate(definitions, 1)
        )
        return SpectralHistoricalStudy(
            request.study_id, parent_run_id, fingerprint, request.session_id,
            request.request_id, request.symbol, request.evaluation_start_session,
            request.evaluation_end_session, request.acquisition_mode.value,
            ResearchEvidenceMode.RETROSPECTIVE_ADJUSTED.value, None, selections,
            points, SpectralHistoricalStudyStatus.FAILED, request.requested_at_utc,
            started, self._clock(), request.created_by, request.reason,
            self._software.package_version, self._software.source_revision,
            self._software.worktree_state.value, ("RETROSPECTIVE_ADJUSTED",), code, summary,
        )

    @staticmethod
    def _request_fingerprint(request: SpectralHistoricalStudyRequest) -> str:
        payload = {
            "study_id": str(request.study_id), "session_id": request.session_id,
            "request_id": request.request_id, "symbol": request.symbol,
            "evaluation_start_session": request.evaluation_start_session.isoformat(),
            "evaluation_end_session": request.evaluation_end_session.isoformat(),
            "definitions": [[str(item.definition_id), item.definition_version] for item in request.definitions],
            "acquisition_mode": request.acquisition_mode.value,
            "requested_at_utc": request.requested_at_utc.isoformat(),
            "created_by": request.created_by, "reason": request.reason,
            "schema_version": request.schema_version,
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()


__all__ = [
    "SpectralHistoricalDefinitionReference",
    "SpectralHistoricalStudyCoordinator",
    "SpectralHistoricalStudyDisclosure",
    "SpectralHistoricalStudyRequest",
    "SpectralHistoricalStudyRunner",
]
