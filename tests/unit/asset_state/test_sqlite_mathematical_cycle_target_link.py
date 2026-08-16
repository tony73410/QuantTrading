from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from quant_trading.asset_state import (
    CreateMathematicalCycleDefinitionCommand,
    MathematicalCyclePromotionCommand,
    MathematicalCycleStateService,
)
from quant_trading.orchestration import (
    CycleTargetPositionResearchCoordinator,
    MathematicalCyclePromotionCoordinator,
    MathematicalCycleTargetPositionLinkCoordinator,
)
from quant_trading.persistence import (
    CentralSQLiteDatabase,
    SQLiteCycleTargetPositionStore,
    SQLiteMathematicalCycleStateStore,
    SQLiteMathematicalCycleTargetLinkStore,
)
from quant_trading.persistence import sqlite_database
from quant_trading.run_history import AlgorithmRunService, AlgorithmRunType
from quant_trading.target_position import (
    CreateAssetCycleTargetConfigurationCommand,
    CreateCycleTargetFormulaCommand,
    CycleTargetPositionService,
    MathematicalCycleTargetLinkStatus,
    MathematicalCycleTargetPreviewCommand,
)

from test_sqlite_mathematical_cycle_state import _p28


def _environment(path: Path, *, link_store_class=SQLiteMathematicalCycleTargetLinkStore):
    reversal, runs, software, p28 = _p28(path)
    state_store = SQLiteMathematicalCycleStateStore(path)
    state_service = MathematicalCycleStateService(
        state_store, AlgorithmRunService(runs), software,
        clock=lambda: p28.completed_at_utc + timedelta(days=5),
    )
    definition_operation = state_service.save_definition(
        CreateMathematicalCycleDefinitionCommand(
            uuid4(), "session", "p37-definition", None, "pytest", "P39 fixture",
        )
    )
    definition = state_store.get_definition(definition_operation.definition_id)
    state_operation = MathematicalCyclePromotionCoordinator(reversal, state_service).promote(
        MathematicalCyclePromotionCommand(
            uuid4(), "session", "p37-promotion", definition.definition_id,
            definition.definition_version, p28.result.result_id, p28.run_id, "AAPL",
            "P39 explicit stream", None, None, "pytest", "P39 exact state fixture",
        )
    )
    detail = state_store.get_stream_detail(state_operation.stream_id)

    target_store = SQLiteCycleTargetPositionStore(path)
    target_service = CycleTargetPositionService(
        target_store, AlgorithmRunService(runs), software,
        clock=lambda: p28.completed_at_utc + timedelta(days=6),
    )
    formula_operation = target_service.save_formula_definition(
        CreateCycleTargetFormulaCommand(
            uuid4(), "session", "p29-formula", "P29", "P39 fixture", "pytest",
        )
    )
    formula = target_store.get_formula_definition(formula_operation.resolved_formula_definition_id)
    configuration_operation = target_service.save_configuration(
        CreateAssetCycleTargetConfigurationCommand(
            uuid4(), "session", "p29-config", "AAPL", formula.formula_definition_id,
            formula.definition_version, "0.1", "0.5", "0.9", "0.05", "2", "4",
            "P39 fixture", "pytest",
        )
    )
    configuration = target_store.get_configuration(configuration_operation.resolved_configuration_id)
    target_runner = CycleTargetPositionResearchCoordinator(reversal, target_service)
    link_store = link_store_class(path)
    coordinator = MathematicalCycleTargetPositionLinkCoordinator(
        state_store, target_store, target_runner, link_store,
        AlgorithmRunService(runs), software,
        clock=lambda: p28.completed_at_utc + timedelta(days=7),
    )
    command = MathematicalCycleTargetPreviewCommand(
        uuid4(), uuid4(), state_operation.operation_id, state_operation.run_id,
        state_operation.stream_id, state_operation.latest_snapshot_id,
        configuration.configuration_id, configuration.configuration_version,
        "100000", "50000", "session", "p39-preview",
        p28.completed_at_utc + timedelta(days=7), "pytest", "explicit P37 to P29",
    )
    return coordinator, command, link_store, target_store, state_store, runs, detail


def test_exact_p37_terminal_state_delegates_unchanged_p29_and_reloads_after_restart(tmp_path: Path):
    path = tmp_path / "central.sqlite3"
    coordinator, command, store, targets, _, runs, detail = _environment(path)

    preflight = coordinator.prepare(command)
    operation = coordinator.preview(command)
    retry = coordinator.preview(command)
    conflict = coordinator.preview(MathematicalCycleTargetPreviewCommand(
        command.operation_id, command.target_operation_id, command.state_operation_id,
        command.state_run_id, command.stream_id, command.latest_snapshot_id,
        command.configuration_id, command.configuration_version,
        command.research_capital_basis_usd, "49000", command.session_id,
        "p39-conflict", command.requested_at_utc, command.created_by, command.reason,
    ))

    assert "exact P37 operation" in preflight.summary
    assert operation.status is MathematicalCycleTargetLinkStatus.COMPLETED
    assert retry == operation
    assert conflict.status is MathematicalCycleTargetLinkStatus.INVALID_INPUT
    assert operation.link_id is not None
    link = SQLiteMathematicalCycleTargetLinkStore(path).get_link(operation.link_id)
    assert link is not None
    assert link.snapshot_id == detail.stream.latest_snapshot_id
    assert link.source_step_id == detail.snapshots[-1].source_step_id
    assert targets.get_result(link.target_result_id) is not None
    assert len(targets.list_results()) == 1
    assert SQLiteMathematicalCycleTargetLinkStore(path).get_operation_by_operation_id(command.operation_id) == operation
    run_detail = runs.get_run_detail(operation.bridge_run_id)
    assert run_detail.summary.run.run_type is AlgorithmRunType.MATHEMATICAL_CYCLE_TARGET_POSITION_LINK
    assert run_detail.summary.run.parent_run_id == command.state_run_id
    assert [stage.name.value for stage in run_detail.stages] == ["state", "target_position"]
    assert any(
        item.artifact_type == "mathematical_cycle_target_link_operation"
        and item.children for item in run_detail.artifacts
    )
    related = {item.run_id for item in run_detail.relationships}
    assert {command.state_run_id, link.target_run_id, link.source_run_id} <= related
    assert any(
        item.run_id == operation.bridge_run_id
        for item in runs.get_run_detail(link.target_run_id).relationships
    )
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 23
        assert connection.execute("SELECT COUNT(*) FROM mathematical_cycle_target_link_operations").fetchone()[0] == 2
        assert connection.execute("SELECT COUNT(*) FROM mathematical_cycle_target_position_links").fetchone()[0] == 1
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def test_exact_id_mismatch_fails_closed_without_p29_result(tmp_path: Path):
    path = tmp_path / "central.sqlite3"
    coordinator, command, store, targets, _, runs, _ = _environment(path)
    bad = MathematicalCycleTargetPreviewCommand(
        command.operation_id, command.target_operation_id, command.state_operation_id,
        command.state_run_id, command.stream_id, uuid4(), command.configuration_id,
        command.configuration_version, command.research_capital_basis_usd,
        command.current_position_value_usd, command.session_id, command.request_id,
        command.requested_at_utc, command.created_by, command.reason,
    )

    operation = coordinator.preview(bad)

    assert operation.status is MathematicalCycleTargetLinkStatus.INVALID_INPUT
    assert operation.error_code.endswith("SOURCE-001")
    assert len(targets.list_results()) == 0
    assert store.list_links() == ()
    assert runs.get_run_detail(operation.bridge_run_id).summary.run.status.value == "invalid_input"


def test_p29_success_then_link_write_failure_is_durable_and_exact_retry_recovers(tmp_path: Path):
    path = tmp_path / "central.sqlite3"

    class FailOnce(SQLiteMathematicalCycleTargetLinkStore):
        failed = False

        def save_success(self, operation, link):
            if not self.failed:
                self.failed = True
                raise RuntimeError("injected P39 accepted-link write failure")
            return super().save_success(operation, link)

    coordinator, command, store, targets, _, _, _ = _environment(path, link_store_class=FailOnce)
    failed = coordinator.preview(command)
    recovered = coordinator.preview(command)

    assert failed.status is MathematicalCycleTargetLinkStatus.FAILED
    assert failed.error_code.endswith("STORAGE-001")
    assert len(targets.list_results()) == 1
    assert recovered.status is MathematicalCycleTargetLinkStatus.COMPLETED
    assert recovered.attempt_id != failed.attempt_id
    assert len(targets.list_results()) == 1
    assert len(store.list_operations()) == 2
    assert len(store.list_links()) == 1


def test_v22_to_v23_migration_is_additive_zero_backfill_and_failure_rolls_back(tmp_path: Path):
    path = tmp_path / "central.sqlite3"
    now = datetime(2026, 8, 15, 12, 0, tzinfo=UTC)
    with sqlite3.connect(path) as connection:
        for version in range(1, 23):
            connection.executescript(sqlite_database._MIGRATIONS[version][1])
            connection.execute(
                "INSERT INTO schema_migrations VALUES (?,?,?)",
                (version, now.isoformat(), f"fixture {version}"),
            )
        connection.execute(
            """INSERT INTO market_bars VALUES
               ('AAPL','2026-01-02T00:00:00+00:00','1Day','raw','iex',
                '100','101','99','100',100,NULL,NULL,'fixture','2026-01-03T00:00:00+00:00')"""
        )
        connection.commit()

    CentralSQLiteDatabase(path).initialize()
    backups = tuple((tmp_path / "backups").glob("*.sqlite3"))
    assert len(backups) == 1 and ".schema-v22-to-v23." in backups[0].name
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 23
        assert connection.execute("SELECT COUNT(*) FROM market_bars").fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM mathematical_cycle_target_link_operations").fetchone()[0] == 0
        assert connection.execute("SELECT COUNT(*) FROM mathematical_cycle_target_position_links").fetchone()[0] == 0
        assert len(sqlite_database.expected_schema_tables()) == 139
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"

    rollback = tmp_path / "rollback.sqlite3"
    with sqlite3.connect(rollback) as connection:
        for version in range(1, 23):
            connection.executescript(sqlite_database._MIGRATIONS[version][1])
            connection.execute(
                "INSERT INTO schema_migrations VALUES (?,?,?)",
                (version, now.isoformat(), f"fixture {version}"),
            )
        connection.commit()
        try:
            connection.executescript(
                "BEGIN IMMEDIATE; CREATE TABLE p39_partial(id TEXT); SELECT * FROM missing_table;"
            )
        except sqlite3.OperationalError:
            connection.rollback()
        assert connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 22
        assert connection.execute("SELECT 1 FROM sqlite_master WHERE name='p39_partial'").fetchone() is None
