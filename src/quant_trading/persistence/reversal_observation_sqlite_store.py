"""Central SQLite adapter for immutable P23-2 research evidence."""

from __future__ import annotations

from contextlib import closing
from datetime import date, datetime
import json
from pathlib import Path
from uuid import UUID

from quant_trading.asset_state.reversal_observation_interfaces import ReversalObservationStore
from quant_trading.asset_state.reversal_observation_models import (
    ReversalAttribution,
    ReversalCandidateState,
    ReversalDirection,
    ReversalEventType,
    ReversalFloatEvidence,
    ReversalObservationDailyStep,
    ReversalObservationDefinition,
    ReversalObservationDefinitionStatus,
    ReversalObservationEvent,
    ReversalObservationOperation,
    ReversalObservationOperationStatus,
    ReversalObservationOperationType,
    ReversalObservationPriceObservation,
    ReversalObservationProfileEvidence,
    ReversalObservationQuery,
    ReversalObservationResult,
    ReversalObservationResultStatus,
    ReversalObservationSourceLink,
    ReversalPriceEvidence,
)

from .sqlite_database import CentralSQLiteDatabase


def _iso(value: datetime) -> str:
    return value.isoformat(timespec="microseconds")


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _json(value) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _float(row, prefix: str) -> ReversalFloatEvidence:
    return ReversalFloatEvidence(float(row[prefix]), row[f"{prefix}_hex"])


def _price(row, prefix: str) -> ReversalPriceEvidence:
    return ReversalPriceEvidence(row[f"{prefix}_text"], _float(row, prefix))


def _price_values(value: ReversalPriceEvidence) -> tuple[object, ...]:
    return (value.decimal_text, value.value.value, value.value.ieee_hex)


def _float_values(value: ReversalFloatEvidence) -> tuple[object, ...]:
    return (value.value, value.ieee_hex)


class SQLiteReversalObservationStore(ReversalObservationStore):
    def __init__(self, database_path: Path | str) -> None:
        self._database = CentralSQLiteDatabase(database_path)

    def initialize(self) -> None:
        self._database.initialize()

    def get_definition(self, definition_id: UUID) -> ReversalObservationDefinition | None:
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                "SELECT * FROM reversal_observation_definitions WHERE definition_id = ?",
                (str(definition_id),),
            ).fetchone()
        return self._load_definition(row) if row else None

    def list_definitions(
        self, *, include_archived: bool = False, limit: int = 500
    ) -> tuple[ReversalObservationDefinition, ...]:
        if not 1 <= limit <= 500:
            raise ValueError("definition query limit must be 1 to 500")
        where = "" if include_archived else " WHERE status = 'disabled'"
        with closing(self._database.connect()) as connection:
            rows = connection.execute(
                "SELECT * FROM reversal_observation_definitions" + where
                + " ORDER BY created_at_utc DESC, definition_version DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return tuple(self._load_definition(row) for row in rows)

    def get_first_operation(self, operation_id: UUID) -> ReversalObservationOperation | None:
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                """SELECT attempt_id FROM reversal_observation_operation_attempts
                WHERE operation_id = ? ORDER BY requested_at_utc, attempt_id LIMIT 1""",
                (str(operation_id),),
            ).fetchone()
        return self.get_operation(UUID(row["attempt_id"])) if row else None

    def get_result_by_fingerprint(self, fingerprint: str) -> ReversalObservationResult | None:
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                "SELECT result_id FROM reversal_observation_results WHERE calculation_fingerprint = ?",
                (fingerprint,),
            ).fetchone()
        return self.get_result(UUID(row["result_id"])) if row else None

    def save_definition(
        self,
        definition: ReversalObservationDefinition,
        operation: ReversalObservationOperation,
    ) -> None:
        with closing(self._database.connect()) as connection:
            with connection:
                self._insert_definition(connection, definition)
                self._insert_operation(connection, operation)

    def save_operation(self, operation: ReversalObservationOperation) -> None:
        with closing(self._database.connect()) as connection:
            with connection:
                if operation.result is not None:
                    row = connection.execute(
                        "SELECT calculation_fingerprint FROM reversal_observation_results WHERE result_id = ?",
                        (str(operation.result.result_id),),
                    ).fetchone()
                    if row is None:
                        self._insert_result(connection, operation.result)
                    elif row["calculation_fingerprint"] != operation.result.calculation_fingerprint:
                        raise ValueError("stored P28 result identity conflicts")
                self._insert_operation(connection, operation)

    def list_operations(
        self, query: ReversalObservationQuery = ReversalObservationQuery()
    ) -> tuple[ReversalObservationOperation, ...]:
        clauses: list[str] = []
        values: list[object] = []
        for value, column in (
            (query.operation_id, "o.operation_id"), (query.run_id, "o.run_id"),
            (query.result_id, "o.result_id"), (query.definition_id, "o.definition_id"),
            (query.profile_result_id, "o.requested_profile_result_id"),
        ):
            if value is not None:
                clauses.append(f"{column} = ?")
                values.append(str(value))
        if query.symbol:
            clauses.append("o.expected_symbol = ?")
            values.append(query.symbol)
        if query.status:
            clauses.append("o.status = ?")
            values.append(query.status.value)
        if query.initial_direction:
            clauses.append("r.initial_direction = ?")
            values.append(query.initial_direction.value)
        for selected, column in (
            (query.has_candidate, "r.candidate_count"),
            (query.has_confirmation, "r.confirmation_count"),
            (query.has_activation, "r.activation_count"),
        ):
            if selected is not None:
                clauses.append(f"COALESCE({column}, 0) {'>' if selected else '='} 0")
        if query.created_from_utc:
            clauses.append("o.completed_at_utc >= ?")
            values.append(_iso(query.created_from_utc))
        if query.created_to_utc:
            clauses.append("o.completed_at_utc <= ?")
            values.append(_iso(query.created_to_utc))
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        values.append(query.limit)
        with closing(self._database.connect()) as connection:
            rows = connection.execute(
                "SELECT o.attempt_id FROM reversal_observation_operation_attempts o "
                "LEFT JOIN reversal_observation_results r ON r.result_id = o.result_id"
                + where + " ORDER BY o.completed_at_utc DESC, o.attempt_id DESC LIMIT ?",
                values,
            ).fetchall()
        return tuple(self.get_operation(UUID(row["attempt_id"])) for row in rows)

    def get_operation(self, attempt_id: UUID) -> ReversalObservationOperation | None:
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                "SELECT * FROM reversal_observation_operation_attempts WHERE attempt_id = ?",
                (str(attempt_id),),
            ).fetchone()
            if row is None:
                return None
            result = self._load_result(connection, UUID(row["result_id"])) if row["result_id"] else None
        return ReversalObservationOperation(
            attempt_id=UUID(row["attempt_id"]), operation_id=UUID(row["operation_id"]),
            run_id=UUID(row["run_id"]), state_stage_id=UUID(row["state_stage_id"]),
            operation_type=ReversalObservationOperationType(row["operation_type"]),
            command_fingerprint=row["command_fingerprint"],
            definition_id=UUID(row["definition_id"]) if row["definition_id"] else None,
            definition_version=int(row["definition_version"]) if row["definition_version"] else None,
            profile_result_id=(UUID(row["requested_profile_result_id"])
                               if row["requested_profile_result_id"] else None),
            expected_symbol=row["expected_symbol"],
            status=ReversalObservationOperationStatus(row["status"]), result=result,
            requested_at_utc=_dt(row["requested_at_utc"]),
            completed_at_utc=_dt(row["completed_at_utc"]), session_id=row["session_id"],
            request_id=row["request_id"], created_by=row["created_by"], reason=row["reason"],
            software_version=row["software_version"], source_revision=row["source_revision"],
            worktree_state=row["worktree_state"],
            warnings=tuple(json.loads(row["warnings_text"])), error_code=row["error_code"],
            error_summary=row["error_summary"], execution_allowed=bool(row["execution_allowed"]),
            live_allowed=bool(row["live_allowed"]), schema_version=int(row["schema_version"]),
        )

    def get_result(self, result_id: UUID) -> ReversalObservationResult | None:
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                "SELECT 1 FROM reversal_observation_results WHERE result_id = ?",
                (str(result_id),),
            ).fetchone()
            return self._load_result(connection, result_id) if row else None

    @staticmethod
    def _insert_definition(connection, item: ReversalObservationDefinition) -> None:
        values = (
            str(item.definition_id), item.definition_version,
            str(item.predecessor_definition_id) if item.predecessor_definition_id else None,
            item.status.value, item.shared_multiplier_input_text,
            item.shared_multiplier.value, item.shared_multiplier.ieee_hex,
            item.component_id, item.component_version, item.threshold_formula,
            item.confirmation_sessions, item.equality_policy, item.activation_policy,
            item.confirmed_buffer_policy, item.cancelled_buffer_policy,
            item.source_time_policy, _iso(item.created_at_utc), item.created_by,
            item.reason, item.software_version, item.source_revision, item.worktree_state,
            int(item.execution_allowed), int(item.live_allowed), item.schema_version,
        )
        connection.execute(
            "INSERT INTO reversal_observation_definitions VALUES ("
            + ",".join("?" for _ in values) + ")", values,
        )

    @staticmethod
    def _load_definition(row) -> ReversalObservationDefinition:
        return ReversalObservationDefinition(
            UUID(row["definition_id"]), int(row["definition_version"]),
            UUID(row["predecessor_definition_id"]) if row["predecessor_definition_id"] else None,
            ReversalObservationDefinitionStatus(row["status"]),
            row["shared_multiplier_input_text"], _float(row, "shared_multiplier"),
            row["component_id"], row["component_version"], row["threshold_formula"],
            int(row["confirmation_sessions"]), row["equality_policy"],
            row["activation_policy"], row["confirmed_buffer_policy"],
            row["cancelled_buffer_policy"], row["source_time_policy"],
            _dt(row["created_at_utc"]), row["created_by"], row["reason"],
            row["software_version"], row["source_revision"], row["worktree_state"],
            bool(row["execution_allowed"]), bool(row["live_allowed"]), int(row["schema_version"]),
        )

    @staticmethod
    def _insert_operation(connection, item: ReversalObservationOperation) -> None:
        values = (
            str(item.attempt_id), str(item.operation_id), str(item.run_id),
            str(item.state_stage_id), item.operation_type.value, item.command_fingerprint,
            str(item.definition_id) if item.definition_id else None, item.definition_version,
            str(item.profile_result_id) if item.profile_result_id else None,
            item.expected_symbol, item.status.value,
            str(item.result.result_id) if item.result else None,
            _iso(item.requested_at_utc), _iso(item.completed_at_utc), item.session_id,
            item.request_id, item.created_by, item.reason, item.software_version,
            item.source_revision, item.worktree_state, _json(item.warnings), item.error_code,
            item.error_summary, int(item.execution_allowed), int(item.live_allowed),
            item.schema_version,
        )
        connection.execute(
            "INSERT INTO reversal_observation_operation_attempts VALUES ("
            + ",".join("?" for _ in values) + ")", values,
        )

    def _insert_result(self, connection, item: ReversalObservationResult) -> None:
        seed_observation = self._seed_for_result(item)
        profile = item.profile
        values = (
            str(item.result_id), item.calculation_fingerprint, str(item.definition_id),
            item.definition_version, str(profile.result_id), str(profile.result_run_id),
            str(profile.source_study_id), str(profile.source_parent_run_id),
            str(profile.source_definition_id), profile.source_definition_version,
            profile.component_id, profile.component_version, profile.calculation_fingerprint,
            profile.source_evaluation_end_session.isoformat(), _iso(profile.created_at_utc),
            profile.profile_log_scale.value, profile.profile_log_scale.ieee_hex,
            str(item.market_evidence_id), item.market_evidence_fingerprint, item.symbol,
            item.seed_session.isoformat(), seed_observation.observation_id,
            seed_observation.raw_source_id, seed_observation.split_source_id,
            _iso(seed_observation.official_close_utc), _iso(seed_observation.first_observed_at_utc),
            _iso(seed_observation.available_at_utc), *_price_values(seed_observation.raw_close),
            *_price_values(seed_observation.split_close), item.final_evaluation_session.isoformat(),
            item.observation_count, item.initial_direction.value, item.status.value,
            item.final_direction.value, item.final_cycle_reference_session.isoformat(),
            *_price_values(item.final_cycle_reference_price),
            *_price_values(item.final_running_extreme), item.final_candidate_state.value,
            item.candidate_count, item.cancellation_count, item.confirmation_count,
            item.activation_count, _json(item.formula_trace), _json(item.warnings),
            item.explanation, _iso(item.created_at_utc), item.software_version,
            item.source_revision, item.worktree_state, int(item.execution_allowed),
            int(item.live_allowed), item.schema_version,
        )
        connection.execute(
            "INSERT INTO reversal_observation_results VALUES ("
            + ",".join("?" for _ in values) + ")", values,
        )
        for step in item.daily_steps:
            self._insert_step(connection, step)
        for event in item.events:
            self._insert_event(connection, event)
        for link in item.source_links:
            connection.execute(
                "INSERT INTO reversal_observation_source_links VALUES (?,?,?,?,?,?)",
                (str(item.result_id), link.ordinal, link.source_type, link.source_id,
                 link.source_version, link.source_fingerprint),
            )

    @staticmethod
    def _seed_for_result(item: ReversalObservationResult) -> ReversalObservationPriceObservation:
        # The explicit seed is normalized into result columns and also retained as a source
        # link so reload/replay never guesses it from the first evaluated session.
        seed_link = next(
            (link for link in item.source_links if link.source_type == "seed_observation"), None
        )
        if seed_link is None:
            raise ValueError("P28 result is missing its explicit seed source link")
        payload = json.loads(seed_link.source_fingerprint or "{}")
        return ReversalObservationPriceObservation(
            seed_link.source_id, item.seed_session, _dt(payload["official_close_utc"]),
            _dt(payload["first_observed_at_utc"]), _dt(payload["available_at_utc"]),
            payload["raw_source_id"], payload["split_source_id"],
            ReversalPriceEvidence(payload["raw_close_text"], ReversalFloatEvidence(
                float.fromhex(payload["raw_close_hex"]), payload["raw_close_hex"]
            )),
            ReversalPriceEvidence(payload["split_close_text"], ReversalFloatEvidence(
                float.fromhex(payload["split_close_hex"]), payload["split_close_hex"]
            )),
        )

    @staticmethod
    def _insert_step(connection, item: ReversalObservationDailyStep) -> None:
        observation = item.observation
        candidate_values = (
            (item.candidate_origin_session.isoformat(), *_price_values(item.candidate_origin_price))
            if item.candidate_origin_price is not None else (None, None, None, None)
        )
        values = (
            str(item.result_id), item.ordinal, str(item.step_id), item.session.isoformat(),
            observation.observation_id, _iso(observation.official_close_utc),
            _iso(observation.first_observed_at_utc), _iso(observation.available_at_utc),
            observation.raw_source_id, observation.split_source_id,
            *_price_values(observation.raw_close), *_price_values(observation.split_close),
            item.direction_at_open.value, item.direction_at_close.value,
            item.cycle_reference_session.isoformat(), *_price_values(item.cycle_reference_price),
            *_price_values(item.running_extreme_before), *_price_values(item.running_extreme_after),
            *candidate_values, *_float_values(item.profile_log_scale),
            *_float_values(item.shared_multiplier), *_float_values(item.threshold),
            *_float_values(item.directional_log_distance), *_float_values(item.display_price_fraction),
            int(item.threshold_reached), item.candidate_state_after_close.value,
            *_float_values(item.prior_close_log_return), item.attribution.value,
            *_float_values(item.cumulative_new_cycle_movement),
            _json(tuple(str(value) for value in item.event_ids)), _json(item.warnings),
            _json(item.formula_trace), item.schema_version,
        )
        connection.execute(
            "INSERT INTO reversal_observation_daily_steps VALUES ("
            + ",".join("?" for _ in values) + ")", values,
        )

    @staticmethod
    def _insert_event(connection, item: ReversalObservationEvent) -> None:
        values = (
            str(item.result_id), item.ordinal, str(item.event_id), item.session.isoformat(),
            item.event_type.value, item.old_direction.value,
            item.new_direction.value if item.new_direction else None,
            item.origin_session.isoformat(), *_price_values(item.origin_price),
            *_float_values(item.threshold), str(item.profile_result_id), str(item.definition_id),
            str(item.candidate_day1_step_id) if item.candidate_day1_step_id else None,
            str(item.candidate_day2_step_id) if item.candidate_day2_step_id else None,
            item.activation_effective_session.isoformat() if item.activation_effective_session else None,
            _json(item.trigger_values), item.reason, item.schema_version,
        )
        connection.execute(
            "INSERT INTO reversal_observation_events VALUES ("
            + ",".join("?" for _ in values) + ")", values,
        )

    def _load_result(self, connection, result_id: UUID) -> ReversalObservationResult:
        row = connection.execute(
            "SELECT * FROM reversal_observation_results WHERE result_id = ?", (str(result_id),)
        ).fetchone()
        profile = ReversalObservationProfileEvidence(
            UUID(row["profile_result_id"]), UUID(row["profile_result_run_id"]),
            UUID(row["source_study_id"]), UUID(row["source_parent_run_id"]),
            UUID(row["source_definition_id"]), int(row["source_definition_version"]),
            row["symbol"], date.fromisoformat(row["profile_source_end_session"]),
            _dt(row["profile_created_at_utc"]), _float(row, "profile_log_scale"),
            row["profile_calculation_fingerprint"], row["profile_component_id"],
            row["profile_component_version"], True,
        )
        steps = tuple(
            self._load_step(item)
            for item in connection.execute(
                "SELECT * FROM reversal_observation_daily_steps WHERE result_id = ? ORDER BY ordinal",
                (str(result_id),),
            )
        )
        events = tuple(
            self._load_event(item)
            for item in connection.execute(
                "SELECT * FROM reversal_observation_events WHERE result_id = ? ORDER BY ordinal",
                (str(result_id),),
            )
        )
        links = tuple(
            ReversalObservationSourceLink(
                int(item["ordinal"]), item["source_type"], item["source_id"],
                item["source_version"], item["source_fingerprint"],
            )
            for item in connection.execute(
                "SELECT * FROM reversal_observation_source_links WHERE result_id = ? ORDER BY ordinal",
                (str(result_id),),
            )
        )
        result = ReversalObservationResult(
            UUID(row["result_id"]), row["calculation_fingerprint"], UUID(row["definition_id"]),
            int(row["definition_version"]), profile, UUID(row["market_evidence_id"]),
            row["market_evidence_fingerprint"], row["symbol"],
            date.fromisoformat(row["seed_session"]),
            date.fromisoformat(row["final_evaluation_session"]), int(row["observation_count"]),
            ReversalDirection(row["initial_direction"]), ReversalObservationResultStatus(row["status"]),
            ReversalDirection(row["final_direction"]),
            date.fromisoformat(row["final_cycle_reference_session"]),
            _price(row, "final_cycle_reference_price"), _price(row, "final_running_extreme"),
            ReversalCandidateState(row["final_candidate_state"]), int(row["candidate_count"]),
            int(row["cancellation_count"]), int(row["confirmation_count"]),
            int(row["activation_count"]), steps, events, links,
            tuple(json.loads(row["formula_trace_text"])), tuple(json.loads(row["warnings_text"])),
            row["explanation"], _dt(row["created_at_utc"]), row["software_version"],
            row["source_revision"], row["worktree_state"], bool(row["execution_allowed"]),
            bool(row["live_allowed"]), int(row["schema_version"]),
        )
        # Fail closed if normalized children no longer match the result identity.
        if any(step.result_id != result.result_id for step in result.daily_steps):
            raise ValueError("P28 daily-step identity mismatch")
        return result

    @staticmethod
    def _load_observation(row) -> ReversalObservationPriceObservation:
        return ReversalObservationPriceObservation(
            row["observation_id"], date.fromisoformat(row["session"]),
            _dt(row["official_close_utc"]), _dt(row["first_observed_at_utc"]),
            _dt(row["available_at_utc"]), row["raw_source_id"], row["split_source_id"],
            _price(row, "raw_close"), _price(row, "split_close"),
        )

    @classmethod
    def _load_step(cls, row) -> ReversalObservationDailyStep:
        candidate_price = (
            _price(row, "candidate_origin_price")
            if row["candidate_origin_price"] is not None else None
        )
        return ReversalObservationDailyStep(
            UUID(row["step_id"]), UUID(row["result_id"]), int(row["ordinal"]),
            date.fromisoformat(row["session"]), cls._load_observation(row),
            ReversalDirection(row["direction_at_open"]),
            ReversalDirection(row["direction_at_close"]),
            date.fromisoformat(row["cycle_reference_session"]),
            _price(row, "cycle_reference_price"), _price(row, "running_extreme_before"),
            _price(row, "running_extreme_after"),
            date.fromisoformat(row["candidate_origin_session"]) if row["candidate_origin_session"] else None,
            candidate_price, _float(row, "profile_log_scale"), _float(row, "shared_multiplier"),
            _float(row, "threshold"), _float(row, "directional_log_distance"),
            _float(row, "display_price_fraction"), bool(row["threshold_reached"]),
            ReversalCandidateState(row["candidate_state_after_close"]),
            _float(row, "prior_close_log_return"), ReversalAttribution(row["attribution"]),
            _float(row, "cumulative_new_cycle_movement"),
            tuple(UUID(value) for value in json.loads(row["event_ids_text"])),
            tuple(json.loads(row["warnings_text"])), tuple(json.loads(row["formula_trace_text"])),
            int(row["schema_version"]),
        )

    @staticmethod
    def _load_event(row) -> ReversalObservationEvent:
        return ReversalObservationEvent(
            UUID(row["event_id"]), UUID(row["result_id"]), int(row["ordinal"]),
            date.fromisoformat(row["session"]), ReversalEventType(row["event_type"]),
            ReversalDirection(row["old_direction"]),
            ReversalDirection(row["new_direction"]) if row["new_direction"] else None,
            date.fromisoformat(row["origin_session"]), _price(row, "origin_price"),
            _float(row, "threshold"), UUID(row["profile_result_id"]),
            UUID(row["definition_id"]),
            UUID(row["candidate_day1_step_id"]) if row["candidate_day1_step_id"] else None,
            UUID(row["candidate_day2_step_id"]) if row["candidate_day2_step_id"] else None,
            date.fromisoformat(row["activation_effective_session"])
            if row["activation_effective_session"] else None,
            tuple(tuple(value) for value in json.loads(row["trigger_values_text"])),
            row["reason"], int(row["schema_version"]),
        )


__all__ = ["SQLiteReversalObservationStore"]
