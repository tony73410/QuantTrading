from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from quant_trading.factors import (
    SpectralOperationQuery,
    SpectralOperationStatus,
    SpectralVolatilityPreviewCommand,
    SpectralVolatilityService,
)
from quant_trading.persistence import (
    SQLiteRunHistoryRepository,
    SQLiteSpectralVolatilityStore,
)
from quant_trading.persistence import sqlite_database
from quant_trading.persistence.sqlite_database import CentralSQLiteDatabase
from quant_trading.run_history import AlgorithmRunService, SoftwareIdentity, WorktreeState
from quant_trading.market_history import ResearchEvidenceMode

from spectral_fixtures import spectral_bundle, spectral_definition


def _v13_database(path: Path) -> None:
    with sqlite3.connect(path) as connection:
        for version in range(1, 14):
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


def test_v13_to_current_migration_backs_up_and_preserves_existing_rows(tmp_path: Path) -> None:
    path = tmp_path / "central.sqlite3"
    _v13_database(path)
    CentralSQLiteDatabase(path).initialize()
    backups = tuple((tmp_path / "backups").glob("*.sqlite3"))
    assert len(backups) == 1
    assert ".schema-v13-to-v21." in backups[0].name
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 21
        assert connection.execute("SELECT COUNT(*) FROM market_bars").fetchone()[0] == 1
        tables = connection.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ).fetchone()[0]
        assert tables == 130
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def test_failed_v14_migration_rolls_back_intact_v13(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "central.sqlite3"
    _v13_database(path)
    broken = dict(sqlite_database._MIGRATIONS)
    broken[14] = ("broken v14", broken[14][1] + "\nINVALID SQL;")
    monkeypatch.setattr(sqlite_database, "_MIGRATIONS", broken)
    with pytest.raises(sqlite3.DatabaseError):
        CentralSQLiteDatabase(path).initialize()
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 13
        assert connection.execute("SELECT COUNT(*) FROM market_bars").fetchone()[0] == 1
        assert connection.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='spectral_volatility_operations'"
        ).fetchone()[0] == 0


def test_preview_persists_exact_graph_reloads_and_opens_from_run(tmp_path: Path) -> None:
    path = tmp_path / "central.sqlite3"
    store = SQLiteSpectralVolatilityStore(path)
    store.initialize()
    run_repository = SQLiteRunHistoryRepository(path)
    run_repository.initialize()
    definition = spectral_definition()
    bundle = spectral_bundle()
    store.save_definition(definition)
    service = SpectralVolatilityService(
        store, AlgorithmRunService(run_repository),
        SoftwareIdentity("0.1.0", "test-revision", WorktreeState.CLEAN),
    )
    command = SpectralVolatilityPreviewCommand(
        uuid4(), "session", "request", bundle.symbol, bundle.as_of_utc,
        definition.definition_id, definition.definition_version, bundle.bundle_id,
        "pytest", "deterministic replay",
    )
    operation = service.preview(command, definition, bundle)
    assert operation.status is SpectralOperationStatus.COMPLETED

    restarted = SQLiteSpectralVolatilityStore(path)
    restarted.initialize()
    assert restarted.get_operation(operation.attempt_id) == operation
    assert restarted.get_operation_for_run(operation.run_id) == operation
    assert restarted.list_operations(SpectralOperationQuery(symbol="aapl")) == (operation,)
    assert restarted.find_latest_evidence_bundle(
        symbol="AAPL",
        as_of_utc=bundle.as_of_utc,
        feed=bundle.feed,
        evidence_mode=bundle.evidence_mode,
    ) == bundle
    detail = run_repository.get_run_detail(operation.run_id)
    artifact = next(
        item for item in detail.artifacts
        if item.artifact_type == "spectral_volatility_operation"
    )
    assert artifact.artifact_id == str(operation.operation_id)
    assert len(artifact.children) == 3
    assert "NO EXECUTION" in artifact.summary


def test_idempotent_retry_returns_original_and_conflict_is_durable_invalid(
    tmp_path: Path,
) -> None:
    path = tmp_path / "central.sqlite3"
    store = SQLiteSpectralVolatilityStore(path)
    store.initialize()
    runs = SQLiteRunHistoryRepository(path)
    runs.initialize()
    definition, bundle = spectral_definition(), spectral_bundle()
    store.save_definition(definition)
    service = SpectralVolatilityService(
        store, AlgorithmRunService(runs),
        SoftwareIdentity("0.1.0", "test", WorktreeState.CLEAN),
    )
    operation_id = uuid4()
    command = SpectralVolatilityPreviewCommand(
        operation_id, "session", "request", "AAPL", bundle.as_of_utc,
        definition.definition_id, 1, bundle.bundle_id, "pytest", "same",
    )
    original = service.preview(command, definition, bundle)
    assert service.preview(command, definition, bundle) == original
    conflict = service.preview(
        SpectralVolatilityPreviewCommand(
            operation_id, "session", "request", "AAPL", bundle.as_of_utc,
            definition.definition_id, 1, bundle.bundle_id, "pytest", "different",
        ),
        definition, bundle,
    )
    assert conflict.status is SpectralOperationStatus.INVALID_INPUT
    assert conflict.windows == ()
    operations = store.list_operations(SpectralOperationQuery(limit=10))
    assert {item.status for item in operations} == {
        SpectralOperationStatus.COMPLETED,
        SpectralOperationStatus.INVALID_INPUT,
    }


def test_retrospective_warning_is_persisted_and_visible_in_run_messages(
    tmp_path: Path,
) -> None:
    path = tmp_path / "central.sqlite3"
    store = SQLiteSpectralVolatilityStore(path)
    store.initialize()
    runs = SQLiteRunHistoryRepository(path)
    runs.initialize()
    definition = spectral_definition(inclusive_evaluation_session=True)
    bundle = spectral_bundle(
        evidence_mode=ResearchEvidenceMode.RETROSPECTIVE_ADJUSTED,
        include_evaluation_session=True,
        observed_after_as_of=True,
    )
    store.save_definition(definition)
    operation = SpectralVolatilityService(
        store,
        AlgorithmRunService(runs),
        SoftwareIdentity("0.1.0", "test", WorktreeState.CLEAN),
    ).preview(
        SpectralVolatilityPreviewCommand(
            uuid4(),
            "session",
            "request",
            bundle.symbol,
            bundle.as_of_utc,
            definition.definition_id,
            definition.definition_version,
            bundle.bundle_id,
            "pytest",
            "retrospective warning",
        ),
        definition,
        bundle,
    )
    assert operation.status is SpectralOperationStatus.COMPLETED_WITH_WARNINGS
    assert "RETROSPECTIVE_ADJUSTED" in operation.warnings
    assert "RETROSPECTIVE_ADJUSTED" in store.get_operation(operation.attempt_id).warnings
    detail = runs.get_run_detail(operation.run_id)
    assert any("RETROSPECTIVE_ADJUSTED" in item.message for item in detail.messages)
