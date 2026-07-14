"""Public interfaces for replaceable single-asset factor calculators."""

from __future__ import annotations

from typing import Protocol

from .models import FactorContext, FactorResult, MarketDataWindow


class FactorCalculator(Protocol):
    @property
    def factor_name(self) -> str: ...

    @property
    def factor_version(self) -> str: ...

    @property
    def minimum_observations(self) -> int: ...

    @property
    def output_unit(self) -> str | None: ...

    @property
    def missing_input_policy(self) -> str: ...

    def calculate(
        self,
        market_data: MarketDataWindow,
        context: FactorContext,
    ) -> FactorResult: ...
