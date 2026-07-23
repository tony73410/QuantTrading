"""SQLite adapter for immutable single-asset exposure-cap research evidence."""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from uuid import UUID

from quant_trading.risk import (
    ExposureCapDefinitionQuery,
    ExposureCapDefinitionStatus,
    ExposureCapDisposition,
    ExposureCapOperationAttempt,
    ExposureCapOperationQuery,
    ExposureCapOperationStatus,
    ExposureCapOperationType,
    ExposureCapResultQuery,
    ExposureCapRuleOutcome,
    ExposureCapRuleResult,
    ExposureCapSourceLink,
    LinkedExposureCapPreviewInput,
    SingleAssetExposureCapDefinitionVersion,
    TargetAdjustmentExposureCapPreviewResult,
)

from .sqlite_database import CentralSQLiteDatabase
from .target_adjustment_risk_sqlite_store import (
    _safety_dict,
    _safety_from,
    _source_dict,
    _source_from,
)


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="microseconds")


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(UTC)


def _definition_dict(definition: SingleAssetExposureCapDefinitionVersion) -> dict[str, object]:
    return {
        "definition_id": str(definition.definition_id),
        "definition_version": definition.definition_version,
        "predecessor_version": definition.predecessor_version,
        "symbol": definition.symbol,
        "max_target_exposure_usd": str(definition.max_target_exposure_usd),
        "status": definition.status.value,
        "reason": definition.reason,
        "created_by": definition.created_by,
        "created_at_utc": _iso(definition.created_at_utc),
        "software_version": definition.software_version,
        "currency": definition.currency,
        "schema_version": definition.schema_version,
    }


def _definition_from(data: dict[str, object]) -> SingleAssetExposureCapDefinitionVersion:
    return SingleAssetExposureCapDefinitionVersion(
        UUID(str(data["definition_id"])), int(data["definition_version"]),
        int(data["predecessor_version"]) if data["predecessor_version"] is not None else None,
        str(data["symbol"]), Decimal(str(data["max_target_exposure_usd"])),
        ExposureCapDefinitionStatus(str(data["status"])), str(data["reason"]),
        str(data["created_by"]), _dt(str(data["created_at_utc"])),
        str(data["software_version"]), str(data["currency"]), int(data["schema_version"]),
    )


def _linked_dict(source: LinkedExposureCapPreviewInput) -> dict[str, object]:
    return {
        "phase6a_review_result_id": str(source.phase6a_review_result_id),
        "phase6a_operation_id": str(source.phase6a_operation_id),
        "phase6a_run_id": str(source.phase6a_run_id),
        "phase6a_stage_id": str(source.phase6a_stage_id),
        "phase6a_gate_id": source.phase6a_gate_id,
        "phase6a_gate_version": source.phase6a_gate_version,
        "phase6a_created_at_utc": _iso(source.phase6a_created_at_utc),
        "phase6a_source": _source_dict(source.phase6a_source),
        "phase6a_safety_snapshot": _safety_dict(source.phase6a_safety_snapshot),
        "phase6a_rule_evidence": [list(item) for item in source.phase6a_rule_evidence],
        "definition": _definition_dict(source.definition),
        "current_safety_snapshot": _safety_dict(source.current_safety_snapshot),
        "schema_version": source.schema_version,
    }


def _linked_from(data: dict[str, object]) -> LinkedExposureCapPreviewInput:
    return LinkedExposureCapPreviewInput(
        UUID(str(data["phase6a_review_result_id"])),
        UUID(str(data["phase6a_operation_id"])), UUID(str(data["phase6a_run_id"])),
        UUID(str(data["phase6a_stage_id"])), str(data["phase6a_gate_id"]),
        str(data["phase6a_gate_version"]), _dt(str(data["phase6a_created_at_utc"])),
        _source_from(dict(data["phase6a_source"])),
        _safety_from(dict(data["phase6a_safety_snapshot"])),
        tuple(tuple(str(value) for value in item) for item in data["phase6a_rule_evidence"]),
        _definition_from(dict(data["definition"])),
        _safety_from(dict(data["current_safety_snapshot"])),
        int(data["schema_version"]),
    )


class SQLiteExposureCapStore:
    def __init__(self, database_path: Path | str) -> None:
        self._database = CentralSQLiteDatabase(database_path)

    def initialize(self) -> None:
        self._database.initialize()

    def get_first_operation(self, operation_id: UUID):
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                """
                SELECT * FROM target_adjustment_exposure_cap_operations
                WHERE operation_id = ?
                ORDER BY CASE WHEN status IN ('completed','blocked') THEN 0 ELSE 1 END,
                         rowid
                LIMIT 1
                """,
                (str(operation_id),),
            ).fetchone()
            return self._operation(row) if row else None

    def get_definition(self, definition_id: UUID, definition_version: int):
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                """SELECT * FROM single_asset_exposure_cap_definitions
                   WHERE definition_id=? AND definition_version=?""",
                (str(definition_id), definition_version),
            ).fetchone()
            return self._definition(row) if row else None

    def get_latest_definition(self, definition_id: UUID):
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                """SELECT * FROM single_asset_exposure_cap_definitions
                   WHERE definition_id=? ORDER BY definition_version DESC LIMIT 1""",
                (str(definition_id),),
            ).fetchone()
            return self._definition(row) if row else None

    def save_definition(self, definition, operation) -> None:
        with closing(self._database.connect()) as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                self._validate_run(connection, operation)
                self._validate_definition_append(connection, definition, operation)
                self._insert_definition(connection, definition)
                self._insert_operation(connection, operation)
                connection.commit()
            except Exception as exc:
                connection.rollback()
                raise sqlite3.DatabaseError("could not save exposure-cap definition operation") from exc

    def save_operation(self, operation: ExposureCapOperationAttempt) -> None:
        with closing(self._database.connect()) as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                self._validate_run(connection, operation)
                self._insert_operation(connection, operation)
                connection.commit()
            except Exception as exc:
                connection.rollback()
                raise sqlite3.DatabaseError("could not save exposure-cap operation") from exc

    def save_completed(self, result, operation, source_link) -> None:
        self._validate_models(result, operation, source_link)
        with closing(self._database.connect()) as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                self._validate_run(connection, operation)
                self._validate_phase6a(connection, result.source)
                self._validate_definition_current(connection, result.source.definition)
                self._insert_operation(connection, operation)
                self._insert_result(connection, result)
                self._insert_rule(connection, result.rule)
                self._insert_link(connection, source_link)
                connection.commit()
            except Exception as exc:
                connection.rollback()
                raise sqlite3.DatabaseError("could not save completed exposure-cap preview") from exc

    def list_exposure_cap_definitions(self, query=ExposureCapDefinitionQuery()):
        clauses, params = [], []
        if query.current_only:
            clauses.append(
                "definition_version=(SELECT MAX(current.definition_version) "
                "FROM single_asset_exposure_cap_definitions current "
                "WHERE current.definition_id=single_asset_exposure_cap_definitions.definition_id)"
            )
        if query.symbol is not None:
            clauses.append("symbol=?"); params.append(query.symbol)
        if query.status is not None:
            clauses.append("status=?"); params.append(query.status.value)
        where = "WHERE " + " AND ".join(clauses) if clauses else ""
        params.append(query.limit)
        with closing(self._database.connect()) as connection:
            rows = connection.execute(
                f"""SELECT * FROM single_asset_exposure_cap_definitions {where}
                    ORDER BY created_at_utc DESC, definition_id, definition_version DESC LIMIT ?""",
                params,
            ).fetchall()
            return tuple(self._definition(row) for row in rows)

    def list_exposure_cap_operations(self, query=ExposureCapOperationQuery()):
        clauses, params = [], []
        if query.operation_type is not None:
            clauses.append("operation_type=?"); params.append(query.operation_type.value)
        if query.status is not None:
            clauses.append("status=?"); params.append(query.status.value)
        if query.symbol is not None:
            clauses.append("COALESCE(resolved_symbol,requested_symbol)=?"); params.append(query.symbol)
        where = "WHERE " + " AND ".join(clauses) if clauses else ""
        params.append(query.limit)
        with closing(self._database.connect()) as connection:
            rows = connection.execute(
                f"""SELECT * FROM target_adjustment_exposure_cap_operations {where}
                    ORDER BY requested_at_utc DESC, attempt_id DESC LIMIT ?""",
                params,
            ).fetchall()
            return tuple(self._operation(row) for row in rows)

    def list_exposure_cap_results(self, query=ExposureCapResultQuery()):
        clauses, params = [], []
        mapping = (
            ("r.symbol", query.symbol), ("r.action", query.action),
            ("r.definition_id", str(query.definition_id) if query.definition_id else None),
            ("r.definition_version", query.definition_version),
            ("r.disposition", query.disposition.value if query.disposition else None),
            ("rr.outcome", query.rule_outcome.value if query.rule_outcome else None),
        )
        for column, value in mapping:
            if value is not None:
                clauses.append(f"{column}=?"); params.append(value)
        if query.as_of_from_utc is not None:
            clauses.append("r.as_of_utc>=?"); params.append(_iso(query.as_of_from_utc))
        if query.as_of_to_utc is not None:
            clauses.append("r.as_of_utc<?"); params.append(_iso(query.as_of_to_utc))
        where = "WHERE " + " AND ".join(clauses) if clauses else ""
        params.append(query.limit)
        with closing(self._database.connect()) as connection:
            rows = connection.execute(
                f"""SELECT r.* FROM target_adjustment_exposure_cap_results r
                    JOIN target_adjustment_exposure_cap_rule_results rr
                      ON rr.preview_result_id=r.preview_result_id
                    {where} ORDER BY r.as_of_utc DESC, r.preview_result_id DESC LIMIT ?""",
                params,
            ).fetchall()
            return tuple(self._result(connection, row) for row in rows)

    def get_exposure_cap_result(self, preview_result_id: UUID):
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                "SELECT * FROM target_adjustment_exposure_cap_results WHERE preview_result_id=?",
                (str(preview_result_id),),
            ).fetchone()
            return self._result(connection, row) if row else None

    def get_exposure_cap_source_link(self, preview_result_id: UUID):
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                "SELECT * FROM target_adjustment_exposure_cap_source_links WHERE preview_result_id=?",
                (str(preview_result_id),),
            ).fetchone()
            return self._link(row) if row else None

    @staticmethod
    def _validate_models(result, operation, link):
        if operation.status is not ExposureCapOperationStatus.COMPLETED:
            raise ValueError("accepted exposure-cap result requires a completed operation")
        if (
            operation.operation_id != result.operation_id
            or operation.run_id != result.run_id
            or operation.stage_id != result.stage_id
            or operation.preview_result_id != result.preview_result_id
            or operation.disposition is not result.disposition
            or operation.resolved_source != result.source
        ):
            raise ValueError("exposure-cap operation/result evidence is inconsistent")
        source = result.source
        expected = (
            result.operation_id, result.preview_result_id, result.run_id, result.stage_id,
            source.phase6a_review_result_id, source.phase6a_run_id, source.phase6a_stage_id,
            source.phase6a_source.decision_run_id, source.phase6a_source.intent_id,
        )
        actual = (
            link.operation_id, link.preview_result_id, link.exposure_cap_run_id,
            link.exposure_cap_stage_id, link.phase6a_review_result_id,
            link.phase6a_run_id, link.phase6a_stage_id, link.decision_run_id, link.intent_id,
        )
        if actual != expected:
            raise ValueError("exposure-cap source-link identity is inconsistent")

    @staticmethod
    def _validate_run(connection, operation):
        run = connection.execute(
            "SELECT run_type,parent_run_id FROM algorithm_runs WHERE run_id=?",
            (str(operation.run_id),),
        ).fetchone()
        if run is None or run["run_type"] != "target_adjustment_exposure_cap_preview":
            raise ValueError("exposure-cap Run is invalid")
        stage = connection.execute(
            "SELECT run_id,stage_name,sequence FROM algorithm_run_stages WHERE stage_id=?",
            (str(operation.stage_id),),
        ).fetchone()
        if stage is None or stage["run_id"] != str(operation.run_id) or stage["stage_name"] != "risk" or int(stage["sequence"]) != 1:
            raise ValueError("exposure-cap Risk stage is invalid")
        if operation.resolved_source is not None and run["parent_run_id"] != str(operation.resolved_source.phase6a_run_id):
            raise ValueError("exposure-cap parent Phase 6A Run is invalid")
        if operation.operation_type is not ExposureCapOperationType.PREVIEW and run["parent_run_id"] is not None:
            raise ValueError("exposure-cap definition Run cannot have a parent")

    @staticmethod
    def _validate_definition_append(connection, definition, operation):
        latest = connection.execute(
            """SELECT * FROM single_asset_exposure_cap_definitions
               WHERE definition_id=? ORDER BY definition_version DESC LIMIT 1""",
            (str(definition.definition_id),),
        ).fetchone()
        if definition.definition_version == 1:
            if latest is not None or definition.predecessor_version is not None:
                raise ValueError("new exposure-cap definition chain is invalid")
        else:
            if latest is None or int(latest["definition_version"]) != definition.predecessor_version:
                raise ValueError("exposure-cap predecessor version is invalid")
            if latest["status"] == "archived":
                raise ValueError("archived exposure-cap definition cannot be extended")
            if latest["symbol"] != definition.symbol:
                raise ValueError("exposure-cap symbol changed across versions")
        if operation.resolved_definition_id != definition.definition_id or operation.resolved_definition_version != definition.definition_version:
            raise ValueError("definition operation/result identity is inconsistent")

    @staticmethod
    def _validate_definition_current(connection, definition):
        row = connection.execute(
            """SELECT * FROM single_asset_exposure_cap_definitions
               WHERE definition_id=? AND definition_version=?""",
            (str(definition.definition_id), definition.definition_version),
        ).fetchone()
        latest = connection.execute(
            """SELECT definition_version,status FROM single_asset_exposure_cap_definitions
               WHERE definition_id=? ORDER BY definition_version DESC LIMIT 1""",
            (str(definition.definition_id),),
        ).fetchone()
        if row is None or SQLiteExposureCapStore._definition(row) != definition:
            raise ValueError("exposure-cap definition evidence was modified")
        if latest is None or int(latest["definition_version"]) != definition.definition_version or latest["status"] != "saved":
            raise ValueError("exposure-cap definition is superseded or archived")

    @staticmethod
    def _validate_phase6a(connection, linked):
        row = connection.execute(
            "SELECT * FROM target_adjustment_risk_review_results WHERE review_result_id=?",
            (str(linked.phase6a_review_result_id),),
        ).fetchone()
        if row is None:
            raise ValueError("Phase 6A review evidence does not exist")
        direct = {
            "operation_id": str(linked.phase6a_operation_id),
            "run_id": str(linked.phase6a_run_id),
            "stage_id": str(linked.phase6a_stage_id),
            "gate_id": linked.phase6a_gate_id,
            "gate_version": linked.phase6a_gate_version,
            "created_at_utc": _iso(linked.phase6a_created_at_utc),
            "status": "manual_review_required",
            "symbol": linked.symbol,
            "action": linked.action,
        }
        for column, expected in direct.items():
            if row[column] != expected:
                raise ValueError("Phase 6A review identity/disposition was modified")
        if _source_from(json.loads(row["source_json"])) != linked.phase6a_source:
            raise ValueError("Phase 6A source evidence was modified")
        if _safety_from(json.loads(row["safety_snapshot_json"])) != linked.phase6a_safety_snapshot:
            raise ValueError("Phase 6A safety evidence was modified")
        rules = connection.execute(
            """SELECT rule_id,rule_version,status FROM target_adjustment_risk_rule_results
               WHERE review_result_id=? ORDER BY evaluation_order""",
            (str(linked.phase6a_review_result_id),),
        ).fetchall()
        if tuple((item["rule_id"], item["rule_version"], item["status"]) for item in rules) != linked.phase6a_rule_evidence:
            raise ValueError("Phase 6A structural rule evidence was modified")
        source_link = connection.execute(
            "SELECT * FROM target_adjustment_risk_source_links WHERE review_result_id=?",
            (str(linked.phase6a_review_result_id),),
        ).fetchone()
        source = linked.phase6a_source
        if source_link is None or any(
            source_link[column] != str(expected)
            for column, expected in {
                "risk_run_id": linked.phase6a_run_id,
                "risk_stage_id": linked.phase6a_stage_id,
                "decision_run_id": source.decision_run_id,
                "intent_id": source.intent_id,
                "linked_parent_run_id": source.linked_parent_run_id,
                "target_child_run_id": source.target_child_run_id,
                "standardized_state_run_id": source.standardized_state_run_id,
            }.items()
        ):
            raise ValueError("Phase 6A source-link evidence was modified")

    @staticmethod
    def _insert_definition(connection, definition):
        connection.execute(
            """INSERT INTO single_asset_exposure_cap_definitions VALUES
               (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                str(definition.definition_id), definition.definition_version,
                definition.predecessor_version, definition.symbol,
                str(definition.max_target_exposure_usd), definition.status.value,
                definition.reason, definition.created_by, _iso(definition.created_at_utc),
                definition.software_version, definition.currency, definition.schema_version,
            ),
        )

    @staticmethod
    def _insert_operation(connection, operation):
        source = operation.resolved_source
        connection.execute(
            """
            INSERT INTO target_adjustment_exposure_cap_operations (
                attempt_id,operation_id,operation_type,status,run_id,stage_id,
                requested_at_utc,completed_at_utc,session_id,request_id,created_by,reason,
                requested_review_result_id,requested_definition_id,requested_definition_version,
                requested_symbol,requested_max_target_exposure_usd_text,
                resolved_definition_id,resolved_definition_version,resolved_source_json,
                current_safety_snapshot_json,resolved_symbol,resolved_action,resolved_as_of_utc,
                preview_result_id,disposition,error_code,error_summary,schema_version
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                str(operation.attempt_id), str(operation.operation_id), operation.operation_type.value,
                operation.status.value, str(operation.run_id), str(operation.stage_id),
                _iso(operation.requested_at_utc), _iso(operation.completed_at_utc),
                operation.session_id, operation.request_id, operation.created_by, operation.reason,
                str(operation.requested_review_result_id) if operation.requested_review_result_id else None,
                str(operation.requested_definition_id) if operation.requested_definition_id else None,
                operation.requested_definition_version, operation.requested_symbol,
                operation.requested_max_target_exposure_usd_text,
                str(operation.resolved_definition_id) if operation.resolved_definition_id else None,
                operation.resolved_definition_version,
                json.dumps(_linked_dict(source), sort_keys=True) if source else None,
                json.dumps(_safety_dict(operation.current_safety_snapshot), sort_keys=True) if operation.current_safety_snapshot else None,
                source.symbol if source else None, source.action if source else None,
                _iso(source.as_of_utc) if source else None,
                str(operation.preview_result_id) if operation.preview_result_id else None,
                operation.disposition.value if operation.disposition else None,
                operation.error_code, operation.error_summary, operation.schema_version,
            ),
        )

    @staticmethod
    def _insert_result(connection, result):
        source, rule = result.source, result.rule
        evidence = source.phase6a_source
        connection.execute(
            """INSERT INTO target_adjustment_exposure_cap_results VALUES
               (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                str(result.preview_result_id), str(result.operation_id), str(result.run_id),
                str(result.stage_id), json.dumps(_linked_dict(source), sort_keys=True),
                str(source.phase6a_review_result_id), str(source.phase6a_run_id),
                str(source.phase6a_stage_id), str(source.definition.definition_id),
                source.definition.definition_version, source.symbol, _iso(source.as_of_utc),
                source.action, str(evidence.current_exposure_usd), str(evidence.target_exposure_usd),
                str(evidence.requested_notional_usd), str(source.definition.max_target_exposure_usd),
                str(rule.cap_constrained_candidate_notional_usd), str(rule.reduction_usd),
                result.disposition.value, json.dumps(result.reason_codes), json.dumps(result.warnings),
                _iso(result.created_at_utc), result.created_by, result.reason,
                result.software_version, result.component_id, result.component_version,
                result.schema_version,
            ),
        )

    @staticmethod
    def _insert_rule(connection, rule):
        connection.execute(
            """INSERT INTO target_adjustment_exposure_cap_rule_results VALUES
               (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                str(rule.rule_result_id), str(rule.preview_result_id), str(rule.run_id),
                str(rule.stage_id), rule.rule_id, rule.rule_version, rule.evaluation_order,
                rule.action, str(rule.current_exposure_usd), str(rule.target_exposure_usd),
                str(rule.original_requested_notional_usd), str(rule.max_target_exposure_usd),
                str(rule.cap_constrained_candidate_notional_usd), str(rule.reduction_usd),
                rule.outcome.value, json.dumps(rule.reason_codes), int(rule.stop_processing),
                _iso(rule.evaluated_at_utc), rule.schema_version,
            ),
        )

    @staticmethod
    def _insert_link(connection, link):
        connection.execute(
            """INSERT INTO target_adjustment_exposure_cap_source_links VALUES
               (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                str(link.source_link_id), str(link.operation_id), str(link.preview_result_id),
                str(link.exposure_cap_run_id), str(link.exposure_cap_stage_id),
                str(link.phase6a_review_result_id), str(link.phase6a_run_id),
                str(link.phase6a_stage_id), str(link.decision_run_id),
                str(link.linked_parent_run_id), str(link.target_child_run_id),
                str(link.standardized_state_run_id), str(link.decision_result_id),
                str(link.intent_id), str(link.target_position_link_id),
                str(link.target_calculation_id), str(link.standardized_state_calculation_id),
                _iso(link.created_at_utc), link.schema_version,
            ),
        )

    @staticmethod
    def _definition(row):
        return SingleAssetExposureCapDefinitionVersion(
            UUID(row["definition_id"]), int(row["definition_version"]),
            int(row["predecessor_version"]) if row["predecessor_version"] is not None else None,
            row["symbol"], Decimal(row["max_target_exposure_usd_text"]),
            ExposureCapDefinitionStatus(row["status"]), row["reason"], row["created_by"],
            _dt(row["created_at_utc"]), row["software_version"], row["currency"],
            int(row["schema_version"]),
        )

    @staticmethod
    def _operation(row):
        source = _linked_from(json.loads(row["resolved_source_json"])) if row["resolved_source_json"] else None
        safety = _safety_from(json.loads(row["current_safety_snapshot_json"])) if row["current_safety_snapshot_json"] else None
        return ExposureCapOperationAttempt(
            UUID(row["attempt_id"]), UUID(row["operation_id"]),
            ExposureCapOperationType(row["operation_type"]), ExposureCapOperationStatus(row["status"]),
            UUID(row["run_id"]), UUID(row["stage_id"]), _dt(row["requested_at_utc"]),
            _dt(row["completed_at_utc"]), row["session_id"], row["request_id"],
            row["created_by"], row["reason"],
            UUID(row["requested_review_result_id"]) if row["requested_review_result_id"] else None,
            UUID(row["requested_definition_id"]) if row["requested_definition_id"] else None,
            int(row["requested_definition_version"]) if row["requested_definition_version"] is not None else None,
            row["requested_symbol"], row["requested_max_target_exposure_usd_text"],
            UUID(row["resolved_definition_id"]) if row["resolved_definition_id"] else None,
            int(row["resolved_definition_version"]) if row["resolved_definition_version"] is not None else None,
            source, safety,
            UUID(row["preview_result_id"]) if row["preview_result_id"] else None,
            ExposureCapDisposition(row["disposition"]) if row["disposition"] else None,
            row["error_code"], row["error_summary"], int(row["schema_version"]),
        )

    @staticmethod
    def _result(connection, row):
        rule_row = connection.execute(
            "SELECT * FROM target_adjustment_exposure_cap_rule_results WHERE preview_result_id=?",
            (row["preview_result_id"],),
        ).fetchone()
        if rule_row is None:
            raise sqlite3.DatabaseError("exposure-cap result is missing its locked rule")
        rule = ExposureCapRuleResult(
            UUID(rule_row["rule_result_id"]), UUID(rule_row["preview_result_id"]),
            UUID(rule_row["run_id"]), UUID(rule_row["stage_id"]), rule_row["action"],
            Decimal(rule_row["current_exposure_usd_text"]),
            Decimal(rule_row["target_exposure_usd_text"]),
            Decimal(rule_row["original_requested_notional_usd_text"]),
            Decimal(rule_row["max_target_exposure_usd_text"]),
            Decimal(rule_row["cap_constrained_candidate_notional_usd_text"]),
            Decimal(rule_row["reduction_usd_text"]),
            ExposureCapRuleOutcome(rule_row["outcome"]),
            tuple(json.loads(rule_row["reason_codes_json"])),
            _dt(rule_row["evaluated_at_utc"]), bool(rule_row["stop_processing"]),
            rule_row["rule_id"], rule_row["rule_version"],
            int(rule_row["evaluation_order"]), int(rule_row["schema_version"]),
        )
        return TargetAdjustmentExposureCapPreviewResult(
            UUID(row["preview_result_id"]), UUID(row["operation_id"]),
            UUID(row["run_id"]), UUID(row["stage_id"]),
            _linked_from(json.loads(row["source_json"])), rule,
            ExposureCapDisposition(row["disposition"]),
            tuple(json.loads(row["reason_codes_json"])), tuple(json.loads(row["warnings_json"])),
            _dt(row["created_at_utc"]), row["created_by"], row["reason"],
            row["software_version"], row["component_id"], row["component_version"],
            int(row["schema_version"]),
        )

    @staticmethod
    def _link(row):
        return ExposureCapSourceLink(
            UUID(row["source_link_id"]), UUID(row["operation_id"]),
            UUID(row["preview_result_id"]), UUID(row["exposure_cap_run_id"]),
            UUID(row["exposure_cap_stage_id"]), UUID(row["phase6a_review_result_id"]),
            UUID(row["phase6a_run_id"]), UUID(row["phase6a_stage_id"]),
            UUID(row["decision_run_id"]), UUID(row["linked_parent_run_id"]),
            UUID(row["target_child_run_id"]), UUID(row["standardized_state_run_id"]),
            UUID(row["decision_result_id"]), UUID(row["intent_id"]),
            UUID(row["target_position_link_id"]), UUID(row["target_calculation_id"]),
            UUID(row["standardized_state_calculation_id"]), _dt(row["created_at_utc"]),
            int(row["schema_version"]),
        )


__all__ = ["SQLiteExposureCapStore"]
