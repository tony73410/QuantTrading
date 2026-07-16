"""Ports for isolated backtest execution and result queries."""

from typing import Protocol, Sequence
from uuid import UUID

from quant_trading.market_history.models import HistoricalDataRequest, MarketBar

from .models import BacktestRequest, BacktestResult


class BacktestRunner(Protocol):
    def run(self, request: BacktestRequest) -> BacktestResult: ...


class BacktestResultRepository(Protocol):
    def save(self, result: BacktestResult) -> None: ...
    def get(self, run_id: UUID) -> BacktestResult: ...
    def list_results(self) -> tuple[BacktestResult, ...]: ...


class HistoricalBarSource(Protocol):
    """Read-only bars required by Backtesting; no cache or Provider authority."""

    def list_symbols(self) -> Sequence[str]: ...

    def query_bars(self, request: HistoricalDataRequest) -> Sequence[MarketBar]: ...
