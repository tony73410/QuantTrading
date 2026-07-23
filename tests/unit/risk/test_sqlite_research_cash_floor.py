from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest

from quant_trading.orchestration import (
    TargetAdjustmentResearchCashFloorPreviewCoordinator,
)
from quant_trading.persistence import CentralSQLiteDatabase, SQLiteResearchCashFloorStore
from quant_trading.persistence import sqlite_database
from quant_trading.persistence.sqlite_database import _MIGRATIONS
from quant_trading.risk import (
    ArchiveResearchAssetCashFloorDefinitionCommand,
    ResearchCashFloorDisposition,
    ResearchCashFloorDefinitionStatus,
    ResearchCashFloorOperationQuery,
    ResearchCashFloorOperationStatus,
    ResearchCashFloorResultQuery,
    ExposureCapRuleOutcome,
    ResearchAssetCashFloorService,
    SaveResearchAssetCashFloorDefinitionCommand,
    SaveSingleAssetExposureCapDefinitionCommand,
    TargetAdjustmentResearchCashFloorPreviewCommand,
    TargetAdjustmentExposureCapPreviewCommand,
)
from quant_trading.run_history import AlgorithmRunService, AlgorithmRunStatus, AlgorithmRunType

from tests.unit.decision.test_sqlite_target_adjustment_decision import NOW, SOFTWARE, _system
from tests.unit.risk.test_sqlite_exposure_cap import _build as _phase6b_build
from tests.unit.risk.test_sqlite_exposure_cap import _phase6a, _safety


def _build_phase6b(path: Path, system):
    phase6a, phase6a_store = _phase6a(system, path)
    cap_store, cap_service, cap_coordinator = _phase6b_build(path, system, phase6a_store)
    saved = cap_service.save_definition(
        SaveSingleAssetExposureCapDefinitionCommand(
            "AAPL", "65", "exact cap", "SESSION", "CAP-DEF", "tester", NOW
        )
    )
    phase6b = cap_coordinator.preview(
        TargetAdjustmentExposureCapPreviewCommand(
            phase6a.review_result_id,
            saved.definition_id,
            saved.definition_version,
            "exact cap preview",
            "SESSION",
            "CAP-PREVIEW",
            "tester",
            NOW,
        )
    )
    return phase6b, cap_store


def test_persisted_phase6c_preview_reloads_exact_source_and_run(tmp_path: Path):
    path = tmp_path / "central.sqlite3"
    system = _system(path)
    phase6b, cap_store = _build_phase6b(path, system)
    store = SQLiteResearchCashFloorStore(path)
    store.initialize()
    runs = AlgorithmRunService(system[7], clock=lambda: NOW)
    service = ResearchAssetCashFloorService(store, store, runs, SOFTWARE, clock=lambda: NOW)
    coordinator = TargetAdjustmentResearchCashFloorPreviewCoordinator(
        cap_store,
        system[5],
        store,
        store,
        service,
        runs,
        SOFTWARE,
        _safety,
    )
    definition = service.save_definition(
        SaveResearchAssetCashFloorDefinitionCommand(
            "AAPL", "35", "explicit floor", "SESSION", "FLOOR-DEF", "tester", NOW
        )
    )
    command = TargetAdjustmentResearchCashFloorPreviewCommand(
        phase6b.preview_result_id,
        definition.definition_id,
        definition.definition_version,
        "evaluate exact research cash floor",
        "SESSION",
        "FLOOR-PREVIEW",
        "tester",
        NOW,
        uuid4(),
    )

    outcome = coordinator.preview(command)
    retry = coordinator.preview(command)

    assert outcome.status is ResearchCashFloorOperationStatus.COMPLETED
    assert outcome.disposition is ResearchCashFloorDisposition.MANUAL_REVIEW_REQUIRED
    assert retry.run_id == outcome.run_id
    result = store.get_research_cash_floor_result(outcome.preview_result_id)
    assert result.rule.research_capital_basis_usd == Decimal("100")
    assert result.rule.current_exposure_usd == Decimal("60.0")
    assert result.rule.phase6b_candidate_notional_usd == Decimal("5.0")
    assert result.rule.cash_floor_constrained_candidate_notional_usd == Decimal("5.0")
    assert SQLiteResearchCashFloorStore(path).get_research_cash_floor_result(
        outcome.preview_result_id
    ) == result
    link = store.get_research_cash_floor_source_link(outcome.preview_result_id)
    assert link.phase6b_run_id == phase6b.run_id
    run = system[7].get_run(outcome.run_id)
    assert run.run_type is AlgorithmRunType.TARGET_ADJUSTMENT_RESEARCH_CASH_FLOOR_PREVIEW
    assert run.parent_run_id == phase6b.run_id
    assert run.status is AlgorithmRunStatus.COMPLETED_WITH_WARNINGS
    detail = system[7].get_run_detail(outcome.run_id)
    artifact = next(
        item
        for item in detail.artifacts
        if item.artifact_type == "target_adjustment_research_cash_floor_operation"
    )
    assert tuple(child.artifact_type for child in artifact.children[0].children) == (
        "target_adjustment_exposure_cap_rule_reference",
        "target_adjustment_research_cash_floor_rule_result",
    )
    relationships = {(item.relationship_type.value, item.run_id) for item in detail.relationships}
    assert ("parent", phase6b.run_id) in relationships
    assert ("source", link.phase6a_run_id) in relationships
    assert store.list_research_cash_floor_results(
        ResearchCashFloorResultQuery(
            phase6b_rule_outcome=ExposureCapRuleOutcome.REDUCED_TO_CAP,
            has_warnings=True,
        )
    ) == (result,)

    conflict = coordinator.preview(
        TargetAdjustmentResearchCashFloorPreviewCommand(
            phase6b.preview_result_id,
            definition.definition_id,
            definition.definition_version,
            "different inputs for reused operation",
            "SESSION",
            "FLOOR-CONFLICT",
            "tester",
            NOW,
            command.operation_id,
        )
    )
    assert conflict.status is ResearchCashFloorOperationStatus.INVALID_INPUT
    assert system[7].get_run(conflict.run_id).status is AlgorithmRunStatus.INVALID_INPUT

    blocking_definition = service.save_definition(
        SaveResearchAssetCashFloorDefinitionCommand(
            "AAPL", "40", "exact zero capacity floor", "SESSION",
            "FLOOR-BLOCK-DEF", "tester", NOW,
        )
    )
    blocked = coordinator.preview(
        TargetAdjustmentResearchCashFloorPreviewCommand(
            phase6b.preview_result_id,
            blocking_definition.definition_id,
            blocking_definition.definition_version,
            "block at exact zero capacity",
            "SESSION",
            "FLOOR-BLOCK",
            "tester",
            NOW,
        )
    )
    assert blocked.status is ResearchCashFloorOperationStatus.COMPLETED
    assert blocked.disposition is ResearchCashFloorDisposition.BLOCKED_BY_RESEARCH_CASH_FLOOR
    blocked_result = SQLiteResearchCashFloorStore(path).get_research_cash_floor_result(
        blocked.preview_result_id
    )
    assert blocked_result.rule.cash_floor_constrained_candidate_notional_usd == Decimal("0")
    assert system[7].get_run(blocked.run_id).status is AlgorithmRunStatus.BLOCKED

    archived = service.archive_definition(
        ArchiveResearchAssetCashFloorDefinitionCommand(
            definition.definition_id,
            definition.definition_version,
            "archive explicit floor",
            "SESSION",
            "FLOOR-ARCHIVE",
            "tester",
            NOW,
        )
    )
    latest = store.get_latest_definition(definition.definition_id)
    assert archived.status is ResearchCashFloorOperationStatus.COMPLETED
    assert latest.status is ResearchCashFloorDefinitionStatus.ARCHIVED
    assert latest.definition_version == definition.definition_version + 1
    rejected = coordinator.preview(
        TargetAdjustmentResearchCashFloorPreviewCommand(
            phase6b.preview_result_id,
            definition.definition_id,
            definition.definition_version,
            "archived floor cannot be selected",
            "SESSION",
            "FLOOR-ARCHIVED",
            "tester",
            NOW,
        )
    )
    assert rejected.status is ResearchCashFloorOperationStatus.INVALID_INPUT
    assert store.get_research_cash_floor_result(outcome.preview_result_id) == result


def test_missing_source_unsafe_state_and_tamper_are_durable(tmp_path: Path):
    path = tmp_path / "central.sqlite3"
    system = _system(path)
    phase6b, cap_store = _build_phase6b(path, system)
    store = SQLiteResearchCashFloorStore(path)
    store.initialize()
    runs = AlgorithmRunService(system[7], clock=lambda: NOW)
    service = ResearchAssetCashFloorService(store, store, runs, SOFTWARE, clock=lambda: NOW)
    saved = service.save_definition(
        SaveResearchAssetCashFloorDefinitionCommand(
            "AAPL", "35", "explicit floor", "SESSION", "FLOOR-DEF", "tester", NOW
        )
    )
    missing = TargetAdjustmentResearchCashFloorPreviewCoordinator(
        cap_store, system[5], store, store, service, runs, SOFTWARE, _safety
    ).preview(
        TargetAdjustmentResearchCashFloorPreviewCommand(
            uuid4(), saved.definition_id, saved.definition_version,
            "missing Phase 6B source", "SESSION", "MISSING", "tester", NOW,
        )
    )

    def unsafe_safety():
        return _safety(automatic=True)

    unsafe = TargetAdjustmentResearchCashFloorPreviewCoordinator(
        cap_store, system[5], store, store, service, runs, SOFTWARE, unsafe_safety
    ).preview(
        TargetAdjustmentResearchCashFloorPreviewCommand(
            phase6b.preview_result_id, saved.definition_id, saved.definition_version,
            "unsafe state", "SESSION", "UNSAFE", "tester", NOW,
        )
    )

    def tamper_then_safety():
        with sqlite3.connect(path) as connection:
            connection.execute(
                """UPDATE research_asset_cash_floor_definitions
                   SET minimum_research_asset_cash_usd_text='36'
                   WHERE definition_id=? AND definition_version=?""",
                (str(saved.definition_id), saved.definition_version),
            )
            connection.commit()
        return _safety()

    tampered = TargetAdjustmentResearchCashFloorPreviewCoordinator(
        cap_store, system[5], store, store, service, runs, SOFTWARE, tamper_then_safety
    ).preview(
        TargetAdjustmentResearchCashFloorPreviewCommand(
            phase6b.preview_result_id, saved.definition_id, saved.definition_version,
            "detect definition tamper", "SESSION", "TAMPER", "tester", NOW,
        )
    )

    assert missing.status is ResearchCashFloorOperationStatus.INVALID_INPUT
    assert unsafe.status is ResearchCashFloorOperationStatus.BLOCKED
    assert system[7].get_run(unsafe.run_id).status is AlgorithmRunStatus.BLOCKED
    assert tampered.status is ResearchCashFloorOperationStatus.FAILED
    assert system[7].get_run(tampered.run_id).status is AlgorithmRunStatus.FAILED
    assert {item.run_id for item in store.list_research_cash_floor_operations()} >= {
        missing.run_id, unsafe.run_id, tampered.run_id,
    }
    assert {item.run_id for item in store.list_research_cash_floor_operations(
        ResearchCashFloorOperationQuery(has_error=True)
    )} >= {missing.run_id, unsafe.run_id, tampered.run_id}


def _create_v11(path: Path) -> None:
    with sqlite3.connect(path) as connection:
        for version in range(1, 12):
            connection.executescript(_MIGRATIONS[version][1])
            connection.execute(
                "INSERT INTO schema_migrations VALUES (?, ?, ?)",
                (version, datetime(2026, 7, 22, tzinfo=UTC).isoformat(), f"test v{version}"),
            )
        connection.execute(
            "INSERT INTO market_bars VALUES ('AAPL', ?, '1Day', 'raw', 'iex', "
            "'100', '101', '99', '100.5', 10, NULL, NULL, 'test', ?)",
            (NOW.isoformat(), NOW.isoformat()),
        )
        connection.commit()


def test_v11_to_current_migration_backs_up_preserves_and_has_zero_backfill(tmp_path: Path):
    path, backups = tmp_path / "central.sqlite3", tmp_path / "backups"
    _create_v11(path)

    CentralSQLiteDatabase(path, backup_directory=backups).initialize()

    backup = next(backups.glob("*.sqlite3"))
    assert ".schema-v11-to-v13." in backup.name
    with sqlite3.connect(backup) as connection:
        assert connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 11
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 13
        assert connection.execute("SELECT COUNT(*) FROM market_bars").fetchone()[0] == 1
        for table in (
            "research_asset_cash_floor_definitions",
            "target_adjustment_cash_floor_operations",
            "target_adjustment_cash_floor_results",
            "target_adjustment_cash_floor_rule_results",
            "target_adjustment_cash_floor_source_links",
        ):
            assert connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []


def test_failed_v12_migration_rolls_back_to_intact_v11(tmp_path: Path, monkeypatch):
    path, backups = tmp_path / "central.sqlite3", tmp_path / "backups"
    _create_v11(path)
    broken = dict(sqlite_database._MIGRATIONS)
    broken[12] = ("intentionally broken v12", broken[12][1] + "\nINVALID SQL;")
    monkeypatch.setattr(sqlite_database, "_MIGRATIONS", broken)

    with pytest.raises(sqlite3.OperationalError):
        CentralSQLiteDatabase(path, backup_directory=backups).initialize()

    assert len(tuple(backups.glob("*.sqlite3"))) == 1
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 11
        assert connection.execute("SELECT COUNT(*) FROM market_bars").fetchone()[0] == 1
        assert connection.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE name='research_asset_cash_floor_definitions'"
        ).fetchone()[0] == 0
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
