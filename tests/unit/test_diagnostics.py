from __future__ import annotations

from quant_trading.diagnostics import DiagnosticStatus, run_diagnostics
from quant_trading.market_history.storage import SQLiteHistoricalDataStore


def test_diagnostics_are_read_only_safe_and_skip_network_by_default(
    tmp_path, monkeypatch
):
    monkeypatch.delenv("APCA_API_KEY_ID", raising=False)
    monkeypatch.delenv("APCA_API_SECRET_KEY", raising=False)
    database_path = tmp_path / "runtime" / "data" / "market_history.sqlite3"
    store = SQLiteHistoricalDataStore(database_path)
    store.initialize()

    results = run_diagnostics(project_root=tmp_path)
    by_name = {result.name: result for result in results}

    assert by_name["sqlite_connection"].status is DiagnosticStatus.PASS
    assert by_name["sqlite_schema"].message == "market_history_v1"
    assert by_name["sqlite_integrity"].status is DiagnosticStatus.PASS
    assert by_name["alpaca_market_data_credentials"].status is DiagnosticStatus.WARNING
    assert by_name["alpaca_market_data_connection"].status is DiagnosticStatus.SKIPPED
    assert by_name["trading_safety"].status is DiagnosticStatus.PASS


def test_diagnostics_detect_incomplete_credentials_without_showing_values(
    tmp_path, monkeypatch
):
    secret_value = "must-never-be-printed"
    monkeypatch.setenv("APCA_API_KEY_ID", secret_value)
    monkeypatch.delenv("APCA_API_SECRET_KEY", raising=False)

    results = run_diagnostics(project_root=tmp_path)
    credential = next(
        result for result in results
        if result.name == "alpaca_market_data_credentials"
    )

    assert credential.status is DiagnosticStatus.WARNING
    assert "incomplete" in credential.message
    assert secret_value not in credential.message
