"""Version and register Market Factors that aggregate exact Asset Factors."""
from datetime import UTC,datetime
from uuid import uuid4
from quant_trading.factors.market import MarketFactorDefinition
from .admission_models import Capability,FeatureState,OwnerLayer,Responsibility
from .models import ComponentMetadata,ComponentStatus,ComponentType,SafetyLevel
class MarketFactorDefinitionService:
    def __init__(self,store,registry,asset_factors):
        self._store=store; self._registry=registry; self._assets=asset_factors
        for x in self.list_definitions(): self._registry.register(self._metadata(x))
    def list_definitions(self,identifier=None):
        items=self._store.list_definitions(); normalized=None if identifier is None else identifier.strip().lower()
        return tuple(sorted((x for x in items if normalized is None or x.market_factor_id==normalized),key=lambda x:(x.market_factor_id,-x.version)))
    def get_by_component_id(self,component_id):
        for x in self.list_definitions():
            if x.component_id==component_id:return x
        raise ValueError("Market Factor definition does not exist")
    def save(self,*,market_factor_id,display_name,description,source_factor_component_id,symbols,aggregation,change_reason,actor="user"):
        source=self._assets.get_by_component_id(source_factor_component_id); versions=self.list_definitions(market_factor_id)
        item=MarketFactorDefinition(uuid4(),market_factor_id,max((x.version for x in versions),default=0)+1,display_name,description,source.component_id,source.factor_id,str(source.version),tuple(symbols),aggregation,datetime.now(UTC),actor,change_reason)
        self._store.save_definition(item); self._registry.register(self._metadata(item)); return item
    @staticmethod
    def _metadata(x): return ComponentMetadata(component_id=x.component_id,display_name=f"{x.display_name} v{x.version}",component_type=ComponentType.MARKET_FACTOR,version=str(x.version),description=x.description,status=ComponentStatus.AVAILABLE,parameter_schema=(),input_contract="AssetFactorResultCollection",output_contract="MarketFactorResult",minimum_data_requirements="All symbols in the immutable universe must provide a VALID exact Asset Factor version.",enabled_by_default=False,implementation_path="quant_trading.factors.market.MarketFactorCalculator",documentation_path="docs/modules/factors.md",safety_level=SafetyLevel.IMPORTANT,owner_layer=OwnerLayer.FACTOR,owner_module="quant_trading.factors.market",responsibilities=(Responsibility.CALCULATE_MARKET_FACTORS,),non_responsibilities=("Decision, account state, sizing, Risk, execution.",),allowed_dependencies=("quant_trading.factors.models",),forbidden_dependencies=("quant_trading.decision","quant_trading.risk","quant_trading.execution","PySide6","alpaca"),required_capabilities=(Capability.READ_FACTOR_SNAPSHOT,Capability.CALCULATE_FACTORS),side_effects=(),financial_effect="Produces one research market context value; never an order.",execution_allowed=False,live_allowed=False,default_feature_state=FeatureState.REGISTERED)
