"""Immutable public contracts for research-only historical simulation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID


def _utc(value: datetime, field_name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must include a timezone")
    return value.astimezone(UTC)


def _text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    return value.strip()


def _decimal(
    value: Decimal,
    field_name: str,
    *,
    positive: bool = False,
    nonnegative: bool = False,
) -> Decimal:
    if not isinstance(value, Decimal) or not value.is_finite():
        raise ValueError(f"{field_name} must be a finite Decimal")
    if positive and value <= 0:
        raise ValueError(f"{field_name} must be positive")
    if nonnegative and value < 0:
        raise ValueError(f"{field_name} must not be negative")
    return value


class BacktestStatus(StrEnum):
    COMPLETED = "completed"
    PARTIAL = "partial"
    BLOCKED = "blocked"


class SimulatedSide(StrEnum):
    BUY = "buy"
    SELL = "sell"


class JournalAction(StrEnum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    NO_DECISION = "no_decision"
    BLOCKED = "blocked"


class JournalOutcome(StrEnum):
    FILLED = "filled"
    NO_TRADE = "no_trade"
    BLOCKED = "blocked"
    PENDING_NEXT_BAR = "pending_next_bar"


@dataclass(frozen=True, slots=True)
class FactorTrace:
    scope: str
    factor_id: str
    factor_version: str
    value: Decimal | int | bool | str | None
    status: str
    as_of_utc: datetime
    lookback: int | None = None
    source_symbols: tuple[str, ...] = ()
    detail: str = ""

    def __post_init__(self) -> None:
        for field_name in ("scope", "factor_id", "factor_version", "status"):
            object.__setattr__(self, field_name, _text(getattr(self, field_name), field_name))
        object.__setattr__(self, "as_of_utc", _utc(self.as_of_utc, "factor trace as_of_utc"))
        if isinstance(self.value, Decimal):
            _decimal(self.value, "factor trace value")
        if self.lookback is not None and self.lookback <= 0:
            raise ValueError("factor trace lookback must be positive")
        symbols = tuple(_text(symbol, "source symbol").upper() for symbol in self.source_symbols)
        if len(symbols) != len(set(symbols)):
            raise ValueError("factor trace source symbols must be unique")
        object.__setattr__(self, "source_symbols", symbols)


@dataclass(frozen=True, slots=True)
class ConditionTrace:
    factor_id: str
    factor_version: str
    actual_value: Decimal | None
    operator: str
    threshold: Decimal
    matched: bool

    def __post_init__(self) -> None:
        for field_name in ("factor_id", "factor_version", "operator"):
            object.__setattr__(self, field_name, _text(getattr(self, field_name), field_name))
        if self.actual_value is not None:
            _decimal(self.actual_value, "condition actual_value")
        _decimal(self.threshold, "condition threshold")
        if not isinstance(self.matched, bool):
            raise ValueError("condition matched must be bool")


@dataclass(frozen=True, slots=True)
class DecisionJournalEntry:
    journal_id: UUID
    run_id: UUID
    strategy_id: str
    trading_date: date
    symbol: str
    as_of_utc: datetime
    action: JournalAction
    outcome: JournalOutcome
    reason: str
    market_open: Decimal
    market_high: Decimal
    market_low: Decimal
    market_close: Decimal
    market_volume: Decimal
    factor_traces: tuple[FactorTrace, ...] = ()
    condition_traces: tuple[ConditionTrace, ...] = ()
    sizing_mode: str = "none"
    sizing_expression: str | None = None
    sizing_references: tuple[tuple[str, Decimal], ...] = ()
    requested_notional: Decimal | None = None
    approved_notional: Decimal | None = None
    quantity: Decimal | None = None
    fill_price: Decimal | None = None
    cash_before: Decimal | None = None
    cash_after: Decimal | None = None
    position_before: Decimal | None = None
    position_after: Decimal | None = None
    trade_id: UUID | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "strategy_id", _text(self.strategy_id, "strategy_id"))
        object.__setattr__(self, "symbol", _text(self.symbol, "symbol").upper())
        object.__setattr__(self, "reason", _text(self.reason, "reason"))
        object.__setattr__(self, "as_of_utc", _utc(self.as_of_utc, "journal as_of_utc"))
        if not isinstance(self.action, JournalAction):
            raise ValueError("journal action must use JournalAction")
        if not isinstance(self.outcome, JournalOutcome):
            raise ValueError("journal outcome must use JournalOutcome")
        prices = (self.market_open, self.market_high, self.market_low, self.market_close)
        for field_name, value in zip(
            ("market_open", "market_high", "market_low", "market_close"), prices
        ):
            _decimal(value, field_name)
        if (
            self.market_high < self.market_low
            or not self.market_low <= self.market_open <= self.market_high
            or not self.market_low <= self.market_close <= self.market_high
        ):
            raise ValueError("journal market OHLC values are inconsistent")
        _decimal(self.market_volume, "market_volume", nonnegative=True)
        if self.sizing_expression is not None:
            object.__setattr__(
                self,
                "sizing_expression",
                _text(self.sizing_expression, "sizing_expression"),
            )
        references = tuple(
            (_text(name, "sizing reference name"), _decimal(value, "sizing reference value"))
            for name, value in self.sizing_references
        )
        if len(references) != len({name for name, _ in references}):
            raise ValueError("sizing reference names must be unique")
        object.__setattr__(self, "sizing_references", references)

        for field_name in ("requested_notional", "approved_notional", "quantity", "fill_price"):
            value = getattr(self, field_name)
            if value is not None:
                _decimal(value, field_name, positive=True)
        for field_name in ("cash_before", "cash_after"):
            value = getattr(self, field_name)
            if value is not None:
                _decimal(value, field_name)
        for field_name in ("position_before", "position_after"):
            value = getattr(self, field_name)
            if value is not None:
                _decimal(value, field_name, nonnegative=True)

        financial_fields = (
            self.requested_notional,
            self.approved_notional,
            self.quantity,
            self.fill_price,
            self.cash_before,
            self.cash_after,
            self.position_before,
            self.position_after,
        )
        if self.outcome is JournalOutcome.FILLED:
            if self.action not in (JournalAction.BUY, JournalAction.SELL):
                raise ValueError("filled journal entry requires a buy or sell action")
            if self.trade_id is None or any(value is None for value in financial_fields):
                raise ValueError("filled journal entry requires complete financial evidence")
            if self.approved_notional != self.quantity * self.fill_price:
                raise ValueError("filled journal approved_notional is inconsistent")
        elif self.trade_id is not None:
            raise ValueError("non-filled journal entry cannot reference a trade")


@dataclass(frozen=True, slots=True)
class BacktestRequest:
    run_id: UUID
    start_date: date
    end_date: date
    initial_cash: Decimal = Decimal("1000000")
    currency: str = "USD"
    short_window: int = 20
    long_window: int = 50

    def __post_init__(self) -> None:
        if self.start_date >= self.end_date:
            raise ValueError("start_date must be before end_date")
        _decimal(self.initial_cash, "initial_cash", positive=True)
        object.__setattr__(self, "currency", _text(self.currency, "currency").upper())
        if self.short_window < 2 or self.long_window <= self.short_window:
            raise ValueError("SMA windows must satisfy 2 <= short < long")


@dataclass(frozen=True, slots=True)
class SimulatedTrade:
    trade_id: UUID
    order_id: str
    symbol: str
    signal_date: date
    filled_at_utc: datetime
    side: SimulatedSide
    quantity: Decimal
    price: Decimal
    gross_amount: Decimal
    fee_amount: Decimal
    cash_effect: Decimal
    operation: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "order_id", _text(self.order_id, "order_id"))
        object.__setattr__(self, "symbol", _text(self.symbol, "symbol").upper())
        object.__setattr__(self, "operation", _text(self.operation, "operation"))
        object.__setattr__(self, "filled_at_utc", _utc(self.filled_at_utc, "filled_at_utc"))
        if not isinstance(self.side, SimulatedSide):
            raise ValueError("side must use SimulatedSide")
        _decimal(self.quantity, "quantity", positive=True)
        _decimal(self.price, "price", positive=True)
        _decimal(self.gross_amount, "gross_amount", positive=True)
        _decimal(self.fee_amount, "fee_amount", nonnegative=True)
        _decimal(self.cash_effect, "cash_effect")
        if self.gross_amount != self.quantity * self.price:
            raise ValueError("gross_amount must equal quantity multiplied by price")
        expected_cash_effect = (
            -self.gross_amount - self.fee_amount
            if self.side is SimulatedSide.BUY
            else self.gross_amount - self.fee_amount
        )
        if self.cash_effect != expected_cash_effect:
            raise ValueError("cash_effect violates the simulated buy/sell sign convention")


@dataclass(frozen=True, slots=True)
class EquityPoint:
    trading_date: date
    cash: Decimal
    market_value: Decimal
    total_equity: Decimal

    def __post_init__(self) -> None:
        _decimal(self.cash, "cash")
        _decimal(self.market_value, "market_value", nonnegative=True)
        _decimal(self.total_equity, "total_equity")
        if self.total_equity != self.cash + self.market_value:
            raise ValueError("total_equity must equal cash plus market_value")


@dataclass(frozen=True, slots=True)
class BacktestResult:
    run_id: UUID
    environment: str
    strategy_id: str
    status: BacktestStatus
    started_at_utc: datetime
    completed_at_utc: datetime
    request: BacktestRequest
    symbols_requested: int
    symbols_tested: int
    symbols_skipped: tuple[str, ...]
    trades: tuple[SimulatedTrade, ...]
    equity_curve: tuple[EquityPoint, ...]
    ending_cash: Decimal
    ending_market_value: Decimal
    ending_equity: Decimal
    total_return: Decimal
    warnings: tuple[str, ...]
    decision_journal: tuple[DecisionJournalEntry, ...] = ()

    def __post_init__(self) -> None:
        for name in ("started_at_utc", "completed_at_utc"):
            object.__setattr__(self, name, _utc(getattr(self, name), name))
        if self.completed_at_utc < self.started_at_utc:
            raise ValueError("completed_at_utc must not precede started_at_utc")
        if self.run_id != self.request.run_id:
            raise ValueError("result run_id must equal request.run_id")
        object.__setattr__(self, "environment", _text(self.environment, "environment"))
        object.__setattr__(self, "strategy_id", _text(self.strategy_id, "strategy_id"))
        if not isinstance(self.status, BacktestStatus):
            raise ValueError("status must use BacktestStatus")
        if (
            not isinstance(self.symbols_requested, int)
            or not isinstance(self.symbols_tested, int)
            or self.symbols_requested < 0
            or self.symbols_tested < 0
            or self.symbols_tested > self.symbols_requested
        ):
            raise ValueError("symbol counts must satisfy 0 <= tested <= requested")
        for field_name in ("ending_cash", "ending_market_value", "ending_equity", "total_return"):
            _decimal(getattr(self, field_name), field_name)
        if self.ending_market_value < 0:
            raise ValueError("ending_market_value must not be negative")
        if self.ending_equity != self.ending_cash + self.ending_market_value:
            raise ValueError("ending_equity must equal ending_cash plus ending_market_value")
        expected_return = self.ending_equity / self.request.initial_cash - Decimal("1")
        if self.total_return != expected_return:
            raise ValueError("total_return is inconsistent with initial and ending equity")

        curve_dates = tuple(point.trading_date for point in self.equity_curve)
        if curve_dates != tuple(sorted(set(curve_dates))):
            raise ValueError("equity_curve trading dates must be unique and ordered")
        if any(not self.request.start_date <= day <= self.request.end_date for day in curve_dates):
            raise ValueError("equity_curve contains a date outside the request")
        if self.equity_curve:
            last = self.equity_curve[-1]
            if (
                last.cash != self.ending_cash
                or last.market_value != self.ending_market_value
                or last.total_equity != self.ending_equity
            ):
                raise ValueError("ending totals must match the last equity point")

        trade_ids = tuple(trade.trade_id for trade in self.trades)
        order_ids = tuple(trade.order_id for trade in self.trades)
        if len(trade_ids) != len(set(trade_ids)) or len(order_ids) != len(set(order_ids)):
            raise ValueError("trade_id and order_id must be unique within a run")
        journal_ids = tuple(entry.journal_id for entry in self.decision_journal)
        journal_keys = tuple((entry.trading_date, entry.symbol) for entry in self.decision_journal)
        if len(journal_ids) != len(set(journal_ids)) or len(journal_keys) != len(set(journal_keys)):
            raise ValueError("journal identity and daily symbol keys must be unique within a run")
        known_trades = {trade.trade_id: trade for trade in self.trades}
        for entry in self.decision_journal:
            if entry.run_id != self.run_id:
                raise ValueError("journal run_id must equal result run_id")
            if entry.strategy_id != self.strategy_id:
                raise ValueError("journal strategy_id must equal result strategy_id")
            if entry.trade_id is not None and entry.trade_id not in known_trades:
                raise ValueError("journal trade_id must reference a trade in the result")
