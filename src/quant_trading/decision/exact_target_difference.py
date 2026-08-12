"""Shared pure exact-difference mapping owned by the Decision layer."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .errors import DecisionContractError
from .models import DecisionAction


ZERO = Decimal("0")


@dataclass(frozen=True, slots=True)
class ExactTargetDifferenceDecision:
    """The complete policy-neutral mapping of one exact signed USD difference."""

    action: DecisionAction
    requested_notional_usd: Decimal | None
    result_reason_code: str


def map_exact_target_difference(difference: Decimal) -> ExactTargetDifferenceDecision:
    """Map an exact Decimal difference without tolerance, rounding, EXIT, or Risk."""

    if not isinstance(difference, Decimal) or not difference.is_finite():
        raise DecisionContractError("target difference must be a finite Decimal")
    if difference == ZERO:
        return ExactTargetDifferenceDecision(
            DecisionAction.HOLD,
            None,
            "TARGET_POSITION_EQUAL_CURRENT",
        )
    return ExactTargetDifferenceDecision(
        DecisionAction.INCREASE if difference > ZERO else DecisionAction.DECREASE,
        abs(difference),
        "TARGET_POSITION_DIFFERENCE",
    )


__all__ = ["ExactTargetDifferenceDecision", "map_exact_target_difference"]
