from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from quant_trading.algorithm_control.app import build_controller
from quant_trading.algorithm_control.ui.decision_authoring_panel import DecisionAuthoringPanel
from quant_trading.algorithm_control.models import ComponentType
from quant_trading.decision import (
    ComparisonOperator,
    DecisionAction,
    DecisionCondition,
    DecisionContext,
    DecisionInput,
    DecisionStatus,
    PortfolioSnapshot,
    RuleCombination,
    SafeRuleDecisionPolicy,
)
from quant_trading.factors import FactorResult, FactorSnapshot, FactorSnapshotCollection, FactorStatus
from quant_trading.market_history.models import Timeframe


def _factor(controller):
    return controller.save_factor_definition(
        factor_id="decision.input",
        display_name="Decision input",
        description="Exact Factor version used by Decision authoring tests.",
        expression='latest("close")',
        minimum_observations=1,
        output_unit="USD",
        missing_input_policy="return_missing_status",
        parameters=(),
        change_reason="Create Decision test input",
    )


def _snapshot(factor_name: str, factor_version: str, value: Decimal) -> FactorSnapshot:
    as_of = datetime(2026, 1, 2, tzinfo=UTC)
    result = FactorResult(
        "AAPL", as_of, Timeframe.DAY, factor_name, factor_version, value, "USD", (), 1,
        FactorStatus.VALID, (), as_of, as_of, as_of,
    )
    return FactorSnapshot(uuid4(), "AAPL", as_of, Timeframe.DAY, (result,), as_of)


def test_decision_definition_is_versioned_disabled_and_references_exact_factor(tmp_path: Path) -> None:
    controller = build_controller(tmp_path)
    factor = _factor(controller)
    condition = DecisionCondition(
        factor.component_id,
        factor.factor_id,
        str(factor.version),
        ComparisonOperator.GREATER_THAN,
        Decimal("100"),
    )

    first = controller.save_decision_definition(
        policy_id="test.direction",
        display_name="Test direction",
        description="Restricted action-only policy for tests.",
        conditions=(condition,),
        combination=RuleCombination.ALL,
        match_action=DecisionAction.INCREASE,
        reason_code="USER_RULE_MATCHED",
        change_reason="Create first immutable Decision version",
    )
    second = controller.save_decision_definition(
        policy_id="test.direction",
        display_name="Test direction",
        description="Restricted action-only policy for tests.",
        conditions=(condition,),
        combination=RuleCombination.ALL,
        match_action=DecisionAction.DECREASE,
        reason_code="USER_RULE_MATCHED",
        change_reason="Create second immutable Decision version",
    )

    assert (first.version, second.version) == (1, 2)
    components = controller.components(ComponentType.DECISION)
    assert {item.component_id for item in components} == {first.component_id, second.component_id}
    assert all(not item.enabled_by_default and not item.execution_allowed for item in components)
    assert all(item.required_factors == (factor.component_id,) for item in components)


def test_safe_decision_policy_can_run_from_fake_factor_snapshot_without_order(tmp_path: Path) -> None:
    controller = build_controller(tmp_path)
    factor = _factor(controller)
    definition = controller.save_decision_definition(
        policy_id="test.fake",
        display_name="Fake snapshot policy",
        description="Runs independently from provider and SQLite.",
        conditions=(DecisionCondition(
            factor.component_id, factor.factor_id, str(factor.version),
            ComparisonOperator.GREATER_THAN_OR_EQUAL, Decimal("100"),
        ),),
        combination=RuleCombination.ALL,
        match_action=DecisionAction.INCREASE,
        reason_code="FAKE_FACTOR_MATCH",
        change_reason="Test Fake FactorSnapshot boundary",
    )
    snapshot = _snapshot(factor.factor_id, str(factor.version), Decimal("101"))
    as_of = snapshot.as_of_utc

    result = SafeRuleDecisionPolicy(definition).evaluate(
        DecisionInput(
            FactorSnapshotCollection(uuid4(), as_of, (snapshot,)),
            PortfolioSnapshot(uuid4(), as_of),
            DecisionContext(as_of),
        )
    )

    assert result.status is DecisionStatus.VALID
    assert result.intents[0].action is DecisionAction.INCREASE
    assert result.intents[0].target_exposure is None
    assert result.intents[0].desired_change is None


def test_add_condition_button_adds_an_empty_row_without_passing_qt_checked_state(tmp_path: Path) -> None:
    application = QApplication.instance() or QApplication([])
    panel = DecisionAuthoringPanel(build_controller(tmp_path))

    calls = []
    original = panel._add_blank_condition
    panel._add_blank_condition = lambda: (calls.append("blank"), original())[1]  # type: ignore[method-assign]
    panel.add_button.clicked[bool].emit(False)

    assert calls == ["blank"]
    assert panel.conditions.rowCount() == 1
    panel.close()
    assert application is not None
