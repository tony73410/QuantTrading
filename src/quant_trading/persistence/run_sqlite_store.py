"""SQLite repository and read model for unified algorithm run history."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from quant_trading.run_history.models import (
    AlgorithmRun,
    AlgorithmRunStatus,
    AlgorithmRunType,
    RunArtifactView,
    RunBinding,
    RunBindingType,
    RunDetailView,
    RunDisplayField,
    RunExecutionMode,
    RunMessage,
    RunMessageSeverity,
    RunRelationship,
    RunRelationshipType,
    RunQuery,
    RunStage,
    RunStageName,
    RunStageStatus,
    RunSummary,
    WorktreeState,
)

from .sqlite_database import CentralSQLiteDatabase


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="microseconds")


def _datetime(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value).astimezone(UTC) if value else None


def _field(name: str, value: object) -> RunDisplayField:
    return RunDisplayField(name, "—" if value is None or value == "" else str(value))


class SQLiteRunHistoryRepository:
    """Own run-history SQL while exposing only typed, read-only views to GUI code."""

    def __init__(self, database_path: Path | str) -> None:
        self._database = CentralSQLiteDatabase(database_path)

    def initialize(self) -> None:
        self._database.initialize()

    def create_run(self, run: AlgorithmRun, *, symbols: tuple[str, ...]) -> None:
        normalized_symbols = tuple(sorted({symbol.strip().upper() for symbol in symbols if symbol.strip()}))
        with closing(self._database.connect()) as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute(
                    """
                    INSERT INTO algorithm_runs (
                        run_id, parent_run_id, run_type, status, session_id,
                        request_id, started_at_utc, completed_at_utc,
                        market_data_as_of_utc, portfolio_snapshot_id,
                        configuration_snapshot_id, strategy_version_id,
                        trigger_source, execution_mode, created_by,
                        software_version, source_revision, worktree_state,
                        notes, created_at_utc
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    self._run_values(run) + (_iso(datetime.now(UTC)),),
                )
                connection.executemany(
                    "INSERT INTO algorithm_run_symbols (run_id, symbol) VALUES (?, ?)",
                    ((str(run.run_id), symbol) for symbol in normalized_symbols),
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise

    def update_run(self, run: AlgorithmRun) -> None:
        with closing(self._database.connect()) as connection:
            cursor = connection.execute(
                """
                UPDATE algorithm_runs SET
                    parent_run_id = ?, run_type = ?, status = ?, session_id = ?,
                    request_id = ?, started_at_utc = ?, completed_at_utc = ?,
                    market_data_as_of_utc = ?, portfolio_snapshot_id = ?,
                    configuration_snapshot_id = ?, strategy_version_id = ?,
                    trigger_source = ?, execution_mode = ?, created_by = ?,
                    software_version = ?, source_revision = ?, worktree_state = ?,
                    notes = ?
                WHERE run_id = ? AND status IN ('pending', 'running')
                """,
                self._run_values(run)[1:] + (str(run.run_id),),
            )
            if cursor.rowcount != 1:
                raise KeyError(f"unknown run {run.run_id}")
            connection.commit()

    @staticmethod
    def _run_values(run: AlgorithmRun) -> tuple[object, ...]:
        return (
            str(run.run_id),
            str(run.parent_run_id) if run.parent_run_id else None,
            run.run_type.value,
            run.status.value,
            run.session_id,
            run.request_id,
            _iso(run.started_at_utc),
            _iso(run.completed_at_utc) if run.completed_at_utc else None,
            _iso(run.market_data_as_of_utc) if run.market_data_as_of_utc else None,
            str(run.portfolio_snapshot_id) if run.portfolio_snapshot_id else None,
            str(run.configuration_snapshot_id) if run.configuration_snapshot_id else None,
            run.strategy_version_id,
            run.trigger_source,
            run.execution_mode.value,
            run.created_by,
            run.software_version,
            run.source_revision,
            run.worktree_state.value,
            run.notes,
        )

    def get_run(self, run_id: UUID) -> AlgorithmRun | None:
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                "SELECT * FROM algorithm_runs WHERE run_id = ?", (str(run_id),)
            ).fetchone()
        return self._run_from_row(row) if row else None

    def save_stage(self, stage: RunStage) -> None:
        with closing(self._database.connect()) as connection:
            connection.execute(
                """
                INSERT INTO algorithm_run_stages (
                    stage_id, run_id, stage_name, sequence, status,
                    started_at_utc, completed_at_utc, result_type, result_id,
                    error_code, error_summary
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._stage_values(stage),
            )
            connection.commit()

    def update_stage(self, stage: RunStage) -> None:
        with closing(self._database.connect()) as connection:
            cursor = connection.execute(
                """
                UPDATE algorithm_run_stages SET
                    run_id = ?, stage_name = ?, sequence = ?, status = ?,
                    started_at_utc = ?, completed_at_utc = ?, result_type = ?,
                    result_id = ?, error_code = ?, error_summary = ?
                WHERE stage_id = ? AND status IN ('pending', 'running')
                """,
                self._stage_values(stage)[1:] + (str(stage.stage_id),),
            )
            if cursor.rowcount != 1:
                raise KeyError(f"unknown stage {stage.stage_id}")
            connection.commit()

    @staticmethod
    def _stage_values(stage: RunStage) -> tuple[object, ...]:
        return (
            str(stage.stage_id),
            str(stage.run_id),
            stage.name.value,
            stage.sequence,
            stage.status.value,
            _iso(stage.started_at_utc),
            _iso(stage.completed_at_utc) if stage.completed_at_utc else None,
            stage.result_type,
            stage.result_id,
            stage.error_code,
            stage.error_summary,
        )

    def save_binding(self, binding: RunBinding) -> None:
        with closing(self._database.connect()) as connection:
            connection.execute(
                """
                INSERT INTO algorithm_run_bindings (
                    binding_id, run_id, binding_type, binding_key,
                    binding_version, source_reference
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    str(binding.binding_id), str(binding.run_id),
                    binding.binding_type.value, binding.binding_key,
                    binding.binding_version, binding.source_reference,
                ),
            )
            connection.commit()

    def save_message(self, message: RunMessage) -> None:
        with closing(self._database.connect()) as connection:
            connection.execute(
                """
                INSERT INTO algorithm_run_messages (
                    message_id, run_id, stage_id, severity, code, message,
                    created_at_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(message.message_id), str(message.run_id),
                    str(message.stage_id) if message.stage_id else None,
                    message.severity.value, message.code, message.message,
                    _iso(message.created_at_utc),
                ),
            )
            connection.commit()

    def list_runs(self, query: RunQuery = RunQuery()) -> tuple[RunSummary, ...]:
        clauses: list[str] = []
        values: list[object] = []
        if query.run_id_text:
            clauses.append("r.run_id LIKE ?")
            values.append(f"{query.run_id_text}%")
        if query.symbol:
            clauses.append(
                "EXISTS (SELECT 1 FROM algorithm_run_symbols s "
                "WHERE s.run_id = r.run_id AND s.symbol = ?)"
            )
            values.append(query.symbol)
        if query.run_type:
            clauses.append("r.run_type = ?")
            values.append(query.run_type.value)
        if query.status:
            clauses.append("r.status = ?")
            values.append(query.status.value)
        if query.started_from_utc:
            clauses.append("r.started_at_utc >= ?")
            values.append(_iso(query.started_from_utc))
        if query.started_to_utc:
            clauses.append("r.started_at_utc < ?")
            values.append(_iso(query.started_to_utc))
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        sql = f"""
            SELECT r.*,
                (SELECT GROUP_CONCAT(symbol, ',') FROM (
                    SELECT symbol FROM algorithm_run_symbols
                    WHERE run_id = r.run_id ORDER BY symbol
                )) AS symbols_text,
                (SELECT COUNT(*) FROM algorithm_run_messages m
                    WHERE m.run_id = r.run_id AND m.severity = 'warning') AS warning_count,
                (SELECT COUNT(*) FROM algorithm_run_messages m
                    WHERE m.run_id = r.run_id AND m.severity = 'error') AS error_count
            FROM algorithm_runs r{where}
            ORDER BY r.started_at_utc DESC, r.run_id DESC
            LIMIT ?
        """
        values.append(query.limit)
        with closing(self._database.connect()) as connection:
            rows = connection.execute(sql, values).fetchall()
        return tuple(
            RunSummary(
                self._run_from_row(row),
                tuple(filter(None, (row["symbols_text"] or "").split(","))),
                int(row["warning_count"]),
                int(row["error_count"]),
            )
            for row in rows
        )

    def get_run_detail(self, run_id: UUID) -> RunDetailView | None:
        summaries = self.list_runs(RunQuery(run_id_text=str(run_id), limit=2))
        summary = next((item for item in summaries if item.run.run_id == run_id), None)
        if summary is None:
            return None
        with closing(self._database.connect()) as connection:
            stages = tuple(
                self._stage_from_row(row)
                for row in connection.execute(
                    "SELECT * FROM algorithm_run_stages WHERE run_id = ? ORDER BY sequence",
                    (str(run_id),),
                )
            )
            bindings = tuple(
                self._binding_from_row(row)
                for row in connection.execute(
                    "SELECT * FROM algorithm_run_bindings WHERE run_id = ? ORDER BY binding_type, binding_key",
                    (str(run_id),),
                )
            )
            messages = tuple(
                self._message_from_row(row)
                for row in connection.execute(
                    "SELECT * FROM algorithm_run_messages WHERE run_id = ? ORDER BY created_at_utc, message_id",
                    (str(run_id),),
                )
            )
            artifacts = self._load_artifacts(connection, run_id)
            relationships = self._load_relationships(connection, summary.run)
        return RunDetailView(
            summary, stages, bindings, messages, artifacts, relationships
        )

    @staticmethod
    def _load_relationships(connection, run) -> tuple[RunRelationship, ...]:
        relationships: set[tuple[RunRelationshipType, UUID]] = set()
        if run.parent_run_id is not None:
            relationships.add((RunRelationshipType.PARENT, run.parent_run_id))
        for row in connection.execute(
            "SELECT run_id FROM algorithm_runs WHERE parent_run_id = ? ORDER BY run_id",
            (str(run.run_id),),
        ):
            relationships.add((RunRelationshipType.CHILD, UUID(row["run_id"])))
        link_rows = connection.execute(
            """
            SELECT parent_run_id, child_run_id, source_run_id
            FROM target_position_standardized_state_links
            WHERE parent_run_id = ? OR child_run_id = ? OR source_run_id = ?
            """,
            (str(run.run_id), str(run.run_id), str(run.run_id)),
        ).fetchall()
        for row in link_rows:
            parent_id = UUID(row["parent_run_id"])
            child_id = UUID(row["child_run_id"])
            source_id = UUID(row["source_run_id"])
            if source_id != run.run_id:
                relationships.add((RunRelationshipType.SOURCE, source_id))
            if parent_id != run.run_id:
                relation = (
                    RunRelationshipType.LINKED_PREVIEW
                    if source_id == run.run_id
                    else RunRelationshipType.PARENT
                )
                relationships.add((relation, parent_id))
            if child_id != run.run_id and parent_id == run.run_id:
                relationships.add((RunRelationshipType.CHILD, child_id))
        decision_link_rows = connection.execute(
            """
            SELECT decision_run_id, linked_parent_run_id, target_child_run_id,
                   standardized_state_run_id
            FROM target_adjustment_decision_source_links
            WHERE decision_run_id = ? OR linked_parent_run_id = ?
               OR target_child_run_id = ? OR standardized_state_run_id = ?
            """,
            (str(run.run_id), str(run.run_id), str(run.run_id), str(run.run_id)),
        ).fetchall()
        for row in decision_link_rows:
            decision_id = UUID(row["decision_run_id"])
            parent_id = UUID(row["linked_parent_run_id"])
            target_child_id = UUID(row["target_child_run_id"])
            source_id = UUID(row["standardized_state_run_id"])
            if decision_id == run.run_id:
                relationships.add((RunRelationshipType.PARENT, parent_id))
                relationships.add((RunRelationshipType.SOURCE, target_child_id))
                relationships.add((RunRelationshipType.SOURCE, source_id))
            elif run.run_id in {target_child_id, source_id}:
                relationships.add((RunRelationshipType.LINKED_PREVIEW, decision_id))
            elif run.run_id == parent_id:
                relationships.add((RunRelationshipType.CHILD, decision_id))
        risk_link_rows = connection.execute(
            """
            SELECT risk_run_id, decision_run_id, linked_parent_run_id,
                   target_child_run_id, standardized_state_run_id
            FROM target_adjustment_risk_source_links
            WHERE risk_run_id = ? OR decision_run_id = ? OR linked_parent_run_id = ?
               OR target_child_run_id = ? OR standardized_state_run_id = ?
            """,
            (str(run.run_id),) * 5,
        ).fetchall()
        for row in risk_link_rows:
            risk_id = UUID(row["risk_run_id"])
            decision_id = UUID(row["decision_run_id"])
            upstream = {
                UUID(row["linked_parent_run_id"]),
                UUID(row["target_child_run_id"]),
                UUID(row["standardized_state_run_id"]),
            }
            if risk_id == run.run_id:
                relationships.add((RunRelationshipType.PARENT, decision_id))
                for source_id in upstream:
                    relationships.add((RunRelationshipType.SOURCE, source_id))
            elif decision_id == run.run_id:
                relationships.add((RunRelationshipType.CHILD, risk_id))
            elif run.run_id in upstream:
                relationships.add((RunRelationshipType.LINKED_PREVIEW, risk_id))
        exposure_cap_rows = connection.execute(
            """
            SELECT exposure_cap_run_id, phase6a_run_id, decision_run_id,
                   linked_parent_run_id, target_child_run_id, standardized_state_run_id
            FROM target_adjustment_exposure_cap_source_links
            WHERE exposure_cap_run_id = ? OR phase6a_run_id = ? OR decision_run_id = ?
               OR linked_parent_run_id = ? OR target_child_run_id = ?
               OR standardized_state_run_id = ?
            """,
            (str(run.run_id),) * 6,
        ).fetchall()
        for row in exposure_cap_rows:
            cap_id = UUID(row["exposure_cap_run_id"])
            phase6a_id = UUID(row["phase6a_run_id"])
            upstream = {
                UUID(row["decision_run_id"]), UUID(row["linked_parent_run_id"]),
                UUID(row["target_child_run_id"]), UUID(row["standardized_state_run_id"]),
            }
            if cap_id == run.run_id:
                relationships.add((RunRelationshipType.PARENT, phase6a_id))
                for source_id in upstream:
                    relationships.add((RunRelationshipType.SOURCE, source_id))
            elif phase6a_id == run.run_id:
                relationships.add((RunRelationshipType.CHILD, cap_id))
            elif run.run_id in upstream:
                relationships.add((RunRelationshipType.LINKED_PREVIEW, cap_id))
        cash_floor_rows = connection.execute(
            """
            SELECT cash_floor_run_id, phase6b_run_id, phase6a_run_id,
                   decision_run_id, linked_parent_run_id, target_child_run_id,
                   standardized_state_run_id
            FROM target_adjustment_cash_floor_source_links
            WHERE cash_floor_run_id = ? OR phase6b_run_id = ? OR phase6a_run_id = ?
               OR decision_run_id = ? OR linked_parent_run_id = ?
               OR target_child_run_id = ? OR standardized_state_run_id = ?
            """,
            (str(run.run_id),) * 7,
        ).fetchall()
        for row in cash_floor_rows:
            cash_floor_id = UUID(row["cash_floor_run_id"])
            phase6b_id = UUID(row["phase6b_run_id"])
            upstream = {
                UUID(row["phase6a_run_id"]), UUID(row["decision_run_id"]),
                UUID(row["linked_parent_run_id"]), UUID(row["target_child_run_id"]),
                UUID(row["standardized_state_run_id"]),
            }
            if cash_floor_id == run.run_id:
                relationships.add((RunRelationshipType.PARENT, phase6b_id))
                for source_id in upstream:
                    relationships.add((RunRelationshipType.SOURCE, source_id))
            elif phase6b_id == run.run_id:
                relationships.add((RunRelationshipType.CHILD, cash_floor_id))
            elif run.run_id in upstream:
                relationships.add(
                    (RunRelationshipType.LINKED_PREVIEW, cash_floor_id)
                )
        asset_cash_rows = connection.execute(
            """
            SELECT asset_cash_run_id, phase6c_run_id, phase6b_run_id,
                   phase6a_run_id, decision_run_id, linked_parent_run_id,
                   target_child_run_id, standardized_state_run_id,
                   capital_snapshot_run_id
            FROM target_adjustment_research_asset_cash_source_links
            WHERE asset_cash_run_id = ? OR phase6c_run_id = ? OR phase6b_run_id = ?
               OR phase6a_run_id = ? OR decision_run_id = ?
               OR linked_parent_run_id = ? OR target_child_run_id = ?
               OR standardized_state_run_id = ? OR capital_snapshot_run_id = ?
            """,
            (str(run.run_id),) * 9,
        ).fetchall()
        for row in asset_cash_rows:
            asset_cash_id = UUID(row["asset_cash_run_id"])
            phase6c_id = UUID(row["phase6c_run_id"])
            upstream = {
                UUID(row["phase6b_run_id"]), UUID(row["phase6a_run_id"]),
                UUID(row["decision_run_id"]), UUID(row["linked_parent_run_id"]),
                UUID(row["target_child_run_id"]),
                UUID(row["standardized_state_run_id"]),
                UUID(row["capital_snapshot_run_id"]),
            }
            if asset_cash_id == run.run_id:
                relationships.add((RunRelationshipType.PARENT, phase6c_id))
                for source_id in upstream:
                    relationships.add((RunRelationshipType.SOURCE, source_id))
            elif phase6c_id == run.run_id:
                relationships.add((RunRelationshipType.CHILD, asset_cash_id))
            elif run.run_id in upstream:
                relationships.add(
                    (RunRelationshipType.LINKED_PREVIEW, asset_cash_id)
                )
        return tuple(
            RunRelationship(kind, related_run_id)
            for kind, related_run_id in sorted(
                relationships, key=lambda item: (item[0].value, str(item[1]))
            )
        )

    @staticmethod
    def _run_from_row(row: sqlite3.Row) -> AlgorithmRun:
        started = _datetime(row["started_at_utc"])
        if started is None:
            raise sqlite3.DatabaseError("algorithm run is missing started_at_utc")
        return AlgorithmRun(
            UUID(row["run_id"]),
            UUID(row["parent_run_id"]) if row["parent_run_id"] else None,
            AlgorithmRunType(row["run_type"]),
            AlgorithmRunStatus(row["status"]),
            row["session_id"], row["request_id"], started,
            _datetime(row["completed_at_utc"]),
            _datetime(row["market_data_as_of_utc"]),
            UUID(row["portfolio_snapshot_id"]) if row["portfolio_snapshot_id"] else None,
            UUID(row["configuration_snapshot_id"]) if row["configuration_snapshot_id"] else None,
            row["strategy_version_id"], row["trigger_source"],
            RunExecutionMode(row["execution_mode"]), row["created_by"],
            row["software_version"], row["source_revision"],
            WorktreeState(row["worktree_state"]), row["notes"],
        )

    @staticmethod
    def _stage_from_row(row: sqlite3.Row) -> RunStage:
        started = _datetime(row["started_at_utc"])
        if started is None:
            raise sqlite3.DatabaseError("algorithm stage is missing started_at_utc")
        return RunStage(
            UUID(row["stage_id"]), UUID(row["run_id"]),
            RunStageName(row["stage_name"]), int(row["sequence"]),
            RunStageStatus(row["status"]), started,
            _datetime(row["completed_at_utc"]), row["result_type"],
            row["result_id"], row["error_code"], row["error_summary"],
        )

    @staticmethod
    def _binding_from_row(row: sqlite3.Row) -> RunBinding:
        return RunBinding(
            UUID(row["binding_id"]), UUID(row["run_id"]),
            RunBindingType(row["binding_type"]), row["binding_key"],
            row["binding_version"], row["source_reference"],
        )

    @staticmethod
    def _message_from_row(row: sqlite3.Row) -> RunMessage:
        created = _datetime(row["created_at_utc"])
        if created is None:
            raise sqlite3.DatabaseError("algorithm message is missing created_at_utc")
        return RunMessage(
            UUID(row["message_id"]), UUID(row["run_id"]),
            UUID(row["stage_id"]) if row["stage_id"] else None,
            RunMessageSeverity(row["severity"]), row["code"], row["message"], created,
        )

    @staticmethod
    def _load_artifacts(
        connection: sqlite3.Connection, run_id: UUID
    ) -> tuple[RunArtifactView, ...]:
        artifacts: list[RunArtifactView] = []
        factor_runs = connection.execute(
            """
            SELECT c.*, s.calculated_at_utc
            FROM factor_calculation_runs c
            LEFT JOIN factor_snapshots s ON s.snapshot_id = c.snapshot_id
            WHERE c.algorithm_run_id = ? ORDER BY c.started_at_utc
            """,
            (str(run_id),),
        ).fetchall()
        for calculation in factor_runs:
            children = ()
            if calculation["snapshot_id"]:
                result_rows = connection.execute(
                    """
                    SELECT * FROM factor_results WHERE snapshot_id = ?
                    ORDER BY factor_name
                    """,
                    (calculation["snapshot_id"],),
                ).fetchall()
                children = tuple(
                    RunArtifactView(
                        "factor_result", f"{row['snapshot_id']}:{row['factor_name']}",
                        RunStageName.FACTOR.value, calculation["symbol"], row["status"],
                        f"{row['factor_name']} {row['factor_version']} = {row['value_text'] or '—'}",
                        _datetime(row["calculated_at_utc"]),
                        (
                            _field("unit", row["unit"]),
                            _field("parameters", row["parameters_json"]),
                            _field("quality flags", row["quality_flags_json"]),
                        ),
                    )
                    for row in result_rows
                )
            artifacts.append(
                RunArtifactView(
                    "factor_calculation", calculation["run_id"],
                    RunStageName.FACTOR.value, calculation["symbol"],
                    calculation["status"],
                    f"Factor calculation for {calculation['symbol']}",
                    _datetime(calculation["completed_at_utc"] or calculation["started_at_utc"]),
                    (
                        _field("snapshot id", calculation["snapshot_id"]),
                        _field("as of", calculation["as_of_utc"]),
                        _field("timeframe", calculation["timeframe"]),
                        _field("adjustment", calculation["adjustment"]),
                        _field("feed", calculation["feed"]),
                        _field("error", calculation["error_summary"]),
                    ),
                    children,
                )
            )
        decisions = connection.execute(
            "SELECT * FROM decision_results WHERE run_id = ? ORDER BY created_at_utc",
            (str(run_id),),
        ).fetchall()
        for decision in decisions:
            intent_rows = connection.execute(
                "SELECT * FROM trade_intents WHERE decision_id = ? ORDER BY created_at_utc",
                (decision["decision_id"],),
            ).fetchall()
            condition_rows = connection.execute(
                """
                SELECT * FROM decision_condition_results
                WHERE decision_id = ? ORDER BY evaluation_order
                """,
                (decision["decision_id"],),
            ).fetchall()
            condition_artifacts = tuple(
                RunArtifactView(
                    "decision_condition",
                    f"{row['decision_id']}:{row['evaluation_order']}",
                    RunStageName.DECISION.value,
                    None,
                    "matched" if row["matched"] else "not_matched",
                    (
                        f"{row['factor_name']} {row['factor_version']}: "
                        f"{row['input_value']} {row['operator']} {row['threshold']}"
                    ),
                    _datetime(decision["created_at_utc"]),
                    (
                        _field("Factor component", row["factor_component_id"]),
                        _field("Factor snapshot", row["factor_snapshot_id"]),
                        _field("Factor status", row["factor_status"]),
                        _field("input unit", row["input_unit"]),
                        _field("matched", bool(row["matched"])),
                    ),
                )
                for row in condition_rows
            )
            intent_artifacts: list[RunArtifactView] = []
            for row in intent_rows:
                sizing_rows = connection.execute(
                    """
                    SELECT * FROM trade_intent_sizing_inputs
                    WHERE intent_id = ? ORDER BY ordinal
                    """,
                    (row["intent_id"],),
                ).fetchall()
                sizing_artifacts = tuple(
                    RunArtifactView(
                        "decision_sizing_input",
                        f"{item['intent_id']}:{item['ordinal']}",
                        RunStageName.DECISION.value,
                        row["symbol"],
                        "captured",
                        f"{item['input_name']} = {item['value_text']}",
                        _datetime(row["created_at_utc"]),
                        (_field("source", item["source_group"]),),
                    )
                    for item in sizing_rows
                )
                intent_artifacts.append(
                    RunArtifactView(
                        "trade_intent", row["intent_id"], RunStageName.DECISION.value,
                        row["symbol"], row["action"],
                        f"{row['action'].upper()} desired change {row['desired_change'] or '—'} {row['exposure_unit'] or ''}".strip(),
                        _datetime(row["created_at_utc"]),
                        (
                            _field("current exposure", row["current_exposure"]),
                            _field("target exposure", row["target_exposure"]),
                            _field("desired change", row["desired_change"]),
                            _field("requested notional", row["requested_notional"]),
                            _field("reason codes", row["reason_codes_json"]),
                            _field("factor snapshot", row["factor_snapshot_id"]),
                        ),
                        sizing_artifacts,
                    )
                )
            children = condition_artifacts + tuple(intent_artifacts)
            artifacts.append(
                RunArtifactView(
                    "decision_result", decision["decision_id"],
                    RunStageName.DECISION.value,
                    intent_rows[0]["symbol"] if intent_rows else None,
                    decision["status"],
                    f"{decision['policy_name']} {decision['policy_version']}",
                    _datetime(decision["created_at_utc"]),
                    (
                        _field("as of", decision["as_of_utc"]),
                        _field("parameters", decision["policy_parameters_json"]),
                        _field("reason codes", decision["reason_codes_json"]),
                        _field("trace status", decision["trace_status"]),
                    ),
                    children,
                )
            )
        risk_rows = connection.execute(
            "SELECT * FROM risk_decisions WHERE run_id = ? ORDER BY evaluated_at_utc",
            (str(run_id),),
        ).fetchall()
        for risk in risk_rows:
            rules = connection.execute(
                """
                SELECT * FROM risk_rule_results WHERE risk_decision_id = ?
                ORDER BY evaluation_order
                """,
                (risk["risk_decision_id"],),
            ).fetchall()
            children = tuple(
                RunArtifactView(
                    "risk_rule_result",
                    f"{row['risk_decision_id']}:{row['evaluation_order']}",
                    RunStageName.RISK.value, risk["symbol"], row["decision"],
                    f"{row['evaluation_order'] + 1}. {row['rule_name']} {row['rule_version']}",
                    _datetime(risk["evaluated_at_utc"]),
                    (
                        _field("reason codes", row["reason_codes_json"]),
                        _field("approved target", row["approved_target"]),
                        _field("approved quantity", row["approved_quantity"]),
                        _field("approved notional", row["approved_notional"]),
                        _field("warnings", row["warnings_json"]),
                    ),
                )
                for row in rules
            )
            artifacts.append(
                RunArtifactView(
                    "risk_decision", risk["risk_decision_id"],
                    RunStageName.RISK.value, risk["symbol"], risk["decision"],
                    f"Risk {risk['decision']} for {risk['symbol']}",
                    _datetime(risk["evaluated_at_utc"]),
                    (
                        _field("source intent", risk["source_trade_intent_id"]),
                        _field("original target", risk["original_target"]),
                        _field("approved target", risk["approved_target"]),
                        _field("original notional", risk["original_notional"]),
                        _field("approved notional", risk["approved_notional"]),
                        _field("reason codes", risk["reason_codes_json"]),
                        _field("warnings", risk["warnings_json"]),
                        _field("manual review", bool(risk["requires_manual_review"])),
                    ),
                    children,
                )
            )
        capital_rows = connection.execute(
            """
            SELECT * FROM capital_allocation_operations
            WHERE run_id = ? ORDER BY requested_at_utc, operation_id
            """,
            (str(run_id),),
        ).fetchall()
        for operation in capital_rows:
            balance_children: tuple[RunArtifactView, ...] = ()
            if operation["result_snapshot_id"]:
                balances = connection.execute(
                    """
                    SELECT sb.balance, b.bucket_id, b.bucket_type, b.symbol,
                           b.currency
                    FROM capital_snapshot_balances sb
                    JOIN capital_plan_buckets b ON b.bucket_id = sb.bucket_id
                    WHERE sb.snapshot_id = ?
                    ORDER BY CASE b.bucket_type
                        WHEN 'locked_reserve' THEN 0
                        WHEN 'tactical_reserve' THEN 1
                        ELSE 2 END, b.symbol, b.bucket_id
                    """,
                    (operation["result_snapshot_id"],),
                ).fetchall()
                balance_children = tuple(
                    RunArtifactView(
                        "capital_bucket_balance",
                        f"{operation['result_snapshot_id']}:{item['bucket_id']}",
                        RunStageName.ALLOCATION.value,
                        item["symbol"],
                        "conserved",
                        (
                            f"{item['symbol'] or item['bucket_type']} = "
                            f"{item['balance']} {item['currency']}"
                        ),
                        _datetime(operation["completed_at_utc"]),
                        (
                            _field("bucket type", item["bucket_type"]),
                            _field("bucket id", item["bucket_id"]),
                        ),
                    )
                    for item in balances
                )
            summary = (
                f"Capital plan creation: {operation['plan_name'] or '—'}"
                if operation["operation_type"] == "plan_create"
                else f"Capital asset transfer: {operation['amount_text'] or '—'} {operation['currency']}"
            )
            artifacts.append(
                RunArtifactView(
                    "capital_allocation_operation",
                    operation["operation_id"],
                    RunStageName.ALLOCATION.value,
                    None,
                    operation["status"],
                    summary,
                    _datetime(operation["completed_at_utc"]),
                    (
                        _field(
                            "plan id",
                            operation["resolved_plan_id"]
                            or operation["requested_plan_id"],
                        ),
                        _field("snapshot id", operation["result_snapshot_id"]),
                        _field("transfer id", operation["transfer_id"]),
                        _field("research cash basis", operation["account_cash_basis_text"]),
                        _field("locked reserve", operation["locked_reserve_text"]),
                        _field("tactical reserve", operation["tactical_reserve_text"]),
                        _field("source bucket", operation["source_bucket_id"]),
                        _field("destination bucket", operation["destination_bucket_id"]),
                        _field("amount", operation["amount_text"]),
                        _field("reason", operation["reason"]),
                        _field("error", operation["error_summary"]),
                    ),
                    balance_children,
                )
            )
        state_rows = connection.execute(
            """
            SELECT * FROM asset_state_operations
            WHERE run_id = ? ORDER BY requested_at_utc, attempt_id
            """,
            (str(run_id),),
        ).fetchall()
        for operation in state_rows:
            state_children: tuple[RunArtifactView, ...] = ()
            if operation["result_snapshot_id"]:
                snapshot = connection.execute(
                    """
                    SELECT * FROM asset_state_snapshots WHERE snapshot_id = ?
                    """,
                    (operation["result_snapshot_id"],),
                ).fetchone()
                if snapshot is not None:
                    state_children = (
                        RunArtifactView(
                            "asset_state_snapshot",
                            snapshot["snapshot_id"],
                            RunStageName.STATE.value,
                            snapshot["symbol"],
                            "immutable",
                            (
                                f"{snapshot['symbol']} = {snapshot['current_state_key']} "
                                f"(sequence {snapshot['sequence']})"
                            ),
                            _datetime(snapshot["created_at_utc"]),
                            (
                                _field("cycle id", snapshot["cycle_id"]),
                                _field("definition id", snapshot["definition_id"]),
                                _field("definition version", snapshot["definition_version"]),
                                _field("predecessor snapshot", snapshot["predecessor_snapshot_id"]),
                                _field("causal transition", snapshot["causal_transition_id"]),
                            ),
                        ),
                    )
            summary_by_type = {
                "definition_save": f"Asset-state definition: {operation['definition_name'] or '—'}",
                "cycle_start": f"Start asset-state cycle: {operation['symbol'] or '—'}",
                "transition": f"Manual state transition: {operation['requested_state_key'] or '—'}",
                "cycle_close": f"Close asset-state cycle: {operation['symbol'] or '—'}",
            }
            artifacts.append(
                RunArtifactView(
                    "asset_state_operation",
                    operation["attempt_id"],
                    RunStageName.STATE.value,
                    operation["symbol"],
                    operation["status"],
                    summary_by_type.get(operation["operation_type"], "Asset-state research operation"),
                    _datetime(operation["completed_at_utc"]),
                    (
                        _field("operation id", operation["operation_id"]),
                        _field(
                            "definition id",
                            operation["resolved_definition_id"]
                            or operation["requested_definition_id"],
                        ),
                        _field("cycle id", operation["cycle_id"] or operation["requested_cycle_id"]),
                        _field("predecessor snapshot", operation["predecessor_snapshot_id"]),
                        _field("requested state", operation["requested_state_key"]),
                        _field("note", operation["note"]),
                        _field("result snapshot", operation["result_snapshot_id"]),
                        _field("transition id", operation["transition_id"]),
                        _field("cycle event id", operation["cycle_event_id"]),
                        _field("reason", operation["reason"]),
                        _field("error", operation["error_summary"]),
                    ),
                    state_children,
                )
            )
        target_rows = connection.execute(
            """
            SELECT * FROM target_position_operations
            WHERE run_id = ? ORDER BY requested_at_utc, attempt_id
            """,
            (str(run_id),),
        ).fetchall()
        for operation in target_rows:
            result_children: tuple[RunArtifactView, ...] = ()
            if operation["result_calculation_id"]:
                result = connection.execute(
                    """
                    SELECT * FROM target_position_results WHERE calculation_id = ?
                    """,
                    (operation["result_calculation_id"],),
                ).fetchone()
                if result is not None:
                    result_children = (
                        RunArtifactView(
                            "target_position_result",
                            result["calculation_id"],
                            RunStageName.TARGET_POSITION.value,
                            None,
                            result["adjustment_direction"],
                            (
                                f"Target {result['target_position_value_usd_text']} USD; "
                                f"difference {result['adjustment_value_usd_text']} USD"
                            ),
                            _datetime(result["created_at_utc"]),
                            (
                                _field("definition id", result["definition_id"]),
                                _field("definition version", result["definition_version"]),
                                _field("research state", result["research_state_value_text"]),
                                _field("capital basis USD", result["research_capital_basis_usd_text"]),
                                _field("current position USD", result["current_position_value_usd_text"]),
                                _field("target fraction", result["target_fraction_text"]),
                                _field("evaluation mode", result["evaluation_mode"]),
                                _field("lower knot", result["lower_knot_ordinal"]),
                                _field("upper knot", result["upper_knot_ordinal"]),
                                _field("interpolation weight", result["interpolation_weight_text"]),
                            ),
                        ),
                    )
            summary = (
                f"Target-position definition: {operation['definition_name'] or '—'}"
                if operation["operation_type"] == "definition_save"
                else "Manual target-position research preview"
            )
            artifacts.append(
                RunArtifactView(
                    "target_position_operation",
                    operation["attempt_id"],
                    RunStageName.TARGET_POSITION.value,
                    None,
                    operation["status"],
                    summary,
                    _datetime(operation["completed_at_utc"]),
                    (
                        _field("operation id", operation["operation_id"]),
                        _field(
                            "definition id",
                            operation["resolved_definition_id"]
                            or operation["requested_definition_id"],
                        ),
                        _field("direction", operation["direction"]),
                        _field("minimum fraction", operation["minimum_fraction_text"]),
                        _field("neutral fraction", operation["neutral_fraction_text"]),
                        _field("maximum fraction", operation["maximum_fraction_text"]),
                        _field("research state", operation["research_state_value_text"]),
                        _field("capital basis USD", operation["research_capital_basis_usd_text"]),
                        _field("current position USD", operation["current_position_value_usd_text"]),
                        _field("calculation id", operation["result_calculation_id"]),
                        _field("reason", operation["reason"]),
                        _field("error", operation["error_summary"]),
                    ),
                    result_children,
                )
            )
        standardized_rows = connection.execute(
            """
            SELECT * FROM standardized_state_operations
            WHERE run_id = ? ORDER BY requested_at_utc, attempt_id
            """,
            (str(run_id),),
        ).fetchall()
        for operation in standardized_rows:
            result_children: tuple[RunArtifactView, ...] = ()
            if operation["result_calculation_id"]:
                result = connection.execute(
                    """
                    SELECT * FROM standardized_state_results
                    WHERE calculation_id = ?
                    """,
                    (operation["result_calculation_id"],),
                ).fetchone()
                if result is not None:
                    result_children = (
                        RunArtifactView(
                            "standardized_price_state_result",
                            result["calculation_id"],
                            RunStageName.STANDARDIZED_STATE.value,
                            result["symbol"],
                            "valid",
                            (
                                f"{result['symbol']} standardized state = "
                                f"{result['standardized_state_text']}"
                            ),
                            _datetime(result["created_at_utc"]),
                            (
                                _field("definition id", result["definition_id"]),
                                _field("definition version", result["definition_version"]),
                                _field("as of", result["as_of_utc"]),
                                _field("manual price USD", result["manual_price_usd_text"]),
                                _field(
                                    "manual reference USD",
                                    result["manual_reference_price_usd_text"],
                                ),
                                _field(
                                    "manual risk scale USD",
                                    result["manual_risk_scale_usd_text"],
                                ),
                                _field(
                                    "price deviation USD",
                                    result["price_deviation_usd_text"],
                                ),
                                _field(
                                    "standardized state",
                                    result["standardized_state_text"],
                                ),
                                _field("formula", result["formula_id"]),
                                _field("input source", result["price_source"]),
                            ),
                        ),
                    )
            summary = (
                f"Standardized-state definition: {operation['definition_name'] or '—'}"
                if operation["operation_type"] == "definition_save"
                else f"Manual standardized-state preview: {operation['symbol'] or '—'}"
            )
            artifacts.append(
                RunArtifactView(
                    "standardized_price_state_operation",
                    operation["attempt_id"],
                    RunStageName.STANDARDIZED_STATE.value,
                    operation["symbol"],
                    operation["status"],
                    summary,
                    _datetime(operation["completed_at_utc"]),
                    (
                        _field("operation id", operation["operation_id"]),
                        _field(
                            "definition id",
                            operation["resolved_definition_id"]
                            or operation["requested_definition_id"],
                        ),
                        _field("manual price USD", operation["manual_price_usd_text"]),
                        _field(
                            "manual reference USD",
                            operation["manual_reference_price_usd_text"],
                        ),
                        _field(
                            "manual risk scale USD",
                            operation["manual_risk_scale_usd_text"],
                        ),
                        _field("as of", operation["as_of_utc"]),
                        _field("calculation id", operation["result_calculation_id"]),
                        _field("reason", operation["reason"]),
                        _field("error", operation["error_summary"]),
                    ),
                    result_children,
                )
            )
        linked_rows = connection.execute(
            """
            SELECT * FROM target_position_linked_preview_operations
            WHERE parent_run_id = ? ORDER BY requested_at_utc, attempt_id
            """,
            (str(run_id),),
        ).fetchall()
        for operation in linked_rows:
            link_children: tuple[RunArtifactView, ...] = ()
            link = connection.execute(
                """
                SELECT * FROM target_position_standardized_state_links
                WHERE operation_id = ?
                """,
                (operation["operation_id"],),
            ).fetchone()
            if link is not None:
                link_children = (
                    RunArtifactView(
                        "standardized_state_target_position_link",
                        link["link_id"],
                        RunStageName.TARGET_POSITION.value,
                        link["symbol"],
                        "immutable",
                        (
                            f"{link['symbol']} state {link['standardized_state_text']} "
                            f"→ Target Position calculation {link['target_calculation_id']}"
                        ),
                        _datetime(link["created_at_utc"]),
                        (
                            _field("source calculation", link["source_calculation_id"]),
                            _field("source Run", link["source_run_id"]),
                            _field("source definition", link["source_definition_id"]),
                            _field("source definition version", link["source_definition_version"]),
                            _field("source as of", link["source_as_of_utc"]),
                            _field("target calculation", link["target_calculation_id"]),
                            _field("target definition", link["target_definition_id"]),
                            _field("target definition version", link["target_definition_version"]),
                            _field("child Run", link["child_run_id"]),
                        ),
                    ),
                )
            artifacts.append(
                RunArtifactView(
                    "linked_target_position_operation",
                    operation["attempt_id"],
                    (
                        RunStageName.TARGET_POSITION.value
                        if operation["target_stage_id"]
                        else RunStageName.STANDARDIZED_STATE.value
                    ),
                    operation["resolved_symbol"],
                    operation["status"],
                    "Exact persisted Standardized State → Target Position preview",
                    _datetime(operation["completed_at_utc"]),
                    (
                        _field("operation id", operation["operation_id"]),
                        _field("source calculation", operation["requested_source_calculation_id"]),
                        _field("source Run", operation["resolved_source_run_id"]),
                        _field("source state", operation["resolved_standardized_state_text"]),
                        _field("target definition", operation["requested_target_definition_id"]),
                        _field("capital basis USD", operation["research_capital_basis_usd_text"]),
                        _field("current position USD", operation["current_position_value_usd_text"]),
                        _field("child Run", operation["child_run_id"]),
                        _field("target calculation", operation["target_result_calculation_id"]),
                        _field("reason", operation["reason"]),
                        _field("error", operation["error_summary"]),
                    ),
                    link_children,
                )
            )
        target_adjustment_rows = connection.execute(
            """
            SELECT * FROM target_adjustment_decision_operations
            WHERE run_id = ? ORDER BY requested_at_utc, attempt_id
            """,
            (str(run_id),),
        ).fetchall()
        for operation in target_adjustment_rows:
            result_children: tuple[RunArtifactView, ...] = ()
            if operation["decision_result_id"]:
                result = connection.execute(
                    """
                    SELECT * FROM target_adjustment_decision_results
                    WHERE decision_result_id = ?
                    """,
                    (operation["decision_result_id"],),
                ).fetchone()
                if result is not None:
                    intent = connection.execute(
                        """
                        SELECT * FROM target_adjustment_trade_intents
                        WHERE decision_result_id = ?
                        """,
                        (result["decision_result_id"],),
                    ).fetchone()
                    intent_children: tuple[RunArtifactView, ...] = ()
                    if intent is not None:
                        intent_children = (
                            RunArtifactView(
                                "target_adjustment_trade_intent",
                                intent["intent_id"],
                                RunStageName.DECISION.value,
                                intent["symbol"],
                                "research_only",
                                (
                                    f"{intent['action']} {intent['requested_notional_usd_text']} "
                                    "USD requested; not Risk-approved"
                                ),
                                _datetime(intent["created_at_utc"]),
                                (
                                    _field("current exposure USD", intent["current_exposure_usd_text"]),
                                    _field("target exposure USD", intent["target_exposure_usd_text"]),
                                    _field("signed desired change USD", intent["desired_change_usd_text"]),
                                    _field("requested notional USD", intent["requested_notional_usd_text"]),
                                    _field("policy", intent["policy_id"]),
                                    _field("policy version", intent["policy_version"]),
                                    _field("Risk admission", "not admitted"),
                                ),
                            ),
                        )
                    result_children = (
                        RunArtifactView(
                            "target_adjustment_decision_result",
                            result["decision_result_id"],
                            RunStageName.DECISION.value,
                            result["symbol"],
                            result["status"],
                            (
                                f"Target adjustment: {result['action']}; "
                                f"difference {result['adjustment_value_usd_text']} USD"
                            ),
                            _datetime(result["created_at_utc"]),
                            (
                                _field("source link", result["target_position_link_id"]),
                                _field("source standardized-state Run", result["standardized_state_run_id"]),
                                _field("Phase 5C parent Run", result["linked_parent_run_id"]),
                                _field("Target Position child Run", result["target_child_run_id"]),
                                _field("target calculation", result["target_calculation_id"]),
                                _field("target definition", result["target_definition_id"]),
                                _field("target definition version", result["target_definition_version"]),
                                _field("as of", result["as_of_utc"]),
                                _field("capital basis USD", result["research_capital_basis_usd_text"]),
                                _field("current position USD", result["current_position_value_usd_text"]),
                                _field("target fraction", result["target_fraction_text"]),
                                _field("target position USD", result["target_position_value_usd_text"]),
                                _field("signed adjustment USD", result["adjustment_value_usd_text"]),
                                _field("reason codes", result["reason_codes_json"]),
                            ),
                            intent_children,
                        ),
                    )
            artifacts.append(
                RunArtifactView(
                    "target_adjustment_decision_operation",
                    operation["attempt_id"],
                    (
                        RunStageName.DECISION.value
                        if operation["decision_stage_id"]
                        else RunStageName.TARGET_POSITION.value
                    ),
                    operation["resolved_symbol"],
                    operation["status"],
                    "Exact linked Target Position → Decision research preview",
                    _datetime(operation["completed_at_utc"]),
                    (
                        _field("operation id", operation["operation_id"]),
                        _field("requested source link", operation["requested_target_position_link_id"]),
                        _field("target calculation", operation["resolved_target_calculation_id"]),
                        _field("current position USD", operation["resolved_current_position_value_usd_text"]),
                        _field("target position USD", operation["resolved_target_position_value_usd_text"]),
                        _field("signed adjustment USD", operation["resolved_adjustment_value_usd_text"]),
                        _field("decision result", operation["decision_result_id"]),
                        _field("reason", operation["reason"]),
                        _field("error", operation["error_summary"]),
                    ),
                    result_children,
                )
            )
        risk_rows = connection.execute(
            "SELECT * FROM target_adjustment_risk_operations WHERE run_id = ? ORDER BY requested_at_utc, attempt_id",
            (str(run_id),),
        ).fetchall()
        for operation in risk_rows:
            result_children: tuple[RunArtifactView, ...] = ()
            if operation["review_result_id"]:
                result = connection.execute(
                    "SELECT * FROM target_adjustment_risk_review_results WHERE review_result_id = ?",
                    (operation["review_result_id"],),
                ).fetchone()
                if result is not None:
                    rule_rows = connection.execute(
                        "SELECT * FROM target_adjustment_risk_rule_results WHERE review_result_id = ? ORDER BY evaluation_order",
                        (result["review_result_id"],),
                    ).fetchall()
                    rule_children = tuple(
                        RunArtifactView(
                            "target_adjustment_risk_rule_result",
                            row["rule_result_id"],
                            RunStageName.RISK.value,
                            result["symbol"],
                            row["status"],
                            f"{row['evaluation_order']}. {row['rule_name']}",
                            _datetime(row["evaluated_at_utc"]),
                            (
                                _field("rule", row["rule_id"]),
                                _field("version", row["rule_version"]),
                                _field("input", row["input_summary"]),
                                _field("expected", row["expected_condition"]),
                                _field("reason codes", row["reason_codes_json"]),
                                _field("stop processing", row["stop_processing"]),
                            ),
                        )
                        for row in rule_rows
                    )
                    result_children = (
                        RunArtifactView(
                            "target_adjustment_risk_review_result",
                            result["review_result_id"],
                            RunStageName.RISK.value,
                            result["symbol"],
                            result["status"],
                            f"{result['action']} {result['requested_notional_usd_text']} USD remains unapproved",
                            _datetime(result["created_at_utc"]),
                            (
                                _field("Decision result", result["decision_result_id"]),
                                _field("source intent", result["intent_id"]),
                                _field("current exposure USD", result["current_exposure_usd_text"]),
                                _field("target exposure USD", result["target_exposure_usd_text"]),
                                _field("signed change USD", result["desired_change_usd_text"]),
                                _field("requested notional USD", result["requested_notional_usd_text"]),
                                _field("approved notional USD", result["approved_notional_usd_text"]),
                                _field("Risk-approved intent", result["risk_approved_intent_id"]),
                                _field("gate", result["gate_id"]),
                                _field("gate version", result["gate_version"]),
                            ),
                            rule_children,
                        ),
                    )
            artifacts.append(
                RunArtifactView(
                    "target_adjustment_risk_operation",
                    operation["attempt_id"],
                    RunStageName.RISK.value if operation["risk_stage_id"] else RunStageName.DECISION.value,
                    operation["resolved_symbol"],
                    operation["status"],
                    "Target adjustment structural Risk review; NO EXECUTION / NO RISK APPROVAL",
                    _datetime(operation["completed_at_utc"]),
                    (
                        _field("operation id", operation["operation_id"]),
                        _field("requested intent", operation["requested_intent_id"]),
                        _field("action", operation["resolved_action"]),
                        _field("review result", operation["review_result_id"]),
                        _field("reason", operation["reason"]),
                        _field("error", operation["error_summary"]),
                    ),
                    result_children,
                )
            )
        exposure_rows = connection.execute(
            """SELECT * FROM target_adjustment_exposure_cap_operations
               WHERE run_id=? ORDER BY requested_at_utc,attempt_id""",
            (str(run_id),),
        ).fetchall()
        for operation in exposure_rows:
            children: tuple[RunArtifactView, ...] = ()
            if operation["preview_result_id"]:
                result = connection.execute(
                    """SELECT * FROM target_adjustment_exposure_cap_results
                       WHERE preview_result_id=?""",
                    (operation["preview_result_id"],),
                ).fetchone()
                rule = connection.execute(
                    """SELECT * FROM target_adjustment_exposure_cap_rule_results
                       WHERE preview_result_id=?""",
                    (operation["preview_result_id"],),
                ).fetchone()
                if result is not None and rule is not None:
                    rule_artifact = RunArtifactView(
                        "target_adjustment_exposure_cap_rule_result",
                        rule["rule_result_id"], RunStageName.RISK.value,
                        result["symbol"], rule["outcome"],
                        "1. MAX_TARGET_EXPOSURE_USD@1",
                        _datetime(rule["evaluated_at_utc"]),
                        (
                            _field("action", rule["action"]),
                            _field("current exposure USD", rule["current_exposure_usd_text"]),
                            _field("target exposure USD", rule["target_exposure_usd_text"]),
                            _field("original requested USD", rule["original_requested_notional_usd_text"]),
                            _field("maximum target exposure USD", rule["max_target_exposure_usd_text"]),
                            _field("cap-constrained candidate USD", rule["cap_constrained_candidate_notional_usd_text"]),
                            _field("reduction USD", rule["reduction_usd_text"]),
                            _field("reason codes", rule["reason_codes_json"]),
                        ),
                    )
                    children = (
                        RunArtifactView(
                            "target_adjustment_exposure_cap_preview_result",
                            result["preview_result_id"], RunStageName.RISK.value,
                            result["symbol"], result["disposition"],
                            f"{result['action']} candidate {result['cap_constrained_candidate_notional_usd_text']} USD; not Risk approval",
                            _datetime(result["created_at_utc"]),
                            (
                                _field("Phase 6A review", result["phase6a_review_result_id"]),
                                _field("definition", result["definition_id"]),
                                _field("definition version", result["definition_version"]),
                                _field("original requested USD", result["original_requested_notional_usd_text"]),
                                _field("maximum target exposure USD", result["max_target_exposure_usd_text"]),
                                _field("candidate USD", result["cap_constrained_candidate_notional_usd_text"]),
                                _field("reduction USD", result["reduction_usd_text"]),
                                _field("component", result["component_id"]),
                                _field("component version", result["component_version"]),
                            ),
                            (rule_artifact,),
                        ),
                    )
            elif operation["resolved_definition_id"]:
                definition = connection.execute(
                    """SELECT * FROM single_asset_exposure_cap_definitions
                       WHERE definition_id=? AND definition_version=?""",
                    (operation["resolved_definition_id"], operation["resolved_definition_version"]),
                ).fetchone()
                if definition is not None:
                    children = (
                        RunArtifactView(
                            "single_asset_exposure_cap_definition",
                            f"{definition['definition_id']}:{definition['definition_version']}",
                            RunStageName.RISK.value, definition["symbol"], definition["status"],
                            f"Maximum target exposure {definition['max_target_exposure_usd_text']} USD",
                            _datetime(definition["created_at_utc"]),
                            (
                                _field("definition", definition["definition_id"]),
                                _field("version", definition["definition_version"]),
                                _field("predecessor version", definition["predecessor_version"]),
                                _field("currency", definition["currency"]),
                                _field("reason", definition["reason"]),
                            ),
                        ),
                    )
            artifacts.append(
                RunArtifactView(
                    "target_adjustment_exposure_cap_operation",
                    operation["attempt_id"], RunStageName.RISK.value,
                    operation["resolved_symbol"] or operation["requested_symbol"],
                    operation["status"],
                    "Single-asset exposure-cap research operation; candidate is not Risk approval; NO EXECUTION",
                    _datetime(operation["completed_at_utc"]),
                    (
                        _field("operation id", operation["operation_id"]),
                        _field("operation type", operation["operation_type"]),
                        _field("requested Phase 6A review", operation["requested_review_result_id"]),
                        _field("requested definition", operation["requested_definition_id"]),
                        _field("requested definition version", operation["requested_definition_version"]),
                        _field("preview result", operation["preview_result_id"]),
                        _field("disposition", operation["disposition"]),
                        _field("reason", operation["reason"]),
                        _field("error", operation["error_summary"]),
                    ),
                    children,
                )
            )
        cash_floor_rows = connection.execute(
            """SELECT * FROM target_adjustment_cash_floor_operations
               WHERE run_id=? ORDER BY requested_at_utc,attempt_id""",
            (str(run_id),),
        ).fetchall()
        for operation in cash_floor_rows:
            children: tuple[RunArtifactView, ...] = ()
            if operation["preview_result_id"]:
                result = connection.execute(
                    """SELECT * FROM target_adjustment_cash_floor_results
                       WHERE preview_result_id=?""",
                    (operation["preview_result_id"],),
                ).fetchone()
                rule = connection.execute(
                    """SELECT * FROM target_adjustment_cash_floor_rule_results
                       WHERE preview_result_id=?""",
                    (operation["preview_result_id"],),
                ).fetchone()
                if result is not None and rule is not None:
                    inherited_rule = RunArtifactView(
                        "target_adjustment_exposure_cap_rule_reference",
                        result["phase6b_preview_result_id"],
                        RunStageName.RISK.value,
                        result["symbol"],
                        "persisted_source",
                        "1. MAX_TARGET_EXPOSURE_USD@1 (inherited Phase 6B evidence)",
                        _datetime(result["created_at_utc"]),
                        (
                            _field("Phase 6B result", result["phase6b_preview_result_id"]),
                            _field("Phase 6B candidate USD", result["phase6b_candidate_notional_usd_text"]),
                        ),
                    )
                    cash_rule = RunArtifactView(
                        "target_adjustment_research_cash_floor_rule_result",
                        rule["rule_result_id"], RunStageName.RISK.value,
                        result["symbol"], rule["outcome"],
                        "2. MIN_RESEARCH_ASSET_CASH_USD@1",
                        _datetime(rule["evaluated_at_utc"]),
                        (
                            _field("action", rule["action"]),
                            _field("research capital basis USD", rule["research_capital_basis_usd_text"]),
                            _field("current exposure USD", rule["current_exposure_usd_text"]),
                            _field("minimum research asset cash USD", rule["minimum_research_asset_cash_usd_text"]),
                            _field("pre-action research cash USD", rule["pre_action_research_cash_usd_text"]),
                            _field("cash capacity USD", rule["cash_capacity_usd_text"]),
                            _field("candidate after rule USD", rule["cash_floor_constrained_candidate_notional_usd_text"]),
                            _field("post-action research cash USD", rule["post_action_research_cash_usd_text"]),
                            _field("remaining shortfall USD", rule["remaining_shortfall_usd_text"]),
                            _field("reduction USD", rule["reduction_usd_text"]),
                            _field("reason codes", rule["reason_codes_json"]),
                        ),
                    )
                    children = (
                        RunArtifactView(
                            "target_adjustment_research_cash_floor_preview_result",
                            result["preview_result_id"], RunStageName.RISK.value,
                            result["symbol"], result["disposition"],
                            f"{result['action']} candidate {result['cash_floor_constrained_candidate_notional_usd_text']} USD; not Risk approval",
                            _datetime(result["created_at_utc"]),
                            (
                                _field("Phase 6B result", result["phase6b_preview_result_id"]),
                                _field("definition", result["definition_id"]),
                                _field("definition version", result["definition_version"]),
                                _field("research capital basis USD", result["research_capital_basis_usd_text"]),
                                _field("minimum research asset cash USD", result["minimum_research_asset_cash_usd_text"]),
                                _field("candidate USD", result["cash_floor_constrained_candidate_notional_usd_text"]),
                                _field("component", result["component_id"]),
                                _field("component version", result["component_version"]),
                            ),
                            (inherited_rule, cash_rule),
                        ),
                    )
            elif operation["resolved_definition_id"]:
                definition = connection.execute(
                    """SELECT * FROM research_asset_cash_floor_definitions
                       WHERE definition_id=? AND definition_version=?""",
                    (
                        operation["resolved_definition_id"],
                        operation["resolved_definition_version"],
                    ),
                ).fetchone()
                if definition is not None:
                    children = (
                        RunArtifactView(
                            "research_asset_cash_floor_definition",
                            f"{definition['definition_id']}:{definition['definition_version']}",
                            RunStageName.RISK.value, definition["symbol"],
                            definition["status"],
                            f"Minimum hypothetical research asset cash {definition['minimum_research_asset_cash_usd_text']} USD",
                            _datetime(definition["created_at_utc"]),
                            (
                                _field("definition", definition["definition_id"]),
                                _field("version", definition["definition_version"]),
                                _field("predecessor version", definition["predecessor_version"]),
                                _field("currency", definition["currency"]),
                                _field("reason", definition["reason"]),
                            ),
                        ),
                    )
            artifacts.append(
                RunArtifactView(
                    "target_adjustment_research_cash_floor_operation",
                    operation["attempt_id"], RunStageName.RISK.value,
                    operation["resolved_symbol"] or operation["requested_symbol"],
                    operation["status"],
                    "Research asset cash-floor operation; candidate is not Risk approval; NO EXECUTION",
                    _datetime(operation["completed_at_utc"]),
                    (
                        _field("operation id", operation["operation_id"]),
                        _field("operation type", operation["operation_type"]),
                        _field("requested Phase 6B result", operation["requested_phase6b_result_id"]),
                        _field("requested definition", operation["requested_definition_id"]),
                        _field("requested definition version", operation["requested_definition_version"]),
                        _field("preview result", operation["preview_result_id"]),
                        _field("disposition", operation["disposition"]),
                        _field("reason", operation["reason"]),
                        _field("error", operation["error_summary"]),
                    ),
                    children,
                )
            )
        asset_cash_rows = connection.execute(
            """SELECT * FROM target_adjustment_research_asset_cash_operations
               WHERE run_id=? ORDER BY requested_at_utc,attempt_id""",
            (str(run_id),),
        ).fetchall()
        for operation in asset_cash_rows:
            children: tuple[RunArtifactView, ...] = ()
            if operation["preview_result_id"]:
                result = connection.execute(
                    """SELECT * FROM target_adjustment_research_asset_cash_results
                       WHERE preview_result_id=?""",
                    (operation["preview_result_id"],),
                ).fetchone()
                rule = connection.execute(
                    """SELECT * FROM target_adjustment_research_asset_cash_rule_results
                       WHERE preview_result_id=?""",
                    (operation["preview_result_id"],),
                ).fetchone()
                phase6c = None
                if result is not None:
                    phase6c = connection.execute(
                        """SELECT * FROM target_adjustment_cash_floor_results
                           WHERE preview_result_id=?""",
                        (result["phase6c_preview_result_id"],),
                    ).fetchone()
                if result is not None and rule is not None and phase6c is not None:
                    inherited_exposure_rule = RunArtifactView(
                        "target_adjustment_exposure_cap_rule_reference",
                        phase6c["phase6b_preview_result_id"],
                        RunStageName.RISK.value, result["symbol"],
                        "persisted_source",
                        "1. MAX_TARGET_EXPOSURE_USD@1 (inherited Phase 6B evidence)",
                        _datetime(result["created_at_utc"]),
                        (
                            _field("Phase 6B result", phase6c["phase6b_preview_result_id"]),
                            _field("Phase 6B candidate USD", phase6c["phase6b_candidate_notional_usd_text"]),
                        ),
                    )
                    inherited_cash_floor_rule = RunArtifactView(
                        "target_adjustment_research_cash_floor_rule_reference",
                        result["phase6c_preview_result_id"],
                        RunStageName.RISK.value, result["symbol"],
                        "persisted_source",
                        "2. MIN_RESEARCH_ASSET_CASH_USD@1 (inherited Phase 6C evidence)",
                        _datetime(result["created_at_utc"]),
                        (
                            _field("Phase 6C result", result["phase6c_preview_result_id"]),
                            _field("Phase 6C candidate USD", result["phase6c_candidate_notional_usd_text"]),
                        ),
                    )
                    asset_cash_rule = RunArtifactView(
                        "target_adjustment_research_asset_cash_rule_result",
                        rule["rule_result_id"], RunStageName.RISK.value,
                        result["symbol"], rule["outcome"],
                        "3. MAX_RESEARCH_ASSET_CASH_DEPLOYMENT_USD@1",
                        _datetime(rule["evaluated_at_utc"]),
                        (
                            _field("action", rule["action"]),
                            _field("Phase 6C candidate USD", rule["phase6c_candidate_notional_usd_text"]),
                            _field("selected asset cash USD", rule["selected_asset_cash_balance_usd_text"]),
                            _field("pre-candidate asset cash USD", rule["pre_candidate_asset_cash_usd_text"]),
                            _field("candidate after rule USD", rule["asset_cash_constrained_candidate_notional_usd_text"]),
                            _field("hypothetical post-candidate asset cash USD", rule["hypothetical_post_candidate_asset_cash_usd_text"]),
                            _field("reduction USD", rule["reduction_usd_text"]),
                            _field("research cash reserved", bool(rule["research_cash_reserved"])),
                            _field("reason codes", rule["reason_codes_json"]),
                        ),
                    )
                    children = (
                        RunArtifactView(
                            "target_adjustment_research_asset_cash_preview_result",
                            result["preview_result_id"], RunStageName.RISK.value,
                            result["symbol"], result["disposition"],
                            f"{result['action']} candidate {result['asset_cash_constrained_candidate_notional_usd_text']} USD; no cash reserved; not Risk approval",
                            _datetime(result["created_at_utc"]),
                            (
                                _field("Phase 6C result", result["phase6c_preview_result_id"]),
                                _field("capital plan", result["capital_plan_id"]),
                                _field("capital plan version", result["capital_plan_version"]),
                                _field("capital snapshot", result["capital_snapshot_id"]),
                                _field("capital snapshot run", result["capital_snapshot_run_id"]),
                                _field("asset cash bucket", result["asset_cash_bucket_id"]),
                                _field("selected asset cash USD", result["selected_asset_cash_balance_usd_text"]),
                                _field("candidate USD", result["asset_cash_constrained_candidate_notional_usd_text"]),
                                _field("research cash reserved", bool(result["research_cash_reserved"])),
                                _field("warnings", result["warnings_json"]),
                                _field("component", result["component_id"]),
                                _field("component version", result["component_version"]),
                            ),
                            (
                                inherited_exposure_rule,
                                inherited_cash_floor_rule,
                                asset_cash_rule,
                            ),
                        ),
                    )
            artifacts.append(
                RunArtifactView(
                    "target_adjustment_research_asset_cash_operation",
                    operation["attempt_id"], RunStageName.RISK.value,
                    operation["resolved_symbol"], operation["status"],
                    "Research capital-plan asset-cash operation; no cash is reserved; candidate is not Risk approval; NO EXECUTION",
                    _datetime(operation["completed_at_utc"]),
                    (
                        _field("operation id", operation["operation_id"]),
                        _field("operation type", "preview"),
                        _field("requested Phase 6C result", operation["requested_phase6c_result_id"]),
                        _field("requested capital plan", operation["requested_capital_plan_id"]),
                        _field("requested capital snapshot", operation["requested_capital_snapshot_id"]),
                        _field("preview result", operation["preview_result_id"]),
                        _field("disposition", operation["disposition"]),
                        _field("reason", operation["reason"]),
                        _field("error", operation["error_summary"]),
                    ),
                    children,
                )
            )
        return tuple(artifacts)


__all__ = ["SQLiteRunHistoryRepository"]
