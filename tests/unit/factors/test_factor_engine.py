from __future__ import annotations

from dataclasses import fields
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

import pytest

from quant_trading.factors import (
    FactorContext,
    FactorRegistry,
    FactorResult,
    FactorSnapshot,
    FactorStatus,
    MarketDataObservation,
    MarketDataWindow,
    SingleAssetFactorEngine,
)
from quant_trading.factors.errors import FactorContractError, FactorInputError, FactorRegistryError
from quant_trading.market_history.models import Adjustment, DataFeed, MarketBar, Timeframe


AS_OF = datetime(2026, 7, 13, 21, 0, tzinfo=UTC)
CALCULATED_AT = datetime(2026, 7, 13, 21, 1, tzinfo=UTC)
SNAPSHOT_ID = UUID("00000000-0000-0000-0000-000000000101")


def _bar(timestamp: datetime, close: str = "123.45") -> MarketBar:
    return MarketBar(
        symbol="AAPL",
        timestamp_utc=timestamp,
        open=Decimal(close),
        high=Decimal(close),
        low=Decimal(close),
        close=Decimal(close),
        volume=100,
        vwap=Decimal(close),
        trade_count=10,
        timeframe=Timeframe.DAY,
        adjustment=Adjustment.RAW,
        feed=DataFeed.IEX,
        source="test",
        fetched_at_utc=AS_OF,
    )


def _window() -> MarketDataWindow:
    bar = _bar(datetime(2026, 7, 10, 13, 30, tzinfo=UTC))
    return MarketDataWindow(
        symbol="AAPL",
        as_of_utc=AS_OF,
        timeframe=Timeframe.DAY,
        adjustment=Adjustment.RAW,
        feed=DataFeed.IEX,
        observations=(MarketDataObservation(bar, AS_OF),),
    )


class FakeCloseFactor:
    factor_name = "test_close"
    factor_version = "test-v1"
    minimum_observations = 1
    output_unit = "USD"
    missing_input_policy = "return INSUFFICIENT_DATA with value=None"

    def calculate(
        self, market_data: MarketDataWindow, context: FactorContext
    ) -> FactorResult:
        if len(market_data.bars) < self.minimum_observations:
            return FactorResult(
                symbol=market_data.symbol,
                as_of_utc=context.as_of_utc,
                timeframe=market_data.timeframe,
                factor_name=self.factor_name,
                factor_version=self.factor_version,
                value=None,
                unit=self.output_unit,
                parameters=context.parameters,
                lookback=self.minimum_observations,
                status=FactorStatus.INSUFFICIENT_DATA,
                quality_flags=("TEST_ONLY",),
                calculated_at_utc=CALCULATED_AT,
                source_data_start_utc=None,
                source_data_end_utc=None,
            )
        bar = market_data.bars[-1]
        return FactorResult(
            symbol=market_data.symbol,
            as_of_utc=context.as_of_utc,
            timeframe=market_data.timeframe,
            factor_name=self.factor_name,
            factor_version=self.factor_version,
            value=bar.close,
            unit=self.output_unit,
            parameters=context.parameters,
            lookback=self.minimum_observations,
            status=FactorStatus.VALID,
            quality_flags=("TEST_ONLY",),
            calculated_at_utc=CALCULATED_AT,
            source_data_start_utc=bar.timestamp_utc,
            source_data_end_utc=bar.timestamp_utc,
        )


def _engine(calculator: object = None) -> SingleAssetFactorEngine:
    return SingleAssetFactorEngine(
        (calculator or FakeCloseFactor(),),
        clock=lambda: CALCULATED_AT,
        id_factory=lambda: SNAPSHOT_ID,
    )


def test_factor_is_deterministic_with_fixed_input_and_metadata_factories() -> None:
    context = FactorContext(AS_OF)
    first = _engine().calculate(_window(), context)
    second = _engine().calculate(_window(), context)

    assert first == second
    assert first.results[0].value == Decimal("123.45")
    assert first.results[0].status is FactorStatus.VALID


def test_insufficient_data_is_explicit_and_never_fabricated_as_zero() -> None:
    empty = MarketDataWindow(
        "AAPL",
        AS_OF,
        Timeframe.DAY,
        Adjustment.RAW,
        DataFeed.IEX,
        (),
    )

    result = _engine().calculate(empty, FactorContext(AS_OF)).results[0]

    assert result.status is FactorStatus.INSUFFICIENT_DATA
    assert result.value is None


@pytest.mark.parametrize(
    ("available_at", "complete"),
    [
        (datetime(2026, 7, 14, 21, 0, tzinfo=UTC), True),
        (AS_OF, False),
    ],
)
def test_factor_window_rejects_future_or_incomplete_bars(
    available_at: datetime, complete: bool
) -> None:
    observation = MarketDataObservation(
        _bar(datetime(2026, 7, 10, 13, 30, tzinfo=UTC)),
        available_at,
        complete,
    )
    with pytest.raises(FactorInputError):
        MarketDataWindow(
            "AAPL",
            AS_OF,
            Timeframe.DAY,
            Adjustment.RAW,
            DataFeed.IEX,
            (observation,),
        )


def test_nonvalid_factor_cannot_fabricate_a_value() -> None:
    with pytest.raises(FactorContractError):
        FactorResult(
            symbol="AAPL",
            as_of_utc=AS_OF,
            timeframe=Timeframe.DAY,
            factor_name="test",
            factor_version="test-v1",
            value=0,
            unit=None,
            parameters=(),
            lookback=1,
            status=FactorStatus.MISSING_INPUT,
            quality_flags=(),
            calculated_at_utc=CALCULATED_AT,
            source_data_start_utc=None,
            source_data_end_utc=None,
        )

    with pytest.raises(FactorContractError):
        FactorResult(
            symbol="AAPL",
            as_of_utc=AS_OF,
            timeframe=Timeframe.DAY,
            factor_name="test",
            factor_version="test-v1",
            value=Decimal("1"),
            unit=None,
            parameters=(),
            lookback=1,
            status="VALID",  # type: ignore[arg-type] - runtime boundary test
            quality_flags=(),
            calculated_at_utc=CALCULATED_AT,
            source_data_start_utc=None,
            source_data_end_utc=None,
        )


def test_factor_contract_rejects_nonfinite_values_and_invalid_market_prices() -> None:
    with pytest.raises(FactorContractError):
        FactorResult(
            symbol="AAPL",
            as_of_utc=AS_OF,
            timeframe=Timeframe.DAY,
            factor_name="test",
            factor_version="test-v1",
            value=Decimal("NaN"),
            unit=None,
            parameters=(),
            lookback=1,
            status=FactorStatus.VALID,
            quality_flags=(),
            calculated_at_utc=CALCULATED_AT,
            source_data_start_utc=None,
            source_data_end_utc=None,
        )

    invalid_bar = _bar(datetime(2026, 7, 10, 13, 30, tzinfo=UTC))
    object.__setattr__(invalid_bar, "volume", -1)
    with pytest.raises(FactorInputError):
        MarketDataWindow(
            "AAPL",
            AS_OF,
            Timeframe.DAY,
            Adjustment.RAW,
            DataFeed.IEX,
            (MarketDataObservation(invalid_bar, AS_OF),),
        )

    with pytest.raises(FactorContractError):
        FactorResult(
            symbol="AAPL",
            as_of_utc=AS_OF,
            timeframe=Timeframe.DAY,
            factor_name="test",
            factor_version="test-v1",
            value=1.5,  # type: ignore[arg-type] - intentional runtime contract test
            unit=None,
            parameters=(),
            lookback=1,
            status=FactorStatus.VALID,
            quality_flags=(),
            calculated_at_utc=CALCULATED_AT,
            source_data_start_utc=None,
            source_data_end_utc=None,
        )


def test_registry_uses_unique_names_instead_of_factor_conditionals() -> None:
    registry = FactorRegistry((FakeCloseFactor(),))
    assert registry.get("test_close").factor_version == "test-v1"
    with pytest.raises(FactorRegistryError):
        registry.register(FakeCloseFactor())


def test_factor_snapshot_contract_keeps_traceability_fields() -> None:
    names = {field.name for field in fields(FactorSnapshot)}
    assert names == {
        "snapshot_id",
        "symbol",
        "as_of_utc",
        "timeframe",
        "results",
        "calculated_at_utc",
    }
