"""Pure Decimal calculator for a manual reference-relative price state."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from .standardized_state_models import (
    DIMENSIONLESS,
    STANDARDIZED_PRICE_STATE_FORMULA_ID,
    USD,
    StandardizedPriceStateDefinition,
    StandardizedPriceStateEvidenceBinding,
    StandardizedPriceStateResult,
    StandardizedPriceStateTrace,
)


class StandardizedPriceStateEngine:
    """Calculate one visible manual observation without data or trading access."""

    def calculate(
        self,
        definition: StandardizedPriceStateDefinition,
        *,
        calculation_id: UUID,
        operation_id: UUID,
        run_id: UUID,
        stage_id: UUID,
        symbol: str,
        as_of_utc: datetime,
        manual_price_usd: Decimal,
        manual_reference_price_usd: Decimal,
        manual_risk_scale_usd: Decimal,
        evidence_bindings: tuple[StandardizedPriceStateEvidenceBinding, ...],
        created_at_utc: datetime,
        created_by: str,
        reason: str,
    ) -> StandardizedPriceStateResult:
        deviation = manual_price_usd - manual_reference_price_usd
        state = deviation / manual_risk_scale_usd
        trace = StandardizedPriceStateTrace(
            STANDARDIZED_PRICE_STATE_FORMULA_ID,
            USD,
            DIMENSIONLESS,
            definition.price_source,
            definition.reference_source,
            definition.risk_scale_source,
            manual_price_usd,
            manual_reference_price_usd,
            deviation,
            manual_risk_scale_usd,
            state,
        )
        return StandardizedPriceStateResult(
            calculation_id,
            operation_id,
            run_id,
            stage_id,
            definition.definition_id,
            definition.definition_version,
            symbol,
            as_of_utc,
            manual_price_usd,
            manual_reference_price_usd,
            manual_risk_scale_usd,
            deviation,
            state,
            trace,
            evidence_bindings,
            created_at_utc,
            created_by,
            reason,
        )


__all__ = ["StandardizedPriceStateEngine"]
