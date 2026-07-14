from datetime import date
from pathlib import Path
from quant_trading.algorithm_control.app import build_controller
from quant_trading.algorithm_control.admission_models import (
    ActivationEvidence,
    Capability,
    FeatureState,
    OwnerLayer,
    Responsibility,
)
from quant_trading.algorithm_control.audit_service import AuditService
from quant_trading.algorithm_control.configuration_service import ConfigurationService
from quant_trading.algorithm_control.models import (
    ComponentMetadata,
    ComponentStatus,
    ComponentType,
    ConfigurationStatus,
    ParameterSchema,
    ParameterType,
)
from quant_trading.algorithm_control.registry import AlgorithmComponentRegistry
from quant_trading.algorithm_control.storage import InMemoryControlPlaneStore, JsonControlPlaneStore
from quant_trading.algorithm_control.validation_service import ConfigurationValidator


def test_locked_defaults_are_active_and_versioned(tmp_path: Path):
    controller = build_controller(tmp_path)
    snapshot = controller.snapshot()
    assert len(snapshot.components) == 4
    assert len(snapshot.configurations) == 4
    assert all(item.status is ConfigurationStatus.ACTIVE and item.enabled for item in snapshot.configurations)
    assert not snapshot.overview.live_trading_enabled
    assert not snapshot.overview.automatic_submission_enabled


def test_json_store_survives_restart_and_is_separate_from_market_database(tmp_path: Path):
    first = build_controller(tmp_path).snapshot()
    state_path = tmp_path / "runtime" / "algorithm_control" / "control_state.json"
    assert state_path.exists()
    assert "market_history.sqlite3" not in str(state_path)
    second = build_controller(tmp_path).snapshot()
    assert [item.configuration_id for item in second.configurations] == [item.configuration_id for item in first.configurations]


def test_json_store_uses_atomic_temporary_file_cleanup(tmp_path: Path):
    controller = build_controller(tmp_path)
    controller.snapshot()
    assert not list((tmp_path / "runtime" / "algorithm_control").glob("*.tmp"))


def test_restore_never_overwrites_history(tmp_path: Path):
    controller = build_controller(tmp_path)
    source = controller.snapshot().configurations[0]
    # Locked configurations cannot be changed through the GUI, but the service's
    # append-only restoration contract remains testable and preserves safety state.
    restored = controller.restore(source.configuration_id, "Regression-test restore")
    history = controller.history(source.component_id)
    assert restored.configuration_version == 2
    assert len(history) == 2
    assert source.configuration_id in {item.configuration_id for item in history}
    assert restored.configuration_id != source.configuration_id


def test_store_round_trips_audit_enum_values(tmp_path: Path):
    controller = build_controller(tmp_path)
    reloaded = JsonControlPlaneStore(tmp_path / "runtime" / "algorithm_control" / "control_state.json").load()
    assert len(reloaded.audit_records) == 4
    assert all(record.session_id.startswith("ALG-") for record in reloaded.audit_records)


def configurable_service():
    metadata = ComponentMetadata(
        component_id="test.factor.metadata",
        display_name="Test metadata",
        component_type=ComponentType.FACTOR,
        version="1",
        description="Configuration lifecycle test; no factor formula.",
        status=ComponentStatus.NOT_IMPLEMENTED,
        parameter_schema=(ParameterSchema("lookback", "Lookback", "Test only", ParameterType.INTEGER, 5, 1, 20),),
        input_contract="NoInput",
        output_contract="NoOutput",
        minimum_data_requirements="None",
        enabled_by_default=False,
        implementation_path="Not implemented",
        documentation_path="tests only",
        owner_layer=OwnerLayer.FACTOR,
        owner_module="tests.factor",
        responsibilities=(Responsibility.CALCULATE_SINGLE_ASSET_FACTORS,),
        non_responsibilities=("Does not create trade intents.",),
        required_capabilities=(Capability.CALCULATE_FACTORS,),
    )
    registry = AlgorithmComponentRegistry((metadata,))
    validator = ConfigurationValidator(registry)
    return ConfigurationService(registry, InMemoryControlPlaneStore(), validator, AuditService("TEST-SESSION"))


def test_draft_save_and_apply_are_distinct_versioned_actions():
    service = configurable_service()
    draft = service.create_draft("test.factor.metadata")
    service.update_draft(draft.draft_id, {"lookback": 10}, True)
    service.set_feature_state(
        draft.draft_id,
        FeatureState.ENABLED_FOR_PREVIEW,
        ActivationEvidence(unit_tested=True),
    )
    saved = service.save_draft(draft.draft_id, reason="Save test settings")
    assert saved.status is ConfigurationStatus.SAVED
    assert service.active("test.factor.metadata") is None
    active = service.activate(saved.configuration_id, reason="Apply after review")
    assert active.status is ConfigurationStatus.ACTIVE
    assert active.configuration_version == 2
    assert service.active("test.factor.metadata") == active


def test_implemented_component_cannot_be_enabled_without_activation_evidence():
    service = configurable_service()
    draft = service.create_draft("test.factor.metadata")
    service.update_draft(draft.draft_id, {"lookback": 10}, True)
    result = service.validate_draft(draft.draft_id)
    assert not result.valid
    assert any(issue.code == "CONFLICT-ACTIVATION-EVIDENCE" for issue in result.issues)


def test_compare_reports_changed_parameters_without_overwriting_versions():
    service = configurable_service()
    first_draft = service.create_draft("test.factor.metadata")
    first = service.save_draft(first_draft.draft_id, reason="First")
    second_draft = service.create_draft("test.factor.metadata")
    service.update_draft(second_draft.draft_id, {"lookback": 12}, False)
    second = service.save_draft(second_draft.draft_id, reason="Second")
    diff = service.compare(first.configuration_id, second.configuration_id)
    assert [(item.name, item.before, item.after) for item in diff] == [("lookback", 5, 12)]
    assert len(service.history("test.factor.metadata")) == 2
