"""Public protocols between provider, storage, service, and chart layers."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, Sequence
from uuid import UUID

from .models import CoverageInterval, HistoricalDataRequest, MarketBar


class HistoricalMarketDataProvider(Protocol):
    @property
    def available(self) -> bool: ...

    def fetch_bars(self, request: HistoricalDataRequest) -> list[MarketBar]: ...


class HistoricalDataStore(Protocol):
    def initialize(self) -> None: ...

    def list_symbols(self) -> list[str]: ...

    def query_bars(self, request: HistoricalDataRequest) -> list[MarketBar]: ...

    def get_coverage(self, request: HistoricalDataRequest) -> list[CoverageInterval]: ...

    def get_last_successful_fetch(self, request: HistoricalDataRequest) -> datetime | None: ...

    def begin_fetch(self, request: HistoricalDataRequest) -> UUID: ...

    def complete_fetch_success(
        self,
        fetch_id: UUID,
        request: HistoricalDataRequest,
        interval: CoverageInterval,
        bars: Sequence[MarketBar],
    ) -> None: ...

    def complete_fetch_failure(self, fetch_id: UUID, error_summary: str) -> None: ...
