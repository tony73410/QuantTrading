"""Local persistence adapters for historical market data."""

from .sqlite_store import SQLiteHistoricalDataStore

__all__ = ["SQLiteHistoricalDataStore"]
