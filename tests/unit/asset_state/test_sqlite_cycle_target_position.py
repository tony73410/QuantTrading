from __future__ import annotations

import sqlite3
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from quant_trading.asset_state import (
    CreateReversalObservationDefinitionCommand,
    ReversalDirection,
    ReversalFloatEvidence,
    ReversalObservationCommand,
    ReversalObservationMarketEvidence,
    ReversalObservationPriceObservation,
    ReversalObservationProfileEvidence,
    ReversalObservationService,
    ReversalPriceEvidence,
)
from quant_trading.orchestration import CycleTargetPositionResearchCoordinator
from quant_trading.persistence import (
    CentralSQLiteDatabase,
    SQLiteCycleTargetPositionStore,
    SQLiteReversalObservationStore,
    SQLiteRunHistoryRepository,
)
from quant_trading.persistence import sqlite_database
from quant_trading.run_history import AlgorithmRunService, AlgorithmRunType, SoftwareIdentity, WorktreeState
from quant_trading.target_position import (
    CreateAssetCycleTargetConfigurationCommand,
    CreateCycleTargetFormulaCommand,
    CycleTargetOperationStatus,
    CycleTargetPositionService,
    CycleTargetPreviewCommand,
    CycleTargetQuery,
    CycleTargetPositionReplayService,
)

from test_daily_volatility_profile import _command as profile_command, _environment


NOW = datetime(2026, 8, 10, 20, 0, tzinfo=UTC)


def _price(value: float):
    return ReversalPriceEvidence(str(value), ReversalFloatEvidence(value))


def _observation(session: date, price: float, available: datetime):
    closed = available - timedelta(minutes=1)
    return ReversalObservationPriceObservation(
        f"obs-{session}", session, closed, available, available,
        f"raw-{session}", f"split-{session}", _price(price), _price(price),
    )


def _p28(path: Path):
    study, source_definition, _, profiles, profile_service, runs, profile_definition = _environment(path)
    profile_operation = profile_service.preview(profile_command(study, source_definition, profile_definition))
    profile_result = profile_operation.result
    assert profile_result is not None
    store = SQLiteReversalObservationStore(path)
    software = SoftwareIdentity("0.1.0", "test-revision", WorktreeState.CLEAN)
    service = ReversalObservationService(store, AlgorithmRunService(runs), software, clock=lambda: NOW)
    definition_operation = service.save_definition(CreateReversalObservationDefinitionCommand(
        uuid4(), "session", "p28-definition", "1.0", None, "pytest", "P28 fixture",
    ))
    definition = store.get_definition(definition_operation.definition_id)
    assert definition is not None
    seed_session = profile_result.evaluation_end_session
    day1, day2, day3 = (seed_session + timedelta(days=value) for value in (1, 2, 3))
    seed = _observation(seed_session, 100.0, profile_result.created_at_utc - timedelta(minutes=1))
    observations = (
        _observation(day1, 97.0, profile_result.created_at_utc + timedelta(days=1)),
        _observation(day2, 96.0, profile_result.created_at_utc + timedelta(days=2)),
        _observation(day3, 95.0, profile_result.created_at_utc + timedelta(days=3)),
    )
    market = ReversalObservationMarketEvidence(
        uuid4(), "market-fingerprint", profile_result.symbol, "alpaca", "iex", "1Day",
        "raw+split", "fixture", "US_EQUITIES_REGULAR_V1", "calendar-v1",
        "calendar-fingerprint", "corporate-evidence", seed, observations,
        (day1, day2, day3), (), NOW,
    )
    profile = ReversalObservationProfileEvidence(
        profile_result.result_id, profile_operation.run_id, profile_result.source_study_id,
        profile_result.source_parent_run_id, profile_result.source_definition_id,
        profile_result.source_definition_version, profile_result.symbol,
        profile_result.evaluation_end_session, profile_result.created_at_utc,
        ReversalFloatEvidence(profile_result.profile_log_scale.value, profile_result.profile_log_scale.ieee_hex),
        profile_result.calculation_fingerprint,
        "factor.daily_volatility_profile.p23_1f.v1", "1.0.0", True,
    )
    operation = service.preview(ReversalObservationCommand(
        uuid4(), "session", "p28-preview", profile_result.symbol,
        definition.definition_id, definition.definition_version, profile_result.result_id,
        ReversalDirection.DOWN, seed_session, seed.observation_id, seed.split_close,
        day3, market.calendar_definition_id, market.calendar_version,
        market.calendar_fingerprint, "pytest", "P28 fixture",
    ), profile, market)
    assert operation.result is not None
    return store, runs, operation, software


def test_p29_service_persists_versions_exact_source_trace_and_run_artifact(tmp_path: Path):
    path = tmp_path / "central.sqlite3"
    reversal, runs, p28, software = _p28(path)
    store = SQLiteCycleTargetPositionStore(CentralSQLiteDatabase(path))
    service = CycleTargetPositionService(
        store, AlgorithmRunService(runs), software, clock=lambda: NOW
    )
    formula_operation = service.save_formula_definition(CreateCycleTargetFormulaCommand(
        uuid4(), "session", "p29-formula", "P29 v1", "approved formula", "pytest",
    ))
    formula = store.get_formula_definition(formula_operation.resolved_formula_definition_id)
    assert formula is not None
    configuration_operation = service.save_configuration(CreateAssetCycleTargetConfigurationCommand(
        uuid4(), "session", "p29-config", "AAPL", formula.formula_definition_id,
        formula.definition_version, "0.1", "0.5", "0.9", "0.05", "2", "4",
        "explicit AAPL test configuration", "pytest",
    ))
    configuration = store.get_configuration(configuration_operation.resolved_configuration_id)
    assert configuration is not None
    step = p28.result.daily_steps[-1]
    command = CycleTargetPreviewCommand(
        uuid4(), "session", "p29-preview", configuration.configuration_id,
        configuration.configuration_version, p28.result.result_id, step.step_id,
        p28.run_id, "100000", "50000", "exact P28 step preview", "pytest",
    )
    operation = CycleTargetPositionResearchCoordinator(reversal, service).preview(command)
    assert operation.status in {
        CycleTargetOperationStatus.COMPLETED,
        CycleTargetOperationStatus.COMPLETED_WITH_WARNINGS,
    }
    assert operation.result is not None
    assert store.get_operation(operation.attempt_id) == operation
    assert store.get_result(operation.result.result_id) == operation.result
    assert store.list_results(CycleTargetQuery(symbol="AAPL")) == (operation.result,)
    replay = CycleTargetPositionReplayService(store)
    assert replay.recalculate(operation.result.result_id) == operation.result
    assert replay.verify(operation.result.result_id).matches
    assert "fingerprint equal: True" in replay.compare(
        operation.result.result_id, operation.result.result_id
    )
    detail = runs.get_run_detail(operation.run_id)
    assert detail.summary.run.run_type is AlgorithmRunType.CYCLE_TARGET_POSITION_RESEARCH
    assert [item.name.value for item in detail.stages] == ["state", "target_position"]
    assert any(item.run_id == p28.run_id for item in detail.relationships)
    assert any(
        item.artifact_type == "cycle_target_position_operation"
        and item.artifact_id == str(operation.attempt_id)
        and item.children
        for item in detail.artifacts
    )
    p28_detail = runs.get_run_detail(p28.run_id)
    assert any(item.run_id == operation.run_id for item in p28_detail.relationships)
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 20
        assert connection.execute("SELECT COUNT(*) FROM cycle_target_results").fetchone()[0] == 1
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def test_v17_to_v19_migration_is_backed_up_additive_and_zero_backfill(tmp_path: Path):
    path = tmp_path / "central.sqlite3"
    with sqlite3.connect(path) as connection:
        for version in range(1, 18):
            connection.executescript(sqlite_database._MIGRATIONS[version][1])
            connection.execute(
                "INSERT INTO schema_migrations VALUES (?, ?, ?)",
                (version, NOW.isoformat(), f"fixture {version}"),
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
    assert ".schema-v17-to-v20." in backups[0].name
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 20
        assert connection.execute("SELECT COUNT(*) FROM market_bars").fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM cycle_target_results").fetchone()[0] == 0
        assert len(sqlite_database.expected_schema_tables()) == 124
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def test_p29_failure_stages_preserve_completed_source_and_fail_unresolved_source(tmp_path: Path):
    path = tmp_path / "failure-stages.sqlite3"
    reversal, runs, p28, software = _p28(path)
    store = SQLiteCycleTargetPositionStore(path)
    base_runs = AlgorithmRunService(runs)

    class FailTargetStage:
        def __getattr__(self, name):
            return getattr(base_runs, name)

        def start_stage(self, run_id, stage_name, sequence):
            if sequence == 2:
                raise RuntimeError("injected target-stage creation failure")
            return base_runs.start_stage(run_id, stage_name, sequence)

    service = CycleTargetPositionService(store, FailTargetStage(), software, clock=lambda: NOW)
    formula_operation = service.save_formula_definition(CreateCycleTargetFormulaCommand(
        uuid4(), "session", "formula", "P29", "failure fixture", "pytest",
    ))
    formula = store.get_formula_definition(formula_operation.resolved_formula_definition_id)
    configuration_operation = service.save_configuration(CreateAssetCycleTargetConfigurationCommand(
        uuid4(), "session", "config", "AAPL", formula.formula_definition_id,
        formula.definition_version, "0.1", "0.5", "0.9", "0.05", "2", "4",
        "failure fixture", "pytest",
    ))
    configuration = store.get_configuration(configuration_operation.resolved_configuration_id)
    step = p28.result.daily_steps[-1]
    failed = CycleTargetPositionResearchCoordinator(reversal, service).preview(
        CycleTargetPreviewCommand(
            uuid4(), "session", "target-stage-failure", configuration.configuration_id,
            configuration.configuration_version, p28.result.result_id, step.step_id,
            p28.run_id, "100000", "50000", "injected failure", "pytest",
        )
    )
    assert failed.status is CycleTargetOperationStatus.FAILED
    detail = runs.get_run_detail(failed.run_id)
    assert [(item.name.value, item.status.value) for item in detail.stages] == [
        ("state", "completed")
    ]
    assert detail.summary.run.status.value == "failed"

    unresolved = CycleTargetPositionResearchCoordinator(reversal, service).preview(
        CycleTargetPreviewCommand(
            uuid4(), "session", "source-failure", configuration.configuration_id,
            configuration.configuration_version, uuid4(), uuid4(), uuid4(),
            "100000", "50000", "missing source", "pytest",
        )
    )
    unresolved_detail = runs.get_run_detail(unresolved.run_id)
    assert unresolved.status is CycleTargetOperationStatus.SOURCE_NOT_FOUND
    assert [(item.name.value, item.status.value) for item in unresolved_detail.stages] == [
        ("state", "failed")
    ]
