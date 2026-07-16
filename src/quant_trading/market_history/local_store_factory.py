"""Narrow factory exposing the existing local-history store through its protocol."""

from __future__ import annotations

from pathlib import Path

from .interfaces import HistoricalDataStore
from .storage.sqlite_store import SQLiteHistoricalDataStore


def build_local_history_store(database_path: Path) -> HistoricalDataStore:
    """Create the canonical SQLite history store without leaking its class outward."""

    store = SQLiteHistoricalDataStore(database_path)
    store.initialize()
    return store
