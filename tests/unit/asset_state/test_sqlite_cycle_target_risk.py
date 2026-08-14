from __future__ import annotations

import json
import sqlite3
from dataclasses import replace
from pathlib import Path
from uuid import uuid4

import pytest

from quant_trading.algorithm_control.cycle_target_risk_export import CycleTargetRiskExportService
from quant_trading.application_settings import ExecutionEnvironment
from quant_trading.orchestration import CycleTargetRiskReviewCoordinator
from quant_trading.persistence import CentralSQLiteDatabase, SQLiteCycleTargetRiskStore
from quant_trading.persistence import sqlite_database
from quant_trading.risk import (
    CycleTargetRiskQuery,
    CycleTargetRiskReplayService,
    CycleTargetRiskReviewCommand,
    CycleTargetRiskService,
    CycleTargetRiskStatus,
    RiskSafetyStateSnapshot,
)
from quant_trading.run_history import AlgorithmRunService, AlgorithmRunType

from test_sqlite_cycle_target_adjustment_decision import NOW, _command, _system


def _safe(software):
    return RiskSafetyStateSnapshot(
        uuid4(), ExecutionEnvironment.ALPACA_PAPER, False, False, True, False,
        "application-role-settings@1", software.package_version,
        software.source_revision, software.worktree_state.value, NOW,
    )


def _p33(path: Path, *, unsafe: bool = False):
    decisions, runs, p28, p29, _, p31 = _system(path)
    p31_outcome = p31.preview(_command(p29))
    result = decisions.get_cycle_target_adjustment_result(p31_outcome.decision_result_id)
    intent = result.intents[0]
    store = SQLiteCycleTargetRiskStore(path); store.initialize()
    software = p31._software
    safety = _safe(software)
    if unsafe:
        safety = replace(safety, automatic_submission_enabled=True)
    coordinator = CycleTargetRiskReviewCoordinator(
        decisions, store, store, CycleTargetRiskService(store, software, clock=lambda: NOW),
        AlgorithmRunService(runs), software, lambda: safety, clock=lambda: NOW,
    )
    command = CycleTargetRiskReviewCommand(
        intent.intent_id, result.decision_result_id, result.run_id, "P33 fixture",
        "session", "p33-request", "pytest", NOW, uuid4(),
    )
    return store, runs, p28, p29, result, intent, coordinator, command


def test_p33_preflight_review_reload_replay_export_and_run_history(tmp_path: Path):
    path = tmp_path / "central.sqlite3"
    store, runs, p28, p29, p31, intent, coordinator, command = _p33(path)
    before_runs = len(runs.list_runs())
    preflight = coordinator.preflight(command)
    assert preflight.accepted and preflight.source.intent_id == intent.intent_id
    assert store.list_cycle_target_risk_operations() == ()
    assert len(runs.list_runs()) == before_runs

    outcome = coordinator.review(command)
    assert outcome.status is CycleTargetRiskStatus.MANUAL_REVIEW_REQUIRED
    result = store.get_cycle_target_risk_result(outcome.review_result_id)
    assert result is not None
    assert result.source.decision_result_id == p31.decision_result_id
    assert result.source.source_result_id == p29.result.result_id
    assert result.source.source_reversal_result_id == p28.result.result_id
    assert [item.rule_id for item in result.rules] == [
        "SOURCE_CHAIN_INTEGRITY", "NON_EXECUTION_SAFETY_STATE",
        "NUMERICAL_RISK_POLICY_AVAILABILITY",
    ]
    assert result.approved_notional_usd is None and result.risk_approved_intent_id is None
    assert not result.execution_allowed and not result.live_allowed
    assert store.list_cycle_target_risk_results(CycleTargetRiskQuery(symbol="AAPL")) == (result,)
    assert store.get_cycle_target_risk_source_link(result.review_result_id)

    retry = coordinator.review(command)
    assert retry.attempt_id == outcome.attempt_id and retry.run_id == outcome.run_id
    assert len(runs.list_runs()) == before_runs + 1

    replay = CycleTargetRiskReplayService(store).replay(result.review_result_id)
    assert replay.matched and replay.differences == ()
    exporter = CycleTargetRiskExportService()
    json_path = exporter.export_json(result, tmp_path / "p33.json")
    csv_path = exporter.export_csv(result, tmp_path / "p33.csv")
    assert json.loads(json_path.read_text(encoding="utf-8"))["review_result_id"] == str(result.review_result_id)
    assert "approved_notional_usd" in csv_path.read_text(encoding="utf-8-sig")

    reloaded = SQLiteCycleTargetRiskStore(path); reloaded.initialize()
    assert reloaded.get_cycle_target_risk_result(result.review_result_id) == result
    detail = runs.get_run_detail(result.run_id)
    assert detail.summary.run.run_type is AlgorithmRunType.CYCLE_TARGET_RISK_REVIEW
    assert detail.summary.run.parent_run_id == p31.run_id
    assert [stage.name.value for stage in detail.stages] == ["decision", "risk"]
    related = {item.run_id for item in detail.relationships}
    assert {p31.run_id, p29.run_id, p28.run_id} <= related
    assert any(item.artifact_type == "cycle_target_risk_operation" and item.children for item in detail.artifacts)
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 22
        assert connection.execute("SELECT COUNT(*) FROM cycle_target_risk_review_results").fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM cycle_target_risk_rule_results").fetchone()[0] == 3
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def test_p33_invalid_exact_ids_are_durable_and_write_no_accepted_result(tmp_path: Path):
    path = tmp_path / "central.sqlite3"
    store, runs, _, _, p31, intent, coordinator, command = _p33(path)
    invalid = CycleTargetRiskReviewCommand(
        intent.intent_id, uuid4(), p31.run_id, "invalid exact result", "session",
        "p33-invalid", "pytest", NOW,
    )
    outcome = coordinator.review(invalid)
    assert outcome.status is CycleTargetRiskStatus.INVALID_INPUT
    attempts = store.list_cycle_target_risk_operations(CycleTargetRiskQuery(status=CycleTargetRiskStatus.INVALID_INPUT))
    assert attempts[0].attempt_id == outcome.attempt_id
    assert store.list_cycle_target_risk_results() == ()
    detail = runs.get_run_detail(outcome.run_id)
    assert detail.summary.run.status.value == "invalid_input"


def test_p33_unsafe_runtime_blocks_without_approved_output(tmp_path: Path):
    path = tmp_path / "central.sqlite3"
    store, _, _, _, _, _, coordinator, command = _p33(path, unsafe=True)
    outcome = coordinator.review(command)
    assert outcome.status is CycleTargetRiskStatus.BLOCKED
    result = store.get_cycle_target_risk_result(outcome.review_result_id)
    assert result is not None
    assert [item.rule_id for item in result.rules] == [
        "SOURCE_CHAIN_INTEGRITY", "NON_EXECUTION_SAFETY_STATE"
    ]
    assert result.rules[-1].stop_processing
    assert result.approved_notional_usd is None
    assert result.risk_approved_intent_id is None
    assert not result.execution_allowed and not result.live_allowed


def test_p33_rejects_tampered_exact_p29_configuration(tmp_path: Path):
    path = tmp_path / "central.sqlite3"
    store, _, _, p29, _, _, coordinator, command = _p33(path)
    with sqlite3.connect(path) as connection:
        connection.execute(
            "UPDATE cycle_target_asset_configurations SET constraint_fingerprint=? WHERE configuration_id=?",
            ("tampered-p29-configuration", str(p29.result.configuration_id)),
        )
        connection.commit()

    outcome = coordinator.review(command)
    assert outcome.status is CycleTargetRiskStatus.FAILED
    assert store.list_cycle_target_risk_results() == ()
    attempts = store.list_cycle_target_risk_operations(
        CycleTargetRiskQuery(status=CycleTargetRiskStatus.FAILED)
    )
    assert len(attempts) == 1
    assert attempts[0].error_code == "QT-RISK-CYCLE-TARGET-STORAGE-001"


def test_v20_to_current_migration_is_backed_up_additive_and_zero_backfill(tmp_path: Path):
    path = tmp_path / "central.sqlite3"
    with sqlite3.connect(path) as connection:
        for version in range(1, 21):
            connection.executescript(sqlite_database._MIGRATIONS[version][1])
            connection.execute("INSERT INTO schema_migrations VALUES (?, ?, ?)", (version, NOW.isoformat(), f"fixture {version}"))
        connection.execute(
            """INSERT INTO market_bars VALUES
            ('AAPL', '2026-01-02T00:00:00+00:00', '1Day', 'raw', 'iex',
             '100', '101', '99', '100', 100, NULL, NULL, 'fixture',
             '2026-01-03T00:00:00+00:00')"""
        )
        connection.commit()
    CentralSQLiteDatabase(path).initialize()
    backups = tuple((tmp_path / "backups").glob("*.sqlite3"))
    assert len(backups) == 1 and ".schema-v20-to-v22." in backups[0].name
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 22
        assert connection.execute("SELECT COUNT(*) FROM market_bars").fetchone()[0] == 1
        for table in (
            "cycle_target_risk_operation_attempts", "cycle_target_risk_review_results",
            "cycle_target_risk_rule_results", "cycle_target_risk_source_links",
            "asset_trading_control_operations", "asset_trading_control_events",
            "cycle_target_asset_admission_operations", "cycle_target_asset_admission_results",
            "cycle_target_asset_admission_rules", "cycle_target_asset_admission_source_links",
        ):
            assert connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0
        assert len(sqlite_database.expected_schema_tables()) == 137
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def test_failed_v21_migration_restores_intact_v20_database(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    path = tmp_path / "central.sqlite3"
    with sqlite3.connect(path) as connection:
        for version in range(1, 21):
            connection.executescript(sqlite_database._MIGRATIONS[version][1])
            connection.execute("INSERT INTO schema_migrations VALUES (?, ?, ?)", (version, NOW.isoformat(), f"fixture {version}"))
        connection.commit()
    broken = dict(sqlite_database._MIGRATIONS); broken[21] = ("broken P35", "CREATE TABL invalid")
    monkeypatch.setattr(sqlite_database, "_MIGRATIONS", broken)
    with pytest.raises(sqlite3.DatabaseError):
        CentralSQLiteDatabase(path).initialize()
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 20
        assert connection.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='cycle_target_asset_admission_results'").fetchone()[0] == 0
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
