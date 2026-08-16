from __future__ import annotations

import sqlite3
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from quant_trading.asset_state import (
    CreateMathematicalCycleDefinitionCommand,
    CreateReversalObservationDefinitionCommand,
    MathematicalCycleOperationStatus,
    MathematicalCyclePromotionCommand,
    MathematicalCycleReplayService,
    MathematicalCycleStateService,
    ReversalDirection,
    ReversalFloatEvidence,
    ReversalObservationCommand,
    ReversalObservationMarketEvidence,
    ReversalObservationPriceObservation,
    ReversalObservationProfileEvidence,
    ReversalObservationService,
    ReversalPriceEvidence,
)
from quant_trading.orchestration import MathematicalCyclePromotionCoordinator
from quant_trading.persistence import (
    SQLiteMathematicalCycleStateStore,
    SQLiteReversalObservationStore,
)
from quant_trading.persistence import sqlite_database
from quant_trading.persistence.sqlite_database import CentralSQLiteDatabase
from quant_trading.run_history import AlgorithmRunService, SoftwareIdentity, WorktreeState

from test_daily_volatility_profile import _command as profile_command, _environment


NOW = datetime(2026, 8, 10, 20, 0, tzinfo=UTC)


def _price(value): return ReversalPriceEvidence(str(value), ReversalFloatEvidence(float(value)))


def _observation(session: date, price: float, available: datetime):
    return ReversalObservationPriceObservation(
        f"obs-{session}", session, available - timedelta(minutes=1), available, available,
        f"raw-{session}", f"split-{session}", _price(price), _price(price),
    )


def _p28(path: Path):
    study, source_definition, _, _, profile_service, runs, profile_definition = _environment(path)
    profile_operation = profile_service.preview(profile_command(study, source_definition, profile_definition))
    profile_result = profile_operation.result
    assert profile_result is not None
    store = SQLiteReversalObservationStore(path)
    software = SoftwareIdentity("0.1.0", "test-revision", WorktreeState.CLEAN)
    run_now = profile_result.created_at_utc + timedelta(days=1)
    service = ReversalObservationService(store, AlgorithmRunService(runs), software, clock=lambda: run_now)
    definition_operation = service.save_definition(CreateReversalObservationDefinitionCommand(
        uuid4(), "session", "p28-definition", "1.0", None, "pytest", "P28 fixture",
    ))
    definition = store.get_definition(definition_operation.definition_id)
    assert definition is not None
    seed_session = profile_result.evaluation_end_session
    sessions = tuple(seed_session + timedelta(days=value) for value in (1, 2, 3))
    seed = _observation(seed_session, 100, profile_result.created_at_utc - timedelta(minutes=1))
    observations = tuple(_observation(session, price, run_now + timedelta(days=index)) for index, (session, price) in enumerate(zip(sessions, (90, 89, 88)), 1))
    market = ReversalObservationMarketEvidence(
        uuid4(), "p37-market-fingerprint", "AAPL", "fixture", "iex", "1Day",
        "raw+split", "fixture", "US_EQUITIES_REGULAR_V1", "1",
        "p37-calendar", "none", seed, observations, sessions, (), run_now,
    )
    profile = ReversalObservationProfileEvidence(
        profile_result.result_id, profile_operation.run_id, profile_result.source_study_id,
        profile_result.source_parent_run_id, profile_result.source_definition_id,
        profile_result.source_definition_version, "AAPL", profile_result.evaluation_end_session,
        profile_result.created_at_utc,
        ReversalFloatEvidence(profile_result.profile_log_scale.value, profile_result.profile_log_scale.ieee_hex),
        profile_result.calculation_fingerprint, "factor.daily_volatility_profile.p23_1f.v1",
        "1.0.0", True,
    )
    operation = service.preview(ReversalObservationCommand(
        uuid4(), "session", "p28-preview", "AAPL", definition.definition_id,
        definition.definition_version, profile.result_id, ReversalDirection.UP,
        seed_session, seed.observation_id, seed.split_close, sessions[-1],
        market.calendar_definition_id, market.calendar_version,
        market.calendar_fingerprint, "pytest", "P28 for P37",
    ), profile, market)
    assert operation.result is not None
    return store, runs, software, operation


def test_exact_p28_promotes_to_restart_safe_disabled_stream_and_run_artifact(tmp_path: Path):
    path = tmp_path / "central.sqlite3"
    reversal, runs, software, p28 = _p28(path)
    store = SQLiteMathematicalCycleStateStore(path)
    store.initialize()
    p37_now = p28.completed_at_utc + timedelta(days=5)
    service = MathematicalCycleStateService(store, AlgorithmRunService(runs), software, clock=lambda: p37_now)
    definition_operation = service.save_definition(CreateMathematicalCycleDefinitionCommand(
        uuid4(), "session", "p37-definition", None, "pytest", "approved P37 definition",
    ))
    definition = store.get_definition(definition_operation.definition_id)
    assert definition is not None
    command = MathematicalCyclePromotionCommand(
        uuid4(), "session", "p37-promotion", definition.definition_id,
        definition.definition_version, p28.result.result_id, p28.run_id, "AAPL",
        "AAPL research stream", None, None, "pytest", "explicit synthetic promotion",
    )
    coordinator = MathematicalCyclePromotionCoordinator(reversal, service)
    preflight = coordinator.prepare(command)
    source = replace(preflight.source, warnings=(
        "LOCAL_ONLY frozen evidence; no Provider or broker call was made.",
    ))
    operation = service.promote(command, source)
    retry = service.promote(command, source)

    assert "exact P28" in preflight.summary
    assert operation.status is MathematicalCycleOperationStatus.COMPLETED_WITH_WARNINGS
    assert retry == operation
    assert operation.stream_id is not None
    reloaded = SQLiteMathematicalCycleStateStore(path)
    detail = MathematicalCycleReplayService(reloaded).replay(operation.stream_id)
    assert len(detail.snapshots) == 3
    assert len(detail.cycles) == 2
    assert detail.snapshots[0].direction_at_open.value == "up"
    assert detail.snapshots[1].direction_at_close.value == "up"
    assert detail.snapshots[2].direction_at_open.value == "down"
    run_detail = runs.get_run_detail(operation.run_id)
    assert any(item.artifact_type == "mathematical_cycle_state_operation" for item in run_detail.artifacts)
    assert run_detail.summary.warning_count == 1
    assert len(run_detail.messages) == 1
    assert run_detail.messages[0].code == "QT-MATHEMATICAL-CYCLE-SOURCE-WARNING"
    assert run_detail.messages[0].message == operation.warnings[0]
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 23
        assert connection.execute("SELECT COUNT(*) FROM mathematical_cycle_streams").fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM mathematical_cycle_state_operations WHERE operation_type='create_stream'").fetchone()[0] == 1
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def test_missing_exact_p28_is_persisted_as_failed_operation_without_state_mutation(tmp_path: Path):
    path = tmp_path / "central.sqlite3"
    reversal, runs, software, _ = _p28(path)
    store = SQLiteMathematicalCycleStateStore(path)
    service = MathematicalCycleStateService(store, AlgorithmRunService(runs), software, clock=lambda: NOW + timedelta(days=30))
    definition_operation = service.save_definition(CreateMathematicalCycleDefinitionCommand(
        uuid4(), "session", "definition", None, "pytest", "failure fixture",
    ))
    definition = store.get_definition(definition_operation.definition_id)
    assert definition is not None
    command = MathematicalCyclePromotionCommand(
        uuid4(), "session", "missing-source", definition.definition_id,
        definition.definition_version, uuid4(), uuid4(), "AAPL", "missing",
        None, None, "pytest", "persist missing exact source",
    )

    operation = MathematicalCyclePromotionCoordinator(reversal, service).promote(command)

    assert operation.status is MathematicalCycleOperationStatus.SOURCE_NOT_FOUND
    assert operation.error_code == "QT-MATHEMATICAL-CYCLE-SOURCE-NOT-FOUND"
    assert store.get_first_operation(command.operation_id) == operation
    assert store.list_streams() == ()
    assert runs.get_run_detail(operation.run_id).summary.run.status.value == "invalid_input"


def test_v21_to_v22_migration_is_additive_backed_up_zero_backfill_and_rolls_back(tmp_path: Path):
    path = tmp_path / "central.sqlite3"
    with sqlite3.connect(path) as connection:
        for version in range(1, 22):
            connection.executescript(sqlite_database._MIGRATIONS[version][1])
            connection.execute("INSERT INTO schema_migrations VALUES (?,?,?)", (version, NOW.isoformat(), f"fixture {version}"))
        connection.execute("""INSERT INTO market_bars VALUES ('AAPL','2026-01-02T00:00:00+00:00','1Day','raw','iex','100','101','99','100',100,NULL,NULL,'fixture','2026-01-03T00:00:00+00:00')""")
        connection.commit()

    CentralSQLiteDatabase(path).initialize()
    backups = tuple((tmp_path / "backups").glob("*.sqlite3"))
    assert len(backups) == 1 and ".schema-v21-to-v23." in backups[0].name
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 23
        assert connection.execute("SELECT COUNT(*) FROM market_bars").fetchone()[0] == 1
        for table in (
            "mathematical_cycle_state_definitions", "mathematical_cycle_state_operations",
            "mathematical_cycle_streams", "mathematical_trading_cycles",
            "mathematical_cycle_snapshots", "mathematical_cycle_transition_events",
            "mathematical_cycle_source_links",
        ):
            assert connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0] == 0
        assert len(sqlite_database.expected_schema_tables()) == 139
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"

    # A failed DDL script remains atomic and does not advance the ledger.
    rollback = tmp_path / "rollback.sqlite3"
    with sqlite3.connect(rollback) as connection:
        for version in range(1, 22):
            connection.executescript(sqlite_database._MIGRATIONS[version][1])
            connection.execute("INSERT INTO schema_migrations VALUES (?,?,?)", (version, NOW.isoformat(), f"fixture {version}"))
        connection.commit()
        try:
            connection.executescript("BEGIN IMMEDIATE; CREATE TABLE p37_partial(id TEXT); SELECT * FROM missing_table;")
        except sqlite3.OperationalError:
            connection.rollback()
        assert connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 21
        assert connection.execute("SELECT 1 FROM sqlite_master WHERE name='p37_partial'").fetchone() is None
