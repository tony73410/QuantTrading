from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from quant_trading.asset_state import (
    AssetStateDefinitionQuery,
    AssetStateOperationStatus,
    AssetStateOperationQuery,
    AssetStateService,
    CloseTradingCycleCommand,
    CreateAssetStateDefinitionCommand,
    StartTradingCycleCommand,
    StateDefinitionInput,
    StateReplayStatus,
    StateTransitionInput,
    TradingCycleQuery,
    TradingCycleStatus,
    TransitionAssetStateCommand,
)
from quant_trading.persistence import SQLiteAssetStateStore, SQLiteRunHistoryRepository
from quant_trading.run_history import AlgorithmRunService, SoftwareIdentity, WorktreeState


NOW = datetime(2026, 7, 20, 20, 0, tzinfo=UTC)


def _service(path: Path):
    state = SQLiteAssetStateStore(path)
    state.initialize()
    runs = SQLiteRunHistoryRepository(path)
    runs.initialize()
    service = AssetStateService(
        state,
        AlgorithmRunService(runs, clock=lambda: NOW),
        SoftwareIdentity("test", "abc123", WorktreeState.CLEAN),
        clock=lambda: NOW,
    )
    return service, state, runs


def _definition_command(*, operation_id=None, edges=None, initial="OBSERVING"):
    return CreateAssetStateDefinitionCommand(
        "Manual research graph",
        "Test only; labels have no financial meaning",
        initial,
        (
            StateDefinitionInput("OBSERVING", "Observing"),
            StateDefinitionInput("STATE_B", "State B"),
            StateDefinitionInput("STATE_C", "State C"),
        ),
        edges
        or (
            StateTransitionInput("OBSERVING", "STATE_B"),
            StateTransitionInput("STATE_B", "STATE_C"),
        ),
        "SESSION",
        "DEFINE",
        "tester",
        operation_id=operation_id,
    )


def _build_open_cycle(path: Path):
    service, state, runs = _service(path)
    definition_result = service.create_definition(_definition_command())
    cycle_result = service.start_cycle(
        StartTradingCycleCommand(
            "aapl",
            definition_result.definition_id,
            "Start explicit research cycle",
            "SESSION",
            "START",
            "tester",
        )
    )
    return service, state, runs, definition_result, cycle_result


def test_definition_cycle_transition_close_and_replay_survive_restart(tmp_path: Path):
    database_path = tmp_path / "central.sqlite3"
    service, state, runs, definition_result, cycle_result = _build_open_cycle(database_path)

    assert definition_result.status is AssetStateOperationStatus.COMPLETED
    assert cycle_result.status is AssetStateOperationStatus.COMPLETED
    transitioned = service.transition(
        TransitionAssetStateCommand(
            cycle_result.cycle_id,
            cycle_result.snapshot_id,
            "state_b",
            "Explicit manual research transition",
            "SESSION",
            "TRANSITION",
            "tester",
        )
    )
    closed = service.close_cycle(
        CloseTradingCycleCommand(
            cycle_result.cycle_id,
            transitioned.snapshot_id,
            "Close research cycle without financial effect",
            "SESSION",
            "CLOSE",
            "tester",
        )
    )

    assert transitioned.status is AssetStateOperationStatus.COMPLETED
    assert closed.status is AssetStateOperationStatus.COMPLETED
    reopened = SQLiteAssetStateStore(database_path)
    reopened.initialize()
    definitions = reopened.list_definitions(AssetStateDefinitionQuery(name_text="manual"))
    cycles = reopened.list_cycles(TradingCycleQuery(symbol="AAPL"))
    detail = reopened.get_cycle_detail(cycle_result.cycle_id)

    assert len(definitions) == 1
    assert len(cycles) == 1
    assert cycles[0].cycle.status is TradingCycleStatus.CLOSED
    assert cycles[0].current_state_key == "STATE_B"
    assert detail.replay.status is StateReplayStatus.MATCH
    assert detail.replay.reconstructed_state_key == "STATE_B"
    assert detail.replay.reconstructed_sequence == 1
    assert len(detail.snapshots) == 2
    assert len(detail.transitions) == 1
    assert len(detail.operations) == 3
    transition_run = runs.get_run_detail(transitioned.run_id)
    assert transition_run.stages[0].name.value == "state"
    artifact = next(
        item for item in transition_run.artifacts
        if item.artifact_type == "asset_state_operation"
    )
    assert artifact.status == "completed"
    assert artifact.children[0].summary == "AAPL = STATE_B (sequence 1)"


def test_disallowed_stale_and_second_open_cycle_fail_without_state_effect(tmp_path: Path):
    service, state, _runs, definition_result, cycle_result = _build_open_cycle(
        tmp_path / "central.sqlite3"
    )

    disallowed = service.transition(
        TransitionAssetStateCommand(
            cycle_result.cycle_id,
            cycle_result.snapshot_id,
            "STATE_C",
            "Not an allowed edge",
            "SESSION",
            "BAD-EDGE",
            "tester",
        )
    )
    second = service.start_cycle(
        StartTradingCycleCommand(
            "AAPL",
            definition_result.definition_id,
            "Duplicate open cycle",
            "SESSION",
            "SECOND",
            "tester",
        )
    )
    accepted = service.transition(
        TransitionAssetStateCommand(
            cycle_result.cycle_id,
            cycle_result.snapshot_id,
            "STATE_B",
            "Accepted edge",
            "SESSION",
            "GOOD",
            "tester",
        )
    )
    stale = service.transition(
        TransitionAssetStateCommand(
            cycle_result.cycle_id,
            cycle_result.snapshot_id,
            "STATE_B",
            "Stale predecessor",
            "SESSION",
            "STALE",
            "tester",
        )
    )

    assert disallowed.status is AssetStateOperationStatus.INVALID_INPUT
    assert second.status is AssetStateOperationStatus.INVALID_INPUT
    assert accepted.status is AssetStateOperationStatus.COMPLETED
    assert stale.status is AssetStateOperationStatus.INVALID_INPUT
    detail = state.get_cycle_detail(cycle_result.cycle_id)
    assert len(detail.transitions) == 1
    assert detail.latest_snapshot.snapshot_id == accepted.snapshot_id
    assert detail.replay.status is StateReplayStatus.MATCH


def test_operation_id_is_idempotent_and_different_payload_is_rejected(tmp_path: Path):
    service, state, _runs, _definition_result, cycle_result = _build_open_cycle(
        tmp_path / "central.sqlite3"
    )
    operation_id = uuid4()
    command = TransitionAssetStateCommand(
        cycle_result.cycle_id,
        cycle_result.snapshot_id,
        "STATE_B",
        "Idempotent manual transition",
        "SESSION",
        "FIRST",
        "tester",
        note="original note",
        operation_id=operation_id,
    )

    first = service.transition(command)
    repeated = service.transition(
        TransitionAssetStateCommand(
            command.cycle_id,
            command.predecessor_snapshot_id,
            command.new_state_key,
            command.reason,
            "SESSION",
            "RETRY",
            "tester",
            note="original note",
            operation_id=operation_id,
        )
    )
    conflicting = service.transition(
        TransitionAssetStateCommand(
            command.cycle_id,
            command.predecessor_snapshot_id,
            "STATE_B",
            command.reason,
            "SESSION",
            "CONFLICT",
            "tester",
            note="different note",
            operation_id=operation_id,
        )
    )
    repeated_after_conflict = service.transition(
        TransitionAssetStateCommand(
            command.cycle_id,
            command.predecessor_snapshot_id,
            command.new_state_key,
            command.reason,
            "SESSION",
            "RETRY-AFTER-CONFLICT",
            "tester",
            note="original note",
            operation_id=operation_id,
        )
    )

    assert repeated.run_id == first.run_id
    assert repeated.snapshot_id == first.snapshot_id
    assert conflicting.status is AssetStateOperationStatus.INVALID_INPUT
    assert repeated_after_conflict.run_id == first.run_id
    detail = state.get_cycle_detail(cycle_result.cycle_id)
    assert len(detail.transitions) == 1
    assert len([item for item in detail.operations if item.operation_id == operation_id]) == 2
    assert next(
        item for item in detail.operations
        if item.status is AssetStateOperationStatus.COMPLETED
        and item.operation_id == operation_id
    ).note == "original note"


def test_unknown_cycle_attempt_preserves_requested_cycle_identity_after_restart(tmp_path: Path):
    database_path = tmp_path / "central.sqlite3"
    service, _state, _runs = _service(database_path)
    unknown_cycle_id = uuid4()
    result = service.close_cycle(
        CloseTradingCycleCommand(
            unknown_cycle_id,
            uuid4(),
            "Unknown cycle must remain auditable",
            "SESSION",
            "UNKNOWN-CYCLE",
            "tester",
        )
    )

    reopened = SQLiteAssetStateStore(database_path)
    reopened.initialize()
    attempts = reopened.list_operations(AssetStateOperationQuery(run_id=result.run_id))
    assert result.status is AssetStateOperationStatus.INVALID_INPUT
    assert len(attempts) == 1
    assert attempts[0].cycle_id == unknown_cycle_id


def test_invalid_definition_is_durable_and_creates_no_definition(tmp_path: Path):
    service, state, runs = _service(tmp_path / "central.sqlite3")
    invalid = service.create_definition(_definition_command(initial="UNKNOWN"))

    assert invalid.status is AssetStateOperationStatus.INVALID_INPUT
    assert state.list_definitions() == ()
    run = runs.get_run_detail(invalid.run_id)
    assert run.summary.run.status.value == "invalid_input"
    assert run.stages[0].status.value == "failed"


def test_sqlite_store_rejects_definition_whose_completed_input_evidence_was_tampered(
    tmp_path: Path,
):
    database_path = tmp_path / "central.sqlite3"
    store = SQLiteAssetStateStore(database_path)
    store.initialize()
    runs = SQLiteRunHistoryRepository(database_path)
    runs.initialize()

    class TamperingStore:
        def __getattr__(self, name):
            return getattr(store, name)

        def create_definition(self, definition, operation):
            store.create_definition(
                definition,
                replace(operation, initial_state_key="STATE_B"),
            )

    service = AssetStateService(
        TamperingStore(),
        AlgorithmRunService(runs, clock=lambda: NOW),
        SoftwareIdentity("test", "abc123", WorktreeState.CLEAN),
        clock=lambda: NOW,
    )
    result = service.create_definition(_definition_command())

    assert result.status is AssetStateOperationStatus.FAILED
    assert store.list_definitions() == ()
    persisted = store.list_operations(AssetStateOperationQuery(run_id=result.run_id))
    assert len(persisted) == 1
    assert "input evidence" in persisted[0].error_summary
