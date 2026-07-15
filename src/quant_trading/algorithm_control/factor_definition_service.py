"""Application service for versioned Factor definitions; no GUI or execution logic."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from quant_trading.factors.definitions import FactorDefinition, FactorDefinitionParameter
from quant_trading.factors.expression_language import parse_and_validate_expression
from quant_trading.factors.errors import FactorDefinitionError
from quant_trading.factors.interfaces import FactorDefinitionStore

from .admission_models import Capability, FeatureState, OwnerLayer, Responsibility
from .models import ComponentMetadata, ComponentStatus, ComponentType, ParameterSchema, ParameterType, SafetyLevel
from .registry import AlgorithmComponentRegistry


class FactorDefinitionService:
    def __init__(self, store: FactorDefinitionStore, registry: AlgorithmComponentRegistry) -> None:
        self._store = store
        self._registry = registry
        for definition in self.list_definitions():
            self._register(definition)

    def list_definitions(self, factor_id: str | None = None) -> tuple[FactorDefinition, ...]:
        items = self._store.list_definitions()
        if factor_id is not None:
            normalized = factor_id.strip().lower()
            items = tuple(item for item in items if item.factor_id == normalized)
        return tuple(sorted(items, key=lambda item: (item.factor_id, -item.version)))

    def get(self, definition_id: UUID) -> FactorDefinition:
        for item in self.list_definitions():
            if item.definition_id == definition_id:
                return item
        raise ValueError("factor definition does not exist")

    def save(
        self,
        *,
        factor_id: str,
        display_name: str,
        description: str,
        expression: str,
        minimum_observations: int,
        output_unit: str | None,
        missing_input_policy: str,
        parameters: tuple[FactorDefinitionParameter, ...],
        change_reason: str,
        actor: str = "user",
    ) -> FactorDefinition:
        parse_and_validate_expression(expression, tuple(item.name for item in parameters))
        versions = self.list_definitions(factor_id)
        definition = FactorDefinition(
            definition_id=uuid4(),
            factor_id=factor_id,
            version=max((item.version for item in versions), default=0) + 1,
            display_name=display_name,
            description=description,
            expression=expression,
            minimum_observations=minimum_observations,
            output_unit=output_unit,
            missing_input_policy=missing_input_policy,
            parameters=parameters,
            created_at_utc=datetime.now(UTC),
            created_by=actor,
            change_reason=change_reason,
        )
        metadata = self._metadata(definition)
        if metadata.component_id in self._registry.component_ids:
            raise FactorDefinitionError(
                "factor component version is already registered"
            )
        conflicts = self._registry.admission.assess_component(metadata)
        if conflicts:
            raise FactorDefinitionError(
                "factor definition registration failed: "
                + "; ".join(item.description for item in conflicts)
            )
        self._store.save_definition(definition)
        self._registry.register(metadata)
        return definition

    def _register(self, definition: FactorDefinition) -> None:
        self._registry.register(self._metadata(definition))

    @staticmethod
    def _metadata(definition: FactorDefinition) -> ComponentMetadata:
        return ComponentMetadata(
            component_id=definition.component_id,
            display_name=f"{definition.display_name} v{definition.version}",
            component_type=ComponentType.FACTOR,
            version=str(definition.version),
            description=definition.description,
            status=ComponentStatus.AVAILABLE,
            parameter_schema=tuple(
                ParameterSchema(
                    name=item.name,
                    display_name=item.name,
                    description="User-defined numeric Factor parameter.",
                    parameter_type=ParameterType.FLOAT,
                    default_value=item.default_value,
                )
                for item in definition.parameters
            ),
            input_contract="MarketDataWindow",
            output_contract="FactorSnapshot",
            minimum_data_requirements=f"{definition.minimum_observations} completed observations",
            enabled_by_default=False,
            implementation_path="quant_trading.factors.expression.SafeExpressionFactorCalculator",
            documentation_path="docs/modules/factor-authoring.md",
            safety_level=SafetyLevel.IMPORTANT,
            owner_layer=OwnerLayer.FACTOR,
            owner_module="quant_trading.factors.expression",
            responsibilities=(Responsibility.CALCULATE_SINGLE_ASSET_FACTORS,),
            non_responsibilities=("Trade decisions, Risk approval, accounts, orders, broker execution.",),
            allowed_dependencies=("quant_trading.factors.models", "quant_trading.market_history.models"),
            forbidden_dependencies=("quant_trading.decision", "quant_trading.risk", "quant_trading.execution", "PySide6", "alpaca"),
            required_capabilities=(Capability.READ_STANDARDIZED_MARKET_DATA, Capability.CALCULATE_FACTORS),
            side_effects=(),
            financial_effect="Produces a strategy-neutral Factor value only; never a trade instruction.",
            execution_allowed=False,
            live_allowed=False,
            default_feature_state=FeatureState.REGISTERED,
        )
