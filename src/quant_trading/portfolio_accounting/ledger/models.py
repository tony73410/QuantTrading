"""Typed ledger facts; operational events are distinct from financial facts."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from types import MappingProxyType
from typing import Mapping, TypeAlias
from uuid import UUID


def _utc(value: datetime, name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must include a timezone")
    return value.astimezone(UTC)


def _text(value: str, name: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError(f"{name} must not be empty")
    return value


def _amount(value: Decimal, name: str, *, positive: bool = False) -> Decimal:
    if not isinstance(value, Decimal) or not value.is_finite():
        raise ValueError(f"{name} must be a finite Decimal")
    if positive and value <= 0:
        raise ValueError(f"{name} must be positive")
    return value


class OrderEventType(StrEnum):
    ORDER_CREATED = "order_created"
    ORDER_SUBMITTED = "order_submitted"
    ORDER_ACCEPTED = "order_accepted"
    ORDER_PARTIALLY_FILLED = "order_partially_filled"
    ORDER_FILLED = "order_filled"
    ORDER_CANCEL_REQUESTED = "order_cancel_requested"
    ORDER_CANCELLED = "order_cancelled"
    ORDER_REJECTED = "order_rejected"
    ORDER_EXPIRED = "order_expired"


class CashMovementType(StrEnum):
    COMMISSION = "commission"
    FEE = "fee"
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    DIVIDEND = "dividend"
    INTEREST = "interest"
    ADJUSTMENT = "adjustment"
    CORRECTION = "correction"
    REVERSAL = "reversal"


class TradeSide(StrEnum):
    BUY = "buy"
    SELL = "sell"


class EntryStatus(StrEnum):
    RECORDED = "recorded"
    CORRECTED = "corrected"
    REVERSED = "reversed"


@dataclass(frozen=True, slots=True)
class OrderLifecycleEvent:
    entry_id: UUID
    event_type: OrderEventType
    occurred_at_utc: datetime
    recorded_at_utc: datetime
    order_id: str
    source: str
    environment: str
    broker_order_id: str | None = None
    broker_event_id: str | None = None
    correlation_id: str | None = None
    status: EntryStatus = EntryStatus.RECORDED

    def __post_init__(self) -> None:
        object.__setattr__(self, "occurred_at_utc", _utc(self.occurred_at_utc, "occurred_at_utc"))
        object.__setattr__(self, "recorded_at_utc", _utc(self.recorded_at_utc, "recorded_at_utc"))
        for name in ("order_id", "source", "environment"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        if not isinstance(self.event_type, OrderEventType):
            raise ValueError("event_type must use OrderEventType")

    @property
    def idempotency_key(self) -> str | None:
        return f"{self.source}:order-event:{self.broker_event_id}" if self.broker_event_id else None


@dataclass(frozen=True, slots=True)
class TradeFill:
    entry_id: UUID
    occurred_at_utc: datetime
    recorded_at_utc: datetime
    symbol: str
    order_id: str
    execution_id: str
    side: TradeSide
    quantity: Decimal
    price: Decimal
    gross_amount: Decimal
    fee_amount: Decimal
    net_cash_effect: Decimal
    currency: str
    source: str
    environment: str
    broker_order_id: str | None = None
    broker_event_id: str | None = None
    correlation_id: str | None = None
    status: EntryStatus = EntryStatus.RECORDED
    metadata: Mapping[str, str] = field(default_factory=dict, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "occurred_at_utc", _utc(self.occurred_at_utc, "occurred_at_utc"))
        object.__setattr__(self, "recorded_at_utc", _utc(self.recorded_at_utc, "recorded_at_utc"))
        for name in ("symbol", "currency"):
            object.__setattr__(self, name, _text(getattr(self, name), name).upper())
        for name in ("order_id", "execution_id", "source", "environment"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        if not isinstance(self.side, TradeSide):
            raise ValueError("side must use TradeSide")
        _amount(self.quantity, "quantity", positive=True)
        _amount(self.price, "price", positive=True)
        _amount(self.gross_amount, "gross_amount")
        _amount(self.fee_amount, "fee_amount")
        _amount(self.net_cash_effect, "net_cash_effect")
        if self.gross_amount != self.quantity * self.price or self.fee_amount < 0:
            raise ValueError("fill gross amount/fee is inconsistent")
        expected = -self.gross_amount - self.fee_amount if self.side is TradeSide.BUY else self.gross_amount - self.fee_amount
        if self.net_cash_effect != expected:
            raise ValueError("fill net_cash_effect violates the buy/sell sign convention")
        if any(not isinstance(key, str) or not isinstance(value, str) for key, value in self.metadata.items()):
            raise ValueError("metadata must contain only string keys and values")
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    @property
    def idempotency_key(self) -> str:
        external = self.broker_event_id or self.execution_id
        return f"{self.source}:trade-fill:{external}"


@dataclass(frozen=True, slots=True)
class CashMovement:
    entry_id: UUID
    event_type: CashMovementType
    occurred_at_utc: datetime
    recorded_at_utc: datetime
    amount: Decimal
    currency: str
    source: str
    environment: str
    external_event_id: str | None = None
    correlation_id: str | None = None
    corrects_entry_id: UUID | None = None
    reason: str | None = None
    status: EntryStatus = EntryStatus.RECORDED

    def __post_init__(self) -> None:
        object.__setattr__(self, "occurred_at_utc", _utc(self.occurred_at_utc, "occurred_at_utc"))
        object.__setattr__(self, "recorded_at_utc", _utc(self.recorded_at_utc, "recorded_at_utc"))
        _amount(self.amount, "amount")
        object.__setattr__(self, "currency", _text(self.currency, "currency").upper())
        for name in ("source", "environment"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        if not isinstance(self.event_type, CashMovementType):
            raise ValueError("event_type must use CashMovementType")
        if self.event_type in (CashMovementType.COMMISSION, CashMovementType.FEE, CashMovementType.WITHDRAWAL) and self.amount > 0:
            raise ValueError("fees and withdrawals must use a non-positive cash effect")
        if self.event_type in (CashMovementType.DEPOSIT, CashMovementType.DIVIDEND, CashMovementType.INTEREST) and self.amount < 0:
            raise ValueError("deposits, dividends, and interest must use a non-negative cash effect")
        if self.event_type in (CashMovementType.CORRECTION, CashMovementType.REVERSAL):
            if self.corrects_entry_id is None or self.reason is None or not self.reason.strip():
                raise ValueError("correction/reversal requires target entry and reason")

    @property
    def idempotency_key(self) -> str | None:
        return f"{self.source}:cash:{self.external_event_id}" if self.external_event_id else None


LedgerEntry: TypeAlias = OrderLifecycleEvent | TradeFill | CashMovement
