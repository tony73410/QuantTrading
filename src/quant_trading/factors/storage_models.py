"""Typed records exposed by factor-history persistence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID

from quant_trading.market_history.models import Adjustment, DataFeed, Timeframe


class FactorCalculationStatus(StrEnum):
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class FactorCalculationRun:
    run_id: UUID
    correlation_id: str | None
    symbol: str
    as_of_utc: datetime
    timeframe: Timeframe
    adjustment: Adjustment
    feed: DataFeed
    started_at_utc: datetime
    completed_at_utc: datetime | None
    status: FactorCalculationStatus
    snapshot_id: UUID | None
    error_code: str | None
    error_summary: str | None

    def __post_init__(self) -> None:
        symbol = self.symbol.strip().upper()
        if not symbol:
            raise ValueError("factor calculation run symbol must not be empty")
        for field_name in ("as_of_utc", "started_at_utc"):
            value = getattr(self, field_name)
            if value.tzinfo is None or value.utcoffset() is None:
                raise ValueError(f"{field_name} must include a timezone")
            object.__setattr__(self, field_name, value.astimezone(UTC))
        if self.completed_at_utc is not None:
            if (
                self.completed_at_utc.tzinfo is None
                or self.completed_at_utc.utcoffset() is None
            ):
                raise ValueError("completed_at_utc must include a timezone")
            object.__setattr__(
                self, "completed_at_utc", self.completed_at_utc.astimezone(UTC)
            )
        object.__setattr__(self, "symbol", symbol)
