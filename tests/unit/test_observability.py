from __future__ import annotations

import logging
import sys
import threading

from quant_trading.error_codes import ErrorCode
from quant_trading.observability import (
    configure_logging,
    install_exception_hooks,
    request_context,
)


def _close_quant_trade_handlers() -> None:
    root = logging.getLogger()
    for handler in list(root.handlers):
        if getattr(handler, "_quant_trade_handler", False):
            root.removeHandler(handler)
            handler.close()


def test_rotating_logs_are_idempotent_contextual_and_redacted(tmp_path):
    secret = "super-secret-value-123"
    try:
        configure_logging(
            tmp_path,
            session_id="SES-TEST",
            log_level="DEBUG",
            secrets=(secret,),
        )
        configure_logging(
            tmp_path,
            session_id="SES-TEST",
            log_level="DEBUG",
            secrets=(secret,),
        )
        handlers = [
            handler
            for handler in logging.getLogger().handlers
            if getattr(handler, "_quant_trade_handler", False)
        ]
        assert len(handlers) == 2

        with request_context("REQ-TEST", "fetch_bars"):
            logging.getLogger("test.observability").warning(
                "Authorization: Bearer %s secret=%s",
                secret,
                secret,
                extra={"error_code": ErrorCode.MARKET_DATA_TIMEOUT.value},
            )
        for handler in handlers:
            handler.flush()

        app_log = (tmp_path / "app.log").read_text(encoding="utf-8")
        error_log = (tmp_path / "error.log").read_text(encoding="utf-8")
        for content in (app_log, error_log):
            assert "session_id=SES-TEST" in content
            assert "request_id=REQ-TEST" in content
            assert "error_code=QT-API-002" in content
            assert "operation=fetch_bars" in content
            assert secret not in content
            assert "***REDACTED***" in content
    finally:
        _close_quant_trade_handlers()


def test_unhandled_exception_hook_writes_error_code_and_stack(tmp_path):
    original_hook = sys.excepthook
    original_thread_hook = threading.excepthook
    try:
        configure_logging(tmp_path, session_id="SES-HOOK")
        install_exception_hooks()
        try:
            raise RuntimeError("hook failure")
        except RuntimeError as exc:
            sys.excepthook(type(exc), exc, exc.__traceback__)
        for handler in logging.getLogger().handlers:
            if getattr(handler, "_quant_trade_handler", False):
                handler.flush()

        error_log = (tmp_path / "error.log").read_text(encoding="utf-8")
        assert "error_code=QT-UNKNOWN-001" in error_log
        assert "RuntimeError: hook failure" in error_log
        assert "Unhandled main-thread exception" in error_log
    finally:
        sys.excepthook = original_hook
        threading.excepthook = original_thread_hook
        _close_quant_trade_handlers()
