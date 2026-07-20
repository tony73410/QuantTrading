from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

import pytest

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


def _query(**changes) -> FactorVisualizationQuery:
    values = {
        "symbol": "aapl",
        "factor_name": "deviation",
        "factor_version": "1",
        "start_time_utc": NOW - timedelta(days=1),
        "end_time_utc": NOW + timedelta(days=1),
        "timeframe": Timeframe.DAY,
        "adjustment": Adjustment.RAW,
        "feed": DataFeed.IEX,
        "price_field": PriceField.CLOSE,
    }
    values.update(changes)
    return FactorVisualizationQuery(**values)


def _point(**changes) -> FactorVisualizationPoint:
    values = {
        "calculation_id": UUID(int=1),
        "algorithm_run_id": UUID(int=2),
        "stage_id": UUID(int=3),
        "snapshot_id": UUID(int=4),
        "symbol": "AAPL",
        "as_of_utc": NOW,
        "timeframe": Timeframe.DAY,
        "adjustment": Adjustment.RAW,
        "feed": DataFeed.IEX,
        "factor_name": "deviation",
        "factor_version": "1",
        "factor_value": Decimal("-2.400"),
        "factor_unit": "zscore",
        "result_status": FactorStatus.VALID,
        "calculation_status": FactorCalculationStatus.SUCCESS,
        "source_data_end_utc": NOW,
        "source_bar_timestamp_utc": NOW,
        "price_field": PriceField.CLOSE,
        "price_value": Decimal("100.5000"),
        "source_price_status": FactorSourcePriceStatus.AVAILABLE,
        "error_code": None,
        "error_summary": None,
    }
    values.update(changes)
    return FactorVisualizationPoint(**values)


def test_visualization_query_normalizes_exact_identity_and_utc() -> None:
    query = _query()

    assert query.symbol == "AAPL"
    assert query.start_time_utc.tzinfo is UTC
    with pytest.raises(ValueError, match="start must be before end"):
        _query(start_time_utc=NOW, end_time_utc=NOW)
    with pytest.raises(ValueError, match="between 1 and 5000"):
        _query(limit=0)


def test_visualization_point_enforces_exact_source_bar_and_failed_evidence() -> None:
    assert _point().price_value == Decimal("100.5000")

    with pytest.raises(ValueError, match="exactly equal"):
        _point(source_bar_timestamp_utc=NOW - timedelta(minutes=1))
    with pytest.raises(ValueError, match="cannot carry Bar evidence"):
        _point(
            source_price_status=FactorSourcePriceStatus.MISSING_SOURCE_BAR,
            source_bar_timestamp_utc=None,
        )
    missing_field = _point(
        source_price_status=FactorSourcePriceStatus.MISSING_PRICE_FIELD,
        price_value=None,
    )
    assert missing_field.source_bar_timestamp_utc == NOW
    with pytest.raises(ValueError, match="cannot fabricate"):
        _point(calculation_status=FactorCalculationStatus.FAILED)


def test_visualization_series_requires_exact_query_identity_and_chronology() -> None:
    query = _query()
    first = _point(as_of_utc=NOW - timedelta(hours=1), calculation_id=UUID(int=5))
    second = _point()
    series = FactorVisualizationSeries(query, (first, second))
    assert series.count == 2

    with pytest.raises(ValueError, match="chronological"):
        FactorVisualizationSeries(query, (second, first))
    with pytest.raises(ValueError, match="query identity"):
        FactorVisualizationSeries(query, (_point(symbol="MSFT"),))
