"""Pure Decimal engine for an approved finite-knot target-position curve."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from .models import (
    TargetPositionAdjustmentDirection,
    TargetPositionCalculationTrace,
    TargetPositionCurveDefinition,
    TargetPositionEvaluationMode,
    TargetPositionEvidenceBinding,
    TargetPositionResult,
    ZERO,
)


class TargetPositionEngine:
    """Evaluate one explicit immutable curve without market, account or order access."""

    def calculate(
        self,
        definition: TargetPositionCurveDefinition,
        *,
        calculation_id: UUID,
        operation_id: UUID,
        run_id: UUID,
        stage_id: UUID,
        as_of_utc: datetime,
        research_state_value: Decimal,
        research_capital_basis_usd: Decimal,
        current_position_value_usd: Decimal,
        evidence_bindings: tuple[TargetPositionEvidenceBinding, ...],
        created_at_utc: datetime,
        created_by: str,
        reason: str,
    ) -> TargetPositionResult:
        knots = definition.knots
        if research_state_value <= knots[0].state_value:
            lower = upper = knots[0]
            mode = TargetPositionEvaluationMode.LOWER_ENDPOINT
            numerator = denominator = weight = ZERO
            target_fraction = lower.target_fraction
        elif research_state_value >= knots[-1].state_value:
            lower = upper = knots[-1]
            mode = TargetPositionEvaluationMode.UPPER_ENDPOINT
            numerator = denominator = weight = ZERO
            target_fraction = lower.target_fraction
        else:
            upper_index = next(
                index for index, knot in enumerate(knots)
                if knot.state_value >= research_state_value
            )
            upper = knots[upper_index]
            if upper.state_value == research_state_value:
                lower = upper
                mode = TargetPositionEvaluationMode.EXACT_KNOT
                numerator = denominator = weight = ZERO
                target_fraction = upper.target_fraction
            else:
                lower = knots[upper_index - 1]
                mode = TargetPositionEvaluationMode.INTERPOLATED
                numerator = research_state_value - lower.state_value
                denominator = upper.state_value - lower.state_value
                weight = numerator / denominator
                target_fraction = lower.target_fraction + (
                    (upper.target_fraction - lower.target_fraction) * weight
                )
        target_value = research_capital_basis_usd * target_fraction
        adjustment = target_value - current_position_value_usd
        direction = (
            TargetPositionAdjustmentDirection.NONE if adjustment == ZERO
            else TargetPositionAdjustmentDirection.INCREASE if adjustment > ZERO
            else TargetPositionAdjustmentDirection.DECREASE
        )
        trace = TargetPositionCalculationTrace(
            mode,
            lower.ordinal,
            upper.ordinal,
            lower.state_value,
            upper.state_value,
            lower.target_fraction,
            upper.target_fraction,
            numerator,
            denominator,
            weight,
        )
        return TargetPositionResult(
            calculation_id,
            operation_id,
            run_id,
            stage_id,
            definition.definition_id,
            definition.definition_version,
            as_of_utc,
            research_state_value,
            research_capital_basis_usd,
            current_position_value_usd,
            target_fraction,
            target_value,
            adjustment,
            direction,
            trace,
            evidence_bindings,
            created_at_utc,
            created_by,
            reason,
        )


__all__ = ["TargetPositionEngine"]
