"""Approved research baseline: long-only SMA20/50 with next-bar-open fills."""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime, time, timedelta
from decimal import Decimal
from uuid import uuid4

from quant_trading.market_history.models import Adjustment, DataFeed, HistoricalDataRequest, Timeframe, validate_market_bars
from quant_trading.market_history.errors import DataValidationError
from .interfaces import BacktestResultRepository, HistoricalBarSource
from .models import BacktestRequest, BacktestResult, BacktestStatus, DecisionJournalEntry, JournalAction, JournalOutcome, EquityPoint, SimulatedSide, SimulatedTrade
from .strategies import HistoricalSignalProvider, ResearchSmaCrossSignalProvider, SignalAction
from quant_trading.decision.models import SizingContext,SizingReference
from quant_trading.decision.sizing import evaluate_sizing


class HistoricalBacktestService:
    ENVIRONMENT = "historical_simulation"
    def __init__(
        self,
        market_store: HistoricalBarSource,
        result_repository: BacktestResultRepository | None = None,
        signal_provider: HistoricalSignalProvider | None = None,
    ) -> None:
        self._market_store = market_store
        self._results = result_repository
        self._signals = signal_provider or ResearchSmaCrossSignalProvider()

    def with_signal_provider(self, signal_provider: HistoricalSignalProvider) -> "HistoricalBacktestService":
        return HistoricalBacktestService(self._market_store, self._results, signal_provider)

    def run(self, request: BacktestRequest) -> BacktestResult:
        started = datetime.now(UTC)
        symbols = self._market_store.list_symbols()
        bars_by_symbol = {}
        skipped = []
        required_observations = max(request.long_window, int(getattr(self._signals, "required_observations", request.long_window)))
        start = datetime.combine(request.start_date, time.min, UTC) - timedelta(days=required_observations * 3)
        end = datetime.combine(request.end_date + timedelta(days=1), time.min, UTC)
        for symbol in symbols:
            market_request = HistoricalDataRequest(symbol, start, end, Timeframe.DAY, Adjustment.RAW, DataFeed.IEX)
            bars = tuple(self._market_store.query_bars(market_request))
            try:
                validate_market_bars(bars, market_request)
            except DataValidationError:
                skipped.append(f"{symbol}: invalid market data")
                continue
            if len(bars) <= required_observations:
                skipped.append(f"{symbol}: insufficient observations")
                continue
            bars_by_symbol[symbol] = bars

        signals = defaultdict(list)
        evaluations = defaultdict(list)
        bars_by_date = defaultdict(dict)
        prepare=getattr(self._signals,"prepare",None)
        if callable(prepare): prepare(bars_by_symbol)
        for symbol, bars in bars_by_symbol.items():
            for index, bar in enumerate(bars):
                bars_by_date[bar.timestamp_utc.date()][symbol] = bar
            evaluator=getattr(self._signals,"evaluations",None)
            if callable(evaluator):
                symbol_evaluations=tuple(evaluator(bars,short_window=request.short_window,long_window=request.long_window,start_date=request.start_date,end_date=request.end_date))
                for evaluation in symbol_evaluations: evaluations[evaluation.signal_date].append((symbol,evaluation))
                symbol_signals=(x.signal for x in symbol_evaluations if x.signal is not None)
            else: symbol_signals=self._signals.signals(bars, short_window=request.short_window, long_window=request.long_window, start_date=request.start_date, end_date=request.end_date)
            for signal in symbol_signals:
                signals[signal.fill_bar.timestamp_utc.date()].append((signal.action, symbol, signal.signal_date, signal.fill_bar,signal))

        cash = request.initial_cash
        positions: dict[str, Decimal] = {}
        trades = []
        curve = []
        journal_by_key={}
        last_prices: dict[str, Decimal] = {}
        all_dates = sorted(d for d in bars_by_date if request.start_date <= d <= request.end_date)
        for trading_date in all_dates:
            for symbol, bar in bars_by_date[trading_date].items():
                last_prices[symbol] = bar.close
            for symbol,evaluation in evaluations.get(trading_date,()):
                action=JournalAction(evaluation.action.value) if evaluation.action else JournalAction.NO_DECISION
                journal_by_key[(trading_date,symbol)]=DecisionJournalEntry(uuid4(),request.run_id,self._signals.strategy_id,trading_date,symbol,evaluation.bar.timestamp_utc,action,JournalOutcome.PENDING_NEXT_BAR if evaluation.signal else JournalOutcome.NO_TRADE,evaluation.reason,evaluation.bar.open,evaluation.bar.high,evaluation.bar.low,evaluation.bar.close,Decimal(evaluation.bar.volume),evaluation.factor_traces,evaluation.condition_traces)
            day_signals = signals.get(trading_date, [])
            for _, symbol, signal_date, fill_bar, signal in (x for x in day_signals if x[0] is SignalAction.SELL):
                position_before = positions.get(symbol, Decimal("0"))
                if position_before > 0:
                    requested = position_before * fill_bar.open
                    fill_quantity = position_before
                    if signal.sizing is not None and signal.sizing.mode.value != "none":
                        equity=cash+sum((q*last_prices.get(s,Decimal("0")) for s,q in positions.items()),Decimal("0")); position_value=position_before*fill_bar.open
                        context=SizingContext(fill_bar.timestamp_utc,signal.asset_references,signal.market_references,(SizingReference("cash",cash),SizingReference("equity",equity)),(SizingReference("quantity",position_before),SizingReference("market_value",position_value)))
                        requested,_=evaluate_sizing(signal.sizing,context)
                        if requested is not None:
                            if requested>position_value: raise ValueError("sell sizing exceeds current position value")
                            fill_quantity=requested//fill_bar.open
                            if fill_quantity<=0:
                                self._block(journal_by_key,signal_date,symbol,"SIZING_BELOW_ONE_SHARE"); continue
                    gross = fill_quantity * fill_bar.open
                    position_after = position_before - fill_quantity
                    cash += gross
                    positions[symbol] = position_after
                    trades.append(self._trade(symbol, signal_date, fill_bar.timestamp_utc, SimulatedSide.SELL, fill_quantity, fill_bar.open, gross))
                    trade=trades[-1]; prior=journal_by_key.get((signal_date,symbol))
                    if prior is not None: journal_by_key[(signal_date,symbol)]=self._completed_entry(prior,signal,trade,cash-gross,cash,position_before,position_after,requested)
                else: self._block(journal_by_key,signal_date,symbol,"NO_POSITION_TO_SELL")
            for _,symbol,signal_date,_,_ in (x for x in day_signals if x[0] is SignalAction.BUY and positions.get(x[1],Decimal("0"))>0): self._block(journal_by_key,signal_date,symbol,"POSITION_ALREADY_HELD")
            buys = [x for x in day_signals if x[0] is SignalAction.BUY and positions.get(x[1], Decimal("0")) == 0]
            allocation = cash / Decimal(len(buys)) if buys else Decimal("0")
            for _, symbol, signal_date, fill_bar, signal in buys:
                requested=allocation
                if signal.sizing is not None and signal.sizing.mode.value != "none":
                    equity=cash+sum((q*last_prices.get(s,Decimal("0")) for s,q in positions.items()),Decimal("0")); context=SizingContext(fill_bar.timestamp_utc,signal.asset_references,signal.market_references,(SizingReference("cash",cash),SizingReference("equity",equity)),(SizingReference("quantity",Decimal("0")),SizingReference("market_value",Decimal("0"))))
                    requested,_=evaluate_sizing(signal.sizing,context)
                    if requested is None:
                        self._block(journal_by_key,signal_date,symbol,"SIZING_RETURNED_NO_AMOUNT"); continue
                    if requested>cash: raise ValueError("buy sizing exceeds available simulated cash")
                quantity = (requested // fill_bar.open)
                gross = quantity * fill_bar.open
                if quantity > 0 and gross <= cash:
                    cash -= gross
                    positions[symbol] = quantity
                    trades.append(self._trade(symbol, signal_date, fill_bar.timestamp_utc, SimulatedSide.BUY, quantity, fill_bar.open, -gross))
                    trade=trades[-1]; prior=journal_by_key.get((signal_date,symbol))
                    if prior is not None: journal_by_key[(signal_date,symbol)]=self._completed_entry(prior,signal,trade,cash+gross,cash,Decimal("0"),quantity,requested)
                else: self._block(journal_by_key,signal_date,symbol,"INSUFFICIENT_CASH_FOR_ONE_SHARE")
            market_value = sum((quantity * last_prices.get(symbol, Decimal("0")) for symbol, quantity in positions.items()), Decimal("0"))
            curve.append(EquityPoint(trading_date, cash, market_value, cash + market_value))
        ending_market = curve[-1].market_value if curve else Decimal("0")
        ending_equity = cash + ending_market
        status = BacktestStatus.COMPLETED if bars_by_symbol else BacktestStatus.BLOCKED
        result = BacktestResult(request.run_id, self.ENVIRONMENT, self._signals.strategy_id, status, started, datetime.now(UTC), request, len(symbols), len(bars_by_symbol), tuple(skipped), tuple(trades), tuple(curve), cash, ending_market, ending_equity, (ending_equity / request.initial_cash) - Decimal("1"), ("Research-only Raw/IEX data; corporate actions, commission and slippage are not modeled.",),tuple(journal_by_key[x] for x in sorted(journal_by_key)))
        if self._results is not None:
            self._results.save(result)
        return result

    @staticmethod
    def _trade(symbol, signal_date, filled_at, side, quantity, price, cash_effect):
        trade_id = uuid4()
        gross = quantity * price
        return SimulatedTrade(trade_id, f"SIM-{trade_id.hex[:12].upper()}", symbol, signal_date, filled_at, side, quantity, price, gross, Decimal("0"), cash_effect, "next_bar_open_market_fill")

    @staticmethod
    def _completed_entry(prior,signal,trade,cash_before,cash_after,position_before,position_after,requested):
        from dataclasses import replace
        references=tuple((x.name,x.value) for x in signal.asset_references+signal.market_references)
        return replace(prior,outcome=JournalOutcome.FILLED,reason="SIMULATED_FILL",sizing_mode=getattr(signal.sizing,"mode",type("X",(),{"value":"none"})) .value,sizing_expression=getattr(signal.sizing,"expression",None),sizing_references=references,requested_notional=requested,approved_notional=trade.gross_amount,quantity=trade.quantity,fill_price=trade.price,cash_before=cash_before,cash_after=cash_after,position_before=position_before,position_after=position_after,trade_id=trade.trade_id)

    @staticmethod
    def _block(entries,signal_date,symbol,reason):
        from dataclasses import replace
        prior=entries.get((signal_date,symbol))
        if prior is not None: entries[(signal_date,symbol)]=replace(prior,outcome=JournalOutcome.BLOCKED,reason=reason)
