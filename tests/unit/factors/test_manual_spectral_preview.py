from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from quant_trading.factors import (
    SpectralOperationStatus,
    SpectralVolatilityService,
)
from quant_trading.market_history import (
    PreparedSpectralEvidence,
    ResearchEvidenceMode,
    SpectralEvidenceAcquisitionMode,
    SpectralEvidencePreparationError,
    SpectralEvidencePreparationErrorCode,
)
from quant_trading.orchestration import (
    ManualSpectralPreviewCoordinator,
    ManualSpectralPreviewRequest,
    ManualSpectralPreviewStatus,
)
from quant_trading.persistence import (
    SQLiteRunHistoryRepository,
    SQLiteSpectralVolatilityStore,
)
from quant_trading.run_history import (
    AlgorithmRunService,
    AlgorithmRunStatus,
    RunStageStatus,
    SoftwareIdentity,
    WorktreeState,
)

from spectral_fixtures import spectral_bundle, spectral_definition


class _Preparation:
    def __init__(self, bundle=None, error=None) -> None:
        self.bundle = bundle
        self.error = error
        self.requests = []

    def prepare(self, request):
        self.requests.append(request)
        if self.error is not None:
            raise self.error
        return PreparedSpectralEvidence(
            self.bundle,
            request.acquisition_mode,
            self.bundle.as_of_utc.date(),
            request.requested_at_utc,
            ("RETROSPECTIVE_ADJUSTED",),
        )


def _request(definition, *, operation_id=None):
    return ManualSpectralPreviewRequest(
        operation_id or uuid4(),
        "session",
        "request",
        "aapl",
        definition.definition_id,
        definition.definition_version,
        SpectralEvidenceAcquisitionMode.FETCH_AND_FREEZE_READ_ONLY,
        datetime(2026, 8, 2, 12, tzinfo=UTC),
        "pytest",
        "manual preview",
    )


def _coordinator(path: Path, preparation, definition):
    store = SQLiteSpectralVolatilityStore(path)
    store.initialize()
    store.save_definition(definition)
    repository = SQLiteRunHistoryRepository(path)
    repository.initialize()
    runs = AlgorithmRunService(repository)
    software = SoftwareIdentity("0.1.0", "test", WorktreeState.CLEAN)
    factor_service = SpectralVolatilityService(store, runs, software)
    coordinator = ManualSpectralPreviewCoordinator(
        store, preparation, factor_service, runs, software
    )
    return coordinator, store, repository


def test_manual_runner_persists_one_inclusive_v11_operation_and_is_idempotent(
    tmp_path: Path,
) -> None:
    path = tmp_path / "central.sqlite3"
    definition = spectral_definition(inclusive_evaluation_session=True)
    bundle = spectral_bundle(
        evidence_mode=ResearchEvidenceMode.RETROSPECTIVE_ADJUSTED,
        include_evaluation_session=True,
        observed_after_as_of=True,
    )
    preparation = _Preparation(bundle)
    coordinator, store, _ = _coordinator(path, preparation, definition)
    request = _request(definition)
    first = coordinator.run(request)
    second = coordinator.run(request)
    assert first.status is ManualSpectralPreviewStatus.COMPLETED_WITH_WARNINGS
    assert first.operation.status is SpectralOperationStatus.COMPLETED_WITH_WARNINGS
    assert "RETROSPECTIVE_ADJUSTED" in first.operation.warnings
    assert first.operation.definition.component_version == "1.1.0"
    assert first.operation.evidence_bundle.observations[-1].session_date == bundle.as_of_utc.date()
    assert second.operation == first.operation
    assert store.get_operation(first.operation.attempt_id) == first.operation
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM algorithm_runs").fetchone()[0] == 1


def test_preparation_failure_creates_searchable_market_data_failure_run(
    tmp_path: Path,
) -> None:
    path = tmp_path / "central.sqlite3"
    definition = spectral_definition(inclusive_evaluation_session=True)
    failure = SpectralEvidencePreparationError(
        SpectralEvidencePreparationErrorCode.LOCAL_EVIDENCE_UNAVAILABLE,
        "no exact local bundle",
    )
    coordinator, store, repository = _coordinator(
        path, _Preparation(error=failure), definition
    )
    outcome = coordinator.run(_request(definition))
    assert outcome.status is ManualSpectralPreviewStatus.FAILED
    assert outcome.operation is None
    assert outcome.error_code == failure.code.value
    detail = repository.get_run_detail(outcome.run_id)
    assert detail.summary.run.status is AlgorithmRunStatus.FAILED
    assert len(detail.stages) == 1
    assert detail.stages[0].status is RunStageStatus.FAILED
    assert detail.stages[0].error_code == failure.code.value
    assert store.list_operations() == ()


def test_runner_rejects_legacy_definition_without_preparing_evidence(
    tmp_path: Path,
) -> None:
    path = tmp_path / "central.sqlite3"
    legacy = spectral_definition()
    preparation = _Preparation()
    coordinator, _, repository = _coordinator(path, preparation, legacy)
    outcome = coordinator.run(_request(legacy))
    assert outcome.status is ManualSpectralPreviewStatus.INVALID_INPUT
    assert outcome.error_code == "QT-SPECTRAL-PREP-DEFINITION-MISMATCH"
    assert preparation.requests == []
    assert (
        repository.get_run_detail(outcome.run_id).summary.run.status
        is AlgorithmRunStatus.INVALID_INPUT
    )
