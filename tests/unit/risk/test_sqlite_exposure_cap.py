from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest

from quant_trading.application_settings import ExecutionEnvironment
from quant_trading.orchestration import TargetAdjustmentExposureCapPreviewCoordinator
from quant_trading.persistence import CentralSQLiteDatabase, SQLiteExposureCapStore
from quant_trading.persistence import sqlite_database
from quant_trading.persistence.sqlite_database import _MIGRATIONS
from quant_trading.risk import (
    ArchiveSingleAssetExposureCapDefinitionCommand,
    ExposureCapDefinitionStatus,
    ExposureCapDisposition,
    ExposureCapOperationStatus,
    RiskSafetyStateSnapshot,
    SaveSingleAssetExposureCapDefinitionCommand,
    SingleAssetExposureCapService,
    TargetAdjustmentExposureCapPreviewCommand,
    TargetAdjustmentRiskReviewCommand,
)
from quant_trading.run_history import AlgorithmRunService, AlgorithmRunStatus, AlgorithmRunType

from tests.unit.decision.test_sqlite_target_adjustment_decision import (
    NOW,
    SOFTWARE,
    _decision_command,
    _prepare,
    _system,
)
from tests.unit.risk.test_sqlite_target_adjustment_risk import _coordinator as _phase6a_coordinator


def _safety(*, automatic=False):
    return RiskSafetyStateSnapshot(
        uuid4(), ExecutionEnvironment.ALPACA_PAPER, False, automatic, True,
        False, "application-role-settings@1", "test", "abc123", "dirty", NOW,
    )


def _build(path: Path, system, phase6a_queries):
    store = SQLiteExposureCapStore(path); store.initialize()
    runs = AlgorithmRunService(system[7], clock=lambda: NOW)
    service = SingleAssetExposureCapService(store, store, runs, SOFTWARE, clock=lambda: NOW)
    coordinator = TargetAdjustmentExposureCapPreviewCoordinator(
        phase6a_queries, store, store, service, runs, SOFTWARE, _safety,
    )
    return store, service, coordinator


def _phase6a(system, path):
    _source, _definition, _linked, link = _prepare(system)
    decision = system[3].preview(_decision_command(link.link_id))
    intent = system[6].get_target_adjustment_result(decision.decision_result_id).intents[0]
    risk_store, risk_coordinator = _phase6a_coordinator(system, path)
    phase6a = risk_coordinator.review(
        TargetAdjustmentRiskReviewCommand(
            intent.intent_id, "structural review", "SESSION", "PHASE6A", "tester", NOW,
        )
    )
    return risk_store.get_target_adjustment_risk_result(phase6a.review_result_id), risk_store


def test_definition_versions_archive_preview_reload_and_run_relationships(tmp_path: Path):
    path = tmp_path / "central.sqlite3"; system = _system(path)
    phase6a, phase6a_store = _phase6a(system, path)
    store, service, coordinator = _build(path, system, phase6a_store)
    save = service.save_definition(SaveSingleAssetExposureCapDefinitionCommand(
        "AAPL", "65", "explicit cap", "SESSION", "CAP-DEF", "tester", NOW,
    ))
    assert save.status is ExposureCapOperationStatus.COMPLETED
    definition = store.get_definition(save.definition_id, save.definition_version)
    command = TargetAdjustmentExposureCapPreviewCommand(
        phase6a.review_result_id, definition.definition_id, definition.definition_version,
        "evaluate exact cap", "SESSION", "CAP-PREVIEW", "tester", NOW,
    )

    outcome = coordinator.preview(command)

    assert outcome.status is ExposureCapOperationStatus.COMPLETED
    assert outcome.disposition is ExposureCapDisposition.MANUAL_REVIEW_REQUIRED
    result = store.get_exposure_cap_result(outcome.preview_result_id)
    assert result.rule.cap_constrained_candidate_notional_usd == Decimal("5")
    assert result.rule.reduction_usd == Decimal("5")
    assert store.get_exposure_cap_source_link(result.preview_result_id).phase6a_run_id == phase6a.run_id
    run = system[7].get_run(outcome.run_id)
    assert run.run_type is AlgorithmRunType.TARGET_ADJUSTMENT_EXPOSURE_CAP_PREVIEW
    assert run.parent_run_id == phase6a.run_id
    assert run.status is AlgorithmRunStatus.COMPLETED_WITH_WARNINGS
    detail = system[7].get_run_detail(outcome.run_id)
    artifact = next(item for item in detail.artifacts if item.artifact_type == "target_adjustment_exposure_cap_operation")
    assert artifact.children[0].children[0].artifact_type == "target_adjustment_exposure_cap_rule_result"
    relationships = {(item.relationship_type.value, item.run_id) for item in detail.relationships}
    assert ("parent", phase6a.run_id) in relationships
    assert ("source", phase6a.source.decision_run_id) in relationships
    assert ("source", phase6a.source.target_child_run_id) in relationships
    assert SQLiteExposureCapStore(path).get_exposure_cap_result(result.preview_result_id) == result
    archived = service.archive_definition(ArchiveSingleAssetExposureCapDefinitionCommand(
        definition.definition_id, definition.definition_version, "archive exact cap",
        "SESSION", "CAP-ARCHIVE", "tester", NOW,
    ))
    latest = store.get_latest_definition(definition.definition_id)
    assert archived.status is ExposureCapOperationStatus.COMPLETED
    assert latest.status is ExposureCapDefinitionStatus.ARCHIVED
    assert latest.definition_version == 2
    rejected = coordinator.preview(TargetAdjustmentExposureCapPreviewCommand(
        phase6a.review_result_id, definition.definition_id, definition.definition_version,
        "archived cannot be selected", "SESSION", "ARCHIVED", "tester", NOW,
    ))
    assert rejected.status is ExposureCapOperationStatus.INVALID_INPUT
    assert store.get_exposure_cap_result(result.preview_result_id) == result


def test_preview_idempotency_missing_source_and_unsafe_state_are_durable(tmp_path: Path):
    path = tmp_path / "central.sqlite3"; system = _system(path)
    phase6a, phase6a_store = _phase6a(system, path)
    store, service, coordinator = _build(path, system, phase6a_store)
    save = service.save_definition(SaveSingleAssetExposureCapDefinitionCommand(
        "AAPL", "60", "explicit cap", "SESSION", "CAP-DEF", "tester", NOW,
    ))
    operation_id = uuid4()
    command = TargetAdjustmentExposureCapPreviewCommand(
        phase6a.review_result_id, save.definition_id, save.definition_version,
        "block exact cap", "SESSION", "CAP-PREVIEW", "tester", NOW, operation_id,
    )
    first = coordinator.preview(command); retry = coordinator.preview(command)
    missing = coordinator.preview(TargetAdjustmentExposureCapPreviewCommand(
        uuid4(), save.definition_id, save.definition_version,
        "missing source", "SESSION", "MISSING", "tester", NOW,
    ))

    unsafe_service = SingleAssetExposureCapService(
        store, store, AlgorithmRunService(system[7], clock=lambda: NOW), SOFTWARE,
        clock=lambda: NOW,
    )
    unsafe = TargetAdjustmentExposureCapPreviewCoordinator(
        phase6a_store, store, store, unsafe_service,
        AlgorithmRunService(system[7], clock=lambda: NOW), SOFTWARE,
        lambda: _safety(automatic=True),
    ).preview(TargetAdjustmentExposureCapPreviewCommand(
        phase6a.review_result_id, save.definition_id, save.definition_version,
        "unsafe state", "SESSION", "UNSAFE", "tester", NOW,
    ))

    assert first.disposition is ExposureCapDisposition.BLOCKED_BY_EXPOSURE_CAP
    assert retry.run_id == first.run_id and retry.preview_result_id == first.preview_result_id
    assert missing.status is ExposureCapOperationStatus.INVALID_INPUT
    assert unsafe.status is ExposureCapOperationStatus.BLOCKED
    assert system[7].get_run(unsafe.run_id).status is AlgorithmRunStatus.BLOCKED
    assert len(store.list_exposure_cap_operations()) == 4  # definition + completed + missing + unsafe


def test_repository_rejects_definition_tamper_and_source_query_failure_is_durable(tmp_path: Path):
    path = tmp_path / "central.sqlite3"; system = _system(path)
    phase6a, phase6a_store = _phase6a(system, path)
    store, service, _coordinator = _build(path, system, phase6a_store)
    save = service.save_definition(SaveSingleAssetExposureCapDefinitionCommand(
        "AAPL", "65", "explicit cap", "SESSION", "CAP-DEF", "tester", NOW,
    ))

    def tamper_then_capture_safety():
        with sqlite3.connect(path) as connection:
            connection.execute(
                """UPDATE single_asset_exposure_cap_definitions
                   SET max_target_exposure_usd_text='66'
                   WHERE definition_id=? AND definition_version=?""",
                (str(save.definition_id), save.definition_version),
            )
            connection.commit()
        return _safety()

    tampered = TargetAdjustmentExposureCapPreviewCoordinator(
        phase6a_store, store, store, service,
        AlgorithmRunService(system[7], clock=lambda: NOW), SOFTWARE,
        tamper_then_capture_safety,
    ).preview(TargetAdjustmentExposureCapPreviewCommand(
        phase6a.review_result_id, save.definition_id, save.definition_version,
        "detect tamper", "SESSION", "TAMPER", "tester", NOW,
    ))
    assert tampered.status is ExposureCapOperationStatus.FAILED
    assert tampered.preview_result_id is None
    assert system[7].get_run(tampered.run_id).status is AlgorithmRunStatus.FAILED

    class FailingPhase6AQueries:
        def get_target_adjustment_risk_result(self, _result_id):
            raise sqlite3.DatabaseError("simulated source query failure")

        def get_target_adjustment_risk_source_link(self, _result_id):
            raise AssertionError("must not be called")

    failed = TargetAdjustmentExposureCapPreviewCoordinator(
        FailingPhase6AQueries(), store, store, service,
        AlgorithmRunService(system[7], clock=lambda: NOW), SOFTWARE, _safety,
    ).preview(TargetAdjustmentExposureCapPreviewCommand(
        phase6a.review_result_id, save.definition_id, save.definition_version,
        "source query failure", "SESSION", "QUERY-FAIL", "tester", NOW,
    ))
    assert failed.status is ExposureCapOperationStatus.FAILED
    assert system[7].get_run(failed.run_id).status is AlgorithmRunStatus.FAILED
    assert any(item.operation_id == failed.operation_id for item in store.list_exposure_cap_operations())


def _create_v10(path: Path):
    with sqlite3.connect(path) as connection:
        for version in range(1, 11):
            connection.executescript(_MIGRATIONS[version][1])
            connection.execute(
                "INSERT INTO schema_migrations VALUES (?, ?, ?)",
                (version, datetime(2026, 7, 21, tzinfo=UTC).isoformat(), f"test v{version}"),
            )
        connection.execute(
            "INSERT INTO market_bars VALUES ('AAPL', ?, '1Day', 'raw', 'iex', '100', '101', '99', '100.5', 10, NULL, NULL, 'test', ?)",
            (NOW.isoformat(), NOW.isoformat()),
        )
        connection.commit()


def test_v10_to_current_migration_backs_up_preserves_and_has_zero_backfill(tmp_path: Path):
    path = tmp_path / "central.sqlite3"; backups = tmp_path / "backups"; _create_v10(path)

    CentralSQLiteDatabase(path, backup_directory=backups).initialize()

    backup = next(backups.glob("*.sqlite3"))
    assert ".schema-v10-to-v13." in backup.name
    with sqlite3.connect(backup) as connection:
        assert connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 10
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 13
        assert connection.execute("SELECT COUNT(*) FROM market_bars").fetchone()[0] == 1
        for table in (
            "single_asset_exposure_cap_definitions",
            "target_adjustment_exposure_cap_operations",
            "target_adjustment_exposure_cap_results",
            "target_adjustment_exposure_cap_rule_results",
            "target_adjustment_exposure_cap_source_links",
        ):
            assert connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []


def test_failed_v11_migration_rolls_back_to_intact_v10(tmp_path: Path, monkeypatch):
    path = tmp_path / "central.sqlite3"; backups = tmp_path / "backups"; _create_v10(path)
    broken = dict(sqlite_database._MIGRATIONS)
    broken[11] = ("intentionally broken v11", broken[11][1] + "\nINVALID SQL;")
    monkeypatch.setattr(sqlite_database, "_MIGRATIONS", broken)

    with pytest.raises(sqlite3.OperationalError):
        CentralSQLiteDatabase(path, backup_directory=backups).initialize()

    assert len(tuple(backups.glob("*.sqlite3"))) == 1
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 10
        assert connection.execute("SELECT COUNT(*) FROM market_bars").fetchone()[0] == 1
        assert connection.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE name='single_asset_exposure_cap_definitions'"
        ).fetchone()[0] == 0
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
