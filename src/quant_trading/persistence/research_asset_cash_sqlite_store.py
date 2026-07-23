"""SQLite adapter for immutable order-3 research asset-cash Risk evidence."""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from uuid import UUID

from quant_trading.capital_allocation import CapitalBasisSource, CapitalBucketType
from quant_trading.risk import (
    LinkedResearchAssetCashPreviewInput,
    ResearchAssetCashDisposition,
    ResearchAssetCashOperationAttempt,
    ResearchAssetCashOperationQuery,
    ResearchAssetCashOperationStatus,
    ResearchAssetCashResultQuery,
    ResearchAssetCashRuleOutcome,
    ResearchAssetCashRuleResult,
    ResearchAssetCashSourceLink,
    ResearchCashFloorDisposition,
    ResearchCashFloorRuleOutcome,
    ResearchCashFloorRuleResult,
    TargetAdjustmentResearchAssetCashPreviewResult,
    TargetAdjustmentResearchCashFloorPreviewResult,
)

from .capital_allocation_sqlite_store import SQLiteCapitalAllocationStore
from .research_cash_floor_sqlite_store import (
    SQLiteResearchCashFloorStore,
    _linked_dict as _phase6c_source_dict,
    _linked_from as _phase6c_source_from,
)
from .sqlite_database import CentralSQLiteDatabase
from .target_adjustment_risk_sqlite_store import _safety_dict, _safety_from


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="microseconds")


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(UTC)


def _phase6c_result_dict(result) -> dict[str, object]:
    rule = result.rule
    return {
        "preview_result_id": str(result.preview_result_id),
        "operation_id": str(result.operation_id),
        "run_id": str(result.run_id),
        "stage_id": str(result.stage_id),
        "source": _phase6c_source_dict(result.source),
        "rule": {
            "rule_result_id": str(rule.rule_result_id),
            "preview_result_id": str(rule.preview_result_id),
            "run_id": str(rule.run_id),
            "stage_id": str(rule.stage_id),
            "action": rule.action,
            "research_capital_basis_usd": str(rule.research_capital_basis_usd),
            "current_exposure_usd": str(rule.current_exposure_usd),
            "phase6b_candidate_notional_usd": str(rule.phase6b_candidate_notional_usd),
            "minimum_research_asset_cash_usd": str(rule.minimum_research_asset_cash_usd),
            "pre_action_research_cash_usd": str(rule.pre_action_research_cash_usd),
            "cash_capacity_usd": str(rule.cash_capacity_usd),
            "cash_floor_constrained_candidate_notional_usd": str(rule.cash_floor_constrained_candidate_notional_usd),
            "post_action_research_cash_usd": str(rule.post_action_research_cash_usd),
            "remaining_shortfall_usd": str(rule.remaining_shortfall_usd),
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


def _phase6c_result_from(data: dict[str, object]):
    values = dict(data["rule"])
    rule = ResearchCashFloorRuleResult(
        UUID(str(values["rule_result_id"])),
        UUID(str(values["preview_result_id"])),
        UUID(str(values["run_id"])),
        UUID(str(values["stage_id"])),
        str(values["action"]),
        Decimal(str(values["research_capital_basis_usd"])),
        Decimal(str(values["current_exposure_usd"])),
        Decimal(str(values["phase6b_candidate_notional_usd"])),
        Decimal(str(values["minimum_research_asset_cash_usd"])),
        Decimal(str(values["pre_action_research_cash_usd"])),
        Decimal(str(values["cash_capacity_usd"])),
        Decimal(str(values["cash_floor_constrained_candidate_notional_usd"])),
        Decimal(str(values["post_action_research_cash_usd"])),
        Decimal(str(values["remaining_shortfall_usd"])),
        Decimal(str(values["reduction_usd"])),
        ResearchCashFloorRuleOutcome(str(values["outcome"])),
        tuple(str(item) for item in values["reason_codes"]),
        _dt(str(values["evaluated_at_utc"])),
        bool(values["stop_processing"]),
        str(values["rule_id"]),
        str(values["rule_version"]),
        int(values["evaluation_order"]),
        int(values["schema_version"]),
    )
    return TargetAdjustmentResearchCashFloorPreviewResult(
        UUID(str(data["preview_result_id"])),
        UUID(str(data["operation_id"])),
        UUID(str(data["run_id"])),
        UUID(str(data["stage_id"])),
        _phase6c_source_from(dict(data["source"])),
        rule,
        ResearchCashFloorDisposition(str(data["disposition"])),
        tuple(str(item) for item in data["reason_codes"]),
        tuple(str(item) for item in data["warnings"]),
        _dt(str(data["created_at_utc"])),
        str(data["created_by"]),
        str(data["reason"]),
        str(data["software_version"]),
        str(data["component_id"]),
        str(data["component_version"]),
        int(data["schema_version"]),
    )


def _phase6c_link_dict(link) -> dict[str, object]:
    names = (
        "source_link_id", "operation_id", "preview_result_id", "cash_floor_run_id",
        "cash_floor_stage_id", "phase6b_preview_result_id", "phase6b_run_id",
        "phase6b_stage_id", "phase6a_review_result_id", "phase6a_run_id",
        "phase6a_stage_id", "decision_run_id", "linked_parent_run_id",
        "target_child_run_id", "standardized_state_run_id", "decision_result_id",
        "intent_id", "target_position_link_id", "target_calculation_id",
        "standardized_state_calculation_id",
    )
    return {name: str(getattr(link, name)) for name in names} | {
        "created_at_utc": _iso(link.created_at_utc),
        "schema_version": link.schema_version,
    }


def _phase6c_link_from(data: dict[str, object]):
    from quant_trading.risk import ResearchCashFloorSourceLink

    names = (
        "source_link_id", "operation_id", "preview_result_id", "cash_floor_run_id",
        "cash_floor_stage_id", "phase6b_preview_result_id", "phase6b_run_id",
        "phase6b_stage_id", "phase6a_review_result_id", "phase6a_run_id",
        "phase6a_stage_id", "decision_run_id", "linked_parent_run_id",
        "target_child_run_id", "standardized_state_run_id", "decision_result_id",
        "intent_id", "target_position_link_id", "target_calculation_id",
        "standardized_state_calculation_id",
    )
    return ResearchCashFloorSourceLink(
        *(UUID(str(data[name])) for name in names),
        _dt(str(data["created_at_utc"])),
        int(data["schema_version"]),
    )


def _source_dict(source: LinkedResearchAssetCashPreviewInput) -> dict[str, object]:
    return {
        "phase6c_result": _phase6c_result_dict(source.phase6c_result),
        "phase6c_source_link": _phase6c_link_dict(source.phase6c_source_link),
        "capital_plan_id": str(source.capital_plan_id),
        "capital_plan_version": source.capital_plan_version,
        "capital_plan_created_at_utc": _iso(source.capital_plan_created_at_utc),
        "capital_snapshot_id": str(source.capital_snapshot_id),
        "capital_snapshot_run_id": str(source.capital_snapshot_run_id),
        "capital_snapshot_created_at_utc": _iso(source.capital_snapshot_created_at_utc),
        "account_cash_basis_usd": str(source.account_cash_basis_usd),
        "conservation_expected_total_usd": str(source.conservation_expected_total_usd),
        "conservation_actual_total_usd": str(source.conservation_actual_total_usd),
        "conservation_difference_usd": str(source.conservation_difference_usd),
        "locked_reserve_bucket_id": str(source.locked_reserve_bucket_id),
        "locked_reserve_balance_usd": str(source.locked_reserve_balance_usd),
        "tactical_reserve_bucket_id": str(source.tactical_reserve_bucket_id),
        "tactical_reserve_balance_usd": str(source.tactical_reserve_balance_usd),
        "asset_cash_bucket_id": str(source.asset_cash_bucket_id),
        "asset_cash_balance_usd": str(source.asset_cash_balance_usd),
        "current_safety_snapshot": _safety_dict(source.current_safety_snapshot),
        "currency": source.currency,
        "capital_plan_schema_version": source.capital_plan_schema_version,
        "capital_snapshot_schema_version": source.capital_snapshot_schema_version,
        "schema_version": source.schema_version,
    }


def _source_from(data: dict[str, object]) -> LinkedResearchAssetCashPreviewInput:
    return LinkedResearchAssetCashPreviewInput(
        _phase6c_result_from(dict(data["phase6c_result"])),
        _phase6c_link_from(dict(data["phase6c_source_link"])),
        UUID(str(data["capital_plan_id"])),
        int(data["capital_plan_version"]),
        _dt(str(data["capital_plan_created_at_utc"])),
        UUID(str(data["capital_snapshot_id"])),
        UUID(str(data["capital_snapshot_run_id"])),
        _dt(str(data["capital_snapshot_created_at_utc"])),
        Decimal(str(data["account_cash_basis_usd"])),
        Decimal(str(data["conservation_expected_total_usd"])),
        Decimal(str(data["conservation_actual_total_usd"])),
        Decimal(str(data["conservation_difference_usd"])),
        UUID(str(data["locked_reserve_bucket_id"])),
        Decimal(str(data["locked_reserve_balance_usd"])),
        UUID(str(data["tactical_reserve_bucket_id"])),
        Decimal(str(data["tactical_reserve_balance_usd"])),
        UUID(str(data["asset_cash_bucket_id"])),
        Decimal(str(data["asset_cash_balance_usd"])),
        _safety_from(dict(data["current_safety_snapshot"])),
        str(data["currency"]),
        int(data["capital_plan_schema_version"]),
        int(data["capital_snapshot_schema_version"]),
        int(data["schema_version"]),
    )


class SQLiteResearchAssetCashStore:
    def __init__(self, database_path: Path | str) -> None:
        self._database = CentralSQLiteDatabase(database_path)

    def initialize(self) -> None:
        self._database.initialize()

    def get_first_operation(self, operation_id: UUID):
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                """SELECT * FROM target_adjustment_research_asset_cash_operations
                   WHERE operation_id=?
                   ORDER BY CASE WHEN status IN ('completed','blocked') THEN 0 ELSE 1 END,
                            rowid LIMIT 1""",
                (str(operation_id),),
            ).fetchone()
            return self._operation(row) if row else None

    def save_operation(self, operation: ResearchAssetCashOperationAttempt) -> None:
        with closing(self._database.connect()) as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                self._validate_run(connection, operation)
                self._insert_operation(connection, operation)
                connection.commit()
            except Exception as exc:
                connection.rollback()
                raise sqlite3.DatabaseError(
                    "could not save research asset-cash operation"
                ) from exc

    def save_completed(self, result, operation, source_link) -> None:
        self._validate_models(result, operation, source_link)
        with closing(self._database.connect()) as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                self._validate_run(connection, operation)
                self._validate_phase6c(connection, result.source)
                self._validate_capital_current(connection, result.source)
                self._insert_operation(connection, operation)
                self._insert_result(connection, result)
                self._insert_rule(connection, result.rule)
                self._insert_link(connection, source_link)
                connection.commit()
            except Exception as exc:
                connection.rollback()
                raise sqlite3.DatabaseError(
                    "could not save completed research asset-cash preview"
                ) from exc

    def get_research_asset_cash_result(self, preview_result_id: UUID):
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                "SELECT * FROM target_adjustment_research_asset_cash_results WHERE preview_result_id=?",
                (str(preview_result_id),),
            ).fetchone()
            return self._result(connection, row) if row else None

    def get_research_asset_cash_source_link(self, preview_result_id: UUID):
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                "SELECT * FROM target_adjustment_research_asset_cash_source_links WHERE preview_result_id=?",
                (str(preview_result_id),),
            ).fetchone()
            return self._link(row) if row else None

    def list_research_asset_cash_operations(self, query=ResearchAssetCashOperationQuery()):
        clauses, params = [], []
        if query.status:
            clauses.append("status=?"); params.append(query.status.value)
        if query.symbol:
            clauses.append("resolved_symbol=?"); params.append(query.symbol)
        if query.has_error is not None:
            clauses.append("error_code IS NOT NULL" if query.has_error else "error_code IS NULL")
        sql = "SELECT * FROM target_adjustment_research_asset_cash_operations"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY requested_at_utc DESC, rowid DESC LIMIT ?"
        params.append(query.limit)
        with closing(self._database.connect()) as connection:
            return tuple(self._operation(row) for row in connection.execute(sql, params))

    def list_research_asset_cash_results(self, query=ResearchAssetCashResultQuery()):
        clauses, params = [], []
        mapping = {
            "symbol": query.symbol,
            "action": query.action,
            "capital_plan_id": str(query.capital_plan_id) if query.capital_plan_id else None,
            "capital_snapshot_id": str(query.capital_snapshot_id) if query.capital_snapshot_id else None,
            "disposition": query.disposition.value if query.disposition else None,
        }
        for column, value in mapping.items():
            if value is not None:
                clauses.append(f"r.{column}=?"); params.append(value)
        if query.rule_outcome:
            clauses.append("q.outcome=?"); params.append(query.rule_outcome.value)
        if query.has_warnings is not None:
            clauses.append("r.warnings_json != '[]'" if query.has_warnings else "r.warnings_json = '[]'")
        if query.as_of_from_utc is not None:
            clauses.append("r.as_of_utc>=?"); params.append(_iso(query.as_of_from_utc))
        if query.as_of_to_utc is not None:
            clauses.append("r.as_of_utc<=?"); params.append(_iso(query.as_of_to_utc))
        sql = (
            "SELECT r.* FROM target_adjustment_research_asset_cash_results r "
            "JOIN target_adjustment_research_asset_cash_rule_results q "
            "ON q.preview_result_id=r.preview_result_id"
        )
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY r.created_at_utc DESC LIMIT ?"; params.append(query.limit)
        with closing(self._database.connect()) as connection:
            return tuple(self._result(connection, row) for row in connection.execute(sql, params))

    @staticmethod
    def _validate_models(result, operation, link):
        if (
            operation.status is not ResearchAssetCashOperationStatus.COMPLETED
            or operation.preview_result_id != result.preview_result_id
            or operation.disposition is not result.disposition
            or result.operation_id != operation.operation_id
            or link.operation_id != result.operation_id
            or link.preview_result_id != result.preview_result_id
            or link.asset_cash_run_id != result.run_id
            or link.asset_cash_stage_id != result.stage_id
            or result.research_cash_reserved
            or result.rule.research_cash_reserved
        ):
            raise ValueError("research asset-cash operation/result/link is inconsistent")

    @staticmethod
    def _validate_run(connection, operation):
        run = connection.execute("SELECT * FROM algorithm_runs WHERE run_id=?", (str(operation.run_id),)).fetchone()
        stage = connection.execute("SELECT * FROM algorithm_run_stages WHERE stage_id=?", (str(operation.stage_id),)).fetchone()
        if (
            run is None or stage is None
            or run["run_type"] != "target_adjustment_research_asset_cash_preview"
            or run["execution_mode"] != "no_execution"
            or run["trigger_source"] != "algorithm_control.research_asset_cash"
            or stage["run_id"] != str(operation.run_id)
            or stage["stage_name"] != "risk"
            or int(stage["sequence"]) != 1
        ):
            raise ValueError("research asset-cash Run/stage is invalid")
        if operation.resolved_source and run["parent_run_id"] != str(operation.resolved_source.phase6c_result.run_id):
            raise ValueError("research asset-cash parent Phase 6C Run is invalid")

    @staticmethod
    def _validate_phase6c(connection, source):
        row = connection.execute(
            "SELECT * FROM target_adjustment_cash_floor_results WHERE preview_result_id=?",
            (str(source.phase6c_result.preview_result_id),),
        ).fetchone()
        if row is None or SQLiteResearchCashFloorStore._result(connection, row) != source.phase6c_result:
            raise ValueError("Phase 6C result/rule evidence was modified")
        link_row = connection.execute(
            "SELECT * FROM target_adjustment_cash_floor_source_links WHERE preview_result_id=?",
            (str(source.phase6c_result.preview_result_id),),
        ).fetchone()
        if link_row is None or SQLiteResearchCashFloorStore._link(link_row) != source.phase6c_source_link:
            raise ValueError("Phase 6C source-link evidence was modified")

    @staticmethod
    def _validate_capital_current(connection, source):
        plan_row = connection.execute("SELECT * FROM capital_plans WHERE plan_id=?", (str(source.capital_plan_id),)).fetchone()
        bucket_rows = connection.execute("SELECT * FROM capital_plan_buckets WHERE plan_id=? ORDER BY rowid", (str(source.capital_plan_id),)).fetchall()
        snapshot_row = connection.execute("SELECT * FROM capital_snapshots WHERE snapshot_id=? AND plan_id=?", (str(source.capital_snapshot_id), str(source.capital_plan_id))).fetchone()
        latest = connection.execute("SELECT snapshot_id FROM capital_snapshots WHERE plan_id=? ORDER BY sequence DESC LIMIT 1", (str(source.capital_plan_id),)).fetchone()
        if plan_row is None or snapshot_row is None or latest is None or latest["snapshot_id"] != str(source.capital_snapshot_id):
            raise ValueError("selected Capital Plan/Snapshot is missing or no longer latest")
        plan = SQLiteCapitalAllocationStore._plan_from_rows(plan_row, bucket_rows)
        snapshot = SQLiteCapitalAllocationStore._snapshot_from_row(connection, snapshot_row)
        if (
            plan.plan_version != source.capital_plan_version
            or plan.created_at_utc != source.capital_plan_created_at_utc
            or plan.account_cash_basis != source.account_cash_basis_usd
            or plan.currency != source.currency
            or plan.schema_version != source.capital_plan_schema_version
            or plan.basis_source is not CapitalBasisSource.RESEARCH_INPUT
            or snapshot.run_id != source.capital_snapshot_run_id
            or snapshot.created_at_utc != source.capital_snapshot_created_at_utc
            or snapshot.schema_version != source.capital_snapshot_schema_version
            or snapshot.conservation.expected_total != source.conservation_expected_total_usd
            or snapshot.conservation.actual_total != source.conservation_actual_total_usd
            or snapshot.conservation.difference != source.conservation_difference_usd
        ):
            raise ValueError("selected Capital Plan/Snapshot evidence was modified")
        definitions = {item.bucket_id: item for item in plan.buckets}
        balances = {item.bucket_id: item for item in snapshot.balances}
        if set(balances) != set(definitions):
            raise ValueError(
                "selected Capital Snapshot bucket identity no longer matches the plan"
            )
        for bucket_id, item in balances.items():
            definition = definitions[bucket_id]
            if (
                item.bucket_type is not definition.bucket_type
                or item.currency != definition.currency
                or item.symbol != definition.symbol
            ):
                raise ValueError(
                    "selected Capital Snapshot bucket metadata no longer matches the plan"
                )
            if (
                definition.bucket_type
                in {
                    CapitalBucketType.LOCKED_RESERVE,
                    CapitalBucketType.TACTICAL_RESERVE,
                }
                and item.balance != definition.initial_balance
            ):
                raise ValueError(
                    "selected Capital Snapshot protected reserve balance no longer matches "
                    "the plan"
                )
        expected = (
            (source.locked_reserve_bucket_id, CapitalBucketType.LOCKED_RESERVE, source.locked_reserve_balance_usd, None),
            (source.tactical_reserve_bucket_id, CapitalBucketType.TACTICAL_RESERVE, source.tactical_reserve_balance_usd, None),
            (source.asset_cash_bucket_id, CapitalBucketType.ASSET_CASH, source.asset_cash_balance_usd, source.symbol),
        )
        for bucket_id, bucket_type, balance, symbol in expected:
            item = balances.get(bucket_id)
            if item is None or item.bucket_type is not bucket_type or item.balance != balance or item.symbol != symbol:
                raise ValueError("selected Capital bucket evidence was modified")

    @staticmethod
    def _insert_operation(connection, item):
        source = item.resolved_source
        connection.execute(
            """INSERT INTO target_adjustment_research_asset_cash_operations VALUES
               (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                str(item.attempt_id), str(item.operation_id), item.status.value,
                str(item.run_id), str(item.stage_id), _iso(item.requested_at_utc),
                _iso(item.completed_at_utc), item.session_id, item.request_id,
                item.created_by, item.reason, str(item.requested_phase6c_result_id),
                str(item.requested_capital_plan_id), str(item.requested_capital_snapshot_id),
                json.dumps(_source_dict(source), sort_keys=True) if source else None,
                json.dumps(_safety_dict(item.current_safety_snapshot), sort_keys=True) if item.current_safety_snapshot else None,
                source.symbol if source else None, source.action if source else None,
                _iso(source.as_of_utc) if source else None,
                str(item.preview_result_id) if item.preview_result_id else None,
                item.disposition.value if item.disposition else None,
                item.error_code, item.error_summary, item.schema_version,
            ),
        )

    @staticmethod
    def _insert_result(connection, result):
        source, rule, upstream = result.source, result.rule, result.source.phase6c_source_link
        connection.execute(
            """INSERT INTO target_adjustment_research_asset_cash_results VALUES
               (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                str(result.preview_result_id), str(result.operation_id), str(result.run_id), str(result.stage_id),
                json.dumps(_source_dict(source), sort_keys=True), str(source.phase6c_result.preview_result_id),
                str(source.phase6c_result.run_id), str(source.phase6c_result.stage_id),
                str(upstream.phase6b_run_id), str(upstream.phase6a_run_id), str(source.capital_plan_id),
                source.capital_plan_version, str(source.capital_snapshot_id), str(source.capital_snapshot_run_id),
                str(source.asset_cash_bucket_id), source.symbol, _iso(source.as_of_utc), source.action,
                str(rule.phase6c_candidate_notional_usd), str(rule.selected_asset_cash_balance_usd),
                str(rule.asset_cash_constrained_candidate_notional_usd),
                str(rule.hypothetical_post_candidate_asset_cash_usd), str(rule.reduction_usd),
                int(result.research_cash_reserved), result.disposition.value,
                json.dumps(result.reason_codes), json.dumps(result.warnings), _iso(result.created_at_utc),
                result.created_by, result.reason, result.software_version, result.component_id,
                result.component_version, result.schema_version,
            ),
        )

    @staticmethod
    def _insert_rule(connection, rule):
        connection.execute(
            """INSERT INTO target_adjustment_research_asset_cash_rule_results VALUES
               (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                str(rule.rule_result_id), str(rule.preview_result_id), str(rule.run_id), str(rule.stage_id),
                rule.rule_id, rule.rule_version, rule.evaluation_order, rule.action,
                str(rule.phase6c_candidate_notional_usd), str(rule.selected_asset_cash_balance_usd),
                str(rule.pre_candidate_asset_cash_usd), str(rule.asset_cash_constrained_candidate_notional_usd),
                str(rule.hypothetical_post_candidate_asset_cash_usd), str(rule.reduction_usd),
                rule.outcome.value, json.dumps(rule.reason_codes), int(rule.research_cash_reserved),
                int(rule.stop_processing), _iso(rule.evaluated_at_utc), rule.schema_version,
            ),
        )

    @staticmethod
    def _insert_link(connection, link):
        values = [
            link.source_link_id, link.operation_id, link.preview_result_id, link.asset_cash_run_id,
            link.asset_cash_stage_id, link.phase6c_preview_result_id, link.phase6c_run_id,
            link.phase6c_stage_id, link.phase6b_run_id, link.phase6a_run_id,
            link.decision_run_id, link.linked_parent_run_id, link.target_child_run_id,
            link.standardized_state_run_id, link.capital_plan_id, link.capital_snapshot_id,
            link.capital_snapshot_run_id, link.asset_cash_bucket_id,
        ]
        connection.execute(
            "INSERT INTO target_adjustment_research_asset_cash_source_links VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (*[str(item) for item in values], _iso(link.created_at_utc), link.schema_version),
        )

    @staticmethod
    def _operation(row):
        source = _source_from(json.loads(row["resolved_source_json"])) if row["resolved_source_json"] else None
        safety = _safety_from(json.loads(row["current_safety_snapshot_json"])) if row["current_safety_snapshot_json"] else None
        return ResearchAssetCashOperationAttempt(
            UUID(row["attempt_id"]), UUID(row["operation_id"]), ResearchAssetCashOperationStatus(row["status"]),
            UUID(row["run_id"]), UUID(row["stage_id"]), _dt(row["requested_at_utc"]),
            _dt(row["completed_at_utc"]), row["session_id"], row["request_id"], row["created_by"], row["reason"],
            UUID(row["requested_phase6c_result_id"]), UUID(row["requested_capital_plan_id"]),
            UUID(row["requested_capital_snapshot_id"]), source, safety,
            UUID(row["preview_result_id"]) if row["preview_result_id"] else None,
            ResearchAssetCashDisposition(row["disposition"]) if row["disposition"] else None,
            row["error_code"], row["error_summary"], int(row["schema_version"]),
        )

    @staticmethod
    def _result(connection, row):
        rule_row = connection.execute(
            "SELECT * FROM target_adjustment_research_asset_cash_rule_results WHERE preview_result_id=?",
            (row["preview_result_id"],),
        ).fetchone()
        if rule_row is None:
            raise sqlite3.DatabaseError("research asset-cash result is missing rule evidence")
        rule = ResearchAssetCashRuleResult(
            UUID(rule_row["rule_result_id"]), UUID(rule_row["preview_result_id"]),
            UUID(rule_row["run_id"]), UUID(rule_row["stage_id"]), rule_row["action"],
            Decimal(rule_row["phase6c_candidate_notional_usd_text"]),
            Decimal(rule_row["selected_asset_cash_balance_usd_text"]),
            Decimal(rule_row["pre_candidate_asset_cash_usd_text"]),
            Decimal(rule_row["asset_cash_constrained_candidate_notional_usd_text"]),
            Decimal(rule_row["hypothetical_post_candidate_asset_cash_usd_text"]),
            Decimal(rule_row["reduction_usd_text"]), ResearchAssetCashRuleOutcome(rule_row["outcome"]),
            tuple(json.loads(rule_row["reason_codes_json"])), _dt(rule_row["evaluated_at_utc"]),
            bool(rule_row["research_cash_reserved"]), bool(rule_row["stop_processing"]),
            rule_row["rule_id"], rule_row["rule_version"], int(rule_row["evaluation_order"]),
            int(rule_row["schema_version"]),
        )
        return TargetAdjustmentResearchAssetCashPreviewResult(
            UUID(row["preview_result_id"]), UUID(row["operation_id"]), UUID(row["run_id"]),
            UUID(row["stage_id"]), _source_from(json.loads(row["source_json"])), rule,
            ResearchAssetCashDisposition(row["disposition"]), tuple(json.loads(row["reason_codes_json"])),
            tuple(json.loads(row["warnings_json"])), bool(row["research_cash_reserved"]),
            _dt(row["created_at_utc"]), row["created_by"], row["reason"], row["software_version"],
            row["component_id"], row["component_version"], int(row["schema_version"]),
        )

    @staticmethod
    def _link(row):
        names = (
            "source_link_id", "operation_id", "preview_result_id", "asset_cash_run_id",
            "asset_cash_stage_id", "phase6c_preview_result_id", "phase6c_run_id",
            "phase6c_stage_id", "phase6b_run_id", "phase6a_run_id", "decision_run_id",
            "linked_parent_run_id", "target_child_run_id", "standardized_state_run_id",
            "capital_plan_id", "capital_snapshot_id", "capital_snapshot_run_id", "asset_cash_bucket_id",
        )
        return ResearchAssetCashSourceLink(
            *(UUID(row[name]) for name in names),
            _dt(row["created_at_utc"]), int(row["schema_version"]),
        )


__all__ = ["SQLiteResearchAssetCashStore"]
