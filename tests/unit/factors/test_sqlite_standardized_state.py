from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import pytest

from quant_trading.persistence import CentralSQLiteDatabase
from quant_trading.persistence import sqlite_database
from quant_trading.persistence.sqlite_database import (
    _SCHEMA_V1,
    _SCHEMA_V2,
    _SCHEMA_V3,
    _SCHEMA_V4,
    _SCHEMA_V5,
    _SCHEMA_V6,
    _SCHEMA_V7,
)


NOW = datetime(2026, 7, 20, 23, 0, tzinfo=UTC)


def _create_v6_database(path: Path) -> None:
    with sqlite3.connect(path) as connection:
        for version, schema in (
            (1, _SCHEMA_V1),
            (2, _SCHEMA_V2),
            (3, _SCHEMA_V3),
            (4, _SCHEMA_V4),
            (5, _SCHEMA_V5),
            (6, _SCHEMA_V6),
        ):
            connection.executescript(schema)
            connection.execute(
                "INSERT INTO schema_migrations VALUES (?, ?, ?)",
                (version, NOW.isoformat(), f"test v{version}"),
            )
        connection.execute(
            """
            INSERT INTO market_bars VALUES (
                'AAPL', ?, '1Day', 'raw', 'iex', '100', '101', '99',
                '100.5', 10, NULL, NULL, 'test', ?
            )
            """,
            (NOW.isoformat(), NOW.isoformat()),
        )
        connection.commit()


def test_v6_to_v7_migration_backs_up_preserves_and_creates_no_default(tmp_path: Path):
    database = tmp_path / "central.sqlite3"
    backups = tmp_path / "backups"
    _create_v6_database(database)

    CentralSQLiteDatabase(database, backup_directory=backups).initialize()

    backup_files = tuple(backups.glob("*.sqlite3"))
    assert len(backup_files) == 1
    assert ".schema-v6-to-v8." in backup_files[0].name
    with sqlite3.connect(backup_files[0]) as backup:
        assert backup.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 6
        assert backup.execute("SELECT COUNT(*) FROM market_bars").fetchone()[0] == 1
        assert backup.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 8
        assert connection.execute(
            "SELECT COUNT(*) FROM target_position_standardized_state_links"
        ).fetchone()[0] == 0
        assert connection.execute("SELECT COUNT(*) FROM market_bars").fetchone()[0] == 1
        for table in (
            "standardized_state_definitions",
            "standardized_state_operations",
            "standardized_state_results",
        ):
            assert connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def test_failed_v7_migration_rolls_back_to_intact_v6(tmp_path: Path, monkeypatch):
    database = tmp_path / "central.sqlite3"
    backups = tmp_path / "backups"
    _create_v6_database(database)
    broken = dict(sqlite_database._MIGRATIONS)
    broken[7] = ("intentionally broken v7", _SCHEMA_V7 + "\nINVALID SQL;")
    monkeypatch.setattr(sqlite_database, "_MIGRATIONS", broken)

    with pytest.raises(sqlite3.OperationalError):
        CentralSQLiteDatabase(database, backup_directory=backups).initialize()

    assert len(tuple(backups.glob("*.sqlite3"))) == 1
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 6
        assert connection.execute("SELECT COUNT(*) FROM market_bars").fetchone()[0] == 1
        assert connection.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE name = 'standardized_state_results'"
        ).fetchone()[0] == 0
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
