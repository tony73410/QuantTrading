"""Strategy-neutral engine that executes injected factor calculators."""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterable
from datetime import UTC, datetime
from uuid import UUID, uuid4

from .errors import FactorContractError, FactorRegistryError
from .interfaces import FactorCalculator
from .models import (
    FactorContext,
    FactorResult,
    FactorSnapshot,
    FactorStatus,
    MarketDataWindow,
)
from .registry import FactorRegistry


logger = logging.getLogger(__name__)


class SingleAssetFactorEngine:
    """Run registered calculators; it never interprets results as trades."""

    def __init__(
        self,
        calculators: Iterable[FactorCalculator] | FactorRegistry,
        *,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
        id_factory: Callable[[], UUID] = uuid4,
    ) -> None:
        self._registry = (
            calculators
            if isinstance(calculators, FactorRegistry)
            else FactorRegistry(calculators)
        )
        self._clock = clock
        self._id_factory = id_factory

    def calculate(
        self,
        market_data: MarketDataWindow,
        context: FactorContext,
    ) -> FactorSnapshot:
        if context.as_of_utc != market_data.as_of_utc:
            raise FactorContractError("factor context and market window must share as_of")
        calculators = self._registry.calculators
        if not calculators:
            raise FactorRegistryError("no factor calculators are registered")
        results = tuple(
            self._calculate_one(calculator, market_data, context)
            for calculator in calculators
        )
        return FactorSnapshot(
            snapshot_id=self._id_factory(),
            symbol=market_data.symbol,
            as_of_utc=market_data.as_of_utc,
            timeframe=market_data.timeframe,
            results=results,
            calculated_at_utc=self._clock(),
        )

    def _calculate_one(
        self,
        calculator: FactorCalculator,
        market_data: MarketDataWindow,
        context: FactorContext,
    ) -> FactorResult:
        try:
            result = calculator.calculate(market_data, context)
            if (
                result.factor_name != calculator.factor_name
                or result.factor_version != calculator.factor_version
                or result.symbol != market_data.symbol
                or result.as_of_utc != market_data.as_of_utc
                or result.timeframe is not market_data.timeframe
            ):
                raise FactorContractError("calculator returned mismatched factor metadata")
            return result
        except Exception as exc:
            logger.exception(
                "Factor calculation failed factor_name=%s factor_version=%s",
                calculator.factor_name,
                calculator.factor_version,
            )
            return FactorResult(
                symbol=market_data.symbol,
                as_of_utc=market_data.as_of_utc,
                timeframe=market_data.timeframe,
                factor_name=calculator.factor_name,
                factor_version=calculator.factor_version,
                value=None,
                unit=calculator.output_unit,
                parameters=context.parameters,
                lookback=calculator.minimum_observations,
                status=FactorStatus.CALCULATION_ERROR,
                quality_flags=(type(exc).__name__,),
                calculated_at_utc=self._clock(),
                source_data_start_utc=None,
                source_data_end_utc=None,
            )
