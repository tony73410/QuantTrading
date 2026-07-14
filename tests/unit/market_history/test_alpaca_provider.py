from __future__ import annotations

import inspect
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from alpaca.data.historical import StockHistoricalDataClient

from conftest import make_request
from quant_trading.market_history.errors import (
    AuthenticationError,
    CredentialsMissingError,
    ProviderError,
    ProviderTimeoutError,
    InvalidSymbolError,
    PermissionDeniedError,
    RateLimitError,
)
from quant_trading.error_codes import ErrorCode
from quant_trading.market_history.models import Adjustment, DataFeed, Timeframe
from quant_trading.market_history.providers import AlpacaHistoricalMarketDataProvider
from quant_trading.market_history.providers import alpaca_provider


class FakeClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []

    def get_stock_bars(self, request):
        self.requests.append(request)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class StatusError(Exception):
    def __init__(self, status_code):
        super().__init__(f"status {status_code}")
        self.status_code = status_code


def external_bar(
    timestamp,
    *,
    open=100.0,
    high=102.0,
    low=99.0,
    close=101.0,
    volume=1000.0,
    trade_count=50.0,
    vwap=100.5,
):
    return SimpleNamespace(
        symbol="AAPL",
        timestamp=timestamp,
        open=open,
        high=high,
        low=low,
        close=close,
        volume=volume,
        trade_count=trade_count,
        vwap=vwap,
    )


def response_with(*bars):
    return SimpleNamespace(data={"AAPL": list(bars)})


def test_missing_credentials_are_reported_without_creating_client():
    provider = AlpacaHistoricalMarketDataProvider()
    assert not provider.available
    with pytest.raises(CredentialsMissingError):
        provider.fetch_bars(make_request())


def test_request_mapping_and_internal_model_conversion():
    client = FakeClient(
        [response_with(external_bar(datetime(2024, 1, 2, tzinfo=UTC), vwap=None))]
    )
    provider = AlpacaHistoricalMarketDataProvider(client=client)
    request = make_request(
        timeframe=Timeframe.WEEK,
        adjustment=Adjustment.ALL,
        feed=DataFeed.SIP,
    )
    bars = provider.fetch_bars(request)
    sent = client.requests[0]
    assert str(sent.timeframe) == "1Week"
    assert sent.adjustment.value == "all"
    assert sent.feed.value == "sip"
    # Alpaca-py normalizes request datetimes to naive UTC before serialization;
    # its official contract treats naive request times as UTC.
    assert sent.start == request.start_time.replace(tzinfo=None)
    assert sent.end == (request.end_time - timedelta(microseconds=1)).replace(tzinfo=None)
    fields = sent.to_request_fields()
    assert datetime.fromisoformat(fields["start"]).utcoffset() == timedelta(0)
    assert datetime.fromisoformat(fields["end"]).utcoffset() == timedelta(0)
    assert bars[0].vwap is None
    assert bars[0].timeframe == Timeframe.WEEK
    assert bars[0].source == "alpaca"


def test_empty_response_returns_empty_list():
    provider = AlpacaHistoricalMarketDataProvider(client=FakeClient([response_with()]))
    assert provider.fetch_bars(make_request()) == []


@pytest.mark.parametrize(
    ("internal_timeframe", "alpaca_timeframe"),
    [
        (Timeframe.TEN_MINUTES, "10Min"),
        (Timeframe.THIRTY_MINUTES, "30Min"),
        # One-hour bars are deliberately built from regular-session 30-minute bars.
        (Timeframe.HOUR, "30Min"),
    ],
)
def test_intraday_timeframes_map_to_expected_alpaca_requests(
    internal_timeframe, alpaca_timeframe
):
    client = FakeClient([response_with()])
    provider = AlpacaHistoricalMarketDataProvider(client=client)

    provider.fetch_bars(make_request(timeframe=internal_timeframe))

    assert str(client.requests[0].timeframe) == alpaca_timeframe


def test_intraday_bars_are_limited_to_regular_new_york_session():
    client = FakeClient(
        [
            response_with(
                external_bar(datetime(2024, 1, 2, 14, 20, tzinfo=UTC)),  # 09:20 ET
                external_bar(datetime(2024, 1, 2, 14, 30, tzinfo=UTC)),  # 09:30 ET
                external_bar(datetime(2024, 1, 2, 20, 50, tzinfo=UTC)),  # 15:50 ET
                external_bar(datetime(2024, 1, 2, 21, 0, tzinfo=UTC)),   # 16:00 ET
            )
        ]
    )
    provider = AlpacaHistoricalMarketDataProvider(client=client)

    bars = provider.fetch_bars(make_request(timeframe=Timeframe.TEN_MINUTES))

    assert [bar.timestamp_utc.hour for bar in bars] == [14, 20]
    assert [bar.timestamp_utc.minute for bar in bars] == [30, 50]


def test_hour_bars_are_aggregated_from_the_0930_regular_session_open():
    client = FakeClient(
        [
            response_with(
                external_bar(datetime(2024, 1, 2, 14, 0, tzinfo=UTC)),
                external_bar(
                    datetime(2024, 1, 2, 14, 30, tzinfo=UTC),
                    open=100,
                    high=104,
                    low=99,
                    close=103,
                    volume=100,
                    vwap=102,
                ),
                external_bar(
                    datetime(2024, 1, 2, 15, 0, tzinfo=UTC),
                    open=103,
                    high=106,
                    low=102,
                    close=105,
                    volume=300,
                    vwap=104,
                ),
                external_bar(datetime(2024, 1, 2, 15, 30, tzinfo=UTC)),
                external_bar(datetime(2024, 1, 2, 16, 0, tzinfo=UTC)),
                external_bar(datetime(2024, 1, 2, 20, 30, tzinfo=UTC)),
            )
        ]
    )
    provider = AlpacaHistoricalMarketDataProvider(client=client)

    bars = provider.fetch_bars(make_request(timeframe=Timeframe.HOUR))

    assert len(bars) == 3
    assert [bar.timestamp_utc.minute for bar in bars] == [30, 30, 30]
    first = bars[0]
    assert first.open == 100
    assert first.high == 106
    assert first.low == 99
    assert first.close == 105
    assert first.volume == 400
    assert first.vwap == pytest.approx(103.5)
    assert first.trade_count == 100
    assert all(bar.timeframe is Timeframe.HOUR for bar in bars)


def test_temporary_server_error_retries_with_backoff():
    sleeps = []
    client = FakeClient(
        [StatusError(500), response_with(external_bar(datetime(2024, 1, 2, tzinfo=UTC)))]
    )
    provider = AlpacaHistoricalMarketDataProvider(
        client=client,
        max_attempts=3,
        base_retry_delay_seconds=0.25,
        sleep=sleeps.append,
    )
    assert len(provider.fetch_bars(make_request())) == 1
    assert len(client.requests) == 2
    assert sleeps == [0.25]


def test_rate_limit_retries_are_finite_and_mapped():
    client = FakeClient([StatusError(429), StatusError(429), StatusError(429)])
    provider = AlpacaHistoricalMarketDataProvider(
        client=client,
        max_attempts=3,
        base_retry_delay_seconds=0,
        sleep=lambda _: None,
    )
    with pytest.raises(RateLimitError):
        provider.fetch_bars(make_request())
    assert len(client.requests) == 3


def test_non_transient_authentication_error_is_not_retried():
    client = FakeClient([StatusError(401)])
    provider = AlpacaHistoricalMarketDataProvider(client=client, sleep=lambda _: None)
    with pytest.raises(AuthenticationError):
        provider.fetch_bars(make_request())
    assert len(client.requests) == 1


@pytest.mark.parametrize(
    ("status", "expected_type", "expected_code"),
    [
        (403, PermissionDeniedError, ErrorCode.PERMISSION_DENIED),
        (404, InvalidSymbolError, ErrorCode.DATA_UNAVAILABLE),
        (500, ProviderError, ErrorCode.MARKET_DATA_CONNECTION),
    ],
)
def test_http_failures_have_stable_codes_and_do_not_retry_non_transient_errors(
    status, expected_type, expected_code
):
    attempts = 3 if status == 500 else 1
    client = FakeClient([StatusError(status) for _ in range(attempts)])
    provider = AlpacaHistoricalMarketDataProvider(
        client=client,
        max_attempts=attempts,
        base_retry_delay_seconds=0,
        sleep=lambda _: None,
    )

    with pytest.raises(expected_type) as captured:
        provider.fetch_bars(make_request())

    assert captured.value.error_code is expected_code
    assert len(client.requests) == attempts


def test_timeout_has_stable_error_code_and_finite_retries():
    client = FakeClient([TimeoutError("secret technical timeout")])
    provider = AlpacaHistoricalMarketDataProvider(
        client=client,
        max_attempts=1,
        sleep=lambda _: None,
    )
    with pytest.raises(ProviderTimeoutError) as captured:
        provider.fetch_bars(make_request())
    assert captured.value.error_code is ErrorCode.MARKET_DATA_TIMEOUT
    assert len(client.requests) == 1


def test_malformed_response_is_mapped_instead_of_escaping_background_worker():
    malformed = SimpleNamespace(
        data={"AAPL": [SimpleNamespace(symbol="AAPL", timestamp=None)]}
    )
    provider = AlpacaHistoricalMarketDataProvider(client=FakeClient([malformed]))

    with pytest.raises(ProviderError) as captured:
        provider.fetch_bars(make_request())

    assert captured.value.error_code is ErrorCode.MARKET_DATA_RESPONSE
    assert "旧的本地数据" in captured.value.user_message


def test_official_sdk_follows_next_page_token_without_network():
    sdk_client = StockHistoricalDataClient("test-key", "test-secret")
    pages = {
        None: {
            "bars": {
                "AAPL": [
                    {"t": "2024-01-02T00:00:00Z", "o": 100, "h": 102, "l": 99, "c": 101, "v": 1000, "n": 50, "vw": 100.5}
                ]
            },
            "next_page_token": "page-2",
        },
        "page-2": {
            "bars": {
                "AAPL": [
                    {"t": "2024-01-03T00:00:00Z", "o": 101, "h": 103, "l": 100, "c": 102, "v": 900, "n": 45, "vw": 101.5}
                ]
            },
            "next_page_token": None,
        },
    }
    tokens = []

    def fake_get(*, path, data):
        assert path == "/stocks/bars"
        token = data.get("page_token")
        tokens.append(token)
        return pages[token]

    sdk_client.get = fake_get
    provider = AlpacaHistoricalMarketDataProvider(client=sdk_client)
    bars = provider.fetch_bars(make_request())
    assert tokens == [None, "page-2"]
    assert [bar.timestamp_utc.day for bar in bars] == [2, 3]
def test_provider_source_cannot_import_alpaca_trading_or_submit_orders():
    source = inspect.getsource(alpaca_provider)
    assert "alpaca.trading" not in source
    assert "TradingClient" not in source
    assert "submit_order" not in source
