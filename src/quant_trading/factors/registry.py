"""Explicit calculator registration without factor-name conditionals."""

from __future__ import annotations

from collections.abc import Iterable

from .errors import FactorRegistryError
from .interfaces import FactorCalculator


class FactorRegistry:
    def __init__(self, calculators: Iterable[FactorCalculator] = ()) -> None:
        self._calculators: dict[str, FactorCalculator] = {}
        for calculator in calculators:
            self.register(calculator)

    def register(self, calculator: FactorCalculator) -> None:
        name = calculator.factor_name.strip()
        if not name:
            raise FactorRegistryError("factor_name must not be empty")
        if name in self._calculators:
            raise FactorRegistryError(f"factor already registered: {name}")
        if not calculator.factor_version.strip():
            raise FactorRegistryError("factor_version must not be empty")
        if calculator.minimum_observations < 0:
            raise FactorRegistryError("minimum_observations must not be negative")
        if not calculator.missing_input_policy.strip():
            raise FactorRegistryError("missing_input_policy must not be empty")
        self._calculators[name] = calculator

    def get(self, factor_name: str) -> FactorCalculator:
        try:
            return self._calculators[factor_name]
        except KeyError as exc:
            raise FactorRegistryError(f"factor is not registered: {factor_name}") from exc

    @property
    def calculators(self) -> tuple[FactorCalculator, ...]:
        return tuple(self._calculators.values())
