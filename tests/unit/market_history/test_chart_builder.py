from __future__ import annotations

from datetime import UTC, datetime

import plotly.graph_objects as go

from conftest import make_bar, make_request
from quant_trading.market_history.charts import PlotlyChartBuilder
from quant_trading.market_history.models import (
    ChartOptions,
    ChartType,
    DataResult,
    DataSource,
    PriceField,
)


def result_with_bars(*, missing_vwap=False, request=None):
    request = request or make_request()
    bars = tuple(
        make_bar(
            datetime(2024, 1, day, tzinfo=UTC),
            request=request,
            vwap=None if missing_vwap else "100.5",
        )
        for day in (2, 3, 4)
    )
    return DataResult(request=request, bars=bars, source=DataSource.LOCAL_CACHE)


def test_candlestick_contains_ohlc_values():
    figure = PlotlyChartBuilder().build(result_with_bars(), ChartOptions())
    trace = figure.data[0]
    assert isinstance(trace, go.Candlestick)
    assert list(trace.open) == [100.0, 100.0, 100.0]
    assert list(trace.close) == [101.0, 101.0, 101.0]


def test_close_line_uses_selected_field():
    figure = PlotlyChartBuilder().build(
        result_with_bars(),
        ChartOptions(chart_type=ChartType.LINE, price_fields=(PriceField.CLOSE,), show_volume=False),
    )
    assert isinstance(figure.data[0], go.Scatter)
    assert figure.data[0].name == "CLOSE"
    assert list(figure.data[0].y) == [101.0, 101.0, 101.0]


def test_ohlc_chart_is_created():
    figure = PlotlyChartBuilder().build(
        result_with_bars(), ChartOptions(chart_type=ChartType.OHLC, show_volume=False)
    )
    assert isinstance(figure.data[0], go.Ohlc)


def test_volume_and_range_slider_switches():
    with_volume = PlotlyChartBuilder().build(
        result_with_bars(), ChartOptions(show_volume=True, show_range_slider=True)
    )
    without_volume = PlotlyChartBuilder().build(
        result_with_bars(), ChartOptions(show_volume=False, show_range_slider=False)
    )
    assert any(isinstance(trace, go.Bar) for trace in with_volume.data)
    assert not any(isinstance(trace, go.Bar) for trace in without_volume.data)
    assert with_volume.layout.xaxis.rangeslider.visible is True
    assert without_volume.layout.xaxis.rangeslider.visible is False


def test_empty_data_returns_visible_empty_state():
    request = make_request()
    result = DataResult(request=request, bars=(), source=DataSource.LOCAL_CACHE)
    figure = PlotlyChartBuilder().build(result, ChartOptions())
    assert "没有历史数据" in figure.layout.annotations[0].text


def test_missing_vwap_is_not_replaced_with_zero():
    figure = PlotlyChartBuilder().build(
        result_with_bars(missing_vwap=True),
        ChartOptions(
            chart_type=ChartType.LINE,
            price_fields=(PriceField.VWAP,),
            show_volume=False,
        ),
    )
    assert len(figure.data) == 0
    assert "没有可用数据" in figure.layout.annotations[0].text


def test_result_contains_only_requested_date_range():
    result = result_with_bars()
    figure = PlotlyChartBuilder().build(result, ChartOptions(show_volume=False))
    assert min(figure.data[0].x).day == 2
    assert max(figure.data[0].x).day == 4


def test_date_range_change_resets_preserved_plotly_view():
    one_year = result_with_bars(
        request=make_request(
            start=datetime(2023, 1, 1, tzinfo=UTC),
            end=datetime(2024, 1, 1, tzinfo=UTC),
        )
    )
    five_years = result_with_bars(
        request=make_request(
            start=datetime(2019, 1, 1, tzinfo=UTC),
            end=datetime(2024, 1, 1, tzinfo=UTC),
        )
    )

    builder = PlotlyChartBuilder()
    one_year_figure = builder.build(one_year, ChartOptions())
    five_year_figure = builder.build(five_years, ChartOptions())

    assert one_year_figure.layout.uirevision != five_year_figure.layout.uirevision


def test_style_change_preserves_plotly_view_for_same_data_range():
    result = result_with_bars()
    builder = PlotlyChartBuilder()

    candlestick = builder.build(
        result, ChartOptions(chart_type=ChartType.CANDLESTICK)
    )
    line = builder.build(result, ChartOptions(chart_type=ChartType.LINE))

    assert candlestick.layout.uirevision == line.layout.uirevision
