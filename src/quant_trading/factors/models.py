"""Versioned, strategy-neutral contracts for single-asset factors."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from typing import TypeAlias
from uuid import UUID

from quant_trading.market_history.models import Adjustment, DataFeed, MarketBar, Timeframe

from .errors import FactorContractError, FactorInputError


FactorValue: TypeAlias = Decimal | int | bool | str
FactorParameterValue: TypeAlias = Decimal | int | bool | str | None


def _utc(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise FactorInputError(f"{field_name} must include a timezone")
    return value.astimezone(UTC)


def _required_text(value: str, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise FactorContractError(f"{field_name} must not be empty")
    return normalized


class FactorStatus(StrEnum):
    VALID = "valid"
    INSUFFICIENT_DATA = "insufficient_data"
    MISSING_INPUT = "missing_input"
    INVALID_INPUT = "invalid_input"
    CALCULATION_ERROR = "calculation_error"
    STALE = "stale"


@dataclass(frozen=True, slots=True, order=True)
class FactorParameter:
    name: str
    value: FactorParameterValue

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _required_text(self.name, "parameter name"))
        if self.value is not None and not isinstance(
            self.value, (Decimal, int, bool, str)
        ):
            raise FactorContractError("factor parameter has an unsupported value type")
        if isinstance(self.value, Decimal) and not self.value.is_finite():
            raise FactorContractError("factor parameter must be finite")


@dataclass(frozen=True, slots=True)
class FactorContext:
    as_of_utc: datetime
    parameters: tuple[FactorParameter, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "as_of_utc", _utc(self.as_of_utc, "as_of_utc"))
        names = [parameter.name for parameter in self.parameters]
        if len(names) != len(set(names)):
            raise FactorContractError("factor parameter names must be unique")


@dataclass(frozen=True, slots=True)
class MarketDataObservation:
    """A completed Bar plus the explicit time at which it became usable."""

    bar: MarketBar
    available_at_utc: datetime
    is_complete: bool = True

    def __post_init__(self) -> None:
        available = _utc(self.available_at_utc, "available_at_utc")
        if self.bar.timestamp_utc > available:
            raise FactorInputError("a bar cannot be available before its timestamp")
        object.__setattr__(self, "available_at_utc", available)


@dataclass(frozen=True, slots=True)
class MarketDataWindow:
    """Single-asset input containing only completed data available by ``as_of``."""

    symbol: str
    as_of_utc: datetime
    timeframe: Timeframe
    adjustment: Adjustment
    feed: DataFeed
    observations: tuple[MarketDataObservation, ...]

    def __post_init__(self) -> None:
        symbol = self.symbol.strip().upper()
        if not symbol:
            raise FactorInputError("symbol must not be empty")
        if not isinstance(self.timeframe, Timeframe):
            raise FactorInputError("timeframe must use the Timeframe enum")
        if not isinstance(self.adjustment, Adjustment):
            raise FactorInputError("adjustment must use the Adjustment enum")
        if not isinstance(self.feed, DataFeed):
            raise FactorInputError("feed must use the DataFeed enum")
        as_of = _utc(self.as_of_utc, "as_of_utc")
        previous_timestamp: datetime | None = None
        for observation in self.observations:
            bar = observation.bar
            if not observation.is_complete:
                raise FactorInputError("incomplete bars cannot enter a factor window")
            if observation.available_at_utc > as_of:
                raise FactorInputError("factor window contains data unavailable at as_of")
            if bar.symbol != symbol:
                raise FactorInputError("factor window mixes symbols")
            if (
                bar.timeframe is not self.timeframe
                or bar.adjustment is not self.adjustment
                or bar.feed is not self.feed
            ):
                raise FactorInputError("factor window mixes data dimensions")
            if previous_timestamp is not None and bar.timestamp_utc <= previous_timestamp:
                raise FactorInputError("factor observations must be strictly ordered")
            prices = (bar.open, bar.high, bar.low, bar.close)
            if any(not value.is_finite() for value in prices):
                raise FactorInputError("factor window contains a non-finite price")
            if bar.vwap is not None and not bar.vwap.is_finite():
                raise FactorInputError("factor window contains a non-finite VWAP")
            if (
                bar.high < bar.low
                or not bar.low <= bar.open <= bar.high
                or not bar.low <= bar.close <= bar.high
            ):
                raise FactorInputError("factor window contains inconsistent OHLC")
            if bar.volume < 0 or (bar.trade_count is not None and bar.trade_count < 0):
                raise FactorInputError("factor window contains a negative count")
            previous_timestamp = bar.timestamp_utc
        object.__setattr__(self, "symbol", symbol)
        object.__setattr__(self, "as_of_utc", as_of)

    @property
    def bars(self) -> tuple[MarketBar, ...]:
        return tuple(observation.bar for observation in self.observations)


@dataclass(frozen=True, slots=True)
class FactorResult:
    symbol: str
    as_of_utc: datetime
    timeframe: Timeframe
    factor_name: str
    factor_version: str
    value: FactorValue | None
    unit: str | None
    parameters: tuple[FactorParameter, ...]
    lookback: int | None
    status: FactorStatus
    quality_flags: tuple[str, ...]
    calculated_at_utc: datetime
    source_data_start_utc: datetime | None
    source_data_end_utc: datetime | None

    def __post_init__(self) -> None:
        symbol = self.symbol.strip().upper()
        if not symbol:
            raise FactorContractError("factor result symbol must not be empty")
        as_of = _utc(self.as_of_utc, "factor as_of_utc")
        calculated = _utc(self.calculated_at_utc, "calculated_at_utc")
        name = _required_text(self.factor_name, "factor_name")
        version = _required_text(self.factor_version, "factor_version")
        if not isinstance(self.timeframe, Timeframe):
            raise FactorContractError("factor timeframe must use the Timeframe enum")
        if not isinstance(self.status, FactorStatus):
            raise FactorContractError("factor status must use the FactorStatus enum")
        if self.lookback is not None and self.lookback < 0:
            raise FactorContractError("lookback must not be negative")
        if self.value is not None and not isinstance(
            self.value, (Decimal, int, bool, str)
        ):
            raise FactorContractError("factor has an unsupported value type")
        if self.status is FactorStatus.VALID and self.value is None:
            raise FactorContractError("a valid factor must contain a value")
        if isinstance(self.value, Decimal) and not self.value.is_finite():
            raise FactorContractError("factor value must be finite")
        missing_statuses = {
            FactorStatus.INSUFFICIENT_DATA,
            FactorStatus.MISSING_INPUT,
            FactorStatus.INVALID_INPUT,
            FactorStatus.CALCULATION_ERROR,
        }
        if self.status in missing_statuses and self.value is not None:
            raise FactorContractError("a missing/invalid factor must not fabricate a value")
        start = (
            _utc(self.source_data_start_utc, "source_data_start_utc")
            if self.source_data_start_utc is not None
            else None
        )
        end = (
            _utc(self.source_data_end_utc, "source_data_end_utc")
            if self.source_data_end_utc is not None
            else None
        )
        if (start is None) != (end is None):
            raise FactorContractError("source data bounds must be both present or both absent")
        if start is not None and (start > end or end > as_of):
            raise FactorContractError("source data bounds are inconsistent with as_of")
        object.__setattr__(self, "symbol", symbol)
        object.__setattr__(self, "as_of_utc", as_of)
        object.__setattr__(self, "calculated_at_utc", calculated)
        object.__setattr__(self, "factor_name", name)
        object.__setattr__(self, "factor_version", version)
        object.__setattr__(self, "source_data_start_utc", start)
        object.__setattr__(self, "source_data_end_utc", end)


@dataclass(frozen=True, slots=True)
class FactorSnapshot:
    snapshot_id: UUID
    symbol: str
    as_of_utc: datetime
    timeframe: Timeframe
    results: tuple[FactorResult, ...]
    calculated_at_utc: datetime

    def __post_init__(self) -> None:
        symbol = self.symbol.strip().upper()
        as_of = _utc(self.as_of_utc, "snapshot as_of_utc")
        calculated = _utc(self.calculated_at_utc, "snapshot calculated_at_utc")
        names: list[str] = []
        for result in self.results:
            if (
                result.symbol != symbol
                or result.as_of_utc != as_of
                or result.timeframe is not self.timeframe
            ):
                raise FactorContractError("snapshot contains a mismatched factor result")
            names.append(result.factor_name)
        if len(names) != len(set(names)):
            raise FactorContractError("snapshot contains duplicate factor names")
        object.__setattr__(self, "symbol", symbol)
        object.__setattr__(self, "as_of_utc", as_of)
        object.__setattr__(self, "calculated_at_utc", calculated)


@dataclass(frozen=True, slots=True)
class FactorSnapshotCollection:
    collection_id: UUID
    as_of_utc: datetime
    snapshots: tuple[FactorSnapshot, ...]

    def __post_init__(self) -> None:
        as_of = _utc(self.as_of_utc, "collection as_of_utc")
        if not self.snapshots:
            raise FactorContractError("factor snapshot collection must not be empty")
        symbols: list[str] = []
        for snapshot in self.snapshots:
            if snapshot.as_of_utc != as_of:
                raise FactorContractError("factor snapshots must share one as_of time")
            symbols.append(snapshot.symbol)
        if len(symbols) != len(set(symbols)):
            raise FactorContractError("factor snapshot collection contains duplicate symbols")
        object.__setattr__(self, "as_of_utc", as_of)
