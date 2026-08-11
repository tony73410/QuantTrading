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
    ReversalObservationOperationStatus,
    ReversalObservationPriceObservation,
    ReversalObservationProfileEvidence,
    ReversalObservationQuery,
    ReversalObservationReplayService,
    ReversalObservationService,
    ReversalPriceEvidence,
)
from quant_trading.factors import DailyVolatilityProfileCommand
from quant_trading.persistence import (
    SQLiteReversalObservationStore,
    SQLiteRunHistoryRepository,
)
from quant_trading.persistence import sqlite_database
from quant_trading.persistence.sqlite_database import CentralSQLiteDatabase
from quant_trading.run_history import AlgorithmRunService, SoftwareIdentity, WorktreeState

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


def test_service_persists_definition_result_steps_events_and_run_artifact(tmp_path: Path) -> None:
    path = tmp_path / "central.sqlite3"
    study, source_definition, _, profiles, profile_service, runs, profile_definition = _environment(path)
    profile_operation = profile_service.preview(
        profile_command(study, source_definition, profile_definition)
    )
    assert profile_operation.result is not None
    profile_result = profile_operation.result

    store = SQLiteReversalObservationStore(path)
    store.initialize()
    software = SoftwareIdentity("0.1.0", "test-revision", WorktreeState.CLEAN)
    service = ReversalObservationService(store, AlgorithmRunService(runs), software, clock=lambda: NOW)
    definition_operation = service.save_definition(CreateReversalObservationDefinitionCommand(
        uuid4(), "session", "definition-request", "1.0", None,
        "pytest", "approved symmetric multiplier",
    ))
    definition = store.get_definition(definition_operation.definition_id)
    assert definition is not None

    seed_session = profile_result.evaluation_end_session
    day1, day2, day3 = (
        seed_session + timedelta(days=offset) for offset in (1, 2, 3)
    )
    seed = _observation(seed_session, 100.0, profile_result.created_at_utc - timedelta(minutes=1))
    observations = (
        _observation(day1, 90.0, profile_result.created_at_utc + timedelta(days=1)),
        _observation(day2, 89.0, profile_result.created_at_utc + timedelta(days=2)),
        _observation(day3, 88.0, profile_result.created_at_utc + timedelta(days=3)),
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
        ReversalFloatEvidence(
            profile_result.profile_log_scale.value, profile_result.profile_log_scale.ieee_hex
        ),
        profile_result.calculation_fingerprint,
        "factor.daily_volatility_profile.p23_1f.v1", "1.0.0", True,
    )
    command = ReversalObservationCommand(
        uuid4(), "session", "preview-request", profile_result.symbol,
        definition.definition_id, definition.definition_version, profile_result.result_id,
        ReversalDirection.UP, seed_session, seed.observation_id, seed.split_close,
        day3, market.calendar_definition_id, market.calendar_version,
        market.calendar_fingerprint, "pytest", "persist P28 preview",
    )
    operation = service.preview(command, profile, market)

    assert operation.status in {
        ReversalObservationOperationStatus.COMPLETED,
        ReversalObservationOperationStatus.COMPLETED_WITH_WARNINGS,
    }
    assert operation.result is not None
    assert store.get_operation(operation.attempt_id) == operation
    assert store.get_result(operation.result.result_id) == operation.result
    assert ReversalObservationReplayService(store).recalculate(operation.result.result_id) == operation.result
    assert store.list_operations(ReversalObservationQuery(has_confirmation=True))[0] == operation
    detail = runs.get_run_detail(operation.run_id)
    assert any(item.artifact_type == "reversal_observation_operation" for item in detail.artifacts)
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 18
        assert connection.execute("SELECT COUNT(*) FROM reversal_observation_daily_steps").fetchone()[0] == 3
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def test_v16_to_v17_migration_is_additive_backed_up_and_zero_backfill(tmp_path: Path) -> None:
    path = tmp_path / "central.sqlite3"
    with sqlite3.connect(path) as connection:
        for version in range(1, 17):
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
    assert ".schema-v16-to-v18." in backups[0].name
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 18
        assert connection.execute("SELECT COUNT(*) FROM market_bars").fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM reversal_observation_results").fetchone()[0] == 0
        assert len(sqlite_database.expected_schema_tables()) == 116
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
