"""Immutable, explainable contracts for pre-execution risk review."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from quant_trading.application_settings import ExecutionEnvironment
from quant_trading.decision.models import DecisionAction, PortfolioSnapshot, TradeIntent
from quant_trading.factors.models import FactorSnapshotCollection, FactorStatus

from .errors import RiskContractError


def _utc(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise RiskContractError(f"{field_name} must include a timezone")
    return value.astimezone(UTC)


def _required_text(value: str, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise RiskContractError(f"{field_name} must not be empty")
    return normalized


def _finite(value: Decimal | None, field_name: str) -> Decimal | None:
    if value is None:
        return None
    if not isinstance(value, Decimal):
        raise RiskContractError(f"{field_name} must use Decimal")
    if not value.is_finite():
        raise RiskContractError(f"{field_name} must be finite")
    return value


def change_is_not_increased(original: Decimal, candidate: Decimal) -> bool:
    """Return whether candidate preserves direction and does not exceed original."""

    if original == 0:
        return candidate == 0
    return candidate * original >= 0 and abs(candidate) <= abs(original)


def target_is_between(
    current: Decimal, original_target: Decimal, approved_target: Decimal
) -> bool:
    return change_is_not_increased(
        original_target - current,
        approved_target - current,
    )


class RiskRuleDecision(StrEnum):
    APPROVE = "approve"
    REJECT = "reject"
    REDUCE = "reduce"
    DEFER = "defer"
    PAUSE_SYMBOL = "pause_symbol"
    PAUSE_SYSTEM = "pause_system"
    REQUIRE_MANUAL_REVIEW = "require_manual_review"


class RiskDecisionType(StrEnum):
    APPROVED = "approved"
    APPROVED_WITH_REDUCTION = "approved_with_reduction"
    REJECTED = "rejected"
    DEFERRED = "deferred"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"
    SYMBOL_PAUSED = "symbol_paused"
    SYSTEM_PAUSED = "system_paused"


class RiskEvaluationStatus(StrEnum):
    EVALUATED = "evaluated"
    BLOCKED_INPUT = "blocked_input"
    POLICY_ERROR = "policy_error"


class ContextAvailability(StrEnum):
    UNAVAILABLE = "unavailable"
    AVAILABLE_REFERENCE = "available_reference"


class MarketState(StrEnum):
    UNKNOWN = "unknown"
    OPEN = "open"
    CLOSED = "closed"


class RiskReasonCode(StrEnum):
    POSITION_LIMIT = "RISK-POSITION-LIMIT"
    ORDER_SIZE_LIMIT = "RISK-ORDER-SIZE-LIMIT"
    PORTFOLIO_EXPOSURE = "RISK-PORTFOLIO-EXPOSURE"
    CASH_INSUFFICIENT = "RISK-CASH-INSUFFICIENT"
    BUYING_POWER = "RISK-BUYING-POWER"
    DAILY_LOSS = "RISK-DAILY-LOSS"
    DRAWDOWN = "RISK-DRAWDOWN"
    CONCENTRATION = "RISK-CONCENTRATION"
    STALE_DATA = "RISK-STALE-DATA"
    INVALID_FACTOR = "RISK-INVALID-FACTOR"
    MARKET_CLOSED = "RISK-MARKET-CLOSED"
    DUPLICATE_ORDER = "RISK-DUPLICATE-ORDER"
    SYMBOL_PAUSED = "RISK-SYMBOL-PAUSED"
    SYSTEM_PAUSED = "RISK-SYSTEM-PAUSED"
    LIVE_DISABLED = "RISK-LIVE-DISABLED"
    AUTOMATIC_SUBMISSION_DISABLED = "RISK-AUTOMATIC-SUBMISSION-DISABLED"
    MANUAL_REVIEW = "RISK-MANUAL-REVIEW"
    POLICY_ERROR = "RISK-POLICY-ERROR"
    INVALID_RULE_OUTPUT = "RISK-INVALID-RULE-OUTPUT"
    INVALID_INTENT = "RISK-INVALID-INTENT"


@dataclass(frozen=True, slots=True)
class AccountSnapshot:
    """Trace-only account reference; no balances or leverage assumptions."""

    snapshot_id: UUID
    as_of_utc: datetime
    status: ContextAvailability = ContextAvailability.UNAVAILABLE
    source_reference: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "as_of_utc", _utc(self.as_of_utc, "account as_of"))
        if not isinstance(self.status, ContextAvailability):
            raise RiskContractError("account status must use ContextAvailability")
        if self.status is ContextAvailability.AVAILABLE_REFERENCE:
            if self.source_reference is None or not self.source_reference.strip():
                raise RiskContractError("available account context needs a reference")


@dataclass(frozen=True, slots=True)
class OpenOrdersSnapshot:
    """Trace-only open-order reference; actual order semantics are not implemented."""

    snapshot_id: UUID
    as_of_utc: datetime
    status: ContextAvailability = ContextAvailability.UNAVAILABLE
    source_reference: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "as_of_utc", _utc(self.as_of_utc, "open orders as_of")
        )
        if not isinstance(self.status, ContextAvailability):
            raise RiskContractError("open-order status must use ContextAvailability")
        if self.status is ContextAvailability.AVAILABLE_REFERENCE:
            if self.source_reference is None or not self.source_reference.strip():
                raise RiskContractError("available open-order context needs a reference")


@dataclass(frozen=True, slots=True)
class MarketRiskContext:
    as_of_utc: datetime
    data_as_of_utc: datetime
    data_complete: bool
    market_state: MarketState = MarketState.UNKNOWN

    def __post_init__(self) -> None:
        as_of = _utc(self.as_of_utc, "market context as_of")
        data_as_of = _utc(self.data_as_of_utc, "market data as_of")
        if data_as_of > as_of:
            raise RiskContractError("risk context cannot use future market data")
        if not isinstance(self.market_state, MarketState):
            raise RiskContractError("market_state must use MarketState")
        object.__setattr__(self, "as_of_utc", as_of)
        object.__setattr__(self, "data_as_of_utc", data_as_of)


@dataclass(frozen=True, slots=True)
class SystemRiskState:
    as_of_utc: datetime
    system_paused: bool = False
    paused_symbols: tuple[str, ...] = ()
    emergency_derisk_requested: bool = False

    def __post_init__(self) -> None:
        as_of = _utc(self.as_of_utc, "system risk state as_of")
        symbols = tuple(symbol.strip().upper() for symbol in self.paused_symbols)
        if any(not symbol for symbol in symbols) or len(symbols) != len(set(symbols)):
            raise RiskContractError("paused symbols must be unique and non-empty")
        object.__setattr__(self, "as_of_utc", as_of)
        object.__setattr__(self, "paused_symbols", symbols)


@dataclass(frozen=True, slots=True)
class RiskContext:
    as_of_utc: datetime
    configuration_version: str
    environment: ExecutionEnvironment
    manual_confirmation_required: bool = True
    live_trading_enabled: bool = False
    automatic_submission_enabled: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "as_of_utc", _utc(self.as_of_utc, "risk as_of"))
        object.__setattr__(
            self,
            "configuration_version",
            _required_text(self.configuration_version, "configuration_version"),
        )
        if not isinstance(self.environment, ExecutionEnvironment):
            raise RiskContractError("environment must use ExecutionEnvironment")


@dataclass(frozen=True, slots=True)
class RiskEvaluationContext:
    factors: FactorSnapshotCollection
    portfolio: PortfolioSnapshot
    account: AccountSnapshot
    open_orders: OpenOrdersSnapshot
    market: MarketRiskContext
    system: SystemRiskState
    risk: RiskContext

    def __post_init__(self) -> None:
        as_of = self.risk.as_of_utc
        context_times = (
            self.factors.as_of_utc,
            self.portfolio.as_of_utc,
            self.account.as_of_utc,
            self.open_orders.as_of_utc,
            self.market.as_of_utc,
            self.system.as_of_utc,
        )
        if any(value > as_of for value in context_times):
            raise RiskContractError("risk evaluation cannot use future context")


@dataclass(frozen=True, slots=True)
class RiskRuleResult:
    rule_name: str
    rule_version: str
    decision: RiskRuleDecision
    reason_codes: tuple[RiskReasonCode, ...]
    approved_target: Decimal | None = None
    approved_quantity: Decimal | None = None
    warnings: tuple[str, ...] = ()
    earliest_execution_utc: datetime | None = None
    approved_notional: Decimal | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "rule_name", _required_text(self.rule_name, "rule_name"))
        object.__setattr__(
            self, "rule_version", _required_text(self.rule_version, "rule_version")
        )
        if not isinstance(self.decision, RiskRuleDecision):
            raise RiskContractError("rule decision must use RiskRuleDecision")
        if not self.reason_codes or any(
            not isinstance(code, RiskReasonCode) for code in self.reason_codes
        ):
            raise RiskContractError("risk rule requires structured reason codes")
        _finite(self.approved_target, "approved_target")
        _finite(self.approved_quantity, "approved_quantity")
        approved_notional=_finite(self.approved_notional,"approved_notional")
        if approved_notional is not None and approved_notional<=0: raise RiskContractError("approved_notional must be positive")
        if self.decision is RiskRuleDecision.REDUCE:
            if self.approved_target is None and self.approved_quantity is None and self.approved_notional is None:
                raise RiskContractError("a reduction must specify an approved limit")
        elif self.approved_target is not None or self.approved_quantity is not None or self.approved_notional is not None:
            raise RiskContractError("only a reduction may alter approved values")
        if self.earliest_execution_utc is not None:
            object.__setattr__(
                self,
                "earliest_execution_utc",
                _utc(self.earliest_execution_utc, "earliest_execution_utc"),
            )


@dataclass(frozen=True, slots=True)
class RiskDecision:
    risk_decision_id: UUID
    source_trade_intent_id: UUID
    symbol: str
    evaluated_at_utc: datetime
    decision: RiskDecisionType
    current_exposure: Decimal | None
    original_target: Decimal | None
    approved_target: Decimal | None
    original_quantity: Decimal | None
    approved_quantity: Decimal | None
    exposure_unit: str | None
    risk_status: RiskEvaluationStatus
    reason_codes: tuple[RiskReasonCode, ...]
    rule_results: tuple[RiskRuleResult, ...]
    warnings: tuple[str, ...]
    requires_manual_review: bool
    system_paused: bool
    symbol_paused: bool
    risk_policy_name: str
    risk_policy_version: str
    configuration_version: str
    portfolio_snapshot_id: UUID
    account_snapshot_id: UUID
    environment: ExecutionEnvironment
    earliest_execution_utc: datetime | None = None
    original_notional: Decimal | None = None
    approved_notional: Decimal | None = None

    def __post_init__(self) -> None:
        symbol = self.symbol.strip().upper()
        if not symbol:
            raise RiskContractError("risk decision symbol must not be empty")
        object.__setattr__(
            self, "evaluated_at_utc", _utc(self.evaluated_at_utc, "evaluated_at_utc")
        )
        if not isinstance(self.decision, RiskDecisionType):
            raise RiskContractError("decision must use RiskDecisionType")
        if not isinstance(self.risk_status, RiskEvaluationStatus):
            raise RiskContractError("risk_status must use RiskEvaluationStatus")
        if not self.reason_codes or any(
            not isinstance(code, RiskReasonCode) for code in self.reason_codes
        ):
            raise RiskContractError("risk decision requires structured reasons")
        current_exposure = _finite(self.current_exposure, "current_exposure")
        original_target = _finite(self.original_target, "original_target")
        approved_target = _finite(self.approved_target, "approved_target")
        original_quantity = _finite(self.original_quantity, "original_quantity")
        approved_quantity = _finite(self.approved_quantity, "approved_quantity")
        original_notional=_finite(self.original_notional,"original_notional"); approved_notional=_finite(self.approved_notional,"approved_notional")
        approved = {
            RiskDecisionType.APPROVED,
            RiskDecisionType.APPROVED_WITH_REDUCTION,
        }
        if self.decision not in approved and (
            approved_target is not None or approved_quantity is not None or approved_notional is not None
        ):
            raise RiskContractError("blocked decisions cannot approve exposure")
        if self.decision is RiskDecisionType.APPROVED:
            if approved_target != original_target or approved_quantity != original_quantity or approved_notional != original_notional:
                raise RiskContractError("approval must preserve original values")
        if self.decision is RiskDecisionType.APPROVED_WITH_REDUCTION:
            target_changed = approved_target != original_target
            quantity_changed = approved_quantity != original_quantity
            notional_changed=approved_notional!=original_notional
            if not target_changed and not quantity_changed and not notional_changed:
                raise RiskContractError("reduction must make at least one value stricter")
            if original_target is not None:
                if current_exposure is None or approved_target is None:
                    raise RiskContractError("target reduction needs current and approved target")
                if not target_is_between(
                    current_exposure, original_target, approved_target
                ):
                    raise RiskContractError("approved target exceeds the original intent")
            elif approved_target is not None:
                raise RiskContractError("risk decision cannot invent a target")
            if original_quantity is not None:
                if approved_quantity is None or not change_is_not_increased(
                    original_quantity, approved_quantity
                ):
                    raise RiskContractError("approved quantity exceeds the original intent")
            elif approved_quantity is not None:
                raise RiskContractError("risk decision cannot invent a quantity")
            if original_notional is not None:
                if approved_notional is None or approved_notional<=0 or approved_notional>original_notional: raise RiskContractError("approved notional exceeds the original intent")
            elif approved_notional is not None: raise RiskContractError("risk decision cannot invent a notional")
        if self.decision is RiskDecisionType.SYSTEM_PAUSED and not self.system_paused:
            raise RiskContractError("SYSTEM_PAUSED must set system_paused")
        if self.decision is RiskDecisionType.SYMBOL_PAUSED and not self.symbol_paused:
            raise RiskContractError("SYMBOL_PAUSED must set symbol_paused")
        if not isinstance(self.environment, ExecutionEnvironment):
            raise RiskContractError("risk environment must use ExecutionEnvironment")
        if self.earliest_execution_utc is not None:
            object.__setattr__(
                self,
                "earliest_execution_utc",
                _utc(self.earliest_execution_utc, "earliest_execution_utc"),
            )
        object.__setattr__(self, "symbol", symbol)
        object.__setattr__(
            self, "risk_policy_name", _required_text(self.risk_policy_name, "risk policy")
        )
        object.__setattr__(
            self,
            "risk_policy_version",
            _required_text(self.risk_policy_version, "risk policy version"),
        )
        object.__setattr__(
            self,
            "configuration_version",
            _required_text(self.configuration_version, "configuration version"),
        )


@dataclass(frozen=True, slots=True)
class RiskApprovedTradeIntent:
    """Risk-reviewed input for future order construction; not an order authorization."""

    trade_intent: TradeIntent
    risk_decision: RiskDecision

    def __post_init__(self) -> None:
        if self.risk_decision.source_trade_intent_id != self.trade_intent.intent_id:
            raise RiskContractError("risk approval references a different trade intent")
        if self.risk_decision.symbol != self.trade_intent.symbol:
            raise RiskContractError("risk approval references a different symbol")
        if (
            self.risk_decision.current_exposure != self.trade_intent.current_exposure
            or self.risk_decision.original_target != self.trade_intent.target_exposure
            or self.risk_decision.original_quantity != self.trade_intent.desired_change
            or self.risk_decision.exposure_unit != self.trade_intent.exposure_unit
        ):
            raise RiskContractError("risk approval does not preserve the source proposal")
        if self.risk_decision.decision not in {
            RiskDecisionType.APPROVED,
            RiskDecisionType.APPROVED_WITH_REDUCTION,
        }:
            raise RiskContractError("only an approved risk decision can pass the gate")
        if self.trade_intent.action in {
            DecisionAction.HOLD,
            DecisionAction.NO_DECISION,
        }:
            raise RiskContractError("a non-action cannot enter order construction")
        if (
            self.risk_decision.approved_target is None
            and self.risk_decision.approved_quantity is None
            and self.risk_decision.approved_notional is None
        ):
            raise RiskContractError("order construction needs an approved exposure value")


def factor_statuses_for_intent(
    intent: TradeIntent, factors: FactorSnapshotCollection
) -> tuple[FactorStatus, ...] | None:
    for snapshot in factors.snapshots:
        if snapshot.snapshot_id == intent.factor_snapshot_id:
            if snapshot.symbol != intent.symbol:
                return None
            return tuple(result.status for result in snapshot.results)
    return None
