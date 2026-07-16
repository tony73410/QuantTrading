"""Deterministic in-memory append-only ledger adapter for tests and scaffolding."""

from uuid import UUID

from .interfaces import DuplicateLedgerEventError
from .models import LedgerEntry


class InMemoryLedgerRepository:
    def __init__(self) -> None:
        self._entries: list[LedgerEntry] = []
        self._by_id: dict[UUID, LedgerEntry] = {}
        self._idempotency_keys: set[str] = set()

    def append(self, entry: LedgerEntry) -> int:
        if entry.entry_id in self._by_id:
            raise DuplicateLedgerEventError(f"entry_id already exists: {entry.entry_id}")
        key = entry.idempotency_key
        if key is not None and key in self._idempotency_keys:
            raise DuplicateLedgerEventError(f"external event already recorded: {key}")
        self._entries.append(entry)
        self._by_id[entry.entry_id] = entry
        if key is not None:
            self._idempotency_keys.add(key)
        return len(self._entries)

    def get(self, entry_id: UUID) -> LedgerEntry:
        return self._by_id[entry_id]

    def entries(self) -> tuple[LedgerEntry, ...]:
        return tuple(self._entries)
