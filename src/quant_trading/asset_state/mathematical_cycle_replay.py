"""Stored-view replay validation for P23-2B state."""

from __future__ import annotations

from .mathematical_cycle_interfaces import MathematicalCycleStateQueryService
from .mathematical_cycle_models import MathematicalCycleStreamDetail, MathematicalCycleTransitionType


def replay_mathematical_cycle(detail: MathematicalCycleStreamDetail) -> MathematicalCycleStreamDetail:
    if not detail.snapshots or not detail.cycles:
        raise ValueError("mathematical-cycle stream history is incomplete")
    if tuple(item.sequence for item in detail.snapshots) != tuple(range(1, len(detail.snapshots) + 1)):
        raise ValueError("mathematical-cycle snapshot sequence has a gap")
    if tuple(item.sequence for item in detail.transitions) != tuple(range(1, len(detail.transitions) + 1)):
        raise ValueError("mathematical-cycle transition sequence has a gap")
    if tuple(item.sequence for item in detail.source_links) != tuple(range(1, len(detail.source_links) + 1)):
        raise ValueError("mathematical-cycle source-link sequence has a gap")
    if len(detail.source_links) != len(detail.snapshots):
        raise ValueError("mathematical-cycle source links do not cover every snapshot")
    cycle_ids = {item.cycle_id for item in detail.cycles}
    previous = None
    for snapshot, link in zip(detail.snapshots, detail.source_links):
        if snapshot.cycle_id not in cycle_ids or snapshot.predecessor_snapshot_id != previous:
            raise ValueError("mathematical-cycle snapshot chain is inconsistent")
        if link.snapshot_id != snapshot.snapshot_id or link.source_step_id != snapshot.source_step_id:
            raise ValueError("mathematical-cycle source link differs from snapshot")
        previous = snapshot.snapshot_id
    if detail.stream.latest_snapshot_id != detail.snapshots[-1].snapshot_id or detail.stream.latest_sequence != detail.snapshots[-1].sequence:
        raise ValueError("mathematical-cycle stream cursor is stale")
    activations = [item for item in detail.transitions if item.event_type is MathematicalCycleTransitionType.CYCLE_ACTIVATED]
    if len(detail.cycles) != len(activations) + 1:
        raise ValueError("mathematical-cycle activation count is inconsistent")
    return detail


class MathematicalCycleReplayService:
    def __init__(self, queries: MathematicalCycleStateQueryService) -> None:
        self._queries = queries

    def replay(self, stream_id) -> MathematicalCycleStreamDetail:
        detail = self._queries.get_stream_detail(stream_id)
        if detail is None:
            raise KeyError("mathematical-cycle stream does not exist")
        return replay_mathematical_cycle(detail)


__all__ = ["MathematicalCycleReplayService", "replay_mathematical_cycle"]
