from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

from conftest import make_bar, make_request
from quant_trading.market_history.controller import HistoryController
from quant_trading.market_history.errors import OperationInProgressError, RequestValidationError
from quant_trading.market_history.models import (
    Adjustment,
    ChartOptions,
    DataFeed,
    DataResult,
    DataSource,
    Timeframe,
)


class FakeService:
    def __init__(self):
        self.calls = []

    def load(self, request, *, refresh_latest=False):
        self.calls.append((request, refresh_latest))
        return DataResult(
            request=request,
            bars=(make_bar(request.start_time, request=request),),
            source=DataSource.LOCAL_CACHE,
        )


def test_gui_values_convert_to_normalized_request():
    request = HistoryController.build_request(
        symbol=" aapl ",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 5),
        timeframe=Timeframe.DAY,
        adjustment=Adjustment.SPLIT,
        feed=DataFeed.IEX,
    )
    assert request.symbol == "AAPL"
    assert request.start_time == datetime(2024, 1, 1, tzinfo=UTC)
    assert request.end_time == datetime(2024, 1, 6, tzinfo=UTC)


def test_qt_string_values_convert_to_domain_enums():
    request = HistoryController.build_request(
        symbol="AAPL",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 5),
        timeframe="1Week",
        adjustment="all",
        feed="sip",
    )
    assert request.timeframe is Timeframe.WEEK
    assert request.adjustment is Adjustment.ALL
    assert request.feed is DataFeed.SIP


def test_invalid_qt_string_value_is_rejected():
    with pytest.raises(RequestValidationError):
        HistoryController.build_request(
            symbol="AAPL",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 5),
            timeframe="unsupported",
            adjustment="raw",
            feed="iex",
        )


def test_invalid_input_raises_domain_validation_error():
    with pytest.raises(RequestValidationError):
        HistoryController.build_request(
            symbol="",
            start_date=date(2024, 1, 5),
            end_date=date(2024, 1, 1),
            timeframe=Timeframe.DAY,
            adjustment=Adjustment.RAW,
            feed=DataFeed.IEX,
        )


def test_refresh_flag_reaches_service():
    service = FakeService()
    controller = HistoryController(service)
    controller.load_data(make_request(), refresh_latest=True)
    assert service.calls[0][1] is True


def test_duplicate_load_is_rejected():
    controller = HistoryController(FakeService())
    controller._load_lock.acquire()
    try:
        with pytest.raises(OperationInProgressError):
            controller.load_data(make_request())
    finally:
        controller._load_lock.release()


def test_chart_setting_changes_do_not_call_service_again():
    service = FakeService()
    controller = HistoryController(service)
    controller.load_data(make_request())
    controller.build_chart(ChartOptions())
    controller.build_chart(ChartOptions(show_volume=False))
    assert len(service.calls) == 1
