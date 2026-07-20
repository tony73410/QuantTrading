"""Public interface for independently testable risk rules."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from quant_trading.decision.models import PortfolioSnapshot, TradeIntent
from quant_trading.portfolio_accounting.interfaces import (
    AccountSnapshotProvider as AccountingAccountSnapshotProvider,
    PortfolioSnapshotProvider as AccountingPortfolioSnapshotProvider,
)

from .models import (
    AccountSnapshot,
    OpenOrdersSnapshot,
    RiskEvaluationContext,
    RiskDecision,
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


class RiskDecisionStore(Protocol):
    """Persist Risk evidence without giving Risk any SQL or execution behavior."""

    def save_risk_decision(
        self,
        algorithm_run_id: UUID,
        stage_id: UUID,
        decision: RiskDecision,
    ) -> None: ...


class AccountStateProvider(Protocol):
    """Planned boundary; no concrete account connection currently exists."""

    def get_account_snapshot(self) -> AccountSnapshot: ...


class PortfolioStateProvider(Protocol):
    """Planned boundary; no concrete portfolio connection currently exists."""

    def get_portfolio_snapshot(self) -> PortfolioSnapshot: ...


class OpenOrderStateProvider(Protocol):
    """Planned boundary; no concrete order connection currently exists."""

    def get_open_orders_snapshot(self) -> OpenOrdersSnapshot: ...
