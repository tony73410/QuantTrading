from datetime import UTC, datetime
from decimal import Decimal

from quant_trading.portfolio_accounting.reconciliation import InMemoryReconciliationService, ReconciliationStatus


NOW = datetime(2026, 7, 15, 18, 0, tzinfo=UTC)


def compare(local, external):
    return InMemoryReconciliationService().compare(local, external, tolerance=Decimal("0"), checked_at_utc=NOW, local_reference="ledger:1", external_reference="fake-broker:1")


def test_equal_values_match():
    assert compare({"cash": Decimal("10")}, {"cash": Decimal("10")}).status is ReconciliationStatus.MATCHED


def test_different_values_report_mismatch_without_correction():
    local = {"cash": Decimal("10")}
    external = {"cash": Decimal("12")}
    result = compare(local, external)
    assert result.status is ReconciliationStatus.MISMATCH
    assert result.differences[0].difference == Decimal("-2")
    assert local["cash"] == Decimal("10") and external["cash"] == Decimal("12")
