"""In-memory read service used by the disabled GUI scaffold."""

from .interfaces import PortfolioLedgerView


class InMemoryPortfolioAccountingQueryService:
    def __init__(self, view: PortfolioLedgerView | None = None) -> None:
        self._view = view or PortfolioLedgerView(None, (), (), None, "No ledger facts recorded; accounting is not connected.")

    def overview(self) -> PortfolioLedgerView:
        return self._view
