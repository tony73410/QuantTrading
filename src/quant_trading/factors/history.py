"""Typed, strategy-neutral views for persisted Factor research history."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from quant_trading.market_history.models import Adjustment, DataFeed, PriceField, Timeframe

from .models import FactorParameter, FactorStatus, FactorValue
from .storage_models import FactorCalculationStatus


def _utc(value: datetime | None, field_name: str) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must include a timezone")
    return value.astimezone(UTC)


def _text(value: str, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return normalized


@dataclass(frozen=True, slots=True)
class FactorHistoryQuery:
    symbol: str | None = None
    start_time_utc: datetime | None = None
    end_time_utc: datetime | None = None
    factor_name: str | None = None
    factor_version: str | None = None
    calculation_status: FactorCalculationStatus | None = None
    result_status: FactorStatus | None = None
    timeframe: Timeframe | None = None
    adjustment: Adjustment | None = None
    feed: DataFeed | None = None
    limit: int = 500

    def __post_init__(self) -> None:
        if not 1 <= self.limit <= 5000:
            raise ValueError("Factor history limit must be between 1 and 5000")
        if self.symbol is not None:
            object.__setattr__(self, "symbol", _text(self.symbol, "symbol").upper())
        if self.factor_name is not None:
            object.__setattr__(self, "factor_name", _text(self.factor_name, "factor_name"))
        if self.factor_version is not None:
            object.__setattr__(self, "factor_version", _text(self.factor_version, "factor_version"))
            if self.factor_name is None:
                raise ValueError("factor_version requires factor_name")
        start = _utc(self.start_time_utc, "start_time_utc")
        end = _utc(self.end_time_utc, "end_time_utc")
        if start is not None and end is not None and start >= end:
            raise ValueError("Factor history start must be before end")
        object.__setattr__(self, "start_time_utc", start)
        object.__setattr__(self, "end_time_utc", end)


@dataclass(frozen=True, slots=True)
class FactorHistoryRecord:
    calculation_id: UUID
    algorithm_run_id: UUID | None
    stage_id: UUID | None
    snapshot_id: UUID | None
    symbol: str
    as_of_utc: datetime
    timeframe: Timeframe
    adjustment: Adjustment
    feed: DataFeed
    factor_name: str | None
    factor_version: str | None
    value: FactorValue | None
    unit: str | None
    parameters: tuple[FactorParameter, ...]
    lookback: int | None
    result_status: FactorStatus | None
    quality_flags: tuple[str, ...]
    calculated_at_utc: datetime | None
    source_data_start_utc: datetime | None
    source_data_end_utc: datetime | None
    calculation_status: FactorCalculationStatus
    started_at_utc: datetime
    completed_at_utc: datetime | None
    error_code: str | None
    error_summary: str | None

    def __post_init__(self) -> None:
        symbol = _text(self.symbol, "symbol").upper()
        as_of = _utc(self.as_of_utc, "as_of_utc")
        started = _utc(self.started_at_utc, "started_at_utc")
        completed = _utc(self.completed_at_utc, "completed_at_utc")
        calculated = _utc(self.calculated_at_utc, "calculated_at_utc")
        source_start = _utc(self.source_data_start_utc, "source_data_start_utc")
        source_end = _utc(self.source_data_end_utc, "source_data_end_utc")
        if (self.factor_name is None) != (self.factor_version is None):
            raise ValueError("Factor history identity must be both present or both absent")
        if self.factor_name is not None:
            object.__setattr__(self, "factor_name", _text(self.factor_name, "factor_name"))
            object.__setattr__(self, "factor_version", _text(self.factor_version or "", "factor_version"))
        if (source_start is None) != (source_end is None):
            raise ValueError("Factor history source bounds must be both present or absent")
        if completed is not None and completed < started:
            raise ValueError("Factor calculation completion cannot precede start")
        if self.lookback is not None and self.lookback < 0:
            raise ValueError("Factor lookback cannot be negative")
        if isinstance(self.value, float):
            raise ValueError("Factor history values must not use binary float")
        if self.calculation_status is FactorCalculationStatus.FAILED:
            if self.snapshot_id is not None or self.value is not None:
                raise ValueError("failed Factor calculations cannot fabricate results")
        object.__setattr__(self, "symbol", symbol)
        object.__setattr__(self, "as_of_utc", as_of)
        object.__setattr__(self, "started_at_utc", started)
        object.__setattr__(self, "completed_at_utc", completed)
        object.__setattr__(self, "calculated_at_utc", calculated)
        object.__setattr__(self, "source_data_start_utc", source_start)
        object.__setattr__(self, "source_data_end_utc", source_end)


class FactorSourcePriceStatus(StrEnum):
    """Whether an exact persisted source-Bar price is available for display."""

    AVAILABLE = "available"
    NO_SOURCE_WINDOW = "no_source_window"
    MISSING_SOURCE_BAR = "missing_source_bar"
    MISSING_PRICE_FIELD = "missing_price_field"


@dataclass(frozen=True, slots=True)
class FactorVisualizationQuery:
    """Request one exact Factor identity and one exact stored price field."""

    symbol: str
    factor_name: str
    factor_version: str
    start_time_utc: datetime
    end_time_utc: datetime
    timeframe: Timeframe
    adjustment: Adjustment
    feed: DataFeed
    price_field: PriceField = PriceField.CLOSE
    limit: int = 500

    def __post_init__(self) -> None:
        if not 1 <= self.limit <= 5000:
            raise ValueError("Factor visualization limit must be between 1 and 5000")
        for field_name, value, enum_type in (
            ("timeframe", self.timeframe, Timeframe),
            ("adjustment", self.adjustment, Adjustment),
            ("feed", self.feed, DataFeed),
            ("price_field", self.price_field, PriceField),
        ):
            if not isinstance(value, enum_type):
                raise ValueError(f"{field_name} must use {enum_type.__name__}")
        start = _utc(self.start_time_utc, "start_time_utc")
        end = _utc(self.end_time_utc, "end_time_utc")
        if start is None or end is None or start >= end:
            raise ValueError("Factor visualization start must be before end")
        object.__setattr__(self, "symbol", _text(self.symbol, "symbol").upper())
        object.__setattr__(self, "factor_name", _text(self.factor_name, "factor_name"))
        object.__setattr__(self, "factor_version", _text(self.factor_version, "factor_version"))
        object.__setattr__(self, "start_time_utc", start)
        object.__setattr__(self, "end_time_utc", end)


@dataclass(frozen=True, slots=True)
class FactorVisualizationPoint:
    """Persisted Factor evidence plus only its exact final source-Bar price."""

    calculation_id: UUID
    algorithm_run_id: UUID | None
    stage_id: UUID | None
    snapshot_id: UUID | None
    symbol: str
    as_of_utc: datetime
    timeframe: Timeframe
    adjustment: Adjustment
    feed: DataFeed
    factor_name: str
    factor_version: str
    factor_value: FactorValue | None
    factor_unit: str | None
    result_status: FactorStatus | None
    calculation_status: FactorCalculationStatus
    source_data_end_utc: datetime | None
    source_bar_timestamp_utc: datetime | None
    price_field: PriceField
    price_value: Decimal | None
    source_price_status: FactorSourcePriceStatus
    error_code: str | None
    error_summary: str | None

    def __post_init__(self) -> None:
        as_of = _utc(self.as_of_utc, "as_of_utc")
        source_end = _utc(self.source_data_end_utc, "source_data_end_utc")
        source_bar = _utc(self.source_bar_timestamp_utc, "source_bar_timestamp_utc")
        if isinstance(self.factor_value, float) or isinstance(self.price_value, float):
            raise ValueError("Factor visualization values must not use binary float")
        if self.calculation_status is FactorCalculationStatus.FAILED:
            if self.snapshot_id is not None or self.factor_value is not None:
                raise ValueError("failed Factor calculations cannot fabricate results")
        if self.source_price_status is FactorSourcePriceStatus.AVAILABLE:
            if source_end is None or source_bar is None or self.price_value is None:
                raise ValueError("available source price requires timestamp and Decimal value")
            if source_bar != source_end:
                raise ValueError("source Bar timestamp must exactly equal source_data_end_utc")
        elif self.source_price_status is FactorSourcePriceStatus.MISSING_PRICE_FIELD:
            if source_end is None or source_bar is None or self.price_value is not None:
                raise ValueError("missing price field requires the exact Bar but no value")
            if source_bar != source_end:
                raise ValueError("source Bar timestamp must exactly equal source_data_end_utc")
        elif self.price_value is not None or source_bar is not None:
            raise ValueError("missing source Bar cannot carry Bar evidence")
        if self.source_price_status is FactorSourcePriceStatus.NO_SOURCE_WINDOW:
            if source_end is not None:
                raise ValueError("no-source-window status requires no source_data_end_utc")
        elif source_end is None:
            raise ValueError("source price status requires source_data_end_utc")
        object.__setattr__(self, "symbol", _text(self.symbol, "symbol").upper())
        object.__setattr__(self, "factor_name", _text(self.factor_name, "factor_name"))
        object.__setattr__(self, "factor_version", _text(self.factor_version, "factor_version"))
        object.__setattr__(self, "as_of_utc", as_of)
        object.__setattr__(self, "source_data_end_utc", source_end)
        object.__setattr__(self, "source_bar_timestamp_utc", source_bar)


@dataclass(frozen=True, slots=True)
class FactorVisualizationSeries:
    """Chronological, bounded visualization evidence for one exact query."""

    query: FactorVisualizationQuery
    points: tuple[FactorVisualizationPoint, ...]
    may_be_truncated: bool = False

    def __post_init__(self) -> None:
        prior_time: datetime | None = None
        for point in self.points:
            identity = (
                point.symbol,
                point.factor_name,
                point.factor_version,
                point.timeframe,
                point.adjustment,
                point.feed,
                point.price_field,
            )
            expected = (
                self.query.symbol,
                self.query.factor_name,
                self.query.factor_version,
                self.query.timeframe,
                self.query.adjustment,
                self.query.feed,
                self.query.price_field,
            )
            if identity != expected:
                raise ValueError("Factor visualization point does not match query identity")
            if not self.query.start_time_utc <= point.as_of_utc < self.query.end_time_utc:
                raise ValueError("Factor visualization point falls outside the query range")
            if prior_time is not None and point.as_of_utc < prior_time:
                raise ValueError("Factor visualization points must be chronological")
            prior_time = point.as_of_utc

    @property
    def count(self) -> int:
        return len(self.points)


@dataclass(frozen=True, slots=True)
class FactorVersionComparisonQuery:
    symbol: str
    factor_name: str
    factor_versions: tuple[str, ...]
    start_time_utc: datetime | None = None
    end_time_utc: datetime | None = None
    timeframe: Timeframe | None = None
    adjustment: Adjustment | None = None
    feed: DataFeed | None = None
    limit: int = 500

    def __post_init__(self) -> None:
        versions = tuple(_text(item, "factor_version") for item in self.factor_versions)
        if not 2 <= len(versions) <= 5 or len(set(versions)) != len(versions):
            raise ValueError("Factor comparison requires two to five unique exact versions")
        if not 1 <= self.limit <= 5000:
            raise ValueError("Factor comparison limit must be between 1 and 5000")
        start = _utc(self.start_time_utc, "start_time_utc")
        end = _utc(self.end_time_utc, "end_time_utc")
        if start is not None and end is not None and start >= end:
            raise ValueError("Factor comparison start must be before end")
        object.__setattr__(self, "symbol", _text(self.symbol, "symbol").upper())
        object.__setattr__(self, "factor_name", _text(self.factor_name, "factor_name"))
        object.__setattr__(self, "factor_versions", versions)
        object.__setattr__(self, "start_time_utc", start)
        object.__setattr__(self, "end_time_utc", end)


@dataclass(frozen=True, slots=True)
class FactorVersionValue:
    factor_version: str
    value: FactorValue | None
    unit: str | None
    status: FactorStatus | None
    calculation_id: UUID | None
    algorithm_run_id: UUID | None

    def __post_init__(self) -> None:
        object.__setattr__(self, "factor_version", _text(self.factor_version, "factor_version"))
        if isinstance(self.value, float):
            raise ValueError("Factor comparison values must not use binary float")


@dataclass(frozen=True, slots=True)
class FactorVersionComparison:
    symbol: str
    factor_name: str
    as_of_utc: datetime
    timeframe: Timeframe
    adjustment: Adjustment
    feed: DataFeed
    values: tuple[FactorVersionValue, ...]

    def __post_init__(self) -> None:
        versions = tuple(item.factor_version for item in self.values)
        if len(versions) < 2 or len(versions) != len(set(versions)):
            raise ValueError("Factor comparison values require unique versions")
        object.__setattr__(self, "symbol", _text(self.symbol, "symbol").upper())
        object.__setattr__(self, "factor_name", _text(self.factor_name, "factor_name"))
        object.__setattr__(self, "as_of_utc", _utc(self.as_of_utc, "as_of_utc"))


__all__ = [
    "FactorHistoryQuery",
    "FactorHistoryRecord",
    "FactorSourcePriceStatus",
    "FactorVisualizationPoint",
    "FactorVisualizationQuery",
    "FactorVisualizationSeries",
    "FactorVersionComparison",
    "FactorVersionComparisonQuery",
    "FactorVersionValue",
]
