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
)


NOW = datetime(2026, 7, 20, 20, 0, tzinfo=UTC)


def _create_v4_database(path: Path) -> None:
    with sqlite3.connect(path) as connection:
        for version, schema in (
            (1, _SCHEMA_V1),
            (2, _SCHEMA_V2),
            (3, _SCHEMA_V3),
            (4, _SCHEMA_V4),
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


def test_v4_to_v5_migration_backs_up_and_preserves_existing_rows(tmp_path: Path):
    database_path = tmp_path / "central.sqlite3"
    backup_path = tmp_path / "backups"
    _create_v4_database(database_path)

    CentralSQLiteDatabase(database_path, backup_directory=backup_path).initialize()

    backups = tuple(backup_path.glob("*.sqlite3"))
    assert len(backups) == 1
    assert ".schema-v4-to-v6." in backups[0].name
    with sqlite3.connect(backups[0]) as backup:
        assert backup.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 4
        assert backup.execute("SELECT COUNT(*) FROM market_bars").fetchone()[0] == 1
        assert backup.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    with sqlite3.connect(database_path) as connection:
        assert connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 6
        assert connection.execute("SELECT COUNT(*) FROM market_bars").fetchone()[0] == 1
        assert connection.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE name = 'asset_state_cycles'"
        ).fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM asset_state_definitions").fetchone()[0] == 0
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def test_failed_v5_migration_rolls_back_to_intact_v4(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    database_path = tmp_path / "central.sqlite3"
    backup_path = tmp_path / "backups"
    _create_v4_database(database_path)
    broken = dict(sqlite_database._MIGRATIONS)
    broken[5] = ("intentionally broken v5", _SCHEMA_V5 + "\nINVALID SQL;")
    monkeypatch.setattr(sqlite_database, "_MIGRATIONS", broken)

    with pytest.raises(sqlite3.OperationalError):
        CentralSQLiteDatabase(database_path, backup_directory=backup_path).initialize()

    assert len(tuple(backup_path.glob("*.sqlite3"))) == 1
    with sqlite3.connect(database_path) as connection:
        assert connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 4
        assert connection.execute("SELECT COUNT(*) FROM market_bars").fetchone()[0] == 1
        assert connection.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE name = 'asset_state_cycles'"
        ).fetchone()[0] == 0
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
