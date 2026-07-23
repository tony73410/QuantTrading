from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest

from quant_trading.capital_allocation import (
    CapitalAllocationService,
    CapitalAssetAllocationInput,
    CapitalBucketType,
)
from quant_trading.orchestration import (
    TargetAdjustmentResearchAssetCashPreviewCoordinator,
    TargetAdjustmentResearchCashFloorPreviewCoordinator,
)
from quant_trading.persistence import (
    CentralSQLiteDatabase,
    SQLiteCapitalAllocationStore,
    SQLiteResearchAssetCashStore,
    SQLiteResearchCashFloorStore,
)
from quant_trading.persistence import sqlite_database
from quant_trading.persistence.sqlite_database import _MIGRATIONS
from quant_trading.risk import (
    ResearchAssetCashAvailabilityService,
    ResearchAssetCashDisposition,
    ResearchAssetCashOperationQuery,
    ResearchAssetCashOperationStatus,
    ResearchAssetCashResultQuery,
    ResearchAssetCashRuleOutcome,
    ResearchAssetCashFloorService,
    SaveResearchAssetCashFloorDefinitionCommand,
    TargetAdjustmentResearchAssetCashPreviewCommand,
    TargetAdjustmentResearchCashFloorPreviewCommand,
)
from quant_trading.risk.errors import RiskContractError
from quant_trading.run_history import AlgorithmRunService, AlgorithmRunStatus, AlgorithmRunType

from tests.unit.capital_allocation.test_capital_allocation import create_command
from tests.unit.decision.test_sqlite_target_adjustment_decision import NOW, SOFTWARE, _system
from tests.unit.risk.test_sqlite_research_cash_floor import _build_phase6b, _safety


def _build_phase6c(path: Path, system):
    phase6b, phase6b_store = _build_phase6b(path, system)
    store = SQLiteResearchCashFloorStore(path)
    store.initialize()
    runs = AlgorithmRunService(system[7], clock=lambda: NOW)
    service = ResearchAssetCashFloorService(store, store, runs, SOFTWARE, clock=lambda: NOW)
    coordinator = TargetAdjustmentResearchCashFloorPreviewCoordinator(
        phase6b_store, system[5], store, store, service, runs, SOFTWARE, _safety
    )
    definition = service.save_definition(
        SaveResearchAssetCashFloorDefinitionCommand(
            "AAPL", "35", "floor", "SESSION", "FLOOR-DEF", "tester", NOW
        )
    )
    outcome = coordinator.preview(
        TargetAdjustmentResearchCashFloorPreviewCommand(
            phase6b.preview_result_id,
            definition.definition_id,
            definition.definition_version,
            "phase6c",
            "SESSION",
            "PHASE6C",
            "tester",
            NOW,
        )
    )
    return outcome, store


def _capital(path: Path, system, *, aapl="3", msft="797", goog=None):
    store = SQLiteCapitalAllocationStore(path)
    store.initialize()
    service = CapitalAllocationService(
        store,
        AlgorithmRunService(system[7], clock=lambda: NOW),
        SOFTWARE,
        clock=lambda: NOW,
    )
    created = service.create_plan(
        create_command(
            request_id=f"CAPITAL-{aapl}",
            asset_allocations=(
                CapitalAssetAllocationInput("AAPL", aapl),
                CapitalAssetAllocationInput("MSFT", msft),
            ) + (
                (CapitalAssetAllocationInput("GOOG", goog),)
                if goog is not None
                else ()
            ),
        )
    )
    return created, store, store.get_plan_detail(created.plan_id)


def _build(path: Path, system, phase6c_store, capital_store):
    store = SQLiteResearchAssetCashStore(path)
    store.initialize()
    runs = AlgorithmRunService(system[7], clock=lambda: NOW)
    service = ResearchAssetCashAvailabilityService(
        store, store, SOFTWARE, clock=lambda: NOW
    )
    coordinator = TargetAdjustmentResearchAssetCashPreviewCoordinator(
        phase6c_store,
        capital_store,
        store,
        store,
        service,
        runs,
        SOFTWARE,
        _safety,
    )
    return store, coordinator


def test_persisted_phase6d_reloads_exact_sources_without_capital_mutation(tmp_path: Path):
    path = tmp_path / "central.sqlite3"
    system = _system(path)
    phase6c, phase6c_store = _build_phase6c(path, system)
    capital, capital_store, detail = _capital(path, system)
    store, coordinator = _build(path, system, phase6c_store, capital_store)
    before_snapshot_count = len(detail.transfers)
    command = TargetAdjustmentResearchAssetCashPreviewCommand(
        phase6c.preview_result_id,
        capital.plan_id,
        detail.latest_snapshot.snapshot_id,
        "limit to explicit asset cash",
        "SESSION",
        "PHASE6D",
        "tester",
        NOW,
        uuid4(),
    )

    outcome = coordinator.preview(command)
    retry = coordinator.preview(command)

    assert outcome.status is ResearchAssetCashOperationStatus.COMPLETED
    assert outcome.disposition is ResearchAssetCashDisposition.MANUAL_REVIEW_REQUIRED
    assert retry.run_id == outcome.run_id
    result = store.get_research_asset_cash_result(outcome.preview_result_id)
    assert result.rule.phase6c_candidate_notional_usd == Decimal("5.0")
    assert result.rule.selected_asset_cash_balance_usd == Decimal("3")
    assert result.rule.asset_cash_constrained_candidate_notional_usd == Decimal("3")
    assert result.rule.outcome is ResearchAssetCashRuleOutcome.REDUCED_TO_RESEARCH_ASSET_CASH
    assert result.research_cash_reserved is False
    assert SQLiteResearchAssetCashStore(path).get_research_asset_cash_result(
        outcome.preview_result_id
    ) == result
    link = store.get_research_asset_cash_source_link(outcome.preview_result_id)
    assert link.phase6c_run_id == phase6c.run_id
    assert link.capital_snapshot_id == detail.latest_snapshot.snapshot_id
    run = system[7].get_run(outcome.run_id)
    assert run.run_type is AlgorithmRunType.TARGET_ADJUSTMENT_RESEARCH_ASSET_CASH_PREVIEW
    assert run.parent_run_id == phase6c.run_id
    assert run.status is AlgorithmRunStatus.COMPLETED_WITH_WARNINGS
    run_detail = system[7].get_run_detail(outcome.run_id)
    artifact = next(
        item
        for item in run_detail.artifacts
        if item.artifact_type
        == "target_adjustment_research_asset_cash_operation"
    )
    assert tuple(child.artifact_type for child in artifact.children[0].children) == (
        "target_adjustment_exposure_cap_rule_reference",
        "target_adjustment_research_cash_floor_rule_reference",
        "target_adjustment_research_asset_cash_rule_result",
    )
    assert "no cash reserved" in artifact.children[0].summary
    relationships = {
        (item.relationship_type.value, item.run_id)
        for item in run_detail.relationships
    }
    assert ("parent", phase6c.run_id) in relationships
    assert ("source", link.phase6b_run_id) in relationships
    assert ("source", link.capital_snapshot_run_id) in relationships
    phase6c_detail = system[7].get_run_detail(phase6c.run_id)
    assert ("child", outcome.run_id) in {
        (item.relationship_type.value, item.run_id)
        for item in phase6c_detail.relationships
    }
    capital_run_detail = system[7].get_run_detail(link.capital_snapshot_run_id)
    assert ("linked_preview", outcome.run_id) in {
        (item.relationship_type.value, item.run_id)
        for item in capital_run_detail.relationships
    }
    after = capital_store.get_plan_detail(capital.plan_id)
    assert after.latest_snapshot == detail.latest_snapshot
    assert len(after.transfers) == before_snapshot_count == 0
    assert store.list_research_asset_cash_results(
        ResearchAssetCashResultQuery(
            symbol="aapl",
            capital_plan_id=capital.plan_id,
            rule_outcome=ResearchAssetCashRuleOutcome.REDUCED_TO_RESEARCH_ASSET_CASH,
            has_warnings=True,
        )
    ) == (result,)
    assert store.list_research_asset_cash_results(
        ResearchAssetCashResultQuery(as_of_from_utc=NOW, as_of_to_utc=NOW)
    ) == (result,)
    assert store.list_research_asset_cash_results(
        ResearchAssetCashResultQuery(as_of_from_utc=NOW + timedelta(microseconds=1))
    ) == ()
    assert store.list_research_asset_cash_results(
        ResearchAssetCashResultQuery(as_of_to_utc=NOW - timedelta(microseconds=1))
    ) == ()
    with pytest.raises(RiskContractError, match="as-of range"):
        ResearchAssetCashResultQuery(
            as_of_from_utc=NOW,
            as_of_to_utc=NOW - timedelta(microseconds=1),
        )
    assert ResearchAssetCashResultQuery(
        None, None, None, None, None, None, None, 123
    ).limit == 123


def test_zero_balance_stale_snapshot_missing_source_and_unsafe_are_durable(tmp_path: Path):
    path = tmp_path / "central.sqlite3"
    system = _system(path)
    phase6c, phase6c_store = _build_phase6c(path, system)
    capital, capital_store, detail = _capital(path, system, aapl="0", msft="800")
    store, coordinator = _build(path, system, phase6c_store, capital_store)
    blocked = coordinator.preview(
        TargetAdjustmentResearchAssetCashPreviewCommand(
            phase6c.preview_result_id,
            capital.plan_id,
            detail.latest_snapshot.snapshot_id,
            "zero asset cash",
            "SESSION",
            "ZERO",
            "tester",
            NOW,
        )
    )
    stale = coordinator.preview(
        TargetAdjustmentResearchAssetCashPreviewCommand(
            phase6c.preview_result_id,
            capital.plan_id,
            uuid4(),
            "stale snapshot",
            "SESSION",
            "STALE",
            "tester",
            NOW,
        )
    )
    missing = coordinator.preview(
        TargetAdjustmentResearchAssetCashPreviewCommand(
            uuid4(),
            capital.plan_id,
            detail.latest_snapshot.snapshot_id,
            "missing phase6c",
            "SESSION",
            "MISSING",
            "tester",
            NOW,
        )
    )

    def unsafe():
        return _safety(automatic=True)

    unsafe_coordinator = TargetAdjustmentResearchAssetCashPreviewCoordinator(
        phase6c_store,
        capital_store,
        store,
        store,
        ResearchAssetCashAvailabilityService(store, store, SOFTWARE, clock=lambda: NOW),
        AlgorithmRunService(system[7], clock=lambda: NOW),
        SOFTWARE,
        unsafe,
    )
    unsafe_result = unsafe_coordinator.preview(
        TargetAdjustmentResearchAssetCashPreviewCommand(
            phase6c.preview_result_id,
            capital.plan_id,
            detail.latest_snapshot.snapshot_id,
            "unsafe",
            "SESSION",
            "UNSAFE",
            "tester",
            NOW,
        )
    )

    assert blocked.disposition is ResearchAssetCashDisposition.BLOCKED_BY_RESEARCH_ASSET_CASH
    assert system[7].get_run(blocked.run_id).status is AlgorithmRunStatus.BLOCKED
    assert stale.status is ResearchAssetCashOperationStatus.INVALID_INPUT
    assert missing.status is ResearchAssetCashOperationStatus.INVALID_INPUT
    assert unsafe_result.status is ResearchAssetCashOperationStatus.BLOCKED
    assert {item.run_id for item in store.list_research_asset_cash_operations(
        ResearchAssetCashOperationQuery(has_error=True)
    )} >= {stale.run_id, missing.run_id, unsafe_result.run_id}


def test_incomplete_but_conserved_tampered_capital_snapshot_fails_closed(tmp_path: Path):
    path = tmp_path / "central.sqlite3"
    system = _system(path)
    phase6c, phase6c_store = _build_phase6c(path, system)
    capital, capital_store, detail = _capital(
        path, system, aapl="3", msft="797", goog="0"
    )
    by_symbol = {
        item.symbol: item.bucket_id
        for item in detail.plan.buckets
        if item.symbol is not None
    }
    with sqlite3.connect(path) as connection:
        connection.execute(
            "DELETE FROM capital_snapshot_balances WHERE snapshot_id=? AND bucket_id=?",
            (str(detail.latest_snapshot.snapshot_id), str(by_symbol["MSFT"])),
        )
        connection.execute(
            "UPDATE capital_snapshot_balances SET balance='797' "
            "WHERE snapshot_id=? AND bucket_id=?",
            (str(detail.latest_snapshot.snapshot_id), str(by_symbol["GOOG"])),
        )
        connection.commit()
    store, coordinator = _build(path, system, phase6c_store, capital_store)

    outcome = coordinator.preview(
        TargetAdjustmentResearchAssetCashPreviewCommand(
            phase6c.preview_result_id,
            capital.plan_id,
            detail.latest_snapshot.snapshot_id,
            "reject incomplete snapshot identity",
            "SESSION",
            "INCOMPLETE-SNAPSHOT",
            "tester",
            NOW,
        )
    )

    assert outcome.status is ResearchAssetCashOperationStatus.INVALID_INPUT
    assert "bucket identity" in outcome.summary
    assert store.list_research_asset_cash_results() == ()


def test_conserved_tampered_protected_reserve_balance_fails_closed(tmp_path: Path):
    path = tmp_path / "central.sqlite3"
    system = _system(path)
    phase6c, phase6c_store = _build_phase6c(path, system)
    capital, capital_store, detail = _capital(path, system)
    locked = next(
        item
        for item in detail.plan.buckets
        if item.bucket_type is CapitalBucketType.LOCKED_RESERVE
    )
    aapl = next(item for item in detail.plan.buckets if item.symbol == "AAPL")
    with sqlite3.connect(path) as connection:
        connection.execute(
            "UPDATE capital_snapshot_balances SET balance='99' "
            "WHERE snapshot_id=? AND bucket_id=?",
            (str(detail.latest_snapshot.snapshot_id), str(locked.bucket_id)),
        )
        connection.execute(
            "UPDATE capital_snapshot_balances SET balance='4' "
            "WHERE snapshot_id=? AND bucket_id=?",
            (str(detail.latest_snapshot.snapshot_id), str(aapl.bucket_id)),
        )
        connection.commit()
    store, coordinator = _build(path, system, phase6c_store, capital_store)

    outcome = coordinator.preview(
        TargetAdjustmentResearchAssetCashPreviewCommand(
            phase6c.preview_result_id,
            capital.plan_id,
            detail.latest_snapshot.snapshot_id,
            "reject protected reserve tampering",
            "SESSION",
            "PROTECTED-RESERVE-TAMPER",
            "tester",
            NOW,
        )
    )

    assert outcome.status is ResearchAssetCashOperationStatus.INVALID_INPUT
    assert "protected reserve balance" in outcome.summary
    assert store.list_research_asset_cash_results() == ()


def test_persistence_transaction_revalidates_protected_reserve_balance(tmp_path: Path):
    path = tmp_path / "central.sqlite3"
    system = _system(path)
    phase6c, phase6c_store = _build_phase6c(path, system)
    capital, capital_store, detail = _capital(path, system)
    store, coordinator = _build(path, system, phase6c_store, capital_store)
    accepted = coordinator.preview(
        TargetAdjustmentResearchAssetCashPreviewCommand(
            phase6c.preview_result_id,
            capital.plan_id,
            detail.latest_snapshot.snapshot_id,
            "capture valid immutable source",
            "SESSION",
            "VALID-BEFORE-RESERVE-TAMPER",
            "tester",
            NOW,
        )
    )
    persisted = store.get_research_asset_cash_result(accepted.preview_result_id)
    locked = next(
        item
        for item in detail.plan.buckets
        if item.bucket_type is CapitalBucketType.LOCKED_RESERVE
    )
    aapl = next(item for item in detail.plan.buckets if item.symbol == "AAPL")
    with sqlite3.connect(path) as connection:
        connection.execute(
            "UPDATE capital_snapshot_balances SET balance='99' "
            "WHERE snapshot_id=? AND bucket_id=?",
            (str(detail.latest_snapshot.snapshot_id), str(locked.bucket_id)),
        )
        connection.execute(
            "UPDATE capital_snapshot_balances SET balance='4' "
            "WHERE snapshot_id=? AND bucket_id=?",
            (str(detail.latest_snapshot.snapshot_id), str(aapl.bucket_id)),
        )
        connection.commit()

    with sqlite3.connect(path) as connection:
        connection.row_factory = sqlite3.Row
        with pytest.raises(ValueError, match="protected reserve balance"):
            store._validate_capital_current(connection, persisted.source)

    assert store.list_research_asset_cash_results() == (persisted,)


def _create_v12(path: Path) -> None:
    with sqlite3.connect(path) as connection:
        for version in range(1, 13):
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


def test_v12_to_v13_migration_backs_up_preserves_and_has_zero_backfill(tmp_path: Path):
    path, backups = tmp_path / "central.sqlite3", tmp_path / "backups"
    _create_v12(path)

    CentralSQLiteDatabase(path, backup_directory=backups).initialize()

    backup = next(backups.glob("*.sqlite3"))
    assert ".schema-v12-to-v13." in backup.name
    with sqlite3.connect(backup) as connection:
        assert connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 12
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 13
        assert connection.execute("SELECT COUNT(*) FROM market_bars").fetchone()[0] == 1
        for table in (
            "target_adjustment_research_asset_cash_operations",
            "target_adjustment_research_asset_cash_results",
            "target_adjustment_research_asset_cash_rule_results",
            "target_adjustment_research_asset_cash_source_links",
        ):
            assert connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []


def test_failed_v13_migration_rolls_back_to_intact_v12(tmp_path: Path, monkeypatch):
    path, backups = tmp_path / "central.sqlite3", tmp_path / "backups"
    _create_v12(path)
    broken = dict(sqlite_database._MIGRATIONS)
    broken[13] = ("broken v13", broken[13][1] + "\nINVALID SQL;")
    monkeypatch.setattr(sqlite_database, "_MIGRATIONS", broken)

    with pytest.raises(sqlite3.OperationalError):
        CentralSQLiteDatabase(path, backup_directory=backups).initialize()

    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 12
        assert connection.execute("SELECT COUNT(*) FROM market_bars").fetchone()[0] == 1
        assert connection.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE name='target_adjustment_research_asset_cash_results'"
        ).fetchone()[0] == 0
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
