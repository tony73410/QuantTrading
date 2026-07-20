from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from quant_trading.algorithm_control.factor_history_chart import FactorHistoryChartBuilder
from quant_trading.factors import (
    FactorCalculationStatus,
    FactorSourcePriceStatus,
    FactorStatus,
    FactorVisualizationPoint,
    FactorVisualizationQuery,
    FactorVisualizationSeries,
)
from quant_trading.market_history import Adjustment, DataFeed, PriceField, Timeframe


NOW = datetime(2026, 7, 16, 20, 0, tzinfo=UTC)


def _point(offset: int, **changes) -> FactorVisualizationPoint:
    timestamp = NOW + timedelta(days=offset)
    values = {
        "calculation_id": UUID(int=10 + offset),
        "algorithm_run_id": UUID(int=20 + offset),
        "stage_id": UUID(int=30 + offset),
        "snapshot_id": UUID(int=40 + offset),
        "symbol": "AAPL",
        "as_of_utc": timestamp,
        "timeframe": Timeframe.DAY,
        "adjustment": Adjustment.RAW,
        "feed": DataFeed.IEX,
        "factor_name": "deviation",
        "factor_version": "1",
        "factor_value": Decimal(str(offset + 1)),
        "factor_unit": "zscore",
        "result_status": FactorStatus.VALID,
        "calculation_status": FactorCalculationStatus.SUCCESS,
        "source_data_end_utc": timestamp,
        "source_bar_timestamp_utc": timestamp,
        "price_field": PriceField.CLOSE,
        "price_value": Decimal(str(100 + offset)),
        "source_price_status": FactorSourcePriceStatus.AVAILABLE,
        "error_code": None,
        "error_summary": None,
    }
    values.update(changes)
    return FactorVisualizationPoint(**values)


def test_chart_keeps_invalid_factor_and_missing_price_as_explicit_gaps() -> None:
    query = FactorVisualizationQuery(
        "AAPL",
        "deviation",
        "1",
        NOW - timedelta(days=1),
        NOW + timedelta(days=5),
        Timeframe.DAY,
        Adjustment.RAW,
        DataFeed.IEX,
        PriceField.CLOSE,
    )
    points = (
        _point(0),
        _point(1, factor_value=None, result_status=FactorStatus.INVALID_INPUT),
        _point(
            2,
            source_bar_timestamp_utc=None,
            price_value=None,
            source_price_status=FactorSourcePriceStatus.MISSING_SOURCE_BAR,
        ),
        _point(3, factor_value=True),
    )

    figure = FactorHistoryChartBuilder().build(FactorVisualizationSeries(query, points))

    factor_trace, price_trace, status_trace = figure.data
    assert tuple(factor_trace.y) == (1.0, None, 3.0, None)
    assert tuple(price_trace.y) == (100.0, 101.0, None, 103.0)
    assert factor_trace.connectgaps is False
    assert price_trace.connectgaps is False
    assert figure.layout.yaxis.title.text == "Factor (zscore)"
    assert figure.layout.yaxis2.title.text == "Price (close)"
    assert str(points[0].calculation_id) in status_trace.text[0]
    assert str(points[0].algorithm_run_id) in status_trace.text[0]
    assert "missing_source_bar" in status_trace.text[2]
    assert "Factor value=True" in status_trace.text[3]
    assert status_trace.marker.color[3] == "#17becf"
