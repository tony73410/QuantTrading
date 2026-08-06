"""Central SQLite adapter for P23-1E-B historical spectral studies."""

from __future__ import annotations

import json
from contextlib import closing
from datetime import date, datetime
from pathlib import Path
from uuid import UUID

from quant_trading.factors.spectral_history_models import (
    SpectralHistoricalDefinitionSelection,
    SpectralHistoricalPointStatus,
    SpectralHistoricalStudy,
    SpectralHistoricalStudyPoint,
    SpectralHistoricalStudyQuery,
    SpectralHistoricalStudyStatus,
)
from quant_trading.market_history import (
    DataFeed,
    ResearchBarObservation,
    ResearchCalendarSession,
    ResearchCalendarSymbolMapping,
    ResearchCorporateActionEvent,
    ResearchCorporateActionSnapshot,
    ResearchEvidenceMode,
    ResearchMarketCalendarSnapshot,
    SpectralEvidenceAcquisitionMode,
    SpectralHistoricalEvidenceSet,
    SpectralMarketEvidenceBundle,
    Timeframe,
)
from .spectral_volatility_sqlite_store import SQLiteSpectralVolatilityStore
from .sqlite_database import CentralSQLiteDatabase


def _iso(value: datetime) -> str:
    return value.isoformat(timespec="microseconds")


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def _json(values: tuple[str, ...]) -> str:
    return json.dumps(values, ensure_ascii=False, separators=(",", ":"))


class SQLiteSpectralHistoricalStudyStore:
    """Persist exact evidence sets and immutable completed study grids."""

    def __init__(self, database_path: Path | str) -> None:
        self._database = CentralSQLiteDatabase(database_path)

    def initialize(self) -> None:
        self._database.initialize()

    def save_evidence_set(self, evidence_set: SpectralHistoricalEvidenceSet) -> None:
        with closing(self._database.connect()) as connection:
            existing = connection.execute(
                "SELECT content_fingerprint FROM spectral_historical_evidence_sets WHERE evidence_set_id = ?",
                (str(evidence_set.evidence_set_id),),
            ).fetchone()
            if existing is not None:
                if existing["content_fingerprint"] != evidence_set.content_fingerprint:
                    raise ValueError("stored historical evidence-set identity conflicts")
                return
            with connection:
                pseudo_bundle = SpectralMarketEvidenceBundle(
                    evidence_set.evidence_set_id,
                    evidence_set.content_fingerprint,
                    evidence_set.symbol,
                    evidence_set.timeframe,
                    evidence_set.feed,
                    evidence_set.evaluation_sessions[-1].close_utc,
                    evidence_set.calendar_snapshot,
                    evidence_set.symbol_mapping,
                    evidence_set.corporate_action_snapshot,
                    evidence_set.evidence_mode,
                    evidence_set.observations,
                    evidence_set.created_at_utc,
                )
                SQLiteSpectralVolatilityStore._save_bundle(connection, pseudo_bundle)
                self._save_observation_facts(connection, evidence_set)
                connection.execute(
                    """INSERT INTO spectral_historical_evidence_sets VALUES
                    (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        str(evidence_set.evidence_set_id), evidence_set.content_fingerprint,
                        evidence_set.symbol, evidence_set.feed.value,
                        evidence_set.timeframe.value, evidence_set.evidence_mode.value,
                        evidence_set.acquisition_mode.value,
                        evidence_set.evaluation_sessions[0].session_date.isoformat(),
                        evidence_set.evaluation_sessions[-1].session_date.isoformat(),
                        evidence_set.source_start_session.isoformat(),
                        evidence_set.source_end_session.isoformat(),
                        len(evidence_set.evaluation_sessions), len(evidence_set.observations),
                        str(evidence_set.calendar_snapshot.snapshot_id),
                        str(evidence_set.symbol_mapping.mapping_id),
                        str(evidence_set.corporate_action_snapshot.snapshot_id),
                        _iso(evidence_set.requested_at_utc), _iso(evidence_set.created_at_utc),
                        _json(evidence_set.warnings), evidence_set.schema_version,
                    ),
                )
                evaluation_ordinals = {
                    item.session_date: ordinal
                    for ordinal, item in enumerate(evidence_set.evaluation_sessions, 1)
                }
                connection.executemany(
                    """INSERT INTO spectral_historical_evidence_observations VALUES
                    (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    [
                        (
                            str(evidence_set.evidence_set_id), item.ordinal,
                            item.session_date.isoformat(),
                            int(item.session_date in evaluation_ordinals),
                            evaluation_ordinals.get(item.session_date),
                            item.raw_content_fingerprint, item.split_content_fingerprint,
                            _iso(item.completed_at_utc), _iso(item.first_observed_at_utc),
                            _iso(item.available_at_utc),
                        )
                        for item in evidence_set.observations
                    ],
                )

    @staticmethod
    def _save_observation_facts(connection, evidence_set) -> None:
        for item in evidence_set.observations:
            for adjustment, fingerprint, values in (
                ("raw", item.raw_content_fingerprint,
                 (item.raw_open_text, item.raw_high_text, item.raw_low_text, item.raw_close_text)),
                ("split", item.split_content_fingerprint,
                 (item.split_open_text, item.split_high_text, item.split_low_text, item.split_close_text)),
            ):
                connection.execute(
                    """INSERT OR IGNORE INTO market_bar_observation_facts VALUES
                    (?, ?, ?, '1Day', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)""",
                    (
                        fingerprint, evidence_set.symbol, item.session_date.isoformat(),
                        adjustment, item.feed.value, *values, item.volume, item.source,
                        _iso(item.completed_at_utc), _iso(item.first_observed_at_utc),
                        _iso(item.available_at_utc), _iso(evidence_set.created_at_utc),
                    ),
                )

    def save_study(self, study: SpectralHistoricalStudy) -> None:
        with closing(self._database.connect()) as connection:
            existing = connection.execute(
                "SELECT request_fingerprint FROM spectral_historical_studies WHERE study_id = ?",
                (str(study.study_id),),
            ).fetchone()
            if existing is not None:
                if existing["request_fingerprint"] != study.request_fingerprint:
                    raise ValueError("stored historical study identity conflicts")
                return
            with connection:
                counts = {
                    status: study.count(status) for status in SpectralHistoricalPointStatus
                }
                connection.execute(
                    """INSERT INTO spectral_historical_studies VALUES
                    (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        str(study.study_id), str(study.parent_run_id), study.request_fingerprint,
                        study.session_id, study.request_id, study.symbol,
                        study.evaluation_start_session.isoformat(), study.evaluation_end_session.isoformat(),
                        study.acquisition_mode, study.evidence_mode,
                        str(study.evidence_set_id) if study.evidence_set_id else None,
                        study.status.value, study.expected_point_count,
                        counts[SpectralHistoricalPointStatus.COMPLETED],
                        counts[SpectralHistoricalPointStatus.COMPLETED_WITH_WARNINGS],
                        counts[SpectralHistoricalPointStatus.INVALID_INPUT],
                        counts[SpectralHistoricalPointStatus.FAILED],
                        counts[SpectralHistoricalPointStatus.CANCELLED],
                        counts[SpectralHistoricalPointStatus.NOT_RUN],
                        _iso(study.requested_at_utc), _iso(study.started_at_utc),
                        _iso(study.completed_at_utc), study.created_by, study.reason,
                        study.software_version, study.source_revision, study.worktree_state,
                        _json(study.warnings), study.error_code, study.error_summary,
                        int(study.execution_allowed), int(study.live_allowed), study.schema_version,
                    ),
                )
                connection.executemany(
                    "INSERT INTO spectral_historical_study_definitions VALUES (?, ?, ?, ?, ?, ?, ?)",
                    [
                        (
                            str(study.study_id), item.ordinal, str(item.definition_id),
                            item.definition_version, item.component_id, item.component_version,
                            item.schema_version,
                        )
                        for item in study.definitions
                    ],
                )
                connection.executemany(
                    """INSERT INTO spectral_historical_study_points VALUES
                    (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    [
                        (
                            str(item.study_id), item.evaluation_ordinal,
                            item.evaluation_session.isoformat(), _iso(item.official_close_utc),
                            item.definition_ordinal, str(item.definition_id),
                            item.definition_version, item.component_version, item.status.value,
                            str(item.child_run_id) if item.child_run_id else None,
                            str(item.operation_id) if item.operation_id else None,
                            str(item.attempt_id) if item.attempt_id else None,
                            str(item.evidence_bundle_id) if item.evidence_bundle_id else None,
                            _json(item.warnings), item.error_code, item.error_summary,
                            item.schema_version,
                        )
                        for item in study.points
                    ],
                )

    def get_study(self, study_id: UUID) -> SpectralHistoricalStudy | None:
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                "SELECT * FROM spectral_historical_studies WHERE study_id = ?",
                (str(study_id),),
            ).fetchone()
            return self._load_study(connection, row) if row is not None else None

    def list_studies(
        self, query: SpectralHistoricalStudyQuery = SpectralHistoricalStudyQuery()
    ) -> tuple[SpectralHistoricalStudy, ...]:
        clauses: list[str] = []
        parameters: list[object] = []
        if query.study_id:
            clauses.append("s.study_id = ?")
            parameters.append(str(query.study_id))
        if query.symbol:
            clauses.append("s.symbol = ?")
            parameters.append(query.symbol)
        if query.status:
            clauses.append("s.status = ?")
            parameters.append(query.status.value)
        if query.definition_id:
            clauses.append(
                "EXISTS (SELECT 1 FROM spectral_historical_study_definitions d "
                "WHERE d.study_id = s.study_id AND d.definition_id = ?)"
            )
            parameters.append(str(query.definition_id))
        if query.created_from_utc:
            clauses.append("s.completed_at_utc >= ?")
            parameters.append(_iso(query.created_from_utc))
        if query.created_to_utc:
            clauses.append("s.completed_at_utc < ?")
            parameters.append(_iso(query.created_to_utc))
        if query.warning_only:
            clauses.append("(s.status <> 'completed' OR s.warnings_text <> '[]')")
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        parameters.append(query.limit)
        with closing(self._database.connect()) as connection:
            rows = connection.execute(
                "SELECT * FROM spectral_historical_studies s" + where
                + " ORDER BY s.completed_at_utc DESC, s.study_id DESC LIMIT ?",
                parameters,
            ).fetchall()
            return tuple(self._load_study(connection, row) for row in rows)

    def find_historical_evidence_set(
        self,
        *,
        symbol: str,
        evaluation_start_session: date,
        evaluation_end_session: date,
        feed: DataFeed,
        evidence_mode: ResearchEvidenceMode,
    ) -> SpectralHistoricalEvidenceSet | None:
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                """SELECT evidence_set_id FROM spectral_historical_evidence_sets
                WHERE symbol = ? AND evaluation_start_session = ?
                  AND evaluation_end_session = ? AND feed = ? AND evidence_mode = ?
                ORDER BY created_at_utc DESC, evidence_set_id DESC LIMIT 1""",
                (
                    symbol.strip().upper(), evaluation_start_session.isoformat(),
                    evaluation_end_session.isoformat(), feed.value, evidence_mode.value,
                ),
            ).fetchone()
            return self._load_evidence(connection, UUID(row["evidence_set_id"])) if row else None

    def get_evidence_set(self, evidence_set_id: UUID) -> SpectralHistoricalEvidenceSet | None:
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                "SELECT 1 FROM spectral_historical_evidence_sets WHERE evidence_set_id = ?",
                (str(evidence_set_id),),
            ).fetchone()
            return self._load_evidence(connection, evidence_set_id) if row else None

    @staticmethod
    def _load_study(connection, row) -> SpectralHistoricalStudy:
        definitions = tuple(
            SpectralHistoricalDefinitionSelection(
                int(item["ordinal"]), UUID(item["definition_id"]),
                int(item["definition_version"]), item["component_id"],
                item["component_version"], int(item["schema_version"]),
            )
            for item in connection.execute(
                "SELECT * FROM spectral_historical_study_definitions WHERE study_id = ? ORDER BY ordinal",
                (row["study_id"],),
            )
        )
        points = tuple(
            SpectralHistoricalStudyPoint(
                UUID(item["study_id"]), int(item["evaluation_ordinal"]),
                date.fromisoformat(item["evaluation_session"]), _dt(item["official_close_utc"]),
                int(item["definition_ordinal"]), UUID(item["definition_id"]),
                int(item["definition_version"]), item["component_version"],
                SpectralHistoricalPointStatus(item["status"]),
                UUID(item["child_run_id"]) if item["child_run_id"] else None,
                UUID(item["operation_id"]) if item["operation_id"] else None,
                UUID(item["attempt_id"]) if item["attempt_id"] else None,
                UUID(item["evidence_bundle_id"]) if item["evidence_bundle_id"] else None,
                tuple(json.loads(item["warnings_text"])), item["error_code"],
                item["error_summary"], int(item["schema_version"]),
            )
            for item in connection.execute(
                """SELECT * FROM spectral_historical_study_points WHERE study_id = ?
                ORDER BY evaluation_ordinal, definition_ordinal""",
                (row["study_id"],),
            )
        )
        return SpectralHistoricalStudy(
            UUID(row["study_id"]), UUID(row["parent_run_id"]), row["request_fingerprint"],
            row["session_id"], row["request_id"], row["symbol"],
            date.fromisoformat(row["evaluation_start_session"]),
            date.fromisoformat(row["evaluation_end_session"]),
            row["acquisition_mode"], row["evidence_mode"],
            UUID(row["evidence_set_id"]) if row["evidence_set_id"] else None,
            definitions, points, SpectralHistoricalStudyStatus(row["status"]),
            _dt(row["requested_at_utc"]), _dt(row["started_at_utc"]),
            _dt(row["completed_at_utc"]), row["created_by"], row["reason"],
            row["software_version"], row["source_revision"], row["worktree_state"],
            tuple(json.loads(row["warnings_text"])), row["error_code"], row["error_summary"],
            bool(row["execution_allowed"]), bool(row["live_allowed"]), int(row["schema_version"]),
        )

    def _load_evidence(self, connection, evidence_set_id: UUID) -> SpectralHistoricalEvidenceSet:
        row = connection.execute(
            "SELECT * FROM spectral_historical_evidence_sets WHERE evidence_set_id = ?",
            (str(evidence_set_id),),
        ).fetchone()
        calendar = self._load_calendar(connection, row["calendar_snapshot_id"])
        mapping = self._load_mapping(connection, row["mapping_id"])
        actions = self._load_actions(connection, row["corporate_action_snapshot_id"])
        observations: list[ResearchBarObservation] = []
        evaluation_dates: list[date] = []
        for source in connection.execute(
            """SELECT * FROM spectral_historical_evidence_observations
            WHERE evidence_set_id = ? ORDER BY ordinal""",
            (str(evidence_set_id),),
        ):
            raw = connection.execute(
                "SELECT * FROM market_bar_observation_facts WHERE content_fingerprint = ?",
                (source["raw_fact_fingerprint"],),
            ).fetchone()
            split = connection.execute(
                "SELECT * FROM market_bar_observation_facts WHERE content_fingerprint = ?",
                (source["split_fact_fingerprint"],),
            ).fetchone()
            session = date.fromisoformat(source["session_date"])
            if source["is_evaluation_session"]:
                evaluation_dates.append(session)
            observations.append(ResearchBarObservation(
                int(source["ordinal"]), session, _dt(source["completed_at_utc"]),
                _dt(source["first_observed_at_utc"]), _dt(source["available_at_utc"]),
                raw["open_text"], raw["high_text"], raw["low_text"], raw["close_text"],
                split["open_text"], split["high_text"], split["low_text"], split["close_text"],
                int(split["volume"]), DataFeed(split["feed"]), split["source"],
                raw["content_fingerprint"], split["content_fingerprint"],
            ))
        session_map = {item.session_date: item for item in calendar.sessions}
        return SpectralHistoricalEvidenceSet(
            evidence_set_id, row["content_fingerprint"], row["symbol"], DataFeed(row["feed"]),
            Timeframe(row["timeframe"]), ResearchEvidenceMode(row["evidence_mode"]),
            SpectralEvidenceAcquisitionMode(row["acquisition_mode"]), calendar, mapping,
            actions, tuple(session_map[item] for item in evaluation_dates),
            tuple(observations), _dt(row["requested_at_utc"]), _dt(row["created_at_utc"]),
            tuple(json.loads(row["warnings_text"])), int(row["schema_version"]),
        )

    @staticmethod
    def _load_calendar(connection, snapshot_id: str) -> ResearchMarketCalendarSnapshot:
        row = connection.execute(
            "SELECT * FROM research_market_calendar_snapshots WHERE snapshot_id = ?", (snapshot_id,)
        ).fetchone()
        sessions = tuple(
            ResearchCalendarSession(
                int(item["ordinal"]), date.fromisoformat(item["session_date"]),
                _dt(item["open_utc"]), _dt(item["close_utc"]),
                _dt(item["break_start_utc"]) if item["break_start_utc"] else None,
                _dt(item["break_end_utc"]) if item["break_end_utc"] else None,
                bool(item["early_close"]),
            )
            for item in connection.execute(
                "SELECT * FROM research_market_calendar_sessions WHERE snapshot_id = ? ORDER BY ordinal",
                (snapshot_id,),
            )
        )
        return ResearchMarketCalendarSnapshot(
            UUID(row["snapshot_id"]), row["calendar_definition_id"], row["engine_name"],
            row["engine_version"], row["exchange_calendar_name"],
            date.fromisoformat(row["covered_start"]), date.fromisoformat(row["covered_end"]),
            row["schedule_fingerprint"], _dt(row["observed_at_utc"]),
            _dt(row["created_at_utc"]), sessions, int(row["schema_version"]),
        )

    @staticmethod
    def _load_mapping(connection, mapping_id: str) -> ResearchCalendarSymbolMapping:
        row = connection.execute(
            "SELECT * FROM research_market_calendar_symbol_mappings WHERE mapping_id = ?", (mapping_id,)
        ).fetchone()
        return ResearchCalendarSymbolMapping(
            UUID(row["mapping_id"]), int(row["mapping_version"]), row["symbol"],
            row["asset_class"], row["calendar_definition_id"],
            date.fromisoformat(row["effective_start"]), _date(row["effective_end"]),
            _dt(row["created_at_utc"]), row["created_by"], row["reason"],
            int(row["schema_version"]),
        )

    @staticmethod
    def _load_actions(connection, snapshot_id: str) -> ResearchCorporateActionSnapshot:
        row = connection.execute(
            "SELECT * FROM research_corporate_action_snapshots WHERE snapshot_id = ?", (snapshot_id,)
        ).fetchone()
        events = tuple(
            ResearchCorporateActionEvent(
                int(item["ordinal"]), item["provider_event_id"], item["symbol"],
                item["action_type"], _date(item["declaration_date"]), _date(item["ex_date"]),
                _date(item["effective_date"]), _date(item["process_date"]),
                item["ratio_text"], item["raw_event_fingerprint"], bool(item["supported"]),
            )
            for item in connection.execute(
                "SELECT * FROM research_corporate_action_events WHERE snapshot_id = ? ORDER BY ordinal",
                (snapshot_id,),
            )
        )
        return ResearchCorporateActionSnapshot(
            UUID(row["snapshot_id"]), row["provider_name"], row["query_identity"],
            _dt(row["requested_at_utc"]), _dt(row["received_at_utc"]),
            date.fromisoformat(row["covered_start"]), date.fromisoformat(row["covered_end"]),
            row["response_fingerprint"], ResearchEvidenceMode(row["evidence_mode"]),
            events, int(row["schema_version"]),
        )


__all__ = ["SQLiteSpectralHistoricalStudyStore"]
