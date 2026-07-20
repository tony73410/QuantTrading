"""SQLite adapter for immutable manual asset-state research evidence."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from quant_trading.asset_state import (
    AllowedAssetStateTransition,
    AssetStateConcurrencyError,
    AssetStateCycleDetail,
    AssetStateCycleEvent,
    AssetStateCycleEventType,
    AssetStateDeclaration,
    AssetStateDefinitionQuery,
    AssetStateDefinitionStatus,
    AssetStateDefinitionSummary,
    AssetStateEvidenceBinding,
    AssetStateEvidenceKind,
    AssetStateMachineDefinition,
    AssetStateOperationAttempt,
    AssetStateOperationQuery,
    AssetStateOperationStatus,
    AssetStateOperationType,
    AssetStateSnapshot,
    AssetStateStorageError,
    AssetStateTransitionEvent,
    AssetStateTriggerType,
    StateDefinitionInput,
    StateTransitionInput,
    TradingCycle,
    TradingCycleQuery,
    TradingCycleStatus,
    TradingCycleSummary,
    replay_asset_state,
)

from .sqlite_database import CentralSQLiteDatabase


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="microseconds")


def _datetime(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value).astimezone(UTC) if value else None


class SQLiteAssetStateStore:
    """Implement state Store/query ports while keeping state meaning in its owner."""

    def __init__(self, database_path: Path | str) -> None:
        self._database = CentralSQLiteDatabase(database_path)

    def initialize(self) -> None:
        self._database.initialize()

    def get_definition(self, definition_id: UUID) -> AssetStateMachineDefinition | None:
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                "SELECT * FROM asset_state_definitions WHERE definition_id = ?",
                (str(definition_id),),
            ).fetchone()
            return self._definition_from_row(connection, row) if row else None

    def get_cycle(self, cycle_id: UUID) -> TradingCycle | None:
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                "SELECT * FROM asset_state_cycles WHERE cycle_id = ?", (str(cycle_id),)
            ).fetchone()
        return self._cycle_from_row(row) if row else None

    def get_open_cycle(self, symbol: str) -> TradingCycle | None:
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                "SELECT * FROM asset_state_cycles WHERE symbol = ? AND status = 'open'",
                (symbol.strip().upper(),),
            ).fetchone()
        return self._cycle_from_row(row) if row else None

    def get_latest_snapshot(self, cycle_id: UUID) -> AssetStateSnapshot | None:
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                """
                SELECT * FROM asset_state_snapshots
                WHERE cycle_id = ? ORDER BY sequence DESC LIMIT 1
                """,
                (str(cycle_id),),
            ).fetchone()
        return self._snapshot_from_row(row) if row else None

    def get_first_operation(self, operation_id: UUID) -> AssetStateOperationAttempt | None:
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                """
                SELECT * FROM asset_state_operations WHERE operation_id = ?
                ORDER BY CASE status WHEN 'completed' THEN 0 ELSE 1 END, rowid LIMIT 1
                """,
                (str(operation_id),),
            ).fetchone()
            return self._operation_from_row(connection, row) if row else None

    def save_operation(self, operation: AssetStateOperationAttempt) -> None:
        with closing(self._database.connect()) as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                self._insert_operation(connection, operation)
                connection.commit()
            except Exception as exc:
                connection.rollback()
                self._raise_storage("could not save asset-state operation", exc)

    def create_definition(
        self,
        definition: AssetStateMachineDefinition,
        operation: AssetStateOperationAttempt,
    ) -> None:
        if (
            operation.operation_type is not AssetStateOperationType.DEFINITION_SAVE
            or operation.status is not AssetStateOperationStatus.COMPLETED
            or operation.resolved_definition_id != definition.definition_id
            or operation.run_id is None
        ):
            raise AssetStateStorageError("definition and operation identity is inconsistent")
        self._validate_definition_operation(definition, operation)
        with closing(self._database.connect()) as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                if definition.predecessor_definition_id is None:
                    if definition.definition_version != 1:
                        raise AssetStateStorageError("a root definition must be version 1")
                else:
                    predecessor = connection.execute(
                        "SELECT definition_version FROM asset_state_definitions WHERE definition_id = ?",
                        (str(definition.predecessor_definition_id),),
                    ).fetchone()
                    if predecessor is None or definition.definition_version != int(predecessor["definition_version"]) + 1:
                        raise AssetStateStorageError("definition version does not follow its predecessor")
                connection.execute(
                    """
                    INSERT INTO asset_state_definitions (
                        definition_id, definition_version, predecessor_definition_id,
                        name, reason, initial_state_key, status, created_at_utc,
                        created_by, schema_version
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(definition.definition_id), definition.definition_version,
                        str(definition.predecessor_definition_id) if definition.predecessor_definition_id else None,
                        definition.name, definition.reason, definition.initial_state_key,
                        definition.status.value, _iso(definition.created_at_utc),
                        definition.created_by, definition.schema_version,
                    ),
                )
                connection.executemany(
                    """
                    INSERT INTO asset_state_definition_states (
                        definition_id, ordinal, state_key, display_label, description
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        (str(definition.definition_id), index, item.state_key, item.display_label, item.description)
                        for index, item in enumerate(definition.states)
                    ),
                )
                connection.executemany(
                    """
                    INSERT INTO asset_state_definition_edges (
                        definition_id, ordinal, source_state_key, destination_state_key
                    ) VALUES (?, ?, ?, ?)
                    """,
                    (
                        (str(definition.definition_id), index, item.source_state_key, item.destination_state_key)
                        for index, item in enumerate(definition.allowed_transitions)
                    ),
                )
                self._validate_definition_rows(connection, definition)
                self._insert_operation(connection, operation)
                connection.commit()
            except Exception as exc:
                connection.rollback()
                self._raise_storage("could not create asset-state definition", exc)

    def start_cycle(
        self,
        cycle: TradingCycle,
        start_event: AssetStateCycleEvent,
        snapshot: AssetStateSnapshot,
        operation: AssetStateOperationAttempt,
    ) -> None:
        if (
            cycle.status is not TradingCycleStatus.OPEN
            or start_event.event_type is not AssetStateCycleEventType.STARTED
            or start_event.operation_id != operation.operation_id
            or start_event.run_id != cycle.opened_run_id
            or start_event.cycle_id != cycle.cycle_id
            or snapshot.run_id != cycle.opened_run_id
            or snapshot.cycle_id != cycle.cycle_id
            or snapshot.sequence != 0
            or operation.operation_type is not AssetStateOperationType.CYCLE_START
            or operation.status is not AssetStateOperationStatus.COMPLETED
            or operation.run_id != cycle.opened_run_id
            or operation.cycle_id != cycle.cycle_id
            or operation.symbol != cycle.symbol
            or operation.requested_definition_id != cycle.definition_id
            or operation.resolved_definition_id != cycle.definition_id
            or operation.reason.strip() != cycle.opening_reason
            or operation.result_snapshot_id != snapshot.snapshot_id
            or operation.cycle_event_id != start_event.event_id
        ):
            raise AssetStateStorageError("cycle start evidence identity is inconsistent")
        with closing(self._database.connect()) as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                definition = self._load_definition(connection, cycle.definition_id)
                if (
                    definition.status is not AssetStateDefinitionStatus.AVAILABLE
                    or definition.definition_version != cycle.definition_version
                    or start_event.symbol != cycle.symbol
                    or start_event.state_key != definition.initial_state_key
                    or snapshot.symbol != cycle.symbol
                    or snapshot.definition_id != definition.definition_id
                    or snapshot.definition_version != definition.definition_version
                    or snapshot.current_state_key != definition.initial_state_key
                ):
                    raise AssetStateStorageError("cycle start does not match the exact available definition")
                if connection.execute(
                    "SELECT 1 FROM asset_state_cycles WHERE symbol = ? AND status = 'open'",
                    (cycle.symbol,),
                ).fetchone():
                    raise AssetStateStorageError("symbol already has an open trading cycle")
                self._insert_cycle(connection, cycle)
                self._insert_cycle_event(connection, start_event)
                self._insert_snapshot(connection, snapshot)
                self._insert_operation(connection, operation)
                connection.commit()
            except Exception as exc:
                connection.rollback()
                self._raise_storage("could not start asset-state cycle", exc)

    def append_transition(
        self,
        transition: AssetStateTransitionEvent,
        snapshot: AssetStateSnapshot,
        operation: AssetStateOperationAttempt,
        *,
        expected_predecessor_snapshot_id: UUID,
    ) -> None:
        if (
            transition.operation_id != operation.operation_id
            or transition.run_id != operation.run_id
            or transition.cycle_id != operation.cycle_id
            or transition.predecessor_snapshot_id != expected_predecessor_snapshot_id
            or snapshot.predecessor_snapshot_id != expected_predecessor_snapshot_id
            or snapshot.causal_transition_id != transition.transition_id
            or snapshot.run_id != transition.run_id
            or snapshot.cycle_id != transition.cycle_id
            or operation.operation_type is not AssetStateOperationType.TRANSITION
            or operation.status is not AssetStateOperationStatus.COMPLETED
            or operation.run_id != transition.run_id
            or operation.symbol != transition.symbol
            or operation.requested_definition_id != transition.definition_id
            or operation.resolved_definition_id != transition.definition_id
            or operation.predecessor_snapshot_id != transition.predecessor_snapshot_id
            or (operation.requested_state_key or "").strip().upper() != transition.new_state_key
            or operation.reason.strip() != transition.reason
            or operation.evidence_bindings != transition.evidence_bindings
            or operation.note != transition.note
            or operation.result_snapshot_id != snapshot.snapshot_id
            or operation.transition_id != transition.transition_id
        ):
            raise AssetStateStorageError("transition evidence identity is inconsistent")
        with closing(self._database.connect()) as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                cycle_row = connection.execute(
                    "SELECT * FROM asset_state_cycles WHERE cycle_id = ?",
                    (str(transition.cycle_id),),
                ).fetchone()
                if cycle_row is None or cycle_row["status"] != TradingCycleStatus.OPEN.value:
                    raise AssetStateStorageError("only an open cycle can accept a transition")
                latest = connection.execute(
                    """
                    SELECT * FROM asset_state_snapshots
                    WHERE cycle_id = ? ORDER BY sequence DESC LIMIT 1
                    """,
                    (str(transition.cycle_id),),
                ).fetchone()
                if latest is None or latest["snapshot_id"] != str(expected_predecessor_snapshot_id):
                    raise AssetStateConcurrencyError("state snapshot changed before transition append")
                definition = self._load_definition(connection, UUID(cycle_row["definition_id"]))
                if (
                    transition.symbol != cycle_row["symbol"]
                    or transition.definition_id != definition.definition_id
                    or transition.definition_version != definition.definition_version
                    or transition.predecessor_sequence != int(latest["sequence"])
                    or transition.previous_state_key != latest["current_state_key"]
                    or not definition.permits(transition.previous_state_key, transition.new_state_key)
                    or snapshot.sequence != int(latest["sequence"]) + 1
                    or snapshot.symbol != transition.symbol
                    or snapshot.definition_id != definition.definition_id
                    or snapshot.definition_version != definition.definition_version
                    or snapshot.current_state_key != transition.new_state_key
                ):
                    raise AssetStateStorageError("transition does not follow the current exact definition state")
                self._validate_evidence(connection, transition.evidence_bindings)
                self._insert_transition(connection, transition)
                self._insert_snapshot(connection, snapshot)
                self._insert_operation(connection, operation)
                connection.commit()
            except Exception as exc:
                connection.rollback()
                self._raise_storage("could not append asset-state transition", exc)

    def close_cycle(
        self,
        cycle: TradingCycle,
        close_event: AssetStateCycleEvent,
        operation: AssetStateOperationAttempt,
        *,
        expected_predecessor_snapshot_id: UUID,
    ) -> None:
        if (
            cycle.status is not TradingCycleStatus.CLOSED
            or close_event.event_type is not AssetStateCycleEventType.CLOSED
            or close_event.operation_id != operation.operation_id
            or close_event.run_id != cycle.closed_run_id
            or close_event.cycle_id != cycle.cycle_id
            or operation.operation_type is not AssetStateOperationType.CYCLE_CLOSE
            or operation.status is not AssetStateOperationStatus.COMPLETED
            or operation.run_id != cycle.closed_run_id
            or operation.symbol != cycle.symbol
            or operation.requested_definition_id != cycle.definition_id
            or operation.resolved_definition_id != cycle.definition_id
            or operation.cycle_id != cycle.cycle_id
            or operation.cycle_event_id != close_event.event_id
            or operation.predecessor_snapshot_id != expected_predecessor_snapshot_id
            or operation.reason.strip() != cycle.closing_reason
        ):
            raise AssetStateStorageError("cycle close evidence identity is inconsistent")
        with closing(self._database.connect()) as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                stored = connection.execute(
                    "SELECT * FROM asset_state_cycles WHERE cycle_id = ?",
                    (str(cycle.cycle_id),),
                ).fetchone()
                latest = connection.execute(
                    """
                    SELECT * FROM asset_state_snapshots
                    WHERE cycle_id = ? ORDER BY sequence DESC LIMIT 1
                    """,
                    (str(cycle.cycle_id),),
                ).fetchone()
                if stored is None or stored["status"] != TradingCycleStatus.OPEN.value:
                    raise AssetStateStorageError("only an open cycle can be closed")
                if latest is None or latest["snapshot_id"] != str(expected_predecessor_snapshot_id):
                    raise AssetStateConcurrencyError("state snapshot changed before cycle close")
                if (
                    cycle.symbol != stored["symbol"]
                    or cycle.definition_id != UUID(stored["definition_id"])
                    or cycle.definition_version != int(stored["definition_version"])
                    or close_event.symbol != cycle.symbol
                    or close_event.state_key != latest["current_state_key"]
                ):
                    raise AssetStateStorageError("cycle close does not match current state evidence")
                updated = connection.execute(
                    """
                    UPDATE asset_state_cycles SET
                        status = ?, closed_run_id = ?, closed_at_utc = ?,
                        closed_by = ?, closing_reason = ?
                    WHERE cycle_id = ? AND status = 'open'
                    """,
                    (
                        cycle.status.value, str(cycle.closed_run_id), _iso(cycle.closed_at_utc),
                        cycle.closed_by, cycle.closing_reason, str(cycle.cycle_id),
                    ),
                )
                if updated.rowcount != 1:
                    raise AssetStateConcurrencyError("cycle changed before close")
                self._insert_cycle_event(connection, close_event)
                self._insert_operation(connection, operation)
                connection.commit()
            except Exception as exc:
                connection.rollback()
                self._raise_storage("could not close asset-state cycle", exc)

    def list_definitions(
        self, query: AssetStateDefinitionQuery = AssetStateDefinitionQuery()
    ) -> tuple[AssetStateDefinitionSummary, ...]:
        clauses: list[str] = []
        values: list[object] = []
        if query.name_text:
            clauses.append("LOWER(d.name) LIKE ?")
            values.append(f"%{query.name_text.lower()}%")
        if query.status:
            clauses.append("d.status = ?")
            values.append(query.status.value)
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        values.append(query.limit)
        with closing(self._database.connect()) as connection:
            rows = connection.execute(
                f"""
                SELECT d.*,
                    (SELECT COUNT(*) FROM asset_state_definition_states s
                     WHERE s.definition_id = d.definition_id) AS state_count,
                    (SELECT COUNT(*) FROM asset_state_definition_edges e
                     WHERE e.definition_id = d.definition_id) AS transition_count
                FROM asset_state_definitions d {where}
                ORDER BY d.created_at_utc DESC, d.definition_id DESC LIMIT ?
                """,
                values,
            ).fetchall()
        return tuple(
            AssetStateDefinitionSummary(
                UUID(row["definition_id"]), int(row["definition_version"]), row["name"],
                AssetStateDefinitionStatus(row["status"]), row["initial_state_key"],
                int(row["state_count"]), int(row["transition_count"]),
                _datetime(row["created_at_utc"]), row["created_by"],
            )
            for row in rows
        )

    def list_cycles(
        self, query: TradingCycleQuery = TradingCycleQuery()
    ) -> tuple[TradingCycleSummary, ...]:
        clauses: list[str] = []
        values: list[object] = []
        if query.symbol:
            clauses.append("c.symbol = ?")
            values.append(query.symbol)
        if query.definition_id:
            clauses.append("c.definition_id = ?")
            values.append(str(query.definition_id))
        if query.state_key:
            clauses.append("s.current_state_key = ?")
            values.append(query.state_key)
        if query.status:
            clauses.append("c.status = ?")
            values.append(query.status.value)
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        values.append(query.limit)
        with closing(self._database.connect()) as connection:
            rows = connection.execute(
                f"""
                SELECT c.*, s.snapshot_id, s.sequence, s.current_state_key,
                    (SELECT COUNT(*) FROM asset_state_transitions t
                     WHERE t.cycle_id = c.cycle_id) AS transition_count
                FROM asset_state_cycles c
                JOIN asset_state_snapshots s ON s.cycle_id = c.cycle_id
                    AND s.sequence = (
                        SELECT MAX(s2.sequence) FROM asset_state_snapshots s2
                        WHERE s2.cycle_id = c.cycle_id
                    )
                {where}
                ORDER BY c.opened_at_utc DESC, c.cycle_id DESC LIMIT ?
                """,
                values,
            ).fetchall()
        return tuple(
            TradingCycleSummary(
                self._cycle_from_row(row), UUID(row["snapshot_id"]), int(row["sequence"]),
                row["current_state_key"], int(row["transition_count"]),
            )
            for row in rows
        )

    def get_cycle_detail(self, cycle_id: UUID) -> AssetStateCycleDetail | None:
        with closing(self._database.connect()) as connection:
            cycle_row = connection.execute(
                "SELECT * FROM asset_state_cycles WHERE cycle_id = ?", (str(cycle_id),)
            ).fetchone()
            if cycle_row is None:
                return None
            cycle = self._cycle_from_row(cycle_row)
            definition = self._load_definition(connection, cycle.definition_id)
            event_rows = connection.execute(
                """
                SELECT * FROM asset_state_cycle_events WHERE cycle_id = ?
                ORDER BY occurred_at_utc, event_id
                """,
                (str(cycle_id),),
            ).fetchall()
            events = tuple(self._cycle_event_from_row(row) for row in event_rows)
            start_events = tuple(item for item in events if item.event_type is AssetStateCycleEventType.STARTED)
            close_events = tuple(item for item in events if item.event_type is AssetStateCycleEventType.CLOSED)
            if len(start_events) != 1 or len(close_events) > 1:
                raise AssetStateStorageError("cycle event history is incomplete or ambiguous")
            snapshot_rows = connection.execute(
                "SELECT * FROM asset_state_snapshots WHERE cycle_id = ? ORDER BY sequence",
                (str(cycle_id),),
            ).fetchall()
            snapshots = tuple(self._snapshot_from_row(row) for row in snapshot_rows)
            if not snapshots:
                raise AssetStateStorageError("cycle has no state snapshot")
            transition_rows = connection.execute(
                """
                SELECT * FROM asset_state_transitions WHERE cycle_id = ?
                ORDER BY predecessor_sequence, occurred_at_utc, transition_id
                """,
                (str(cycle_id),),
            ).fetchall()
            transitions = tuple(self._transition_from_row(connection, row) for row in transition_rows)
            operation_rows = connection.execute(
                """
                SELECT * FROM asset_state_operations WHERE cycle_id = ?
                ORDER BY requested_at_utc, attempt_id
                """,
                (str(cycle_id),),
            ).fetchall()
            operations = tuple(self._operation_from_row(connection, row) for row in operation_rows)
        close_event = close_events[0] if close_events else None
        replay = replay_asset_state(
            definition, cycle, start_events[0], snapshots, transitions, close_event
        )
        return AssetStateCycleDetail(
            definition, cycle, start_events[0], snapshots[-1], snapshots,
            transitions, close_event, operations, replay,
        )

    def list_operations(
        self, query: AssetStateOperationQuery = AssetStateOperationQuery()
    ) -> tuple[AssetStateOperationAttempt, ...]:
        clauses: list[str] = []
        values: list[object] = []
        if query.symbol:
            clauses.append("symbol = ?")
            values.append(query.symbol)
        if query.operation_type:
            clauses.append("operation_type = ?")
            values.append(query.operation_type.value)
        if query.status:
            clauses.append("status = ?")
            values.append(query.status.value)
        if query.run_id:
            clauses.append("run_id = ?")
            values.append(str(query.run_id))
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        values.append(query.limit)
        with closing(self._database.connect()) as connection:
            rows = connection.execute(
                f"""
                SELECT * FROM asset_state_operations {where}
                ORDER BY requested_at_utc DESC, attempt_id DESC LIMIT ?
                """,
                values,
            ).fetchall()
            return tuple(self._operation_from_row(connection, row) for row in rows)

    @staticmethod
    def _validate_definition_operation(
        definition: AssetStateMachineDefinition,
        operation: AssetStateOperationAttempt,
    ) -> None:
        try:
            states = tuple(
                AssetStateDeclaration(item.state_key, item.display_label, item.description)
                for item in operation.state_inputs
            )
            edges = tuple(
                AllowedAssetStateTransition(item.source_state_key, item.destination_state_key)
                for item in operation.transition_inputs
            )
        except ValueError as exc:
            raise AssetStateStorageError(
                "completed definition operation contains invalid raw inputs"
            ) from exc
        if (
            (operation.definition_name or "").strip() != definition.name
            or operation.reason.strip() != definition.reason
            or operation.predecessor_definition_id != definition.predecessor_definition_id
            or (operation.initial_state_key or "").strip().upper() != definition.initial_state_key
            or states != definition.states
            or edges != definition.allowed_transitions
        ):
            raise AssetStateStorageError(
                "definition and completed operation input evidence is inconsistent"
            )

    @staticmethod
    def _insert_cycle(connection: sqlite3.Connection, cycle: TradingCycle) -> None:
        connection.execute(
            """
            INSERT INTO asset_state_cycles (
                cycle_id, symbol, definition_id, definition_version, status,
                opened_run_id, opened_at_utc, opened_by, opening_reason,
                closed_run_id, closed_at_utc, closed_by, closing_reason, schema_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(cycle.cycle_id), cycle.symbol, str(cycle.definition_id),
                cycle.definition_version, cycle.status.value, str(cycle.opened_run_id),
                _iso(cycle.opened_at_utc), cycle.opened_by, cycle.opening_reason,
                str(cycle.closed_run_id) if cycle.closed_run_id else None,
                _iso(cycle.closed_at_utc) if cycle.closed_at_utc else None,
                cycle.closed_by, cycle.closing_reason, cycle.schema_version,
            ),
        )

    @staticmethod
    def _insert_cycle_event(connection: sqlite3.Connection, event: AssetStateCycleEvent) -> None:
        connection.execute(
            """
            INSERT INTO asset_state_cycle_events (
                event_id, operation_id, run_id, cycle_id, symbol, event_type,
                state_key, occurred_at_utc, created_by, reason, schema_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(event.event_id), str(event.operation_id), str(event.run_id),
                str(event.cycle_id), event.symbol, event.event_type.value,
                event.state_key, _iso(event.occurred_at_utc), event.created_by,
                event.reason, event.schema_version,
            ),
        )

    @staticmethod
    def _insert_snapshot(connection: sqlite3.Connection, snapshot: AssetStateSnapshot) -> None:
        connection.execute(
            """
            INSERT INTO asset_state_snapshots (
                snapshot_id, run_id, cycle_id, symbol, definition_id,
                definition_version, sequence, current_state_key,
                predecessor_snapshot_id, causal_transition_id,
                created_at_utc, schema_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(snapshot.snapshot_id), str(snapshot.run_id), str(snapshot.cycle_id),
                snapshot.symbol, str(snapshot.definition_id), snapshot.definition_version,
                snapshot.sequence, snapshot.current_state_key,
                str(snapshot.predecessor_snapshot_id) if snapshot.predecessor_snapshot_id else None,
                str(snapshot.causal_transition_id) if snapshot.causal_transition_id else None,
                _iso(snapshot.created_at_utc), snapshot.schema_version,
            ),
        )

    @staticmethod
    def _insert_transition(connection: sqlite3.Connection, transition: AssetStateTransitionEvent) -> None:
        connection.execute(
            """
            INSERT INTO asset_state_transitions (
                transition_id, operation_id, run_id, cycle_id, symbol,
                definition_id, definition_version, predecessor_snapshot_id,
                predecessor_sequence, previous_state_key, new_state_key,
                trigger_type, occurred_at_utc, created_by, reason, note, schema_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(transition.transition_id), str(transition.operation_id), str(transition.run_id),
                str(transition.cycle_id), transition.symbol, str(transition.definition_id),
                transition.definition_version, str(transition.predecessor_snapshot_id),
                transition.predecessor_sequence, transition.previous_state_key,
                transition.new_state_key, transition.trigger_type.value,
                _iso(transition.occurred_at_utc), transition.created_by,
                transition.reason, transition.note, transition.schema_version,
            ),
        )
        connection.executemany(
            """
            INSERT INTO asset_state_transition_evidence (
                transition_id, ordinal, evidence_kind, evidence_id,
                source_component, source_version
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                (
                    str(transition.transition_id), index, item.evidence_kind.value,
                    item.evidence_id, item.source_component, item.source_version,
                )
                for index, item in enumerate(transition.evidence_bindings)
            ),
        )

    def _insert_operation(
        self, connection: sqlite3.Connection, operation: AssetStateOperationAttempt
    ) -> None:
        stage = connection.execute(
            "SELECT run_id FROM algorithm_run_stages WHERE stage_id = ?",
            (str(operation.stage_id),),
        ).fetchone()
        if stage is None or stage["run_id"] != str(operation.run_id):
            raise AssetStateStorageError(
                "asset-state operation stage must belong to its exact Run"
            )
        resolved_definition_id = self._existing_id(
            connection, "asset_state_definitions", "definition_id", operation.resolved_definition_id
        )
        cycle_id = self._existing_id(connection, "asset_state_cycles", "cycle_id", operation.cycle_id)
        result_snapshot_id = self._existing_id(
            connection, "asset_state_snapshots", "snapshot_id", operation.result_snapshot_id
        )
        transition_id = self._existing_id(
            connection, "asset_state_transitions", "transition_id", operation.transition_id
        )
        cycle_event_id = self._existing_id(
            connection, "asset_state_cycle_events", "event_id", operation.cycle_event_id
        )
        connection.execute(
            """
            INSERT INTO asset_state_operations (
                attempt_id, operation_id, run_id, stage_id, operation_type, status,
                requested_at_utc, completed_at_utc, created_by, reason,
                definition_name, predecessor_definition_id, initial_state_key,
                symbol, requested_definition_id, resolved_definition_id,
                requested_cycle_id, cycle_id, predecessor_snapshot_id,
                requested_state_key, note, result_snapshot_id,
                transition_id, cycle_event_id, error_code, error_summary
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(operation.attempt_id), str(operation.operation_id), str(operation.run_id),
                str(operation.stage_id), operation.operation_type.value, operation.status.value,
                _iso(operation.requested_at_utc), _iso(operation.completed_at_utc),
                operation.created_by, operation.reason, operation.definition_name,
                str(operation.predecessor_definition_id) if operation.predecessor_definition_id else None,
                operation.initial_state_key, operation.symbol,
                str(operation.requested_definition_id) if operation.requested_definition_id else None,
                resolved_definition_id,
                str(operation.cycle_id) if operation.cycle_id else None,
                cycle_id,
                str(operation.predecessor_snapshot_id) if operation.predecessor_snapshot_id else None,
                operation.requested_state_key, operation.note, result_snapshot_id, transition_id,
                cycle_event_id, operation.error_code, operation.error_summary,
            ),
        )
        connection.executemany(
            """
            INSERT INTO asset_state_operation_state_inputs (
                attempt_id, ordinal, state_key, display_label, description
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                (str(operation.attempt_id), index, item.state_key, item.display_label, item.description)
                for index, item in enumerate(operation.state_inputs)
            ),
        )
        connection.executemany(
            """
            INSERT INTO asset_state_operation_edge_inputs (
                attempt_id, ordinal, source_state_key, destination_state_key
            ) VALUES (?, ?, ?, ?)
            """,
            (
                (str(operation.attempt_id), index, item.source_state_key, item.destination_state_key)
                for index, item in enumerate(operation.transition_inputs)
            ),
        )
        connection.executemany(
            """
            INSERT INTO asset_state_operation_evidence_inputs (
                attempt_id, ordinal, evidence_kind, evidence_id,
                source_component, source_version
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                (
                    str(operation.attempt_id), index, item.evidence_kind.value,
                    item.evidence_id, item.source_component, item.source_version,
                )
                for index, item in enumerate(operation.evidence_bindings)
            ),
        )

    @staticmethod
    def _existing_id(connection, table: str, column: str, value: UUID | None) -> str | None:
        if value is None:
            return None
        row = connection.execute(
            f"SELECT 1 FROM {table} WHERE {column} = ?", (str(value),)
        ).fetchone()
        return str(value) if row else None

    @staticmethod
    def _validate_evidence(
        connection: sqlite3.Connection,
        bindings: tuple[AssetStateEvidenceBinding, ...],
    ) -> None:
        for binding in bindings:
            if binding.evidence_kind is AssetStateEvidenceKind.ALGORITHM_RUN:
                table, column = "algorithm_runs", "run_id"
            else:
                table, column = "factor_calculation_runs", "run_id"
            if connection.execute(
                f"SELECT 1 FROM {table} WHERE {column} = ?", (binding.evidence_id,)
            ).fetchone() is None:
                raise AssetStateStorageError(
                    f"referenced {binding.evidence_kind.value} evidence does not exist"
                )

    @staticmethod
    def _validate_definition_rows(
        connection: sqlite3.Connection, definition: AssetStateMachineDefinition
    ) -> None:
        state_rows = connection.execute(
            "SELECT state_key FROM asset_state_definition_states WHERE definition_id = ? ORDER BY ordinal",
            (str(definition.definition_id),),
        ).fetchall()
        edge_rows = connection.execute(
            """
            SELECT source_state_key, destination_state_key
            FROM asset_state_definition_edges WHERE definition_id = ? ORDER BY ordinal
            """,
            (str(definition.definition_id),),
        ).fetchall()
        if tuple(row["state_key"] for row in state_rows) != tuple(item.state_key for item in definition.states):
            raise AssetStateStorageError("stored state declarations are incomplete")
        if tuple((row["source_state_key"], row["destination_state_key"]) for row in edge_rows) != tuple(
            (item.source_state_key, item.destination_state_key) for item in definition.allowed_transitions
        ):
            raise AssetStateStorageError("stored transition graph is incomplete")

    def _load_definition(
        self, connection: sqlite3.Connection, definition_id: UUID
    ) -> AssetStateMachineDefinition:
        row = connection.execute(
            "SELECT * FROM asset_state_definitions WHERE definition_id = ?",
            (str(definition_id),),
        ).fetchone()
        if row is None:
            raise AssetStateStorageError("asset-state definition does not exist")
        return self._definition_from_row(connection, row)

    @staticmethod
    def _definition_from_row(
        connection: sqlite3.Connection, row: sqlite3.Row
    ) -> AssetStateMachineDefinition:
        states = connection.execute(
            "SELECT * FROM asset_state_definition_states WHERE definition_id = ? ORDER BY ordinal",
            (row["definition_id"],),
        ).fetchall()
        edges = connection.execute(
            "SELECT * FROM asset_state_definition_edges WHERE definition_id = ? ORDER BY ordinal",
            (row["definition_id"],),
        ).fetchall()
        return AssetStateMachineDefinition(
            UUID(row["definition_id"]), int(row["definition_version"]),
            UUID(row["predecessor_definition_id"]) if row["predecessor_definition_id"] else None,
            row["name"], row["reason"], row["initial_state_key"],
            tuple(AssetStateDeclaration(item["state_key"], item["display_label"], item["description"]) for item in states),
            tuple(AllowedAssetStateTransition(item["source_state_key"], item["destination_state_key"]) for item in edges),
            AssetStateDefinitionStatus(row["status"]), _datetime(row["created_at_utc"]),
            row["created_by"], int(row["schema_version"]),
        )

    @staticmethod
    def _cycle_from_row(row: sqlite3.Row) -> TradingCycle:
        return TradingCycle(
            UUID(row["cycle_id"]), row["symbol"], UUID(row["definition_id"]),
            int(row["definition_version"]), TradingCycleStatus(row["status"]),
            UUID(row["opened_run_id"]), _datetime(row["opened_at_utc"]),
            row["opened_by"], row["opening_reason"],
            UUID(row["closed_run_id"]) if row["closed_run_id"] else None,
            _datetime(row["closed_at_utc"]), row["closed_by"], row["closing_reason"],
            int(row["schema_version"]),
        )

    @staticmethod
    def _cycle_event_from_row(row: sqlite3.Row) -> AssetStateCycleEvent:
        return AssetStateCycleEvent(
            UUID(row["event_id"]), UUID(row["operation_id"]), UUID(row["run_id"]),
            UUID(row["cycle_id"]), row["symbol"], AssetStateCycleEventType(row["event_type"]),
            row["state_key"], _datetime(row["occurred_at_utc"]), row["created_by"],
            row["reason"], int(row["schema_version"]),
        )

    @staticmethod
    def _snapshot_from_row(row: sqlite3.Row) -> AssetStateSnapshot:
        return AssetStateSnapshot(
            UUID(row["snapshot_id"]), UUID(row["run_id"]), UUID(row["cycle_id"]),
            row["symbol"], UUID(row["definition_id"]), int(row["definition_version"]),
            int(row["sequence"]), row["current_state_key"],
            UUID(row["predecessor_snapshot_id"]) if row["predecessor_snapshot_id"] else None,
            UUID(row["causal_transition_id"]) if row["causal_transition_id"] else None,
            _datetime(row["created_at_utc"]), int(row["schema_version"]),
        )

    @staticmethod
    def _transition_from_row(
        connection: sqlite3.Connection, row: sqlite3.Row
    ) -> AssetStateTransitionEvent:
        evidence_rows = connection.execute(
            "SELECT * FROM asset_state_transition_evidence WHERE transition_id = ? ORDER BY ordinal",
            (row["transition_id"],),
        ).fetchall()
        return AssetStateTransitionEvent(
            UUID(row["transition_id"]), UUID(row["operation_id"]), UUID(row["run_id"]),
            UUID(row["cycle_id"]), row["symbol"], UUID(row["definition_id"]),
            int(row["definition_version"]), UUID(row["predecessor_snapshot_id"]),
            int(row["predecessor_sequence"]), row["previous_state_key"], row["new_state_key"],
            AssetStateTriggerType(row["trigger_type"]), _datetime(row["occurred_at_utc"]),
            row["created_by"], row["reason"],
            tuple(
                AssetStateEvidenceBinding(
                    AssetStateEvidenceKind(item["evidence_kind"]), item["evidence_id"],
                    item["source_component"], item["source_version"],
                )
                for item in evidence_rows
            ),
            row["note"], int(row["schema_version"]),
        )

    @staticmethod
    def _operation_from_row(
        connection: sqlite3.Connection, row: sqlite3.Row
    ) -> AssetStateOperationAttempt:
        states = connection.execute(
            "SELECT * FROM asset_state_operation_state_inputs WHERE attempt_id = ? ORDER BY ordinal",
            (row["attempt_id"],),
        ).fetchall()
        edges = connection.execute(
            "SELECT * FROM asset_state_operation_edge_inputs WHERE attempt_id = ? ORDER BY ordinal",
            (row["attempt_id"],),
        ).fetchall()
        evidence = connection.execute(
            "SELECT * FROM asset_state_operation_evidence_inputs WHERE attempt_id = ? ORDER BY ordinal",
            (row["attempt_id"],),
        ).fetchall()
        return AssetStateOperationAttempt(
            attempt_id=UUID(row["attempt_id"]),
            operation_id=UUID(row["operation_id"]),
            run_id=UUID(row["run_id"]),
            stage_id=UUID(row["stage_id"]),
            operation_type=AssetStateOperationType(row["operation_type"]),
            status=AssetStateOperationStatus(row["status"]),
            requested_at_utc=_datetime(row["requested_at_utc"]),
            completed_at_utc=_datetime(row["completed_at_utc"]),
            created_by=row["created_by"],
            reason=row["reason"],
            definition_name=row["definition_name"],
            predecessor_definition_id=UUID(row["predecessor_definition_id"]) if row["predecessor_definition_id"] else None,
            initial_state_key=row["initial_state_key"],
            state_inputs=tuple(StateDefinitionInput(item["state_key"], item["display_label"], item["description"]) for item in states),
            transition_inputs=tuple(StateTransitionInput(item["source_state_key"], item["destination_state_key"]) for item in edges),
            symbol=row["symbol"],
            requested_definition_id=UUID(row["requested_definition_id"]) if row["requested_definition_id"] else None,
            resolved_definition_id=UUID(row["resolved_definition_id"]) if row["resolved_definition_id"] else None,
            cycle_id=UUID(row["cycle_id"] or row["requested_cycle_id"]) if (row["cycle_id"] or row["requested_cycle_id"]) else None,
            predecessor_snapshot_id=UUID(row["predecessor_snapshot_id"]) if row["predecessor_snapshot_id"] else None,
            requested_state_key=row["requested_state_key"],
            evidence_bindings=tuple(
                AssetStateEvidenceBinding(
                    AssetStateEvidenceKind(item["evidence_kind"]), item["evidence_id"],
                    item["source_component"], item["source_version"],
                )
                for item in evidence
            ),
            note=row["note"],
            result_snapshot_id=UUID(row["result_snapshot_id"]) if row["result_snapshot_id"] else None,
            transition_id=UUID(row["transition_id"]) if row["transition_id"] else None,
            cycle_event_id=UUID(row["cycle_event_id"]) if row["cycle_event_id"] else None,
            error_code=row["error_code"],
            error_summary=row["error_summary"],
        )

    @staticmethod
    def _raise_storage(message: str, exc: BaseException) -> None:
        if isinstance(exc, (AssetStateStorageError, AssetStateConcurrencyError)):
            raise exc
        raise AssetStateStorageError(message, cause=exc) from exc


__all__ = ["SQLiteAssetStateStore"]
