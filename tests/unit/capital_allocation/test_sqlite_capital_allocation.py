from __future__ import annotations

import sqlite3
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest

from quant_trading.capital_allocation import (
    CapitalAllocationService,
    CapitalAssetAllocationInput,
    CapitalBucketBalance,
    CapitalOperationStatus,
    CapitalPlanQuery,
    CreateCapitalPlanCommand,
    TransferCapitalCommand,
)
from quant_trading.persistence import (
    CentralSQLiteDatabase,
    SQLiteCapitalAllocationStore,
    SQLiteRunHistoryRepository,
)
from quant_trading.persistence import sqlite_database
from quant_trading.persistence.sqlite_database import (
    _SCHEMA_V1,
    _SCHEMA_V2,
    _SCHEMA_V3,
    _SCHEMA_V4,
)
from quant_trading.run_history import AlgorithmRunService, SoftwareIdentity, WorktreeState


NOW = datetime(2026, 7, 20, 18, 0, tzinfo=UTC)


def _create_v3_database(path: Path) -> None:
    with sqlite3.connect(path) as connection:
        connection.executescript(_SCHEMA_V1)
        connection.execute(
            "INSERT INTO schema_migrations VALUES (1, ?, 'test v1')",
            (NOW.isoformat(),),
        )
        connection.executescript(_SCHEMA_V2)
        connection.execute(
            "INSERT INTO schema_migrations VALUES (2, ?, 'test v2')",
            (NOW.isoformat(),),
        )
        connection.executescript(_SCHEMA_V3)
        connection.execute(
            "INSERT INTO schema_migrations VALUES (3, ?, 'test v3')",
            (NOW.isoformat(),),
        )
        connection.execute(
            """
            INSERT INTO market_bars VALUES (
                'AAPL', ?, '1Day', 'raw', 'iex', '100', '101', '99',
                '100.5', 10, NULL, NULL, 'test', ?
            )
            """,
            (NOW.isoformat(), NOW.isoformat()),
        )
        connection.commit()


def _service(path: Path):
    store = SQLiteCapitalAllocationStore(path)
    store.initialize()
    runs = SQLiteRunHistoryRepository(path)
    runs.initialize()
    service = CapitalAllocationService(
        store,
        AlgorithmRunService(runs, clock=lambda: NOW),
        SoftwareIdentity("test", "abc123", WorktreeState.CLEAN),
        clock=lambda: NOW,
    )
    return service, store, runs


def _command(*, request_id: str = "CREATE", total: str = "1000"):
    return CreateCapitalPlanCommand(
        "Persisted plan",
        "Research-only initial allocation",
        total,
        "100",
        "100",
        (
            CapitalAssetAllocationInput("AAPL", "400"),
            CapitalAssetAllocationInput("MSFT", "400"),
        ),
        "SESSION",
        request_id,
        "tester",
    )


def test_v3_to_current_migration_backs_up_and_preserves_existing_rows(tmp_path: Path):
    database_path = tmp_path / "central.sqlite3"
    backup_path = tmp_path / "backups"
    _create_v3_database(database_path)

    CentralSQLiteDatabase(
        database_path, backup_directory=backup_path
    ).initialize()

    backups = tuple(backup_path.glob("*.sqlite3"))
    assert len(backups) == 1
    assert ".schema-v3-to-v8." in backups[0].name
    with sqlite3.connect(backups[0]) as backup:
        assert backup.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 3
        assert backup.execute("SELECT COUNT(*) FROM market_bars").fetchone()[0] == 1
        assert backup.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    with sqlite3.connect(database_path) as connection:
        assert connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 8
        assert connection.execute("SELECT COUNT(*) FROM market_bars").fetchone()[0] == 1
        assert connection.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE name = 'capital_plans'"
        ).fetchone()[0] == 1
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def test_failed_v4_migration_rolls_back_to_intact_v3(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    database_path = tmp_path / "central.sqlite3"
    backup_path = tmp_path / "backups"
    _create_v3_database(database_path)
    broken = dict(sqlite_database._MIGRATIONS)
    broken[4] = ("intentionally broken v4", _SCHEMA_V4 + "\nINVALID SQL;")
    monkeypatch.setattr(sqlite_database, "_MIGRATIONS", broken)

    with pytest.raises(sqlite3.OperationalError):
        CentralSQLiteDatabase(
            database_path, backup_directory=backup_path
        ).initialize()

    assert len(tuple(backup_path.glob("*.sqlite3"))) == 1
    with sqlite3.connect(database_path) as connection:
        assert connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 3
        assert connection.execute("SELECT COUNT(*) FROM market_bars").fetchone()[0] == 1
        assert connection.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE name = 'capital_plans'"
        ).fetchone()[0] == 0
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def test_plan_transfer_and_run_artifacts_reload_after_reopen(tmp_path: Path):
    database_path = tmp_path / "central.sqlite3"
    service, store, runs = _service(database_path)

    created = service.create_plan(_command())
    assert created.status is CapitalOperationStatus.COMPLETED
    initial_detail = store.get_plan_detail(created.plan_id)
    by_symbol = {
        item.symbol: item
        for item in initial_detail.plan.buckets
        if item.symbol is not None
    }
    transferred = service.transfer(
        TransferCapitalCommand(
            created.plan_id,
            by_symbol["AAPL"].bucket_id,
            by_symbol["MSFT"].bucket_id,
            "25.50",
            "Manual persisted transfer",
            "SESSION",
            "TRANSFER",
            "tester",
        )
    )
    assert transferred.status is CapitalOperationStatus.COMPLETED

    reopened = SQLiteCapitalAllocationStore(database_path)
    reopened.initialize()
    summaries = reopened.list_plans(CapitalPlanQuery(name_text="persisted"))
    assert len(summaries) == 1
    detail = reopened.get_plan_detail(created.plan_id)
    assert len(detail.transfers) == 1
    assert len(detail.transfer_history) == 1
    assert len(detail.operations) == 2
    history = detail.transfer_history[0]
    assert str(history.source_balance_before) == "400"
    assert str(history.source_balance_after) == "374.50"
    assert str(history.destination_balance_before) == "400"
    assert str(history.destination_balance_after) == "425.50"
    balances = {
        item.symbol: item.balance
        for item in detail.latest_snapshot.balances
        if item.symbol is not None
    }
    assert str(balances["AAPL"]) == "374.50"
    assert str(balances["MSFT"]) == "425.50"
    assert detail.latest_snapshot.conservation.difference == 0

    run_detail = runs.get_run_detail(transferred.run_id)
    assert run_detail is not None
    assert run_detail.stages[0].name.value == "allocation"
    artifact = next(
        item
        for item in run_detail.artifacts
        if item.artifact_type == "capital_allocation_operation"
    )
    assert artifact.status == "completed"
    assert len(artifact.children) == 4
    assert all(child.status == "conserved" for child in artifact.children)


def test_invalid_plan_attempt_survives_restart_and_is_visible_in_run(tmp_path: Path):
    database_path = tmp_path / "central.sqlite3"
    service, _store, runs = _service(database_path)

    result = service.create_plan(_command(request_id="INVALID", total="999"))

    assert result.status is CapitalOperationStatus.INVALID_INPUT
    reopened_runs = SQLiteRunHistoryRepository(database_path)
    reopened_runs.initialize()
    detail = reopened_runs.get_run_detail(result.run_id)
    assert detail is not None
    assert detail.summary.run.status.value == "invalid_input"
    artifact = next(
        item
        for item in detail.artifacts
        if item.artifact_type == "capital_allocation_operation"
    )
    assert artifact.status == "invalid_input"
    assert any(field.name == "error" and "conserve" in field.value for field in artifact.fields)
    with sqlite3.connect(database_path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM capital_plans").fetchone()[0] == 0
        assert connection.execute("SELECT COUNT(*) FROM capital_snapshots").fetchone()[0] == 0
        assert connection.execute("SELECT COUNT(*) FROM capital_allocation_operations").fetchone()[0] == 1
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []


def test_sqlite_store_rejects_a_conserved_snapshot_with_a_missing_plan_bucket(
    tmp_path: Path,
):
    database_path = tmp_path / "central.sqlite3"
    store = SQLiteCapitalAllocationStore(database_path)
    store.initialize()
    runs = SQLiteRunHistoryRepository(database_path)
    runs.initialize()

    class TamperingStore:
        def __getattr__(self, name):
            return getattr(store, name)

        def create_plan(self, plan, snapshot, operation):
            aapl = next(item for item in snapshot.balances if item.symbol == "AAPL")
            msft = next(item for item in snapshot.balances if item.symbol == "MSFT")
            malformed = replace(
                snapshot,
                balances=tuple(
                    CapitalBucketBalance(
                        item.bucket_id,
                        item.bucket_type,
                        item.currency,
                        item.balance + msft.balance
                        if item.bucket_id == aapl.bucket_id
                        else item.balance,
                        item.symbol,
                    )
                    for item in snapshot.balances
                    if item.bucket_id != msft.bucket_id
                ),
            )
            store.create_plan(plan, malformed, operation)

    service = CapitalAllocationService(
        TamperingStore(),
        AlgorithmRunService(runs, clock=lambda: NOW),
        SoftwareIdentity("test", "abc123", WorktreeState.CLEAN),
        clock=lambda: NOW,
    )

    result = service.create_plan(_command(request_id="MALFORMED"))

    assert result.status is CapitalOperationStatus.FAILED
    detail = runs.get_run_detail(result.run_id)
    assert detail.summary.run.status.value == "failed"
    assert "every plan bucket" in detail.artifacts[0].fields[-1].value
    with sqlite3.connect(database_path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM capital_plans").fetchone()[0] == 0
        assert connection.execute("SELECT COUNT(*) FROM capital_snapshots").fetchone()[0] == 0
        assert connection.execute("SELECT COUNT(*) FROM capital_allocation_operations").fetchone()[0] == 1
