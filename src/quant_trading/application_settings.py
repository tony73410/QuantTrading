"""Application-wide role and safety settings.

Market-data sourcing, the user's brokerage, and execution mode are separate
concepts. These settings describe the current project state; they do not
connect to a brokerage or implement order execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class MarketDataProviderType(str, Enum):
    ALPACA = "alpaca"


class BrokerageType(str, Enum):
    ALPACA = "alpaca"
    FIDELITY = "fidelity"


class ExecutionEnvironment(str, Enum):
    ALPACA_PAPER = "alpaca_paper"
    ALPACA_LIVE = "alpaca_live"
    MANUAL_FIDELITY = "manual_fidelity"


# Backward-compatible name retained for code written before the environment
# terminology was clarified. New code should use ExecutionEnvironment.
ExecutionMode = ExecutionEnvironment


@dataclass(frozen=True, slots=True)
class ApplicationRoleSettings:
    """Fixed safe defaults for the currently approved application scope."""

    market_data_provider: MarketDataProviderType = MarketDataProviderType.ALPACA
    primary_brokerage: BrokerageType = BrokerageType.ALPACA
    execution_environment: ExecutionEnvironment = (
        ExecutionEnvironment.ALPACA_PAPER
    )
    automatic_order_submission: bool = False
    paper_trading_enabled: bool = True
    live_trading_enabled: bool = False
    require_manual_confirmation: bool = True

    @property
    def execution_mode(self) -> ExecutionEnvironment:
        """Compatibility view for the earlier configuration field name."""
        return self.execution_environment

    def __post_init__(self) -> None:
        """Reject contradictory Paper/Live state descriptions."""
        if self.execution_environment is ExecutionEnvironment.ALPACA_PAPER:
            if not self.paper_trading_enabled or self.live_trading_enabled:
                raise ValueError(
                    "Alpaca Paper requires paper enabled and live disabled"
                )
        elif self.execution_environment is ExecutionEnvironment.ALPACA_LIVE:
            if self.paper_trading_enabled or not self.live_trading_enabled:
                raise ValueError(
                    "Alpaca Live requires paper disabled and live enabled"
                )
        elif self.execution_environment is ExecutionEnvironment.MANUAL_FIDELITY:
            if self.paper_trading_enabled or self.live_trading_enabled:
                raise ValueError(
                    "Manual Fidelity cannot enable Alpaca Paper or Live"
                )
