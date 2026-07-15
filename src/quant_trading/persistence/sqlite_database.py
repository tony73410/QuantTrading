"""Central SQLite file management without feature-specific query logic."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path


SCHEMA_VERSION = 1


_SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at_utc TEXT NOT NULL,
    description TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS market_bars (
    symbol TEXT NOT NULL,
    timestamp_utc TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    adjustment TEXT NOT NULL,
    feed TEXT NOT NULL,
    open TEXT NOT NULL,
    high TEXT NOT NULL,
    low TEXT NOT NULL,
    close TEXT NOT NULL,
    volume INTEGER NOT NULL CHECK (volume >= 0),
    vwap TEXT,
    trade_count INTEGER CHECK (trade_count IS NULL OR trade_count >= 0),
    source TEXT NOT NULL,
    fetched_at_utc TEXT NOT NULL,
    PRIMARY KEY (symbol, timestamp_utc, timeframe, adjustment, feed)
);

CREATE INDEX IF NOT EXISTS idx_market_bars_lookup
ON market_bars (symbol, timeframe, adjustment, feed, timestamp_utc);

CREATE TABLE IF NOT EXISTS data_coverage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    adjustment TEXT NOT NULL,
    feed TEXT NOT NULL,
    coverage_start_utc TEXT NOT NULL,
    coverage_end_utc TEXT NOT NULL,
    last_successful_fetch_utc TEXT NOT NULL,
    CHECK (coverage_start_utc < coverage_end_utc),
    UNIQUE (
        symbol, timeframe, adjustment, feed,
        coverage_start_utc, coverage_end_utc
    )
);

CREATE INDEX IF NOT EXISTS idx_data_coverage_lookup
ON data_coverage (
    symbol, timeframe, adjustment, feed,
    coverage_start_utc, coverage_end_utc
);

CREATE TABLE IF NOT EXISTS fetch_history (
    request_id TEXT PRIMARY KEY,
    symbol TEXT NOT NULL,
    requested_start_utc TEXT NOT NULL,
    requested_end_utc TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    adjustment TEXT NOT NULL,
    feed TEXT NOT NULL,
    started_at_utc TEXT NOT NULL,
    completed_at_utc TEXT,
    status TEXT NOT NULL,
    rows_received INTEGER NOT NULL DEFAULT 0,
    error_summary TEXT
);

CREATE INDEX IF NOT EXISTS idx_fetch_history_lookup
ON fetch_history (symbol, timeframe, adjustment, feed, started_at_utc);

CREATE TABLE IF NOT EXISTS factor_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    symbol TEXT NOT NULL,
    as_of_utc TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    adjustment TEXT NOT NULL,
    feed TEXT NOT NULL,
    calculated_at_utc TEXT NOT NULL,
    source_data_start_utc TEXT,
    source_data_end_utc TEXT,
    configuration_fingerprint TEXT NOT NULL,
    source_data_fingerprint TEXT NOT NULL,
    content_fingerprint TEXT NOT NULL UNIQUE,
    schema_version INTEGER NOT NULL,
    created_at_utc TEXT NOT NULL,
    CHECK (
        (source_data_start_utc IS NULL AND source_data_end_utc IS NULL)
        OR
        (source_data_start_utc IS NOT NULL AND source_data_end_utc IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_factor_snapshots_lookup
ON factor_snapshots (
    symbol, timeframe, adjustment, feed, as_of_utc
);

CREATE TABLE IF NOT EXISTS factor_results (
    snapshot_id TEXT NOT NULL,
    factor_name TEXT NOT NULL,
    factor_version TEXT NOT NULL,
    value_type TEXT,
    value_text TEXT,
    unit TEXT,
    parameters_json TEXT NOT NULL,
    lookback INTEGER,
    status TEXT NOT NULL,
    quality_flags_json TEXT NOT NULL,
    calculated_at_utc TEXT NOT NULL,
    source_data_start_utc TEXT,
    source_data_end_utc TEXT,
    PRIMARY KEY (snapshot_id, factor_name),
    FOREIGN KEY (snapshot_id) REFERENCES factor_snapshots(snapshot_id)
        ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_factor_results_lookup
ON factor_results (factor_name, factor_version, snapshot_id);

CREATE TABLE IF NOT EXISTS factor_calculation_runs (
    run_id TEXT PRIMARY KEY,
    correlation_id TEXT,
    symbol TEXT NOT NULL,
    as_of_utc TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    adjustment TEXT NOT NULL,
    feed TEXT NOT NULL,
    started_at_utc TEXT NOT NULL,
    completed_at_utc TEXT,
    status TEXT NOT NULL,
    snapshot_id TEXT,
    error_code TEXT,
    error_summary TEXT,
    FOREIGN KEY (snapshot_id) REFERENCES factor_snapshots(snapshot_id)
        ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_factor_calculation_runs_lookup
ON factor_calculation_runs (symbol, timeframe, adjustment, feed, as_of_utc);
"""


class CentralSQLiteDatabase:
    """Own connections and idempotent schema initialization for one local file."""

    def __init__(self, database_path: Path | str) -> None:
        self.database_path = Path(database_path)

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=30.0)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 30000")
        return connection

    def initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self.connect()) as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.execute("PRAGMA synchronous = NORMAL")
            migration_table_exists = connection.execute(
                """
                SELECT 1 FROM sqlite_master
                WHERE type = 'table' AND name = 'schema_migrations'
                """
            ).fetchone()
            if migration_table_exists:
                row = connection.execute(
                    "SELECT MAX(version) AS version FROM schema_migrations"
                ).fetchone()
                existing_version = row["version"] if row else None
                if existing_version is not None and existing_version > SCHEMA_VERSION:
                    raise sqlite3.DatabaseError(
                        "database schema is newer than this application supports"
                    )
            try:
                connection.executescript("BEGIN IMMEDIATE;\n" + _SCHEMA)
                connection.execute(
                    """
                    INSERT OR IGNORE INTO schema_migrations (
                        version, applied_at_utc, description
                    ) VALUES (?, ?, ?)
                    """,
                    (
                        SCHEMA_VERSION,
                        datetime.now(UTC).isoformat(timespec="microseconds"),
                        "central market-data and factor-history schema",
                    ),
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
