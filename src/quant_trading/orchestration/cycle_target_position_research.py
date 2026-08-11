"""Resolve one explicit P28 result/step/Run into a source-neutral P29 input."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from quant_trading.asset_state import (
    REVERSAL_OBSERVATION_COMPONENT_ID,
    REVERSAL_OBSERVATION_COMPONENT_VERSION,
    ReversalObservationOperationStatus,
    ReversalObservationQuery,
    ReversalObservationQueryService,
)
from quant_trading.target_position import (
    CycleTargetAttribution,
    CycleTargetCandidateState,
    CycleTargetDirection,
    CycleTargetFloatEvidence,
    CycleTargetOperation,
    CycleTargetPositionService,
    CycleTargetPreviewCommand,
    CycleTargetPriceEvidence,
    ReversalObservationTargetInput,
)


@dataclass(frozen=True, slots=True)
class CycleTargetPositionPreflight:
    command: CycleTargetPreviewCommand
    source: ReversalObservationTargetInput
    summary: str


class CycleTargetPositionResearchRunner(Protocol):
    def prepare(self, command: CycleTargetPreviewCommand) -> CycleTargetPositionPreflight: ...
    def preview(self, command: CycleTargetPreviewCommand) -> CycleTargetOperation: ...
    def preview_prepared(self, prepared: CycleTargetPositionPreflight) -> CycleTargetOperation: ...


class CycleTargetPositionResearchCoordinator:
    """Read public P28 history only; never select latest evidence or calculate a curve."""

    def __init__(
        self,
        reversal_queries: ReversalObservationQueryService,
        service: CycleTargetPositionService,
    ) -> None:
        self._reversal = reversal_queries
        self._service = service

    def prepare(self, command: CycleTargetPreviewCommand) -> CycleTargetPositionPreflight:
        operations = self._reversal.list_operations(ReversalObservationQuery(
            run_id=command.source_reversal_run_id,
            result_id=command.source_reversal_result_id,
            limit=2,
        ))
        operation = next(
            (
                item for item in operations
                if item.run_id == command.source_reversal_run_id
                and item.result is not None
                and item.status in {
                    ReversalObservationOperationStatus.COMPLETED,
                    ReversalObservationOperationStatus.COMPLETED_WITH_WARNINGS,
                }
            ),
            None,
        )
        if operation is None or operation.result is None:
            raise KeyError("exact successful P28 result/Run pair cannot be reloaded")
        result = operation.result
        if (
            result.schema_version != 1
            or result.execution_allowed
            or result.live_allowed
        ):
            raise ValueError("P28 result schema or safety metadata is incompatible")
        step = next(
            (item for item in result.daily_steps if item.step_id == command.source_reversal_step_id),
            None,
        )
        if step is None:
            raise KeyError("exact P28 daily step does not belong to the selected result")
        if step.result_id != result.result_id:
            raise ValueError("P28 daily-step result identity is inconsistent")
        source = ReversalObservationTargetInput(
            result.result_id,
            operation.run_id,
            operation.state_stage_id,
            step.step_id,
            step.ordinal,
            result.definition_id,
            result.definition_version,
            REVERSAL_OBSERVATION_COMPONENT_ID,
            REVERSAL_OBSERVATION_COMPONENT_VERSION,
            result.calculation_fingerprint,
            result.profile.result_id,
            result.profile.result_run_id,
            result.profile.source_parent_run_id,
            result.market_evidence_id,
            result.market_evidence_fingerprint,
            result.symbol,
            step.session,
            step.observation.official_close_utc,
            step.observation.available_at_utc,
            CycleTargetDirection(step.direction_at_open.value),
            CycleTargetDirection(step.direction_at_close.value),
            CycleTargetCandidateState(step.candidate_state_after_close.value),
            CycleTargetAttribution(step.attribution.value),
            step.event_ids,
            step.cycle_reference_session,
            self._price(step.cycle_reference_price),
            self._price(step.observation.split_close),
            CycleTargetFloatEvidence(
                repr(step.profile_log_scale.value),
                step.profile_log_scale.value,
                step.profile_log_scale.ieee_hex,
            ),
            tuple(result.warnings) + tuple(step.warnings),
        )
        summary = (
            f"{source.symbol} {source.session}: exact P28 result {source.source_result_id}, "
            f"step {source.source_step_id}, Run {source.source_run_id}; "
            f"direction={source.direction_at_open.value}; reference={source.cycle_reference_price.input_text}; "
            f"close={source.split_close.input_text}; k={source.profile_log_scale.decimal_text}; NO EXECUTION."
        )
        return CycleTargetPositionPreflight(command, source, summary)

    def preview(self, command: CycleTargetPreviewCommand) -> CycleTargetOperation:
        try:
            prepared = self.prepare(command)
        except Exception as exc:
            return self._service.record_source_failure(
                command, exc, source_not_found=isinstance(exc, KeyError)
            )
        return self.preview_prepared(prepared)

    def preview_prepared(self, prepared: CycleTargetPositionPreflight) -> CycleTargetOperation:
        return self._service.preview(prepared.command, prepared.source)

    @staticmethod
    def _price(value) -> CycleTargetPriceEvidence:
        return CycleTargetPriceEvidence(
            value.decimal_text,
            CycleTargetFloatEvidence(
                repr(value.value.value), value.value.value, value.value.ieee_hex
            ),
        )


__all__ = [
    "CycleTargetPositionPreflight",
    "CycleTargetPositionResearchCoordinator",
    "CycleTargetPositionResearchRunner",
]
