"""Traceable decision contracts that cannot represent executed orders."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from typing import TypeAlias
from uuid import UUID

from quant_trading.factors.models import FactorSnapshotCollection, FactorStatus

from .errors import DecisionContractError


DecisionParameterValue: TypeAlias = Decimal | int | bool | str | None


def _utc(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise DecisionContractError(f"{field_name} must include a timezone")
    return value.astimezone(UTC)


def _required_text(value: str, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise DecisionContractError(f"{field_name} must not be empty")
    return normalized


class PortfolioContextStatus(StrEnum):
    UNAVAILABLE = "unavailable"
    AVAILABLE_REFERENCE = "available_reference"


class DecisionAction(StrEnum):
    INCREASE = "increase"
    DECREASE = "decrease"
    HOLD = "hold"
    EXIT = "exit"
    NO_DECISION = "no_decision"


class DecisionStatus(StrEnum):
    VALID = "valid"
    NO_DECISION = "no_decision"
    INVALID_FACTORS = "invalid_factors"
    STALE_FACTORS = "stale_factors"
    POLICY_ERROR = "policy_error"


class DecisionTraceStatus(StrEnum):
    CAPTURED = "captured"
    NOT_EVALUATED = "not_evaluated"
    TRACE_NOT_CAPTURED = "trace_not_captured"


class DecisionSizingInputSource(StrEnum):
    ASSET = "asset"
    MARKET = "market"
    ACCOUNT = "account"
    POSITION = "position"


@dataclass(frozen=True, slots=True, order=True)
class DecisionParameter:
    name: str
    value: DecisionParameterValue

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _required_text(self.name, "parameter name"))
        if self.value is not None and not isinstance(
            self.value, (Decimal, int, bool, str)
        ):
            raise DecisionContractError("decision parameter has an unsupported value type")
        if isinstance(self.value, Decimal) and not self.value.is_finite():
            raise DecisionContractError("decision parameter must be finite")


@dataclass(frozen=True, slots=True)
class DecisionContext:
    as_of_utc: datetime
    parameters: tuple[DecisionParameter, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "as_of_utc", _utc(self.as_of_utc, "as_of_utc"))
        names = [parameter.name for parameter in self.parameters]
        if len(names) != len(set(names)):
            raise DecisionContractError("decision parameter names must be unique")

@dataclass(frozen=True,slots=True,order=True)
class SizingReference:
    name: str
    value: Decimal
    def __post_init__(self):
        if not self.name.strip() or not isinstance(self.value,Decimal) or not self.value.is_finite(): raise DecisionContractError("sizing reference requires a name and finite Decimal")

@dataclass(frozen=True,slots=True)
class SizingContext:
    as_of_utc: datetime
    asset_factors: tuple[SizingReference,...]=()
    market_factors: tuple[SizingReference,...]=()
    account_fields: tuple[SizingReference,...]=()
    position_fields: tuple[SizingReference,...]=()
    def __post_init__(self):
        object.__setattr__(self,"as_of_utc",_utc(self.as_of_utc,"sizing as_of_utc"))
        names=[f"asset.{x.name}" for x in self.asset_factors]+[f"market.{x.name}" for x in self.market_factors]+[f"account.{x.name}" for x in self.account_fields]+[f"position.{x.name}" for x in self.position_fields]
        if len(names)!=len(set(names)): raise DecisionContractError("sizing context references must be unique")


@dataclass(frozen=True, slots=True, order=True)
class DecisionSizingInputTrace:
    name: str
    source: DecisionSizingInputSource
    value: Decimal

    def __post_init__(self) -> None:
        name = _required_text(self.name, "sizing input name")
        if not isinstance(self.source, DecisionSizingInputSource):
            raise DecisionContractError("sizing input source is invalid")
        if not isinstance(self.value, Decimal) or not self.value.is_finite():
            raise DecisionContractError("sizing input value must be a finite Decimal")
        if not name.startswith(f"{self.source.value}."):
            raise DecisionContractError("sizing input name must match its source")
        object.__setattr__(self, "name", name)


@dataclass(frozen=True, slots=True)
class DecisionConditionTrace:
    evaluation_order: int
    factor_component_id: str
    factor_name: str
    factor_version: str
    factor_snapshot_id: UUID
    input_value: Decimal
    input_unit: str | None
    factor_status: FactorStatus
    operator: str
    threshold: Decimal
    matched: bool

    def __post_init__(self) -> None:
        if self.evaluation_order < 0:
            raise DecisionContractError("condition evaluation order cannot be negative")
        for field_name in ("factor_component_id", "factor_name", "factor_version"):
            object.__setattr__(self, field_name, _required_text(getattr(self, field_name), field_name))
        if not isinstance(self.input_value, Decimal) or not self.input_value.is_finite():
            raise DecisionContractError("condition input must be a finite Decimal")
        if not isinstance(self.threshold, Decimal) or not self.threshold.is_finite():
            raise DecisionContractError("condition threshold must be a finite Decimal")
        if not isinstance(self.factor_status, FactorStatus):
            raise DecisionContractError("condition factor_status is invalid")
        if self.operator not in {"<", "<=", "==", ">=", ">"}:
            raise DecisionContractError("condition operator is invalid")
        if self.input_unit is not None:
            object.__setattr__(self, "input_unit", _required_text(self.input_unit, "input_unit"))


@dataclass(frozen=True, slots=True)
class PortfolioSnapshot:
    """Neutral trace envelope; holdings/exposure semantics are not implemented."""

    snapshot_id: UUID
    as_of_utc: datetime
    status: PortfolioContextStatus = PortfolioContextStatus.UNAVAILABLE
    source_reference: str | None = None

    def __post_init__(self) -> None:
        as_of = _utc(self.as_of_utc, "portfolio as_of_utc")
        if not isinstance(self.status, PortfolioContextStatus):
            raise DecisionContractError(
                "portfolio status must use the PortfolioContextStatus enum"
            )
        if self.status is PortfolioContextStatus.AVAILABLE_REFERENCE:
            if self.source_reference is None or not self.source_reference.strip():
                raise DecisionContractError(
                    "available portfolio context requires a source reference"
                )
        object.__setattr__(self, "as_of_utc", as_of)


@dataclass(frozen=True, slots=True)
class TradeIntent:
    """A proposed direction only; this is not an order or execution result."""

    intent_id: UUID
    decision_id: UUID
    symbol: str
    as_of_utc: datetime
    action: DecisionAction
    current_exposure: Decimal | None
    target_exposure: Decimal | None
    desired_change: Decimal | None
    exposure_unit: str | None
    confidence: Decimal | None
    reason_codes: tuple[str, ...]
    factor_snapshot_id: UUID
    policy_name: str
    policy_version: str
    created_at_utc: datetime
    requested_notional: Decimal | None = None
    notional_currency: str | None = None
    sizing_mode: str | None = None
    sizing_expression: str | None = None
    sizing_references: tuple[str,...] = ()
    sizing_inputs: tuple[DecisionSizingInputTrace, ...] = ()

    def __post_init__(self) -> None:
        symbol = self.symbol.strip().upper()
        if not symbol:
            raise DecisionContractError("intent symbol must not be empty")
        as_of = _utc(self.as_of_utc, "intent as_of_utc")
        created = _utc(self.created_at_utc, "intent created_at_utc")
        policy_name = _required_text(self.policy_name, "policy_name")
        policy_version = _required_text(self.policy_version, "policy_version")
        if not isinstance(self.action, DecisionAction):
            raise DecisionContractError("action must use the DecisionAction enum")
        exposures = (
            self.current_exposure,
            self.target_exposure,
            self.desired_change,
        )
        if any(value is not None and not isinstance(value, Decimal) for value in exposures):
            raise DecisionContractError("exposure values must use Decimal")
        if any(value is not None and not value.is_finite() for value in exposures):
            raise DecisionContractError("exposure values must be finite")
        if any(value is not None for value in exposures):
            if self.exposure_unit is None or not self.exposure_unit.strip():
                raise DecisionContractError("exposure values require an explicit unit")
        if self.confidence is not None:
            if not isinstance(self.confidence, Decimal):
                raise DecisionContractError("confidence must use Decimal")
            if not self.confidence.is_finite():
                raise DecisionContractError("confidence must be finite")
            if not Decimal("0") <= self.confidence <= Decimal("1"):
                raise DecisionContractError("confidence must be between 0 and 1")
        if self.requested_notional is not None:
            if not isinstance(self.requested_notional,Decimal) or not self.requested_notional.is_finite() or self.requested_notional<=0: raise DecisionContractError("requested_notional must be a positive finite Decimal")
            if self.notional_currency is None or not self.notional_currency.strip(): raise DecisionContractError("requested_notional requires currency")
        if not self.reason_codes:
            raise DecisionContractError("trade intent requires at least one reason code")
        input_names = tuple(item.name for item in self.sizing_inputs)
        if len(input_names) != len(set(input_names)):
            raise DecisionContractError("sizing input traces must be unique")
        if self.sizing_inputs and input_names != self.sizing_references:
            raise DecisionContractError("sizing references and input traces must align")
        object.__setattr__(self, "symbol", symbol)
        object.__setattr__(self, "as_of_utc", as_of)
        object.__setattr__(self, "created_at_utc", created)
        object.__setattr__(self, "policy_name", policy_name)
        object.__setattr__(self, "policy_version", policy_version)


@dataclass(frozen=True, slots=True)
class DecisionResult:
    decision_id: UUID
    as_of_utc: datetime
    policy_name: str
    policy_version: str
    policy_parameters: tuple[DecisionParameter, ...]
    factor_snapshot_ids: tuple[UUID, ...]
    status: DecisionStatus
    intents: tuple[TradeIntent, ...]
    reason_codes: tuple[str, ...]
    created_at_utc: datetime
    condition_traces: tuple[DecisionConditionTrace, ...] = ()
    trace_status: DecisionTraceStatus = DecisionTraceStatus.TRACE_NOT_CAPTURED

    def __post_init__(self) -> None:
        as_of = _utc(self.as_of_utc, "decision as_of_utc")
        created = _utc(self.created_at_utc, "decision created_at_utc")
        policy_name = _required_text(self.policy_name, "policy_name")
        policy_version = _required_text(self.policy_version, "policy_version")
        if not isinstance(self.status, DecisionStatus):
            raise DecisionContractError("status must use the DecisionStatus enum")
        if not self.factor_snapshot_ids:
            raise DecisionContractError("decision must reference factor snapshots")
        if self.status is DecisionStatus.VALID and not self.intents:
            raise DecisionContractError("a valid decision must contain at least one intent")
        if self.status is not DecisionStatus.VALID and self.intents:
            raise DecisionContractError("non-valid decisions must not contain intents")
        if not isinstance(self.trace_status, DecisionTraceStatus):
            raise DecisionContractError("trace_status must use DecisionTraceStatus")
        orders = tuple(trace.evaluation_order for trace in self.condition_traces)
        if orders != tuple(range(len(self.condition_traces))):
            raise DecisionContractError("condition traces must use contiguous evaluation order")
        if any(trace.factor_snapshot_id not in self.factor_snapshot_ids for trace in self.condition_traces):
            raise DecisionContractError("condition trace references an unknown Factor snapshot")
        if self.trace_status is DecisionTraceStatus.CAPTURED and not self.condition_traces:
            raise DecisionContractError("captured Decision traces cannot be empty")
        if self.trace_status is not DecisionTraceStatus.CAPTURED and self.condition_traces:
            raise DecisionContractError("uncaptured or unevaluated Decisions cannot contain traces")
        for intent in self.intents:
            if (
                intent.decision_id != self.decision_id
                or intent.as_of_utc != as_of
                or intent.factor_snapshot_id not in self.factor_snapshot_ids
                or intent.policy_name != policy_name
                or intent.policy_version != policy_version
            ):
                raise DecisionContractError("decision contains a mismatched trade intent")
        object.__setattr__(self, "as_of_utc", as_of)
        object.__setattr__(self, "created_at_utc", created)
        object.__setattr__(self, "policy_name", policy_name)
        object.__setattr__(self, "policy_version", policy_version)


@dataclass(frozen=True, slots=True)
class DecisionInput:
    factors: FactorSnapshotCollection
    portfolio: PortfolioSnapshot
    context: DecisionContext
    sizing: SizingContext | None = None

    def __post_init__(self) -> None:
        if self.factors.as_of_utc > self.context.as_of_utc:
            raise DecisionContractError("decision cannot use future factor snapshots")
        if self.portfolio.as_of_utc > self.context.as_of_utc:
            raise DecisionContractError("decision cannot use future portfolio context")
        if self.sizing is not None and self.sizing.as_of_utc > self.context.as_of_utc: raise DecisionContractError("decision cannot use future sizing context")
