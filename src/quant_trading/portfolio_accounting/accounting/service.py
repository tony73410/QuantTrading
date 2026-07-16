"""Minimal replay service; advanced accounting conventions remain open decisions."""

from datetime import datetime
from decimal import Decimal
from uuid import uuid5, NAMESPACE_URL

from ..ledger.models import CashMovement, LedgerEntry, OrderLifecycleEvent, TradeFill, TradeSide
from ..models import AccountSnapshot, CalculationStatus, PortfolioSnapshot, PositionSnapshot


class InMemoryPortfolioAccountingService:
    def rebuild(self, entries: tuple[LedgerEntry, ...], *, starting_cash: Decimal, currency: str, as_of_utc: datetime) -> PortfolioSnapshot:
        if not isinstance(starting_cash, Decimal) or not starting_cash.is_finite():
            raise ValueError("starting_cash must be a finite Decimal")
        cash = starting_cash
        quantities: dict[str, Decimal] = {}
        for entry in entries:
            if isinstance(entry, OrderLifecycleEvent):
                continue
            if entry.occurred_at_utc > as_of_utc:
                continue
            if isinstance(entry, TradeFill):
                if entry.currency != currency.upper():
                    raise ValueError("multi-currency accounting is an open decision")
                cash += entry.net_cash_effect
                delta = entry.quantity if entry.side is TradeSide.BUY else -entry.quantity
                resulting_quantity = quantities.get(entry.symbol, Decimal("0")) + delta
                if resulting_quantity < 0:
                    raise ValueError("short-position accounting is an open decision")
                quantities[entry.symbol] = resulting_quantity
            elif isinstance(entry, CashMovement):
                if entry.currency != currency.upper():
                    raise ValueError("multi-currency accounting is an open decision")
                cash += entry.amount
        identity = uuid5(NAMESPACE_URL, f"quant-trading:portfolio:{currency.upper()}:{as_of_utc.isoformat()}:{len(entries)}:{cash}:{sorted(quantities.items())}")
        positions = tuple(PositionSnapshot(symbol, as_of_utc, quantity) for symbol, quantity in sorted(quantities.items()) if quantity != 0)
        status = CalculationStatus.PARTIAL if entries else CalculationStatus.EMPTY
        account = AccountSnapshot(identity, as_of_utc, currency, cash, None, None, None, None, None, None, None, len(entries), status)
        return PortfolioSnapshot(identity, as_of_utc, account, positions, status)
