"""GUI-safe query contracts; callers receive immutable read models only."""

from dataclasses import dataclass
from typing import Protocol

from ..ledger.models import LedgerEntry
from ..models import PortfolioSnapshot
from ..reconciliation.models import ReconciliationResult


@dataclass(frozen=True, slots=True)
class PortfolioLedgerView:
    portfolio: PortfolioSnapshot | None
    transactions: tuple[LedgerEntry, ...]
    operations: tuple[LedgerEntry, ...]
    last_reconciliation: ReconciliationResult | None
    status_message: str


class PortfolioAccountingQueryService(Protocol):
    def overview(self) -> PortfolioLedgerView: ...


class EmptyPortfolioAccountingQueryService:
    """No-data query object for compatible GUI construction and offline tests."""

    def overview(self) -> PortfolioLedgerView:
        return PortfolioLedgerView(None, (), (), None, "No ledger facts recorded; accounting is not connected.")
