from __future__ import annotations

from decimal import Decimal
from pathlib import Path
import json

import pytest

from quant_trading.algorithm_control.app import build_controller
from quant_trading.algorithm_control.factor_definition_store import (
    JsonFactorDefinitionStore,
)
from quant_trading.algorithm_control.models import ComponentType, ConfigurationStatus
from quant_trading.factors import FactorDefinitionParameter
from quant_trading.factors.errors import FactorDefinitionError
from quant_trading.algorithm_control.errors import ControlStoreError
from quant_trading.algorithm_control.factor_lifecycle import FactorLifecycleState
from quant_trading.algorithm_control.models import ComponentStatus


def _save(controller, expression: str = 'latest("close")'):
    return controller.save_factor_definition(
        factor_id="user.close_value",
        display_name="User close value",
        description="User-authored restricted Factor for tests.",
        expression=expression,
        minimum_observations=1,
        output_unit="USD",
        missing_input_policy="return_missing_status",
        parameters=(FactorDefinitionParameter("scale", Decimal("1")),),
        change_reason="Test immutable authoring",
    )


def test_saved_factor_definitions_are_immutable_versioned_and_disabled(
    tmp_path: Path,
) -> None:
    controller = build_controller(tmp_path)
    first = _save(controller)
    second = _save(controller, 'latest("close") * scale')

    assert (first.version, second.version) == (1, 2)
    assert first.definition_id != second.definition_id
    assert first.expression == 'latest("close")'
    components = controller.components(ComponentType.FACTOR)
    assert {item.component_id for item in components} == {
        first.component_id,
        second.component_id,
    }
    assert all(not item.enabled_by_default for item in components)
    assert all(not item.execution_allowed and not item.live_allowed for item in components)
    assert controller.configurations.active(first.component_id) is None


def test_factor_definition_json_round_trip_preserves_decimal_values(
    tmp_path: Path,
) -> None:
    controller = build_controller(tmp_path)
    expected = _save(controller)

    reloaded = JsonFactorDefinitionStore(
        tmp_path / "runtime" / "algorithm_control" / "factor_definitions.json"
    ).list_definitions()

    assert reloaded == (expected,)
    assert reloaded[0].parameters[0].default_value == Decimal("1")


def test_invalid_expression_is_never_saved_or_registered(tmp_path: Path) -> None:
    controller = build_controller(tmp_path)

    with pytest.raises(FactorDefinitionError):
        _save(controller, '__import__("os")')

    assert controller.factor_definition_history() == ()
    assert controller.components(ComponentType.FACTOR) == ()


def test_controller_restart_restores_authored_factor_catalog(tmp_path: Path) -> None:
    first = build_controller(tmp_path)
    saved = _save(first)

    second = build_controller(tmp_path)

    assert second.factor_definition_history() == (saved,)
    draft = second.create_draft(saved.component_id)
    assert draft.selected_factor_ids == ()
    record = second.save_draft(draft.draft_id, "Keep disabled after restart")
    assert record.status is ConfigurationStatus.SAVED


def test_definition_store_rejects_tampered_content(tmp_path: Path) -> None:
    controller = build_controller(tmp_path)
    _save(controller)
    path = tmp_path / "runtime" / "algorithm_control" / "factor_definitions.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["definitions"][0]["expression"] = 'latest("high")'
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ControlStoreError):
        JsonFactorDefinitionStore(path).list_definitions()


def test_factor_version_can_be_archived_and_restored_without_deletion(tmp_path: Path) -> None:
    controller = build_controller(tmp_path)
    saved = _save(controller)

    archived = controller.set_factor_lifecycle(
        saved.component_id,
        FactorLifecycleState.ARCHIVED,
        "Hide this version from new Decision configurations",
    )

    assert archived.state is FactorLifecycleState.ARCHIVED
    assert controller.registry.get(saved.component_id).status is ComponentStatus.DEPRECATED
    assert controller.factor_definition_history() == (saved,)

    restarted = build_controller(tmp_path)
    assert restarted.factor_lifecycle_record(saved.component_id).state is FactorLifecycleState.ARCHIVED
    assert restarted.registry.get(saved.component_id).status is ComponentStatus.DEPRECATED
    assert restarted.factor_definition_history() == (saved,)

    restarted.set_factor_lifecycle(
        saved.component_id,
        FactorLifecycleState.AVAILABLE,
        "Restore this immutable version for future selection",
    )
    assert restarted.registry.get(saved.component_id).status is ComponentStatus.AVAILABLE
