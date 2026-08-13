"""Central SQLite adapter for P23-4B structural Risk evidence."""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from uuid import UUID

from quant_trading.application_settings import ExecutionEnvironment
from quant_trading.risk import (
    CycleTargetRiskOperationAttempt,
    CycleTargetRiskQuery,
    CycleTargetRiskReviewInput,
    CycleTargetRiskReviewResult,
    CycleTargetRiskSourceLink,
    CycleTargetRiskStatus,
    CycleTargetStructuralRiskRuleResult,
    RiskSafetyStateSnapshot,
    StructuralRuleSeverity,
    StructuralRuleStatus,
)

from .sqlite_database import CentralSQLiteDatabase


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="microseconds")


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(UTC)


def _source_dict(source: CycleTargetRiskReviewInput) -> dict[str, object]:
    values: dict[str, object] = {}
    for name in source.__dataclass_fields__:
        value = getattr(source, name)
        if isinstance(value, (UUID, Decimal)):
            values[name] = str(value)
        elif isinstance(value, datetime):
            values[name] = _iso(value)
        elif isinstance(value, date):
            values[name] = value.isoformat()
        else:
            values[name] = value
    return values


def _source_from(data: dict[str, object]) -> CycleTargetRiskReviewInput:
    values = dict(data)
    uuid_names = {
        "decision_result_id", "decision_operation_id", "decision_run_id",
        "decision_target_stage_id", "decision_stage_id", "intent_id", "source_result_id",
        "source_operation_id", "source_run_id", "source_state_stage_id",
        "source_target_stage_id", "source_formula_definition_id", "source_configuration_id",
        "source_reversal_result_id", "source_reversal_run_id", "source_reversal_step_id",
    }
    decimal_names = {
        "target_fraction", "research_capital_basis_usd", "current_exposure_usd",
        "target_exposure_usd", "desired_change_usd", "requested_notional_usd",
    }
    time_names = {
        "decision_created_at_utc", "intent_created_at_utc", "source_available_at_utc",
        "source_created_at_utc",
    }
    for name in uuid_names:
        values[name] = UUID(str(values[name]))
    for name in decimal_names:
        values[name] = Decimal(str(values[name]))
    for name in time_names:
        values[name] = _dt(str(values[name]))
    values["source_session"] = date.fromisoformat(str(values["source_session"]))
    return CycleTargetRiskReviewInput(**values)


def _safety_dict(snapshot: RiskSafetyStateSnapshot) -> dict[str, object]:
    return {
        "snapshot_id": str(snapshot.snapshot_id),
        "execution_environment": snapshot.execution_environment.value,
        "live_trading_enabled": snapshot.live_trading_enabled,
        "automatic_submission_enabled": snapshot.automatic_submission_enabled,
        "manual_confirmation_required": snapshot.manual_confirmation_required,
        "execution_capability_implemented": snapshot.execution_capability_implemented,
        "configuration_version": snapshot.configuration_version,
        "software_version": snapshot.software_version,
        "source_revision": snapshot.source_revision,
        "worktree_state": snapshot.worktree_state,
        "captured_at_utc": _iso(snapshot.captured_at_utc),
        "schema_version": snapshot.schema_version,
    }


def _safety_from(data: dict[str, object]) -> RiskSafetyStateSnapshot:
    return RiskSafetyStateSnapshot(
        UUID(str(data["snapshot_id"])),
        ExecutionEnvironment(str(data["execution_environment"])),
        bool(data["live_trading_enabled"]), bool(data["automatic_submission_enabled"]),
        bool(data["manual_confirmation_required"]), bool(data["execution_capability_implemented"]),
        str(data["configuration_version"]), str(data["software_version"]),
        str(data["source_revision"]) if data["source_revision"] is not None else None,
        str(data["worktree_state"]), _dt(str(data["captured_at_utc"])),
        int(data["schema_version"]),
    )


class SQLiteCycleTargetRiskStore:
    def __init__(self, database_path: Path | str) -> None:
        self._database = CentralSQLiteDatabase(database_path)

    def initialize(self) -> None:
        self._database.initialize()

    def get_first_operation(self, operation_id: UUID):
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                """SELECT * FROM cycle_target_risk_operation_attempts
                   WHERE operation_id = ?
                   ORDER BY CASE WHEN status IN ('manual_review_required','blocked') THEN 0 ELSE 1 END,
                            rowid LIMIT 1""",
                (str(operation_id),),
            ).fetchone()
            return self._operation(row) if row else None

    def save_operation(self, operation: CycleTargetRiskOperationAttempt) -> None:
        with closing(self._database.connect()) as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                self._validate_run(connection, operation)
                self._insert_operation(connection, operation)
                connection.commit()
            except Exception as exc:
                connection.rollback()
                raise sqlite3.DatabaseError("could not save P33 Risk operation") from exc

    def save_completed(self, result, operation, source_link) -> None:
        self._validate_models(result, operation, source_link)
        with closing(self._database.connect()) as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                self._validate_run(connection, operation)
                self._validate_source(connection, result.source)
                self._insert_operation(connection, operation)
                self._insert_result(connection, result)
                for rule in result.rules:
                    self._insert_rule(connection, rule)
                self._insert_link(connection, source_link)
                connection.commit()
            except Exception as exc:
                connection.rollback()
                raise sqlite3.DatabaseError("could not save completed P33 Risk review") from exc

    def list_cycle_target_risk_operations(self, query=CycleTargetRiskQuery()):
        clauses, params = self._clauses(query, "o")
        where = "WHERE " + " AND ".join(clauses) if clauses else ""
        params.append(query.limit)
        with closing(self._database.connect()) as connection:
            rows = connection.execute(
                f"SELECT o.* FROM cycle_target_risk_operation_attempts o {where} ORDER BY requested_at_utc DESC, attempt_id DESC LIMIT ?",
                params,
            ).fetchall()
            return tuple(self._operation(row) for row in rows)

    def list_cycle_target_risk_results(self, query=CycleTargetRiskQuery()):
        clauses, params = self._clauses(query, "r")
        where = "WHERE " + " AND ".join(clauses) if clauses else ""
        params.append(query.limit)
        with closing(self._database.connect()) as connection:
            rows = connection.execute(
                f"SELECT r.* FROM cycle_target_risk_review_results r {where} ORDER BY created_at_utc DESC, review_result_id DESC LIMIT ?",
                params,
            ).fetchall()
            return tuple(self._result(connection, row) for row in rows)

    def get_cycle_target_risk_result(self, review_result_id: UUID):
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                "SELECT * FROM cycle_target_risk_review_results WHERE review_result_id=?",
                (str(review_result_id),),
            ).fetchone()
            return self._result(connection, row) if row else None

    def get_cycle_target_risk_source_link(self, review_result_id: UUID):
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                "SELECT * FROM cycle_target_risk_source_links WHERE review_result_id=?",
                (str(review_result_id),),
            ).fetchone()
            return self._link(row) if row else None

    @staticmethod
    def _clauses(query, alias):
        clauses: list[str] = []
        params: list[object] = []
        if alias == "o":
            mapping = (
                ("resolved_symbol", query.symbol), ("resolved_action", query.action),
                ("status", query.status.value if query.status else None),
                ("requested_intent_id", str(query.intent_id) if query.intent_id else None),
                ("requested_decision_result_id", str(query.decision_result_id) if query.decision_result_id else None),
                ("requested_decision_run_id", str(query.decision_run_id) if query.decision_run_id else None),
            )
        else:
            mapping = (
                ("symbol", query.symbol), ("action", query.action),
                ("status", query.status.value if query.status else None),
                ("intent_id", str(query.intent_id) if query.intent_id else None),
                ("decision_result_id", str(query.decision_result_id) if query.decision_result_id else None),
                ("decision_run_id", str(query.decision_run_id) if query.decision_run_id else None),
                ("source_result_id", str(query.source_result_id) if query.source_result_id else None),
                ("source_run_id", str(query.source_run_id) if query.source_run_id else None),
            )
        for column, value in mapping:
            if value is not None:
                clauses.append(f"{alias}.{column} = ?")
                params.append(value)
        session_column = "resolved_source_session" if alias == "o" else "source_session"
        if query.source_session_from:
            clauses.append(f"{alias}.{session_column} >= ?")
            params.append(query.source_session_from.isoformat())
        if query.source_session_to:
            clauses.append(f"{alias}.{session_column} <= ?")
            params.append(query.source_session_to.isoformat())
        created_column = "requested_at_utc" if alias == "o" else "created_at_utc"
        if query.created_from_utc:
            clauses.append(f"{alias}.{created_column} >= ?")
            params.append(_iso(query.created_from_utc))
        if query.created_to_utc:
            clauses.append(f"{alias}.{created_column} < ?")
            params.append(_iso(query.created_to_utc))
        return clauses, params

    @staticmethod
    def _validate_models(result, operation, link):
        if (
            operation.status != result.status or operation.review_result_id != result.review_result_id
            or operation.resolved_source != result.source
            or operation.safety_snapshot != result.safety_snapshot
            or (operation.operation_id, operation.run_id, operation.risk_stage_id)
               != (result.operation_id, result.run_id, result.stage_id)
        ):
            raise ValueError("P33 operation/result evidence is inconsistent")
        source = result.source
        if (
            link.operation_id, link.review_result_id, link.risk_run_id, link.risk_stage_id,
            link.decision_result_id, link.intent_id, link.source_result_id
        ) != (
            result.operation_id, result.review_result_id, result.run_id, result.stage_id,
            source.decision_result_id, source.intent_id, source.source_result_id
        ):
            raise ValueError("P33 source-link identity is inconsistent")

    @staticmethod
    def _validate_run(connection, operation):
        run = connection.execute(
            "SELECT run_type,parent_run_id FROM algorithm_runs WHERE run_id=?",
            (str(operation.run_id),),
        ).fetchone()
        if run is None or run["run_type"] != "cycle_target_risk_review":
            raise ValueError("P33 Run is invalid")
        if run["parent_run_id"] != str(operation.requested_decision_run_id):
            raise ValueError("P33 parent Run is invalid")
        for stage_id, name, sequence in ((operation.decision_stage_id, "decision", 1), (operation.risk_stage_id, "risk", 2)):
            if stage_id is None:
                continue
            stage = connection.execute(
                "SELECT run_id,stage_name,sequence FROM algorithm_run_stages WHERE stage_id=?",
                (str(stage_id),),
            ).fetchone()
            if stage is None or stage["run_id"] != str(operation.run_id) or stage["stage_name"] != name or int(stage["sequence"]) != sequence:
                raise ValueError(f"P33 {name} stage is invalid")

    @staticmethod
    def _validate_source(connection, source):
        intent = connection.execute("SELECT * FROM cycle_target_decision_trade_intents WHERE intent_id=?", (str(source.intent_id),)).fetchone()
        result = connection.execute("SELECT * FROM cycle_target_decision_results WHERE decision_result_id=?", (str(source.decision_result_id),)).fetchone()
        link = connection.execute("SELECT * FROM cycle_target_decision_source_links WHERE decision_result_id=?", (str(source.decision_result_id),)).fetchone()
        target = connection.execute("SELECT * FROM cycle_target_results WHERE result_id=?", (str(source.source_result_id),)).fetchone()
        configuration = connection.execute(
            "SELECT * FROM cycle_target_asset_configurations WHERE configuration_id=?",
            (str(source.source_configuration_id),),
        ).fetchone()
        if not all((intent, result, link, target, configuration)):
            raise ValueError("exact P31/P29 source evidence does not exist")
        expected_intent = {
            "decision_result_id": str(source.decision_result_id), "operation_id": str(source.decision_operation_id),
            "run_id": str(source.decision_run_id), "decision_stage_id": str(source.decision_stage_id),
            "source_result_id": str(source.source_result_id), "source_run_id": str(source.source_run_id),
            "symbol": source.symbol, "source_session": source.source_session.isoformat(),
            "source_available_at_utc": _iso(source.source_available_at_utc), "action": source.action,
            "current_exposure_usd_text": str(source.current_exposure_usd),
            "target_exposure_usd_text": str(source.target_exposure_usd),
            "desired_change_usd_text": str(source.desired_change_usd),
            "requested_notional_usd_text": str(source.requested_notional_usd),
            "created_at_utc": _iso(source.intent_created_at_utc),
            "policy_id": source.decision_policy_id, "policy_version": source.decision_policy_version,
            "execution_allowed": 0, "live_allowed": 0, "schema_version": source.intent_schema_version,
        }
        SQLiteCycleTargetRiskStore._match_row(intent, expected_intent, "P31 intent")
        expected_result = {
            "operation_id": str(source.decision_operation_id), "run_id": str(source.decision_run_id),
            "target_stage_id": str(source.decision_target_stage_id), "decision_stage_id": str(source.decision_stage_id),
            "source_result_id": str(source.source_result_id), "source_run_id": str(source.source_run_id),
            "status": "intent_created", "action": source.action,
            "created_at_utc": _iso(source.decision_created_at_utc),
            "software_version": source.decision_software_version,
            "source_revision": source.decision_source_revision,
            "worktree_state": source.decision_worktree_state,
            "policy_id": source.decision_policy_id, "policy_version": source.decision_policy_version,
            "execution_allowed": 0, "live_allowed": 0, "schema_version": source.decision_result_schema_version,
        }
        SQLiteCycleTargetRiskStore._match_row(result, expected_result, "P31 result")
        expected_link = {
            "intent_id": str(source.intent_id), "decision_run_id": str(source.decision_run_id),
            "source_result_id": str(source.source_result_id), "source_operation_id": str(source.source_operation_id),
            "source_run_id": str(source.source_run_id), "source_state_stage_id": str(source.source_state_stage_id),
            "source_target_stage_id": str(source.source_target_stage_id),
            "source_formula_definition_id": str(source.source_formula_definition_id),
            "source_configuration_id": str(source.source_configuration_id),
            "source_reversal_result_id": str(source.source_reversal_result_id),
            "source_reversal_run_id": str(source.source_reversal_run_id),
            "source_reversal_step_id": str(source.source_reversal_step_id),
        }
        SQLiteCycleTargetRiskStore._match_row(link, expected_link, "P31 source link")
        expected_target = {
            "operation_id": str(source.source_operation_id), "run_id": str(source.source_run_id),
            "state_stage_id": str(source.source_state_stage_id), "target_stage_id": str(source.source_target_stage_id),
            "formula_definition_id": str(source.source_formula_definition_id),
            "formula_definition_version": source.source_formula_definition_version,
            "configuration_id": str(source.source_configuration_id),
            "configuration_version": source.source_configuration_version,
            "source_result_id": str(source.source_reversal_result_id),
            "source_run_id": str(source.source_reversal_run_id),
            "source_step_id": str(source.source_reversal_step_id),
            "calculation_fingerprint": source.source_calculation_fingerprint,
            "symbol": source.symbol, "session": source.source_session.isoformat(),
            "available_at_utc": _iso(source.source_available_at_utc),
            "region": source.source_region, "status": source.source_status,
            "target_fraction_text": str(source.target_fraction),
            "research_capital_basis_usd_text": str(source.research_capital_basis_usd),
            "current_position_value_usd_text": str(source.current_exposure_usd),
            "target_position_value_usd_text": str(source.target_exposure_usd),
            "adjustment_value_usd_text": str(source.desired_change_usd),
            "adjustment_direction": source.action,
            "created_at_utc": _iso(source.source_created_at_utc),
            "execution_allowed": 0, "live_allowed": 0, "schema_version": source.source_schema_version,
        }
        SQLiteCycleTargetRiskStore._match_row(target, expected_target, "P29 result")
        expected_configuration = {
            "configuration_version": source.source_configuration_version,
            "formula_definition_id": str(source.source_formula_definition_id),
            "formula_definition_version": source.source_formula_definition_version,
            "symbol": source.symbol,
            "constraint_fingerprint": source.source_configuration_fingerprint,
            "execution_allowed": 0,
            "live_allowed": 0,
            "schema_version": 1,
        }
        SQLiteCycleTargetRiskStore._match_row(
            configuration, expected_configuration, "P29 configuration"
        )

    @staticmethod
    def _match_row(row, expected, label):
        for column, value in expected.items():
            actual = row[column]
            if column.endswith("_text") and value is not None:
                if Decimal(actual) != Decimal(value):
                    raise ValueError(f"{label} amount was modified")
            elif column.endswith("_utc") and value is not None:
                if _dt(actual) != _dt(value):
                    raise ValueError(f"{label} timestamp was modified: {column}")
            elif actual != value:
                raise ValueError(f"{label} identity was modified: {column}")

    @staticmethod
    def _insert_operation(connection, operation):
        source = operation.resolved_source
        connection.execute(
            "INSERT INTO cycle_target_risk_operation_attempts VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                str(operation.attempt_id), str(operation.operation_id), str(operation.run_id),
                str(operation.decision_stage_id), str(operation.risk_stage_id) if operation.risk_stage_id else None,
                operation.command_fingerprint, str(operation.requested_intent_id),
                str(operation.requested_decision_result_id), str(operation.requested_decision_run_id),
                operation.status.value, _iso(operation.requested_at_utc), _iso(operation.completed_at_utc),
                operation.session_id, operation.request_id, operation.created_by, operation.reason,
                json.dumps(_source_dict(source), sort_keys=True, separators=(",", ":")) if source else None,
                json.dumps(_safety_dict(operation.safety_snapshot), sort_keys=True, separators=(",", ":")) if operation.safety_snapshot else None,
                source.symbol if source else None, source.action if source else None,
                source.source_session.isoformat() if source else None,
                str(operation.review_result_id) if operation.review_result_id else None,
                operation.error_code, operation.error_summary, int(operation.execution_allowed),
                int(operation.live_allowed), operation.schema_version,
            ),
        )

    @staticmethod
    def _insert_result(connection, result):
        source = result.source
        connection.execute(
            "INSERT INTO cycle_target_risk_review_results VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                str(result.review_result_id), str(result.operation_id), str(result.run_id), str(result.stage_id),
                json.dumps(_source_dict(source), sort_keys=True, separators=(",", ":")),
                json.dumps(_safety_dict(result.safety_snapshot), sort_keys=True, separators=(",", ":")),
                str(result.safety_snapshot.snapshot_id), str(source.decision_result_id), str(source.intent_id),
                str(source.decision_run_id), str(source.source_result_id), str(source.source_run_id),
                str(source.source_reversal_result_id), str(source.source_reversal_run_id),
                str(source.source_reversal_step_id), source.symbol, source.source_session.isoformat(),
                _iso(source.source_available_at_utc), source.action, str(source.current_exposure_usd),
                str(source.target_exposure_usd), str(source.desired_change_usd),
                str(source.requested_notional_usd), result.status.value,
                json.dumps(result.reason_codes), json.dumps(result.warnings), _iso(result.created_at_utc),
                result.created_by, result.reason, result.software_version, None, None,
                int(result.execution_allowed), int(result.live_allowed), result.gate_id,
                result.gate_version, result.schema_version,
            ),
        )

    @staticmethod
    def _insert_rule(connection, rule):
        connection.execute(
            "INSERT INTO cycle_target_risk_rule_results VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                str(rule.rule_result_id), str(rule.review_result_id), str(rule.run_id),
                str(rule.stage_id), rule.rule_id, rule.rule_version, rule.rule_name,
                rule.evaluation_order, rule.status.value, rule.input_summary,
                rule.expected_condition, json.dumps(rule.reason_codes), rule.severity.value,
                int(rule.stop_processing), _iso(rule.evaluated_at_utc), rule.schema_version,
            ),
        )

    @staticmethod
    def _insert_link(connection, link):
        connection.execute(
            "INSERT INTO cycle_target_risk_source_links VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                str(link.source_link_id), str(link.operation_id), str(link.review_result_id),
                str(link.risk_run_id), str(link.risk_stage_id), str(link.decision_result_id),
                str(link.intent_id), str(link.decision_run_id), str(link.source_result_id),
                str(link.source_run_id), str(link.source_reversal_result_id),
                str(link.source_reversal_run_id), str(link.source_reversal_step_id),
                str(link.source_formula_definition_id), str(link.source_configuration_id),
                _iso(link.created_at_utc), link.schema_version,
            ),
        )

    @staticmethod
    def _operation(row):
        source = _source_from(json.loads(row["resolved_source_json"])) if row["resolved_source_json"] else None
        safety = _safety_from(json.loads(row["safety_snapshot_json"])) if row["safety_snapshot_json"] else None
        return CycleTargetRiskOperationAttempt(
            UUID(row["attempt_id"]), UUID(row["operation_id"]), UUID(row["run_id"]),
            UUID(row["decision_stage_id"]), UUID(row["risk_stage_id"]) if row["risk_stage_id"] else None,
            row["command_fingerprint"], UUID(row["requested_intent_id"]),
            UUID(row["requested_decision_result_id"]), UUID(row["requested_decision_run_id"]),
            CycleTargetRiskStatus(row["status"]), _dt(row["requested_at_utc"]),
            _dt(row["completed_at_utc"]), row["session_id"], row["request_id"],
            row["created_by"], row["reason"], source, safety,
            UUID(row["review_result_id"]) if row["review_result_id"] else None,
            row["error_code"], row["error_summary"], bool(row["execution_allowed"]),
            bool(row["live_allowed"]), int(row["schema_version"]),
        )

    @staticmethod
    def _result(connection, row):
        rule_rows = connection.execute(
            "SELECT * FROM cycle_target_risk_rule_results WHERE review_result_id=? ORDER BY evaluation_order",
            (row["review_result_id"],),
        ).fetchall()
        rules = tuple(
            CycleTargetStructuralRiskRuleResult(
                UUID(item["rule_result_id"]), UUID(item["review_result_id"]), UUID(item["run_id"]),
                UUID(item["stage_id"]), item["rule_id"], item["rule_version"], item["rule_name"],
                int(item["evaluation_order"]), StructuralRuleStatus(item["status"]),
                item["input_summary"], item["expected_condition"],
                tuple(json.loads(item["reason_codes_json"])), StructuralRuleSeverity(item["severity"]),
                bool(item["stop_processing"]), _dt(item["evaluated_at_utc"]), int(item["schema_version"]),
            )
            for item in rule_rows
        )
        return CycleTargetRiskReviewResult(
            UUID(row["review_result_id"]), UUID(row["operation_id"]), UUID(row["run_id"]),
            UUID(row["stage_id"]), _source_from(json.loads(row["source_json"])),
            _safety_from(json.loads(row["safety_snapshot_json"])), CycleTargetRiskStatus(row["status"]),
            rules, tuple(json.loads(row["reason_codes_json"])), tuple(json.loads(row["warnings_json"])),
            _dt(row["created_at_utc"]), row["created_by"], row["reason"], row["software_version"],
            execution_allowed=bool(row["execution_allowed"]), live_allowed=bool(row["live_allowed"]),
            gate_id=row["gate_id"], gate_version=row["gate_version"], schema_version=int(row["schema_version"]),
        )

    @staticmethod
    def _link(row):
        return CycleTargetRiskSourceLink(
            UUID(row["source_link_id"]), UUID(row["operation_id"]), UUID(row["review_result_id"]),
            UUID(row["risk_run_id"]), UUID(row["risk_stage_id"]), UUID(row["decision_result_id"]),
            UUID(row["intent_id"]), UUID(row["decision_run_id"]), UUID(row["source_result_id"]),
            UUID(row["source_run_id"]), UUID(row["source_reversal_result_id"]),
            UUID(row["source_reversal_run_id"]), UUID(row["source_reversal_step_id"]),
            UUID(row["source_formula_definition_id"]), UUID(row["source_configuration_id"]),
            _dt(row["created_at_utc"]), int(row["schema_version"]),
        )


__all__ = ["SQLiteCycleTargetRiskStore"]
