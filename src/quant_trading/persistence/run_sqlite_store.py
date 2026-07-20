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
        return RunDetailView(summary, stages, bindings, messages, artifacts)

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
        return tuple(artifacts)


__all__ = ["SQLiteRunHistoryRepository"]
