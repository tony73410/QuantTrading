"""Restricted expression validator and calculator; never executes Python source."""

from __future__ import annotations

import ast
from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal, DivisionByZero, InvalidOperation

from .definitions import FactorDefinition
from .errors import FactorDefinitionError
from .expression_language import (
    MARKET_FIELDS,
    SERIES_FUNCTIONS,
    parse_and_validate_expression,
)
from .models import FactorContext, FactorParameter, FactorResult, FactorStatus, MarketDataWindow


class _InsufficientData(Exception):
    pass


class _MissingInput(Exception):
    pass


class SafeExpressionFactorCalculator:
    """Evaluate one immutable definition using a small numeric DSL."""

    def __init__(
        self,
        definition: FactorDefinition,
        *,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self.definition = definition
        self._tree = parse_and_validate_expression(
            definition.expression,
            tuple(item.name for item in definition.parameters),
        )
        self._clock = clock

    @property
    def factor_name(self) -> str:
        return self.definition.factor_id

    @property
    def factor_version(self) -> str:
        return str(self.definition.version)

    @property
    def minimum_observations(self) -> int:
        return self.definition.minimum_observations

    @property
    def output_unit(self) -> str | None:
        return self.definition.output_unit

    @property
    def missing_input_policy(self) -> str:
        return self.definition.missing_input_policy

    def calculate(self, market_data: MarketDataWindow, context: FactorContext) -> FactorResult:
        defaults = {item.name: item.default_value for item in self.definition.parameters}
        supplied = {item.name: item.value for item in context.parameters}
        unknown = set(supplied) - set(defaults)
        if unknown:
            raise FactorDefinitionError(f"unknown factor parameters: {', '.join(sorted(unknown))}")
        parameters: dict[str, Decimal] = dict(defaults)
        for name, value in supplied.items():
            if isinstance(value, bool) or not isinstance(value, (Decimal, int)):
                raise FactorDefinitionError(f"parameter {name} must be numeric")
            parameters[name] = Decimal(value)
        status = FactorStatus.VALID
        value: Decimal | None = None
        flags: tuple[str, ...] = ()
        if len(market_data.observations) < self.minimum_observations:
            status = FactorStatus.INSUFFICIENT_DATA
            flags = ("minimum_observations",)
        else:
            try:
                value = self._evaluate(self._tree.body, market_data, parameters)
                if not value.is_finite():
                    raise FactorDefinitionError("expression produced a non-finite value")
            except _InsufficientData:
                status = FactorStatus.INSUFFICIENT_DATA
                flags = ("expression_lookback",)
            except _MissingInput:
                status = FactorStatus.MISSING_INPUT
                flags = ("missing_market_field",)
            except (DivisionByZero, InvalidOperation, ZeroDivisionError):
                status = FactorStatus.CALCULATION_ERROR
                flags = ("numeric_error",)
        bars = market_data.bars
        return FactorResult(
            symbol=market_data.symbol,
            as_of_utc=market_data.as_of_utc,
            timeframe=market_data.timeframe,
            factor_name=self.factor_name,
            factor_version=self.factor_version,
            value=value,
            unit=self.output_unit,
            parameters=tuple(FactorParameter(name, item) for name, item in sorted(parameters.items())),
            lookback=self.minimum_observations,
            status=status,
            quality_flags=flags,
            calculated_at_utc=self._clock(),
            source_data_start_utc=bars[0].timestamp_utc if bars and status is FactorStatus.VALID else None,
            source_data_end_utc=bars[-1].timestamp_utc if bars and status is FactorStatus.VALID else None,
        )

    def _evaluate(self, node: ast.AST, market_data: MarketDataWindow, parameters: dict[str, Decimal]) -> Decimal:
        if isinstance(node, ast.Constant):
            if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
                raise FactorDefinitionError("only numeric constants are allowed")
            return Decimal(str(node.value))
        if isinstance(node, ast.Name):
            try:
                return parameters[node.id]
            except KeyError as exc:
                raise FactorDefinitionError(f"unknown parameter: {node.id}") from exc
        if isinstance(node, ast.UnaryOp):
            value = self._evaluate(node.operand, market_data, parameters)
            return value if isinstance(node.op, ast.UAdd) else -value
        if isinstance(node, ast.BinOp):
            left = self._evaluate(node.left, market_data, parameters)
            right = self._evaluate(node.right, market_data, parameters)
            if isinstance(node.op, ast.Add): return left + right
            if isinstance(node.op, ast.Sub): return left - right
            if isinstance(node.op, ast.Mult): return left * right
            return left / right
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id == "absolute":
                if len(node.args) != 1:
                    raise FactorDefinitionError("absolute(value) requires one argument")
                return abs(self._evaluate(node.args[0], market_data, parameters))
            return self._series_call(node.func.id, node.args, market_data, parameters)
        raise FactorDefinitionError("unsupported expression node")

    def _series_call(self, function: str, args: list[ast.expr], market_data: MarketDataWindow, parameters: dict[str, Decimal]) -> Decimal:
        expected = 1 if function == "latest" else 2
        if len(args) != expected or not isinstance(args[0], ast.Constant) or not isinstance(args[0].value, str):
            raise FactorDefinitionError(f"{function} requires a quoted market field" + (" and a period" if expected == 2 else ""))
        field = args[0].value
        if field not in MARKET_FIELDS:
            raise FactorDefinitionError(f"unsupported market field: {field}")
        bars = market_data.bars
        if not bars:
            raise _InsufficientData
        if function == "latest":
            return self._field_value(bars[-1], field)
        period_value = self._evaluate(args[1], market_data, parameters)
        if period_value != period_value.to_integral_value() or period_value < 0:
            raise FactorDefinitionError("period must be a non-negative integer")
        period = int(period_value)
        if function == "lag":
            if period >= len(bars): raise _InsufficientData
            return self._field_value(bars[-1 - period], field)
        if period < 1:
            raise FactorDefinitionError("window length must be positive")
        if period > len(bars): raise _InsufficientData
        values = [self._field_value(bar, field) for bar in bars[-period:]]
        if function == "mean": return sum(values, Decimal(0)) / Decimal(period)
        if function == "sum": return sum(values, Decimal(0))
        if function == "minimum": return min(values)
        return max(values)

    @staticmethod
    def _field_value(bar: object, field: str) -> Decimal:
        value = getattr(bar, field)
        if value is None:
            raise _MissingInput
        return value if isinstance(value, Decimal) else Decimal(value)
