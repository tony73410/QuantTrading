"""Desktop application composition root and runtime logging setup."""

from __future__ import annotations

import sys
import logging

from PySide6.QtWidgets import QApplication

from quant_trading.observability import (
    configure_logging,
    install_exception_hooks,
    new_session_id,
)

from .charts import PlotlyChartBuilder
from .config import AppSettings
from .controller import HistoryController
from .providers import AlpacaHistoricalMarketDataProvider
from .service import HistoricalDataService
from .storage import SQLiteHistoricalDataStore
from .ui import HistoryPanel


logger = logging.getLogger(__name__)


def configure_runtime_logging(
    settings: AppSettings, *, session_id: str | None = None
) -> str:
    return configure_logging(
        settings.runtime_log_path.parent,
        log_level="DEBUG" if settings.debug_mode else settings.log_level,
        session_id=session_id,
        secrets=(
            settings.alpaca_market_data_api_key or "",
            settings.alpaca_market_data_secret_key or "",
        ),
    )


def build_controller(settings: AppSettings) -> HistoryController:
    store = SQLiteHistoricalDataStore(settings.database_path)
    store.initialize()
    provider = AlpacaHistoricalMarketDataProvider(
        settings.alpaca_market_data_api_key,
        settings.alpaca_market_data_secret_key,
    )
    service = HistoricalDataService(store, provider, settings.cache_policy)
    return HistoryController(service, PlotlyChartBuilder())


def main() -> int:
    settings = AppSettings.from_environment()
    session_id = configure_runtime_logging(settings, session_id=new_session_id())
    install_exception_hooks()
    logger.info(
        "Application starting",
        extra={
            "operation": "application_start",
            "environment": settings.roles.execution_environment.value,
        },
    )
    logger.info(
        "Configuration loaded credentials_complete=%s debug_mode=%s log_level=%s",
        settings.market_data_credentials_available,
        settings.debug_mode,
        settings.log_level,
        extra={
            "operation": "configuration_load",
            "environment": settings.roles.execution_environment.value,
        },
    )
    application = QApplication(sys.argv)
    application.setApplicationName("股票历史数据浏览器")
    application.aboutToQuit.connect(
        lambda: logger.info(
            "Application closing",
            extra={
                "operation": "application_close",
                "environment": settings.roles.execution_environment.value,
            },
        )
    )
    panel = HistoryPanel(
        build_controller(settings),
        market_data_credentials_available=settings.market_data_credentials_available,
        role_settings=settings.roles,
        auto_refresh_interval_ms=int(
            settings.cache_policy.auto_refresh_interval.total_seconds() * 1000
        ),
    )
    logger.info(
        "GUI ready",
        extra={"operation": "gui_ready", "session_id": session_id},
    )
    panel.show()
    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())
