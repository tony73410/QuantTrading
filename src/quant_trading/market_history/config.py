"""Environment and filesystem settings without market-data business logic."""

from __future__ import annotations

import os
import logging
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

from quant_trading.application_settings import ApplicationRoleSettings

from .models import CachePolicy


logger = logging.getLogger(__name__)


def _boolean_environment(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    normalized = raw.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    logger.warning("Ignoring invalid boolean configuration value name=%s", name)
    return default


def _log_level_environment() -> str:
    value = (os.getenv("QUANT_TRADE_LOG_LEVEL") or "INFO").strip().upper()
    if value not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
        logger.warning("Ignoring invalid log level value")
        return "INFO"
    return value


def _positive_int_environment(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError:
        logger.warning("Ignoring non-integer configuration value name=%s", name)
        return default
    if value < 1:
        logger.warning("Ignoring non-positive configuration value name=%s", name)
        return default
    return value


@dataclass(frozen=True, slots=True)
class AppSettings:
    project_root: Path
    database_path: Path
    runtime_log_path: Path
    alpaca_market_data_api_key: str | None
    alpaca_market_data_secret_key: str | None
    cache_policy: CachePolicy = CachePolicy()
    roles: ApplicationRoleSettings = ApplicationRoleSettings()
    debug_mode: bool = False
    log_level: str = "INFO"

    @property
    def error_log_path(self) -> Path:
        return self.runtime_log_path.with_name("error.log")

    @property
    def market_data_credentials_available(self) -> bool:
        return bool(
            self.alpaca_market_data_api_key
            and self.alpaca_market_data_secret_key
        )

    @classmethod
    def from_environment(cls, project_root: Path | None = None) -> "AppSettings":
        root = (project_root or Path.cwd()).resolve()
        cache_policy = CachePolicy(
            max_age=timedelta(
                hours=_positive_int_environment("MARKET_HISTORY_CACHE_MAX_AGE_HOURS", 24)
            ),
            overlap_bars=_positive_int_environment("MARKET_HISTORY_OVERLAP_BARS", 5),
            auto_refresh_interval=timedelta(
                minutes=_positive_int_environment("MARKET_HISTORY_AUTO_REFRESH_MINUTES", 5)
            ),
        )
        return cls(
            project_root=root,
            database_path=root / "runtime" / "data" / "market_history.sqlite3",
            runtime_log_path=root / "runtime" / "logs" / "app.log",
            alpaca_market_data_api_key=os.getenv("APCA_API_KEY_ID") or None,
            alpaca_market_data_secret_key=os.getenv("APCA_API_SECRET_KEY") or None,
            cache_policy=cache_policy,
            debug_mode=_boolean_environment("QUANT_TRADE_DEBUG", False),
            log_level=_log_level_environment(),
        )
