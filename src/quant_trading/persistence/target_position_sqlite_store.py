"""SQLite adapter for bounded target-position definitions and preview evidence."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from uuid import UUID

from quant_trading.target_position import (
    LinkedTargetPositionOperationAttempt,
    LinkedTargetPositionOperationStatus,
    LinkedTargetPositionQuery,
    StandardizedStateTargetPositionLink,
    TargetPositionAdjustmentDirection,
    TargetPositionCalculationTrace,
    TargetPositionCurveDefinition,
    TargetPositionDefinitionQuery,
    TargetPositionDefinitionStatus,
    TargetPositionDirection,
    TargetPositionEvaluationMode,
    TargetPositionEvidenceBinding,
    TargetPositionEvidenceKind,
    TargetPositionKnot,
    TargetPositionKnotInput,
    TargetPositionOperationAttempt,
    TargetPositionOperationQuery,
    TargetPositionOperationStatus,
    TargetPositionOperationType,
    TargetPositionResult,
    TargetPositionResultQuery,
    TargetPositionStorageError,
)
from quant_trading.target_position.models import decimal_text

from .sqlite_database import CentralSQLiteDatabase


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="microseconds")


def _datetime(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value).astimezone(UTC) if value else None


def _decimal(value: str) -> Decimal:
    return Decimal(value)


class SQLiteTargetPositionStore:
    """Implement target-position Store/query ports in the central database."""

    def __init__(self, database_path: Path | str) -> None:
        self._database = CentralSQLiteDatabase(database_path)

    def initialize(self) -> None:
        self._database.initialize()

    def get_definition(self, definition_id: UUID) -> TargetPositionCurveDefinition | None:
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                "SELECT * FROM target_position_definitions WHERE definition_id = ?",
                (str(definition_id),),
            ).fetchone()
            return self._definition_from_row(connection, row) if row else None

    def get_first_operation(self, operation_id: UUID) -> TargetPositionOperationAttempt | None:
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                """
                SELECT * FROM target_position_operations WHERE operation_id = ?
                ORDER BY CASE status WHEN 'completed' THEN 0 ELSE 1 END, rowid LIMIT 1
                """,
                (str(operation_id),),
            ).fetchone()
            return self._operation_from_row(connection, row) if row else None

    def get_first_linked_operation(
        self, operation_id: UUID
    ) -> LinkedTargetPositionOperationAttempt | None:
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                """
                SELECT * FROM target_position_linked_preview_operations
                WHERE operation_id = ?
                ORDER BY CASE status WHEN 'completed' THEN 0 ELSE 1 END, rowid
                LIMIT 1
                """,
                (str(operation_id),),
            ).fetchone()
            return self._linked_operation_from_row(row) if row else None

    def get_standardized_state_link(
        self, operation_id: UUID
    ) -> StandardizedStateTargetPositionLink | None:
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                """
                SELECT * FROM target_position_standardized_state_links
                WHERE operation_id = ?
                """,
                (str(operation_id),),
            ).fetchone()
            return self._link_from_row(row) if row else None

    def save_operation(self, operation: TargetPositionOperationAttempt) -> None:
        with closing(self._database.connect()) as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                self._insert_operation(connection, operation)
                connection.commit()
            except Exception as exc:
                connection.rollback()
                self._raise_storage("could not save target-position operation", exc)

    def save_linked_operation(
        self, operation: LinkedTargetPositionOperationAttempt
    ) -> None:
        with closing(self._database.connect()) as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                self._insert_linked_operation(connection, operation)
                connection.commit()
            except Exception as exc:
                connection.rollback()
                self._raise_storage("could not save linked target-position operation", exc)

    def save_linked_failure(
        self,
        target_operation: TargetPositionOperationAttempt,
        linked_operation: LinkedTargetPositionOperationAttempt,
    ) -> None:
        if target_operation.status is TargetPositionOperationStatus.COMPLETED:
            raise TargetPositionStorageError("linked failure cannot contain a completed target operation")
        if linked_operation.status is LinkedTargetPositionOperationStatus.COMPLETED:
            raise TargetPositionStorageError("linked failure cannot contain a completed link operation")
        self._validate_linked_failure_identity(target_operation, linked_operation)
        with closing(self._database.connect()) as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                self._insert_operation(connection, target_operation)
                self._insert_linked_operation(connection, linked_operation)
                connection.commit()
            except Exception as exc:
                connection.rollback()
                self._raise_storage("could not save failed linked target-position evidence", exc)

    def save_linked_preview(
        self,
        result: TargetPositionResult,
        target_operation: TargetPositionOperationAttempt,
        linked_operation: LinkedTargetPositionOperationAttempt,
        link: StandardizedStateTargetPositionLink,
    ) -> None:
        if (
            target_operation.status is not TargetPositionOperationStatus.COMPLETED
            or linked_operation.status is not LinkedTargetPositionOperationStatus.COMPLETED
        ):
            raise TargetPositionStorageError("linked preview requires completed operations")
        if (
            target_operation.result_calculation_id != result.calculation_id
            or target_operation.operation_id != result.operation_id
            or target_operation.run_id != result.run_id
            or target_operation.stage_id != result.stage_id
            or target_operation.resolved_definition_id != result.definition_id
        ):
            raise TargetPositionStorageError("linked target result and operation are inconsistent")
        self._validate_preview_operation(result, target_operation)
        self._validate_completed_link_models(result, linked_operation, link)
        with closing(self._database.connect()) as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                self._validate_completed_link_database(
                    connection, result, linked_operation, link
                )
                self._insert_preview(connection, result, target_operation)
                self._insert_linked_operation(connection, linked_operation)
                self._insert_link(connection, link)
                connection.commit()
            except Exception as exc:
                connection.rollback()
                self._raise_storage("could not save linked target-position preview", exc)

    def create_definition(
        self,
        definition: TargetPositionCurveDefinition,
        operation: TargetPositionOperationAttempt,
    ) -> None:
        if (
            operation.operation_type is not TargetPositionOperationType.DEFINITION_SAVE
            or operation.status is not TargetPositionOperationStatus.COMPLETED
            or operation.resolved_definition_id != definition.definition_id
        ):
            raise TargetPositionStorageError("definition and operation identity is inconsistent")
        self._validate_definition_operation(definition, operation)
        with closing(self._database.connect()) as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                if definition.predecessor_definition_id is not None:
                    predecessor = connection.execute(
                        "SELECT definition_version FROM target_position_definitions WHERE definition_id = ?",
                        (str(definition.predecessor_definition_id),),
                    ).fetchone()
                    if predecessor is None or definition.definition_version != int(predecessor[0]) + 1:
                        raise TargetPositionStorageError("definition predecessor/version is invalid")
                elif definition.definition_version != 1:
                    raise TargetPositionStorageError("a root definition must use version 1")
                connection.execute(
                    """
                    INSERT INTO target_position_definitions (
                        definition_id, definition_version, predecessor_definition_id,
                        name, reason, direction, minimum_fraction_text,
                        neutral_fraction_text, maximum_fraction_text, status,
                        created_at_utc, created_by, schema_version
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(definition.definition_id), definition.definition_version,
                        str(definition.predecessor_definition_id) if definition.predecessor_definition_id else None,
                        definition.name, definition.reason, definition.direction.value,
                        str(definition.minimum_fraction), str(definition.neutral_fraction),
                        str(definition.maximum_fraction), definition.status.value,
                        _iso(definition.created_at_utc), definition.created_by,
                        definition.schema_version,
                    ),
                )
                connection.executemany(
                    """
                    INSERT INTO target_position_definition_knots (
                        definition_id, ordinal, state_value_text, target_fraction_text
                    ) VALUES (?, ?, ?, ?)
                    """,
                    (
                        (
                            str(definition.definition_id), item.ordinal,
                            str(item.state_value), str(item.target_fraction),
                        )
                        for item in definition.knots
                    ),
                )
                self._insert_operation(connection, operation)
                connection.commit()
            except Exception as exc:
                connection.rollback()
                self._raise_storage("could not save target-position definition", exc)

    def save_preview(
        self,
        result: TargetPositionResult,
        operation: TargetPositionOperationAttempt,
    ) -> None:
        if (
            operation.operation_type is not TargetPositionOperationType.PREVIEW
            or operation.status is not TargetPositionOperationStatus.COMPLETED
            or operation.result_calculation_id != result.calculation_id
            or operation.operation_id != result.operation_id
            or operation.run_id != result.run_id
            or operation.stage_id != result.stage_id
            or operation.resolved_definition_id != result.definition_id
        ):
            raise TargetPositionStorageError("preview result and operation identity is inconsistent")
        self._validate_preview_operation(result, operation)
        with closing(self._database.connect()) as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                self._insert_preview(connection, result, operation)
                connection.commit()
            except Exception as exc:
                connection.rollback()
                self._raise_storage("could not save target-position preview", exc)

    def list_definitions(
        self, query: TargetPositionDefinitionQuery = TargetPositionDefinitionQuery()
    ) -> tuple[TargetPositionCurveDefinition, ...]:
        clauses: list[str] = []
        parameters: list[object] = []
        if query.name_text and query.name_text.strip():
            clauses.append("LOWER(name) LIKE ?")
            parameters.append(f"%{query.name_text.strip().lower()}%")
        if query.status is not None:
            clauses.append("status = ?")
            parameters.append(query.status.value)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        parameters.append(query.limit)
        with closing(self._database.connect()) as connection:
            rows = connection.execute(
                f"""
                SELECT * FROM target_position_definitions {where}
                ORDER BY created_at_utc DESC, definition_id DESC LIMIT ?
                """,
                tuple(parameters),
            ).fetchall()
            return tuple(self._definition_from_row(connection, row) for row in rows)

    def list_results(
        self, query: TargetPositionResultQuery = TargetPositionResultQuery()
    ) -> tuple[TargetPositionResult, ...]:
        clauses: list[str] = []
        parameters: list[object] = []
        if query.definition_id is not None:
            clauses.append("definition_id = ?")
            parameters.append(str(query.definition_id))
        if query.direction is not None:
            clauses.append("adjustment_direction = ?")
            parameters.append(query.direction.value)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        parameters.append(query.limit)
        with closing(self._database.connect()) as connection:
            rows = connection.execute(
                f"""
                SELECT * FROM target_position_results {where}
                ORDER BY as_of_utc DESC, created_at_utc DESC, calculation_id DESC LIMIT ?
                """,
                tuple(parameters),
            ).fetchall()
            return tuple(self._result_from_row(connection, row) for row in rows)

    def get_result(self, calculation_id: UUID) -> TargetPositionResult | None:
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                "SELECT * FROM target_position_results WHERE calculation_id = ?",
                (str(calculation_id),),
            ).fetchone()
            return self._result_from_row(connection, row) if row else None

    def list_operations(
        self, query: TargetPositionOperationQuery = TargetPositionOperationQuery()
    ) -> tuple[TargetPositionOperationAttempt, ...]:
        clauses: list[str] = []
        parameters: list[object] = []
        if query.status is not None:
            clauses.append("status = ?")
            parameters.append(query.status.value)
        if query.operation_type is not None:
            clauses.append("operation_type = ?")
            parameters.append(query.operation_type.value)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        parameters.append(query.limit)
        with closing(self._database.connect()) as connection:
            rows = connection.execute(
                f"""
                SELECT * FROM target_position_operations {where}
                ORDER BY requested_at_utc DESC, attempt_id DESC LIMIT ?
                """,
                tuple(parameters),
            ).fetchall()
            return tuple(self._operation_from_row(connection, row) for row in rows)

    def list_linked_operations(
        self, query: LinkedTargetPositionQuery = LinkedTargetPositionQuery()
    ) -> tuple[LinkedTargetPositionOperationAttempt, ...]:
        clauses: list[str] = []
        parameters: list[object] = []
        if query.symbol is not None:
            clauses.append("resolved_symbol = ?")
            parameters.append(query.symbol)
        if query.source_definition_id is not None:
            clauses.append("resolved_source_definition_id = ?")
            parameters.append(str(query.source_definition_id))
        if query.target_definition_id is not None:
            clauses.append("resolved_target_definition_id = ?")
            parameters.append(str(query.target_definition_id))
        if query.status is not None:
            clauses.append("status = ?")
            parameters.append(query.status.value)
        if query.as_of_from_utc is not None:
            clauses.append("resolved_source_as_of_utc >= ?")
            parameters.append(_iso(query.as_of_from_utc))
        if query.as_of_to_utc is not None:
            clauses.append("resolved_source_as_of_utc < ?")
            parameters.append(_iso(query.as_of_to_utc))
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        parameters.append(query.limit)
        with closing(self._database.connect()) as connection:
            rows = connection.execute(
                f"""
                SELECT * FROM target_position_linked_preview_operations {where}
                ORDER BY requested_at_utc DESC, attempt_id DESC LIMIT ?
                """,
                tuple(parameters),
            ).fetchall()
            return tuple(self._linked_operation_from_row(row) for row in rows)

    def list_standardized_state_links(
        self, query: LinkedTargetPositionQuery = LinkedTargetPositionQuery()
    ) -> tuple[StandardizedStateTargetPositionLink, ...]:
        clauses: list[str] = []
        parameters: list[object] = []
        if query.symbol is not None:
            clauses.append("l.symbol = ?")
            parameters.append(query.symbol)
        if query.source_definition_id is not None:
            clauses.append("l.source_definition_id = ?")
            parameters.append(str(query.source_definition_id))
        if query.target_definition_id is not None:
            clauses.append("l.target_definition_id = ?")
            parameters.append(str(query.target_definition_id))
        if query.status is not None:
            clauses.append("o.status = ?")
            parameters.append(query.status.value)
        if query.as_of_from_utc is not None:
            clauses.append("l.source_as_of_utc >= ?")
            parameters.append(_iso(query.as_of_from_utc))
        if query.as_of_to_utc is not None:
            clauses.append("l.source_as_of_utc < ?")
            parameters.append(_iso(query.as_of_to_utc))
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        parameters.append(query.limit)
        with closing(self._database.connect()) as connection:
            rows = connection.execute(
                f"""
                SELECT l.* FROM target_position_standardized_state_links l
                JOIN target_position_linked_preview_operations o
                  ON o.operation_id = l.operation_id AND o.status = 'completed'
                {where}
                ORDER BY l.source_as_of_utc DESC, l.created_at_utc DESC, l.link_id DESC
                LIMIT ?
                """,
                tuple(parameters),
            ).fetchall()
            return tuple(self._link_from_row(row) for row in rows)

    def _insert_linked_operation(
        self,
        connection: sqlite3.Connection,
        operation: LinkedTargetPositionOperationAttempt,
    ) -> None:
        self._validate_linked_run_context(connection, operation)
        connection.execute(
            """
            INSERT INTO target_position_linked_preview_operations (
                attempt_id, operation_id, parent_run_id, source_stage_id,
                target_stage_id, child_run_id, child_stage_id, status,
                requested_at_utc, completed_at_utc,
                requested_source_calculation_id,
                requested_target_definition_id,
                research_capital_basis_usd_text,
                current_position_value_usd_text, session_id, request_id,
                created_by, reason, resolved_source_run_id,
                resolved_source_stage_id, resolved_source_definition_id,
                resolved_source_definition_version, resolved_symbol,
                resolved_source_as_of_utc, resolved_standardized_state_text,
                resolved_target_definition_id,
                resolved_target_definition_version,
                target_result_calculation_id, error_code, error_summary,
                schema_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(operation.attempt_id),
                str(operation.operation_id),
                str(operation.parent_run_id),
                str(operation.source_stage_id),
                str(operation.target_stage_id) if operation.target_stage_id else None,
                str(operation.child_run_id) if operation.child_run_id else None,
                str(operation.child_stage_id) if operation.child_stage_id else None,
                operation.status.value,
                _iso(operation.requested_at_utc),
                _iso(operation.completed_at_utc),
                str(operation.requested_source_calculation_id),
                str(operation.requested_target_definition_id),
                operation.research_capital_basis_usd_text,
                operation.current_position_value_usd_text,
                operation.session_id,
                operation.request_id,
                operation.created_by,
                operation.reason,
                str(operation.resolved_source_run_id)
                if operation.resolved_source_run_id
                else None,
                str(operation.resolved_source_stage_id)
                if operation.resolved_source_stage_id
                else None,
                str(operation.resolved_source_definition_id)
                if operation.resolved_source_definition_id
                else None,
                operation.resolved_source_definition_version,
                operation.resolved_symbol,
                _iso(operation.resolved_source_as_of_utc)
                if operation.resolved_source_as_of_utc
                else None,
                operation.resolved_standardized_state_text,
                str(operation.resolved_target_definition_id)
                if operation.resolved_target_definition_id
                else None,
                operation.resolved_target_definition_version,
                str(operation.target_result_calculation_id)
                if operation.target_result_calculation_id
                else None,
                operation.error_code,
                operation.error_summary,
                operation.schema_version,
            ),
        )

    @staticmethod
    def _insert_link(
        connection: sqlite3.Connection,
        link: StandardizedStateTargetPositionLink,
    ) -> None:
        connection.execute(
            """
            INSERT INTO target_position_standardized_state_links (
                link_id, operation_id, parent_run_id, source_stage_id,
                target_stage_id, child_run_id, child_stage_id,
                source_calculation_id, source_run_id,
                source_result_stage_id, source_definition_id,
                source_definition_version, symbol, source_as_of_utc,
                standardized_state_text, target_calculation_id,
                target_definition_id, target_definition_version,
                created_at_utc, created_by, reason, schema_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(link.link_id), str(link.operation_id), str(link.parent_run_id),
                str(link.source_stage_id), str(link.target_stage_id),
                str(link.child_run_id), str(link.child_stage_id),
                str(link.source_calculation_id), str(link.source_run_id),
                str(link.source_result_stage_id), str(link.source_definition_id),
                link.source_definition_version, link.symbol,
                _iso(link.source_as_of_utc), str(link.standardized_state),
                str(link.target_calculation_id), str(link.target_definition_id),
                link.target_definition_version, _iso(link.created_at_utc),
                link.created_by, link.reason, link.schema_version,
            ),
        )

    @staticmethod
    def _validate_linked_failure_identity(target_operation, linked_operation) -> None:
        if not (
            target_operation.operation_id == linked_operation.operation_id
            and target_operation.run_id == linked_operation.child_run_id
            and target_operation.stage_id == linked_operation.child_stage_id
            and target_operation.requested_definition_id
            == linked_operation.requested_target_definition_id
            and target_operation.research_capital_basis_usd_text
            == linked_operation.research_capital_basis_usd_text
            and target_operation.current_position_value_usd_text
            == linked_operation.current_position_value_usd_text
            and target_operation.created_by == linked_operation.created_by
            and target_operation.reason == linked_operation.reason
        ):
            raise TargetPositionStorageError(
                "failed target and linked operation evidence is inconsistent"
            )

    @staticmethod
    def _validate_completed_link_models(result, operation, link) -> None:
        try:
            matches = (
                operation.operation_id == link.operation_id == result.operation_id
                and operation.parent_run_id == link.parent_run_id
                and operation.source_stage_id == link.source_stage_id
                and operation.target_stage_id == link.target_stage_id
                and operation.child_run_id == link.child_run_id == result.run_id
                and operation.child_stage_id == link.child_stage_id == result.stage_id
                and operation.requested_source_calculation_id
                == link.source_calculation_id
                and operation.requested_target_definition_id
                == link.target_definition_id == result.definition_id
                and operation.resolved_source_run_id == link.source_run_id
                and operation.resolved_source_stage_id == link.source_result_stage_id
                and operation.resolved_source_definition_id
                == link.source_definition_id
                and operation.resolved_source_definition_version
                == link.source_definition_version
                and operation.resolved_symbol == link.symbol
                and operation.resolved_source_as_of_utc
                == link.source_as_of_utc == result.as_of_utc
                and decimal_text(
                    operation.resolved_standardized_state_text or "",
                    "resolved_standardized_state",
                )
                == link.standardized_state == result.research_state_value
                and decimal_text(
                    operation.research_capital_basis_usd_text,
                    "research_capital_basis_usd",
                )
                == result.research_capital_basis_usd
                and decimal_text(
                    operation.current_position_value_usd_text,
                    "current_position_value_usd",
                )
                == result.current_position_value_usd
                and operation.resolved_target_definition_id
                == link.target_definition_id
                and operation.resolved_target_definition_version
                == link.target_definition_version == result.definition_version
                and operation.target_result_calculation_id
                == link.target_calculation_id == result.calculation_id
                and operation.created_by == link.created_by == result.created_by
                and operation.reason == link.reason == result.reason
            )
        except Exception as exc:
            raise TargetPositionStorageError(
                "completed linked operation contains invalid evidence"
            ) from exc
        if not matches:
            raise TargetPositionStorageError(
                "completed linked operation does not match source and target results"
            )

    @staticmethod
    def _validate_linked_run_context(connection, operation) -> None:
        parent = connection.execute(
            "SELECT run_type, execution_mode FROM algorithm_runs WHERE run_id = ?",
            (str(operation.parent_run_id),),
        ).fetchone()
        if (
            parent is None
            or parent["run_type"] != "standardized_target_position_preview"
            or parent["execution_mode"] != "no_execution"
        ):
            raise TargetPositionStorageError(
                "linked operation requires its exact NO EXECUTION parent Run"
            )
        source_stage = connection.execute(
            "SELECT run_id, stage_name FROM algorithm_run_stages WHERE stage_id = ?",
            (str(operation.source_stage_id),),
        ).fetchone()
        if (
            source_stage is None
            or source_stage["run_id"] != str(operation.parent_run_id)
            or source_stage["stage_name"] != "standardized_state"
        ):
            raise TargetPositionStorageError(
                "linked source stage must belong to the exact parent Run"
            )
        if operation.target_stage_id is not None:
            target_stage = connection.execute(
                "SELECT run_id, stage_name FROM algorithm_run_stages WHERE stage_id = ?",
                (str(operation.target_stage_id),),
            ).fetchone()
            if (
                target_stage is None
                or target_stage["run_id"] != str(operation.parent_run_id)
                or target_stage["stage_name"] != "target_position"
            ):
                raise TargetPositionStorageError(
                    "linked target stage must belong to the exact parent Run"
                )
        child_fields = (operation.child_run_id, operation.child_stage_id)
        if any(item is not None for item in child_fields):
            if any(item is None for item in child_fields):
                raise TargetPositionStorageError(
                    "linked child Run and stage must be supplied together"
                )
            child = connection.execute(
                "SELECT parent_run_id, run_type, execution_mode FROM algorithm_runs WHERE run_id = ?",
                (str(operation.child_run_id),),
            ).fetchone()
            child_stage = connection.execute(
                "SELECT run_id, stage_name FROM algorithm_run_stages WHERE stage_id = ?",
                (str(operation.child_stage_id),),
            ).fetchone()
            if (
                child is None
                or child["parent_run_id"] != str(operation.parent_run_id)
                or child["run_type"] != "target_position_preview"
                or child["execution_mode"] != "no_execution"
                or child_stage is None
                or child_stage["run_id"] != str(operation.child_run_id)
                or child_stage["stage_name"] != "target_position"
            ):
                raise TargetPositionStorageError(
                    "linked child must be the exact Target Position NO EXECUTION Run/Stage"
                )

    @staticmethod
    def _validate_completed_link_database(connection, result, operation, link) -> None:
        SQLiteTargetPositionStore._validate_linked_run_context(connection, operation)
        source = connection.execute(
            "SELECT * FROM standardized_state_results WHERE calculation_id = ?",
            (str(link.source_calculation_id),),
        ).fetchone()
        if source is None:
            raise TargetPositionStorageError("linked standardized-state source is unavailable")
        source_stage = connection.execute(
            """
            SELECT s.run_id, s.stage_name, r.run_type, r.execution_mode
            FROM algorithm_run_stages s
            JOIN algorithm_runs r ON r.run_id = s.run_id
            WHERE s.stage_id = ?
            """,
            (str(link.source_result_stage_id),),
        ).fetchone()
        source_matches = (
            source["run_id"] == str(link.source_run_id)
            and source["stage_id"] == str(link.source_result_stage_id)
            and source["definition_id"] == str(link.source_definition_id)
            and int(source["definition_version"]) == link.source_definition_version
            and source["symbol"] == link.symbol
            and _datetime(source["as_of_utc"]) == link.source_as_of_utc
            and _decimal(source["standardized_state_text"])
            == link.standardized_state
            and source["output_unit"] == "dimensionless"
            and int(source["schema_version"]) == 1
            and source_stage is not None
            and source_stage["run_id"] == str(link.source_run_id)
            and source_stage["stage_name"] == "standardized_state"
            and source_stage["run_type"] == "standardized_state_preview"
            and source_stage["execution_mode"] == "no_execution"
        )
        if not source_matches:
            raise TargetPositionStorageError(
                "linked source identity, unit, value or Run provenance is inconsistent"
            )
        if not (
            link.child_run_id == result.run_id
            and link.child_stage_id == result.stage_id
            and link.target_calculation_id == result.calculation_id
            and link.target_definition_id == result.definition_id
            and link.target_definition_version == result.definition_version
            and link.source_as_of_utc == result.as_of_utc
            and link.standardized_state == result.research_state_value
        ):
            raise TargetPositionStorageError(
                "linked target result identity or copied source fields are inconsistent"
            )
        for run_id in (link.parent_run_id, link.child_run_id):
            symbols = tuple(
                row["symbol"]
                for row in connection.execute(
                    "SELECT symbol FROM algorithm_run_symbols WHERE run_id = ? ORDER BY symbol",
                    (str(run_id),),
                )
            )
            if symbols != (link.symbol,):
                raise TargetPositionStorageError(
                    "linked parent and child Run symbols must equal the source symbol"
                )

    @staticmethod
    def _linked_operation_from_row(row) -> LinkedTargetPositionOperationAttempt:
        return LinkedTargetPositionOperationAttempt(
            UUID(row["attempt_id"]),
            UUID(row["operation_id"]),
            UUID(row["parent_run_id"]),
            UUID(row["source_stage_id"]),
            UUID(row["target_stage_id"]) if row["target_stage_id"] else None,
            UUID(row["child_run_id"]) if row["child_run_id"] else None,
            UUID(row["child_stage_id"]) if row["child_stage_id"] else None,
            LinkedTargetPositionOperationStatus(row["status"]),
            _datetime(row["requested_at_utc"]),
            _datetime(row["completed_at_utc"]),
            UUID(row["requested_source_calculation_id"]),
            UUID(row["requested_target_definition_id"]),
            row["research_capital_basis_usd_text"],
            row["current_position_value_usd_text"],
            row["session_id"],
            row["request_id"],
            row["created_by"],
            row["reason"],
            UUID(row["resolved_source_run_id"])
            if row["resolved_source_run_id"]
            else None,
            UUID(row["resolved_source_stage_id"])
            if row["resolved_source_stage_id"]
            else None,
            UUID(row["resolved_source_definition_id"])
            if row["resolved_source_definition_id"]
            else None,
            int(row["resolved_source_definition_version"])
            if row["resolved_source_definition_version"] is not None
            else None,
            row["resolved_symbol"],
            _datetime(row["resolved_source_as_of_utc"]),
            row["resolved_standardized_state_text"],
            UUID(row["resolved_target_definition_id"])
            if row["resolved_target_definition_id"]
            else None,
            int(row["resolved_target_definition_version"])
            if row["resolved_target_definition_version"] is not None
            else None,
            UUID(row["target_result_calculation_id"])
            if row["target_result_calculation_id"]
            else None,
            row["error_code"],
            row["error_summary"],
            int(row["schema_version"]),
        )

    @staticmethod
    def _link_from_row(row) -> StandardizedStateTargetPositionLink:
        return StandardizedStateTargetPositionLink(
            UUID(row["link_id"]), UUID(row["operation_id"]),
            UUID(row["parent_run_id"]), UUID(row["source_stage_id"]),
            UUID(row["target_stage_id"]), UUID(row["child_run_id"]),
            UUID(row["child_stage_id"]), UUID(row["source_calculation_id"]),
            UUID(row["source_run_id"]), UUID(row["source_result_stage_id"]),
            UUID(row["source_definition_id"]), int(row["source_definition_version"]),
            row["symbol"], _datetime(row["source_as_of_utc"]),
            _decimal(row["standardized_state_text"]),
            UUID(row["target_calculation_id"]), UUID(row["target_definition_id"]),
            int(row["target_definition_version"]), _datetime(row["created_at_utc"]),
            row["created_by"], row["reason"], int(row["schema_version"]),
        )

    def _insert_preview(
        self,
        connection: sqlite3.Connection,
        result: TargetPositionResult,
        operation: TargetPositionOperationAttempt,
    ) -> None:
        definition = connection.execute(
            "SELECT definition_version FROM target_position_definitions WHERE definition_id = ?",
            (str(result.definition_id),),
        ).fetchone()
        if definition is None or int(definition[0]) != result.definition_version:
            raise TargetPositionStorageError("preview definition/version is unavailable")
        self._validate_stage(connection, result.run_id, result.stage_id)
        self._insert_operation(connection, operation)
        trace = result.trace
        connection.execute(
            """
            INSERT INTO target_position_results (
                calculation_id, operation_id, run_id, stage_id,
                definition_id, definition_version, as_of_utc,
                research_state_value_text, research_capital_basis_usd_text,
                current_position_value_usd_text, target_fraction_text,
                target_position_value_usd_text, adjustment_value_usd_text,
                adjustment_direction, evaluation_mode, lower_knot_ordinal,
                upper_knot_ordinal, lower_state_value_text, upper_state_value_text,
                lower_target_fraction_text, upper_target_fraction_text,
                interpolation_numerator_text, interpolation_denominator_text,
                interpolation_weight_text, created_at_utc, created_by, reason,
                schema_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(result.calculation_id), str(result.operation_id),
                str(result.run_id), str(result.stage_id), str(result.definition_id),
                result.definition_version, _iso(result.as_of_utc),
                str(result.research_state_value), str(result.research_capital_basis_usd),
                str(result.current_position_value_usd), str(result.target_fraction),
                str(result.target_position_value_usd), str(result.adjustment_value_usd),
                result.adjustment_direction.value, trace.evaluation_mode.value,
                trace.lower_knot_ordinal, trace.upper_knot_ordinal,
                str(trace.lower_state_value), str(trace.upper_state_value),
                str(trace.lower_target_fraction), str(trace.upper_target_fraction),
                str(trace.interpolation_numerator), str(trace.interpolation_denominator),
                str(trace.interpolation_weight), _iso(result.created_at_utc),
                result.created_by, result.reason, result.schema_version,
            ),
        )
        self._insert_evidence(
            connection,
            "target_position_result_evidence",
            "calculation_id",
            result.calculation_id,
            result.evidence_bindings,
        )

    def _insert_operation(
        self, connection: sqlite3.Connection, operation: TargetPositionOperationAttempt
    ) -> None:
        self._validate_stage(connection, operation.run_id, operation.stage_id)
        resolved = None
        if operation.resolved_definition_id is not None:
            row = connection.execute(
                "SELECT 1 FROM target_position_definitions WHERE definition_id = ?",
                (str(operation.resolved_definition_id),),
            ).fetchone()
            resolved = str(operation.resolved_definition_id) if row else None
        connection.execute(
            """
            INSERT INTO target_position_operations (
                attempt_id, operation_id, run_id, stage_id, operation_type, status,
                requested_at_utc, completed_at_utc, created_by, reason,
                definition_name, direction, minimum_fraction_text,
                neutral_fraction_text, maximum_fraction_text,
                predecessor_definition_id, requested_definition_id,
                resolved_definition_id, research_state_value_text,
                research_capital_basis_usd_text, current_position_value_usd_text,
                as_of_utc, result_calculation_id, error_code, error_summary
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(operation.attempt_id), str(operation.operation_id), str(operation.run_id),
                str(operation.stage_id), operation.operation_type.value, operation.status.value,
                _iso(operation.requested_at_utc), _iso(operation.completed_at_utc),
                operation.created_by, operation.reason, operation.definition_name,
                operation.direction, operation.minimum_fraction_text,
                operation.neutral_fraction_text, operation.maximum_fraction_text,
                str(operation.predecessor_definition_id) if operation.predecessor_definition_id else None,
                str(operation.requested_definition_id) if operation.requested_definition_id else None,
                resolved, operation.research_state_value_text,
                operation.research_capital_basis_usd_text,
                operation.current_position_value_usd_text,
                _iso(operation.as_of_utc) if operation.as_of_utc else None,
                str(operation.result_calculation_id) if operation.result_calculation_id else None,
                operation.error_code, operation.error_summary,
            ),
        )
        connection.executemany(
            """
            INSERT INTO target_position_operation_knots (
                attempt_id, ordinal, state_value_text, target_fraction_text
            ) VALUES (?, ?, ?, ?)
            """,
            (
                (str(operation.attempt_id), index, item.state_value, item.target_fraction)
                for index, item in enumerate(operation.knot_inputs)
            ),
        )
        self._insert_evidence(
            connection,
            "target_position_operation_evidence_inputs",
            "attempt_id",
            operation.attempt_id,
            operation.evidence_bindings,
        )

    @staticmethod
    def _insert_evidence(connection, table, id_column, object_id, bindings) -> None:
        connection.executemany(
            f"""
            INSERT INTO {table} (
                {id_column}, ordinal, evidence_kind, evidence_id,
                source_component, source_version
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                (
                    str(object_id), index, item.evidence_kind.value, item.evidence_id,
                    item.source_component, item.source_version,
                )
                for index, item in enumerate(bindings)
            ),
        )

    @staticmethod
    def _validate_stage(connection, run_id: UUID, stage_id: UUID) -> None:
        row = connection.execute(
            "SELECT run_id FROM algorithm_run_stages WHERE stage_id = ?",
            (str(stage_id),),
        ).fetchone()
        if row is None or row["run_id"] != str(run_id):
            raise TargetPositionStorageError("operation stage must belong to its exact Run")

    @staticmethod
    def _validate_definition_operation(definition, operation) -> None:
        try:
            raw_knots = tuple(
                (
                    decimal_text(item.state_value, f"knot[{index}].state_value"),
                    decimal_text(item.target_fraction, f"knot[{index}].target_fraction"),
                )
                for index, item in enumerate(operation.knot_inputs)
            )
            accepted_knots = tuple(
                (item.state_value, item.target_fraction) for item in definition.knots
            )
            matches = (
                operation.definition_name == definition.name
                and operation.reason == definition.reason
                and operation.direction == definition.direction.value
                and decimal_text(operation.minimum_fraction_text or "", "minimum_fraction")
                == definition.minimum_fraction
                and decimal_text(operation.neutral_fraction_text or "", "neutral_fraction")
                == definition.neutral_fraction
                and decimal_text(operation.maximum_fraction_text or "", "maximum_fraction")
                == definition.maximum_fraction
                and operation.predecessor_definition_id == definition.predecessor_definition_id
                and raw_knots == accepted_knots
                and operation.created_by == definition.created_by
            )
        except Exception as exc:
            raise TargetPositionStorageError(
                "completed definition operation contains invalid raw evidence"
            ) from exc
        if not matches:
            raise TargetPositionStorageError(
                "completed definition operation does not match the accepted definition"
            )

    @staticmethod
    def _validate_preview_operation(result, operation) -> None:
        try:
            matches = (
                operation.requested_definition_id == result.definition_id
                and decimal_text(operation.research_state_value_text or "", "research_state_value")
                == result.research_state_value
                and decimal_text(
                    operation.research_capital_basis_usd_text or "", "research_capital_basis_usd"
                ) == result.research_capital_basis_usd
                and decimal_text(
                    operation.current_position_value_usd_text or "", "current_position_value_usd"
                ) == result.current_position_value_usd
                and operation.as_of_utc == result.as_of_utc
                and operation.evidence_bindings == result.evidence_bindings
                and operation.created_by == result.created_by
                and operation.reason == result.reason
            )
        except Exception as exc:
            raise TargetPositionStorageError(
                "completed preview operation contains invalid raw evidence"
            ) from exc
        if not matches:
            raise TargetPositionStorageError(
                "completed preview operation does not match the accepted result"
            )

    @staticmethod
    def _evidence_from_rows(rows) -> tuple[TargetPositionEvidenceBinding, ...]:
        return tuple(
            TargetPositionEvidenceBinding(
                TargetPositionEvidenceKind(row["evidence_kind"]), row["evidence_id"],
                row["source_component"], row["source_version"],
            )
            for row in rows
        )

    @staticmethod
    def _definition_from_row(connection, row) -> TargetPositionCurveDefinition:
        knots = connection.execute(
            """
            SELECT * FROM target_position_definition_knots
            WHERE definition_id = ? ORDER BY ordinal
            """,
            (row["definition_id"],),
        ).fetchall()
        return TargetPositionCurveDefinition(
            UUID(row["definition_id"]), int(row["definition_version"]),
            UUID(row["predecessor_definition_id"]) if row["predecessor_definition_id"] else None,
            row["name"], row["reason"], TargetPositionDirection(row["direction"]),
            _decimal(row["minimum_fraction_text"]),
            _decimal(row["neutral_fraction_text"]),
            _decimal(row["maximum_fraction_text"]),
            tuple(
                TargetPositionKnot(
                    int(item["ordinal"]), _decimal(item["state_value_text"]),
                    _decimal(item["target_fraction_text"]),
                )
                for item in knots
            ),
            TargetPositionDefinitionStatus(row["status"]),
            _datetime(row["created_at_utc"]), row["created_by"], int(row["schema_version"]),
        )

    @classmethod
    def _result_from_row(cls, connection, row) -> TargetPositionResult:
        evidence = connection.execute(
            """
            SELECT * FROM target_position_result_evidence
            WHERE calculation_id = ? ORDER BY ordinal
            """,
            (row["calculation_id"],),
        ).fetchall()
        trace = TargetPositionCalculationTrace(
            TargetPositionEvaluationMode(row["evaluation_mode"]),
            int(row["lower_knot_ordinal"]), int(row["upper_knot_ordinal"]),
            _decimal(row["lower_state_value_text"]), _decimal(row["upper_state_value_text"]),
            _decimal(row["lower_target_fraction_text"]),
            _decimal(row["upper_target_fraction_text"]),
            _decimal(row["interpolation_numerator_text"]),
            _decimal(row["interpolation_denominator_text"]),
            _decimal(row["interpolation_weight_text"]),
        )
        return TargetPositionResult(
            UUID(row["calculation_id"]), UUID(row["operation_id"]), UUID(row["run_id"]),
            UUID(row["stage_id"]), UUID(row["definition_id"]),
            int(row["definition_version"]), _datetime(row["as_of_utc"]),
            _decimal(row["research_state_value_text"]),
            _decimal(row["research_capital_basis_usd_text"]),
            _decimal(row["current_position_value_usd_text"]),
            _decimal(row["target_fraction_text"]),
            _decimal(row["target_position_value_usd_text"]),
            _decimal(row["adjustment_value_usd_text"]),
            TargetPositionAdjustmentDirection(row["adjustment_direction"]),
            trace, cls._evidence_from_rows(evidence), _datetime(row["created_at_utc"]),
            row["created_by"], row["reason"], int(row["schema_version"]),
        )

    @classmethod
    def _operation_from_row(cls, connection, row) -> TargetPositionOperationAttempt:
        knots = connection.execute(
            """
            SELECT * FROM target_position_operation_knots
            WHERE attempt_id = ? ORDER BY ordinal
            """,
            (row["attempt_id"],),
        ).fetchall()
        evidence = connection.execute(
            """
            SELECT * FROM target_position_operation_evidence_inputs
            WHERE attempt_id = ? ORDER BY ordinal
            """,
            (row["attempt_id"],),
        ).fetchall()
        return TargetPositionOperationAttempt(
            UUID(row["attempt_id"]), UUID(row["operation_id"]), UUID(row["run_id"]),
            UUID(row["stage_id"]), TargetPositionOperationType(row["operation_type"]),
            TargetPositionOperationStatus(row["status"]),
            _datetime(row["requested_at_utc"]), _datetime(row["completed_at_utc"]),
            row["created_by"], row["reason"], definition_name=row["definition_name"],
            direction=row["direction"], minimum_fraction_text=row["minimum_fraction_text"],
            neutral_fraction_text=row["neutral_fraction_text"],
            maximum_fraction_text=row["maximum_fraction_text"],
            knot_inputs=tuple(
                TargetPositionKnotInput(item["state_value_text"], item["target_fraction_text"])
                for item in knots
            ),
            predecessor_definition_id=UUID(row["predecessor_definition_id"]) if row["predecessor_definition_id"] else None,
            requested_definition_id=UUID(row["requested_definition_id"]) if row["requested_definition_id"] else None,
            resolved_definition_id=UUID(row["resolved_definition_id"]) if row["resolved_definition_id"] else None,
            research_state_value_text=row["research_state_value_text"],
            research_capital_basis_usd_text=row["research_capital_basis_usd_text"],
            current_position_value_usd_text=row["current_position_value_usd_text"],
            as_of_utc=_datetime(row["as_of_utc"]),
            evidence_bindings=cls._evidence_from_rows(evidence),
            result_calculation_id=UUID(row["result_calculation_id"]) if row["result_calculation_id"] else None,
            error_code=row["error_code"], error_summary=row["error_summary"],
        )

    @staticmethod
    def _raise_storage(message: str, exc: BaseException) -> None:
        if isinstance(exc, TargetPositionStorageError):
            raise exc
        raise TargetPositionStorageError(message) from exc


__all__ = ["SQLiteTargetPositionStore"]
