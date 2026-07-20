"""Restricted deterministic Decision policy; no Python source evaluation."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from .definitions import ComparisonOperator, DecisionPolicyDefinition, RuleCombination
from .models import (
    DecisionConditionTrace,
    DecisionInput,
    DecisionResult,
    DecisionStatus,
    DecisionTraceStatus,
    TradeIntent,
)
from .sizing import evaluate_sizing_with_trace


class SafeRuleDecisionPolicy:
    def __init__(self, definition: DecisionPolicyDefinition) -> None:
        self.definition = definition

    @property
    def policy_name(self) -> str:
        return self.definition.policy_id

    @property
    def policy_version(self) -> str:
        return str(self.definition.version)

    def evaluate(self, decision_input: DecisionInput) -> DecisionResult:
        results = {
            (result.factor_name, result.factor_version): (snapshot.snapshot_id, result)
            for snapshot in decision_input.factors.snapshots
            for result in snapshot.results
        }
        checks: list[bool] = []
        traces: list[DecisionConditionTrace] = []
        for order, condition in enumerate(self.definition.conditions):
            snapshot_id, result = results[(condition.factor_name, condition.factor_version)]
            if isinstance(result.value, bool) or not isinstance(result.value, (Decimal, int)):
                raise ValueError("Decision conditions require numeric Factor values")
            input_value = Decimal(result.value)
            matched = self._compare(input_value, condition.operator, condition.threshold)
            checks.append(matched)
            traces.append(
                DecisionConditionTrace(
                    order,
                    condition.factor_component_id,
                    condition.factor_name,
                    condition.factor_version,
                    snapshot_id,
                    input_value,
                    result.unit,
                    result.status,
                    condition.operator.value,
                    condition.threshold,
                    matched,
                )
            )
        matched = all(checks) if self.definition.combination is RuleCombination.ALL else any(checks)
        decision_id = uuid4()
        snapshot_ids = tuple(snapshot.snapshot_id for snapshot in decision_input.factors.snapshots)
        now = datetime.now(UTC)
        if not matched or self.definition.match_action.value == "no_decision":
            return DecisionResult(
                decision_id,
                decision_input.context.as_of_utc,
                self.policy_name,
                self.policy_version,
                decision_input.context.parameters,
                snapshot_ids,
                DecisionStatus.NO_DECISION,
                (),
                ("CONDITIONS_NOT_MET" if not matched else self.definition.reason_code,),
                now,
                tuple(traces),
                DecisionTraceStatus.CAPTURED,
            )
        first_snapshot = decision_input.factors.snapshots[0]
        requested_notional, sizing_inputs = evaluate_sizing_with_trace(
            self.definition.sizing, decision_input.sizing
        )
        sizing_references = tuple(item.name for item in sizing_inputs)
        intent = TradeIntent(
            uuid4(),
            decision_id,
            first_snapshot.symbol,
            decision_input.context.as_of_utc,
            self.definition.match_action,
            None,
            None,
            None,
            None,
            None,
            (self.definition.reason_code,),
            first_snapshot.snapshot_id,
            self.policy_name,
            self.policy_version,
            now,
            requested_notional=requested_notional,
            notional_currency="USD" if requested_notional is not None else None,
            sizing_mode=self.definition.sizing.mode.value,
            sizing_expression=self.definition.sizing.expression,
            sizing_references=sizing_references,
            sizing_inputs=sizing_inputs,
        )
        return DecisionResult(
            decision_id,
            decision_input.context.as_of_utc,
            self.policy_name,
            self.policy_version,
            decision_input.context.parameters,
            snapshot_ids,
            DecisionStatus.VALID,
            (intent,),
            (self.definition.reason_code,),
            now,
            tuple(traces),
            DecisionTraceStatus.CAPTURED,
        )

    @staticmethod
    def _compare(value: Decimal, operator: ComparisonOperator, threshold: Decimal) -> bool:
        return {
            ComparisonOperator.LESS_THAN: value < threshold,
            ComparisonOperator.LESS_THAN_OR_EQUAL: value <= threshold,
            ComparisonOperator.EQUAL: value == threshold,
            ComparisonOperator.GREATER_THAN_OR_EQUAL: value >= threshold,
            ComparisonOperator.GREATER_THAN: value > threshold,
        }[operator]
