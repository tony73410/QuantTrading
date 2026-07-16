from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import uuid4
from quant_trading.backtesting import BacktestRequest, HistoricalBacktestService, JsonBacktestResultRepository
from quant_trading.market_history.models import Adjustment, DataFeed, MarketBar, Timeframe
from quant_trading.backtesting.strategies import HistoricalEvaluation,HistoricalSignal,SignalAction
from quant_trading.decision import SizingDefinition,SizingMode

class FakeStore:
    def list_symbols(self): return ["AAA"]
    def query_bars(self, request):
        bars = []
        for index in range(80):
            close = Decimal(200-index) if index < 45 else Decimal(155+(index-45)*4)
            stamp = datetime(2025, 1, 1, tzinfo=UTC) + timedelta(days=index)
            bars.append(MarketBar("AAA", stamp, close, close, close, close, 100, close, 1, Timeframe.DAY, Adjustment.RAW, DataFeed.IEX, "fake", stamp))
        return bars

def test_sma_backtest_uses_next_bar_and_is_isolated(tmp_path: Path):
    repository = JsonBacktestResultRepository(tmp_path / "simulations"); service = HistoricalBacktestService(FakeStore(), repository)
    result = service.run(BacktestRequest(uuid4(), date(2025,1,1), date(2025,3,31), Decimal("1000000")))
    assert result.environment == "historical_simulation"; assert result.trades
    assert result.trades[0].signal_date < result.trades[0].filled_at_utc.date(); assert result.trades[0].fee_amount == Decimal("0"); assert repository.get(result.run_id) == result
    expected_days=sum(1 for bar in FakeStore().query_bars(None) if result.request.start_date <= bar.timestamp_utc.date() <= result.request.end_date)
    assert len(result.decision_journal)==expected_days
    assert {x.symbol for x in result.decision_journal}=={"AAA"}
    assert any(x.factor_traces for x in result.decision_journal)
    assert any(x.trade_id is not None and x.cash_before is not None and x.cash_after is not None for x in result.decision_journal)
    assert not any(x.outcome.value=="pending_next_bar" for x in result.decision_journal)

def test_invalid_cash_and_dates_are_blocked():
    for start, end, cash in ((date(2025,2,1),date(2025,1,1),Decimal("100")),(date(2025,1,1),date(2025,2,1),Decimal("0"))):
        try: BacktestRequest(uuid4(), start, end, cash)
        except ValueError: pass
        else: raise AssertionError("invalid request accepted")

def test_unexpected_market_validation_exception_is_not_silently_skipped():
    class BrokenStore:
        def list_symbols(self): return ["AAA"]
        def query_bars(self,request): return [object()]
    try:
        HistoricalBacktestService(BrokenStore()).run(BacktestRequest(uuid4(),date(2025,1,1),date(2025,2,1),Decimal("1000"),short_window=2,long_window=3))
    except AttributeError: pass
    else: raise AssertionError("unexpected validation failure was silently converted to skipped data")

def test_simulation_consumes_decision_cash_percentage_sizing():
    class SizedProvider:
        strategy_id="sized"
        def signals(self,bars,**kwargs): return (HistoricalSignal(SignalAction.BUY,bars[50].timestamp_utc.date(),bars[51],SizingDefinition(SizingMode.PERCENT_AVAILABLE_CASH,Decimal("10"))),)
    result=HistoricalBacktestService(FakeStore(),signal_provider=SizedProvider()).run(BacktestRequest(uuid4(),date(2025,1,1),date(2025,3,31),Decimal("1000000")))
    assert len(result.trades)==1 and result.trades[0].gross_amount<=Decimal("100000")

def test_partial_sell_preserves_remaining_position_and_requested_notional():
    class FlatStore:
        def list_symbols(self): return ["AAA"]
        def query_bars(self,request):
            return [MarketBar("AAA",datetime(2025,1,1,tzinfo=UTC)+timedelta(days=i),Decimal("10"),Decimal("10"),Decimal("10"),Decimal("10"),100,Decimal("10"),1,Timeframe.DAY,Adjustment.RAW,DataFeed.IEX,"fake",datetime(2025,1,1,tzinfo=UTC)+timedelta(days=i)) for i in range(7)]
    class PartialSellProvider:
        strategy_id="partial-sell"
        def evaluations(self,bars,**kwargs):
            buy=HistoricalSignal(SignalAction.BUY,bars[3].timestamp_utc.date(),bars[4],SizingDefinition(SizingMode.FIXED_USD,Decimal("1005")))
            sell=HistoricalSignal(SignalAction.SELL,bars[4].timestamp_utc.date(),bars[5],SizingDefinition(SizingMode.FIXED_USD,Decimal("305")))
            return (HistoricalEvaluation(buy.signal_date,bars[3],buy.action,buy,"BUY"),HistoricalEvaluation(sell.signal_date,bars[4],sell.action,sell,"SELL"))
        def signals(self,bars,**kwargs): return ()
    result=HistoricalBacktestService(FlatStore(),signal_provider=PartialSellProvider()).run(BacktestRequest(uuid4(),date(2025,1,1),date(2025,1,7),Decimal("2000"),short_window=2,long_window=3))
    sell=next(x for x in result.decision_journal if x.action.value=="sell")
    assert sell.requested_notional==Decimal("305")
    assert sell.approved_notional==Decimal("300")
    assert sell.position_before==Decimal("100")
    assert sell.position_after==Decimal("70")
    assert result.ending_market_value==Decimal("700")
