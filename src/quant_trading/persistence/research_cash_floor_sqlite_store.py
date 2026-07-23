"""SQLite adapter for immutable research asset cash-floor Risk evidence."""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from uuid import UUID

from quant_trading.risk import (
    ExposureCapDisposition,
    ExposureCapRuleOutcome,
    ExposureCapRuleResult,
    ExposureCapSourceLink,
    LinkedResearchCashFloorPreviewInput,
    ResearchAssetCashFloorDefinitionVersion,
    ResearchCashFloorDefinitionQuery,
    ResearchCashFloorDefinitionStatus,
    ResearchCashFloorDisposition,
    ResearchCashFloorOperationAttempt,
    ResearchCashFloorOperationQuery,
    ResearchCashFloorOperationStatus,
    ResearchCashFloorOperationType,
    ResearchCashFloorResultQuery,
    ResearchCashFloorRuleOutcome,
    ResearchCashFloorRuleResult,
    ResearchCashFloorSourceLink,
    TargetAdjustmentExposureCapPreviewResult,
    TargetAdjustmentResearchCashFloorPreviewResult,
)

from .exposure_cap_sqlite_store import (
    SQLiteExposureCapStore,
    _linked_dict as _cap_source_dict,
    _linked_from as _cap_source_from,
)
from .sqlite_database import CentralSQLiteDatabase
from .target_adjustment_risk_sqlite_store import _safety_dict, _safety_from
from .target_position_sqlite_store import SQLiteTargetPositionStore


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="microseconds")


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(UTC)


def _definition_dict(
    definition: ResearchAssetCashFloorDefinitionVersion,
) -> dict[str, object]:
    return {
        "definition_id": str(definition.definition_id),
        "definition_version": definition.definition_version,
        "predecessor_version": definition.predecessor_version,
        "symbol": definition.symbol,
        "minimum_research_asset_cash_usd": str(
            definition.minimum_research_asset_cash_usd
        ),
        "status": definition.status.value,
        "reason": definition.reason,
        "created_by": definition.created_by,
        "created_at_utc": _iso(definition.created_at_utc),
        "software_version": definition.software_version,
        "currency": definition.currency,
        "schema_version": definition.schema_version,
    }


def _definition_from(
    data: dict[str, object],
) -> ResearchAssetCashFloorDefinitionVersion:
    return ResearchAssetCashFloorDefinitionVersion(
        UUID(str(data["definition_id"])),
        int(data["definition_version"]),
        int(data["predecessor_version"])
        if data["predecessor_version"] is not None
        else None,
        str(data["symbol"]),
        Decimal(str(data["minimum_research_asset_cash_usd"])),
        ResearchCashFloorDefinitionStatus(str(data["status"])),
        str(data["reason"]),
        str(data["created_by"]),
        _dt(str(data["created_at_utc"])),
        str(data["software_version"]),
        str(data["currency"]),
        int(data["schema_version"]),
    )


def _phase6b_result_dict(
    result: TargetAdjustmentExposureCapPreviewResult,
) -> dict[str, object]:
    rule = result.rule
    return {
        "preview_result_id": str(result.preview_result_id),
        "operation_id": str(result.operation_id),
        "run_id": str(result.run_id),
        "stage_id": str(result.stage_id),
        "source": _cap_source_dict(result.source),
        "rule": {
            "rule_result_id": str(rule.rule_result_id),
            "preview_result_id": str(rule.preview_result_id),
            "run_id": str(rule.run_id),
            "stage_id": str(rule.stage_id),
            "action": rule.action,
            "current_exposure_usd": str(rule.current_exposure_usd),
            "target_exposure_usd": str(rule.target_exposure_usd),
            "original_requested_notional_usd": str(
                rule.original_requested_notional_usd
            ),
            "max_target_exposure_usd": str(rule.max_target_exposure_usd),
            "cap_constrained_candidate_notional_usd": str(
                rule.cap_constrained_candidate_notional_usd
            ),
            "reduction_usd": str(rule.reduction_usd),
            "outcome": rule.outcome.value,
            "reason_codes": list(rule.reason_codes),
            "evaluated_at_utc": _iso(rule.evaluated_at_utc),
            "stop_processing": rule.stop_processing,
            "rule_id": rule.rule_id,
            "rule_version": rule.rule_version,
            "evaluation_order": rule.evaluation_order,
            "schema_version": rule.schema_version,
        },
        "disposition": result.disposition.value,
        "reason_codes": list(result.reason_codes),
        "warnings": list(result.warnings),
        "created_at_utc": _iso(result.created_at_utc),
        "created_by": result.created_by,
        "reason": result.reason,
        "software_version": result.software_version,
        "component_id": result.component_id,
        "component_version": result.component_version,
        "schema_version": result.schema_version,
    }


def _phase6b_result_from(
    data: dict[str, object],
) -> TargetAdjustmentExposureCapPreviewResult:
    rule_data = dict(data["rule"])
    rule = ExposureCapRuleResult(
        UUID(str(rule_data["rule_result_id"])),
        UUID(str(rule_data["preview_result_id"])),
        UUID(str(rule_data["run_id"])),
        UUID(str(rule_data["stage_id"])),
        str(rule_data["action"]),
        Decimal(str(rule_data["current_exposure_usd"])),
        Decimal(str(rule_data["target_exposure_usd"])),
        Decimal(str(rule_data["original_requested_notional_usd"])),
        Decimal(str(rule_data["max_target_exposure_usd"])),
        Decimal(str(rule_data["cap_constrained_candidate_notional_usd"])),
        Decimal(str(rule_data["reduction_usd"])),
        ExposureCapRuleOutcome(str(rule_data["outcome"])),
        tuple(str(value) for value in rule_data["reason_codes"]),
        _dt(str(rule_data["evaluated_at_utc"])),
        bool(rule_data["stop_processing"]),
        str(rule_data["rule_id"]),
        str(rule_data["rule_version"]),
        int(rule_data["evaluation_order"]),
        int(rule_data["schema_version"]),
    )
    return TargetAdjustmentExposureCapPreviewResult(
        UUID(str(data["preview_result_id"])),
        UUID(str(data["operation_id"])),
        UUID(str(data["run_id"])),
        UUID(str(data["stage_id"])),
        _cap_source_from(dict(data["source"])),
        rule,
        ExposureCapDisposition(str(data["disposition"])),
        tuple(str(value) for value in data["reason_codes"]),
        tuple(str(value) for value in data["warnings"]),
        _dt(str(data["created_at_utc"])),
        str(data["created_by"]),
        str(data["reason"]),
        str(data["software_version"]),
        str(data["component_id"]),
        str(data["component_version"]),
        int(data["schema_version"]),
    )


def _cap_link_dict(link: ExposureCapSourceLink) -> dict[str, object]:
    return {
        name: str(getattr(link, name))
        for name in (
            "source_link_id",
            "operation_id",
            "preview_result_id",
            "exposure_cap_run_id",
            "exposure_cap_stage_id",
            "phase6a_review_result_id",
            "phase6a_run_id",
            "phase6a_stage_id",
            "decision_run_id",
            "linked_parent_run_id",
            "target_child_run_id",
            "standardized_state_run_id",
            "decision_result_id",
            "intent_id",
            "target_position_link_id",
            "target_calculation_id",
            "standardized_state_calculation_id",
        )
    } | {
        "created_at_utc": _iso(link.created_at_utc),
        "schema_version": link.schema_version,
    }


def _cap_link_from(data: dict[str, object]) -> ExposureCapSourceLink:
    names = (
        "source_link_id",
        "operation_id",
        "preview_result_id",
        "exposure_cap_run_id",
        "exposure_cap_stage_id",
        "phase6a_review_result_id",
        "phase6a_run_id",
        "phase6a_stage_id",
        "decision_run_id",
        "linked_parent_run_id",
        "target_child_run_id",
        "standardized_state_run_id",
        "decision_result_id",
        "intent_id",
        "target_position_link_id",
        "target_calculation_id",
        "standardized_state_calculation_id",
    )
    return ExposureCapSourceLink(
        *(UUID(str(data[name])) for name in names),
        _dt(str(data["created_at_utc"])),
        int(data["schema_version"]),
    )


def _linked_dict(source: LinkedResearchCashFloorPreviewInput) -> dict[str, object]:
    return {
        "phase6b_result": _phase6b_result_dict(source.phase6b_result),
        "phase6b_source_link": _cap_link_dict(source.phase6b_source_link),
        "research_capital_basis_usd": str(source.research_capital_basis_usd),
        "target_result_created_at_utc": _iso(source.target_result_created_at_utc),
        "target_result_schema_version": source.target_result_schema_version,
        "definition": _definition_dict(source.definition),
        "current_safety_snapshot": _safety_dict(source.current_safety_snapshot),
        "schema_version": source.schema_version,
    }


def _linked_from(data: dict[str, object]) -> LinkedResearchCashFloorPreviewInput:
    return LinkedResearchCashFloorPreviewInput(
        _phase6b_result_from(dict(data["phase6b_result"])),
        _cap_link_from(dict(data["phase6b_source_link"])),
        Decimal(str(data["research_capital_basis_usd"])),
        _dt(str(data["target_result_created_at_utc"])),
        int(data["target_result_schema_version"]),
        _definition_from(dict(data["definition"])),
        _safety_from(dict(data["current_safety_snapshot"])),
        int(data["schema_version"]),
    )


class SQLiteResearchCashFloorStore:
    def __init__(self, database_path: Path | str) -> None:
        self._database = CentralSQLiteDatabase(database_path)

    def initialize(self) -> None:
        self._database.initialize()

    def get_first_operation(self, operation_id: UUID):
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                """
                SELECT * FROM target_adjustment_cash_floor_operations
                WHERE operation_id=?
                ORDER BY CASE WHEN status IN ('completed','blocked') THEN 0 ELSE 1 END,
                         rowid LIMIT 1
                """,
                (str(operation_id),),
            ).fetchone()
            return self._operation(row) if row else None

    def get_definition(self, definition_id: UUID, definition_version: int):
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                """SELECT * FROM research_asset_cash_floor_definitions
                   WHERE definition_id=? AND definition_version=?""",
                (str(definition_id), definition_version),
            ).fetchone()
            return self._definition(row) if row else None

    def get_latest_definition(self, definition_id: UUID):
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                """SELECT * FROM research_asset_cash_floor_definitions
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
                raise sqlite3.DatabaseError(
                    "could not save research cash-floor definition operation"
                ) from exc

    def save_operation(self, operation: ResearchCashFloorOperationAttempt) -> None:
        with closing(self._database.connect()) as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                self._validate_run(connection, operation)
                self._insert_operation(connection, operation)
                connection.commit()
            except Exception as exc:
                connection.rollback()
                raise sqlite3.DatabaseError(
                    "could not save research cash-floor operation"
                ) from exc

    def save_completed(self, result, operation, source_link) -> None:
        self._validate_models(result, operation, source_link)
        with closing(self._database.connect()) as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                self._validate_run(connection, operation)
                self._validate_phase6b_and_target(connection, result.source)
                self._validate_definition_current(connection, result.source.definition)
                self._insert_operation(connection, operation)
                self._insert_result(connection, result)
                self._insert_rule(connection, result.rule)
                self._insert_link(connection, source_link)
                connection.commit()
            except Exception as exc:
                connection.rollback()
                raise sqlite3.DatabaseError(
                    "could not save completed research cash-floor preview"
                ) from exc

    def list_research_cash_floor_definitions(
        self, query=ResearchCashFloorDefinitionQuery()
    ):
        clauses, params = [], []
        if query.current_only:
            clauses.append(
                "definition_version=(SELECT MAX(current.definition_version) "
                "FROM research_asset_cash_floor_definitions current "
                "WHERE current.definition_id="
                "research_asset_cash_floor_definitions.definition_id)"
            )
        if query.symbol is not None:
            clauses.append("symbol=?")
            params.append(query.symbol)
        if query.status is not None:
            clauses.append("status=?")
            params.append(query.status.value)
        where = "WHERE " + " AND ".join(clauses) if clauses else ""
        params.append(query.limit)
        with closing(self._database.connect()) as connection:
            rows = connection.execute(
                f"""SELECT * FROM research_asset_cash_floor_definitions {where}
                    ORDER BY created_at_utc DESC,definition_id,definition_version DESC
                    LIMIT ?""",
                params,
            ).fetchall()
            return tuple(self._definition(row) for row in rows)

    def list_research_cash_floor_operations(
        self, query=ResearchCashFloorOperationQuery()
    ):
        clauses, params = [], []
        if query.operation_type is not None:
            clauses.append("operation_type=?")
            params.append(query.operation_type.value)
        if query.status is not None:
            clauses.append("status=?")
            params.append(query.status.value)
        if query.symbol is not None:
            clauses.append("COALESCE(resolved_symbol,requested_symbol)=?")
            params.append(query.symbol)
        if query.has_error is not None:
            clauses.append("error_code IS NOT NULL" if query.has_error else "error_code IS NULL")
        where = "WHERE " + " AND ".join(clauses) if clauses else ""
        params.append(query.limit)
        with closing(self._database.connect()) as connection:
            rows = connection.execute(
                f"""SELECT * FROM target_adjustment_cash_floor_operations {where}
                    ORDER BY requested_at_utc DESC,attempt_id DESC LIMIT ?""",
                params,
            ).fetchall()
            return tuple(self._operation(row) for row in rows)

    def list_research_cash_floor_results(
        self, query=ResearchCashFloorResultQuery()
    ):
        clauses, params = [], []
        mapping = (
            ("r.symbol", query.symbol),
            ("r.action", query.action),
            ("r.definition_id", str(query.definition_id) if query.definition_id else None),
            ("r.definition_version", query.definition_version),
            ("r.disposition", query.disposition.value if query.disposition else None),
            ("cap.outcome", query.phase6b_rule_outcome.value if query.phase6b_rule_outcome else None),
            ("rr.outcome", query.rule_outcome.value if query.rule_outcome else None),
        )
        for column, value in mapping:
            if value is not None:
                clauses.append(f"{column}=?")
                params.append(value)
        if query.as_of_from_utc is not None:
            clauses.append("r.as_of_utc>=?")
            params.append(_iso(query.as_of_from_utc))
        if query.as_of_to_utc is not None:
            clauses.append("r.as_of_utc<?")
            params.append(_iso(query.as_of_to_utc))
        if query.has_warnings is not None:
            clauses.append("r.warnings_json <> '[]'" if query.has_warnings else "r.warnings_json = '[]'")
        where = "WHERE " + " AND ".join(clauses) if clauses else ""
        params.append(query.limit)
        with closing(self._database.connect()) as connection:
            rows = connection.execute(
                f"""SELECT r.* FROM target_adjustment_cash_floor_results r
                    JOIN target_adjustment_cash_floor_rule_results rr
                      ON rr.preview_result_id=r.preview_result_id
                    JOIN target_adjustment_exposure_cap_rule_results cap
                      ON cap.preview_result_id=r.phase6b_preview_result_id
                    {where} ORDER BY r.as_of_utc DESC,r.preview_result_id DESC
                    LIMIT ?""",
                params,
            ).fetchall()
            return tuple(self._result(connection, row) for row in rows)

    def get_research_cash_floor_result(self, preview_result_id: UUID):
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                "SELECT * FROM target_adjustment_cash_floor_results "
                "WHERE preview_result_id=?",
                (str(preview_result_id),),
            ).fetchone()
            return self._result(connection, row) if row else None

    def get_research_cash_floor_source_link(self, preview_result_id: UUID):
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                "SELECT * FROM target_adjustment_cash_floor_source_links "
                "WHERE preview_result_id=?",
                (str(preview_result_id),),
            ).fetchone()
            return self._link(row) if row else None

    @staticmethod
    def _validate_models(result, operation, link):
        if operation.status is not ResearchCashFloorOperationStatus.COMPLETED:
            raise ValueError("accepted cash-floor result requires a completed operation")
        if (
            operation.operation_id != result.operation_id
            or operation.run_id != result.run_id
            or operation.stage_id != result.stage_id
            or operation.preview_result_id != result.preview_result_id
            or operation.disposition is not result.disposition
            or operation.resolved_source != result.source
        ):
            raise ValueError("cash-floor operation/result evidence is inconsistent")
        source = result.source
        cap_link = source.phase6b_source_link
        expected = (
            result.operation_id,
            result.preview_result_id,
            result.run_id,
            result.stage_id,
            source.phase6b_result.preview_result_id,
            source.phase6b_result.run_id,
            source.phase6b_result.stage_id,
            cap_link.phase6a_review_result_id,
            cap_link.phase6a_run_id,
            cap_link.phase6a_stage_id,
            cap_link.target_calculation_id,
        )
        actual = (
            link.operation_id,
            link.preview_result_id,
            link.cash_floor_run_id,
            link.cash_floor_stage_id,
            link.phase6b_preview_result_id,
            link.phase6b_run_id,
            link.phase6b_stage_id,
            link.phase6a_review_result_id,
            link.phase6a_run_id,
            link.phase6a_stage_id,
            link.target_calculation_id,
        )
        if actual != expected:
            raise ValueError("cash-floor source-link identity is inconsistent")

    @staticmethod
    def _validate_run(connection, operation):
        run = connection.execute(
            "SELECT run_type,parent_run_id FROM algorithm_runs WHERE run_id=?",
            (str(operation.run_id),),
        ).fetchone()
        if (
            run is None
            or run["run_type"]
            != "target_adjustment_research_cash_floor_preview"
        ):
            raise ValueError("research cash-floor Run is invalid")
        stage = connection.execute(
            "SELECT run_id,stage_name,sequence FROM algorithm_run_stages "
            "WHERE stage_id=?",
            (str(operation.stage_id),),
        ).fetchone()
        if (
            stage is None
            or stage["run_id"] != str(operation.run_id)
            or stage["stage_name"] != "risk"
            or int(stage["sequence"]) != 1
        ):
            raise ValueError("research cash-floor Risk stage is invalid")
        if (
            operation.resolved_source is not None
            and run["parent_run_id"]
            != str(operation.resolved_source.phase6b_result.run_id)
        ):
            raise ValueError("cash-floor parent Phase 6B Run is invalid")
        if (
            operation.operation_type is not ResearchCashFloorOperationType.PREVIEW
            and run["parent_run_id"] is not None
        ):
            raise ValueError("cash-floor definition Run cannot have a parent")

    @staticmethod
    def _validate_definition_append(connection, definition, operation):
        latest = connection.execute(
            """SELECT * FROM research_asset_cash_floor_definitions
               WHERE definition_id=? ORDER BY definition_version DESC LIMIT 1""",
            (str(definition.definition_id),),
        ).fetchone()
        if definition.definition_version == 1:
            if latest is not None or definition.predecessor_version is not None:
                raise ValueError("new cash-floor definition chain is invalid")
        else:
            if (
                latest is None
                or int(latest["definition_version"]) != definition.predecessor_version
            ):
                raise ValueError("cash-floor predecessor version is invalid")
            if latest["status"] == "archived":
                raise ValueError("archived cash-floor definition cannot be extended")
            if latest["symbol"] != definition.symbol:
                raise ValueError("cash-floor symbol changed across versions")
        if (
            operation.resolved_definition_id != definition.definition_id
            or operation.resolved_definition_version != definition.definition_version
        ):
            raise ValueError("definition operation/result identity is inconsistent")

    @staticmethod
    def _validate_definition_current(connection, definition):
        row = connection.execute(
            """SELECT * FROM research_asset_cash_floor_definitions
               WHERE definition_id=? AND definition_version=?""",
            (str(definition.definition_id), definition.definition_version),
        ).fetchone()
        latest = connection.execute(
            """SELECT definition_version,status
               FROM research_asset_cash_floor_definitions
               WHERE definition_id=? ORDER BY definition_version DESC LIMIT 1""",
            (str(definition.definition_id),),
        ).fetchone()
        if row is None or SQLiteResearchCashFloorStore._definition(row) != definition:
            raise ValueError("research cash-floor definition evidence was modified")
        if (
            latest is None
            or int(latest["definition_version"]) != definition.definition_version
            or latest["status"] != "saved"
        ):
            raise ValueError("research cash-floor definition is superseded or archived")

    @staticmethod
    def _validate_phase6b_and_target(connection, linked):
        phase6b_row = connection.execute(
            "SELECT * FROM target_adjustment_exposure_cap_results "
            "WHERE preview_result_id=?",
            (str(linked.phase6b_result.preview_result_id),),
        ).fetchone()
        if (
            phase6b_row is None
            or SQLiteExposureCapStore._result(connection, phase6b_row)
            != linked.phase6b_result
        ):
            raise ValueError("Phase 6B result/rule evidence was modified")
        cap_link_row = connection.execute(
            "SELECT * FROM target_adjustment_exposure_cap_source_links "
            "WHERE preview_result_id=?",
            (str(linked.phase6b_result.preview_result_id),),
        ).fetchone()
        if (
            cap_link_row is None
            or SQLiteExposureCapStore._link(cap_link_row)
            != linked.phase6b_source_link
        ):
            raise ValueError("Phase 6B source-link evidence was modified")
        target_row = connection.execute(
            "SELECT * FROM target_position_results WHERE calculation_id=?",
            (str(linked.phase6b_source_link.target_calculation_id),),
        ).fetchone()
        if target_row is None:
            raise ValueError("Target Position source evidence does not exist")
        target = SQLiteTargetPositionStore._result_from_row(connection, target_row)
        source = linked.phase6b_result.source.phase6a_source
        if (
            target.calculation_id != source.target_calculation_id
            or target.run_id != linked.phase6b_source_link.target_child_run_id
            or target.definition_id != source.target_definition_id
            or target.definition_version != source.target_definition_version
            or target.as_of_utc != source.as_of_utc
            or target.current_position_value_usd != source.current_exposure_usd
            or target.target_position_value_usd != source.target_exposure_usd
            or target.adjustment_value_usd != source.desired_change_usd
            or target.research_capital_basis_usd
            != linked.research_capital_basis_usd
            or target.created_at_utc != linked.target_result_created_at_utc
            or target.schema_version != linked.target_result_schema_version
        ):
            raise ValueError("Target Position research-basis evidence was modified")

    @staticmethod
    def _insert_definition(connection, definition):
        connection.execute(
            """INSERT INTO research_asset_cash_floor_definitions VALUES
               (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                str(definition.definition_id),
                definition.definition_version,
                definition.predecessor_version,
                definition.symbol,
                str(definition.minimum_research_asset_cash_usd),
                definition.status.value,
                definition.reason,
                definition.created_by,
                _iso(definition.created_at_utc),
                definition.software_version,
                definition.currency,
                definition.schema_version,
            ),
        )

    @staticmethod
    def _insert_operation(connection, operation):
        source = operation.resolved_source
        connection.execute(
            """
            INSERT INTO target_adjustment_cash_floor_operations (
                attempt_id,operation_id,operation_type,status,run_id,stage_id,
                requested_at_utc,completed_at_utc,session_id,request_id,created_by,reason,
                requested_phase6b_result_id,requested_definition_id,
                requested_definition_version,requested_symbol,
                requested_minimum_research_asset_cash_usd_text,
                resolved_definition_id,resolved_definition_version,resolved_source_json,
                current_safety_snapshot_json,resolved_symbol,resolved_action,
                resolved_as_of_utc,preview_result_id,disposition,error_code,error_summary,
                schema_version
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                str(operation.attempt_id),
                str(operation.operation_id),
                operation.operation_type.value,
                operation.status.value,
                str(operation.run_id),
                str(operation.stage_id),
                _iso(operation.requested_at_utc),
                _iso(operation.completed_at_utc),
                operation.session_id,
                operation.request_id,
                operation.created_by,
                operation.reason,
                str(operation.requested_phase6b_result_id)
                if operation.requested_phase6b_result_id
                else None,
                str(operation.requested_definition_id)
                if operation.requested_definition_id
                else None,
                operation.requested_definition_version,
                operation.requested_symbol,
                operation.requested_minimum_research_asset_cash_usd_text,
                str(operation.resolved_definition_id)
                if operation.resolved_definition_id
                else None,
                operation.resolved_definition_version,
                json.dumps(_linked_dict(source), sort_keys=True) if source else None,
                json.dumps(_safety_dict(operation.current_safety_snapshot), sort_keys=True)
                if operation.current_safety_snapshot
                else None,
                source.symbol if source else None,
                source.action if source else None,
                _iso(source.as_of_utc) if source else None,
                str(operation.preview_result_id) if operation.preview_result_id else None,
                operation.disposition.value if operation.disposition else None,
                operation.error_code,
                operation.error_summary,
                operation.schema_version,
            ),
        )

    @staticmethod
    def _insert_result(connection, result):
        source, rule = result.source, result.rule
        phase6b, cap_link = source.phase6b_result, source.phase6b_source_link
        connection.execute(
            """INSERT INTO target_adjustment_cash_floor_results VALUES
               (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                str(result.preview_result_id),
                str(result.operation_id),
                str(result.run_id),
                str(result.stage_id),
                json.dumps(_linked_dict(source), sort_keys=True),
                str(phase6b.preview_result_id),
                str(phase6b.run_id),
                str(phase6b.stage_id),
                str(cap_link.phase6a_review_result_id),
                str(cap_link.phase6a_run_id),
                str(cap_link.phase6a_stage_id),
                str(cap_link.target_calculation_id),
                str(source.definition.definition_id),
                source.definition.definition_version,
                source.symbol,
                _iso(source.as_of_utc),
                source.action,
                str(rule.research_capital_basis_usd),
                str(rule.current_exposure_usd),
                str(rule.phase6b_candidate_notional_usd),
                str(rule.minimum_research_asset_cash_usd),
                str(rule.pre_action_research_cash_usd),
                str(rule.cash_capacity_usd),
                str(rule.cash_floor_constrained_candidate_notional_usd),
                str(rule.post_action_research_cash_usd),
                str(rule.remaining_shortfall_usd),
                str(rule.reduction_usd),
                result.disposition.value,
                json.dumps(result.reason_codes),
                json.dumps(result.warnings),
                _iso(result.created_at_utc),
                result.created_by,
                result.reason,
                result.software_version,
                result.component_id,
                result.component_version,
                result.schema_version,
            ),
        )

    @staticmethod
    def _insert_rule(connection, rule):
        connection.execute(
            """INSERT INTO target_adjustment_cash_floor_rule_results VALUES
               (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                str(rule.rule_result_id),
                str(rule.preview_result_id),
                str(rule.run_id),
                str(rule.stage_id),
                rule.rule_id,
                rule.rule_version,
                rule.evaluation_order,
                rule.action,
                str(rule.research_capital_basis_usd),
                str(rule.current_exposure_usd),
                str(rule.phase6b_candidate_notional_usd),
                str(rule.minimum_research_asset_cash_usd),
                str(rule.pre_action_research_cash_usd),
                str(rule.cash_capacity_usd),
                str(rule.cash_floor_constrained_candidate_notional_usd),
                str(rule.post_action_research_cash_usd),
                str(rule.remaining_shortfall_usd),
                str(rule.reduction_usd),
                rule.outcome.value,
                json.dumps(rule.reason_codes),
                int(rule.stop_processing),
                _iso(rule.evaluated_at_utc),
                rule.schema_version,
            ),
        )

    @staticmethod
    def _insert_link(connection, link):
        connection.execute(
            """INSERT INTO target_adjustment_cash_floor_source_links VALUES
               (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                str(link.source_link_id),
                str(link.operation_id),
                str(link.preview_result_id),
                str(link.cash_floor_run_id),
                str(link.cash_floor_stage_id),
                str(link.phase6b_preview_result_id),
                str(link.phase6b_run_id),
                str(link.phase6b_stage_id),
                str(link.phase6a_review_result_id),
                str(link.phase6a_run_id),
                str(link.phase6a_stage_id),
                str(link.decision_run_id),
                str(link.linked_parent_run_id),
                str(link.target_child_run_id),
                str(link.standardized_state_run_id),
                str(link.decision_result_id),
                str(link.intent_id),
                str(link.target_position_link_id),
                str(link.target_calculation_id),
                str(link.standardized_state_calculation_id),
                _iso(link.created_at_utc),
                link.schema_version,
            ),
        )

    @staticmethod
    def _definition(row):
        return ResearchAssetCashFloorDefinitionVersion(
            UUID(row["definition_id"]),
            int(row["definition_version"]),
            int(row["predecessor_version"])
            if row["predecessor_version"] is not None
            else None,
            row["symbol"],
            Decimal(row["minimum_research_asset_cash_usd_text"]),
            ResearchCashFloorDefinitionStatus(row["status"]),
            row["reason"],
            row["created_by"],
            _dt(row["created_at_utc"]),
            row["software_version"],
            row["currency"],
            int(row["schema_version"]),
        )

    @staticmethod
    def _operation(row):
        source = (
            _linked_from(json.loads(row["resolved_source_json"]))
            if row["resolved_source_json"]
            else None
        )
        safety = (
            _safety_from(json.loads(row["current_safety_snapshot_json"]))
            if row["current_safety_snapshot_json"]
            else None
        )
        return ResearchCashFloorOperationAttempt(
            UUID(row["attempt_id"]),
            UUID(row["operation_id"]),
            ResearchCashFloorOperationType(row["operation_type"]),
            ResearchCashFloorOperationStatus(row["status"]),
            UUID(row["run_id"]),
            UUID(row["stage_id"]),
            _dt(row["requested_at_utc"]),
            _dt(row["completed_at_utc"]),
            row["session_id"],
            row["request_id"],
            row["created_by"],
            row["reason"],
            UUID(row["requested_phase6b_result_id"])
            if row["requested_phase6b_result_id"]
            else None,
            UUID(row["requested_definition_id"])
            if row["requested_definition_id"]
            else None,
            int(row["requested_definition_version"])
            if row["requested_definition_version"] is not None
            else None,
            row["requested_symbol"],
            row["requested_minimum_research_asset_cash_usd_text"],
            UUID(row["resolved_definition_id"])
            if row["resolved_definition_id"]
            else None,
            int(row["resolved_definition_version"])
            if row["resolved_definition_version"] is not None
            else None,
            source,
            safety,
            UUID(row["preview_result_id"]) if row["preview_result_id"] else None,
            ResearchCashFloorDisposition(row["disposition"])
            if row["disposition"]
            else None,
            row["error_code"],
            row["error_summary"],
            int(row["schema_version"]),
        )

    @staticmethod
    def _result(connection, row):
        rule_row = connection.execute(
            "SELECT * FROM target_adjustment_cash_floor_rule_results "
            "WHERE preview_result_id=?",
            (row["preview_result_id"],),
        ).fetchone()
        if rule_row is None:
            raise sqlite3.DatabaseError(
                "research cash-floor result is missing its locked rule"
            )
        rule = ResearchCashFloorRuleResult(
            UUID(rule_row["rule_result_id"]),
            UUID(rule_row["preview_result_id"]),
            UUID(rule_row["run_id"]),
            UUID(rule_row["stage_id"]),
            rule_row["action"],
            Decimal(rule_row["research_capital_basis_usd_text"]),
            Decimal(rule_row["current_exposure_usd_text"]),
            Decimal(rule_row["phase6b_candidate_notional_usd_text"]),
            Decimal(rule_row["minimum_research_asset_cash_usd_text"]),
            Decimal(rule_row["pre_action_research_cash_usd_text"]),
            Decimal(rule_row["cash_capacity_usd_text"]),
            Decimal(rule_row["cash_floor_constrained_candidate_notional_usd_text"]),
            Decimal(rule_row["post_action_research_cash_usd_text"]),
            Decimal(rule_row["remaining_shortfall_usd_text"]),
            Decimal(rule_row["reduction_usd_text"]),
            ResearchCashFloorRuleOutcome(rule_row["outcome"]),
            tuple(json.loads(rule_row["reason_codes_json"])),
            _dt(rule_row["evaluated_at_utc"]),
            bool(rule_row["stop_processing"]),
            rule_row["rule_id"],
            rule_row["rule_version"],
            int(rule_row["evaluation_order"]),
            int(rule_row["schema_version"]),
        )
        return TargetAdjustmentResearchCashFloorPreviewResult(
            UUID(row["preview_result_id"]),
            UUID(row["operation_id"]),
            UUID(row["run_id"]),
            UUID(row["stage_id"]),
            _linked_from(json.loads(row["source_json"])),
            rule,
            ResearchCashFloorDisposition(row["disposition"]),
            tuple(json.loads(row["reason_codes_json"])),
            tuple(json.loads(row["warnings_json"])),
            _dt(row["created_at_utc"]),
            row["created_by"],
            row["reason"],
            row["software_version"],
            row["component_id"],
            row["component_version"],
            int(row["schema_version"]),
        )

    @staticmethod
    def _link(row):
        return ResearchCashFloorSourceLink(
            *(UUID(row[name]) for name in (
                "source_link_id",
                "operation_id",
                "preview_result_id",
                "cash_floor_run_id",
                "cash_floor_stage_id",
                "phase6b_preview_result_id",
                "phase6b_run_id",
                "phase6b_stage_id",
                "phase6a_review_result_id",
                "phase6a_run_id",
                "phase6a_stage_id",
                "decision_run_id",
                "linked_parent_run_id",
                "target_child_run_id",
                "standardized_state_run_id",
                "decision_result_id",
                "intent_id",
                "target_position_link_id",
                "target_calculation_id",
                "standardized_state_calculation_id",
            )),
            _dt(row["created_at_utc"]),
            int(row["schema_version"]),
        )


__all__ = ["SQLiteResearchCashFloorStore"]
