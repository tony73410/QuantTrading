"""Session/request context, redacted rotating logs, and exception hooks."""

from __future__ import annotations

import contextlib
import contextvars
import logging
import re
import sys
import threading
import time
import uuid
from collections.abc import Iterable, Iterator, Mapping
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from .error_codes import ErrorCode
from .errors import QuantTradeError


_session_id: contextvars.ContextVar[str] = contextvars.ContextVar(
    "quant_trade_session_id", default="-"
)
_request_id: contextvars.ContextVar[str] = contextvars.ContextVar(
    "quant_trade_request_id", default="-"
)
_operation: contextvars.ContextVar[str] = contextvars.ContextVar(
    "quant_trade_operation", default="-"
)


def new_session_id() -> str:
    return f"SES-{uuid.uuid4().hex[:12].upper()}"


def new_request_id() -> str:
    return f"REQ-{uuid.uuid4().hex[:12].upper()}"


def set_session_id(session_id: str) -> None:
    _session_id.set(session_id)


def current_session_id() -> str:
    return _session_id.get()


def current_request_id() -> str:
    return _request_id.get()


@contextlib.contextmanager
def session_context(session_id: str) -> Iterator[None]:
    token = _session_id.set(session_id)
    try:
        yield
    finally:
        _session_id.reset(token)


@contextlib.contextmanager
def request_context(request_id: str, operation: str) -> Iterator[None]:
    request_token = _request_id.set(request_id)
    operation_token = _operation.set(operation)
    try:
        yield
    finally:
        _operation.reset(operation_token)
        _request_id.reset(request_token)


_SENSITIVE_PATTERNS = (
    re.compile(r"(?i)(authorization\s*[:=]\s*)(?:bearer\s+)?[^\s,;]+"),
    re.compile(r"(?i)((?:api[_-]?secret|secret[_-]?key|password|token)\s*[:=]\s*)[^\s,;]+"),
    re.compile(r"\b(?:PK|AK)[A-Z0-9]{8,}\b"),
)


def redact_text(value: object, secrets: Iterable[str] = ()) -> str:
    text = str(value)
    for secret in secrets:
        if secret and len(secret) >= 4:
            text = text.replace(secret, "***REDACTED***")
    for pattern in _SENSITIVE_PATTERNS:
        text = pattern.sub(lambda match: match.group(1) + "***REDACTED***" if match.lastindex else "***REDACTED***", text)
    return text


class _ContextFilter(logging.Filter):
    _defaults = {
        "error_code": "-",
        "symbol": "-",
        "timeframe": "-",
        "date_range": "-",
        "adjustment": "-",
        "feed": "-",
        "environment": "alpaca_paper",
        "exception_type": "-",
    }

    def filter(self, record: logging.LogRecord) -> bool:
        record.session_id = getattr(record, "session_id", current_session_id())
        record.request_id = getattr(record, "request_id", current_request_id())
        record.operation = getattr(record, "operation", _operation.get())
        for name, value in self._defaults.items():
            if not hasattr(record, name):
                setattr(record, name, value)
        return True


class _UTCFormatter(logging.Formatter):
    converter = time.gmtime


class RedactingFormatter(_UTCFormatter):
    def __init__(self, *args: Any, secrets: Iterable[str] = (), **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._secrets = tuple(secret for secret in secrets if secret)

    def format(self, record: logging.LogRecord) -> str:
        return redact_text(super().format(record), self._secrets)


_LOG_FORMAT = (
    "%(asctime)sZ level=%(levelname)s session_id=%(session_id)s "
    "request_id=%(request_id)s error_code=%(error_code)s "
    "module=%(name)s function=%(funcName)s operation=%(operation)s "
    "symbol=%(symbol)s timeframe=%(timeframe)s date_range=%(date_range)s "
    "adjustment=%(adjustment)s feed=%(feed)s environment=%(environment)s "
    "exception_type=%(exception_type)s message=\"%(message)s\""
)


def configure_logging(
    log_directory: Path,
    *,
    log_level: str = "INFO",
    session_id: str | None = None,
    secrets: Iterable[str] = (),
) -> str:
    """Configure app.log and error.log without duplicating prior handlers."""

    active_session_id = session_id or new_session_id()
    set_session_id(active_session_id)
    log_directory.mkdir(parents=True, exist_ok=True)
    root_logger = logging.getLogger()
    for handler in list(root_logger.handlers):
        if getattr(handler, "_quant_trade_handler", False):
            root_logger.removeHandler(handler)
            handler.close()

    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    root_logger.setLevel(min(numeric_level, logging.WARNING))
    context_filter = _ContextFilter()
    formatter = RedactingFormatter(
        _LOG_FORMAT,
        datefmt="%Y-%m-%dT%H:%M:%S",
        secrets=secrets,
    )
    for filename, level in (("app.log", numeric_level), ("error.log", logging.WARNING)):
        handler = RotatingFileHandler(
            log_directory / filename,
            maxBytes=5_000_000,
            backupCount=5,
            encoding="utf-8",
        )
        handler.setLevel(level)
        handler.setFormatter(formatter)
        handler.addFilter(context_filter)
        handler._quant_trade_handler = True  # type: ignore[attr-defined]
        root_logger.addHandler(handler)
    return active_session_id


def _exception_extra(
    exc: BaseException,
    *,
    error_code: ErrorCode | None = None,
    context: Mapping[str, object] | None = None,
) -> dict[str, object]:
    code = error_code
    if code is None and isinstance(exc, QuantTradeError):
        code = exc.error_code
    extra: dict[str, object] = {
        "error_code": (code or ErrorCode.UNKNOWN).value,
        "exception_type": type(exc).__name__,
    }
    if isinstance(exc, QuantTradeError):
        extra.update(exc.context)
    if context:
        extra.update(context)
    return extra


def log_exception(
    logger: logging.Logger,
    exc: BaseException,
    *,
    message: str,
    error_code: ErrorCode | None = None,
    context: Mapping[str, object] | None = None,
    level: int = logging.ERROR,
) -> None:
    logger.log(
        level,
        message,
        exc_info=(type(exc), exc, exc.__traceback__),
        extra=_exception_extra(exc, error_code=error_code, context=context),
    )


def install_exception_hooks(logger: logging.Logger | None = None) -> None:
    target = logger or logging.getLogger("quant_trading.unhandled")

    def handle_main(
        exc_type: type[BaseException],
        exc: BaseException,
        traceback: object,
    ) -> None:
        target.critical(
            "Unhandled main-thread exception",
            exc_info=(exc_type, exc, traceback),
            extra=_exception_extra(exc),
        )

    def handle_thread(args: threading.ExceptHookArgs) -> None:
        target.critical(
            "Unhandled background-thread exception",
            exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
            extra=_exception_extra(args.exc_value, error_code=ErrorCode.BACKGROUND_TASK),
        )

    sys.excepthook = handle_main
    threading.excepthook = handle_thread
