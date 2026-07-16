"""Typed reconciliation results that never mutate either source."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID


class ReconciliationStatus(StrEnum):
    MATCHED = "matched"
    MISMATCH = "mismatch"
    PARTIAL = "partial"
    STALE_REFERENCE = "stale_reference"
    NOT_AVAILABLE = "not_available"
    ERROR = "error"


class ReconciliationSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class ReconciliationDifference:
    field: str
    local_value: Decimal | str | None
    external_value: Decimal | str | None
    difference: Decimal | None
    tolerance: Decimal | None
    severity: ReconciliationSeverity
    possible_reason: str | None = None


@dataclass(frozen=True, slots=True)
class ReconciliationResult:
    reconciliation_id: UUID
    checked_at_utc: datetime
    status: ReconciliationStatus
    differences: tuple[ReconciliationDifference, ...]
    local_reference: str
    external_reference: str

    def __post_init__(self) -> None:
        if self.checked_at_utc.tzinfo is None or self.checked_at_utc.utcoffset() is None:
            raise ValueError("checked_at_utc must include a timezone")
        object.__setattr__(self, "checked_at_utc", self.checked_at_utc.astimezone(UTC))
