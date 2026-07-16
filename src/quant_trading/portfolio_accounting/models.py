"""Immutable public read models for portfolio accounting."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must include a timezone")
    return value.astimezone(UTC)


def _decimal(value: Decimal | None, name: str) -> Decimal | None:
    if value is not None and (not isinstance(value, Decimal) or not value.is_finite()):
        raise ValueError(f"{name} must be a finite Decimal or None")
    return value


class CalculationStatus(StrEnum):
    EMPTY = "empty"
    PARTIAL = "partial"
    CALCULATED = "calculated"
    NOT_CALCULATED = "not_calculated"
    ERROR = "error"


class PriceStatus(StrEnum):
    NOT_AVAILABLE = "not_available"
    AVAILABLE = "available"
    STALE = "stale"


@dataclass(frozen=True, slots=True)
class PositionSnapshot:
    symbol: str
    as_of_utc: datetime
    quantity: Decimal
    average_cost: Decimal | None = None
    cost_basis: Decimal | None = None
    market_price: Decimal | None = None
    market_value: Decimal | None = None
    realized_pnl: Decimal | None = None
    unrealized_pnl: Decimal | None = None
    daily_pnl: Decimal | None = None
    price_timestamp_utc: datetime | None = None
    price_status: PriceStatus = PriceStatus.NOT_AVAILABLE

    def __post_init__(self) -> None:
        symbol = self.symbol.strip().upper()
        if not symbol:
            raise ValueError("symbol must not be empty")
        object.__setattr__(self, "symbol", symbol)
        object.__setattr__(self, "as_of_utc", _utc(self.as_of_utc))
        for name in ("quantity", "average_cost", "cost_basis", "market_price", "market_value", "realized_pnl", "unrealized_pnl", "daily_pnl"):
            _decimal(getattr(self, name), name)
        if self.price_timestamp_utc is not None:
            object.__setattr__(self, "price_timestamp_utc", _utc(self.price_timestamp_utc))


@dataclass(frozen=True, slots=True)
class AccountSnapshot:
    snapshot_id: UUID
    as_of_utc: datetime
    currency: str
    cash: Decimal
    settled_cash: Decimal | None
    unsettled_cash: Decimal | None
    equity: Decimal | None
    market_value: Decimal | None
    realized_pnl: Decimal | None
    unrealized_pnl: Decimal | None
    daily_pnl: Decimal | None
    source_ledger_sequence: int
    calculation_status: CalculationStatus

    def __post_init__(self) -> None:
        object.__setattr__(self, "as_of_utc", _utc(self.as_of_utc))
        currency = self.currency.strip().upper()
        if not currency:
            raise ValueError("currency must not be empty")
        object.__setattr__(self, "currency", currency)
        for name in ("cash", "settled_cash", "unsettled_cash", "equity", "market_value", "realized_pnl", "unrealized_pnl", "daily_pnl"):
            _decimal(getattr(self, name), name)
        if self.source_ledger_sequence < 0:
            raise ValueError("source_ledger_sequence must be non-negative")


@dataclass(frozen=True, slots=True)
class PortfolioSnapshot:
    snapshot_id: UUID
    as_of_utc: datetime
    account: AccountSnapshot
    positions: tuple[PositionSnapshot, ...]
    calculation_status: CalculationStatus

    def __post_init__(self) -> None:
        object.__setattr__(self, "as_of_utc", _utc(self.as_of_utc))
        if self.account.snapshot_id != self.snapshot_id or self.account.as_of_utc != self.as_of_utc:
            raise ValueError("portfolio and account snapshot identity/as-of must match")
        symbols = tuple(item.symbol for item in self.positions)
        if len(symbols) != len(set(symbols)):
            raise ValueError("portfolio positions must have unique symbols")


@dataclass(frozen=True, slots=True)
class DailyPnLSnapshot:
    trading_date: date
    starting_equity: Decimal | None
    ending_equity: Decimal | None
    net_deposits: Decimal
    net_withdrawals: Decimal
    realized_pnl: Decimal | None
    unrealized_pnl_change: Decimal | None
    dividends: Decimal
    fees: Decimal
    total_pnl: Decimal | None
    calculation_status: CalculationStatus

    def __post_init__(self) -> None:
        for name in ("starting_equity", "ending_equity", "net_deposits", "net_withdrawals", "realized_pnl", "unrealized_pnl_change", "dividends", "fees", "total_pnl"):
            _decimal(getattr(self, name), name)
