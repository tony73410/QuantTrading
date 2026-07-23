from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from quant_trading.application_settings import ExecutionEnvironment
from quant_trading.orchestration import TargetAdjustmentRiskReviewCoordinator
from quant_trading.persistence import CentralSQLiteDatabase, SQLiteTargetAdjustmentRiskStore
from quant_trading.persistence.sqlite_database import _MIGRATIONS
from quant_trading.risk import RiskSafetyStateSnapshot, TargetAdjustmentRiskReviewCommand, TargetAdjustmentRiskService, TargetAdjustmentRiskStatus
from quant_trading.run_history import AlgorithmRunService, AlgorithmRunStatus, AlgorithmRunType

from tests.unit.decision.test_sqlite_target_adjustment_decision import NOW, SOFTWARE, _decision_command, _prepare, _system


def _coordinator(system, path):
    store = SQLiteTargetAdjustmentRiskStore(path); store.initialize()
    service = TargetAdjustmentRiskService(store, SOFTWARE, clock=lambda: NOW)
    coordinator = TargetAdjustmentRiskReviewCoordinator(
        system[6], store, store, service, AlgorithmRunService(system[7], clock=lambda: NOW), SOFTWARE,
        lambda: RiskSafetyStateSnapshot(uuid4(), ExecutionEnvironment.ALPACA_PAPER, False, False, True, False, "application-role-settings@1", "test", "abc123", "clean", NOW),
    )
    return store, coordinator


def test_completed_manual_review_persists_rules_links_and_run_artifacts(tmp_path: Path):
    path = tmp_path / "central.sqlite3"; system = _system(path)
    source, _definition, linked, link = _prepare(system)
    decision = system[3].preview(_decision_command(link.link_id))
    intent = system[6].get_target_adjustment_result(decision.decision_result_id).intents[0]
    store, coordinator = _coordinator(system, path)
    command = TargetAdjustmentRiskReviewCommand(intent.intent_id, "review exact intent", "SESSION", "RISK", "tester", NOW)

    outcome = coordinator.review(command)

    assert outcome.status is TargetAdjustmentRiskStatus.MANUAL_REVIEW_REQUIRED
    result = store.get_target_adjustment_risk_result(outcome.review_result_id)
    assert result.source.intent_id == intent.intent_id
    assert len(result.rules) == 3
    assert result.approved_notional_usd is None
    assert store.get_target_adjustment_risk_source_link(result.review_result_id).decision_run_id == decision.run_id
    run = system[7].get_run(outcome.run_id)
    assert run.run_type is AlgorithmRunType.TARGET_ADJUSTMENT_RISK_REVIEW
    assert run.parent_run_id == decision.run_id
    assert run.status is AlgorithmRunStatus.COMPLETED_WITH_WARNINGS
    detail = system[7].get_run_detail(outcome.run_id)
    assert [stage.name.value for stage in detail.stages] == ["decision", "risk"]
    artifact = next(x for x in detail.artifacts if x.artifact_type == "target_adjustment_risk_operation")
    assert len(artifact.children[0].children) == 3
    assert ("source", linked.child_run_id) in {(x.relationship_type.value, x.run_id) for x in detail.relationships}
    assert ("source", source.run_id) in {(x.relationship_type.value, x.run_id) for x in detail.relationships}
    assert SQLiteTargetAdjustmentRiskStore(path).get_target_adjustment_risk_result(result.review_result_id) == result


def test_missing_intent_and_idempotent_retry_are_durable(tmp_path: Path):
    path = tmp_path / "central.sqlite3"; system = _system(path)
    _source, _definition, _linked, link = _prepare(system)
    decision = system[3].preview(_decision_command(link.link_id))
    intent = system[6].get_target_adjustment_result(decision.decision_result_id).intents[0]
    store, coordinator = _coordinator(system, path)
    operation_id = uuid4()
    command = TargetAdjustmentRiskReviewCommand(intent.intent_id, "review", "SESSION", "RISK", "tester", NOW, operation_id)

    first = coordinator.review(command); retry = coordinator.review(command)
    missing = coordinator.review(TargetAdjustmentRiskReviewCommand(uuid4(), "missing", "SESSION", "MISSING", "tester", NOW))

    assert retry.run_id == first.run_id and retry.review_result_id == first.review_result_id
    assert missing.status is TargetAdjustmentRiskStatus.INVALID_INPUT
    assert system[7].get_run(missing.run_id).status is AlgorithmRunStatus.INVALID_INPUT
    assert len(store.list_target_adjustment_risk_operations()) == 2


def test_source_query_failure_creates_failed_run_and_durable_attempt(tmp_path: Path):
    path = tmp_path / "central.sqlite3"; system = _system(path)
    store = SQLiteTargetAdjustmentRiskStore(path); store.initialize()

    class FailingDecisionQueries:
        def get_target_adjustment_intent(self, intent_id):
            raise sqlite3.OperationalError("simulated read failure")

    service = TargetAdjustmentRiskService(store, SOFTWARE, clock=lambda: NOW)
    coordinator = TargetAdjustmentRiskReviewCoordinator(
        FailingDecisionQueries(), store, store, service,
        AlgorithmRunService(system[7], clock=lambda: NOW), SOFTWARE,
        lambda: RiskSafetyStateSnapshot(uuid4(), ExecutionEnvironment.ALPACA_PAPER, False, False, True, False, "application-role-settings@1", "test", "abc123", "clean", NOW),
    )

    outcome = coordinator.review(
        TargetAdjustmentRiskReviewCommand(uuid4(), "read failure", "SESSION", "READ-FAIL", "tester", NOW)
    )

    assert outcome.status is TargetAdjustmentRiskStatus.FAILED
    assert system[7].get_run(outcome.run_id).status is AlgorithmRunStatus.FAILED
    assert store.list_target_adjustment_risk_operations()[0].status is TargetAdjustmentRiskStatus.FAILED


def test_store_transaction_rejects_source_tamper_and_preserves_failed_attempt(tmp_path: Path):
    path = tmp_path / "central.sqlite3"; system = _system(path)
    _source, _definition, _linked, link = _prepare(system)
    decision = system[3].preview(_decision_command(link.link_id))
    intent = system[6].get_target_adjustment_result(decision.decision_result_id).intents[0]
    store = SQLiteTargetAdjustmentRiskStore(path); store.initialize()
    service = TargetAdjustmentRiskService(store, SOFTWARE, clock=lambda: NOW)

    def tampering_safety_snapshot():
        with sqlite3.connect(path) as connection:
            connection.execute(
                "UPDATE target_adjustment_trade_intents SET requested_notional_usd_text='11' WHERE intent_id=?",
                (str(intent.intent_id),),
            )
            connection.commit()
        return RiskSafetyStateSnapshot(uuid4(), ExecutionEnvironment.ALPACA_PAPER, False, False, True, False, "application-role-settings@1", "test", "abc123", "clean", NOW)

    coordinator = TargetAdjustmentRiskReviewCoordinator(
        system[6], store, store, service, AlgorithmRunService(system[7], clock=lambda: NOW),
        SOFTWARE, tampering_safety_snapshot,
    )

    outcome = coordinator.review(
        TargetAdjustmentRiskReviewCommand(intent.intent_id, "tamper check", "SESSION", "TAMPER", "tester", NOW)
    )

    assert outcome.status is TargetAdjustmentRiskStatus.FAILED
    assert store.list_target_adjustment_risk_results() == ()
    assert store.list_target_adjustment_risk_operations()[0].status is TargetAdjustmentRiskStatus.FAILED
    assert system[7].get_run(outcome.run_id).status is AlgorithmRunStatus.FAILED


def _create_v9(path):
    with sqlite3.connect(path) as connection:
        for version in range(1, 10):
            connection.executescript(_MIGRATIONS[version][1])
            connection.execute("INSERT INTO schema_migrations VALUES (?, ?, ?)", (version, NOW.isoformat(), f"test v{version}"))
        connection.execute("INSERT INTO market_bars VALUES ('AAPL', ?, '1Day', 'raw', 'iex', '100', '101', '99', '100.5', 10, NULL, NULL, 'test', ?)", (NOW.isoformat(), NOW.isoformat()))
        connection.commit()


def test_v9_to_current_migration_backs_up_preserves_and_has_zero_phase6a_backfill(tmp_path: Path):
    path = tmp_path / "central.sqlite3"; backups = tmp_path / "backups"; _create_v9(path)

    CentralSQLiteDatabase(path, backup_directory=backups).initialize()

    backup = next(backups.glob("*.sqlite3")); assert ".schema-v9-to-v13." in backup.name
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 13
        assert connection.execute("SELECT COUNT(*) FROM market_bars").fetchone()[0] == 1
        for table in ("target_adjustment_risk_operations", "target_adjustment_risk_review_results", "target_adjustment_risk_rule_results", "target_adjustment_risk_source_links"):
            assert connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
