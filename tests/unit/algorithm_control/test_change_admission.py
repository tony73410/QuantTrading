from dataclasses import replace
from datetime import UTC, date, datetime
from uuid import uuid4

import pytest

from quant_trading.algorithm_control.admission_models import (
    ActivationEvidence,
    Capability,
    ChangeProposal,
    ConflictAssessmentStatus,
    FeatureState,
    OwnerLayer,
    PipelineReadiness,
    ProposalStatus,
    Responsibility,
)
from quant_trading.algorithm_control.admission_service import ChangeAdmissionService
from quant_trading.algorithm_control.contracts import (
    CompatibilityResult,
    ContractStatus,
    DataContractDeclaration,
    default_contract_registry,
)
from quant_trading.algorithm_control.models import (
    ComponentMetadata,
    ComponentStatus,
    ComponentType,
    ConfigurationRecord,
    ConfigurationStatus,
)
from quant_trading.algorithm_control.registry import AlgorithmComponentRegistry
from quant_trading.algorithm_control.system_components import locked_safety_components


def metadata(
    component_id: str,
    component_type: ComponentType,
    owner: OwnerLayer,
    responsibility: Responsibility,
    capability: Capability,
) -> ComponentMetadata:
    return ComponentMetadata(
        component_id=component_id,
        display_name=component_id,
        component_type=component_type,
        version="1.0",
        description="Test-only metadata; no algorithm or order behavior.",
        status=ComponentStatus.NOT_IMPLEMENTED,
        parameter_schema=(),
        input_contract="NoInput",
        output_contract="NoOutput",
        minimum_data_requirements="None",
        enabled_by_default=False,
        implementation_path="tests only",
        documentation_path="tests only",
        owner_layer=owner,
        owner_module=f"tests.{owner.value}",
        responsibilities=(responsibility,),
        non_responsibilities=("Does not submit orders.",),
        required_capabilities=(capability,),
    )


def record(component: ComponentMetadata, state: FeatureState) -> ConfigurationRecord:
    return ConfigurationRecord(
        configuration_id=uuid4(),
        configuration_version=1,
        component_id=component.component_id,
        component_version=component.version,
        created_at_utc=datetime.now(UTC),
        created_by="test",
        parameter_values=(),
        previous_version=None,
        change_reason="Admission test",
        status=ConfigurationStatus.ACTIVE,
        enabled=True,
        feature_state=state,
        activation_evidence=ActivationEvidence(
            unit_tested=True,
            integration_tested=True,
            dry_run_validated=True,
            historical_simulation_validated=True,
            paper_validated=True,
            manual_approval=True,
        ),
    )


def test_component_defaults_to_registered_and_cannot_gain_another_layers_capability():
    component = metadata(
        "factor.bad-permission",
        ComponentType.FACTOR,
        OwnerLayer.FACTOR,
        Responsibility.CALCULATE_SINGLE_ASSET_FACTORS,
        Capability.SUBMIT_PAPER_ORDER,
    )
    registry = AlgorithmComponentRegistry()
    assert component.default_feature_state is FeatureState.REGISTERED
    assert registry.registration_status(component) is ComponentStatus.INVALID
    conflict = registry.admission.assess_component(component)[0]
    assert conflict.status is ConflictAssessmentStatus.PERMISSION_CONFLICT


def test_activation_requires_evidence_and_cannot_skip_stages():
    component = metadata(
        "factor.safe",
        ComponentType.FACTOR,
        OwnerLayer.FACTOR,
        Responsibility.CALCULATE_SINGLE_ASSET_FACTORS,
        Capability.CALCULATE_FACTORS,
    )
    service = ChangeAdmissionService(default_contract_registry())
    missing = service.validate_transition(
        component, FeatureState.REGISTERED, FeatureState.ENABLED_FOR_PREVIEW
    )
    assert any(item.conflict_id == "CONFLICT-ACTIVATION-EVIDENCE" for item in missing)
    skipping = service.validate_transition(
        component,
        FeatureState.REGISTERED,
        FeatureState.ENABLED_FOR_DRY_RUN,
        ActivationEvidence(unit_tested=True, integration_tested=True),
    )
    assert any(item.conflict_id == "CONFLICT-ACTIVATION-SKIP" for item in skipping)


def test_opposing_decision_policies_block_pipeline_instead_of_being_combined():
    factor = metadata(
        "factor.one", ComponentType.FACTOR, OwnerLayer.FACTOR,
        Responsibility.CALCULATE_SINGLE_ASSET_FACTORS, Capability.CALCULATE_FACTORS,
    )
    first = metadata(
        "decision.one", ComponentType.DECISION, OwnerLayer.DECISION,
        Responsibility.CREATE_TRADE_INTENTS, Capability.CREATE_TRADE_INTENT,
    )
    second = metadata(
        "decision.two", ComponentType.DECISION, OwnerLayer.DECISION,
        Responsibility.CREATE_TRADE_INTENTS, Capability.CREATE_TRADE_INTENT,
    )
    risk = metadata(
        "risk.one", ComponentType.RISK, OwnerLayer.RISK,
        Responsibility.EVALUATE_RISK, Capability.REJECT_TRADE,
    )
    components = (*locked_safety_components(), factor, first, second, risk)
    records = tuple(record(item, FeatureState.ENABLED_FOR_DRY_RUN) for item in components if not item.locked)
    records += tuple(record(item, FeatureState.ACTIVE) for item in components if item.locked)
    result = ChangeAdmissionService(default_contract_registry()).assess_pipeline(components, records)
    assert result.readiness is PipelineReadiness.BLOCKED
    assert any(item.conflict_id == "CONFLICT-DECISION-MULTIPLE-PRIMARY" for item in result.conflicts)


def test_preview_only_components_cannot_enter_complete_pipeline_dry_run():
    factor = metadata(
        "factor.one", ComponentType.FACTOR, OwnerLayer.FACTOR,
        Responsibility.CALCULATE_SINGLE_ASSET_FACTORS, Capability.CALCULATE_FACTORS,
    )
    decision = metadata(
        "decision.one", ComponentType.DECISION, OwnerLayer.DECISION,
        Responsibility.CREATE_TRADE_INTENTS, Capability.CREATE_TRADE_INTENT,
    )
    risk = metadata(
        "risk.one", ComponentType.RISK, OwnerLayer.RISK,
        Responsibility.EVALUATE_RISK, Capability.REJECT_TRADE,
    )
    components = (*locked_safety_components(), factor, decision, risk)
    records = tuple(record(item, FeatureState.ENABLED_FOR_PREVIEW) for item in (factor, decision, risk))
    records += tuple(record(item, FeatureState.ACTIVE) for item in components if item.locked)
    result = ChangeAdmissionService(default_contract_registry()).assess_pipeline(components, records)
    assert result.readiness is PipelineReadiness.BLOCKED
    assert any(item.conflict_id == "CONFLICT-PIPELINE-ACTIVATION-STAGE" for item in result.conflicts)


def test_multiple_risk_rules_may_be_registered_for_strict_combination():
    first = metadata(
        "risk.one", ComponentType.RISK, OwnerLayer.RISK,
        Responsibility.EVALUATE_RISK, Capability.REJECT_TRADE,
    )
    second = metadata(
        "risk.two", ComponentType.RISK, OwnerLayer.RISK,
        Responsibility.EVALUATE_RISK, Capability.REDUCE_TRADE,
    )
    registry = AlgorithmComponentRegistry((first, second))
    assert registry.component_ids == ("risk.one", "risk.two")


def test_contract_major_change_requires_migration_and_type_change_requires_adapter():
    registry = default_contract_registry()
    current = registry.get("FactorSnapshot")
    common = (
        current.contract_id,
        current.producer_layer,
        current.consumer_layers,
        current.created_at_semantics,
        current.source_component_semantics,
        current.source_version_semantics,
        current.correlation_id_semantics,
        ContractStatus.IMPLEMENTED,
    )
    major = DataContractDeclaration(common[0], "2.0", current.python_type, *common[1:])
    changed_type = DataContractDeclaration(common[0], "1.1", "other.Type", *common[1:])
    assert registry.compare("FactorSnapshot", major) is CompatibilityResult.REQUIRES_MIGRATION
    assert registry.compare("FactorSnapshot", changed_type) is CompatibilityResult.REQUIRES_ADAPTER


def test_component_cannot_consume_contract_outside_declared_layer_boundary():
    component = metadata(
        "factor.wrong-contract",
        ComponentType.FACTOR,
        OwnerLayer.FACTOR,
        Responsibility.CALCULATE_SINGLE_ASSET_FACTORS,
        Capability.CALCULATE_FACTORS,
    )
    component = replace(component, input_contract="TradeIntent")
    conflicts = ChangeAdmissionService(default_contract_registry()).assess_component(component)
    assert any(item.conflict_id == "CONFLICT-CONTRACT-CONSUMER" for item in conflicts)


def test_ai_recommendation_cannot_be_recorded_as_user_approved():
    with pytest.raises(ValueError, match="explicit user approval"):
        ChangeProposal(
            proposal_id="PROPOSAL-999",
            title="Test",
            status=ProposalStatus.APPROVED,
            proposal_date=date.today(),
            user_request="Test request",
            user_goal="Test goal",
            user_suggested_method="None",
            professional_interpretation="Test only",
            owning_layer=OwnerLayer.FACTOR,
            owning_module="tests.factor",
            responsibilities=(Responsibility.CALCULATE_SINGLE_ASSET_FACTORS,),
            non_responsibilities=("No decisions",),
            input_contracts=("MarketDataWindow",),
            output_contracts=("FactorSnapshot",),
            required_dependencies=(),
            forbidden_dependencies=("decision",),
            required_capabilities=(Capability.CALCULATE_FACTORS,),
            side_effects=(),
            financial_meaning="None",
            risk_implications="None",
            safety_implications="Disabled",
            affected_components=(),
            conflicts=(),
            backward_compatibility="Compatible",
            migration_requirements="None",
            feature_state=FeatureState.DISABLED,
            testing_plan="Unit tests",
            dry_run_plan="Dry run",
            rollback_plan="Disable",
            documentation_impact="Test only",
            recommendation="AI recommendation only",
            user_approval_status="AI recommended",
            created_at_utc=datetime.now(UTC),
        )
