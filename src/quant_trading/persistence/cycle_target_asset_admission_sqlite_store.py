"""SQLite adapter for exact P33-to-P35 frozen-asset admission evidence."""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
from pathlib import Path

from quant_trading.risk.asset_admission_models import (
    AssetTradingControlEvidence,
    CycleTargetAssetAdmissionOperationAttempt,
    CycleTargetAssetAdmissionQuery,
    CycleTargetAssetAdmissionReviewResult,
    CycleTargetAssetAdmissionRuleResult,
    CycleTargetAssetAdmissionSource,
    CycleTargetAssetAdmissionSourceLink,
    CycleTargetAssetAdmissionStatus,
)
from quant_trading.risk.target_adjustment_models import StructuralRuleSeverity, StructuralRuleStatus

from .sqlite_database import CentralSQLiteDatabase


def _iso(value: datetime) -> str: return value.isoformat(timespec="microseconds")
def _dt(value: str) -> datetime: return datetime.fromisoformat(value)


def _source_dict(value: CycleTargetAssetAdmissionSource) -> dict[str, object]:
    return {
        "p33_result_id": str(value.p33_result_id), "p33_operation_id": str(value.p33_operation_id),
        "p33_run_id": str(value.p33_run_id), "p33_stage_id": str(value.p33_stage_id),
        "p33_status": value.p33_status, "p33_gate_id": value.p33_gate_id,
        "p33_gate_version": value.p33_gate_version, "p33_created_at_utc": _iso(value.p33_created_at_utc),
        "p33_reason_codes": list(value.p33_reason_codes),
        "p31_decision_result_id": str(value.p31_decision_result_id), "p31_intent_id": str(value.p31_intent_id),
        "p31_run_id": str(value.p31_run_id), "p29_result_id": str(value.p29_result_id),
        "p29_run_id": str(value.p29_run_id), "p28_result_id": str(value.p28_result_id),
        "p28_run_id": str(value.p28_run_id), "p28_step_id": str(value.p28_step_id),
        "symbol": value.symbol, "source_session": value.source_session.isoformat(),
        "action": value.action, "requested_notional_usd": str(value.requested_notional_usd),
        "execution_allowed": value.execution_allowed, "live_allowed": value.live_allowed,
        "schema_version": value.schema_version,
    }


def _source_from(data: dict[str, object]) -> CycleTargetAssetAdmissionSource:
    return CycleTargetAssetAdmissionSource(
        UUID(str(data["p33_result_id"])), UUID(str(data["p33_operation_id"])),
        UUID(str(data["p33_run_id"])), UUID(str(data["p33_stage_id"])),
        str(data["p33_status"]), str(data["p33_gate_id"]), str(data["p33_gate_version"]),
        _dt(str(data["p33_created_at_utc"])), tuple(str(item) for item in data["p33_reason_codes"]),
        UUID(str(data["p31_decision_result_id"])), UUID(str(data["p31_intent_id"])),
        UUID(str(data["p31_run_id"])), UUID(str(data["p29_result_id"])), UUID(str(data["p29_run_id"])),
        UUID(str(data["p28_result_id"])), UUID(str(data["p28_run_id"])), UUID(str(data["p28_step_id"])),
        str(data["symbol"]), date.fromisoformat(str(data["source_session"])), str(data["action"]),
        Decimal(str(data["requested_notional_usd"])), bool(data.get("execution_allowed", False)),
        bool(data.get("live_allowed", False)), int(data.get("schema_version", 1)),
    )


def _control_dict(value: AssetTradingControlEvidence) -> dict[str, object]:
    return {
        "event_id": str(value.event_id), "operation_id": str(value.operation_id),
        "run_id": str(value.run_id), "stage_id": str(value.stage_id),
        "predecessor_event_id": str(value.predecessor_event_id) if value.predecessor_event_id else None,
        "symbol": value.symbol, "status": value.status,
        "requested_at_utc": _iso(value.requested_at_utc), "effective_at_utc": _iso(value.effective_at_utc),
        "effective_session": value.effective_session.isoformat(), "component_id": value.component_id,
        "component_version": value.component_version, "mapping_id": str(value.mapping_id),
        "mapping_version": value.mapping_version, "calendar_definition_id": value.calendar_definition_id,
        "calendar_snapshot_id": str(value.calendar_snapshot_id), "schedule_fingerprint": value.schedule_fingerprint,
        "execution_allowed": value.execution_allowed, "live_allowed": value.live_allowed,
        "schema_version": value.schema_version,
    }


def _control_from(data: dict[str, object]) -> AssetTradingControlEvidence:
    predecessor = data.get("predecessor_event_id")
    return AssetTradingControlEvidence(
        UUID(str(data["event_id"])), UUID(str(data["operation_id"])), UUID(str(data["run_id"])),
        UUID(str(data["stage_id"])), UUID(str(predecessor)) if predecessor else None,
        str(data["symbol"]), str(data["status"]), _dt(str(data["requested_at_utc"])),
        _dt(str(data["effective_at_utc"])), date.fromisoformat(str(data["effective_session"])),
        str(data["component_id"]), str(data["component_version"]), UUID(str(data["mapping_id"])),
        int(data["mapping_version"]), str(data["calendar_definition_id"]),
        UUID(str(data["calendar_snapshot_id"])), str(data["schedule_fingerprint"]),
        bool(data.get("execution_allowed", False)), bool(data.get("live_allowed", False)),
        int(data.get("schema_version", 1)),
    )


class SQLiteCycleTargetAssetAdmissionStore:
    def __init__(self, database: CentralSQLiteDatabase | Path | str) -> None:
        self._database = database if isinstance(database, CentralSQLiteDatabase) else CentralSQLiteDatabase(database)
    def initialize(self) -> None: self._database.initialize()

    def get_first_operation(self, operation_id: UUID):
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                "SELECT * FROM cycle_target_asset_admission_operations WHERE operation_id=? ORDER BY completed_at_utc,attempt_id LIMIT 1",
                (str(operation_id),),
            ).fetchone()
            return self._operation(row) if row else None

    def save_operation(self, operation: CycleTargetAssetAdmissionOperationAttempt) -> None:
        if operation.status.accepted:
            raise ValueError("completed P35 operation must be stored with result")
        with closing(self._database.connect()) as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                self._validate_run(connection, operation)
                self._insert_operation(connection, operation)
                connection.commit()
            except Exception as exc:
                connection.rollback(); raise sqlite3.DatabaseError(f"could not save failed P35 operation: {exc}") from exc

    def save_completed(self, result, operation, source_link) -> None:
        self._validate_models(result, operation, source_link)
        with closing(self._database.connect()) as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                self._validate_run(connection, operation)
                self._validate_sources(connection, result)
                self._insert_operation(connection, operation)
                self._insert_result(connection, result)
                for rule in result.rules: self._insert_rule(connection, rule)
                self._insert_link(connection, source_link)
                connection.commit()
            except Exception as exc:
                connection.rollback(); raise sqlite3.DatabaseError(f"could not save completed P35 review: {exc}") from exc

    def list_cycle_target_asset_admission_operations(self, query=CycleTargetAssetAdmissionQuery()):
        clauses, params = self._clauses(query, operations=True)
        where = "WHERE " + " AND ".join(clauses) if clauses else ""
        params.append(query.limit)
        with closing(self._database.connect()) as connection:
            rows = connection.execute(f"SELECT * FROM cycle_target_asset_admission_operations {where} ORDER BY requested_at_utc DESC,attempt_id DESC LIMIT ?", params).fetchall()
            return tuple(self._operation(row) for row in rows)

    def list_cycle_target_asset_admission_results(self, query=CycleTargetAssetAdmissionQuery()):
        clauses, params = self._clauses(query, operations=False)
        where = "WHERE " + " AND ".join(clauses) if clauses else ""
        params.append(query.limit)
        with closing(self._database.connect()) as connection:
            rows = connection.execute(f"SELECT * FROM cycle_target_asset_admission_results {where} ORDER BY created_at_utc DESC,result_id DESC LIMIT ?", params).fetchall()
            return tuple(self._result(connection, row) for row in rows)

    def get_cycle_target_asset_admission_result(self, result_id: UUID):
        with closing(self._database.connect()) as connection:
            row = connection.execute("SELECT * FROM cycle_target_asset_admission_results WHERE result_id=?", (str(result_id),)).fetchone()
            return self._result(connection, row) if row else None

    def get_cycle_target_asset_admission_source_link(self, result_id: UUID):
        with closing(self._database.connect()) as connection:
            row = connection.execute("SELECT * FROM cycle_target_asset_admission_source_links WHERE result_id=?", (str(result_id),)).fetchone()
            return self._link(row) if row else None

    @staticmethod
    def _clauses(query, *, operations):
        clauses, params = [], []
        mapping = (
            (("resolved_symbol" if operations else "symbol"), query.symbol),
            ("status", query.status.value if query.status else None),
            (("requested_p33_result_id" if operations else "p33_result_id"), str(query.p33_result_id) if query.p33_result_id else None),
            (("requested_p33_run_id" if operations else "p33_run_id"), str(query.p33_run_id) if query.p33_run_id else None),
        )
        for column, value in mapping:
            if value is not None: clauses.append(f"{column}=?"); params.append(value)
        if not operations and query.control_event_id:
            clauses.append("control_event_id=?"); params.append(str(query.control_event_id))
        created = "requested_at_utc" if operations else "created_at_utc"
        if query.created_from_utc: clauses.append(f"{created}>=?"); params.append(_iso(query.created_from_utc))
        if query.created_to_utc: clauses.append(f"{created}<?"); params.append(_iso(query.created_to_utc))
        return clauses, params

    @staticmethod
    def _validate_models(result, operation, link):
        if operation.status is not result.status or operation.result_id != result.result_id:
            raise ValueError("P35 operation/result status or identity is inconsistent")
        if (operation.operation_id, operation.run_id, operation.risk_stage_id) != (result.operation_id, result.run_id, result.stage_id):
            raise ValueError("P35 operation/result Run identity is inconsistent")
        source, control = result.source, result.control
        if (link.operation_id, link.result_id, link.admission_run_id, link.admission_stage_id, link.p33_result_id) != (
            result.operation_id, result.result_id, result.run_id, result.stage_id, source.p33_result_id
        ):
            raise ValueError("P35 source-link identity is inconsistent")
        if link.control_event_id != (control.event_id if control else None):
            raise ValueError("P35 source-link control identity is inconsistent")

    @staticmethod
    def _validate_run(connection, operation):
        run = connection.execute("SELECT run_type,parent_run_id FROM algorithm_runs WHERE run_id=?", (str(operation.run_id),)).fetchone()
        expected_parent = str(operation.requested_p33_run_id) if operation.status.accepted else None
        if run is None or run["run_type"] != "cycle_target_asset_admission_review" or run["parent_run_id"] != expected_parent:
            raise ValueError("P35 Run/parent is invalid")
        for stage_id, name, sequence in ((operation.state_stage_id, "state", 1), (operation.risk_stage_id, "risk", 2)):
            if stage_id is None: continue
            stage = connection.execute("SELECT run_id,stage_name,sequence FROM algorithm_run_stages WHERE stage_id=?", (str(stage_id),)).fetchone()
            if stage is None or stage["run_id"] != str(operation.run_id) or stage["stage_name"] != name or int(stage["sequence"]) != sequence:
                raise ValueError(f"P35 {name} stage is invalid")

    @staticmethod
    def _validate_sources(connection, result):
        source = result.source
        row = connection.execute("SELECT * FROM cycle_target_risk_review_results WHERE review_result_id=?", (str(source.p33_result_id),)).fetchone()
        if row is None:
            raise ValueError("exact P33 result does not exist")
        expected = {
            "operation_id": str(source.p33_operation_id), "run_id": str(source.p33_run_id),
            "stage_id": str(source.p33_stage_id), "status": source.p33_status,
            "gate_id": source.p33_gate_id, "gate_version": source.p33_gate_version,
            "created_at_utc": _iso(source.p33_created_at_utc), "decision_result_id": str(source.p31_decision_result_id),
            "intent_id": str(source.p31_intent_id), "decision_run_id": str(source.p31_run_id),
            "source_result_id": str(source.p29_result_id), "source_run_id": str(source.p29_run_id),
            "source_reversal_result_id": str(source.p28_result_id), "source_reversal_run_id": str(source.p28_run_id),
            "source_reversal_step_id": str(source.p28_step_id), "symbol": source.symbol,
            "source_session": source.source_session.isoformat(), "action": source.action,
            "requested_notional_usd_text": str(source.requested_notional_usd),
            "execution_allowed": 0, "live_allowed": 0, "schema_version": 1,
        }
        for column, value in expected.items():
            actual = row[column]
            if column.endswith("_text"):
                if Decimal(actual) != Decimal(value): raise ValueError("P33 requested amount was modified")
            elif column.endswith("_utc"):
                if _dt(actual) != _dt(value): raise ValueError(f"P33 timestamp was modified: {column}")
            elif actual != value: raise ValueError(f"P33 identity was modified: {column}")
        control = result.control
        effective = connection.execute(
            "SELECT * FROM asset_trading_control_events WHERE symbol=? AND effective_at_utc<=? ORDER BY effective_at_utc DESC,rowid DESC LIMIT 1",
            (source.symbol, _iso(result.created_at_utc)),
        ).fetchone()
        if control is None:
            if effective is not None: raise ValueError("P35 missing-control claim is stale")
            return
        if effective is None or effective["event_id"] != str(control.event_id):
            raise ValueError("P35 did not bind the exact effective control event")
        control_expected = {
            "operation_id": str(control.operation_id), "run_id": str(control.run_id), "stage_id": str(control.stage_id),
            "predecessor_event_id": str(control.predecessor_event_id) if control.predecessor_event_id else None,
            "symbol": control.symbol, "new_status": control.status, "requested_at_utc": _iso(control.requested_at_utc),
            "effective_at_utc": _iso(control.effective_at_utc), "effective_session": control.effective_session.isoformat(),
            "component_id": control.component_id, "component_version": control.component_version,
            "mapping_id": str(control.mapping_id), "mapping_version": control.mapping_version,
            "calendar_definition_id": control.calendar_definition_id, "calendar_snapshot_id": str(control.calendar_snapshot_id),
            "schedule_fingerprint": control.schedule_fingerprint, "execution_allowed": 0, "live_allowed": 0, "schema_version": 1,
        }
        for column, value in control_expected.items():
            actual = effective[column]
            if column.endswith("_utc"):
                if _dt(actual) != _dt(value): raise ValueError(f"control timestamp was modified: {column}")
            elif actual != value: raise ValueError(f"control identity was modified: {column}")

    @staticmethod
    def _insert_operation(connection, value):
        connection.execute("INSERT INTO cycle_target_asset_admission_operations VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
            str(value.attempt_id), str(value.operation_id), str(value.run_id), str(value.state_stage_id),
            str(value.risk_stage_id) if value.risk_stage_id else None, value.command_fingerprint,
            str(value.requested_p33_result_id), str(value.requested_p33_run_id), value.status.value,
            _iso(value.requested_at_utc), _iso(value.completed_at_utc), value.session_id, value.request_id,
            value.created_by, value.reason, value.resolved_symbol, str(value.result_id) if value.result_id else None,
            value.error_code, value.error_summary, int(value.execution_allowed), int(value.live_allowed), value.schema_version,
        ))

    @staticmethod
    def _insert_result(connection, value):
        source, control = value.source, value.control
        connection.execute("INSERT INTO cycle_target_asset_admission_results VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
            str(value.result_id), str(value.operation_id), str(value.run_id), str(value.stage_id),
            json.dumps(_source_dict(source), sort_keys=True, separators=(",", ":")),
            json.dumps(_control_dict(control), sort_keys=True, separators=(",", ":")) if control else None,
            str(source.p33_result_id), str(source.p33_run_id), str(control.event_id) if control else None,
            str(control.run_id) if control else None, source.symbol, source.action, str(source.requested_notional_usd),
            value.status.value, json.dumps(value.reason_codes), json.dumps(value.warnings), _iso(value.created_at_utc),
            value.created_by, value.reason, value.software_version, None, None, int(value.execution_allowed),
            int(value.live_allowed), value.gate_id, value.gate_version, value.schema_version,
        ))

    @staticmethod
    def _insert_rule(connection, value):
        connection.execute("INSERT INTO cycle_target_asset_admission_rules VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
            str(value.rule_result_id), str(value.result_id), str(value.run_id), str(value.stage_id), value.rule_id,
            value.rule_version, value.rule_name, value.evaluation_order, value.status.value, value.input_summary,
            value.expected_condition, json.dumps(value.reason_codes), value.severity.value, int(value.stop_processing),
            _iso(value.evaluated_at_utc), value.schema_version,
        ))

    @staticmethod
    def _insert_link(connection, value):
        connection.execute("INSERT INTO cycle_target_asset_admission_source_links VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
            str(value.source_link_id), str(value.operation_id), str(value.result_id), str(value.admission_run_id),
            str(value.admission_stage_id), str(value.p33_result_id), str(value.p33_run_id),
            str(value.p31_decision_result_id), str(value.p31_intent_id), str(value.p29_result_id),
            str(value.p28_result_id), str(value.control_event_id) if value.control_event_id else None,
            str(value.control_run_id) if value.control_run_id else None, _iso(value.created_at_utc), value.schema_version,
        ))

    @staticmethod
    def _operation(row):
        return CycleTargetAssetAdmissionOperationAttempt(
            UUID(row["attempt_id"]), UUID(row["operation_id"]), UUID(row["run_id"]), UUID(row["state_stage_id"]),
            UUID(row["risk_stage_id"]) if row["risk_stage_id"] else None, row["command_fingerprint"],
            UUID(row["requested_p33_result_id"]), UUID(row["requested_p33_run_id"]),
            CycleTargetAssetAdmissionStatus(row["status"]), _dt(row["requested_at_utc"]), _dt(row["completed_at_utc"]),
            row["session_id"], row["request_id"], row["created_by"], row["reason"], row["resolved_symbol"],
            UUID(row["result_id"]) if row["result_id"] else None, row["error_code"], row["error_summary"],
            bool(row["execution_allowed"]), bool(row["live_allowed"]), int(row["schema_version"]),
        )

    @staticmethod
    def _result(connection, row):
        rules = connection.execute("SELECT * FROM cycle_target_asset_admission_rules WHERE result_id=? ORDER BY evaluation_order", (row["result_id"],)).fetchall()
        return CycleTargetAssetAdmissionReviewResult(
            UUID(row["result_id"]), UUID(row["operation_id"]), UUID(row["run_id"]), UUID(row["stage_id"]),
            _source_from(json.loads(row["source_json"])), _control_from(json.loads(row["control_evidence_json"])) if row["control_evidence_json"] else None,
            CycleTargetAssetAdmissionStatus(row["status"]), tuple(SQLiteCycleTargetAssetAdmissionStore._rule(item) for item in rules),
            tuple(json.loads(row["reason_codes_json"])), tuple(json.loads(row["warnings_json"])), _dt(row["created_at_utc"]),
            row["created_by"], row["reason"], row["software_version"], None, None,
            bool(row["execution_allowed"]), bool(row["live_allowed"]), row["gate_id"], row["gate_version"], int(row["schema_version"]),
        )

    @staticmethod
    def _rule(row):
        return CycleTargetAssetAdmissionRuleResult(
            UUID(row["rule_result_id"]), UUID(row["result_id"]), UUID(row["run_id"]), UUID(row["stage_id"]),
            row["rule_id"], row["rule_version"], row["rule_name"], int(row["evaluation_order"]),
            StructuralRuleStatus(row["status"]), row["input_summary"], row["expected_condition"],
            tuple(json.loads(row["reason_codes_json"])), StructuralRuleSeverity(row["severity"]),
            bool(row["stop_processing"]), _dt(row["evaluated_at_utc"]), int(row["schema_version"]),
        )

    @staticmethod
    def _link(row):
        return CycleTargetAssetAdmissionSourceLink(
            UUID(row["source_link_id"]), UUID(row["operation_id"]), UUID(row["result_id"]), UUID(row["admission_run_id"]),
            UUID(row["admission_stage_id"]), UUID(row["p33_result_id"]), UUID(row["p33_run_id"]),
            UUID(row["p31_decision_result_id"]), UUID(row["p31_intent_id"]), UUID(row["p29_result_id"]),
            UUID(row["p28_result_id"]), UUID(row["control_event_id"]) if row["control_event_id"] else None,
            UUID(row["control_run_id"]) if row["control_run_id"] else None, _dt(row["created_at_utc"]), int(row["schema_version"]),
        )


__all__ = ["SQLiteCycleTargetAssetAdmissionStore"]
