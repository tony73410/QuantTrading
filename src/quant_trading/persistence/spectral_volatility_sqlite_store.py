"""Typed SQLite adapter for P23-1 spectral-volatility evidence."""

from __future__ import annotations

import json
from contextlib import closing
from datetime import date, datetime
from pathlib import Path
from uuid import UUID

from quant_trading.factors.spectral_interfaces import SpectralOperationQuery
from quant_trading.factors.spectral_models import (
    CrossWindowPairEvidence,
    CrossWindowStabilityEvidence,
    CrossWindowStatus,
    DominanceClass,
    FloatEvidence,
    MethodComparisonEvidence,
    MethodComparisonStatus,
    PeakMemberEvidence,
    PeakNeighborhoodEvidence,
    PeakStatus,
    RelativeShareStatus,
    ResidualScaleEvidence,
    SpectralAmplitudeEvidence,
    SpectralDefinitionStatus,
    SpectralOperationStatus,
    SpectralSegmentEvidence,
    SpectralSeriesPoint,
    SpectralVolatilityDefinition,
    SpectralVolatilityOperation,
    SpectralWindowDefinition,
    SpectralWindowEvidence,
    SpectrumBinEvidence,
    WindowCalculationStatus,
)
from quant_trading.market_history.models import DataFeed, Timeframe
from quant_trading.market_history.research_evidence import (
    ResearchBarObservation,
    ResearchCalendarSession,
    ResearchCalendarSymbolMapping,
    ResearchCorporateActionEvent,
    ResearchCorporateActionSnapshot,
    ResearchEvidenceMode,
    ResearchMarketCalendarSnapshot,
    SpectralMarketEvidenceBundle,
)

from .sqlite_database import CentralSQLiteDatabase


def _iso(value: datetime) -> str:
    return value.isoformat(timespec="microseconds")


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def _pair(value: FloatEvidence | None) -> tuple[float | None, str | None]:
    return (None, None) if value is None else (value.value, value.ieee_hex)


def _float(row, name: str) -> FloatEvidence | None:
    value = row[name]
    if value is None:
        return None
    # IEEE text is authoritative for exact replay; SQLite REAL can normalize
    # signed zero while loading.
    ieee_hex = row[f"{name}_hex"]
    return FloatEvidence(float.fromhex(ieee_hex), ieee_hex)


def _warnings(value: tuple[str, ...]) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


class SQLiteSpectralVolatilityStore:
    """Persist the complete structured evidence graph in central SQLite."""

    def __init__(self, database_path: Path | str) -> None:
        self._database = CentralSQLiteDatabase(database_path)

    def initialize(self) -> None:
        self._database.initialize()

    def save_definition(self, definition: SpectralVolatilityDefinition) -> None:
        with closing(self._database.connect()) as connection:
            with connection:
                connection.execute(
                    """
                    INSERT INTO spectral_volatility_definitions VALUES
                    (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(definition.definition_id), definition.component_id,
                        definition.component_version, definition.definition_version,
                        definition.status.value, _iso(definition.created_at_utc),
                        definition.created_by, definition.reason,
                        int(definition.execution_allowed), int(definition.live_allowed),
                        definition.schema_version,
                    ),
                )
                connection.executemany(
                    """
                    INSERT INTO spectral_volatility_definition_windows VALUES
                    (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            str(definition.definition_id), item.window,
                            item.leading_start, item.leading_end,
                            item.trailing_start, item.trailing_end,
                            item.fft_length, item.eligible_bin_start,
                            item.eligible_bin_end,
                        )
                        for item in definition.windows
                    ],
                )

    def get_definition(self, definition_id: UUID) -> SpectralVolatilityDefinition | None:
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                "SELECT * FROM spectral_volatility_definitions WHERE definition_id = ?",
                (str(definition_id),),
            ).fetchone()
            if row is None:
                return None
            windows = tuple(
                SpectralWindowDefinition(
                    int(item["window_sessions"]), int(item["leading_start"]),
                    int(item["leading_end"]), int(item["trailing_start"]),
                    int(item["trailing_end"]), int(item["fft_length"]),
                    int(item["eligible_bin_start"]), int(item["eligible_bin_end"]),
                )
                for item in connection.execute(
                    """SELECT * FROM spectral_volatility_definition_windows
                    WHERE definition_id = ? ORDER BY window_sessions""",
                    (str(definition_id),),
                )
            )
            return SpectralVolatilityDefinition(
                UUID(row["definition_id"]), row["component_id"],
                row["component_version"], int(row["definition_version"]),
                SpectralDefinitionStatus(row["status"]), windows,
                _dt(row["created_at_utc"]), row["created_by"], row["reason"],
                bool(row["execution_allowed"]), bool(row["live_allowed"]),
                int(row["schema_version"]),
            )

    def get_first_operation(self, operation_id: UUID) -> SpectralVolatilityOperation | None:
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                """SELECT attempt_id FROM spectral_volatility_operations
                WHERE operation_id = ? ORDER BY requested_at_utc, attempt_id LIMIT 1""",
                (str(operation_id),),
            ).fetchone()
        return self.get_operation(UUID(row["attempt_id"])) if row else None

    def save_operation(self, operation: SpectralVolatilityOperation) -> None:
        with closing(self._database.connect()) as connection:
            with connection:
                self._save_definition_if_missing(connection, operation.definition)
                self._save_bundle(connection, operation.evidence_bundle)
                self._insert_operation(connection, operation)
                self._save_source_observations(connection, operation)
                self._save_source_link(connection, operation)
                for window in operation.windows:
                    self._save_window(connection, operation.attempt_id, window)
                if operation.cross_window is not None:
                    self._save_cross_window(connection, operation.attempt_id, operation.cross_window)

    def list_operations(
        self, query: SpectralOperationQuery = SpectralOperationQuery()
    ) -> tuple[SpectralVolatilityOperation, ...]:
        clauses: list[str] = []
        parameters: list[object] = []
        if query.symbol:
            clauses.append("o.symbol = ?")
            parameters.append(query.symbol)
        if query.definition_id:
            clauses.append("o.definition_id = ?")
            parameters.append(str(query.definition_id))
        if query.status:
            clauses.append("o.status = ?")
            parameters.append(query.status.value)
        if query.as_of_from_utc:
            clauses.append("o.as_of_utc >= ?")
            parameters.append(_iso(query.as_of_from_utc))
        if query.as_of_to_utc:
            clauses.append("o.as_of_utc < ?")
            parameters.append(_iso(query.as_of_to_utc))
        if query.evidence_mode:
            clauses.append("l.evidence_mode = ?")
            parameters.append(query.evidence_mode)
        if query.warning_only:
            clauses.append("o.warnings_text <> '[]'")
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        parameters.append(query.limit)
        with closing(self._database.connect()) as connection:
            rows = connection.execute(
                """SELECT o.attempt_id FROM spectral_volatility_operations o
                JOIN spectral_source_links l ON l.attempt_id = o.attempt_id"""
                + where + " ORDER BY o.completed_at_utc DESC, o.attempt_id DESC LIMIT ?",
                parameters,
            ).fetchall()
        return tuple(
            item for row in rows
            if (item := self.get_operation(UUID(row["attempt_id"]))) is not None
        )

    def find_latest_evidence_bundle(
        self,
        *,
        symbol: str,
        as_of_utc: datetime,
        feed: DataFeed,
        evidence_mode: ResearchEvidenceMode,
    ) -> SpectralMarketEvidenceBundle | None:
        """Return one exact frozen bundle; never reconstruct from generic Bars."""
        operations = self.list_operations(
            SpectralOperationQuery(
                symbol=symbol,
                evidence_mode=evidence_mode.value,
                limit=5000,
            )
        )
        for operation in operations:
            bundle = operation.evidence_bundle
            if (
                operation.status
                in {
                    SpectralOperationStatus.COMPLETED,
                    SpectralOperationStatus.COMPLETED_WITH_WARNINGS,
                }
                and bundle.as_of_utc == as_of_utc
                and bundle.feed is feed
                and bundle.evidence_mode is evidence_mode
            ):
                return bundle
        return None

    def get_operation_for_run(self, run_id: UUID) -> SpectralVolatilityOperation | None:
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                "SELECT attempt_id FROM spectral_volatility_operations WHERE run_id = ?",
                (str(run_id),),
            ).fetchone()
        return self.get_operation(UUID(row["attempt_id"])) if row else None

    def get_operation(self, attempt_id: UUID) -> SpectralVolatilityOperation | None:
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                "SELECT * FROM spectral_volatility_operations WHERE attempt_id = ?",
                (str(attempt_id),),
            ).fetchone()
            if row is None:
                return None
            definition = self._load_definition(connection, UUID(row["definition_id"]))
            bundle = self._load_bundle(connection, attempt_id)
            windows = tuple(
                self._load_window(connection, attempt_id, item)
                for item in connection.execute(
                    """SELECT * FROM spectral_window_results WHERE attempt_id = ?
                    ORDER BY window_sessions""",
                    (str(attempt_id),),
                )
            )
            cross = self._load_cross_window(connection, attempt_id)
            return SpectralVolatilityOperation(
                UUID(row["attempt_id"]), UUID(row["operation_id"]), UUID(row["run_id"]),
                UUID(row["market_data_stage_id"]), UUID(row["factor_stage_id"]),
                row["command_fingerprint"], SpectralOperationStatus(row["status"]),
                definition, bundle, windows, cross,
                _dt(row["requested_at_utc"]), _dt(row["completed_at_utc"]),
                row["numpy_version"], row["exchange_calendars_version"],
                row["software_version"], row["source_revision"], row["worktree_state"],
                tuple(json.loads(row["warnings_text"])), row["error_code"],
                row["error_summary"], int(row["schema_version"]),
            )

    @staticmethod
    def _save_definition_if_missing(connection, definition) -> None:
        existing = connection.execute(
            "SELECT component_id, component_version, definition_version FROM spectral_volatility_definitions WHERE definition_id = ?",
            (str(definition.definition_id),),
        ).fetchone()
        if existing:
            if (existing[0], existing[1], int(existing[2])) != (
                definition.component_id, definition.component_version, definition.definition_version
            ):
                raise ValueError("stored spectral definition identity conflicts")
            return
        connection.execute(
            "INSERT INTO spectral_volatility_definitions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                str(definition.definition_id), definition.component_id,
                definition.component_version, definition.definition_version,
                definition.status.value, _iso(definition.created_at_utc),
                definition.created_by, definition.reason,
                int(definition.execution_allowed), int(definition.live_allowed),
                definition.schema_version,
            ),
        )
        connection.executemany(
            "INSERT INTO spectral_volatility_definition_windows VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [(str(definition.definition_id), w.window, w.leading_start, w.leading_end,
              w.trailing_start, w.trailing_end, w.fft_length,
              w.eligible_bin_start, w.eligible_bin_end) for w in definition.windows],
        )

    @staticmethod
    def _save_bundle(connection, bundle: SpectralMarketEvidenceBundle) -> None:
        calendar = bundle.calendar_snapshot
        connection.execute(
            "INSERT OR IGNORE INTO research_market_calendar_snapshots VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (str(calendar.snapshot_id), calendar.calendar_definition_id, calendar.engine_name,
             calendar.engine_version, calendar.exchange_calendar_name,
             calendar.covered_start.isoformat(), calendar.covered_end.isoformat(),
             calendar.schedule_fingerprint, _iso(calendar.observed_at_utc),
             _iso(calendar.created_at_utc), calendar.schema_version),
        )
        connection.executemany(
            "INSERT OR IGNORE INTO research_market_calendar_sessions VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [(str(calendar.snapshot_id), s.ordinal, s.session_date.isoformat(),
              _iso(s.open_utc), _iso(s.close_utc),
              _iso(s.break_start_utc) if s.break_start_utc else None,
              _iso(s.break_end_utc) if s.break_end_utc else None, int(s.early_close))
             for s in calendar.sessions],
        )
        mapping = bundle.symbol_mapping
        connection.execute(
            "INSERT OR IGNORE INTO research_market_calendar_symbol_mappings VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (str(mapping.mapping_id), mapping.mapping_version, mapping.symbol,
             mapping.asset_class, mapping.calendar_definition_id,
             mapping.effective_start.isoformat(),
             mapping.effective_end.isoformat() if mapping.effective_end else None,
             _iso(mapping.created_at_utc), mapping.created_by, mapping.reason,
             mapping.schema_version),
        )
        actions = bundle.corporate_action_snapshot
        connection.execute(
            "INSERT OR IGNORE INTO research_corporate_action_snapshots VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (str(actions.snapshot_id), actions.provider_name, actions.query_identity,
             _iso(actions.requested_at_utc), _iso(actions.received_at_utc),
             actions.covered_start.isoformat(), actions.covered_end.isoformat(),
             actions.response_fingerprint, actions.evidence_mode.value,
             actions.schema_version),
        )
        connection.executemany(
            "INSERT OR IGNORE INTO research_corporate_action_events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [(str(actions.snapshot_id), e.ordinal, e.provider_event_id, e.symbol,
              e.action_type, e.declaration_date.isoformat() if e.declaration_date else None,
              e.ex_date.isoformat() if e.ex_date else None,
              e.effective_date.isoformat() if e.effective_date else None,
              e.process_date.isoformat() if e.process_date else None,
              e.ratio_text, e.raw_event_fingerprint, int(e.supported))
             for e in actions.events],
        )

    @staticmethod
    def _insert_operation(connection, operation) -> None:
        values = (str(operation.attempt_id), str(operation.operation_id), str(operation.run_id),
                  str(operation.market_data_stage_id), str(operation.factor_stage_id),
                  str(operation.definition.definition_id), str(operation.evidence_bundle.bundle_id),
                  operation.evidence_bundle.symbol, _iso(operation.evidence_bundle.as_of_utc),
                  operation.command_fingerprint, operation.status.value,
                  _iso(operation.requested_at_utc), _iso(operation.completed_at_utc),
                  operation.numpy_version, operation.exchange_calendars_version,
                  operation.software_version, operation.source_revision, operation.worktree_state,
                  _warnings(operation.warnings), operation.error_code, operation.error_summary,
                  operation.schema_version)
        connection.execute(
            "INSERT INTO spectral_volatility_operations VALUES ("
            + ",".join("?" for _ in values) + ")",
            values,
        )

    @staticmethod
    def _save_source_observations(connection, operation) -> None:
        bundle = operation.evidence_bundle
        for item in bundle.observations:
            for adjustment, fingerprint, values in (
                ("raw", item.raw_content_fingerprint,
                 (item.raw_open_text, item.raw_high_text, item.raw_low_text, item.raw_close_text)),
                ("split", item.split_content_fingerprint,
                 (item.split_open_text, item.split_high_text, item.split_low_text, item.split_close_text)),
            ):
                connection.execute(
                    """INSERT OR IGNORE INTO market_bar_observation_facts VALUES
                    (?, ?, ?, '1Day', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)""",
                    (fingerprint, bundle.symbol, item.session_date.isoformat(), adjustment,
                     item.feed.value, *values, item.volume, item.source,
                     _iso(item.completed_at_utc), _iso(item.first_observed_at_utc),
                     _iso(item.available_at_utc), _iso(bundle.created_at_utc)),
                )
            connection.execute(
                "INSERT INTO spectral_source_observations VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (str(operation.attempt_id), item.ordinal, item.session_date.isoformat(),
                 item.raw_content_fingerprint, item.split_content_fingerprint,
                 _iso(item.completed_at_utc), _iso(item.first_observed_at_utc),
                 _iso(item.available_at_utc)),
            )

    @staticmethod
    def _save_source_link(connection, operation) -> None:
        bundle = operation.evidence_bundle
        connection.execute(
            "INSERT INTO spectral_source_links VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (str(operation.attempt_id), str(operation.operation_id), str(operation.run_id),
             str(operation.market_data_stage_id), str(operation.factor_stage_id),
             str(operation.definition.definition_id), str(bundle.bundle_id),
             bundle.content_fingerprint, str(bundle.calendar_snapshot.snapshot_id),
             str(bundle.symbol_mapping.mapping_id),
             str(bundle.corporate_action_snapshot.snapshot_id), bundle.evidence_mode.value,
             _iso(bundle.created_at_utc), 1),
        )

    def _save_window(self, connection, attempt_id: UUID, window: SpectralWindowEvidence) -> None:
        amplitude = window.amplitude
        residual = window.residual_scale
        values = (
            _pair(window.trend_intercept) + _pair(window.trend_slope)
            + _pair(window.eligible_power) + _pair(window.qualified_frequency)
            + _pair(window.qualified_period_sessions)
            + _pair(amplitude.log_half_amplitude if amplitude else None)
            + _pair(amplitude.log_peak_to_trough if amplitude else None)
            + _pair(amplitude.upper_price_fraction if amplitude else None)
            + _pair(amplitude.lower_price_fraction if amplitude else None)
            + _pair(amplitude.center_relative_full_span if amplitude else None)
            + _pair(amplitude.trough_to_peak_return if amplitude else None)
            + _pair(residual.trend_difference_median if residual else None)
            + _pair(residual.trend_raw_mad if residual else None)
            + _pair(residual.trend_standardized_mad if residual else None)
            + _pair(residual.cycle_difference_median if residual else None)
            + _pair(residual.cycle_raw_mad if residual else None)
            + _pair(residual.cycle_standardized_mad if residual else None)
            + _pair(residual.normalization_constant if residual else None)
        )
        row_values = (str(attempt_id), window.window, window.status.value,
                      window.share_status.value, window.peak_status.value,
                      window.dominance_class.value, window.observation_count,
                      *values, int(residual.zero_residual_mad) if residual else None,
                      _warnings(window.warnings))
        connection.execute(
            "INSERT INTO spectral_window_results VALUES ("
            + ",".join("?" for _ in row_values) + ")",
            row_values,
        )
        connection.executemany(
            "INSERT INTO spectral_segment_results VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [(str(attempt_id), window.window, s.segment_name, s.start_index, s.end_index,
              s.source_length, s.fft_length, s.coherent_gain_squared.value,
              s.coherent_gain_squared.ieee_hex, s.status.value) for s in window.segments],
        )
        connection.executemany(
            """INSERT INTO spectral_series_points VALUES
            (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [(str(attempt_id), window.window, p.segment_name, p.point_index,
              p.source_ordinal, int(p.is_padding), *_pair(p.input_log), *_pair(p.trend),
              *_pair(p.detrended), *_pair(p.baseline_difference), *_pair(p.periodic_fit),
              *_pair(p.residual), *_pair(p.hann_weight), *_pair(p.weighted_value))
             for p in window.series_points],
        )
        bin_rows = [(str(attempt_id), window.window, b.segment_name, b.bin_index,
              *_pair(b.frequency_cycles_per_session), *_pair(b.period_sessions), int(b.eligible),
              *_pair(b.fft_real), *_pair(b.fft_imag), *_pair(b.squared_magnitude),
              *_pair(b.coherent_gain_squared), *_pair(b.one_sided_multiplier),
              *_pair(b.corrected_power), *_pair(b.relative_share))
             for b in window.spectrum_bins]
        if bin_rows:
            connection.executemany(
                "INSERT INTO spectral_spectrum_bins VALUES ("
                + ",".join("?" for _ in bin_rows[0]) + ")",
                bin_rows,
            )
        for neighborhood in window.peak_neighborhoods:
            neighborhood_values = (str(attempt_id), window.window, neighborhood.method_name,
                 neighborhood.rank, neighborhood.peak_status.value,
                 neighborhood.center_bin, neighborhood.requested_start_bin,
                 neighborhood.requested_end_bin, neighborhood.effective_start_bin,
                 neighborhood.effective_end_bin, *_pair(neighborhood.neighborhood_power),
                 *_pair(neighborhood.dominance), neighborhood.dominance_class.value,
                 int(neighborhood.truncated))
            connection.execute(
                "INSERT INTO spectral_peak_neighborhoods VALUES ("
                + ",".join("?" for _ in neighborhood_values) + ")",
                neighborhood_values,
            )
            connection.executemany(
                """INSERT INTO spectral_peak_members VALUES
                (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                [(str(attempt_id), window.window, neighborhood.method_name,
                  neighborhood.rank, ordinal, member.bin_index, int(member.requested),
                  int(member.effective), *_pair(member.power), *_pair(member.relative_share))
                 for ordinal, member in enumerate(neighborhood.members, 1)],
            )
        if window.method_comparison:
            item = window.method_comparison
            connection.execute(
                """INSERT INTO spectral_method_comparisons VALUES
                (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (str(attempt_id), window.window, *_pair(item.welch_period_sessions),
                 *_pair(item.fourier_period_sessions), *_pair(item.symmetric_delta),
                 item.status.value),
            )

    @staticmethod
    def _save_cross_window(connection, attempt_id, cross) -> None:
        connection.execute(
            "INSERT INTO spectral_cross_window_results VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (str(attempt_id), cross.status.value,
             json.dumps(cross.qualified_windows, separators=(",", ":")),
             json.dumps(cross.supporting_windows, separators=(",", ":")),
             *_pair(cross.consensus_frequency), *_pair(cross.consensus_period_sessions)),
        )
        pair_rows = [(str(attempt_id), p.left_window, p.right_window,
              *_pair(p.left_period_sessions), *_pair(p.right_period_sessions),
              *_pair(p.symmetric_delta), int(p.supports)) for p in cross.pairs]
        if pair_rows:
            connection.executemany(
                "INSERT INTO spectral_cross_window_pairs VALUES ("
                + ",".join("?" for _ in pair_rows[0]) + ")",
                pair_rows,
            )

    def _load_definition(self, connection, definition_id: UUID):
        row = connection.execute(
            "SELECT * FROM spectral_volatility_definitions WHERE definition_id = ?",
            (str(definition_id),),
        ).fetchone()
        windows = tuple(SpectralWindowDefinition(
            int(w["window_sessions"]), int(w["leading_start"]), int(w["leading_end"]),
            int(w["trailing_start"]), int(w["trailing_end"]), int(w["fft_length"]),
            int(w["eligible_bin_start"]), int(w["eligible_bin_end"]),
        ) for w in connection.execute(
            "SELECT * FROM spectral_volatility_definition_windows WHERE definition_id = ? ORDER BY window_sessions",
            (str(definition_id),),
        ))
        return SpectralVolatilityDefinition(
            definition_id, row["component_id"], row["component_version"],
            int(row["definition_version"]), SpectralDefinitionStatus(row["status"]),
            windows, _dt(row["created_at_utc"]), row["created_by"], row["reason"],
            bool(row["execution_allowed"]), bool(row["live_allowed"]), int(row["schema_version"]),
        )

    def _load_bundle(self, connection, attempt_id: UUID) -> SpectralMarketEvidenceBundle:
        link = connection.execute("SELECT * FROM spectral_source_links WHERE attempt_id = ?", (str(attempt_id),)).fetchone()
        cal = connection.execute("SELECT * FROM research_market_calendar_snapshots WHERE snapshot_id = ?", (link["calendar_snapshot_id"],)).fetchone()
        sessions = tuple(ResearchCalendarSession(
            int(s["ordinal"]), date.fromisoformat(s["session_date"]), _dt(s["open_utc"]),
            _dt(s["close_utc"]), _dt(s["break_start_utc"]) if s["break_start_utc"] else None,
            _dt(s["break_end_utc"]) if s["break_end_utc"] else None, bool(s["early_close"]),
        ) for s in connection.execute("SELECT * FROM research_market_calendar_sessions WHERE snapshot_id = ? ORDER BY ordinal", (cal["snapshot_id"],)))
        calendar = ResearchMarketCalendarSnapshot(
            UUID(cal["snapshot_id"]), cal["calendar_definition_id"], cal["engine_name"],
            cal["engine_version"], cal["exchange_calendar_name"],
            date.fromisoformat(cal["covered_start"]), date.fromisoformat(cal["covered_end"]),
            cal["schedule_fingerprint"], _dt(cal["observed_at_utc"]),
            _dt(cal["created_at_utc"]), sessions, int(cal["schema_version"]),
        )
        m = connection.execute("SELECT * FROM research_market_calendar_symbol_mappings WHERE mapping_id = ?", (link["mapping_id"],)).fetchone()
        mapping = ResearchCalendarSymbolMapping(
            UUID(m["mapping_id"]), int(m["mapping_version"]), m["symbol"], m["asset_class"],
            m["calendar_definition_id"], date.fromisoformat(m["effective_start"]),
            _date(m["effective_end"]), _dt(m["created_at_utc"]), m["created_by"],
            m["reason"], int(m["schema_version"]),
        )
        ca = connection.execute("SELECT * FROM research_corporate_action_snapshots WHERE snapshot_id = ?", (link["corporate_action_snapshot_id"],)).fetchone()
        events = tuple(ResearchCorporateActionEvent(
            int(e["ordinal"]), e["provider_event_id"], e["symbol"], e["action_type"],
            _date(e["declaration_date"]), _date(e["ex_date"]), _date(e["effective_date"]),
            _date(e["process_date"]), e["ratio_text"], e["raw_event_fingerprint"], bool(e["supported"]),
        ) for e in connection.execute("SELECT * FROM research_corporate_action_events WHERE snapshot_id = ? ORDER BY ordinal", (ca["snapshot_id"],)))
        actions = ResearchCorporateActionSnapshot(
            UUID(ca["snapshot_id"]), ca["provider_name"], ca["query_identity"],
            _dt(ca["requested_at_utc"]), _dt(ca["received_at_utc"]),
            date.fromisoformat(ca["covered_start"]), date.fromisoformat(ca["covered_end"]),
            ca["response_fingerprint"], ResearchEvidenceMode(ca["evidence_mode"]), events,
            int(ca["schema_version"]),
        )
        op = connection.execute("SELECT * FROM spectral_volatility_operations WHERE attempt_id = ?", (str(attempt_id),)).fetchone()
        observations = []
        for source in connection.execute("SELECT * FROM spectral_source_observations WHERE attempt_id = ? ORDER BY ordinal", (str(attempt_id),)):
            raw = connection.execute("SELECT * FROM market_bar_observation_facts WHERE content_fingerprint = ?", (source["raw_fact_fingerprint"],)).fetchone()
            split = connection.execute("SELECT * FROM market_bar_observation_facts WHERE content_fingerprint = ?", (source["split_fact_fingerprint"],)).fetchone()
            observations.append(ResearchBarObservation(
                int(source["ordinal"]), date.fromisoformat(source["session_date"]),
                _dt(source["completed_at_utc"]), _dt(source["first_observed_at_utc"]),
                _dt(source["available_at_utc"]), raw["open_text"], raw["high_text"],
                raw["low_text"], raw["close_text"], split["open_text"], split["high_text"],
                split["low_text"], split["close_text"], int(split["volume"]),
                DataFeed(split["feed"]), split["source"], raw["content_fingerprint"],
                split["content_fingerprint"],
            ))
        return SpectralMarketEvidenceBundle(
            UUID(link["evidence_bundle_id"]), link["evidence_bundle_fingerprint"],
            op["symbol"], Timeframe.DAY, observations[0].feed if observations else DataFeed.IEX,
            _dt(op["as_of_utc"]), calendar, mapping, actions,
            ResearchEvidenceMode(link["evidence_mode"]), tuple(observations),
            _dt(link["created_at_utc"]), 1,
        )

    def _load_window(self, connection, attempt_id: UUID, row) -> SpectralWindowEvidence:
        key = (str(attempt_id), int(row["window_sessions"]))
        segments = tuple(SpectralSegmentEvidence(
            s["segment_name"], int(s["start_index"]), int(s["end_index"]),
            int(s["source_length"]), int(s["fft_length"]),
            FloatEvidence(float(s["coherent_gain_squared"]), s["coherent_gain_squared_hex"]),
            WindowCalculationStatus(s["status"]),
        ) for s in connection.execute("""SELECT * FROM spectral_segment_results
            WHERE attempt_id = ? AND window_sessions = ? ORDER BY CASE segment_name
            WHEN 'welch_leading' THEN 1 WHEN 'welch_trailing' THEN 2
            WHEN 'fourier_full' THEN 3 ELSE 9 END""", key))
        series = tuple(SpectralSeriesPoint(
            p["segment_name"], int(p["point_index"]), p["source_ordinal"], bool(p["is_padding"]),
            _float(p, "input_log"), _float(p, "trend"), _float(p, "detrended"),
            _float(p, "baseline_difference"), _float(p, "periodic_fit"),
            _float(p, "residual"), _float(p, "hann_weight"), _float(p, "weighted_value"),
        ) for p in connection.execute("""SELECT * FROM spectral_series_points
            WHERE attempt_id = ? AND window_sessions = ? ORDER BY CASE segment_name
            WHEN 'full_model' THEN 1 WHEN 'welch_leading' THEN 2
            WHEN 'welch_trailing' THEN 3 WHEN 'fourier_full' THEN 4 ELSE 9 END,
            point_index""", key))
        bins = tuple(SpectrumBinEvidence(
            b["segment_name"], int(b["bin_index"]), _float(b, "frequency"),
            _float(b, "period"), bool(b["eligible"]), _float(b, "fft_real"),
            _float(b, "fft_imag"), _float(b, "squared_magnitude"),
            _float(b, "coherent_gain_squared"), _float(b, "one_sided_multiplier"),
            _float(b, "corrected_power"), _float(b, "relative_share"),
        ) for b in connection.execute("""SELECT * FROM spectral_spectrum_bins
            WHERE attempt_id = ? AND window_sessions = ? ORDER BY CASE segment_name
            WHEN 'welch_leading' THEN 1 WHEN 'welch_trailing' THEN 2
            WHEN 'welch_average' THEN 3 WHEN 'fourier_full' THEN 4 ELSE 9 END,
            bin_index""", key))
        neighborhoods = []
        for n in connection.execute("""SELECT * FROM spectral_peak_neighborhoods
            WHERE attempt_id = ? AND window_sessions = ? ORDER BY CASE method_name
            WHEN 'welch_average' THEN 1 WHEN 'fourier_full' THEN 2 ELSE 9 END, rank""", key):
            members = tuple(PeakMemberEvidence(
                int(m["bin_index"]), bool(m["requested"]), bool(m["effective"]),
                _float(m, "power"), _float(m, "relative_share"),
            ) for m in connection.execute("""SELECT * FROM spectral_peak_members
                WHERE attempt_id = ? AND window_sessions = ? AND method_name = ? AND neighborhood_rank = ?
                ORDER BY member_ordinal""", (*key, n["method_name"], n["rank"])))
            neighborhoods.append(PeakNeighborhoodEvidence(
                n["method_name"], int(n["rank"]), PeakStatus(n["peak_status"]), n["center_bin"],
                n["requested_start_bin"], n["requested_end_bin"], n["effective_start_bin"],
                n["effective_end_bin"], _float(n, "neighborhood_power"), _float(n, "dominance"),
                DominanceClass(n["dominance_class"]), bool(n["truncated"]), members,
            ))
        comparison_row = connection.execute("SELECT * FROM spectral_method_comparisons WHERE attempt_id = ? AND window_sessions = ?", key).fetchone()
        comparison = MethodComparisonEvidence(
            _float(comparison_row, "welch_period"), _float(comparison_row, "fourier_period"),
            _float(comparison_row, "symmetric_delta"), MethodComparisonStatus(comparison_row["status"]),
        ) if comparison_row else None
        amplitude = None if row["amplitude_log_half"] is None else SpectralAmplitudeEvidence(
            _float(row, "amplitude_log_half"), _float(row, "amplitude_log_peak_to_trough"),
            _float(row, "amplitude_upper_price_fraction"), _float(row, "amplitude_lower_price_fraction"),
            _float(row, "amplitude_center_relative_span"), _float(row, "amplitude_trough_to_peak_return"),
        )
        residual = None if row["trend_raw_mad"] is None else ResidualScaleEvidence(
            _float(row, "trend_difference_median"), _float(row, "trend_raw_mad"),
            _float(row, "trend_standardized_mad"), _float(row, "cycle_difference_median"),
            _float(row, "cycle_raw_mad"), _float(row, "cycle_standardized_mad"),
            _float(row, "mad_normalization"), bool(row["zero_residual_mad"]),
        )
        return SpectralWindowEvidence(
            int(row["window_sessions"]), WindowCalculationStatus(row["status"]),
            RelativeShareStatus(row["share_status"]), PeakStatus(row["peak_status"]),
            DominanceClass(row["dominance_class"]), int(row["observation_count"]),
            _float(row, "trend_intercept"), _float(row, "trend_slope"),
            _float(row, "eligible_power"), _float(row, "qualified_frequency"),
            _float(row, "qualified_period"), segments, series, bins, tuple(neighborhoods),
            comparison, amplitude, residual, tuple(json.loads(row["warnings_text"])),
        )

    @staticmethod
    def _load_cross_window(connection, attempt_id: UUID):
        row = connection.execute("SELECT * FROM spectral_cross_window_results WHERE attempt_id = ?", (str(attempt_id),)).fetchone()
        if row is None:
            return None
        pairs = tuple(CrossWindowPairEvidence(
            int(p["left_window"]), int(p["right_window"]), _float(p, "left_period"),
            _float(p, "right_period"), _float(p, "symmetric_delta"), bool(p["supports"]),
        ) for p in connection.execute("SELECT * FROM spectral_cross_window_pairs WHERE attempt_id = ? ORDER BY left_window, right_window", (str(attempt_id),)))
        return CrossWindowStabilityEvidence(
            CrossWindowStatus(row["status"]), tuple(json.loads(row["qualified_windows_text"])),
            tuple(json.loads(row["supporting_windows_text"])), pairs,
            _float(row, "consensus_frequency"), _float(row, "consensus_period"),
        )


__all__ = ["SQLiteSpectralVolatilityStore"]
