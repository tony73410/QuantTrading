from datetime import date
from decimal import Decimal

import pytest

from quant_trading.algorithm_control.errors import ComponentRegistrationError
from quant_trading.algorithm_control.admission_models import (
    ActivationEvidence,
    Capability,
    FeatureState,
    OwnerLayer,
    Responsibility,
)
from quant_trading.algorithm_control.models import (
    ComponentMetadata,
    ComponentStatus,
    ComponentType,
    ParameterSchema,
    ParameterSetting,
    ParameterType,
    SafetyLevel,
    ValidationStatus,
)
from quant_trading.algorithm_control.registry import AlgorithmComponentRegistry
from quant_trading.algorithm_control.system_components import locked_safety_components
from quant_trading.algorithm_control.validation_service import ConfigurationValidator


def component(*, required_factors=()):
    return ComponentMetadata(
        component_id="example.factor",
        display_name="Example metadata only",
        component_type=ComponentType.FACTOR,
        version="1",
        description="Test-only metadata; no formula.",
        status=ComponentStatus.NOT_IMPLEMENTED,
        parameter_schema=(
            ParameterSchema("count", "Count", "Integer test", ParameterType.INTEGER, 2, 1, 5),
            ParameterSchema("rate", "Rate", "Percentage test", ParameterType.PERCENTAGE, Decimal("10"), Decimal("0"), Decimal("100")),
            ParameterSchema("mode", "Mode", "Enum test", ParameterType.ENUM, "a", allowed_values=("a", "b")),
            ParameterSchema("day", "Day", "Date test", ParameterType.DATE, date(2026, 1, 1)),
            ParameterSchema("items", "Items", "List test", ParameterType.LIST, ("A",)),
        ),
        input_contract="NoInput",
        output_contract="NoOutput",
        minimum_data_requirements="None",
        enabled_by_default=False,
        implementation_path="Not implemented",
        documentation_path="tests only",
        required_factors=required_factors,
        owner_layer=OwnerLayer.FACTOR,
        owner_module="tests.factor",
        responsibilities=(Responsibility.CALCULATE_SINGLE_ASSET_FACTORS,),
        non_responsibilities=("Does not make trading decisions.",),
        required_capabilities=(Capability.CALCULATE_FACTORS,),
    )


def test_registry_rejects_duplicate_component_ids():
    metadata = component()
    registry = AlgorithmComponentRegistry((metadata,))
    with pytest.raises(ComponentRegistrationError):
        registry.register(metadata)


def test_registry_filters_by_component_type_without_algorithm_conditionals():
    registry = AlgorithmComponentRegistry((*locked_safety_components(), component()))
    assert registry.list(ComponentType.FACTOR) == (component(),)
    assert all(item.component_type is ComponentType.RISK for item in registry.list(ComponentType.RISK))


def test_schema_validation_accepts_all_supported_representative_values():
    metadata = component()
    validator = ConfigurationValidator(AlgorithmComponentRegistry((metadata,)))
    result = validator.validate(
        metadata,
        (
            ParameterSetting("count", 3),
            ParameterSetting("rate", Decimal("25.5")),
            ParameterSetting("mode", "b"),
            ParameterSetting("day", date(2026, 7, 14)),
            ParameterSetting("items", ("AAPL", "MSFT")),
        ),
        True,
        feature_state=FeatureState.ENABLED_FOR_PREVIEW,
        activation_evidence=ActivationEvidence(unit_tested=True),
    )
    assert result.status is ValidationStatus.VALID


def test_schema_validation_reports_type_range_enum_and_unknown_errors():
    metadata = component()
    result = ConfigurationValidator(AlgorithmComponentRegistry((metadata,))).validate(
        metadata,
        (
            ParameterSetting("count", 20),
            ParameterSetting("rate", "not numeric"),
            ParameterSetting("mode", "c"),
            ParameterSetting("day", date(2026, 7, 14)),
            ParameterSetting("items", ("",)),
            ParameterSetting("unknown", 1),
        ),
        True,
    )
    assert result.status is ValidationStatus.INVALID
    assert {issue.code for issue in result.issues} >= {"MAXIMUM", "TYPE", "ENUM", "LIST_ITEM", "UNKNOWN_PARAMETER"}


def test_locked_safety_component_cannot_be_disabled():
    metadata = locked_safety_components()[0]
    result = ConfigurationValidator(AlgorithmComponentRegistry((metadata,))).validate(metadata, (), False)
    assert result.status is ValidationStatus.INVALID
    assert result.issues[0].code == "LOCKED_SAFETY"


def test_required_factor_dependency_must_be_active():
    metadata = component(required_factors=("missing.factor",))
    result = ConfigurationValidator(AlgorithmComponentRegistry((metadata,))).validate(
        metadata,
        tuple(ParameterSetting(schema.name, schema.default_value) for schema in metadata.parameter_schema),
        True,
    )
    assert result.status is ValidationStatus.INVALID
    assert any(issue.code == "MISSING_DEPENDENCY" for issue in result.issues)
