"""Application controller for the algorithm control center."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from quant_trading.application_settings import ApplicationRoleSettings

from .configuration_service import ConfigurationService
from .factor_definition_service import FactorDefinitionService
from .factor_lifecycle import FactorLifecycleRecord, FactorLifecycleService, FactorLifecycleState
from .decision_definition_service import DecisionDefinitionService
from quant_trading.decision.definitions import DecisionPolicyDefinition
from quant_trading.factors.definitions import FactorDefinition, FactorDefinitionParameter
from quant_trading.backtesting.strategy_definitions import SimulationStrategyDefinition
from quant_trading.backtesting.strategy_service import SimulationStrategyService
from quant_trading.factors.market import MarketFactorDefinition
from .market_factor_service import MarketFactorDefinitionService
from .models import (
    AlgorithmOverview,
    AuditAction,
    ComponentMetadata,
    ComponentType,
    ConfigurationDiff,
    ConfigurationRecord,
    ControlSnapshot,
    DraftConfiguration,
    ParameterValue,
    PreviewKind,
    PreviewRequest,
    PreviewResult,
    ValidationResult,
)
from .admission_models import ActivationEvidence, FeatureState, PipelineAdmissionResult
from .preview_service import PreviewService
from .proposal_registry import ChangeProposalRegistry
from .registry import AlgorithmComponentRegistry
from .validation_service import ConfigurationValidator


class AlgorithmControlController:
    """Coordinate management operations without containing algorithm logic."""

    def __init__(
        self,
        registry: AlgorithmComponentRegistry,
        configurations: ConfigurationService,
        validator: ConfigurationValidator,
        previews: PreviewService,
        roles: ApplicationRoleSettings = ApplicationRoleSettings(),
        proposals: ChangeProposalRegistry | None = None,
        factor_definitions: FactorDefinitionService | None = None,
        factor_lifecycle: FactorLifecycleService | None = None,
        decision_definitions: DecisionDefinitionService | None = None,
        simulation_strategies: SimulationStrategyService | None = None,
        market_factor_definitions: MarketFactorDefinitionService | None = None,
    ) -> None:
        self.registry = registry
        self.configurations = configurations
        self.validator = validator
        self.previews = previews
        self.roles = roles
        self.proposals = proposals or ChangeProposalRegistry()
        self.factor_definitions = factor_definitions
        self.factor_lifecycle = factor_lifecycle
        self.decision_definitions = decision_definitions
        self.simulation_strategies = simulation_strategies
        self.market_factor_definitions = market_factor_definitions

    def snapshot(self) -> ControlSnapshot:
        state = self.configurations.state()
        active = self.configurations.active_records()
        components = self.registry.list()
        admission = self.registry.admission.assess_pipeline(
            components, active, self.proposals.unresolved_ids()
        )
        return ControlSnapshot(
            components=components,
            configurations=state.configurations,
            audit_records=state.audit_records,
            overview=AlgorithmOverview(
                factor_count=sum(item.component_type in (ComponentType.FACTOR,ComponentType.MARKET_FACTOR) for item in components),
                decision_count=sum(item.component_type is ComponentType.DECISION for item in components),
                risk_count=sum(item.component_type is ComponentType.RISK for item in components),
                active_configuration_count=len(active),
                pipeline_validation=self.validator.validate_pipeline(active),
                execution_environment=self.roles.execution_environment,
                live_trading_enabled=self.roles.live_trading_enabled,
                automatic_submission_enabled=self.roles.automatic_order_submission,
                last_verified_utc=datetime.now(UTC),
                pipeline_readiness=admission.readiness,
                conflicts=admission.conflicts,
            ),
        )

    def components(self, component_type: ComponentType | None = None) -> tuple[ComponentMetadata, ...]:
        return self.registry.list(component_type)

    def create_draft(self, component_id: str) -> DraftConfiguration:
        return self.configurations.create_draft(component_id)

    def update_draft(self, draft_id: UUID, values: dict[str, ParameterValue], enabled: bool, selected_factor_ids: tuple[str, ...] | None = None) -> DraftConfiguration:
        return self.configurations.update_draft(draft_id, values, enabled, selected_factor_ids=selected_factor_ids)

    def factor_definition_history(self, factor_id: str | None = None) -> tuple[FactorDefinition, ...]:
        return () if self.factor_definitions is None else self.factor_definitions.list_definitions(factor_id)

    def save_factor_definition(self, **values: object) -> FactorDefinition:
        if self.factor_definitions is None:
            raise RuntimeError("Factor authoring is not configured")
        return self.factor_definitions.save(**values)

    def market_factor_definition_history(self, identifier: str | None = None) -> tuple[MarketFactorDefinition,...]:
        return () if self.market_factor_definitions is None else self.market_factor_definitions.list_definitions(identifier)

    def save_market_factor_definition(self, **values: object) -> MarketFactorDefinition:
        if self.market_factor_definitions is None: raise RuntimeError("Market Factor authoring is not configured")
        return self.market_factor_definitions.save(**values)

    def factor_lifecycle_record(self, component_id: str) -> FactorLifecycleRecord:
        if self.factor_lifecycle is None:
            raise RuntimeError("Factor lifecycle management is not configured")
        return self.factor_lifecycle.record_for(component_id)

    def set_factor_lifecycle(
        self,
        component_id: str,
        state: FactorLifecycleState,
        reason: str,
    ) -> FactorLifecycleRecord:
        if self.factor_lifecycle is None:
            raise RuntimeError("Factor lifecycle management is not configured")
        return self.factor_lifecycle.transition(component_id, state, reason=reason)

    def decision_definition_history(self, policy_id: str | None = None) -> tuple[DecisionPolicyDefinition, ...]:
        return () if self.decision_definitions is None else self.decision_definitions.list_definitions(policy_id)

    def save_decision_definition(self, **values: object) -> DecisionPolicyDefinition:
        if self.decision_definitions is None:
            raise RuntimeError("Decision authoring is not configured")
        return self.decision_definitions.save(**values)

    def simulation_strategy_history(self, strategy_id: str | None = None) -> tuple[SimulationStrategyDefinition, ...]:
        return () if self.simulation_strategies is None else self.simulation_strategies.list_definitions(strategy_id)

    def save_simulation_strategy(self, **values: object) -> SimulationStrategyDefinition:
        if self.simulation_strategies is None: raise RuntimeError("Simulation Strategy management is not configured")
        return self.simulation_strategies.save(**values)

    def set_feature_state(
        self,
        draft_id: UUID,
        feature_state: FeatureState,
        evidence: ActivationEvidence,
    ) -> DraftConfiguration:
        return self.configurations.set_feature_state(draft_id, feature_state, evidence)

    def pipeline_admission(self) -> PipelineAdmissionResult:
        return self.registry.admission.assess_pipeline(
            self.registry.list(),
            self.configurations.active_records(),
            self.proposals.unresolved_ids(),
        )

    def validate_draft(self, draft_id: UUID) -> ValidationResult:
        return self.configurations.validate_draft(draft_id)

    def discard_draft(self, draft_id: UUID) -> None:
        self.configurations.discard_draft(draft_id)

    def save_draft(self, draft_id: UUID, reason: str) -> ConfigurationRecord:
        return self.configurations.save_draft(draft_id, reason=reason)

    def activate(self, configuration_id: UUID, reason: str) -> ConfigurationRecord:
        return self.configurations.activate(configuration_id, reason=reason)

    def restore(self, configuration_id: UUID, reason: str) -> ConfigurationRecord:
        return self.configurations.restore(configuration_id, reason=reason)

    def history(self, component_id: str) -> tuple[ConfigurationRecord, ...]:
        return self.configurations.history(component_id)

    def compare(self, before_id: UUID, after_id: UUID) -> tuple[ConfigurationDiff, ...]:
        return self.configurations.compare(before_id, after_id)

    def preview(self, request: PreviewRequest) -> PreviewResult:
        action = {
            PreviewKind.FACTOR: AuditAction.RUN_FACTOR_TEST,
            PreviewKind.DECISION: AuditAction.RUN_DECISION_PREVIEW,
            PreviewKind.RISK: AuditAction.RUN_RISK_PREVIEW,
            PreviewKind.PIPELINE_DRY_RUN: AuditAction.RUN_PIPELINE_DRY_RUN,
        }[request.kind]
        component_id = request.component_ids[0] if len(request.component_ids) == 1 else None
        try:
            result = self.previews.run(request)
        except Exception:
            self.configurations.record_preview(action, component_id, "failed_no_execution")
            raise
        self.configurations.record_preview(action, component_id, result.status.value)
        return result
