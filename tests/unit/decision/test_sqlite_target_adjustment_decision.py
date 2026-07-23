from __future__ import annotations

import sqlite3
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from quant_trading.decision import (
    DecisionAction,
    TargetAdjustmentDecisionPreviewCommand,
    TargetAdjustmentDecisionQuery,
    TargetAdjustmentDecisionService,
    TargetAdjustmentDecisionStatus,
)
from quant_trading.factors import (
    CreateStandardizedPriceStateDefinitionCommand,
    PreviewStandardizedPriceStateCommand,
    StandardizedPriceStateService,
)
from quant_trading.orchestration import (
    StandardizedStateTargetPositionPreviewCoordinator,
    TargetAdjustmentDecisionPreviewCoordinator,
)
from quant_trading.persistence import (
    CentralSQLiteDatabase,
    SQLiteRunHistoryRepository,
    SQLiteStandardizedPriceStateStore,
    SQLiteTargetAdjustmentDecisionStore,
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
    _SCHEMA_V9,
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
    LinkedTargetPositionPreviewCommand,
    LinkedTargetPositionService,
    TargetPositionDirection,
    TargetPositionKnotInput,
    TargetPositionService,
)


NOW = datetime(2026, 7, 21, 1, 30, tzinfo=UTC)
SOFTWARE = SoftwareIdentity("test", "abc123", WorktreeState.CLEAN)


def _system(path: Path, *, decision_store=None):
    runs = SQLiteRunHistoryRepository(path)
    runs.initialize()
    source_store = SQLiteStandardizedPriceStateStore(path)
    target_store = SQLiteTargetPositionStore(path)
    durable_decisions = SQLiteTargetAdjustmentDecisionStore(path)
    for store in (source_store, target_store, durable_decisions):
        store.initialize()
    run_service = AlgorithmRunService(runs, clock=lambda: NOW)
    source_service = StandardizedPriceStateService(
        source_store, run_service, SOFTWARE, clock=lambda: NOW
    )
    target_service = TargetPositionService(
        target_store, run_service, SOFTWARE, clock=lambda: NOW
    )
    linked_service = LinkedTargetPositionService(
        target_store, run_service, SOFTWARE, clock=lambda: NOW
    )
    linked_coordinator = StandardizedStateTargetPositionPreviewCoordinator(
        source_store,
        target_store,
        linked_service,
        run_service,
        SOFTWARE,
        clock=lambda: NOW,
    )
    effective_store = decision_store or durable_decisions
    decision_service = TargetAdjustmentDecisionService(
        effective_store, SOFTWARE, clock=lambda: NOW
    )
    decision_coordinator = TargetAdjustmentDecisionPreviewCoordinator(
        source_store,
        target_store,
        effective_store,
        durable_decisions,
        decision_service,
        run_service,
        SOFTWARE,
        clock=lambda: NOW,
    )
    return (
        source_service,
        target_service,
        linked_coordinator,
        decision_coordinator,
        source_store,
        target_store,
        durable_decisions,
        runs,
    )


def _prepare(system, *, current="60"):
    source_service, target_service, linked, *_rest = system
    source_definition = source_service.create_definition(
        CreateStandardizedPriceStateDefinitionCommand(
            "Manual state", "Exact source", "SESSION", "S-DEF", "tester"
        )
    )
    source = source_service.preview(
        PreviewStandardizedPriceStateCommand(
            source_definition.definition_id,
            "AAPL",
            "90",
            "100",
            "10",
            NOW,
            "Exact source",
            "SESSION",
            "S-PREVIEW",
            "tester",
        )
    )
    target_definition = target_service.create_definition(
        CreateTargetPositionDefinitionCommand(
            "Bounded curve",
            "Exact target",
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
            "T-DEF",
            "tester",
        )
    )
    linked_outcome = linked.preview(
        LinkedTargetPositionPreviewCommand(
            source.calculation_id,
            target_definition.definition_id,
            "100",
            current,
            "Exact Phase 5C source",
            "SESSION",
            f"LINK-{current}",
            "tester",
        )
    )
    link = system[5].get_standardized_state_link(linked_outcome.operation_id)
    return source, target_definition, linked_outcome, link


def _decision_command(link_id, *, operation_id=None, reason="Exact target adjustment"):
    return TargetAdjustmentDecisionPreviewCommand(
        link_id, reason, "SESSION", "DECISION", "tester", operation_id
    )


def test_completed_target_adjustment_persists_exact_intent_and_run_links(tmp_path: Path):
    system = _system(tmp_path / "central.sqlite3")
    source, target_definition, linked_outcome, link = _prepare(system)

    outcome = system[3].preview(_decision_command(link.link_id))

    assert outcome.status is TargetAdjustmentDecisionStatus.INTENT_CREATED
    result = system[6].get_target_adjustment_result(outcome.decision_result_id)
    assert result.action is DecisionAction.INCREASE
    assert result.source.target_position_link_id == link.link_id
    assert result.source.current_position_value_usd == 60
    assert result.source.target_position_value_usd == 70
    assert result.source.adjustment_value_usd == 10
    assert result.intents[0].desired_change_usd == 10
    assert result.intents[0].requested_notional_usd == 10
    source_link = system[6].get_target_adjustment_source_link(result.decision_result_id)
    assert source_link.linked_parent_run_id == linked_outcome.parent_run_id
    assert source_link.target_child_run_id == linked_outcome.child_run_id
    assert source_link.standardized_state_run_id == source.run_id
    assert system[6].list_target_adjustment_results(
        TargetAdjustmentDecisionQuery(
            symbol="aapl",
            action=DecisionAction.INCREASE,
            status=TargetAdjustmentDecisionStatus.INTENT_CREATED,
            target_definition_id=target_definition.definition_id,
            target_definition_version=1,
            target_position_link_id=link.link_id,
        )
    ) == (result,)

    run = system[7].get_run(outcome.run_id)
    detail = system[7].get_run_detail(outcome.run_id)
    assert run.run_type is AlgorithmRunType.TARGET_ADJUSTMENT_DECISION_PREVIEW
    assert run.parent_run_id == linked_outcome.parent_run_id
    assert run.status is AlgorithmRunStatus.COMPLETED
    assert [stage.name.value for stage in detail.stages] == ["target_position", "decision"]
    relationships = {(item.relationship_type.value, item.run_id) for item in detail.relationships}
    assert ("parent", linked_outcome.parent_run_id) in relationships
    assert ("source", linked_outcome.child_run_id) in relationships
    assert ("source", source.run_id) in relationships
    operation_artifact = next(
        item for item in detail.artifacts
        if item.artifact_type == "target_adjustment_decision_operation"
    )
    assert operation_artifact.children[0].children[0].artifact_type == "target_adjustment_trade_intent"

    reopened = SQLiteTargetAdjustmentDecisionStore(tmp_path / "central.sqlite3")
    reopened.initialize()
    assert reopened.get_target_adjustment_result(result.decision_result_id) == result
    assert reopened.get_target_adjustment_source_link(result.decision_result_id) == source_link


def test_exact_zero_is_durable_hold_without_intent(tmp_path: Path):
    system = _system(tmp_path / "central.sqlite3")
    _source, _definition, _linked_outcome, link = _prepare(system, current="70")

    outcome = system[3].preview(_decision_command(link.link_id))
    result = system[6].get_target_adjustment_result(outcome.decision_result_id)

    assert outcome.status is TargetAdjustmentDecisionStatus.HOLD
    assert result.action is DecisionAction.HOLD
    assert result.intents == ()
    with sqlite3.connect(tmp_path / "central.sqlite3") as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM target_adjustment_trade_intents"
        ).fetchone()[0] == 0


def test_idempotency_conflict_and_missing_link_attempts_are_durable(tmp_path: Path):
    system = _system(tmp_path / "central.sqlite3")
    _source, _definition, _linked_outcome, link = _prepare(system)
    operation_id = uuid4()
    command = _decision_command(link.link_id, operation_id=operation_id)

    first = system[3].preview(command)
    retry = system[3].preview(command)
    conflict = system[3].preview(replace(command, reason="Different reason"))
    missing = system[3].preview(_decision_command(uuid4()))

    assert retry.run_id == first.run_id
    assert retry.decision_result_id == first.decision_result_id
    assert "no new Run" in retry.summary
    assert conflict.status is TargetAdjustmentDecisionStatus.INVALID_INPUT
    assert missing.status is TargetAdjustmentDecisionStatus.INVALID_INPUT
    attempts = system[6].list_target_adjustment_operations()
    assert len(attempts) == 3
    assert sum(item.operation_id == operation_id for item in attempts) == 2
    assert system[7].get_run(conflict.run_id).status is AlgorithmRunStatus.INVALID_INPUT
    assert system[7].get_run(missing.run_id).status is AlgorithmRunStatus.INVALID_INPUT


def test_store_failure_rolls_back_result_and_preserves_failed_attempt(tmp_path: Path):
    database = tmp_path / "central.sqlite3"
    durable = SQLiteTargetAdjustmentDecisionStore(database)

    class FailingCompletedStore:
        def __getattr__(self, name):
            return getattr(durable, name)

        def save_completed(self, result, operation, source_link):
            raise RuntimeError("simulated transaction failure")

    system = _system(database, decision_store=FailingCompletedStore())
    _source, _definition, _linked_outcome, link = _prepare(system)

    outcome = system[3].preview(_decision_command(link.link_id))

    assert outcome.status is TargetAdjustmentDecisionStatus.FAILED
    assert durable.list_target_adjustment_results() == ()
    attempts = durable.list_target_adjustment_operations()
    assert len(attempts) == 1
    assert attempts[0].status is TargetAdjustmentDecisionStatus.FAILED
    assert system[7].get_run(outcome.run_id).status is AlgorithmRunStatus.FAILED


def _create_v8_database(path: Path) -> None:
    with sqlite3.connect(path) as connection:
        for version, schema in (
            (1, _SCHEMA_V1), (2, _SCHEMA_V2), (3, _SCHEMA_V3),
            (4, _SCHEMA_V4), (5, _SCHEMA_V5), (6, _SCHEMA_V6),
            (7, _SCHEMA_V7), (8, _SCHEMA_V8),
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


def test_v8_to_v9_migration_backs_up_preserves_and_creates_no_decision_rows(tmp_path: Path):
    database = tmp_path / "central.sqlite3"
    backups = tmp_path / "backups"
    _create_v8_database(database)

    CentralSQLiteDatabase(database, backup_directory=backups).initialize()

    backup_files = tuple(backups.glob("*.sqlite3"))
    assert len(backup_files) == 1
    assert ".schema-v8-to-v13." in backup_files[0].name
    with sqlite3.connect(backup_files[0]) as backup:
        assert backup.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 8
        assert backup.execute("SELECT COUNT(*) FROM market_bars").fetchone()[0] == 1
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 13
        assert connection.execute("SELECT COUNT(*) FROM market_bars").fetchone()[0] == 1
        for table in (
            "target_adjustment_decision_operations",
            "target_adjustment_decision_results",
            "target_adjustment_trade_intents",
            "target_adjustment_decision_source_links",
        ):
            assert connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []


def test_failed_v9_migration_rolls_back_to_intact_v8(tmp_path: Path, monkeypatch):
    database = tmp_path / "central.sqlite3"
    _create_v8_database(database)
    broken = dict(sqlite_database._MIGRATIONS)
    broken[9] = ("intentionally broken v9", _SCHEMA_V9 + "\nINVALID SQL;")
    monkeypatch.setattr(sqlite_database, "_MIGRATIONS", broken)

    with pytest.raises(sqlite3.Error):
        CentralSQLiteDatabase(database, backup_directory=tmp_path / "backups").initialize()

    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 8
        assert connection.execute("SELECT COUNT(*) FROM market_bars").fetchone()[0] == 1
        assert connection.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='target_adjustment_decision_results'"
        ).fetchone()[0] == 0
