from dataclasses import replace
from datetime import UTC, date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from quant_trading.backtesting.models import (
    BacktestRequest,
    BacktestResult,
    BacktestStatus,
    DecisionJournalEntry,
    EquityPoint,
    FactorTrace,
    JournalAction,
    JournalOutcome,
    SimulatedSide,
    SimulatedTrade,
)
from quant_trading.backtesting.repository import JsonBacktestResultRepository


def _request(run_id: UUID | None = None) -> BacktestRequest:
    return BacktestRequest(
        run_id or uuid4(),
        date(2025, 1, 1),
        date(2025, 1, 31),
        Decimal("1000"),
    )


def _result(run_id: UUID | None = None) -> BacktestResult:
    request = _request(run_id)
    started = datetime(2025, 2, 1, tzinfo=UTC)
    point = EquityPoint(date(2025, 1, 31), Decimal("1000"), Decimal("0"), Decimal("1000"))
    return BacktestResult(
        request.run_id,
        "historical_simulation",
        "research.sma-cross",
        BacktestStatus.COMPLETED,
        started,
        started + timedelta(seconds=1),
        request,
        1,
        1,
        (),
        (),
        (point,),
        Decimal("1000"),
        Decimal("0"),
        Decimal("1000"),
        Decimal("0"),
        (),
    )


def _trade(**changes: object) -> SimulatedTrade:
    values = {
        "trade_id": uuid4(),
        "order_id": "SIM-001",
        "symbol": " aaa ",
        "signal_date": date(2025, 1, 2),
        "filled_at_utc": datetime(2025, 1, 3, 9, 30, tzinfo=timezone(timedelta(hours=-5))),
        "side": SimulatedSide.BUY,
        "quantity": Decimal("2"),
        "price": Decimal("10"),
        "gross_amount": Decimal("20"),
        "fee_amount": Decimal("0"),
        "cash_effect": Decimal("-20"),
        "operation": "next_bar_open_market_fill",
    }
    values.update(changes)
    return SimulatedTrade(**values)


def _journal(**changes: object) -> DecisionJournalEntry:
    values = {
        "journal_id": uuid4(),
        "run_id": uuid4(),
        "strategy_id": "research.sma-cross",
        "trading_date": date(2025, 1, 2),
        "symbol": "AAA",
        "as_of_utc": datetime(2025, 1, 2, tzinfo=UTC),
        "action": JournalAction.HOLD,
        "outcome": JournalOutcome.NO_TRADE,
        "reason": "NO_CROSSOVER",
        "market_open": Decimal("10"),
        "market_high": Decimal("12"),
        "market_low": Decimal("9"),
        "market_close": Decimal("11"),
        "market_volume": Decimal("100"),
    }
    values.update(changes)
    return DecisionJournalEntry(**values)


def test_request_normalizes_currency_and_rejects_non_finite_cash() -> None:
    request = BacktestRequest(
        uuid4(),
        date(2025, 1, 1),
        date(2025, 1, 2),
        Decimal("1000"),
        " usd ",
        2,
        3,
    )

    assert request.currency == "USD"
    with pytest.raises(ValueError, match="finite"):
        replace(request, initial_cash=Decimal("NaN"))


def test_simulated_trade_normalizes_identity_and_time() -> None:
    trade = _trade()

    assert trade.symbol == "AAA"
    assert trade.filled_at_utc.tzinfo is UTC
    assert trade.filled_at_utc.hour == 14


@pytest.mark.parametrize(
    "changes, message",
    (
        ({"gross_amount": Decimal("19")}, "gross"),
        ({"cash_effect": Decimal("20")}, "cash_effect"),
        ({"quantity": Decimal("NaN")}, "finite"),
        ({"filled_at_utc": datetime(2025, 1, 3, 9, 30)}, "timezone"),
    ),
)
def test_simulated_trade_rejects_invalid_financial_contract(changes: dict[str, object], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        _trade(**changes)


def test_equity_point_rejects_inconsistent_total() -> None:
    with pytest.raises(ValueError, match="cash plus market_value"):
        EquityPoint(date(2025, 1, 2), Decimal("10"), Decimal("5"), Decimal("14"))


def test_journal_rejects_invalid_market_and_incomplete_fill_evidence() -> None:
    with pytest.raises(ValueError, match="OHLC"):
        _journal(market_high=Decimal("8"))

    with pytest.raises(ValueError, match="filled journal entry"):
        _journal(action=JournalAction.BUY, outcome=JournalOutcome.FILLED, trade_id=uuid4())


def test_factor_trace_requires_valid_timestamp_and_finite_value() -> None:
    with pytest.raises(ValueError, match="timezone"):
        FactorTrace("asset", "factor", "1", Decimal("1"), "valid", datetime(2025, 1, 1))

    with pytest.raises(ValueError, match="finite"):
        FactorTrace("asset", "factor", "1", Decimal("NaN"), "valid", datetime(2025, 1, 1, tzinfo=UTC))


def test_backtest_result_rejects_cross_field_inconsistency() -> None:
    result = _result()

    with pytest.raises(ValueError, match="request.run_id"):
        replace(result, run_id=uuid4())
    with pytest.raises(ValueError, match="completed_at_utc"):
        replace(result, completed_at_utc=result.started_at_utc - timedelta(seconds=1))
    with pytest.raises(ValueError, match="ending_equity"):
        replace(result, ending_equity=Decimal("999"))
    with pytest.raises(ValueError, match="journal run_id"):
        replace(result, decision_journal=(_journal(),))


def test_repository_rejects_overwrite_and_wrong_file_identity(tmp_path: Path) -> None:
    repository = JsonBacktestResultRepository(tmp_path)
    result = _result()
    repository.save(result)

    with pytest.raises(FileExistsError, match="already exists"):
        repository.save(result)

    requested_id = uuid4()
    (tmp_path / f"{result.run_id}.json").replace(tmp_path / f"{requested_id}.json")
    with pytest.raises(ValueError, match="does not match requested run_id"):
        repository.get(requested_id)
