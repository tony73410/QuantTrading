"""Central SQLite adapter for immutable P23-3A cycle-target evidence."""

from __future__ import annotations

from contextlib import closing
from datetime import date, datetime
from decimal import Decimal
import json
from pathlib import Path
import sqlite3
from uuid import UUID

from quant_trading.target_position.cycle_interfaces import CycleTargetPositionStore
from quant_trading.target_position.cycle_models import (
    AssetCycleTargetConfiguration,
    CycleTargetAttribution,
    CycleTargetCalculationTrace,
    CycleTargetCandidateState,
    CycleTargetDefinitionStatus,
    CycleTargetDirection,
    CycleTargetFloatEvidence,
    CycleTargetFormulaDefinition,
    CycleTargetOperation,
    CycleTargetOperationStatus,
    CycleTargetOperationType,
    CycleTargetPositionResult,
    CycleTargetPriceEvidence,
    CycleTargetQuery,
    CycleTargetRegion,
    CycleTargetResponseDirection,
    CycleTargetResultStatus,
    CycleTargetSourceLink,
    ReversalObservationTargetInput,
)
from quant_trading.target_position.models import TargetPositionAdjustmentDirection

from .sqlite_database import CentralSQLiteDatabase


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _float(row, prefix: str) -> CycleTargetFloatEvidence:
    return CycleTargetFloatEvidence(
        row[f"{prefix}_text"], row[prefix], row[f"{prefix}_hex"]
    )


def _optional_float(row, prefix: str) -> CycleTargetFloatEvidence | None:
    return None if row[f"{prefix}_text"] is None else _float(row, prefix)


class SQLiteCycleTargetPositionStore(CycleTargetPositionStore):
    def __init__(self, database: CentralSQLiteDatabase | Path | str) -> None:
        self._database = (
            database
            if isinstance(database, CentralSQLiteDatabase)
            else CentralSQLiteDatabase(database)
        )

    def initialize(self) -> None:
        self._database.initialize()

    def get_formula_definition(self, definition_id: UUID):
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                "SELECT * FROM cycle_target_formula_definitions WHERE formula_definition_id = ?",
                (str(definition_id),),
            ).fetchone()
        return self._formula(row) if row else None

    def list_formula_definitions(self, *, include_archived=False, limit=500):
        where = "" if include_archived else " WHERE status = 'disabled'"
        with closing(self._database.connect()) as connection:
            rows = connection.execute(
                "SELECT * FROM cycle_target_formula_definitions" + where
                + " ORDER BY created_at_utc DESC, definition_version DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return tuple(self._formula(row) for row in rows)

    def get_configuration(self, configuration_id: UUID):
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                "SELECT * FROM cycle_target_asset_configurations WHERE configuration_id = ?",
                (str(configuration_id),),
            ).fetchone()
        return self._configuration(row) if row else None

    def list_configurations(self, query: CycleTargetQuery = CycleTargetQuery()):
        clauses, values = [], []
        if query.symbol:
            clauses.append("symbol = ?"); values.append(query.symbol)
        if query.formula_definition_id:
            clauses.append("formula_definition_id = ?"); values.append(str(query.formula_definition_id))
        if query.configuration_id:
            clauses.append("configuration_id = ?"); values.append(str(query.configuration_id))
        sql = "SELECT * FROM cycle_target_asset_configurations"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY created_at_utc DESC, configuration_version DESC LIMIT ?"
        values.append(query.limit)
        with closing(self._database.connect()) as connection:
            rows = connection.execute(sql, values).fetchall()
        return tuple(self._configuration(row) for row in rows)

    def get_first_operation(self, operation_id: UUID):
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                """SELECT attempt_id FROM cycle_target_operation_attempts
                   WHERE operation_id = ? ORDER BY completed_at_utc, attempt_id LIMIT 1""",
                (str(operation_id),),
            ).fetchone()
        return self.get_operation(UUID(row["attempt_id"])) if row else None

    def get_operation_by_operation_id(self, operation_id: UUID):
        """Reload one exact operation through the read-only query boundary."""

        return self.get_first_operation(operation_id)

    def get_operation(self, attempt_id: UUID):
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                "SELECT * FROM cycle_target_operation_attempts WHERE attempt_id = ?",
                (str(attempt_id),),
            ).fetchone()
            result = self._load_result(connection, UUID(row["result_id"])) if row and row["result_id"] else None
        return self._operation(row, result) if row else None

    def list_operations(self, query: CycleTargetQuery = CycleTargetQuery()):
        clauses, values = [], []
        if query.symbol:
            clauses.append("o.requested_symbol = ?"); values.append(query.symbol)
        if query.formula_definition_id:
            clauses.append("o.resolved_formula_definition_id = ?"); values.append(str(query.formula_definition_id))
        if query.configuration_id:
            clauses.append("o.resolved_configuration_id = ?"); values.append(str(query.configuration_id))
        if query.source_result_id:
            clauses.append("o.requested_source_result_id = ?"); values.append(str(query.source_result_id))
        if query.source_step_id:
            clauses.append("o.requested_source_step_id = ?"); values.append(str(query.source_step_id))
        if query.run_id:
            clauses.append("o.run_id = ?"); values.append(str(query.run_id))
        if query.status:
            clauses.append("o.status = ?"); values.append(query.status.value)
        if query.region:
            clauses.append("r.region = ?"); values.append(query.region.value)
        if query.created_from_utc:
            clauses.append("o.completed_at_utc >= ?"); values.append(query.created_from_utc.isoformat())
        if query.created_to_utc:
            clauses.append("o.completed_at_utc <= ?"); values.append(query.created_to_utc.isoformat())
        sql = (
            "SELECT o.* FROM cycle_target_operation_attempts o "
            "LEFT JOIN cycle_target_results r ON r.result_id = o.result_id"
        )
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY o.completed_at_utc DESC, o.attempt_id DESC LIMIT ?"
        values.append(query.limit)
        operations = []
        with closing(self._database.connect()) as connection:
            rows = connection.execute(sql, values).fetchall()
            for row in rows:
                result = self._load_result(connection, UUID(row["result_id"])) if row["result_id"] else None
                operations.append(self._operation(row, result))
        return tuple(operations)

    def get_result(self, result_id: UUID):
        with closing(self._database.connect()) as connection:
            return self._load_result(connection, result_id)

    def list_results(self, query: CycleTargetQuery = CycleTargetQuery()):
        clauses, values = [], []
        mapping = (
            (query.symbol, "symbol"),
            (query.formula_definition_id, "formula_definition_id"),
            (query.configuration_id, "configuration_id"),
            (query.source_result_id, "source_result_id"),
            (query.source_step_id, "source_step_id"),
            (query.run_id, "run_id"),
        )
        for value, column in mapping:
            if value is not None:
                clauses.append(f"{column} = ?"); values.append(str(value))
        if query.region:
            clauses.append("region = ?"); values.append(query.region.value)
        if query.created_from_utc:
            clauses.append("created_at_utc >= ?"); values.append(query.created_from_utc.isoformat())
        if query.created_to_utc:
            clauses.append("created_at_utc <= ?"); values.append(query.created_to_utc.isoformat())
        sql = "SELECT result_id FROM cycle_target_results"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY created_at_utc DESC, result_id DESC LIMIT ?"
        values.append(query.limit)
        with closing(self._database.connect()) as connection:
            rows = connection.execute(sql, values).fetchall()
            return tuple(self._load_result(connection, UUID(row["result_id"])) for row in rows)

    def save_formula_definition(self, definition, operation):
        with closing(self._database.connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            self._validate_run(connection, operation)
            connection.execute(
                """INSERT INTO cycle_target_formula_definitions VALUES (
                   :formula_definition_id,:definition_version,:predecessor_formula_definition_id,
                   :status,:name,:reason,:component_id,:component_version,:response_direction,
                   :state_formula,:linear_formula,:acceleration_formula,:region_policy,:numeric_policy,
                   :solver_id,:solver_tolerance_text,:solver_tolerance,:solver_tolerance_hex,
                   :solver_max_iterations,:created_at_utc,:created_by,:software_version,
                   :source_revision,:worktree_state,:execution_allowed,:live_allowed,:schema_version)""",
                self._formula_values(definition),
            )
            self._insert_operation(connection, operation)
            connection.commit()

    def save_configuration(self, configuration, operation):
        with closing(self._database.connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            self._validate_run(connection, operation)
            formula = connection.execute(
                "SELECT definition_version FROM cycle_target_formula_definitions WHERE formula_definition_id = ?",
                (str(configuration.formula_definition_id),),
            ).fetchone()
            if not formula or formula["definition_version"] != configuration.formula_definition_version:
                raise sqlite3.IntegrityError("cycle-target formula identity/version mismatch")
            connection.execute(
                """INSERT INTO cycle_target_asset_configurations VALUES (
                   :configuration_id,:configuration_version,:predecessor_configuration_id,
                   :formula_definition_id,:formula_definition_version,:symbol,:status,
                   :minimum_fraction_input_text,:minimum_fraction,:minimum_fraction_hex,
                   :neutral_fraction_input_text,:neutral_fraction,:neutral_fraction_hex,
                   :maximum_fraction_input_text,:maximum_fraction,:maximum_fraction_hex,
                   :linear_slope_input_text,:linear_slope,:linear_slope_hex,
                   :acceleration_start_input_text,:acceleration_start,:acceleration_start_hex,
                   :saturation_input_text,:saturation,:saturation_hex,:constraint_fingerprint,
                   :created_at_utc,:created_by,:reason,:software_version,:source_revision,
                   :worktree_state,:execution_allowed,:live_allowed,:schema_version)""",
                self._configuration_values(configuration),
            )
            self._insert_operation(connection, operation)
            connection.commit()

    def save_preview(self, result, operation):
        with closing(self._database.connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            self._validate_run(connection, operation)
            self._validate_preview_sources(connection, result, operation)
            self._insert_result(connection, result)
            self._insert_trace(connection, result)
            for link in result.source_links:
                connection.execute(
                    "INSERT INTO cycle_target_source_links VALUES (?,?,?,?,?,?,?)",
                    (str(result.result_id), link.ordinal, link.source_type, link.source_id,
                     link.source_version, link.source_fingerprint,
                     str(link.source_run_id) if link.source_run_id else None),
                )
            self._insert_operation(connection, operation)
            connection.commit()

    def save_operation(self, operation):
        with closing(self._database.connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            self._validate_run(connection, operation)
            self._insert_operation(connection, operation)
            connection.commit()

    @staticmethod
    def _validate_run(connection, operation):
        run = connection.execute(
            "SELECT run_type, execution_mode FROM algorithm_runs WHERE run_id = ?",
            (str(operation.run_id),),
        ).fetchone()
        if not run or run["run_type"] != "cycle_target_position_research" or run["execution_mode"] != "no_execution":
            raise sqlite3.IntegrityError("P29 operation Run identity is invalid")
        expected = []
        if operation.state_stage_id:
            expected.append((operation.state_stage_id, "state"))
        if operation.target_stage_id:
            expected.append((operation.target_stage_id, "target_position"))
        for stage_id, name in expected:
            stage = connection.execute(
                "SELECT run_id, stage_name FROM algorithm_run_stages WHERE stage_id = ?",
                (str(stage_id),),
            ).fetchone()
            if (
                not stage
                or stage["run_id"] != str(operation.run_id)
                or stage["stage_name"] != name
            ):
                raise sqlite3.IntegrityError("P29 operation stage identity is invalid")

    @staticmethod
    def _validate_preview_sources(connection, result, operation):
        if operation.result is None or operation.result.result_id != result.result_id:
            raise sqlite3.IntegrityError("P29 operation/result cardinality mismatch")
        config = connection.execute(
            """SELECT formula_definition_id, formula_definition_version, symbol,
                      configuration_version FROM cycle_target_asset_configurations
               WHERE configuration_id = ?""",
            (str(result.configuration_id),),
        ).fetchone()
        if not config or (
            config["formula_definition_id"] != str(result.formula_definition_id)
            or config["formula_definition_version"] != result.formula_definition_version
            or config["configuration_version"] != result.configuration_version
            or config["symbol"] != result.source.symbol
        ):
            raise sqlite3.IntegrityError("P29 configuration/result identity mismatch")
        source = connection.execute(
            """SELECT r.calculation_fingerprint, r.symbol, s.result_id, s.ordinal
               FROM reversal_observation_results r
               JOIN reversal_observation_daily_steps s ON s.result_id = r.result_id
               WHERE r.result_id = ? AND s.step_id = ?""",
            (str(result.source.source_result_id), str(result.source.source_step_id)),
        ).fetchone()
        if not source or (
            source["calculation_fingerprint"] != result.source.source_calculation_fingerprint
            or source["symbol"] != result.source.symbol
            or source["ordinal"] != result.source.source_step_ordinal
        ):
            raise sqlite3.IntegrityError("P29 exact P28 result/step evidence mismatch")

    @staticmethod
    def _formula_values(item):
        return {
            "formula_definition_id": str(item.formula_definition_id),
            "definition_version": item.definition_version,
            "predecessor_formula_definition_id": str(item.predecessor_formula_definition_id) if item.predecessor_formula_definition_id else None,
            "status": item.status.value, "name": item.name, "reason": item.reason,
            "component_id": item.component_id, "component_version": item.component_version,
            "response_direction": item.response_direction.value, "state_formula": item.state_formula,
            "linear_formula": item.linear_formula, "acceleration_formula": item.acceleration_formula,
            "region_policy": item.region_policy, "numeric_policy": item.numeric_policy,
            "solver_id": item.solver_id, "solver_tolerance_text": item.solver_tolerance.decimal_text,
            "solver_tolerance": item.solver_tolerance.value,
            "solver_tolerance_hex": item.solver_tolerance.ieee_hex,
            "solver_max_iterations": item.solver_max_iterations,
            "created_at_utc": item.created_at_utc.isoformat(), "created_by": item.created_by,
            "software_version": item.software_version, "source_revision": item.source_revision,
            "worktree_state": item.worktree_state, "execution_allowed": int(item.execution_allowed),
            "live_allowed": int(item.live_allowed), "schema_version": item.schema_version,
        }

    @staticmethod
    def _configuration_values(item):
        return {
            "configuration_id": str(item.configuration_id), "configuration_version": item.configuration_version,
            "predecessor_configuration_id": str(item.predecessor_configuration_id) if item.predecessor_configuration_id else None,
            "formula_definition_id": str(item.formula_definition_id),
            "formula_definition_version": item.formula_definition_version,
            "symbol": item.symbol, "status": item.status.value,
            "minimum_fraction_input_text": item.minimum_fraction_input_text,
            "minimum_fraction": item.minimum_fraction.value, "minimum_fraction_hex": item.minimum_fraction.ieee_hex,
            "neutral_fraction_input_text": item.neutral_fraction_input_text,
            "neutral_fraction": item.neutral_fraction.value, "neutral_fraction_hex": item.neutral_fraction.ieee_hex,
            "maximum_fraction_input_text": item.maximum_fraction_input_text,
            "maximum_fraction": item.maximum_fraction.value, "maximum_fraction_hex": item.maximum_fraction.ieee_hex,
            "linear_slope_input_text": item.linear_slope_input_text,
            "linear_slope": item.linear_slope_per_scale.value, "linear_slope_hex": item.linear_slope_per_scale.ieee_hex,
            "acceleration_start_input_text": item.acceleration_start_input_text,
            "acceleration_start": item.acceleration_start_scales.value,
            "acceleration_start_hex": item.acceleration_start_scales.ieee_hex,
            "saturation_input_text": item.saturation_input_text,
            "saturation": item.saturation_scales.value, "saturation_hex": item.saturation_scales.ieee_hex,
            "constraint_fingerprint": item.constraint_fingerprint,
            "created_at_utc": item.created_at_utc.isoformat(), "created_by": item.created_by,
            "reason": item.reason, "software_version": item.software_version,
            "source_revision": item.source_revision, "worktree_state": item.worktree_state,
            "execution_allowed": int(item.execution_allowed), "live_allowed": int(item.live_allowed),
            "schema_version": item.schema_version,
        }

    @staticmethod
    def _insert_operation(connection, item):
        connection.execute(
            """INSERT INTO cycle_target_operation_attempts VALUES (
               :attempt_id,:operation_id,:run_id,:state_stage_id,:target_stage_id,
               :operation_type,:command_fingerprint,:status,:requested_at_utc,:completed_at_utc,
               :session_id,:request_id,:created_by,:reason,:requested_formula_definition_id,
               :requested_formula_definition_version,:requested_configuration_id,
               :requested_configuration_version,:requested_source_result_id,
               :requested_source_step_id,:requested_source_run_id,:requested_symbol,
               :input_values_text,:resolved_formula_definition_id,
               :resolved_formula_definition_version,:resolved_configuration_id,
               :resolved_configuration_version,:result_id,:warnings_text,:error_code,
               :error_summary,:software_version,:source_revision,:worktree_state,
               :execution_allowed,:live_allowed,:schema_version)""",
            {
                "attempt_id": str(item.attempt_id), "operation_id": str(item.operation_id),
                "run_id": str(item.run_id),
                "state_stage_id": str(item.state_stage_id) if item.state_stage_id else None,
                "target_stage_id": str(item.target_stage_id) if item.target_stage_id else None,
                "operation_type": item.operation_type.value, "command_fingerprint": item.command_fingerprint,
                "status": item.status.value, "requested_at_utc": item.requested_at_utc.isoformat(),
                "completed_at_utc": item.completed_at_utc.isoformat(), "session_id": item.session_id,
                "request_id": item.request_id, "created_by": item.created_by, "reason": item.reason,
                "requested_formula_definition_id": str(item.requested_formula_definition_id) if item.requested_formula_definition_id else None,
                "requested_formula_definition_version": item.requested_formula_definition_version,
                "requested_configuration_id": str(item.requested_configuration_id) if item.requested_configuration_id else None,
                "requested_configuration_version": item.requested_configuration_version,
                "requested_source_result_id": str(item.requested_source_result_id) if item.requested_source_result_id else None,
                "requested_source_step_id": str(item.requested_source_step_id) if item.requested_source_step_id else None,
                "requested_source_run_id": str(item.requested_source_run_id) if item.requested_source_run_id else None,
                "requested_symbol": item.requested_symbol, "input_values_text": _json(item.input_values),
                "resolved_formula_definition_id": str(item.resolved_formula_definition_id) if item.resolved_formula_definition_id else None,
                "resolved_formula_definition_version": item.resolved_formula_definition_version,
                "resolved_configuration_id": str(item.resolved_configuration_id) if item.resolved_configuration_id else None,
                "resolved_configuration_version": item.resolved_configuration_version,
                "result_id": str(item.result.result_id) if item.result else None,
                "warnings_text": _json(item.warnings), "error_code": item.error_code,
                "error_summary": item.error_summary, "software_version": item.software_version,
                "source_revision": item.source_revision, "worktree_state": item.worktree_state,
                "execution_allowed": int(item.execution_allowed), "live_allowed": int(item.live_allowed),
                "schema_version": item.schema_version,
            },
        )

    @staticmethod
    def _insert_result(connection, item):
        source = item.source
        connection.execute(
            """INSERT INTO cycle_target_results VALUES (
               :result_id,:calculation_fingerprint,:operation_id,:run_id,:state_stage_id,
               :target_stage_id,:formula_definition_id,:formula_definition_version,
               :configuration_id,:configuration_version,:source_result_id,:source_run_id,
               :source_stage_id,:source_step_id,:source_step_ordinal,:source_definition_id,
               :source_definition_version,:source_component_id,:source_component_version,
               :source_calculation_fingerprint,:source_profile_result_id,:source_profile_run_id,
               :source_parent_run_id,:source_market_evidence_id,:source_market_fingerprint,
               :symbol,:session,:official_close_utc,:available_at_utc,:direction_at_open,
               :direction_at_close,:candidate_state_after_close,:attribution,:event_ids_text,
               :cycle_reference_session,:cycle_reference_price_input_text,
               :cycle_reference_price,:cycle_reference_price_hex,:split_close_input_text,
               :split_close,:split_close_hex,:profile_log_scale_text,:profile_log_scale,
               :profile_log_scale_hex,:source_warnings_text,:region,:status,:target_fraction_text,
               :research_capital_basis_usd_text,:current_position_value_usd_text,
               :target_position_value_usd_text,:adjustment_value_usd_text,:adjustment_direction,
               :warnings_text,:explanation,:created_at_utc,:created_by,:reason,:software_version,
               :source_revision,:worktree_state,:execution_allowed,:live_allowed,:schema_version)""",
            {
                "result_id": str(item.result_id), "calculation_fingerprint": item.calculation_fingerprint,
                "operation_id": str(item.operation_id), "run_id": str(item.run_id),
                "state_stage_id": str(item.state_stage_id), "target_stage_id": str(item.target_stage_id),
                "formula_definition_id": str(item.formula_definition_id),
                "formula_definition_version": item.formula_definition_version,
                "configuration_id": str(item.configuration_id), "configuration_version": item.configuration_version,
                "source_result_id": str(source.source_result_id), "source_run_id": str(source.source_run_id),
                "source_stage_id": str(source.source_stage_id), "source_step_id": str(source.source_step_id),
                "source_step_ordinal": source.source_step_ordinal,
                "source_definition_id": str(source.source_definition_id),
                "source_definition_version": source.source_definition_version,
                "source_component_id": source.source_component_id,
                "source_component_version": source.source_component_version,
                "source_calculation_fingerprint": source.source_calculation_fingerprint,
                "source_profile_result_id": str(source.source_profile_result_id),
                "source_profile_run_id": str(source.source_profile_run_id),
                "source_parent_run_id": str(source.source_parent_run_id),
                "source_market_evidence_id": str(source.source_market_evidence_id),
                "source_market_fingerprint": source.source_market_fingerprint,
                "symbol": source.symbol, "session": source.session.isoformat(),
                "official_close_utc": source.official_close_utc.isoformat(),
                "available_at_utc": source.available_at_utc.isoformat(),
                "direction_at_open": source.direction_at_open.value,
                "direction_at_close": source.direction_at_close.value,
                "candidate_state_after_close": source.candidate_state_after_close.value,
                "attribution": source.attribution.value,
                "event_ids_text": _json(tuple(map(str, source.event_ids))),
                "cycle_reference_session": source.cycle_reference_session.isoformat(),
                "cycle_reference_price_input_text": source.cycle_reference_price.input_text,
                "cycle_reference_price": source.cycle_reference_price.value.value,
                "cycle_reference_price_hex": source.cycle_reference_price.value.ieee_hex,
                "split_close_input_text": source.split_close.input_text,
                "split_close": source.split_close.value.value,
                "split_close_hex": source.split_close.value.ieee_hex,
                "profile_log_scale_text": source.profile_log_scale.decimal_text,
                "profile_log_scale": source.profile_log_scale.value,
                "profile_log_scale_hex": source.profile_log_scale.ieee_hex,
                "source_warnings_text": _json(source.warnings), "region": item.region.value,
                "status": item.status.value, "target_fraction_text": str(item.target_fraction),
                "research_capital_basis_usd_text": str(item.research_capital_basis_usd),
                "current_position_value_usd_text": str(item.current_position_value_usd),
                "target_position_value_usd_text": str(item.target_position_value_usd),
                "adjustment_value_usd_text": str(item.adjustment_value_usd),
                "adjustment_direction": item.adjustment_direction.value,
                "warnings_text": _json(item.warnings), "explanation": item.explanation,
                "created_at_utc": item.created_at_utc.isoformat(), "created_by": item.created_by,
                "reason": item.reason, "software_version": item.software_version,
                "source_revision": item.source_revision, "worktree_state": item.worktree_state,
                "execution_allowed": int(item.execution_allowed), "live_allowed": int(item.live_allowed),
                "schema_version": item.schema_version,
            },
        )

    @staticmethod
    def _insert_trace(connection, result):
        trace = result.trace
        values = {"result_id": str(result.result_id)}
        for prefix, evidence in (
            ("log_price_ratio", trace.log_price_ratio),
            ("normalized_state", trace.normalized_state),
            ("absolute_state", trace.absolute_state),
            ("linear_raw_fraction", trace.linear_raw_fraction),
            ("linear_bounded_fraction", trace.linear_bounded_fraction),
            ("boundary_fraction", trace.boundary_fraction),
            ("headroom", trace.headroom), ("rho", trace.rho), ("beta", trace.beta),
            ("normalized_acceleration_progress", trace.normalized_acceleration_progress),
            ("exponential_progress", trace.exponential_progress),
            ("pre_bound_target_fraction", trace.pre_bound_target_fraction),
            ("final_target_fraction", trace.final_target_fraction),
            ("solver_tolerance", trace.solver_tolerance),
        ):
            values[f"{prefix}_text"] = evidence.decimal_text if evidence else None
            values[prefix] = evidence.value if evidence else None
            values[f"{prefix}_hex"] = evidence.ieee_hex if evidence else None
        values.update({
            "direction_matches": int(trace.direction_matches),
            "confirmation_forces_linear": int(trace.confirmation_forces_linear),
            "counter_move_forces_linear": int(trace.counter_move_forces_linear),
            "within_linear_boundary": int(trace.within_linear_boundary),
            "at_or_beyond_saturation": int(trace.at_or_beyond_saturation),
            "solver_iterations": trace.solver_iterations,
            "exact_decimal_fraction_text": trace.exact_decimal_fraction_text,
            "solver_id": trace.solver_id, "solver_max_iterations": trace.solver_max_iterations,
            "formula_trace_text": _json(trace.formula_trace),
        })
        columns = tuple(values)
        connection.execute(
            f"INSERT INTO cycle_target_calculation_traces ({','.join(columns)}) "
            f"VALUES ({','.join(':'+item for item in columns)})",
            values,
        )

    @staticmethod
    def _formula(row):
        return CycleTargetFormulaDefinition(
            UUID(row["formula_definition_id"]), row["definition_version"],
            UUID(row["predecessor_formula_definition_id"]) if row["predecessor_formula_definition_id"] else None,
            CycleTargetDefinitionStatus(row["status"]), row["name"], row["reason"],
            row["component_id"], row["component_version"],
            CycleTargetResponseDirection(row["response_direction"]), row["state_formula"],
            row["linear_formula"], row["acceleration_formula"], row["region_policy"],
            row["numeric_policy"], row["solver_id"], _float(row, "solver_tolerance"),
            row["solver_max_iterations"], _dt(row["created_at_utc"]), row["created_by"],
            row["software_version"], row["source_revision"], row["worktree_state"],
            bool(row["execution_allowed"]), bool(row["live_allowed"]), row["schema_version"],
        )

    @staticmethod
    def _configuration(row):
        return AssetCycleTargetConfiguration(
            UUID(row["configuration_id"]), row["configuration_version"],
            UUID(row["predecessor_configuration_id"]) if row["predecessor_configuration_id"] else None,
            UUID(row["formula_definition_id"]), row["formula_definition_version"],
            row["symbol"], CycleTargetDefinitionStatus(row["status"]),
            row["minimum_fraction_input_text"], CycleTargetFloatEvidence(row["minimum_fraction_input_text"], row["minimum_fraction"], row["minimum_fraction_hex"]),
            row["neutral_fraction_input_text"], CycleTargetFloatEvidence(row["neutral_fraction_input_text"], row["neutral_fraction"], row["neutral_fraction_hex"]),
            row["maximum_fraction_input_text"], CycleTargetFloatEvidence(row["maximum_fraction_input_text"], row["maximum_fraction"], row["maximum_fraction_hex"]),
            row["linear_slope_input_text"], CycleTargetFloatEvidence(row["linear_slope_input_text"], row["linear_slope"], row["linear_slope_hex"]),
            row["acceleration_start_input_text"], CycleTargetFloatEvidence(row["acceleration_start_input_text"], row["acceleration_start"], row["acceleration_start_hex"]),
            row["saturation_input_text"], CycleTargetFloatEvidence(row["saturation_input_text"], row["saturation"], row["saturation_hex"]),
            row["constraint_fingerprint"], _dt(row["created_at_utc"]), row["created_by"],
            row["reason"], row["software_version"], row["source_revision"], row["worktree_state"],
            bool(row["execution_allowed"]), bool(row["live_allowed"]), row["schema_version"],
        )

    def _load_result(self, connection, result_id):
        row = connection.execute(
            "SELECT * FROM cycle_target_results WHERE result_id = ?", (str(result_id),)
        ).fetchone()
        if row is None:
            return None
        trace_row = connection.execute(
            "SELECT * FROM cycle_target_calculation_traces WHERE result_id = ?", (str(result_id),)
        ).fetchone()
        link_rows = connection.execute(
            "SELECT * FROM cycle_target_source_links WHERE result_id = ? ORDER BY ordinal",
            (str(result_id),),
        ).fetchall()
        source = ReversalObservationTargetInput(
            UUID(row["source_result_id"]), UUID(row["source_run_id"]), UUID(row["source_stage_id"]),
            UUID(row["source_step_id"]), row["source_step_ordinal"], UUID(row["source_definition_id"]),
            row["source_definition_version"], row["source_component_id"], row["source_component_version"],
            row["source_calculation_fingerprint"], UUID(row["source_profile_result_id"]),
            UUID(row["source_profile_run_id"]), UUID(row["source_parent_run_id"]),
            UUID(row["source_market_evidence_id"]), row["source_market_fingerprint"], row["symbol"],
            date.fromisoformat(row["session"]), _dt(row["official_close_utc"]), _dt(row["available_at_utc"]),
            CycleTargetDirection(row["direction_at_open"]), CycleTargetDirection(row["direction_at_close"]),
            CycleTargetCandidateState(row["candidate_state_after_close"]),
            CycleTargetAttribution(row["attribution"]),
            tuple(UUID(item) for item in json.loads(row["event_ids_text"])),
            date.fromisoformat(row["cycle_reference_session"]),
            CycleTargetPriceEvidence(row["cycle_reference_price_input_text"], CycleTargetFloatEvidence(
                row["cycle_reference_price_input_text"], row["cycle_reference_price"], row["cycle_reference_price_hex"]
            )),
            CycleTargetPriceEvidence(row["split_close_input_text"], CycleTargetFloatEvidence(
                row["split_close_input_text"], row["split_close"], row["split_close_hex"]
            )),
            CycleTargetFloatEvidence(
                row["profile_log_scale_text"], row["profile_log_scale"], row["profile_log_scale_hex"]
            ),
            tuple(json.loads(row["source_warnings_text"])),
        )
        trace = CycleTargetCalculationTrace(
            _float(trace_row, "log_price_ratio"), _float(trace_row, "normalized_state"),
            _float(trace_row, "absolute_state"), bool(trace_row["direction_matches"]),
            bool(trace_row["confirmation_forces_linear"]), bool(trace_row["counter_move_forces_linear"]),
            bool(trace_row["within_linear_boundary"]), bool(trace_row["at_or_beyond_saturation"]),
            _float(trace_row, "linear_raw_fraction"), _float(trace_row, "linear_bounded_fraction"),
            _optional_float(trace_row, "boundary_fraction"), _optional_float(trace_row, "headroom"),
            _optional_float(trace_row, "rho"), _optional_float(trace_row, "beta"),
            trace_row["solver_iterations"], _optional_float(trace_row, "normalized_acceleration_progress"),
            _optional_float(trace_row, "exponential_progress"),
            _float(trace_row, "pre_bound_target_fraction"), _float(trace_row, "final_target_fraction"),
            trace_row["exact_decimal_fraction_text"], trace_row["solver_id"],
            _float(trace_row, "solver_tolerance"), trace_row["solver_max_iterations"],
            tuple(json.loads(trace_row["formula_trace_text"])),
        )
        links = tuple(CycleTargetSourceLink(
            item["ordinal"], item["source_type"], item["source_id"], item["source_version"],
            item["source_fingerprint"], UUID(item["source_run_id"]) if item["source_run_id"] else None,
        ) for item in link_rows)
        return CycleTargetPositionResult(
            UUID(row["result_id"]), row["calculation_fingerprint"], UUID(row["operation_id"]),
            UUID(row["run_id"]), UUID(row["state_stage_id"]), UUID(row["target_stage_id"]),
            UUID(row["formula_definition_id"]), row["formula_definition_version"],
            UUID(row["configuration_id"]), row["configuration_version"], source,
            CycleTargetRegion(row["region"]), CycleTargetResultStatus(row["status"]),
            Decimal(row["target_fraction_text"]), Decimal(row["research_capital_basis_usd_text"]),
            Decimal(row["current_position_value_usd_text"]), Decimal(row["target_position_value_usd_text"]),
            Decimal(row["adjustment_value_usd_text"]), TargetPositionAdjustmentDirection(row["adjustment_direction"]),
            trace, links, tuple(json.loads(row["warnings_text"])), row["explanation"],
            _dt(row["created_at_utc"]), row["created_by"], row["reason"], row["software_version"],
            row["source_revision"], row["worktree_state"], bool(row["execution_allowed"]),
            bool(row["live_allowed"]), row["schema_version"],
        )

    @staticmethod
    def _operation(row, result):
        return CycleTargetOperation(
            UUID(row["attempt_id"]), UUID(row["operation_id"]), UUID(row["run_id"]),
            UUID(row["state_stage_id"]) if row["state_stage_id"] else None,
            UUID(row["target_stage_id"]) if row["target_stage_id"] else None,
            CycleTargetOperationType(row["operation_type"]), row["command_fingerprint"],
            CycleTargetOperationStatus(row["status"]), _dt(row["requested_at_utc"]),
            _dt(row["completed_at_utc"]), row["session_id"], row["request_id"],
            row["created_by"], row["reason"],
            UUID(row["requested_formula_definition_id"]) if row["requested_formula_definition_id"] else None,
            row["requested_formula_definition_version"],
            UUID(row["requested_configuration_id"]) if row["requested_configuration_id"] else None,
            row["requested_configuration_version"],
            UUID(row["requested_source_result_id"]) if row["requested_source_result_id"] else None,
            UUID(row["requested_source_step_id"]) if row["requested_source_step_id"] else None,
            UUID(row["requested_source_run_id"]) if row["requested_source_run_id"] else None,
            row["requested_symbol"], tuple(tuple(item) for item in json.loads(row["input_values_text"])),
            UUID(row["resolved_formula_definition_id"]) if row["resolved_formula_definition_id"] else None,
            row["resolved_formula_definition_version"],
            UUID(row["resolved_configuration_id"]) if row["resolved_configuration_id"] else None,
            row["resolved_configuration_version"], result, tuple(json.loads(row["warnings_text"])),
            row["error_code"], row["error_summary"], row["software_version"],
            row["source_revision"], row["worktree_state"], bool(row["execution_allowed"]),
            bool(row["live_allowed"]), row["schema_version"],
        )


__all__ = ["SQLiteCycleTargetPositionStore"]
