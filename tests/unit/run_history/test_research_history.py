from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from quant_trading.decision import (
    DecisionAction,
    DecisionConditionTrace,
    DecisionHistoryQuery,
    DecisionResult,
    DecisionSizingInputSource,
    DecisionSizingInputTrace,
    DecisionStatus,
    DecisionTraceStatus,
    TradeIntent,
)
from quant_trading.factors import (
    FactorSourcePriceStatus,
    FactorHistoryQuery,
    FactorResult,
    FactorSnapshot,
    FactorStatus,
    FactorVersionComparisonQuery,
    FactorVisualizationQuery,
    MarketDataObservation,
    MarketDataWindow,
)
from quant_trading.market_history.models import (
    Adjustment,
    DataFeed,
    MarketBar,
    PriceField,
    Timeframe,
)
from quant_trading.persistence import (
    CentralSQLiteDatabase,
    SQLiteAlgorithmResultStore,
    SQLiteResearchHistoryQueryService,
    SQLiteRunHistoryRepository,
)
from quant_trading.persistence import sqlite_database
from quant_trading.persistence.factor_sqlite_store import SQLiteFactorSnapshotStore
from quant_trading.persistence.sqlite_database import _SCHEMA_V1, _SCHEMA_V2, _SCHEMA_V3
from quant_trading.run_history import (
    AlgorithmRunService,
    AlgorithmRunType,
    RunBindingType,
    RunStageName,
    SoftwareIdentity,
    StartRunRequest,
    WorktreeState,
)


NOW = datetime(2026, 7, 16, 20, 0, tzinfo=UTC)
LEGACY_RUN_ID = UUID("00000000-0000-0000-0000-000000003001")
LEGACY_STAGE_ID = UUID("00000000-0000-0000-0000-000000003002")
LEGACY_DECISION_ID = UUID("00000000-0000-0000-0000-000000003003")


def _create_v2_database(path: Path) -> None:
    with sqlite3.connect(path) as connection:
        connection.executescript(_SCHEMA_V1)
        connection.execute(
            "INSERT INTO schema_migrations VALUES (1, ?, ?)",
            (NOW.isoformat(), "test v1"),
        )
        connection.executescript(_SCHEMA_V2)
        connection.execute(
            "INSERT INTO schema_migrations VALUES (2, ?, ?)",
            (NOW.isoformat(), "test v2"),
        )
        connection.execute(
            """
            INSERT INTO algorithm_runs (
                run_id, parent_run_id, run_type, status, session_id, request_id,
                started_at_utc, completed_at_utc, market_data_as_of_utc,
                portfolio_snapshot_id, configuration_snapshot_id,
                strategy_version_id, trigger_source, execution_mode, created_by,
                software_version, source_revision, worktree_state, notes,
                created_at_utc
            ) VALUES (?, NULL, 'decision_preview', 'completed', 'SESSION', 'REQUEST',
                      ?, ?, ?, NULL, NULL, NULL, 'test', 'no_execution', 'tester',
                      '0.1.0', NULL, 'clean', NULL, ?)
            """,
            (
                str(LEGACY_RUN_ID),
                NOW.isoformat(),
                NOW.isoformat(),
                NOW.isoformat(),
                NOW.isoformat(),
            ),
        )
        connection.execute(
            """
            INSERT INTO algorithm_run_stages (
                stage_id, run_id, stage_name, sequence, status, started_at_utc,
                completed_at_utc, result_type, result_id, error_code, error_summary
            ) VALUES (?, ?, 'decision', 1, 'completed', ?, ?,
                      'decision_result', ?, NULL, NULL)
            """,
            (
                str(LEGACY_STAGE_ID),
                str(LEGACY_RUN_ID),
                NOW.isoformat(),
                NOW.isoformat(),
                str(LEGACY_DECISION_ID),
            ),
        )
        connection.execute(
            """
            INSERT INTO decision_results (
                decision_id, run_id, stage_id, as_of_utc, policy_name,
                policy_version, policy_parameters_json, status,
                reason_codes_json, created_at_utc
            ) VALUES (?, ?, ?, ?, 'legacy_policy', '1', '[]',
                      'no_decision', '["LEGACY"]', ?)
            """,
            (
                str(LEGACY_DECISION_ID),
                str(LEGACY_RUN_ID),
                str(LEGACY_STAGE_ID),
                NOW.isoformat(),
                NOW.isoformat(),
            ),
        )
        connection.commit()


def test_schema_v2_to_current_migration_backs_up_and_marks_legacy_trace(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "central.sqlite3"
    backup_path = tmp_path / "backups"
    _create_v2_database(database_path)

    CentralSQLiteDatabase(
        database_path, backup_directory=backup_path
    ).initialize()

    backups = tuple(backup_path.glob("*.sqlite3"))
    assert len(backups) == 1
    assert ".schema-v2-to-v13." in backups[0].name
    with sqlite3.connect(backups[0]) as backup:
        assert backup.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 2
        assert backup.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    with sqlite3.connect(database_path) as connection:
        assert connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 13
        trace = connection.execute(
            "SELECT trace_status FROM decision_results WHERE decision_id = ?",
            (str(LEGACY_DECISION_ID),),
        ).fetchone()[0]
        assert trace == DecisionTraceStatus.TRACE_NOT_CAPTURED.value
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"

    records = SQLiteResearchHistoryQueryService(database_path).query_decision_history(
        DecisionHistoryQuery(policy_name="legacy_policy", policy_version="1")
    )
    assert len(records) == 1
    assert records[0].trace_status is DecisionTraceStatus.TRACE_NOT_CAPTURED
    assert records[0].condition_traces == ()


def test_failed_v3_migration_rolls_back_to_intact_v2(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database_path = tmp_path / "central.sqlite3"
    backup_path = tmp_path / "backups"
    _create_v2_database(database_path)
    broken = dict(sqlite_database._MIGRATIONS)
    broken[3] = ("intentionally broken v3", _SCHEMA_V3 + "\nINVALID SQL;")
    monkeypatch.setattr(sqlite_database, "_MIGRATIONS", broken)

    with pytest.raises(sqlite3.OperationalError):
        CentralSQLiteDatabase(
            database_path, backup_directory=backup_path
        ).initialize()

    assert len(tuple(backup_path.glob("*.sqlite3"))) == 1
    with sqlite3.connect(database_path) as connection:
        assert connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 2
        columns = {
            row[1] for row in connection.execute("PRAGMA table_info(decision_results)")
        }
        assert "trace_status" not in columns
        assert connection.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE name = 'decision_condition_results'"
        ).fetchone()[0] == 0
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def _window() -> MarketDataWindow:
    bar = MarketBar(
        "AAPL",
        NOW,
        Decimal("100"),
        Decimal("101"),
        Decimal("99"),
        Decimal("100.5"),
        10,
        None,
        None,
        Timeframe.DAY,
        Adjustment.RAW,
        DataFeed.IEX,
        "test",
        NOW,
    )
    return MarketDataWindow(
        "AAPL",
        NOW,
        Timeframe.DAY,
        Adjustment.RAW,
        DataFeed.IEX,
        (MarketDataObservation(bar, NOW),),
    )


def _start_run(repository: SQLiteRunHistoryRepository, request_id: str):
    service = AlgorithmRunService(repository, clock=lambda: NOW)
    run = service.start_run(
        StartRunRequest(
            AlgorithmRunType.FACTOR_PREVIEW,
            "SESSION",
            request_id,
            NOW,
            ("AAPL",),
            "test",
            "tester",
            SoftwareIdentity("0.1.0", "abc", WorktreeState.CLEAN),
        )
    )
    return service, run


def _persist_factor_version(
    database_path: Path,
    repository: SQLiteRunHistoryRepository,
    *,
    version: str,
    value: Decimal | None,
    status: FactorStatus,
) -> tuple[UUID, UUID]:
    service, run = _start_run(repository, f"REQ-{version}")
    service.bind(run.run_id, RunBindingType.FACTOR_DEFINITION, "research_factor", version)
    stage = service.start_stage(run.run_id, RunStageName.FACTOR, 1)
    store = SQLiteFactorSnapshotStore(database_path)
    calculation_id = store.begin_calculation(
        _window(), algorithm_run_id=run.run_id, stage_id=stage.stage_id
    )
    snapshot = FactorSnapshot(
        uuid4(),
        "AAPL",
        NOW,
        Timeframe.DAY,
        (
            FactorResult(
                "AAPL", NOW, Timeframe.DAY, "research_factor", version,
                value, "score", (), 1, status, (), NOW, NOW, NOW,
            ),
        ),
        NOW,
    )
    stored = store.complete_calculation_success(calculation_id, snapshot, _window())
    service.complete_stage(stage, result_type="factor_snapshot", result_id=str(stored.snapshot_id))
    service.complete_run(run.run_id)
    return run.run_id, calculation_id


def test_factor_history_includes_valid_invalid_failed_and_exact_version_compare(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "central.sqlite3"
    repository = SQLiteRunHistoryRepository(database_path)
    repository.initialize()
    run_v1, _ = _persist_factor_version(
        database_path,
        repository,
        version="1",
        value=Decimal("1.5"),
        status=FactorStatus.VALID,
    )
    _persist_factor_version(
        database_path,
        repository,
        version="2",
        value=None,
        status=FactorStatus.INVALID_INPUT,
    )
    service, failed_run = _start_run(repository, "REQ-3")
    service.bind(failed_run.run_id, RunBindingType.FACTOR_DEFINITION, "research_factor", "3")
    stage = service.start_stage(failed_run.run_id, RunStageName.FACTOR, 1)
    store = SQLiteFactorSnapshotStore(database_path)
    calculation_id = store.begin_calculation(
        _window(), algorithm_run_id=failed_run.run_id, stage_id=stage.stage_id
    )
    store.complete_calculation_failure(
        calculation_id, error_code="TEST-FACTOR", error_summary="expected failure"
    )
    service.fail_stage(stage, error_code="TEST-FACTOR", error_summary="expected failure")
    service.fail_run(
        failed_run.run_id, error_code="TEST-RUN", error_summary="expected failure"
    )

    queries = SQLiteResearchHistoryQueryService(database_path)
    records = queries.query_factor_history(
        FactorHistoryQuery(symbol="aapl", factor_name="research_factor")
    )
    assert len(records) == 3
    by_version = {record.factor_version: record for record in records}
    assert by_version["1"].value == Decimal("1.5")
    assert by_version["1"].algorithm_run_id == run_v1
    assert by_version["2"].result_status is FactorStatus.INVALID_INPUT
    assert by_version["2"].value is None
    assert by_version["3"].calculation_status.value == "failed"
    assert by_version["3"].error_code == "TEST-FACTOR"
    assert by_version["3"].snapshot_id is None

    comparison = queries.compare_factor_versions(
        FactorVersionComparisonQuery("AAPL", "research_factor", ("1", "2"))
    )
    assert len(comparison) == 1
    assert comparison[0].values[0].value == Decimal("1.5")
    assert comparison[0].values[1].status is FactorStatus.INVALID_INPUT


def test_factor_visualization_joins_only_exact_source_bar_identity(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "central.sqlite3"
    repository = SQLiteRunHistoryRepository(database_path)
    repository.initialize()
    _persist_factor_version(
        database_path,
        repository,
        version="1",
        value=Decimal("1.5"),
        status=FactorStatus.VALID,
    )
    exact_timestamp = NOW.isoformat(timespec="microseconds")
    nearby_timestamp = (NOW - timedelta(minutes=1)).isoformat(timespec="microseconds")
    with sqlite3.connect(database_path) as connection:
        connection.executemany(
            """
            INSERT INTO market_bars (
                symbol, timestamp_utc, timeframe, adjustment, feed,
                open, high, low, close, volume, vwap, trade_count,
                source, fetched_at_utc
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                (
                    "AAPL", exact_timestamp, "1Day", "raw", "iex",
                    "100", "101", "99", "100.5000", 10, None, None,
                    "test", exact_timestamp,
                ),
                (
                    "AAPL", nearby_timestamp, "1Day", "raw", "iex",
                    "999", "999", "999", "999", 10, "999", None,
                    "test", exact_timestamp,
                ),
                (
                    "AAPL", exact_timestamp, "1Day", "raw", "sip",
                    "888", "888", "888", "888", 10, "888", None,
                    "test", exact_timestamp,
                ),
            ),
        )
        connection.commit()

    queries = SQLiteResearchHistoryQueryService(database_path)
    base = dict(
        symbol="AAPL",
        factor_name="research_factor",
        factor_version="1",
        start_time_utc=NOW - timedelta(days=1),
        end_time_utc=NOW + timedelta(days=1),
        timeframe=Timeframe.DAY,
        adjustment=Adjustment.RAW,
        feed=DataFeed.IEX,
    )
    close = queries.query_factor_visualization(
        FactorVisualizationQuery(**base, price_field=PriceField.CLOSE)
    )
    assert close.count == 1
    assert close.points[0].price_value == Decimal("100.5000")
    assert close.points[0].source_bar_timestamp_utc == NOW
    assert close.points[0].source_price_status is FactorSourcePriceStatus.AVAILABLE

    vwap = queries.query_factor_visualization(
        FactorVisualizationQuery(**base, price_field=PriceField.VWAP)
    )
    assert vwap.points[0].price_value is None
    assert vwap.points[0].source_bar_timestamp_utc == NOW
    assert vwap.points[0].source_price_status is FactorSourcePriceStatus.MISSING_PRICE_FIELD

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            DELETE FROM market_bars
            WHERE symbol = 'AAPL' AND timestamp_utc = ?
              AND timeframe = '1Day' AND adjustment = 'raw' AND feed = 'iex'
            """,
            (exact_timestamp,),
        )
        connection.commit()
    missing = queries.query_factor_visualization(
        FactorVisualizationQuery(**base, price_field=PriceField.CLOSE)
    )
    assert missing.points[0].price_value is None
    assert missing.points[0].source_price_status is FactorSourcePriceStatus.MISSING_SOURCE_BAR


def test_decision_condition_and_sizing_trace_reload_and_open_run_artifacts(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "central.sqlite3"
    repository = SQLiteRunHistoryRepository(database_path)
    repository.initialize()
    service = AlgorithmRunService(repository, clock=lambda: NOW)
    run = service.start_run(
        StartRunRequest(
            AlgorithmRunType.DECISION_PREVIEW,
            "SESSION",
            "REQ-DECISION",
            NOW,
            ("AAPL",),
            "test",
            "tester",
            SoftwareIdentity("0.1.0", "abc", WorktreeState.CLEAN),
        )
    )
    factor_stage = service.start_stage(run.run_id, RunStageName.FACTOR, 1)
    factor_store = SQLiteFactorSnapshotStore(database_path)
    calculation_id = factor_store.begin_calculation(
        _window(), algorithm_run_id=run.run_id, stage_id=factor_stage.stage_id
    )
    snapshot = FactorSnapshot(
        uuid4(),
        "AAPL",
        NOW,
        Timeframe.DAY,
        (
            FactorResult(
                "AAPL", NOW, Timeframe.DAY, "deviation", "1",
                Decimal("-2.4"), "zscore", (), 20, FactorStatus.VALID,
                (), NOW, NOW, NOW,
            ),
        ),
        NOW,
    )
    stored = factor_store.complete_calculation_success(calculation_id, snapshot, _window())
    service.complete_stage(
        factor_stage, result_type="factor_snapshot", result_id=str(stored.snapshot_id)
    )
    decision_stage = service.start_stage(run.run_id, RunStageName.DECISION, 2)
    decision_id = uuid4()
    trace = DecisionConditionTrace(
        0,
        "user_factor.deviation.v1",
        "deviation",
        "1",
        stored.snapshot_id,
        Decimal("-2.4"),
        "zscore",
        FactorStatus.VALID,
        "<=",
        Decimal("-2"),
        True,
    )
    sizing_input = DecisionSizingInputTrace(
        "account.cash", DecisionSizingInputSource.ACCOUNT, Decimal("1000")
    )
    intent_id = uuid4()
    intent = TradeIntent(
        intent_id,
        decision_id,
        "AAPL",
        NOW,
        DecisionAction.INCREASE,
        None,
        None,
        None,
        None,
        None,
        ("TEST_MATCH",),
        stored.snapshot_id,
        "test_policy",
        "1",
        NOW,
        requested_notional=Decimal("100"),
        notional_currency="USD",
        sizing_mode="percent_available_cash",
        sizing_references=("account.cash",),
        sizing_inputs=(sizing_input,),
    )
    result = DecisionResult(
        decision_id,
        NOW,
        "test_policy",
        "1",
        (),
        (stored.snapshot_id,),
        DecisionStatus.VALID,
        (intent,),
        ("TEST_MATCH",),
        NOW,
        (trace,),
        DecisionTraceStatus.CAPTURED,
    )
    SQLiteAlgorithmResultStore(database_path).save_decision_result(
        algorithm_run_id=run.run_id,
        stage_id=decision_stage.stage_id,
        result=result,
    )
    service.complete_stage(
        decision_stage, result_type="decision_result", result_id=str(decision_id)
    )
    service.complete_run(run.run_id)

    records = SQLiteResearchHistoryQueryService(database_path).query_decision_history(
        DecisionHistoryQuery(symbol="AAPL", policy_name="test_policy", policy_version="1")
    )
    assert len(records) == 1
    reloaded = records[0]
    assert reloaded.trace_status is DecisionTraceStatus.CAPTURED
    assert reloaded.condition_traces == (trace,)
    assert reloaded.factor_inputs[0].value == Decimal("-2.4")
    assert reloaded.intents[0].sizing_inputs == (sizing_input,)

    detail = SQLiteRunHistoryRepository(database_path).get_run_detail(run.run_id)
    assert detail is not None
    decision_artifact = next(
        item for item in detail.artifacts if item.artifact_type == "decision_result"
    )
    assert {child.artifact_type for child in decision_artifact.children} == {
        "decision_condition",
        "trade_intent",
    }
    trade_intent = next(
        child for child in decision_artifact.children if child.artifact_type == "trade_intent"
    )
    assert trade_intent.children[0].summary == "account.cash = 1000"
