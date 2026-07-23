"""SQLite adapter for type-distinct target-adjustment Decision evidence."""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from uuid import UUID

from quant_trading.decision import (
    DecisionAction,
    LinkedTargetDecisionInput,
    TargetAdjustmentDecisionOperationAttempt,
    TargetAdjustmentDecisionQuery,
    TargetAdjustmentDecisionResult,
    TargetAdjustmentDecisionSourceLink,
    TargetAdjustmentDecisionStatus,
    TargetAdjustmentTradeIntent,
)
from quant_trading.decision.errors import DecisionStorageError

from .sqlite_database import CentralSQLiteDatabase


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="microseconds")


def _datetime(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value).astimezone(UTC) if value else None


class SQLiteTargetAdjustmentDecisionStore:
    """Implement Decision Store/query ports in the central SQLite database."""

    def __init__(self, database_path: Path | str) -> None:
        self._database = CentralSQLiteDatabase(database_path)

    def initialize(self) -> None:
        self._database.initialize()

    def get_first_operation(
        self, operation_id: UUID
    ) -> TargetAdjustmentDecisionOperationAttempt | None:
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                """
                SELECT * FROM target_adjustment_decision_operations
                WHERE operation_id = ?
                ORDER BY CASE
                    WHEN status IN ('intent_created', 'hold') THEN 0 ELSE 1
                END, rowid
                LIMIT 1
                """,
                (str(operation_id),),
            ).fetchone()
            return self._operation_from_row(row) if row else None

    def save_operation(self, operation: TargetAdjustmentDecisionOperationAttempt) -> None:
        with closing(self._database.connect()) as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                self._validate_run_context(connection, operation)
                if operation.resolved_source is not None:
                    self._validate_source_database(connection, operation.resolved_source)
                self._insert_operation(connection, operation)
                connection.commit()
            except Exception as exc:
                connection.rollback()
                self._raise_storage("could not save target-adjustment operation", exc)

    def save_completed(
        self,
        result: TargetAdjustmentDecisionResult,
        operation: TargetAdjustmentDecisionOperationAttempt,
        source_link: TargetAdjustmentDecisionSourceLink,
    ) -> None:
        self._validate_completed_models(result, operation, source_link)
        with closing(self._database.connect()) as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                self._validate_run_context(connection, operation)
                self._validate_source_database(connection, result.source)
                self._insert_operation(connection, operation)
                self._insert_result(connection, result)
                for intent in result.intents:
                    self._insert_intent(connection, intent)
                self._insert_source_link(connection, source_link)
                intent_count = connection.execute(
                    """
                    SELECT COUNT(*) FROM target_adjustment_trade_intents
                    WHERE decision_result_id = ?
                    """,
                    (str(result.decision_result_id),),
                ).fetchone()[0]
                expected = 0 if result.status is TargetAdjustmentDecisionStatus.HOLD else 1
                if int(intent_count) != expected:
                    raise DecisionStorageError("stored target-adjustment intent cardinality is invalid")
                connection.commit()
            except Exception as exc:
                connection.rollback()
                self._raise_storage("could not save completed target-adjustment Decision", exc)

    def list_target_adjustment_operations(
        self, query: TargetAdjustmentDecisionQuery = TargetAdjustmentDecisionQuery()
    ) -> tuple[TargetAdjustmentDecisionOperationAttempt, ...]:
        clauses: list[str] = []
        parameters: list[object] = []
        if query.symbol is not None:
            clauses.append("o.resolved_symbol = ?")
            parameters.append(query.symbol)
        if query.action is not None:
            clauses.append("r.action = ?")
            parameters.append(query.action.value)
        if query.status is not None:
            clauses.append("o.status = ?")
            parameters.append(query.status.value)
        if query.target_definition_id is not None:
            clauses.append("o.resolved_target_definition_id = ?")
            parameters.append(str(query.target_definition_id))
        if query.target_definition_version is not None:
            clauses.append("o.resolved_target_definition_version = ?")
            parameters.append(query.target_definition_version)
        if query.target_position_link_id is not None:
            clauses.append("o.requested_target_position_link_id = ?")
            parameters.append(str(query.target_position_link_id))
        if query.as_of_from_utc is not None:
            clauses.append("o.resolved_as_of_utc >= ?")
            parameters.append(_iso(query.as_of_from_utc))
        if query.as_of_to_utc is not None:
            clauses.append("o.resolved_as_of_utc < ?")
            parameters.append(_iso(query.as_of_to_utc))
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        parameters.append(query.limit)
        with closing(self._database.connect()) as connection:
            rows = connection.execute(
                f"""
                SELECT o.* FROM target_adjustment_decision_operations o
                LEFT JOIN target_adjustment_decision_results r
                  ON r.decision_result_id = o.decision_result_id
                {where}
                ORDER BY o.requested_at_utc DESC, o.attempt_id DESC LIMIT ?
                """,
                tuple(parameters),
            ).fetchall()
            return tuple(self._operation_from_row(row) for row in rows)

    def list_target_adjustment_results(
        self, query: TargetAdjustmentDecisionQuery = TargetAdjustmentDecisionQuery()
    ) -> tuple[TargetAdjustmentDecisionResult, ...]:
        clauses, parameters = self._result_clauses(query)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        parameters.append(query.limit)
        with closing(self._database.connect()) as connection:
            rows = connection.execute(
                f"""
                SELECT * FROM target_adjustment_decision_results {where}
                ORDER BY as_of_utc DESC, created_at_utc DESC, decision_result_id DESC
                LIMIT ?
                """,
                tuple(parameters),
            ).fetchall()
            return tuple(self._result_from_row(connection, row) for row in rows)

    def get_target_adjustment_result(
        self, decision_result_id: UUID
    ) -> TargetAdjustmentDecisionResult | None:
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                """
                SELECT * FROM target_adjustment_decision_results
                WHERE decision_result_id = ?
                """,
                (str(decision_result_id),),
            ).fetchone()
            return self._result_from_row(connection, row) if row else None

    def get_target_adjustment_source_link(
        self, decision_result_id: UUID
    ) -> TargetAdjustmentDecisionSourceLink | None:
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                """
                SELECT * FROM target_adjustment_decision_source_links
                WHERE decision_result_id = ?
                """,
                (str(decision_result_id),),
            ).fetchone()
            return self._source_link_from_row(row) if row else None

    def get_target_adjustment_intent(
        self, intent_id: UUID
    ) -> TargetAdjustmentTradeIntent | None:
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                "SELECT * FROM target_adjustment_trade_intents WHERE intent_id = ?",
                (str(intent_id),),
            ).fetchone()
            return self._intent_from_row(row) if row else None

    @staticmethod
    def _result_clauses(query: TargetAdjustmentDecisionQuery):
        clauses: list[str] = []
        parameters: list[object] = []
        if query.symbol is not None:
            clauses.append("symbol = ?")
            parameters.append(query.symbol)
        if query.action is not None:
            clauses.append("action = ?")
            parameters.append(query.action.value)
        if query.status is not None:
            clauses.append("status = ?")
            parameters.append(query.status.value)
        if query.target_definition_id is not None:
            clauses.append("target_definition_id = ?")
            parameters.append(str(query.target_definition_id))
        if query.target_definition_version is not None:
            clauses.append("target_definition_version = ?")
            parameters.append(query.target_definition_version)
        if query.target_position_link_id is not None:
            clauses.append("target_position_link_id = ?")
            parameters.append(str(query.target_position_link_id))
        if query.as_of_from_utc is not None:
            clauses.append("as_of_utc >= ?")
            parameters.append(_iso(query.as_of_from_utc))
        if query.as_of_to_utc is not None:
            clauses.append("as_of_utc < ?")
            parameters.append(_iso(query.as_of_to_utc))
        return clauses, parameters

    @staticmethod
    def _validate_completed_models(result, operation, source_link) -> None:
        if operation.status != result.status or operation.resolved_source != result.source:
            raise DecisionStorageError("target-adjustment operation/result evidence is inconsistent")
        if (
            operation.decision_result_id != result.decision_result_id
            or operation.operation_id != result.operation_id
            or operation.run_id != result.run_id
            or operation.decision_stage_id != result.stage_id
        ):
            raise DecisionStorageError("target-adjustment result identity is inconsistent")
        if (
            source_link.operation_id != result.operation_id
            or source_link.decision_result_id != result.decision_result_id
            or source_link.decision_run_id != result.run_id
            or source_link.decision_stage_id != result.stage_id
            or source_link.target_position_link_id != result.source.target_position_link_id
            or source_link.linked_target_operation_id != result.source.linked_target_operation_id
            or source_link.linked_parent_run_id != result.source.linked_parent_run_id
            or source_link.target_child_run_id != result.source.target_child_run_id
            or source_link.standardized_state_run_id != result.source.standardized_state_run_id
            or source_link.target_calculation_id != result.source.target_calculation_id
            or source_link.standardized_state_calculation_id
            != result.source.standardized_state_calculation_id
        ):
            raise DecisionStorageError("target-adjustment source link is inconsistent")

    @staticmethod
    def _validate_run_context(connection, operation) -> None:
        run = connection.execute(
            "SELECT run_type, parent_run_id FROM algorithm_runs WHERE run_id = ?",
            (str(operation.run_id),),
        ).fetchone()
        if run is None or run["run_type"] != "target_adjustment_decision_preview":
            raise DecisionStorageError("target-adjustment operation Run is invalid")
        source = operation.resolved_source
        if source is not None and run["parent_run_id"] != str(source.linked_parent_run_id):
            raise DecisionStorageError("target-adjustment Run parent is inconsistent")
        target_stage = connection.execute(
            "SELECT run_id, stage_name, sequence FROM algorithm_run_stages WHERE stage_id = ?",
            (str(operation.target_stage_id),),
        ).fetchone()
        if (
            target_stage is None
            or target_stage["run_id"] != str(operation.run_id)
            or target_stage["stage_name"] != "target_position"
            or int(target_stage["sequence"]) != 1
        ):
            raise DecisionStorageError("target-adjustment Target Position stage is invalid")
        if operation.decision_stage_id is not None:
            decision_stage = connection.execute(
                "SELECT run_id, stage_name, sequence FROM algorithm_run_stages WHERE stage_id = ?",
                (str(operation.decision_stage_id),),
            ).fetchone()
            if (
                decision_stage is None
                or decision_stage["run_id"] != str(operation.run_id)
                or decision_stage["stage_name"] != "decision"
                or int(decision_stage["sequence"]) != 2
            ):
                raise DecisionStorageError("target-adjustment Decision stage is invalid")

    @staticmethod
    def _validate_source_database(connection, source: LinkedTargetDecisionInput) -> None:
        link = connection.execute(
            """
            SELECT * FROM target_position_standardized_state_links
            WHERE link_id = ?
            """,
            (str(source.target_position_link_id),),
        ).fetchone()
        if link is None:
            raise DecisionStorageError("target-adjustment source link does not exist")
        expected_link = {
            "operation_id": str(source.linked_target_operation_id),
            "parent_run_id": str(source.linked_parent_run_id),
            "source_stage_id": str(source.linked_source_stage_id),
            "target_stage_id": str(source.linked_target_stage_id),
            "child_run_id": str(source.target_child_run_id),
            "child_stage_id": str(source.target_child_stage_id),
            "source_calculation_id": str(source.standardized_state_calculation_id),
            "source_run_id": str(source.standardized_state_run_id),
            "source_result_stage_id": str(source.standardized_state_stage_id),
            "source_definition_id": str(source.standardized_state_definition_id),
            "source_definition_version": source.standardized_state_definition_version,
            "symbol": source.symbol,
            "source_as_of_utc": _iso(source.as_of_utc),
            "standardized_state_text": str(source.standardized_state),
            "target_calculation_id": str(source.target_calculation_id),
            "target_definition_id": str(source.target_definition_id),
            "target_definition_version": source.target_definition_version,
            "created_at_utc": _iso(source.link_created_at_utc),
            "schema_version": source.link_schema_version,
        }
        for column, expected in expected_link.items():
            actual = link[column]
            if column.endswith("_text"):
                if Decimal(actual) != Decimal(expected):
                    raise DecisionStorageError("target-adjustment copied link value is inconsistent")
            elif actual != expected:
                raise DecisionStorageError("target-adjustment copied link identity is inconsistent")
        target = connection.execute(
            "SELECT * FROM target_position_results WHERE calculation_id = ?",
            (str(source.target_calculation_id),),
        ).fetchone()
        if target is None:
            raise DecisionStorageError("target-adjustment target result does not exist")
        expected_target = {
            "run_id": str(source.target_child_run_id),
            "stage_id": str(source.target_child_stage_id),
            "definition_id": str(source.target_definition_id),
            "definition_version": source.target_definition_version,
            "as_of_utc": _iso(source.as_of_utc),
            "research_capital_basis_usd_text": str(source.research_capital_basis_usd),
            "current_position_value_usd_text": str(source.current_position_value_usd),
            "target_fraction_text": str(source.target_fraction),
            "target_position_value_usd_text": str(source.target_position_value_usd),
            "adjustment_value_usd_text": str(source.adjustment_value_usd),
            "adjustment_direction": source.source_direction,
            "created_at_utc": _iso(source.target_created_at_utc),
            "schema_version": source.target_schema_version,
        }
        for column, expected in expected_target.items():
            actual = target[column]
            if column.endswith("_text"):
                if Decimal(actual) != Decimal(expected):
                    raise DecisionStorageError("target-adjustment copied target value is inconsistent")
            elif actual != expected:
                raise DecisionStorageError("target-adjustment copied target identity is inconsistent")
        standardized = connection.execute(
            "SELECT * FROM standardized_state_results WHERE calculation_id = ?",
            (str(source.standardized_state_calculation_id),),
        ).fetchone()
        if standardized is None or (
            standardized["run_id"] != str(source.standardized_state_run_id)
            or standardized["stage_id"] != str(source.standardized_state_stage_id)
            or standardized["definition_id"] != str(source.standardized_state_definition_id)
            or int(standardized["definition_version"]) != source.standardized_state_definition_version
            or standardized["symbol"] != source.symbol
            or standardized["as_of_utc"] != _iso(source.as_of_utc)
            or Decimal(standardized["standardized_state_text"]) != source.standardized_state
            or standardized["created_at_utc"] != _iso(source.standardized_state_created_at_utc)
            or int(standardized["schema_version"]) != source.source_schema_version
            or standardized["output_unit"] != source.state_unit
        ):
            raise DecisionStorageError("target-adjustment standardized-state source is inconsistent")

    @staticmethod
    def _source_values(source: LinkedTargetDecisionInput | None, prefix: str) -> dict[str, object]:
        if source is None:
            names = (
                "target_position_link_id", "linked_target_operation_id", "linked_parent_run_id",
                "linked_source_stage_id", "linked_target_stage_id", "target_child_run_id",
                "target_child_stage_id", "standardized_state_calculation_id",
                "standardized_state_run_id", "standardized_state_stage_id",
                "standardized_state_definition_id", "standardized_state_definition_version",
                "standardized_state_created_at_utc", "target_calculation_id",
                "target_definition_id", "target_definition_version", "target_created_at_utc",
                "symbol", "as_of_utc", "standardized_state_text",
                "research_capital_basis_usd_text", "current_position_value_usd_text",
                "target_fraction_text", "target_position_value_usd_text",
                "adjustment_value_usd_text", "source_direction", "link_created_at_utc",
                "source_schema_version", "target_schema_version", "link_schema_version",
                "currency", "state_unit", "input_schema_version",
            )
            return {f"{prefix}{name}": None for name in names}
        return {
            f"{prefix}target_position_link_id": str(source.target_position_link_id),
            f"{prefix}linked_target_operation_id": str(source.linked_target_operation_id),
            f"{prefix}linked_parent_run_id": str(source.linked_parent_run_id),
            f"{prefix}linked_source_stage_id": str(source.linked_source_stage_id),
            f"{prefix}linked_target_stage_id": str(source.linked_target_stage_id),
            f"{prefix}target_child_run_id": str(source.target_child_run_id),
            f"{prefix}target_child_stage_id": str(source.target_child_stage_id),
            f"{prefix}standardized_state_calculation_id": str(source.standardized_state_calculation_id),
            f"{prefix}standardized_state_run_id": str(source.standardized_state_run_id),
            f"{prefix}standardized_state_stage_id": str(source.standardized_state_stage_id),
            f"{prefix}standardized_state_definition_id": str(source.standardized_state_definition_id),
            f"{prefix}standardized_state_definition_version": source.standardized_state_definition_version,
            f"{prefix}standardized_state_created_at_utc": _iso(source.standardized_state_created_at_utc),
            f"{prefix}target_calculation_id": str(source.target_calculation_id),
            f"{prefix}target_definition_id": str(source.target_definition_id),
            f"{prefix}target_definition_version": source.target_definition_version,
            f"{prefix}target_created_at_utc": _iso(source.target_created_at_utc),
            f"{prefix}symbol": source.symbol,
            f"{prefix}as_of_utc": _iso(source.as_of_utc),
            f"{prefix}standardized_state_text": str(source.standardized_state),
            f"{prefix}research_capital_basis_usd_text": str(source.research_capital_basis_usd),
            f"{prefix}current_position_value_usd_text": str(source.current_position_value_usd),
            f"{prefix}target_fraction_text": str(source.target_fraction),
            f"{prefix}target_position_value_usd_text": str(source.target_position_value_usd),
            f"{prefix}adjustment_value_usd_text": str(source.adjustment_value_usd),
            f"{prefix}source_direction": source.source_direction,
            f"{prefix}link_created_at_utc": _iso(source.link_created_at_utc),
            f"{prefix}source_schema_version": source.source_schema_version,
            f"{prefix}target_schema_version": source.target_schema_version,
            f"{prefix}link_schema_version": source.link_schema_version,
            f"{prefix}currency": source.currency,
            f"{prefix}state_unit": source.state_unit,
            f"{prefix}input_schema_version": source.schema_version,
        }

    def _insert_operation(self, connection, operation) -> None:
        values = {
            "attempt_id": str(operation.attempt_id),
            "operation_id": str(operation.operation_id),
            "run_id": str(operation.run_id),
            "target_stage_id": str(operation.target_stage_id),
            "decision_stage_id": str(operation.decision_stage_id) if operation.decision_stage_id else None,
            "status": operation.status.value,
            "requested_at_utc": _iso(operation.requested_at_utc),
            "completed_at_utc": _iso(operation.completed_at_utc),
            "requested_target_position_link_id": str(operation.requested_target_position_link_id),
            "session_id": operation.session_id,
            "request_id": operation.request_id,
            "created_by": operation.created_by,
            "reason": operation.reason,
            "decision_result_id": str(operation.decision_result_id) if operation.decision_result_id else None,
            "error_code": operation.error_code,
            "error_summary": operation.error_summary,
            "schema_version": operation.schema_version,
        }
        source_values = self._source_values(operation.resolved_source, "resolved_")
        values.update(source_values)
        columns = tuple(values)
        connection.execute(
            f"INSERT INTO target_adjustment_decision_operations ({', '.join(columns)}) VALUES ({', '.join(':' + item for item in columns)})",
            values,
        )

    def _insert_result(self, connection, result) -> None:
        values = {
            "decision_result_id": str(result.decision_result_id),
            "operation_id": str(result.operation_id),
            "run_id": str(result.run_id),
            "stage_id": str(result.stage_id),
            **self._source_values(result.source, ""),
            "status": result.status.value,
            "action": result.action.value,
            "reason_codes_json": json.dumps(result.reason_codes),
            "created_at_utc": _iso(result.created_at_utc),
            "created_by": result.created_by,
            "reason": result.reason,
            "software_version": result.software_version,
            "source_revision": result.source_revision,
            "worktree_state": result.worktree_state,
            "policy_id": result.policy_id,
            "policy_version": result.policy_version,
            "schema_version": result.schema_version,
        }
        columns = tuple(values)
        connection.execute(
            f"INSERT INTO target_adjustment_decision_results ({', '.join(columns)}) VALUES ({', '.join(':' + item for item in columns)})",
            values,
        )

    @staticmethod
    def _insert_intent(connection, intent) -> None:
        values = {
            "intent_id": str(intent.intent_id),
            "decision_result_id": str(intent.decision_result_id),
            "operation_id": str(intent.operation_id),
            "run_id": str(intent.run_id),
            "stage_id": str(intent.stage_id),
            "target_position_link_id": str(intent.target_position_link_id),
            "target_calculation_id": str(intent.target_calculation_id),
            "symbol": intent.symbol,
            "as_of_utc": _iso(intent.as_of_utc),
            "action": intent.action.value,
            "current_exposure_usd_text": str(intent.current_exposure_usd),
            "target_exposure_usd_text": str(intent.target_exposure_usd),
            "desired_change_usd_text": str(intent.desired_change_usd),
            "requested_notional_usd_text": str(intent.requested_notional_usd),
            "reason_codes_json": json.dumps(intent.reason_codes),
            "created_at_utc": _iso(intent.created_at_utc),
            "policy_id": intent.policy_id,
            "policy_version": intent.policy_version,
            "currency": intent.currency,
            "schema_version": intent.schema_version,
        }
        columns = tuple(values)
        connection.execute(
            f"INSERT INTO target_adjustment_trade_intents ({', '.join(columns)}) VALUES ({', '.join(':' + item for item in columns)})",
            values,
        )

    @staticmethod
    def _insert_source_link(connection, link) -> None:
        values = {
            "source_link_id": str(link.source_link_id),
            "operation_id": str(link.operation_id),
            "decision_result_id": str(link.decision_result_id),
            "decision_run_id": str(link.decision_run_id),
            "decision_stage_id": str(link.decision_stage_id),
            "target_position_link_id": str(link.target_position_link_id),
            "linked_target_operation_id": str(link.linked_target_operation_id),
            "linked_parent_run_id": str(link.linked_parent_run_id),
            "target_child_run_id": str(link.target_child_run_id),
            "standardized_state_run_id": str(link.standardized_state_run_id),
            "target_calculation_id": str(link.target_calculation_id),
            "standardized_state_calculation_id": str(link.standardized_state_calculation_id),
            "created_at_utc": _iso(link.created_at_utc),
            "schema_version": link.schema_version,
        }
        columns = tuple(values)
        connection.execute(
            f"INSERT INTO target_adjustment_decision_source_links ({', '.join(columns)}) VALUES ({', '.join(':' + item for item in columns)})",
            values,
        )

    @staticmethod
    def _source_from_row(row, prefix: str) -> LinkedTargetDecisionInput | None:
        if row[f"{prefix}target_position_link_id"] is None:
            return None
        get = lambda name: row[f"{prefix}{name}"]
        return LinkedTargetDecisionInput(
            UUID(get("target_position_link_id")),
            UUID(get("linked_target_operation_id")),
            UUID(get("linked_parent_run_id")),
            UUID(get("linked_source_stage_id")),
            UUID(get("linked_target_stage_id")),
            UUID(get("target_child_run_id")),
            UUID(get("target_child_stage_id")),
            UUID(get("standardized_state_calculation_id")),
            UUID(get("standardized_state_run_id")),
            UUID(get("standardized_state_stage_id")),
            UUID(get("standardized_state_definition_id")),
            int(get("standardized_state_definition_version")),
            _datetime(get("standardized_state_created_at_utc")),
            UUID(get("target_calculation_id")),
            UUID(get("target_definition_id")),
            int(get("target_definition_version")),
            _datetime(get("target_created_at_utc")),
            get("symbol"),
            _datetime(get("as_of_utc")),
            Decimal(get("standardized_state_text")),
            Decimal(get("research_capital_basis_usd_text")),
            Decimal(get("current_position_value_usd_text")),
            Decimal(get("target_fraction_text")),
            Decimal(get("target_position_value_usd_text")),
            Decimal(get("adjustment_value_usd_text")),
            get("source_direction"),
            _datetime(get("link_created_at_utc")),
            int(get("source_schema_version")),
            int(get("target_schema_version")),
            int(get("link_schema_version")),
            get("currency"),
            get("state_unit"),
            int(get("input_schema_version")),
        )

    def _operation_from_row(self, row) -> TargetAdjustmentDecisionOperationAttempt:
        return TargetAdjustmentDecisionOperationAttempt(
            UUID(row["attempt_id"]),
            UUID(row["operation_id"]),
            UUID(row["run_id"]),
            UUID(row["target_stage_id"]),
            UUID(row["decision_stage_id"]) if row["decision_stage_id"] else None,
            TargetAdjustmentDecisionStatus(row["status"]),
            _datetime(row["requested_at_utc"]),
            _datetime(row["completed_at_utc"]),
            UUID(row["requested_target_position_link_id"]),
            row["session_id"],
            row["request_id"],
            row["created_by"],
            row["reason"],
            self._source_from_row(row, "resolved_"),
            UUID(row["decision_result_id"]) if row["decision_result_id"] else None,
            row["error_code"],
            row["error_summary"],
            int(row["schema_version"]),
        )

    def _result_from_row(self, connection, row) -> TargetAdjustmentDecisionResult:
        source = self._source_from_row(row, "")
        if source is None:
            raise sqlite3.DatabaseError("target-adjustment result is missing its source")
        intent_rows = connection.execute(
            """
            SELECT * FROM target_adjustment_trade_intents
            WHERE decision_result_id = ? ORDER BY intent_id
            """,
            (row["decision_result_id"],),
        ).fetchall()
        return TargetAdjustmentDecisionResult(
            UUID(row["decision_result_id"]),
            UUID(row["operation_id"]),
            UUID(row["run_id"]),
            UUID(row["stage_id"]),
            source,
            TargetAdjustmentDecisionStatus(row["status"]),
            DecisionAction(row["action"]),
            tuple(self._intent_from_row(item) for item in intent_rows),
            tuple(json.loads(row["reason_codes_json"])),
            _datetime(row["created_at_utc"]),
            row["created_by"],
            row["reason"],
            row["software_version"],
            row["source_revision"],
            row["worktree_state"],
            row["policy_id"],
            row["policy_version"],
            int(row["schema_version"]),
        )

    @staticmethod
    def _intent_from_row(row) -> TargetAdjustmentTradeIntent:
        return TargetAdjustmentTradeIntent(
            UUID(row["intent_id"]),
            UUID(row["decision_result_id"]),
            UUID(row["operation_id"]),
            UUID(row["run_id"]),
            UUID(row["stage_id"]),
            UUID(row["target_position_link_id"]),
            UUID(row["target_calculation_id"]),
            row["symbol"],
            _datetime(row["as_of_utc"]),
            DecisionAction(row["action"]),
            Decimal(row["current_exposure_usd_text"]),
            Decimal(row["target_exposure_usd_text"]),
            Decimal(row["desired_change_usd_text"]),
            Decimal(row["requested_notional_usd_text"]),
            tuple(json.loads(row["reason_codes_json"])),
            _datetime(row["created_at_utc"]),
            row["policy_id"],
            row["policy_version"],
            row["currency"],
            int(row["schema_version"]),
        )

    @staticmethod
    def _source_link_from_row(row) -> TargetAdjustmentDecisionSourceLink:
        return TargetAdjustmentDecisionSourceLink(
            UUID(row["source_link_id"]),
            UUID(row["operation_id"]),
            UUID(row["decision_result_id"]),
            UUID(row["decision_run_id"]),
            UUID(row["decision_stage_id"]),
            UUID(row["target_position_link_id"]),
            UUID(row["linked_target_operation_id"]),
            UUID(row["linked_parent_run_id"]),
            UUID(row["target_child_run_id"]),
            UUID(row["standardized_state_run_id"]),
            UUID(row["target_calculation_id"]),
            UUID(row["standardized_state_calculation_id"]),
            _datetime(row["created_at_utc"]),
            int(row["schema_version"]),
        )

    @staticmethod
    def _raise_storage(message: str, exc: Exception) -> None:
        if isinstance(exc, DecisionStorageError):
            raise exc
        raise DecisionStorageError(message) from exc


__all__ = ["SQLiteTargetAdjustmentDecisionStore"]
