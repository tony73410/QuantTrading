"""Read-only health checks for the local QuantTrade installation."""

from __future__ import annotations

import argparse
import platform
import sqlite3
import sys
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from .market_history.config import AppSettings
from .market_history.models import Adjustment, DataFeed, HistoricalDataRequest, Timeframe
from .market_history.providers import AlpacaHistoricalMarketDataProvider
from .persistence.sqlite_database import SCHEMA_VERSION, inspect_central_schema
from .error_codes import ErrorCode
from .validation import (
    HealthCheckResult,
    HealthStatus,
    ValidationIssue,
    ValidationResult,
    ValidationSeverity,
)


class DiagnosticStatus(str, Enum):
    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"
    SKIPPED = "SKIPPED"


@dataclass(frozen=True, slots=True)
class DiagnosticResult:
    name: str
    status: DiagnosticStatus
    message: str


_DEPENDENCIES = ("PySide6", "plotly", "pandas", "alpaca-py")
def _dependency_checks() -> list[DiagnosticResult]:
    results: list[DiagnosticResult] = []
    for package in _DEPENDENCIES:
        try:
            installed = version(package)
        except PackageNotFoundError:
            results.append(
                DiagnosticResult(package, DiagnosticStatus.FAIL, "not installed")
            )
        else:
            results.append(
                DiagnosticResult(package, DiagnosticStatus.PASS, installed)
            )
    return results


def _directory_check(path: Path, name: str) -> DiagnosticResult:
    try:
        path.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=path, prefix="diagnostic-", delete=True):
            pass
    except OSError as exc:
        return DiagnosticResult(name, DiagnosticStatus.FAIL, type(exc).__name__)
    return DiagnosticResult(name, DiagnosticStatus.PASS, f"writable: {path}")


def _database_checks(path: Path) -> list[DiagnosticResult]:
    if not path.exists():
        return [
            DiagnosticResult(
                "sqlite_database",
                DiagnosticStatus.WARNING,
                f"not created yet: {path}",
            )
        ]
    try:
        uri = f"file:{path.as_posix()}?mode=ro"
        with sqlite3.connect(uri, uri=True, timeout=5) as connection:
            integrity = connection.execute("PRAGMA quick_check").fetchone()[0]
            foreign_key_errors = connection.execute(
                "PRAGMA foreign_key_check"
            ).fetchall()
            schema = inspect_central_schema(connection)
    except sqlite3.Error as exc:
        return [
            DiagnosticResult(
                "sqlite_database",
                DiagnosticStatus.FAIL,
                f"{type(exc).__name__}: {exc}",
            )
        ]
    schema_problems: list[str] = []
    if schema.applied_versions != schema.expected_versions:
        schema_problems.append(
            f"migration versions {schema.applied_versions}; "
            f"expected 1..{SCHEMA_VERSION}"
        )
    if schema.missing_tables:
        missing = sorted(schema.missing_tables)
        schema_problems.append(
            f"missing tables ({len(missing)}): {', '.join(missing)}"
        )
    return [
        DiagnosticResult(
            "sqlite_connection",
            DiagnosticStatus.PASS,
            f"read-only connection succeeded: {path}",
        ),
        DiagnosticResult(
            "sqlite_schema",
            DiagnosticStatus.FAIL if schema_problems else DiagnosticStatus.PASS,
            "; ".join(schema_problems)
            if schema_problems
            else f"central_sqlite_v{schema.current_version}; tables={len(schema.actual_tables)}",
        ),
        DiagnosticResult(
            "sqlite_integrity",
            DiagnosticStatus.PASS if integrity == "ok" else DiagnosticStatus.FAIL,
            str(integrity),
        ),
        DiagnosticResult(
            "sqlite_foreign_keys",
            DiagnosticStatus.FAIL if foreign_key_errors else DiagnosticStatus.PASS,
            f"{len(foreign_key_errors)} violation(s)"
            if foreign_key_errors
            else "ok",
        ),
    ]


def _credential_check(settings: AppSettings) -> DiagnosticResult:
    key_present = bool(settings.alpaca_market_data_api_key)
    secret_present = bool(settings.alpaca_market_data_secret_key)
    if key_present and secret_present:
        return DiagnosticResult(
            "alpaca_market_data_credentials",
            DiagnosticStatus.PASS,
            "both variables are present (values hidden)",
        )
    if key_present or secret_present:
        return DiagnosticResult(
            "alpaca_market_data_credentials",
            DiagnosticStatus.WARNING,
            "configuration is incomplete; values hidden",
        )
    return DiagnosticResult(
        "alpaca_market_data_credentials",
        DiagnosticStatus.WARNING,
        "not configured; local-cache mode remains available",
    )


def _network_checks(settings: AppSettings, enabled: bool) -> list[DiagnosticResult]:
    if not enabled:
        return [
            DiagnosticResult(
                "alpaca_market_data_connection",
                DiagnosticStatus.SKIPPED,
                "use --network to perform an optional read-only request",
            )
        ]
    if not settings.market_data_credentials_available:
        return [
            DiagnosticResult(
                "alpaca_market_data_connection",
                DiagnosticStatus.SKIPPED,
                "credentials are incomplete or missing",
            )
        ]
    now = datetime.now(UTC)
    request = HistoricalDataRequest(
        symbol="AAPL",
        start_time=now - timedelta(days=7),
        end_time=now,
        timeframe=Timeframe.DAY,
        adjustment=Adjustment.RAW,
        feed=DataFeed.IEX,
    )
    provider = AlpacaHistoricalMarketDataProvider(
        settings.alpaca_market_data_api_key,
        settings.alpaca_market_data_secret_key,
        max_attempts=1,
    )
    try:
        bars = provider.fetch_bars(request)
    except Exception as exc:
        error_code = getattr(getattr(exc, "error_code", None), "value", "unknown")
        return [
            DiagnosticResult(
                "alpaca_market_data_connection",
                DiagnosticStatus.FAIL,
                f"{error_code} {type(exc).__name__}",
            )
        ]
    return [
        DiagnosticResult(
            "alpaca_market_data_connection",
            DiagnosticStatus.PASS,
            f"read-only AAPL request succeeded; rows={len(bars)}",
        )
    ]


def run_diagnostics(
    *,
    project_root: Path | None = None,
    include_network: bool = False,
) -> list[DiagnosticResult]:
    root = (project_root or Path.cwd()).resolve()
    settings = AppSettings.from_environment(root)
    results = [
        DiagnosticResult("operating_system", DiagnosticStatus.PASS, platform.platform()),
        DiagnosticResult("python", DiagnosticStatus.PASS, sys.version.split()[0]),
        DiagnosticResult(
            "virtual_environment",
            DiagnosticStatus.PASS if sys.prefix != sys.base_prefix else DiagnosticStatus.WARNING,
            sys.executable,
        ),
        DiagnosticResult("configuration_source", DiagnosticStatus.PASS, "environment variables"),
    ]
    results.extend(_dependency_checks())
    results.append(_directory_check(root / "runtime" / "data", "runtime_data_directory"))
    results.append(_directory_check(root / "runtime" / "logs", "runtime_log_directory"))
    results.extend(_database_checks(settings.database_path))
    results.append(_credential_check(settings))
    safe_roles = (
        settings.roles.execution_environment.value == "alpaca_paper"
        and not settings.roles.live_trading_enabled
        and not settings.roles.automatic_order_submission
    )
    results.append(
        DiagnosticResult(
            "trading_safety",
            DiagnosticStatus.PASS if safe_roles else DiagnosticStatus.FAIL,
            "environment=alpaca_paper live=false automatic_submission=false",
        )
    )
    results.extend(_network_checks(settings, include_network))
    return results


def summarize_diagnostics(results: list[DiagnosticResult]) -> HealthCheckResult:
    """Translate existing read-only checks into the unified health contract."""

    validation_results: list[ValidationResult] = []
    incomplete = False
    for result in results:
        if result.status is DiagnosticStatus.PASS:
            issues: tuple[ValidationIssue, ...] = ()
        else:
            if result.status is DiagnosticStatus.SKIPPED:
                incomplete = True
                severity = ValidationSeverity.INFO
            elif result.status is DiagnosticStatus.WARNING:
                severity = ValidationSeverity.WARNING
            else:
                severity = ValidationSeverity.BLOCKING
            issues = (ValidationIssue(
                ErrorCode.INTEGRITY_VALIDATION,
                severity,
                "diagnostics",
                result.name,
                result.message,
                suggested_action="Review this check before enabling any execution path.",
            ),)
        validation_results.append(
            ValidationResult.from_issues(result.name, "diagnostics", issues)
        )
    statuses = {item.status for item in validation_results}
    if any(status is DiagnosticStatus.FAIL for status in (item.status for item in results)):
        health = HealthStatus.BLOCKED
    elif incomplete:
        health = HealthStatus.UNKNOWN
    elif any(status.value == "warning" for status in statuses):
        health = HealthStatus.DEGRADED
    else:
        health = HealthStatus.HEALTHY
    return HealthCheckResult(health, tuple(validation_results))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run read-only QuantTrade diagnostics")
    parser.add_argument(
        "--network",
        action="store_true",
        help="perform one optional read-only Alpaca Market Data request",
    )
    args = parser.parse_args(argv)
    results = run_diagnostics(include_network=args.network)
    for result in results:
        print(f"{result.status.value:<7} {result.name}: {result.message}")
    health = summarize_diagnostics(results)
    print(f"SYSTEM_HEALTH {health.status.value.upper()} automatic_execution_allowed={str(health.allows_automatic_execution).lower()}")
    return 1 if any(result.status is DiagnosticStatus.FAIL for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
