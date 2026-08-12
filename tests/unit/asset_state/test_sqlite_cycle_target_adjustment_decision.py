from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from uuid import uuid4

import pytest

from quant_trading.algorithm_control.cycle_target_adjustment_decision_export import (
    CycleTargetAdjustmentDecisionExportService,
)
from quant_trading.decision import (
    CycleTargetAdjustmentDecisionService,
    CycleTargetAdjustmentDecisionReplayService,
    CycleTargetAdjustmentOperationStatus,
    CycleTargetAdjustmentPreviewCommand,
    CycleTargetAdjustmentQuery,
    CycleTargetAdjustmentResultStatus,
    DecisionAction,
)
from quant_trading.orchestration import (
    CycleTargetAdjustmentDecisionPreviewCoordinator,
    CycleTargetPositionResearchCoordinator,
)
from quant_trading.persistence import (
    CentralSQLiteDatabase,
    SQLiteCycleTargetAdjustmentDecisionStore,
    SQLiteCycleTargetPositionStore,
)
from quant_trading.persistence import sqlite_database
from quant_trading.run_history import AlgorithmRunService, AlgorithmRunType
from quant_trading.target_position import (
    CreateAssetCycleTargetConfigurationCommand,
    CreateCycleTargetFormulaCommand,
    CycleTargetPositionService,
    CycleTargetPreviewCommand,
)

from test_sqlite_cycle_target_position import NOW, _p28


def _system(path: Path):
    reversal, runs, p28, software = _p28(path)
    targets = SQLiteCycleTargetPositionStore(CentralSQLiteDatabase(path))
    target_service = CycleTargetPositionService(
        targets, AlgorithmRunService(runs), software, clock=lambda: NOW
    )
    formula_operation = target_service.save_formula_definition(
        CreateCycleTargetFormulaCommand(
            uuid4(), "session", "p31-formula", "P29 v1", "P31 fixture", "pytest"
        )
    )
    formula = targets.get_formula_definition(
        formula_operation.resolved_formula_definition_id
    )
    configuration_operation = target_service.save_configuration(
        CreateAssetCycleTargetConfigurationCommand(
            uuid4(), "session", "p31-config", "AAPL",
            formula.formula_definition_id, formula.definition_version,
            "0.1", "0.5", "0.9", "0.05", "2", "4", "P31 fixture", "pytest",
        )
    )
    configuration = targets.get_configuration(
        configuration_operation.resolved_configuration_id
    )
    step = p28.result.daily_steps[-1]
    target_coordinator = CycleTargetPositionResearchCoordinator(
        reversal, target_service
    )

    def create_p29(current: str, operation_id=None):
        return target_coordinator.preview(CycleTargetPreviewCommand(
            operation_id or uuid4(), "session", f"p29-{uuid4().hex}",
            configuration.configuration_id, configuration.configuration_version,
            p28.result.result_id, step.step_id, p28.run_id,
            "100000", current, "P31 fixture", "pytest",
        ))

    p29 = create_p29("50000")
    assert p29.result is not None
    decisions = SQLiteCycleTargetAdjustmentDecisionStore(path)
    decisions.initialize()
    decision_service = CycleTargetAdjustmentDecisionService(
        decisions, software, clock=lambda: NOW
    )
    coordinator = CycleTargetAdjustmentDecisionPreviewCoordinator(
        targets, decisions, decisions, decision_service,
        AlgorithmRunService(runs), software, clock=lambda: NOW,
    )
    return decisions, runs, p28, p29, create_p29, coordinator


def _command(result, *, operation_id=None, reason="P31 fixture"):
    return CycleTargetAdjustmentPreviewCommand(
        source_result_id=result.result.result_id,
        source_run_id=result.run_id,
        reason=reason,
        session_id="session",
        request_id=f"p31-{uuid4().hex}",
        created_by="pytest",
        operation_id=operation_id,
    )


def test_p31_persists_exact_intent_chain_reload_export_and_run_history(tmp_path: Path):
    path = tmp_path / "central.sqlite3"
    store, runs, p28, p29, _, coordinator = _system(path)
    command = _command(p29)
    before_runs = len(runs.list_runs())
    preflight = coordinator.preflight(command)
    assert preflight.source.source_result_id == p29.result.result_id
    assert store.list_cycle_target_adjustment_operations() == ()
    assert len(runs.list_runs()) == before_runs
    outcome = coordinator.preview(command)

    assert outcome.operation_status is CycleTargetAdjustmentOperationStatus.COMPLETED
    result = store.get_cycle_target_adjustment_result(outcome.decision_result_id)
    assert result is not None
    assert result.source.source_result_id == p29.result.result_id
    assert result.source.source_run_id == p29.run_id
    assert result.source.adjustment_value_usd == (
        result.source.target_position_value_usd
        - result.source.current_position_value_usd
    )
    assert result.action is DecisionAction.INCREASE
    assert result.status is CycleTargetAdjustmentResultStatus.INTENT_CREATED
    assert len(result.intents) == 1
    assert result.intents[0].requested_notional_usd == abs(
        result.source.adjustment_value_usd
    )
    assert not result.execution_allowed and not result.live_allowed
    assert store.list_cycle_target_adjustment_results(
        CycleTargetAdjustmentQuery(symbol="AAPL", action=DecisionAction.INCREASE)
    ) == (result,)
    assert store.get_cycle_target_adjustment_source_link(result.decision_result_id)
    assert store.get_cycle_target_adjustment_intent(result.intents[0].intent_id) == result.intents[0]

    detail = runs.get_run_detail(result.run_id)
    assert detail.summary.run.run_type is AlgorithmRunType.CYCLE_TARGET_DECISION_PREVIEW
    assert detail.summary.run.parent_run_id == p29.run_id
    assert [stage.name.value for stage in detail.stages] == ["target_position", "decision"]
    assert any(item.run_id == p29.run_id for item in detail.relationships)
    assert any(item.run_id == p28.run_id for item in detail.relationships)
    assert any(
        item.artifact_type == "cycle_target_adjustment_decision_operation"
        and item.children and item.children[0].children
        for item in detail.artifacts
    )
    assert any(item.run_id == result.run_id for item in runs.get_run_detail(p29.run_id).relationships)

    export = CycleTargetAdjustmentDecisionExportService()
    json_path = export.export_json(result, tmp_path / "result.json")
    csv_path = export.export_csv(result, tmp_path / "result.csv")
    assert json.loads(json_path.read_text(encoding="utf-8"))["decision_result_id"] == str(result.decision_result_id)
    assert "signed_difference_usd" in csv_path.read_text(encoding="utf-8-sig")

    reloaded = SQLiteCycleTargetAdjustmentDecisionStore(path)
    reloaded.initialize()
    assert reloaded.get_cycle_target_adjustment_result(result.decision_result_id) == result
    replay = CycleTargetAdjustmentDecisionReplayService(reloaded)
    assert replay.recalculate(result.decision_result_id) == result
    assert replay.verify(result.decision_result_id).matched is True
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 19
        assert connection.execute("SELECT COUNT(*) FROM cycle_target_decision_results").fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM cycle_target_decision_trade_intents").fetchone()[0] == 1
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def test_p31_hold_idempotency_conflict_missing_source_and_storage_failure_are_durable(tmp_path: Path):
    path = tmp_path / "central.sqlite3"
    store, runs, _, p29, create_p29, coordinator = _system(path)
    operation_id = uuid4()
    command = _command(p29, operation_id=operation_id)
    first = coordinator.preview(command)
    retry = coordinator.preview(command)
    assert retry.attempt_id == first.attempt_id
    assert retry.run_id == first.run_id
    assert retry.decision_result_id == first.decision_result_id

    conflict = coordinator.preview(_command(
        p29, operation_id=operation_id, reason="different P31 input"
    ))
    assert conflict.operation_status is CycleTargetAdjustmentOperationStatus.INVALID_INPUT
    assert runs.get_run_detail(conflict.run_id).summary.run.parent_run_id == p29.run_id

    missing = coordinator.preview(CycleTargetAdjustmentPreviewCommand(
        uuid4(), uuid4(), "missing source", "session", "p31-missing", "pytest"
    ))
    assert missing.operation_status is CycleTargetAdjustmentOperationStatus.INVALID_INPUT
    attempts = store.list_cycle_target_adjustment_operations(
        CycleTargetAdjustmentQuery(limit=50)
    )
    assert {item.attempt_id for item in attempts} >= {
        first.attempt_id, conflict.attempt_id, missing.attempt_id,
    }

    zero_p29 = create_p29(str(p29.result.target_position_value_usd))
    assert zero_p29.result.adjustment_value_usd == 0
    hold = coordinator.preview(_command(zero_p29))
    hold_result = store.get_cycle_target_adjustment_result(hold.decision_result_id)
    assert hold_result.status is CycleTargetAdjustmentResultStatus.HOLD
    assert hold_result.action is DecisionAction.HOLD
    assert hold_result.intents == ()

    class FailCompleted(SQLiteCycleTargetAdjustmentDecisionStore):
        def save_completed(self, result, operation, source_link):
            raise sqlite3.DatabaseError("injected completed transaction failure")

    failing_store = FailCompleted(path)
    failing = CycleTargetAdjustmentDecisionPreviewCoordinator(
        coordinator._cycle_targets,
        failing_store,
        failing_store,
        CycleTargetAdjustmentDecisionService(
            failing_store, coordinator._software, clock=lambda: NOW
        ),
        coordinator._runs,
        coordinator._software,
        clock=lambda: NOW,
    )
    failed = failing.preview(_command(p29))
    assert failed.operation_status is CycleTargetAdjustmentOperationStatus.FAILED
    failed_attempt = store.list_cycle_target_adjustment_operations(
        CycleTargetAdjustmentQuery(operation_status=CycleTargetAdjustmentOperationStatus.FAILED)
    )[0]
    assert failed_attempt.attempt_id == failed.attempt_id
    assert failed_attempt.decision_result_id is None and failed_attempt.intent_id is None
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM cycle_target_decision_results").fetchone()[0] == 2
        assert connection.execute("SELECT COUNT(*) FROM cycle_target_decision_trade_intents").fetchone()[0] == 1
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []


def test_v18_to_v19_migration_is_backed_up_additive_and_zero_backfill(tmp_path: Path):
    path = tmp_path / "central.sqlite3"
    with sqlite3.connect(path) as connection:
        for version in range(1, 19):
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
    assert ".schema-v18-to-v19." in backups[0].name
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 19
        assert connection.execute("SELECT COUNT(*) FROM market_bars").fetchone()[0] == 1
        for table in (
            "cycle_target_decision_operation_attempts",
            "cycle_target_decision_results",
            "cycle_target_decision_trade_intents",
            "cycle_target_decision_source_links",
        ):
            assert connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0
        assert len(sqlite_database.expected_schema_tables()) == 120
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def test_failed_v19_migration_restores_intact_v18_database(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    path = tmp_path / "central.sqlite3"
    with sqlite3.connect(path) as connection:
        for version in range(1, 19):
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
    broken = dict(sqlite_database._MIGRATIONS)
    broken[19] = ("broken P31 migration", "CREATE TABL definitely_invalid")
    monkeypatch.setattr(sqlite_database, "_MIGRATIONS", broken)

    with pytest.raises(sqlite3.DatabaseError):
        CentralSQLiteDatabase(path).initialize()

    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 18
        assert connection.execute("SELECT COUNT(*) FROM market_bars").fetchone()[0] == 1
        assert connection.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' "
            "AND name='cycle_target_decision_results'"
        ).fetchone()[0] == 0
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
