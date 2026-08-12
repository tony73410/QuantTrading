"""SQLite adapter for type-distinct P23-4A cycle-target Decision evidence."""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from uuid import UUID

from quant_trading.decision import (
    CycleTargetAdjustmentDecisionResult,
    CycleTargetAdjustmentOperationAttempt,
    CycleTargetAdjustmentOperationStatus,
    CycleTargetAdjustmentQuery,
    CycleTargetAdjustmentResultStatus,
    CycleTargetAdjustmentSourceLink,
    CycleTargetAdjustmentTradeIntent,
    CycleTargetDecisionInput,
    DecisionAction,
)
from quant_trading.decision.errors import DecisionStorageError

from .sqlite_database import CentralSQLiteDatabase


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="microseconds")


def _datetime(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value).astimezone(UTC) if value else None


def _source_dict(source: CycleTargetDecisionInput) -> dict[str, object]:
    return {
        "source_result_id": str(source.source_result_id),
        "source_operation_id": str(source.source_operation_id),
        "source_run_id": str(source.source_run_id),
        "source_state_stage_id": str(source.source_state_stage_id),
        "source_target_stage_id": str(source.source_target_stage_id),
        "source_formula_definition_id": str(source.source_formula_definition_id),
        "source_formula_definition_version": source.source_formula_definition_version,
        "source_configuration_id": str(source.source_configuration_id),
        "source_configuration_version": source.source_configuration_version,
        "source_configuration_fingerprint": source.source_configuration_fingerprint,
        "source_reversal_result_id": str(source.source_reversal_result_id),
        "source_reversal_run_id": str(source.source_reversal_run_id),
        "source_reversal_step_id": str(source.source_reversal_step_id),
        "source_calculation_fingerprint": source.source_calculation_fingerprint,
        "symbol": source.symbol,
        "source_session": source.source_session.isoformat(),
        "source_available_at_utc": _iso(source.source_available_at_utc),
        "source_region": source.source_region,
        "source_status": source.source_status,
        "target_fraction": str(source.target_fraction),
        "research_capital_basis_usd": str(source.research_capital_basis_usd),
        "current_position_value_usd": str(source.current_position_value_usd),
        "target_position_value_usd": str(source.target_position_value_usd),
        "adjustment_value_usd": str(source.adjustment_value_usd),
        "source_direction": source.source_direction,
        "source_created_at_utc": _iso(source.source_created_at_utc),
        "source_execution_allowed": source.source_execution_allowed,
        "source_live_allowed": source.source_live_allowed,
        "source_schema_version": source.source_schema_version,
        "currency": source.currency,
        "schema_version": source.schema_version,
    }


def _source_from_dict(data: dict[str, object]) -> CycleTargetDecisionInput:
    return CycleTargetDecisionInput(
        source_result_id=UUID(str(data["source_result_id"])),
        source_operation_id=UUID(str(data["source_operation_id"])),
        source_run_id=UUID(str(data["source_run_id"])),
        source_state_stage_id=UUID(str(data["source_state_stage_id"])),
        source_target_stage_id=UUID(str(data["source_target_stage_id"])),
        source_formula_definition_id=UUID(str(data["source_formula_definition_id"])),
        source_formula_definition_version=int(data["source_formula_definition_version"]),
        source_configuration_id=UUID(str(data["source_configuration_id"])),
        source_configuration_version=int(data["source_configuration_version"]),
        source_configuration_fingerprint=str(data["source_configuration_fingerprint"]),
        source_reversal_result_id=UUID(str(data["source_reversal_result_id"])),
        source_reversal_run_id=UUID(str(data["source_reversal_run_id"])),
        source_reversal_step_id=UUID(str(data["source_reversal_step_id"])),
        source_calculation_fingerprint=str(data["source_calculation_fingerprint"]),
        symbol=str(data["symbol"]),
        source_session=date.fromisoformat(str(data["source_session"])),
        source_available_at_utc=datetime.fromisoformat(str(data["source_available_at_utc"])),
        source_region=str(data["source_region"]),
        source_status=str(data["source_status"]),
        target_fraction=Decimal(str(data["target_fraction"])),
        research_capital_basis_usd=Decimal(str(data["research_capital_basis_usd"])),
        current_position_value_usd=Decimal(str(data["current_position_value_usd"])),
        target_position_value_usd=Decimal(str(data["target_position_value_usd"])),
        adjustment_value_usd=Decimal(str(data["adjustment_value_usd"])),
        source_direction=str(data["source_direction"]),
        source_created_at_utc=datetime.fromisoformat(str(data["source_created_at_utc"])),
        source_execution_allowed=bool(data["source_execution_allowed"]),
        source_live_allowed=bool(data["source_live_allowed"]),
        source_schema_version=int(data["source_schema_version"]),
        currency=str(data["currency"]),
        schema_version=int(data["schema_version"]),
    )


class SQLiteCycleTargetAdjustmentDecisionStore:
    """Implement P31 Decision Store and read-only query ports in central SQLite."""

    def __init__(self, database_path: Path | str) -> None:
        self._database = CentralSQLiteDatabase(database_path)

    def initialize(self) -> None:
        self._database.initialize()

    def get_first_operation(self, operation_id: UUID):
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                """SELECT * FROM cycle_target_decision_operation_attempts
                   WHERE operation_id = ?
                   ORDER BY CASE WHEN status = 'completed' THEN 0 ELSE 1 END, rowid
                   LIMIT 1""",
                (str(operation_id),),
            ).fetchone()
            return self._operation_from_row(row) if row else None

    def save_operation(self, operation: CycleTargetAdjustmentOperationAttempt) -> None:
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
                self._raise_storage("could not save P31 Decision operation", exc)

    def save_completed(self, result, operation, source_link) -> None:
        self._validate_completed_models(result, operation, source_link)
        with closing(self._database.connect()) as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                self._validate_run_context(connection, operation)
                self._validate_source_database(connection, result.source)
                self._insert_result(connection, result)
                for intent in result.intents:
                    self._insert_intent(connection, intent)
                self._insert_source_link(connection, source_link)
                self._insert_operation(connection, operation)
                count = connection.execute(
                    "SELECT COUNT(*) FROM cycle_target_decision_trade_intents WHERE decision_result_id = ?",
                    (str(result.decision_result_id),),
                ).fetchone()[0]
                expected = 0 if result.status is CycleTargetAdjustmentResultStatus.HOLD else 1
                if int(count) != expected:
                    raise DecisionStorageError("stored P31 intent cardinality is invalid")
                connection.commit()
            except Exception as exc:
                connection.rollback()
                self._raise_storage("could not save completed P31 Decision", exc)

    def list_cycle_target_adjustment_operations(
        self, query: CycleTargetAdjustmentQuery = CycleTargetAdjustmentQuery()
    ):
        clauses: list[str] = []
        parameters: list[object] = []
        if query.symbol is not None:
            clauses.append("r.symbol = ?"); parameters.append(query.symbol)
        if query.action is not None:
            clauses.append("r.action = ?"); parameters.append(query.action.value)
        if query.result_status is not None:
            clauses.append("r.status = ?"); parameters.append(query.result_status.value)
        if query.operation_status is not None:
            clauses.append("o.status = ?"); parameters.append(query.operation_status.value)
        if query.source_result_id is not None:
            clauses.append("o.requested_source_result_id = ?"); parameters.append(str(query.source_result_id))
        if query.source_run_id is not None:
            clauses.append("o.requested_source_run_id = ?"); parameters.append(str(query.source_run_id))
        if query.formula_definition_id is not None:
            clauses.append("r.source_formula_definition_id = ?"); parameters.append(str(query.formula_definition_id))
        if query.configuration_id is not None:
            clauses.append("r.source_configuration_id = ?"); parameters.append(str(query.configuration_id))
        if query.source_session_from is not None:
            clauses.append("r.source_session >= ?"); parameters.append(query.source_session_from.isoformat())
        if query.source_session_to is not None:
            clauses.append("r.source_session <= ?"); parameters.append(query.source_session_to.isoformat())
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        parameters.append(query.limit)
        with closing(self._database.connect()) as connection:
            rows = connection.execute(
                f"""SELECT o.* FROM cycle_target_decision_operation_attempts o
                    LEFT JOIN cycle_target_decision_results r
                      ON r.decision_result_id = o.decision_result_id
                    {where}
                    ORDER BY o.requested_at_utc DESC, o.attempt_id DESC LIMIT ?""",
                tuple(parameters),
            ).fetchall()
            return tuple(self._operation_from_row(row) for row in rows)

    def list_cycle_target_adjustment_results(
        self, query: CycleTargetAdjustmentQuery = CycleTargetAdjustmentQuery()
    ):
        clauses, parameters = self._result_clauses(query)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        parameters.append(query.limit)
        with closing(self._database.connect()) as connection:
            rows = connection.execute(
                f"""SELECT * FROM cycle_target_decision_results {where}
                    ORDER BY source_session DESC, created_at_utc DESC, decision_result_id DESC
                    LIMIT ?""",
                tuple(parameters),
            ).fetchall()
            return tuple(self._result_from_row(connection, row) for row in rows)

    def get_cycle_target_adjustment_result(self, decision_result_id: UUID):
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                "SELECT * FROM cycle_target_decision_results WHERE decision_result_id = ?",
                (str(decision_result_id),),
            ).fetchone()
            return self._result_from_row(connection, row) if row else None

    def get_cycle_target_adjustment_source_link(self, decision_result_id: UUID):
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                "SELECT * FROM cycle_target_decision_source_links WHERE decision_result_id = ?",
                (str(decision_result_id),),
            ).fetchone()
            return self._source_link_from_row(row) if row else None

    def get_cycle_target_adjustment_intent(self, intent_id: UUID):
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                "SELECT * FROM cycle_target_decision_trade_intents WHERE intent_id = ?",
                (str(intent_id),),
            ).fetchone()
            return self._intent_from_row(row) if row else None

    @staticmethod
    def _result_clauses(query):
        clauses: list[str] = []
        parameters: list[object] = []
        for attribute, column, transform in (
            ("symbol", "symbol", lambda value: value),
            ("action", "action", lambda value: value.value),
            ("result_status", "status", lambda value: value.value),
            ("source_result_id", "source_result_id", str),
            ("source_run_id", "source_run_id", str),
            ("formula_definition_id", "source_formula_definition_id", str),
            ("configuration_id", "source_configuration_id", str),
        ):
            value = getattr(query, attribute)
            if value is not None:
                clauses.append(f"{column} = ?")
                parameters.append(transform(value))
        if query.source_session_from is not None:
            clauses.append("source_session >= ?"); parameters.append(query.source_session_from.isoformat())
        if query.source_session_to is not None:
            clauses.append("source_session <= ?"); parameters.append(query.source_session_to.isoformat())
        return clauses, parameters

    @staticmethod
    def _validate_completed_models(result, operation, link) -> None:
        intent_id = result.intents[0].intent_id if result.intents else None
        if (
            operation.status is not CycleTargetAdjustmentOperationStatus.COMPLETED
            or operation.decision_result_id != result.decision_result_id
            or operation.intent_id != intent_id
            or operation.resolved_source != result.source
            or link.operation_id != operation.operation_id
            or link.decision_result_id != result.decision_result_id
            or link.intent_id != intent_id
            or link.decision_run_id != result.run_id
            or link.decision_stage_id != result.decision_stage_id
            or link.source_result_id != result.source.source_result_id
            or link.source_run_id != result.source.source_run_id
        ):
            raise DecisionStorageError("P31 completed object graph is inconsistent")

    @staticmethod
    def _validate_run_context(connection, operation) -> None:
        run = connection.execute(
            "SELECT run_type, execution_mode, parent_run_id FROM algorithm_runs WHERE run_id = ?",
            (str(operation.run_id),),
        ).fetchone()
        allowed_parents = (
            {str(operation.requested_source_run_id)}
            if operation.resolved_source is not None
            else {None, str(operation.requested_source_run_id)}
        )
        if (
            run is None
            or run["run_type"] != "cycle_target_decision_preview"
            or run["execution_mode"] != "no_execution"
            or run["parent_run_id"] not in allowed_parents
        ):
            raise DecisionStorageError("P31 operation Run context is invalid")
        if operation.target_stage_id is not None:
            stage = connection.execute(
                "SELECT run_id, stage_name FROM algorithm_run_stages WHERE stage_id = ?",
                (str(operation.target_stage_id),),
            ).fetchone()
            if stage is None or stage["run_id"] != str(operation.run_id) or stage["stage_name"] != "target_position":
                raise DecisionStorageError("P31 TARGET_POSITION stage is invalid")
        if operation.decision_stage_id is not None:
            stage = connection.execute(
                "SELECT run_id, stage_name FROM algorithm_run_stages WHERE stage_id = ?",
                (str(operation.decision_stage_id),),
            ).fetchone()
            if stage is None or stage["run_id"] != str(operation.run_id) or stage["stage_name"] != "decision":
                raise DecisionStorageError("P31 DECISION stage is invalid")

    @staticmethod
    def _validate_source_database(connection, source: CycleTargetDecisionInput) -> None:
        row = connection.execute(
            """SELECT r.*, c.constraint_fingerprint
               FROM cycle_target_results r
               JOIN cycle_target_asset_configurations c
                 ON c.configuration_id = r.configuration_id
               WHERE r.result_id = ?""",
            (str(source.source_result_id),),
        ).fetchone()
        expected = {
            "operation_id": str(source.source_operation_id),
            "run_id": str(source.source_run_id),
            "state_stage_id": str(source.source_state_stage_id),
            "target_stage_id": str(source.source_target_stage_id),
            "formula_definition_id": str(source.source_formula_definition_id),
            "formula_definition_version": source.source_formula_definition_version,
            "configuration_id": str(source.source_configuration_id),
            "configuration_version": source.source_configuration_version,
            "constraint_fingerprint": source.source_configuration_fingerprint,
            "source_result_id": str(source.source_reversal_result_id),
            "source_run_id": str(source.source_reversal_run_id),
            "source_step_id": str(source.source_reversal_step_id),
            "calculation_fingerprint": source.source_calculation_fingerprint,
            "symbol": source.symbol,
            "session": source.source_session.isoformat(),
            "region": source.source_region,
            "status": source.source_status,
            "target_fraction_text": str(source.target_fraction),
            "research_capital_basis_usd_text": str(source.research_capital_basis_usd),
            "current_position_value_usd_text": str(source.current_position_value_usd),
            "target_position_value_usd_text": str(source.target_position_value_usd),
            "adjustment_value_usd_text": str(source.adjustment_value_usd),
            "adjustment_direction": source.source_direction,
            "execution_allowed": 0,
            "live_allowed": 0,
            "schema_version": source.source_schema_version,
        }
        timestamps_match = row is not None and (
            _datetime(row["available_at_utc"]) == source.source_available_at_utc
            and _datetime(row["created_at_utc"]) == source.source_created_at_utc
        )
        if (
            row is None
            or not timestamps_match
            or any(row[key] != value for key, value in expected.items())
        ):
            raise DecisionStorageError("persisted P29 source does not match P31 evidence")

    @staticmethod
    def _insert_operation(connection, operation) -> None:
        source_json = (
            json.dumps(_source_dict(operation.resolved_source), sort_keys=True, separators=(",", ":"))
            if operation.resolved_source is not None else None
        )
        connection.execute(
            """INSERT INTO cycle_target_decision_operation_attempts VALUES
               (:attempt_id,:operation_id,:run_id,:target_stage_id,:decision_stage_id,
                :command_fingerprint,:status,:requested_at_utc,:completed_at_utc,
                :requested_source_result_id,:requested_source_run_id,:session_id,:request_id,
                :created_by,:reason,:resolved_source_json,:decision_result_id,:intent_id,
                :error_code,:error_summary,:software_version,:source_revision,:worktree_state,
                :execution_allowed,:live_allowed,:schema_version)""",
            {
                "attempt_id": str(operation.attempt_id), "operation_id": str(operation.operation_id),
                "run_id": str(operation.run_id),
                "target_stage_id": str(operation.target_stage_id) if operation.target_stage_id else None,
                "decision_stage_id": str(operation.decision_stage_id) if operation.decision_stage_id else None,
                "command_fingerprint": operation.command_fingerprint, "status": operation.status.value,
                "requested_at_utc": _iso(operation.requested_at_utc),
                "completed_at_utc": _iso(operation.completed_at_utc) if operation.completed_at_utc else None,
                "requested_source_result_id": str(operation.requested_source_result_id),
                "requested_source_run_id": str(operation.requested_source_run_id),
                "session_id": operation.session_id, "request_id": operation.request_id,
                "created_by": operation.created_by, "reason": operation.reason,
                "resolved_source_json": source_json,
                "decision_result_id": str(operation.decision_result_id) if operation.decision_result_id else None,
                "intent_id": str(operation.intent_id) if operation.intent_id else None,
                "error_code": operation.error_code, "error_summary": operation.error_summary,
                "software_version": operation.software_version,
                "source_revision": operation.source_revision, "worktree_state": operation.worktree_state,
                "execution_allowed": int(operation.execution_allowed),
                "live_allowed": int(operation.live_allowed), "schema_version": operation.schema_version,
            },
        )

    @staticmethod
    def _insert_result(connection, result) -> None:
        source = result.source
        connection.execute(
            """INSERT INTO cycle_target_decision_results VALUES
               (:decision_result_id,:operation_id,:run_id,:target_stage_id,:decision_stage_id,
                :source_result_id,:source_operation_id,:source_run_id,:source_state_stage_id,
                :source_target_stage_id,:source_formula_definition_id,:source_formula_definition_version,
                :source_configuration_id,:source_configuration_version,:source_configuration_fingerprint,
                :source_reversal_result_id,:source_reversal_run_id,:source_reversal_step_id,
                :source_calculation_fingerprint,:symbol,:source_session,:source_available_at_utc,
                :source_region,:source_status,:target_fraction_text,:research_capital_basis_usd_text,
                :current_position_value_usd_text,:target_position_value_usd_text,:adjustment_value_usd_text,
                :source_direction,:source_created_at_utc,:source_execution_allowed,:source_live_allowed,
                :source_schema_version,:currency,:status,:action,:reason_codes_json,:explanation,
                :created_at_utc,:created_by,:reason,:software_version,:source_revision,:worktree_state,
                :policy_id,:policy_version,:execution_allowed,:live_allowed,:schema_version)""",
            {
                "decision_result_id": str(result.decision_result_id), "operation_id": str(result.operation_id),
                "run_id": str(result.run_id), "target_stage_id": str(result.target_stage_id),
                "decision_stage_id": str(result.decision_stage_id),
                **{
                    key: value for key, value in {
                        "source_result_id": str(source.source_result_id),
                        "source_operation_id": str(source.source_operation_id),
                        "source_run_id": str(source.source_run_id),
                        "source_state_stage_id": str(source.source_state_stage_id),
                        "source_target_stage_id": str(source.source_target_stage_id),
                        "source_formula_definition_id": str(source.source_formula_definition_id),
                        "source_formula_definition_version": source.source_formula_definition_version,
                        "source_configuration_id": str(source.source_configuration_id),
                        "source_configuration_version": source.source_configuration_version,
                        "source_configuration_fingerprint": source.source_configuration_fingerprint,
                        "source_reversal_result_id": str(source.source_reversal_result_id),
                        "source_reversal_run_id": str(source.source_reversal_run_id),
                        "source_reversal_step_id": str(source.source_reversal_step_id),
                        "source_calculation_fingerprint": source.source_calculation_fingerprint,
                        "symbol": source.symbol, "source_session": source.source_session.isoformat(),
                        "source_available_at_utc": _iso(source.source_available_at_utc),
                        "source_region": source.source_region, "source_status": source.source_status,
                        "target_fraction_text": str(source.target_fraction),
                        "research_capital_basis_usd_text": str(source.research_capital_basis_usd),
                        "current_position_value_usd_text": str(source.current_position_value_usd),
                        "target_position_value_usd_text": str(source.target_position_value_usd),
                        "adjustment_value_usd_text": str(source.adjustment_value_usd),
                        "source_direction": source.source_direction,
                        "source_created_at_utc": _iso(source.source_created_at_utc),
                        "source_execution_allowed": int(source.source_execution_allowed),
                        "source_live_allowed": int(source.source_live_allowed),
                        "source_schema_version": source.source_schema_version,
                        "currency": source.currency,
                    }.items()
                },
                "status": result.status.value, "action": result.action.value,
                "reason_codes_json": json.dumps(result.reason_codes), "explanation": result.explanation,
                "created_at_utc": _iso(result.created_at_utc), "created_by": result.created_by,
                "reason": result.reason, "software_version": result.software_version,
                "source_revision": result.source_revision, "worktree_state": result.worktree_state,
                "policy_id": result.policy_id, "policy_version": result.policy_version,
                "execution_allowed": int(result.execution_allowed), "live_allowed": int(result.live_allowed),
                "schema_version": result.schema_version,
            },
        )

    @staticmethod
    def _insert_intent(connection, intent) -> None:
        connection.execute(
            """INSERT INTO cycle_target_decision_trade_intents VALUES
               (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                str(intent.intent_id), str(intent.decision_result_id), str(intent.operation_id),
                str(intent.run_id), str(intent.decision_stage_id), str(intent.source_result_id),
                str(intent.source_run_id), intent.symbol, intent.source_session.isoformat(),
                _iso(intent.source_available_at_utc), intent.action.value,
                str(intent.current_exposure_usd), str(intent.target_exposure_usd),
                str(intent.desired_change_usd), str(intent.requested_notional_usd),
                json.dumps(intent.reason_codes), _iso(intent.created_at_utc), intent.policy_id,
                intent.policy_version, intent.currency, int(intent.execution_allowed),
                int(intent.live_allowed), intent.schema_version,
            ),
        )

    @staticmethod
    def _insert_source_link(connection, link) -> None:
        connection.execute(
            """INSERT INTO cycle_target_decision_source_links VALUES
               (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                str(link.source_link_id), str(link.operation_id), str(link.decision_result_id),
                str(link.intent_id) if link.intent_id else None, str(link.decision_run_id),
                str(link.decision_stage_id), str(link.source_result_id),
                str(link.source_operation_id), str(link.source_run_id),
                str(link.source_state_stage_id), str(link.source_target_stage_id),
                str(link.source_formula_definition_id), str(link.source_configuration_id),
                str(link.source_reversal_result_id), str(link.source_reversal_run_id),
                str(link.source_reversal_step_id), _iso(link.created_at_utc), link.schema_version,
            ),
        )

    @staticmethod
    def _operation_from_row(row):
        source = _source_from_dict(json.loads(row["resolved_source_json"])) if row["resolved_source_json"] else None
        return CycleTargetAdjustmentOperationAttempt(
            attempt_id=UUID(row["attempt_id"]), operation_id=UUID(row["operation_id"]),
            run_id=UUID(row["run_id"]),
            target_stage_id=UUID(row["target_stage_id"]) if row["target_stage_id"] else None,
            decision_stage_id=UUID(row["decision_stage_id"]) if row["decision_stage_id"] else None,
            command_fingerprint=row["command_fingerprint"],
            status=CycleTargetAdjustmentOperationStatus(row["status"]),
            requested_at_utc=_datetime(row["requested_at_utc"]),
            completed_at_utc=_datetime(row["completed_at_utc"]),
            requested_source_result_id=UUID(row["requested_source_result_id"]),
            requested_source_run_id=UUID(row["requested_source_run_id"]),
            session_id=row["session_id"], request_id=row["request_id"],
            created_by=row["created_by"], reason=row["reason"], resolved_source=source,
            decision_result_id=UUID(row["decision_result_id"]) if row["decision_result_id"] else None,
            intent_id=UUID(row["intent_id"]) if row["intent_id"] else None,
            error_code=row["error_code"], error_summary=row["error_summary"],
            software_version=row["software_version"], source_revision=row["source_revision"],
            worktree_state=row["worktree_state"],
            execution_allowed=bool(row["execution_allowed"]), live_allowed=bool(row["live_allowed"]),
            schema_version=int(row["schema_version"]),
        )

    def _result_from_row(self, connection, row):
        source = self._source_from_result_row(row)
        intents = tuple(
            self._intent_from_row(item) for item in connection.execute(
                "SELECT * FROM cycle_target_decision_trade_intents WHERE decision_result_id = ? ORDER BY intent_id",
                (row["decision_result_id"],),
            ).fetchall()
        )
        return CycleTargetAdjustmentDecisionResult(
            decision_result_id=UUID(row["decision_result_id"]), operation_id=UUID(row["operation_id"]),
            run_id=UUID(row["run_id"]), target_stage_id=UUID(row["target_stage_id"]),
            decision_stage_id=UUID(row["decision_stage_id"]), source=source,
            status=CycleTargetAdjustmentResultStatus(row["status"]),
            action=DecisionAction(row["action"]), intents=intents,
            reason_codes=tuple(json.loads(row["reason_codes_json"])), explanation=row["explanation"],
            created_at_utc=_datetime(row["created_at_utc"]), created_by=row["created_by"],
            reason=row["reason"], software_version=row["software_version"],
            source_revision=row["source_revision"], worktree_state=row["worktree_state"],
            policy_id=row["policy_id"], policy_version=row["policy_version"],
            execution_allowed=bool(row["execution_allowed"]), live_allowed=bool(row["live_allowed"]),
            schema_version=int(row["schema_version"]),
        )

    @staticmethod
    def _source_from_result_row(row):
        return CycleTargetDecisionInput(
            source_result_id=UUID(row["source_result_id"]),
            source_operation_id=UUID(row["source_operation_id"]), source_run_id=UUID(row["source_run_id"]),
            source_state_stage_id=UUID(row["source_state_stage_id"]),
            source_target_stage_id=UUID(row["source_target_stage_id"]),
            source_formula_definition_id=UUID(row["source_formula_definition_id"]),
            source_formula_definition_version=int(row["source_formula_definition_version"]),
            source_configuration_id=UUID(row["source_configuration_id"]),
            source_configuration_version=int(row["source_configuration_version"]),
            source_configuration_fingerprint=row["source_configuration_fingerprint"],
            source_reversal_result_id=UUID(row["source_reversal_result_id"]),
            source_reversal_run_id=UUID(row["source_reversal_run_id"]),
            source_reversal_step_id=UUID(row["source_reversal_step_id"]),
            source_calculation_fingerprint=row["source_calculation_fingerprint"], symbol=row["symbol"],
            source_session=date.fromisoformat(row["source_session"]),
            source_available_at_utc=_datetime(row["source_available_at_utc"]),
            source_region=row["source_region"], source_status=row["source_status"],
            target_fraction=Decimal(row["target_fraction_text"]),
            research_capital_basis_usd=Decimal(row["research_capital_basis_usd_text"]),
            current_position_value_usd=Decimal(row["current_position_value_usd_text"]),
            target_position_value_usd=Decimal(row["target_position_value_usd_text"]),
            adjustment_value_usd=Decimal(row["adjustment_value_usd_text"]),
            source_direction=row["source_direction"], source_created_at_utc=_datetime(row["source_created_at_utc"]),
            source_execution_allowed=bool(row["source_execution_allowed"]),
            source_live_allowed=bool(row["source_live_allowed"]),
            source_schema_version=int(row["source_schema_version"]), currency=row["currency"],
        )

    @staticmethod
    def _intent_from_row(row):
        return CycleTargetAdjustmentTradeIntent(
            intent_id=UUID(row["intent_id"]), decision_result_id=UUID(row["decision_result_id"]),
            operation_id=UUID(row["operation_id"]), run_id=UUID(row["run_id"]),
            decision_stage_id=UUID(row["decision_stage_id"]), source_result_id=UUID(row["source_result_id"]),
            source_run_id=UUID(row["source_run_id"]), symbol=row["symbol"],
            source_session=date.fromisoformat(row["source_session"]),
            source_available_at_utc=_datetime(row["source_available_at_utc"]),
            action=DecisionAction(row["action"]),
            current_exposure_usd=Decimal(row["current_exposure_usd_text"]),
            target_exposure_usd=Decimal(row["target_exposure_usd_text"]),
            desired_change_usd=Decimal(row["desired_change_usd_text"]),
            requested_notional_usd=Decimal(row["requested_notional_usd_text"]),
            reason_codes=tuple(json.loads(row["reason_codes_json"])),
            created_at_utc=_datetime(row["created_at_utc"]), policy_id=row["policy_id"],
            policy_version=row["policy_version"], currency=row["currency"],
            execution_allowed=bool(row["execution_allowed"]), live_allowed=bool(row["live_allowed"]),
            schema_version=int(row["schema_version"]),
        )

    @staticmethod
    def _source_link_from_row(row):
        return CycleTargetAdjustmentSourceLink(
            source_link_id=UUID(row["source_link_id"]), operation_id=UUID(row["operation_id"]),
            decision_result_id=UUID(row["decision_result_id"]),
            intent_id=UUID(row["intent_id"]) if row["intent_id"] else None,
            decision_run_id=UUID(row["decision_run_id"]), decision_stage_id=UUID(row["decision_stage_id"]),
            source_result_id=UUID(row["source_result_id"]), source_operation_id=UUID(row["source_operation_id"]),
            source_run_id=UUID(row["source_run_id"]), source_state_stage_id=UUID(row["source_state_stage_id"]),
            source_target_stage_id=UUID(row["source_target_stage_id"]),
            source_formula_definition_id=UUID(row["source_formula_definition_id"]),
            source_configuration_id=UUID(row["source_configuration_id"]),
            source_reversal_result_id=UUID(row["source_reversal_result_id"]),
            source_reversal_run_id=UUID(row["source_reversal_run_id"]),
            source_reversal_step_id=UUID(row["source_reversal_step_id"]),
            created_at_utc=_datetime(row["created_at_utc"]), schema_version=int(row["schema_version"]),
        )

    @staticmethod
    def _raise_storage(message: str, exc: Exception) -> None:
        if isinstance(exc, DecisionStorageError):
            raise exc
        raise DecisionStorageError(message) from exc


__all__ = ["SQLiteCycleTargetAdjustmentDecisionStore"]
