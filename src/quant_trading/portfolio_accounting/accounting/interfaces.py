"""Accounting service protocol."""

from datetime import datetime
from decimal import Decimal
from typing import Protocol

from ..ledger.models import LedgerEntry
from ..models import PortfolioSnapshot


class PortfolioAccountingService(Protocol):
    def rebuild(self, entries: tuple[LedgerEntry, ...], *, starting_cash: Decimal, currency: str, as_of_utc: datetime) -> PortfolioSnapshot: ...
