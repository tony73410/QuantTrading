"""Resolve one exact successful P28 Result/Run for P23-2B promotion."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Protocol

from quant_trading.asset_state import (
    MathematicalCyclePromotionCommand,
    MathematicalCycleSourceEvidence,
    MathematicalCycleSourceEvent,
    MathematicalCycleSourceStep,
    MathematicalCycleStateOperation,
    MathematicalCycleStateService,
    MathematicalDirection,
    MathematicalNumberEvidence,
    MathematicalPriceEvidence,
    ReversalObservationOperationStatus,
    ReversalObservationQuery,
    ReversalObservationQueryService,
)


@dataclass(frozen=True, slots=True)
class MathematicalCyclePromotionPreflight:
    command: MathematicalCyclePromotionCommand
    source: MathematicalCycleSourceEvidence
    summary: str


class MathematicalCyclePromotionRunner(Protocol):
    def prepare(self, command: MathematicalCyclePromotionCommand) -> MathematicalCyclePromotionPreflight: ...
    def promote(self, command: MathematicalCyclePromotionCommand) -> MathematicalCycleStateOperation: ...


class MathematicalCyclePromotionCoordinator:
    def __init__(self, reversal_queries: ReversalObservationQueryService, service: MathematicalCycleStateService) -> None:
        self._reversal = reversal_queries
        self._service = service

    def prepare(self, command: MathematicalCyclePromotionCommand) -> MathematicalCyclePromotionPreflight:
        operations = self._reversal.list_operations(ReversalObservationQuery(
            run_id=command.source_run_id, result_id=command.source_result_id, limit=2,
        ))
        operation = next((item for item in operations if item.run_id == command.source_run_id and item.result is not None and item.status in {ReversalObservationOperationStatus.COMPLETED, ReversalObservationOperationStatus.COMPLETED_WITH_WARNINGS}), None)
        if operation is None or operation.result is None:
            raise KeyError("exact successful P28 result/Run pair cannot be reloaded")
        result = operation.result
        if result.execution_allowed or result.live_allowed or result.schema_version != 1:
            raise ValueError("P28 source safety metadata is incompatible")
        if result.symbol != command.symbol:
            raise ValueError("P28 source symbol differs from the command")
        calendar = next((item for item in result.source_links if item.source_type == "calendar"), None)
        seed_link = next((item for item in result.source_links if item.source_type == "seed_observation"), None)
        if calendar is None or seed_link is None:
            raise ValueError("P28 source is missing exact calendar or seed evidence")
        seed_payload = json.loads(seed_link.source_fingerprint or "{}")
        events = tuple(self._event(item) for item in result.events)
        event_by_id = {item.event_id: item for item in result.events}
        steps = tuple(self._step(item, event_by_id) for item in result.daily_steps)
        source = MathematicalCycleSourceEvidence(
            result.result_id, operation.run_id, result.definition_id,
            result.definition_version, result.profile.result_id,
            result.profile.result_run_id, result.profile.source_definition_id,
            result.profile.source_definition_version, result.symbol,
            result.seed_session, seed_link.source_id,
            MathematicalPriceEvidence(
                seed_payload["split_close_text"],
                MathematicalNumberEvidence(float.fromhex(seed_payload["split_close_hex"]), seed_payload["split_close_hex"]),
            ),
            MathematicalDirection(result.initial_direction.value),
            result.market_evidence_id, result.market_evidence_fingerprint,
            calendar.source_id, calendar.source_version or "unknown",
            calendar.source_fingerprint or "unknown", steps, events,
            result.warnings,
        )
        return MathematicalCyclePromotionPreflight(
            command, source,
            f"{source.symbol}: exact P28 Result {source.result_id}, Run {source.run_id}, "
            f"{len(source.steps)} completed sessions; mathematical state remains DISABLED / NO EXECUTION.",
        )

    def promote(self, command: MathematicalCyclePromotionCommand) -> MathematicalCycleStateOperation:
        try:
            prepared = self.prepare(command)
        except Exception as exc:
            return self._service.record_source_failure(command, exc)
        return self._service.promote(command, prepared.source)

    @classmethod
    def _step(cls, item, events_by_id) -> MathematicalCycleSourceStep:
        event_semantics = tuple(
            cls._event_payload(events_by_id[event_id]) for event_id in item.event_ids
        )
        payload = {
            "ordinal": item.ordinal, "session": item.session.isoformat(),
            "observation_id": item.observation.observation_id,
            "official_close_utc": item.observation.official_close_utc.isoformat(),
            "split_close": cls._price_payload(item.observation.split_close),
            "direction_open": item.direction_at_open.value,
            "direction_close": item.direction_at_close.value,
            "reference_session": item.cycle_reference_session.isoformat(),
            "reference_price": cls._price_payload(item.cycle_reference_price),
            "extreme_before": cls._price_payload(item.running_extreme_before),
            "extreme_after": cls._price_payload(item.running_extreme_after),
            "candidate_origin_session": item.candidate_origin_session.isoformat() if item.candidate_origin_session else None,
            "candidate_origin_price": cls._price_payload(item.candidate_origin_price) if item.candidate_origin_price else None,
            "candidate_state": item.candidate_state_after_close.value,
            "threshold": item.threshold.ieee_hex,
            "directional_distance": item.directional_log_distance.ieee_hex,
            "cumulative_movement": item.cumulative_new_cycle_movement.ieee_hex,
            "events": event_semantics,
        }
        return MathematicalCycleSourceStep(
            item.step_id, item.ordinal, item.session, item.observation.observation_id,
            item.observation.official_close_utc,
            MathematicalDirection(item.direction_at_open.value),
            MathematicalDirection(item.direction_at_close.value),
            item.cycle_reference_session, cls._price(item.cycle_reference_price),
            cls._price(item.running_extreme_before), cls._price(item.running_extreme_after),
            item.candidate_origin_session,
            cls._price(item.candidate_origin_price) if item.candidate_origin_price else None,
            item.candidate_state_after_close.value,
            MathematicalNumberEvidence(item.threshold.value, item.threshold.ieee_hex),
            MathematicalNumberEvidence(item.directional_log_distance.value, item.directional_log_distance.ieee_hex),
            item.attribution.value,
            MathematicalNumberEvidence(item.cumulative_new_cycle_movement.value, item.cumulative_new_cycle_movement.ieee_hex),
            item.event_ids, cls._hash(payload),
        )

    @classmethod
    def _event(cls, item) -> MathematicalCycleSourceEvent:
        return MathematicalCycleSourceEvent(
            item.event_id, item.ordinal, item.session, item.event_type.value,
            MathematicalDirection(item.old_direction.value),
            MathematicalDirection(item.new_direction.value) if item.new_direction else None,
            item.origin_session, cls._price(item.origin_price),
            item.candidate_day1_step_id, item.candidate_day2_step_id,
            item.activation_effective_session, item.reason,
            cls._hash(cls._event_payload(item)),
        )

    @classmethod
    def _event_payload(cls, item):
        return {
            "ordinal": item.ordinal, "session": item.session.isoformat(),
            "type": item.event_type.value, "old_direction": item.old_direction.value,
            "new_direction": item.new_direction.value if item.new_direction else None,
            "origin_session": item.origin_session.isoformat(),
            "origin_price": cls._price_payload(item.origin_price),
            "activation_session": item.activation_effective_session.isoformat() if item.activation_effective_session else None,
            "reason": item.reason, "trigger_values": item.trigger_values,
        }

    @staticmethod
    def _price(value) -> MathematicalPriceEvidence:
        return MathematicalPriceEvidence(value.decimal_text, MathematicalNumberEvidence(value.value.value, value.value.ieee_hex))

    @staticmethod
    def _price_payload(value):
        return [value.decimal_text, value.value.ieee_hex]

    @staticmethod
    def _hash(payload) -> str:
        return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


__all__ = ["MathematicalCyclePromotionCoordinator", "MathematicalCyclePromotionPreflight", "MathematicalCyclePromotionRunner"]
