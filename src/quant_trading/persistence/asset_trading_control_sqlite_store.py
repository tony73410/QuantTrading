"""SQLite adapter for immutable P23-4C1 per-symbol trading-control evidence."""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import datetime
from uuid import UUID
from pathlib import Path

from quant_trading.asset_state import (
    AssetTradingControlCalendarEvidence,
    AssetTradingControlEvent,
    AssetTradingControlOperationAttempt,
    AssetTradingControlOperationStatus,
    AssetTradingControlQuery,
    AssetTradingControlStatus,
)

from .sqlite_database import CentralSQLiteDatabase


def _iso(value: datetime) -> str:
    return value.isoformat(timespec="microseconds")


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _calendar_dict(value: AssetTradingControlCalendarEvidence) -> dict[str, object]:
    return {
        "mapping_id": str(value.mapping_id), "mapping_version": value.mapping_version,
        "calendar_definition_id": value.calendar_definition_id,
        "calendar_snapshot_id": str(value.calendar_snapshot_id),
        "calendar_engine_name": value.calendar_engine_name,
        "calendar_engine_version": value.calendar_engine_version,
        "exchange_calendar_name": value.exchange_calendar_name,
        "schedule_fingerprint": value.schedule_fingerprint,
        "effective_session": value.effective_session.isoformat(),
        "session_open_utc": _iso(value.session_open_utc),
        "session_close_utc": _iso(value.session_close_utc),
        "observed_at_utc": _iso(value.observed_at_utc),
        "schema_version": value.schema_version,
    }


def _calendar_from(data: dict[str, object]) -> AssetTradingControlCalendarEvidence:
    from datetime import date
    return AssetTradingControlCalendarEvidence(
        UUID(str(data["mapping_id"])), int(data["mapping_version"]),
        str(data["calendar_definition_id"]), UUID(str(data["calendar_snapshot_id"])),
        str(data["calendar_engine_name"]), str(data["calendar_engine_version"]),
        str(data["exchange_calendar_name"]), str(data["schedule_fingerprint"]),
        date.fromisoformat(str(data["effective_session"])),
        _dt(str(data["session_open_utc"])), _dt(str(data["session_close_utc"])),
        _dt(str(data["observed_at_utc"])), int(data.get("schema_version", 1)),
    )


class SQLiteAssetTradingControlStore:
    def __init__(self, database: CentralSQLiteDatabase | Path | str) -> None:
        self._database = database if isinstance(database, CentralSQLiteDatabase) else CentralSQLiteDatabase(database)

    def initialize(self) -> None:
        self._database.initialize()

    def get_first_operation(self, operation_id: UUID):
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                "SELECT * FROM asset_trading_control_operations WHERE operation_id=? ORDER BY completed_at_utc, attempt_id LIMIT 1",
                (str(operation_id),),
            ).fetchone()
            return self._operation(row) if row else None

    def get_latest_event(self, symbol: str):
        return self.get_latest_asset_trading_control_event(symbol)

    def save_operation(self, operation: AssetTradingControlOperationAttempt) -> None:
        if operation.status is AssetTradingControlOperationStatus.COMPLETED:
            raise ValueError("completed control operation must be saved with its event")
        with closing(self._database.connect()) as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                self._validate_run(connection, operation)
                self._insert_operation(connection, operation)
                connection.commit()
            except Exception as exc:
                connection.rollback()
                raise sqlite3.DatabaseError(f"could not save failed trading-control operation: {exc}") from exc

    def append_event(self, event: AssetTradingControlEvent, operation: AssetTradingControlOperationAttempt) -> None:
        if operation.event_id != event.event_id or operation.operation_id != event.operation_id:
            raise ValueError("trading-control operation/event identity is inconsistent")
        with closing(self._database.connect()) as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                self._validate_run(connection, operation)
                latest = connection.execute(
                    "SELECT event_id,new_status FROM asset_trading_control_events WHERE symbol=? ORDER BY rowid DESC LIMIT 1",
                    (event.symbol,),
                ).fetchone()
                latest_id = UUID(latest["event_id"]) if latest else None
                if latest_id != event.predecessor_event_id:
                    raise ValueError("trading-control predecessor changed before append")
                previous = AssetTradingControlStatus(latest["new_status"]) if latest else None
                if previous is not event.previous_status:
                    raise ValueError("trading-control previous status was modified")
                self._insert_operation(connection, operation)
                self._insert_event(connection, event)
                connection.commit()
            except Exception as exc:
                connection.rollback()
                raise sqlite3.DatabaseError(f"could not append trading-control event: {exc}") from exc

    def get_asset_trading_control_event(self, event_id: UUID):
        with closing(self._database.connect()) as connection:
            row = connection.execute("SELECT * FROM asset_trading_control_events WHERE event_id=?", (str(event_id),)).fetchone()
            return self._event(row) if row else None

    def get_latest_asset_trading_control_event(self, symbol: str):
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                "SELECT * FROM asset_trading_control_events WHERE symbol=? ORDER BY rowid DESC LIMIT 1",
                (symbol.strip().upper(),),
            ).fetchone()
            return self._event(row) if row else None

    def get_effective_asset_trading_control_event(self, symbol: str, as_of_utc: datetime):
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                "SELECT * FROM asset_trading_control_events WHERE symbol=? AND effective_at_utc<=? ORDER BY effective_at_utc DESC,rowid DESC LIMIT 1",
                (symbol.strip().upper(), _iso(as_of_utc)),
            ).fetchone()
            return self._event(row) if row else None

    def list_asset_trading_control_events(self, query=AssetTradingControlQuery()):
        clauses, params = [], []
        if query.symbol:
            clauses.append("symbol=?"); params.append(query.symbol)
        if query.status:
            clauses.append("new_status=?"); params.append(query.status.value)
        if query.effective_from_utc:
            clauses.append("effective_at_utc>=?"); params.append(_iso(query.effective_from_utc))
        if query.effective_to_utc:
            clauses.append("effective_at_utc<?"); params.append(_iso(query.effective_to_utc))
        where = "WHERE " + " AND ".join(clauses) if clauses else ""
        params.append(query.limit)
        with closing(self._database.connect()) as connection:
            rows = connection.execute(
                f"SELECT * FROM asset_trading_control_events {where} ORDER BY effective_at_utc DESC,rowid DESC LIMIT ?", params,
            ).fetchall()
            return tuple(self._event(row) for row in rows)

    def list_asset_trading_control_operations(self, query=AssetTradingControlQuery()):
        clauses, params = [], []
        if query.symbol:
            clauses.append("requested_symbol=?"); params.append(query.symbol)
        if query.status:
            clauses.append("requested_status=?"); params.append(query.status.value)
        if query.effective_from_utc:
            clauses.append("requested_at_utc>=?"); params.append(_iso(query.effective_from_utc))
        if query.effective_to_utc:
            clauses.append("requested_at_utc<?"); params.append(_iso(query.effective_to_utc))
        where = "WHERE " + " AND ".join(clauses) if clauses else ""
        params.append(query.limit)
        with closing(self._database.connect()) as connection:
            rows = connection.execute(
                f"SELECT * FROM asset_trading_control_operations {where} ORDER BY requested_at_utc DESC,attempt_id DESC LIMIT ?", params,
            ).fetchall()
            return tuple(self._operation(row) for row in rows)

    @staticmethod
    def _validate_run(connection, operation):
        run = connection.execute("SELECT run_type FROM algorithm_runs WHERE run_id=?", (str(operation.run_id),)).fetchone()
        stage = connection.execute("SELECT run_id,stage_name,sequence FROM algorithm_run_stages WHERE stage_id=?", (str(operation.stage_id),)).fetchone()
        if run is None or run["run_type"] != "asset_trading_control_change":
            raise ValueError("trading-control Run is invalid")
        if stage is None or stage["run_id"] != str(operation.run_id) or stage["stage_name"] != "state" or int(stage["sequence"]) != 1:
            raise ValueError("trading-control state stage is invalid")

    @staticmethod
    def _insert_operation(connection, value):
        connection.execute(
            "INSERT INTO asset_trading_control_operations VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (str(value.attempt_id), str(value.operation_id), str(value.run_id), str(value.stage_id),
             value.command_fingerprint, value.requested_symbol, value.requested_status.value,
             str(value.requested_predecessor_event_id) if value.requested_predecessor_event_id else None,
             value.status.value, _iso(value.requested_at_utc), _iso(value.completed_at_utc),
             value.session_id, value.request_id, value.created_by, value.reason,
             str(value.event_id) if value.event_id else None, value.error_code, value.error_summary,
             int(value.execution_allowed), int(value.live_allowed), value.schema_version),
        )

    @staticmethod
    def _insert_event(connection, value):
        calendar = value.calendar
        connection.execute(
            "INSERT INTO asset_trading_control_events VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (str(value.event_id), str(value.operation_id), str(value.run_id), str(value.stage_id),
             str(value.predecessor_event_id) if value.predecessor_event_id else None, value.symbol,
             value.previous_status.value if value.previous_status else None, value.new_status.value,
             _iso(value.requested_at_utc), _iso(value.effective_at_utc), calendar.effective_session.isoformat(),
             str(calendar.mapping_id), calendar.mapping_version, calendar.calendar_definition_id,
             str(calendar.calendar_snapshot_id), calendar.calendar_engine_name, calendar.calendar_engine_version,
             calendar.exchange_calendar_name, calendar.schedule_fingerprint, _iso(calendar.session_open_utc),
             _iso(calendar.session_close_utc), _iso(calendar.observed_at_utc),
             json.dumps(_calendar_dict(calendar), sort_keys=True, separators=(",", ":")),
             value.reason, value.created_by, _iso(value.created_at_utc), json.dumps(value.warnings),
             int(value.execution_allowed), int(value.live_allowed), value.component_id,
             value.component_version, value.schema_version),
        )

    @staticmethod
    def _operation(row):
        return AssetTradingControlOperationAttempt(
            UUID(row["attempt_id"]), UUID(row["operation_id"]), UUID(row["run_id"]), UUID(row["stage_id"]),
            row["command_fingerprint"], row["requested_symbol"], AssetTradingControlStatus(row["requested_status"]),
            UUID(row["requested_predecessor_event_id"]) if row["requested_predecessor_event_id"] else None,
            AssetTradingControlOperationStatus(row["status"]), _dt(row["requested_at_utc"]), _dt(row["completed_at_utc"]),
            row["session_id"], row["request_id"], row["created_by"], row["reason"],
            UUID(row["event_id"]) if row["event_id"] else None, row["error_code"], row["error_summary"],
            bool(row["execution_allowed"]), bool(row["live_allowed"]), int(row["schema_version"]),
        )

    @staticmethod
    def _event(row):
        return AssetTradingControlEvent(
            UUID(row["event_id"]), UUID(row["operation_id"]), UUID(row["run_id"]), UUID(row["stage_id"]),
            UUID(row["predecessor_event_id"]) if row["predecessor_event_id"] else None,
            row["symbol"], AssetTradingControlStatus(row["previous_status"]) if row["previous_status"] else None,
            AssetTradingControlStatus(row["new_status"]), _dt(row["requested_at_utc"]), _dt(row["effective_at_utc"]),
            _calendar_from(json.loads(row["calendar_json"])), row["reason"], row["created_by"], _dt(row["created_at_utc"]),
            tuple(json.loads(row["warnings_json"])), bool(row["execution_allowed"]), bool(row["live_allowed"]),
            row["component_id"], row["component_version"], int(row["schema_version"]),
        )


__all__ = ["SQLiteAssetTradingControlStore"]
