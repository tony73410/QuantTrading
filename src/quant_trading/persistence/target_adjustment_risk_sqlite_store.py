"""SQLite adapter for target-adjustment Risk manual-review evidence."""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from uuid import UUID

from quant_trading.application_settings import ExecutionEnvironment
from quant_trading.risk import (
    LinkedTargetRiskReviewInput,
    RiskSafetyStateSnapshot,
    StructuralRuleSeverity,
    StructuralRuleStatus,
    TargetAdjustmentRiskOperationAttempt,
    TargetAdjustmentRiskQuery,
    TargetAdjustmentRiskReviewResult,
    TargetAdjustmentRiskSourceLink,
    TargetAdjustmentRiskStatus,
    TargetAdjustmentStructuralRuleResult,
)

from .sqlite_database import CentralSQLiteDatabase


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="microseconds")


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(UTC)


def _source_dict(source: LinkedTargetRiskReviewInput) -> dict[str, object]:
    values = {}
    for name in source.__dataclass_fields__:
        value = getattr(source, name)
        values[name] = str(value) if isinstance(value, (UUID, Decimal)) else _iso(value) if isinstance(value, datetime) else value
    return values


def _source_from(data: dict[str, object]) -> LinkedTargetRiskReviewInput:
    uuid_names = {
        "decision_result_id", "decision_operation_id", "decision_run_id",
        "decision_stage_id", "intent_id", "target_position_link_id",
        "linked_target_operation_id",
        "linked_parent_run_id", "target_child_run_id", "standardized_state_run_id",
        "target_calculation_id", "target_definition_id",
        "standardized_state_calculation_id", "standardized_state_definition_id",
    }
    time_names = {
        "as_of_utc", "decision_created_at_utc", "intent_created_at_utc",
        "target_position_link_created_at_utc", "target_result_created_at_utc",
        "standardized_state_created_at_utc",
    }
    money_names = {"current_exposure_usd", "target_exposure_usd", "desired_change_usd", "requested_notional_usd"}
    values = dict(data)
    for name in uuid_names: values[name] = UUID(str(values[name]))
    for name in time_names: values[name] = _dt(str(values[name]))
    for name in money_names: values[name] = Decimal(str(values[name]))
    return LinkedTargetRiskReviewInput(**values)


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
    return RiskSafetyStateSnapshot(UUID(str(data["snapshot_id"])), ExecutionEnvironment(str(data["execution_environment"])), bool(data["live_trading_enabled"]), bool(data["automatic_submission_enabled"]), bool(data["manual_confirmation_required"]), bool(data["execution_capability_implemented"]), str(data["configuration_version"]), str(data["software_version"]), str(data["source_revision"]) if data["source_revision"] is not None else None, str(data["worktree_state"]), _dt(str(data["captured_at_utc"])), int(data["schema_version"]))


class SQLiteTargetAdjustmentRiskStore:
    def __init__(self, database_path: Path | str) -> None:
        self._database = CentralSQLiteDatabase(database_path)

    def initialize(self) -> None:
        self._database.initialize()

    def get_first_operation(self, operation_id: UUID):
        with closing(self._database.connect()) as connection:
            row = connection.execute("SELECT * FROM target_adjustment_risk_operations WHERE operation_id = ? ORDER BY CASE WHEN status IN ('manual_review_required','blocked') THEN 0 ELSE 1 END, rowid LIMIT 1", (str(operation_id),)).fetchone()
            return self._operation(row) if row else None

    def save_operation(self, operation: TargetAdjustmentRiskOperationAttempt) -> None:
        with closing(self._database.connect()) as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                self._validate_run(connection, operation)
                self._insert_operation(connection, operation)
                connection.commit()
            except Exception as exc:
                connection.rollback()
                raise sqlite3.DatabaseError("could not save target-adjustment Risk operation") from exc

    def save_completed(self, result, operation, source_link) -> None:
        self._validate_models(result, operation, source_link)
        with closing(self._database.connect()) as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                self._validate_run(connection, operation)
                self._validate_source(connection, result.source)
                self._insert_operation(connection, operation)
                self._insert_result(connection, result)
                for rule in result.rules: self._insert_rule(connection, rule)
                self._insert_link(connection, source_link)
                connection.commit()
            except Exception as exc:
                connection.rollback()
                raise sqlite3.DatabaseError("could not save completed target-adjustment Risk review") from exc

    def list_target_adjustment_risk_operations(self, query=TargetAdjustmentRiskQuery()):
        clauses, params = self._clauses(query, "o")
        where = "WHERE " + " AND ".join(clauses) if clauses else ""
        params.append(query.limit)
        with closing(self._database.connect()) as connection:
            rows = connection.execute(f"SELECT o.* FROM target_adjustment_risk_operations o {where} ORDER BY requested_at_utc DESC, attempt_id DESC LIMIT ?", params).fetchall()
            return tuple(self._operation(row) for row in rows)

    def list_target_adjustment_risk_results(self, query=TargetAdjustmentRiskQuery()):
        clauses, params = self._clauses(query, "r")
        where = "WHERE " + " AND ".join(clauses) if clauses else ""
        params.append(query.limit)
        with closing(self._database.connect()) as connection:
            rows = connection.execute(f"SELECT r.* FROM target_adjustment_risk_review_results r {where} ORDER BY as_of_utc DESC, review_result_id DESC LIMIT ?", params).fetchall()
            return tuple(self._result(connection, row) for row in rows)

    def get_target_adjustment_risk_result(self, review_result_id: UUID):
        with closing(self._database.connect()) as connection:
            row = connection.execute("SELECT * FROM target_adjustment_risk_review_results WHERE review_result_id = ?", (str(review_result_id),)).fetchone()
            return self._result(connection, row) if row else None

    def get_target_adjustment_risk_source_link(self, review_result_id: UUID):
        with closing(self._database.connect()) as connection:
            row = connection.execute("SELECT * FROM target_adjustment_risk_source_links WHERE review_result_id = ?", (str(review_result_id),)).fetchone()
            return self._link(row) if row else None

    @staticmethod
    def _clauses(query, alias):
        clauses, params = [], []
        mapping = (("symbol", query.symbol), ("action", query.action), ("status", query.status.value if query.status else None))
        for column, value in mapping:
            if value is not None:
                actual = f"resolved_{column}" if alias == "o" and column in {"symbol", "action"} else column
                clauses.append(f"{alias}.{actual} = ?"); params.append(value)
        date_column = "resolved_as_of_utc" if alias == "o" else "as_of_utc"
        if query.as_of_from_utc: clauses.append(f"{alias}.{date_column} >= ?"); params.append(_iso(query.as_of_from_utc))
        if query.as_of_to_utc: clauses.append(f"{alias}.{date_column} < ?"); params.append(_iso(query.as_of_to_utc))
        return clauses, params

    @staticmethod
    def _validate_models(result, operation, link):
        if operation.status != result.status or operation.review_result_id != result.review_result_id or operation.resolved_source != result.source or operation.safety_snapshot != result.safety_snapshot:
            raise ValueError("Risk operation/result evidence is inconsistent")
        if operation.operation_id != result.operation_id or operation.run_id != result.run_id or operation.risk_stage_id != result.stage_id:
            raise ValueError("Risk result identity is inconsistent")
        source = result.source
        if (link.operation_id, link.review_result_id, link.risk_run_id, link.risk_stage_id, link.decision_result_id, link.intent_id) != (result.operation_id, result.review_result_id, result.run_id, result.stage_id, source.decision_result_id, source.intent_id):
            raise ValueError("Risk source-link identity is inconsistent")

    @staticmethod
    def _validate_run(connection, operation):
        run = connection.execute("SELECT run_type,parent_run_id FROM algorithm_runs WHERE run_id=?", (str(operation.run_id),)).fetchone()
        if run is None or run["run_type"] != "target_adjustment_risk_review":
            raise ValueError("target-adjustment Risk Run is invalid")
        if operation.resolved_source and run["parent_run_id"] != str(operation.resolved_source.decision_run_id):
            raise ValueError("target-adjustment Risk parent Run is invalid")
        for stage_id, name, sequence in ((operation.decision_stage_id, "decision", 1), (operation.risk_stage_id, "risk", 2)):
            if stage_id is None: continue
            stage = connection.execute("SELECT run_id,stage_name,sequence FROM algorithm_run_stages WHERE stage_id=?", (str(stage_id),)).fetchone()
            if stage is None or stage["run_id"] != str(operation.run_id) or stage["stage_name"] != name or int(stage["sequence"]) != sequence:
                raise ValueError(f"target-adjustment Risk {name} stage is invalid")

    @staticmethod
    def _validate_source(connection, source):
        intent = connection.execute("SELECT * FROM target_adjustment_trade_intents WHERE intent_id=?", (str(source.intent_id),)).fetchone()
        result = connection.execute("SELECT * FROM target_adjustment_decision_results WHERE decision_result_id=?", (str(source.decision_result_id),)).fetchone()
        link = connection.execute("SELECT * FROM target_adjustment_decision_source_links WHERE decision_result_id=?", (str(source.decision_result_id),)).fetchone()
        if not intent or not result or not link:
            raise ValueError("Phase 5D source evidence does not exist")
        expected_intent = {
            "decision_result_id": str(source.decision_result_id), "operation_id": str(source.decision_operation_id), "run_id": str(source.decision_run_id), "stage_id": str(source.decision_stage_id), "policy_id": source.decision_policy_id, "policy_version": source.decision_policy_version, "target_position_link_id": str(source.target_position_link_id), "target_calculation_id": str(source.target_calculation_id), "symbol": source.symbol, "as_of_utc": _iso(source.as_of_utc), "action": source.action, "current_exposure_usd_text": str(source.current_exposure_usd), "target_exposure_usd_text": str(source.target_exposure_usd), "desired_change_usd_text": str(source.desired_change_usd), "requested_notional_usd_text": str(source.requested_notional_usd), "created_at_utc": _iso(source.intent_created_at_utc), "schema_version": source.intent_schema_version,
        }
        for column, expected in expected_intent.items():
            actual = intent[column]
            if column.endswith("_text"):
                if Decimal(actual) != Decimal(expected): raise ValueError("Phase 5D intent amount was modified")
            elif actual != expected: raise ValueError("Phase 5D intent identity was modified")
        if result["status"] != "intent_created" or result["run_id"] != str(source.decision_run_id) or result["stage_id"] != str(source.decision_stage_id) or result["created_at_utc"] != _iso(source.decision_created_at_utc) or int(result["schema_version"]) != source.decision_schema_version:
            raise ValueError("Phase 5D Decision result is inconsistent")
        expected_link = {"decision_run_id": source.decision_run_id, "linked_parent_run_id": source.linked_parent_run_id, "target_child_run_id": source.target_child_run_id, "standardized_state_run_id": source.standardized_state_run_id, "target_position_link_id": source.target_position_link_id, "target_calculation_id": source.target_calculation_id, "standardized_state_calculation_id": source.standardized_state_calculation_id}
        for column, expected in expected_link.items():
            if link[column] != str(expected): raise ValueError("Phase 5D source chain was modified")
        phase5c = connection.execute("SELECT operation_id,created_at_utc,schema_version FROM target_position_standardized_state_links WHERE link_id=?", (str(source.target_position_link_id),)).fetchone()
        if not phase5c or phase5c["operation_id"] != str(source.linked_target_operation_id) or phase5c["created_at_utc"] != _iso(source.target_position_link_created_at_utc) or int(phase5c["schema_version"]) != source.target_position_link_schema_version:
            raise ValueError("Phase 5C link evidence is inconsistent")
        target = connection.execute("SELECT definition_id,definition_version,created_at_utc,schema_version FROM target_position_results WHERE calculation_id=?", (str(source.target_calculation_id),)).fetchone()
        standardized = connection.execute("SELECT definition_id,definition_version,created_at_utc,schema_version FROM standardized_state_results WHERE calculation_id=?", (str(source.standardized_state_calculation_id),)).fetchone()
        if not target or target["definition_id"] != str(source.target_definition_id) or int(target["definition_version"]) != source.target_definition_version or target["created_at_utc"] != _iso(source.target_result_created_at_utc) or int(target["schema_version"]) != source.target_result_schema_version:
            raise ValueError("Target Position definition evidence is inconsistent")
        if not standardized or standardized["definition_id"] != str(source.standardized_state_definition_id) or int(standardized["definition_version"]) != source.standardized_state_definition_version or standardized["created_at_utc"] != _iso(source.standardized_state_created_at_utc) or int(standardized["schema_version"]) != source.standardized_state_schema_version:
            raise ValueError("standardized-state definition evidence is inconsistent")

    @staticmethod
    def _insert_operation(connection, operation):
        source = operation.resolved_source
        values = (str(operation.attempt_id), str(operation.operation_id), str(operation.run_id), str(operation.decision_stage_id), str(operation.risk_stage_id) if operation.risk_stage_id else None, str(operation.requested_intent_id), operation.status.value, _iso(operation.requested_at_utc), _iso(operation.completed_at_utc), operation.session_id, operation.request_id, operation.created_by, operation.reason, json.dumps(_source_dict(source), sort_keys=True) if source else None, json.dumps(_safety_dict(operation.safety_snapshot), sort_keys=True) if operation.safety_snapshot else None, source.symbol if source else None, source.action if source else None, _iso(source.as_of_utc) if source else None, str(operation.review_result_id) if operation.review_result_id else None, operation.error_code, operation.error_summary, operation.schema_version)
        connection.execute("INSERT INTO target_adjustment_risk_operations VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", values)

    @staticmethod
    def _insert_result(connection, result):
        s = result.source
        values = (str(result.review_result_id), str(result.operation_id), str(result.run_id), str(result.stage_id), json.dumps(_source_dict(s), sort_keys=True), json.dumps(_safety_dict(result.safety_snapshot), sort_keys=True), str(result.safety_snapshot.snapshot_id), str(s.decision_result_id), str(s.intent_id), str(s.decision_run_id), s.symbol, _iso(s.as_of_utc), s.action, str(s.current_exposure_usd), str(s.target_exposure_usd), str(s.desired_change_usd), str(s.requested_notional_usd), result.status.value, json.dumps(result.reason_codes), json.dumps(result.warnings), _iso(result.created_at_utc), result.created_by, result.reason, result.software_version, None, None, result.gate_id, result.gate_version, result.schema_version)
        connection.execute("INSERT INTO target_adjustment_risk_review_results VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", values)

    @staticmethod
    def _insert_rule(connection, rule):
        connection.execute("INSERT INTO target_adjustment_risk_rule_results VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (str(rule.rule_result_id), str(rule.review_result_id), str(rule.run_id), str(rule.stage_id), rule.rule_id, rule.rule_version, rule.rule_name, rule.evaluation_order, rule.status.value, rule.input_summary, rule.expected_condition, json.dumps(rule.reason_codes), rule.severity.value, int(rule.stop_processing), _iso(rule.evaluated_at_utc), rule.schema_version))

    @staticmethod
    def _insert_link(connection, link):
        connection.execute("INSERT INTO target_adjustment_risk_source_links VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (str(link.source_link_id), str(link.operation_id), str(link.review_result_id), str(link.risk_run_id), str(link.risk_stage_id), str(link.decision_result_id), str(link.intent_id), str(link.decision_run_id), str(link.linked_parent_run_id), str(link.target_child_run_id), str(link.standardized_state_run_id), str(link.target_position_link_id), str(link.target_calculation_id), str(link.standardized_state_calculation_id), _iso(link.created_at_utc), link.schema_version))

    @staticmethod
    def _operation(row):
        source = _source_from(json.loads(row["resolved_source_json"])) if row["resolved_source_json"] else None
        safety = _safety_from(json.loads(row["safety_snapshot_json"])) if row["safety_snapshot_json"] else None
        return TargetAdjustmentRiskOperationAttempt(UUID(row["attempt_id"]), UUID(row["operation_id"]), UUID(row["run_id"]), UUID(row["decision_stage_id"]), UUID(row["risk_stage_id"]) if row["risk_stage_id"] else None, UUID(row["requested_intent_id"]), TargetAdjustmentRiskStatus(row["status"]), _dt(row["requested_at_utc"]), _dt(row["completed_at_utc"]), row["session_id"], row["request_id"], row["created_by"], row["reason"], source, safety, UUID(row["review_result_id"]) if row["review_result_id"] else None, row["error_code"], row["error_summary"], int(row["schema_version"]))

    @staticmethod
    def _result(connection, row):
        rules = connection.execute("SELECT * FROM target_adjustment_risk_rule_results WHERE review_result_id=? ORDER BY evaluation_order", (row["review_result_id"],)).fetchall()
        parsed = tuple(TargetAdjustmentStructuralRuleResult(UUID(x["rule_result_id"]), UUID(x["review_result_id"]), UUID(x["run_id"]), UUID(x["stage_id"]), x["rule_id"], x["rule_version"], x["rule_name"], int(x["evaluation_order"]), StructuralRuleStatus(x["status"]), x["input_summary"], x["expected_condition"], tuple(json.loads(x["reason_codes_json"])), StructuralRuleSeverity(x["severity"]), bool(x["stop_processing"]), _dt(x["evaluated_at_utc"]), int(x["schema_version"])) for x in rules)
        return TargetAdjustmentRiskReviewResult(UUID(row["review_result_id"]), UUID(row["operation_id"]), UUID(row["run_id"]), UUID(row["stage_id"]), _source_from(json.loads(row["source_json"])), _safety_from(json.loads(row["safety_snapshot_json"])), TargetAdjustmentRiskStatus(row["status"]), parsed, tuple(json.loads(row["reason_codes_json"])), tuple(json.loads(row["warnings_json"])), _dt(row["created_at_utc"]), row["created_by"], row["reason"], row["software_version"], gate_id=row["gate_id"], gate_version=row["gate_version"], schema_version=int(row["schema_version"]))

    @staticmethod
    def _link(row):
        return TargetAdjustmentRiskSourceLink(UUID(row["source_link_id"]), UUID(row["operation_id"]), UUID(row["review_result_id"]), UUID(row["risk_run_id"]), UUID(row["risk_stage_id"]), UUID(row["decision_result_id"]), UUID(row["intent_id"]), UUID(row["decision_run_id"]), UUID(row["linked_parent_run_id"]), UUID(row["target_child_run_id"]), UUID(row["standardized_state_run_id"]), UUID(row["target_position_link_id"]), UUID(row["target_calculation_id"]), UUID(row["standardized_state_calculation_id"]), _dt(row["created_at_utc"]), int(row["schema_version"]))


__all__ = ["SQLiteTargetAdjustmentRiskStore"]
