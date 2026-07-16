from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from quant_trading.portfolio_accounting.ledger.in_memory_repository import InMemoryLedgerRepository
from quant_trading.portfolio_accounting.ledger.interfaces import DuplicateLedgerEventError
from quant_trading.portfolio_accounting.ledger.models import (
    CashMovement, CashMovementType, OrderEventType, OrderLifecycleEvent, TradeFill, TradeSide,
)


NOW = datetime(2026, 7, 15, 18, 0, tzinfo=UTC)


def fill(*, entry_id=None, broker_event_id="evt-1", execution_id="exec-1", side=TradeSide.BUY, quantity=Decimal("2"), price=Decimal("10"), fee=Decimal("1")):
    gross = quantity * price
    cash = -gross - fee if side is TradeSide.BUY else gross - fee
    return TradeFill(entry_id or uuid4(), NOW, NOW, "AAPL", "order-1", execution_id, side, quantity, price, gross, fee, cash, "USD", "fake-broker", "alpaca_paper", broker_event_id=broker_event_id)


def test_trade_fill_can_be_appended_and_uses_decimal():
    repository = InMemoryLedgerRepository()
    item = fill()
    assert repository.append(item) == 1
    assert repository.entries() == (item,)
    assert isinstance(item.quantity, Decimal) and isinstance(item.price, Decimal)


def test_duplicate_broker_event_is_rejected_idempotently():
    repository = InMemoryLedgerRepository()
    repository.append(fill())
    with pytest.raises(DuplicateLedgerEventError):
        repository.append(fill(entry_id=uuid4(), execution_id="exec-other"))


def test_existing_entry_cannot_be_overwritten():
    repository = InMemoryLedgerRepository()
    entry_id = uuid4()
    original = fill(entry_id=entry_id)
    repository.append(original)
    with pytest.raises(DuplicateLedgerEventError):
        repository.append(fill(entry_id=entry_id, broker_event_id="evt-2"))
    assert repository.get(entry_id) is original


def test_correction_is_a_new_entry_and_preserves_original():
    repository = InMemoryLedgerRepository()
    original = fill()
    repository.append(original)
    correction = CashMovement(uuid4(), CashMovementType.CORRECTION, NOW, NOW, Decimal("1"), "USD", "manual-review", "alpaca_paper", corrects_entry_id=original.entry_id, reason="Correct documented fee")
    repository.append(correction)
    assert repository.entries() == (original, correction)


def test_float_money_or_quantity_is_rejected():
    with pytest.raises(ValueError, match="Decimal"):
        TradeFill(uuid4(), NOW, NOW, "AAPL", "order-1", "exec-float", TradeSide.BUY, 2.0, Decimal("10"), Decimal("20"), Decimal("0"), Decimal("-20"), "USD", "fake", "alpaca_paper")  # type: ignore[arg-type]


def order_event(event_type: OrderEventType) -> OrderLifecycleEvent:
    return OrderLifecycleEvent(uuid4(), event_type, NOW, NOW, "order-1", "fake-broker", "alpaca_paper", broker_event_id=f"event-{event_type.value}")
