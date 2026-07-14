"""Explicit domain models shared across market-history components."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from enum import StrEnum
from typing import Iterable

from .errors import DataValidationError, RequestValidationError


_SYMBOL_PATTERN = re.compile(r"^[A-Z][A-Z0-9.\-]{0,14}$")


class Timeframe(StrEnum):
    TEN_MINUTES = "10Min"
    THIRTY_MINUTES = "30Min"
    HOUR = "1Hour"
    DAY = "1Day"
    WEEK = "1Week"
    MONTH = "1Month"

    @property
    def approximate_duration(self) -> timedelta:
        return {
            Timeframe.TEN_MINUTES: timedelta(minutes=10),
            Timeframe.THIRTY_MINUTES: timedelta(minutes=30),
            Timeframe.HOUR: timedelta(hours=1),
            Timeframe.DAY: timedelta(days=1),
            Timeframe.WEEK: timedelta(days=7),
            Timeframe.MONTH: timedelta(days=31),
        }[self]

    @property
    def is_intraday(self) -> bool:
        return self in {
            Timeframe.TEN_MINUTES,
            Timeframe.THIRTY_MINUTES,
            Timeframe.HOUR,
        }

    @property
    def maximum_request_duration(self) -> timedelta | None:
        return {
            Timeframe.TEN_MINUTES: timedelta(days=366),
            Timeframe.THIRTY_MINUTES: timedelta(days=366 * 5),
            Timeframe.HOUR: timedelta(days=366 * 5),
            Timeframe.DAY: None,
            Timeframe.WEEK: None,
            Timeframe.MONTH: None,
        }[self]


class Adjustment(StrEnum):
    RAW = "raw"
    SPLIT = "split"
    DIVIDEND = "dividend"
    ALL = "all"


class DataFeed(StrEnum):
    IEX = "iex"
    SIP = "sip"


class ChartType(StrEnum):
    CANDLESTICK = "candlestick"
    LINE = "line"
    OHLC = "ohlc"


class PriceField(StrEnum):
    OPEN = "open"
    HIGH = "high"
    LOW = "low"
    CLOSE = "close"
    VWAP = "vwap"


class DataSource(StrEnum):
    LOCAL_CACHE = "Local cache"
    API_UPDATE = "API update"
    LOCAL_AND_API = "Local cache + API update"
    STALE_LOCAL = "Stale local cache"
    OFFLINE_LOCAL = "Offline local cache"


class FetchStatus(StrEnum):
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


def ensure_utc(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise RequestValidationError(f"{field_name} must include a timezone")
    return value.astimezone(UTC)


@dataclass(frozen=True, slots=True)
class HistoricalDataRequest:
    symbol: str
    start_time: datetime
    end_time: datetime
    timeframe: Timeframe = Timeframe.DAY
    adjustment: Adjustment = Adjustment.RAW
    feed: DataFeed = DataFeed.IEX
    force_refresh: bool = False

    def __post_init__(self) -> None:
        symbol = self.symbol.strip().upper()
        start = ensure_utc(self.start_time, "start_time")
        end = ensure_utc(self.end_time, "end_time")
        if not symbol or not _SYMBOL_PATTERN.fullmatch(symbol):
            raise RequestValidationError("symbol is empty or malformed")
        if start >= end:
            raise RequestValidationError("start_time must be before end_time")
        if end > datetime.now(UTC) + timedelta(days=1):
            raise RequestValidationError("end_time is unreasonably far in the future")
        maximum_duration = self.timeframe.maximum_request_duration
        if maximum_duration is not None and end - start > maximum_duration:
            friendly_limit = (
                "1 年" if self.timeframe is Timeframe.TEN_MINUTES else "5 年"
            )
            raise RequestValidationError(
                f"{self.timeframe.value} request exceeds {maximum_duration}",
                user_message=(
                    f"{self.timeframe.value} 数据量较大，单次最多查看{friendly_limit}。"
                ),
                recovery_message="请缩短日期范围，或选择更大的时间粒度。",
            )
        object.__setattr__(self, "symbol", symbol)
        object.__setattr__(self, "start_time", start)
        object.__setattr__(self, "end_time", end)

    def with_range(
        self,
        start_time: datetime,
        end_time: datetime,
        *,
        force_refresh: bool | None = None,
    ) -> "HistoricalDataRequest":
        return HistoricalDataRequest(
            symbol=self.symbol,
            start_time=start_time,
            end_time=end_time,
            timeframe=self.timeframe,
            adjustment=self.adjustment,
            feed=self.feed,
            force_refresh=self.force_refresh if force_refresh is None else force_refresh,
        )


@dataclass(frozen=True, slots=True)
class MarketBar:
    symbol: str
    timestamp_utc: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    vwap: Decimal | None
    trade_count: int | None
    timeframe: Timeframe
    adjustment: Adjustment
    feed: DataFeed
    source: str
    fetched_at_utc: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "symbol", self.symbol.strip().upper())
        object.__setattr__(self, "timestamp_utc", ensure_utc(self.timestamp_utc, "timestamp_utc"))
        object.__setattr__(self, "fetched_at_utc", ensure_utc(self.fetched_at_utc, "fetched_at_utc"))


@dataclass(frozen=True, slots=True, order=True)
class CoverageInterval:
    start_utc: datetime
    end_utc: datetime

    def __post_init__(self) -> None:
        start = ensure_utc(self.start_utc, "coverage start")
        end = ensure_utc(self.end_utc, "coverage end")
        if start >= end:
            raise RequestValidationError("coverage interval must have positive duration")
        object.__setattr__(self, "start_utc", start)
        object.__setattr__(self, "end_utc", end)


@dataclass(frozen=True, slots=True)
class CachePolicy:
    max_age: timedelta = timedelta(hours=24)
    overlap_bars: int = 5
    auto_refresh_interval: timedelta = timedelta(minutes=5)

    def __post_init__(self) -> None:
        if self.max_age <= timedelta(0):
            raise ValueError("max_age must be positive")
        if self.overlap_bars < 1:
            raise ValueError("overlap_bars must be at least 1")
        if self.auto_refresh_interval < timedelta(minutes=1):
            raise ValueError("auto refresh interval must be at least 1 minute")


@dataclass(frozen=True, slots=True)
class DataResult:
    request: HistoricalDataRequest
    bars: tuple[MarketBar, ...]
    source: DataSource
    coverage: tuple[CoverageInterval, ...] = ()
    fetched_ranges: tuple[CoverageInterval, ...] = ()
    warnings: tuple[str, ...] = ()
    last_successful_fetch_utc: datetime | None = None


@dataclass(frozen=True, slots=True)
class ChartOptions:
    chart_type: ChartType = ChartType.CANDLESTICK
    price_fields: tuple[PriceField, ...] = (PriceField.CLOSE,)
    show_volume: bool = True
    show_range_slider: bool = True
    reset_view: bool = False


def validate_market_bars(
    bars: Iterable[MarketBar], request: HistoricalDataRequest
) -> tuple[MarketBar, ...]:
    validated = tuple(bars)
    seen: set[tuple[str, datetime, Timeframe, Adjustment, DataFeed]] = set()
    previous_timestamp: datetime | None = None
    for bar in validated:
        key = (bar.symbol, bar.timestamp_utc, bar.timeframe, bar.adjustment, bar.feed)
        if key in seen:
            raise DataValidationError("provider returned a duplicate market bar")
        seen.add(key)
        if bar.symbol != request.symbol:
            raise DataValidationError("provider returned a different symbol")
        if (
            bar.timeframe != request.timeframe
            or bar.adjustment != request.adjustment
            or bar.feed != request.feed
        ):
            raise DataValidationError("provider returned mismatched dimensions")
        if not request.start_time <= bar.timestamp_utc < request.end_time:
            raise DataValidationError("provider returned a bar outside the requested range")
        if previous_timestamp is not None and bar.timestamp_utc <= previous_timestamp:
            raise DataValidationError("provider bars are not strictly ordered")
        previous_timestamp = bar.timestamp_utc
        prices = (bar.open, bar.high, bar.low, bar.close)
        if any(not value.is_finite() for value in prices):
            raise DataValidationError("provider returned a non-finite price")
        if bar.vwap is not None and not bar.vwap.is_finite():
            raise DataValidationError("provider returned a non-finite VWAP")
        if (
            bar.high < bar.low
            or not (bar.low <= bar.open <= bar.high)
            or not (bar.low <= bar.close <= bar.high)
        ):
            raise DataValidationError("provider returned inconsistent OHLC values")
        if bar.volume < 0 or (bar.trade_count is not None and bar.trade_count < 0):
            raise DataValidationError("provider returned a negative count")
    return validated
