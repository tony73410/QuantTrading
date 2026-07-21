"""SQLite adapter for manual standardized-price-state Factor evidence."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from uuid import UUID

from quant_trading.factors.errors import StandardizedPriceStateStorageError
from quant_trading.factors.standardized_state_models import (
    StandardizedPriceStateDefinition,
    StandardizedPriceStateDefinitionQuery,
    StandardizedPriceStateDefinitionStatus,
    StandardizedPriceStateEvidenceBinding,
    StandardizedPriceStateEvidenceKind,
    StandardizedPriceStateInputSource,
    StandardizedPriceStateOperationAttempt,
    StandardizedPriceStateOperationQuery,
    StandardizedPriceStateOperationStatus,
    StandardizedPriceStateOperationType,
    StandardizedPriceStateResult,
    StandardizedPriceStateResultQuery,
    StandardizedPriceStateTrace,
    decimal_text,
    normalized_symbol,
)

from .sqlite_database import CentralSQLiteDatabase


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="microseconds")


def _datetime(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value).astimezone(UTC) if value else None


def _decimal(value: str) -> Decimal:
    return Decimal(value)


class SQLiteStandardizedPriceStateStore:
    """Implement Factor-owned standardized-state Store/query ports."""

    def __init__(self, database_path: Path | str) -> None:
        self._database = CentralSQLiteDatabase(database_path)

    def initialize(self) -> None:
        self._database.initialize()

    def get_definition(
        self, definition_id: UUID
    ) -> StandardizedPriceStateDefinition | None:
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                "SELECT * FROM standardized_state_definitions WHERE definition_id = ?",
                (str(definition_id),),
            ).fetchone()
            return self._definition_from_row(row) if row else None

    def get_first_operation(
        self, operation_id: UUID
    ) -> StandardizedPriceStateOperationAttempt | None:
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                """
                SELECT * FROM standardized_state_operations
                WHERE operation_id = ?
                ORDER BY CASE status WHEN 'completed' THEN 0 ELSE 1 END, rowid
                LIMIT 1
                """,
                (str(operation_id),),
            ).fetchone()
            return self._operation_from_row(connection, row) if row else None

    def save_operation(
        self, operation: StandardizedPriceStateOperationAttempt
    ) -> None:
        with closing(self._database.connect()) as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                self._insert_operation(connection, operation)
                connection.commit()
            except Exception as exc:
                connection.rollback()
                self._raise_storage(
                    "could not save standardized-state operation", exc
                )

    def create_definition(
        self,
        definition: StandardizedPriceStateDefinition,
        operation: StandardizedPriceStateOperationAttempt,
    ) -> None:
        if (
            operation.operation_type
            is not StandardizedPriceStateOperationType.DEFINITION_SAVE
            or operation.status
            is not StandardizedPriceStateOperationStatus.COMPLETED
            or operation.resolved_definition_id != definition.definition_id
        ):
            raise StandardizedPriceStateStorageError(
                "definition and operation identity is inconsistent"
            )
        self._validate_definition_operation(definition, operation)
        with closing(self._database.connect()) as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                if definition.predecessor_definition_id is not None:
                    predecessor = connection.execute(
                        """
                        SELECT definition_version
                        FROM standardized_state_definitions
                        WHERE definition_id = ?
                        """,
                        (str(definition.predecessor_definition_id),),
                    ).fetchone()
                    if (
                        predecessor is None
                        or definition.definition_version != int(predecessor[0]) + 1
                    ):
                        raise StandardizedPriceStateStorageError(
                            "definition predecessor/version is invalid"
                        )
                elif definition.definition_version != 1:
                    raise StandardizedPriceStateStorageError(
                        "a root definition must use version 1"
                    )
                connection.execute(
                    """
                    INSERT INTO standardized_state_definitions (
                        definition_id, definition_version,
                        predecessor_definition_id, name, reason, formula_id,
                        price_currency, output_unit, price_source,
                        reference_source, risk_scale_source, status,
                        created_at_utc, created_by, schema_version
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(definition.definition_id),
                        definition.definition_version,
                        str(definition.predecessor_definition_id)
                        if definition.predecessor_definition_id
                        else None,
                        definition.name,
                        definition.reason,
                        definition.formula_id,
                        definition.price_currency,
                        definition.output_unit,
                        definition.price_source.value,
                        definition.reference_source.value,
                        definition.risk_scale_source.value,
                        definition.status.value,
                        _iso(definition.created_at_utc),
                        definition.created_by,
                        definition.schema_version,
                    ),
                )
                self._insert_operation(connection, operation)
                connection.commit()
            except Exception as exc:
                connection.rollback()
                self._raise_storage(
                    "could not save standardized-state definition", exc
                )

    def save_preview(
        self,
        result: StandardizedPriceStateResult,
        operation: StandardizedPriceStateOperationAttempt,
    ) -> None:
        if (
            operation.operation_type is not StandardizedPriceStateOperationType.PREVIEW
            or operation.status
            is not StandardizedPriceStateOperationStatus.COMPLETED
            or operation.result_calculation_id != result.calculation_id
            or operation.operation_id != result.operation_id
            or operation.run_id != result.run_id
            or operation.stage_id != result.stage_id
            or operation.resolved_definition_id != result.definition_id
        ):
            raise StandardizedPriceStateStorageError(
                "preview result and operation identity is inconsistent"
            )
        self._validate_preview_operation(result, operation)
        with closing(self._database.connect()) as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                definition_row = connection.execute(
                    """
                    SELECT * FROM standardized_state_definitions
                    WHERE definition_id = ?
                    """,
                    (str(result.definition_id),),
                ).fetchone()
                if definition_row is None:
                    raise StandardizedPriceStateStorageError(
                        "preview definition is unavailable"
                    )
                definition = self._definition_from_row(definition_row)
                if definition.definition_version != result.definition_version:
                    raise StandardizedPriceStateStorageError(
                        "preview definition version is inconsistent"
                    )
                if (
                    result.trace.formula_id != definition.formula_id
                    or result.trace.price_currency != definition.price_currency
                    or result.trace.output_unit != definition.output_unit
                    or result.trace.price_source is not definition.price_source
                    or result.trace.reference_source is not definition.reference_source
                    or result.trace.risk_scale_source is not definition.risk_scale_source
                ):
                    raise StandardizedPriceStateStorageError(
                        "result trace does not match its exact definition"
                    )
                self._validate_stage(connection, result.run_id, result.stage_id)
                self._insert_operation(connection, operation)
                trace = result.trace
                connection.execute(
                    """
                    INSERT INTO standardized_state_results (
                        calculation_id, operation_id, run_id, stage_id,
                        definition_id, definition_version, symbol, as_of_utc,
                        manual_price_usd_text, manual_reference_price_usd_text,
                        manual_risk_scale_usd_text, price_deviation_usd_text,
                        standardized_state_text, formula_id, price_currency,
                        output_unit, price_source, reference_source,
                        risk_scale_source, created_at_utc, created_by, reason,
                        schema_version
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(result.calculation_id),
                        str(result.operation_id),
                        str(result.run_id),
                        str(result.stage_id),
                        str(result.definition_id),
                        result.definition_version,
                        result.symbol,
                        _iso(result.as_of_utc),
                        str(result.manual_price_usd),
                        str(result.manual_reference_price_usd),
                        str(result.manual_risk_scale_usd),
                        str(result.price_deviation_usd),
                        str(result.standardized_state),
                        trace.formula_id,
                        trace.price_currency,
                        trace.output_unit,
                        trace.price_source.value,
                        trace.reference_source.value,
                        trace.risk_scale_source.value,
                        _iso(result.created_at_utc),
                        result.created_by,
                        result.reason,
                        result.schema_version,
                    ),
                )
                self._insert_evidence(
                    connection,
                    "standardized_state_result_evidence",
                    "calculation_id",
                    result.calculation_id,
                    result.evidence_bindings,
                )
                connection.commit()
            except Exception as exc:
                connection.rollback()
                self._raise_storage(
                    "could not save standardized-state preview", exc
                )

    def list_definitions(
        self,
        query: StandardizedPriceStateDefinitionQuery = StandardizedPriceStateDefinitionQuery(),
    ) -> tuple[StandardizedPriceStateDefinition, ...]:
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
                SELECT * FROM standardized_state_definitions {where}
                ORDER BY created_at_utc DESC, definition_id DESC LIMIT ?
                """,
                tuple(parameters),
            ).fetchall()
            return tuple(self._definition_from_row(row) for row in rows)

    def list_results(
        self,
        query: StandardizedPriceStateResultQuery = StandardizedPriceStateResultQuery(),
    ) -> tuple[StandardizedPriceStateResult, ...]:
        clauses: list[str] = []
        parameters: list[object] = []
        if query.symbol is not None:
            clauses.append("symbol = ?")
            parameters.append(query.symbol)
        if query.definition_id is not None:
            clauses.append("definition_id = ?")
            parameters.append(str(query.definition_id))
        if query.as_of_from_utc is not None:
            clauses.append("as_of_utc >= ?")
            parameters.append(_iso(query.as_of_from_utc))
        if query.as_of_to_utc is not None:
            clauses.append("as_of_utc < ?")
            parameters.append(_iso(query.as_of_to_utc))
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        parameters.append(query.limit)
        with closing(self._database.connect()) as connection:
            rows = connection.execute(
                f"""
                SELECT * FROM standardized_state_results {where}
                ORDER BY as_of_utc DESC, created_at_utc DESC, calculation_id DESC
                LIMIT ?
                """,
                tuple(parameters),
            ).fetchall()
            return tuple(self._result_from_row(connection, row) for row in rows)

    def get_result(
        self, calculation_id: UUID
    ) -> StandardizedPriceStateResult | None:
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                """
                SELECT * FROM standardized_state_results WHERE calculation_id = ?
                """,
                (str(calculation_id),),
            ).fetchone()
            return self._result_from_row(connection, row) if row else None

    def list_operations(
        self,
        query: StandardizedPriceStateOperationQuery = StandardizedPriceStateOperationQuery(),
    ) -> tuple[StandardizedPriceStateOperationAttempt, ...]:
        clauses: list[str] = []
        parameters: list[object] = []
        if query.symbol is not None:
            clauses.append("symbol = ?")
            parameters.append(query.symbol)
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
                SELECT * FROM standardized_state_operations {where}
                ORDER BY requested_at_utc DESC, attempt_id DESC LIMIT ?
                """,
                tuple(parameters),
            ).fetchall()
            return tuple(self._operation_from_row(connection, row) for row in rows)

    def _insert_operation(
        self,
        connection: sqlite3.Connection,
        operation: StandardizedPriceStateOperationAttempt,
    ) -> None:
        self._validate_stage(connection, operation.run_id, operation.stage_id)
        resolved = None
        if operation.resolved_definition_id is not None:
            row = connection.execute(
                """
                SELECT 1 FROM standardized_state_definitions WHERE definition_id = ?
                """,
                (str(operation.resolved_definition_id),),
            ).fetchone()
            resolved = str(operation.resolved_definition_id) if row else None
        connection.execute(
            """
            INSERT INTO standardized_state_operations (
                attempt_id, operation_id, run_id, stage_id, operation_type,
                status, requested_at_utc, completed_at_utc, created_by,
                reason, definition_name, predecessor_definition_id,
                requested_definition_id, resolved_definition_id, symbol,
                manual_price_usd_text, manual_reference_price_usd_text,
                manual_risk_scale_usd_text, as_of_utc,
                result_calculation_id, error_code, error_summary
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(operation.attempt_id),
                str(operation.operation_id),
                str(operation.run_id),
                str(operation.stage_id),
                operation.operation_type.value,
                operation.status.value,
                _iso(operation.requested_at_utc),
                _iso(operation.completed_at_utc),
                operation.created_by,
                operation.reason,
                operation.definition_name,
                str(operation.predecessor_definition_id)
                if operation.predecessor_definition_id
                else None,
                str(operation.requested_definition_id)
                if operation.requested_definition_id
                else None,
                resolved,
                operation.symbol,
                operation.manual_price_usd_text,
                operation.manual_reference_price_usd_text,
                operation.manual_risk_scale_usd_text,
                _iso(operation.as_of_utc) if operation.as_of_utc else None,
                str(operation.result_calculation_id)
                if operation.result_calculation_id
                else None,
                operation.error_code,
                operation.error_summary,
            ),
        )
        self._insert_evidence(
            connection,
            "standardized_state_operation_evidence_inputs",
            "attempt_id",
            operation.attempt_id,
            operation.evidence_bindings,
        )

    @staticmethod
    def _insert_evidence(
        connection, table, id_column, object_id, bindings
    ) -> None:
        connection.executemany(
            f"""
            INSERT INTO {table} (
                {id_column}, ordinal, evidence_kind, evidence_id,
                source_component, source_version
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                (
                    str(object_id),
                    index,
                    item.evidence_kind.value,
                    item.evidence_id,
                    item.source_component,
                    item.source_version,
                )
                for index, item in enumerate(bindings)
            ),
        )

    @staticmethod
    def _validate_stage(
        connection: sqlite3.Connection, run_id: UUID, stage_id: UUID
    ) -> None:
        row = connection.execute(
            """
            SELECT s.run_id, s.stage_name, r.run_type, r.execution_mode
            FROM algorithm_run_stages s
            JOIN algorithm_runs r ON r.run_id = s.run_id
            WHERE s.stage_id = ?
            """,
            (str(stage_id),),
        ).fetchone()
        if (
            row is None
            or row["run_id"] != str(run_id)
            or row["stage_name"] != "standardized_state"
            or row["run_type"] != "standardized_state_preview"
            or row["execution_mode"] != "no_execution"
        ):
            raise StandardizedPriceStateStorageError(
                "operation must belong to its exact NO EXECUTION standardized-state Run/Stage"
            )

    @staticmethod
    def _validate_definition_operation(definition, operation) -> None:
        if not (
            operation.definition_name == definition.name
            and operation.reason == definition.reason
            and operation.predecessor_definition_id
            == definition.predecessor_definition_id
            and operation.created_by == definition.created_by
        ):
            raise StandardizedPriceStateStorageError(
                "completed definition operation does not match the accepted definition"
            )

    @staticmethod
    def _validate_preview_operation(result, operation) -> None:
        try:
            matches = (
                operation.requested_definition_id == result.definition_id
                and normalized_symbol(operation.symbol or "") == result.symbol
                and decimal_text(
                    operation.manual_price_usd_text or "", "manual_price_usd"
                )
                == result.manual_price_usd
                and decimal_text(
                    operation.manual_reference_price_usd_text or "",
                    "manual_reference_price_usd",
                )
                == result.manual_reference_price_usd
                and decimal_text(
                    operation.manual_risk_scale_usd_text or "",
                    "manual_risk_scale_usd",
                )
                == result.manual_risk_scale_usd
                and operation.as_of_utc == result.as_of_utc
                and operation.evidence_bindings == result.evidence_bindings
                and operation.created_by == result.created_by
                and operation.reason == result.reason
            )
        except Exception as exc:
            raise StandardizedPriceStateStorageError(
                "completed preview operation contains invalid raw evidence"
            ) from exc
        if not matches:
            raise StandardizedPriceStateStorageError(
                "completed preview operation does not match the accepted result"
            )

    @staticmethod
    def _definition_from_row(row) -> StandardizedPriceStateDefinition:
        return StandardizedPriceStateDefinition(
            UUID(row["definition_id"]),
            int(row["definition_version"]),
            UUID(row["predecessor_definition_id"])
            if row["predecessor_definition_id"]
            else None,
            row["name"],
            row["reason"],
            row["formula_id"],
            row["price_currency"],
            row["output_unit"],
            StandardizedPriceStateInputSource(row["price_source"]),
            StandardizedPriceStateInputSource(row["reference_source"]),
            StandardizedPriceStateInputSource(row["risk_scale_source"]),
            StandardizedPriceStateDefinitionStatus(row["status"]),
            _datetime(row["created_at_utc"]),
            row["created_by"],
            int(row["schema_version"]),
        )

    @classmethod
    def _result_from_row(cls, connection, row) -> StandardizedPriceStateResult:
        evidence = connection.execute(
            """
            SELECT * FROM standardized_state_result_evidence
            WHERE calculation_id = ? ORDER BY ordinal
            """,
            (row["calculation_id"],),
        ).fetchall()
        trace = StandardizedPriceStateTrace(
            row["formula_id"],
            row["price_currency"],
            row["output_unit"],
            StandardizedPriceStateInputSource(row["price_source"]),
            StandardizedPriceStateInputSource(row["reference_source"]),
            StandardizedPriceStateInputSource(row["risk_scale_source"]),
            _decimal(row["manual_price_usd_text"]),
            _decimal(row["manual_reference_price_usd_text"]),
            _decimal(row["price_deviation_usd_text"]),
            _decimal(row["manual_risk_scale_usd_text"]),
            _decimal(row["standardized_state_text"]),
        )
        return StandardizedPriceStateResult(
            UUID(row["calculation_id"]),
            UUID(row["operation_id"]),
            UUID(row["run_id"]),
            UUID(row["stage_id"]),
            UUID(row["definition_id"]),
            int(row["definition_version"]),
            row["symbol"],
            _datetime(row["as_of_utc"]),
            _decimal(row["manual_price_usd_text"]),
            _decimal(row["manual_reference_price_usd_text"]),
            _decimal(row["manual_risk_scale_usd_text"]),
            _decimal(row["price_deviation_usd_text"]),
            _decimal(row["standardized_state_text"]),
            trace,
            cls._evidence_from_rows(evidence),
            _datetime(row["created_at_utc"]),
            row["created_by"],
            row["reason"],
            int(row["schema_version"]),
        )

    @classmethod
    def _operation_from_row(
        cls, connection, row
    ) -> StandardizedPriceStateOperationAttempt:
        evidence = connection.execute(
            """
            SELECT * FROM standardized_state_operation_evidence_inputs
            WHERE attempt_id = ? ORDER BY ordinal
            """,
            (row["attempt_id"],),
        ).fetchall()
        return StandardizedPriceStateOperationAttempt(
            UUID(row["attempt_id"]),
            UUID(row["operation_id"]),
            UUID(row["run_id"]),
            UUID(row["stage_id"]),
            StandardizedPriceStateOperationType(row["operation_type"]),
            StandardizedPriceStateOperationStatus(row["status"]),
            _datetime(row["requested_at_utc"]),
            _datetime(row["completed_at_utc"]),
            row["created_by"],
            row["reason"],
            definition_name=row["definition_name"],
            predecessor_definition_id=UUID(row["predecessor_definition_id"])
            if row["predecessor_definition_id"]
            else None,
            requested_definition_id=UUID(row["requested_definition_id"])
            if row["requested_definition_id"]
            else None,
            resolved_definition_id=UUID(row["resolved_definition_id"])
            if row["resolved_definition_id"]
            else None,
            symbol=row["symbol"],
            manual_price_usd_text=row["manual_price_usd_text"],
            manual_reference_price_usd_text=row[
                "manual_reference_price_usd_text"
            ],
            manual_risk_scale_usd_text=row["manual_risk_scale_usd_text"],
            as_of_utc=_datetime(row["as_of_utc"]),
            evidence_bindings=cls._evidence_from_rows(evidence),
            result_calculation_id=UUID(row["result_calculation_id"])
            if row["result_calculation_id"]
            else None,
            error_code=row["error_code"],
            error_summary=row["error_summary"],
        )

    @staticmethod
    def _evidence_from_rows(
        rows,
    ) -> tuple[StandardizedPriceStateEvidenceBinding, ...]:
        return tuple(
            StandardizedPriceStateEvidenceBinding(
                StandardizedPriceStateEvidenceKind(row["evidence_kind"]),
                row["evidence_id"],
                row["source_component"],
                row["source_version"],
            )
            for row in rows
        )

    @staticmethod
    def _raise_storage(message: str, exc: BaseException) -> None:
        if isinstance(exc, StandardizedPriceStateStorageError):
            raise exc
        raise StandardizedPriceStateStorageError(message) from exc


__all__ = ["SQLiteStandardizedPriceStateStore"]
