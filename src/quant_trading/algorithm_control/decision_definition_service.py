"""Application service for immutable, disabled-by-default Decision policies."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from quant_trading.decision.definitions import DecisionCondition, DecisionPolicyDefinition, RuleCombination, SizingDefinition, SizingMode
from quant_trading.decision.models import DecisionAction

from .admission_models import Capability, FeatureState, OwnerLayer, Responsibility
from .decision_definition_store import JsonDecisionDefinitionStore
from .factor_definition_service import FactorDefinitionService
from .models import ComponentMetadata, ComponentStatus, ComponentType, SafetyLevel
from .registry import AlgorithmComponentRegistry


class DecisionDefinitionService:
    def __init__(
        self,
        store: JsonDecisionDefinitionStore,
        registry: AlgorithmComponentRegistry,
        factors: FactorDefinitionService,
    ) -> None:
        self._store = store
        self._registry = registry
        self._factors = factors
        for definition in self.list_definitions():
            self._registry.register(self._metadata(definition))

    def list_definitions(self, policy_id: str | None = None) -> tuple[DecisionPolicyDefinition, ...]:
        items = self._store.list_definitions()
        if policy_id is not None:
            normalized = policy_id.strip().lower()
            items = tuple(item for item in items if item.policy_id == normalized)
        return tuple(sorted(items, key=lambda item: (item.policy_id, -item.version)))

    def get_by_component_id(self, component_id: str) -> DecisionPolicyDefinition:
        for item in self.list_definitions():
            if item.component_id == component_id:
                return item
        raise ValueError("Decision component definition does not exist")

    def save(
        self,
        *,
        policy_id: str,
        display_name: str,
        description: str,
        conditions: tuple[DecisionCondition, ...],
        combination: RuleCombination,
        match_action: DecisionAction,
        reason_code: str,
        change_reason: str,
        sizing: SizingDefinition = SizingDefinition(),
        actor: str = "user",
    ) -> DecisionPolicyDefinition:
        if match_action in (DecisionAction.HOLD,DecisionAction.NO_DECISION) and sizing.mode is not SizingMode.NONE: raise ValueError("HOLD/NO_DECISION cannot request a trade amount")
        if match_action is DecisionAction.INCREASE and sizing.mode in (SizingMode.PERCENT_POSITION_VALUE,SizingMode.EXIT_ALL): raise ValueError("buy Decision cannot use sell-only sizing")
        if match_action in (DecisionAction.DECREASE,DecisionAction.EXIT) and sizing.mode in (SizingMode.PERCENT_AVAILABLE_CASH,SizingMode.PERCENT_EQUITY): raise ValueError("sell Decision cannot use buy-only sizing")
        for component_id in sizing.market_factor_component_ids:
            metadata=self._registry.get(component_id)
            if metadata.component_type is not ComponentType.MARKET_FACTOR: raise ValueError("sizing Market Factor reference has the wrong component type")
        for condition in conditions:
            factor = self._factors.get_by_component_id(condition.factor_component_id)
            if (condition.factor_name, condition.factor_version) != (factor.factor_id, str(factor.version)):
                raise ValueError("Decision condition Factor identity does not match the selected component")
            if self._registry.get(condition.factor_component_id).status is ComponentStatus.DEPRECATED:
                raise ValueError("archived or deprecated Factors cannot enter a new Decision version")
        versions = self.list_definitions(policy_id)
        definition = DecisionPolicyDefinition(
            uuid4(),
            policy_id,
            max((item.version for item in versions), default=0) + 1,
            display_name,
            description,
            conditions,
            combination,
            match_action,
            reason_code,
            datetime.now(UTC),
            actor,
            change_reason,
            sizing,
        )
        metadata = self._metadata(definition)
        conflicts = self._registry.admission.assess_component(metadata)
        if conflicts:
            raise ValueError("Decision definition registration failed: " + "; ".join(item.description for item in conflicts))
        self._store.save_definition(definition)
        self._registry.register(metadata)
        return definition

    @staticmethod
    def _metadata(definition: DecisionPolicyDefinition) -> ComponentMetadata:
        return ComponentMetadata(
            component_id=definition.component_id,
            display_name=f"{definition.display_name} v{definition.version}",
            component_type=ComponentType.DECISION,
            version=str(definition.version),
            description=definition.description,
            status=ComponentStatus.AVAILABLE,
            parameter_schema=(),
            input_contract="FactorSnapshot",
            output_contract="TradeIntent",
            minimum_data_requirements="All exact Factor versions referenced by the definition must be VALID.",
            enabled_by_default=False,
            implementation_path="quant_trading.decision.rule_policy.SafeRuleDecisionPolicy",
            documentation_path="docs/modules/trading-decision.md",
            required_factors=definition.selected_factor_ids + definition.sizing.market_factor_component_ids,
            safety_level=SafetyLevel.HIGH_RISK,
            owner_layer=OwnerLayer.DECISION,
            owner_module="quant_trading.decision.rule_policy",
            responsibilities=(Responsibility.CREATE_TRADE_INTENTS,),
            non_responsibilities=("Factor calculation, Risk approval, position sizing, order construction, broker execution.",),
            allowed_dependencies=("quant_trading.factors.models", "quant_trading.decision.models"),
            forbidden_dependencies=("quant_trading.risk", "quant_trading.execution", "alpaca", "sqlite3", "PySide6"),
            required_capabilities=(Capability.READ_FACTOR_SNAPSHOT, Capability.CREATE_TRADE_INTENT),
            side_effects=(),
            financial_effect="May produce an unapproved direction-only TradeIntent; never an order or position size.",
            execution_allowed=False,
            live_allowed=False,
            default_feature_state=FeatureState.REGISTERED,
        )
