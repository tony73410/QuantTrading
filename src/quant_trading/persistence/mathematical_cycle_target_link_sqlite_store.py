"""Central SQLite adapter for immutable disabled P23-3B bridge evidence."""

from __future__ import annotations

from contextlib import closing
from datetime import date, datetime
import json
from pathlib import Path
from uuid import UUID

from quant_trading.target_position.mathematical_cycle_link_interfaces import (
    MathematicalCycleTargetLinkStore,
)
from quant_trading.target_position.mathematical_cycle_link_models import (
    MathematicalCycleTargetLinkOperation,
    MathematicalCycleTargetLinkQuery,
    MathematicalCycleTargetLinkStatus,
    MathematicalCycleTargetPositionLink,
)

from .sqlite_database import CentralSQLiteDatabase


class SQLiteMathematicalCycleTargetLinkStore(MathematicalCycleTargetLinkStore):
    def __init__(self, database: CentralSQLiteDatabase | Path | str) -> None:
        self._database = database if isinstance(database, CentralSQLiteDatabase) else CentralSQLiteDatabase(database)

    def initialize(self) -> None:
        self._database.initialize()

    def get_operation(self, attempt_id: UUID):
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                "SELECT * FROM mathematical_cycle_target_link_operations WHERE attempt_id=?",
                (str(attempt_id),),
            ).fetchone()
        return self._load_operation(row) if row else None

    def get_operation_by_operation_id(self, operation_id: UUID):
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                """SELECT * FROM mathematical_cycle_target_link_operations
                   WHERE operation_id=?
                   ORDER BY CASE WHEN status IN ('completed','completed_with_warnings') THEN 0 ELSE 1 END,
                            completed_at_utc DESC, attempt_id DESC LIMIT 1""",
                (str(operation_id),),
            ).fetchone()
        return self._load_operation(row) if row else None

    def list_operations(self, query: MathematicalCycleTargetLinkQuery = MathematicalCycleTargetLinkQuery()):
        clauses, values = [], []
        if query.symbol:
            clauses.append("resolved_symbol=?"); values.append(query.symbol)
        if query.status:
            clauses.append("status=?"); values.append(query.status.value)
        if query.stream_id:
            clauses.append("requested_stream_id=?"); values.append(str(query.stream_id))
        if query.configuration_id:
            clauses.append("requested_configuration_id=?"); values.append(str(query.configuration_id))
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        values.append(query.limit)
        with closing(self._database.connect()) as connection:
            rows = connection.execute(
                "SELECT * FROM mathematical_cycle_target_link_operations" + where
                + " ORDER BY completed_at_utc DESC, attempt_id DESC LIMIT ?", values,
            ).fetchall()
        return tuple(self._load_operation(row) for row in rows)

    def get_link(self, link_id: UUID):
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                "SELECT * FROM mathematical_cycle_target_position_links WHERE link_id=?",
                (str(link_id),),
            ).fetchone()
        return self._load_link(row) if row else None

    def list_links(self, query: MathematicalCycleTargetLinkQuery = MathematicalCycleTargetLinkQuery()):
        clauses, values = [], []
        if query.symbol:
            clauses.append("symbol=?"); values.append(query.symbol)
        if query.stream_id:
            clauses.append("stream_id=?"); values.append(str(query.stream_id))
        if query.configuration_id:
            clauses.append("configuration_id=?"); values.append(str(query.configuration_id))
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        values.append(query.limit)
        with closing(self._database.connect()) as connection:
            rows = connection.execute(
                "SELECT * FROM mathematical_cycle_target_position_links" + where
                + " ORDER BY created_at_utc DESC, link_id DESC LIMIT ?", values,
            ).fetchall()
        return tuple(self._load_link(row) for row in rows)

    def save_success(self, operation, link) -> None:
        if not operation.status.succeeded or operation.link_id != link.link_id:
            raise ValueError("P39 success persistence requires matching terminal evidence")
        with closing(self._database.connect()) as connection:
            with connection:
                self._insert_operation(connection, operation)
                self._insert_link(connection, link)

    def save_operation(self, operation) -> None:
        if operation.status.succeeded:
            raise ValueError("successful P39 operations require an immutable accepted link")
        with closing(self._database.connect()) as connection:
            with connection:
                self._insert_operation(connection, operation)

    @staticmethod
    def _insert_operation(connection, item):
        values = {
            "attempt_id": str(item.attempt_id), "operation_id": str(item.operation_id),
            "target_operation_id": str(item.target_operation_id), "bridge_run_id": str(item.bridge_run_id),
            "state_stage_id": str(item.state_stage_id),
            "target_stage_id": str(item.target_stage_id) if item.target_stage_id else None,
            "command_fingerprint": item.command_fingerprint, "status": item.status.value,
            "requested_at_utc": item.requested_at_utc.isoformat(),
            "completed_at_utc": item.completed_at_utc.isoformat(),
            "requested_state_operation_id": str(item.requested_state_operation_id),
            "requested_state_run_id": str(item.requested_state_run_id),
            "requested_stream_id": str(item.requested_stream_id),
            "requested_latest_snapshot_id": str(item.requested_latest_snapshot_id),
            "requested_configuration_id": str(item.requested_configuration_id),
            "requested_configuration_version": item.requested_configuration_version,
            "research_capital_basis_usd_text": item.research_capital_basis_usd_text,
            "current_position_value_usd_text": item.current_position_value_usd_text,
            "session_id": item.session_id, "request_id": item.request_id,
            "created_by": item.created_by, "reason": item.reason,
            "resolved_state_attempt_id": str(item.resolved_state_attempt_id) if item.resolved_state_attempt_id else None,
            "resolved_state_definition_id": str(item.resolved_state_definition_id) if item.resolved_state_definition_id else None,
            "resolved_state_definition_version": item.resolved_state_definition_version,
            "resolved_symbol": item.resolved_symbol,
            "resolved_session": item.resolved_session.isoformat() if item.resolved_session else None,
            "resolved_source_result_id": str(item.resolved_source_result_id) if item.resolved_source_result_id else None,
            "resolved_source_run_id": str(item.resolved_source_run_id) if item.resolved_source_run_id else None,
            "resolved_source_step_id": str(item.resolved_source_step_id) if item.resolved_source_step_id else None,
            "resolved_target_attempt_id": str(item.resolved_target_attempt_id) if item.resolved_target_attempt_id else None,
            "resolved_target_result_id": str(item.resolved_target_result_id) if item.resolved_target_result_id else None,
            "resolved_target_run_id": str(item.resolved_target_run_id) if item.resolved_target_run_id else None,
            "link_id": str(item.link_id) if item.link_id else None,
            "warnings_json": json.dumps(item.warnings, separators=(",", ":")),
            "error_code": item.error_code, "error_summary": item.error_summary,
            "software_version": item.software_version, "source_revision": item.source_revision,
            "worktree_state": item.worktree_state,
            "execution_allowed": int(item.execution_allowed), "live_allowed": int(item.live_allowed),
            "schema_version": item.schema_version,
        }
        columns = tuple(values)
        connection.execute(
            f"INSERT INTO mathematical_cycle_target_link_operations ({','.join(columns)}) "
            f"VALUES ({','.join(':'+column for column in columns)})", values,
        )

    @staticmethod
    def _insert_link(connection, item):
        values = {
            "link_id": str(item.link_id), "bridge_attempt_id": str(item.bridge_attempt_id),
            "bridge_operation_id": str(item.bridge_operation_id), "bridge_run_id": str(item.bridge_run_id),
            "state_stage_id": str(item.state_stage_id), "target_stage_id": str(item.target_stage_id),
            "state_attempt_id": str(item.state_attempt_id), "state_operation_id": str(item.state_operation_id),
            "state_run_id": str(item.state_run_id), "state_definition_id": str(item.state_definition_id),
            "state_definition_version": item.state_definition_version, "stream_id": str(item.stream_id),
            "cycle_id": str(item.cycle_id), "snapshot_id": str(item.snapshot_id),
            "snapshot_sequence": item.snapshot_sequence,
            "snapshot_semantic_fingerprint": item.snapshot_semantic_fingerprint,
            "source_result_id": str(item.source_result_id), "source_run_id": str(item.source_run_id),
            "source_step_id": str(item.source_step_id),
            "source_calculation_fingerprint": item.source_calculation_fingerprint,
            "target_attempt_id": str(item.target_attempt_id), "target_operation_id": str(item.target_operation_id),
            "target_result_id": str(item.target_result_id), "target_run_id": str(item.target_run_id),
            "formula_definition_id": str(item.formula_definition_id),
            "formula_definition_version": item.formula_definition_version,
            "configuration_id": str(item.configuration_id), "configuration_version": item.configuration_version,
            "symbol": item.symbol, "session": item.session.isoformat(),
            "direction_at_open": item.direction_at_open, "direction_at_close": item.direction_at_close,
            "reference_session": item.reference_session.isoformat(),
            "reference_price_text": item.reference_price_text, "reference_price_hex": item.reference_price_hex,
            "target_region": item.target_region, "target_fraction_text": item.target_fraction_text,
            "research_capital_basis_usd_text": item.research_capital_basis_usd_text,
            "current_position_value_usd_text": item.current_position_value_usd_text,
            "target_position_value_usd_text": item.target_position_value_usd_text,
            "adjustment_value_usd_text": item.adjustment_value_usd_text,
            "created_at_utc": item.created_at_utc.isoformat(), "created_by": item.created_by,
            "reason": item.reason, "execution_allowed": int(item.execution_allowed),
            "live_allowed": int(item.live_allowed), "schema_version": item.schema_version,
        }
        columns = tuple(values)
        connection.execute(
            f"INSERT INTO mathematical_cycle_target_position_links ({','.join(columns)}) "
            f"VALUES ({','.join(':'+column for column in columns)})", values,
        )

    @staticmethod
    def _load_operation(row):
        return MathematicalCycleTargetLinkOperation(
            UUID(row["attempt_id"]), UUID(row["operation_id"]), UUID(row["target_operation_id"]),
            UUID(row["bridge_run_id"]), UUID(row["state_stage_id"]),
            UUID(row["target_stage_id"]) if row["target_stage_id"] else None,
            row["command_fingerprint"], MathematicalCycleTargetLinkStatus(row["status"]),
            datetime.fromisoformat(row["requested_at_utc"]), datetime.fromisoformat(row["completed_at_utc"]),
            UUID(row["requested_state_operation_id"]), UUID(row["requested_state_run_id"]),
            UUID(row["requested_stream_id"]), UUID(row["requested_latest_snapshot_id"]),
            UUID(row["requested_configuration_id"]), int(row["requested_configuration_version"]),
            row["research_capital_basis_usd_text"], row["current_position_value_usd_text"],
            row["session_id"], row["request_id"], row["created_by"], row["reason"],
            UUID(row["resolved_state_attempt_id"]) if row["resolved_state_attempt_id"] else None,
            UUID(row["resolved_state_definition_id"]) if row["resolved_state_definition_id"] else None,
            int(row["resolved_state_definition_version"]) if row["resolved_state_definition_version"] else None,
            row["resolved_symbol"], date.fromisoformat(row["resolved_session"]) if row["resolved_session"] else None,
            UUID(row["resolved_source_result_id"]) if row["resolved_source_result_id"] else None,
            UUID(row["resolved_source_run_id"]) if row["resolved_source_run_id"] else None,
            UUID(row["resolved_source_step_id"]) if row["resolved_source_step_id"] else None,
            UUID(row["resolved_target_attempt_id"]) if row["resolved_target_attempt_id"] else None,
            UUID(row["resolved_target_result_id"]) if row["resolved_target_result_id"] else None,
            UUID(row["resolved_target_run_id"]) if row["resolved_target_run_id"] else None,
            UUID(row["link_id"]) if row["link_id"] else None,
            tuple(json.loads(row["warnings_json"])), row["error_code"], row["error_summary"],
            row["software_version"], row["source_revision"], row["worktree_state"],
            bool(row["execution_allowed"]), bool(row["live_allowed"]), int(row["schema_version"]),
        )

    @staticmethod
    def _load_link(row):
        return MathematicalCycleTargetPositionLink(
            UUID(row["link_id"]), UUID(row["bridge_attempt_id"]), UUID(row["bridge_operation_id"]),
            UUID(row["bridge_run_id"]), UUID(row["state_stage_id"]), UUID(row["target_stage_id"]),
            UUID(row["state_attempt_id"]), UUID(row["state_operation_id"]), UUID(row["state_run_id"]),
            UUID(row["state_definition_id"]), int(row["state_definition_version"]), UUID(row["stream_id"]),
            UUID(row["cycle_id"]), UUID(row["snapshot_id"]), int(row["snapshot_sequence"]),
            row["snapshot_semantic_fingerprint"], UUID(row["source_result_id"]), UUID(row["source_run_id"]),
            UUID(row["source_step_id"]), row["source_calculation_fingerprint"], UUID(row["target_attempt_id"]),
            UUID(row["target_operation_id"]), UUID(row["target_result_id"]), UUID(row["target_run_id"]),
            UUID(row["formula_definition_id"]), int(row["formula_definition_version"]),
            UUID(row["configuration_id"]), int(row["configuration_version"]), row["symbol"],
            date.fromisoformat(row["session"]), row["direction_at_open"], row["direction_at_close"],
            date.fromisoformat(row["reference_session"]), row["reference_price_text"], row["reference_price_hex"],
            row["target_region"], row["target_fraction_text"], row["research_capital_basis_usd_text"],
            row["current_position_value_usd_text"], row["target_position_value_usd_text"],
            row["adjustment_value_usd_text"], datetime.fromisoformat(row["created_at_utc"]),
            row["created_by"], row["reason"], bool(row["execution_allowed"]),
            bool(row["live_allowed"]), int(row["schema_version"]),
        )


__all__ = ["SQLiteMathematicalCycleTargetLinkStore"]
