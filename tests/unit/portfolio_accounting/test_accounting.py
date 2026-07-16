from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from quant_trading.portfolio_accounting.accounting.service import InMemoryPortfolioAccountingService
from quant_trading.portfolio_accounting.ledger.models import CashMovement, CashMovementType, OrderEventType, OrderLifecycleEvent, TradeFill, TradeSide


NOW = datetime(2026, 7, 15, 18, 0, tzinfo=UTC)


def fill(side: TradeSide, quantity: str, price: str, fee: str, execution_id: str) -> TradeFill:
    q, p, f = Decimal(quantity), Decimal(price), Decimal(fee)
    gross = q * p
    effect = -gross - f if side is TradeSide.BUY else gross - f
    return TradeFill(uuid4(), NOW, NOW, "AAPL", "order-1", execution_id, side, q, p, gross, f, effect, "USD", "fake", "alpaca_paper")


def rebuild(entries):
    return InMemoryPortfolioAccountingService().rebuild(tuple(entries), starting_cash=Decimal("1000"), currency="USD", as_of_utc=NOW)


def test_filled_buy_reduces_cash_and_increases_position():
    result = rebuild((fill(TradeSide.BUY, "2", "100", "1", "buy-1"),))
    assert result.account.cash == Decimal("799")
    assert result.positions[0].quantity == Decimal("2")
    assert result.positions[0].average_cost is None


def test_filled_sell_increases_cash_and_reduces_position():
    result = rebuild((fill(TradeSide.BUY, "3", "100", "0", "buy-1"), fill(TradeSide.SELL, "1", "120", "1", "sell-1")))
    assert result.account.cash == Decimal("819")
    assert result.positions[0].quantity == Decimal("2")


def test_fee_and_deposit_change_cash():
    deposit = CashMovement(uuid4(), CashMovementType.DEPOSIT, NOW, NOW, Decimal("50"), "USD", "fake", "alpaca_paper")
    fee = CashMovement(uuid4(), CashMovementType.FEE, NOW, NOW, Decimal("-2"), "USD", "fake", "alpaca_paper")
    assert rebuild((deposit, fee)).account.cash == Decimal("1048")


def test_unfilled_or_rejected_order_does_not_change_financial_state():
    events = (
        OrderLifecycleEvent(uuid4(), OrderEventType.ORDER_SUBMITTED, NOW, NOW, "o1", "fake", "alpaca_paper"),
        OrderLifecycleEvent(uuid4(), OrderEventType.ORDER_REJECTED, NOW, NOW, "o1", "fake", "alpaca_paper"),
    )
    result = rebuild(events)
    assert result.account.cash == Decimal("1000") and result.positions == ()


def test_same_events_rebuild_same_state_without_mutating_ledger_records():
    entries = (fill(TradeSide.BUY, "2", "100", "1", "buy-1"),)
    before = repr(entries)
    first, second = rebuild(entries), rebuild(entries)
    assert first == second
    assert repr(entries) == before


def test_unapproved_short_position_fails_closed():
    with pytest.raises(ValueError, match="open decision"):
        rebuild((fill(TradeSide.SELL, "1", "100", "0", "sell-short"),))


def test_unapproved_multi_currency_fails_closed():
    movement = CashMovement(uuid4(), CashMovementType.DEPOSIT, NOW, NOW, Decimal("10"), "EUR", "fake", "alpaca_paper")
    with pytest.raises(ValueError, match="multi-currency"):
        rebuild((movement,))
