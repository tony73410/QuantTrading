"""Validate and version user-named simulation strategy compositions."""
from datetime import UTC, datetime
from uuid import uuid4
from quant_trading.decision.models import DecisionAction
from .strategy_definitions import SimulationStrategyDefinition

class SimulationStrategyService:
    def __init__(self, store, decisions, factors) -> None: self._store=store; self._decisions=decisions; self._factors=factors
    def list_definitions(self, strategy_id=None):
        items=self._store.list_definitions(); normalized=None if strategy_id is None else strategy_id.strip().lower()
        return tuple(sorted((x for x in items if normalized is None or x.strategy_id==normalized),key=lambda x:(x.strategy_id,-x.version)))
    def get(self, component_id):
        for item in self.list_definitions():
            if item.component_id==component_id: return item
        raise ValueError("simulation strategy does not exist")
    def save(self, *, strategy_id, display_name, description, buy_decision_component_id, sell_decision_component_id, change_reason, actor="user"):
        buy=self._decisions.get_by_component_id(buy_decision_component_id); sell=self._decisions.get_by_component_id(sell_decision_component_id)
        if buy.match_action is not DecisionAction.INCREASE: raise ValueError("buy Decision must produce INCREASE")
        if sell.match_action not in (DecisionAction.DECREASE, DecisionAction.EXIT): raise ValueError("sell Decision must produce DECREASE or EXIT")
        for decision in (buy,sell):
            for factor_id in decision.selected_factor_ids: self._factors.get_by_component_id(factor_id)
        versions=self.list_definitions(strategy_id)
        item=SimulationStrategyDefinition(uuid4(),strategy_id,max((x.version for x in versions),default=0)+1,display_name,description,buy_decision_component_id,sell_decision_component_id,datetime.now(UTC),actor,change_reason)
        self._store.save_definition(item); return item
