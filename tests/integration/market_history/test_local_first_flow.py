from __future__ import annotations

from datetime import UTC, datetime

from conftest import make_bar, make_request
from quant_trading.market_history.charts import PlotlyChartBuilder
from quant_trading.market_history.models import ChartOptions, DataSource
from quant_trading.market_history.service import HistoricalDataService


class FakeProvider:
    available = True

    def __init__(self):
        self.calls = []

    def fetch_bars(self, request):
        self.calls.append(request)
        return [
            make_bar(datetime(2024, 1, day, tzinfo=UTC), request=request)
            for day in range(1, 10)
            if request.start_time <= datetime(2024, 1, day, tzinfo=UTC) < request.end_time
        ]


def test_request_cache_fetch_store_reuse_and_chart(store):
    provider = FakeProvider()
    service = HistoricalDataService(store, provider)
    request = make_request()

    first = service.load(request)
    assert first.source == DataSource.API_UPDATE
    assert len(provider.calls) == 1
    assert store.query_bars(request) == list(first.bars)

    second = service.load(request)
    assert second.source == DataSource.LOCAL_CACHE
    assert len(provider.calls) == 1
    assert second.bars == first.bars

    figure = PlotlyChartBuilder().build(second, ChartOptions())
    assert figure.data
    assert figure.layout.title.text.startswith("AAPL")
