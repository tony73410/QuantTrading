"""Central SQLite adapter for disabled P23-1F profile evidence."""

from __future__ import annotations

import json
from contextlib import closing
from datetime import date, datetime
from pathlib import Path
from uuid import UUID

from quant_trading.factors.daily_volatility_profile_models import (
    DailyScaleAggregation,
    DailyVolatilityProfileDailyInput,
    DailyVolatilityProfileDefinition,
    DailyVolatilityProfileDefinitionStatus,
    DailyVolatilityProfileOperation,
    DailyVolatilityProfileQuery,
    DailyVolatilityProfileResult,
    DailyVolatilityProfileStatus,
    DailyVolatilityProfileWindowSummary,
    DailyVolatilityWindowInput,
    ProfileCategoryCount,
    ProfileDispersionMethod,
    ProfileHistoryAggregation,
    ProfilePriceBandMethod,
    ProfileSpectralEvidenceLabel,
    ProfileSpectralRole,
)
from quant_trading.factors.spectral_models import FloatEvidence

from .sqlite_database import CentralSQLiteDatabase


def _iso(value: datetime) -> str:
    return value.isoformat(timespec="microseconds")


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _json(value) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _pair(value: FloatEvidence | None) -> tuple[float | None, str | None]:
    return (None, None) if value is None else (value.value, value.ieee_hex)


def _float(row, name: str) -> FloatEvidence | None:
    if row[name] is None:
        return None
    evidence = FloatEvidence(float.fromhex(row[f"{name}_hex"]), row[f"{name}_hex"])
    if float(row[name]).hex() != evidence.ieee_hex and not (
        float(row[name]) == 0.0 and evidence.value == 0.0
    ):
        raise ValueError(f"stored {name} REAL/IEEE evidence conflicts")
    return evidence


def _category_json(values: tuple[ProfileCategoryCount, ...]) -> str:
    return _json([[item.category, item.count] for item in values])


def _categories(value: str) -> tuple[ProfileCategoryCount, ...]:
    return tuple(ProfileCategoryCount(str(item[0]), int(item[1])) for item in json.loads(value))


class SQLiteDailyVolatilityProfileStore:
    """Append and exactly reload P27 definitions, attempts and results."""

    def __init__(self, database_path: Path | str) -> None:
        self._database = CentralSQLiteDatabase(database_path)

    def initialize(self) -> None:
        self._database.initialize()

    def save_definition(self, definition: DailyVolatilityProfileDefinition) -> None:
        with closing(self._database.connect()) as connection:
            existing = connection.execute(
                "SELECT * FROM daily_volatility_profile_definitions WHERE definition_id = ?",
                (str(definition.definition_id),),
            ).fetchone()
            if existing is not None:
                loaded = self._load_definition(existing)
                if (
                    loaded.component_id != definition.component_id
                    or loaded.component_version != definition.component_version
                    or loaded.definition_version != definition.definition_version
                    or loaded.required_windows != definition.required_windows
                ):
                    raise ValueError("stored daily-volatility profile definition conflicts")
                return
            with connection:
                connection.execute(
                    """INSERT INTO daily_volatility_profile_definitions VALUES
                    (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    self._definition_values(definition),
                )

    def get_definition(self, definition_id: UUID) -> DailyVolatilityProfileDefinition | None:
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                "SELECT * FROM daily_volatility_profile_definitions WHERE definition_id = ?",
                (str(definition_id),),
            ).fetchone()
            return self._load_definition(row) if row is not None else None

    def get_first_operation(self, operation_id: UUID) -> DailyVolatilityProfileOperation | None:
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                """SELECT attempt_id FROM daily_volatility_profile_operation_attempts
                WHERE operation_id = ? ORDER BY requested_at_utc, attempt_id LIMIT 1""",
                (str(operation_id),),
            ).fetchone()
        return self.get_operation(UUID(row["attempt_id"])) if row else None

    def get_result_by_fingerprint(self, fingerprint: str) -> DailyVolatilityProfileResult | None:
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                "SELECT result_id FROM daily_volatility_profile_results WHERE calculation_fingerprint = ?",
                (fingerprint,),
            ).fetchone()
        return self.get_result(UUID(row["result_id"])) if row else None

    def save_operation(self, operation: DailyVolatilityProfileOperation) -> None:
        with closing(self._database.connect()) as connection:
            with connection:
                self._save_definition_if_missing(connection, operation.definition)
                if operation.result is not None:
                    existing = connection.execute(
                        "SELECT calculation_fingerprint FROM daily_volatility_profile_results WHERE result_id = ?",
                        (str(operation.result.result_id),),
                    ).fetchone()
                    if existing is None:
                        self._save_result(connection, operation.result)
                    elif existing["calculation_fingerprint"] != operation.result.calculation_fingerprint:
                        raise ValueError("stored profile result identity conflicts")
                values = (
                    str(operation.attempt_id), str(operation.operation_id), str(operation.run_id),
                    str(operation.factor_stage_id), operation.command_fingerprint,
                    str(operation.definition.definition_id),
                    str(operation.requested_source_study_id),
                    str(operation.requested_source_definition_id),
                    operation.requested_source_definition_version, operation.expected_symbol,
                    operation.status.value,
                    str(operation.result.result_id) if operation.result else None,
                    _iso(operation.requested_at_utc), _iso(operation.completed_at_utc),
                    operation.session_id, operation.request_id, operation.created_by,
                    operation.reason, operation.software_version, operation.source_revision,
                    operation.worktree_state, _json(operation.warnings), operation.error_code,
                    operation.error_summary, int(operation.execution_allowed),
                    int(operation.live_allowed), operation.schema_version,
                )
                connection.execute(
                    "INSERT INTO daily_volatility_profile_operation_attempts VALUES ("
                    + ",".join("?" for _ in values) + ")",
                    values,
                )

    def list_operations(
        self, query: DailyVolatilityProfileQuery = DailyVolatilityProfileQuery()
    ) -> tuple[DailyVolatilityProfileOperation, ...]:
        clauses: list[str] = []
        values: list[object] = []
        mappings = (
            (query.operation_id, "o.operation_id"),
            (query.run_id, "o.run_id"),
            (query.result_id, "o.result_id"),
            (query.definition_id, "o.definition_id"),
            (query.source_study_id, "o.requested_source_study_id"),
            (query.source_definition_id, "o.requested_source_definition_id"),
        )
        for value, column in mappings:
            if value is not None:
                clauses.append(f"{column} = ?")
                values.append(str(value))
        if query.symbol:
            clauses.append("o.expected_symbol = ?")
            values.append(query.symbol)
        if query.status:
            clauses.append("o.status = ?")
            values.append(query.status.value)
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
                "SELECT o.attempt_id FROM daily_volatility_profile_operation_attempts o"
                + where
                + " ORDER BY o.completed_at_utc DESC, o.attempt_id DESC LIMIT ?",
                values,
            ).fetchall()
        return tuple(self.get_operation(UUID(row["attempt_id"])) for row in rows)

    def get_operation_for_run(self, run_id: UUID) -> DailyVolatilityProfileOperation | None:
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                "SELECT attempt_id FROM daily_volatility_profile_operation_attempts WHERE run_id = ?",
                (str(run_id),),
            ).fetchone()
        return self.get_operation(UUID(row["attempt_id"])) if row else None

    def get_operation(self, attempt_id: UUID) -> DailyVolatilityProfileOperation | None:
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                "SELECT * FROM daily_volatility_profile_operation_attempts WHERE attempt_id = ?",
                (str(attempt_id),),
            ).fetchone()
            if row is None:
                return None
            definition_row = connection.execute(
                "SELECT * FROM daily_volatility_profile_definitions WHERE definition_id = ?",
                (row["definition_id"],),
            ).fetchone()
            definition = self._load_definition(definition_row)
            result = self._load_result(connection, UUID(row["result_id"])) if row["result_id"] else None
            return DailyVolatilityProfileOperation(
                UUID(row["attempt_id"]), UUID(row["operation_id"]), UUID(row["run_id"]),
                UUID(row["factor_stage_id"]), row["command_fingerprint"], definition,
                UUID(row["requested_source_study_id"]),
                UUID(row["requested_source_definition_id"]),
                int(row["requested_source_definition_version"]), row["expected_symbol"],
                DailyVolatilityProfileStatus(row["status"]), result,
                _dt(row["requested_at_utc"]), _dt(row["completed_at_utc"]),
                row["session_id"], row["request_id"], row["created_by"], row["reason"],
                row["software_version"], row["source_revision"], row["worktree_state"],
                tuple(json.loads(row["warnings_text"])), row["error_code"], row["error_summary"],
                bool(row["execution_allowed"]), bool(row["live_allowed"]), int(row["schema_version"]),
            )

    def get_result(self, result_id: UUID) -> DailyVolatilityProfileResult | None:
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                "SELECT 1 FROM daily_volatility_profile_results WHERE result_id = ?",
                (str(result_id),),
            ).fetchone()
            return self._load_result(connection, result_id) if row else None

    @staticmethod
    def _definition_values(definition):
        return (
            str(definition.definition_id), definition.component_id,
            definition.component_version, definition.definition_version,
            definition.status.value, definition.source_component_id,
            definition.allowed_source_component_version,
            _json(definition.required_windows), definition.minimum_evaluation_sessions,
            definition.maximum_evaluation_sessions, definition.daily_aggregation.value,
            definition.history_aggregation.value, definition.dispersion_method.value,
            definition.price_band_method.value, int(definition.require_complete_source_grid),
            definition.spectral_role.value, _iso(definition.created_at_utc),
            definition.created_by, definition.reason, definition.software_version,
            definition.source_revision, definition.worktree_state,
            int(definition.execution_allowed), int(definition.live_allowed), definition.schema_version,
        )

    @classmethod
    def _save_definition_if_missing(cls, connection, definition):
        row = connection.execute(
            "SELECT component_id, component_version FROM daily_volatility_profile_definitions WHERE definition_id = ?",
            (str(definition.definition_id),),
        ).fetchone()
        if row:
            if (row["component_id"], row["component_version"]) != (
                definition.component_id, definition.component_version
            ):
                raise ValueError("stored profile definition identity conflicts")
            return
        connection.execute(
            "INSERT INTO daily_volatility_profile_definitions VALUES ("
            + ",".join("?" for _ in cls._definition_values(definition)) + ")",
            cls._definition_values(definition),
        )

    @staticmethod
    def _load_definition(row):
        return DailyVolatilityProfileDefinition(
            UUID(row["definition_id"]), row["component_id"], row["component_version"],
            int(row["definition_version"]), DailyVolatilityProfileDefinitionStatus(row["status"]),
            row["source_component_id"], row["allowed_source_component_version"],
            tuple(json.loads(row["required_windows_text"])),
            int(row["minimum_evaluation_sessions"]), int(row["maximum_evaluation_sessions"]),
            DailyScaleAggregation(row["daily_aggregation"]),
            ProfileHistoryAggregation(row["history_aggregation"]),
            ProfileDispersionMethod(row["dispersion_method"]),
            ProfilePriceBandMethod(row["price_band_method"]),
            bool(row["require_complete_source_grid"]), ProfileSpectralRole(row["spectral_role"]),
            _dt(row["created_at_utc"]), row["created_by"], row["reason"],
            row["software_version"], row["source_revision"], row["worktree_state"],
            bool(row["execution_allowed"]), bool(row["live_allowed"]), int(row["schema_version"]),
        )

    def _save_result(self, connection, result):
        values = (
            str(result.result_id), result.calculation_fingerprint, str(result.definition_id),
            result.definition_version, str(result.source_study_id), str(result.source_parent_run_id),
            str(result.source_definition_id), result.source_definition_version, result.symbol,
            result.evaluation_start_session.isoformat(), result.evaluation_end_session.isoformat(),
            result.evaluation_session_count, result.status.value, int(result.usable_as_positive_scale),
            *_pair(result.profile_log_scale), *_pair(result.temporal_raw_mad),
            *_pair(result.temporal_standardized_mad), *_pair(result.normalization_constant),
            *_pair(result.minimum_daily_log_scale), *_pair(result.maximum_daily_log_scale),
            *_pair(result.upper_price_fraction), *_pair(result.lower_price_fraction),
            _json(result.formula_trace), _json(result.warnings), result.explanation,
            _iso(result.created_at_utc), result.software_version, result.source_revision,
            result.worktree_state, int(result.execution_allowed), int(result.live_allowed),
            result.schema_version,
        )
        connection.execute(
            "INSERT INTO daily_volatility_profile_results VALUES ("
            + ",".join("?" for _ in values) + ")", values,
        )
        for item in result.daily_inputs:
            self._validate_source_input(connection, item)
            windows = {window.window: window for window in item.windows}
            values = (
                str(item.result_id), item.ordinal, item.evaluation_session.isoformat(),
                str(item.source_study_id), str(item.source_study_point_id),
                item.source_evaluation_ordinal, item.source_definition_ordinal,
                str(item.source_child_run_id), str(item.source_operation_id),
                str(item.source_attempt_id), str(item.source_evidence_bundle_id),
                item.source_operation_fingerprint,
                windows[60].source_status, *_pair(windows[60].trend_standardized_mad),
                windows[120].source_status, *_pair(windows[120].trend_standardized_mad),
                windows[250].source_status, *_pair(windows[250].trend_standardized_mad),
                _json(item.sorted_windows), item.median_source_window,
                *_pair(item.daily_log_scale), item.spectral_evidence_label.value,
                _json(item.source_warnings), item.schema_version,
            )
            connection.execute(
                "INSERT INTO daily_volatility_profile_daily_inputs VALUES ("
                + ",".join("?" for _ in values) + ")", values,
            )
        for item in result.window_summaries:
            values = (
                str(item.result_id), item.window, item.member_count,
                *_pair(item.minimum_trend_standardized_mad),
                *_pair(item.median_trend_standardized_mad),
                *_pair(item.maximum_trend_standardized_mad),
                *_pair(item.minimum_candidate_period), *_pair(item.median_candidate_period),
                *_pair(item.maximum_candidate_period),
                *_pair(item.minimum_center_relative_full_span),
                *_pair(item.median_center_relative_full_span),
                *_pair(item.maximum_center_relative_full_span),
                _category_json(item.dominance_counts), _category_json(item.method_counts),
                _category_json(item.cross_window_counts), item.qualified_source_count,
                item.unqualified_source_count, item.spectral_authority.value, item.schema_version,
            )
            connection.execute(
                "INSERT INTO daily_volatility_profile_window_summaries VALUES ("
                + ",".join("?" for _ in values) + ")", values,
            )

    @staticmethod
    def _validate_source_input(connection, item):
        point = connection.execute(
            """SELECT * FROM spectral_historical_study_points
            WHERE study_id = ? AND evaluation_ordinal = ? AND definition_ordinal = ?""",
            (str(item.source_study_id), item.source_evaluation_ordinal, item.source_definition_ordinal),
        ).fetchone()
        if point is None or (
            point["evaluation_session"] != item.evaluation_session.isoformat()
            or point["child_run_id"] != str(item.source_child_run_id)
            or point["operation_id"] != str(item.source_operation_id)
            or point["attempt_id"] != str(item.source_attempt_id)
            or point["evidence_bundle_id"] != str(item.source_evidence_bundle_id)
        ):
            raise ValueError("P27 source point no longer matches immutable P26 identity")
        operation = connection.execute(
            "SELECT command_fingerprint FROM spectral_volatility_operations WHERE attempt_id = ?",
            (str(item.source_attempt_id),),
        ).fetchone()
        if operation is None or operation["command_fingerprint"] != item.source_operation_fingerprint:
            raise ValueError("P27 source operation fingerprint mismatch")
        for window in item.windows:
            source = connection.execute(
                """SELECT status, trend_standardized_mad_hex FROM spectral_window_results
                WHERE attempt_id = ? AND window_sessions = ?""",
                (str(item.source_attempt_id), window.window),
            ).fetchone()
            if source is None or (
                source["status"] != window.source_status
                or source["trend_standardized_mad_hex"] != window.trend_standardized_mad.ieee_hex
            ):
                raise ValueError("P27 copied source window evidence mismatch")

    def _load_result(self, connection, result_id):
        row = connection.execute(
            "SELECT * FROM daily_volatility_profile_results WHERE result_id = ?",
            (str(result_id),),
        ).fetchone()
        daily = tuple(
            self._load_daily_input(connection, item)
            for item in connection.execute(
                """SELECT * FROM daily_volatility_profile_daily_inputs
                WHERE result_id = ? ORDER BY ordinal""", (str(result_id),)
            )
        )
        summaries = tuple(
            self._load_summary(item)
            for item in connection.execute(
                """SELECT * FROM daily_volatility_profile_window_summaries
                WHERE result_id = ? ORDER BY window_sessions""", (str(result_id),)
            )
        )
        result = DailyVolatilityProfileResult(
            UUID(row["result_id"]), row["calculation_fingerprint"], UUID(row["definition_id"]),
            int(row["definition_version"]), UUID(row["source_study_id"]),
            UUID(row["source_parent_run_id"]), UUID(row["source_definition_id"]),
            int(row["source_definition_version"]), row["symbol"],
            date.fromisoformat(row["evaluation_start_session"]),
            date.fromisoformat(row["evaluation_end_session"]),
            int(row["evaluation_session_count"]), DailyVolatilityProfileStatus(row["status"]),
            bool(row["usable_as_positive_scale"]), _float(row, "profile_log_scale"),
            _float(row, "temporal_raw_mad"), _float(row, "temporal_standardized_mad"),
            _float(row, "normalization_constant"), _float(row, "minimum_daily_log_scale"),
            _float(row, "maximum_daily_log_scale"), _float(row, "upper_price_fraction"),
            _float(row, "lower_price_fraction"), daily, summaries,
            tuple(json.loads(row["formula_trace_text"])), tuple(json.loads(row["warnings_text"])),
            row["explanation"], _dt(row["created_at_utc"]), row["software_version"],
            row["source_revision"], row["worktree_state"], bool(row["execution_allowed"]),
            bool(row["live_allowed"]), int(row["schema_version"]),
        )
        return result

    def _load_daily_input(self, connection, row):
        item = DailyVolatilityProfileDailyInput(
            UUID(row["result_id"]), int(row["ordinal"]), date.fromisoformat(row["evaluation_session"]),
            UUID(row["source_study_id"]), UUID(row["source_study_point_id"]),
            int(row["source_evaluation_ordinal"]), int(row["source_definition_ordinal"]),
            UUID(row["source_child_run_id"]), UUID(row["source_operation_id"]),
            UUID(row["source_attempt_id"]), UUID(row["source_evidence_bundle_id"]),
            row["source_operation_fingerprint"],
            tuple(
                DailyVolatilityWindowInput(
                    window, row[f"w{window}_status"], _float(row, f"w{window}_scale")
                ) for window in (60, 120, 250)
            ),
            tuple(json.loads(row["sorted_windows_text"])), int(row["median_source_window"]),
            _float(row, "daily_log_scale"), ProfileSpectralEvidenceLabel(row["spectral_evidence_label"]),
            tuple(json.loads(row["source_warnings_text"])), int(row["schema_version"]),
        )
        self._validate_source_input(connection, item)
        return item

    @staticmethod
    def _load_summary(row):
        return DailyVolatilityProfileWindowSummary(
            UUID(row["result_id"]), int(row["window_sessions"]), int(row["member_count"]),
            _float(row, "minimum_scale"), _float(row, "median_scale"), _float(row, "maximum_scale"),
            _float(row, "minimum_candidate_period"), _float(row, "median_candidate_period"),
            _float(row, "maximum_candidate_period"), _float(row, "minimum_full_span"),
            _float(row, "median_full_span"), _float(row, "maximum_full_span"),
            _categories(row["dominance_counts_text"]), _categories(row["method_counts_text"]),
            _categories(row["cross_window_counts_text"]), int(row["qualified_source_count"]),
            int(row["unqualified_source_count"]), ProfileSpectralRole(row["spectral_authority"]),
            int(row["schema_version"]),
        )


__all__ = ["SQLiteDailyVolatilityProfileStore"]
