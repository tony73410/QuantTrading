"""Replaceable signal port and the explicitly approved research-only baseline."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum
from typing import Protocol, Sequence
from quant_trading.market_history.models import MarketBar
from quant_trading.factors.expression import SafeExpressionFactorCalculator
from quant_trading.factors.models import FactorContext, FactorSnapshot, FactorSnapshotCollection, FactorStatus, MarketDataObservation, MarketDataWindow
from quant_trading.factors.market import MarketFactorCalculator
from quant_trading.decision.models import DecisionContext, DecisionInput, DecisionStatus, PortfolioSnapshot
from quant_trading.decision.rule_policy import SafeRuleDecisionPolicy
from uuid import uuid4
from dataclasses import replace
from quant_trading.decision.definitions import SizingDefinition
from quant_trading.decision.models import SizingReference
from .models import ConditionTrace, FactorTrace

class SignalAction(StrEnum):
    BUY = "buy"
    SELL = "sell"

@dataclass(frozen=True, slots=True)
class HistoricalSignal:
    action: SignalAction
    signal_date: date
    fill_bar: MarketBar
    sizing: object | None = None
    asset_references: tuple[SizingReference,...] = ()
    market_references: tuple[SizingReference,...] = ()
    factor_traces: tuple[object,...] = ()
    condition_traces: tuple[object,...] = ()

@dataclass(frozen=True, slots=True)
class HistoricalEvaluation:
    signal_date: date
    bar: MarketBar
    action: SignalAction | None
    signal: HistoricalSignal | None
    reason: str
    factor_traces: tuple[object,...] = ()
    condition_traces: tuple[object,...] = ()

class HistoricalSignalProvider(Protocol):
    strategy_id: str
    def signals(self, bars: Sequence[MarketBar], *, short_window: int, long_window: int, start_date: date, end_date: date) -> tuple[HistoricalSignal, ...]: ...

class ResearchSmaCrossSignalProvider:
    """Approved fixture only; it is not a registered production Factor/Decision."""
    strategy_id = "research.sma_20_50.long_only.v1"

    def signals(self, bars: Sequence[MarketBar], *, short_window: int, long_window: int, start_date: date, end_date: date) -> tuple[HistoricalSignal, ...]:
        return tuple(x.signal for x in self.evaluations(bars, short_window=short_window, long_window=long_window, start_date=start_date, end_date=end_date) if x.signal is not None)

    def evaluations(self, bars: Sequence[MarketBar], *, short_window: int, long_window: int, start_date: date, end_date: date):
        closes = [bar.close for bar in bars]
        found = []
        for index, bar in enumerate(bars):
            day=bar.timestamp_utc.date()
            if day < start_date or day > end_date:
                continue
            if index < long_window:
                found.append(HistoricalEvaluation(day,bar,None,None,"INSUFFICIENT_DATA")); continue
            short_now = sum(closes[index-short_window+1:index+1]) / Decimal(short_window)
            long_now = sum(closes[index-long_window+1:index+1]) / Decimal(long_window)
            short_prev = sum(closes[index-short_window:index]) / Decimal(short_window)
            long_prev = sum(closes[index-long_window:index]) / Decimal(long_window)
            action = SignalAction.BUY if short_prev <= long_prev and short_now > long_now else SignalAction.SELL if short_prev >= long_prev and short_now < long_now else None
            traces=(FactorTrace("asset","research.sma.short",str(short_window),short_now,"valid",bar.timestamp_utc,short_window),FactorTrace("asset","research.sma.long",str(long_window),long_now,"valid",bar.timestamp_utc,long_window))
            checks=(ConditionTrace("research.sma.short",str(short_window),short_now,">" if action is SignalAction.BUY else "<",long_now,action is not None),)
            signal=None
            if action is not None and index + 1 < len(bars):
                fill_bar = bars[index + 1]
                if fill_bar.timestamp_utc.date() <= end_date:
                    signal=HistoricalSignal(action,day,fill_bar,factor_traces=traces,condition_traces=checks)
            reason="CROSSOVER" if signal else "CONDITIONS_NOT_MET" if action is None else "NO_NEXT_BAR"
            found.append(HistoricalEvaluation(day,bar,action if signal else None,signal,reason,traces,checks))
        return tuple(found)

class DefinitionSignalProvider:
    """Replay exact saved Factor and Decision versions without execution authority."""
    def __init__(self, strategy, factors, decisions, market_factors=None) -> None:
        self.strategy_id=strategy.component_id; self._strategy=strategy; self._factors=factors; self._decisions=decisions; self._market_factors=market_factors; self._market_by_date={}; self._market_traces_by_date={}
        referenced=[]
        for decision_id in (strategy.buy_decision_component_id,strategy.sell_decision_component_id):
            referenced.extend(self._decisions.get_by_component_id(decision_id).selected_factor_ids)
        self.required_observations=max(self._factors.get_by_component_id(item).minimum_observations for item in referenced)

    def prepare(self,bars_by_symbol):
        self._market_by_date = {}
        self._market_traces_by_date = {}
        decision_defs=tuple(self._decisions.get_by_component_id(x) for x in (self._strategy.buy_decision_component_id,self._strategy.sell_decision_component_id))
        component_ids=tuple(dict.fromkeys(x for decision in decision_defs for x in decision.sizing.market_factor_component_ids))
        if component_ids and self._market_factors is None: raise ValueError("Market Factor sizing catalog is unavailable")
        for component_id in component_ids:
            definition=self._market_factors.get_by_component_id(component_id); source=self._factors.get_by_component_id(definition.source_factor_component_id)
            if any(symbol not in bars_by_symbol for symbol in definition.symbols): continue
            dates=set.intersection(*(set(x.timestamp_utc.date() for x in bars_by_symbol[symbol]) for symbol in definition.symbols))
            for day in dates:
                asset_results=[]; as_of=None
                for symbol in definition.symbols:
                    history=tuple(x for x in bars_by_symbol[symbol] if x.timestamp_utc.date()<=day); bar=history[-1]; as_of=bar.timestamp_utc
                    window=MarketDataWindow(symbol,as_of,bar.timeframe,bar.adjustment,bar.feed,tuple(MarketDataObservation(x,x.timestamp_utc) for x in history))
                    asset_results.append(SafeExpressionFactorCalculator(source).calculate(window,FactorContext(as_of)))
                output=MarketFactorCalculator(definition).calculate(tuple(asset_results),as_of_utc=as_of)
                if output.status is FactorStatus.VALID:
                    self._market_by_date.setdefault(day,{})[definition.market_factor_id]=SizingReference(definition.market_factor_id,output.value)
                    self._market_traces_by_date.setdefault(day,{})[definition.market_factor_id]=FactorTrace(
                        "market",
                        definition.market_factor_id,
                        str(definition.version),
                        output.value,
                        output.status.value,
                        output.as_of_utc,
                        source_symbols=definition.symbols,
                        detail=f"aggregation={definition.aggregation.value}; source={definition.source_factor_component_id}",
                    )

    def signals(self, bars, *, short_window, long_window, start_date, end_date):
        return tuple(x.signal for x in self.evaluations(bars,short_window=short_window,long_window=long_window,start_date=start_date,end_date=end_date) if x.signal is not None)

    def evaluations(self, bars, *, short_window, long_window, start_date, end_date):
        buy=self._decisions.get_by_component_id(self._strategy.buy_decision_component_id); sell=self._decisions.get_by_component_id(self._strategy.sell_decision_component_id)
        found=[]
        for index, bar in enumerate(bars):
            day=bar.timestamp_utc.date()
            if day < start_date or day > end_date: continue
            factor_cache={}
            buy_match,buy_refs,buy_results,buy_checks=self._matches(buy,bars[:index+1],factor_cache); sell_match,sell_refs,sell_results,sell_checks=self._matches(sell,bars[:index+1],factor_cache)
            if buy_match and sell_match: raise ValueError("simulation strategy produced conflicting buy and sell Decisions")
            action=SignalAction.BUY if buy_match else SignalAction.SELL if sell_match else None
            sizing=buy.sizing if action is SignalAction.BUY else sell.sizing if action is SignalAction.SELL else None
            refs=buy_refs if action is SignalAction.BUY else sell_refs
            market_refs=tuple(self._market_by_date.get(bar.timestamp_utc.date(),{}).values())
            results=tuple({(x.factor_name,x.factor_version):x for x in buy_results+sell_results}.values())
            traces=tuple(FactorTrace("asset",x.factor_name,x.factor_version,x.value,x.status.value,x.as_of_utc,x.lookback) for x in results)
            traces+=tuple(self._market_traces_by_date.get(day,{}).values())
            checks=buy_checks+sell_checks
            signal=None
            if action is not None and index+1<len(bars) and bars[index+1].timestamp_utc.date()<=end_date:
                signal=HistoricalSignal(action,day,bars[index+1],sizing,refs,market_refs,traces,checks)
            found.append(HistoricalEvaluation(day,bar,action if signal else None,signal,"DECISION_MATCHED" if signal else "CONDITIONS_NOT_MET" if action is None else "NO_NEXT_BAR",traces,checks))
        return tuple(found)

    def _matches(self, decision, bars, factor_cache=None):
        as_of=bars[-1].timestamp_utc
        factor_cache = {} if factor_cache is None else factor_cache
        results=[]
        for condition in decision.conditions:
            definition=self._factors.get_by_component_id(condition.factor_component_id)
            result=factor_cache.get(condition.factor_component_id)
            if result is None:
                window=MarketDataWindow(bars[-1].symbol,as_of,bars[-1].timeframe,bars[-1].adjustment,bars[-1].feed,tuple(MarketDataObservation(x,x.timestamp_utc) for x in bars))
                result=SafeExpressionFactorCalculator(definition).calculate(window,FactorContext(as_of))
                factor_cache[condition.factor_component_id]=result
            if result.status is not FactorStatus.VALID:
                trace=ConditionTrace(condition.factor_name,condition.factor_version,None,condition.operator.value,condition.threshold,False)
                return False,(),tuple(results)+(result,),(trace,)
            results.append(result)
        snapshot=FactorSnapshot(uuid4(),bars[-1].symbol,as_of,bars[-1].timeframe,tuple(results),as_of)
        direction_only=replace(decision,sizing=SizingDefinition())
        output=SafeRuleDecisionPolicy(direction_only).evaluate(DecisionInput(FactorSnapshotCollection(uuid4(),as_of,(snapshot,)),PortfolioSnapshot(uuid4(),as_of),DecisionContext(as_of)))
        refs=tuple(SizingReference(x.factor_name,Decimal(x.value)) for x in results if isinstance(x.value,(Decimal,int)) and not isinstance(x.value,bool))
        checks=tuple(ConditionTrace(c.factor_name,c.factor_version,Decimal(r.value),c.operator.value,c.threshold,SafeRuleDecisionPolicy._compare(Decimal(r.value),c.operator,c.threshold)) for c,r in zip(decision.conditions,results))
        return output.status is DecisionStatus.VALID,refs,tuple(results),checks
