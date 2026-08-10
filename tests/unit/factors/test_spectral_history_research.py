from __future__ import annotations

import math
import sqlite3
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from quant_trading.factors import (
    SpectralHistoricalPointStatus,
    SpectralHistoricalStudyQuery,
    SpectralHistoricalStudyStatus,
    SpectralVolatilityService,
)
from quant_trading.market_history import (
    DataFeed,
    PreparedSpectralHistoricalEvidence,
    ResearchBarObservation,
    ResearchCalendarSymbolMapping,
    ResearchCorporateActionSnapshot,
    ResearchEvidenceMode,
    SpectralEvidenceAcquisitionMode,
    SpectralHistoricalEvidenceSet,
    SpectralHistoricalStudyPlan,
    Timeframe,
    US_EQUITIES_REGULAR_V1,
    US_EQUITY_OR_ETF_WITH_EXPLICIT_MAPPING,
    XNYSResearchCalendarAdapter,
)
from quant_trading.orchestration import (
    SpectralHistoricalDefinitionReference,
    SpectralHistoricalStudyCoordinator,
    SpectralHistoricalStudyRequest,
)
from quant_trading.persistence import (
    SQLiteRunHistoryRepository,
    SQLiteSpectralHistoricalStudyStore,
    SQLiteSpectralVolatilityStore,
)
from quant_trading.persistence import sqlite_database
from quant_trading.persistence.sqlite_database import CentralSQLiteDatabase
from quant_trading.run_history import (
    AlgorithmRunService,
    AlgorithmRunStatus,
    AlgorithmRunType,
    SoftwareIdentity,
    WorktreeState,
)

from spectral_fixtures import spectral_definition


def _historical_evidence(session_count: int = 2):
    locator = XNYSResearchCalendarAdapter().build_snapshot(
        date(2024, 1, 1), date(2026, 7, 31),
        observed_at_utc=datetime(2026, 8, 1, tzinfo=UTC),
    )
    selected = locator.sessions[-(250 + session_count):]
    calendar = XNYSResearchCalendarAdapter().build_snapshot(
        selected[0].session_date, selected[-1].session_date,
        observed_at_utc=datetime(2026, 8, 1, tzinfo=UTC),
    )
    evaluation = calendar.sessions[-session_count:]
    observations = []
    for ordinal, session in enumerate(calendar.sessions, 1):
        price = 100.0 * math.exp(0.02 * math.sin(2.0 * math.pi * ordinal / 20.0))
        value = repr(price)
        observed = datetime(2026, 8, 1, tzinfo=UTC)
        observations.append(ResearchBarObservation(
            ordinal, session.session_date, session.close_utc, observed,
            max(session.close_utc, observed), value, value, value, value,
            value, value, value, value, 1000, DataFeed.IEX, "fixture",
            f"raw-{ordinal}-{price.hex()}", f"split-{ordinal}-{price.hex()}",
        ))
    mapping = ResearchCalendarSymbolMapping(
        uuid4(), 26, "AAPL", US_EQUITY_OR_ETF_WITH_EXPLICIT_MAPPING,
        US_EQUITIES_REGULAR_V1, calendar.covered_start, None,
        datetime(2026, 8, 1, tzinfo=UTC), "pytest", "P26 mapping",
    )
    actions = ResearchCorporateActionSnapshot(
        uuid4(), "fixture", "fixture-query",
        datetime(2026, 8, 1, tzinfo=UTC), datetime(2026, 8, 1, tzinfo=UTC),
        calendar.covered_start, calendar.covered_end, "fixture-actions",
        ResearchEvidenceMode.RETROSPECTIVE_ADJUSTED,
    )
    evidence = SpectralHistoricalEvidenceSet(
        uuid4(), "historical-fingerprint", "AAPL", DataFeed.IEX, Timeframe.DAY,
        ResearchEvidenceMode.RETROSPECTIVE_ADJUSTED,
        SpectralEvidenceAcquisitionMode.FETCH_AND_FREEZE_READ_ONLY,
        calendar, mapping, actions, evaluation, tuple(observations),
        datetime(2026, 8, 1, tzinfo=UTC), datetime(2026, 8, 1, tzinfo=UTC),
    )
    return SpectralHistoricalStudyPlan(calendar, evaluation, calendar.sessions), evidence


class _Preparation:
    def __init__(self, plan, evidence):
        self.resolved_plan = plan
        self.evidence = evidence
        self.prepare_count = 0

    def plan(self, request):
        return self.resolved_plan

    def prepare(self, request):
        self.prepare_count += 1
        return PreparedSpectralHistoricalEvidence(self.resolved_plan, self.evidence)


def _request(definitions, plan, *, study_id=None):
    return SpectralHistoricalStudyRequest(
        study_id or uuid4(), "session", "request", "aapl",
        plan.evaluation_sessions[0].session_date,
        plan.evaluation_sessions[-1].session_date,
        tuple(
            SpectralHistoricalDefinitionReference(item.definition_id, item.definition_version)
            for item in definitions
        ),
        SpectralEvidenceAcquisitionMode.FETCH_AND_FREEZE_READ_ONLY,
        datetime(2026, 8, 1, tzinfo=UTC), "pytest", "P26 history",
    )


def test_evidence_child_cutoffs_are_exact_and_no_look_ahead() -> None:
    plan, evidence = _historical_evidence()
    first = plan.evaluation_sessions[0]
    legacy = evidence.bundle_for(
        first.session_date, include_evaluation_session=False,
        bundle_id=uuid4(), created_at_utc=datetime.now(UTC),
    )
    inclusive = evidence.bundle_for(
        first.session_date, include_evaluation_session=True,
        bundle_id=uuid4(), created_at_utc=datetime.now(UTC),
    )
    assert len(legacy.observations) == len(inclusive.observations) == 250
    assert legacy.observations[-1].session_date < first.session_date
    assert inclusive.observations[-1].session_date == first.session_date
    assert all(item.session_date <= first.session_date for item in inclusive.observations)


def test_historical_study_persists_complete_parent_child_grid_and_reloads(tmp_path: Path) -> None:
    path = tmp_path / "central.sqlite3"
    plan, evidence = _historical_evidence()
    legacy = spectral_definition()
    inclusive = spectral_definition(inclusive_evaluation_session=True)
    operations = SQLiteSpectralVolatilityStore(path)
    operations.initialize()
    operations.save_definition(legacy)
    operations.save_definition(inclusive)
    studies = SQLiteSpectralHistoricalStudyStore(path)
    studies.initialize()
    runs = SQLiteRunHistoryRepository(path)
    runs.initialize()
    run_service = AlgorithmRunService(runs)
    software = SoftwareIdentity("0.1.0", "test", WorktreeState.CLEAN)
    preparation = _Preparation(plan, evidence)
    coordinator = SpectralHistoricalStudyCoordinator(
        studies, operations, preparation,
        SpectralVolatilityService(operations, run_service, software),
        run_service, software,
    )
    request = _request((legacy, inclusive), plan)
    progress = []
    study = coordinator.run(request, progress_callback=lambda done, total: progress.append((done, total)))
    retry = coordinator.run(request)
    assert preparation.prepare_count == 1
    assert study.status is SpectralHistoricalStudyStatus.COMPLETED_WITH_WARNINGS
    assert retry == study
    assert len(study.points) == 4
    assert progress[-1] == (4, 4)
    assert all(item.status is SpectralHistoricalPointStatus.COMPLETED_WITH_WARNINGS for item in study.points)
    assert studies.get_study(study.study_id) == study
    assert studies.list_studies(SpectralHistoricalStudyQuery(symbol="aapl")) == (study,)
    parent = runs.get_run_detail(study.parent_run_id)
    assert parent.summary.run.run_type is AlgorithmRunType.SPECTRAL_HISTORY_RESEARCH
    assert parent.summary.run.status is AlgorithmRunStatus.COMPLETED_WITH_WARNINGS
    study_artifact = next(
        item for item in parent.artifacts if item.artifact_type == "spectral_historical_study"
    )
    assert study_artifact.artifact_id == str(study.study_id)
    assert len(study_artifact.children) == 4
    children = [item for item in parent.relationships if item.relationship_type.value == "child"]
    assert len(children) == 4
    for point in study.points:
        operation = operations.get_operation(point.attempt_id)
        assert operation.run_id == point.child_run_id
        assert runs.get_run_detail(point.child_run_id).summary.run.parent_run_id == study.parent_run_id
        latest = operation.evidence_bundle.observations[-1].session_date
        if point.component_version == "1.0.0":
            assert latest < point.evaluation_session
        else:
            assert latest == point.evaluation_session
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 16
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []


def test_cancellation_marks_every_unstarted_point_without_creating_children(tmp_path: Path) -> None:
    path = tmp_path / "central.sqlite3"
    plan, evidence = _historical_evidence(3)
    definition = spectral_definition(inclusive_evaluation_session=True)
    operations = SQLiteSpectralVolatilityStore(path)
    operations.initialize()
    operations.save_definition(definition)
    studies = SQLiteSpectralHistoricalStudyStore(path)
    runs = SQLiteRunHistoryRepository(path)
    runs.initialize()
    service = AlgorithmRunService(runs)
    software = SoftwareIdentity("0.1.0", "test", WorktreeState.CLEAN)
    coordinator = SpectralHistoricalStudyCoordinator(
        studies, operations, _Preparation(plan, evidence),
        SpectralVolatilityService(operations, service, software), service, software,
    )
    progress: list[tuple[int, int]] = []
    study = coordinator.run(
        _request((definition,), plan),
        cancellation_requested=lambda: True,
        progress_callback=lambda done, total: progress.append((done, total)),
    )
    assert study.status is SpectralHistoricalStudyStatus.CANCELLED
    assert all(item.status is SpectralHistoricalPointStatus.CANCELLED for item in study.points)
    assert progress[-1] == (3, 3)
    assert runs.get_run_detail(study.parent_run_id).summary.run.status is AlgorithmRunStatus.CANCELLED
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM spectral_volatility_operations").fetchone()[0] == 0


def test_v14_to_current_migration_is_additive_backed_up_and_does_not_backfill(tmp_path: Path) -> None:
    path = tmp_path / "central.sqlite3"
    with sqlite3.connect(path) as connection:
        for version in range(1, 15):
            connection.executescript(sqlite_database._MIGRATIONS[version][1])
            connection.execute(
                "INSERT INTO schema_migrations VALUES (?, ?, ?)",
                (version, datetime.now(UTC).isoformat(), f"fixture {version}"),
            )
        connection.execute(
            """INSERT INTO market_bars VALUES
            ('AAPL', '2026-01-02T00:00:00+00:00', '1Day', 'raw', 'iex',
             '100', '101', '99', '100', 100, NULL, NULL, 'fixture',
             '2026-01-03T00:00:00+00:00')"""
        )
        connection.commit()
    CentralSQLiteDatabase(path).initialize()
    backups = tuple((tmp_path / "backups").glob("*.sqlite3"))
    assert len(backups) == 1
    assert ".schema-v14-to-v16." in backups[0].name
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 16
        assert connection.execute("SELECT COUNT(*) FROM market_bars").fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM spectral_historical_studies").fetchone()[0] == 0
        assert connection.execute("SELECT COUNT(*) FROM daily_volatility_profile_results").fetchone()[0] == 0
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def test_same_study_id_with_changed_request_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "central.sqlite3"
    plan, evidence = _historical_evidence()
    definition = spectral_definition(inclusive_evaluation_session=True)
    operations = SQLiteSpectralVolatilityStore(path)
    operations.initialize()
    operations.save_definition(definition)
    studies = SQLiteSpectralHistoricalStudyStore(path)
    runs = SQLiteRunHistoryRepository(path)
    runs.initialize()
    service = AlgorithmRunService(runs)
    software = SoftwareIdentity("0.1.0", "test", WorktreeState.CLEAN)
    coordinator = SpectralHistoricalStudyCoordinator(
        studies, operations, _Preparation(plan, evidence),
        SpectralVolatilityService(operations, service, software), service, software,
    )
    study_id = uuid4()
    original = _request((definition,), plan, study_id=study_id)
    coordinator.run(original)
    changed = SpectralHistoricalStudyRequest(
        study_id, original.session_id, original.request_id, original.symbol,
        original.evaluation_start_session, original.evaluation_end_session,
        original.definitions, original.acquisition_mode, original.requested_at_utc,
        original.created_by, "changed reason",
    )
    import pytest
    with pytest.raises(ValueError, match="different content"):
        coordinator.run(changed)
