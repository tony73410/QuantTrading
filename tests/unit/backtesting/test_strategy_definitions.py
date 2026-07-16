from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import uuid4
from quant_trading.algorithm_control.app import build_controller
from quant_trading.backtesting import BacktestRequest, DefinitionSignalProvider, HistoricalBacktestService
from quant_trading.decision import ComparisonOperator, DecisionAction, DecisionCondition, RuleCombination
from quant_trading.factors import FactorDefinitionParameter
from quant_trading.factors import MarketAggregation
from quant_trading.decision import SizingDefinition,SizingMode
from quant_trading.market_history.models import Adjustment,DataFeed,MarketBar,Timeframe
import os
os.environ.setdefault("QT_QPA_PLATFORM","offscreen")
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QDate
from quant_trading.backtesting.app import BacktestingWindow

def _create(controller):
    factor=controller.save_factor_definition(factor_id="strategy.price",display_name="Strategy price",description="Saved strategy test factor",expression='mean("close", short) - mean("close", long)',minimum_observations=3,output_unit="USD",missing_input_policy="return_missing_status",parameters=(FactorDefinitionParameter("short",Decimal("2")),FactorDefinitionParameter("long",Decimal("3"))),change_reason="test")
    def decision(name,action,operator): return controller.save_decision_definition(policy_id=name,display_name=name,description="Saved strategy decision",conditions=(DecisionCondition(factor.component_id,factor.factor_id,str(factor.version),operator,Decimal("0")),),combination=RuleCombination.ALL,match_action=action,reason_code="TEST",change_reason="test")
    buy=decision("strategy.buy",DecisionAction.INCREASE,ComparisonOperator.GREATER_THAN); sell=decision("strategy.sell",DecisionAction.DECREASE,ComparisonOperator.LESS_THAN)
    return factor,buy,sell

def test_strategy_is_named_versioned_and_execution_disabled(tmp_path: Path):
    controller=build_controller(tmp_path); _,buy,sell=_create(controller)
    one=controller.save_simulation_strategy(strategy_id="my.strategy",display_name="策略1",description="Local research strategy",buy_decision_component_id=buy.component_id,sell_decision_component_id=sell.component_id,change_reason="create")
    two=controller.save_simulation_strategy(strategy_id="my.strategy",display_name="策略1 revised",description="Local research strategy",buy_decision_component_id=buy.component_id,sell_decision_component_id=sell.component_id,change_reason="revise")
    assert (one.version,two.version)==(1,2); assert not one.execution_allowed and not one.live_allowed and one.research_only
    assert (tmp_path/"runtime"/"algorithm_control"/"simulation_strategies.json").exists()

def test_wrong_decision_action_is_rejected(tmp_path: Path):
    controller=build_controller(tmp_path); _,buy,_=_create(controller)
    try: controller.save_simulation_strategy(strategy_id="bad",display_name="Bad",description="Bad action",buy_decision_component_id=buy.component_id,sell_decision_component_id=buy.component_id,change_reason="test")
    except ValueError: pass
    else: raise AssertionError("invalid strategy accepted")

class FakeStore:
    def list_symbols(self): return ["AAA"]
    def query_bars(self,request):
        values=(10,9,8,9,11,12,10,8,7)
        return [MarketBar("AAA",datetime(2025,1,1,tzinfo=UTC)+timedelta(days=i),Decimal(v),Decimal(v),Decimal(v),Decimal(v),100,Decimal(v),1,Timeframe.DAY,Adjustment.RAW,DataFeed.IEX,"fake",datetime(2025,1,1,tzinfo=UTC)+timedelta(days=i)) for i,v in enumerate(values)]

def test_saved_factor_and_decisions_drive_backtest(tmp_path: Path):
    controller=build_controller(tmp_path); _,buy,sell=_create(controller)
    strategy=controller.save_simulation_strategy(strategy_id="replay",display_name="Replay",description="Replay exact versions",buy_decision_component_id=buy.component_id,sell_decision_component_id=sell.component_id,change_reason="test")
    provider=DefinitionSignalProvider(strategy,controller.factor_definitions,controller.decision_definitions)
    result=HistoricalBacktestService(FakeStore(),signal_provider=provider).run(BacktestRequest(uuid4(),date(2025,1,1),date(2025,1,10),Decimal("1000"),short_window=2,long_window=3))
    assert result.strategy_id==strategy.component_id; assert [x.side.value for x in result.trades]==["buy","sell"]
    assert len(result.decision_journal)==9
    assert all(x.factor_traces and x.condition_traces for x in result.decision_journal)
    assert {x.action.value for x in result.decision_journal} >= {"buy","sell","no_decision"}

def test_backtesting_gui_lists_saved_strategy(tmp_path: Path):
    app=QApplication.instance() or QApplication([]); controller=build_controller(tmp_path); _,buy,sell=_create(controller)
    strategy=controller.save_simulation_strategy(strategy_id="gui",display_name="策略2",description="GUI selection",buy_decision_component_id=buy.component_id,sell_decision_component_id=sell.component_id,change_reason="test")
    window=BacktestingWindow(HistoricalBacktestService(FakeStore()),controller.simulation_strategies,controller.factor_definitions,controller.decision_definitions)
    assert window.strategy.findData(strategy.component_id)>=0; assert window.strategy.currentText(); window.close(); assert app is not None

def test_backtesting_gui_exposes_daily_decision_journal(tmp_path: Path):
    class LongStore(FakeStore):
        def query_bars(self,request):
            return [MarketBar("AAA",datetime(2025,1,1,tzinfo=UTC)+timedelta(days=i),Decimal(100+i),Decimal(100+i),Decimal(100+i),Decimal(100+i),100,Decimal(100+i),1,Timeframe.DAY,Adjustment.RAW,DataFeed.IEX,"fake",datetime(2025,1,1,tzinfo=UTC)+timedelta(days=i)) for i in range(80)]
    app=QApplication.instance() or QApplication([]); window=BacktestingWindow(HistoricalBacktestService(LongStore()))
    window.start_date.setDate(QDate(2025,1,1)); window.end_date.setDate(QDate(2025,3,31)); window.initial_cash.setText("1000"); window.run_backtest()
    assert window.journal.rowCount()==80
    window.journal.selectRow(3); window._show_journal_detail()
    assert "OHLCV" in window.journal_detail.toPlainText() and "Factors:" in window.journal_detail.toPlainText()
    window.journal_symbol.setText("ZZZ"); assert window.journal.rowCount()==0
    window.close(); assert app is not None

def test_saved_market_factor_can_reference_simulated_cash_for_sizing(tmp_path: Path):
    controller=build_controller(tmp_path); factor,buy,sell=_create(controller)
    market=controller.save_market_factor_definition(market_factor_id="market.one",display_name="Market one",description="One-symbol market context",source_factor_component_id=factor.component_id,symbols=("AAA",),aggregation=MarketAggregation.MEAN,change_reason="test")
    sized_buy=controller.save_decision_definition(policy_id="strategy.sized.buy",display_name="Sized buy",description="Uses account and market context",conditions=buy.conditions,combination=buy.combination,match_action=buy.match_action,reason_code="SIZED",change_reason="test",sizing=SizingDefinition(SizingMode.RESTRICTED_EXPRESSION,expression="account.cash * 0.10 + market.market.one * 0",market_factor_component_ids=(market.component_id,)))
    strategy=controller.save_simulation_strategy(strategy_id="market.sized",display_name="Market sized",description="Exact market reference",buy_decision_component_id=sized_buy.component_id,sell_decision_component_id=sell.component_id,change_reason="test")
    provider=DefinitionSignalProvider(strategy,controller.factor_definitions,controller.decision_definitions,controller.market_factor_definitions)
    result=HistoricalBacktestService(FakeStore(),signal_provider=provider).run(BacktestRequest(uuid4(),date(2025,1,1),date(2025,1,10),Decimal("1000"),short_window=2,long_window=3))
    assert result.trades and result.trades[0].gross_amount<=Decimal("100")
    market_traces=tuple(trace for entry in result.decision_journal for trace in entry.factor_traces if trace.scope=="market")
    assert market_traces and {trace.factor_version for trace in market_traces}=={"1"}
    assert all(trace.source_symbols==("AAA",) for trace in market_traces)
    assert all(len({(trace.scope,trace.factor_id,trace.factor_version) for trace in entry.factor_traces})==len(entry.factor_traces) for entry in result.decision_journal)
    provider.prepare({})
    assert not any(trace.scope=="market" for trace in provider.evaluations(FakeStore().query_bars(None),short_window=2,long_window=3,start_date=date(2025,1,1),end_date=date(2025,1,10))[0].factor_traces)
