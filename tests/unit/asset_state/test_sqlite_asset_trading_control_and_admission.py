from __future__ import annotations

import json
import sqlite3
from datetime import timedelta
from pathlib import Path
from uuid import uuid4

from quant_trading.algorithm_control.cycle_target_asset_admission_export import (
    CycleTargetAssetAdmissionExportService,
)
from quant_trading.asset_state import (
    AssetTradingControlChangeCommand,
    AssetTradingControlService,
    AssetTradingControlStatus,
    ASSET_TRADING_CONTROL_CALENDAR_DEFINITION_ID,
    p35_us_equity_mapping_id,
)
from quant_trading.orchestration import (
    AssetTradingControlCoordinator,
    CycleTargetAssetAdmissionCoordinator,
)
from quant_trading.persistence import (
    CentralSQLiteDatabase,
    SQLiteAssetTradingControlStore,
    SQLiteCycleTargetAssetAdmissionStore,
)
from quant_trading.risk import (
    CycleTargetAssetAdmissionQuery,
    CycleTargetAssetAdmissionReplayService,
    CycleTargetAssetAdmissionReviewCommand,
    CycleTargetAssetAdmissionService,
    CycleTargetAssetAdmissionStatus,
)
from quant_trading.run_history import AlgorithmRunService, AlgorithmRunType

from test_sqlite_cycle_target_risk import NOW, _p33


def _control(path: Path, runs, software, *, status, requested_at, predecessor=None, accepted_at=None):
    database = CentralSQLiteDatabase(path)
    store = SQLiteAssetTradingControlStore(database); store.initialize()
    accepted_at = accepted_at or requested_at
    service = AssetTradingControlService(store, clock=lambda: accepted_at)
    coordinator = AssetTradingControlCoordinator(
        store, service, AlgorithmRunService(runs), software,
        clock=lambda: accepted_at,
    )
    command = AssetTradingControlChangeCommand(
        "AAPL", status, predecessor, p35_us_equity_mapping_id("AAPL"), 1,
        ASSET_TRADING_CONTROL_CALENDAR_DEFINITION_ID, f"set {status.value}", "session",
        f"control-{uuid4().hex}", "pytest", requested_at, uuid4(),
    )
    return store, coordinator, command


def _admission(path, runs, software, p33_store, control_store, p33_result, *, at):
    database = CentralSQLiteDatabase(path)
    store = SQLiteCycleTargetAssetAdmissionStore(database); store.initialize()
    service = CycleTargetAssetAdmissionService(store, software, clock=lambda: at)
    coordinator = CycleTargetAssetAdmissionCoordinator(
        p33_store, control_store, store, store, service,
        AlgorithmRunService(runs), software, clock=lambda: at,
    )
    command = CycleTargetAssetAdmissionReviewCommand(
        p33_result.review_result_id, p33_result.run_id, "P35 fixture", "session",
        f"p35-{uuid4().hex}", "pytest", at, uuid4(),
    )
    return store, coordinator, command


def test_trading_control_immediate_freeze_next_session_unfreeze_and_reload(tmp_path: Path):
    path = tmp_path / "central.sqlite3"
    _, runs, _, _, _, _, p33, _ = _p33(path)
    software = p33._software

    store, coordinator, initial = _control(
        path, runs, software, status=AssetTradingControlStatus.ELIGIBLE,
        requested_at=NOW - timedelta(minutes=2),
    )
    preflight = coordinator.preflight(initial)
    assert preflight.accepted
    assert store.list_asset_trading_control_events() == ()
    eligible = coordinator.change(initial)
    assert eligible.status.value == "completed"
    first = store.get_asset_trading_control_event(eligible.event_id)
    assert first.effective_at_utc == initial.requested_at_utc

    _, coordinator, freeze_command = _control(
        path, runs, software, status=AssetTradingControlStatus.FROZEN,
        requested_at=NOW - timedelta(minutes=1), predecessor=first.event_id,
    )
    frozen = coordinator.change(freeze_command)
    freeze_event = store.get_asset_trading_control_event(frozen.event_id)
    assert freeze_event.effective_at_utc == freeze_command.requested_at_utc

    _, coordinator, unfreeze_command = _control(
        path, runs, software, status=AssetTradingControlStatus.ELIGIBLE,
        requested_at=NOW, predecessor=freeze_event.event_id,
    )
    unfreeze = coordinator.change(unfreeze_command)
    unfreeze_event = store.get_asset_trading_control_event(unfreeze.event_id)
    assert unfreeze_event.effective_at_utc > unfreeze_command.requested_at_utc
    assert store.get_effective_asset_trading_control_event("AAPL", NOW).event_id == freeze_event.event_id
    assert store.get_effective_asset_trading_control_event("AAPL", unfreeze_event.effective_at_utc).event_id == unfreeze_event.event_id

    retry = coordinator.change(unfreeze_command)
    assert retry.attempt_id == unfreeze.attempt_id and retry.run_id == unfreeze.run_id
    reloaded = SQLiteAssetTradingControlStore(CentralSQLiteDatabase(path)); reloaded.initialize()
    assert reloaded.get_asset_trading_control_event(unfreeze.event_id) == unfreeze_event
    assert len(reloaded.list_asset_trading_control_events()) == 3
    assert runs.get_run_detail(unfreeze.run_id).summary.run.run_type is AlgorithmRunType.ASSET_TRADING_CONTROL_CHANGE


def test_trading_control_cannot_backdate_and_conflicts_are_durable(tmp_path: Path):
    path = tmp_path / "central.sqlite3"
    _, runs, _, _, _, _, p33, _ = _p33(path)
    software = p33._software
    requested = NOW - timedelta(days=30)
    accepted = NOW
    store, coordinator, command = _control(
        path, runs, software, status=AssetTradingControlStatus.FROZEN,
        requested_at=requested, accepted_at=accepted,
    )
    outcome = coordinator.change(command)
    event = store.get_asset_trading_control_event(outcome.event_id)
    assert event.requested_at_utc == requested
    assert event.effective_at_utc == accepted
    assert event.created_at_utc == accepted
    assert store.get_effective_asset_trading_control_event("AAPL", accepted - timedelta(microseconds=1)) is None

    _, conflicting, conflict = _control(
        path, runs, software, status=AssetTradingControlStatus.ELIGIBLE,
        requested_at=accepted + timedelta(minutes=1),
        accepted_at=accepted + timedelta(minutes=1), predecessor=None,
    )
    rejected = conflicting.change(conflict)
    assert rejected.status.value == "invalid_input"
    assert len(store.list_asset_trading_control_events()) == 1
    assert any(item.operation_id == conflict.operation_id for item in store.list_asset_trading_control_operations())


def test_p35_missing_frozen_and_eligible_are_fail_closed_or_manual_review(tmp_path: Path):
    path = tmp_path / "central.sqlite3"
    p33_store, runs, _, _, _, _, p33_coordinator, p33_command = _p33(path)
    p33_outcome = p33_coordinator.review(p33_command)
    p33_result = p33_store.get_cycle_target_risk_result(p33_outcome.review_result_id)
    software = p33_coordinator._software
    control_store = SQLiteAssetTradingControlStore(CentralSQLiteDatabase(path)); control_store.initialize()

    admission_store, admission, missing_command = _admission(
        path, runs, software, p33_store, control_store, p33_result, at=NOW + timedelta(minutes=1),
    )
    preflight = admission.preflight(missing_command)
    assert preflight.accepted and preflight.control is None
    missing = admission.review(missing_command)
    assert missing.status is CycleTargetAssetAdmissionStatus.BLOCKED_MISSING_TRADING_CONTROL
    missing_result = admission_store.get_cycle_target_asset_admission_result(missing.result_id)
    assert [item.rule_id for item in missing_result.rules] == [
        "P33_STRUCTURAL_REVIEW_INTEGRITY", "ASSET_TRADING_CONTROL_AVAILABILITY"
    ]

    _, control, freeze_command = _control(
        path, runs, software, status=AssetTradingControlStatus.FROZEN,
        requested_at=NOW + timedelta(minutes=2),
    )
    frozen_event = control.change(freeze_command)
    admission_store, admission, frozen_command = _admission(
        path, runs, software, p33_store, control_store, p33_result, at=NOW + timedelta(minutes=3),
    )
    frozen = admission.review(frozen_command)
    assert frozen.status is CycleTargetAssetAdmissionStatus.BLOCKED_FROZEN_ASSET
    frozen_result = admission_store.get_cycle_target_asset_admission_result(frozen.result_id)
    assert frozen_result.control.event_id == frozen_event.event_id
    assert frozen_result.approved_notional_usd is None and frozen_result.risk_approved_intent_id is None
    assert not frozen_result.execution_allowed and not frozen_result.live_allowed

    latest = control_store.get_latest_asset_trading_control_event("AAPL")
    _, control, eligible_command = _control(
        path, runs, software, status=AssetTradingControlStatus.ELIGIBLE,
        requested_at=NOW + timedelta(minutes=4), predecessor=latest.event_id,
    )
    eligible_event = control.change(eligible_command)
    effective = control_store.get_asset_trading_control_event(eligible_event.event_id).effective_at_utc
    admission_store, admission, eligible_command = _admission(
        path, runs, software, p33_store, control_store, p33_result, at=effective + timedelta(minutes=1),
    )
    eligible = admission.review(eligible_command)
    assert eligible.status is CycleTargetAssetAdmissionStatus.MANUAL_REVIEW_REQUIRED
    result = admission_store.get_cycle_target_asset_admission_result(eligible.result_id)
    assert [item.rule_id for item in result.rules] == [
        "P33_STRUCTURAL_REVIEW_INTEGRITY", "ASSET_TRADING_CONTROL_AVAILABILITY", "FROZEN_ASSET_BLOCK"
    ]
    assert result.rules[-1].status.value == "manual_review"
    assert admission_store.list_cycle_target_asset_admission_results(CycleTargetAssetAdmissionQuery(symbol="AAPL"))[0] == result
    assert admission_store.get_cycle_target_asset_admission_source_link(result.result_id).control_event_id == eligible_event.event_id

    retry = admission.review(eligible_command)
    assert retry.attempt_id == eligible.attempt_id and retry.run_id == eligible.run_id
    assert CycleTargetAssetAdmissionReplayService(admission_store).replay(result.result_id).matched
    exporter = CycleTargetAssetAdmissionExportService()
    assert json.loads(exporter.export_json(result, tmp_path / "p35.json").read_text(encoding="utf-8"))["result_id"] == str(result.result_id)
    assert "approved_notional_usd" in exporter.export_csv(result, tmp_path / "p35.csv").read_text(encoding="utf-8-sig")
    reloaded = SQLiteCycleTargetAssetAdmissionStore(CentralSQLiteDatabase(path)); reloaded.initialize()
    assert reloaded.get_cycle_target_asset_admission_result(result.result_id) == result
    detail = runs.get_run_detail(result.run_id)
    assert detail.summary.run.run_type is AlgorithmRunType.CYCLE_TARGET_ASSET_ADMISSION_REVIEW
    assert [stage.name.value for stage in detail.stages] == ["state", "risk"]
    related = {item.run_id for item in detail.relationships}
    assert {p33_result.run_id, result.control.run_id} <= related
    assert any(
        item.artifact_type == "cycle_target_asset_admission_operation" and item.children
        for item in detail.artifacts
    )


def test_missing_p33_source_is_a_durable_invalid_attempt_without_false_parent(tmp_path: Path):
    path = tmp_path / "central.sqlite3"
    p33_store, runs, _, _, _, _, p33_coordinator, _ = _p33(path)
    software = p33_coordinator._software
    control_store = SQLiteAssetTradingControlStore(CentralSQLiteDatabase(path)); control_store.initialize()
    admission_store = SQLiteCycleTargetAssetAdmissionStore(CentralSQLiteDatabase(path)); admission_store.initialize()
    at = NOW + timedelta(minutes=1)
    command = CycleTargetAssetAdmissionReviewCommand(
        uuid4(), uuid4(), "missing exact P33 source", "session", "p35-missing-p33",
        "pytest", at, uuid4(),
    )
    coordinator = CycleTargetAssetAdmissionCoordinator(
        p33_store, control_store, admission_store, admission_store,
        CycleTargetAssetAdmissionService(admission_store, software, clock=lambda: at),
        AlgorithmRunService(runs), software, clock=lambda: at,
    )
    outcome = coordinator.review(command)
    assert outcome.status is CycleTargetAssetAdmissionStatus.INVALID_INPUT
    attempts = admission_store.list_cycle_target_asset_admission_operations(
        CycleTargetAssetAdmissionQuery(status=CycleTargetAssetAdmissionStatus.INVALID_INPUT)
    )
    assert len(attempts) == 1 and attempts[0].operation_id == command.operation_id
    detail = runs.get_run_detail(outcome.run_id)
    assert detail.summary.run.parent_run_id is None
    assert admission_store.list_cycle_target_asset_admission_results() == ()


def test_v20_to_current_is_additive_zero_backfill_and_backed_up(tmp_path: Path):
    from quant_trading.persistence import sqlite_database

    path = tmp_path / "central.sqlite3"
    with sqlite3.connect(path) as connection:
        for version in range(1, 21):
            connection.executescript(sqlite_database._MIGRATIONS[version][1])
            connection.execute("INSERT INTO schema_migrations VALUES (?, ?, ?)", (version, NOW.isoformat(), f"fixture {version}"))
        connection.execute("INSERT INTO market_bars VALUES ('AAPL','2026-01-02T00:00:00+00:00','1Day','raw','iex','100','101','99','100',100,NULL,NULL,'fixture','2026-01-03T00:00:00+00:00')")
        connection.commit()
    CentralSQLiteDatabase(path).initialize()
    backups = tuple((tmp_path / "backups").glob("*.sqlite3"))
    assert len(backups) == 1 and ".schema-v20-to-v22." in backups[0].name
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 22
        assert connection.execute("SELECT COUNT(*) FROM market_bars").fetchone()[0] == 1
        for table in (
            "asset_trading_control_operations", "asset_trading_control_events",
            "cycle_target_asset_admission_operations", "cycle_target_asset_admission_results",
            "cycle_target_asset_admission_rules", "cycle_target_asset_admission_source_links",
        ):
            assert connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0
        assert len(sqlite_database.expected_schema_tables()) == 137
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
