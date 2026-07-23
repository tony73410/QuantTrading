from __future__ import annotations

import os
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from quant_trading.algorithm_control.ui.research_cash_floor_panel import (
    ResearchCashFloorPanel,
)
from quant_trading.risk import (
    ExposureCapDisposition,
    ExposureCapRuleOutcome,
    ResearchCashFloorDefinitionStatus,
    ResearchCashFloorDisposition,
    ResearchCashFloorRuleOutcome,
)


NOW = datetime(2026, 7, 22, 12, tzinfo=UTC)


def test_panel_has_no_floor_default_delegates_and_opens_full_lineage():
    app = QApplication.instance() or QApplication([])
    definition_id, phase6b_result_id, target_calculation_id = (uuid4() for _ in range(3))
    cash_run, phase6b_run, phase6a_run, decision_run, phase5c_run, target_run, source_run = (
        uuid4() for _ in range(7)
    )
    definition = SimpleNamespace(
        definition_id=definition_id,
        definition_version=1,
        predecessor_version=None,
        symbol="AAPL",
        minimum_research_asset_cash_usd=Decimal("35"),
        status=ResearchCashFloorDefinitionStatus.SAVED,
        created_at_utc=NOW,
        reason="explicit floor",
    )
    upstream = SimpleNamespace(
        target_calculation_id=target_calculation_id,
    )
    phase6b_source = SimpleNamespace(
        symbol="AAPL",
        as_of_utc=NOW,
        action="increase",
        current_exposure_usd=Decimal("60"),
        phase6a_source=upstream,
    )
    inherited_rule = SimpleNamespace(
        evaluation_order=1,
        rule_id="MAX_TARGET_EXPOSURE_USD",
        rule_version="1",
        original_requested_notional_usd=Decimal("10"),
        max_target_exposure_usd=Decimal("65"),
        cap_constrained_candidate_notional_usd=Decimal("5"),
        outcome=ExposureCapRuleOutcome.REDUCED_TO_CAP,
        reason_codes=("TARGET_EXCEEDS_CAP",),
    )
    phase6b = SimpleNamespace(
        preview_result_id=phase6b_result_id,
        run_id=phase6b_run,
        disposition=ExposureCapDisposition.MANUAL_REVIEW_REQUIRED,
        source=phase6b_source,
        rule=inherited_rule,
        cap_constrained_candidate_notional_usd=Decimal("5"),
    )
    link = SimpleNamespace(
        phase6a_run_id=phase6a_run,
        decision_run_id=decision_run,
        linked_parent_run_id=phase5c_run,
        target_child_run_id=target_run,
        standardized_state_run_id=source_run,
    )
    linked = SimpleNamespace(
        phase6b_result=phase6b,
        phase6b_source_link=link,
        symbol="AAPL",
        as_of_utc=NOW,
        action="increase",
    )
    rule = SimpleNamespace(
        evaluation_order=2,
        rule_id="MIN_RESEARCH_ASSET_CASH_USD",
        rule_version="1",
        action="increase",
        research_capital_basis_usd=Decimal("100"),
        current_exposure_usd=Decimal("60"),
        phase6b_candidate_notional_usd=Decimal("5"),
        minimum_research_asset_cash_usd=Decimal("35"),
        cash_floor_constrained_candidate_notional_usd=Decimal("5"),
        post_action_research_cash_usd=Decimal("35"),
        outcome=ResearchCashFloorRuleOutcome.PASSED_AT_OR_ABOVE_CASH_FLOOR,
        reason_codes=("CANDIDATE_PRESERVES_RESEARCH_CASH_FLOOR",),
    )
    result = SimpleNamespace(
        run_id=cash_run,
        source=linked,
        rule=rule,
        disposition=ResearchCashFloorDisposition.MANUAL_REVIEW_REQUIRED,
    )
    target = SimpleNamespace(
        calculation_id=target_calculation_id,
        research_capital_basis_usd=Decimal("100"),
    )

    class Queries:
        definition_queries = []

        def list_research_cash_floor_definitions(self, query):
            self.definition_queries.append(query)
            return (definition,)

        def list_research_cash_floor_results(self, query):
            return (result,)

        def list_research_cash_floor_operations(self, query):
            return ()

    class Phase6BQueries:
        def list_exposure_cap_results(self, query):
            assert query.disposition is ExposureCapDisposition.MANUAL_REVIEW_REQUIRED
            return (phase6b,)

    class TargetQueries:
        def get_result(self, calculation_id):
            assert calculation_id == target_calculation_id
            return target

    class DefinitionService:
        save_command = archive_command = None

        def save_definition(self, command):
            self.save_command = command
            return SimpleNamespace(summary="definition delegated")

        def archive_definition(self, command):
            self.archive_command = command
            return SimpleNamespace(summary="archive delegated")

    class PreviewService:
        command = None

        def preview(self, command):
            self.command = command
            return SimpleNamespace(summary="preview delegated")

    queries, definitions, previews = Queries(), DefinitionService(), PreviewService()
    panel = ResearchCashFloorPanel(
        definitions, previews, queries, Phase6BQueries(), TargetQueries(), session_id="GUI"
    )
    opened = []
    panel.open_run_requested.connect(opened.append)

    assert panel.floor_text.text() == ""
    assert panel.definition_choice.currentData() is None
    assert any(item.current_only for item in queries.definition_queries)
    panel.symbol.setText("aapl")
    panel.floor_text.setText("0")
    panel.definition_reason.setText("explicit zero is valid")
    panel.save_button.click()
    assert definitions.save_command.minimum_research_asset_cash_usd == "0"
    assert definitions.save_command.symbol == "AAPL"

    panel.definition_choice.setCurrentIndex(1)
    panel.phase6b_choice.setCurrentIndex(1)
    assert "100" in panel.source_table.item(12, 1).text()
    panel.preview_reason.setText("explicit preview")
    panel.preview_button.click()
    assert previews.command.target_adjustment_exposure_cap_preview_result_id == phase6b_result_id
    assert previews.command.research_cash_floor_definition_id == definition_id
    assert panel.rule_table.rowCount() == 2

    for key in ("cash_floor", "phase6b", "phase6a", "decision", "phase5c", "target", "source"):
        panel._run_buttons[key].click()
    assert opened == [
        cash_run, phase6b_run, phase6a_run, decision_run, phase5c_run, target_run, source_run,
    ]
    panel.close()
    assert app is not None


def test_panel_requires_explicit_definition_source_and_reason():
    app = QApplication.instance() or QApplication([])
    panel = ResearchCashFloorPanel()
    panel.preview_button.setEnabled(True)
    panel.preview_button.click()
    assert "required" in panel.status_text.text()
    panel.save_button.setEnabled(True)
    panel.save_button.click()
    assert "required" in panel.status_text.text()
    panel.archive_button.setEnabled(True)
    panel.archive_button.click()
    assert "required" in panel.status_text.text()
    panel.close()
    assert app is not None
