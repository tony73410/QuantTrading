"""Pure materializer for an exact cumulative P28 source."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, time
from uuid import UUID, uuid5
from zoneinfo import ZoneInfo

from .mathematical_cycle_models import (
    MathematicalCycleMaterialization,
    MathematicalCycleSnapshot,
    MathematicalCycleSourceEvidence,
    MathematicalCycleSourceLink,
    MathematicalCycleStream,
    MathematicalCycleStreamDetail,
    MathematicalCycleStreamStatus,
    MathematicalCycleTransitionEvent,
    MathematicalCycleTransitionType,
    MathematicalTradingCycle,
    MathematicalTradingCycleStatus,
)


class MathematicalCycleValidationError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


_EVENT_MAP = {
    "candidate_started": MathematicalCycleTransitionType.CANDIDATE_OBSERVED,
    "candidate_cancelled": MathematicalCycleTransitionType.CANDIDATE_CANCELLED,
    "reversal_confirmed": MathematicalCycleTransitionType.REVERSAL_CONFIRMED,
    "cycle_activated": MathematicalCycleTransitionType.CYCLE_ACTIVATED,
}
_ALLOWED_ATTRIBUTION_PROGRESSIONS = {
    ("provisional_new_cycle", "committed_to_new_cycle"),
    ("provisional_new_cycle", "discarded_for_new_cycle"),
}


def _id(stream_id: UUID, kind: str, identity: str) -> UUID:
    return uuid5(stream_id, f"{kind}:{identity}")


def _xnys_open(session) -> datetime:
    return datetime.combine(session, time(9, 30), ZoneInfo("America/New_York"))


class MathematicalCycleEngine:
    """Build append-only snapshots/transitions without importing P28."""

    def materialize(
        self,
        *,
        stream_id: UUID,
        stream_name: str,
        definition_id: UUID,
        definition_version: int,
        source: MathematicalCycleSourceEvidence,
        created_at_utc: datetime,
        created_by: str,
        reason: str,
        prior: MathematicalCycleStreamDetail | None = None,
    ) -> MathematicalCycleMaterialization:
        if prior is not None:
            self._validate_extension(prior, source)
        cycles = list(prior.cycles if prior else ())
        snapshots = list(prior.snapshots if prior else ())
        transitions = list(prior.transitions if prior else ())
        links = list(prior.source_links if prior else ())
        prefix = len(snapshots)

        if not cycles:
            initial_cycle = MathematicalTradingCycle(
                _id(stream_id, "cycle", "1"), stream_id, 1, source.initial_direction,
                source.steps[0].session, _xnys_open(source.steps[0].session),
                source.seed_session, source.seed_price, None,
                MathematicalTradingCycleStatus.OPEN, None, None, None,
            )
            cycles.append(initial_cycle)

        # Attribution resolution is an append-only formal event.  Historical
        # snapshots intentionally retain what was visible when first recorded.
        for index in range(prefix):
            previous_link = links[index]
            next_step = source.steps[index]
            if previous_link.recorded_attribution != next_step.attribution:
                transition_id = _id(
                    stream_id, "attribution",
                    f"{index + 1}:{previous_link.recorded_attribution}:{next_step.attribution}",
                )
                if all(item.transition_id != transition_id for item in transitions):
                    transitions.append(MathematicalCycleTransitionEvent(
                        transition_id, stream_id, len(transitions) + 1, next_step.session,
                        MathematicalCycleTransitionType.ATTRIBUTION_RESOLVED,
                        snapshots[index].cycle_id, snapshots[index].cycle_id,
                        next_step.direction_at_open, next_step.direction_at_close,
                        next_step.candidate_origin_session or next_step.session,
                        next_step.candidate_origin_price or next_step.cycle_reference_price,
                        source.result_id, source.run_id, None, next_step.source_step_id,
                        None, None, snapshots[index].snapshot_id,
                        previous_link.recorded_attribution, next_step.attribution,
                        "later exact cumulative P28 evidence resolved provisional attribution",
                        created_at_utc,
                    ))

        events_by_session: dict[object, list] = {}
        for event in source.events:
            events_by_session.setdefault(event.session, []).append(event)

        current_cycle = self._current_cycle(cycles, snapshots)
        predecessor_snapshot_id = snapshots[-1].snapshot_id if snapshots else None
        for step in source.steps[prefix:]:
            session_events = events_by_session.get(step.session, ())
            activation = next((event for event in session_events if event.event_type == "cycle_activated"), None)
            if activation is not None:
                if activation.new_direction is None or activation.activation_effective_session != step.session:
                    raise MathematicalCycleValidationError("SOURCE_INCOMPATIBLE", "activation evidence is incomplete")
                new_cycle_id = _id(stream_id, "cycle", str(len(cycles) + 1))
                activation_transition_id = _id(stream_id, "event", activation.semantic_fingerprint)
                cycles.append(MathematicalTradingCycle(
                    new_cycle_id, stream_id, len(cycles) + 1, activation.new_direction,
                    step.session, _xnys_open(step.session), activation.origin_session,
                    activation.origin_price, current_cycle.cycle_id,
                    MathematicalTradingCycleStatus.OPEN, None, None,
                    activation_transition_id,
                ))
                current_cycle = cycles[-1]

            if step.direction_at_open != current_cycle.direction:
                raise MathematicalCycleValidationError(
                    "SOURCE_INCOMPATIBLE", "source direction does not match operational cycle"
                )
            snapshot_id = _id(stream_id, "snapshot", str(step.session))
            snapshot = MathematicalCycleSnapshot(
                snapshot_id, stream_id, current_cycle.cycle_id, len(snapshots) + 1,
                step.session, step.direction_at_open, step.direction_at_close,
                step.cycle_reference_session, step.cycle_reference_price,
                step.running_extreme_before, step.running_extreme_after,
                step.candidate_state, step.threshold, step.directional_log_distance,
                step.attribution, step.cumulative_new_cycle_movement,
                source.result_id, source.run_id, step.source_step_id,
                step.observation_id, predecessor_snapshot_id, created_at_utc,
            )
            snapshots.append(snapshot)
            links.append(MathematicalCycleSourceLink(
                _id(stream_id, "source-link", str(step.session)), stream_id,
                snapshot_id, snapshot.sequence, source.result_id, source.run_id,
                step.source_step_id, step.observation_id,
                step.semantic_fingerprint, step.attribution, created_at_utc,
            ))
            predecessor_snapshot_id = snapshot_id

            for event in session_events:
                event_type = _EVENT_MAP.get(event.event_type)
                if event_type is None:
                    raise MathematicalCycleValidationError("SOURCE_INCOMPATIBLE", "unknown P28 event type")
                transition_id = _id(stream_id, "event", event.semantic_fingerprint)
                new_cycle_id = current_cycle.cycle_id if event_type is MathematicalCycleTransitionType.CYCLE_ACTIVATED else None
                old_cycle_id = (
                    current_cycle.predecessor_cycle_id
                    if event_type is MathematicalCycleTransitionType.CYCLE_ACTIVATED
                    else current_cycle.cycle_id
                )
                transitions.append(MathematicalCycleTransitionEvent(
                    transition_id, stream_id, len(transitions) + 1, event.session,
                    event_type, old_cycle_id, new_cycle_id, event.old_direction,
                    event.new_direction, event.origin_session, event.origin_price,
                    source.result_id, source.run_id, event.source_event_id,
                    event.candidate_day1_step_id, event.candidate_day2_step_id,
                    event.activation_effective_session, snapshot_id, None, None,
                    event.reason, created_at_utc,
                ))
                if event_type is MathematicalCycleTransitionType.REVERSAL_CONFIRMED:
                    index = next(i for i, item in enumerate(cycles) if item.cycle_id == current_cycle.cycle_id)
                    cycles[index] = replace(
                        current_cycle,
                        status=MathematicalTradingCycleStatus.CLOSED,
                        confirmed_close_session=step.session,
                        confirmed_close_utc=step.official_close_utc,
                    )
                    current_cycle = cycles[index]

        if len(snapshots) == prefix:
            raise MathematicalCycleValidationError("INVALID_INPUT", "source adds no new session")
        latest = snapshots[-1]
        original = prior.stream if prior else None
        stream = MathematicalCycleStream(
            stream_id, stream_name, source.symbol, definition_id, definition_version,
            MathematicalCycleStreamStatus.OPEN,
            original.original_source_result_id if original else source.result_id,
            original.original_source_run_id if original else source.run_id,
            source.definition_id, source.definition_version, source.profile_result_id,
            source.profile_run_id, source.profile_definition_id,
            source.profile_definition_version, source.seed_session,
            source.seed_observation_id, source.seed_price,
            source.initial_direction, source.calendar_fingerprint,
            source.result_id, source.run_id, latest.snapshot_id, latest.sequence,
            original.created_at_utc if original else created_at_utc,
            original.created_by if original else created_by,
            original.reason if original else reason,
        )
        return MathematicalCycleMaterialization(
            stream, tuple(cycles), tuple(snapshots), tuple(transitions), tuple(links)
        )

    @staticmethod
    def _current_cycle(cycles, snapshots):
        if not snapshots:
            return cycles[-1]
        cycle_id = snapshots[-1].cycle_id
        return next(item for item in cycles if item.cycle_id == cycle_id)

    @staticmethod
    def _validate_extension(prior: MathematicalCycleStreamDetail, source: MathematicalCycleSourceEvidence) -> None:
        stream = prior.stream
        identity = (
            source.symbol == stream.symbol
            and source.definition_id == stream.source_definition_id
            and source.definition_version == stream.source_definition_version
            and source.profile_result_id == stream.profile_result_id
            and source.profile_run_id == stream.profile_run_id
            and source.profile_definition_id == stream.profile_definition_id
            and source.profile_definition_version == stream.profile_definition_version
            and source.seed_session == stream.seed_session
            and source.seed_observation_id == stream.seed_observation_id
            and source.seed_price == stream.seed_price
            and source.initial_direction == stream.initial_direction
            and source.calendar_fingerprint == stream.calendar_fingerprint
        )
        if not identity:
            raise MathematicalCycleValidationError("SOURCE_INCOMPATIBLE", "source identity differs from stream seed")
        if len(source.steps) <= len(prior.snapshots):
            raise MathematicalCycleValidationError("INVALID_INPUT", "cumulative source must extend the stream")
        if len(prior.source_links) != len(prior.snapshots):
            raise MathematicalCycleValidationError("SOURCE_INCOMPATIBLE", "stored source-link history is incomplete")
        for link, step in zip(prior.source_links, source.steps):
            if link.stable_semantic_fingerprint != step.semantic_fingerprint:
                raise MathematicalCycleValidationError("SOURCE_PREFIX_DIVERGENCE", "historical source prefix changed")
            if link.recorded_attribution != step.attribution and (
                link.recorded_attribution, step.attribution
            ) not in _ALLOWED_ATTRIBUTION_PROGRESSIONS:
                raise MathematicalCycleValidationError("SOURCE_PREFIX_DIVERGENCE", "historical attribution changed incompatibly")


__all__ = ["MathematicalCycleEngine", "MathematicalCycleValidationError"]
