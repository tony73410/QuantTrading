"""Central SQLite adapter for disabled P23-2B mathematical-cycle state."""

from __future__ import annotations

from contextlib import closing
from datetime import date, datetime
import json
from pathlib import Path
from uuid import UUID

from quant_trading.asset_state.mathematical_cycle_interfaces import MathematicalCycleStateStore
from quant_trading.asset_state.mathematical_cycle_models import (
    MathematicalCycleDefinitionStatus,
    MathematicalCycleMaterialization,
    MathematicalCycleOperationStatus,
    MathematicalCycleOperationType,
    MathematicalCycleQuery,
    MathematicalCycleSnapshot,
    MathematicalCycleSourceLink,
    MathematicalCycleStateDefinition,
    MathematicalCycleStateOperation,
    MathematicalCycleStream,
    MathematicalCycleStreamDetail,
    MathematicalCycleStreamStatus,
    MathematicalCycleTransitionEvent,
    MathematicalCycleTransitionType,
    MathematicalDirection,
    MathematicalNumberEvidence,
    MathematicalPriceEvidence,
    MathematicalTradingCycle,
    MathematicalTradingCycleStatus,
)

from .sqlite_database import CentralSQLiteDatabase


def _iso(value: datetime) -> str: return value.isoformat(timespec="microseconds")
def _dt(value: str) -> datetime: return datetime.fromisoformat(value)
def _date(value: str): return date.fromisoformat(value)
def _json(value) -> str: return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
def _number(row, prefix): return MathematicalNumberEvidence(float(row[f"{prefix}_value"]), row[f"{prefix}_hex"])
def _price(row, prefix): return MathematicalPriceEvidence(row[f"{prefix}_text"], _number(row, prefix))
def _price_values(value): return (value.decimal_text, value.value.value, value.value.ieee_hex)


class SQLiteMathematicalCycleStateStore(MathematicalCycleStateStore):
    def __init__(self, database_path: Path | str) -> None:
        self._database = CentralSQLiteDatabase(database_path)

    def initialize(self) -> None:
        self._database.initialize()

    def get_definition(self, definition_id: UUID):
        with closing(self._database.connect()) as connection:
            row = connection.execute("SELECT * FROM mathematical_cycle_state_definitions WHERE definition_id=?", (str(definition_id),)).fetchone()
        return self._load_definition(row) if row else None

    def list_definitions(self, *, include_archived: bool = False, limit: int = 500):
        if not 1 <= limit <= 500: raise ValueError("definition query limit must be 1 to 500")
        where = "" if include_archived else " WHERE status='disabled'"
        with closing(self._database.connect()) as connection:
            rows = connection.execute("SELECT * FROM mathematical_cycle_state_definitions" + where + " ORDER BY created_at_utc DESC LIMIT ?", (limit,)).fetchall()
        return tuple(self._load_definition(row) for row in rows)

    def get_first_operation(self, operation_id: UUID):
        with closing(self._database.connect()) as connection:
            row = connection.execute("SELECT * FROM mathematical_cycle_state_operations WHERE operation_id=? ORDER BY requested_at_utc,attempt_id LIMIT 1", (str(operation_id),)).fetchone()
        return self._load_operation(row) if row else None

    def get_stream(self, stream_id: UUID):
        with closing(self._database.connect()) as connection:
            row = connection.execute("SELECT * FROM mathematical_cycle_streams WHERE stream_id=?", (str(stream_id),)).fetchone()
        return self._load_stream(row) if row else None

    def get_stream_detail(self, stream_id: UUID):
        with closing(self._database.connect()) as connection:
            stream_row = connection.execute("SELECT * FROM mathematical_cycle_streams WHERE stream_id=?", (str(stream_id),)).fetchone()
            if stream_row is None: return None
            cycles = tuple(self._load_cycle(row) for row in connection.execute("SELECT * FROM mathematical_trading_cycles WHERE stream_id=? ORDER BY ordinal", (str(stream_id),)))
            snapshots = tuple(self._load_snapshot(row) for row in connection.execute("SELECT * FROM mathematical_cycle_snapshots WHERE stream_id=? ORDER BY sequence", (str(stream_id),)))
            transitions = tuple(self._load_transition(row) for row in connection.execute("SELECT * FROM mathematical_cycle_transition_events WHERE stream_id=? ORDER BY sequence", (str(stream_id),)))
            links = tuple(self._load_link(row) for row in connection.execute("SELECT * FROM mathematical_cycle_source_links WHERE stream_id=? ORDER BY sequence", (str(stream_id),)))
        return MathematicalCycleStreamDetail(self._load_stream(stream_row), cycles, snapshots, transitions, links)

    def list_streams(self, query: MathematicalCycleQuery = MathematicalCycleQuery()):
        clauses, values = [], []
        if query.symbol: clauses.append("symbol=?"); values.append(query.symbol)
        if query.stream_id: clauses.append("stream_id=?"); values.append(str(query.stream_id))
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        values.append(query.limit)
        with closing(self._database.connect()) as connection:
            rows = connection.execute("SELECT * FROM mathematical_cycle_streams" + where + " ORDER BY created_at_utc DESC,stream_id DESC LIMIT ?", values).fetchall()
        return tuple(self._load_stream(row) for row in rows)

    def list_operations(self, query: MathematicalCycleQuery = MathematicalCycleQuery()):
        clauses, values = [], []
        if query.stream_id: clauses.append("stream_id=?"); values.append(str(query.stream_id))
        if query.status: clauses.append("status=?"); values.append(query.status.value)
        if query.symbol:
            clauses.append("stream_id IN (SELECT stream_id FROM mathematical_cycle_streams WHERE symbol=?)")
            values.append(query.symbol)
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        values.append(query.limit)
        with closing(self._database.connect()) as connection:
            rows = connection.execute("SELECT * FROM mathematical_cycle_state_operations" + where + " ORDER BY completed_at_utc DESC,attempt_id DESC LIMIT ?", values).fetchall()
        return tuple(self._load_operation(row) for row in rows)

    def save_definition(self, definition, operation) -> None:
        with closing(self._database.connect()) as connection:
            with connection:
                connection.execute("INSERT INTO mathematical_cycle_state_definitions VALUES (" + ",".join("?" for _ in range(20)) + ")", (
                    str(definition.definition_id), definition.definition_version,
                    str(definition.predecessor_definition_id) if definition.predecessor_definition_id else None,
                    definition.status.value, definition.component_id, definition.component_version,
                    definition.source_policy, definition.confirmation_state_policy,
                    definition.activation_policy, definition.reference_policy,
                    definition.attribution_policy, _iso(definition.created_at_utc),
                    definition.created_by, definition.reason, definition.software_version,
                    definition.source_revision, definition.worktree_state,
                    int(definition.execution_allowed), int(definition.live_allowed),
                    definition.schema_version,
                ))
                self._insert_operation(connection, operation)

    def save_operation(self, operation) -> None:
        with closing(self._database.connect()) as connection:
            with connection: self._insert_operation(connection, operation)

    def save_materialization(self, operation, materialization, *, prior_detail) -> None:
        with closing(self._database.connect()) as connection:
            with connection:
                current = connection.execute("SELECT latest_snapshot_id,latest_sequence FROM mathematical_cycle_streams WHERE stream_id=?", (str(materialization.stream.stream_id),)).fetchone()
                if prior_detail is None:
                    if current is not None: raise ValueError("mathematical-cycle stream already exists")
                    self._insert_stream(connection, materialization.stream)
                    prior_cycle_count = prior_snapshot_count = prior_transition_count = prior_link_count = 0
                else:
                    if current is None or current["latest_snapshot_id"] != str(prior_detail.stream.latest_snapshot_id) or int(current["latest_sequence"]) != prior_detail.stream.latest_sequence:
                        raise ValueError("mathematical-cycle stream cursor changed concurrently")
                    connection.execute("UPDATE mathematical_cycle_streams SET latest_source_result_id=?,latest_source_run_id=?,latest_snapshot_id=?,latest_sequence=? WHERE stream_id=?", (
                        str(materialization.stream.latest_source_result_id), str(materialization.stream.latest_source_run_id),
                        str(materialization.stream.latest_snapshot_id), materialization.stream.latest_sequence,
                        str(materialization.stream.stream_id),
                    ))
                    prior_cycle_count, prior_snapshot_count = len(prior_detail.cycles), len(prior_detail.snapshots)
                    prior_transition_count, prior_link_count = len(prior_detail.transitions), len(prior_detail.source_links)

                for index, cycle in enumerate(materialization.cycles):
                    if index < prior_cycle_count:
                        old = prior_detail.cycles[index]
                        if old == cycle: continue
                        if old.status is not MathematicalTradingCycleStatus.OPEN or cycle.status is not MathematicalTradingCycleStatus.CLOSED or old.cycle_id != cycle.cycle_id:
                            raise ValueError("stored cycle changed incompatibly")
                        connection.execute("UPDATE mathematical_trading_cycles SET status='closed',confirmed_close_session=?,confirmed_close_utc=? WHERE cycle_id=? AND status='open'", (cycle.confirmed_close_session.isoformat(), _iso(cycle.confirmed_close_utc), str(cycle.cycle_id)))
                    else:
                        self._insert_cycle(connection, cycle)
                for snapshot in materialization.snapshots[prior_snapshot_count:]: self._insert_snapshot(connection, snapshot)
                for transition in materialization.transitions[prior_transition_count:]: self._insert_transition(connection, transition)
                for link in materialization.source_links[prior_link_count:]: self._insert_link(connection, link)
                self._insert_operation(connection, operation)

    @staticmethod
    def _insert_stream(connection, item):
        values = (str(item.stream_id), item.stream_name, item.symbol, str(item.definition_id), item.definition_version, item.status.value, str(item.original_source_result_id), str(item.original_source_run_id), str(item.source_definition_id), item.source_definition_version, str(item.profile_result_id), str(item.profile_run_id), str(item.profile_definition_id), item.profile_definition_version, item.seed_session.isoformat(), item.seed_observation_id, *_price_values(item.seed_price), item.initial_direction.value, item.calendar_fingerprint, str(item.latest_source_result_id), str(item.latest_source_run_id), str(item.latest_snapshot_id), item.latest_sequence, _iso(item.created_at_utc), item.created_by, item.reason, int(item.execution_allowed), int(item.live_allowed), item.schema_version)
        connection.execute("INSERT INTO mathematical_cycle_streams VALUES (" + ",".join("?" for _ in values) + ")", values)

    @staticmethod
    def _insert_cycle(connection, item):
        values = (str(item.cycle_id), str(item.stream_id), item.ordinal, item.direction.value, item.operational_start_session.isoformat(), _iso(item.operational_start_utc), item.reference_session.isoformat(), *_price_values(item.reference_price), str(item.predecessor_cycle_id) if item.predecessor_cycle_id else None, item.status.value, item.confirmed_close_session.isoformat() if item.confirmed_close_session else None, _iso(item.confirmed_close_utc) if item.confirmed_close_utc else None, str(item.activation_transition_id) if item.activation_transition_id else None, int(item.execution_allowed), int(item.live_allowed), item.schema_version)
        connection.execute("INSERT INTO mathematical_trading_cycles VALUES (" + ",".join("?" for _ in values) + ")", values)

    @staticmethod
    def _insert_snapshot(connection, item):
        values = (str(item.snapshot_id), str(item.stream_id), str(item.cycle_id), item.sequence, item.session.isoformat(), item.direction_at_open.value, item.direction_at_close.value, item.reference_session.isoformat(), *_price_values(item.reference_price), *_price_values(item.running_extreme_before), *_price_values(item.running_extreme_after), item.candidate_state, item.threshold.value, item.threshold.ieee_hex, item.directional_log_distance.value, item.directional_log_distance.ieee_hex, item.attribution_at_recording, item.cumulative_new_cycle_movement.value, item.cumulative_new_cycle_movement.ieee_hex, str(item.source_result_id), str(item.source_run_id), str(item.source_step_id), item.source_observation_id, str(item.predecessor_snapshot_id) if item.predecessor_snapshot_id else None, _iso(item.created_at_utc), item.schema_version)
        connection.execute("INSERT INTO mathematical_cycle_snapshots VALUES (" + ",".join("?" for _ in values) + ")", values)

    @staticmethod
    def _insert_transition(connection, item):
        values = (str(item.transition_id), str(item.stream_id), item.sequence, item.session.isoformat(), item.event_type.value, str(item.old_cycle_id) if item.old_cycle_id else None, str(item.new_cycle_id) if item.new_cycle_id else None, item.old_direction.value, item.new_direction.value if item.new_direction else None, item.origin_session.isoformat(), *_price_values(item.origin_price), str(item.source_result_id), str(item.source_run_id), str(item.source_event_id) if item.source_event_id else None, str(item.source_day1_step_id) if item.source_day1_step_id else None, str(item.source_day2_step_id) if item.source_day2_step_id else None, item.activation_effective_session.isoformat() if item.activation_effective_session else None, str(item.related_snapshot_id) if item.related_snapshot_id else None, item.attribution_from, item.attribution_to, item.reason, _iso(item.created_at_utc), item.schema_version)
        connection.execute("INSERT INTO mathematical_cycle_transition_events VALUES (" + ",".join("?" for _ in values) + ")", values)

    @staticmethod
    def _insert_link(connection, item):
        values = (str(item.link_id), str(item.stream_id), str(item.snapshot_id), item.sequence, str(item.source_result_id), str(item.source_run_id), str(item.source_step_id), item.source_observation_id, item.stable_semantic_fingerprint, item.recorded_attribution, _iso(item.created_at_utc), item.schema_version)
        connection.execute("INSERT INTO mathematical_cycle_source_links VALUES (" + ",".join("?" for _ in values) + ")", values)

    @staticmethod
    def _insert_operation(connection, item):
        values = (str(item.attempt_id), str(item.operation_id), str(item.run_id), str(item.stage_id), item.operation_type.value, item.command_fingerprint, str(item.definition_id) if item.definition_id else None, item.definition_version, str(item.stream_id) if item.stream_id else None, str(item.requested_source_result_id) if item.requested_source_result_id else None, str(item.requested_source_run_id) if item.requested_source_run_id else None, str(item.expected_latest_snapshot_id) if item.expected_latest_snapshot_id else None, item.status.value, str(item.latest_snapshot_id) if item.latest_snapshot_id else None, _iso(item.requested_at_utc), _iso(item.completed_at_utc), item.session_id, item.request_id, item.created_by, item.reason, item.software_version, item.source_revision, item.worktree_state, _json(item.warnings), item.error_code, item.error_summary, int(item.execution_allowed), int(item.live_allowed), item.schema_version)
        connection.execute("INSERT INTO mathematical_cycle_state_operations VALUES (" + ",".join("?" for _ in values) + ")", values)

    @staticmethod
    def _load_definition(row):
        return MathematicalCycleStateDefinition(UUID(row["definition_id"]), int(row["definition_version"]), UUID(row["predecessor_definition_id"]) if row["predecessor_definition_id"] else None, MathematicalCycleDefinitionStatus(row["status"]), row["component_id"], row["component_version"], row["source_policy"], row["confirmation_state_policy"], row["activation_policy"], row["reference_policy"], row["attribution_policy"], _dt(row["created_at_utc"]), row["created_by"], row["reason"], row["software_version"], row["source_revision"], row["worktree_state"], bool(row["execution_allowed"]), bool(row["live_allowed"]), int(row["schema_version"]))

    @staticmethod
    def _load_stream(row):
        return MathematicalCycleStream(UUID(row["stream_id"]), row["stream_name"], row["symbol"], UUID(row["definition_id"]), int(row["definition_version"]), MathematicalCycleStreamStatus(row["status"]), UUID(row["original_source_result_id"]), UUID(row["original_source_run_id"]), UUID(row["source_definition_id"]), int(row["source_definition_version"]), UUID(row["profile_result_id"]), UUID(row["profile_run_id"]), UUID(row["profile_definition_id"]), int(row["profile_definition_version"]), _date(row["seed_session"]), row["seed_observation_id"], _price(row, "seed_price"), MathematicalDirection(row["initial_direction"]), row["calendar_fingerprint"], UUID(row["latest_source_result_id"]), UUID(row["latest_source_run_id"]), UUID(row["latest_snapshot_id"]), int(row["latest_sequence"]), _dt(row["created_at_utc"]), row["created_by"], row["reason"], bool(row["execution_allowed"]), bool(row["live_allowed"]), int(row["schema_version"]))

    @staticmethod
    def _load_cycle(row):
        return MathematicalTradingCycle(UUID(row["cycle_id"]), UUID(row["stream_id"]), int(row["ordinal"]), MathematicalDirection(row["direction"]), _date(row["operational_start_session"]), _dt(row["operational_start_utc"]), _date(row["reference_session"]), _price(row, "reference_price"), UUID(row["predecessor_cycle_id"]) if row["predecessor_cycle_id"] else None, MathematicalTradingCycleStatus(row["status"]), _date(row["confirmed_close_session"]) if row["confirmed_close_session"] else None, _dt(row["confirmed_close_utc"]) if row["confirmed_close_utc"] else None, UUID(row["activation_transition_id"]) if row["activation_transition_id"] else None, bool(row["execution_allowed"]), bool(row["live_allowed"]), int(row["schema_version"]))

    @staticmethod
    def _load_snapshot(row):
        return MathematicalCycleSnapshot(UUID(row["snapshot_id"]), UUID(row["stream_id"]), UUID(row["cycle_id"]), int(row["sequence"]), _date(row["session"]), MathematicalDirection(row["direction_at_open"]), MathematicalDirection(row["direction_at_close"]), _date(row["reference_session"]), _price(row, "reference_price"), _price(row, "running_extreme_before"), _price(row, "running_extreme_after"), row["candidate_state"], _number(row, "threshold"), _number(row, "directional_log_distance"), row["attribution_at_recording"], _number(row, "cumulative_new_cycle_movement"), UUID(row["source_result_id"]), UUID(row["source_run_id"]), UUID(row["source_step_id"]), row["source_observation_id"], UUID(row["predecessor_snapshot_id"]) if row["predecessor_snapshot_id"] else None, _dt(row["created_at_utc"]), int(row["schema_version"]))

    @staticmethod
    def _load_transition(row):
        return MathematicalCycleTransitionEvent(UUID(row["transition_id"]), UUID(row["stream_id"]), int(row["sequence"]), _date(row["session"]), MathematicalCycleTransitionType(row["event_type"]), UUID(row["old_cycle_id"]) if row["old_cycle_id"] else None, UUID(row["new_cycle_id"]) if row["new_cycle_id"] else None, MathematicalDirection(row["old_direction"]), MathematicalDirection(row["new_direction"]) if row["new_direction"] else None, _date(row["origin_session"]), _price(row, "origin_price"), UUID(row["source_result_id"]), UUID(row["source_run_id"]), UUID(row["source_event_id"]) if row["source_event_id"] else None, UUID(row["source_day1_step_id"]) if row["source_day1_step_id"] else None, UUID(row["source_day2_step_id"]) if row["source_day2_step_id"] else None, _date(row["activation_effective_session"]) if row["activation_effective_session"] else None, UUID(row["related_snapshot_id"]) if row["related_snapshot_id"] else None, row["attribution_from"], row["attribution_to"], row["reason"], _dt(row["created_at_utc"]), int(row["schema_version"]))

    @staticmethod
    def _load_link(row):
        return MathematicalCycleSourceLink(UUID(row["link_id"]), UUID(row["stream_id"]), UUID(row["snapshot_id"]), int(row["sequence"]), UUID(row["source_result_id"]), UUID(row["source_run_id"]), UUID(row["source_step_id"]), row["source_observation_id"], row["stable_semantic_fingerprint"], row["recorded_attribution"], _dt(row["created_at_utc"]), int(row["schema_version"]))

    @staticmethod
    def _load_operation(row):
        return MathematicalCycleStateOperation(UUID(row["attempt_id"]), UUID(row["operation_id"]), UUID(row["run_id"]), UUID(row["stage_id"]), MathematicalCycleOperationType(row["operation_type"]), row["command_fingerprint"], UUID(row["definition_id"]) if row["definition_id"] else None, int(row["definition_version"]) if row["definition_version"] else None, UUID(row["stream_id"]) if row["stream_id"] else None, UUID(row["requested_source_result_id"]) if row["requested_source_result_id"] else None, UUID(row["requested_source_run_id"]) if row["requested_source_run_id"] else None, UUID(row["expected_latest_snapshot_id"]) if row["expected_latest_snapshot_id"] else None, MathematicalCycleOperationStatus(row["status"]), UUID(row["latest_snapshot_id"]) if row["latest_snapshot_id"] else None, _dt(row["requested_at_utc"]), _dt(row["completed_at_utc"]), row["session_id"], row["request_id"], row["created_by"], row["reason"], row["software_version"], row["source_revision"], row["worktree_state"], tuple(json.loads(row["warnings_json"])), row["error_code"], row["error_summary"], bool(row["execution_allowed"]), bool(row["live_allowed"]), int(row["schema_version"]))


__all__ = ["SQLiteMathematicalCycleStateStore"]
