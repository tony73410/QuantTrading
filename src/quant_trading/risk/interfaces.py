"""Public interface for independently testable risk rules."""

from __future__ import annotations

from typing import Protocol

from quant_trading.decision.models import PortfolioSnapshot, TradeIntent

from .models import (
    AccountSnapshot,
    OpenOrdersSnapshot,
    RiskEvaluationContext,
    RiskRuleResult,
)


class RiskPolicy(Protocol):
    @property
    def policy_name(self) -> str: ...

    @property
    def policy_version(self) -> str: ...

    def evaluate(
        self,
        trade_intent: TradeIntent,
        context: RiskEvaluationContext,
    ) -> RiskRuleResult: ...


class AccountStateProvider(Protocol):
    """Planned boundary; no concrete account connection currently exists."""

    def get_account_snapshot(self) -> AccountSnapshot: ...


class PortfolioStateProvider(Protocol):
    """Planned boundary; no concrete portfolio connection currently exists."""

    def get_portfolio_snapshot(self) -> PortfolioSnapshot: ...


class OpenOrderStateProvider(Protocol):
    """Planned boundary; no concrete order connection currently exists."""

    def get_open_orders_snapshot(self) -> OpenOrdersSnapshot: ...
