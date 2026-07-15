from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

import pytest

from quant_trading.factors import (
    FactorContext,
    FactorDefinition,
    FactorDefinitionParameter,
    FactorStatus,
    MarketDataObservation,
    MarketDataWindow,
    SafeExpressionFactorCalculator,
    parse_and_validate_expression,
)
from quant_trading.factors.errors import FactorDefinitionError
from quant_trading.market_history.models import (
    Adjustment,
    DataFeed,
    MarketBar,
    Timeframe,
)


AS_OF = datetime(2026, 7, 13, 21, 0, tzinfo=UTC)


def _definition(expression: str, *, minimum: int = 1) -> FactorDefinition:
    return FactorDefinition(
        definition_id=UUID("00000000-0000-0000-0000-000000000801"),
        factor_id="user.return_ratio",
        version=1,
        display_name="User return ratio",
        description="Test-only user-authored restricted expression.",
        expression=expression,
        minimum_observations=minimum,
        output_unit="ratio",
        missing_input_policy="return_missing_status",
        parameters=(FactorDefinitionParameter("window", Decimal("2")),),
        created_at_utc=AS_OF,
        created_by="test",
        change_reason="Regression test",
    )


def _window(*closes: str, vwap: bool = True) -> MarketDataWindow:
    observations = []
    for index, close in enumerate(closes):
        timestamp = AS_OF - timedelta(days=len(closes) - index)
        value = Decimal(close)
        bar = MarketBar(
            symbol="AAPL",
            timestamp_utc=timestamp,
            open=value,
            high=value,
            low=value,
            close=value,
            volume=100 + index,
            vwap=value if vwap else None,
            trade_count=10,
            timeframe=Timeframe.DAY,
            adjustment=Adjustment.RAW,
            feed=DataFeed.IEX,
            source="fake",
            fetched_at_utc=AS_OF,
        )
        observations.append(MarketDataObservation(bar, timestamp))
    return MarketDataWindow(
        "AAPL",
        AS_OF,
        Timeframe.DAY,
        Adjustment.RAW,
        DataFeed.IEX,
        tuple(observations),
    )


def test_restricted_expression_calculates_deterministically() -> None:
    calculator = SafeExpressionFactorCalculator(
        _definition('latest("close") / mean("close", window)'),
        clock=lambda: AS_OF,
    )

    result = calculator.calculate(_window("10", "20"), FactorContext(AS_OF))

    assert result.status is FactorStatus.VALID
    assert result.value == Decimal("20") / Decimal("15")
    assert result.factor_name == "user.return_ratio"
    assert result.factor_version == "1"


@pytest.mark.parametrize(
    "expression",
    (
        '__import__("os")',
        '(1).__class__',
        '[value for value in (1, 2)]',
        'open("file")',
        'latest("close")[0]',
        'latest("not_a_market_field")',
        '"plain text"',
        'mean("close")',
    ),
)
def test_restricted_expression_rejects_arbitrary_python(expression: str) -> None:
    with pytest.raises(FactorDefinitionError):
        parse_and_validate_expression(expression, ("window",))


def test_insufficient_and_missing_inputs_never_become_zero() -> None:
    insufficient = SafeExpressionFactorCalculator(
        _definition('latest("close")', minimum=2),
        clock=lambda: AS_OF,
    ).calculate(_window("10"), FactorContext(AS_OF))
    missing = SafeExpressionFactorCalculator(
        _definition('latest("vwap")'),
        clock=lambda: AS_OF,
    ).calculate(_window("10", vwap=False), FactorContext(AS_OF))

    assert (insufficient.status, insufficient.value) == (
        FactorStatus.INSUFFICIENT_DATA,
        None,
    )
    assert (missing.status, missing.value) == (FactorStatus.MISSING_INPUT, None)


def test_definition_rejects_an_unimplemented_missing_value_policy() -> None:
    with pytest.raises(FactorDefinitionError):
        FactorDefinition(
            **{
                field: getattr(_definition("1"), field)
                for field in _definition("1").__dataclass_fields__
                if field != "missing_input_policy"
            },
            missing_input_policy="fill_with_zero",
        )
