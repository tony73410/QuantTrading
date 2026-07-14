"""Conservative risk-policy composition with no broker or order access."""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterable
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from quant_trading.application_settings import ExecutionEnvironment
from quant_trading.decision.models import TradeIntent
from quant_trading.factors.models import FactorStatus

from .errors import RiskContractError
from .interfaces import RiskPolicy
from .models import (
    RiskDecision,
    RiskDecisionType,
    RiskEvaluationContext,
    RiskEvaluationStatus,
    RiskReasonCode,
    RiskRuleDecision,
    RiskRuleResult,
    factor_statuses_for_intent,
    target_is_between,
    change_is_not_increased,
)
from .registry import RiskPolicyRegistry


logger = logging.getLogger(__name__)


_PRIORITY = {
    RiskRuleDecision.APPROVE: 0,
    RiskRuleDecision.REDUCE: 1,
    RiskRuleDecision.DEFER: 2,
    RiskRuleDecision.REQUIRE_MANUAL_REVIEW: 3,
    RiskRuleDecision.PAUSE_SYMBOL: 4,
    RiskRuleDecision.REJECT: 5,
    RiskRuleDecision.PAUSE_SYSTEM: 6,
}


class RiskEngine:
    """Combine injected rules; a result can never exceed its source intent."""

    def __init__(
        self,
        policies: Iterable[RiskPolicy] | RiskPolicyRegistry = (),
        *,
        engine_name: str = "composite_risk_engine",
        engine_version: str = "1",
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
        id_factory: Callable[[], UUID] = uuid4,
    ) -> None:
        self._registry = (
            policies if isinstance(policies, RiskPolicyRegistry) else RiskPolicyRegistry(policies)
        )
        self._engine_name = engine_name.strip()
        self._engine_version = engine_version.strip()
        if not self._engine_name or not self._engine_version:
            raise RiskContractError("risk engine name and version are required")
        self._clock = clock
        self._id_factory = id_factory

    def evaluate(
        self,
        trade_intent: TradeIntent,
        context: RiskEvaluationContext,
    ) -> RiskDecision:
        blocked = self._preflight(trade_intent, context)
        if blocked is not None:
            self._log_decision(blocked)
            return blocked

        if not self._registry.policies:
            decision = self._blocked_decision(
                trade_intent,
                context,
                RiskDecisionType.MANUAL_REVIEW_REQUIRED,
                RiskEvaluationStatus.BLOCKED_INPUT,
                (RiskReasonCode.MANUAL_REVIEW,),
                requires_manual_review=True,
            )
            self._log_decision(decision)
            return decision

        results: list[RiskRuleResult] = []
        policy_error = False
        for policy in self._registry.policies:
            try:
                result = policy.evaluate(trade_intent, context)
                if (
                    result.rule_name != policy.policy_name
                    or result.rule_version != policy.policy_version
                ):
                    raise RiskContractError("risk policy returned mismatched metadata")
                self._validate_reduction(trade_intent, result)
                results.append(result)
            except Exception as exc:
                policy_error = True
                logger.exception(
                    "Risk policy failed policy_name=%s policy_version=%s intent_id=%s",
                    policy.policy_name,
                    policy.policy_version,
                    trade_intent.intent_id,
                )
                results.append(
                    RiskRuleResult(
                        policy.policy_name,
                        policy.policy_version,
                        RiskRuleDecision.REJECT,
                        (RiskReasonCode.POLICY_ERROR, RiskReasonCode.INVALID_RULE_OUTPUT),
                        warnings=(type(exc).__name__,),
                    )
                )

        strongest = max(results, key=lambda result: _PRIORITY[result.decision]).decision
        decision = self._decision_type(strongest)
        approved_target, approved_quantity = self._approved_values(
            trade_intent, results, decision
        )
        reasons = tuple(dict.fromkeys(code for result in results for code in result.reason_codes))
        warnings = tuple(dict.fromkeys(value for result in results for value in result.warnings))
        deferrals = tuple(
            result.earliest_execution_utc
            for result in results
            if result.earliest_execution_utc is not None
        )
        final_decision = self._make_decision(
            trade_intent,
            context,
            decision,
            RiskEvaluationStatus.POLICY_ERROR if policy_error else RiskEvaluationStatus.EVALUATED,
            reasons,
            tuple(results),
            approved_target=approved_target,
            approved_quantity=approved_quantity,
            warnings=warnings,
            requires_manual_review=(
                context.risk.manual_confirmation_required
                or decision is RiskDecisionType.MANUAL_REVIEW_REQUIRED
            ),
            system_paused=decision is RiskDecisionType.SYSTEM_PAUSED,
            symbol_paused=decision is RiskDecisionType.SYMBOL_PAUSED,
            earliest_execution_utc=max(deferrals) if deferrals else None,
        )
        self._log_decision(final_decision)
        return final_decision

    def _preflight(
        self, intent: TradeIntent, context: RiskEvaluationContext
    ) -> RiskDecision | None:
        if (
            intent.as_of_utc != context.risk.as_of_utc
            or intent.factor_snapshot_id
            not in {snapshot.snapshot_id for snapshot in context.factors.snapshots}
        ):
            return self._blocked_decision(
                intent,
                context,
                RiskDecisionType.REJECTED,
                RiskEvaluationStatus.BLOCKED_INPUT,
                (RiskReasonCode.INVALID_INTENT,),
            )
        if context.system.system_paused or context.system.emergency_derisk_requested:
            return self._blocked_decision(
                intent,
                context,
                RiskDecisionType.SYSTEM_PAUSED,
                RiskEvaluationStatus.EVALUATED,
                (RiskReasonCode.SYSTEM_PAUSED,),
                system_paused=True,
                warnings=(
                    "Emergency de-risking is not implemented; new intents are paused."
                    if context.system.emergency_derisk_requested
                    else "System risk state is paused."
                ,),
            )
        if intent.symbol in context.system.paused_symbols:
            return self._blocked_decision(
                intent,
                context,
                RiskDecisionType.SYMBOL_PAUSED,
                RiskEvaluationStatus.EVALUATED,
                (RiskReasonCode.SYMBOL_PAUSED,),
                symbol_paused=True,
            )
        if context.risk.environment is ExecutionEnvironment.ALPACA_LIVE:
            return self._blocked_decision(
                intent,
                context,
                RiskDecisionType.REJECTED,
                RiskEvaluationStatus.BLOCKED_INPUT,
                (RiskReasonCode.LIVE_DISABLED,),
            )
        if context.risk.automatic_submission_enabled:
            return self._blocked_decision(
                intent,
                context,
                RiskDecisionType.REJECTED,
                RiskEvaluationStatus.BLOCKED_INPUT,
                (RiskReasonCode.AUTOMATIC_SUBMISSION_DISABLED,),
            )
        statuses = factor_statuses_for_intent(intent, context.factors)
        if statuses is None or not statuses or any(
            status not in {FactorStatus.VALID, FactorStatus.STALE} for status in statuses
        ):
            return self._blocked_decision(
                intent,
                context,
                RiskDecisionType.REJECTED,
                RiskEvaluationStatus.BLOCKED_INPUT,
                (RiskReasonCode.INVALID_FACTOR,),
            )
        if any(status is FactorStatus.STALE for status in statuses) or not context.market.data_complete:
            return self._blocked_decision(
                intent,
                context,
                RiskDecisionType.DEFERRED,
                RiskEvaluationStatus.BLOCKED_INPUT,
                (RiskReasonCode.STALE_DATA,),
            )
        return None

    @staticmethod
    def _log_decision(decision: RiskDecision) -> None:
        logger.info(
            "Risk review completed risk_decision_id=%s trade_intent_id=%s "
            "symbol=%s decision=%s original_target=%s approved_target=%s "
            "original_quantity=%s approved_quantity=%s reason_codes=%s "
            "policy=%s policy_version=%s configuration_version=%s "
            "environment=%s manual_review_required=%s",
            decision.risk_decision_id,
            decision.source_trade_intent_id,
            decision.symbol,
            decision.decision.value,
            decision.original_target,
            decision.approved_target,
            decision.original_quantity,
            decision.approved_quantity,
            ",".join(code.value for code in decision.reason_codes),
            decision.risk_policy_name,
            decision.risk_policy_version,
            decision.configuration_version,
            decision.environment.value,
            decision.requires_manual_review,
        )

    def _validate_reduction(self, intent: TradeIntent, result: RiskRuleResult) -> None:
        if result.decision is not RiskRuleDecision.REDUCE:
            return
        originals = (intent.current_exposure, intent.target_exposure, intent.desired_change)
        if intent.target_exposure is not None:
            if intent.current_exposure is None or result.approved_target is None:
                raise RiskContractError("target reduction needs current and approved target")
            if not target_is_between(
                intent.current_exposure, intent.target_exposure, result.approved_target
            ):
                raise RiskContractError("risk rule attempted to increase or reverse target risk")
        elif result.approved_target is not None:
            raise RiskContractError("risk rule cannot invent a target")
        if intent.desired_change is not None:
            if result.approved_quantity is None:
                raise RiskContractError("quantity reduction needs an approved quantity")
            if not change_is_not_increased(intent.desired_change, result.approved_quantity):
                raise RiskContractError("risk rule attempted to increase or reverse quantity")
        elif result.approved_quantity is not None:
            raise RiskContractError("risk rule cannot invent a quantity")
        if originals == (
            intent.current_exposure,
            result.approved_target,
            result.approved_quantity,
        ):
            raise RiskContractError("REDUCE must make at least one value stricter")

    def _approved_values(
        self,
        intent: TradeIntent,
        results: list[RiskRuleResult],
        decision: RiskDecisionType,
    ) -> tuple[Decimal | None, Decimal | None]:
        if decision not in {
            RiskDecisionType.APPROVED,
            RiskDecisionType.APPROVED_WITH_REDUCTION,
        }:
            return None, None
        if decision is RiskDecisionType.APPROVED:
            return intent.target_exposure, intent.desired_change
        reductions = [result for result in results if result.decision is RiskRuleDecision.REDUCE]
        target = intent.target_exposure
        if target is not None and intent.current_exposure is not None:
            target = min(
                (result.approved_target for result in reductions),
                key=lambda value: abs(value - intent.current_exposure),  # type: ignore[operator]
            )
        quantity = intent.desired_change
        if quantity is not None:
            quantity = min(
                (result.approved_quantity for result in reductions),
                key=lambda value: abs(value),  # type: ignore[arg-type]
            )
        return target, quantity

    @staticmethod
    def _decision_type(decision: RiskRuleDecision) -> RiskDecisionType:
        return {
            RiskRuleDecision.APPROVE: RiskDecisionType.APPROVED,
            RiskRuleDecision.REDUCE: RiskDecisionType.APPROVED_WITH_REDUCTION,
            RiskRuleDecision.DEFER: RiskDecisionType.DEFERRED,
            RiskRuleDecision.REQUIRE_MANUAL_REVIEW: RiskDecisionType.MANUAL_REVIEW_REQUIRED,
            RiskRuleDecision.PAUSE_SYMBOL: RiskDecisionType.SYMBOL_PAUSED,
            RiskRuleDecision.REJECT: RiskDecisionType.REJECTED,
            RiskRuleDecision.PAUSE_SYSTEM: RiskDecisionType.SYSTEM_PAUSED,
        }[decision]

    def _blocked_decision(
        self,
        intent: TradeIntent,
        context: RiskEvaluationContext,
        decision: RiskDecisionType,
        status: RiskEvaluationStatus,
        reasons: tuple[RiskReasonCode, ...],
        **kwargs: object,
    ) -> RiskDecision:
        return self._make_decision(intent, context, decision, status, reasons, (), **kwargs)

    def _make_decision(
        self,
        intent: TradeIntent,
        context: RiskEvaluationContext,
        decision: RiskDecisionType,
        status: RiskEvaluationStatus,
        reasons: tuple[RiskReasonCode, ...],
        rule_results: tuple[RiskRuleResult, ...],
        *,
        approved_target: Decimal | None = None,
        approved_quantity: Decimal | None = None,
        warnings: tuple[str, ...] = (),
        requires_manual_review: bool | None = None,
        system_paused: bool = False,
        symbol_paused: bool = False,
        earliest_execution_utc: datetime | None = None,
    ) -> RiskDecision:
        return RiskDecision(
            risk_decision_id=self._id_factory(),
            source_trade_intent_id=intent.intent_id,
            symbol=intent.symbol,
            evaluated_at_utc=self._clock(),
            decision=decision,
            current_exposure=intent.current_exposure,
            original_target=intent.target_exposure,
            approved_target=approved_target,
            original_quantity=intent.desired_change,
            approved_quantity=approved_quantity,
            exposure_unit=intent.exposure_unit,
            risk_status=status,
            reason_codes=reasons,
            rule_results=rule_results,
            warnings=warnings,
            requires_manual_review=context.risk.manual_confirmation_required
            if requires_manual_review is None
            else requires_manual_review,
            system_paused=system_paused,
            symbol_paused=symbol_paused,
            risk_policy_name=self._engine_name,
            risk_policy_version=self._engine_version,
            configuration_version=context.risk.configuration_version,
            portfolio_snapshot_id=context.portfolio.snapshot_id,
            account_snapshot_id=context.account.snapshot_id,
            environment=context.risk.environment,
            earliest_execution_utc=earliest_execution_utc,
        )
