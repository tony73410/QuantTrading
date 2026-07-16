"""Top-level portfolio accounting interfaces."""

from typing import Protocol

from .models import AccountSnapshot, PortfolioSnapshot


class AccountSnapshotProvider(Protocol):
    def get_account_snapshot(self) -> AccountSnapshot: ...


class PortfolioSnapshotProvider(Protocol):
    def get_portfolio_snapshot(self) -> PortfolioSnapshot: ...
