from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from conftest import make_bar, make_request
from quant_trading.market_history.errors import ProviderError
from quant_trading.market_history.models import (
    CachePolicy,
    CoverageInterval,
    DataSource,
    Timeframe,
)
from quant_trading.market_history.service import HistoricalDataService


class FakeProvider:
    available = True

    def __init__(self):
        self.calls = []
        self.failure: ProviderError | None = None

    def fetch_bars(self, request):
        self.calls.append(request)
        if self.failure:
            raise self.failure
        bars = []
        cursor = request.start_time
        step = request.timeframe.approximate_duration
        while cursor < request.end_time:
            bars.append(make_bar(cursor, request=request))
            cursor += step
        return bars


def seed(store, request, start, end):
    provider = FakeProvider()
    service = HistoricalDataService(store, provider)
    service.load(request.with_range(start, end))
    return provider


def test_complete_local_hit_does_not_call_provider(store):
    request = make_request()
    provider = FakeProvider()
    service = HistoricalDataService(store, provider)
    service.load(request)
    provider.calls.clear()
    result = service.load(request)
    assert provider.calls == []
    assert result.source == DataSource.LOCAL_CACHE


def test_complete_miss_requests_full_range(store):
    request = make_request()
    provider = FakeProvider()
    result = HistoricalDataService(store, provider).load(request)
    assert [(call.start_time, call.end_time) for call in provider.calls] == [
        (request.start_time, request.end_time)
    ]
    assert result.source == DataSource.API_UPDATE


@pytest.mark.parametrize(
    ("seed_start", "seed_end", "expected_start", "expected_end"),
    [
        (
            datetime(2024, 1, 5, tzinfo=UTC),
            datetime(2024, 1, 10, tzinfo=UTC),
            datetime(2024, 1, 1, tzinfo=UTC),
            datetime(2024, 1, 5, tzinfo=UTC),
        ),
        (
            datetime(2024, 1, 1, tzinfo=UTC),
            datetime(2024, 1, 5, tzinfo=UTC),
            datetime(2024, 1, 5, tzinfo=UTC),
            datetime(2024, 1, 10, tzinfo=UTC),
        ),
    ],
)
def test_only_front_or_back_gap_is_requested(
    store, seed_start, seed_end, expected_start, expected_end
):
    request = make_request()
    seed(store, request, seed_start, seed_end)
    provider = FakeProvider()
    HistoricalDataService(store, provider).load(request)
    assert [(call.start_time, call.end_time) for call in provider.calls] == [
        (expected_start, expected_end)
    ]


def test_middle_gap_is_requested_without_redownloading_edges(store):
    request = make_request()
    seed(store, request, request.start_time, datetime(2024, 1, 3, tzinfo=UTC))
    seed(store, request, datetime(2024, 1, 7, tzinfo=UTC), request.end_time)
    provider = FakeProvider()
    HistoricalDataService(store, provider).load(request)
    assert [(call.start_time, call.end_time) for call in provider.calls] == [
        (datetime(2024, 1, 3, tzinfo=UTC), datetime(2024, 1, 7, tzinfo=UTC))
    ]


def test_refresh_latest_uses_configured_overlap(store):
    end = datetime.now(UTC).replace(microsecond=0)
    request = make_request(start=end - timedelta(days=20), end=end)
    seed(store, request, request.start_time, request.end_time)
    provider = FakeProvider()
    HistoricalDataService(store, provider).load(request, refresh_latest=True)
    assert provider.calls[0].start_time == request.end_time - timedelta(days=5)
    assert provider.calls[0].end_time == request.end_time


@pytest.mark.parametrize(
    "timeframe",
    [Timeframe.TEN_MINUTES, Timeframe.THIRTY_MINUTES, Timeframe.HOUR],
)
def test_intraday_refresh_uses_timeframe_specific_overlap(store, timeframe):
    end = datetime.now(UTC).replace(microsecond=0)
    request = make_request(
        start=end - timedelta(days=2),
        end=end,
        timeframe=timeframe,
    )
    seed(store, request, request.start_time, request.end_time)
    provider = FakeProvider()

    HistoricalDataService(store, provider).load(request, refresh_latest=True)

    assert provider.calls[0].start_time == (
        request.end_time - timeframe.approximate_duration * 5
    )
    assert provider.calls[0].end_time == request.end_time


def test_stale_recent_cache_refreshes_only_tail(store):
    end = datetime.now(UTC).replace(microsecond=0)
    request = make_request(start=end - timedelta(days=20), end=end)
    seed(store, request, request.start_time, request.end_time)
    provider = FakeProvider()
    service = HistoricalDataService(
        store,
        provider,
        CachePolicy(max_age=timedelta(microseconds=1), overlap_bars=3),
    )
    service.load(request)
    assert [(call.start_time, call.end_time) for call in provider.calls] == [
        (request.end_time - timedelta(days=3), request.end_time)
    ]


def test_api_failure_returns_existing_local_data_with_warning(store):
    request = make_request()
    seed(store, request, request.start_time, datetime(2024, 1, 5, tzinfo=UTC))
    provider = FakeProvider()
    provider.failure = ProviderError("offline", user_message="offline")
    result = HistoricalDataService(store, provider).load(request)
    assert result.bars
    assert result.source == DataSource.OFFLINE_LOCAL
    assert result.warnings == ("offline（错误编号：QT-API-001）",)
    assert store.get_coverage(request) == [
        CoverageInterval(request.start_time, datetime(2024, 1, 5, tzinfo=UTC))
    ]


def test_api_failure_without_local_data_is_raised(store):
    provider = FakeProvider()
    provider.failure = ProviderError("offline")
    with pytest.raises(ProviderError):
        HistoricalDataService(store, provider).load(make_request())


def test_force_refresh_failure_does_not_delete_old_data(store):
    request = make_request()
    seed(store, request, request.start_time, request.end_time)
    old = store.query_bars(request)
    provider = FakeProvider()
    provider.failure = ProviderError("offline")
    forced = make_request(force_refresh=True)
    result = HistoricalDataService(store, provider).load(forced)
    assert result.source == DataSource.OFFLINE_LOCAL
    assert store.query_bars(request) == old


def test_missing_interval_calculation_handles_multiple_coverage_ranges():
    request = make_request()
    coverage = [
        CoverageInterval(datetime(2024, 1, 2, tzinfo=UTC), datetime(2024, 1, 4, tzinfo=UTC)),
        CoverageInterval(datetime(2024, 1, 6, tzinfo=UTC), datetime(2024, 1, 8, tzinfo=UTC)),
    ]
    assert HistoricalDataService.calculate_missing_intervals(request, coverage) == [
        CoverageInterval(datetime(2024, 1, 1, tzinfo=UTC), datetime(2024, 1, 2, tzinfo=UTC)),
        CoverageInterval(datetime(2024, 1, 4, tzinfo=UTC), datetime(2024, 1, 6, tzinfo=UTC)),
        CoverageInterval(datetime(2024, 1, 8, tzinfo=UTC), datetime(2024, 1, 10, tzinfo=UTC)),
    ]
