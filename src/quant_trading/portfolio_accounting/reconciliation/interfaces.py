"""Reconciliation service protocol."""

from datetime import datetime
from decimal import Decimal
from typing import Mapping, Protocol

from .models import ReconciliationResult


class ReconciliationService(Protocol):
    def compare(self, local: Mapping[str, Decimal], external: Mapping[str, Decimal], *, tolerance: Decimal, checked_at_utc: datetime, local_reference: str, external_reference: str) -> ReconciliationResult: ...
