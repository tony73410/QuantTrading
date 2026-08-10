"""Stored-view and deterministic recalculation replay for P23-2."""

from __future__ import annotations

from datetime import datetime
import json

from .reversal_observation_engine import ReversalObservationEngine
from .reversal_observation_models import (
    ReversalObservationCommand,
    ReversalObservationDefinition,
    ReversalObservationMarketEvidence,
    ReversalObservationPriceObservation,
    ReversalObservationResult,
    ReversalPriceEvidence,
    ReversalFloatEvidence,
)
from .reversal_observation_interfaces import ReversalObservationQueryService


def replay_reversal_observation(
    historical: ReversalObservationResult,
    definition: ReversalObservationDefinition,
    *,
    engine: ReversalObservationEngine | None = None,
) -> ReversalObservationResult:
    """Recalculate from normalized stored evidence without changing history."""
    calendar = next(item for item in historical.source_links if item.source_type == "calendar")
    corporate = next(
        item for item in historical.source_links if item.source_type == "corporate_action_evidence"
    )
    seed_link = next(item for item in historical.source_links if item.source_type == "seed_observation")
    payload = json.loads(seed_link.source_fingerprint or "{}")
    seed = ReversalObservationPriceObservation(
        seed_link.source_id, historical.seed_session,
        datetime.fromisoformat(payload["official_close_utc"]),
        datetime.fromisoformat(payload["first_observed_at_utc"]),
        datetime.fromisoformat(payload["available_at_utc"]),
        payload["raw_source_id"], payload["split_source_id"],
        ReversalPriceEvidence(payload["raw_close_text"], ReversalFloatEvidence(
            float.fromhex(payload["raw_close_hex"]), payload["raw_close_hex"]
        )),
        ReversalPriceEvidence(payload["split_close_text"], ReversalFloatEvidence(
            float.fromhex(payload["split_close_hex"]), payload["split_close_hex"]
        )),
    )
    market = ReversalObservationMarketEvidence(
        historical.market_evidence_id, historical.market_evidence_fingerprint,
        historical.symbol, "persisted-replay", "persisted-replay", "1Day",
        "raw+split", "persisted-replay", calendar.source_id,
        calendar.source_version or "unknown", calendar.source_fingerprint or "unknown",
        corporate.source_id, seed,
        tuple(step.observation for step in historical.daily_steps),
        tuple(step.session for step in historical.daily_steps), historical.warnings,
        historical.created_at_utc,
    )
    command = ReversalObservationCommand(
        historical.result_id, "persisted-replay", "persisted-replay", historical.symbol,
        historical.definition_id, historical.definition_version,
        historical.profile.result_id, historical.initial_direction,
        historical.seed_session, seed.observation_id, seed.split_close,
        historical.final_evaluation_session, calendar.source_id,
        calendar.source_version or "unknown", calendar.source_fingerprint or "unknown",
        "persisted-replay", "deterministic recalculation replay",
    )
    recalculated = (engine or ReversalObservationEngine()).calculate(
        definition, command, historical.profile, market,
        created_at_utc=historical.created_at_utc,
        software_version=historical.software_version,
        source_revision=historical.source_revision,
        worktree_state=historical.worktree_state,
    )
    if recalculated != historical:
        raise ValueError("P28 recalculation replay differs from immutable history")
    return recalculated


class ReversalObservationReplayService:
    def __init__(self, queries: ReversalObservationQueryService) -> None:
        self._queries = queries

    def recalculate(self, result_id) -> ReversalObservationResult:
        historical = self._queries.get_result(result_id)
        if historical is None:
            raise KeyError("P28 result does not exist")
        definition = self._queries.get_definition(historical.definition_id)
        if definition is None:
            raise KeyError("P28 definition cannot be reloaded")
        return replay_reversal_observation(historical, definition)

    def compare(self, left_id, right_id) -> tuple[str, ...]:
        left = self._queries.get_result(left_id)
        right = self._queries.get_result(right_id)
        if left is None or right is None:
            raise KeyError("both P28 comparison results must exist")
        if (
            left.symbol != right.symbol
            or left.seed_session != right.seed_session
            or left.market_evidence_fingerprint != right.market_evidence_fingerprint
        ):
            raise ValueError("P28 comparison requires the same symbol, seed and exact source series")
        return (
            f"status: {left.status.value} → {right.status.value}",
            f"definition: v{left.definition_version} → v{right.definition_version}",
            f"candidate/cancel/confirm/activate: "
            f"{left.candidate_count}/{left.cancellation_count}/{left.confirmation_count}/{left.activation_count} → "
            f"{right.candidate_count}/{right.cancellation_count}/{right.confirmation_count}/{right.activation_count}",
            f"fingerprint equal: {left.calculation_fingerprint == right.calculation_fingerprint}",
        )


__all__ = ["ReversalObservationReplayService", "replay_reversal_observation"]
