"""Pure P23-2 symmetric two-session reversal evaluator."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, datetime
import hashlib
import json
import math
from uuid import NAMESPACE_URL, UUID, uuid5

from .reversal_observation_models import (
    REVERSAL_OBSERVATION_COMPONENT_VERSION,
    ReversalAttribution,
    ReversalCandidateState,
    ReversalDirection,
    ReversalEventType,
    ReversalFloatEvidence,
    ReversalObservationCommand,
    ReversalObservationDailyStep,
    ReversalObservationDefinition,
    ReversalObservationEvent,
    ReversalObservationMarketEvidence,
    ReversalObservationProfileEvidence,
    ReversalObservationResult,
    ReversalObservationResultStatus,
    ReversalObservationSourceLink,
    ReversalPriceEvidence,
)


_RESULT_NAMESPACE = uuid5(NAMESPACE_URL, "quanttrade:p28:reversal-observation-result")
_P27_COMPONENT_ID = "factor.daily_volatility_profile.p23_1f.v1"
_P27_COMPONENT_VERSION = "1.0.0"


class ReversalObservationValidationError(ValueError):
    def __init__(self, status: ReversalObservationResultStatus, message: str) -> None:
        super().__init__(message)
        self.status = status


@dataclass(slots=True)
class _Candidate:
    old_direction: ReversalDirection
    origin_session: date
    origin_price: ReversalPriceEvidence
    day1_index: int
    day1_step_id: UUID
    activation_session: date | None = None
    confirmed: bool = False


class ReversalObservationEngine:
    """Evaluate completed sessions without mutating formal Asset State."""

    def calculate(
        self,
        definition: ReversalObservationDefinition,
        command: ReversalObservationCommand,
        profile: ReversalObservationProfileEvidence,
        market: ReversalObservationMarketEvidence,
        *,
        created_at_utc: datetime,
        software_version: str,
        source_revision: str | None,
        worktree_state: str,
    ) -> ReversalObservationResult:
        self._validate_sources(definition, command, profile, market)
        fingerprint = self._fingerprint(definition, command, profile, market)
        result_id = uuid5(_RESULT_NAMESPACE, fingerprint)
        threshold_value = definition.shared_multiplier.value * profile.profile_log_scale.value
        if not math.isfinite(threshold_value) or threshold_value <= 0:
            raise ReversalObservationValidationError(
                ReversalObservationResultStatus.NONFINITE_CALCULATION,
                "P28 threshold must be positive and finite",
            )
        threshold = ReversalFloatEvidence(threshold_value)
        direction = command.initial_direction
        cycle_reference_session = command.seed_session
        cycle_reference_price = command.seed_split_close
        extreme_session = command.seed_session
        extreme_price = command.seed_split_close
        previous_close = command.seed_split_close
        candidate: _Candidate | None = None
        steps: list[ReversalObservationDailyStep] = []
        events: list[ReversalObservationEvent] = []
        candidate_count = cancellation_count = confirmation_count = activation_count = 0

        def new_event(
            session: date,
            event_type: ReversalEventType,
            old_direction: ReversalDirection,
            new_direction: ReversalDirection | None,
            origin_session: date,
            origin_price: ReversalPriceEvidence,
            *,
            day1: UUID | None = None,
            day2: UUID | None = None,
            activation_session: date | None = None,
            trigger_values: tuple[tuple[str, str], ...] = (),
            reason: str,
        ) -> ReversalObservationEvent:
            ordinal = len(events) + 1
            event = ReversalObservationEvent(
                uuid5(_RESULT_NAMESPACE, f"{fingerprint}:event:{ordinal}"), result_id,
                ordinal, session, event_type, old_direction, new_direction,
                origin_session, origin_price, threshold, profile.result_id,
                definition.definition_id, day1, day2, activation_session,
                trigger_values, reason,
            )
            events.append(event)
            return event

        for ordinal, observation in enumerate(market.observations, 1):
            session = observation.session
            close = observation.split_close
            direction_at_open = direction
            step_events: list[UUID] = []

            if (
                candidate is not None
                and candidate.confirmed
                and candidate.activation_session == session
            ):
                old = candidate.old_direction
                direction = old.opposite
                direction_at_open = direction
                cycle_reference_session = candidate.origin_session
                cycle_reference_price = candidate.origin_price
                buffer_prices = [candidate.origin_price]
                for buffered in steps[candidate.day1_index:]:
                    if buffered.attribution is ReversalAttribution.COMMITTED_TO_NEW_CYCLE:
                        buffer_prices.append(buffered.observation.split_close)
                extreme_price = (
                    max(buffer_prices, key=lambda item: item.value.value)
                    if direction is ReversalDirection.UP
                    else min(buffer_prices, key=lambda item: item.value.value)
                )
                extreme_session = next(
                    item.session for item in [market.seed_observation, *market.observations]
                    if item.split_close.value.ieee_hex == extreme_price.value.ieee_hex
                )
                event = new_event(
                    session, ReversalEventType.CYCLE_ACTIVATED, old, direction,
                    candidate.origin_session, candidate.origin_price,
                    day1=candidate.day1_step_id,
                    activation_session=session,
                    trigger_values=(("effective_at", "session_start"),),
                    reason="Confirmed reversal became operational at the next expected session start.",
                )
                step_events.append(event.event_id)
                activation_count += 1
                candidate = None

            extreme_before = extreme_price
            candidate_origin_session = candidate.origin_session if candidate else None
            candidate_origin_price = candidate.origin_price if candidate else None
            attribution = ReversalAttribution.NONE
            state_after = ReversalCandidateState.NONE

            if candidate is not None:
                distance_value = self._distance(
                    candidate.old_direction, candidate.origin_price.value.value, close.value.value
                )
                reached = distance_value >= threshold_value
                movement = self._new_cycle_movement(
                    candidate.old_direction, candidate.origin_price.value.value, close.value.value
                )
                step_id = uuid5(_RESULT_NAMESPACE, f"{fingerprint}:step:{ordinal}")
                if reached:
                    attribution = ReversalAttribution.COMMITTED_TO_NEW_CYCLE
                    steps[candidate.day1_index] = replace(
                        steps[candidate.day1_index],
                        attribution=ReversalAttribution.COMMITTED_TO_NEW_CYCLE,
                    )
                    next_session = (
                        market.expected_sessions[ordinal]
                        if ordinal < len(market.expected_sessions)
                        else None
                    )
                    candidate.activation_session = next_session
                    candidate.confirmed = True
                    state_after = ReversalCandidateState.CONFIRMED_AWAITING_ACTIVATION
                    event = new_event(
                        session, ReversalEventType.REVERSAL_CONFIRMED,
                        candidate.old_direction, candidate.old_direction.opposite,
                        candidate.origin_session, candidate.origin_price,
                        day1=candidate.day1_step_id, day2=step_id,
                        activation_session=next_session,
                        trigger_values=(
                            ("distance_hex", float(distance_value).hex()),
                            ("threshold_hex", threshold.ieee_hex),
                        ),
                        reason="The second consecutive expected-session close remained at or beyond the frozen threshold.",
                    )
                    step_events.append(event.event_id)
                    confirmation_count += 1
                else:
                    attribution = ReversalAttribution.DISCARDED_FOR_NEW_CYCLE
                    steps[candidate.day1_index] = replace(
                        steps[candidate.day1_index],
                        attribution=ReversalAttribution.DISCARDED_FOR_NEW_CYCLE,
                    )
                    event = new_event(
                        session, ReversalEventType.CANDIDATE_CANCELLED,
                        candidate.old_direction, None, candidate.origin_session,
                        candidate.origin_price, day1=candidate.day1_step_id, day2=step_id,
                        trigger_values=(
                            ("distance_hex", float(distance_value).hex()),
                            ("threshold_hex", threshold.ieee_hex),
                        ),
                        reason="The next expected-session close moved back inside the frozen threshold.",
                    )
                    step_events.append(event.event_id)
                    cancellation_count += 1
                    if self._extends(direction, close.value.value, extreme_price.value.value):
                        extreme_price, extreme_session = close, session
                    candidate = None
            else:
                if self._extends(direction, close.value.value, extreme_price.value.value):
                    extreme_price, extreme_session = close, session
                distance_value = self._distance(direction, extreme_price.value.value, close.value.value)
                reached = distance_value >= threshold_value
                movement = 0.0
                step_id = uuid5(_RESULT_NAMESPACE, f"{fingerprint}:step:{ordinal}")
                if reached:
                    candidate = _Candidate(direction, extreme_session, extreme_price, len(steps), step_id)
                    candidate_origin_session = extreme_session
                    candidate_origin_price = extreme_price
                    attribution = ReversalAttribution.PROVISIONAL_NEW_CYCLE
                    movement = self._new_cycle_movement(
                        direction, extreme_price.value.value, close.value.value
                    )
                    state_after = ReversalCandidateState.DAY_1_PENDING
                    event = new_event(
                        session, ReversalEventType.CANDIDATE_STARTED, direction,
                        direction.opposite, extreme_session, extreme_price, day1=step_id,
                        trigger_values=(
                            ("distance_hex", float(distance_value).hex()),
                            ("threshold_hex", threshold.ieee_hex),
                        ),
                        reason="The completed-session close reached the inclusive symmetric reversal threshold.",
                    )
                    step_events.append(event.event_id)
                    candidate_count += 1

            if candidate is not None and candidate.confirmed:
                state_after = ReversalCandidateState.CONFIRMED_AWAITING_ACTIVATION
            display_fraction = (
                -math.expm1(-max(distance_value, 0.0))
                if direction_at_open is ReversalDirection.UP
                else math.expm1(max(distance_value, 0.0))
            )
            prior_return = math.log(close.value.value / previous_close.value.value)
            steps.append(ReversalObservationDailyStep(
                step_id, result_id, ordinal, session, observation,
                direction_at_open, direction, cycle_reference_session,
                cycle_reference_price, extreme_before, extreme_price,
                candidate_origin_session, candidate_origin_price,
                profile.profile_log_scale, definition.shared_multiplier, threshold,
                ReversalFloatEvidence(distance_value), ReversalFloatEvidence(display_fraction),
                reached, state_after, ReversalFloatEvidence(prior_return), attribution,
                ReversalFloatEvidence(movement), tuple(step_events), (),
                (
                    "T = shared_multiplier * P27_profile_log_scale",
                    "UP distance = ln(running_high / close)",
                    "DOWN distance = ln(close / running_low)",
                    "comparison = distance >= frozen_threshold",
                ),
            ))
            previous_close = close

        final_candidate = (
            ReversalCandidateState.NONE
            if candidate is None
            else ReversalCandidateState.CONFIRMED_AWAITING_ACTIVATION
            if candidate.confirmed
            else ReversalCandidateState.DAY_1_PENDING
        )
        status = (
            ReversalObservationResultStatus.VALID_WITH_ACTIVATED_CYCLE
            if activation_count
            else ReversalObservationResultStatus.CONFIRMED_AWAITING_ACTIVATION
            if final_candidate is ReversalCandidateState.CONFIRMED_AWAITING_ACTIVATION
            else ReversalObservationResultStatus.VALID_WITH_PENDING_CANDIDATE
            if final_candidate is ReversalCandidateState.DAY_1_PENDING
            else ReversalObservationResultStatus.VALID_NO_REVERSAL
        )
        source_links = self._source_links(definition, profile, market)
        return ReversalObservationResult(
            result_id, fingerprint, definition.definition_id, definition.definition_version,
            profile, market.evidence_id, market.content_fingerprint, command.symbol,
            command.seed_session, command.final_evaluation_session, len(steps),
            command.initial_direction, status, direction, cycle_reference_session,
            cycle_reference_price, extreme_price, final_candidate, candidate_count,
            cancellation_count, confirmation_count, activation_count, tuple(steps),
            tuple(events), source_links,
            (
                "One shared multiplier is used for both reversal directions.",
                "Two consecutive expected completed XNYS sessions confirm a reversal.",
                "Confirmed day-1/day-2 observations are committed from the prior reversal extreme.",
                "Activation occurs at the next expected session start; no missing day is invented.",
            ),
            market.warnings,
            (
                f"{command.symbol}: {candidate_count} candidate(s), {confirmation_count} confirmed, "
                f"{activation_count} activated; final research direction={direction.value}."
            ),
            created_at_utc, software_version, source_revision, worktree_state,
        )

    @staticmethod
    def _validate_sources(definition, command, profile, market) -> None:
        if definition.status.value != "disabled":
            raise ReversalObservationValidationError(
                ReversalObservationResultStatus.SOURCE_VERSION_INCOMPATIBLE,
                "archived reversal definitions cannot be evaluated",
            )
        if (command.definition_id, command.definition_version) != (
            definition.definition_id, definition.definition_version
        ):
            raise ReversalObservationValidationError(
                ReversalObservationResultStatus.SOURCE_VERSION_INCOMPATIBLE,
                "requested definition identity does not match",
            )
        if command.profile_result_id != profile.result_id or command.symbol != profile.symbol:
            raise ReversalObservationValidationError(
                ReversalObservationResultStatus.SOURCE_EVIDENCE_MISMATCH,
                "P27 result identity or symbol does not match",
            )
        if (
            profile.component_id != _P27_COMPONENT_ID
            or profile.component_version != _P27_COMPONENT_VERSION
        ):
            raise ReversalObservationValidationError(
                ReversalObservationResultStatus.SOURCE_VERSION_INCOMPATIBLE,
                "P27 component version must be exactly 1.0.0",
            )
        if command.symbol != market.symbol:
            raise ReversalObservationValidationError(
                ReversalObservationResultStatus.SOURCE_EVIDENCE_MISMATCH,
                "market evidence symbol does not match",
            )
        if command.seed_session != market.seed_observation.session:
            raise ReversalObservationValidationError(
                ReversalObservationResultStatus.SOURCE_EVIDENCE_MISMATCH,
                "explicit seed session does not match market evidence",
            )
        if command.seed_observation_id != market.seed_observation.observation_id:
            raise ReversalObservationValidationError(
                ReversalObservationResultStatus.SOURCE_EVIDENCE_MISMATCH,
                "explicit seed observation identity does not match",
            )
        if command.seed_split_close != market.seed_observation.split_close:
            raise ReversalObservationValidationError(
                ReversalObservationResultStatus.SOURCE_EVIDENCE_MISMATCH,
                "explicit seed close does not match",
            )
        if command.final_evaluation_session != (
            market.expected_sessions[-1] if market.expected_sessions else command.seed_session
        ):
            raise ReversalObservationValidationError(
                ReversalObservationResultStatus.MISSING_EXPECTED_SESSION,
                "final evaluation session is absent from the exact evidence grid",
            )
        calendar_identity = (
            command.calendar_definition_id, command.calendar_version, command.calendar_fingerprint
        )
        if calendar_identity != (
            market.calendar_definition_id, market.calendar_version, market.calendar_fingerprint
        ):
            raise ReversalObservationValidationError(
                ReversalObservationResultStatus.SOURCE_EVIDENCE_MISMATCH,
                "calendar identity does not match",
            )
        if command.seed_session < profile.source_evaluation_end_session:
            raise ReversalObservationValidationError(
                ReversalObservationResultStatus.SOURCE_EVIDENCE_MISMATCH,
                "seed cannot precede the P27 source study end",
            )
        if market.seed_observation.available_at_utc > profile.created_at_utc:
            raise ReversalObservationValidationError(
                ReversalObservationResultStatus.SOURCE_EVIDENCE_MISMATCH,
                "seed close was not available when the P27 result was created",
            )
        if any(
            item.session <= command.seed_session
            or item.session <= profile.source_evaluation_end_session
            or item.official_close_utc <= profile.created_at_utc
            for item in market.observations
        ):
            raise ReversalObservationValidationError(
                ReversalObservationResultStatus.SOURCE_EVIDENCE_MISMATCH,
                "evaluated sessions violate the forward-frozen source-time boundary",
            )

    @staticmethod
    def _extends(direction: ReversalDirection, price: float, extreme: float) -> bool:
        return price > extreme if direction is ReversalDirection.UP else price < extreme

    @staticmethod
    def _distance(direction: ReversalDirection, origin: float, close: float) -> float:
        value = math.log(origin / close) if direction is ReversalDirection.UP else math.log(close / origin)
        if not math.isfinite(value):
            raise ReversalObservationValidationError(
                ReversalObservationResultStatus.NONFINITE_CALCULATION,
                "directional log distance is non-finite",
            )
        return max(value, 0.0)

    @staticmethod
    def _new_cycle_movement(old_direction: ReversalDirection, origin: float, close: float) -> float:
        value = math.log(origin / close) if old_direction is ReversalDirection.UP else math.log(close / origin)
        return max(value, 0.0)

    @staticmethod
    def _fingerprint(definition, command, profile, market) -> str:
        payload = {
            "component": REVERSAL_OBSERVATION_COMPONENT_VERSION,
            "definition": [str(definition.definition_id), definition.definition_version,
                           definition.shared_multiplier.ieee_hex],
            "profile": [str(profile.result_id), profile.calculation_fingerprint,
                        profile.profile_log_scale.ieee_hex],
            "market": [str(market.evidence_id), market.content_fingerprint],
            "symbol": command.symbol,
            "direction": command.initial_direction.value,
            "seed": [command.seed_session.isoformat(), command.seed_observation_id,
                     command.seed_split_close.value.ieee_hex],
            "end": command.final_evaluation_session.isoformat(),
            "calendar": [command.calendar_definition_id, command.calendar_version,
                         command.calendar_fingerprint],
            "observations": [
                [item.session.isoformat(), item.observation_id,
                 item.raw_close.value.ieee_hex, item.split_close.value.ieee_hex]
                for item in market.observations
            ],
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    @staticmethod
    def _source_links(definition, profile, market) -> tuple[ReversalObservationSourceLink, ...]:
        seed = market.seed_observation
        seed_payload = json.dumps({
            "official_close_utc": seed.official_close_utc.isoformat(),
            "first_observed_at_utc": seed.first_observed_at_utc.isoformat(),
            "available_at_utc": seed.available_at_utc.isoformat(),
            "raw_source_id": seed.raw_source_id,
            "split_source_id": seed.split_source_id,
            "raw_close_text": seed.raw_close.decimal_text,
            "raw_close_hex": seed.raw_close.value.ieee_hex,
            "split_close_text": seed.split_close.decimal_text,
            "split_close_hex": seed.split_close.value.ieee_hex,
        }, sort_keys=True, separators=(",", ":"))
        return (
            ReversalObservationSourceLink(1, "p28_definition", str(definition.definition_id), str(definition.definition_version), None),
            ReversalObservationSourceLink(2, "p27_result", str(profile.result_id), profile.component_version, profile.calculation_fingerprint),
            ReversalObservationSourceLink(3, "p27_run", str(profile.result_run_id), None, None),
            ReversalObservationSourceLink(4, "p26_study", str(profile.source_study_id), None, None),
            ReversalObservationSourceLink(5, "p26_parent_run", str(profile.source_parent_run_id), None, None),
            ReversalObservationSourceLink(6, "market_evidence", str(market.evidence_id), "1", market.content_fingerprint),
            ReversalObservationSourceLink(7, "calendar", market.calendar_definition_id, market.calendar_version, market.calendar_fingerprint),
            ReversalObservationSourceLink(8, "corporate_action_evidence", market.corporate_action_evidence, None, None),
            ReversalObservationSourceLink(9, "seed_observation", seed.observation_id, "1", seed_payload),
        )


__all__ = ["ReversalObservationEngine", "ReversalObservationValidationError"]
