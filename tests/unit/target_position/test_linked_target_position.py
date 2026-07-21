from __future__ import annotations

import sqlite3
from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from quant_trading.factors import (
    CreateStandardizedPriceStateDefinitionCommand,
    PreviewStandardizedPriceStateCommand,
    StandardizedPriceStateService,
)
from quant_trading.orchestration import (
    StandardizedStateTargetPositionPreviewCoordinator,
)
from quant_trading.persistence import (
    CentralSQLiteDatabase,
    SQLiteRunHistoryRepository,
    SQLiteStandardizedPriceStateStore,
    SQLiteTargetPositionStore,
)
from quant_trading.persistence import sqlite_database
from quant_trading.persistence.sqlite_database import (
    _SCHEMA_V1,
    _SCHEMA_V2,
    _SCHEMA_V3,
    _SCHEMA_V4,
    _SCHEMA_V5,
    _SCHEMA_V6,
    _SCHEMA_V7,
    _SCHEMA_V8,
)
from quant_trading.run_history import (
    AlgorithmRunService,
    AlgorithmRunStatus,
    AlgorithmRunType,
    SoftwareIdentity,
    WorktreeState,
)
from quant_trading.target_position import (
    CreateTargetPositionDefinitionCommand,
    LinkedTargetPositionOperationStatus,
    LinkedTargetPositionPreviewCommand,
    LinkedTargetPositionQuery,
    LinkedTargetPositionService,
    TargetPositionDirection,
    TargetPositionKnotInput,
    TargetPositionOperationStatus,
    TargetPositionService,
)


NOW = datetime(2026, 7, 21, 0, 30, tzinfo=UTC)
SOFTWARE = SoftwareIdentity("test", "abc123", WorktreeState.CLEAN)


def _system(path: Path, *, linked_store=None):
    runs = SQLiteRunHistoryRepository(path)
    runs.initialize()
    source_store = SQLiteStandardizedPriceStateStore(path)
    source_store.initialize()
    target_store = SQLiteTargetPositionStore(path)
    target_store.initialize()
    source_service = StandardizedPriceStateService(
        source_store,
        AlgorithmRunService(runs, clock=lambda: NOW),
        SOFTWARE,
        clock=lambda: NOW,
    )
    target_service = TargetPositionService(
        target_store,
        AlgorithmRunService(runs, clock=lambda: NOW),
        SOFTWARE,
        clock=lambda: NOW,
    )
    child_service = LinkedTargetPositionService(
        linked_store or target_store,
        AlgorithmRunService(runs, clock=lambda: NOW),
        SOFTWARE,
        clock=lambda: NOW,
    )
    coordinator = StandardizedStateTargetPositionPreviewCoordinator(
        source_store,
        target_store,
        child_service,
        AlgorithmRunService(runs, clock=lambda: NOW),
        SOFTWARE,
        clock=lambda: NOW,
    )
    return source_service, target_service, coordinator, source_store, target_store, runs


def _source(service: StandardizedPriceStateService):
    definition = service.create_definition(
        CreateStandardizedPriceStateDefinitionCommand(
            "Manual state",
            "Exact source definition",
            "SESSION",
            "SOURCE-DEFINE",
            "tester",
        )
    )
    preview = service.preview(
        PreviewStandardizedPriceStateCommand(
            definition.definition_id,
            "AAPL",
            "90",
            "100",
            "10",
            NOW,
            "Exact persisted source",
            "SESSION",
            "SOURCE-PREVIEW",
            "tester",
        )
    )
    return definition, preview


def _target(service: TargetPositionService):
    return service.create_definition(
        CreateTargetPositionDefinitionCommand(
            "Bounded curve",
            "Exact target definition",
            TargetPositionDirection.NON_INCREASING,
            "0.1",
            "0.5",
            "0.9",
            (
                TargetPositionKnotInput("-2", "0.9"),
                TargetPositionKnotInput("0", "0.5"),
                TargetPositionKnotInput("2", "0.1"),
            ),
            "SESSION",
            "TARGET-DEFINE",
            "tester",
        )
    )


def _command(source_id, target_id, *, operation_id=None, basis="100"):
    return LinkedTargetPositionPreviewCommand(
        source_id,
        target_id,
        basis,
        "60",
        "Exact linked research preview",
        "SESSION",
        "LINKED-PREVIEW",
        "tester",
        operation_id,
    )


def test_linked_preview_preserves_exact_source_and_parent_child_runs(tmp_path: Path):
    database = tmp_path / "central.sqlite3"
    source_service, target_service, coordinator, source_store, target_store, runs = _system(database)
    source_definition, source_preview = _source(source_service)
    target_definition = _target(target_service)

    outcome = coordinator.preview(
        _command(source_preview.calculation_id, target_definition.definition_id)
    )

    assert outcome.status is LinkedTargetPositionOperationStatus.COMPLETED
    source = source_store.get_result(source_preview.calculation_id)
    target = target_store.get_result(outcome.target_calculation_id)
    link = target_store.get_standardized_state_link(outcome.operation_id)
    assert target.research_state_value == source.standardized_state == Decimal("-1")
    assert target.as_of_utc == source.as_of_utc
    assert target.target_fraction == Decimal("0.7")
    assert target.target_position_value_usd == Decimal("70.0")
    assert target.adjustment_value_usd == Decimal("10.0")
    assert link.source_calculation_id == source.calculation_id
    assert link.source_definition_id == source_definition.definition_id
    assert link.symbol == "AAPL"
    assert link.standardized_state == Decimal("-1")
    assert link.target_calculation_id == target.calculation_id
    assert link.target_definition_id == target_definition.definition_id
    filtered = target_store.list_standardized_state_links(
        LinkedTargetPositionQuery(
            symbol="aapl",
            source_definition_id=source_definition.definition_id,
            target_definition_id=target_definition.definition_id,
            status=LinkedTargetPositionOperationStatus.COMPLETED,
            as_of_from_utc=NOW.replace(hour=0),
            as_of_to_utc=NOW.replace(hour=1),
        )
    )
    assert filtered == (link,)
    assert target_store.list_standardized_state_links(
        LinkedTargetPositionQuery(symbol="MSFT")
    ) == ()

    parent = runs.get_run(outcome.parent_run_id)
    child = runs.get_run(outcome.child_run_id)
    source_run = runs.get_run(source.run_id)
    assert parent.run_type is AlgorithmRunType.STANDARDIZED_TARGET_POSITION_PREVIEW
    assert parent.status is AlgorithmRunStatus.COMPLETED
    assert child.parent_run_id == parent.run_id
    assert child.run_type is AlgorithmRunType.TARGET_POSITION_PREVIEW
    assert child.status is AlgorithmRunStatus.COMPLETED
    assert source_run.run_type is AlgorithmRunType.STANDARDIZED_STATE_PREVIEW
    source_detail = runs.get_run_detail(source.run_id)
    assert all("â€”" not in artifact.summary for artifact in source_detail.artifacts)
    assert [item.name.value for item in runs.get_run_detail(parent.run_id).stages] == [
        "standardized_state",
        "target_position",
    ]
    parent_detail = runs.get_run_detail(parent.run_id)
    parent_relationships = {
        (item.relationship_type.value, item.run_id)
        for item in parent_detail.relationships
    }
    assert ("source", source.run_id) in parent_relationships
    assert ("child", child.run_id) in parent_relationships
    child_relationships = {
        (item.relationship_type.value, item.run_id)
        for item in runs.get_run_detail(child.run_id).relationships
    }
    assert ("parent", parent.run_id) in child_relationships
    assert ("source", source.run_id) in child_relationships
    source_relationships = {
        (item.relationship_type.value, item.run_id)
        for item in source_detail.relationships
    }
    assert ("linked_preview", parent.run_id) in source_relationships
    linked_artifact = next(
        item
        for item in parent_detail.artifacts
        if item.artifact_type == "linked_target_position_operation"
    )
    assert linked_artifact.children[0].artifact_type == (
        "standardized_state_target_position_link"
    )

    reopened = SQLiteTargetPositionStore(database)
    reopened.initialize()
    assert reopened.get_standardized_state_link(outcome.operation_id) == link
    assert reopened.get_result(target.calculation_id) == target


def test_linked_preview_is_idempotent_and_conflicting_reuse_is_durable(tmp_path: Path):
    source_service, target_service, coordinator, _sources, targets, runs = _system(
        tmp_path / "central.sqlite3"
    )
    _source_definition, source_preview = _source(source_service)
    target_definition = _target(target_service)
    operation_id = uuid4()
    command = _command(
        source_preview.calculation_id,
        target_definition.definition_id,
        operation_id=operation_id,
    )

    first = coordinator.preview(command)
    retry = coordinator.preview(command)
    conflict = coordinator.preview(replace(command, research_capital_basis_usd="200"))

    assert retry.parent_run_id == first.parent_run_id
    assert retry.target_calculation_id == first.target_calculation_id
    assert "no new Run" in retry.summary
    assert conflict.status is LinkedTargetPositionOperationStatus.INVALID_INPUT
    attempts = targets.list_linked_operations()
    assert len(attempts) == 2
    assert sum(item.status is LinkedTargetPositionOperationStatus.COMPLETED for item in attempts) == 1
    assert sum(item.status is LinkedTargetPositionOperationStatus.INVALID_INPUT for item in attempts) == 1
    assert targets.get_first_linked_operation(operation_id).status is LinkedTargetPositionOperationStatus.COMPLETED
    assert runs.get_run(conflict.parent_run_id).status is AlgorithmRunStatus.INVALID_INPUT


def test_missing_source_and_unknown_target_are_durable_without_accepted_link(tmp_path: Path):
    source_service, target_service, coordinator, _sources, targets, runs = _system(
        tmp_path / "central.sqlite3"
    )
    _source_definition, source_preview = _source(source_service)
    target_definition = _target(target_service)

    missing_source = coordinator.preview(
        _command(uuid4(), target_definition.definition_id)
    )
    unknown_target = coordinator.preview(
        _command(source_preview.calculation_id, uuid4())
    )

    assert missing_source.status is LinkedTargetPositionOperationStatus.INVALID_INPUT
    assert missing_source.child_run_id is None
    assert targets.get_standardized_state_link(missing_source.operation_id) is None
    assert runs.get_run(missing_source.parent_run_id).status is AlgorithmRunStatus.INVALID_INPUT
    assert unknown_target.status is LinkedTargetPositionOperationStatus.INVALID_INPUT
    assert unknown_target.child_run_id is not None
    assert targets.get_standardized_state_link(unknown_target.operation_id) is None
    assert targets.get_first_operation(unknown_target.operation_id).status is TargetPositionOperationStatus.INVALID_INPUT
    assert runs.get_run(unknown_target.child_run_id).status is AlgorithmRunStatus.INVALID_INPUT


def test_store_rejects_tampered_source_to_target_link_transactionally(tmp_path: Path):
    database = tmp_path / "central.sqlite3"
    durable = SQLiteTargetPositionStore(database)

    class CorruptingStore:
        def __getattr__(self, name):
            return getattr(durable, name)

        def save_linked_preview(self, result, target_operation, linked_operation, link):
            durable.save_linked_preview(
                result,
                target_operation,
                linked_operation,
                replace(link, standardized_state=Decimal("999")),
            )

    source_service, target_service, coordinator, _sources, targets, runs = _system(
        database, linked_store=CorruptingStore()
    )
    _source_definition, source_preview = _source(source_service)
    target_definition = _target(target_service)

    outcome = coordinator.preview(
        _command(source_preview.calculation_id, target_definition.definition_id)
    )

    assert outcome.status is LinkedTargetPositionOperationStatus.FAILED
    assert targets.list_standardized_state_links() == ()
    assert targets.list_results() == ()
    assert targets.get_first_operation(outcome.operation_id).status is TargetPositionOperationStatus.FAILED
    assert runs.get_run(outcome.child_run_id).status is AlgorithmRunStatus.FAILED
    assert runs.get_run(outcome.parent_run_id).status is AlgorithmRunStatus.FAILED


def _create_v7_database(path: Path) -> None:
    with sqlite3.connect(path) as connection:
        for version, schema in (
            (1, _SCHEMA_V1),
            (2, _SCHEMA_V2),
            (3, _SCHEMA_V3),
            (4, _SCHEMA_V4),
            (5, _SCHEMA_V5),
            (6, _SCHEMA_V6),
            (7, _SCHEMA_V7),
        ):
            connection.executescript(schema)
            connection.execute(
                "INSERT INTO schema_migrations VALUES (?, ?, ?)",
                (version, NOW.isoformat(), f"test v{version}"),
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


def test_v7_to_v8_migration_backs_up_preserves_and_creates_no_links(tmp_path: Path):
    database = tmp_path / "central.sqlite3"
    backups = tmp_path / "backups"
    _create_v7_database(database)

    CentralSQLiteDatabase(database, backup_directory=backups).initialize()

    backup_files = tuple(backups.glob("*.sqlite3"))
    assert len(backup_files) == 1
    assert ".schema-v7-to-v8." in backup_files[0].name
    with sqlite3.connect(backup_files[0]) as backup:
        assert backup.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 7
        assert backup.execute("SELECT COUNT(*) FROM market_bars").fetchone()[0] == 1
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 8
        assert connection.execute("SELECT COUNT(*) FROM market_bars").fetchone()[0] == 1
        assert connection.execute(
            "SELECT COUNT(*) FROM target_position_linked_preview_operations"
        ).fetchone()[0] == 0
        assert connection.execute(
            "SELECT COUNT(*) FROM target_position_standardized_state_links"
        ).fetchone()[0] == 0
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def test_failed_v8_migration_rolls_back_to_intact_v7(tmp_path: Path, monkeypatch):
    database = tmp_path / "central.sqlite3"
    backups = tmp_path / "backups"
    _create_v7_database(database)
    broken = dict(sqlite_database._MIGRATIONS)
    broken[8] = ("intentionally broken v8", _SCHEMA_V8 + "\nINVALID SQL;")
    monkeypatch.setattr(sqlite_database, "_MIGRATIONS", broken)

    with pytest.raises(sqlite3.OperationalError):
        CentralSQLiteDatabase(database, backup_directory=backups).initialize()

    assert len(tuple(backups.glob("*.sqlite3"))) == 1
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 7
        assert connection.execute("SELECT COUNT(*) FROM market_bars").fetchone()[0] == 1
        assert connection.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE name = 'target_position_standardized_state_links'"
        ).fetchone()[0] == 0
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
