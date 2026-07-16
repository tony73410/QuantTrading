"""Append-only ledger repository protocol."""

from typing import Protocol
from uuid import UUID

from .models import LedgerEntry


class DuplicateLedgerEventError(ValueError):
    pass


class LedgerRepository(Protocol):
    def append(self, entry: LedgerEntry) -> int: ...
    def get(self, entry_id: UUID) -> LedgerEntry: ...
    def entries(self) -> tuple[LedgerEntry, ...]: ...
