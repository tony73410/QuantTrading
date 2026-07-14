from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from conftest import make_bar, make_request
from quant_trading.application_settings import (
    ApplicationRoleSettings,
    BrokerageType,
    ExecutionEnvironment,
    ExecutionMode,
    MarketDataProviderType,
)
from quant_trading.market_history.config import AppSettings
from quant_trading.market_history.errors import DataValidationError, RequestValidationError
from quant_trading.market_history.models import Timeframe, validate_market_bars


def test_request_normalizes_symbol_and_utc_offset():
    request = make_request(
        symbol=" aapl ",
        start=datetime.fromisoformat("2024-01-01T08:00:00+08:00"),
        end=datetime.fromisoformat("2024-01-02T08:00:00+08:00"),
    )
    assert request.symbol == "AAPL"
    assert request.start_time == datetime(2024, 1, 1, tzinfo=UTC)


@pytest.mark.parametrize("symbol", ["aapl", " AAPL", "AAPL ", "BRK.B"])
def test_supported_symbol_formats_are_normalized(symbol):
    request = make_request(symbol=symbol)
    assert request.symbol == symbol.strip().upper()


@pytest.mark.parametrize(
    "changes",
    [
        {"symbol": ""},
        {"symbol": "not a symbol!"},
        {"symbol": "A" * 16},
        {"start": datetime(2024, 1, 2), "end": datetime(2024, 1, 3)},
        {
            "start": datetime(2024, 1, 3, tzinfo=UTC),
            "end": datetime(2024, 1, 2, tzinfo=UTC),
        },
        {
            "start": datetime.now(UTC),
            "end": datetime.now(UTC) + timedelta(days=2),
        },
    ],
)
def test_invalid_requests_are_rejected(changes):
    with pytest.raises(RequestValidationError):
        make_request(**changes)


@pytest.mark.parametrize(
    ("timeframe", "expected_duration"),
    [
        (Timeframe.TEN_MINUTES, timedelta(minutes=10)),
        (Timeframe.THIRTY_MINUTES, timedelta(minutes=30)),
        (Timeframe.HOUR, timedelta(hours=1)),
    ],
)
def test_intraday_timeframes_have_explicit_durations(timeframe, expected_duration):
    assert timeframe.is_intraday is True
    assert timeframe.approximate_duration == expected_duration


@pytest.mark.parametrize(
    ("timeframe", "days"),
    [
        (Timeframe.TEN_MINUTES, 367),
        (Timeframe.THIRTY_MINUTES, 1_831),
        (Timeframe.HOUR, 1_831),
    ],
)
def test_oversized_intraday_requests_are_rejected(timeframe, days):
    with pytest.raises(RequestValidationError) as captured:
        make_request(
            start=datetime(2020, 1, 1, tzinfo=UTC),
            end=datetime(2020, 1, 1, tzinfo=UTC) + timedelta(days=days),
            timeframe=timeframe,
        )

    assert "数据量较大" in captured.value.user_message
    assert "缩短日期范围" in captured.value.recovery_message


@pytest.mark.parametrize(
    "mutator",
    [
        lambda bar: replace(bar, high=Decimal("98")),
        lambda bar: replace(bar, open=Decimal("110")),
        lambda bar: replace(bar, close=Decimal("110")),
        lambda bar: replace(bar, volume=-1),
        lambda bar: replace(bar, close=Decimal("NaN")),
    ],
)
def test_invalid_market_values_are_rejected(mutator):
    request = make_request()
    bar = make_bar(datetime(2024, 1, 2, tzinfo=UTC), request=request)
    with pytest.raises(DataValidationError):
        validate_market_bars([mutator(bar)], request)


def test_duplicate_market_bar_is_rejected():
    request = make_request()
    bar = make_bar(datetime(2024, 1, 2, tzinfo=UTC), request=request)
    with pytest.raises(DataValidationError):
        validate_market_bars([bar, bar], request)


def test_environment_configures_cache_without_credentials(monkeypatch, tmp_path):
    monkeypatch.delenv("APCA_API_KEY_ID", raising=False)
    monkeypatch.delenv("APCA_API_SECRET_KEY", raising=False)
    monkeypatch.setenv("MARKET_HISTORY_CACHE_MAX_AGE_HOURS", "12")
    monkeypatch.setenv("MARKET_HISTORY_OVERLAP_BARS", "7")
    monkeypatch.setenv("MARKET_HISTORY_AUTO_REFRESH_MINUTES", "10")
    settings = AppSettings.from_environment(tmp_path)
    assert settings.market_data_credentials_available is False
    assert settings.roles.market_data_provider is MarketDataProviderType.ALPACA
    assert settings.roles.primary_brokerage is BrokerageType.ALPACA
    assert (
        settings.roles.execution_environment
        is ExecutionEnvironment.ALPACA_PAPER
    )
    assert settings.roles.automatic_order_submission is False
    assert settings.roles.paper_trading_enabled is True
    assert settings.roles.live_trading_enabled is False
    assert settings.roles.require_manual_confirmation is True
    assert settings.cache_policy.max_age == timedelta(hours=12)
    assert settings.cache_policy.overlap_bars == 7
    assert settings.cache_policy.auto_refresh_interval == timedelta(minutes=10)
    assert settings.database_path == tmp_path / "runtime" / "data" / "market_history.sqlite3"
    assert settings.runtime_log_path == tmp_path / "runtime" / "logs" / "app.log"
    assert settings.error_log_path == tmp_path / "runtime" / "logs" / "error.log"
    assert settings.debug_mode is False
    assert settings.log_level == "INFO"


def test_debug_logging_configuration_does_not_change_trading_safety(
    monkeypatch, tmp_path
):
    monkeypatch.setenv("QUANT_TRADE_DEBUG", "true")
    monkeypatch.setenv("QUANT_TRADE_LOG_LEVEL", "DEBUG")
    settings = AppSettings.from_environment(tmp_path)
    assert settings.debug_mode is True
    assert settings.log_level == "DEBUG"
    assert settings.roles.live_trading_enabled is False
    assert settings.roles.automatic_order_submission is False


def test_fidelity_credentials_are_not_required_or_read(monkeypatch, tmp_path):
    monkeypatch.setenv("FIDELITY_USERNAME", "must-not-be-read")
    monkeypatch.setenv("FIDELITY_PASSWORD", "must-not-be-read")
    settings = AppSettings.from_environment(tmp_path)
    assert not hasattr(settings, "fidelity_username")
    assert not hasattr(settings, "fidelity_password")


def test_market_data_credentials_do_not_enable_order_submission(
    monkeypatch, tmp_path
):
    monkeypatch.setenv("APCA_API_KEY_ID", "fake-market-data-key")
    monkeypatch.setenv("APCA_API_SECRET_KEY", "fake-market-data-secret")
    settings = AppSettings.from_environment(tmp_path)
    assert settings.market_data_credentials_available is True
    assert settings.roles.automatic_order_submission is False
    assert settings.roles.live_trading_enabled is False
    assert settings.roles.require_manual_confirmation is True


def test_paper_and_live_environments_cannot_be_mixed():
    with pytest.raises(ValueError):
        ApplicationRoleSettings(live_trading_enabled=True)
    with pytest.raises(ValueError):
        ApplicationRoleSettings(
            execution_environment=ExecutionEnvironment.ALPACA_LIVE,
        )


def test_fidelity_manual_environment_is_retained_but_not_default():
    optional_fidelity = ApplicationRoleSettings(
        primary_brokerage=BrokerageType.FIDELITY,
        execution_environment=ExecutionEnvironment.MANUAL_FIDELITY,
        paper_trading_enabled=False,
    )
    assert optional_fidelity.execution_environment is ExecutionMode.MANUAL_FIDELITY
    assert optional_fidelity.execution_mode is ExecutionMode.MANUAL_FIDELITY
    assert ApplicationRoleSettings().primary_brokerage is BrokerageType.ALPACA


def test_invalid_optional_cache_config_falls_back_to_safe_defaults(monkeypatch, tmp_path):
    monkeypatch.setenv("MARKET_HISTORY_OVERLAP_BARS", "0")
    monkeypatch.setenv("MARKET_HISTORY_AUTO_REFRESH_MINUTES", "not-a-number")
    settings = AppSettings.from_environment(tmp_path)
    assert settings.cache_policy.overlap_bars == 5
    assert settings.cache_policy.auto_refresh_interval == timedelta(minutes=5)
