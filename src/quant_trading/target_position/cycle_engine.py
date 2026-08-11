"""Pure binary64/Decimal evaluator for the approved P23-3A formula family."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
import hashlib
import json
import math
from uuid import UUID

from .cycle_models import (
    CYCLE_TARGET_SOLVER_ID,
    CYCLE_TARGET_SOLVER_MAX_ITERATIONS,
    CYCLE_TARGET_SOLVER_TOLERANCE,
    AssetCycleTargetConfiguration,
    CycleTargetAttribution,
    CycleTargetCalculationTrace,
    CycleTargetCandidateState,
    CycleTargetDirection,
    CycleTargetFloatEvidence,
    CycleTargetFormulaDefinition,
    CycleTargetPositionResult,
    CycleTargetRegion,
    CycleTargetResultStatus,
    CycleTargetSourceLink,
    ReversalObservationTargetInput,
)
from .errors import TargetPositionValidationError
from .models import TargetPositionAdjustmentDirection


class CycleTargetPositionEngine:
    """Map one exact P28 step to one bounded hypothetical target."""

    def calculate(
        self,
        formula: CycleTargetFormulaDefinition,
        configuration: AssetCycleTargetConfiguration,
        source: ReversalObservationTargetInput,
        *,
        result_id: UUID,
        operation_id: UUID,
        run_id: UUID,
        state_stage_id: UUID,
        target_stage_id: UUID,
        research_capital_basis_usd: Decimal,
        current_position_value_usd: Decimal,
        created_at_utc: datetime,
        created_by: str,
        reason: str,
        software_version: str,
        source_revision: str | None,
        worktree_state: str,
    ) -> CycleTargetPositionResult:
        self._validate_compatibility(formula, configuration, source)
        if research_capital_basis_usd < 0 or current_position_value_usd < 0:
            raise TargetPositionValidationError("hypothetical USD inputs must be non-negative")
        if not research_capital_basis_usd.is_finite() or not current_position_value_usd.is_finite():
            raise TargetPositionValidationError("hypothetical USD inputs must be finite")

        price = source.split_close.value.value
        reference = source.cycle_reference_price.value.value
        scale = source.profile_log_scale.value
        log_ratio = math.log(price / reference)
        normalized = log_ratio / scale
        absolute = abs(normalized)
        if not all(math.isfinite(value) for value in (log_ratio, normalized, absolute)):
            raise TargetPositionValidationError("normalized price state is non-finite")

        minimum = configuration.minimum_fraction.value
        neutral = configuration.neutral_fraction.value
        maximum = configuration.maximum_fraction.value
        slope = configuration.linear_slope_per_scale.value
        start = configuration.acceleration_start_scales.value
        saturation = configuration.saturation_scales.value
        linear_raw = neutral - slope * normalized
        linear_bounded = min(max(linear_raw, minimum), maximum)
        direction_matches = (
            source.direction_at_open is CycleTargetDirection.UP and normalized > 0
        ) or (
            source.direction_at_open is CycleTargetDirection.DOWN and normalized < 0
        )
        confirmation_forces_linear = source.forces_linear
        counter_forces_linear = not direction_matches
        within_linear_boundary = absolute <= start
        at_or_beyond_saturation = absolute >= saturation

        boundary = headroom = rho = beta = q = exponential = None
        solver_iterations = None
        if confirmation_forces_linear or counter_forces_linear or within_linear_boundary:
            final = linear_bounded
            pre_bound = linear_raw
            region = (
                CycleTargetRegion.LINEAR_CLAMPED
                if linear_raw < minimum or linear_raw > maximum
                else CycleTargetRegion.LINEAR
            )
        elif at_or_beyond_saturation:
            final = minimum if source.direction_at_open is CycleTargetDirection.UP else maximum
            pre_bound = final
            region = CycleTargetRegion.SATURATED
        else:
            if source.direction_at_open is CycleTargetDirection.UP:
                boundary = neutral - slope * start
                headroom = boundary - minimum
            else:
                boundary = neutral + slope * start
                headroom = maximum - boundary
            rho = slope * (saturation - start) / headroom
            beta, solver_iterations = self._solve_beta(rho)
            q = (absolute - start) / (saturation - start)
            exponential = math.expm1(beta * q) / math.expm1(beta)
            if source.direction_at_open is CycleTargetDirection.UP:
                pre_bound = boundary - headroom * exponential
            else:
                pre_bound = boundary + headroom * exponential
            final = min(max(pre_bound, minimum), maximum)
            region = CycleTargetRegion.ACCELERATING

        if not all(math.isfinite(value) for value in (linear_raw, linear_bounded, pre_bound, final)):
            raise TargetPositionValidationError("target-position calculation is non-finite")
        final_decimal = Decimal.from_float(final)
        target_value = research_capital_basis_usd * final_decimal
        adjustment = target_value - current_position_value_usd
        adjustment_direction = (
            TargetPositionAdjustmentDirection.NONE if adjustment == 0
            else TargetPositionAdjustmentDirection.INCREASE if adjustment > 0
            else TargetPositionAdjustmentDirection.DECREASE
        )
        trace = CycleTargetCalculationTrace(
            CycleTargetFloatEvidence.calculated(log_ratio),
            CycleTargetFloatEvidence.calculated(normalized),
            CycleTargetFloatEvidence.calculated(absolute),
            direction_matches,
            confirmation_forces_linear,
            counter_forces_linear,
            within_linear_boundary,
            at_or_beyond_saturation,
            CycleTargetFloatEvidence.calculated(linear_raw),
            CycleTargetFloatEvidence.calculated(linear_bounded),
            self._optional(boundary),
            self._optional(headroom),
            self._optional(rho),
            self._optional(beta),
            solver_iterations,
            self._optional(q),
            self._optional(exponential),
            CycleTargetFloatEvidence.calculated(pre_bound),
            CycleTargetFloatEvidence.calculated(final),
            str(final_decimal),
            CYCLE_TARGET_SOLVER_ID,
            CycleTargetFloatEvidence.calculated(CYCLE_TARGET_SOLVER_TOLERANCE),
            CYCLE_TARGET_SOLVER_MAX_ITERATIONS,
            (
                "source: exact completed P28 daily step selected explicitly",
                "state: x=ln(P/R)/k",
                f"confirmation_forces_linear={confirmation_forces_linear}",
                f"direction_matches={direction_matches}",
                f"abs(x)<=A={within_linear_boundary}",
                f"abs(x)>=B={at_or_beyond_saturation}",
                f"region={region.value}",
                "target direction: lower price -> higher desired target",
                "USD arithmetic: exact Decimal.from_float fraction; no rounding",
            ),
        )
        status = {
            CycleTargetRegion.LINEAR: CycleTargetResultStatus.VALID_LINEAR,
            CycleTargetRegion.LINEAR_CLAMPED: CycleTargetResultStatus.VALID_LINEAR_CLAMPED,
            CycleTargetRegion.ACCELERATING: CycleTargetResultStatus.VALID_ACCELERATING,
            CycleTargetRegion.SATURATED: CycleTargetResultStatus.VALID_SATURATED,
        }[region]
        source_links = self._source_links(source)
        fingerprint = self._fingerprint(
            formula, configuration, source, research_capital_basis_usd,
            current_position_value_usd, trace, region, target_value, adjustment,
        )
        explanation = (
            f"{source.symbol} {source.session}: x={trace.normalized_state.decimal_text}; "
            f"{region.value}; target fraction={final_decimal}; target={target_value} USD; "
            f"current={current_position_value_usd} USD; difference={adjustment} USD. "
            "Research only; no Decision, Risk approval, cash reservation or order was created."
        )
        return CycleTargetPositionResult(
            result_id,
            fingerprint,
            operation_id,
            run_id,
            state_stage_id,
            target_stage_id,
            formula.formula_definition_id,
            formula.definition_version,
            configuration.configuration_id,
            configuration.configuration_version,
            source,
            region,
            status,
            final_decimal,
            research_capital_basis_usd,
            current_position_value_usd,
            target_value,
            adjustment,
            adjustment_direction,
            trace,
            source_links,
            source.warnings,
            explanation,
            created_at_utc,
            created_by,
            reason,
            software_version,
            source_revision,
            worktree_state,
        )

    @staticmethod
    def _validate_compatibility(formula, configuration, source) -> None:
        if configuration.formula_definition_id != formula.formula_definition_id:
            raise TargetPositionValidationError("configuration references another formula definition")
        if configuration.formula_definition_version != formula.definition_version:
            raise TargetPositionValidationError("configuration formula version does not match")
        if configuration.symbol != source.symbol:
            raise TargetPositionValidationError("configuration symbol does not match P28 source")
        if formula.status.value != "disabled" or configuration.status.value != "disabled":
            raise TargetPositionValidationError("only explicit current disabled research versions may run")

    @staticmethod
    def _optional(value: float | None) -> CycleTargetFloatEvidence | None:
        return None if value is None else CycleTargetFloatEvidence.calculated(value)

    @staticmethod
    def _solve_beta(rho: float) -> tuple[float, int]:
        if not 0 < rho < 1:
            raise TargetPositionValidationError("derived rho must be within (0, 1)")

        def residual(beta: float) -> float:
            return beta / math.expm1(beta) - rho

        low = 0.0
        high = 1.0
        while residual(high) > 0:
            high *= 2.0
            if not math.isfinite(high) or high > 1024:
                raise TargetPositionValidationError("beta root could not be bracketed")
        for iteration in range(1, CYCLE_TARGET_SOLVER_MAX_ITERATIONS + 1):
            midpoint = (low + high) / 2.0
            value = residual(midpoint)
            if abs(value) <= CYCLE_TARGET_SOLVER_TOLERANCE or (
                high - low <= CYCLE_TARGET_SOLVER_TOLERANCE * max(1.0, midpoint)
            ):
                if midpoint <= 0 or not math.isfinite(midpoint):
                    break
                return midpoint, iteration
            if value > 0:
                low = midpoint
            else:
                high = midpoint
        raise TargetPositionValidationError("beta root solver did not converge")

    @staticmethod
    def _source_links(source: ReversalObservationTargetInput) -> tuple[CycleTargetSourceLink, ...]:
        return (
            CycleTargetSourceLink(1, "p28_result", str(source.source_result_id), "1", source.source_calculation_fingerprint, source.source_run_id),
            CycleTargetSourceLink(2, "p28_daily_step", str(source.source_step_id), "1", None, source.source_run_id),
            CycleTargetSourceLink(3, "p28_definition", str(source.source_definition_id), str(source.source_definition_version), None, source.source_run_id),
            CycleTargetSourceLink(4, "p27_profile", str(source.source_profile_result_id), "1.0.0", None, source.source_profile_run_id),
            CycleTargetSourceLink(5, "p26_parent", str(source.source_parent_run_id), None, None, source.source_parent_run_id),
            CycleTargetSourceLink(6, "market_evidence", str(source.source_market_evidence_id), "1", source.source_market_fingerprint, None),
        )

    @staticmethod
    def _fingerprint(
        formula,
        configuration,
        source,
        basis,
        current,
        trace,
        region,
        target_value,
        adjustment,
    ) -> str:
        payload = {
            "formula": [str(formula.formula_definition_id), formula.definition_version, formula.component_id, formula.component_version],
            "configuration": [str(configuration.configuration_id), configuration.configuration_version, configuration.constraint_fingerprint],
            "source": [
                str(source.source_result_id), str(source.source_step_id), str(source.source_run_id),
                source.source_calculation_fingerprint, source.split_close.value.ieee_hex,
                source.cycle_reference_price.value.ieee_hex, source.profile_log_scale.ieee_hex,
                source.direction_at_open.value, source.candidate_state_after_close.value,
            ],
            "usd": [str(basis), str(current), str(target_value), str(adjustment)],
            "region": region.value,
            "trace": {
                "x": trace.normalized_state.ieee_hex,
                "linear": trace.linear_raw_fraction.ieee_hex,
                "boundary": trace.boundary_fraction.ieee_hex if trace.boundary_fraction else None,
                "headroom": trace.headroom.ieee_hex if trace.headroom else None,
                "rho": trace.rho.ieee_hex if trace.rho else None,
                "beta": trace.beta.ieee_hex if trace.beta else None,
                "q": trace.normalized_acceleration_progress.ieee_hex if trace.normalized_acceleration_progress else None,
                "E": trace.exponential_progress.ieee_hex if trace.exponential_progress else None,
                "target": trace.final_target_fraction.ieee_hex,
                "target_decimal": trace.exact_decimal_fraction_text,
            },
        }
        return hashlib.sha256(json.dumps(
            payload, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")).hexdigest()


__all__ = ["CycleTargetPositionEngine"]
