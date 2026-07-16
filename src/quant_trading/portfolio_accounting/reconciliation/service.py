"""Minimal scalar comparison; it reports and never repairs mismatches."""

from datetime import datetime
from decimal import Decimal
from typing import Mapping
from uuid import uuid4

from .models import ReconciliationDifference, ReconciliationResult, ReconciliationSeverity, ReconciliationStatus


class InMemoryReconciliationService:
    def compare(self, local: Mapping[str, Decimal], external: Mapping[str, Decimal], *, tolerance: Decimal, checked_at_utc: datetime, local_reference: str, external_reference: str) -> ReconciliationResult:
        if not isinstance(tolerance, Decimal) or not tolerance.is_finite() or tolerance < 0:
            raise ValueError("tolerance must be a non-negative finite Decimal")
        differences = []
        for field in sorted(set(local) | set(external)):
            local_value = local.get(field)
            external_value = external.get(field)
            difference = None if local_value is None or external_value is None else local_value - external_value
            if difference is None or abs(difference) > tolerance:
                differences.append(ReconciliationDifference(field, local_value, external_value, difference, tolerance, ReconciliationSeverity.WARNING, "Missing reference value" if difference is None else None))
        if not differences:
            status = ReconciliationStatus.MATCHED
        elif any(item.difference is None for item in differences):
            status = ReconciliationStatus.PARTIAL
        else:
            status = ReconciliationStatus.MISMATCH
        return ReconciliationResult(uuid4(), checked_at_utc, status, tuple(differences), local_reference, external_reference)
