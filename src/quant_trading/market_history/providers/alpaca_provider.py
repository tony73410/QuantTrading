"""Alpaca Market Data adapter. It never accesses trading or account APIs."""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime, time as wall_time, timedelta
from decimal import Decimal
from typing import Any, Callable
from zoneinfo import ZoneInfo

from alpaca.common.exceptions import APIError
from alpaca.data.enums import Adjustment as AlpacaAdjustment
from alpaca.data.enums import DataFeed as AlpacaDataFeed
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame as AlpacaTimeFrame
from alpaca.data.timeframe import TimeFrameUnit as AlpacaTimeFrameUnit

from quant_trading.error_codes import ErrorCode

from ..errors import (
    AuthenticationError,
    CredentialsMissingError,
    InvalidSymbolError,
    PermissionDeniedError,
    ProviderError,
    ProviderTimeoutError,
    RateLimitError,
)
from ..models import Adjustment, DataFeed, HistoricalDataRequest, MarketBar, Timeframe


logger = logging.getLogger(__name__)

_NEW_YORK = ZoneInfo("America/New_York")
_REGULAR_OPEN = wall_time(9, 30)
_REGULAR_CLOSE = wall_time(16, 0)


class AlpacaHistoricalMarketDataProvider:
    """Fetch stock bars through Alpaca's official paginating SDK client."""

    def __init__(
        self,
        api_key: str | None = None,
        secret_key: str | None = None,
        *,
        client: Any | None = None,
        max_attempts: int = 3,
        base_retry_delay_seconds: float = 0.5,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        self._credentials_present = bool(api_key and secret_key)
        self._client = client
        if client is None and self._credentials_present:
            self._client = StockHistoricalDataClient(api_key, secret_key)
        self._max_attempts = max_attempts
        self._base_retry_delay_seconds = base_retry_delay_seconds
        self._sleep = sleep

    @property
    def available(self) -> bool:
        return self._client is not None

    def fetch_bars(self, request: HistoricalDataRequest) -> list[MarketBar]:
        if self._client is None:
            raise CredentialsMissingError()
        alpaca_request = StockBarsRequest(
            symbol_or_symbols=request.symbol,
            timeframe=self._map_timeframe(request.timeframe),
            start=request.start_time,
            # Alpaca's HTTP end is inclusive; our domain end is exclusive.
            end=request.end_time - timedelta(microseconds=1),
            adjustment=AlpacaAdjustment(request.adjustment.value),
            feed=AlpacaDataFeed(request.feed.value),
        )
        response: Any = None
        for attempt in range(1, self._max_attempts + 1):
            try:
                logger.info(
                    "Alpaca fetch started symbol=%s timeframe=%s start=%s end=%s attempt=%d",
                    request.symbol,
                    request.timeframe.value,
                    request.start_time.isoformat(),
                    request.end_time.isoformat(),
                    attempt,
                    extra={
                        "operation": "fetch_bars",
                        "symbol": request.symbol,
                        "timeframe": request.timeframe.value,
                        "date_range": (
                            f"{request.start_time.isoformat()}/"
                            f"{request.end_time.isoformat()}"
                        ),
                        "adjustment": request.adjustment.value,
                        "feed": request.feed.value,
                    },
                )
                # Alpaca-py _get_marketdata follows next_page_token until exhausted.
                response = self._client.get_stock_bars(alpaca_request)
                break
            except Exception as exc:  # mapped immediately; raw exception is never shown by GUI
                if self._is_transient(exc) and attempt < self._max_attempts:
                    delay = self._base_retry_delay_seconds * (2 ** (attempt - 1))
                    logger.warning(
                        "Temporary Alpaca error status=%s; retrying in %.2fs",
                        self._status_code(exc),
                        delay,
                        extra={
                            "operation": "fetch_bars_retry",
                            "symbol": request.symbol,
                            "timeframe": request.timeframe.value,
                            "exception_type": type(exc).__name__,
                        },
                    )
                    self._sleep(delay)
                    continue
                raise self._map_error(exc) from exc
        try:
            bars = self._extract_symbol_bars(response, request.symbol)
            fetched_at = datetime.now(UTC)
            converted = [self._convert_bar(item, request, fetched_at) for item in bars]
        except (AttributeError, TypeError, ValueError, ArithmeticError) as exc:
            raise ProviderError(
                f"Alpaca response conversion failed ({type(exc).__name__})",
                user_message="Alpaca 返回了无法识别的行情数据，旧的本地数据已保留。",
                error_code=ErrorCode.MARKET_DATA_RESPONSE,
                cause=exc,
            ) from exc
        converted.sort(key=lambda bar: bar.timestamp_utc)
        if request.timeframe.is_intraday:
            converted = self._regular_session_bars(converted)
        if request.timeframe is Timeframe.HOUR:
            converted = self._aggregate_regular_session_hours(converted)
        logger.info(
            "Alpaca fetch completed symbol=%s rows=%d",
            request.symbol,
            len(converted),
            extra={
                "operation": "fetch_bars",
                "symbol": request.symbol,
                "timeframe": request.timeframe.value,
                "adjustment": request.adjustment.value,
                "feed": request.feed.value,
            },
        )
        return converted

    @staticmethod
    def _map_timeframe(timeframe: Timeframe) -> AlpacaTimeFrame:
        return {
            Timeframe.TEN_MINUTES: AlpacaTimeFrame(10, AlpacaTimeFrameUnit.Minute),
            Timeframe.THIRTY_MINUTES: AlpacaTimeFrame(30, AlpacaTimeFrameUnit.Minute),
            # Alpaca's native 1Hour bars are aligned to whole hours, so the
            # 09:00 bar can mix pre-market and regular-session trades. Fetch
            # 30-minute bars and aggregate from the 09:30 market open instead.
            Timeframe.HOUR: AlpacaTimeFrame(30, AlpacaTimeFrameUnit.Minute),
            Timeframe.DAY: AlpacaTimeFrame.Day,
            Timeframe.WEEK: AlpacaTimeFrame.Week,
            Timeframe.MONTH: AlpacaTimeFrame.Month,
        }[timeframe]

    @staticmethod
    def _regular_session_bars(bars: list[MarketBar]) -> list[MarketBar]:
        return [
            bar
            for bar in bars
            if _REGULAR_OPEN
            <= bar.timestamp_utc.astimezone(_NEW_YORK).time().replace(tzinfo=None)
            < _REGULAR_CLOSE
        ]

    @staticmethod
    def _aggregate_regular_session_hours(
        bars: list[MarketBar],
    ) -> list[MarketBar]:
        buckets: dict[tuple[object, int], list[MarketBar]] = {}
        for bar in bars:
            eastern = bar.timestamp_utc.astimezone(_NEW_YORK)
            minutes_from_open = (eastern.hour * 60 + eastern.minute) - (9 * 60 + 30)
            bucket = minutes_from_open // 60
            buckets.setdefault((eastern.date(), bucket), []).append(bar)

        aggregated: list[MarketBar] = []
        for bucket_bars in buckets.values():
            total_volume = sum(bar.volume for bar in bucket_bars)
            if total_volume > 0 and all(bar.vwap is not None for bar in bucket_bars):
                vwap = sum(
                    bar.vwap * bar.volume  # type: ignore[operator]
                    for bar in bucket_bars
                ) / total_volume
            else:
                vwap = None
            trade_count = (
                sum(bar.trade_count for bar in bucket_bars)  # type: ignore[arg-type]
                if all(bar.trade_count is not None for bar in bucket_bars)
                else None
            )
            first = bucket_bars[0]
            last = bucket_bars[-1]
            aggregated.append(
                MarketBar(
                    symbol=first.symbol,
                    timestamp_utc=first.timestamp_utc,
                    open=first.open,
                    high=max(bar.high for bar in bucket_bars),
                    low=min(bar.low for bar in bucket_bars),
                    close=last.close,
                    volume=total_volume,
                    vwap=vwap,
                    trade_count=trade_count,
                    timeframe=first.timeframe,
                    adjustment=first.adjustment,
                    feed=first.feed,
                    source=first.source,
                    fetched_at_utc=max(
                        bar.fetched_at_utc for bar in bucket_bars
                    ),
                )
            )
        return aggregated

    @staticmethod
    def _extract_symbol_bars(response: Any, symbol: str) -> list[Any]:
        if response is None:
            return []
        data = getattr(response, "data", response)
        if isinstance(data, dict):
            return list(data.get(symbol, data.get(symbol.upper(), [])))
        try:
            return list(response[symbol])
        except (KeyError, TypeError):
            return []

    @staticmethod
    def _convert_bar(
        item: Any,
        request: HistoricalDataRequest,
        fetched_at: datetime,
    ) -> MarketBar:
        timestamp = item.timestamp
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=UTC)
        return MarketBar(
            symbol=getattr(item, "symbol", request.symbol),
            timestamp_utc=timestamp.astimezone(UTC),
            open=Decimal(str(item.open)),
            high=Decimal(str(item.high)),
            low=Decimal(str(item.low)),
            close=Decimal(str(item.close)),
            volume=int(item.volume),
            vwap=None if item.vwap is None else Decimal(str(item.vwap)),
            trade_count=None if item.trade_count is None else int(item.trade_count),
            timeframe=request.timeframe,
            adjustment=request.adjustment,
            feed=request.feed,
            source="alpaca",
            fetched_at_utc=fetched_at,
        )

    @classmethod
    def _is_transient(cls, exc: Exception) -> bool:
        status = cls._status_code(exc)
        return (
            status == 429
            or (status is not None and 500 <= status <= 599)
            or isinstance(exc, (TimeoutError, ConnectionError))
            or exc.__class__.__name__ in {"Timeout", "ReadTimeout", "ConnectTimeout", "ConnectionError"}
        )

    @staticmethod
    def _status_code(exc: Exception) -> int | None:
        status = getattr(exc, "status_code", None)
        if status is not None:
            return int(status)
        response = getattr(exc, "response", None)
        return int(response.status_code) if response is not None and hasattr(response, "status_code") else None

    @classmethod
    def _map_error(cls, exc: Exception) -> ProviderError:
        status = cls._status_code(exc)
        safe_message = f"Alpaca request failed ({exc.__class__.__name__}, status={status})"
        if status == 401:
            return AuthenticationError(safe_message)
        if status == 403:
            return PermissionDeniedError(safe_message)
        if status == 429:
            return RateLimitError(safe_message)
        if status in {400, 404, 422}:
            return InvalidSymbolError(safe_message)
        if status is not None and 500 <= status <= 599:
            return ProviderError(safe_message, user_message="Alpaca 服务暂时出错，请稍后重试。")
        if cls._is_transient(exc):
            return ProviderTimeoutError(safe_message)
        return ProviderError(safe_message, cause=exc)
