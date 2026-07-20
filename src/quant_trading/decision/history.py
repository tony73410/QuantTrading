"""Typed read models for persisted Decision research history."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from quant_trading.factors.models import FactorStatus, FactorValue

from .models import (
    DecisionAction,
    DecisionConditionTrace,
    DecisionSizingInputTrace,
    DecisionStatus,
    DecisionTraceStatus,
)


def _utc(value: datetime | None, field_name: str) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must include a timezone")
    return value.astimezone(UTC)


def _text(value: str, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return normalized


@dataclass(frozen=True, slots=True)
class DecisionHistoryQuery:
    symbol: str | None = None
    start_time_utc: datetime | None = None
    end_time_utc: datetime | None = None
    policy_name: str | None = None
    policy_version: str | None = None
    status: DecisionStatus | None = None
    trace_status: DecisionTraceStatus | None = None
    limit: int = 500

    def __post_init__(self) -> None:
        if not 1 <= self.limit <= 5000:
            raise ValueError("Decision history limit must be between 1 and 5000")
        if self.symbol is not None:
            object.__setattr__(self, "symbol", _text(self.symbol, "symbol").upper())
        if self.policy_name is not None:
            object.__setattr__(self, "policy_name", _text(self.policy_name, "policy_name"))
        if self.policy_version is not None:
            object.__setattr__(self, "policy_version", _text(self.policy_version, "policy_version"))
            if self.policy_name is None:
                raise ValueError("policy_version requires policy_name")
        start = _utc(self.start_time_utc, "start_time_utc")
        end = _utc(self.end_time_utc, "end_time_utc")
        if start is not None and end is not None and start >= end:
            raise ValueError("Decision history start must be before end")
        object.__setattr__(self, "start_time_utc", start)
        object.__setattr__(self, "end_time_utc", end)


@dataclass(frozen=True, slots=True)
class DecisionFactorInputRecord:
    snapshot_id: UUID
    symbol: str
    factor_name: str
    factor_version: str
    value: FactorValue | None
    unit: str | None
    status: FactorStatus

    def __post_init__(self) -> None:
        object.__setattr__(self, "symbol", _text(self.symbol, "symbol").upper())
        object.__setattr__(self, "factor_name", _text(self.factor_name, "factor_name"))
        object.__setattr__(self, "factor_version", _text(self.factor_version, "factor_version"))
        if isinstance(self.value, float):
            raise ValueError("Decision Factor input must not use binary float")


@dataclass(frozen=True, slots=True)
class DecisionIntentHistoryRecord:
    intent_id: UUID
    symbol: str
    action: DecisionAction
    current_exposure: Decimal | None
    target_exposure: Decimal | None
    desired_change: Decimal | None
    exposure_unit: str | None
    requested_notional: Decimal | None
    notional_currency: str | None
    sizing_mode: str | None
    sizing_expression: str | None
    sizing_inputs: tuple[DecisionSizingInputTrace, ...]
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "symbol", _text(self.symbol, "symbol").upper())
        for field_name in (
            "current_exposure",
            "target_exposure",
            "desired_change",
            "requested_notional",
        ):
            value = getattr(self, field_name)
            if value is not None and (
                not isinstance(value, Decimal) or not value.is_finite()
            ):
                raise ValueError(f"{field_name} must be a finite Decimal")


@dataclass(frozen=True, slots=True)
class DecisionHistoryRecord:
    decision_id: UUID
    algorithm_run_id: UUID
    stage_id: UUID
    as_of_utc: datetime
    policy_name: str
    policy_version: str
    status: DecisionStatus
    trace_status: DecisionTraceStatus
    reason_codes: tuple[str, ...]
    created_at_utc: datetime
    factor_inputs: tuple[DecisionFactorInputRecord, ...]
    condition_traces: tuple[DecisionConditionTrace, ...]
    intents: tuple[DecisionIntentHistoryRecord, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "as_of_utc", _utc(self.as_of_utc, "as_of_utc"))
        object.__setattr__(self, "created_at_utc", _utc(self.created_at_utc, "created_at_utc"))
        object.__setattr__(self, "policy_name", _text(self.policy_name, "policy_name"))
        object.__setattr__(self, "policy_version", _text(self.policy_version, "policy_version"))
        if self.trace_status is DecisionTraceStatus.CAPTURED and not self.condition_traces:
            raise ValueError("captured Decision history requires condition traces")
        if self.trace_status is not DecisionTraceStatus.CAPTURED and self.condition_traces:
            raise ValueError("Decision history trace status conflicts with condition rows")


__all__ = [
    "DecisionFactorInputRecord",
    "DecisionHistoryQuery",
    "DecisionHistoryRecord",
    "DecisionIntentHistoryRecord",
]
