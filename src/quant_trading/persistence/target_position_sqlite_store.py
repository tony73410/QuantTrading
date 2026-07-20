"""SQLite adapter for bounded target-position definitions and preview evidence."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from uuid import UUID

from quant_trading.target_position import (
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

    def save_operation(self, operation: TargetPositionOperationAttempt) -> None:
        with closing(self._database.connect()) as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                self._insert_operation(connection, operation)
                connection.commit()
            except Exception as exc:
                connection.rollback()
                self._raise_storage("could not save target-position operation", exc)

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
