from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from uuid import UUID

import pytest

from quant_trading.application_settings import ExecutionEnvironment
from quant_trading.decision import (
    DecisionAction,
    DecisionResult,
    DecisionStatus,
    TradeIntent,
)
from quant_trading.factors import (
    FactorResult,
    FactorSnapshot,
    FactorStatus,
    MarketDataObservation,
    MarketDataWindow,
)
from quant_trading.market_history.models import Adjustment, DataFeed, MarketBar, Timeframe
from quant_trading.persistence import (
    CentralSQLiteDatabase,
    SQLiteAlgorithmResultStore,
    SQLiteRunHistoryRepository,
)
from quant_trading.persistence.factor_sqlite_store import SQLiteFactorSnapshotStore
from quant_trading.persistence import sqlite_database
from quant_trading.persistence.sqlite_database import _SCHEMA_V1, _SCHEMA_V2
from quant_trading.risk import (
    RiskDecision,
    RiskDecisionType,
    RiskEvaluationStatus,
    RiskReasonCode,
)
from quant_trading.run_history import (
    AlgorithmRunService,
    AlgorithmRunStatus,
    AlgorithmRunType,
    RunBindingType,
    RunQuery,
    RunStageName,
    SoftwareIdentity,
    StartRunRequest,
    WorktreeState,
)


NOW = datetime(2026, 7, 16, 18, 0, tzinfo=UTC)
SNAPSHOT_ID = UUID("00000000-0000-0000-0000-000000001001")
DECISION_ID = UUID("00000000-0000-0000-0000-000000001002")
INTENT_ID = UUID("00000000-0000-0000-0000-000000001003")
RISK_ID = UUID("00000000-0000-0000-0000-000000001004")
PORTFOLIO_ID = UUID("00000000-0000-0000-0000-000000001005")
ACCOUNT_ID = UUID("00000000-0000-0000-0000-000000001006")


def test_schema_v1_to_current_migration_backs_up_and_preserves_rows(tmp_path: Path) -> None:
    database_path = tmp_path / "central.sqlite3"
    backup_path = tmp_path / "migration_backups"
    with sqlite3.connect(database_path) as connection:
        connection.executescript(_SCHEMA_V1)
        connection.execute(
            "INSERT INTO schema_migrations VALUES (1, ?, ?)",
            (NOW.isoformat(), "test v1"),
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

    CentralSQLiteDatabase(
        database_path, backup_directory=backup_path
    ).initialize()

    backups = tuple(backup_path.glob("*.sqlite3"))
    assert len(backups) == 1
    with sqlite3.connect(backups[0]) as backup:
        assert backup.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert backup.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 1
        assert backup.execute("SELECT COUNT(*) FROM market_bars").fetchone()[0] == 1
    with sqlite3.connect(database_path) as connection:
        assert connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 13
        assert connection.execute("SELECT COUNT(*) FROM market_bars").fetchone()[0] == 1
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def test_failed_v2_migration_rolls_back_to_intact_v1(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database_path = tmp_path / "central.sqlite3"
    backup_path = tmp_path / "migration_backups"
    with sqlite3.connect(database_path) as connection:
        connection.executescript(_SCHEMA_V1)
        connection.execute(
            "INSERT INTO schema_migrations VALUES (1, ?, ?)",
            (NOW.isoformat(), "test v1"),
        )
        connection.commit()
    broken = dict(sqlite_database._MIGRATIONS)
    broken[2] = ("intentionally broken test migration", _SCHEMA_V2 + "\nINVALID SQL;")
    monkeypatch.setattr(sqlite_database, "_MIGRATIONS", broken)

    with pytest.raises(sqlite3.OperationalError):
        CentralSQLiteDatabase(
            database_path, backup_directory=backup_path
        ).initialize()

    assert len(tuple(backup_path.glob("*.sqlite3"))) == 1
    with sqlite3.connect(database_path) as connection:
        assert connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 1
        assert connection.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type = 'table' AND name = 'algorithm_runs'"
        ).fetchone()[0] == 0
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def test_current_schema_initialization_rejects_a_missing_required_table(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "central.sqlite3"
    database = CentralSQLiteDatabase(database_path)
    database.initialize()
    missing_table = "target_adjustment_research_asset_cash_rule_results"
    with sqlite3.connect(database_path) as connection:
        connection.execute(f'DROP TABLE "{missing_table}"')
        connection.commit()

    with pytest.raises(
        sqlite3.DatabaseError,
        match=f"database schema is missing required tables: {missing_table}",
    ):
        database.initialize()


def test_incomplete_old_schema_is_rejected_before_any_forward_migration(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "central.sqlite3"
    with sqlite3.connect(database_path) as connection:
        connection.executescript(_SCHEMA_V1)
        connection.execute(
            "INSERT INTO schema_migrations VALUES (1, ?, ?)",
            (NOW.isoformat(), "test v1"),
        )
        connection.execute("DROP TABLE factor_results")
        connection.commit()

    with pytest.raises(
        sqlite3.DatabaseError,
        match="database schema is missing required tables: factor_results",
    ):
        CentralSQLiteDatabase(database_path).initialize()

    with sqlite3.connect(database_path) as connection:
        assert connection.execute(
            "SELECT MAX(version) FROM schema_migrations"
        ).fetchone()[0] == 1
        assert connection.execute(
            """
            SELECT COUNT(*) FROM sqlite_master
            WHERE type = 'table' AND name = 'algorithm_runs'
            """
        ).fetchone()[0] == 0


def test_current_schema_initialization_rejects_a_migration_history_gap(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "central.sqlite3"
    database = CentralSQLiteDatabase(database_path)
    database.initialize()
    with sqlite3.connect(database_path) as connection:
        connection.execute("DELETE FROM schema_migrations WHERE version = 7")
        connection.commit()

    with pytest.raises(
        sqlite3.DatabaseError,
        match="database schema migration history is incomplete",
    ):
        database.initialize()

    with sqlite3.connect(database_path) as connection:
        versions = tuple(
            row[0]
            for row in connection.execute(
                "SELECT version FROM schema_migrations ORDER BY version"
            )
        )
    assert 7 not in versions
    assert versions[-1] == 13


def _start_run(repository: SQLiteRunHistoryRepository):
    service = AlgorithmRunService(repository, clock=lambda: NOW)
    run = service.start_run(
        StartRunRequest(
            AlgorithmRunType.FULL_PIPELINE_PREVIEW,
            "SESSION-1",
            "REQUEST-1",
            NOW,
            ("AAPL",),
            "algorithm_control",
            "local_user",
            SoftwareIdentity("0.1.0", "abc123", WorktreeState.CLEAN),
        )
    )
    service.bind(run.run_id, RunBindingType.DECISION_DEFINITION, "policy", "v1")
    return service, run


def _persist_factor(
    database_path: Path,
    *,
    algorithm_run_id: UUID,
    stage_id: UUID,
) -> FactorSnapshot:
    bar = MarketBar(
        "AAPL", NOW, Decimal("100"), Decimal("101"), Decimal("99"),
        Decimal("100.5"), 10, None, None, Timeframe.DAY,
        Adjustment.RAW, DataFeed.IEX, "test", NOW,
    )
    window = MarketDataWindow(
        "AAPL", NOW, Timeframe.DAY, Adjustment.RAW, DataFeed.IEX,
        (MarketDataObservation(bar, NOW),),
    )
    result = FactorResult(
        "AAPL", NOW, Timeframe.DAY, "test_factor", "v1", Decimal("1.5"),
        "score", (), 1, FactorStatus.VALID, (), NOW, NOW, NOW,
    )
    snapshot = FactorSnapshot(
        SNAPSHOT_ID, "AAPL", NOW, Timeframe.DAY, (result,), NOW
    )
    store = SQLiteFactorSnapshotStore(database_path)
    calculation_id = store.begin_calculation(
        window,
        correlation_id="REQUEST-1",
        algorithm_run_id=algorithm_run_id,
        stage_id=stage_id,
    )
    return store.complete_calculation_success(calculation_id, snapshot, window)


def test_run_and_domain_results_reload_as_typed_detail(tmp_path: Path) -> None:
    database_path = tmp_path / "central.sqlite3"
    repository = SQLiteRunHistoryRepository(database_path)
    repository.initialize()
    service, run = _start_run(repository)
    factor_stage = service.start_stage(run.run_id, RunStageName.FACTOR, 1)
    snapshot = _persist_factor(
        database_path,
        algorithm_run_id=run.run_id,
        stage_id=factor_stage.stage_id,
    )
    service.complete_stage(
        factor_stage, result_type="factor_snapshot", result_id=str(snapshot.snapshot_id)
    )

    result_store = SQLiteAlgorithmResultStore(database_path)
    decision_stage = service.start_stage(run.run_id, RunStageName.DECISION, 2)
    intent = TradeIntent(
        INTENT_ID, DECISION_ID, "AAPL", NOW, DecisionAction.INCREASE,
        Decimal("0.2"), Decimal("0.3"), Decimal("0.1"), "portfolio_fraction",
        Decimal("0.8"), ("TEST",), snapshot.snapshot_id,
        "test_policy", "v1", NOW,
    )
    decision = DecisionResult(
        DECISION_ID, NOW, "test_policy", "v1", (), (snapshot.snapshot_id,),
        DecisionStatus.VALID, (intent,), ("TEST",), NOW,
    )
    result_store.save_decision_result(
        algorithm_run_id=run.run_id,
        stage_id=decision_stage.stage_id,
        result=decision,
    )
    service.complete_stage(
        decision_stage, result_type="decision_result", result_id=str(DECISION_ID)
    )

    risk_stage = service.start_stage(run.run_id, RunStageName.RISK, 3)
    risk = RiskDecision(
        RISK_ID, INTENT_ID, "AAPL", NOW,
        RiskDecisionType.MANUAL_REVIEW_REQUIRED,
        Decimal("0.2"), Decimal("0.3"), None, Decimal("0.1"), None,
        "portfolio_fraction", RiskEvaluationStatus.EVALUATED,
        (RiskReasonCode.MANUAL_REVIEW,), (), ("NO NUMERIC RULES",),
        True, False, False, "empty_dry_run_policy", "v1", "v1",
        PORTFOLIO_ID, ACCOUNT_ID, ExecutionEnvironment.ALPACA_PAPER,
    )
    result_store.save_risk_decision(
        algorithm_run_id=run.run_id, stage_id=risk_stage.stage_id, decision=risk
    )
    service.complete_stage(
        risk_stage, result_type="risk_decision", result_id=str(RISK_ID),
        with_warnings=True,
    )
    service.complete_run(run.run_id, with_warnings=True)

    reloaded = SQLiteRunHistoryRepository(database_path)
    summaries = reloaded.list_runs(RunQuery(symbol="aapl"))
    assert len(summaries) == 1
    assert summaries[0].run.status is AlgorithmRunStatus.COMPLETED_WITH_WARNINGS
    assert summaries[0].symbols == ("AAPL",)
    detail = reloaded.get_run_detail(run.run_id)
    assert detail is not None
    assert [stage.name for stage in detail.stages] == [
        RunStageName.FACTOR, RunStageName.DECISION, RunStageName.RISK
    ]
    assert [artifact.artifact_type for artifact in detail.artifacts] == [
        "factor_calculation", "decision_result", "risk_decision"
    ]
    assert detail.artifacts[0].children[0].summary.endswith("= 1.5")
    assert detail.artifacts[1].children[0].artifact_id == str(INTENT_ID)
    assert detail.artifacts[2].status == "manual_review_required"


def test_failed_run_is_saved_and_reloadable(tmp_path: Path) -> None:
    repository = SQLiteRunHistoryRepository(tmp_path / "central.sqlite3")
    repository.initialize()
    service, run = _start_run(repository)
    stage = service.start_stage(run.run_id, RunStageName.FACTOR, 1)
    service.fail_stage(stage, error_code="TEST-FAIL", error_summary="expected failure")
    service.fail_run(run.run_id, error_code="TEST-RUN-FAIL", error_summary="failed")

    detail = repository.get_run_detail(run.run_id)
    assert detail is not None
    assert detail.summary.run.status is AlgorithmRunStatus.FAILED
    assert detail.summary.error_count == 2
    assert {message.code for message in detail.messages} == {
        "TEST-FAIL", "TEST-RUN-FAIL"
    }
