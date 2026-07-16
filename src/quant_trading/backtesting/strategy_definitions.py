"""Immutable, research-only simulation strategy composition contracts."""
from __future__ import annotations
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

_ID = re.compile(r"^[a-z][a-z0-9_.-]{0,63}$")

@dataclass(frozen=True, slots=True)
class SimulationStrategyDefinition:
    definition_id: UUID
    strategy_id: str
    version: int
    display_name: str
    description: str
    buy_decision_component_id: str
    sell_decision_component_id: str
    created_at_utc: datetime
    created_by: str
    change_reason: str
    universe: str = "all_eligible_local_symbols"
    allocation: str = "sell_then_equal_available_cash"
    fill_model: str = "next_bar_open_whole_shares"
    cost_model: str = "zero_commission_zero_slippage"
    research_only: bool = True
    execution_allowed: bool = False
    live_allowed: bool = False

    def __post_init__(self) -> None:
        strategy_id = self.strategy_id.strip().lower()
        if not _ID.fullmatch(strategy_id): raise ValueError("strategy_id must use lowercase letters, digits, dot, dash, or underscore")
        if self.version < 1: raise ValueError("strategy version must be positive")
        for field in ("display_name", "description", "buy_decision_component_id", "sell_decision_component_id", "created_by", "change_reason"):
            if not getattr(self, field).strip(): raise ValueError(f"{field} must not be empty")
        if self.buy_decision_component_id == self.sell_decision_component_id: raise ValueError("buy and sell Decisions must be different")
        if self.created_at_utc.tzinfo is None: raise ValueError("created_at_utc must include a timezone")
        if not self.research_only or self.execution_allowed or self.live_allowed: raise ValueError("simulation strategies must remain research-only with execution disabled")
        object.__setattr__(self, "strategy_id", strategy_id); object.__setattr__(self, "created_at_utc", self.created_at_utc.astimezone(UTC))

    @property
    def component_id(self) -> str: return f"simulation_strategy.{self.strategy_id}.v{self.version}"
