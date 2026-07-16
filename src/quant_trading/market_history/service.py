"""Local-first orchestration, coverage calculation, refresh, and fallback logic."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from quant_trading.observability import log_exception

from .errors import (
    CredentialsMissingError,
    DataUnavailableError,
    MarketHistoryError,
)
from .interfaces import HistoricalDataStore, HistoricalMarketDataProvider
from .models import (
    CachePolicy,
    CoverageInterval,
    DataResult,
    DataSource,
    HistoricalDataRequest,
    validate_market_bars,
)


logger = logging.getLogger(__name__)


class HistoricalDataService:
    """Coordinate cache coverage and provider updates; never called directly by GUI widgets."""

    def __init__(
        self,
        store: HistoricalDataStore,
        provider: HistoricalMarketDataProvider,
        cache_policy: CachePolicy | None = None,
    ) -> None:
        self.store = store
        self.provider = provider
        self.cache_policy = cache_policy or CachePolicy()

    def list_cached_symbols(self) -> list[str]:
        """List locally available symbols without contacting the Provider."""
        return self.store.list_symbols()

    def load(
        self,
        request: HistoricalDataRequest,
        *,
        refresh_latest: bool = False,
    ) -> DataResult:
        existing_bars = self.store.query_bars(request)
        coverage_before = self.store.get_coverage(request)
        last_fetch_before = self.store.get_last_successful_fetch(request)
        stale = self._is_stale(request, last_fetch_before)
        stale_for_display = stale and self._is_recent_range(request)
        ranges = self._ranges_to_fetch(request, coverage_before, stale, refresh_latest)
        logger.info(
            "Cache evaluated local_rows=%d coverage_intervals=%d fetch_ranges=%d stale=%s",
            len(existing_bars),
            len(coverage_before),
            len(ranges),
            stale,
            extra={
                "operation": "evaluate_cache",
                "symbol": request.symbol,
                "timeframe": request.timeframe.value,
                "date_range": f"{request.start_time.isoformat()}/{request.end_time.isoformat()}",
                "adjustment": request.adjustment.value,
                "feed": request.feed.value,
            },
        )
        fetched_ranges: list[CoverageInterval] = []
        warnings: list[str] = []
        failure: MarketHistoryError | None = None

        if ranges and not self.provider.available:
            failure = CredentialsMissingError()
            warnings.append(
                f"{failure.user_message}（错误编号：{failure.error_code.value}）"
            )
            logger.warning(
                "Market-data update skipped because Alpaca Market Data "
                "credentials are unavailable",
                extra={
                    "error_code": failure.error_code.value,
                    "operation": "fetch_bars",
                    "symbol": request.symbol,
                    "timeframe": request.timeframe.value,
                },
            )
        else:
            for interval in ranges:
                interval_request = request.with_range(
                    interval.start_utc,
                    interval.end_utc,
                    force_refresh=False,
                )
                fetch_id = self.store.begin_fetch(interval_request)
                try:
                    downloaded = self.provider.fetch_bars(interval_request)
                    validated = validate_market_bars(downloaded, interval_request)
                    self.store.complete_fetch_success(fetch_id, interval_request, interval, validated)
                    fetched_ranges.append(interval)
                except MarketHistoryError as exc:
                    failure = exc
                    self.store.complete_fetch_failure(
                        fetch_id,
                        f"{exc.__class__.__name__}: {exc.user_message}",
                    )
                    warnings.append(
                        f"{exc.user_message}（错误编号：{exc.error_code.value}）"
                    )
                    log_exception(
                        logger,
                        exc.original_exception or exc,
                        message="Market data interval update failed",
                        error_code=exc.error_code,
                        context={
                            "operation": "fetch_bars",
                            "symbol": request.symbol,
                            "timeframe": request.timeframe.value,
                            "date_range": (
                                f"{interval.start_utc.isoformat()}/"
                                f"{interval.end_utc.isoformat()}"
                            ),
                            "adjustment": request.adjustment.value,
                            "feed": request.feed.value,
                        },
                        level=logging.WARNING,
                    )
                    break

        bars = self.store.query_bars(request)
        coverage_after = self.store.get_coverage(request)
        last_fetch_after = self.store.get_last_successful_fetch(request)
        if not bars:
            if failure is not None:
                raise failure
            raise DataUnavailableError()
        logger.info(
            "History data ready rows=%d fetched_ranges=%d warnings=%d",
            len(bars),
            len(fetched_ranges),
            len(warnings),
            extra={
                "operation": "history_ready",
                "symbol": request.symbol,
                "timeframe": request.timeframe.value,
            },
        )
        source = self._select_source(
            had_local=bool(existing_bars),
            fetched=bool(fetched_ranges),
            failed=failure is not None,
            stale=stale_for_display,
        )
        return DataResult(
            request=request,
            bars=tuple(bars),
            source=source,
            coverage=tuple(coverage_after),
            fetched_ranges=tuple(fetched_ranges),
            warnings=tuple(warnings),
            last_successful_fetch_utc=last_fetch_after,
        )

    def _ranges_to_fetch(
        self,
        request: HistoricalDataRequest,
        coverage: list[CoverageInterval],
        stale: bool,
        refresh_latest: bool,
    ) -> list[CoverageInterval]:
        if request.force_refresh:
            return [CoverageInterval(request.start_time, request.end_time)]
        if refresh_latest:
            return [self._tail_interval(request)]
        missing = self.calculate_missing_intervals(request, coverage)
        if missing:
            return missing
        if stale and self._is_recent_range(request):
            return [self._tail_interval(request)]
        return []

    def _tail_interval(self, request: HistoricalDataRequest) -> CoverageInterval:
        overlap = request.timeframe.approximate_duration * self.cache_policy.overlap_bars
        return CoverageInterval(max(request.start_time, request.end_time - overlap), request.end_time)

    def _is_stale(
        self,
        request: HistoricalDataRequest,
        last_successful_fetch: datetime | None,
    ) -> bool:
        if last_successful_fetch is None:
            return True
        return datetime.now(UTC) - last_successful_fetch > self.cache_policy.max_age

    @staticmethod
    def _is_recent_range(request: HistoricalDataRequest) -> bool:
        threshold = datetime.now(UTC) - (request.timeframe.approximate_duration * 2)
        return request.end_time >= threshold

    @staticmethod
    def calculate_missing_intervals(
        request: HistoricalDataRequest,
        coverage: list[CoverageInterval],
    ) -> list[CoverageInterval]:
        cursor = request.start_time
        missing: list[CoverageInterval] = []
        for interval in sorted(coverage):
            if interval.end_utc <= cursor or interval.start_utc >= request.end_time:
                continue
            interval_start = max(interval.start_utc, request.start_time)
            interval_end = min(interval.end_utc, request.end_time)
            if interval_start > cursor:
                missing.append(CoverageInterval(cursor, interval_start))
            cursor = max(cursor, interval_end)
            if cursor >= request.end_time:
                break
        if cursor < request.end_time:
            missing.append(CoverageInterval(cursor, request.end_time))
        return missing

    @staticmethod
    def _select_source(
        *, had_local: bool, fetched: bool, failed: bool, stale: bool
    ) -> DataSource:
        if fetched and had_local:
            return DataSource.LOCAL_AND_API
        if fetched:
            return DataSource.API_UPDATE
        if failed:
            return DataSource.OFFLINE_LOCAL
        if stale:
            return DataSource.STALE_LOCAL
        return DataSource.LOCAL_CACHE
