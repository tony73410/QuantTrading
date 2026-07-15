from __future__ import annotations

import sqlite3
from datetime import UTC, datetime

import pytest

from conftest import make_bar, make_request
from quant_trading.market_history.errors import StorageError
from quant_trading.market_history.models import Adjustment, CoverageInterval, DataFeed, Timeframe


def save_interval(store, request, start, end, bars):
    fetch_id = store.begin_fetch(request.with_range(start, end))
    store.complete_fetch_success(
        fetch_id,
        request.with_range(start, end),
        CoverageInterval(start, end),
        bars,
    )


def test_insert_and_read_bars(store):
    request = make_request()
    bar = make_bar(datetime(2024, 1, 2, tzinfo=UTC), request=request)
    save_interval(store, request, request.start_time, request.end_time, [bar])
    assert store.query_bars(request) == [bar]


def test_schema_contains_required_tables_and_query_indexes(store):
    with sqlite3.connect(store.database_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        indexes = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'index'"
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
    assert {
        "idx_market_bars_lookup",
        "idx_data_coverage_lookup",
        "idx_fetch_history_lookup",
    } <= indexes


def test_duplicate_unique_bar_is_upserted(store):
    request = make_request()
    timestamp = datetime(2024, 1, 2, tzinfo=UTC)
    save_interval(store, request, request.start_time, request.end_time, [make_bar(timestamp, request=request)])
    save_interval(
        store,
        request,
        request.start_time,
        request.end_time,
        [make_bar(timestamp, request=request, close="105")],
    )
    bars = store.query_bars(request)
    assert len(bars) == 1
    assert str(bars[0].close) == "105"


@pytest.mark.parametrize(
    ("different", "value"),
    [
        ("symbol", "MSFT"),
        ("timeframe", Timeframe.WEEK),
        ("adjustment", Adjustment.SPLIT),
        ("feed", DataFeed.SIP),
    ],
)
def test_dimensions_do_not_mix(store, different, value):
    base = make_request()
    options = {different: value}
    other = make_request(**options)
    timestamp = datetime(2024, 1, 2, tzinfo=UTC)
    save_interval(store, base, base.start_time, base.end_time, [make_bar(timestamp, request=base)])
    save_interval(store, other, other.start_time, other.end_time, [make_bar(timestamp, request=other)])
    assert len(store.query_bars(base)) == 1
    assert len(store.query_bars(other)) == 1
    assert store.query_bars(base)[0].symbol == "AAPL"


@pytest.mark.parametrize(
    "timeframe",
    [Timeframe.TEN_MINUTES, Timeframe.THIRTY_MINUTES, Timeframe.HOUR],
)
def test_intraday_timeframes_are_stored_separately(store, timeframe):
    daily = make_request()
    intraday = make_request(timeframe=timeframe)
    timestamp = datetime(2024, 1, 2, tzinfo=UTC)

    save_interval(
        store,
        daily,
        daily.start_time,
        daily.end_time,
        [make_bar(timestamp, request=daily)],
    )
    save_interval(
        store,
        intraday,
        intraday.start_time,
        intraday.end_time,
        [make_bar(timestamp, request=intraday)],
    )

    assert store.query_bars(daily)[0].timeframe is Timeframe.DAY
    assert store.query_bars(intraday)[0].timeframe is timeframe


def test_time_range_query_is_end_exclusive(store):
    request = make_request()
    bars = [
        make_bar(datetime(2024, 1, day, tzinfo=UTC), request=request)
        for day in (2, 4, 6)
    ]
    save_interval(store, request, request.start_time, request.end_time, bars)
    subset = make_request(
        start=datetime(2024, 1, 4, tzinfo=UTC),
        end=datetime(2024, 1, 6, tzinfo=UTC),
    )
    assert [bar.timestamp_utc.day for bar in store.query_bars(subset)] == [4]


def test_transaction_failure_preserves_existing_data_and_coverage(store):
    base = make_request()
    existing = make_bar(datetime(2024, 1, 2, tzinfo=UTC), request=base)
    save_interval(store, base, base.start_time, base.end_time, [existing])
    with sqlite3.connect(store.database_path) as connection:
        connection.execute(
            """
            CREATE TRIGGER reject_fail_symbol BEFORE INSERT ON market_bars
            WHEN NEW.symbol = 'FAIL'
            BEGIN SELECT RAISE(ABORT, 'intentional test failure'); END;
            """
        )
    failing = make_request(symbol="FAIL")
    fetch_id = store.begin_fetch(failing)
    with pytest.raises(StorageError):
        store.complete_fetch_success(
            fetch_id,
            failing,
            CoverageInterval(failing.start_time, failing.end_time),
            [make_bar(datetime(2024, 1, 2, tzinfo=UTC), request=failing)],
        )
    assert store.query_bars(base) == [existing]
    assert store.get_coverage(failing) == []


def test_adjacent_coverage_intervals_merge(store):
    request = make_request()
    middle = datetime(2024, 1, 5, tzinfo=UTC)
    save_interval(store, request, request.start_time, middle, [])
    save_interval(store, request, middle, request.end_time, [])
    assert store.get_coverage(request) == [
        CoverageInterval(request.start_time, request.end_time)
    ]


def test_failed_fetch_does_not_update_coverage(store):
    request = make_request()
    fetch_id = store.begin_fetch(request)
    store.complete_fetch_failure(fetch_id, "temporary failure")
    assert store.get_coverage(request) == []
    with sqlite3.connect(store.database_path) as connection:
        status, summary = connection.execute(
            "SELECT status, error_summary FROM fetch_history WHERE request_id = ?",
            (str(fetch_id),),
        ).fetchone()
    assert status == "failed"
    assert summary == "temporary failure"
