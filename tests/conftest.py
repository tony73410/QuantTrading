from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from quant_trading.market_history.models import (
    Adjustment,
    DataFeed,
    HistoricalDataRequest,
    MarketBar,
    Timeframe,
)
from quant_trading.market_history.storage import SQLiteHistoricalDataStore


@pytest.fixture
def store(tmp_path):
    value = SQLiteHistoricalDataStore(tmp_path / "market_history.sqlite3")
    value.initialize()
    return value


def make_request(
    *,
    symbol: str = "AAPL",
    start: datetime = datetime(2024, 1, 1, tzinfo=UTC),
    end: datetime = datetime(2024, 1, 10, tzinfo=UTC),
    timeframe: Timeframe = Timeframe.DAY,
    adjustment: Adjustment = Adjustment.RAW,
    feed: DataFeed = DataFeed.IEX,
    force_refresh: bool = False,
) -> HistoricalDataRequest:
    return HistoricalDataRequest(
        symbol=symbol,
        start_time=start,
        end_time=end,
        timeframe=timeframe,
        adjustment=adjustment,
        feed=feed,
        force_refresh=force_refresh,
    )


def make_bar(
    timestamp: datetime,
    *,
    request: HistoricalDataRequest | None = None,
    symbol: str = "AAPL",
    close: str = "101",
    vwap: str | None = "100.5",
) -> MarketBar:
    if request is not None:
        symbol = request.symbol
        timeframe = request.timeframe
        adjustment = request.adjustment
        feed = request.feed
    else:
        timeframe = Timeframe.DAY
        adjustment = Adjustment.RAW
        feed = DataFeed.IEX
    close_value = Decimal(close)
    return MarketBar(
        symbol=symbol,
        timestamp_utc=timestamp,
        open=Decimal("100"),
        high=max(Decimal("102"), close_value),
        low=Decimal("99"),
        close=close_value,
        volume=1_000,
        vwap=None if vwap is None else Decimal(vwap),
        trade_count=50,
        timeframe=timeframe,
        adjustment=adjustment,
        feed=feed,
        source="fake",
        fetched_at_utc=datetime(2024, 1, 11, tzinfo=UTC),
    )
