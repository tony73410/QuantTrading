"""Deterministically verify stored asset-state history without repairing it."""

from __future__ import annotations

from .models import (
    AssetStateCycleEvent,
    AssetStateCycleEventType,
    AssetStateMachineDefinition,
    AssetStateSnapshot,
    AssetStateTransitionEvent,
    StateReplayIssue,
    StateReplayResult,
    StateReplayStatus,
    TradingCycle,
    TradingCycleStatus,
)


def replay_asset_state(
    definition: AssetStateMachineDefinition,
    cycle: TradingCycle,
    start_event: AssetStateCycleEvent,
    snapshots: tuple[AssetStateSnapshot, ...],
    transitions: tuple[AssetStateTransitionEvent, ...],
    close_event: AssetStateCycleEvent | None,
) -> StateReplayResult:
    """Return exact integrity evidence; never infer or mutate a missing fact."""

    issues: list[StateReplayIssue] = []

    def issue(code: str, message: str) -> None:
        issues.append(StateReplayIssue(code, message))

    if cycle.definition_id != definition.definition_id or cycle.definition_version != definition.definition_version:
        issue("STATE-DEFINITION", "Cycle definition identity does not match the loaded definition.")
    if start_event.event_type is not AssetStateCycleEventType.STARTED:
        issue("STATE-START-TYPE", "Cycle history does not begin with a start event.")
    if start_event.cycle_id != cycle.cycle_id or start_event.symbol != cycle.symbol:
        issue("STATE-START-IDENTITY", "Cycle start identity does not match the cycle.")
    if start_event.state_key != definition.initial_state_key:
        issue("STATE-INITIAL", "Cycle start state does not match the exact definition version.")
    if not snapshots:
        issue("STATE-SNAPSHOT-MISSING", "Cycle history has no immutable state snapshot.")
        return StateReplayResult(
            cycle.cycle_id,
            StateReplayStatus.MISMATCH,
            None,
            0,
            None,
            0,
            tuple(issues),
            "状态重放失败：缺少初始快照。",
        )

    ordered_snapshots = tuple(sorted(snapshots, key=lambda item: item.sequence))
    ordered_transitions = tuple(
        sorted(transitions, key=lambda item: (item.predecessor_sequence, item.occurred_at_utc, str(item.transition_id)))
    )
    initial = ordered_snapshots[0]
    state = definition.initial_state_key
    sequence = 0
    if (
        initial.sequence != 0
        or initial.current_state_key != state
        or initial.cycle_id != cycle.cycle_id
        or initial.definition_id != definition.definition_id
        or initial.definition_version != definition.definition_version
    ):
        issue("STATE-SNAPSHOT-INITIAL", "Initial snapshot does not match cycle start evidence.")

    if len(ordered_snapshots) != len(ordered_transitions) + 1:
        issue("STATE-SNAPSHOT-COUNT", "Snapshot count must equal accepted transition count plus one.")

    for index, transition in enumerate(ordered_transitions, start=1):
        previous_snapshot = ordered_snapshots[index - 1] if index - 1 < len(ordered_snapshots) else None
        next_snapshot = ordered_snapshots[index] if index < len(ordered_snapshots) else None
        if transition.cycle_id != cycle.cycle_id or transition.symbol != cycle.symbol:
            issue("STATE-TRANSITION-IDENTITY", f"Transition {transition.transition_id} has wrong cycle identity.")
        if transition.definition_id != definition.definition_id or transition.definition_version != definition.definition_version:
            issue("STATE-TRANSITION-DEFINITION", f"Transition {transition.transition_id} has wrong definition identity.")
        if transition.predecessor_sequence != sequence or transition.previous_state_key != state:
            issue("STATE-TRANSITION-PREDECESSOR", f"Transition {transition.transition_id} does not follow reconstructed state.")
        if previous_snapshot is None or transition.predecessor_snapshot_id != previous_snapshot.snapshot_id:
            issue("STATE-TRANSITION-SNAPSHOT", f"Transition {transition.transition_id} has wrong predecessor snapshot.")
        if not definition.permits(state, transition.new_state_key):
            issue("STATE-EDGE", f"Transition {transition.transition_id} is not allowed by the exact definition version.")
        state = transition.new_state_key
        sequence += 1
        if next_snapshot is None:
            issue("STATE-SNAPSHOT-MISSING", f"Transition {transition.transition_id} has no result snapshot.")
        elif (
            next_snapshot.sequence != sequence
            or next_snapshot.predecessor_snapshot_id != (previous_snapshot.snapshot_id if previous_snapshot else None)
            or next_snapshot.causal_transition_id != transition.transition_id
            or next_snapshot.current_state_key != state
            or next_snapshot.cycle_id != cycle.cycle_id
            or next_snapshot.definition_id != definition.definition_id
            or next_snapshot.definition_version != definition.definition_version
        ):
            issue("STATE-SNAPSHOT-CHAIN", f"Snapshot after transition {transition.transition_id} is inconsistent.")

    latest = ordered_snapshots[-1]
    if latest.current_state_key != state or latest.sequence != sequence:
        issue("STATE-LATEST", "Stored latest snapshot does not match reconstructed state.")
    if cycle.status is TradingCycleStatus.CLOSED:
        if close_event is None or close_event.event_type is not AssetStateCycleEventType.CLOSED:
            issue("STATE-CLOSE-MISSING", "Closed cycle has no immutable close event.")
        elif (
            close_event.cycle_id != cycle.cycle_id
            or close_event.symbol != cycle.symbol
            or close_event.state_key != state
            or close_event.run_id != cycle.closed_run_id
        ):
            issue("STATE-CLOSE-IDENTITY", "Cycle close event does not match final reconstructed state.")
    elif close_event is not None:
        issue("STATE-CLOSE-UNEXPECTED", "Open cycle contains a close event.")

    status = StateReplayStatus.MATCH if not issues else StateReplayStatus.MISMATCH
    return StateReplayResult(
        cycle.cycle_id,
        status,
        state,
        sequence,
        latest.current_state_key,
        latest.sequence,
        tuple(issues),
        (
            f"状态重放一致：{cycle.symbol} 当前为 {state}，序号 {sequence}。"
            if status is StateReplayStatus.MATCH
            else f"状态重放不一致：发现 {len(issues)} 个完整性问题。"
        ),
    )


__all__ = ["replay_asset_state"]
