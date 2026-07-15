from __future__ import annotations

import sqlite3
from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

import pytest

from quant_trading.factors import (
    FactorParameter,
    FactorResult,
    FactorSnapshot,
    FactorStatus,
    MarketDataObservation,
    MarketDataWindow,
)
from quant_trading.factors.errors import FactorStorageError
from quant_trading.factors.storage_models import FactorCalculationStatus
from quant_trading.market_history.models import (
    Adjustment,
    DataFeed,
    MarketBar,
    Timeframe,
)
from quant_trading.persistence.factor_sqlite_store import SQLiteFactorSnapshotStore


AS_OF = datetime(2026, 7, 13, 21, 0, tzinfo=UTC)
CALCULATED = datetime(2026, 7, 13, 21, 1, tzinfo=UTC)
BAR_TIME = datetime(2026, 7, 10, 20, 0, tzinfo=UTC)
SNAPSHOT_ID = UUID("00000000-0000-0000-0000-000000000901")
SECOND_SNAPSHOT_ID = UUID("00000000-0000-0000-0000-000000000902")


def _window(
    *,
    symbol: str = "AAPL",
    adjustment: Adjustment = Adjustment.RAW,
    feed: DataFeed = DataFeed.IEX,
) -> MarketDataWindow:
    bar = MarketBar(
        symbol,
        BAR_TIME,
        Decimal("100"),
        Decimal("102"),
        Decimal("99"),
        Decimal("101.25"),
        1_000,
        Decimal("100.75"),
        50,
        Timeframe.DAY,
        adjustment,
        feed,
        "fake",
        CALCULATED,
    )
    return MarketDataWindow(
        symbol,
        AS_OF,
        Timeframe.DAY,
        adjustment,
        feed,
        (MarketDataObservation(bar, AS_OF),),
    )


def _snapshot(
    window: MarketDataWindow,
    *,
    snapshot_id: UUID = SNAPSHOT_ID,
    version: str = "v1",
    value: Decimal = Decimal("1.25"),
) -> FactorSnapshot:
    result = FactorResult(
        window.symbol,
        window.as_of_utc,
        window.timeframe,
        "approved_test_factor",
        version,
        value,
        "score",
        (
            FactorParameter("lookback", 20),
            FactorParameter("threshold", Decimal("0.5")),
            FactorParameter("enabled", True),
            FactorParameter("label", "test"),
        ),
        20,
        FactorStatus.VALID,
        ("TEST_ONLY",),
        CALCULATED,
        BAR_TIME,
        BAR_TIME,
    )
    return FactorSnapshot(
        snapshot_id,
        window.symbol,
        window.as_of_utc,
        window.timeframe,
        (result,),
        CALCULATED,
    )


@pytest.fixture
def factor_store(tmp_path):
    store = SQLiteFactorSnapshotStore(tmp_path / "market_history.sqlite3")
    store.initialize()
    return store


def _save(store, window, snapshot, correlation_id="REQ-TEST"):
    run_id = store.begin_calculation(window, correlation_id=correlation_id)
    stored = store.complete_calculation_success(run_id, snapshot, window)
    return run_id, stored


def test_central_schema_contains_market_and_factor_tables(factor_store) -> None:
    with sqlite3.connect(factor_store.database_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
    assert {
        "schema_migrations",
        "market_bars",
        "data_coverage",
        "fetch_history",
        "factor_snapshots",
        "factor_results",
        "factor_calculation_runs",
    } <= tables


def test_snapshot_round_trip_preserves_decimal_parameters_and_provenance(
    factor_store,
) -> None:
    window = _window()
    run_id, stored = _save(factor_store, window, _snapshot(window))

    loaded = factor_store.query_snapshots(
        symbol="aapl",
        start_time=AS_OF.replace(day=12),
        end_time=AS_OF.replace(day=14),
        timeframe=Timeframe.DAY,
        adjustment=Adjustment.RAW,
        feed=DataFeed.IEX,
    )
    assert loaded == [stored]
    assert loaded[0].results[0].value == Decimal("1.25")
    assert loaded[0].results[0].parameters[1].value == Decimal("0.5")
    run = factor_store.get_calculation_run(run_id)
    assert run is not None
    assert run.status is FactorCalculationStatus.SUCCESS
    assert run.snapshot_id == stored.snapshot_id
    assert run.correlation_id == "REQ-TEST"


def test_identical_recalculation_reuses_result_but_keeps_both_runs(factor_store) -> None:
    window = _window()
    first_run, first = _save(factor_store, window, _snapshot(window), "REQ-1")
    duplicate = replace(_snapshot(window), snapshot_id=SECOND_SNAPSHOT_ID)
    second_run, second = _save(factor_store, window, duplicate, "REQ-2")

    assert second.snapshot_id == first.snapshot_id
    with sqlite3.connect(factor_store.database_path) as connection:
        snapshot_count = connection.execute(
            "SELECT COUNT(*) FROM factor_snapshots"
        ).fetchone()[0]
        result_count = connection.execute(
            "SELECT COUNT(*) FROM factor_results"
        ).fetchone()[0]
        run_count = connection.execute(
            "SELECT COUNT(*) FROM factor_calculation_runs"
        ).fetchone()[0]
    assert (snapshot_count, result_count, run_count) == (1, 1, 2)
    assert factor_store.get_calculation_run(first_run).snapshot_id == first.snapshot_id
    assert factor_store.get_calculation_run(second_run).snapshot_id == first.snapshot_id


def test_factor_versions_and_market_dimensions_do_not_mix(factor_store) -> None:
    raw = _window()
    split = _window(adjustment=Adjustment.SPLIT)
    _save(factor_store, raw, _snapshot(raw, version="v1"))
    _save(
        factor_store,
        raw,
        _snapshot(raw, snapshot_id=SECOND_SNAPSHOT_ID, version="v2"),
    )
    split_snapshot = replace(
        _snapshot(split),
        snapshot_id=UUID("00000000-0000-0000-0000-000000000903"),
    )
    _save(factor_store, split, split_snapshot)

    raw_loaded = factor_store.query_snapshots(
        symbol="AAPL",
        start_time=AS_OF.replace(day=12),
        end_time=AS_OF.replace(day=14),
        adjustment=Adjustment.RAW,
    )
    split_loaded = factor_store.query_snapshots(
        symbol="AAPL",
        start_time=AS_OF.replace(day=12),
        end_time=AS_OF.replace(day=14),
        adjustment=Adjustment.SPLIT,
    )
    assert [item.results[0].factor_version for item in raw_loaded] == ["v1", "v2"]
    assert len(split_loaded) == 1


def test_failed_run_is_audited_without_creating_snapshot(factor_store) -> None:
    run_id = factor_store.begin_calculation(_window(), correlation_id="REQ-FAIL")
    factor_store.complete_calculation_failure(
        run_id,
        error_code="QT-FACTOR-CALC-001",
        error_summary="controlled test failure",
    )
    run = factor_store.get_calculation_run(run_id)
    assert run is not None
    assert run.status is FactorCalculationStatus.FAILED
    assert run.snapshot_id is None
    assert run.error_summary == "controlled test failure"


def test_transaction_failure_preserves_existing_snapshot(factor_store) -> None:
    window = _window()
    _, existing = _save(factor_store, window, _snapshot(window))
    with sqlite3.connect(factor_store.database_path) as connection:
        connection.execute(
            """
            CREATE TRIGGER reject_v2_factor BEFORE INSERT ON factor_results
            WHEN NEW.factor_version = 'v2'
            BEGIN SELECT RAISE(ABORT, 'intentional factor write failure'); END;
            """
        )
    run_id = factor_store.begin_calculation(window)
    with pytest.raises(FactorStorageError):
        factor_store.complete_calculation_success(
            run_id,
            _snapshot(window, snapshot_id=SECOND_SNAPSHOT_ID, version="v2"),
            window,
        )
    loaded = factor_store.query_snapshots(
        symbol="AAPL",
        start_time=AS_OF.replace(day=12),
        end_time=AS_OF.replace(day=14),
    )
    assert loaded == [existing]
    assert factor_store.get_calculation_run(run_id).status is FactorCalculationStatus.RUNNING


def test_existing_market_rows_survive_central_schema_initialization(tmp_path) -> None:
    path = tmp_path / "market_history.sqlite3"
    with sqlite3.connect(path) as connection:
        connection.execute(
            """
            CREATE TABLE market_bars (
                symbol TEXT NOT NULL, timestamp_utc TEXT NOT NULL,
                timeframe TEXT NOT NULL, adjustment TEXT NOT NULL, feed TEXT NOT NULL,
                open TEXT NOT NULL, high TEXT NOT NULL, low TEXT NOT NULL,
                close TEXT NOT NULL, volume INTEGER NOT NULL, vwap TEXT,
                trade_count INTEGER, source TEXT NOT NULL, fetched_at_utc TEXT NOT NULL,
                PRIMARY KEY (symbol, timestamp_utc, timeframe, adjustment, feed)
            )
            """
        )
        connection.execute(
            """
            INSERT INTO market_bars VALUES (
                'AAPL', '2026-07-10T20:00:00+00:00', '1Day', 'raw', 'iex',
                '100', '102', '99', '101', 1000, '100.5', 50, 'legacy',
                '2026-07-13T21:00:00+00:00'
            )
            """
        )
    store = SQLiteFactorSnapshotStore(path)
    store.initialize()
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM market_bars").fetchone()[0] == 1
        assert connection.execute(
            "SELECT COUNT(*) FROM schema_migrations WHERE version = 1"
        ).fetchone()[0] == 1


def test_newer_unknown_schema_is_rejected_without_rewriting_it(tmp_path) -> None:
    path = tmp_path / "market_history.sqlite3"
    with sqlite3.connect(path) as connection:
        connection.execute(
            """
            CREATE TABLE schema_migrations (
                version INTEGER PRIMARY KEY,
                applied_at_utc TEXT NOT NULL,
                description TEXT NOT NULL
            )
            """
        )
        connection.execute(
            "INSERT INTO schema_migrations VALUES (999, '2026-07-14T00:00:00+00:00', 'future')"
        )
    store = SQLiteFactorSnapshotStore(path)
    with pytest.raises(FactorStorageError, match="newer"):
        store.initialize()
    with sqlite3.connect(path) as connection:
        assert connection.execute(
            "SELECT version FROM schema_migrations"
        ).fetchone()[0] == 999
        assert connection.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE name = 'factor_snapshots'"
        ).fetchone()[0] == 0
